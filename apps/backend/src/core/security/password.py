"""
Password Hashing & Verification
===============================

Secure password hashing using bcrypt.

See: .github/instructions/22-QUALITY_CONTROL.instructions.md for modularization standards
"""

import logging

import bcrypt

logger = logging.getLogger(__name__)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash using bcrypt directly"""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception as e:
        logger.warning(f"Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """Generate password hash using bcrypt directly"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def hash_password_bcrypt(password: str, rounds: int = 12) -> str:
    """Hash password with bcrypt (alternative method)"""
    salt = bcrypt.gensalt(rounds=rounds)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password_bcrypt(password: str, hashed: str) -> bool:
    """Verify password against bcrypt hash"""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


__all__ = [
    "verify_password",
    "get_password_hash",
    "hash_password_bcrypt",
    "verify_password_bcrypt",
]
