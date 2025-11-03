"""Encryption utility alias for lead/newsletter models."""

from api.app.utils.encryption import get_field_encryption


class CryptoUtil:
    """Alias for FieldEncryption to match model usage."""

    @staticmethod
    def encrypt_text(text: str) -> str:
        """Encrypt text and return as string."""
        if not text:
            return ""
        return get_field_encryption().encrypt(text)

    @staticmethod
    def decrypt_text(encrypted_text: str) -> str:
        """Decrypt text string."""
        if not encrypted_text:
            return ""
        return get_field_encryption().decrypt(encrypted_text)
