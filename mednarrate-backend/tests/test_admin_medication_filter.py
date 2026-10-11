"""Regression coverage for the active-medication admin filter."""

from app.api.v1.admin_automation_ops import list_medications
from app.models.medication_schedule import MedicationSchedule
from app.models.user import User


async def test_admin_active_medications_filter_returns_only_active(db_session) -> None:
    user = User(email="med-filter@example.com", hashed_password="unused", full_name="Test")
    db_session.add(user)
    await db_session.flush()
    db_session.add_all(
        [
            MedicationSchedule(
                user_id=user.id,
                medication_name="Active",
                times_of_day=["09:00"],
                is_active=True,
            ),
            MedicationSchedule(
                user_id=user.id,
                medication_name="Inactive",
                times_of_day=["10:00"],
                is_active=False,
            ),
        ]
    )
    await db_session.commit()

    result = await list_medications(
        active_only=True,
        sort_by="created_at",
        sort_desc=True,
        page=1,
        limit=25,
        admin_ctx=None,
        db=db_session,
    )
    assert result["total"] == 1
    assert [item["medication_name"] for item in result["items"]] == ["Active"]
