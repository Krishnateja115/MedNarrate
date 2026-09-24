import asyncio
from PIL import Image
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.services.text_extraction import run_ocr_on_image

img = Image.new("RGB", (800, 800), color="white")
# Draw some text
from PIL import ImageDraw
d = ImageDraw.Draw(img)
d.text((10,10), "This is a medical report.\nBlood Test: 120 mg/dL", fill=(0,0,0))

try:
    text, engine = run_ocr_on_image(img)
    print("SUCCESS")
    print(text)
except Exception as e:
    print(f"FAILED: {type(e).__name__} - {e}")

