from PIL import Image, ImageDraw, ImageFont
import numpy as np
import easyocr
import traceback
try:
    # create a dummy image with some text
    img = Image.new('RGB', (200, 100), color = (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((10,10), "Hemoglobin 13.5 g/dL", fill=(0,0,0))
    img_np = np.array(img)
    
    reader = easyocr.Reader(['en'], gpu=False)
    results = reader.readtext(img_np, detail=0)
    print("Results:", results)
except Exception as e:
    print("Exception:")
    traceback.print_exc()
