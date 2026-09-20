import json

prompt = """
Extracted report text:
Some text

Structured lab values:
[{"test": 1}]

Clinical Knowledge Reference (RAG Context):
None
"""

json_part = prompt.split("Structured lab values:")[1].split("Clinical Knowledge")[0].split("Extracted report text")[0].strip()
print("JSON part:", repr(json_part))
try:
    labs = json.loads(json_part)
    print("Success:", len(labs))
except Exception as e:
    print("Error:", e)
