import asyncio, json
from app.services.llm_client import llm_client_instance, _translation_request

async def test():
    _translation_request.set(True)
    provider = llm_client_instance.get_provider('local')
    res = await provider.generate('{"text": "The patient has a mild fever."}\nReturn JSON with a "translation" key.')
    print("RAW CONTENT:", repr(res['content']))

if __name__ == "__main__":
    asyncio.run(test())
