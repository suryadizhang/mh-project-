"""
Field-level encryption for PII data (Customer emails, phones, addresses)

Industry Best Practices:
- Uses Fernet (symmetric encryption) from cryptography library
- Key rotation support via versioned keys
- Idempotent encryption (detects already-encrypted data)
- Backward compatibility for migration period

Environment Variables:
- FIELD_ENCRYPTION_KEY: Primary Fernet key (required)
- FIELD_ENCRYPTION_KEY_OLD: Previous key for rotation (optional)

Key Generation:
```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(f"FIELD_ENCRYPTION_KEY={key.decode()}")
```

Usage:
```python
from core.encryption import encrypt_field, decrypt_field

# In model @property
@property
def email(self) -> str:
    return decrypt_field(self.email_encrypted)

@email.setter
def email(self, value: str):
    self.email_encrypted = encrypt_field(value)
```
"""

import logging
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from core.config import get_settings

logger = logging.getLogger(__name__)


class EncryptionError(Exception):
    """Raised when encryption/decryption fails"""
    pass


def _get_fernet() -> Optional[Fernet]:
    """Get Fernet cipher with primary key"""
    settings = get_settings()

    if not settings.FIELD_ENCRYPTION_KEY:
        # For backward compatibility during migration:
        # If key not set, log warning but don't encrypt (passthrough mode)
        logger.warning(
            "FIELD_ENCRYPTION_KEY not configured. Running in passthrough mode (no encryption). "
            "Generate key with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )
        return None

    try:
        return Fernet(settings.FIELD_ENCRYPTION_KEY.encode())
    except Exception as e:
        raise EncryptionError(f"Invalid FIELD_ENCRYPTION_KEY: {e}")


def _get_fernet_old() -> Optional[Fernet]:
    """Get Fernet cipher with old key for rotation"""
    settings = get_settings()

    if not settings.FIELD_ENCRYPTION_KEY_OLD:
        return None

    try:
        return Fernet(settings.FIELD_ENCRYPTION_KEY_OLD.encode())
    except Exception as e:
        logger.warning(f"Invalid FIELD_ENCRYPTION_KEY_OLD: {e}")
        return None


def encrypt_field(value: str) -> str:
    """
    Encrypt a string field value

    Args:
        value: Plaintext string to encrypt

    Returns:
        Encrypted string (base64 encoded Fernet token)

    Notes:
        - Idempotent: If value looks encrypted, returns as-is
        - Safe to call multiple times on same value
        - Returns empty string if value is None or empty
        - PASSTHROUGH MODE: If FIELD_ENCRYPTION_KEY not set, returns plaintext (for migration)
    """
    if not value:
        return ""

    # Idempotency check: If already encrypted (Fernet tokens start with 'gAAAAA')
    if isinstance(value, str) and value.startswith("gAAAAA"):
        logger.debug("Value appears already encrypted, skipping encryption")
        return value

    try:
        fernet = _get_fernet()

        # Passthrough mode (no key configured)
        if fernet is None:
            logger.debug("PASSTHROUGH MODE: Returning plaintext (no encryption key)")
            return value

        encrypted_bytes = fernet.encrypt(value.encode('utf-8'))
        return encrypted_bytes.decode('utf-8')
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise EncryptionError(f"Failed to encrypt field: {e}")


def decrypt_field(encrypted_value: str) -> str:
    """
    Decrypt an encrypted string field value

    Args:
        encrypted_value: Encrypted string (base64 encoded Fernet token)

    Returns:
        Decrypted plaintext string

    Notes:
        - Tries primary key first, falls back to old key if configured
        - Returns empty string if encrypted_value is None or empty
        - PASSTHROUGH MODE: If FIELD_ENCRYPTION_KEY not set, returns value as-is
        - Raises EncryptionError if decryption fails with both keys
    """
    if not encrypted_value:
        return ""

    # Check if value looks unencrypted (passthrough or plain text)
    if not encrypted_value.startswith("gAAAAA"):
        logger.debug("Value doesn't look encrypted, returning as-is")
        return encrypted_value

    # Try primary key first
    fernet = _get_fernet()

    # Passthrough mode (no key configured)
    if fernet is None:
        logger.debug("PASSTHROUGH MODE: Returning value as-is (no decryption key)")
        return encrypted_value

    try:
        decrypted_bytes = fernet.decrypt(encrypted_value.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
    except InvalidToken:
        # Try old key if configured (for key rotation)
        fernet_old = _get_fernet_old()
        if fernet_old:
            try:
                decrypted_bytes = fernet_old.decrypt(encrypted_value.encode('utf-8'))
                logger.info("Decrypted with old key - consider re-encrypting with new key")
                return decrypted_bytes.decode('utf-8')
            except InvalidToken:
                pass

        # If both keys fail, raise error
        logger.error("Decryption failed with both primary and old keys")
        raise EncryptionError("Failed to decrypt field: Invalid token or key")
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise EncryptionError(f"Failed to decrypt field: {e}")


def is_encrypted(value: str) -> bool:
    """
    Check if a value appears to be encrypted

    Args:
        value: String to check

    Returns:
        True if value looks like a Fernet token, False otherwise

    Notes:
        - Heuristic check: Fernet tokens start with 'gAAAAA'
        - Not 100% accurate but good for migration detection
    """
    if not value or not isinstance(value, str):
        return False

    # Fernet tokens are base64 encoded and start with specific bytes
    # After base64 encoding, they start with 'gAAAAA'
    return value.startswith("gAAAAA")


# Convenience functions for common patterns

def encrypt_email(email: str) -> str:
    """Encrypt email address"""
    return encrypt_field(email.lower().strip()) if email else ""


def decrypt_email(encrypted_email: str) -> str:
    """Decrypt email address"""
    return decrypt_field(encrypted_email).lower().strip() if encrypted_email else ""


def encrypt_phone(phone: str) -> str:
    """Encrypt phone number"""
    # Normalize phone (remove spaces, dashes, etc.) before encryption
    normalized = ''.join(c for c in phone if c.isdigit() or c == '+')
    return encrypt_field(normalized) if normalized else ""


def decrypt_phone(encrypted_phone: str) -> str:
    """Decrypt phone number"""
    return decrypt_field(encrypted_phone) if encrypted_phone else ""
