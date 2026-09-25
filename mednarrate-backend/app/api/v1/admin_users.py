import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy import String, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.admin_auth import (
    AdminContext,
    require_all_permissions,
    require_permission,
)
from app.core.database import get_db
from app.core.pagination import build_pagination_response, clamp_limit, page_to_offset
from app.core.security import hash_password
from app.models.admin import AdminAuditLog
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole

router = APIRouter()


class ChangeRoleRequest(BaseModel):
    role: UserRole


async def log_admin_action(
    db: AsyncSession,
    admin_ctx: AdminContext,
    action: str,
    resource_type: str,
    resource_id: str,
    metadata_payload: dict,
    request: Request,
):
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    audit_log = AdminAuditLog(
        actor_admin_id=admin_ctx.user.id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata_payload=metadata_payload,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(audit_log)
    await db.commit()


@router.get("")
async def get_users(
    request: Request,
    admin_ctx: AdminContext = Depends(require_permission("users.view")),
    db: AsyncSession = Depends(get_db),
    sort_by: str = Query("created_at"),
    sort_desc: bool = Query(True),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    search: Optional[str] = None,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
):
    limit = clamp_limit(limit)
    stmt = select(User)

    if search:
        search_term = f"%{search}%"
        stmt = stmt.where(
            or_(
                User.full_name.ilike(search_term),
                User.email.ilike(search_term),
                User.id.cast(String).ilike(search_term)
                if search.replace("-", "").isalnum()
                else False,
            )
        )

    if role:
        stmt = stmt.where(User.role == role)

    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)

    # Count total matching records
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_count = (await db.execute(count_stmt)).scalar() or 0

    sort_col = getattr(User, sort_by, User.created_at)
    if sort_desc:
        stmt = stmt.order_by(desc(sort_col))
    else:
        stmt = stmt.order_by(sort_col)

    # Paginate and fetch
    stmt = stmt.offset(page_to_offset(page, limit)).limit(limit)
    users = (await db.execute(stmt)).scalars().all()

    items = [
        {
            "id": str(u.id),
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role.value,
            "preferred_language": u.preferred_language,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "updated_at": u.updated_at.isoformat() if u.updated_at else None,
        }
        for u in users
    ]

    return build_pagination_response(items, total_count, page, limit)


@router.get("/{user_id}")
async def get_user_detail(
    user_id: uuid.UUID,
    admin_ctx: AdminContext = Depends(require_permission("users.view")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(User).where(User.id == user_id)
    user = (await db.execute(stmt)).scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Fetch report count for this user
    from app.models.report import Report

    report_count_stmt = select(func.count(Report.id)).where(Report.user_id == user_id)
    report_count = (await db.execute(report_count_stmt)).scalar() or 0

    # Check last login (approximate via latest refresh token created_at)
    last_login_stmt = (
        select(RefreshToken.created_at)
        .where(RefreshToken.user_id == user_id)
        .order_by(desc(RefreshToken.created_at))
        .limit(1)
    )
    last_login = (await db.execute(last_login_stmt)).scalar()

    return {
        "status": "ok",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "preferred_language": user.preferred_language,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            "reports_count": report_count,
            "last_login": last_login.isoformat() if last_login else None,
        },
    }


@router.post("/{user_id}/actions/suspend")
async def suspend_user(
    request: Request,
    user_id: uuid.UUID,
    admin_ctx: AdminContext = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db),
):
    user = (await db.execute(select(User).where(User.id == user_id))).scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == admin_ctx.user.id:
        raise HTTPException(status_code=400, detail="Cannot suspend yourself")

    user.is_active = False
    await log_admin_action(
        db,
        admin_ctx,
        "USER_SUSPEND",
        "user",
        str(user.id),
        {"email": user.email},
        request,
    )

    return {"status": "ok", "message": f"User {user.email} suspended"}


@router.post("/{user_id}/actions/activate")
async def activate_user(
    request: Request,
    user_id: uuid.UUID,
    admin_ctx: AdminContext = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db),
):
    user = (await db.execute(select(User).where(User.id == user_id))).scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = True
    await log_admin_action(
        db,
        admin_ctx,
        "USER_ACTIVATE",
        "user",
        str(user.id),
        {"email": user.email},
        request,
    )

    return {"status": "ok", "message": f"User {user.email} activated"}


@router.post("/{user_id}/actions/force_logout")
async def force_logout(
    request: Request,
    user_id: uuid.UUID,
    admin_ctx: AdminContext = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db),
):
    user = (await db.execute(select(User).where(User.id == user_id))).scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    tokens = (
        (await db.execute(select(RefreshToken).where(RefreshToken.user_id == user_id)))
        .scalars()
        .all()
    )
    count = 0
    for t in tokens:
        if not t.revoked:
            t.revoked = True
            count += 1

    await log_admin_action(
        db,
        admin_ctx,
        "USER_FORCE_LOGOUT",
        "user",
        str(user.id),
        {"sessions_revoked": count},
        request,
    )

    return {"status": "ok", "message": f"Revoked {count} active sessions"}


@router.post("/{user_id}/actions/change_role")
async def change_role(
    request: Request,
    user_id: uuid.UUID,
    payload: ChangeRoleRequest,
    admin_ctx: AdminContext = Depends(
        require_all_permissions(["users.manage", "super_admin"])
    ),
    db: AsyncSession = Depends(get_db),
):
    user = (await db.execute(select(User).where(User.id == user_id))).scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == admin_ctx.user.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")

    old_role = user.role
    user.role = payload.role

    await log_admin_action(
        db,
        admin_ctx,
        "USER_ROLE_CHANGE",
        "user",
        str(user.id),
        {"old_role": old_role.value, "new_role": payload.role.value},
        request,
    )

    return {
        "status": "ok",
        "message": f"Role changed from {old_role.value} to {payload.role.value}",
    }


@router.post("/{user_id}/actions/reset_password")
async def reset_password(
    request: Request,
    user_id: uuid.UUID,
    admin_ctx: AdminContext = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db),
):
    user = (await db.execute(select(User).where(User.id == user_id))).scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    import secrets

    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_password(raw_token)

    pr_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(pr_token)

    await log_admin_action(
        db,
        admin_ctx,
        "USER_PASSWORD_RESET_GENERATED",
        "user",
        str(user.id),
        {},
        request,
    )

    # Return the raw token for the admin to distribute securely
    reset_link = f"https://app.mednarrate.com/reset-password?token={raw_token}"
    return {
        "status": "ok",
        "reset_link": reset_link,
        "message": "Password reset link generated securely.",
    }

# User Detail Tabs - Sub-endpoints

from app.models.chat import ChatSession
from app.models.medication_schedule import MedicationSchedule
from app.models.notification_log import NotificationLog
from app.models.report import Report
from app.models.report_analysis import ReportAnalysis
from app.models.support import SupportTicket
from app.models.push_token import PushToken
from app.models.medical_profile import MedicalProfile
from app.models.doctor_profile import DoctorProfile
from app.models.caregiver_profile import CaregiverProfile
from app.models.admin import SensitiveAccessGrant

@router.get("/{user_id}/medical_profile")
async def get_medical_profile(
    request: Request,
    user_id: uuid.UUID,
    admin_ctx: AdminContext = Depends(require_permission("users.view")),
    db: AsyncSession = Depends(get_db),
):
    # Verify break-glass access or explicit permission
    if "super_admin" not in admin_ctx.permissions:
        stmt_bg = select(SensitiveAccessGrant).where(
            SensitiveAccessGrant.admin_id == admin_ctx.user.id,
            SensitiveAccessGrant.resource_type == "medical_profile",
            SensitiveAccessGrant.resource_id == str(user_id),
            SensitiveAccessGrant.expires_at > datetime.utcnow()
        )
        bg = (await db.execute(stmt_bg)).scalars().first()
        if not bg:
            raise HTTPException(status_code=403, detail="Active break-glass grant required to view PHI")

    stmt = select(MedicalProfile).where(MedicalProfile.user_id == user_id)
    prof = (await db.execute(stmt)).scalars().first()
    
    await log_admin_action(
        db, admin_ctx, "PHI_ACCESSED", "medical_profile", str(user_id), {}, request
    )

    if not prof:
        return {"status": "ok", "profile": None}

    return {
        "status": "ok",
        "profile": {
            "id": str(prof.id),
            "blood_group": prof.blood_group,
            "known_allergies": prof.known_allergies,
            "chronic_conditions": prof.chronic_conditions,
            "emergency_contact_name": prof.emergency_contact_name,
            "emergency_contact_phone": prof.emergency_contact_phone,
            "updated_at": prof.updated_at.isoformat() if prof.updated_at else None
        }
    }

@router.get("/{user_id}/doctor_profile")
async def get_doctor_profile(
    user_id: uuid.UUID,
    admin_ctx: AdminContext = Depends(require_permission("users.view")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(DoctorProfile).where(DoctorProfile.user_id == user_id)
    prof = (await db.execute(stmt)).scalars().first()
    
    if not prof:
        return {"status": "ok", "profile": None}

    return {
        "status": "ok",
        "profile": {
            "id": str(prof.id),
            "specialty": prof.specialty,
            "qualifications": prof.qualifications,
            "license_number": prof.license_number,
            "years_of_experience": prof.years_of_experience,
            "hospital": prof.hospital,
            "professional_address": prof.professional_address,
            "bio": prof.bio,
            "updated_at": prof.updated_at.isoformat() if prof.updated_at else None
        }
    }

@router.get("/{user_id}/caregiver_profile")
async def get_caregiver_profile(
    user_id: uuid.UUID,
    admin_ctx: AdminContext = Depends(require_permission("users.view")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CaregiverProfile).where(CaregiverProfile.user_id == user_id)
    prof = (await db.execute(stmt)).scalars().first()
    
    if not prof:
        return {"status": "ok", "profile": None}

    return {
        "status": "ok",
        "profile": {
            "id": str(prof.id),
            "relationship": prof.relationship,
            "caregiver_role": prof.caregiver_role,
            "supported_patient_name": prof.supported_patient_name,
            "organization": prof.organization,
            "updated_at": prof.updated_at.isoformat() if prof.updated_at else None
        }
    }

@router.get("/{user_id}/sessions")
async def get_user_sessions(
    user_id: uuid.UUID,
    admin_ctx: AdminContext = Depends(require_permission("users.view")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(RefreshToken).where(RefreshToken.user_id == user_id).order_by(desc(RefreshToken.created_at))
    tokens = (await db.execute(stmt)).scalars().all()
    
    pt_stmt = select(PushToken).where(PushToken.user_id == user_id).order_by(desc(PushToken.created_at))
    push_tokens = (await db.execute(pt_stmt)).scalars().all()
    
    return {
        "status": "ok",
        "sessions": [
            {
                "id": str(t.id),
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "expires_at": t.expires_at.isoformat() if t.expires_at else None,
                "revoked": t.revoked
            }
            for t in tokens
        ],
        "device_sessions": [
            {
                "id": str(pt.id),
                "device_token": pt.device_token,
                "platform": pt.platform,
                "created_at": pt.created_at.isoformat() if pt.created_at else None,
                "updated_at": pt.updated_at.isoformat() if pt.updated_at else None,
            }
            for pt in push_tokens
        ]
    }


@router.post("/{user_id}/doctor_profile/verify")
async def verify_doctor_profile(
    request: Request,
    user_id: uuid.UUID,
    admin_ctx: AdminContext = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(DoctorProfile).where(DoctorProfile.user_id == user_id)
    prof = (await db.execute(stmt)).scalars().first()
    if not prof:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
        
    user = (await db.execute(select(User).where(User.id == user_id))).scalars().first()
    if user:
        user.role = UserRole.clinician
    
    await log_admin_action(
        db, admin_ctx, "DOCTOR_VERIFIED", "user", str(user_id), {"specialty": prof.specialty}, request
    )
    await db.commit()
    return {"status": "ok", "message": "Doctor profile verified and user role updated"}

@router.post("/{user_id}/caregiver_profile/verify")
async def verify_caregiver_profile(
    request: Request,
    user_id: uuid.UUID,
    admin_ctx: AdminContext = Depends(require_permission("users.manage")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CaregiverProfile).where(CaregiverProfile.user_id == user_id)
    prof = (await db.execute(stmt)).scalars().first()
    if not prof:
        raise HTTPException(status_code=404, detail="Caregiver profile not found")
        
    user = (await db.execute(select(User).where(User.id == user_id))).scalars().first()
    if user:
        user.role = UserRole.caregiver
        
    await log_admin_action(
        db, admin_ctx, "CAREGIVER_VERIFIED", "user", str(user_id), {"relationship": prof.relationship}, request
    )
    await db.commit()
    return {"status": "ok", "message": "Caregiver profile verified and user role updated"}

@router.get("/{user_id}/reports")
async def get_user_reports(
    user_id: uuid.UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    admin_ctx: AdminContext = Depends(require_permission("users.view")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Report).where(Report.user_id == user_id).order_by(desc(Report.uploaded_at))
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_count = (await db.execute(count_stmt)).scalar() or 0
    
    stmt = stmt.offset(page_to_offset(page, limit)).limit(limit)
    reports = (await db.execute(stmt)).scalars().all()
    
    items = [
        {
            "id": str(r.id),
            "title": r.title,
            "report_type": r.report_type.value if r.report_type else "unknown",
            "processing_status": r.processing_status.value if r.processing_status else "unknown",
            "uploaded_at": r.uploaded_at.isoformat() if r.uploaded_at else None
        } for r in reports
    ]
    return build_pagination_response(items, total_count, page, limit)

@router.get("/{user_id}/analyses")
async def get_user_analyses(
    user_id: uuid.UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    admin_ctx: AdminContext = Depends(require_permission("users.view")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ReportAnalysis).join(Report, ReportAnalysis.report_id == Report.id).where(Report.user_id == user_id).order_by(desc(ReportAnalysis.created_at))
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_count = (await db.execute(count_stmt)).scalar() or 0
    
    stmt = stmt.offset(page_to_offset(page, limit)).limit(limit)
    analyses = (await db.execute(stmt)).scalars().all()
    
    items = [
        {
            "id": str(a.id),
            "report_id": str(a.report_id),
            "status": a.status,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "error_message": a.error_message
        } for a in analyses
    ]
    return build_pagination_response(items, total_count, page, limit)

@router.get("/{user_id}/chats")
async def get_user_chats(
    user_id: uuid.UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    admin_ctx: AdminContext = Depends(require_permission("users.view")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ChatSession).where(ChatSession.user_id == user_id).order_by(desc(ChatSession.created_at))
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_count = (await db.execute(count_stmt)).scalar() or 0
    
    stmt = stmt.offset(page_to_offset(page, limit)).limit(limit)
    chats = (await db.execute(stmt)).scalars().all()
    
    items = [
        {
            "id": str(c.id),
            "title": c.title,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None
        } for c in chats
    ]
    return build_pagination_response(items, total_count, page, limit)

@router.get("/{user_id}/reminders")
async def get_user_reminders(
    user_id: uuid.UUID,
    admin_ctx: AdminContext = Depends(require_permission("users.view")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(MedicationSchedule).where(MedicationSchedule.user_id == user_id).order_by(desc(MedicationSchedule.created_at))
    reminders = (await db.execute(stmt)).scalars().all()
    
    return {
        "status": "ok",
        "reminders": [
            {
                "id": str(r.id),
                "medication_name": r.medication_name,
                "dosage": r.dosage,
                "frequency": r.frequency,
                "is_active": r.is_active,
                "created_at": r.created_at.isoformat() if r.created_at else None
            } for r in reminders
        ]
    }

@router.get("/{user_id}/notifications")
async def get_user_notifications(
    user_id: uuid.UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    admin_ctx: AdminContext = Depends(require_permission("users.view")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(NotificationLog).where(NotificationLog.user_id == user_id).order_by(desc(NotificationLog.sent_at))
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_count = (await db.execute(count_stmt)).scalar() or 0
    
    stmt = stmt.offset(page_to_offset(page, limit)).limit(limit)
    logs = (await db.execute(stmt)).scalars().all()
    
    items = [
        {
            "id": str(l.id),
            "notification_type": l.notification_type,
            "status": l.status,
            "error_message": l.error_message,
            "sent_at": l.sent_at.isoformat() if l.sent_at else None
        } for l in logs
    ]
    return build_pagination_response(items, total_count, page, limit)

@router.get("/{user_id}/support")
async def get_user_support(
    user_id: uuid.UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    admin_ctx: AdminContext = Depends(require_permission("users.view")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(SupportTicket).where(SupportTicket.user_id == user_id).order_by(desc(SupportTicket.created_at))
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_count = (await db.execute(count_stmt)).scalar() or 0
    
    stmt = stmt.offset(page_to_offset(page, limit)).limit(limit)
    tickets = (await db.execute(stmt)).scalars().all()
    
    items = [
        {
            "id": str(t.id),
            "subject": t.subject,
            "status": t.status.value if t.status else "unknown",
            "priority": t.priority.value if t.priority else "unknown",
            "created_at": t.created_at.isoformat() if t.created_at else None
        } for t in tickets
    ]
    return build_pagination_response(items, total_count, page, limit)

@router.get("/{user_id}/security")
async def get_user_security(
    user_id: uuid.UUID,
    admin_ctx: AdminContext = Depends(require_permission("users.view")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AdminAuditLog).where(AdminAuditLog.resource_id == str(user_id)).order_by(desc(AdminAuditLog.timestamp))
    logs = (await db.execute(stmt)).scalars().all()
    
    return {
        "status": "ok",
        "logs": [
            {
                "id": str(l.id),
                "action": l.action,
                "actor_admin_id": str(l.actor_admin_id) if l.actor_admin_id else None,
                "timestamp": l.timestamp.isoformat() if l.timestamp else None,
                "metadata_payload": l.metadata_payload
            } for l in logs
        ]
    }
