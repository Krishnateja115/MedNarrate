import os
import requests

api_key = os.environ.get('GROQ_API_KEY')
if not api_key:
    from app.core.config import settings
    api_key = settings.GROQ_API_KEY

headers = {
    "Authorization": f"Bearer {api_key}"
}
response = requests.get("https://api.groq.com/openai/v1/models", headers=headers)
print("Status:", response.status_code)
if response.status_code == 200:
    for m in response.json()['data']:
        print(f"- {m['id']} (context: {m.get('context_window', 'unknown')})")
else:
    print(response.text)
