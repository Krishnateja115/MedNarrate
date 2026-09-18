import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_role_escalation_blocked(client: AsyncClient, token_headers: dict):
    # Attempt to update profile and inject 'role': 'admin'
    response = await client.patch(
        "/api/v1/users/me",
        headers=token_headers,
        json={"role": "admin", "full_name": "Hacker User"}
    )
    
    # extra='forbid' should cause a 422 Unprocessable Entity
    assert response.status_code == 422
    assert "Extra inputs are not permitted" in response.text
