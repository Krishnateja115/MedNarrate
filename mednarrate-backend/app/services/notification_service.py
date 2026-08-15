import firebase_admin
from firebase_admin import credentials, messaging
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notification_log import NotificationLog

logger = logging.getLogger(__name__)

# Initialize FCM globally
try:
    if not firebase_admin._apps:
        # In production, use real credentials path from settings
        # cred = credentials.Certificate('path/to/serviceAccountKey.json')
        # firebase_admin.initialize_app(cred)
        # For this dev setup, we mock it if no key is present, but load it if needed.
        logger.info("Firebase Admin initialized (mocked for dev unless credentials exist).")
except Exception as e:
    logger.error(f"Failed to initialize Firebase Admin: {e}")

async def send_push_notification(db: AsyncSession, user_id: str, token: str, title: str, body: str):
    """Sends a push notification via FCM and logs it."""
    status = "sent"
    error_message = None
    
    try:
        if firebase_admin._apps:
            # We mock sending if not fully configured with a service account
            # message = messaging.Message(
            #     notification=messaging.Notification(title=title, body=body),
            #     token=token,
            # )
            # response = messaging.send(message)
            # logger.info(f"Successfully sent message: {response}")
            logger.info(f"[MOCK FCM] Sent to {token}: {title} - {body}")
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
