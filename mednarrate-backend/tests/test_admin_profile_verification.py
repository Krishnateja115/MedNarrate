"""Admin user detail: clinician / caregiver verification state and the medical profile fields.

The admin page reads `is_verified`, `date_of_birth` and `gender`. Profiles have no verified column, so the
verified state comes from the audit entry the verify route writes (the user's role proves nothing: users can
choose the clinician role themselves).
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import SensitiveAccessGrant
from app.models.caregiver_profile import CaregiverProfile
from app.models.doctor_profile import DoctorProfile
from app.models.medical_profile import MedicalProfile
from app.models.user import User, UserRole


async def _grant(db: AsyncSession, admin_id, resource_type: str) -> None:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(
        SensitiveAccessGrant(
            id=uuid.uuid4(),
            admin_id=admin_id,
            resource_type=resource_type,
            resource_id="*",
            reason="test",
            requested_duration_hours=1,
            created_at=now,
            expires_at=now + timedelta(hours=1),
            status="active",
        )
    )
    await db.commit()


@pytest.fixture
async def profile_user(db_session: AsyncSession):
    user = User(
        email=f"profiles_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="pw",
        full_name="Profile User",
        role=UserRole.clinician,  # self-selected: must not count as verified
        date_of_birth="1980-05-17",
        gender="female",
    )
    db_session.add(user)
    await db_session.flush()
    db_session.add_all(
        [
            MedicalProfile(user_id=user.id, blood_group="O+", known_allergies="Penicillin", chronic_conditions="Asthma"),
            DoctorProfile(user_id=user.id, specialty="Cardiology", hospital="City Hospital"),
            CaregiverProfile(user_id=user.id, relationship="daughter"),
        ]
    )
    await db_session.commit()
    return user


@pytest.mark.asyncio
async def test_medical_profile_includes_date_of_birth_and_gender(
    client: AsyncClient, db_session: AsyncSession, admin_token_and_user, profile_user
):
    headers, admin = admin_token_and_user
    await _grant(db_session, admin.id, "medical_profile")
    resp = await client.get(f"/api/v1/admin/users/{profile_user.id}/medical_profile", headers=headers)
    assert resp.status_code == 200
    profile = resp.json()["profile"]
    assert profile["date_of_birth"] == "1980-05-17"
    assert profile["gender"] == "female"
    assert profile["blood_group"] == "O+"
    assert profile["known_allergies"] == "Penicillin"


@pytest.mark.asyncio
async def test_doctor_is_unverified_until_an_admin_verifies(
    client: AsyncClient, db_session: AsyncSession, admin_token_and_user, profile_user
):
    headers, admin = admin_token_and_user
    await _grant(db_session, admin.id, "doctor_profile")
    url = f"/api/v1/admin/users/{profile_user.id}/doctor_profile"

    before = await client.get(url, headers=headers)
    assert before.status_code == 200
    assert before.json()["profile"]["is_verified"] is False  # role is clinician, still unverified

    verify = await client.post(f"{url}/verify", headers=headers)
    assert verify.status_code == 200

    after = await client.get(url, headers=headers)
    assert after.json()["profile"]["is_verified"] is True


@pytest.mark.asyncio
async def test_caregiver_is_unverified_until_an_admin_verifies(
    client: AsyncClient, db_session: AsyncSession, admin_token_and_user, profile_user
):
    headers, admin = admin_token_and_user
    await _grant(db_session, admin.id, "caregiver_profile")
    url = f"/api/v1/admin/users/{profile_user.id}/caregiver_profile"

    assert (await client.get(url, headers=headers)).json()["profile"]["is_verified"] is False
    assert (await client.post(f"{url}/verify", headers=headers)).status_code == 200
    assert (await client.get(url, headers=headers)).json()["profile"]["is_verified"] is True


@pytest.mark.asyncio
async def test_verifying_one_user_does_not_verify_another(
    client: AsyncClient, db_session: AsyncSession, admin_token_and_user, profile_user
):
    headers, admin = admin_token_and_user
    await _grant(db_session, admin.id, "doctor_profile")
    other = User(email=f"other_{uuid.uuid4().hex[:8]}@example.com", hashed_password="pw", full_name="Other", role=UserRole.patient)
    db_session.add(other)
    await db_session.flush()
    db_session.add(DoctorProfile(user_id=other.id, specialty="Neurology"))
    await db_session.commit()

    await client.post(f"/api/v1/admin/users/{profile_user.id}/doctor_profile/verify", headers=headers)
    other_view = await client.get(f"/api/v1/admin/users/{other.id}/doctor_profile", headers=headers)
    assert other_view.json()["profile"]["is_verified"] is False
