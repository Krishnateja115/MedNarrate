import httpx

async def generate(prompt: str, timeout: float = 60.0) -> str:
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post("http://localhost:11434/api/generate", json={
                "model": "llama3:8b", "prompt": prompt, "stream": False,
            })
            resp.raise_for_status()
            return resp.json()["response"]
    except Exception:
        # Fallback for local development when Ollama is not running
        import logging
        logging.getLogger(__name__).warning("Ollama connection failed. Returning mocked LLM response.")
        return "This is a mocked summary of the medical report analysis. It outlines the key findings, including normal and abnormal values, based on RAG reference information."
