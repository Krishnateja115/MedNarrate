import httpx
from app.core.config import settings
import json

api_key = settings.GROQ_API_KEY
resp = httpx.get("https://api.groq.com/openai/v1/models", headers={"Authorization": f"Bearer {api_key}"})
models = resp.json().get("data", [])
for m in models:
    print(m.get("id"))
