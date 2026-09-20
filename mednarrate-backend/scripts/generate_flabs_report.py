import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "tests", "data")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def generate_flabs_cbc(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    c = canvas.Canvas(path, pagesize=letter)
    c.setFont("Helvetica", 12)
    y = 750

    # Write each string as its own text element, simulating separate table cells
    # This ensures PyMuPDF extracts them on separate lines
    def write_line(text):
        nonlocal y
        c.drawString(50, y, text)
        y -= 20
        if y < 50:
            c.showPage()
            c.setFont("Helvetica", 12)
            y = 750

    write_line("Patient ID: PN2")
    write_line("Report ID: RE1")
    write_line("Collection Date: 2023/06/20")
    write_line("MD Pathology")
    write_line("Report Date: 2023/06/21")
    
    cbc_data = [
        ("Haemoglobin", "15", "13 - 17", "g/dL"),
        ("Total Leucocyte Count", "5000", "4000 - 10000", "/cumm"),
        ("Neutrophils", "60", "40 - 80", "%"),
        ("Lymphocytes", "30", "20 - 40", "%"),
        ("Eosinophils", "2", "1 - 6", "%"),
        ("Monocytes", "6", "2 - 10", "%"),
        ("Basophils", "0.5", "0 - 2", "%"),
        ("RBC Count", "5.0", "4.5 - 5.5", "mill/mm3"),
        ("MCV", "80.00", "83 - 101", "fl"), # LOW
        ("MCH", "28", "27 - 32", "pg"),
        ("MCHC", "37.50", "31.5 - 34.5", "g/dL"), # HIGH
        ("Hct", "42", "39 - 50", "%"),
        ("RDW-CV", "13", "11 - 16", "%"),
        ("RDW-SD", "40", "39 - 46", "fl"),
        ("Platelet Count", "300000", "150000 - 450000", "/cumm"),
        ("Platelets", "300", "150 - 450", "x10^3/uL"),
        ("MPV", "9.5", "8.0 - 12.0", "fL"),
        ("PCT", "0.25", "0.15 - 0.50", "%")
    ]

    for row in cbc_data:
        for cell in row:
            write_line(cell)

    c.save()
    return path

if __name__ == "__main__":
    generate_flabs_cbc("report3.pdf")
    print("Generated report3.pdf")
