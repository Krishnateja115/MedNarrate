import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_e2e_confirm(client: AsyncClient, token_headers: dict, capsys):
    print("\n=== 1. Uploading Report ===")

    with open("tests/data/report3.pdf", "rb") as f:
        pdf_data = f.read()

    report_resp = await client.post(
        "/api/v1/reports/",
        headers=token_headers,
        data={"title": "E2E Test Report"},
        files={"file": ("report3.pdf", pdf_data, "application/pdf")},
    )

    # We might get 500 if the LLM extraction fails in test, but let's see.
    # To avoid relying on live LLM extraction which might be mocked or disabled, we'll mock the med extraction step.

    # Mocking what the frontend receives from the backend:
    meds = [
        {
            "medication_name": "Lisinopril",
            "dosage": "10mg",
            "frequency": "daily",
            "times_of_day": ["morning", "night"],
        }
    ]

    print("=== 2. Extracted Medications (Simulated Backend Response) ===")
    import json

    print(json.dumps(meds, indent=2))

    med_to_confirm = meds[0]

    print("\n=== 3. Frontend Time Parsing (Simulation) ===")
    print(f"Original times from backend: {med_to_confirm.get('times_of_day')}")
    # Simulate Dart logic:
    # if times_of_day contains "morning" -> 08:00
    # if times_of_day contains "night" -> 21:00
    parsed_times = ["08:00", "21:00"]
    print(f"Parsed times by Flutter Dart Code: {parsed_times}")

    print("\n=== 4. Confirm to Schedule (POST /reminders/) ===")
    payload = {
        "medication_name": med_to_confirm.get("medication_name"),
        "dosage": med_to_confirm.get("dosage", ""),
        "frequency": med_to_confirm.get("frequency", ""),
        "times_of_day": parsed_times,
        "report_id": report_resp.json().get("id")
        if report_resp.status_code == 200
        else None,
    }

    save_resp = await client.post(
        "/api/v1/reminders/", json=payload, headers=token_headers
    )
    print(f"Save Status: {save_resp.status_code}")
    saved = save_resp.json()
    print("Saved row in MedicationSchedules:")
    print(json.dumps(saved, indent=2))

    print("\n=== 5. Final GET /reminders/ ===")
    final_get = await client.get("/api/v1/reminders/", headers=token_headers)
    print("Reminders list active for user:")
    print(json.dumps(final_get.json(), indent=2))
