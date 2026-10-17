import base64
import hashlib

from cryptography.fernet import Fernet, MultiFernet

from app.core.config import settings


def _jwt_derived_key() -> bytes:
    """Legacy key: derived from JWT_SECRET (kept so existing data stays readable)."""
    key_bytes = hashlib.sha256(settings.JWT_SECRET.encode()).digest()
    return base64.urlsafe_b64encode(key_bytes)


def _configured_keys() -> list[bytes]:
    keys: list[bytes] = []
    if settings.ENCRYPTION_KEY:
        keys.append(settings.ENCRYPTION_KEY.strip().encode())
    for previous in (settings.ENCRYPTION_KEY_PREVIOUS or "").split(","):
        previous = previous.strip()
        if previous:
            keys.append(previous.encode())
    # Always keep the JWT-derived key as the last decrypt-only candidate. When
    # no ENCRYPTION_KEY is configured it is also the (only) encryption key.
    keys.append(_jwt_derived_key())
    return keys


def get_fernet() -> MultiFernet:
    """Encrypt with the first key, decrypt with any configured key.

    Rotating JWT_SECRET no longer bricks stored MFA secrets / AI keys once
    ENCRYPTION_KEY is set (move the old JWT-derived data by re-saving it).
    """
    return MultiFernet([Fernet(k) for k in _configured_keys()])


def encrypt_value(value: str) -> str:
    """Encrypt a string value using Fernet."""
    if not value:
        return value
    f = get_fernet()
    return f.encrypt(value.encode()).decode()


def decrypt_value(encrypted_value: str) -> str:
    """Decrypt a string value using Fernet. Returns original if not encrypted (legacy migration)."""
    if not encrypted_value:
        return encrypted_value
    try:
        f = get_fernet()
        return f.decrypt(encrypted_value.encode()).decode()
    except Exception as e:
        # Fallback for unencrypted legacy keys during migration
        # Fernet tokens start with "gAAAAA". If it looks encrypted but fails, fail safely.
        if encrypted_value.startswith("gAAAAA"):
            raise ValueError("Failed to decrypt sensitive value. Invalid key or corrupted data.") from e
        return encrypted_value
