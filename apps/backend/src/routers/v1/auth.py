"""
Authentication and authorization endpoints.

This module handles user authentication operations including:
- User login and token generation
- Token refresh
- User logout
- Current user information retrieval
- Password reset functionality

All endpoints except /login and /register require JWT Bearer token authentication.
"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

# Import for session creation (station-aware tokens)
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.auth.models import UserSession
from core.config import settings
from core.database import get_db
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    require_auth,
    verify_password,
    verify_refresh_token,
)
from db.models.identity import Role, StationUser, User, UserRole, UserStatus
from db.models.ops import Chef
from services.password_reset_service import PasswordResetService
from services.token_blacklist_service import TokenBlacklistService

router = APIRouter(tags=["authentication"])
security = HTTPBearer()
logger = logging.getLogger(__name__)


# Pydantic Schemas
class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")

    model_config = {
        "json_schema_extra": {
            "examples": [{"email": "john@example.com", "password": "SecurePass123!"}]
        }
    }


class TokenResponse(BaseModel):
    """Authentication token response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    refresh_token: str = Field(..., description="Refresh token for obtaining new access tokens")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 3600,
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                }
            ]
        }
    }


class UserResponse(BaseModel):
    """User information response."""

    id: str = Field(..., description="Unique user identifier")
    email: EmailStr = Field(..., description="User email address")
    name: str = Field(..., description="User full name")
    is_admin: bool = Field(default=False, description="Whether user has admin privileges")
    created_at: str = Field(..., description="Account creation timestamp (ISO 8601)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "user-abc123",
                    "email": "john@example.com",
                    "name": "John Doe",
                    "is_admin": False,
                    "created_at": "2024-10-19T10:30:00Z",
                }
            ]
        }
    }


class RegisterRequest(BaseModel):
    """User registration request schema."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (minimum 8 characters)")
    full_name: str = Field(..., min_length=2, max_length=100, description="User's full name")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "jane@example.com",
                    "password": "SecurePass123!",
                    "full_name": "Jane Smith",
                }
            ]
        }
    }


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str = Field(..., description="Error message")


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="""
    Create a new user account.

    ## Process:
    1. Validates email is not already registered
    2. Validates password strength (minimum 8 characters)
    3. Hashes password with bcrypt (12 rounds)
    4. Creates user account with encrypted email
    5. Returns user information

    ## Security:
    - Password hashing: bcrypt with 12 rounds
    - Email encryption: AES-256-GCM
    - Rate limiting: 3 attempts per hour per IP
    - Email validation: RFC 5322 compliant

    ## Default Permissions:
    New users are created with:
    - Basic user role
    - Active status
    - Email verification pending (if enabled)
    """,
    responses={
        201: {
            "description": "User registered successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "user-abc123",
                        "email": "jane@example.com",
                        "name": "Jane Smith",
                        "is_admin": False,
                        "created_at": "2024-10-19T10:30:00Z",
                    }
                }
            },
        },
        400: {
            "description": "Invalid input or email already registered",
            "content": {"application/json": {"example": {"detail": "Email already registered"}}},
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {"detail": "Password must be at least 8 characters"}
                }
            },
        },
    },
)
async def register(request: RegisterRequest) -> dict[str, Any]:
    """
    Register a new user account.

    This endpoint is publicly accessible and does not require authentication.
    """
    # TODO: Implement actual registration logic
    # For now, return placeholder response
    return {
        "id": "user-placeholder",
        "email": request.email,
        "name": request.full_name,
        "is_admin": False,
        "created_at": "2024-10-19T10:30:00Z",
    }


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="""
    Authenticate user and generate access tokens.

    ## Process:
    1. Validates user credentials (email + password)
    2. Generates JWT access token (expires in 1 hour)
    3. Generates refresh token (expires in 7 days)
    4. Returns both tokens for client storage

    ## Security:
    - Password hashing: bcrypt with 12 rounds
    - JWT signing: HS256 algorithm
    - Rate limiting: 5 attempts per 15 minutes per IP
    - Account lockout: After 5 failed attempts

    ## Token Usage:
    Store access_token securely and include in all API requests:
    ```
    Authorization: Bearer <access_token>
    ```

    When access_token expires, use refresh_token to obtain new tokens via `/refresh` endpoint.
    """,
    responses={
        200: {
            "description": "Login successful, tokens generated",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "expires_in": 3600,
                        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    }
                }
            },
        },
        400: {
            "description": "Invalid request data",
            "model": ErrorResponse,
            "content": {"application/json": {"example": {"detail": "Invalid email format"}}},
        },
        401: {
            "description": "Invalid credentials",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_credentials": {
                            "summary": "Wrong password",
                            "value": {"detail": "Invalid email or password"},
                        },
                        "account_locked": {
                            "summary": "Too many failed attempts",
                            "value": {
                                "detail": "Account locked due to too many failed login attempts. Try again in 15 minutes."
                            },
                        },
                    }
                }
            },
        },
        429: {
            "description": "Too many requests",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Too many login attempts. Please try again in 15 minutes."
                    }
                }
            },
        },
    },
)
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """
    Authenticate user and generate access tokens.

    Args:
        credentials: User email and password

    Returns:
        Access token, refresh token, and token metadata

    Raises:
        HTTPException(400): Invalid email format
        HTTPException(401): Invalid credentials or account locked
        HTTPException(429): Too many login attempts
    """
    import logging
    import os

    # IMMEDIATE DEBUG at very start of function
    debug_file = os.path.join(os.path.dirname(__file__), "..", "..", "login_debug.log")
    with open(debug_file, "a") as f:
        f.write(f"\n=== LOGIN FUNCTION ENTERED at {datetime.now(timezone.utc)} ===\n")
        f.write(f"credentials.email={credentials.email}\n")

    logger = logging.getLogger(__name__)

    try:
        # Find user by email (case-insensitive) with roles loaded
        logger.info(f"Attempting login for email: {credentials.email.lower()}")
        result = await db.execute(
            select(User)
            .where(User.email == credentials.email.lower())
            .options(selectinload(User.user_roles))
        )
        user = result.scalar_one_or_none()
        logger.info(f"User found: {user is not None}")
    except Exception as e:
        logger.error(f"Database error during login: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )

    # User not found
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    # Check account status
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {user.status.value.lower()}",
        )

    # Check password (password_hash may be NULL for OAuth-only users)
    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account uses Google OAuth. Please login with Google.",
        )

    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    # =========================================================================
    # ENRICH TOKEN WITH ROLE, STATION_IDS, AND CHEF_ID
    # Per 25-TOKEN_AUTHENTICATION_STANDARDS.instructions.md
    # =========================================================================

    # 1. Get user's primary role by querying UserRole -> Role
    user_role = None
    try:
        role_result = await db.execute(
            select(Role.role_type)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user.id)
            .limit(1)  # Take first/primary role
        )
        role_row = role_result.scalar_one_or_none()
        if role_row:
            # role_type is an enum, get its string value
            user_role = role_row.value if hasattr(role_row, "value") else str(role_row)
            logger.debug(f"User {user.email} has role: {user_role}")
    except Exception as e:
        logger.warning(f"Failed to load role for user {user.email}: {e}")

    # 2. Get user's station_ids from StationUser table
    station_ids = []
    try:
        station_result = await db.execute(
            select(StationUser.station_id).where(
                StationUser.user_id == user.id, StationUser.is_active == True
            )
        )
        station_ids = [str(row[0]) for row in station_result.fetchall()]
        logger.debug(f"User {user.email} has station_ids: {station_ids}")
    except Exception as e:
        logger.warning(f"Failed to load station_ids for user {user.email}: {e}")

    # 3. Get chef_id if user is a CHEF (Chef links via email, not user_id)
    chef_id = None
    if user_role and user_role.upper() == "CHEF":
        try:
            chef_result = await db.execute(select(Chef.id).where(Chef.email == user.email))
            chef_row = chef_result.scalar_one_or_none()
            if chef_row:
                chef_id = str(chef_row)
                logger.debug(f"User {user.email} has chef_id: {chef_id}")
        except Exception as e:
            logger.warning(f"Failed to load chef_id for user {user.email}: {e}")

    # Create access token with enriched user info (role, stations, chef_id)
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "is_super_admin": user.is_super_admin,
    }

    # Add role if available
    if user_role:
        token_data["role"] = user_role

    # Add station_ids if available (for STATION_MANAGER filtering)
    if station_ids:
        token_data["station_ids"] = station_ids

    # Add chef_id if available (for CHEF filtering)
    if chef_id:
        token_data["chef_id"] = chef_id

    # Create UserSession record for station-aware authentication
    # This is required for endpoints using get_current_station_user dependency
    session_id = uuid4()
    session_token = secrets.token_urlsafe(48)
    access_token_jti = str(uuid4())
    refresh_token_jti = str(uuid4())

    # Add session_id to token data for station-aware endpoints
    token_data["session_id"] = str(session_id)
    token_data["jti"] = access_token_jti

    logger.info(
        f"Creating token for {user.email} with role={user_role}, stations={len(station_ids)}, chef_id={chef_id is not None}, session_id={session_id}"
    )

    # DEBUG: Early file logging to trace where failure occurs
    import os

    debug_file = os.path.join(os.path.dirname(__file__), "..", "..", "login_debug.log")
    with open(debug_file, "a") as f:
        f.write(f"\n=== LOGIN ATTEMPT at {datetime.now(timezone.utc)} ===\n")
        f.write(f"STEP 1: About to create access token for user.email={user.email}\n")
        f.write(f"token_data={token_data}\n")

    try:
        access_token = create_access_token(data=token_data)
        with open(debug_file, "a") as f:
            f.write("STEP 2: access_token created successfully\n")
    except Exception as e:
        import traceback

        with open(debug_file, "a") as f:
            f.write(f"ERROR in create_access_token: {e}\n")
            f.write(f"Traceback:\n{traceback.format_exc()}\n")
        raise HTTPException(status_code=500, detail=f"Access token creation failed: {str(e)}")

    # Create refresh token with separate secret and longer expiry (7 days)
    try:
        refresh_token = create_refresh_token(user_id=str(user.id))
        with open(debug_file, "a") as f:
            f.write("STEP 3: refresh_token created successfully\n")
    except Exception as e:
        import traceback

        with open(debug_file, "a") as f:
            f.write(f"ERROR in create_refresh_token: {e}\n")
            f.write(f"Traceback:\n{traceback.format_exc()}\n")
        raise HTTPException(status_code=500, detail=f"Refresh token creation failed: {str(e)}")

    # Hash refresh token for storage
    refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    with open(debug_file, "a") as f:
        f.write("STEP 4: refresh_token hashed\n")

    # Create UserSession record in database
    session_expires = datetime.now(timezone.utc) + timedelta(days=7)

    # DEBUG: Write to file for debugging (user can't see terminal)
    import os

    debug_file = os.path.join(os.path.dirname(__file__), "..", "..", "login_debug.log")
    with open(debug_file, "a") as f:
        f.write(f"\n=== LOGIN ATTEMPT at {datetime.now(timezone.utc)} ===\n")
        f.write(f"user.email={user.email}\n")
        f.write(f"session_id={session_id}\n")
        f.write(f"user_id={user.id}\n")
        f.write(f"access_token_jti={access_token_jti}\n")
        f.write(f"refresh_token_jti={refresh_token_jti}\n")

    try:
        user_session = UserSession(
            id=session_id,
            user_id=user.id,
            session_token=session_token,
            refresh_token_hash=refresh_token_hash,
            access_token_jti=access_token_jti,
            refresh_token_jti=refresh_token_jti,
            status="active",
            expires_at=session_expires,
        )
        with open(debug_file, "a") as f:
            f.write("UserSession object created, adding to db...\n")
        db.add(user_session)
        with open(debug_file, "a") as f:
            f.write("db.add() complete, committing...\n")
        await db.commit()
        with open(debug_file, "a") as f:
            f.write("commit() successful!\n")
        logger.info(f"Created UserSession {session_id} for user {user.email}")
    except Exception as e:
        import traceback

        tb = traceback.format_exc()
        with open(debug_file, "a") as f:
            f.write(f"ERROR: Failed to create UserSession: {e}\n")
            f.write(f"Traceback:\n{tb}\n")
        # Re-raise with more detail for HTTP response
        raise HTTPException(status_code=500, detail=f"Session creation failed: {str(e)}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token": refresh_token,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "is_super_admin": user.is_super_admin,
            "role": user_role,  # Include role for frontend navigation
            "station_ids": (
                station_ids if station_ids else None
            ),  # Include station_ids for STATION_MANAGER
            "chef_id": chef_id,  # Include chef_id for CHEF role
        },
    }


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user information",
    description="""
    Retrieve information about the currently authenticated user.

    ## Authentication Required:
    This endpoint requires a valid JWT Bearer token in the Authorization header.

    ## Use Cases:
    - Display user profile
    - Check user permissions
    - Verify authentication status
    - Get user ID for other API calls

    ## Response:
    Returns complete user profile including role and account creation date.
    """,
    responses={
        200: {
            "description": "User information retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "user-abc123",
                        "email": "john@example.com",
                        "name": "John Doe",
                        "is_admin": False,
                        "created_at": "2024-10-19T10:30:00Z",
                    }
                }
            },
        },
        401: {
            "description": "Authentication required",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "missing_token": {
                            "summary": "No token provided",
                            "value": {"detail": "Not authenticated"},
                        },
                        "invalid_token": {
                            "summary": "Invalid or expired token",
                            "value": {"detail": "Invalid authentication credentials"},
                        },
                    }
                }
            },
        },
    },
)
async def get_current_user_info(
    current_user: dict[str, Any] = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Get current user information.

    Returns:
        User profile with id, email, name, role, and creation date

    Raises:
        HTTPException(401): Missing or invalid authentication token
    """
    # Get user from database to fetch full profile
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Determine admin status from role (handles both string and enum)
    role = current_user.get("role")
    if role:
        # Normalize role to string
        role_str = role.value if hasattr(role, "value") else str(role)
        role_normalized = role_str.lower().replace("_", "")
        is_admin = role_normalized in ("superadmin", "admin", "stationmanager")
    else:
        is_admin = False

    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.full_name or user.email,
        "is_admin": is_admin or user.is_super_admin,
        "created_at": (user.created_at.isoformat() if user.created_at else "2024-01-01T00:00:00Z"),
    }


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="User logout",
    description="""
    Logout user and invalidate tokens.

    ## Process:
    1. Invalidates current access token
    2. Invalidates refresh token
    3. Removes user session from cache
    4. Logs logout event for security audit

    ## Client Actions Required:
    After successful logout, client should:
    - Remove stored access_token
    - Remove stored refresh_token
    - Redirect to login page
    - Clear any cached user data

    ## Note:
    This endpoint still requires authentication (the token being invalidated).
    """,
    responses={
        200: {
            "description": "Logout successful",
            "content": {"application/json": {"example": {"message": "Logged out successfully"}}},
        },
        401: {
            "description": "Authentication required",
            "model": ErrorResponse,
        },
    },
)
async def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Logout user and invalidate tokens.

    This endpoint:
    1. Extracts JTI from the current access token
    2. Adds the JTI to the blacklist (Redis + DB)
    3. Token becomes invalid for future requests

    Returns:
        Success message

    Raises:
        HTTPException(401): Missing or invalid authentication token
    """
    try:
        token = credentials.credentials
        payload = decode_access_token(token)

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        jti = payload.get("jti")
        user_id = payload.get("user_id") or payload.get("sub")
        exp = payload.get("exp")

        if not jti:
            # Token without JTI - still accept logout but log warning
            logger.warning(f"Logout with token missing JTI for user {user_id}")
            return {"message": "Logged out successfully"}

        # Get cache from app state
        cache = getattr(request.app.state, "cache", None)

        # Blacklist the token
        blacklist_service = TokenBlacklistService(db=db, cache=cache)
        await blacklist_service.blacklist_token(
            jti=jti,
            user_id=str(user_id) if user_id else None,
            token_type="access",
            expires_at_unix=exp,
            reason="user_logout",
        )

        logger.info(f"User {user_id} logged out successfully, token {jti[:8]}... blacklisted")
        return {"message": "Logged out successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Logout error: {e}")
        # Don't fail logout - user intent is clear
        return {"message": "Logged out successfully"}


@router.post(
    "/logout-all-devices",
    summary="Logout from all devices",
    description="""
    Invalidate ALL tokens for the current user.

    ## Use Cases:
    - Security concern (account may be compromised)
    - Changed password and want to force re-login everywhere
    - Lost a device with saved login

    ## Process:
    1. Identifies the current user from their access token
    2. Blacklists ALL tokens for that user (access + refresh)
    3. All other sessions become invalid immediately
    4. User must re-authenticate on all devices

    ## Returns:
    - Success message with count of invalidated sessions
    """,
    responses={
        200: {
            "description": "All sessions invalidated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "All sessions invalidated",
                        "sessions_invalidated": 5,
                    }
                }
            },
        },
        401: {
            "description": "Invalid or expired authentication token",
            "model": ErrorResponse,
        },
    },
)
async def logout_all_devices(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Logout from all devices by invalidating all user tokens.

    This is the "nuclear option" for security - use when:
    - User suspects account compromise
    - User changed password
    - User lost a device
    """
    try:
        token = credentials.credentials
        payload = decode_access_token(token)

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        user_id = payload.get("user_id") or payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing user identifier",
            )

        # Get cache from app state
        cache = getattr(request.app.state, "cache", None)

        # Blacklist ALL tokens for this user
        blacklist_service = TokenBlacklistService(db=db, cache=cache)
        count = await blacklist_service.blacklist_all_user_tokens(
            user_id=str(user_id),
            reason="logout_all_devices",
        )

        logger.info(f"User {user_id} logged out from all devices, {count} tokens blacklisted")
        return {"message": "All sessions invalidated", "sessions_invalidated": count}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Logout all devices error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to logout from all devices",
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="""
    Generate new access token using refresh token.

    ## When to Use:
    - Access token has expired (401 error)
    - Proactively before expiration
    - After long period of inactivity

    ## Process:
    1. Validates refresh token
    2. Generates new access token (1 hour expiry)
    3. Optionally generates new refresh token (7 days expiry)
    4. Returns new tokens

    ## Security:
    - Refresh tokens are single-use only
    - Old refresh token is immediately invalidated
    - New refresh token must be stored

    ## Request Body:
    ```json
    {
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```
    """,
    responses={
        200: {"description": "Tokens refreshed successfully"},
        401: {
            "description": "Invalid or expired refresh token",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "expired": {
                            "summary": "Refresh token expired",
                            "value": {"detail": "Refresh token has expired. Please login again."},
                        },
                        "invalid": {
                            "summary": "Invalid token",
                            "value": {"detail": "Invalid refresh token"},
                        },
                        "already_used": {
                            "summary": "Token already used",
                            "value": {
                                "detail": "Refresh token has already been used. Please login again."
                            },
                        },
                    }
                }
            },
        },
    },
)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Generate new access token using refresh token.

    Implements secure token rotation:
    1. Validates the refresh token with separate secret
    2. Checks if token is blacklisted
    3. Creates new access token
    4. Rotates refresh token (new token, blacklists old one)
    5. Returns new token pair

    Args:
        refresh_token: Valid refresh token from login response
        db: Database session

    Returns:
        New access token and refresh token

    Raises:
        HTTPException(401): Invalid, expired, or already used refresh token
    """
    from services.token_blacklist_service import TokenBlacklistService

    # 1. Verify the refresh token
    payload = verify_refresh_token(refresh_token)
    if payload is None:
        logger.warning("🔒 Refresh token verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token. Please login again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Check if token is blacklisted
    jti = payload.get("jti")
    if jti:
        blacklist_service = TokenBlacklistService(db)
        is_blacklisted = await blacklist_service.is_blacklisted(jti)
        if is_blacklisted:
            logger.warning(f"🔒 Attempt to use blacklisted refresh token: {jti[:8]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has already been used. Please login again.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # 3. Extract user info
    user_id = payload.get("sub")
    if not user_id:
        logger.error("🔒 Refresh token missing user ID")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token. Please login again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. Blacklist the old refresh token (token rotation)
    if jti:
        try:
            await blacklist_service.blacklist_token(
                jti=jti,
                user_id=user_id,
                token_type="refresh",
                reason="token_rotation",
                expires_at=datetime.fromtimestamp(payload.get("exp", 0)),
            )
            logger.info(f"✅ Rotated refresh token for user {user_id[:8]}...")
        except Exception as e:
            logger.warning(f"⚠️ Failed to blacklist old refresh token: {e}")
            # Continue anyway - the new token will still be valid

    # 5. Get user info for new tokens using SQL query (same pattern as login)
    # The User model has relationships, not direct role/station_id attributes
    from sqlalchemy import text

    query = text(
        """
        SELECT u.id, u.email, u.status, r.role_type as role,
               su.station_id
        FROM identity.users u
        LEFT JOIN identity.user_roles ur ON u.id = ur.user_id
        LEFT JOIN identity.roles r ON ur.role_id = r.id
        LEFT JOIN identity.station_users su ON u.id = su.user_id
        WHERE u.id = :user_id
    """
    )
    result = await db.execute(query, {"user_id": user_id})
    user_row = result.fetchone()

    if not user_row:
        logger.error(f"🔒 User not found for refresh: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found. Please login again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db_user_id, email, user_status, role, station_id = user_row

    # Check if user is still active
    status_str = str(user_status).upper() if user_status else ""
    if "ACTIVE" not in status_str:
        logger.warning(f"🔒 Inactive user attempted refresh: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated. Please contact support.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Map role to UserRole enum value (UPPERCASE to match login endpoint)
    from core.config import UserRole

    role_str = str(role).upper() if role else "CUSTOMER_SUPPORT"
    role_mapping = {
        "SUPER_ADMIN": UserRole.SUPER_ADMIN,
        "ADMIN": UserRole.ADMIN,
        "MANAGER": UserRole.CUSTOMER_SUPPORT,
        "CUSTOMER_SUPPORT": UserRole.CUSTOMER_SUPPORT,
        "STAFF": UserRole.STATION_MANAGER,
        "STATION_MANAGER": UserRole.STATION_MANAGER,
        "CHEF": UserRole.CHEF,
    }
    user_role = role_mapping.get(role_str, UserRole.CUSTOMER_SUPPORT)

    # 6. Create new access token
    access_token_data = {
        "sub": str(db_user_id),
        "email": email,
        "role": user_role.value,  # Use .value for uppercase string
    }
    if station_id:
        access_token_data["station_id"] = str(station_id)

    new_access_token = create_access_token(data=access_token_data)

    # 7. Create new refresh token (rotation)
    new_refresh_token = create_refresh_token(user_id=str(db_user_id))

    logger.info(f"✅ Token refresh successful for user {email}")

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token": new_refresh_token,
    }


# Schema for password reset request
class PasswordResetRequest(BaseModel):
    """Request body for requesting password reset."""

    email: EmailStr = Field(..., description="Email address to send reset link")

    model_config = {"json_schema_extra": {"examples": [{"email": "user@example.com"}]}}


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description="""
    Request a password reset link via email.

    ## Process:
    1. Validates email exists in system
    2. Generates secure reset token (expires in 1 hour)
    3. Sends reset link to user's email
    4. Logs security event

    ## Security:
    - Rate limited: 3 requests per hour per email
    - Token expires in 1 hour
    - One-time use only
    - Email verification required
    - No user enumeration (always returns success)

    ## Reset Link Format:
    ```
    https://myhibachichef.com/reset-password?token=<reset_token>
    ```

    ## Request Body:
    ```json
    {
        "email": "john@example.com"
    }
    ```
    """,
    responses={
        200: {
            "description": "Reset email sent (if account exists)",
            "content": {
                "application/json": {
                    "example": {
                        "message": "If an account with that email exists, a password reset link has been sent."
                    }
                }
            },
        },
        400: {"description": "Invalid email format", "model": ErrorResponse},
        429: {
            "description": "Too many reset requests",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Too many password reset requests. Please try again in 1 hour."
                    }
                }
            },
        },
    },
)
async def reset_password(
    request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Request password reset link.

    Args:
        request: Password reset request with email address
        db: Database session

    Returns:
        Success message (always returns success for security)

    Raises:
        HTTPException(400): Invalid email format
        HTTPException(429): Too many reset requests
    """
    try:
        service = PasswordResetService(db)
        await service.request_reset(request.email)
    except HTTPException:
        # Re-raise HTTP exceptions (rate limiting, etc.)
        raise
    except Exception as e:
        # Log error but don't expose details (security)
        logger.error(f"Password reset error for {request.email}: {e}")

    # Always return success to prevent user enumeration
    return {"message": "If an account with that email exists, a password reset link has been sent."}


# Schema for confirm password reset request
class ConfirmPasswordResetRequest(BaseModel):
    """Request body for confirming password reset."""

    token: str = Field(..., description="Password reset token from email link")
    new_password: str = Field(
        ...,
        min_length=8,
        description="New password (min 8 chars, must include upper, lower, number)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{"token": "abc123xyz789...", "new_password": "NewSecurePass123!"}]
        }
    }


@router.post(
    "/confirm-reset-password",
    status_code=status.HTTP_200_OK,
    summary="Confirm password reset with token",
    description="""
    Complete password reset using the token from the email link.

    ## Process:
    1. Validates reset token (not expired, not used)
    2. Verifies new password meets requirements
    3. Updates user password (hashed)
    4. Invalidates all existing sessions (security)
    5. Marks token as used (one-time use)
    6. Logs security event

    ## Password Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number

    ## Security:
    - Token expires in 1 hour
    - Token is one-time use only
    - All existing sessions are invalidated
    - Password is hashed with bcrypt

    ## Request Body:
    ```json
    {
        "token": "abc123xyz789...",
        "new_password": "NewSecurePass123!"
    }
    ```
    """,
    responses={
        200: {
            "description": "Password reset successful",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Password has been reset successfully. Please login with your new password."
                    }
                }
            },
        },
        400: {
            "description": "Invalid or expired token",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid or expired reset token. Please request a new one."
                    }
                }
            },
        },
        422: {
            "description": "Invalid password format",
            "model": ErrorResponse,
        },
    },
)
async def confirm_reset_password(
    request: ConfirmPasswordResetRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Confirm password reset with token from email.

    Args:
        request: Token and new password
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException(400): Invalid or expired token
        HTTPException(422): Invalid password format
    """
    service = PasswordResetService(db)
    success = await service.reset_password(token=request.token, new_password=request.new_password)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token. Please request a new one.",
        )

    return {"message": "Password has been reset successfully. Please login with your new password."}
