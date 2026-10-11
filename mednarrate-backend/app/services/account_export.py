"""Build a user-owned medical-data archive without exporting credentials."""

import json
import os
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import PurePath
from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.caregiver_profile import CaregiverProfile
from app.models.chat import ChatMessage, ChatSession
from app.models.doctor_profile import DoctorProfile
from app.models.medical_profile import MedicalProfile
from app.models.medication_schedule import MedicationSchedule
from app.models.report import Report
from app.models.report_analysis import ReportAnalysis
from app.models.support import SupportTicket, SupportTicketMessage
from app.models.user import User
from app.services.storage import get_storage_backend


def _row_data(row: Any, *, exclude: set[str] | None = None) -> dict[str, Any]:
    """Serialize a selected row, never an entire user/auth ORM object."""
    excluded = exclude or set()
    return jsonable_encoder(
        {
            column.key: getattr(row, column.key)
            for column in row.__table__.columns
            if column.key not in excluded
        }
    )


async def build_account_archive(user: User, db: AsyncSession) -> str:
    """Create a temporary ZIP of the user's records and original documents."""
    reports = (
        await db.execute(select(Report).where(Report.user_id == user.id))
    ).scalars().all()
    report_ids = [report.id for report in reports]
    analyses = (
        (
            await db.execute(
                select(ReportAnalysis).where(ReportAnalysis.report_id.in_(report_ids))
            )
        ).scalars().all()
        if report_ids
        else []
    )
    sessions = (
        await db.execute(select(ChatSession).where(ChatSession.user_id == user.id))
    ).scalars().all()
    session_ids = [session.id for session in sessions]
    messages = (
        (
            await db.execute(
                select(ChatMessage).where(ChatMessage.chat_session_id.in_(session_ids))
            )
        ).scalars().all()
        if session_ids
        else []
    )
    tickets = (
        await db.execute(select(SupportTicket).where(SupportTicket.user_id == user.id))
    ).scalars().all()
    ticket_ids = [ticket.id for ticket in tickets]
    ticket_messages = (
        (
            await db.execute(
                select(SupportTicketMessage).where(
                    SupportTicketMessage.ticket_id.in_(ticket_ids),
                    SupportTicketMessage.is_internal.is_(False),
                )
            )
        ).scalars().all()
        if ticket_ids
        else []
    )

    async def user_rows(model: Any) -> list[dict[str, Any]]:
        rows = (
            await db.execute(select(model).where(model.user_id == user.id))
        ).scalars().all()
        return [_row_data(row) for row in rows]

    payload = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "account": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value if user.role else None,
            "preferred_language": user.preferred_language,
            "date_of_birth": user.date_of_birth,
            "gender": user.gender,
            "created_at": jsonable_encoder(user.created_at),
        },
        "medical_profiles": await user_rows(MedicalProfile),
        "doctor_profiles": await user_rows(DoctorProfile),
        "caregiver_profiles": await user_rows(CaregiverProfile),
        "reports": [_row_data(report, exclude={"file_path"}) for report in reports],
        "analyses": [_row_data(analysis) for analysis in analyses],
        "medication_schedules": await user_rows(MedicationSchedule),
        "chat_sessions": [_row_data(session) for session in sessions],
        "chat_messages": [_row_data(message) for message in messages],
        "support_tickets": [_row_data(ticket) for ticket in tickets],
        "support_messages": [_row_data(message) for message in ticket_messages],
    }

    with tempfile.NamedTemporaryFile(prefix="mednarrate-export-", suffix=".zip", delete=False) as temp:
        archive_path = temp.name

    try:
        storage = get_storage_backend()
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("account.json", json.dumps(payload, indent=2, ensure_ascii=False))
            for report in reports:
                original = await storage.download_file(report.file_path)
                safe_name = PurePath(report.file_name.replace("\\", "/")).name
                archive.writestr(f"reports/{report.id}/{safe_name}", original)
    except Exception:
        os.unlink(archive_path)
        raise

    return archive_path
