"""Symmetric encryption helpers for sensitive fields.

The database stores integration tokens, webhook secrets, and SSO client
secrets. They must never be stored in plaintext once the API layer starts
writing them — encrypt at rest with this helper (AES-128-CBC via Fernet)
using the app's ENCRYPTION_KEY.

Usage:
    from app.utils.encryption import encrypt_value, decrypt_value

    row.access_token = encrypt_value(token)   # before commit
    token = decrypt_value(row.access_token)   # when calling the provider
"""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def _fernet() -> Fernet:
    """Build a Fernet cipher from ENCRYPTION_KEY (falls back to the JWT secret).

    A stable 32-byte key is derived via SHA-256, so existing ciphertexts
    survive key rotation only if ENCRYPTION_KEY itself is preserved.
    """
    secret = settings.ENCRYPTION_KEY or settings.JWT_SECRET_KEY
    if not secret:
        raise RuntimeError(
            "ENCRYPTION_KEY (or JWT_SECRET_KEY) must be configured "
            "before encrypting sensitive values"
        )
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
    return Fernet(key)


def encrypt_value(value: str | None) -> str | None:
    """Encrypt a sensitive string for storage. None/empty pass through."""
    if not value:
        return value
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_value(value: str | None) -> str | None:
    """Decrypt a stored value. Plaintext legacy values pass through."""
    if not value:
        return value
    try:
        return _fernet().decrypt(value.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError):
        # Legacy rows written before encryption was enabled.
        return value
