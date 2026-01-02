"""
Encryption (PII & Field-Level)
==============================

Fernet-based encryption for personally identifiable information
and sensitive field data.

See: .github/instructions/22-QUALITY_CONTROL.instructions.md for modularization standards
"""

import base64
import hashlib
import logging
from typing import Any

from cryptography.fernet import Fernet

from core.config import settings

logger = logging.getLogger(__name__)


def get_fernet_key() -> Fernet:
    """Get encryption key for PII data"""
    key = settings.ENCRYPTION_KEY.encode()
    if len(key) != 44:  # Fernet key must be 32 bytes base64 encoded (44 chars)
        hashed = hashlib.sha256(key).digest()
        key = base64.urlsafe_b64encode(hashed)
    return Fernet(key)


# Global Fernet instance
fernet = get_fernet_key()


def encrypt_pii(data: str) -> str:
    """Encrypt personally identifiable information"""
    if not data:
        return ""

    try:
        encrypted = fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    except Exception as e:
        raise ValueError(f"Encryption failed: {e}")


def decrypt_pii(encrypted_data: str) -> str:
    """Decrypt personally identifiable information"""
    if not encrypted_data:
        return ""

    try:
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted = fernet.decrypt(encrypted_bytes)
        return decrypted.decode()
    except Exception as e:
        raise ValueError(f"Decryption failed: {e}")


class FieldEncryption:
    """Field-level encryption for sensitive data"""

    def __init__(self, key: str | None = None):
        if key:
            self.key = base64.urlsafe_b64decode(key.encode())
        else:
            self.key = Fernet.generate_key()
        self.fernet = Fernet(self.key)

    def encrypt(self, data: str) -> str:
        """Encrypt sensitive field data"""
        if not data:
            return data
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive field data"""
        if not encrypted_data:
            return encrypted_data
        return self.fernet.decrypt(encrypted_data.encode()).decode()

    def encrypt_dict(self, data: dict[str, Any], fields: list[str]) -> dict[str, Any]:
        """Encrypt specific fields in a dictionary"""
        result = data.copy()
        for field in fields:
            if result.get(field):
                result[field] = self.encrypt(str(result[field]))
        return result

    def decrypt_dict(self, data: dict[str, Any], fields: list[str]) -> dict[str, Any]:
        """Decrypt specific fields in a dictionary"""
        result = data.copy()
        for field in fields:
            if result.get(field):
                result[field] = self.decrypt(result[field])
        return result


# Global field encryption instance
field_encryption = FieldEncryption(
    settings.field_encryption_key if hasattr(settings, "field_encryption_key") else None
)


__all__ = [
    "get_fernet_key",
    "fernet",
    "encrypt_pii",
    "decrypt_pii",
    "FieldEncryption",
    "field_encryption",
]
