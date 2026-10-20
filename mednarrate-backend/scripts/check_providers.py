"""Try every free AI provider that has a key and print which ones work.

Run from the mednarrate-backend folder:  python scripts/check_providers.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services import llm_client

# OpenAI is deliberately left out (paid). Vertex AI and the offline Qwen model are not tested here.
TESTS = [
    ("gemini", llm_client.DevGeminiProvider()),
    ("groq", llm_client.OpenAICompatibleProvider("groq")),
    ("groq_qwen", llm_client.OpenAICompatibleProvider("groq_qwen")),
    ("cerebras", llm_client.OpenAICompatibleProvider("cerebras")),
    ("github", llm_client.OpenAICompatibleProvider("github")),
    ("openrouter", llm_client.OpenAICompatibleProvider("openrouter")),
    ("mistral", llm_client.MistralProvider()),
    ("anthropic", llm_client.AnthropicProvider()),
    ("ollama", llm_client.OllamaProvider()),
]


async def check(name, provider):
    # Gemini and Ollama report their own problems when called; the others need a key first.
    needs_key = name not in ("ollama", "gemini")
    try:
        key = provider.get_api_key()
    except Exception:
        key = None
    if needs_key and not (key and str(key).strip()):
        print(f"{name:11} NO KEY SET")
        return
    try:
        r = await provider.generate("Reply with the single word OK", timeout=40)
        print(f"{name:11} WORKS   {r['model']} | {r['latency_ms']} ms | {r['content'][:30]!r}")
    except Exception as e:
        detail = getattr(e, "error_detail", None) or str(e)
        print(f"{name:11} FAILED  status {getattr(e, 'status_code', '?')} | {type(e).__name__} | {str(detail)[:200]}")


async def main():
    for name, provider in TESTS:
        await check(name, provider)


asyncio.run(main())
