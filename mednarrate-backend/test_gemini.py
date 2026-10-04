import asyncio
import os
import sys

sys.path.append(os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from app.services.llm_client import generate_translation

async def main():
    try:
        res = await generate_translation("Translate to Hindi: hello world")
        print(f"Result: {res}")
    except Exception as e:
        print(f"Exception: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
