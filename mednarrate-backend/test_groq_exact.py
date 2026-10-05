import os
import requests

api_key = os.environ.get('GROQ_API_KEY')
if not api_key:
    from app.core.config import settings
    api_key = settings.GROQ_API_KEY

payload = {
    "model": "openai/gpt-oss-120b",
    "messages": [
        {"role": "user", "content": "Hello, how are you? " * 3000}
    ],
    "temperature": 0.2,
    "max_tokens": 1000
}
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
print("Status:", response.status_code)
print("Response:", response.text)
