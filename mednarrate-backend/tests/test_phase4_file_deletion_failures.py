import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.report import Report
from app.models.orphan_file import OrphanFile
from app.core.security import create_step_up_token
from sqlalchemy import select
from datetime import date
import uuid

@pytest.mark.asyncio
async def test_file_deletion_failures(client: AsyncClient, db_session: AsyncSession, admin_token_and_user, target_user, bystander_user):
    headers, admin = admin_token_and_user

    # 1. Unrelated user's file (skipped)
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
    # 2. Malformed path (skipped)
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
    # 3. Valid file that will fail (orphan created)
    r3 = Report(
        user_id=target_user.id,
        file_path=f"/uploads/{target_user.id}/will_fail.pdf",
        title="Will Fail",
        report_type="blood",
        report_date=date.today(),
        file_name="will_fail.pdf",
        file_type="pdf",
        processing_status="completed"
    )
    # 4. Valid file that will succeed (no orphan)
    r4 = Report(
        user_id=target_user.id,
        file_path=f"/uploads/{target_user.id}/will_succeed.pdf",
        title="Will Succeed",
        report_type="blood",
        report_date=date.today(),
        file_name="will_succeed.pdf",
        file_type="pdf",
        processing_status="completed"
    )
    db_session.add_all([r1, r2, r3, r4])
    await db_session.commit()

    step_up = create_step_up_token(str(admin.id), admin.session_version)
    headers["x-step-up-token"] = step_up

    from unittest.mock import patch

    async def mock_delete_file(fp):
        if fp == f"/uploads/{target_user.id}/will_fail.pdf":
            raise Exception("Storage error")
        return None

    with patch("app.services.file_storage.delete_file", side_effect=mock_delete_file):
        resp = await client.request(
            "DELETE", f"/api/v1/admin/users/{target_user.id}",
            headers=headers,
            json={"reason": "test", "confirmation": f"DELETE {target_user.id}"}
        )

    assert resp.status_code == 200
    assert (await db_session.execute(select(User).where(User.id == target_user.id))).scalar() is None

    # Verify OrphanFile records
    orphans = (await db_session.execute(
        select(OrphanFile).where(OrphanFile.file_path.contains(str(target_user.id)))
    )).scalars().all()

    # Only exactly one pending OrphanFile should be created
    assert len(orphans) == 1

    orphan = orphans[0]
    assert orphan.file_path == f"/uploads/{target_user.id}/will_fail.pdf"
    assert orphan.status == "pending"
    # Sanitized error category, raw exception is not stored
    assert orphan.last_error_code == "unknown"
    assert "Storage error" not in (orphan.last_error_code or "")

    # Successful deletion (will_succeed.pdf) created no orphan
    # Malformed/unrelated skipped
