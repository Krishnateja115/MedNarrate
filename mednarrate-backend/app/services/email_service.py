"""Transactional e-mail delivery (password reset, etc.).

Providers (``EMAIL_PROVIDER``):
  * ``sendgrid`` - SendGrid v3 REST API (needs ``SENDGRID_API_KEY``)
  * ``smtp``     - any SMTP server (``SMTP_HOST`` / ``SMTP_PORT`` / ...)
  * ``log``      - development fallback; the message is written to the server
                   log and NOTHING is sent. Never use in production.

Sending never raises into request handlers: failures are logged and reported
through the boolean return value so account-enumeration protections in the
callers (always the same HTTP response) stay intact.
"""

from __future__ import annotations

import asyncio
import logging
import smtplib
import ssl
from email.message import EmailMessage

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

SENDGRID_URL = "https://api.sendgrid.com/v3/mail/send"


def _provider() -> str:
    return (settings.EMAIL_PROVIDER or "log").strip().lower()


async def _send_sendgrid(to: str, subject: str, text: str) -> bool:
    payload = {
        "personalizations": [{"to": [{"email": to}]}],
        "from": {"email": settings.EMAIL_FROM, "name": settings.EMAIL_FROM_NAME},
        "subject": subject,
        "content": [{"type": "text/plain", "value": text}],
    }
    async with httpx.AsyncClient(timeout=settings.EMAIL_TIMEOUT_SECONDS) as client:
        resp = await client.post(
            SENDGRID_URL,
            json=payload,
            headers={"Authorization": f"Bearer {settings.SENDGRID_API_KEY}"},
        )
    if resp.status_code >= 300:
        logger.error("SendGrid rejected e-mail (status=%s)", resp.status_code)
        return False
    return True


def _send_smtp_blocking(to: str, subject: str, text: str) -> None:
    msg = EmailMessage()
    msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(text)
    host, port = settings.SMTP_HOST, settings.SMTP_PORT
    if settings.SMTP_USE_SSL:
        smtp = smtplib.SMTP_SSL(
            host, port, timeout=settings.EMAIL_TIMEOUT_SECONDS,
            context=ssl.create_default_context(),
        )
    else:
        smtp = smtplib.SMTP(host, port, timeout=settings.EMAIL_TIMEOUT_SECONDS)
    with smtp:
        if settings.SMTP_USE_TLS and not settings.SMTP_USE_SSL:
            smtp.starttls(context=ssl.create_default_context())
        if settings.SMTP_USERNAME:
            smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD or "")
        smtp.send_message(msg)


async def send_email(to: str, subject: str, text: str) -> bool:
    """Send a plain-text e-mail. Returns True on success, never raises."""
    provider = _provider()
    try:
        if provider == "sendgrid":
            if not settings.SENDGRID_API_KEY:
                logger.error("EMAIL_PROVIDER=sendgrid but SENDGRID_API_KEY is unset")
                return False
            return await _send_sendgrid(to, subject, text)
        if provider == "smtp":
            if not settings.SMTP_HOST:
                logger.error("EMAIL_PROVIDER=smtp but SMTP_HOST is unset")
                return False
            await asyncio.to_thread(_send_smtp_blocking, to, subject, text)
            return True
        # "log" provider: development only, nothing leaves the server.
        if (settings.ENVIRONMENT or "").lower() == "production":
            logger.error(
                "E-mail NOT sent: EMAIL_PROVIDER=log is not allowed in production"
            )
            return False
        logger.warning("[DEV EMAIL - not sent] to=%s subject=%s\n%s", to, subject, text)
        return True
    except Exception as exc:  # noqa: BLE001 - delivery must never break callers
        logger.error("E-mail delivery failed: %s", type(exc).__name__)
        return False


async def send_password_reset_email(to: str, raw_token: str, ttl_minutes: int = 60) -> bool:
    subject = f"{settings.PROJECT_NAME} password reset code"
    text = (
        f"Hello,\n\n"
        f"We received a request to reset your {settings.PROJECT_NAME} password.\n"
        f"Open the app, choose \"Forgot password\" and enter this reset code:\n\n"
        f"    {raw_token}\n\n"
        f"The code is valid for {ttl_minutes} minutes and can be used once.\n"
        f"If you did not request this, you can safely ignore this e-mail; "
        f"your password will not change.\n\n"
        f"- The {settings.PROJECT_NAME} team\n"
    )
    return await send_email(to, subject, text)
