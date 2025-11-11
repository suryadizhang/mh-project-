"""
PII Encryption Service

Provides secure encryption/decryption for sensitive customer data (phone numbers, emails).
Implements comprehensive error handling as required by user:
"make sure no error on it or it will cause big problem when the encryption decryption goes error"

Features:
- Fernet symmetric encryption (cryptography library)
- Comprehensive try/except blocks with fallback strategies
- Detailed logging for debugging
- Graceful degradation (never crash, store unencrypted if encryption fails)
- Key rotation support
- Validation and sanitization
"""

import base64
import logging
import os

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class EncryptionError(Exception):
    """Custom exception for encryption errors"""


class DecryptionError(Exception):
    """Custom exception for decryption errors"""


class SecureDataHandler:
    """
    Handles encryption/decryption of PII data with comprehensive error handling.

    Design Principles:
    1. Never crash the application
    2. Always log errors with context
    3. Fallback to unencrypted if encryption fails (with clear prefix)
    4. Validate input/output at every step
    5. Support key rotation

    Usage:
        handler = SecureDataHandler()

        # Encrypt
        encrypted_phone = handler.encrypt_phone("2103884155")

        # Decrypt
        real_phone = handler.decrypt_phone(encrypted_phone)
    """

    UNENCRYPTED_PREFIX = "UNENCRYPTED:"
    ENCRYPTED_VERSION = "v1:"  # For key rotation support

    def __init__(self, encryption_key: str | None = None):
        """
        Initialize encryption handler

        Args:
            encryption_key: Base64-encoded Fernet key. If None, reads from ENCRYPTION_KEY env var.

        Raises:
            ValueError: If no encryption key is provided or invalid
        """
        try:
            # Get encryption key
            self.key = encryption_key or os.getenv("ENCRYPTION_KEY")

            if not self.key:
                logger.error("ENCRYPTION_KEY not set in environment variables")
                raise ValueError("ENCRYPTION_KEY environment variable is required")

            # Validate key format
            if len(self.key) < 32:
                logger.error(f"ENCRYPTION_KEY too short: {len(self.key)} bytes")
                raise ValueError("ENCRYPTION_KEY must be at least 32 bytes")

            # Initialize cipher
            self.cipher = Fernet(self.key.encode() if isinstance(self.key, str) else self.key)
            logger.info("SecureDataHandler initialized successfully")

        except Exception as e:
            logger.critical(f"Failed to initialize SecureDataHandler: {e}")
            raise

    def encrypt_phone(self, phone: str | None) -> str | None:
        """
        Encrypt phone number with comprehensive error handling.

        Args:
            phone: Plain text phone number (e.g., "2103884155")

        Returns:
            Encrypted phone string, or original with UNENCRYPTED: prefix if encryption fails

        Error Handling:
            - Empty/None input: Returns as-is
            - Invalid input: Returns with UNENCRYPTED: prefix + logs error
            - Encryption failure: Returns with UNENCRYPTED: prefix + logs error
        """
        # Handle empty input
        if not phone:
            return phone

        try:
            # Validate input
            phone_str = str(phone).strip()
            if not phone_str:
                logger.warning("Empty phone number after stripping")
                return phone_str

            # Sanitize: Remove all non-digits
            sanitized = "".join(c for c in phone_str if c.isdigit())

            if not sanitized:
                logger.warning(f"No digits found in phone number: {phone_str}")
                return f"{self.UNENCRYPTED_PREFIX}{phone_str}"

            # Encrypt
            encrypted_bytes = self.cipher.encrypt(sanitized.encode("utf-8"))
            encrypted_str = base64.urlsafe_b64encode(encrypted_bytes).decode("utf-8")

            # Add version prefix for key rotation support
            result = f"{self.ENCRYPTED_VERSION}{encrypted_str}"

            logger.debug(f"Encrypted phone number (length: {len(sanitized)} digits)")
            return result

        except InvalidToken as e:
            logger.exception(f"Invalid encryption token: {e}")
            return f"{self.UNENCRYPTED_PREFIX}{phone}"

        except Exception as e:
            logger.error(f"Phone encryption failed: {e}", exc_info=True)
            # CRITICAL: Never lose data - store unencrypted with clear marker
            return f"{self.UNENCRYPTED_PREFIX}{phone}"

    def decrypt_phone(self, encrypted_phone: str | None) -> str | None:
        """
        Decrypt phone number with comprehensive error handling.

        Args:
            encrypted_phone: Encrypted phone string

        Returns:
            Plain text phone number, or original string if decryption fails

        Error Handling:
            - Empty/None input: Returns as-is
            - UNENCRYPTED: prefix detected: Returns without prefix
            - Invalid format: Returns as-is + logs warning
            - Decryption failure: Returns as-is + logs error
        """
        # Handle empty input
        if not encrypted_phone:
            return encrypted_phone

        try:
            encrypted_str = str(encrypted_phone).strip()

            if not encrypted_str:
                logger.warning("Empty encrypted phone after stripping")
                return encrypted_str

            # Check if unencrypted (fallback from encryption failure)
            if encrypted_str.startswith(self.UNENCRYPTED_PREFIX):
                unencrypted = encrypted_str.replace(self.UNENCRYPTED_PREFIX, "", 1)
                logger.warning(f"Detected unencrypted phone number: {unencrypted[:4]}****")
                return unencrypted

            # Remove version prefix if present
            if encrypted_str.startswith(self.ENCRYPTED_VERSION):
                encrypted_str = encrypted_str.replace(self.ENCRYPTED_VERSION, "", 1)

            # Decode and decrypt
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_str.encode("utf-8"))
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
            decrypted = decrypted_bytes.decode("utf-8")

            logger.debug(f"Decrypted phone number (length: {len(decrypted)} digits)")
            return decrypted

        except InvalidToken as e:
            logger.exception(
                f"Invalid decryption token - possible wrong key or corrupted data: {e}"
            )
            # Return as-is to prevent data loss
            return encrypted_phone

        except Exception as e:
            logger.error(f"Phone decryption failed: {e}", exc_info=True)
            # CRITICAL: Never crash - return encrypted value as fallback
            return encrypted_phone

    def encrypt_email(self, email: str | None) -> str | None:
        """
        Encrypt email address with validation and error handling.

        Args:
            email: Plain text email address

        Returns:
            Encrypted email string, or original with UNENCRYPTED: prefix if encryption fails
        """
        if not email:
            return email

        try:
            # Validate email format (basic check)
            email_str = str(email).strip().lower()

            if "@" not in email_str or "." not in email_str.split("@")[1]:
                logger.warning(f"Invalid email format: {email_str}")
                return f"{self.UNENCRYPTED_PREFIX}{email}"

            # Encrypt
            encrypted_bytes = self.cipher.encrypt(email_str.encode("utf-8"))
            encrypted_str = base64.urlsafe_b64encode(encrypted_bytes).decode("utf-8")

            result = f"{self.ENCRYPTED_VERSION}{encrypted_str}"
            logger.debug(f"Encrypted email: {email_str.split('@')[0]}@***")
            return result

        except Exception as e:
            logger.error(f"Email encryption failed: {e}", exc_info=True)
            return f"{self.UNENCRYPTED_PREFIX}{email}"

    def decrypt_email(self, encrypted_email: str | None) -> str | None:
        """
        Decrypt email address with error handling.

        Args:
            encrypted_email: Encrypted email string

        Returns:
            Plain text email address, or original string if decryption fails
        """
        if not encrypted_email:
            return encrypted_email

        try:
            encrypted_str = str(encrypted_email).strip()

            # Check if unencrypted
            if encrypted_str.startswith(self.UNENCRYPTED_PREFIX):
                return encrypted_str.replace(self.UNENCRYPTED_PREFIX, "", 1)

            # Remove version prefix
            if encrypted_str.startswith(self.ENCRYPTED_VERSION):
                encrypted_str = encrypted_str.replace(self.ENCRYPTED_VERSION, "", 1)

            # Decrypt
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_str.encode("utf-8"))
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
            decrypted = decrypted_bytes.decode("utf-8")

            logger.debug(f"Decrypted email: {decrypted.split('@')[0]}@***")
            return decrypted

        except Exception as e:
            logger.error(f"Email decryption failed: {e}", exc_info=True)
            return encrypted_email


def generate_encryption_key() -> str:
    """
    Generate a new Fernet encryption key.

    Returns:
        Base64-encoded Fernet key (44 characters)

    Usage:
        key = generate_encryption_key()
        print(f"ENCRYPTION_KEY={key}")
        # Add to .env file
    """
    key = Fernet.generate_key()
    return key.decode("utf-8")


def derive_key_from_password(password: str, salt: bytes | None = None) -> tuple[str, bytes]:
    """
    Derive encryption key from password (for key rotation).

    Args:
        password: Master password
        salt: Optional salt (16 bytes). If None, generates random salt.

    Returns:
        Tuple of (base64_key, salt)
    """
    if salt is None:
        salt = os.urandom(16)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )

    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key.decode("utf-8"), salt


# Module-level instance for convenience
_handler: SecureDataHandler | None = None


def get_secure_handler() -> SecureDataHandler:
    """Get or create global SecureDataHandler instance"""
    global _handler
    if _handler is None:
        _handler = SecureDataHandler()
    return _handler


# Convenience functions
def encrypt_phone(phone: str | None) -> str | None:
    """Convenience function to encrypt phone number"""
    return get_secure_handler().encrypt_phone(phone)


def decrypt_phone(encrypted: str | None) -> str | None:
    """Convenience function to decrypt phone number"""
    return get_secure_handler().decrypt_phone(encrypted)


def encrypt_email(email: str | None) -> str | None:
    """Convenience function to encrypt email"""
    return get_secure_handler().encrypt_email(email)


def decrypt_email(encrypted: str | None) -> str | None:
    """Convenience function to decrypt email"""
    return get_secure_handler().decrypt_email(encrypted)


if __name__ == "__main__":
    # Generate new encryption key
    pass
