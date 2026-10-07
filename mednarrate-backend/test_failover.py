import asyncio
from app.services.translation_planner import _execute_with_fallback
from app.exceptions import TranslationServiceError
import json

async def run_test():
    call_counts = {"gemini": 0, "openai": 0, "mistral": 0, "local": 0}
    
    async def mock_generate(prompt, provider):
        call_counts[provider] += 1
        if provider == "gemini":
            raise Exception("Gemini API error")
        elif provider == "openai":
            raise Exception("OpenAI API error")
        elif provider == "mistral":
            raise Exception("Mistral 403 Forbidden")
        elif provider == "local":
            # Must return valid JSON according to parse_translation schema
            return {"provider": "local", "content": json.dumps({
                "clinician_summary": "local text",
                "patient_summary": "local text",
                "abnormal_findings": [],
                "medications": [],
                "translated_parameters": {},
                "doctor_discussion_points": [],
                "ui_labels": {}
            })}
            
    def mock_validate(parsed, lang, clin, pat, abn, meds, req):
        pass # pass validation
        
    providers = ["gemini", "openai", "mistral", "local"]
    chunk_data = {"clinician_summary": "test", "patient_summary": "test", "abnormal_findings": [], "medications": []}
    
    try:
        res = await _execute_with_fallback("prompt", providers, mock_validate, "hi", chunk_data, set(), "req123", mock_generate)
        print("Success! Result:", res.get("clinician_summary"))
    except Exception as e:
        print("Failed:", type(e).__name__, e)
        
    print("Call counts:", call_counts)

if __name__ == "__main__":
    asyncio.run(run_test())
