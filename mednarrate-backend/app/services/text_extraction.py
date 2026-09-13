import fitz
import pytesseract
from PIL import Image
import io
import re
import logging

logger = logging.getLogger(__name__)

def clean_extracted_text(text: str) -> str:
    """Cleans extracted OCR or PDF text to prepare it for NER and lab extraction."""
    # Remove random OCR artifacts like standalone pipes or underscores
    text = re.sub(r'(?<!\S)[|_](?!\S)', ' ', text)
    # Fix broken lines that have hyphens at the end
    text = re.sub(r'-\n+', '', text)
    # Replace multiple spaces with a single space (while keeping newlines intact)
    text = re.sub(r'[ \t]+', ' ', text)
    # Replace multiple newlines with a double newline to preserve paragraph structure
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def _ocr_page_pixmap(page: fitz.Page) -> str:
    """Render a PyMuPDF page to an image and attempt OCR via pytesseract."""
    try:
        pix = page.get_pixmap(dpi=150)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        return pytesseract.image_to_string(img)
    except Exception as e:
        logger.warning(f"OCR failed for PDF page: {e}")
        return ""

def extract_text_from_file(file_path: str, file_type: str) -> str:
    """Extracts text using PyMuPDF for PDFs and pytesseract as a fallback or for images."""
    extracted_text = ""
    
    if file_type == "pdf":
        try:
            doc = fitz.open(file_path)
            for page in doc:
                page_text = page.get_text()
                
                # If extracted char count < 50 for this page, attempt OCR
                if len(page_text.strip()) < 50:
                    ocr_text = _ocr_page_pixmap(page)
                    if ocr_text.strip():
                        page_text = ocr_text
                        
                extracted_text += page_text + "\n"
        except Exception as e:
            logger.error(f"Failed to extract text from PDF using PyMuPDF: {e}")
            try:
                doc = fitz.open(file_path)
                for page in doc:
                    extracted_text += _ocr_page_pixmap(page) + "\n"
            except Exception as e2:
                logger.error(f"Failed PDF fallback: {e2}")
    elif file_type == "image":
        try:
            extracted_text = pytesseract.image_to_string(file_path)
        except Exception as e:
            logger.warning(f"OCR failed for image: {e}")
            
    cleaned = clean_extracted_text(extracted_text)
    if len(cleaned) < 15:
        raise ValueError("Could not extract readable medical text from this document.")
        
    return cleaned


