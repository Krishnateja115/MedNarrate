from httpx import AsyncClient


async def test_public_account_deletion_page(client: AsyncClient) -> None:
    response = await client.get("/account-deletion")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert "Delete your MedNarrate account" in response.text
    assert "/api/v1/auth/login" in response.text
    assert "/api/v1/users/me" in response.text
    assert "__NONCE__" not in response.text
    assert "Content-Security-Policy" in response.headers
