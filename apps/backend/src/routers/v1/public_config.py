"""
Public Configuration Endpoints (No Authentication Required)
============================================================

These endpoints provide SSoT business configuration to the customer website.
They are public (no auth) and cached for performance.

Endpoints:
    GET /config/all       → Complete business configuration (nested structure)
    GET /policies/current → Policies with human-readable text

Frontend Consumers:
    - apps/customer/src/hooks/useConfig.ts
    - apps/customer/src/hooks/usePolicies.ts

SSoT Architecture:
    See: .github/instructions/20-SINGLE_SOURCE_OF_TRUTH.instructions.md
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.business_config_service import get_business_config

# =============================================================================
# Router Definition
# =============================================================================

router = APIRouter(tags=["public-config"])


# =============================================================================
# Response Models (Match Frontend TypeScript Interfaces)
# =============================================================================

# These models MUST match the TypeScript interfaces in:
# apps/customer/src/hooks/useConfig.ts


class PricingConfig(BaseModel):
    """Pricing configuration values (all amounts in cents)."""

    adult_price_cents: int = Field(..., description="Adult price per person in cents")
    child_price_cents: int = Field(..., description="Child (6-12) price per person in cents")
    child_free_under_age: int = Field(..., description="Age under which children are free")
    party_minimum_cents: int = Field(..., description="Minimum party total in cents")


class TravelConfig(BaseModel):
    """Travel fee configuration."""

    free_miles: int = Field(..., description="Free travel radius in miles")
    per_mile_cents: int = Field(..., description="Cost per mile in cents after free radius")


class DepositConfig(BaseModel):
    """Deposit configuration."""

    deposit_amount_cents: int = Field(..., description="Fixed deposit amount in cents")
    deposit_refundable_days: int = Field(
        ..., description="Days before event for deposit to be refundable"
    )


class BookingConfig(BaseModel):
    """Booking rules configuration."""

    min_advance_hours: int = Field(..., description="Minimum hours in advance to book")


class GuestLimitsConfig(BaseModel):
    """Guest count limits."""

    minimum: int = Field(default=1, description="Minimum guest count")
    maximum: int = Field(default=100, description="Maximum guest count")
    minimum_for_hibachi: int = Field(default=10, description="Minimum guests for standard hibachi")


class TimingConfig(BaseModel):
    """Timing and deadline configuration (all values in hours unless noted)."""

    menu_change_cutoff_hours: int = Field(
        ..., description="Hours before event when menu changes are no longer allowed"
    )
    guest_count_finalize_hours: int = Field(
        ..., description="Hours before event when guest count must be finalized"
    )
    free_reschedule_hours: int = Field(..., description="Hours before event to reschedule for free")


class ServiceConfig(BaseModel):
    """Service duration and logistics configuration (all values in minutes)."""

    standard_duration_minutes: int = Field(..., description="Standard service duration in minutes")
    extended_duration_minutes: int = Field(
        ..., description="Maximum extended service duration for large parties"
    )
    chef_arrival_minutes_before: int = Field(
        ..., description="Minutes before event when chef arrives"
    )


class PolicyConfig(BaseModel):
    """Policy configuration for fees and limits."""

    reschedule_fee_cents: int = Field(..., description="Fee for late rescheduling in cents")
    free_reschedule_count: int = Field(..., description="Number of free reschedules allowed")


class ContactConfig(BaseModel):
    """Business contact information."""

    business_phone: str = Field(..., description="Business phone number")
    business_email: str = Field(..., description="Business email address")


class UpgradesConfig(BaseModel):
    """Premium protein upgrade prices (all amounts in cents per person)."""

    salmon_cents: int = Field(..., description="Salmon upgrade price in cents")
    scallops_cents: int = Field(..., description="Scallops upgrade price in cents")
    filet_mignon_cents: int = Field(..., description="Filet Mignon upgrade price in cents")
    lobster_tail_cents: int = Field(..., description="Lobster Tail upgrade price in cents")
    extra_protein_cents: int = Field(..., description="Extra protein (3rd+) price in cents")


class AddonsConfig(BaseModel):
    """Addon item prices (all amounts in cents per person)."""

    yakisoba_noodles_cents: int = Field(..., description="Yakisoba noodles price in cents")
    extra_fried_rice_cents: int = Field(..., description="Extra fried rice price in cents")
    extra_vegetables_cents: int = Field(..., description="Extra vegetables price in cents")
    edamame_cents: int = Field(..., description="Edamame price in cents")
    gyoza_cents: int = Field(..., description="Gyoza price in cents")


class MenuConfig(BaseModel):
    """Menu pricing including upgrades and addons."""

    upgrades: UpgradesConfig
    addons: AddonsConfig


class BusinessConfigResponse(BaseModel):
    """
    Complete business configuration response.

    This is the nested structure expected by the frontend useConfig hook.
    Backend stores flat, we transform to nested here.
    """

    pricing: PricingConfig
    travel: TravelConfig
    deposit: DepositConfig
    booking: BookingConfig
    timing: TimingConfig
    service: ServiceConfig
    policy: PolicyConfig
    contact: ContactConfig
    menu: Optional[MenuConfig] = None
    guest_limits: Optional[GuestLimitsConfig] = None
    source: str = Field(default="api", description="Data source for debugging")


# =============================================================================
# Policies Response Models
# =============================================================================

# These models MUST match the TypeScript interfaces in:
# apps/customer/src/hooks/usePolicies.ts


class DepositPolicy(BaseModel):
    """Deposit policy with amount and human-readable text."""

    amount: int = Field(..., description="Deposit amount in dollars")
    refund_days: int = Field(..., description="Days before event for refund eligibility")
    text: str = Field(..., description="Human-readable policy text")


class CancellationPolicy(BaseModel):
    """Cancellation policy with human-readable text."""

    refund_days: int = Field(..., description="Days before event for full refund")
    text: str = Field(..., description="Human-readable policy text")


class TravelPolicy(BaseModel):
    """Travel policy with rates and human-readable text."""

    free_miles: int = Field(..., description="Free travel radius in miles")
    per_mile_rate: float = Field(..., description="Cost per mile in dollars")
    text: str = Field(..., description="Human-readable policy text")


class BookingPolicy(BaseModel):
    """Booking policy with human-readable text."""

    advance_hours: int = Field(..., description="Minimum advance booking hours")
    text: str = Field(..., description="Human-readable policy text")


class PoliciesResponse(BaseModel):
    """
    Complete policies response with human-readable text.

    This is the structure expected by the frontend usePolicies hook.
    Text fields are dynamically generated from config values.
    """

    deposit: DepositPolicy
    cancellation: CancellationPolicy
    travel: TravelPolicy
    booking: BookingPolicy
    source: str = Field(default="api", description="Data source for debugging")
    fetched_at: str = Field(..., description="ISO timestamp when fetched")


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/config/all", response_model=BusinessConfigResponse)
async def get_all_config(
    db: AsyncSession = Depends(get_db),
) -> BusinessConfigResponse:
    """
    Get complete business configuration.

    This endpoint is PUBLIC (no authentication required).
    Used by customer website to display pricing, policies, etc.

    Returns:
        BusinessConfigResponse: Nested configuration matching frontend interfaces

    Frontend Consumer:
        apps/customer/src/hooks/useConfig.ts
    """
    try:
        # Get flat config from service
        config = await get_business_config(db)

        # Transform flat → nested structure for frontend
        response = BusinessConfigResponse(
            pricing=PricingConfig(
                adult_price_cents=config.adult_price_cents,
                child_price_cents=config.child_price_cents,
                child_free_under_age=config.child_free_under_age,
                party_minimum_cents=config.party_minimum_cents,
            ),
            travel=TravelConfig(
                free_miles=config.travel_free_miles,
                per_mile_cents=config.travel_per_mile_cents,
            ),
            deposit=DepositConfig(
                deposit_amount_cents=config.deposit_amount_cents,
                deposit_refundable_days=config.deposit_refundable_days,
            ),
            booking=BookingConfig(
                min_advance_hours=config.min_advance_hours,
            ),
            timing=TimingConfig(
                menu_change_cutoff_hours=config.menu_change_cutoff_hours,
                guest_count_finalize_hours=config.guest_count_finalize_hours,
                free_reschedule_hours=config.free_reschedule_hours,
            ),
            service=ServiceConfig(
                standard_duration_minutes=config.standard_duration_minutes,
                extended_duration_minutes=config.extended_duration_minutes,
                chef_arrival_minutes_before=config.chef_arrival_minutes_before,
            ),
            policy=PolicyConfig(
                reschedule_fee_cents=config.reschedule_fee_cents,
                free_reschedule_count=config.free_reschedule_count,
            ),
            contact=ContactConfig(
                business_phone=config.business_phone,
                business_email=config.business_email,
            ),
            menu=MenuConfig(
                upgrades=UpgradesConfig(
                    salmon_cents=config.salmon_upgrade_cents,
                    scallops_cents=config.scallops_upgrade_cents,
                    filet_mignon_cents=config.filet_mignon_upgrade_cents,
                    lobster_tail_cents=config.lobster_tail_upgrade_cents,
                    extra_protein_cents=config.extra_protein_cents,
                ),
                addons=AddonsConfig(
                    yakisoba_noodles_cents=config.yakisoba_noodles_cents,
                    extra_fried_rice_cents=config.extra_fried_rice_cents,
                    extra_vegetables_cents=config.extra_vegetables_cents,
                    edamame_cents=config.edamame_cents,
                    gyoza_cents=config.gyoza_cents,
                ),
            ),
            guest_limits=GuestLimitsConfig(
                minimum=1,
                maximum=100,
                minimum_for_hibachi=10,  # Party minimum / adult price ≈ 10
            ),
            source=config.source,
        )

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch configuration: {str(e)}",
        )


@router.get("/policies/current", response_model=PoliciesResponse)
async def get_current_policies(
    db: AsyncSession = Depends(get_db),
) -> PoliciesResponse:
    """
    Get current policies with human-readable text.

    This endpoint is PUBLIC (no authentication required).
    Used by customer website to display policy information.

    Returns:
        PoliciesResponse: Policies with computed text fields

    Frontend Consumer:
        apps/customer/src/hooks/usePolicies.ts
    """
    try:
        # Get flat config from service
        config = await get_business_config(db)

        # Convert cents to dollars for display
        deposit_dollars = config.deposit_amount_cents // 100
        per_mile_dollars = config.travel_per_mile_cents / 100

        # Generate human-readable policy text
        response = PoliciesResponse(
            deposit=DepositPolicy(
                amount=deposit_dollars,
                refund_days=config.deposit_refundable_days,
                text=f"${deposit_dollars} deposit required, refundable if canceled {config.deposit_refundable_days}+ days before event.",
            ),
            cancellation=CancellationPolicy(
                refund_days=config.deposit_refundable_days,
                text=f"Full refund if canceled {config.deposit_refundable_days}+ days before event.",
            ),
            travel=TravelPolicy(
                free_miles=config.travel_free_miles,
                per_mile_rate=per_mile_dollars,
                text=f"First {config.travel_free_miles} miles free, then ${per_mile_dollars:.0f}/mile.",
            ),
            booking=BookingPolicy(
                advance_hours=config.min_advance_hours,
                text=f"Book at least {config.min_advance_hours} hours in advance.",
            ),
            source=config.source,
            fetched_at=datetime.utcnow().isoformat() + "Z",
        )

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch policies: {str(e)}",
        )
