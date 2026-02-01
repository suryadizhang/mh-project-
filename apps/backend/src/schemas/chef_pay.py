"""
Chef Pay Schemas
================

Pydantic models for chef earnings calculation, scores, and pay management.

Access Control:
- Station Managers and Super Admins can view/manage chef pay
- Chefs CANNOT see pay visibility (user decision Dec 2024)

See: services/chef_pay_service.py for business logic
See: db/models/ops.py for database models
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# Chef Pay Configuration (SSoT Values)
# ============================================================================


class ChefPayConfigResponse(BaseModel):
    """
    Chef pay configuration values from SSoT (dynamic_variables table).

    NEW SYSTEM: Fixed per-tier rates (no multipliers).
    Each tier has its own per-person rates for adults, kids, and toddlers.

    Used by admin UI to display current pay rates.
    """

    # Junior Chef (new_chef) rates
    junior_adult_cents: int = Field(
        ..., description="Junior chef pay per adult ($10 = 1000)"
    )
    junior_kid_cents: int = Field(..., description="Junior chef pay per kid ($5 = 500)")
    junior_toddler_cents: int = Field(
        ..., description="Junior chef pay per toddler ($0 = 0)"
    )

    # Chef rates
    chef_adult_cents: int = Field(..., description="Chef pay per adult ($12 = 1200)")
    chef_kid_cents: int = Field(..., description="Chef pay per kid ($6 = 600)")
    chef_toddler_cents: int = Field(..., description="Chef pay per toddler ($0 = 0)")

    # Senior Chef rates
    senior_adult_cents: int = Field(
        ..., description="Senior chef pay per adult ($13 = 1300)"
    )
    senior_kid_cents: int = Field(
        ..., description="Senior chef pay per kid ($6.50 = 650)"
    )
    senior_toddler_cents: int = Field(
        ..., description="Senior chef pay per toddler ($0 = 0)"
    )

    # Station Manager rates
    manager_adult_cents: int = Field(
        ..., description="Manager pay per adult ($15 = 1500)"
    )
    manager_kid_cents: int = Field(..., description="Manager pay per kid ($7.50 = 750)")
    manager_toddler_cents: int = Field(
        ..., description="Manager pay per toddler ($0 = 0)"
    )

    # Travel fee
    travel_pct: int = Field(
        ..., description="Travel fee percentage chef receives (100 = 100%)"
    )

    source: str = Field(..., description="Data source: 'database' or 'defaults'")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Earnings Calculation
# ============================================================================


class CalculateEarningsRequest(BaseModel):
    """Request to calculate chef earnings for a specific booking."""

    booking_id: UUID = Field(..., description="Booking to calculate earnings for")
    chef_id: UUID = Field(..., description="Chef to calculate earnings for")


class EarningsBreakdownResponse(BaseModel):
    """
    Detailed breakdown of chef earnings calculation.

    NEW FORMULA (per-tier fixed rates, no multipliers):
    Chef Earnings = (adults × tier_adult_rate) + (kids × tier_kid_rate) + (toddlers × tier_toddler_rate) + travel_fee_portion

    Each tier has fixed per-person rates - no multiplier applied.
    """

    # Guest counts
    adults_count: int
    kids_count: int
    toddlers_count: int

    # Per-person rates for THIS chef's tier (in cents)
    adult_rate_cents: int = Field(..., description="Pay per adult for chef's tier")
    kid_rate_cents: int = Field(..., description="Pay per kid for chef's tier")
    toddler_rate_cents: int = Field(..., description="Pay per toddler for chef's tier")

    # Subtotals (count × rate)
    adults_total_cents: int = Field(..., description="Adults subtotal")
    kids_total_cents: int = Field(..., description="Kids subtotal")
    toddlers_total_cents: int = Field(..., description="Toddlers subtotal")

    # Travel fee
    travel_fee_cents: int = Field(..., description="Total travel fee in cents")
    travel_pct: int = Field(..., description="Travel fee percentage chef receives")
    travel_chef_cents: int = Field(..., description="Chef's travel fee portion")

    # Chef tier info
    pay_rate_class: str = Field(
        ..., description="NEW_CHEF, CHEF, SENIOR_CHEF, or STATION_MANAGER"
    )

    # Guest subtotal (adults + kids + toddlers, before travel)
    guest_subtotal_cents: int = Field(
        ..., description="Total for guests before travel fee"
    )

    # Final earnings
    final_earnings_cents: int = Field(..., description="Final chef earnings in cents")
    final_earnings_dollars: float = Field(..., description="Final earnings in dollars")

    model_config = ConfigDict(from_attributes=True)


class CalculateEarningsResponse(BaseModel):
    """Response with calculated earnings for a booking."""

    booking_id: UUID
    chef_id: UUID
    chef_name: str
    event_date: date

    breakdown: EarningsBreakdownResponse

    # Status
    calculated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Chef Score Recording
# ============================================================================


class RecordScoreRequest(BaseModel):
    """Request to record a performance score for a chef."""

    chef_id: UUID = Field(..., description="Chef to score")
    booking_id: Optional[UUID] = Field(
        None, description="Related booking (if event-specific)"
    )
    score: int = Field(..., ge=1, le=5, description="Score from 1-5")
    rater_type: str = Field(
        ...,
        description="Who rated: 'customer', 'station_manager', or 'admin'",
    )
    comment: Optional[str] = Field(
        None, max_length=1000, description="Optional feedback"
    )


class ScoreRecordedResponse(BaseModel):
    """Response after recording a chef score."""

    score_id: UUID
    chef_id: UUID
    score: int
    rater_type: str
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Earnings Summary (for period)
# ============================================================================


class EarningsSummaryRequest(BaseModel):
    """Request to get earnings summary for a period."""

    start_date: date
    end_date: date


class EarningsSummaryResponse(BaseModel):
    """Summary of chef earnings over a period."""

    chef_id: UUID
    chef_name: str
    period_start: date
    period_end: date

    # Aggregated totals
    total_events: int
    total_earnings_cents: int
    total_earnings_dollars: float

    # Breakdown by status
    pending_count: int
    pending_cents: int
    approved_count: int
    approved_cents: int
    paid_count: int
    paid_cents: int

    # Averages
    avg_earnings_per_event_cents: int
    avg_earnings_per_event_dollars: float

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Pay Rate Class Management
# ============================================================================


class UpdatePayRateClassRequest(BaseModel):
    """Request to update a chef's pay rate class."""

    pay_rate_class: str = Field(
        ...,
        description="New pay rate class: 'new_chef', 'chef', 'senior_chef', or 'station_manager'",
    )
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Reason for the change (for audit log)",
    )


class PayRateClassUpdatedResponse(BaseModel):
    """Response after updating pay rate class."""

    chef_id: UUID
    previous_pay_rate_class: str
    new_pay_rate_class: str
    updated_at: datetime
    updated_by: UUID

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Earnings Record Creation
# ============================================================================


class CreateEarningsRecordRequest(BaseModel):
    """Request to create an earnings record (after booking complete)."""

    booking_id: UUID
    chef_id: UUID
    status: str = Field(
        default="pending",
        description="Initial status: 'pending', 'approved', 'paid'",
    )


class EarningsRecordResponse(BaseModel):
    """Response with created earnings record."""

    earnings_id: UUID
    booking_id: UUID
    chef_id: UUID
    event_date: date
    final_earnings_cents: int
    final_earnings_dollars: float
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Chef Earnings List (for admin view)
# ============================================================================


class ChefEarningsListItem(BaseModel):
    """Single earnings record in a list."""

    id: UUID
    booking_id: UUID
    event_date: date
    final_earnings_cents: int
    final_earnings_dollars: float
    status: str
    created_at: datetime
    approved_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ChefEarningsListResponse(BaseModel):
    """List of earnings records for a chef."""

    chef_id: UUID
    chef_name: str
    earnings: list[ChefEarningsListItem]
    total_count: int
    total_earnings_cents: int
    total_earnings_dollars: float

    model_config = ConfigDict(from_attributes=True)
