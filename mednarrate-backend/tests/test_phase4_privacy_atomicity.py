import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.privacy import PrivacyDataRequest
from app.models.admin import AdminAuditLog
from app.core.security import create_step_up_token
from unittest.mock import patch
from app.main import app

@pytest.mark.asyncio
async def test_privacy_status_update_atomicity(client: AsyncClient, db_session: AsyncSession, admin_token_and_user, target_user):
    headers, admin = admin_token_and_user
    
    # Create privacy request
    pr = PrivacyDataRequest(user_id=target_user.id, request_type="deletion", reason="test")
    db_session.add(pr)
    await db_session.commit()
    await db_session.refresh(pr)
    
    # Step up
    step_up = create_step_up_token(str(admin.id), admin.session_version)
    headers["x-step-up-token"] = step_up
    
    # Update status
    resp = await client.request("PATCH", f"/api/v1/admin/privacy/requests/{pr.id}/status", headers=headers, json={"status": "approved", "admin_notes": "test atomicity"})
    assert resp.status_code == 200
    
    # Verify business state
    await db_session.refresh(pr)
    assert pr.status == "approved"
    
    # Verify audit log
    audit_res = await db_session.execute(select(AdminAuditLog).where(AdminAuditLog.resource_id == str(pr.id), AdminAuditLog.action == "privacy_request_status_update"))
    audit_log = audit_res.scalar_one_or_none()
    assert audit_log is not None
    assert audit_log.metadata_payload.get("new_status") == "approved"
    
@pytest.mark.asyncio
async def test_privacy_status_update_atomicity_failure(client: AsyncClient, db_session: AsyncSession, admin_token_and_user, target_user):
    headers, admin = admin_token_and_user
    
    pr = PrivacyDataRequest(user_id=target_user.id, request_type="deletion", reason="test2")
    db_session.add(pr)
    await db_session.commit()
    await db_session.refresh(pr)
    
    step_up = create_step_up_token(str(admin.id), admin.session_version)
    headers["x-step-up-token"] = step_up
    
    # Simulate DB failure during commit
    try:
        with patch("app.api.v1.admin_privacy.AsyncSession.commit", side_effect=Exception("DB Failure")):
            await client.request("PATCH", f"/api/v1/admin/privacy/requests/{pr.id}/status", headers=headers, json={"status": "rejected", "admin_notes": "should fail"})
    except BaseException:
        pass # Client propagated exception
        
    # Verify business state rollback (or rather, not committed)
    await db_session.refresh(pr)
    assert pr.status != "rejected"
    assert pr.status == "requested" # default
    
    # Verify no audit log
    audit_res = await db_session.execute(select(AdminAuditLog).where(AdminAuditLog.resource_id == str(pr.id), AdminAuditLog.action == "privacy_request_status_update"))
    audit_log = audit_res.scalar_one_or_none()
    assert audit_log is None
