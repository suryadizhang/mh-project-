"""
Customer Preferences API Router
================================

Endpoints for managing unified customer preferences:
- Chef request tracking
- Allergen/dietary capture
- Special instructions

Endpoints:
- GET  /api/v1/bookings/{booking_id}/preferences - Get preferences
- PUT  /api/v1/bookings/{booking_id}/preferences - Update preferences
- GET  /api/v1/bookings/{booking_id}/prep-allergens - Chef prep view
- GET  /api/v1/bookings/{booking_id}/chef-bonus - Bonus calculation
- GET  /api/v1/allergens - List common allergens

Auth: Admin, Customer Support, Station Manager
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from schemas.customer_preferences import (
    ChefPrepAllergensResponse,
    ChefRequestBonusInfo,
    CommonAllergensListResponse,
    CustomerPreferencesResponse,
    CustomerPreferencesUpdate,
)
from services.customer_preferences_service import (
    calculate_chef_request_bonus,
    get_chef_prep_allergens,
    get_common_allergens,
    get_customer_preferences,
    update_customer_preferences,
)
from utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Customer Preferences"])


# =====================================================
# Common Allergens Reference
# =====================================================


@router.get(
    "/allergens",
    response_model=CommonAllergensListResponse,
    summary="List common allergens",
    description="Get list of common allergens with icons and chef cooking actions. Used to populate allergen checkboxes in booking UI.",
)
async def list_common_allergens(
    db: AsyncSession = Depends(get_db),
) -> CommonAllergensListResponse:
    """
    List all available common allergens.

    No auth required - used by public booking form.
    """
    return await get_common_allergens(db)


# =====================================================
# Customer Preferences CRUD
# =====================================================


@router.get(
    "/bookings/{booking_id}/preferences",
    response_model=CustomerPreferencesResponse,
    summary="Get customer preferences",
    description="Get chef request, allergens, and special instructions for a booking.",
)
async def get_booking_preferences(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> CustomerPreferencesResponse:
    """
    Get customer preferences for a booking.

    Includes:
    - Chef request info (was chef requested, which chef, source)
    - Allergen info (common allergens, other dietary, confirmation status)
    - Special requests
    """
    preferences = await get_customer_preferences(db, booking_id)

    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking {booking_id} not found",
        )

    return preferences


@router.put(
    "/bookings/{booking_id}/preferences",
    response_model=CustomerPreferencesResponse,
    summary="Update customer preferences",
    description="Update chef request, allergens, and/or special instructions. Only provided fields are updated.",
)
async def update_booking_preferences(
    booking_id: UUID,
    updates: CustomerPreferencesUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> CustomerPreferencesResponse:
    """
    Update customer preferences for a booking.

    Partial update - only fields provided in request body are updated.

    If setting allergen_confirmed=true:
    - allergen_confirmed_at is auto-set to now
    - allergen_confirmed_by is auto-set to current user
    """
    # Verify booking exists
    existing = await get_customer_preferences(db, booking_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking {booking_id} not found",
        )

    # Get current user ID for audit
    user_id = None
    if hasattr(current_user, "id"):
        user_id = current_user.id
    elif isinstance(current_user, dict) and "id" in current_user:
        user_id = current_user["id"]

    result = await update_customer_preferences(
        db=db,
        booking_id=booking_id,
        updates=updates,
        updated_by_user_id=user_id,
    )

    logger.info(f"User {user_id} updated preferences for booking {booking_id}")

    return result


# =====================================================
# Chef Prep View
# =====================================================


@router.get(
    "/bookings/{booking_id}/prep-allergens",
    response_model=ChefPrepAllergensResponse,
    summary="Get allergen prep summary for chef",
    description="Get allergen info with cooking actions for chef's prep summary view.",
)
async def get_booking_prep_allergens(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ChefPrepAllergensResponse:
    """
    Get allergen summary for chef prep view.

    Combines customer's allergen selections with cooking instructions
    from the common_allergens reference table.

    Used by chef mobile app to display prep summary.
    """
    result = await get_chef_prep_allergens(db, booking_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking {booking_id} not found",
        )

    return result


# =====================================================
# Chef Request Bonus
# =====================================================


@router.get(
    "/bookings/{booking_id}/chef-bonus",
    response_model=ChefRequestBonusInfo,
    summary="Get chef request bonus calculation",
    description="Calculate bonus for chef if customer requested them specifically.",
)
async def get_chef_request_bonus(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ChefRequestBonusInfo:
    """
    Calculate chef request bonus for a booking.

    Returns:
    - Whether customer requested a specific chef
    - Whether bonus is eligible (requested = assigned)
    - Bonus percentage from SSoT
    - Base order value (excluding travel, upgrades, add-ons)
    - Calculated bonus amount
    """
    result = await calculate_chef_request_bonus(db, booking_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking {booking_id} not found",
        )

    return result
