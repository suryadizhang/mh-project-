"""
Password hashing and verification utilities.

Uses bcrypt directly for security (bypassing passlib version issues).
"""

import logging
import secrets
import string

import bcrypt
from core.config import get_settings
from fastapi import HTTPException, status

settings = get_settings()
logger = logging.getLogger(__name__)

# Bcrypt rounds for hashing (12 is standard, balancing security and performance)
BCRYPT_ROUNDS = getattr(settings, "bcrypt_rounds", 12)


def hash_password(password: str) -> str:
    """Hash password using bcrypt directly (bypassing passlib version issues)."""
    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password cannot be empty",
        )

    # Check password strength
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long",
        )

    # Use bcrypt directly
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against hash using bcrypt directly (bypassing passlib version issues)."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception as e:
        logger.warning(f"Password verification error: {e}")
        return False


def generate_secure_password(length: int = 16) -> str:
    """Generate a cryptographically secure password."""
    length = max(length, 8)

    # Ensure complexity requirements
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    password = "".join(secrets.choice(characters) for _ in range(length))

    # Ensure at least one of each type
    if not any(c.islower() for c in password):
        password = password[:-1] + secrets.choice(string.ascii_lowercase)
    if not any(c.isupper() for c in password):
        password = password[:-1] + secrets.choice(string.ascii_uppercase)
    if not any(c.isdigit() for c in password):
        password = password[:-1] + secrets.choice(string.digits)
    if not any(c in "!@#$%^&*" for c in password):
        password = password[:-1] + secrets.choice("!@#$%^&*")

    return password
