"""
2FA and IP Verification API Router
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.auth import get_current_user
from models.user import User
from services.totp_service import get_totp_service, TOTPService
from services.ip_verification_service import get_ip_verification_service, IPVerificationService
from services.audit_service import get_audit_service, AuditService

router = APIRouter(prefix="/security", tags=["Security"])


# Pydantic schemas
class Setup2FARequest(BaseModel):
    """Request to initiate 2FA setup."""

    pass


class Enable2FARequest(BaseModel):
    """Request to enable 2FA with verification code."""

    code: str


class Disable2FARequest(BaseModel):
    """Request to disable 2FA."""

    password: str


class Verify2FARequest(BaseModel):
    """Request to verify 2FA code during login."""

    temp_token: str
    code: str


class EnableIPVerificationRequest(BaseModel):
    """Request to enable IP verification."""

    pass


class AddTrustedIPRequest(BaseModel):
    """Request to add IP to trusted list."""

    ip_address: str


class RemoveTrustedIPRequest(BaseModel):
    """Request to remove IP from trusted list."""

    ip_address: str


# Helper function
async def get_client_info(request: Request) -> dict:
    """Extract client IP and user agent."""
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


# ==================== 2FA Endpoints ====================


@router.post("/2fa/setup")
async def setup_2fa(
    request: Request,
    current_user: User = Depends(get_current_user),
    totp_service: TOTPService = Depends(get_totp_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Step 1: Generate TOTP secret and QR code for 2FA setup.

    Returns:
    - secret: TOTP secret (for manual entry)
    - qr_code: Base64-encoded QR code image
    """

    # Generate new secret
    secret = totp_service.generate_secret()

    # Generate QR code
    qr_code = totp_service.generate_qr_code(secret, current_user.email)

    # Store secret temporarily (not enabled yet)
    current_user.mfa_secret = secret
    await db.commit()

    return {
        "secret": secret,
        "qr_code": qr_code,
        "instructions": (
            "1. Scan the QR code with Google Authenticator\n"
            "2. Enter the 6-digit code to enable 2FA\n"
            "3. Save your backup codes securely"
        ),
    }


@router.post("/2fa/enable")
async def enable_2fa(
    request: Request,
    data: Enable2FARequest,
    current_user: User = Depends(get_current_user),
    totp_service: TOTPService = Depends(get_totp_service),
    audit_service: AuditService = Depends(get_audit_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Step 2: Enable 2FA after verifying setup code.

    Returns:
    - backup_codes: List of backup codes (save these!)
    """

    client_info = await get_client_info(request)

    success, backup_codes = await totp_service.enable_2fa(current_user, data.code, **client_info)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code. Please try again.",
        )

    return {
        "message": "2FA enabled successfully",
        "backup_codes": backup_codes,
        "warning": "Save these backup codes securely. You won't see them again!",
    }


@router.post("/2fa/disable")
async def disable_2fa(
    request: Request,
    data: Disable2FARequest,
    current_user: User = Depends(get_current_user),
    totp_service: TOTPService = Depends(get_totp_service),
    audit_service: AuditService = Depends(get_audit_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Disable 2FA after verifying password.
    """

    client_info = await get_client_info(request)

    success = await totp_service.disable_2fa(current_user, data.password, **client_info)

    if not success:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong password")

    return {"message": "2FA disabled successfully"}


@router.get("/2fa/status")
async def get_2fa_status(current_user: User = Depends(get_current_user)):
    """
    Get current 2FA status.
    """

    return {
        "enabled": current_user.mfa_enabled,
        "backup_codes_remaining": (
            len(current_user.mfa_backup_codes) if current_user.mfa_backup_codes else 0
        ),
    }


# ==================== IP Verification Endpoints ====================


@router.post("/ip-verification/enable")
async def enable_ip_verification(
    request: Request,
    current_user: User = Depends(get_current_user),
    ip_service: IPVerificationService = Depends(get_ip_verification_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Enable IP verification. Current IP will be added as first trusted IP.
    """

    client_info = await get_client_info(request)

    await ip_service.enable_ip_verification(
        current_user, client_info["ip_address"], client_info["user_agent"]
    )

    return {
        "message": "IP verification enabled",
        "current_ip": client_info["ip_address"],
        "info": "You'll receive SMS alerts when logging in from new IP addresses",
    }


@router.post("/ip-verification/disable")
async def disable_ip_verification(
    request: Request,
    current_user: User = Depends(get_current_user),
    ip_service: IPVerificationService = Depends(get_ip_verification_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Disable IP verification.
    """

    client_info = await get_client_info(request)

    await ip_service.disable_ip_verification(current_user, client_info["user_agent"])

    return {"message": "IP verification disabled"}


@router.post("/ip-verification/trust")
async def add_trusted_ip(
    request: Request,
    data: AddTrustedIPRequest,
    current_user: User = Depends(get_current_user),
    ip_service: IPVerificationService = Depends(get_ip_verification_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Add IP address to trusted list.
    """

    client_info = await get_client_info(request)

    added = await ip_service.add_trusted_ip(
        current_user, data.ip_address, client_info["user_agent"]
    )

    if not added:
        return {"message": "IP address already trusted"}

    return {"message": f"IP address {data.ip_address} added to trusted list"}


@router.post("/ip-verification/untrust")
async def remove_trusted_ip(
    request: Request,
    data: RemoveTrustedIPRequest,
    current_user: User = Depends(get_current_user),
    ip_service: IPVerificationService = Depends(get_ip_verification_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove IP address from trusted list.
    """

    client_info = await get_client_info(request)

    removed = await ip_service.remove_trusted_ip(
        current_user, data.ip_address, client_info["user_agent"]
    )

    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="IP address not in trusted list"
        )

    return {"message": f"IP address {data.ip_address} removed from trusted list"}


@router.get("/ip-verification/status")
async def get_ip_verification_status(
    request: Request, current_user: User = Depends(get_current_user)
):
    """
    Get IP verification status and trusted IPs.
    """

    client_info = await get_client_info(request)

    return {
        "enabled": current_user.ip_verification_enabled,
        "current_ip": client_info["ip_address"],
        "trusted_ips": current_user.trusted_ips or [],
        "last_known_ip": current_user.last_known_ip,
    }
