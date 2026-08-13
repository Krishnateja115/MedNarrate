import requests
import time
import os
import random
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_happy_path(report_file_path, report_title):
    print(f"=== Starting happy path test with: {report_title} ===")
    
    # Generate unique email
    email = f"user_{random.randint(1000, 9999)}@example.com"
    password = "Password123"
    full_name = "Happy Path User"
    
    # 1. Signup
    print("1. Signing up...")
    signup_resp = requests.post(f"{BASE_URL}/auth/signup", json={
        "email": email,
        "password": password,
        "full_name": full_name
    })
    if signup_resp.status_code != 201:
        print(f"Signup failed: {signup_resp.text}")
        return False
    print("Signup successful.")
    
    # 2. Login
    print("2. Logging in...")
    login_resp = requests.post(f"{BASE_URL}/auth/login", data={
        "username": email,
        "password": password
    })
    if login_resp.status_code != 200:
        print(f"Login failed: {login_resp.text}")
        return False
    token_data = login_resp.json()
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Login successful.")
    
    # 3. Update profile
    print("3. Updating profile...")
    profile_resp = requests.patch(f"{BASE_URL}/users/me", headers=headers, json={
        "preferred_language": "hi",
        "gender": "male",
        "date_of_birth": "1990-01-01"
    })
    if profile_resp.status_code != 200:
        print(f"Profile update failed: {profile_resp.text}")
        return False
    print("Profile updated successfully.")
    
    # 4. Upload report
    print("4. Uploading report...")
    if not os.path.exists(report_file_path):
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "Glucose 120 mg/dL (70-99)\nHemoglobin 14.5 g/dL (13.5-17.5)")
        doc.save(report_file_path)
        doc.close()
            
    with open(report_file_path, "rb") as f:
        upload_resp = requests.post(
            f"{BASE_URL}/reports/upload",
            headers=headers,
            data={
                "title": report_title,
                "report_date": "2024-01-01",
                "report_type": "blood"
            },
            files={"file": (os.path.basename(report_file_path), f, "application/pdf")}
        )
    if upload_resp.status_code != 201:
        print(f"Upload failed: {upload_resp.text}")
        return False
    report_data = upload_resp.json()
    report_id = report_data["id"]
    print(f"Report uploaded successfully. ID: {report_id}")
    
    # 5. Process report
    print("5. Triggering report processing...")
    process_resp = requests.post(f"{BASE_URL}/reports/{report_id}/process", headers=headers)
    if process_resp.status_code not in [200, 202]:
        print(f"Process trigger failed: {process_resp.text}")
        return False
    print("Report processing triggered.")
    
    # 6. Poll status
    print("6. Polling report status...")
    status = "uploaded"
    retries = 30
    while status in ["uploaded", "processing"] and retries > 0:
        time.sleep(1)
        status_resp = requests.get(f"{BASE_URL}/reports/{report_id}/status", headers=headers)
        if status_resp.status_code == 200:
            status = status_resp.json()["processing_status"]
            print(f"Current status: {status}")
        else:
            print(f"Status check failed: {status_resp.text}")
        retries -= 1
        
    if status != "completed":
        print(f"Processing failed or timed out with status: {status}")
        # Fetch status detail
        status_resp = requests.get(f"{BASE_URL}/reports/{report_id}/status", headers=headers)
        print(status_resp.json())
        return False
    print("Processing completed successfully.")
    
    # 7. Get analysis
    print("7. Fetching report analysis...")
    analysis_resp = requests.get(f"{BASE_URL}/reports/{report_id}/analysis", headers=headers)
    if analysis_resp.status_code != 200:
        print(f"Fetching analysis failed: {analysis_resp.text}")
        return False
    analysis_data = analysis_resp.json()
    print("Analysis fetched. Summaries generated.")
    
    # 8. Translate analysis
    print("8. Translating analysis...")
    trans_resp = requests.post(f"{BASE_URL}/reports/{report_id}/analysis/translate", headers=headers, json={
        "language": "hi"
    })
    if trans_resp.status_code != 200:
        print(f"Translation failed: {trans_resp.text}")
        return False
    print("Translation generated successfully.")
    
    # 9. Compare previous (should say not comparable or no previous report since this is the first)
    print("9. Checking report comparison...")
    compare_resp = requests.get(f"{BASE_URL}/reports/{report_id}/compare-previous", headers=headers)
    if compare_resp.status_code != 200:
        print(f"Comparison check failed: {compare_resp.text}")
        return False
    print("Comparison check passed.")
    
    # 10. Start chat session
    print("10. Creating chat session...")
    chat_resp = requests.post(f"{BASE_URL}/chat/sessions", headers=headers, json={
        "report_id": report_id,
        "title": "Discussion about report"
    })
    if chat_resp.status_code not in [200, 201]:
        print(f"Chat session creation failed: {chat_resp.text}")
        return False
    session_id = chat_resp.json()["id"]
    print(f"Chat session created. ID: {session_id}")
    
    # 11. Send message
    print("11. Sending chat message...")
    msg_resp = requests.post(f"{BASE_URL}/chat/sessions/{session_id}/messages", headers=headers, json={
        "content": "What is my fasting glucose?"
    })
    if msg_resp.status_code != 200:
        print(f"Sending chat message failed: {msg_resp.text}")
        return False
    print("Chat message sent and reply received.")
    print("Reply:", msg_resp.json()["message"]["content"])
    
    # 12. Logout
    print("12. Logging out...")
    logout_resp = requests.post(f"{BASE_URL}/auth/logout", headers=headers, json={
        "refresh_token": token_data["refresh_token"]
    })
    if logout_resp.status_code != 204:
        print(f"Logout failed: {logout_resp.text}")
        return False
    print("Logout successful.")
    print("=== Happy path test succeeded! ===\n")
    return True

if __name__ == "__main__":
    report_file = "test_happy_path_report.pdf"
    success = True
    for i in range(1, 4):
        title = f"Blood Test Run {i}"
        if not test_happy_path(report_file, title):
            success = False
            break
            
    if success:
        print("All 3 runs completed successfully!")
        sys.exit(0)
    else:
        print("Test run failed.")
        sys.exit(1)
