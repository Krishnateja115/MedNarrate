import asyncio
import json
from app.services.llm_client import llm_client_instance
from app.services.prompts import TRANSLATION_PROMPT

async def run_test():
    prompt = TRANSLATION_PROMPT.format(
        target_language="Telugu",
        patient_summary="The patient is healthy.",
        abnormal_findings_json="[]",
        medications_json="[]",
    )
    provider = llm_client_instance.get_provider("dev_gemini")
    print(f"Testing provider: {provider}")
    try:
        res = await provider.generate(prompt)
        print("SUCCESS LEN:", len(res.get('content', '')))
        
        with open("test_out.json", "w", encoding="utf-8") as f:
            f.write(res.get('content', ''))
            
    except Exception as e:
        print("ERROR:")
        import traceback
        traceback.print_exc()

asyncio.run(run_test())
