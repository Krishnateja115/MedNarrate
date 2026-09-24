import fitz
import pytesseract
from PIL import Image, ImageEnhance, ImageOps
import io
import os
import re
import sys
import shutil
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# --- Custom Exception Hierarchy with Specific Failure Categories ---

class ExtractionError(ValueError):
    """Base exception for all text extraction failures."""
    failure_category: str = "EXTRACTION_ERROR"
    
    def __init__(self, message: str, failure_category: str = None):
        super().__init__(message)
        if failure_category:
            self.failure_category = failure_category

class ExtractionFileNotFoundError(ExtractionError):
    failure_category = "FILE_NOT_FOUND"

# Module level alias for backwards compatibility
FileNotFoundError = ExtractionFileNotFoundError

class EmptyFileError(ExtractionError):
    failure_category = "EMPTY_FILE"

class CorruptPDFError(ExtractionError):
    failure_category = "CORRUPT_PDF"

class UnreadablePDFError(ExtractionError):
    failure_category = "PDF_EXTRACTION_ERROR"

class ImageDecodeError(ExtractionError):
    failure_category = "IMAGE_DECODE_ERROR"

class OCRUnavailableError(ExtractionError):
    failure_category = "OCR_ENGINE_UNAVAILABLE"

class OCRFailedError(ExtractionError):
    failure_category = "OCR_FAILED"

class OCRNoMeaningfulTextError(ExtractionError):
    failure_category = "OCR_NO_MEANINGFUL_TEXT"

class UnsupportedFileTypeError(ExtractionError):
    failure_category = "FILE_INVALID"


# --- Helper Utilities & Tesseract Auto-Discovery ---

def find_tesseract_cmd() -> str | None:
    """Finds available Tesseract executable path on system path or standard install locations."""
    # Check explicitly configured path
    tesseract_cmd = getattr(pytesseract.pytesseract, 'tesseract_cmd', 'tesseract')
    if tesseract_cmd and tesseract_cmd != 'tesseract' and os.path.exists(tesseract_cmd):
        return tesseract_cmd

    # Check environment variable
    env_cmd = os.getenv("TESSERACT_CMD")
    if env_cmd and os.path.exists(env_cmd):
        pytesseract.pytesseract.tesseract_cmd = env_cmd
        return env_cmd

    # Check system PATH
    which_path = shutil.which('tesseract')
    if which_path:
        return which_path

    # Common Windows & Linux candidate locations
    candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.join(os.path.expanduser("~"), r"AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        os.path.join(os.path.expanduser("~"), r"AppData\Local\Tesseract-OCR\tesseract.exe"),
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
    ]

    for candidate in candidates:
        if os.path.exists(candidate):
            pytesseract.pytesseract.tesseract_cmd = candidate
            return candidate

    return None

def is_tesseract_available() -> bool:
    """Checks whether the Tesseract OCR executable is available on the system."""
    return find_tesseract_cmd() is not None

def resolve_physical_path(file_path: str) -> str:
    """
    Standardizes and resolves relative '/uploads/...' or relative paths to physical disk paths via settings.UPLOAD_DIR.
    Handles POSIX '/' and Windows '\\' path separators safely and prevents path traversal.
    """
    if not file_path or not str(file_path).strip():
        raise ExtractionFileNotFoundError("File path is empty.", failure_category="FILE_NOT_FOUND")

    upload_dir = os.path.abspath(settings.UPLOAD_DIR)
    
    # Normalize slashes to POSIX for consistent splitting
    normalized_input = str(file_path).replace("\\", "/")
    
    # Strip leading /uploads/ or uploads/ prefixes
    cleaned_rel = normalized_input
    if cleaned_rel.startswith("/uploads/"):
        cleaned_rel = cleaned_rel[len("/uploads/"):]
    elif cleaned_rel.startswith("uploads/"):
        cleaned_rel = cleaned_rel[len("uploads/"):]
    elif cleaned_rel.startswith("/"):
        cleaned_rel = cleaned_rel[1:]

    # Path traversal safety check
    parts = [p for p in cleaned_rel.split("/") if p]
    if ".." in parts:
        raise ExtractionFileNotFoundError("Path traversal attempt detected.", failure_category="FILE_NOT_FOUND")

    # If the input path is already an absolute path that exists on disk (e.g., in test fixtures)
    if os.path.isabs(file_path) and os.path.exists(file_path):
        resolved = os.path.abspath(file_path)
    else:
        resolved = os.path.abspath(os.path.join(upload_dir, *parts))

    # Verification of path safety relative to upload_dir
    try:
        common = os.path.commonpath([upload_dir, resolved])
        is_under_upload = (common == upload_dir)
    except ValueError:
        is_under_upload = False

    if not is_under_upload and not (os.path.isabs(file_path) and os.path.exists(file_path)):
        raise ExtractionFileNotFoundError(f"Resolved path '{resolved}' is outside upload directory.", failure_category="FILE_NOT_FOUND")

    # Physical checks
    if not os.path.exists(resolved) or not os.path.isfile(resolved):
        raise ExtractionFileNotFoundError(f"File not found on server disk: {file_path}", failure_category="FILE_NOT_FOUND")

    if not os.access(resolved, os.R_OK):
        raise UnreadablePDFError(f"File is not readable due to permission restrictions: {file_path}", failure_category="PDF_EXTRACTION_ERROR")

    if os.path.getsize(resolved) == 0:
        raise EmptyFileError(f"File is empty (zero bytes): {file_path}", failure_category="EMPTY_FILE")

    return resolved

def clean_extracted_text(text: str) -> str:
    """
    Cleans extracted OCR or PDF text to prepare it for NER and lab extraction.
    Strictly preserves numeric fidelity (decimals like 8.0, 1.5, medical units, etc.).
    """
    if not text:
        return ""
    # Remove random standalone OCR artifacts like isolated pipes or underscores without mutating numbers
    text = re.sub(r'(?<!\S)[|_](?!\S)', ' ', text)
    # Fix broken word hyphenations across newlines
    text = re.sub(r'(\w+)-\n+(\w+)', r'\1\2', text)
    # Standardize horizontal whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    # Replace 3+ consecutive newlines with a double newline
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def preprocess_image_variants(img: Image.Image) -> list[Image.Image]:
    """Generates preprocessed variants of an image to optimize OCR accuracy for scans/photos."""
    variants = [img]
    try:
        # Grayscale variant
        gray = ImageOps.grayscale(img)
        variants.append(gray)
        
        # High contrast grayscale
        enhancer = ImageEnhance.Contrast(gray)
        high_contrast = enhancer.enhance(1.8)
        variants.append(high_contrast)

        # Rescale if image resolution is low (< 1000px in either dimension)
        w, h = img.size
        if w < 1000 or h < 1000:
            scale = max(2.0, 1200.0 / min(w, h))
            new_size = (int(w * scale), int(h * scale))
            upscaled = high_contrast.resize(new_size, Image.Resampling.LANCZOS)
            variants.append(upscaled)
    except Exception as e:
        logger.warning(f"Image preprocessing warning: {e}")
    return variants

def run_ocr_on_image(img: Image.Image) -> tuple[str, str]:
    """
    Attempts OCR on a PIL Image using Tesseract (with preprocessed variants)
    or EasyOCR as fallback. Returns (extracted_text, ocr_engine_used).
    """
    tesseract_cmd = find_tesseract_cmd()
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        variants = preprocess_image_variants(img)
        best_text = ""
        for v in variants:
            try:
                res = pytesseract.image_to_string(v)
                if len(res.strip()) > len(best_text.strip()):
                    best_text = res
            except Exception as e:
                logger.warning(f"Tesseract OCR variant execution failed: {e}")

        cleaned = clean_extracted_text(best_text)
        if len(cleaned) >= 15:
            return best_text, "tesseract_ocr"

    # Try EasyOCR fallback if available
    try:
        import easyocr
        import numpy as np
        reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        img_np = np.array(img.convert('RGB'))
        results = reader.readtext(img_np, detail=0)
        easy_text = "\n".join(results)
        cleaned_easy = clean_extracted_text(easy_text)
        if len(cleaned_easy) >= 15:
            return easy_text, "easyocr"
    except Exception as easy_e:
        logger.debug(f"EasyOCR fallback not available or failed: {easy_e}")

    if not tesseract_cmd and 'easyocr' not in sys.modules and not best_text and not locals().get('easy_text'):
        raise OCRUnavailableError(
            "The report was uploaded successfully, but text recognition is not available on this server.",
            failure_category="OCR_ENGINE_UNAVAILABLE"
        )

    raise OCRNoMeaningfulTextError(
        "The image was uploaded successfully, but readable medical text could not be extracted from it. Please upload a clearer scan or image.",
        failure_category="OCR_NO_MEANINGFUL_TEXT"
    )

def _ocr_page_pixmap(page: fitz.Page) -> str:
    """Render a PyMuPDF page to an image and attempt OCR with proper cleanup."""
    if not is_tesseract_available():
        raise OCRUnavailableError(
            "Scanned document requires OCR but Tesseract OCR engine is not installed on this server.",
            failure_category="OCR_ENGINE_UNAVAILABLE"
        )
    
    pix = None
    img = None
    try:
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_bytes))
        ocr_result, _ = run_ocr_on_image(img)
        return ocr_result
    except Exception as e:
        if isinstance(e, ExtractionError):
            raise e
        logger.warning(f"OCR failed for PDF page: {e}")
        return ""
    finally:
        if img:
            img.close()
        pix = None

def validate_extracted_text(text: str, is_image: bool = False) -> None:
    """Validates extracted text for character count, word count, and alphanumeric ratio."""
    cleaned = clean_extracted_text(text)
    if not cleaned or len(cleaned) < 15:
        if is_image:
            raise OCRNoMeaningfulTextError(
                "The image was uploaded successfully, but readable medical text could not be extracted from it. Please upload a clearer scan or image.",
                failure_category="OCR_NO_MEANINGFUL_TEXT"
            )
        else:
            raise UnreadablePDFError(
                "Could not extract readable medical text from this PDF document. The file may be scanned or unreadable.",
                failure_category="PDF_EXTRACTION_ERROR"
            )

    words = cleaned.split()
    if len(words) < 3:
        if is_image:
            raise OCRNoMeaningfulTextError(
                "Extracted image text is incomplete or unreadable.",
                failure_category="OCR_NO_MEANINGFUL_TEXT"
            )
        else:
            raise UnreadablePDFError(
                "Extracted PDF text is incomplete or unreadable.",
                failure_category="PDF_EXTRACTION_ERROR"
            )

    # Validate character quality (alphanumeric & standard punctuation ratio)
    alnum_chars = sum(1 for c in cleaned if c.isalnum() or c in " .%/-:()[],;\n")
    if len(cleaned) > 0 and (alnum_chars / len(cleaned)) < 0.4:
        if is_image:
            raise OCRNoMeaningfulTextError(
                "The image quality or layout prevented reliable text extraction.",
                failure_category="OCR_NO_MEANINGFUL_TEXT"
            )
        else:
            raise UnreadablePDFError(
                "Extracted PDF text contained invalid or corrupted character encoding.",
                failure_category="PDF_EXTRACTION_ERROR"
            )

def extract_text_with_diagnostics(file_path: str, file_type: str) -> tuple[str, dict]:
    """
    Extracts text from a physical file (PDF or Image) with diagnostics metadata.
    Returns (cleaned_text, diagnostics_metadata).
    Raises specific ExtractionError subclasses on failure.
    """
    resolved_path = resolve_physical_path(file_path)
    extracted_text = ""
    page_count = 0
    ocr_attempted = False
    extraction_method = "pymupdf"
    file_type_lower = (file_type or "").lower().strip()

    if file_type_lower in ["pdf", "application/pdf"]:
        try:
            doc = fitz.open(resolved_path)
        except Exception as open_err:
            logger.error(f"Failed to open PDF file with fitz: {open_err}")
            raise CorruptPDFError("Could not extract readable medical text: corrupt or invalid PDF document.", failure_category="CORRUPT_PDF") from open_err

        try:
            page_count = len(doc)
            for page in doc:
                page_text = page.get_text()
                extracted_text += page_text + "\n"

            cleaned = clean_extracted_text(extracted_text)

            # If text is too short (< 15 chars), attempt OCR on each page
            if len(cleaned) < 15:
                ocr_attempted = True
                extraction_method = "tesseract_ocr"
                if not is_tesseract_available():
                    raise OCRUnavailableError(
                        "Scanned PDF contains no embedded text, and Tesseract OCR engine is unavailable on this server.",
                        failure_category="OCR_ENGINE_UNAVAILABLE"
                    )

                ocr_text_accum = ""
                for page in doc:
                    ocr_text_accum += _ocr_page_pixmap(page) + "\n"
                
                extracted_text = ocr_text_accum
        finally:
            doc.close()

    elif file_type_lower in ["image", "jpg", "jpeg", "png", "image/png", "image/jpeg", "image/jpg"]:
        page_count = 1
        ocr_attempted = True
        
        img = None
        try:
            img = Image.open(resolved_path)
            img.verify()  # Verify image integrity
            img = Image.open(resolved_path)  # Re-open for reading after verify
        except Exception as img_err:
            logger.error(f"Failed to decode image file {file_path}: {img_err}")
            raise ImageDecodeError("Unable to read this image file. The file may be corrupt or formatted improperly.", failure_category="IMAGE_DECODE_ERROR") from img_err

        try:
            extracted_text, extraction_method = run_ocr_on_image(img)
        finally:
            if img:
                img.close()
    else:
        raise UnsupportedFileTypeError(f"Unsupported file type: {file_type}", failure_category="FILE_INVALID")

    # Validate extracted text against quality thresholds
    is_img = file_type_lower in ["image", "jpg", "jpeg", "png", "image/png", "image/jpeg", "image/jpg"]
    validate_extracted_text(extracted_text, is_image=is_img)

    cleaned_final = clean_extracted_text(extracted_text)

    diagnostics = {
        "extraction_method": extraction_method,
        "page_count": page_count,
        "char_count": len(cleaned_final),
        "ocr_attempted": ocr_attempted,
        "failure_category": None
    }

    return cleaned_final, diagnostics

def extract_text_from_file(file_path: str, file_type: str) -> str:
    """Wrapper function returning cleaned extracted text directly for backwards compatibility."""
    cleaned_text, _ = extract_text_with_diagnostics(file_path, file_type)
    return cleaned_text
