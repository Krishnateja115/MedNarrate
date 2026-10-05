import json
import logging

import firebase_admin
from firebase_admin import credentials, messaging

from app.core.config import settings

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

    masked = f"{token[:6]}…" if len(token) > 6 else "***"
    if not settings.FIREBASE_SERVICE_ACCOUNT_JSON:
        # A development response must not claim delivery when no provider exists.
        # Callers can still exercise the complete failure/logging path locally.
        logger.error("Firebase is not configured; notification to %s NOT sent.", masked)
        return False

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
        logger.error("Error sending message to %s: %s", masked, type(e).__name__)
        return False
