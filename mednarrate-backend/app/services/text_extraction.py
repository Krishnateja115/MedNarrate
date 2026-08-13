import fitz
import pytesseract
from pdf2image import convert_from_path
import re

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

def extract_text_from_file(file_path: str, file_type: str) -> str:
    """Extracts text using PyMuPDF for PDFs and pytesseract as a fallback or for images."""
    extracted_text = ""
    
    if file_type == "pdf":
        try:
            doc = fitz.open(file_path)
            for i, page in enumerate(doc):
                page_text = page.get_text()
                
                # If extracted char count < 50 for this page, it's likely a scanned image
                if len(page_text.strip()) < 50:
                    images = convert_from_path(file_path, first_page=i+1, last_page=i+1)
                    if images:
                        page_text = pytesseract.image_to_string(images[0])
                        
                extracted_text += page_text + "\n"
        except Exception as e:
            # Fallback for corrupted PDFs or processing errors
            images = convert_from_path(file_path)
            for img in images:
                extracted_text += pytesseract.image_to_string(img) + "\n"
    elif file_type == "image":
        extracted_text = pytesseract.image_to_string(file_path)
        
    return extracted_text
