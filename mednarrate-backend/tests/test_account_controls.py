"""Account export/deletion and user-owned support checks."""

import io
import json
import zipfile

from httpx import AsyncClient

from tests.pdf_fixtures import VALID_PDF
from app.services.storage import get_storage_backend


async def _signup(client: AsyncClient, email: str) -> dict[str, str]:
    created = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "StrongP@ssword1",
            "full_name": "Account Test",
        },
    )
    assert created.status_code in (200, 201)
    login = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "StrongP@ssword1"},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def test_export_contains_only_own_report_and_no_credentials(
    client: AsyncClient,
) -> None:
    owner = await _signup(client, "export_owner@example.com")
    other = await _signup(client, "export_other@example.com")
    fields = {"title": "Blood Test", "report_date": "2024-01-01", "report_type": "blood"}
    own_upload = await client.post(
        "/api/v1/reports/upload",
        headers=owner,
        files={"file": ("own.pdf", VALID_PDF, "application/pdf")},
        data=fields,
    )
    other_upload = await client.post(
        "/api/v1/reports/upload",
        headers=other,
        files={"file": ("other.pdf", VALID_PDF, "application/pdf")},
        data=fields,
    )
    assert own_upload.status_code == 201
    assert other_upload.status_code == 201

    response = await client.get("/api/v1/users/me/export", headers=owner)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        names = archive.namelist()
        assert any(name.endswith("/own.pdf") for name in names)
        assert not any(name.endswith("/other.pdf") for name in names)
        data = json.loads(archive.read("account.json"))
        assert data["account"]["email"] == "export_owner@example.com"
        assert len(data["reports"]) == 1
        assert "hashed_password" not in archive.read("account.json").decode()
        assert "mfa_secret" not in archive.read("account.json").decode()


async def test_delete_requires_password_and_revokes_account(client: AsyncClient) -> None:
    headers = await _signup(client, "delete_owner@example.com")
    wrong = await client.request(
        "DELETE", "/api/v1/users/me", headers=headers, json={"password": "wrong"}
    )
    assert wrong.status_code == 403
    assert (await client.get("/api/v1/users/me", headers=headers)).status_code == 200

    deleted = await client.request(
        "DELETE",
        "/api/v1/users/me",
        headers=headers,
        json={"password": "StrongP@ssword1"},
    )
    assert deleted.status_code == 204
    assert (await client.get("/api/v1/users/me", headers=headers)).status_code == 401


async def test_support_report_link_must_be_owned(client: AsyncClient) -> None:
    owner = await _signup(client, "support_owner@example.com")
    other = await _signup(client, "support_other@example.com")
    upload = await client.post(
        "/api/v1/reports/upload",
        headers=other,
        files={"file": ("other.pdf", VALID_PDF, "application/pdf")},
        data={"title": "Other", "report_date": "2024-01-01", "report_type": "blood"},
    )
    assert upload.status_code == 201
    response = await client.post(
        "/api/v1/support",
        headers=owner,
        json={
            "title": "Wrong result",
            "description": "This result belongs to a different report.",
            "category": "AI/Analysis",
            "related_report_id": upload.json()["id"],
        },
    )
    assert response.status_code in (403, 404)


async def test_support_round_trip_and_report_file_deleted(client: AsyncClient) -> None:
    headers = await _signup(client, "support_round_trip@example.com")
    upload = await client.post(
        "/api/v1/reports/upload",
        headers=headers,
        files={"file": ("report.pdf", VALID_PDF, "application/pdf")},
        data={"title": "My Report", "report_date": "2024-01-01", "report_type": "blood"},
    )
    assert upload.status_code == 201
    report_id = upload.json()["id"]
    storage_key = upload.json()["file_path"]
    assert await get_storage_backend().file_exists(storage_key)
    ticket = await client.post(
        "/api/v1/support",
        headers=headers,
        json={
            "title": "Question about result",
            "description": "The extracted number does not match the uploaded file.",
            "category": "AI/Analysis",
            "related_report_id": report_id,
        },
    )
    assert ticket.status_code == 201
    ticket_id = ticket.json()["ticket_id"]
    assert len((await client.get("/api/v1/support", headers=headers)).json()["tickets"]) == 1
    reply = await client.post(
        f"/api/v1/support/{ticket_id}/reply",
        headers=headers,
        json={"content": "I checked the original PDF."},
    )
    assert reply.status_code == 200
    detail = await client.get(f"/api/v1/support/{ticket_id}", headers=headers)
    assert detail.status_code == 200
    assert len(detail.json()["ticket"]["messages"]) == 2

    deleted = await client.request(
        "DELETE", "/api/v1/users/me", headers=headers,
        json={"password": "StrongP@ssword1"},
    )
    assert deleted.status_code == 204
    assert not await get_storage_backend().file_exists(storage_key)


async def test_export_survives_a_missing_original_file(client: AsyncClient, monkeypatch) -> None:
    headers = await _signup(client, "export_missing@example.com")
    fields = {"title": "Blood Test", "report_date": "2024-01-01", "report_type": "blood"}
    up = await client.post(
        "/api/v1/reports/upload",
        headers=headers,
        files={"file": ("gone.pdf", VALID_PDF, "application/pdf")},
        data=fields,
    )
    assert up.status_code == 201

    class _GoneStorage:
        async def download_file(self, _path):
            raise FileNotFoundError("gone")

    monkeypatch.setattr(
        "app.services.account_export.get_storage_backend", lambda: _GoneStorage()
    )
    response = await client.get("/api/v1/users/me/export", headers=headers)
    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert "reports/MISSING_FILES.txt" in archive.namelist()
        assert json.loads(archive.read("account.json"))["account"]["email"] == "export_missing@example.com"
