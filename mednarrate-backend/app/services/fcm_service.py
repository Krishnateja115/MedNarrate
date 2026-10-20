import json
import logging
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, messaging

from app.core.config import settings

logger = logging.getLogger(__name__)

BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _load_service_account(value: str) -> dict:
    """FIREBASE_SERVICE_ACCOUNT_JSON may hold the JSON itself or a path to the key file."""
    text = value.strip()
    if text.startswith("{"):
        return json.loads(text)
    path = Path(text).expanduser()
    if not path.is_absolute():
        path = BACKEND_ROOT / path
    if not path.is_file():
        raise FileNotFoundError(f"service account file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


# Initialize Firebase app if configured
if settings.FIREBASE_SERVICE_ACCOUNT_JSON:
    try:
        cred = credentials.Certificate(_load_service_account(settings.FIREBASE_SERVICE_ACCOUNT_JSON))
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized successfully.")
    except Exception as e:
        logger.error(
            "Push notifications are OFF: could not load FIREBASE_SERVICE_ACCOUNT_JSON (%s: %s). "
            "Set it to the service-account JSON text or a path to that file, or leave it empty.",
            type(e).__name__,
            e,
        )


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
