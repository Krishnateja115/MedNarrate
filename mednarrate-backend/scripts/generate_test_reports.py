import os
import random
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "tests", "data")

def ensure_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def generate_native_pdf(filename, content_lines):
    path = os.path.join(OUTPUT_DIR, filename)
    c = canvas.Canvas(path, pagesize=letter)
    c.setFont("Helvetica", 12)
    y = 750
    for line in content_lines:
        c.drawString(50, y, line)
        y -= 20
        if y < 50:
            c.showPage()
            c.setFont("Helvetica", 12)
            y = 750
    c.save()
    return path

from pdf2image import convert_from_path

def generate_image_report(filename, content_lines):
    temp_pdf = generate_native_pdf("temp_for_image.pdf", content_lines)
    images = convert_from_path(temp_pdf)
    path = os.path.join(OUTPUT_DIR, filename)
    images[0].save(path)
    os.remove(temp_pdf)
    return path

def generate_mixed_pdf(filename, text_lines, image_lines):
    path = os.path.join(OUTPUT_DIR, filename)
    c = canvas.Canvas(path, pagesize=letter)
    c.setFont("Helvetica", 12)
    
    # Page 1: Native Text
    y = 750
    for line in text_lines:
        c.drawString(50, y, line)
        y -= 20
        
    c.showPage()
    
    # Page 2: Image (scanned)
    img_path = generate_image_report("temp_page2.png", image_lines)
    c.drawImage(img_path, 0, 0, width=letter[0], height=letter[1])
    c.save()
    
    os.remove(img_path)
    return path

def main():
    ensure_dir()
    print("Generating synthetic test reports...")
    
    # 1. Clean Blood Test (Native PDF)
    generate_native_pdf("01_blood_clean.pdf", [
        "Patient: John Doe",
        "Report Type: Complete Blood Count",
        "Hemoglobin 14.2 g/dL 13.0 - 17.0",
        "WBC Count 5.5 x 10^3 / uL 4.0 to 11.0",
        "Platelets 300 10*9/L 150-450",
    ])
    
    # 2. Noisy Pathology (Native PDF)
    generate_native_pdf("02_pathology_noisy.pdf", [
        "Surgical Pathology Report",
        "Glucose (Fasting) : 105 mg/dl 70-99",
        "TSH  :  4.5   µIU/mL 0.4 - 4.0",
        "Random Noise line || _",
    ])
    
    # 3. Image Report (PNG)
    generate_image_report("03_health_scanned.png", [
        "General Health Panel",
        "RBC 4.8 mil/mm3 4.2-5.4",
        "Cholesterol 210 mg/dL 125 - 200",
    ])
    
    # 4. Mixed PDF (Text + Scanned)
    generate_mixed_pdf("04_mixed_report.pdf", [
        "Page 1 - Patient Info",
        "Name: Jane Doe",
        "Age: 35"
    ], [
        "Page 2 - Lab Results",
        "Creatinine 0.9 mg/dL 0.6 - 1.1",
        "Uric Acid 5.2 mg/dL 2.4 - 6.0"
    ])
    
    print(f"Generated 4 distinct test files in {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
