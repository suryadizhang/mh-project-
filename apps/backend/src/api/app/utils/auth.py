import logging
from typing import Any, Optional
import os
import sqlite3
from datetime import datetime, timedelta
import secrets
import string

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
import bcrypt

from api.app.config import settings

logger = logging.getLogger(__name__)
security = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Enhanced password context with stronger settings
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.bcrypt_rounds if hasattr(settings, 'bcrypt_rounds') else 12
)


def hash_password(password: str) -> str:
    """Hash password using bcrypt with enhanced security."""
    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password cannot be empty"
        )
    
    # Check password strength
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against hash with timing attack protection."""
    try:
        return pwd_context.verify(plain, hashed)
    except Exception as e:
        logger.warning(f"Password verification error: {e}")
        return False


def generate_secure_password(length: int = 16) -> str:
    """Generate a cryptographically secure password."""
    if length < 8:
        length = 8
    
    # Ensure complexity requirements
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(characters) for _ in range(length))
    
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


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token with enhanced security."""
    to_encode = data.copy()
    
    # Add timestamp and jti for token tracking
    now = datetime.utcnow()
    to_encode.update({
        "iat": now,
        "jti": secrets.token_urlsafe(16)  # Unique token ID
    })
    
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    
    try:
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Token creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token creation failed"
        )


def decode_access_token(token: str) -> Optional[dict]:
    """Decode JWT access token with enhanced validation."""
    try:
        payload = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.jwt_algorithm],
            options={"verify_exp": True, "verify_iat": True}
        )
        
        # Additional security checks
        if "jti" not in payload:
            logger.warning("Token missing JTI claim")
            return None
            
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None
    except Exception as e:
        logger.error(f"Token decode error: {e}")
        return None


def get_user_db():
    """Get connection to user database."""
    # For compatibility with source backend
    db_path = "users.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any]:
    """Get current user from JWT token."""
    try:
        token = credentials.credentials
        payload = decode_access_token(token)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        username = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # For development mode with mock user
        if settings.environment == "development" and username == "dev-user":
            return {
                "id": "dev-user-123",
                "username": "dev-user",
                "email": "dev@myhibachi.com",
                "role": "superadmin",
                "is_admin": True,
            }
        
        # Check user database (compatible with source backend)
        try:
            conn = get_user_db()
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = c.fetchone()
            conn.close()
            
            if user:
                return dict(user)
                
        except sqlite3.Error as e:
            logger.warning(f"Database error: {e}")
        
        # Fallback for JWT-only authentication
        return {
            "id": payload.get("user_id", username),
            "username": username,
            "role": payload.get("role", "user"),
            "email": payload.get("email", ""),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_oauth(token: str = Depends(oauth2_scheme)) -> dict[str, Any]:
    """Get current user from OAuth2 token (for compatibility)."""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    username = payload.get("sub")
    
    # Mock for development
    if settings.environment == "development":
        return {
            "id": 1,
            "username": username,
            "role": payload.get("role", "admin"),
        }
    
    # Production user lookup
    try:
        conn = get_user_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        
        if user:
            return dict(user)
            
    except sqlite3.Error:
        pass
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User not found"
    )


def superadmin_required(user=Depends(get_current_user_oauth)):
    """Dependency to require superadmin privileges."""
    if user.get("role") != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Superadmin privileges required"
        )
    return user


def admin_required(user=Depends(get_current_user_oauth)):
    """Dependency to require admin privileges."""
    if user.get("role") not in ("admin", "superadmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Admin privileges required"
        )
    return user


async def get_admin_user(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Ensure current user is admin (legacy compatibility)."""
    if current_user.get("role") not in ("admin", "superadmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict[str, Any] | None:
    """Get current user if authenticated, None otherwise."""
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
