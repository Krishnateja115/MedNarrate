import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete

from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.mfa_challenge import MFAChallenge
from app.models.user import User

logger = logging.getLogger(__name__)

async def run_data_retention_cleanup(db: AsyncSession) -> dict:
    """
    Cleans up expired transient tokens and unverified/inactive users
    to enforce data retention timeouts and minimize data exposure.
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    metrics = {
        "password_reset_tokens_deleted": 0,
        "refresh_tokens_deleted": 0,
        "mfa_challenges_deleted": 0,
        "inactive_users_deleted": 0
    }

    try:
        # 1. Prune expired or used password reset tokens (older than 24h)
        # Even if they are valid for 24h, we aggressively delete them once expired or used.
        stmt = delete(PasswordResetToken).where(
            (PasswordResetToken.expires_at < now) | (PasswordResetToken.used == True)
        )
        res = await db.execute(stmt)
        metrics["password_reset_tokens_deleted"] = res.rowcount

        # 2. Prune expired or revoked refresh tokens
        stmt = delete(RefreshToken).where(
            (RefreshToken.expires_at < now) | (RefreshToken.revoked == True)
        )
        res = await db.execute(stmt)
        metrics["refresh_tokens_deleted"] = res.rowcount

        # 3. Prune expired MFA challenges
        stmt = delete(MFAChallenge).where(
            (MFAChallenge.expires_at < now) | (MFAChallenge.used_at.is_not(None))
        )
        res = await db.execute(stmt)
        metrics["mfa_challenges_deleted"] = res.rowcount

        # 4. Prune unverified/inactive users older than 7 days
        # Assuming is_active=False represents unverified or disabled users
        seven_days_ago = now - timedelta(days=7)
        stmt = delete(User).where(
            (User.is_active == False) & (User.created_at < seven_days_ago)
        )
        res = await db.execute(stmt)
        metrics["inactive_users_deleted"] = res.rowcount

        await db.commit()
        logger.info(f"Data retention cleanup completed: {metrics}")
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error during data retention cleanup: {e}")
        raise e

    return metrics
