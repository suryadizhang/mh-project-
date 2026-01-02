"""
API Key Management
==================

Generation, hashing, and verification of API keys.

See: .github/instructions/22-QUALITY_CONTROL.instructions.md for modularization standards
"""

import hashlib
import secrets


def generate_api_key() -> str:
    """Generate secure API key"""
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """Hash API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify API key against hash"""
    return hash_api_key(plain_key) == hashed_key


def generate_secure_token(length: int = 32) -> str:
    """Generate cryptographically secure random token"""
    return secrets.token_urlsafe(length)


__all__ = [
    "generate_api_key",
    "hash_api_key",
    "verify_api_key",
    "generate_secure_token",
]
