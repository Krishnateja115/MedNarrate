import base64
import hashlib
from cryptography.fernet import Fernet
from app.core.config import settings

def get_fernet() -> Fernet:
    """Derive a 32-byte url-safe base64 key from JWT_SECRET."""
    key_bytes = hashlib.sha256(settings.JWT_SECRET.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)

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
    except Exception:
        # Fallback for unencrypted legacy keys during migration
        return encrypted_value
