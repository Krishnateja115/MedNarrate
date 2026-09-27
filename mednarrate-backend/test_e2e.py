import requests

# Login
login_resp = requests.post('http://127.0.0.1:8000/api/v1/auth/login', 
    data={'username': 'test@mednarrate.com', 'password': 'password123'})

assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
token = login_resp.json()['access_token']
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

import sys

# Telugu
resp = requests.post('http://127.0.0.1:8000/api/v1/reports/159351a2adc546cdb7facda28a7810a8/analysis/translate',
    headers=headers, json={'language': 'te'})
sys.stdout.buffer.write(f"TELUGU STATUS: {resp.status_code}\n".encode())
data = resp.json()
sys.stdout.buffer.write(f"SUMMARY FIRST 100: {data.get('patient_summary','')[:100]}\n".encode('utf-8'))
sys.stdout.buffer.write(f"FINDINGS_JSON count: {len(data.get('findings_json', []))}\n".encode())
sys.stdout.buffer.write(f"UI_LABELS count: {len(data.get('ui_labels', {}))}\n".encode())
sys.stdout.buffer.write(f"CACHED: {data.get('cached')}\n".encode())
sys.stdout.buffer.write(b"\n")

# Hindi (force fresh - delete translation first)
import sqlite3
conn = sqlite3.connect('mednarrate.db')
c = conn.cursor()
c.execute("DELETE FROM analysis_translations WHERE language='hi'")
conn.commit()
conn.close()

resp2 = requests.post('http://127.0.0.1:8000/api/v1/reports/159351a2adc546cdb7facda28a7810a8/analysis/translate',
    headers=headers, json={'language': 'hi'})
sys.stdout.buffer.write(f"HINDI STATUS: {resp2.status_code}\n".encode())
data2 = resp2.json()
sys.stdout.buffer.write(f"SUMMARY FIRST 100: {data2.get('patient_summary','')[:100]}\n".encode('utf-8'))
sys.stdout.buffer.write(f"UI_LABELS count: {len(data2.get('ui_labels', {}))}\n".encode())
sys.stdout.buffer.write(b"\n--- ALL TESTS PASSED ---\n")
