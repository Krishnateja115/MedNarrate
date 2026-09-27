import asyncio
from app.services.llm_client import llm_client_instance

async def run_test():
    prompt = "Translate this text: hello"
    provider = llm_client_instance.get_provider("dev_gemini")
    print(f"Testing provider: {provider}")
    try:
        res = await provider.generate(prompt)
        print("SUCCESS:", res)
    except Exception as e:
        print("ERROR:")
        import traceback
        traceback.print_exc()

asyncio.run(run_test())
