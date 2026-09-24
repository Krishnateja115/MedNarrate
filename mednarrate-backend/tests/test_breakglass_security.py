import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone, timedelta

from app.models.user import User, UserRole
from app.models.admin import AdminRole, AdminPermission, AdminRolePermission, AdminRoleAssignment, SensitiveAccessGrant, AdminAuditLog
from app.core.security import create_access_token

@pytest.fixture
async def admin_requester(db_session: AsyncSession):
    user = User(
        email=f"req_{uuid.uuid4()}@test.com",
        hashed_password="hashed",
        full_name="Requester Admin",
        role=UserRole.admin
    )
    db_session.add(user)
    
    role = AdminRole(name=f"Breakglass Requester_{uuid.uuid4()}")
    db_session.add(role)
    
    # Assign required permissions
    for perm_name in ["break_glass.request", "reports.sensitive_view"]:
        stmt = select(AdminPermission).where(AdminPermission.name == perm_name)
        perm = (await db_session.execute(stmt)).scalars().first()
        if not perm:
            perm = AdminPermission(name=perm_name)
            db_session.add(perm)
        await db_session.flush()
        db_session.add(AdminRolePermission(role_id=role.id, permission_id=perm.id))
    
    await db_session.flush()
    db_session.add(AdminRoleAssignment(user_id=user.id, role_id=role.id))
    await db_session.commit()
    return user

@pytest.fixture
async def admin_approver(db_session: AsyncSession):
    user = User(
        email=f"app_{uuid.uuid4()}@test.com",
        hashed_password="hashed",
        full_name="Approver Admin",
        role=UserRole.admin
    )
    db_session.add(user)
    
    role = AdminRole(name=f"Breakglass Approver_{uuid.uuid4()}")
    db_session.add(role)
    
    stmt = select(AdminPermission).where(AdminPermission.name == "approve_sensitive_access")
    perm = (await db_session.execute(stmt)).scalars().first()
    if not perm:
        perm = AdminPermission(name="approve_sensitive_access")
        db_session.add(perm)
    
    await db_session.flush()
    db_session.add(AdminRolePermission(role_id=role.id, permission_id=perm.id))
    db_session.add(AdminRoleAssignment(user_id=user.id, role_id=role.id))
    await db_session.commit()
    return user

@pytest.fixture
async def test_report(db_session: AsyncSession):
    from app.models.report import Report, ReportType, ProcessingStatus, FileType
    report = Report(
        user_id=uuid.uuid4(),
        title="Test Report for Breakglass",
        report_type=ReportType.other,
        report_date=datetime.now(timezone.utc).date(),
        file_name="test.pdf",
        file_path="/tmp/test.pdf",
        file_type=FileType.pdf,
        processing_status=ProcessingStatus.completed,
        extracted_text="VERY SENSITIVE CLINICAL DATA"
    )
    db_session.add(report)
    await db_session.commit()
    return report

@pytest.mark.asyncio
async def test_breakglass_request_lifecycle(client: AsyncClient, admin_requester: User, admin_approver: User, db_session: AsyncSession):
    """Scenario A: Request -> Approve -> Active"""
    req_token = create_access_token(subject=str(admin_requester.id))
    app_token = create_access_token(subject=str(admin_approver.id))

    # 1. Requester requests access
    req_resp = await client.post(
        "/api/v1/admin/break-glass/request",
        json={
            "resource_type": "medical_report",
            "resource_id": "rep_123",
            "reason": "Emergency review"
        },
        headers={"Authorization": f"Bearer {req_token}"}
    )
    assert req_resp.status_code == 200, req_resp.text
    grant_id = req_resp.json()["grant"]["id"]
    assert req_resp.json()["grant"]["status"] == "requested"

    # 2. Approver approves access
    app_resp = await client.post(
        f"/api/v1/admin/break-glass/grants/{grant_id}/approve",
        json={"notes": "Approved for emergency"},
        headers={"Authorization": f"Bearer {app_token}"}
    )
    assert app_resp.status_code == 200

    # Verify DB state
    grant = (await db_session.execute(select(SensitiveAccessGrant).where(SensitiveAccessGrant.id == uuid.UUID(grant_id)))).scalar_one()
    assert grant.status == "active"
    assert grant.approved_by_id == admin_approver.id

@pytest.mark.asyncio
async def test_breakglass_self_approval_blocked(client: AsyncClient, admin_requester: User, db_session: AsyncSession):
    """Scenario B: Admin cannot approve their own request"""
    req_token = create_access_token(subject=str(admin_requester.id))

    # We need to give requester approve permission just for this test to prove self-approval block works
    role_assignment = (await db_session.execute(select(AdminRoleAssignment).where(AdminRoleAssignment.user_id == admin_requester.id))).scalar_one()
    perm = (await db_session.execute(select(AdminPermission).where(AdminPermission.name == "approve_sensitive_access"))).scalars().first()
    if not perm:
        perm = AdminPermission(name="approve_sensitive_access")
        db_session.add(perm)
        await db_session.flush()
    db_session.add(AdminRolePermission(role_id=role_assignment.role_id, permission_id=perm.id))
    await db_session.commit()

    # Request
    req_resp = await client.post(
        "/api/v1/admin/break-glass/request",
        json={"resource_type": "medical_report", "resource_id": "rep_123", "reason": "Emergency review"},
        headers={"Authorization": f"Bearer {req_token}"}
    )
    grant_id = req_resp.json()["grant"]["id"]

    # Try to self-approve
    app_resp = await client.post(
        f"/api/v1/admin/break-glass/grants/{grant_id}/approve",
        json={"notes": "Self approve"},
        headers={"Authorization": f"Bearer {req_token}"}
    )
    assert app_resp.status_code == 403
    assert "Self-approval is not permitted" in app_resp.json()["detail"]

@pytest.mark.asyncio
async def test_sensitive_access_denied_without_grant(client: AsyncClient, admin_requester: User, test_report):
    """Scenario C: Access to sensitive endpoint fails without active breakglass grant"""
    req_token = create_access_token(subject=str(admin_requester.id))

    resp = await client.get(
        f"/api/v1/admin/reports/{test_report.id}/sensitive",
        headers={"Authorization": f"Bearer {req_token}"}
    )
    # 403 Forbidden because no active grant exists
    assert resp.status_code == 403
    assert "No active sensitive access grant" in resp.json()["detail"]

@pytest.mark.asyncio
async def test_sensitive_access_allowed_with_grant(client: AsyncClient, admin_requester: User, admin_approver: User, test_report, db_session: AsyncSession):
    """Scenario D: Access to sensitive endpoint succeeds with active breakglass grant"""
    req_token = create_access_token(subject=str(admin_requester.id))
    app_token = create_access_token(subject=str(admin_approver.id))

    # Create & approve grant directly targeting the report ID
    req_resp = await client.post(
        "/api/v1/admin/break-glass/request",
        json={"resource_type": "medical_report", "resource_id": str(test_report.id), "reason": "Emergency review", "duration_minutes": 30},
        headers={"Authorization": f"Bearer {req_token}"}
    )
    grant_id = req_resp.json()["grant"]["id"]

    await client.post(
        f"/api/v1/admin/break-glass/grants/{grant_id}/approve",
        json={},
        headers={"Authorization": f"Bearer {app_token}"}
    )

    # Now access the sensitive endpoint
    resp = await client.get(
        f"/api/v1/admin/reports/{test_report.id}/sensitive",
        headers={"Authorization": f"Bearer {req_token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["report"]["extracted_text"] == "VERY SENSITIVE CLINICAL DATA"
    assert resp.json()["grant_id"] == grant_id

@pytest.mark.asyncio
async def test_sensitive_access_denied_with_expired_grant(client: AsyncClient, admin_requester: User, admin_approver: User, test_report, db_session: AsyncSession):
    """Scenario E: Access denied if grant is expired"""
    req_token = create_access_token(subject=str(admin_requester.id))
    
    # 1. Manually insert an EXPIRED grant
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    expired_grant = SensitiveAccessGrant(
        id=uuid.uuid4(),
        admin_id=admin_requester.id,
        resource_type="medical_report",
        resource_id=str(test_report.id),
        reason="Testing expiration",
        created_at=now - timedelta(hours=5),
        status="active",
        approved_by_id=admin_approver.id,
        approved_at=now - timedelta(hours=5),
        expires_at=now - timedelta(hours=1)
    )
    db_session.add(expired_grant)
    await db_session.commit()

    # 2. Attempt to access
    resp = await client.get(
        f"/api/v1/admin/reports/{test_report.id}/sensitive",
        headers={"Authorization": f"Bearer {req_token}"}
    )
    assert resp.status_code == 403
    assert "grant has expired" in resp.text

@pytest.mark.asyncio
async def test_audit_log_atomicity(client: AsyncClient, admin_requester: User, db_session: AsyncSession):
    """Scenario F: Audit log is atomic with state change. Force failure."""
    from unittest.mock import patch
    from sqlalchemy.exc import IntegrityError
    
    req_token = create_access_token(subject=str(admin_requester.id))
    
    # Count initial audit logs
    res = await db_session.execute(select(func.count()).select_from(AdminAuditLog))
    initial_count = res.scalar()

    # Mock db.commit to raise an exception
    with patch("sqlalchemy.ext.asyncio.AsyncSession.commit", side_effect=Exception("Simulated DB Failure")):
        try:
            await client.post(
                "/api/v1/admin/break-glass/request",
                json={
                    "resource_type": "medical_report",
                    "resource_id": "rep_123",
                    "reason": "Emergency review"
                },
                headers={"Authorization": f"Bearer {req_token}"}
            )
        except Exception as e:
            assert "Simulated DB Failure" in str(e)

    # Ensure no orphaned audit row was written (transaction rolled back)
    await db_session.rollback()
    res = await db_session.execute(select(func.count()).select_from(AdminAuditLog))
    final_count = res.scalar()
    assert final_count == initial_count
