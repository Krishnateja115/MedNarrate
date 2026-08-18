import pytest
from httpx import AsyncClient
import io
import os
from app.core.config import settings

@pytest.fixture
async def auth_headers(client: AsyncClient):
    # Register and login a user for reports testing
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "reports@example.com", "password": "StrongP@ssword1", "full_name": "Reports User"}
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "reports@example.com", "password": "StrongP@ssword1"}
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
async def other_auth_headers(client: AsyncClient):
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "other@example.com", "password": "StrongP@ssword1", "full_name": "Other User"}
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "other@example.com", "password": "StrongP@ssword1"}
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

async def test_upload_success(client: AsyncClient, auth_headers):
    file_content = b"%PDF-1.4 dummy pdf content"
    files = {"file": ("test.pdf", file_content, "application/pdf")}
    data = {
        "title": "My Blood Test",
        "report_date": "2024-01-01",
        "report_type": "blood"
    }
    
    resp = await client.post("/api/v1/reports/upload", headers=auth_headers, files=files, data=data)
    print("UPLOAD RESPONSE:", resp.text)
    assert resp.status_code == 201
    resp_data = resp.json()
    assert resp_data["title"] == "My Blood Test"
    assert resp_data["file_type"] == "pdf"
    assert resp_data["processing_status"] == "uploaded"

async def test_upload_wrong_filetype(client: AsyncClient, auth_headers):
    file_content = b"dummy text content"
    files = {"file": ("test.txt", file_content, "text/plain")}
    data = {
        "title": "Text Report",
        "report_date": "2024-01-01",
        "report_type": "other"
    }
    
    resp = await client.post("/api/v1/reports/upload", headers=auth_headers, files=files, data=data)
    assert resp.status_code == 422

async def test_upload_oversized_file(client: AsyncClient, auth_headers):
    # Dummy oversized file
    file_content = b"0" * (settings.MAX_UPLOAD_MB * 1024 * 1024 + 1024)
    files = {"file": ("large.pdf", file_content, "application/pdf")}
    data = {
        "title": "Large Report",
        "report_date": "2024-01-01",
        "report_type": "other"
    }
    
    resp = await client.post("/api/v1/reports/upload", headers=auth_headers, files=files, data=data)
    assert resp.status_code == 422

async def test_list_reports(client: AsyncClient, auth_headers):
    resp = await client.get("/api/v1/reports", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) > 0

async def test_patch_report_favourite(client: AsyncClient, auth_headers):
    list_resp = await client.get("/api/v1/reports", headers=auth_headers)
    report_id = list_resp.json()[0]["id"]
    
    patch_resp = await client.patch(f"/api/v1/reports/{report_id}", headers=auth_headers, json={"is_favourite": True})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["is_favourite"] == True

async def test_other_user_cannot_access(client: AsyncClient, auth_headers, other_auth_headers):
    list_resp = await client.get("/api/v1/reports", headers=auth_headers)
    report_id = list_resp.json()[0]["id"]
    
    get_resp = await client.get(f"/api/v1/reports/{report_id}", headers=other_auth_headers)
    assert get_resp.status_code == 403
    
    patch_resp = await client.patch(f"/api/v1/reports/{report_id}", headers=other_auth_headers, json={"title": "Hacked"})
    assert patch_resp.status_code == 403
    
    del_resp = await client.delete(f"/api/v1/reports/{report_id}", headers=other_auth_headers)
    assert del_resp.status_code == 403

async def test_delete_removes_file(client: AsyncClient, auth_headers):
    list_resp = await client.get("/api/v1/reports", headers=auth_headers)
    report = list_resp.json()[0]
    report_id = report["id"]
    file_path = report["file_path"]
    
    # file_path is something like "/uploads/...", we check relative to cwd
    local_path = file_path.lstrip("/")
    assert os.path.exists(local_path)
    
    del_resp = await client.delete(f"/api/v1/reports/{report_id}", headers=auth_headers)
    assert del_resp.status_code == 204
    
    assert not os.path.exists(local_path)

async def test_export_csv(client: AsyncClient, auth_headers):
    file_content = b"%PDF-1.4 dummy pdf content"
    files = {"file": ("test.pdf", file_content, "application/pdf")}
    data = {
        "title": "Export Test",
        "report_date": "2024-01-01",
        "report_type": "blood"
    }
    
    resp = await client.post("/api/v1/reports/upload", headers=auth_headers, files=files, data=data)
    report_id = resp.json()["id"]
    
    export_resp = await client.get(f"/api/v1/reports/{report_id}/export/csv", headers=auth_headers)
    assert export_resp.status_code == 404
    assert export_resp.json()["detail"] == "No structured lab data available for this report"
