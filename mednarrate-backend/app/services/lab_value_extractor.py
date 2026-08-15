import re

LAB_LINE_RE = re.compile(
    r"^\s*(?P<name>[A-Za-z][A-Za-z0-9 /\-\(\)]{2,40}?)"
    r"(?:\s+[:\-]?\s*|[:\-]\s*)"
    r"(?P<value>-?\d+\.?\d*)\s*"
    r"(?P<unit>.*?)\s*"
    r"(?:\(?\s*(?:ref|reference|normal)?[:\s]*"
    r"(?P<low>\d+\.?\d*)\s*[-–~to]+\s*(?P<high>\d+\.?\d*)\s*\)?)?\s*$",
    re.IGNORECASE | re.MULTILINE
)

from app.services.normalization import normalize_lab_value

def extract_lab_values(text: str) -> list[dict]:
    results = []
    for m in LAB_LINE_RE.finditer(text):
        name = m.group("name").strip()
        try:
            value = float(m.group("value"))
        except (TypeError, ValueError):
            continue
        low = float(m.group("low")) if m.group("low") else None
        high = float(m.group("high")) if m.group("high") else None
        flag = "normal"
        if low is not None and value < low:
            flag = "low"
        elif high is not None and value > high:
            flag = "high"
        raw_dict = {
            "test_name": name, "value": value, "unit": m.group("unit") or "",
            "ref_low": low, "ref_high": high, "flag": flag,
        }
        results.append(normalize_lab_value(raw_dict))
    return results

import json
from pydantic import BaseModel, ValidationError
from typing import Optional, List
from app.services.llm_client import generate

class MedicationScheduleModel(BaseModel):
    medication_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    times_of_day: List[str] = []
    duration_days: Optional[int] = None
    notes: Optional[str] = None

async def extract_medication_schedule(report_text: str) -> list[MedicationScheduleModel]:
    prompt = f"""From the following medical report text, extract all prescribed 
medications. For each medication, extract: name, dosage, 
frequency, estimated times of day (convert frequency to 
specific times: twice daily -> 08:00 and 20:00, 
three times daily -> 08:00, 14:00, 20:00, 
once daily -> 08:00), duration_days (as integer) if mentioned, and any special 
notes (take with food, avoid sunlight, etc.).
Return ONLY a valid JSON array. If no medications found, 
return [].
Report text: {report_text}"""

    try:
        response = await generate(prompt)
        # Strip potential markdown formatting like ```json ... ```
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        data = json.loads(response)
        
        schedules = []
        for item in data:
            try:
                # rename duration if present
                if "duration" in item and "duration_days" not in item:
                    item["duration_days"] = item["duration"]
                schedules.append(MedicationScheduleModel(**item))
            except ValidationError:
                continue
                
        return schedules
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to extract medications: {e}")
        return []
