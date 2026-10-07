import asyncio
from unittest.mock import AsyncMock, patch
from app.services.translation_planner import execute_translation_plan
from app.services import llm_client
from app.services.translation_validation import validate_translation
import json

async def test_failover():
    print('Starting failover test...')
    def mock_err(msg, code):
        e = llm_client.LLMConnectionError(msg)
        e.status_code = code
        return e
    
    gemini_mock = AsyncMock(side_effect=mock_err('gemini fail', 503))
    openai_mock = AsyncMock(side_effect=mock_err('openai fail', 500))
    mistral_mock = AsyncMock(side_effect=mock_err('mistral fail', 403))
    
    valid_json = {
        "findings": [],
        "medications": [],
        "patient_summary": "Hindi summary",
        "clinician_summary": "Hindi clinician summary",
        "doctor_discussion_points": [],
        "ui_labels": {}
    }
    local_mock = AsyncMock(return_value={'content': json.dumps(valid_json), 'provider': 'local', 'model': 'Qwen'})
    
    llm_client._translation_request.set(True)
    
    with patch.object(llm_client.DevGeminiProvider, 'generate', gemini_mock), \
         patch.object(llm_client.OpenAIProvider, 'generate', openai_mock), \
         patch.object(llm_client.MistralProvider, 'generate', mistral_mock), \
         patch.object(llm_client.LocalProvider, 'generate', local_mock):
         
        try:
            # Call the planner directly
            res = await execute_translation_plan(
                text="Test report",
                target_language="hi",
                original_findings=[],
                original_meds=[],
                original_entities=[]
            )
            print("Translation returned:", res is not None)
            print(f"Gemini call count: {gemini_mock.call_count}")
            print(f"OpenAI call count: {openai_mock.call_count}")
            print(f"Mistral call count: {mistral_mock.call_count}")
            print(f"Local call count: {local_mock.call_count}")
            
        except Exception as e:
            print("Error:", repr(e))

asyncio.run(test_failover())
