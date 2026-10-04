import pytest
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User, UserRole
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.mfa_challenge import MFAChallenge
from app.tasks.maintenance import run_data_retention_cleanup

@pytest.mark.asyncio
async def test_data_retention_cleanup(db_session: AsyncSession):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    
    # 1. Setup User
    active_user = User(
        email="active@example.com",
        hashed_password="hash",
        full_name="Active",
        is_active=True,
        created_at=now - timedelta(days=10)
    )
    unverified_old_user = User(
        email="old_unverified@example.com",
        hashed_password="hash",
        full_name="Old",
        is_active=False,
        created_at=now - timedelta(days=8)
    )
    unverified_new_user = User(
        email="new_unverified@example.com",
        hashed_password="hash",
        full_name="New",
        is_active=False,
        created_at=now - timedelta(days=2)
    )
    db_session.add_all([active_user, unverified_old_user, unverified_new_user])
    await db_session.commit()
    
    # 2. Setup Tokens
    valid_prt = PasswordResetToken(
        user_id=active_user.id,
        token_hash="hash1",
        expires_at=now + timedelta(hours=1),
        used=False
    )
    expired_prt = PasswordResetToken(
        user_id=active_user.id,
        token_hash="hash2",
        expires_at=now - timedelta(hours=1),
        used=False
    )
    used_prt = PasswordResetToken(
        user_id=active_user.id,
        token_hash="hash3",
        expires_at=now + timedelta(hours=1),
        used=True
    )
    
    valid_rt = RefreshToken(
        user_id=active_user.id,
        token_hash="rt1",
        expires_at=now + timedelta(days=1),
        revoked=False
    )
    expired_rt = RefreshToken(
        user_id=active_user.id,
        token_hash="rt2",
        expires_at=now - timedelta(hours=1),
        revoked=False
    )
    revoked_rt = RefreshToken(
        user_id=active_user.id,
        token_hash="rt3",
        expires_at=now + timedelta(days=1),
        revoked=True
    )
    
    valid_mfa = MFAChallenge(
        jti="mfa1",
        user_id=active_user.id,
        expires_at=now + timedelta(minutes=5)
    )
    expired_mfa = MFAChallenge(
        jti="mfa2",
        user_id=active_user.id,
        expires_at=now - timedelta(minutes=5)
    )
    used_mfa = MFAChallenge(
        jti="mfa3",
        user_id=active_user.id,
        expires_at=now + timedelta(minutes=5),
        used_at=now - timedelta(minutes=1)
    )
    
    db_session.add_all([
        valid_prt, expired_prt, used_prt,
        valid_rt, expired_rt, revoked_rt,
        valid_mfa, expired_mfa, used_mfa
    ])
    await db_session.commit()
    
    # 3. Run Cleanup
    metrics = await run_data_retention_cleanup(db_session)
    
    assert metrics["password_reset_tokens_deleted"] == 2
    assert metrics["refresh_tokens_deleted"] == 2
    assert metrics["mfa_challenges_deleted"] == 2
    assert metrics["inactive_users_deleted"] == 1
    
    # 4. Verify State
    users = (await db_session.execute(select(User))).scalars().all()
    user_emails = [u.email for u in users]
    assert "active@example.com" in user_emails
    assert "new_unverified@example.com" in user_emails
    assert "old_unverified@example.com" not in user_emails
    
    prts = (await db_session.execute(select(PasswordResetToken))).scalars().all()
    assert len(prts) == 1
    assert prts[0].token_hash == "hash1"
    
    rts = (await db_session.execute(select(RefreshToken))).scalars().all()
    assert len(rts) == 1
    assert rts[0].token_hash == "rt1"
    
    mfas = (await db_session.execute(select(MFAChallenge))).scalars().all()
    assert len(mfas) == 1
    assert mfas[0].jti == "mfa1"
