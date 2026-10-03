import json

with open("llm_crash.txt", "r", encoding="utf-8") as f:
    text = f.read()

import re
fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
if fence:
    text = fence.group(1)
else:
    match = re.search(r"(\{[\s\S]*\})", text)
    if match:
        text = match.group(1)

try:
    parsed, _ = json.JSONDecoder().raw_decode(text.strip())
    print("Parsed OK")
    findings = parsed.get("abnormal_findings", [])
    print("Length of findings:", len(findings))
    for f in findings:
        print("  Test:", f.get("test_name"))
except Exception as e:
    print("Error:", e)
