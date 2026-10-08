import asyncio
from app.services.lab_value_extractor import extract_lab_values

text = """DELHI
110085
SWASTHFIT SUPER
4
U/L
40 ALT
U/L
50 GGTP"""

results = extract_lab_values(text)
for r in results:
    print(r)
