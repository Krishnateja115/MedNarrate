import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete

from app.models.user import User
from app.models.admin import AdminAuditLog
from app.models.report import Report
from app.models.medical_profile import MedicalProfile
from app.models.doctor_profile import DoctorProfile
from app.models.caregiver_profile import CaregiverProfile
from app.models.chat import ChatSession
from app.models.notification_log import NotificationLog
from app.core.security import revoke_all_user_sessions, hash_token
from app.services.file_storage import delete_file

logger = logging.getLogger(__name__)

async def anonymize_and_delete_user_data(target_user: User, db: AsyncSession):
    # Revoke sessions
    await revoke_all_user_sessions(target_user, db, increment_session_version=True)
    
    # Get all reports to delete their files
    reports_stmt = select(Report).where(Report.user_id == target_user.id)
    reports = (await db.execute(reports_stmt)).scalars().all()
    file_paths = [r.file_path for r in reports if r.file_path]
    
    # Anonymize target user's metadata in existing admin audit logs
    audit_stmt = select(AdminAuditLog).where(AdminAuditLog.resource_id == str(target_user.id))
    audits = (await db.execute(audit_stmt)).scalars().all()
    for audit in audits:
        if audit.metadata_payload and isinstance(audit.metadata_payload, dict):
            new_payload = audit.metadata_payload.copy()
            if "email" in new_payload:
                new_payload["email"] = "[REDACTED]"
            if "full_name" in new_payload:
                new_payload["full_name"] = "[REDACTED]"
            audit.metadata_payload = new_payload
            db.add(audit)
            
    # Delete PHI and PII records
    # Imports for all tables
    from app.models.support import SupportTicket
    from app.models.push_token import PushToken
    from app.models.refresh_token import RefreshToken
    from app.models.password_reset_token import PasswordResetToken
    from app.models.mfa_challenge import MFAChallenge
    from app.models.privacy import PrivacyDataRequest
    from app.models.admin import AdminRoleAssignment, SensitiveAccessGrant
    from app.models.medication_schedule import MedicationSchedule
    from app.models.chat_safety import ChatSafetyEvent
    
    await db.execute(delete(Report).where(Report.user_id == target_user.id))
    await db.execute(delete(MedicalProfile).where(MedicalProfile.user_id == target_user.id))
    await db.execute(delete(DoctorProfile).where(DoctorProfile.user_id == target_user.id))
    await db.execute(delete(CaregiverProfile).where(CaregiverProfile.user_id == target_user.id))
    await db.execute(delete(ChatSession).where(ChatSession.user_id == target_user.id))
    await db.execute(delete(NotificationLog).where(NotificationLog.user_id == target_user.id))
    await db.execute(delete(SupportTicket).where(SupportTicket.user_id == target_user.id))
    await db.execute(delete(PushToken).where(PushToken.user_id == target_user.id))
    await db.execute(delete(RefreshToken).where(RefreshToken.user_id == target_user.id))
    await db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == target_user.id))
    await db.execute(delete(MFAChallenge).where(MFAChallenge.user_id == target_user.id))
    await db.execute(delete(PrivacyDataRequest).where(PrivacyDataRequest.user_id == target_user.id))
    await db.execute(delete(AdminRoleAssignment).where(AdminRoleAssignment.user_id == target_user.id))
    await db.execute(delete(SensitiveAccessGrant).where(SensitiveAccessGrant.admin_id == target_user.id))
    await db.execute(delete(MedicationSchedule).where(MedicationSchedule.user_id == target_user.id))
    await db.execute(delete(ChatSafetyEvent).where(ChatSafetyEvent.user_id == target_user.id.hex))
    
    # Anonymize User Record
    target_user.full_name = "[DELETED]"
    target_user.email = f"deleted_{uuid.uuid4()}@example.com"
    target_user.hashed_password = ""
    target_user.is_active = False
    target_user.date_of_birth = None
    target_user.gender = None
    target_user.mfa_enabled = False
    target_user.mfa_secret = None
    target_user.mfa_recovery_codes = None
    db.add(target_user)
    
    # Delete physical files
    for fp in file_paths:
        if fp and fp.startswith(f"{target_user.id}/") and ".." not in fp:
            try:
                await delete_file(fp)
            except PermissionError:
                from app.models.orphan_file import OrphanFile
                db.add(OrphanFile(file_path=fp, last_error_code="permission_error", status="pending"))
            except FileNotFoundError:
                pass
            except Exception:
                from app.models.orphan_file import OrphanFile
                db.add(OrphanFile(file_path=fp, last_error_code="unknown", status="pending"))
