"""
Field-level encryption utilities for PII protection.

Uses AES-GCM with envelope encryption pattern:
- Data Encryption Keys (DEK) for actual encryption
- Key Encryption Key (KEK) from environment/KMS
- Base64 encoding for database storage
"""
import base64
import json
import os
import secrets
from functools import lru_cache
from typing import Optional

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class FieldEncryption:
    """
    Field-level encryption using AES-GCM with envelope encryption.

    Format of encrypted field: base64(json({
        "version": 1,
        "encrypted_dek": base64_encoded_encrypted_dek,
        "nonce": base64_encoded_nonce,
        "ciphertext": base64_encoded_ciphertext,
        "tag": base64_encoded_auth_tag
    }))
    """

    VERSION = 1
    KEY_SIZE = 32  # 256 bits
    NONCE_SIZE = 12  # 96 bits for GCM

    def __init__(self, master_key: Optional[str] = None):
        """Initialize with master key from environment or parameter."""
        if master_key:
            self.master_key = master_key.encode()
        else:
            # Get from settings - in production this should come from KMS/Vault
            try:
                from ..config import settings
                master_key_b64 = settings.field_encryption_key
            except ImportError:
                # Fallback to environment variable for standalone usage
                master_key_b64 = os.environ.get('FIELD_ENCRYPTION_KEY')
            
            if not master_key_b64:
                raise ValueError(
                    "field_encryption_key setting or FIELD_ENCRYPTION_KEY environment variable required. "
                    "Generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
                )
            try:
                self.master_key = base64.urlsafe_b64decode(master_key_b64)
            except Exception as e:
                raise ValueError(f"Invalid field_encryption_key format: {e}")

        if len(self.master_key) != self.KEY_SIZE:
            raise ValueError(f"Master key must be {self.KEY_SIZE} bytes")

    @lru_cache(maxsize=1)
    def _get_kek(self) -> bytes:
        """
        Derive Key Encryption Key from master key using PBKDF2.
        Cached for performance.
        """
        # Use a fixed salt for KEK derivation - in production, store this securely
        salt = b"myhibachi_field_encryption_kek_salt_v1"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEY_SIZE,
            salt=salt,
            iterations=100000,  # Adjust based on performance requirements
        )
        return kdf.derive(self.master_key)

    def _generate_dek(self) -> bytes:
        """Generate a new Data Encryption Key."""
        return secrets.token_bytes(self.KEY_SIZE)

    def _encrypt_dek(self, dek: bytes) -> tuple[bytes, bytes]:
        """Encrypt DEK with KEK. Returns (encrypted_dek, nonce)."""
        kek = self._get_kek()
        nonce = secrets.token_bytes(self.NONCE_SIZE)
        aesgcm = AESGCM(kek)
        encrypted_dek = aesgcm.encrypt(nonce, dek, None)
        return encrypted_dek, nonce

    def _decrypt_dek(self, encrypted_dek: bytes, nonce: bytes) -> bytes:
        """Decrypt DEK with KEK."""
        kek = self._get_kek()
        aesgcm = AESGCM(kek)
        return aesgcm.decrypt(nonce, encrypted_dek, None)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext string and return base64-encoded encrypted blob.

        Args:
            plaintext: The string to encrypt

        Returns:
            Base64-encoded encrypted blob containing all necessary data for decryption
        """
        if not plaintext:
            return ""

        # Generate DEK and encrypt it
        dek = self._generate_dek()
        encrypted_dek, dek_nonce = self._encrypt_dek(dek)

        # Encrypt the plaintext with DEK
        data_nonce = secrets.token_bytes(self.NONCE_SIZE)
        aesgcm = AESGCM(dek)
        ciphertext = aesgcm.encrypt(data_nonce, plaintext.encode('utf-8'), None)

        # Package everything together
        envelope = {
            "version": self.VERSION,
            "encrypted_dek": base64.b64encode(encrypted_dek).decode('ascii'),
            "dek_nonce": base64.b64encode(dek_nonce).decode('ascii'),
            "data_nonce": base64.b64encode(data_nonce).decode('ascii'),
            "ciphertext": base64.b64encode(ciphertext).decode('ascii')
        }

        # Return base64-encoded JSON
        envelope_json = json.dumps(envelope, separators=(',', ':'))
        return base64.b64encode(envelope_json.encode('utf-8')).decode('ascii')

    def decrypt(self, encrypted_blob: str) -> str:
        """
        Decrypt base64-encoded encrypted blob and return plaintext string.

        Args:
            encrypted_blob: Base64-encoded encrypted blob from encrypt()

        Returns:
            Decrypted plaintext string
        """
        if not encrypted_blob:
            return ""

        try:
            # Decode and parse envelope
            envelope_json = base64.b64decode(encrypted_blob.encode('ascii')).decode('utf-8')
            envelope = json.loads(envelope_json)

            # Version check
            if envelope.get("version") != self.VERSION:
                raise ValueError(f"Unsupported encryption version: {envelope.get('version')}")

            # Extract components
            encrypted_dek = base64.b64decode(envelope["encrypted_dek"])
            dek_nonce = base64.b64decode(envelope["dek_nonce"])
            data_nonce = base64.b64decode(envelope["data_nonce"])
            ciphertext = base64.b64decode(envelope["ciphertext"])

            # Decrypt DEK
            dek = self._decrypt_dek(encrypted_dek, dek_nonce)

            # Decrypt data
            aesgcm = AESGCM(dek)
            plaintext_bytes = aesgcm.decrypt(data_nonce, ciphertext, None)

            return plaintext_bytes.decode('utf-8')

        except Exception as e:
            raise ValueError(f"Failed to decrypt field: {e}")

    def is_encrypted(self, value: str) -> bool:
        """Check if a value appears to be encrypted by this system."""
        if not value:
            return False

        try:
            envelope_json = base64.b64decode(value.encode('ascii')).decode('utf-8')
            envelope = json.loads(envelope_json)
            return envelope.get("version") == self.VERSION
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError, KeyError) as e:
            logger.warning(f"Failed to validate encryption format: {e}")
            return False


# Global instance - initialized when module is imported
_field_encryption: Optional[FieldEncryption] = None

def get_field_encryption() -> FieldEncryption:
    """Get global field encryption instance."""
    global _field_encryption
    if _field_encryption is None:
        _field_encryption = FieldEncryption()
    return _field_encryption

def encrypt_field(plaintext: str) -> str:
    """Encrypt a field value."""
    return get_field_encryption().encrypt(plaintext)

def decrypt_field(encrypted_value: str) -> str:
    """Decrypt a field value."""
    return get_field_encryption().decrypt(encrypted_value)

def is_field_encrypted(value: str) -> bool:
    """Check if a field value is encrypted."""
    return get_field_encryption().is_encrypted(value)


class EncryptedColumn:
    """
    SQLAlchemy custom type for encrypted columns.
    Automatically encrypts on write and decrypts on read.
    """

    def __init__(self, field_encryption: Optional[FieldEncryption] = None):
        self.field_encryption = field_encryption or get_field_encryption()

    def process_bind_param(self, value, dialect):
        """Encrypt value before storing in database."""
        if value is not None:
            return self.field_encryption.encrypt(str(value))
        return value

    def process_result_value(self, value, dialect):
        """Decrypt value after loading from database."""
        if value is not None:
            return self.field_encryption.decrypt(value)
        return value


# Validation utilities for common PII types
def normalize_phone(phone: str) -> str:
    """Normalize phone number to E.164 format."""
    import re

    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)

    # Add country code if missing
    if len(digits_only) == 10:
        digits_only = '1' + digits_only
    elif len(digits_only) == 11 and digits_only.startswith('1'):
        pass  # Already has country code
    else:
        raise ValueError(f"Invalid phone number format: {phone}")

    return '+' + digits_only

def normalize_email(email: str) -> str:
    """Normalize email address."""
    return email.lower().strip()

def validate_email(email: str) -> bool:
    """Basic email validation."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """Validate phone number format."""
    try:
        normalized = normalize_phone(phone)
        return len(normalized) in [12, 13]  # +1xxxxxxxxxx or +xxxxxxxxxxxx
    except (ValueError, TypeError, AttributeError) as e:
        logger.warning(f"Failed to validate phone number: {e}")
        return False


# Development/testing utilities
def generate_master_key() -> str:
    """Generate a new master key for development/testing."""
    key_bytes = secrets.token_bytes(32)
    return base64.urlsafe_b64encode(key_bytes).decode('ascii')

if __name__ == "__main__":
    # Generate a new master key for development
    print("New master key (set as FIELD_ENCRYPTION_KEY):")
    print(generate_master_key())

    # Test encryption
    test_key = generate_master_key()
    enc = FieldEncryption(test_key)

    test_data = [
        "john.doe@example.com",
        "+15551234567",
        "123 Main St, Sacramento, CA 95823",
        "Test User Name",
        ""
    ]

    print("\nTesting encryption/decryption:")
    for data in test_data:
        encrypted = enc.encrypt(data)
        decrypted = enc.decrypt(encrypted)
        print(f"Original:  '{data}'")
        print(f"Encrypted: {encrypted[:50]}..." if len(encrypted) > 50 else f"Encrypted: {encrypted}")
        print(f"Decrypted: '{decrypted}'")
        print(f"Match:     {data == decrypted}")
        print()
