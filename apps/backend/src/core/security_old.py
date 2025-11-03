"""
Security utilities: authentication, encryption, password hashing
"""

import base64
from datetime import datetime, timedelta
import hashlib
import secrets
from typing import Any

from core.config import UserRole, get_settings
from cryptography.fernet import Fernet
from jose import JWTError, jwt
from passlib.context import CryptContext

settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Encryption for PII
def get_fernet_key() -> Fernet:
    """Get encryption key for PII data"""
    key = settings.ENCRYPTION_KEY.encode()
    if len(key) != 44:  # Fernet key must be 32 bytes base64 encoded (44 chars)
        # Generate key from settings key
        hashed = hashlib.sha256(key).digest()
        key = base64.urlsafe_b64encode(hashed)
    return Fernet(key)


fernet = get_fernet_key()


# Authentication functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def verify_token(token: str) -> dict[str, Any] | None:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        return None


def extract_user_from_token(token: str) -> dict[str, Any] | None:
    """Extract user information from JWT token"""
    payload = verify_token(token)
    if payload:
        user_id: str = payload.get("sub")
        role_str: str = payload.get("role", "customer")
        email: str = payload.get("email")

        if user_id is None:
            return None

        # Safely convert role string to UserRole enum
        try:
            role = UserRole(role_str.lower())
        except (ValueError, AttributeError):
            # If role is invalid, default to customer
            role = UserRole.CUSTOMER

        return {"id": user_id, "email": email, "role": role}
    return None


# PII Encryption functions
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
        # Decode from base64
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        # Decrypt
        decrypted = fernet.decrypt(encrypted_bytes)
        return decrypted.decode()
    except Exception as e:
        raise ValueError(f"Decryption failed: {e}")


def generate_api_key() -> str:
    """Generate secure API key"""
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """Hash API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify API key against hash"""
    return hash_api_key(plain_key) == hashed_key


# Rate limiting helpers
def get_user_rate_limit_tier(user_role: UserRole | None) -> str:
    """Get rate limit tier based on user role"""
    if user_role in [UserRole.OWNER, UserRole.MANAGER]:
        return "admin_super"
    elif user_role == UserRole.ADMIN:
        return "admin"
    else:
        return "public"


def is_admin_user(user_role: UserRole | None) -> bool:
    """Check if user has admin privileges"""
    return user_role in [UserRole.ADMIN, UserRole.MANAGER, UserRole.OWNER]


def is_super_admin(user_role: UserRole | None) -> bool:
    """Check if user has super admin privileges"""
    return user_role in [UserRole.MANAGER, UserRole.OWNER]


# Business data sanitization
def sanitize_business_data(data: dict[str, Any]) -> dict[str, Any]:
    """Remove sensitive business data from public responses"""
    sensitive_fields = [
        "ein",
        "tax_id",
        "ssn",
        "full_address",
        "personal_email",
        "api_key",
        "secret",
    ]

    sanitized = data.copy()
    for field in sensitive_fields:
        if field in sanitized:
            del sanitized[field]

    return sanitized


def get_public_business_info() -> dict[str, Any]:
    """Get public-safe business information"""
    return {
        "business_name": settings.BUSINESS_NAME,
        "email": settings.BUSINESS_EMAIL,
        "phone": settings.BUSINESS_PHONE,
        "city": settings.BUSINESS_CITY,
        "state": settings.BUSINESS_STATE,
        "service_areas": settings.SERVICE_AREAS,
    }
