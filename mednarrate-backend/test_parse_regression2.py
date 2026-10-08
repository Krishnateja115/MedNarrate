import asyncio
from app.services.lab_value_extractor import extract_lab_values

async def run_test():
    text = """
DELHI
110085
SWASTHFIT SUPER
4
U/L
40 ALT
U/L
50 GGTP
    """
    results = await extract_lab_values(text)
    print("Parsed Results:", results)

if __name__ == "__main__":
    asyncio.run(run_test())
