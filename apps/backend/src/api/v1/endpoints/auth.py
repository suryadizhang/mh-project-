"""
Authentication endpoints (v1 API - PRODUCTION IMPLEMENTATION)

Real authentication with database-backed users.
Queries identity.users table and verifies bcrypt password hashes.

Supports both:
1. Password login (for testing)
2. Google OAuth (for production)
"""

import logging
from datetime import timedelta

import bcrypt
from api.deps import get_current_user, get_db
from core.config import UserRole, get_settings
from core.security import create_access_token
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)


# Pydantic models
class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: "UserResponse"


class UserResponse(BaseModel):
    id: str
    email: str
    role: UserRole
    full_name: str | None = None
    is_active: bool = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


def verify_password_bcrypt(plain_password: str, hashed_password: str) -> bool:
    """Verify password using bcrypt directly."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


@router.post("/login", response_model=Token, tags=["Authentication"])
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Login with email and password.

    Queries identity.users table for user authentication.
    Returns JWT access token with user information.

    Test credentials:
    - admin@myhibachichef.com / Test2025!Secure (SUPER_ADMIN role)
    - station.admin@myhibachichef.com / Test2025!Secure (ADMIN role)
    - support@myhibachichef.com / Test2025!Secure (CUSTOMER_SUPPORT role)
    - manager@myhibachichef.com / Test2025!Secure (STATION_MANAGER role)
    - chef@myhibachichef.com / Test2025!Secure (CHEF role)
    """
    logger.info(f"Login attempt for: {login_data.email}")

    try:
        # Query user from identity.users table with role from user_roles/roles
        query = text(
            """
            SELECT u.id, u.email, u.password_hash, r.role_type as role,
                   CONCAT(u.first_name, ' ', u.last_name) as full_name, u.status
            FROM identity.users u
            LEFT JOIN identity.user_roles ur ON u.id = ur.user_id
            LEFT JOIN identity.roles r ON ur.role_id = r.id
            WHERE u.email = :email
        """
        )
        result = await db.execute(query, {"email": login_data.email})
        user_row = result.fetchone()

        if not user_row:
            logger.warning(f"User not found: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
            )

        user_id, email, password_hash, role, full_name, user_status = user_row
        logger.info(f"Found user: id={user_id}, role={role}, status={user_status}")

        # Check if user is active (compare as string since DB returns enum)
        status_str = str(user_status).upper() if user_status else ""
        if "ACTIVE" not in status_str:
            logger.warning(f"User not active: {login_data.email}, status={user_status}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is not active"
            )

        # Verify password
        if not password_hash:
            logger.warning(f"No password hash for user: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
            )

        if not verify_password_bcrypt(login_data.password, password_hash):
            logger.warning(f"Password verification failed for: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
            )

        logger.info(f"Password verified successfully for: {login_data.email}")

        # Map database role_type to UserRole enum
        # Database uses UPPERCASE (SUPER_ADMIN), UserRole uses lowercase (super_admin)
        role_mapping = {
            "SUPER_ADMIN": UserRole.SUPER_ADMIN,
            "ADMIN": UserRole.ADMIN,
            "MANAGER": UserRole.CUSTOMER_SUPPORT,  # MANAGER in DB = customer_support role
            "CUSTOMER_SUPPORT": UserRole.CUSTOMER_SUPPORT,
            "STAFF": UserRole.STATION_MANAGER,  # STAFF in DB = station_manager role
            "STATION_MANAGER": UserRole.STATION_MANAGER,
            "CHEF": UserRole.STATION_MANAGER,  # CHEF defaults to station_manager for now
        }

        role_str = str(role).upper() if role else "CUSTOMER_SUPPORT"
        user_role = role_mapping.get(role_str, UserRole.CUSTOMER_SUPPORT)
        logger.info(f"Mapped role '{role}' to UserRole.{user_role.value}")

        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": str(user_id),
                "email": email,
                "role": user_role.value,
            },
            expires_delta=access_token_expires,
        )

        logger.info(f"Login successful for: {login_data.email}")

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse(
                id=str(user_id),
                email=email,
                role=user_role,
                full_name=full_name,
                is_active=True,
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for {login_data.email}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}",
        )


@router.post("/logout", tags=["Authentication"])
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout current user.
    In a stateless JWT system, logout is handled client-side by discarding the token.
    """
    logger.info(f"Logout for user: {current_user.get('email', 'unknown')}")
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse, tags=["Authentication"])
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user information."""
    return UserResponse(
        id=current_user["id"] if "id" in current_user else current_user.get("sub", ""),
        email=current_user["email"],
        role=(
            UserRole(current_user["role"])
            if isinstance(current_user["role"], str)
            else current_user["role"]
        ),
        full_name=current_user.get("full_name"),
        is_active=True,
    )


@router.post("/refresh", response_model=Token, tags=["Authentication"])
async def refresh_token(refresh_data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """
    Refresh access token.

    Note: Full refresh token rotation requires additional infrastructure.
    For now, this endpoint is not implemented.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Refresh token functionality not yet implemented. Please login again.",
    )
