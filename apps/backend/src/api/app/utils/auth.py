import logging
from typing import Any, Optional
import os
import sqlite3
from datetime import datetime, timedelta, timezone
import secrets
import string

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
import bcrypt

from core.config import get_settings

settings = get_settings()

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
    now = datetime.now(timezone.utc)
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


# ============================================================================
# 4-TIER RBAC SYSTEM (New Implementation)
# ============================================================================

from enum import Enum
from typing import List, Callable


class UserRole(str, Enum):
    """
    4-tier role hierarchy for admin access control.
    
    Roles (highest to lowest):
    - SUPER_ADMIN: Full system access, can manage admins
    - ADMIN: Most operations, cannot manage admin accounts
    - CUSTOMER_SUPPORT: Customer-facing operations only
    - STATION_MANAGER: Station-specific operations
    """
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    CUSTOMER_SUPPORT = "CUSTOMER_SUPPORT"
    STATION_MANAGER = "STATION_MANAGER"


class Permission:
    """
    Granular permission definitions for each role.
    Each permission is a list of roles that have access.
    """
    
    # ========== BOOKING PERMISSIONS ==========
    BOOKING_VIEW_ALL = [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT]
    BOOKING_CREATE = [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT]
    BOOKING_UPDATE = [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT]
    BOOKING_DELETE = [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT]
    BOOKING_VIEW_STATION = [UserRole.STATION_MANAGER]  # View own station only
    
    # ========== CUSTOMER PERMISSIONS ==========
    CUSTOMER_VIEW = [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT]
    CUSTOMER_CREATE = [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT]
    CUSTOMER_UPDATE = [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT]
    CUSTOMER_DELETE = [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT]
    
    # ========== LEAD PERMISSIONS ==========
    LEAD_VIEW = [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT]
    LEAD_MANAGE = [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT]
    LEAD_DELETE = [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT]
    
    # ========== REVIEW PERMISSIONS ==========
    REVIEW_VIEW = [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT]
    REVIEW_MODERATE = [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT]
    REVIEW_DELETE = [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT]
    
    # ========== CHEF PERMISSIONS ==========
    CHEF_VIEW_ALL = [UserRole.SUPER_ADMIN, UserRole.ADMIN]
    CHEF_VIEW_STATION = [UserRole.STATION_MANAGER]  # View own station only
    CHEF_ASSIGN = [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.STATION_MANAGER]
    CHEF_SCHEDULE = [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.STATION_MANAGER]
    
    # ========== STATION PERMISSIONS ==========
    STATION_VIEW_ALL = [UserRole.SUPER_ADMIN, UserRole.ADMIN]
    STATION_VIEW_OWN = [UserRole.STATION_MANAGER]
    STATION_MANAGE = [UserRole.SUPER_ADMIN, UserRole.ADMIN]
    STATION_MANAGE_OWN = [UserRole.STATION_MANAGER]  # Edit own station only
    STATION_DELETE = [UserRole.SUPER_ADMIN]
    
    # ========== ADMIN PERMISSIONS ==========
    ADMIN_VIEW = [UserRole.SUPER_ADMIN]
    ADMIN_CREATE = [UserRole.SUPER_ADMIN]
    ADMIN_UPDATE = [UserRole.SUPER_ADMIN]
    ADMIN_DELETE = [UserRole.SUPER_ADMIN]
    ADMIN_ASSIGN_ROLES = [UserRole.SUPER_ADMIN]
    
    # ========== FINANCIAL PERMISSIONS ==========
    FINANCIAL_VIEW = [UserRole.SUPER_ADMIN, UserRole.ADMIN]
    FINANCIAL_REFUND = [UserRole.SUPER_ADMIN, UserRole.ADMIN]
    FINANCIAL_REPORTS = [UserRole.SUPER_ADMIN, UserRole.ADMIN]
    
    # ========== AUDIT PERMISSIONS ==========
    AUDIT_VIEW_ALL = [UserRole.SUPER_ADMIN, UserRole.ADMIN]
    AUDIT_VIEW_OWN = [UserRole.CUSTOMER_SUPPORT, UserRole.STATION_MANAGER]
    AUDIT_EXPORT = [UserRole.SUPER_ADMIN, UserRole.ADMIN]
    
    # ========== SYSTEM PERMISSIONS ==========
    SYSTEM_SETTINGS = [UserRole.SUPER_ADMIN, UserRole.ADMIN]
    SYSTEM_ANALYTICS = [UserRole.SUPER_ADMIN, UserRole.ADMIN]
    SYSTEM_ANALYTICS_STATION = [UserRole.STATION_MANAGER]  # Station analytics only


def require_role(allowed_roles: List[UserRole]) -> Callable:
    """
    Dependency factory to require specific roles.
    
    Usage:
        @router.get("/admin/bookings")
        async def get_bookings(
            current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT]))
        ):
            # Only SUPER_ADMIN, ADMIN, or CUSTOMER_SUPPORT can access
            ...
    
    Args:
        allowed_roles: List of roles that can access the endpoint
        
    Returns:
        Dependency function that validates user role
    """
    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        # Get user role (support both new and legacy formats)
        user_role_str = current_user.get("role")
        
        # Handle legacy roles (convert to new format)
        role_mapping = {
            "superadmin": UserRole.SUPER_ADMIN,
            "admin": UserRole.ADMIN,
            "staff": UserRole.CUSTOMER_SUPPORT,
            "support": UserRole.CUSTOMER_SUPPORT,
            "manager": UserRole.STATION_MANAGER,
        }
        
        # Try to get role from enum or mapping
        try:
            if user_role_str in [r.value for r in UserRole]:
                user_role = UserRole(user_role_str)
            else:
                user_role = role_mapping.get(user_role_str.lower(), None)
        except (ValueError, AttributeError):
            user_role = None
        
        if user_role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Invalid user role: {user_role_str}"
            )
        
        if user_role not in allowed_roles:
            allowed_role_names = ", ".join([r.value for r in allowed_roles])
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {allowed_role_names}. Your role: {user_role.value}"
            )
        
        return current_user
    
    return role_checker


# ========== CONVENIENCE DEPENDENCIES ==========

def require_super_admin() -> Callable:
    """Require SUPER_ADMIN role (full system access)."""
    return require_role([UserRole.SUPER_ADMIN])


def require_admin() -> Callable:
    """Require ADMIN or SUPER_ADMIN role (most operations)."""
    return require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN])


def require_customer_support() -> Callable:
    """Require CUSTOMER_SUPPORT, ADMIN, or SUPER_ADMIN role (customer-facing operations)."""
    return require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT])


def require_station_manager() -> Callable:
    """Require STATION_MANAGER role (station-specific operations)."""
    return require_role([UserRole.STATION_MANAGER])


def require_any_admin() -> Callable:
    """Require any admin role (any authenticated admin user)."""
    return require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT, UserRole.STATION_MANAGER])


# ========== UTILITY FUNCTIONS ==========

def has_permission(user: dict, allowed_roles: List[UserRole]) -> bool:
    """
    Check if user has permission (utility function for non-endpoint logic).
    
    Usage:
        if has_permission(current_user, Permission.BOOKING_DELETE):
            # User can delete bookings
            ...
    
    Args:
        user: User dictionary
        allowed_roles: List of roles that have permission
        
    Returns:
        True if user has permission, False otherwise
    """
    user_role_str = user.get("role")
    
    # Handle legacy roles
    role_mapping = {
        "superadmin": UserRole.SUPER_ADMIN,
        "admin": UserRole.ADMIN,
        "staff": UserRole.CUSTOMER_SUPPORT,
        "support": UserRole.CUSTOMER_SUPPORT,
        "manager": UserRole.STATION_MANAGER,
    }
    
    try:
        if user_role_str in [r.value for r in UserRole]:
            user_role = UserRole(user_role_str)
        else:
            user_role = role_mapping.get(user_role_str.lower(), None)
    except (ValueError, AttributeError):
        return False
    
    return user_role in allowed_roles


def get_role_hierarchy_level(role: UserRole) -> int:
    """
    Get numeric level for role hierarchy (higher = more permissions).
    
    Returns:
        4: SUPER_ADMIN
        3: ADMIN
        2: CUSTOMER_SUPPORT
        1: STATION_MANAGER
        0: Unknown
    """
    hierarchy = {
        UserRole.SUPER_ADMIN: 4,
        UserRole.ADMIN: 3,
        UserRole.CUSTOMER_SUPPORT: 2,
        UserRole.STATION_MANAGER: 1,
    }
    return hierarchy.get(role, 0)


def can_access_station(user: dict, station_id: str) -> bool:
    """
    Check if user can access a specific station.
    
    - SUPER_ADMIN and ADMIN can access all stations
    - CUSTOMER_SUPPORT can access all stations (read-only for internal ops)
    - STATION_MANAGER can only access their assigned station
    
    Args:
        user: User dictionary
        station_id: Station ID to check access for
        
    Returns:
        True if user can access station, False otherwise
    """
    user_role_str = user.get("role")
    
    # SUPER_ADMIN and ADMIN can access everything
    if user_role_str in [UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, "superadmin", "admin"]:
        return True
    
    # CUSTOMER_SUPPORT can view all stations (for booking management)
    if user_role_str in [UserRole.CUSTOMER_SUPPORT.value, "support", "staff"]:
        return True
    
    # STATION_MANAGER can only access their assigned station
    if user_role_str in [UserRole.STATION_MANAGER.value, "manager"]:
        assigned_station_id = user.get("assigned_station_id")
        return assigned_station_id == station_id
    
    return False
