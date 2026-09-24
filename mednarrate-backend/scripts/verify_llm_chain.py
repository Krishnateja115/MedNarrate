"""
FIX 3 Verification Script — verify the LLM provider chain degrades correctly.
Run from mednarrate-backend/: python3 scripts/verify_llm_chain.py
"""

import asyncio

from app.services.llm_client import generate, llm_client_instance


async def main():
    print("=== LLM Provider Health Check ===")
    for name, provider in llm_client_instance.providers.items():
        health = await provider.health_check()
        print(
            f"[{name}] configured={health['configured']} authenticated={health['authenticated']} reachable={health['reachable']}"
        )

    print("\n=== Testing generate() ===")
    result = await generate("Summarize: Hemoglobin 15 g/dL (ref 13-17), normal.")
    print("\n--- GENERATE OUTPUT ---")
    print(result)
    assert result and len(result.strip()) > 0, "generate() returned empty content"
    print("\nPASS: generate() returned non-empty content without raising.")


asyncio.run(main())
