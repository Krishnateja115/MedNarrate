import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, timedelta, date
import uuid
import os
import json

from app.models.user import User, UserRole
from app.models.report import Report
from app.models.report_analysis import ReportAnalysis
from app.models.report_translation import ReportTranslation
from app.models.analysis_translation import AnalysisTranslation
from app.models.chat import ChatSession, ChatMessage
from app.models.chat_safety import ChatSafetyEvent
from app.models.support import SupportTicket, SupportTicketMessage
from app.models.notification_log import NotificationLog
from app.models.admin import AdminAuditLog, AdminRoleAssignment, AdminRole
from app.models.admin import SensitiveAccessGrant
from app.models.medical_profile import MedicalProfile
from app.models.doctor_profile import DoctorProfile
from app.models.caregiver_profile import CaregiverProfile
from app.models.medication_schedule import MedicationSchedule
from app.models.push_token import PushToken
from app.models.refresh_token import RefreshToken
from app.models.password_reset_token import PasswordResetToken
from app.models.mfa_challenge import MFAChallenge
from app.models.privacy import PrivacyDataRequest
from app.models.rag_chunk import RagChunk
from app.core.security import create_step_up_token

@pytest.mark.asyncio
async def test_extensive_hard_delete(client: AsyncClient, db_session: AsyncSession, admin_token_and_user):
    headers, admin = admin_token_and_user

    # 1. Create target user
    target_user = User(
        email=f"target_{uuid.uuid4().hex[:6]}@example.com",
        hashed_password="pw",
        full_name="Target Extensive",
        role=UserRole.patient
    )
    db_session.add(target_user)

    # 2. Create unrelated user
    unrelated_user = User(
        email=f"unrelated_{uuid.uuid4().hex[:6]}@example.com",
        hashed_password="pw",
        full_name="Unrelated Extensive",
        role=UserRole.patient
    )
    db_session.add(unrelated_user)
    
    admin_role = AdminRole(name=f"role_{uuid.uuid4().hex[:6]}")
    db_session.add(admin_role)
    await db_session.commit()

    def seed_data(user):
        rep = Report(
            user_id=user.id, file_path="fake", title="Rep", hospital="H",
            report_date=date.today(), file_name="f.pdf", file_type="pdf", report_type="blood", processing_status="completed"
        )
        db_session.add(rep)
        chat = ChatSession(user_id=user.id, title="Chat")
        db_session.add(chat)
        ticket = SupportTicket(user_id=user.id.hex, title="T", description="Desc")
        db_session.add(ticket)
        notif = NotificationLog(user_id=user.id, title="N", body="B", status="sent")
        db_session.add(notif)
        audit = AdminAuditLog(actor_admin_id=user.id, action="test", resource_type="User", resource_id=str(user.id))
        db_session.add(audit)
        
        # New additions
        med_prof = MedicalProfile(user_id=user.id, blood_group="O+")
        db_session.add(med_prof)
        doc_prof = DoctorProfile(user_id=user.id, specialty="Cardiology", license_number="123")
        db_session.add(doc_prof)
        cg_prof = CaregiverProfile(user_id=user.id, relationship="Parent")
        db_session.add(cg_prof)
        push = PushToken(user_id=user.id, device_token=f"tok_{user.id.hex}", platform="ios")
        db_session.add(push)
        ref_tok = RefreshToken(user_id=user.id, token_hash=f"rt_{user.id.hex}", expires_at=datetime.now(timezone.utc) + timedelta(days=1))
        db_session.add(ref_tok)
        pr_tok = PasswordResetToken(user_id=user.id, token_hash=f"pr_{user.id.hex}", expires_at=datetime.now(timezone.utc) + timedelta(hours=1))
        db_session.add(pr_tok)
        mfa_chal = MFAChallenge(user_id=user.id, jti=f"jti_{uuid.uuid4().hex}", expires_at=datetime.now(timezone.utc) + timedelta(hours=1))
        db_session.add(mfa_chal)
        priv_req = PrivacyDataRequest(user_id=user.id, request_type="deletion", reason="test")
        db_session.add(priv_req)
        role_ass = AdminRoleAssignment(user_id=user.id, role_id=admin_role.id)
        db_session.add(role_ass)
        grant = SensitiveAccessGrant(admin_id=user.id, resource_type="medical_report", resource_id="fake", reason="test", status="active", expires_at=datetime.now(timezone.utc) + timedelta(hours=1))
        db_session.add(grant)
        
        return rep, chat, ticket, audit

    tr_rep, tr_chat, tr_ticket, tr_audit = seed_data(target_user)
    ur_rep, ur_chat, ur_ticket, ur_audit = seed_data(unrelated_user)
    await db_session.commit()

    def seed_indirect(rep, chat, ticket, user_id):
        analysis = ReportAnalysis(report_id=rep.id, clinician_summary="Analysis")
        db_session.add(analysis)
        translation = ReportTranslation(report_id=rep.id, language_code="es", translated_text="Trans")
        db_session.add(translation)
        chat_msg = ChatMessage(chat_session_id=chat.id, role="user", content="Hello")
        db_session.add(chat_msg)
        ticket_msg = SupportTicketMessage(ticket_id=ticket.id, sender_id=user_id.hex, content="Help")
        db_session.add(ticket_msg)
        med_sch = MedicationSchedule(report_id=rep.id, user_id=user_id, medication_name="A", dosage="10mg", frequency="daily", times_of_day=[])
        db_session.add(med_sch)
        safety_evt = ChatSafetyEvent(chat_session_id=chat.id.hex, user_id=user_id.hex, classification="hate", action_taken="blocked")
        db_session.add(safety_evt)
        chunk = RagChunk(report_id=rep.id, chunk_text="test", chunk_index=1, embedding_json=[0.1])
        db_session.add(chunk)
        return analysis, translation, chat_msg, ticket_msg

    tr_analysis, tr_translation, tr_chat_msg, tr_ticket_msg = seed_indirect(tr_rep, tr_chat, tr_ticket, target_user.id)
    ur_analysis, ur_translation, ur_chat_msg, ur_ticket_msg = seed_indirect(ur_rep, ur_chat, ur_ticket, unrelated_user.id)
    await db_session.commit()

    tr_a_trans = AnalysisTranslation(report_analysis_id=tr_analysis.id, language="es", patient_summary="es")
    db_session.add(tr_a_trans)
    ur_a_trans = AnalysisTranslation(report_analysis_id=ur_analysis.id, language="es", patient_summary="es")
    db_session.add(ur_a_trans)
    await db_session.commit()

    step_up = create_step_up_token(str(admin.id), admin.session_version)
    headers["x-step-up-token"] = step_up

    resp = await client.request(
        "DELETE", f"/api/v1/admin/users/{target_user.id}",
        headers=headers,
        json={"reason": "test", "confirmation": f"DELETE {target_user.id}"}
    )
    assert resp.status_code == 200, resp.text

    # Verify Target Direct
    assert (await db_session.execute(select(User).where(User.id == target_user.id))).scalar() is None
    assert (await db_session.execute(select(Report).where(Report.user_id == target_user.id))).scalar() is None
    assert (await db_session.execute(select(ChatSession).where(ChatSession.user_id == target_user.id))).scalar() is None
    assert (await db_session.execute(select(SupportTicket).where(SupportTicket.user_id == target_user.id))).scalar() is None
    assert (await db_session.execute(select(MedicalProfile).where(MedicalProfile.user_id == target_user.id))).scalar() is None
    assert (await db_session.execute(select(DoctorProfile).where(DoctorProfile.user_id == target_user.id))).scalar() is None
    assert (await db_session.execute(select(CaregiverProfile).where(CaregiverProfile.user_id == target_user.id))).scalar() is None
    assert (await db_session.execute(select(PushToken).where(PushToken.user_id == target_user.id))).scalar() is None
    assert (await db_session.execute(select(RefreshToken).where(RefreshToken.user_id == target_user.id))).scalar() is None
    assert (await db_session.execute(select(PasswordResetToken).where(PasswordResetToken.user_id == target_user.id))).scalar() is None
    assert (await db_session.execute(select(MFAChallenge).where(MFAChallenge.user_id == target_user.id))).scalar() is None
    assert (await db_session.execute(select(PrivacyDataRequest).where(PrivacyDataRequest.user_id == target_user.id))).scalar() is None
    assert (await db_session.execute(select(AdminRoleAssignment).where(AdminRoleAssignment.user_id == target_user.id))).scalar() is None
    assert (await db_session.execute(select(SensitiveAccessGrant).where(SensitiveAccessGrant.admin_id == target_user.id))).scalar() is None

    # Verify Target Indirect
    assert (await db_session.execute(select(ReportAnalysis).where(ReportAnalysis.report_id == tr_rep.id))).scalar() is None
    assert (await db_session.execute(select(ReportTranslation).where(ReportTranslation.report_id == tr_rep.id))).scalar() is None
    assert (await db_session.execute(select(AnalysisTranslation).where(AnalysisTranslation.report_analysis_id == tr_analysis.id))).scalar() is None
    assert (await db_session.execute(select(ChatMessage).where(ChatMessage.chat_session_id == tr_chat.id))).scalar() is None
    assert (await db_session.execute(select(SupportTicketMessage).where(SupportTicketMessage.ticket_id == tr_ticket.id))).scalar() is None
    assert (await db_session.execute(select(MedicationSchedule).where(MedicationSchedule.user_id == target_user.id))).scalar() is None
    assert (await db_session.execute(select(ChatSafetyEvent).where(ChatSafetyEvent.user_id == target_user.id.hex))).scalar() is None
    assert (await db_session.execute(select(RagChunk).where(RagChunk.report_id == tr_rep.id))).scalar() is None

    # Verify Audit (Retained but anonymized/nullified)
    t_audit = (await db_session.execute(select(AdminAuditLog).where(AdminAuditLog.id == tr_audit.id))).scalar()
    assert t_audit is not None
    await db_session.refresh(t_audit)
    assert t_audit.actor_admin_id is None # SET NULL

    # Verify Unrelated Unchanged
    assert (await db_session.execute(select(User).where(User.id == unrelated_user.id))).scalar() is not None
    assert (await db_session.execute(select(Report).where(Report.user_id == unrelated_user.id))).scalar() is not None
    assert (await db_session.execute(select(ReportAnalysis).where(ReportAnalysis.report_id == ur_rep.id))).scalar() is not None
    assert (await db_session.execute(select(AnalysisTranslation).where(AnalysisTranslation.id == ur_a_trans.id))).scalar() is not None
