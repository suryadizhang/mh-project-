"""
Customer Preferences Service
============================

Handles unified customer preferences capture:
- Chef request tracking (for bonus)
- Allergen/dietary capture (for safety)
- Special instructions

Related Schemas:
- schemas/customer_preferences.py

Related Tables:
- core.bookings
- core.common_allergens

SSoT Integration:
- requested_chef_bonus_pct from dynamic_variables
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.customer_preferences import (
    AllergenInfo,
    AllergenPrepNote,
    ChefPrepAllergensResponse,
    ChefRequestBonusInfo,
    ChefRequestInfo,
    CommonAllergenInfo,
    CommonAllergensListResponse,
    CustomerPreferencesResponse,
    CustomerPreferencesUpdate,
)

logger = logging.getLogger(__name__)


# =====================================================
# Common Allergens Reference
# =====================================================


async def get_common_allergens(db: AsyncSession) -> CommonAllergensListResponse:
    """
    Get list of common allergens from reference table.

    Used to populate allergen checkboxes in UI.
    """
    result = await db.execute(
        text(
            """
            SELECT code, display_name, icon, chef_action, display_order
            FROM core.common_allergens
            WHERE is_active = true
            ORDER BY display_order
        """
        )
    )
    rows = result.fetchall()

    allergens = [
        CommonAllergenInfo(
            code=row.code,
            display_name=row.display_name,
            icon=row.icon,
            chef_action=row.chef_action,
            display_order=row.display_order,
        )
        for row in rows
    ]

    return CommonAllergensListResponse(allergens=allergens, total=len(allergens))


# =====================================================
# Customer Preferences CRUD
# =====================================================


async def get_customer_preferences(
    db: AsyncSession, booking_id: UUID
) -> Optional[CustomerPreferencesResponse]:
    """
    Get customer preferences for a booking.

    Returns None if booking not found.
    """
    result = await db.execute(
        text(
            """
            SELECT
                b.id as booking_id,
                -- Chef request
                b.chef_was_requested,
                b.requested_chef_id,
                rc.name as requested_chef_name,
                b.chef_request_source,
                -- Allergens
                b.common_allergens,
                b.allergen_disclosure,
                b.allergen_confirmed,
                b.allergen_confirmed_method,
                b.allergen_confirmed_at,
                b.allergen_confirmed_by,
                conf_user.first_name || ' ' || conf_user.last_name as confirmed_by_name,
                -- Special requests
                b.special_requests,
                b.updated_at
            FROM core.bookings b
            LEFT JOIN ops.chefs rc ON b.requested_chef_id = rc.id
            LEFT JOIN identity.users conf_user ON b.allergen_confirmed_by = conf_user.id
            WHERE b.id = :booking_id
        """
        ),
        {"booking_id": str(booking_id)},
    )
    row = result.fetchone()

    if not row:
        return None

    return CustomerPreferencesResponse(
        booking_id=row.booking_id,
        chef_request=ChefRequestInfo(
            chef_was_requested=row.chef_was_requested or False,
            requested_chef_id=row.requested_chef_id,
            requested_chef_name=row.requested_chef_name,
            chef_request_source=row.chef_request_source,
        ),
        allergens=AllergenInfo(
            common_allergens=row.common_allergens or [],
            allergen_disclosure=row.allergen_disclosure,
            allergen_confirmed=row.allergen_confirmed or False,
            allergen_confirmed_method=row.allergen_confirmed_method,
            allergen_confirmed_at=row.allergen_confirmed_at,
            allergen_confirmed_by_id=row.allergen_confirmed_by,
            allergen_confirmed_by_name=row.confirmed_by_name,
        ),
        special_requests=row.special_requests,
        last_updated=row.updated_at,
    )


async def update_customer_preferences(
    db: AsyncSession,
    booking_id: UUID,
    updates: CustomerPreferencesUpdate,
    updated_by_user_id: Optional[UUID] = None,
) -> CustomerPreferencesResponse:
    """
    Update customer preferences for a booking.

    Only updates fields that are provided (not None).
    """
    # Build dynamic SET clause
    set_clauses = []
    params = {"booking_id": str(booking_id)}

    # Chef request fields
    if updates.chef_was_requested is not None:
        set_clauses.append("chef_was_requested = :chef_was_requested")
        params["chef_was_requested"] = updates.chef_was_requested

    if updates.requested_chef_id is not None:
        set_clauses.append("requested_chef_id = :requested_chef_id")
        params["requested_chef_id"] = str(updates.requested_chef_id)

    if updates.chef_request_source is not None:
        set_clauses.append("chef_request_source = :chef_request_source")
        params["chef_request_source"] = updates.chef_request_source

    # Allergen fields
    if updates.common_allergens is not None:
        set_clauses.append("common_allergens = CAST(:common_allergens AS jsonb)")
        import json

        params["common_allergens"] = json.dumps(updates.common_allergens)

    if updates.allergen_disclosure is not None:
        set_clauses.append("allergen_disclosure = :allergen_disclosure")
        params["allergen_disclosure"] = updates.allergen_disclosure

    if updates.allergen_confirmed is not None:
        set_clauses.append("allergen_confirmed = :allergen_confirmed")
        params["allergen_confirmed"] = updates.allergen_confirmed

        # Auto-set confirmation timestamp and user
        if updates.allergen_confirmed:
            set_clauses.append("allergen_confirmed_at = NOW()")
            if updated_by_user_id:
                set_clauses.append("allergen_confirmed_by = :confirmed_by")
                params["confirmed_by"] = str(updated_by_user_id)

    if updates.allergen_confirmed_method is not None:
        set_clauses.append("allergen_confirmed_method = :allergen_confirmed_method")
        params["allergen_confirmed_method"] = updates.allergen_confirmed_method

    # Special requests
    if updates.special_requests is not None:
        set_clauses.append("special_requests = :special_requests")
        params["special_requests"] = updates.special_requests

    # Always update timestamp
    set_clauses.append("updated_at = NOW()")

    if not set_clauses:
        # Nothing to update, just return current state
        return await get_customer_preferences(db, booking_id)

    query = f"""
        UPDATE core.bookings
        SET {', '.join(set_clauses)}
        WHERE id = :booking_id
    """

    await db.execute(text(query), params)
    await db.commit()

    logger.info(f"Updated customer preferences for booking {booking_id}")

    return await get_customer_preferences(db, booking_id)


# =====================================================
# Chef Prep Summary (for Chef App)
# =====================================================


async def get_chef_prep_allergens(
    db: AsyncSession, booking_id: UUID
) -> Optional[ChefPrepAllergensResponse]:
    """
    Get allergen summary for chef prep view.

    Combines allergen info with cooking actions from reference table.
    """
    # Get booking info
    result = await db.execute(
        text(
            """
            SELECT
                b.id as booking_id,
                c.first_name || ' ' || c.last_name as customer_name,
                b.event_datetime,
                b.common_allergens,
                b.allergen_disclosure,
                b.allergen_confirmed,
                b.allergen_confirmed_method,
                b.special_requests
            FROM core.bookings b
            JOIN core.customers c ON b.customer_id = c.id
            WHERE b.id = :booking_id
        """
        ),
        {"booking_id": str(booking_id)},
    )
    booking = result.fetchone()

    if not booking:
        return None

    # Get allergen cooking actions
    allergen_notes = []
    common_allergens = booking.common_allergens or []

    if common_allergens:
        result = await db.execute(
            text(
                """
                SELECT code, display_name, icon, chef_action
                FROM core.common_allergens
                WHERE code = ANY(:codes)
                ORDER BY display_order
            """
            ),
            {"codes": common_allergens},
        )
        for row in result.fetchall():
            allergen_notes.append(
                AllergenPrepNote(
                    allergen=row.code,
                    display_name=row.display_name,
                    icon=row.icon or "⚠️",
                    chef_action=row.chef_action
                    or "Please confirm accommodations with customer.",
                )
            )

    return ChefPrepAllergensResponse(
        booking_id=booking.booking_id,
        customer_name=booking.customer_name,
        event_datetime=booking.event_datetime,
        has_allergens=bool(allergen_notes) or bool(booking.allergen_disclosure),
        allergen_notes=allergen_notes,
        other_dietary=booking.allergen_disclosure,
        allergen_confirmed=booking.allergen_confirmed or False,
        allergen_confirmed_method=booking.allergen_confirmed_method,
        special_requests=booking.special_requests,
    )


# =====================================================
# Chef Request Bonus Calculation
# =====================================================


async def get_requested_chef_bonus_pct(db: AsyncSession) -> int:
    """
    Get requested chef bonus percentage from SSoT.

    Defaults to 10% if not set.
    """
    result = await db.execute(
        text(
            """
            SELECT value
            FROM dynamic_variables
            WHERE category = 'chef_pay' AND key = 'requested_chef_bonus_pct'
            AND is_active = true
        """
        )
    )
    row = result.fetchone()

    if row:
        try:
            return int(row.value)
        except (ValueError, TypeError):
            logger.warning("Invalid requested_chef_bonus_pct value, using default 10")
            return 10

    return 10  # Default


async def calculate_chef_request_bonus(
    db: AsyncSession,
    booking_id: UUID,
) -> Optional[ChefRequestBonusInfo]:
    """
    Calculate chef request bonus for a booking.

    Bonus is only applied if:
    1. Customer requested a specific chef
    2. The requested chef is the one assigned to the booking

    Bonus formula:
        bonus = (adults × adult_rate + kids × kid_rate) × (bonus_pct / 100)

    Note: Excludes travel fees, protein upgrades, and add-ons (base order only).
    """
    # Get booking with chef info and guest counts
    result = await db.execute(
        text(
            """
            SELECT
                b.id as booking_id,
                b.chef_was_requested,
                b.requested_chef_id,
                rc.name as requested_chef_name,
                ca.chef_id as assigned_chef_id,
                ac.name as assigned_chef_name,
                ac.pay_rate_class as chef_tier,
                b.adult_count,
                b.child_count,
                b.toddler_count
            FROM core.bookings b
            LEFT JOIN ops.chefs rc ON b.requested_chef_id = rc.id
            LEFT JOIN ops.chef_assignments ca ON b.id = ca.booking_id AND ca.is_lead = true
            LEFT JOIN ops.chefs ac ON ca.chef_id = ac.id
            WHERE b.id = :booking_id
        """
        ),
        {"booking_id": str(booking_id)},
    )
    row = result.fetchone()

    if not row:
        return None

    # Determine if bonus eligible (requested = assigned)
    bonus_eligible = (
        row.chef_was_requested
        and row.requested_chef_id is not None
        and row.assigned_chef_id is not None
        and str(row.requested_chef_id) == str(row.assigned_chef_id)
    )

    # Get bonus percentage from SSoT
    bonus_pct = await get_requested_chef_bonus_pct(db)

    # Calculate base order value (need tier rates)
    base_order_cents = 0
    bonus_amount_cents = 0

    if bonus_eligible and row.chef_tier:
        # Get tier rates from SSoT
        tier_rates = await _get_tier_rates(db, row.chef_tier)

        adults = row.adult_count or 0
        kids = row.child_count or 0
        # Toddlers are free, not included in base

        base_order_cents = (
            adults * tier_rates["adult_cents"] + kids * tier_rates["kid_cents"]
        )

        bonus_amount_cents = int(base_order_cents * bonus_pct / 100)

    return ChefRequestBonusInfo(
        booking_id=row.booking_id,
        chef_was_requested=row.chef_was_requested or False,
        requested_chef_id=row.requested_chef_id,
        requested_chef_name=row.requested_chef_name,
        assigned_chef_id=row.assigned_chef_id,
        assigned_chef_name=row.assigned_chef_name,
        bonus_eligible=bonus_eligible,
        bonus_percentage=bonus_pct,
        base_order_cents=base_order_cents,
        bonus_amount_cents=bonus_amount_cents,
    )


async def _get_tier_rates(db: AsyncSession, tier: str) -> dict:
    """
    Get per-tier rates from SSoT.

    Maps tier name to rate keys:
    - new_chef -> junior_*
    - chef -> chef_*
    - senior_chef -> senior_*
    - station_manager -> manager_*
    """
    tier_prefix_map = {
        "new_chef": "junior",
        "chef": "chef",
        "senior_chef": "senior",
        "station_manager": "manager",
    }

    prefix = tier_prefix_map.get(tier, "chef")

    result = await db.execute(
        text(
            """
            SELECT key, value
            FROM dynamic_variables
            WHERE category = 'chef_pay'
            AND key IN (:adult_key, :kid_key)
            AND is_active = true
        """
        ),
        {
            "adult_key": f"{prefix}_adult_cents",
            "kid_key": f"{prefix}_kid_cents",
        },
    )

    rates = {"adult_cents": 1200, "kid_cents": 600}  # Default to chef tier

    for row in result.fetchall():
        if row.key.endswith("_adult_cents"):
            rates["adult_cents"] = int(row.value)
        elif row.key.endswith("_kid_cents"):
            rates["kid_cents"] = int(row.value)

    return rates


# =====================================================
# Exports
# =====================================================

__all__ = [
    "get_common_allergens",
    "get_customer_preferences",
    "update_customer_preferences",
    "get_chef_prep_allergens",
    "get_requested_chef_bonus_pct",
    "calculate_chef_request_bonus",
]
