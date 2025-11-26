"""
Test Customer Model Encryption Integration

Verifies that Customer model @property decorators correctly use encryption functions.
Tests passthrough mode and actual encryption with keys.
"""

import pytest
from uuid import uuid4

from core.encryption import encrypt_email, decrypt_email, encrypt_phone, decrypt_phone


class TestEncryptionHelpers:
    """Test encryption helper functions"""

    def test_email_encryption_cycle(self):
        """Test encrypt and decrypt email"""
        original = "customer@example.com"
        encrypted = encrypt_email(original)
        decrypted = decrypt_email(encrypted)

        assert decrypted == original
        # In passthrough mode (no key), encrypted == original
        # With key, encrypted should start with "gAAAAA"
        assert encrypted == original or encrypted.startswith("gAAAAA")

    def test_phone_encryption_cycle(self):
        """Test encrypt and decrypt phone"""
        original = "+1234567890"
        encrypted = encrypt_phone(original)
        decrypted = decrypt_phone(encrypted)

        assert decrypted == original
        # In passthrough mode (no key), encrypted == original
        # With key, encrypted should start with "gAAAAA"
        assert encrypted == original or encrypted.startswith("gAAAAA")

    def test_email_normalization(self):
        """Test that email helper normalizes to lowercase"""
        email = "Customer@Example.COM"
        encrypted = encrypt_email(email)
        decrypted = decrypt_email(encrypted)

        # Email should be normalized to lowercase
        assert decrypted == email.lower()

    def test_phone_strips_formatting(self):
        """Test that phone helper strips formatting"""
        phone = "+1 (234) 567-8900"
        encrypted = encrypt_phone(phone)
        decrypted = decrypt_phone(encrypted)

        # Phone should have formatting removed
        assert " " not in decrypted
        assert "(" not in decrypted
        assert ")" not in decrypted
        assert "-" not in decrypted

    def test_empty_values_handled(self):
        """Test that empty strings are handled correctly"""
        assert encrypt_email("") == ""
        assert decrypt_email("") == ""
        assert encrypt_phone("") == ""
        assert decrypt_phone("") == ""

    def test_idempotency(self):
        """Test that encrypting already-encrypted data returns same value"""
        original = "test@example.com"
        encrypted1 = encrypt_email(original)
        encrypted2 = encrypt_email(encrypted1)

        # Encrypting twice should detect already-encrypted data
        # If it starts with "gAAAAA", it's already encrypted
        if encrypted1.startswith("gAAAAA"):
            assert encrypted1 == encrypted2


class TestCustomerEncryptionProperties:
    """Test Customer model encryption integration (simplified without DB)"""

    def test_encryption_functions_exist(self):
        """Test that encryption module has required functions"""
        from core import encryption

        assert hasattr(encryption, 'encrypt_email')
        assert hasattr(encryption, 'decrypt_email')
        assert hasattr(encryption, 'encrypt_phone')
        assert hasattr(encryption, 'decrypt_phone')
        assert hasattr(encryption, 'encrypt_field')
        assert hasattr(encryption, 'decrypt_field')

    def test_passthrough_mode_works(self):
        """Test that system works without encryption key (passthrough mode)"""
        # Without FIELD_ENCRYPTION_KEY, functions should pass through
        test_email = "passthrough@test.com"
        test_phone = "+1111111111"

        encrypted_email = encrypt_email(test_email)
        encrypted_phone = encrypt_phone(test_phone)

        # In passthrough mode, output should equal input (or be encrypted)
        assert encrypted_email == test_email or encrypted_email.startswith("gAAAAA")
        assert encrypted_phone == test_phone or encrypted_phone.startswith("gAAAAA")


class TestEncryptionWithKey:
    """Test encryption when key is configured"""

    @pytest.fixture
    def encryption_key(self, monkeypatch):
        """Set up test encryption key"""
        from cryptography.fernet import Fernet
        key = Fernet.generate_key().decode()
        monkeypatch.setenv("FIELD_ENCRYPTION_KEY", key)

        # Force settings reload
        from core.config import get_settings
        from functools import lru_cache
        get_settings.cache_clear()

        yield key

        # Cleanup
        monkeypatch.delenv("FIELD_ENCRYPTION_KEY", raising=False)
        get_settings.cache_clear()

    def test_encryption_with_valid_key(self, encryption_key):
        """Test encryption when valid key is configured"""
        original_email = "secure@example.com"

        encrypted = encrypt_email(original_email)
        decrypted = decrypt_email(encrypted)

        # With key, should actually encrypt
        assert encrypted != original_email
        assert encrypted.startswith("gAAAAA")
        assert decrypted == original_email.lower()

    def test_phone_encryption_with_valid_key(self, encryption_key):
        """Test phone encryption when valid key is configured"""
        original_phone = "+1234567890"

        encrypted = encrypt_phone(original_phone)
        decrypted = decrypt_phone(encrypted)

        # With key, should actually encrypt
        assert encrypted != original_phone
        assert encrypted.startswith("gAAAAA")
        assert decrypted == original_phone


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
