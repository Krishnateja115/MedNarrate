import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_role_escalation_blocked(client: AsyncClient, token_headers: dict):
    # Attempt to update profile and inject 'role': 'admin'
    response = await client.patch(
        "/api/v1/users/me",
        headers=token_headers,
        json={"role": "admin", "full_name": "Hacker User"},
    )

    # Self-service role switching is restricted to patient and clinician.
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_patient_can_switch_to_doctor_profile(
    client: AsyncClient, token_headers: dict
):
    response = await client.patch(
        "/api/v1/users/me",
        headers=token_headers,
        json={"role": "clinician"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "clinician"
