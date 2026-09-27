import requests, time, sys

# Login
login_resp = requests.post('http://127.0.0.1:8000/api/v1/auth/login', 
    data={'username': 'test@mednarrate.com', 'password': 'password123'})
assert login_resp.status_code == 200
token = login_resp.json()['access_token']
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

# Delete cached Hindi and try again with retry
import sqlite3
conn = sqlite3.connect('mednarrate.db')
c = conn.cursor()
c.execute("DELETE FROM analysis_translations WHERE language IN ('hi', 'ta', 'te')")
conn.commit()
conn.close()

for lang in [('te', 'Telugu'), ('hi', 'Hindi'), ('ta', 'Tamil')]:
    sys.stdout.buffer.write(f"\nTesting {lang[1]} ({lang[0]})...\n".encode())
    resp = requests.post('http://127.0.0.1:8000/api/v1/reports/159351a2adc546cdb7facda28a7810a8/analysis/translate',
        headers=headers, json={'language': lang[0]})
    sys.stdout.buffer.write(f"STATUS: {resp.status_code}\n".encode())
    if resp.status_code == 200:
        data = resp.json()
        sys.stdout.buffer.write(f"SUMMARY FIRST 80: ".encode())
        sys.stdout.buffer.write(data.get('patient_summary','')[:80].encode('utf-8'))
        sys.stdout.buffer.write(b"\n")
    else:
        sys.stdout.buffer.write(f"ERROR: {resp.text[:200]}\n".encode())
    time.sleep(2)  # Rate limit avoidance

sys.stdout.buffer.write(b"\nDone.\n")
