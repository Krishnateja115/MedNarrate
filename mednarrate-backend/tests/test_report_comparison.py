import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_compare_multiple_reports(client: AsyncClient, token_headers: dict):
    # This is an authenticated regression test for multi-report comparison
    # We will upload 2 reports and then call /api/v1/reports/compare?report_ids=1,2

    # 1. Upload Report 1
    # We will use the deterministic mock instead of file if needed, but since report3.pdf is tracked/deterministically generated, we can just use the minimal PDF byte string like before.
    minimal_pdf = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Count 1\n/Kids [ 3 0 R ]\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [ 0 0 612 792 ]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 21\n>>\nstream\nBT\n/F1 12 Tf\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000213 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n277\n%%EOF\n"

    resp1 = await client.post(
        "/api/v1/reports/upload",
        headers=token_headers,
        data={"title": "Report 1", "report_date": "2024-01-01", "report_type": "blood"},
        files={"file": ("report3.pdf", minimal_pdf, "application/pdf")},
    )
    assert resp1.status_code == 201
    report1_id = resp1.json()["id"]

    # 2. Upload Report 2
    resp2 = await client.post(
        "/api/v1/reports/upload",
        headers=token_headers,
        data={"title": "Report 2", "report_date": "2024-02-01", "report_type": "blood"},
        files={"file": ("report3.pdf", minimal_pdf, "application/pdf")},
    )
    assert resp2.status_code == 201
    report2_id = resp2.json()["id"]

    # 3. Call Compare Endpoint
    compare_resp = await client.get(
        f"/api/v1/reports/compare?report_ids={report1_id},{report2_id}",
        headers=token_headers,
    )

    # If the route collision is fixed, this should return 200 (or at least not 422 for uuid '{id}')
    assert compare_resp.status_code == 200
    data = compare_resp.json()
    # verify that both reports are present
    assert report1_id in data["report_ids"]
    assert report2_id in data["report_ids"]
    assert "comparisons" in data
