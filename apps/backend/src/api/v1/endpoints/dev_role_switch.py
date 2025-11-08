"""
Development Role Switching API
Allows SUPER_ADMIN to temporarily switch roles for testing purposes
ONLY ENABLED IN DEVELOPMENT MODE
"""

import logging
from datetime import datetime, timezone, timedelta

from api.deps import get_current_user
from core.config import UserRole, get_settings
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


class RoleSwitchRequest(BaseModel):
    """Request to switch to a different role temporarily"""

    target_role: str  # admin, customer_support, station_manager
    duration_minutes: int = 60  # How long to stay in this role


class RoleSwitchResponse(BaseModel):
    """Response after role switch"""

    success: bool
    current_role: str
    original_role: str
    expires_at: str
    message: str


class RestoreRoleResponse(BaseModel):
    """Response after restoring original role"""

    success: bool
    restored_role: str
    message: str


# Store temporary role switches in memory (in production, use Redis)
_role_switches = {}


@router.post("/switch-role", response_model=RoleSwitchResponse)
async def switch_role(
    request: RoleSwitchRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Switch SUPER_ADMIN to a different role temporarily for testing

    **DEVELOPMENT ONLY** - Returns 404 in production

    Allows super admins to test the system as:
    - admin
    - customer_support
    - station_manager

    The switch is temporary and can be restored anytime.
    """
    # Block in production
    if not settings.DEV_MODE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role switching only available in development mode",
        )

    # Only super admins can switch roles
    if current_user.get("role") != UserRole.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only SUPER_ADMIN can switch roles",
        )

    # Validate target role
    valid_roles = ["admin", "customer_support", "station_manager"]
    if request.target_role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid target role. Must be one of: {', '.join(valid_roles)}",
        )

    # Store original role and set expiration
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=request.duration_minutes)

    _role_switches[str(current_user.get("id"))] = {
        "original_role": current_user.get("role"),
        "target_role": request.target_role,
        "expires_at": expires_at,
    }

    # Note: Cannot modify user dict directly as it's immutable from JWT
    # Role switching is tracked in _role_switches dict
    # Caller should check _role_switches to determine effective role

    logger.info(
        f"🔄 SUPER_ADMIN {current_user.get('email')} switched to {request.target_role} "
        f"for {request.duration_minutes} minutes"
    )

    return RoleSwitchResponse(
        success=True,
        current_role=request.target_role,
        original_role=UserRole.SUPER_ADMIN.value,
        expires_at=expires_at.isoformat(),
        message=f"Role switched to {request.target_role} for {request.duration_minutes} minutes. "
        f"Use /restore-role to switch back anytime.",
    )


@router.post("/restore-role", response_model=RestoreRoleResponse)
async def restore_role(
    current_user: dict = Depends(get_current_user),
):
    """
    Restore original SUPER_ADMIN role after temporary switch

    **DEVELOPMENT ONLY** - Returns 404 in production
    """
    # Block in production
    if not settings.DEV_MODE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role switching only available in development mode",
        )

    # Check if user has an active role switch
    user_id = str(current_user.get("id"))
    if user_id not in _role_switches:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active role switch found. You are already in your original role.",
        )

    # Restore original role
    original_role = _role_switches[user_id]["original_role"]

    # Clean up
    del _role_switches[user_id]

    logger.info(f"✅ Restored {current_user.get('email')} to original role: {original_role}")

    return RestoreRoleResponse(
        success=True,
        restored_role=original_role,
        message=f"Role restored to {original_role}",
    )


@router.get("/current-role")
async def get_current_role(
    current_user: dict = Depends(get_current_user),
):
    """
    Get current role information

    Shows:
    - Current active role
    - Original role (if switched)
    - Time remaining (if switched)
    """
    user_id = str(current_user.get("id"))

    if user_id in _role_switches:
        switch_info = _role_switches[user_id]
        expires_at = switch_info["expires_at"]
        time_remaining = int((expires_at - datetime.now(timezone.utc)).total_seconds() / 60)

        return {
            "current_role": switch_info["target_role"],  # Show switched role
            "original_role": switch_info["original_role"],
            "is_switched": True,
            "expires_at": expires_at.isoformat(),
            "time_remaining_minutes": max(0, time_remaining),
        }

    return {
        "current_role": current_user.get("role"),
        "is_switched": False,
    }


@router.get("/available-roles")
async def get_available_roles(
    current_user: dict = Depends(get_current_user),
):
    """
    Get list of roles available for switching

    **DEVELOPMENT ONLY**
    """
    if not settings.DEV_MODE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role switching only available in development mode",
        )

    if current_user.get("role") != UserRole.SUPER_ADMIN.value:
        return {"available_roles": [], "message": "Only SUPER_ADMIN can switch roles"}

    return {
        "available_roles": [
            {
                "role": "admin",
                "name": "Admin",
                "description": "Full administrative access to all features",
            },
            {
                "role": "customer_support",
                "name": "Customer Support",
                "description": "Handle customer inquiries, manage bookings and leads",
            },
            {
                "role": "station_manager",
                "name": "Station Manager",
                "description": "Manage station-specific operations and staff",
            },
        ],
        "current_role": current_user.get("role"),
    }
