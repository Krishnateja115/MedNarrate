import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, timedelta

from app.models.user import User, UserRole
from app.models.admin import AdminRole, AdminPermission, AdminRolePermission, AdminRoleAssignment, SensitiveAccessGrant
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
    
    stmt = select(AdminPermission).where(AdminPermission.name == "break_glass.approve")
    perm = (await db_session.execute(stmt)).scalars().first()
    if not perm:
        perm = AdminPermission(name="break_glass.approve")
        db_session.add(perm)
    
    await db_session.flush()
    db_session.add(AdminRolePermission(role_id=role.id, permission_id=perm.id))
    db_session.add(AdminRoleAssignment(user_id=user.id, role_id=role.id))
    await db_session.commit()
    return user

@pytest.fixture
async def test_report(db_session: AsyncSession):
    from app.models.report import Report, ReportType, ProcessingStatus
    report = Report(
        user_id=uuid.uuid4(),
        title="Test Report for Breakglass",
        report_type=ReportType.radiology,
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
            "reason": "Emergency review",
            "duration_minutes": 30
        },
        headers={"Authorization": f"Bearer {req_token}"}
    )
    assert req_resp.status_code == 200
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
    perm = (await db_session.execute(select(AdminPermission).where(AdminPermission.name == "break_glass.approve"))).scalars().first()
    if not perm:
        perm = AdminPermission(name="break_glass.approve")
        db_session.add(perm)
        await db_session.flush()
    db_session.add(AdminRolePermission(role_id=role_assignment.role_id, permission_id=perm.id))
    await db_session.commit()

    # Request
    req_resp = await client.post(
        "/api/v1/admin/break-glass/request",
        json={"resource_type": "medical_report", "resource_id": "rep_123", "reason": "Emergency review", "duration_minutes": 30},
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
    assert "Active break-glass grant required" in resp.json()["detail"]

@pytest.mark.asyncio
async def test_sensitive_access_allowed_with_grant(client: AsyncClient, admin_requester: User, admin_approver: User, test_report, db_session: AsyncSession):
    """Scenario D: Access to sensitive endpoint succeeds with active breakglass grant"""
    req_token = create_access_token(subject=str(admin_requester.id))
    app_token = create_access_token(subject=str(admin_approver.id))

    # Create & approve grant directly targeting the report ID
    req_resp = await client.post(
        "/api/v1/admin/break-glass/request",
        json={"resource_type": "medical_report", "resource_id": str(test_report.id), "reason": "Review", "duration_minutes": 30},
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
