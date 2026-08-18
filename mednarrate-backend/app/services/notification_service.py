import firebase_admin
from firebase_admin import credentials, messaging
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notification_log import NotificationLog

logger = logging.getLogger(__name__)

# Initialize FCM globally
try:
    if not firebase_admin._apps:
        from app.core.config import settings
        import os
        cred_path = settings.GOOGLE_APPLICATION_CREDENTIALS or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin initialized with credentials.")
        else:
            logger.info("Firebase Admin initialized (mocked for dev as no credentials exist).")
except Exception as e:
    logger.error(f"Failed to initialize Firebase Admin: {e}")

async def send_push_notification(db: AsyncSession, user_id: str, token: str, title: str, body: str):
    """Sends a push notification via FCM and logs it."""
    status = "sent"
    error_message = None
    
    try:
        if firebase_admin._apps:
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                token=token,
            )
            response = messaging.send(message)
            logger.info(f"Successfully sent message: {response}")
        else:
            logger.info(f"[MOCK FCM - No App] Sent to {token}: {title} - {body}")
    except Exception as e:
        status = "failed"
        error_message = str(e)
        logger.error(f"Error sending push notification to {token}: {e}")
        
    # Log it
    log = NotificationLog(
        user_id=user_id,
        title=title,
        body=body,
        status=status,
        error_message=error_message
    )
    db.add(log)
    await db.commit()
    return status == "sent"
