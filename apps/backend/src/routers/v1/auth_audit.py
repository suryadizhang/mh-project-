"""
Authentication router with security audit logging
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import create_access_token, verify_password, get_password_hash
from models.user import User, UserStatus
from services.audit_service import get_audit_service, AuditService
from sqlalchemy import select

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_client_info(request: Request) -> dict:
    """Extract client information for audit logging."""
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    audit_service: AuditService = Depends(get_audit_service),
):
    """
    Login endpoint with security audit logging.

    Logs:
    - Successful logins
    - Failed login attempts (wrong password, user not found, account locked)
    - Failed MFA attempts
    """

    client_info = await get_client_info(request)

    # Find user by email
    result = await db.execute(select(User).where(User.email == form_data.username.lower()))
    user = result.scalar_one_or_none()

    # User not found
    if not user:
        await audit_service.log_security_event(
            event_type="LOGIN",
            description=f"Failed login attempt - user not found: {form_data.username}",
            success=False,
            failure_reason="User not found",
            **client_info,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
        )

    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        await audit_service.log_security_event(
            event_type="LOGIN",
            description=f"Failed login attempt - account locked: {user.email}",
            user_id=user.id,
            success=False,
            failure_reason=f"Account locked until {user.locked_until.isoformat()}",
            **client_info,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account locked until {user.locked_until.isoformat()}",
        )

    # Check account status
    if user.status != UserStatus.ACTIVE:
        await audit_service.log_security_event(
            event_type="LOGIN",
            description=f"Failed login attempt - account {user.status.value}: {user.email}",
            user_id=user.id,
            success=False,
            failure_reason=f"Account status: {user.status.value}",
            **client_info,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Account is {user.status.value}"
        )

    # Verify password
    if not verify_password(form_data.password, user.hashed_password):
        # Increment failed login attempts
        user.failed_login_attempts += 1

        # Lock account after 5 failed attempts (lock for 30 minutes)
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            await db.commit()

            await audit_service.log_security_event(
                event_type="LOGIN",
                description=f"Account locked after {user.failed_login_attempts} failed attempts: {user.email}",
                user_id=user.id,
                success=False,
                failure_reason="Too many failed attempts - account locked",
                metadata={"failed_attempts": user.failed_login_attempts},
                **client_info,
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account locked due to too many failed login attempts",
            )

        await db.commit()

        await audit_service.log_security_event(
            event_type="LOGIN",
            description=f"Failed login attempt - wrong password: {user.email}",
            user_id=user.id,
            success=False,
            failure_reason="Wrong password",
            metadata={"failed_attempts": user.failed_login_attempts},
            **client_info,
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
        )

    # Reset failed login attempts on successful password verification
    user.failed_login_attempts = 0
    user.last_login_at = datetime.utcnow()
    user.last_login_ip = client_info["ip_address"]
    user.last_activity_at = datetime.utcnow()
    await db.commit()

    # Check if 2FA is enabled
    if user.mfa_enabled:
        # Return temporary token for 2FA verification
        # (Implementation depends on 2FA service)
        await audit_service.log_security_event(
            event_type="LOGIN",
            description=f"Login successful (2FA required): {user.email}",
            user_id=user.id,
            success=True,
            metadata={"mfa_required": True},
            **client_info,
        )

        return {
            "requires_mfa": True,
            "temp_token": create_access_token(
                data={"sub": str(user.id), "mfa_pending": True}, expires_delta=timedelta(minutes=5)
            ),
        }

    # Create access token
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})

    # Log successful login
    await audit_service.log_security_event(
        event_type="LOGIN",
        description=f"Successful login: {user.email}",
        user_id=user.id,
        success=True,
        **client_info,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "is_super_admin": user.is_super_admin,
        },
    }


@router.post("/logout")
async def logout(
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    audit_service: AuditService = Depends(get_audit_service),
    current_user: User = Depends(get_current_user),  # Requires auth
):
    """
    Logout endpoint with security audit logging.
    """

    client_info = await get_client_info(request)

    # Log logout event
    await audit_service.log_security_event(
        event_type="LOGOUT",
        description=f"User logout: {current_user.email}",
        user_id=current_user.id,
        success=True,
        **client_info,
    )

    return {"message": "Successfully logged out"}


@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    audit_service: AuditService = Depends(get_audit_service),
    current_user: User = Depends(get_current_user),
):
    """
    Change password endpoint with security audit logging.
    """

    client_info = await get_client_info(request)

    # Verify old password
    if not verify_password(old_password, current_user.hashed_password):
        await audit_service.log_security_event(
            event_type="PASSWORD_CHANGE",
            description=f"Failed password change - wrong old password: {current_user.email}",
            user_id=current_user.id,
            success=False,
            failure_reason="Wrong old password",
            **client_info,
        )

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong password")

    # Update password
    current_user.hashed_password = get_password_hash(new_password)
    current_user.password_changed_at = datetime.utcnow()
    await db.commit()

    # Log password change
    await audit_service.log_security_event(
        event_type="PASSWORD_CHANGE",
        description=f"Password changed successfully: {current_user.email}",
        user_id=current_user.id,
        success=True,
        **client_info,
    )

    return {"message": "Password changed successfully"}
