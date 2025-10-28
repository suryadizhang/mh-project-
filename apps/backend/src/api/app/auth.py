"""
Authentication and authorization module for MyHibachi API
Comprehensive security implementation with OAuth 2.1, JWT, and MFA
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any, List
from passlib.context import CryptContext
from passlib.totp import TOTP
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
import pyotp
import qrcode
import io
import base64
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from core.config import get_settings

settings = get_settings()
from api.app.database import get_db

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.bcrypt_rounds
)

# Security scheme
security = HTTPBearer(auto_error=False)

class TokenData(BaseModel):
    """Token data structure"""
    user_id: Optional[str] = None
    email: Optional[str] = None
    roles: List[str] = []
    permissions: List[str] = []
    mfa_verified: bool = False
    session_id: Optional[str] = None

class UserAuth(BaseModel):
    """User authentication data"""
    id: str
    email: EmailStr
    hashed_password: str
    is_active: bool = True
    is_verified: bool = False
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
    roles: List[str] = []
    permissions: List[str] = []
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None

class MFASetup(BaseModel):
    """MFA setup response"""
    secret: str
    qr_code: str
    backup_codes: List[str]

class AuthService:
    """Comprehensive authentication service"""
    
    def __init__(self):
        self.algorithm = settings.jwt_algorithm
        self.secret_key = settings.jwt_secret
        self.access_token_expire_minutes = settings.access_token_expire_minutes
        self.refresh_token_expire_days = settings.refresh_token_expire_days
        
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> TokenData:
        """Verify and decode JWT token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise credentials_exception
                
            token_data = TokenData(
                user_id=user_id,
                email=payload.get("email"),
                roles=payload.get("roles", []),
                permissions=payload.get("permissions", []),
                mfa_verified=payload.get("mfa_verified", False),
                session_id=payload.get("session_id")
            )
            return token_data
            
        except JWTError:
            raise credentials_exception
    
    def generate_mfa_secret(self) -> str:
        """Generate MFA secret for TOTP"""
        return pyotp.random_base32()
    
    def generate_qr_code(self, user_email: str, secret: str) -> str:
        """Generate QR code for MFA setup"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name=settings.totp_issuer
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{qr_code_base64}"
    
    def verify_mfa_token(self, secret: str, token: str) -> bool:
        """Verify MFA TOTP token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate MFA backup codes"""
        return [secrets.token_hex(4).upper() for _ in range(count)]
    
    async def authenticate_user(
        self, 
        db: AsyncSession, 
        email: str, 
        password: str
    ) -> Optional[UserAuth]:
        """
        Authenticate user with email and password
        
        DOCUMENTED: This is a placeholder method.
        Actual authentication is handled by the database-backed
        user repository in production. This method would:
        1. Query user by email from database
        2. Verify password hash using bcrypt
        3. Return user object if valid
        
        Integration point: Replace with UserRepository.get_by_email()
        """
        # Placeholder - no database lookup implemented
        # Production: Use UserRepository with SQLAlchemy models
        return None
    
    async def get_current_user(
        self,
        db: AsyncSession = Depends(get_db),
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ) -> UserAuth:
        """Get current user from JWT token"""
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token_data = self.verify_token(credentials.credentials)
        
        # DOCUMENTED: Mock user creation from token data
        # In production, this should query the database to get fresh user data
        # including updated roles/permissions and account status.
        # Integration point: Replace with UserRepository.get_by_id(token_data.user_id)
        user = UserAuth(
            id=token_data.user_id,
            email=token_data.email,
            hashed_password="",
            roles=token_data.roles,
            permissions=token_data.permissions
        )
        
        return user
    
    def require_roles(self, required_roles: List[str]):
        """Dependency to require specific roles"""
        async def role_checker(current_user: UserAuth = Depends(self.get_current_user)):
            if not any(role in current_user.roles for role in required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            return current_user
        return role_checker
    
    def require_permissions(self, required_permissions: List[str]):
        """Dependency to require specific permissions"""
        async def permission_checker(current_user: UserAuth = Depends(self.get_current_user)):
            if not any(perm in current_user.permissions for perm in required_permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            return current_user
        return permission_checker

# Global auth service instance
auth_service = AuthService()

# Dependency functions for FastAPI
async def get_current_user(
    db: AsyncSession = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> UserAuth:
    """FastAPI dependency to get current user"""
    return await auth_service.get_current_user(db, credentials)

async def get_current_active_user(current_user: UserAuth = Depends(get_current_user)) -> UserAuth:
    """FastAPI dependency to ensure user is active"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_admin():
    """Require admin role"""
    return auth_service.require_roles(["admin"])

def require_staff():
    """Require staff or admin role"""
    return auth_service.require_roles(["staff", "admin"])

def require_customer():
    """Require customer role"""
    return auth_service.require_roles(["customer"])

# Rate limiting for authentication endpoints
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@limiter.limit("5/minute")
async def rate_limited_auth(request: Request):
    """Rate limit authentication attempts"""
    return request

# Security headers middleware would be imported from security.py
# from app.security import SecurityHeadersMiddleware