"""
Authentication endpoints for login, logout, MFA, and user management.
"""

import base64
from datetime import datetime
from typing import Any
from uuid import uuid4

from api.app.auth.middleware import (
    AuthenticatedUser,
    audit_log_action,
    get_current_active_user,
    rate_limit,
    require_permission,
)
from api.app.auth.models import (
    AuthenticationService,
    Permission,
    Role,
    SessionStatus,
    User,
    UserSession,
    UserStatus,
)
from api.app.database import get_db_session
from api.app.utils.encryption import FieldEncryption
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import and_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth", tags=["Authentication"])


# Request/Response Models
class LoginRequest(BaseModel):
    """Login request model."""

    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=1, max_length=200)
    mfa_token: str | None = Field(None, pattern=r"^[0-9]{6}$")
    remember_me: bool = False


class LoginResponse(BaseModel):
    """Login response model."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    mfa_required: bool = False
    user: dict[str, Any]


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""

    refresh_token: str


class MFASetupResponse(BaseModel):
    """MFA setup response."""

    secret: str
    qr_code: str  # Base64 encoded image
    backup_codes: list[str]


class EnableMFARequest(BaseModel):
    """Enable MFA request."""

    verification_code: str = Field(..., pattern=r"^[0-9]{6}$")


class CreateUserRequest(BaseModel):
    """Create user request."""

    username: str = Field(..., min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")
    password: str = Field(..., min_length=8, max_length=200)
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, pattern=r"^\+?[\d\s\-\(\)]+$")
    role: Role = Role.STAFF


class ChangePasswordRequest(BaseModel):
    """Change password request."""

    current_password: str
    new_password: str = Field(..., min_length=8, max_length=200)

    @field_validator("new_password")
    def passwords_must_differ(cls, v, info):
        if "current_password" in info.data and v == info.data["current_password"]:
            raise ValueError("New password must be different from current password")
        return v


class PasswordResetRequestModel(BaseModel):
    """Password reset request."""

    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")


class PasswordResetConfirmModel(BaseModel):
    """Password reset confirmation."""

    token: str
    new_password: str = Field(..., min_length=8, max_length=200)


# Initialize services
def get_auth_service() -> AuthenticationService:
    """Get authentication service instance."""
    from core.config import get_settings

    settings = get_settings()
    return AuthenticationService(
        FieldEncryption(), jwt_secret=settings.secret_key  # From environment variable JWT_SECRET
    )


@router.post("/login", response_model=LoginResponse)
@rate_limit(max_requests=5, window_seconds=300, per_user=False)  # 5 attempts per 5 minutes per IP
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db_session),
    auth_service: AuthenticationService = Depends(get_auth_service),
):
    """Authenticate user and create session."""

    try:
        # Find user by username
        stmt = select(User).where(User.username == login_data.username)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            # Log failed attempt
            await audit_log_action(
                "LOGIN_FAILED",
                None,
                db,
                details={"username": login_data.username, "reason": "user_not_found"},
                success=False,
                error_message="User not found",
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password"
            )

        # Check if account is locked
        if user.lockout_until and user.lockout_until > datetime.utcnow():
            await audit_log_action(
                "LOGIN_FAILED",
                None,
                db,
                details={"username": login_data.username, "reason": "account_locked"},
                success=False,
                error_message="Account locked",
            )
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is temporarily locked due to multiple failed login attempts",
            )

        # Verify password
        if not auth_service.verify_password(
            login_data.password, user.password_hash, user.password_salt
        ):
            # Increment failed attempts
            user.failed_login_attempts += 1
            user.last_failed_login = datetime.utcnow()

            # Lock account if too many attempts
            if user.failed_login_attempts >= auth_service.max_failed_attempts:
                user.lockout_until = datetime.utcnow() + auth_service.lockout_duration

            await db.commit()

            await audit_log_action(
                "LOGIN_FAILED",
                None,
                db,
                details={"username": login_data.username, "reason": "invalid_password"},
                success=False,
                error_message="Invalid password",
            )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password"
            )

        # Check user status
        if user.status != UserStatus.ACTIVE:
            await audit_log_action(
                "LOGIN_FAILED",
                None,
                db,
                details={"username": login_data.username, "reason": "inactive_account"},
                success=False,
                error_message="Account inactive",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Account is not active"
            )

        # Check MFA if enabled
        mfa_verified = True
        if user.mfa_enabled:
            if not login_data.mfa_token:
                # Return response indicating MFA is required
                return LoginResponse(
                    access_token="",
                    refresh_token="",
                    expires_in=0,
                    mfa_required=True,
                    user={"username": user.username, "mfa_enabled": True},
                )

            # Verify MFA token
            encryption = FieldEncryption()
            mfa_secret = encryption.decrypt(user.mfa_secret_encrypted)

            if not auth_service.verify_mfa_token(mfa_secret, login_data.mfa_token):
                # Check if it's a backup code
                if user.backup_codes_encrypted:
                    backup_codes = encryption.decrypt_json(user.backup_codes_encrypted)
                    code_valid, updated_codes = auth_service.verify_backup_code(
                        backup_codes, login_data.mfa_token
                    )

                    if code_valid:
                        user.backup_codes_encrypted = encryption.encrypt_json(updated_codes)
                        mfa_verified = True
                    else:
                        mfa_verified = False
                else:
                    mfa_verified = False

            if not mfa_verified:
                await audit_log_action(
                    "LOGIN_FAILED",
                    None,
                    db,
                    details={"username": login_data.username, "reason": "invalid_mfa"},
                    success=False,
                    error_message="Invalid MFA token",
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MFA token"
                )

        # Reset failed login attempts on successful login
        user.failed_login_attempts = 0
        user.last_failed_login = None
        user.lockout_until = None
        user.last_login_at = datetime.utcnow()
        user.last_active_at = datetime.utcnow()

        # Create session
        session_id = uuid4()
        session_token = auth_service.generate_session_token()

        # Generate JWT tokens
        access_token, refresh_token, access_jti, refresh_jti = auth_service.create_jwt_tokens(
            user, session_id
        )

        # Create session record
        session = UserSession(
            id=session_id,
            user_id=user.id,
            session_token=session_token,
            refresh_token_hash=auth_service.hash_refresh_token(refresh_token),
            access_token_jti=access_jti,
            refresh_token_jti=refresh_jti,
            device_fingerprint=auth_service.generate_device_fingerprint(
                request.headers.get("user-agent", ""), request.client.host
            ),
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host,
            mfa_verified=mfa_verified,
            mfa_verified_at=datetime.utcnow() if mfa_verified else None,
            expires_at=datetime.utcnow()
            + (
                auth_service.refresh_lifetime
                if login_data.remember_me
                else auth_service.session_lifetime
            ),
        )

        db.add(session)
        await db.commit()

        # Log successful login
        await audit_log_action(
            "LOGIN_SUCCESS",
            AuthenticatedUser(user, session, auth_service.get_user_permissions(user)),
            db,
            details={
                "username": user.username,
                "ip_address": request.client.host,
                "user_agent": request.headers.get("user-agent"),
                "mfa_used": user.mfa_enabled,
            },
            success=True,
        )

        # Prepare user data for response (decrypt sensitive fields)
        encryption = FieldEncryption()
        user_data = {
            "id": str(user.id),
            "username": user.username,
            "email": encryption.decrypt(user.email_encrypted),
            "role": user.role,
            "permissions": list(auth_service.get_user_permissions(user)),
            "mfa_enabled": user.mfa_enabled,
        }

        if user.first_name_encrypted:
            user_data["first_name"] = encryption.decrypt(user.first_name_encrypted)
        if user.last_name_encrypted:
            user_data["last_name"] = encryption.decrypt(user.last_name_encrypted)

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=900,  # 15 minutes
            user=user_data,
        )

    except HTTPException:
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login",
        )


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(
    request: Request,
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db_session),
    auth_service: AuthenticationService = Depends(get_auth_service),
):
    """Refresh access token using refresh token."""

    try:
        # Verify refresh token
        payload = auth_service.verify_jwt_token(refresh_data.refresh_token, "refresh")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        user_id = payload.get("sub")
        session_id = payload.get("session_id")
        refresh_jti = payload.get("jti")

        # Get user and session
        stmt = (
            select(User, UserSession)
            .join(UserSession, User.id == UserSession.user_id)
            .where(
                and_(
                    User.id == user_id,
                    UserSession.id == session_id,
                    UserSession.refresh_token_jti == refresh_jti,
                    UserSession.status == SessionStatus.ACTIVE.value,
                    UserSession.expires_at > datetime.utcnow(),
                )
            )
        )

        result = await db.execute(stmt)
        row = result.first()

        if not row:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

        user, session = row

        # Check if refresh token hash matches
        provided_hash = auth_service.hash_refresh_token(refresh_data.refresh_token)
        if session.refresh_token_hash != provided_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        # Generate new tokens
        new_access_token, new_refresh_token, new_access_jti, new_refresh_jti = (
            auth_service.create_jwt_tokens(user, session.id)
        )

        # Update session with new token info
        session.access_token_jti = new_access_jti
        session.refresh_token_jti = new_refresh_jti
        session.refresh_token_hash = auth_service.hash_refresh_token(new_refresh_token)
        session.last_used_at = datetime.utcnow()

        user.last_active_at = datetime.utcnow()

        await db.commit()

        # Prepare user data
        encryption = FieldEncryption()
        user_data = {
            "id": str(user.id),
            "username": user.username,
            "email": encryption.decrypt(user.email_encrypted),
            "role": user.role,
            "permissions": list(auth_service.get_user_permissions(user)),
            "mfa_enabled": user.mfa_enabled,
        }

        return LoginResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=900,
            user=user_data,
        )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during token refresh",
        )


@router.post("/logout")
async def logout(
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Logout current user and revoke session."""

    try:
        # Revoke current session
        current_user.session.status = SessionStatus.LOGGED_OUT
        current_user.session.updated_at = datetime.utcnow()

        await db.commit()

        # Log logout
        await audit_log_action(
            "LOGOUT",
            current_user,
            db,
            details={"session_id": str(current_user.session.id)},
            success=True,
        )

        return {"message": "Successfully logged out"}

    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during logout",
        )


@router.get("/me")
async def get_current_user_info(current_user: AuthenticatedUser = Depends(get_current_active_user)):
    """Get current user information."""

    encryption = FieldEncryption()
    user_data = {
        "id": str(current_user.id),
        "username": current_user.user.username,
        "email": encryption.decrypt(current_user.user.email_encrypted),
        "role": current_user.role.value,
        "permissions": list(current_user.permissions),
        "mfa_enabled": current_user.user.mfa_enabled,
        "last_login_at": current_user.user.last_login_at,
        "created_at": current_user.user.created_at,
    }

    if current_user.user.first_name_encrypted:
        user_data["first_name"] = encryption.decrypt(current_user.user.first_name_encrypted)
    if current_user.user.last_name_encrypted:
        user_data["last_name"] = encryption.decrypt(current_user.user.last_name_encrypted)
    if current_user.user.phone_encrypted:
        user_data["phone"] = encryption.decrypt(current_user.user.phone_encrypted)

    return {"user": user_data}


@router.post("/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    auth_service: AuthenticationService = Depends(get_auth_service),
):
    """Setup MFA for current user."""

    if current_user.user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is already enabled"
        )

    try:
        encryption = FieldEncryption()

        # Generate MFA secret
        secret = auth_service.generate_mfa_secret()
        email = encryption.decrypt(current_user.user.email_encrypted)

        # Generate QR code
        qr_code_bytes = auth_service.generate_mfa_qr_code(email, secret)
        qr_code_b64 = base64.b64encode(qr_code_bytes).decode()

        # Generate backup codes
        backup_codes = auth_service.generate_backup_codes()
        hashed_backup_codes = auth_service.hash_backup_codes(backup_codes)

        # Store in database (but don't enable yet)
        current_user.user.mfa_secret_encrypted = encryption.encrypt(secret)
        current_user.user.backup_codes_encrypted = encryption.encrypt_json(hashed_backup_codes)

        await db.commit()

        await audit_log_action(
            "MFA_SETUP_INITIATED",
            current_user,
            db,
            details={"backup_codes_generated": len(backup_codes)},
            success=True,
        )

        return MFASetupResponse(secret=secret, qr_code=qr_code_b64, backup_codes=backup_codes)

    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during MFA setup",
        )


@router.post("/mfa/enable")
async def enable_mfa(
    request_data: EnableMFARequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    auth_service: AuthenticationService = Depends(get_auth_service),
):
    """Enable MFA after verification."""

    if current_user.user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is already enabled"
        )

    if not current_user.user.mfa_secret_encrypted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="MFA must be set up first"
        )

    try:
        encryption = FieldEncryption()
        secret = encryption.decrypt(current_user.user.mfa_secret_encrypted)

        # Verify the token
        if not auth_service.verify_mfa_token(secret, request_data.verification_code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code"
            )

        # Enable MFA
        current_user.user.mfa_enabled = True
        await db.commit()

        await audit_log_action(
            "MFA_ENABLED", current_user, db, details={"verification_successful": True}, success=True
        )

        return {"message": "MFA enabled successfully"}

    except HTTPException:
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while enabling MFA",
        )


@router.post("/users")
@require_permission(Permission.USER_MANAGE)
async def create_user(
    user_data: CreateUserRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    auth_service: AuthenticationService = Depends(get_auth_service),
):
    """Create a new user account."""

    try:
        # Validate password strength
        password_valid, password_errors = auth_service.validate_password_strength(
            user_data.password
        )
        if not password_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Password does not meet requirements",
                    "errors": password_errors,
                },
            )

        encryption = FieldEncryption()

        # Check if username or email already exists
        stmt = select(User).where(
            or_(
                User.username == user_data.username,
                User.email_encrypted == encryption.encrypt(user_data.email),
            )
        )
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            if existing_user.username == user_data.username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists"
                )

        # Hash password
        password_hash, password_salt = auth_service.hash_password(user_data.password)

        # Create user
        new_user = User(
            username=user_data.username,
            email_encrypted=encryption.encrypt(user_data.email),
            password_hash=password_hash,
            password_salt=password_salt,
            role=user_data.role.value,
            status=UserStatus.ACTIVE.value,
            first_name_encrypted=(
                encryption.encrypt(user_data.first_name) if user_data.first_name else None
            ),
            last_name_encrypted=(
                encryption.encrypt(user_data.last_name) if user_data.last_name else None
            ),
            phone_encrypted=encryption.encrypt(user_data.phone) if user_data.phone else None,
        )

        db.add(new_user)
        await db.commit()

        await audit_log_action(
            "USER_CREATED",
            current_user,
            db,
            resource_type="user",
            resource_id=str(new_user.id),
            details={
                "username": user_data.username,
                "email": user_data.email,
                "role": user_data.role.value,
            },
            success=True,
        )

        return {
            "message": "User created successfully",
            "user_id": str(new_user.id),
            "username": user_data.username,
        }

    except HTTPException:
        raise
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already exists"
        )
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating user",
        )


__all__ = ["router"]
