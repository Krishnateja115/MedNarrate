import firebase_admin
from firebase_admin import credentials, messaging
from app.core.config import settings
import logging
import json

logger = logging.getLogger(__name__)

# Initialize Firebase app if configured
if settings.FIREBASE_SERVICE_ACCOUNT_JSON:
    try:
        # Load from string representation
        cert_dict = json.loads(settings.FIREBASE_SERVICE_ACCOUNT_JSON)
        cred = credentials.Certificate(cert_dict)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {e}")

async def send_push_notification(token: str, title: str, body: str, data: dict = None):
    if not token:
        logger.warning("Attempted to send notification without a token.")
        return False
        
    if not settings.FIREBASE_SERVICE_ACCOUNT_JSON:
        logger.info(f"Firebase not configured. Mock sending notification to {token}: {title} - {body}")
        return True

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            token=token,
        )
        response = messaging.send(message)
        logger.info(f"Successfully sent message: {response}")
        return True
    except Exception as e:
        logger.error(f"Error sending message to {token}: {e}")
        return False
