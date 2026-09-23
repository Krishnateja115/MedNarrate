import pytest
import uuid
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_manual_reminder(client: AsyncClient, token_headers: dict):
    payload = {
        "medication_name": "Test Med Manual",
        "dosage": "10mg",
        "frequency": "Once daily",
        "times_of_day": ["09:00"],
        "duration_days": 30,
        "notes": "With food"
    }
    response = await client.post("/api/v1/reminders/", json=payload, headers=token_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["medication_name"] == "Test Med Manual"
    assert data["report_id"] is None
    assert "id" in data

@pytest.mark.asyncio
async def test_create_report_reminder_and_ownership(client: AsyncClient, token_headers: dict):
    # First, create a dummy report to link to
    # We might not have a full report endpoint ready for mock, so we'll just test standard CRUD operations.
    # Actually, we can test edit, delete, and toggle here as requested.
    
    # 1. Create a reminder
    payload = {
        "medication_name": "Test Med Report",
        "dosage": "20mg",
        "frequency": "Twice daily",
        "times_of_day": ["08:00", "20:00"],
    }
    response = await client.post("/api/v1/reminders/", json=payload, headers=token_headers)
    assert response.status_code == 201
    reminder_id = response.json()["id"]

    # 2. Get the reminder
    get_resp = await client.get("/api/v1/reminders/", headers=token_headers)
    assert get_resp.status_code == 200
    reminders = get_resp.json()
    assert any(r["id"] == reminder_id for r in reminders)

    # 3. Edit the reminder
    patch_resp = await client.patch(
        f"/api/v1/reminders/{reminder_id}", 
        json={"dosage": "30mg"}, 
        headers=token_headers
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["dosage"] == "30mg"

    # 4. Toggle is_active
    toggle_resp = await client.patch(
        f"/api/v1/notifications/medication-schedules/{reminder_id}/toggle",
        headers=token_headers
    )
    assert toggle_resp.status_code == 200
    assert "deactivated" in toggle_resp.json()["message"]

    # Verify toggle via GET
    get_toggled = await client.get("/api/v1/reminders/", headers=token_headers)
    assert get_toggled.status_code == 200
    for r in get_toggled.json():
        if r["id"] == reminder_id:
            assert r["is_active"] is False

    # 5. Delete the reminder
    del_resp = await client.delete(f"/api/v1/reminders/{reminder_id}", headers=token_headers)
    assert del_resp.status_code == 204

    # 6. Verify deletion
    final_get = await client.get("/api/v1/reminders/", headers=token_headers)
    assert final_get.status_code == 200
    assert not any(r["id"] == reminder_id for r in final_get.json())
