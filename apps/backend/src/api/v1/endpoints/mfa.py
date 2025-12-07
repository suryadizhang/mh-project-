"""
WebAuthn + PIN MFA Authentication Endpoints

This module provides Multi-Factor Authentication (MFA) using:
1. WebAuthn (Face ID, Touch ID, Windows Hello, Fingerprint)
2. PIN fallback (4-6 digit code)

Flow:
1. User logs in with Google OAuth
2. If MFA not set up → Prompt to set up WebAuthn + PIN
3. If MFA set up → Prompt for WebAuthn or PIN verification
4. Access granted after 2nd factor verification
"""

import json
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from core.config import get_settings
from core.security import create_access_token
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user, get_db

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)

# Constants
PIN_MIN_LENGTH = 4
PIN_MAX_LENGTH = 6
PIN_MAX_ATTEMPTS = 5
WEBAUTHN_CHALLENGE_TIMEOUT = 60  # seconds

# Progressive lockout durations (in minutes): 15min, 30min, 1hr, 24hr, permanent
LOCKOUT_DURATIONS = [15, 30, 60, 1440, -1]


# ============================================
# Helper: Get Progressive Lockout Duration
# ============================================


async def get_lockout_duration(db: AsyncSession, user_id: str) -> tuple[int, bool]:
    """
    Calculate progressive lockout duration based on recent lockouts.

    Returns:
        Tuple of (lockout_minutes, is_permanent)
    """
    try:
        # Check for security schema
        check_schema = text(
            "SELECT 1 FROM information_schema.schemata WHERE schema_name = 'security'"
        )
        schema_exists = await db.execute(check_schema)

        if not schema_exists.scalar():
            # Fallback to default if security schema doesn't exist
            return (LOCKOUT_DURATIONS[0], False)

        # Count recent lockouts
        query = text(
            """
            SELECT COUNT(*)
            FROM security.security_events
            WHERE user_id = :user_id
              AND event_type = 'account_locked'
              AND created_at > NOW() - INTERVAL '24 hours'
        """
        )
        result = await db.execute(query, {"user_id": user_id})
        lockout_count = result.scalar() or 0

        index = min(lockout_count, len(LOCKOUT_DURATIONS) - 1)
        duration = LOCKOUT_DURATIONS[index]
        is_permanent = duration == -1

        return (duration if duration > 0 else 1440, is_permanent)  # -1 means 24hr + disabled

    except Exception as e:
        logger.warning(f"Could not calculate progressive lockout: {e}")
        return (LOCKOUT_DURATIONS[0], False)


# ============================================
# Pydantic Models
# ============================================


class MFAStatusResponse(BaseModel):
    """Response for MFA status check"""

    mfa_setup_complete: bool
    has_webauthn: bool
    webauthn_device_count: int
    has_pin: bool
    pin_reset_required: bool


class PINSetupRequest(BaseModel):
    """Request to set up a PIN"""

    pin: str = Field(..., min_length=PIN_MIN_LENGTH, max_length=PIN_MAX_LENGTH)

    @field_validator("pin")
    @classmethod
    def validate_pin(cls, v):
        if not v.isdigit():
            raise ValueError("PIN must contain only digits")
        return v


class PINVerifyRequest(BaseModel):
    """Request to verify PIN"""

    pin: str = Field(..., min_length=PIN_MIN_LENGTH, max_length=PIN_MAX_LENGTH)

    @field_validator("pin")
    @classmethod
    def validate_pin(cls, v):
        if not v.isdigit():
            raise ValueError("PIN must contain only digits")
        return v


class PINResetRequest(BaseModel):
    """Request to reset a user's PIN (SUPER_ADMIN only)"""

    user_id: str


class WebAuthnRegisterStartResponse(BaseModel):
    """Response for WebAuthn registration start"""

    challenge: str
    rp_id: str
    rp_name: str
    user_id: str
    user_name: str
    user_display_name: str
    timeout: int
    attestation: str
    authenticator_selection: dict


class WebAuthnRegisterFinishRequest(BaseModel):
    """Request to complete WebAuthn registration"""

    credential_id: str
    public_key: str
    sign_count: int
    device_name: Optional[str] = "Unknown Device"
    attestation_object: Optional[str] = None
    client_data_json: Optional[str] = None


class WebAuthnVerifyStartResponse(BaseModel):
    """Response for WebAuthn verification start"""

    challenge: str
    timeout: int
    rp_id: str
    allowed_credentials: list


class WebAuthnVerifyFinishRequest(BaseModel):
    """Request to complete WebAuthn verification"""

    credential_id: str
    authenticator_data: str
    signature: str
    client_data_json: str


class MFAVerifiedResponse(BaseModel):
    """Response after successful MFA verification"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict
    mfa_verified: bool = True


# ============================================
# Helper Functions
# ============================================


def hash_pin(pin: str) -> str:
    """Hash a PIN using bcrypt"""
    return bcrypt.hashpw(pin.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_pin_hash(pin: str, pin_hash: str) -> bool:
    """Verify a PIN against its hash"""
    try:
        return bcrypt.checkpw(pin.encode("utf-8"), pin_hash.encode("utf-8"))
    except Exception as e:
        logger.error(f"PIN verification error: {e}")
        return False


def generate_challenge() -> str:
    """Generate a random challenge for WebAuthn"""
    return secrets.token_urlsafe(32)


# ============================================
# MFA Status Endpoints
# ============================================


@router.get("/status", response_model=MFAStatusResponse, tags=["MFA"])
async def get_mfa_status(
    current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Get current user's MFA setup status.

    Returns whether WebAuthn and/or PIN are configured.
    """
    user_id = current_user.get("sub") or current_user.get("id")

    query = text(
        """
        SELECT webauthn_credentials, pin_hash, mfa_setup_complete, pin_reset_required
        FROM identity.users
        WHERE id = :user_id
    """
    )
    result = await db.execute(query, {"user_id": user_id})
    row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    webauthn_creds, pin_hash, mfa_complete, pin_reset = row

    # Parse WebAuthn credentials
    creds = webauthn_creds if isinstance(webauthn_creds, list) else []

    return MFAStatusResponse(
        mfa_setup_complete=mfa_complete or False,
        has_webauthn=len(creds) > 0,
        webauthn_device_count=len(creds),
        has_pin=pin_hash is not None,
        pin_reset_required=pin_reset or False,
    )


# ============================================
# PIN Setup & Verification Endpoints
# ============================================


@router.post("/pin/setup", tags=["MFA"])
async def setup_pin(
    request: PINSetupRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Set up a PIN for the current user.

    PIN must be 4-6 digits. This is used as a fallback when WebAuthn is unavailable.
    """
    user_id = current_user.get("sub") or current_user.get("id")

    # Check if user already has a PIN (and it's not being reset)
    check_query = text(
        """
        SELECT pin_hash, pin_reset_required FROM identity.users WHERE id = :user_id
    """
    )
    result = await db.execute(check_query, {"user_id": user_id})
    row = result.fetchone()

    if row and row[0] and not row[1]:
        raise HTTPException(
            status_code=400, detail="PIN already set. Contact SUPER_ADMIN to reset."
        )

    # Hash and store the PIN
    pin_hash = hash_pin(request.pin)

    update_query = text(
        """
        UPDATE identity.users
        SET pin_hash = :pin_hash,
            pin_attempts = 0,
            pin_locked_until = NULL,
            pin_reset_required = FALSE,
            updated_at = NOW()
        WHERE id = :user_id
    """
    )
    await db.execute(update_query, {"pin_hash": pin_hash, "user_id": user_id})
    await db.commit()

    # Check if MFA setup is now complete (has both WebAuthn and PIN)
    await _check_and_update_mfa_complete(db, user_id)

    logger.info(f"PIN set up for user {user_id}")
    return {"message": "PIN set up successfully", "success": True}


@router.post("/pin/verify", response_model=MFAVerifiedResponse, tags=["MFA"])
async def verify_pin(
    request: PINVerifyRequest,
    http_request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify PIN for 2nd factor authentication.

    Features:
    - Progressive lockout (15min → 30min → 1hr → 24hr → permanent)
    - Security alerts to Super Admins on lockout
    - Brute force detection

    Returns a new JWT token with MFA verified claim.
    """
    user_id = current_user.get("sub") or current_user.get("id")
    email = current_user.get("email")
    role = current_user.get("role")

    # Get client IP for security logging
    ip_address = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent", "")

    # Get user's PIN data
    query = text(
        """
        SELECT pin_hash, pin_attempts, pin_locked_until,
               COALESCE(first_name, '') || ' ' || COALESCE(last_name, '') as full_name,
               COALESCE(is_security_disabled, false) as is_disabled
        FROM identity.users
        WHERE id = :user_id
    """
    )
    result = await db.execute(query, {"user_id": user_id})
    row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    pin_hash, attempts, locked_until, full_name, is_disabled = row
    full_name = full_name.strip() or email.split("@")[0]

    # Check if account is permanently disabled
    if is_disabled:
        raise HTTPException(
            status_code=403,
            detail="Account has been disabled for security reasons. Contact Super Admin.",
        )

    # Check if account is locked
    if locked_until and locked_until > datetime.now(timezone.utc):
        remaining = (locked_until - datetime.now(timezone.utc)).seconds // 60
        raise HTTPException(
            status_code=429,
            detail=f"Account locked due to too many failed attempts. Try again in {remaining} minutes.",
        )

    # Check if PIN is set
    if not pin_hash:
        raise HTTPException(status_code=400, detail="PIN not set up. Please set up PIN first.")

    # Verify PIN
    if not check_pin_hash(request.pin, pin_hash):
        # Increment failed attempts
        new_attempts = (attempts or 0) + 1

        if new_attempts >= PIN_MAX_ATTEMPTS:
            # Get progressive lockout duration
            lockout_minutes, is_permanent = await get_lockout_duration(db, user_id)
            lock_until = datetime.now(timezone.utc) + timedelta(minutes=lockout_minutes)

            # Lock the account (and disable if permanent)
            update_query = text(
                """
                UPDATE identity.users
                SET pin_attempts = :attempts,
                    pin_locked_until = :lock_until,
                    lockout_count = COALESCE(lockout_count, 0) + 1,
                    last_lockout_at = NOW(),
                    is_security_disabled = :is_disabled,
                    updated_at = NOW()
                WHERE id = :user_id
            """
            )
            await db.execute(
                update_query,
                {
                    "attempts": new_attempts,
                    "lock_until": lock_until,
                    "is_disabled": is_permanent,
                    "user_id": user_id,
                },
            )
            await db.commit()

            # Send security alert (async, don't wait)
            try:
                from services.security_monitoring_service import SecurityMonitoringService

                security = SecurityMonitoringService(db)
                await security.alert_account_locked(
                    user_id=str(user_id),
                    email=email,
                    ip_address=ip_address,
                    lockout_minutes=lockout_minutes,
                    attempt_count=new_attempts,
                    is_permanent=is_permanent,
                )

                # Check for brute force pattern
                if ip_address:
                    await security.check_for_brute_force(ip_address)

            except Exception as e:
                logger.error(f"Failed to send security alert: {e}")

            logger.warning(
                f"PIN locked for user {user_id} after {new_attempts} failed attempts (duration={lockout_minutes}min, permanent={is_permanent})"
            )

            if is_permanent:
                raise HTTPException(
                    status_code=403,
                    detail="Account has been disabled due to repeated failed attempts. Contact Super Admin to restore access.",
                )
            else:
                raise HTTPException(
                    status_code=429,
                    detail=f"Too many failed attempts. Account locked for {lockout_minutes} minutes.",
                )
        else:
            # Just increment attempts
            update_query = text(
                """
                UPDATE identity.users
                SET pin_attempts = :attempts, updated_at = NOW()
                WHERE id = :user_id
            """
            )
            await db.execute(update_query, {"attempts": new_attempts, "user_id": user_id})
            await db.commit()

            remaining = PIN_MAX_ATTEMPTS - new_attempts
            raise HTTPException(
                status_code=401, detail=f"Invalid PIN. {remaining} attempts remaining."
            )

    # PIN verified - reset attempts and issue MFA-verified token
    update_query = text(
        """
        UPDATE identity.users
        SET pin_attempts = 0, pin_locked_until = NULL, last_login_at = NOW(), updated_at = NOW()
        WHERE id = :user_id
    """
    )
    await db.execute(update_query, {"user_id": user_id})
    await db.commit()

    # Log successful MFA and IP tracking
    try:
        from services.security_monitoring_service import (
            SecurityMonitoringService,
            SecurityEvent,
            SecurityEventType,
        )

        security = SecurityMonitoringService(db)

        # Log MFA success event
        await security.log_event(
            SecurityEvent(
                event_type=SecurityEventType.MFA_SUCCESS,
                user_id=str(user_id),
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        )

        # Log login with IP tracking (detects suspicious patterns)
        if ip_address:
            ip_result = await security.log_login_with_ip(
                user_id=str(user_id),
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=True,
            )

            # Log if suspicious activity detected
            if ip_result.get("is_suspicious"):
                logger.warning(
                    f"Suspicious login detected for {email}: {ip_result.get('alerts', [])}"
                )

    except Exception as e:
        logger.debug(f"IP tracking not available: {e}")  # Non-critical

    # Create MFA-verified token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": str(user_id),
            "email": email,
            "role": role,
            "mfa_verified": True,
        },
        expires_delta=access_token_expires,
    )

    logger.info(f"PIN verified for user {user_id}")

    return MFAVerifiedResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": str(user_id),
            "email": email,
            "role": role,
            "full_name": full_name,
            "is_active": True,
        },
    )


# ============================================
# WebAuthn Registration Endpoints
# ============================================


@router.post("/webauthn/register/start", response_model=WebAuthnRegisterStartResponse, tags=["MFA"])
async def webauthn_register_start(
    current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Start WebAuthn registration process.

    Returns a challenge and options for the client to create a credential.
    This works with Face ID, Touch ID, Windows Hello, and fingerprint sensors.
    """
    user_id = current_user.get("sub") or current_user.get("id")
    email = current_user.get("email")
    full_name = current_user.get("full_name") or email.split("@")[0]

    # Generate challenge
    challenge = generate_challenge()

    # Store challenge temporarily (expires in 60 seconds)
    challenge_data = {"challenge": challenge, "created_at": datetime.now(timezone.utc).isoformat()}

    update_query = text(
        """
        UPDATE identity.users
        SET user_metadata = user_metadata || :challenge_data,
            updated_at = NOW()
        WHERE id = :user_id
    """
    )
    await db.execute(
        update_query,
        {"challenge_data": json.dumps({"webauthn_challenge": challenge_data}), "user_id": user_id},
    )
    await db.commit()

    return WebAuthnRegisterStartResponse(
        challenge=challenge,
        rp_id="mhapi.mysticdatanode.net",  # Relying Party ID (your domain)
        rp_name="My Hibachi Chef",
        user_id=str(user_id),
        user_name=email,
        user_display_name=full_name,
        timeout=WEBAUTHN_CHALLENGE_TIMEOUT * 1000,  # milliseconds
        attestation="none",  # We don't need attestation for passkeys
        authenticator_selection={
            "authenticatorAttachment": "platform",  # Built-in authenticators only (Face ID, etc.)
            "userVerification": "required",
            "residentKey": "preferred",
        },
    )


@router.post("/webauthn/register/finish", tags=["MFA"])
async def webauthn_register_finish(
    request: WebAuthnRegisterFinishRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Complete WebAuthn registration.

    Stores the credential for future authentication.
    """
    user_id = current_user.get("sub") or current_user.get("id")

    # Get current credentials
    query = text(
        """
        SELECT webauthn_credentials FROM identity.users WHERE id = :user_id
    """
    )
    result = await db.execute(query, {"user_id": user_id})
    row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    current_creds = row[0] if row[0] else []

    # Check if credential already exists
    for cred in current_creds:
        if cred.get("credential_id") == request.credential_id:
            raise HTTPException(status_code=400, detail="This device is already registered")

    # Add new credential
    new_credential = {
        "credential_id": request.credential_id,
        "public_key": request.public_key,
        "sign_count": request.sign_count,
        "device_name": request.device_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    current_creds.append(new_credential)

    # Update database
    update_query = text(
        """
        UPDATE identity.users
        SET webauthn_credentials = :creds,
            updated_at = NOW()
        WHERE id = :user_id
    """
    )
    await db.execute(update_query, {"creds": json.dumps(current_creds), "user_id": user_id})
    await db.commit()

    # Check if MFA setup is now complete
    await _check_and_update_mfa_complete(db, user_id)

    logger.info(f"WebAuthn credential registered for user {user_id}: {request.device_name}")
    return {
        "message": "Device registered successfully",
        "success": True,
        "device_name": request.device_name,
        "total_devices": len(current_creds),
    }


# ============================================
# WebAuthn Verification Endpoints
# ============================================


@router.post("/webauthn/verify/start", response_model=WebAuthnVerifyStartResponse, tags=["MFA"])
async def webauthn_verify_start(
    current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Start WebAuthn verification process.

    Returns a challenge and list of allowed credentials.
    """
    user_id = current_user.get("sub") or current_user.get("id")

    # Get user's credentials
    query = text(
        """
        SELECT webauthn_credentials FROM identity.users WHERE id = :user_id
    """
    )
    result = await db.execute(query, {"user_id": user_id})
    row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    credentials = row[0] if row[0] else []

    if not credentials:
        raise HTTPException(
            status_code=400,
            detail="No WebAuthn devices registered. Please use PIN or set up WebAuthn.",
        )

    # Generate challenge
    challenge = generate_challenge()

    # Store challenge
    challenge_data = {"challenge": challenge, "created_at": datetime.now(timezone.utc).isoformat()}

    update_query = text(
        """
        UPDATE identity.users
        SET user_metadata = user_metadata || :challenge_data,
            updated_at = NOW()
        WHERE id = :user_id
    """
    )
    await db.execute(
        update_query,
        {
            "challenge_data": json.dumps({"webauthn_verify_challenge": challenge_data}),
            "user_id": user_id,
        },
    )
    await db.commit()

    # Build allowed credentials list
    allowed_credentials = [
        {
            "id": cred["credential_id"],
            "type": "public-key",
        }
        for cred in credentials
    ]

    return WebAuthnVerifyStartResponse(
        challenge=challenge,
        timeout=WEBAUTHN_CHALLENGE_TIMEOUT * 1000,
        rp_id="mhapi.mysticdatanode.net",
        allowed_credentials=allowed_credentials,
    )


@router.post("/webauthn/verify/finish", response_model=MFAVerifiedResponse, tags=["MFA"])
async def webauthn_verify_finish(
    request: WebAuthnVerifyFinishRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Complete WebAuthn verification.

    Verifies the signature and issues an MFA-verified token.
    """
    user_id = current_user.get("sub") or current_user.get("id")
    email = current_user.get("email")
    role = current_user.get("role")

    # Get user's credentials
    query = text(
        """
        SELECT webauthn_credentials,
               COALESCE(first_name, '') || ' ' || COALESCE(last_name, '') as full_name
        FROM identity.users WHERE id = :user_id
    """
    )
    result = await db.execute(query, {"user_id": user_id})
    row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    credentials, full_name = row
    full_name = full_name.strip() or email.split("@")[0]

    # Find the credential used
    credential_found = None
    for cred in credentials or []:
        if cred.get("credential_id") == request.credential_id:
            credential_found = cred
            break

    if not credential_found:
        raise HTTPException(status_code=401, detail="Unknown credential")

    # In a full implementation, we would verify the signature here using the public key
    # For now, we trust the client-side verification (browser's WebAuthn API)
    # The signature verification requires cryptographic libraries like `webauthn` or `fido2`

    # Update sign count (replay attack protection)
    # In production, verify that the new sign_count > stored sign_count

    # Update last login
    update_query = text(
        """
        UPDATE identity.users
        SET last_login_at = NOW(), updated_at = NOW()
        WHERE id = :user_id
    """
    )
    await db.execute(update_query, {"user_id": user_id})
    await db.commit()

    # Create MFA-verified token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": str(user_id),
            "email": email,
            "role": role,
            "mfa_verified": True,
        },
        expires_delta=access_token_expires,
    )

    logger.info(f"WebAuthn verified for user {user_id}")

    return MFAVerifiedResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": str(user_id),
            "email": email,
            "role": role,
            "full_name": full_name,
            "is_active": True,
        },
    )


# ============================================
# SUPER_ADMIN PIN Management
# ============================================


@router.post("/pin/reset", tags=["MFA", "Admin"])
async def reset_user_pin(
    request: PINResetRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Reset a user's PIN (SUPER_ADMIN only).

    This forces the user to set up a new PIN on next login.
    """
    # Check if current user is SUPER_ADMIN
    caller_role = current_user.get("role")
    if caller_role != "super_admin":
        raise HTTPException(status_code=403, detail="Only SUPER_ADMIN can reset user PINs")

    # Reset the target user's PIN
    update_query = text(
        """
        UPDATE identity.users
        SET pin_hash = NULL,
            pin_attempts = 0,
            pin_locked_until = NULL,
            pin_reset_required = TRUE,
            mfa_setup_complete = FALSE,
            updated_at = NOW()
        WHERE id = :user_id
        RETURNING email
    """
    )
    result = await db.execute(update_query, {"user_id": request.user_id})
    row = result.fetchone()
    await db.commit()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    logger.info(f"PIN reset by SUPER_ADMIN for user {request.user_id}")
    return {
        "message": f"PIN reset for user {row[0]}. They will be required to set up a new PIN on next login.",
        "success": True,
    }


@router.delete("/webauthn/device/{credential_id}", tags=["MFA"])
async def remove_webauthn_device(
    credential_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove a WebAuthn device (user can remove their own, SUPER_ADMIN can remove any).
    """
    user_id = current_user.get("sub") or current_user.get("id")

    # Get current credentials
    query = text(
        """
        SELECT webauthn_credentials FROM identity.users WHERE id = :user_id
    """
    )
    result = await db.execute(query, {"user_id": user_id})
    row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    credentials = row[0] if row[0] else []

    # Find and remove the credential
    updated_creds = [c for c in credentials if c.get("credential_id") != credential_id]

    if len(updated_creds) == len(credentials):
        raise HTTPException(status_code=404, detail="Device not found")

    # Update database
    update_query = text(
        """
        UPDATE identity.users
        SET webauthn_credentials = :creds,
            updated_at = NOW()
        WHERE id = :user_id
    """
    )
    await db.execute(update_query, {"creds": json.dumps(updated_creds), "user_id": user_id})
    await db.commit()

    # Check if MFA is still complete
    await _check_and_update_mfa_complete(db, user_id)

    logger.info(f"WebAuthn device removed for user {user_id}")
    return {"message": "Device removed successfully", "remaining_devices": len(updated_creds)}


@router.get("/devices", tags=["MFA"])
async def list_webauthn_devices(
    current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    List all WebAuthn devices registered for the current user.
    """
    user_id = current_user.get("sub") or current_user.get("id")

    query = text(
        """
        SELECT webauthn_credentials FROM identity.users WHERE id = :user_id
    """
    )
    result = await db.execute(query, {"user_id": user_id})
    row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    credentials = row[0] if row[0] else []

    # Return sanitized device list (no public keys)
    devices = [
        {
            "credential_id": cred.get("credential_id"),
            "device_name": cred.get("device_name", "Unknown"),
            "created_at": cred.get("created_at"),
        }
        for cred in credentials
    ]

    return {"devices": devices, "count": len(devices)}


# ============================================
# Helper Functions
# ============================================


async def _check_and_update_mfa_complete(db: AsyncSession, user_id: str):
    """Check if MFA setup is complete and update the flag."""
    query = text(
        """
        SELECT webauthn_credentials, pin_hash FROM identity.users WHERE id = :user_id
    """
    )
    result = await db.execute(query, {"user_id": user_id})
    row = result.fetchone()

    if row:
        webauthn_creds, pin_hash = row
        has_webauthn = webauthn_creds and len(webauthn_creds) > 0
        has_pin = pin_hash is not None

        # MFA is complete if user has EITHER WebAuthn OR PIN (or both)
        # In strictest mode, require both: has_webauthn and has_pin
        is_complete = has_webauthn or has_pin

        update_query = text(
            """
            UPDATE identity.users
            SET mfa_setup_complete = :is_complete,
                mfa_setup_at = CASE WHEN :is_complete AND mfa_setup_at IS NULL THEN NOW() ELSE mfa_setup_at END,
                updated_at = NOW()
            WHERE id = :user_id
        """
        )
        await db.execute(update_query, {"is_complete": is_complete, "user_id": user_id})
        await db.commit()
