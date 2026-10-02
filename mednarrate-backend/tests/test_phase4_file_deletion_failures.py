import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.report import Report
from app.core.security import create_step_up_token
from sqlalchemy import select
from datetime import date
import uuid

@pytest.mark.asyncio
async def test_file_deletion_failures(client: AsyncClient, db_session: AsyncSession, admin_token_and_user, target_user, bystander_user):
    headers, admin = admin_token_and_user

    r1 = Report(
        user_id=target_user.id,
        file_path=f"/uploads/{bystander_user.id}/report.pdf",
        title="Traversal Report",
        report_type="blood",
        report_date=date.today(),
        file_name="report.pdf",
        file_type="pdf",
        processing_status="completed"
    )
    r2 = Report(
        user_id=target_user.id,
        file_path=f"/uploads/{target_user.id}/../../../etc/passwd",
        title="Etc Passwd",
        report_type="blood",
        report_date=date.today(),
        file_name="report.pdf",
        file_type="pdf",
        processing_status="completed"
    )
    db_session.add(r1)
    db_session.add(r2)
    await db_session.commit()

    step_up = create_step_up_token(str(admin.id), admin.session_version)
    headers["x-step-up-token"] = step_up

    from unittest.mock import patch
    with patch("app.services.file_storage.delete_file") as mock_delete:
        mock_delete.side_effect = Exception("Storage error")
        resp = await client.request(
            "DELETE", f"/api/v1/admin/users/{target_user.id}",
            headers=headers,
            json={"reason": "test", "confirmation": f"DELETE {target_user.id}"}
        )

    assert resp.status_code == 200
    assert (await db_session.execute(select(User).where(User.id == target_user.id))).scalar() is None

    calls = mock_delete.call_args_list
    assert len(calls) == 1
    assert calls[0][0][0] == f"/uploads/{target_user.id}/report.pdf"
