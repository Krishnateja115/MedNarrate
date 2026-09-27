import asyncio
from app.services.llm_orchestrator import translate_text_indic, generate_primary_reasoning
from app.services.llm_client import generate, generate_with_metadata

async def main():
    print("Testing generate_with_metadata (Gemini/Fallback):")
    res = await generate_with_metadata("Translate 'Hello World' into Telugu")
    print(res)
    
    print("\nTesting translate_text_indic (IndicTrans2):")
    res2 = await translate_text_indic("Hello World", "te")
    print(res2)

asyncio.run(main())
