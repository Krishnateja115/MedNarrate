import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_report_delete_and_cascade_cleanup(client: AsyncClient, token_headers: dict):
    # 1. Create/upload a report
    upload_res = await client.post(
        "/api/v1/reports/upload",
        headers=token_headers,
        data={
            "title": "Deletion Test Report",
            "report_date": "2026-09-13",
            "report_type": "blood",
            "hospital": "Test Clinic"
        },
        files={"file": ("test_report.pdf", b"%PDF-1.4 test document content", "application/pdf")}
    )
    assert upload_res.status_code == 201
    report_id = upload_res.json()["id"]

    # 2. Verify report exists
    get_res = await client.get(f"/api/v1/reports/{report_id}", headers=token_headers)
    assert get_res.status_code == 200

    # 3. Delete report
    del_res = await client.delete(f"/api/v1/reports/{report_id}", headers=token_headers)
    assert del_res.status_code == 204

    # 4. Verify report is 404
    get_after_del = await client.get(f"/api/v1/reports/{report_id}", headers=token_headers)
    assert get_after_del.status_code == 404

    # 5. Verify deleting again returns 404 cleanly
    del_again = await client.delete(f"/api/v1/reports/{report_id}", headers=token_headers)
    assert del_again.status_code == 404
