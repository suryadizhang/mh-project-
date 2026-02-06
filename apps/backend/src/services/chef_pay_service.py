"""
Chef Pay Service
================

Calculates chef earnings based on SSoT (Single Source of Truth) variables.

Formula:
    Chef Event Income = (party_adults × tier_adult_rate) + (party_kids × tier_kid_rate)
                      + (party_toddlers × 0) + travel_fee

Each chef tier has its own FIXED rates (NOT a base × multiplier system):
    - Junior Chef (new_chef): $10/adult, $5/kid, $0/toddler
    - Chef:                   $12/adult, $6/kid, $0/toddler
    - Senior Chef:            $13/adult, $6.50/kid, $0/toddler
    - Station Manager:        $15/adult, $7.50/kid, $0/toddler

SSoT Variables (category: chef_pay):
    - junior_adult_cents: Junior rate per adult (default: 1000 = $10.00)
    - junior_kid_cents: Junior rate per child 6-12 (default: 500 = $5.00)
    - junior_toddler_cents: Junior rate per toddler (default: 0)
    - chef_adult_cents: Chef rate per adult (default: 1200 = $12.00)
    - chef_kid_cents: Chef rate per child 6-12 (default: 600 = $6.00)
    - chef_toddler_cents: Chef rate per toddler (default: 0)
    - senior_adult_cents: Senior rate per adult (default: 1300 = $13.00)
    - senior_kid_cents: Senior rate per child 6-12 (default: 650 = $6.50)
    - senior_toddler_cents: Senior rate per toddler (default: 0)
    - manager_adult_cents: Manager rate per adult (default: 1500 = $15.00)
    - manager_kid_cents: Manager rate per child 6-12 (default: 750 = $7.50)
    - manager_toddler_cents: Manager rate per toddler (default: 0)
    - travel_pct: Travel fee percentage to chef (default: 100%)

Usage:
    from services.chef_pay_service import (
        calculate_chef_earnings,
        record_chef_score,
        get_chef_earnings_summary,
    )

    # Calculate what chef earns for a booking
    earnings = await calculate_chef_earnings(db, booking, chef)

    # Record a score for a chef
    score = await record_chef_score(db, chef_id, booking_id, 4.5, "CUSTOMER", customer_id)

    # Get chef's earnings summary for a period
    summary = await get_chef_earnings_summary(db, chef_id, start_date, end_date)

Related:
    - Migration: database/migrations/021_fix_chef_pay_tiers.sql
    - Models: db/models/ops.py (ChefEarnings, ChefScore, PayRateClass, SeniorityLevel)
    - Business Config: services/business_config_service.py
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from db.models.core import Booking
    from db.models.ops import Chef

logger = logging.getLogger(__name__)


# =============================================================================
# SSoT Category Constant
# =============================================================================

CATEGORY_CHEF_PAY = "chef_pay"


# =============================================================================
# Chef Pay Configuration (fetched from SSoT)
# =============================================================================


@dataclass
class ChefTierRates:
    """
    Pay rates for a single chef tier (all amounts in cents).
    """

    adult_cents: int
    kid_cents: int
    toddler_cents: int = 0


@dataclass
class ChefPayConfig:
    """
    Chef pay configuration values (all amounts in cents).

    Each tier has its own FIXED rates - NOT a base × multiplier system.
    Loaded from dynamic_variables table with sensible defaults.
    """

    # Junior Chef (new_chef) rates
    junior_adult_cents: int = 1000  # $10.00 per adult
    junior_kid_cents: int = 500  # $5.00 per child (6-12)
    junior_toddler_cents: int = 0  # $0.00 per toddler (under 5)

    # Chef rates
    chef_adult_cents: int = 1200  # $12.00 per adult
    chef_kid_cents: int = 600  # $6.00 per child (6-12)
    chef_toddler_cents: int = 0  # $0.00 per toddler

    # Senior Chef rates
    senior_adult_cents: int = 1300  # $13.00 per adult
    senior_kid_cents: int = 650  # $6.50 per child (6-12)
    senior_toddler_cents: int = 0  # $0.00 per toddler

    # Station Manager rates (backup when all chefs busy)
    manager_adult_cents: int = 1500  # $15.00 per adult
    manager_kid_cents: int = 750  # $7.50 per child (6-12)
    manager_toddler_cents: int = 0  # $0.00 per toddler

    # Travel fee percentage (100 = chef gets 100% of travel fee)
    travel_pct: int = 100

    # Source tracking
    source: str = "defaults"

    def get_tier_rates(self, pay_rate_class: str) -> ChefTierRates:
        """
        Get rates for a specific chef tier.

        Args:
            pay_rate_class: One of 'new_chef', 'chef', 'senior_chef', 'station_manager'

        Returns:
            ChefTierRates for the specified tier
        """
        tier_map = {
            "new_chef": ChefTierRates(
                adult_cents=self.junior_adult_cents,
                kid_cents=self.junior_kid_cents,
                toddler_cents=self.junior_toddler_cents,
            ),
            "chef": ChefTierRates(
                adult_cents=self.chef_adult_cents,
                kid_cents=self.chef_kid_cents,
                toddler_cents=self.chef_toddler_cents,
            ),
            "senior_chef": ChefTierRates(
                adult_cents=self.senior_adult_cents,
                kid_cents=self.senior_kid_cents,
                toddler_cents=self.senior_toddler_cents,
            ),
            "station_manager": ChefTierRates(
                adult_cents=self.manager_adult_cents,
                kid_cents=self.manager_kid_cents,
                toddler_cents=self.manager_toddler_cents,
            ),
        }
        # Default to 'chef' rates if unknown tier
        return tier_map.get(pay_rate_class, tier_map["chef"])


async def get_chef_pay_config(db: AsyncSession) -> ChefPayConfig:
    """
    Fetch chef pay configuration from dynamic_variables table.

    Falls back to sensible defaults if not configured.

    Args:
        db: Database session

    Returns:
        ChefPayConfig with current values
    """
    config = ChefPayConfig()

    try:
        result = await db.execute(
            text(
                """
                SELECT key, value
                FROM dynamic_variables
                WHERE category = :category
                AND is_active = true
                AND (effective_from IS NULL OR effective_from <= NOW())
                AND (effective_to IS NULL OR effective_to > NOW())
            """
            ),
            {"category": CATEGORY_CHEF_PAY},
        )
        variables = result.fetchall()

        if variables:
            config.source = "database"
            for row in variables:
                key, value = row

                # Parse value (handle JSONB wrapping)
                parsed = _parse_value(value)
                if parsed is None:
                    continue  # Skip None values, keep defaults

                # Junior Chef rates
                if key == "junior_adult_cents":
                    config.junior_adult_cents = int(parsed)
                elif key == "junior_kid_cents":
                    config.junior_kid_cents = int(parsed)
                elif key == "junior_toddler_cents":
                    config.junior_toddler_cents = int(parsed)
                # Chef rates
                elif key == "chef_adult_cents":
                    config.chef_adult_cents = int(parsed)
                elif key == "chef_kid_cents":
                    config.chef_kid_cents = int(parsed)
                elif key == "chef_toddler_cents":
                    config.chef_toddler_cents = int(parsed)
                # Senior Chef rates
                elif key == "senior_adult_cents":
                    config.senior_adult_cents = int(parsed)
                elif key == "senior_kid_cents":
                    config.senior_kid_cents = int(parsed)
                elif key == "senior_toddler_cents":
                    config.senior_toddler_cents = int(parsed)
                # Station Manager rates
                elif key == "manager_adult_cents":
                    config.manager_adult_cents = int(parsed)
                elif key == "manager_kid_cents":
                    config.manager_kid_cents = int(parsed)
                elif key == "manager_toddler_cents":
                    config.manager_toddler_cents = int(parsed)
                # Travel percentage
                elif key == "travel_pct":
                    config.travel_pct = int(parsed)

            logger.info(
                f"✅ Loaded chef pay config from DB: junior=${config.junior_adult_cents/100}/adult, chef=${config.chef_adult_cents/100}/adult, senior=${config.senior_adult_cents/100}/adult, manager=${config.manager_adult_cents/100}/adult"
            )
        else:
            logger.warning("⚠️ No chef pay variables found, using defaults")

    except Exception as e:
        logger.error(f"❌ Failed to load chef pay config: {e}")

    return config


def _parse_value(value):
    """Parse JSONB value, handling wrapped and direct values."""
    if value is None:
        return None
    if isinstance(value, dict):
        return value.get("value", value.get("amount", value))
    return value


# =============================================================================
# Earnings Calculation
# =============================================================================


@dataclass
class ChefEarningsResult:
    """
    Result of chef earnings calculation.

    Pay is calculated using FIXED tier rates (not base × multiplier!):
    - Junior Chef: $10/adult, $5/kid, $0/toddler
    - Chef: $12/adult, $6/kid, $0/toddler
    - Senior Chef: $13/adult, $6.50/kid, $0/toddler
    - Station Manager: $15/adult, $7.50/kid, $0/toddler
    + 100% of travel fee
    """

    # Components
    adult_component_cents: int  # adults × tier rate
    kid_component_cents: int  # kids × tier rate
    toddler_component_cents: int  # toddlers × tier rate (always 0)
    travel_component_cents: int  # 100% of travel fee goes to chef

    # Total
    total_earnings_cents: int  # Sum of all components

    # Rates used (for display/audit)
    adult_rate_cents: int  # Per-adult rate for this tier
    kid_rate_cents: int  # Per-kid rate for this tier

    # Metadata
    pay_rate_class: str  # new_chef, chef, senior_chef, station_manager

    @property
    def total_earnings_dollars(self) -> Decimal:
        return Decimal(self.total_earnings_cents) / 100

    @property
    def adult_rate_dollars(self) -> Decimal:
        return Decimal(self.adult_rate_cents) / 100

    @property
    def kid_rate_dollars(self) -> Decimal:
        return Decimal(self.kid_rate_cents) / 100


async def calculate_chef_earnings(
    db: AsyncSession,
    booking_id: UUID,
    chef_id: UUID,
) -> Optional[ChefEarningsResult]:
    """
    Calculate chef earnings for a booking using per-tier fixed rates.

    Each tier has its own fixed rates (NOT a multiplier system):
        - new_chef:        $10/adult,  $5/kid,    $0/toddler
        - chef:            $12/adult,  $6/kid,    $0/toddler
        - senior_chef:     $13/adult,  $6.50/kid, $0/toddler
        - station_manager: $15/adult,  $7.50/kid, $0/toddler

    Travel fee: 100% goes to chef

    Args:
        db: Database session
        booking_id: UUID of the booking
        chef_id: UUID of the chef

    Returns:
        ChefEarningsResult with full breakdown, or None if booking/chef not found

    Example:
        >>> result = await calculate_chef_earnings(db, booking_id, chef_id)
        >>> if result:
        ...     print(f"Chef earns ${result.total_earnings_dollars}")
    """
    # Import models here to avoid circular imports
    from sqlalchemy import select

    from db.models.core import Booking
    from db.models.ops import Chef

    # Fetch booking
    booking_result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = booking_result.scalar_one_or_none()
    if not booking:
        logger.warning(f"⚠️ Booking {booking_id} not found for earnings calculation")
        return None

    # Fetch chef
    chef_result = await db.execute(select(Chef).where(Chef.id == chef_id))
    chef = chef_result.scalar_one_or_none()
    if not chef:
        logger.warning(f"⚠️ Chef {chef_id} not found for earnings calculation")
        return None

    config = await get_chef_pay_config(db)

    # Get party counts from booking
    adults = booking.party_adults or 0
    kids = booking.party_kids or 0
    toddlers = getattr(booking, "party_toddlers", 0) or 0

    # Get chef's pay rate class (lowercase enum value)
    pay_rate_class = chef.pay_rate_class if hasattr(chef, "pay_rate_class") else "new_chef"
    if pay_rate_class is not None and hasattr(pay_rate_class, "value"):
        pay_rate_class = pay_rate_class.value
    # Normalize to lowercase for consistency
    pay_rate_class = (pay_rate_class or "new_chef").lower()

    # Get tier-specific rates (NOT a multiplier - each tier has fixed rates)
    tier_rates = config.get_tier_rates(pay_rate_class)

    # Calculate components using tier-specific rates
    adult_component = adults * tier_rates.adult_cents
    kid_component = kids * tier_rates.kid_cents
    toddler_component = toddlers * tier_rates.toddler_cents  # Always $0

    # Get travel fee from booking (stored in dollars, convert to cents)
    travel_fee_cents = int((booking.travel_fee or 0) * 100) if booking.travel_fee else 0
    # 100% of travel fee goes to chef
    travel_component = int(travel_fee_cents * config.travel_pct / 100)

    # Calculate total earnings (sum of all components)
    total_earnings = adult_component + kid_component + toddler_component + travel_component

    logger.info(
        f"💰 Chef earnings calculated: ${total_earnings/100:.2f} "
        f"({adults} adults × ${tier_rates.adult_cents/100:.2f}, "
        f"{kids} kids × ${tier_rates.kid_cents/100:.2f}, "
        f"{toddlers} toddlers × $0, "
        f"${travel_component/100:.2f} travel) "
        f"[{pay_rate_class}]"
    )

    return ChefEarningsResult(
        adult_component_cents=adult_component,
        kid_component_cents=kid_component,
        toddler_component_cents=toddler_component,
        travel_component_cents=travel_component,
        total_earnings_cents=total_earnings,
        adult_rate_cents=tier_rates.adult_cents,
        kid_rate_cents=tier_rates.kid_cents,
        pay_rate_class=pay_rate_class,
    )


# =============================================================================
# Chef Score Recording
# =============================================================================


async def record_chef_score(
    db: AsyncSession,
    chef_id: UUID,
    booking_id: UUID,
    score: float,
    rater_type: str,
    rater_id: Optional[UUID] = None,
    rater_name: Optional[str] = None,
    comment: Optional[str] = None,
    categories: Optional[dict] = None,
) -> UUID:
    """
    Record a performance score for a chef.

    Args:
        db: Database session
        chef_id: Chef being rated
        booking_id: Related booking
        score: Overall score (0.0 to 5.0)
        rater_type: CUSTOMER, STATION_MANAGER, ADMIN, SYSTEM
        rater_id: Optional UUID of rater (user or customer)
        rater_name: Optional display name of rater
        comment: Optional feedback comment
        categories: Optional dict of category scores
            e.g., {"food_quality": 4.5, "entertainment": 5.0, "punctuality": 4.0}

    Returns:
        UUID of created ChefScore record

    Example:
        >>> score_id = await record_chef_score(
        ...     db, chef_id, booking_id, 4.5, "CUSTOMER",
        ...     rater_id=customer_id, categories={"food_quality": 4.5}
        ... )
    """
    import json

    result = await db.execute(
        text(
            """
            INSERT INTO ops.chef_scores (
                chef_id, booking_id, score, rater_type,
                rater_id, rater_name, comment, categories, scored_at
            ) VALUES (
                :chef_id, :booking_id, :score, :rater_type,
                :rater_id, :rater_name, :comment, :categories, NOW()
            )
            RETURNING id
        """
        ),
        {
            "chef_id": str(chef_id),
            "booking_id": str(booking_id),
            "score": score,
            "rater_type": rater_type,
            "rater_id": str(rater_id) if rater_id else None,
            "rater_name": rater_name,
            "comment": comment,
            "categories": json.dumps(categories) if categories else None,
        },
    )

    row = result.fetchone()
    if row is None:
        raise ValueError(f"Failed to insert chef score for chef {chef_id}")
    score_id = UUID(str(row[0]))

    await db.commit()

    logger.info(f"📊 Recorded chef score: chef={chef_id}, score={score}, type={rater_type}")

    return score_id


# =============================================================================
# Earnings Summary
# =============================================================================


@dataclass
class ChefEarningsSummary:
    """Summary of chef earnings over a period."""

    chef_id: UUID
    period_start: date
    period_end: date

    # Aggregates
    total_events: int
    total_earnings_cents: int
    total_travel_cents: int

    # Averages
    avg_earnings_per_event_cents: int
    avg_score: Optional[float]

    @property
    def total_earnings_dollars(self) -> Decimal:
        return Decimal(self.total_earnings_cents) / 100


async def get_chef_earnings_summary(
    db: AsyncSession,
    chef_id: UUID,
    start_date: date,
    end_date: date,
) -> ChefEarningsSummary:
    """
    Get aggregated earnings summary for a chef over a period.

    Args:
        db: Database session
        chef_id: Chef to summarize
        start_date: Start of period (inclusive)
        end_date: End of period (inclusive)

    Returns:
        ChefEarningsSummary with aggregated data

    Note:
        This queries the chef_earnings table for completed/paid events.
        For pending calculations, use calculate_chef_earnings() per booking.
    """
    # Get earnings totals
    result = await db.execute(
        text(
            """
            SELECT
                COUNT(*) as total_events,
                COALESCE(SUM(final_earnings_cents), 0) as total_earnings,
                COALESCE(SUM(travel_component_cents), 0) as total_travel
            FROM ops.chef_earnings
            WHERE chef_id = :chef_id
            AND event_date >= :start_date
            AND event_date <= :end_date
            AND status IN ('COMPLETED', 'PAID')
        """
        ),
        {
            "chef_id": str(chef_id),
            "start_date": start_date,
            "end_date": end_date,
        },
    )

    row = result.fetchone()
    if row:
        total_events = row[0] or 0
        total_earnings = row[1] or 0
        total_travel = row[2] or 0
    else:
        total_events = 0
        total_earnings = 0
        total_travel = 0

    # Calculate average
    avg_per_event = total_earnings // total_events if total_events > 0 else 0

    # Get average score
    score_result = await db.execute(
        text(
            """
            SELECT AVG(score)
            FROM ops.chef_scores
            WHERE chef_id = :chef_id
            AND scored_at >= :start_date
            AND scored_at <= :end_date + interval '1 day'
        """
        ),
        {
            "chef_id": str(chef_id),
            "start_date": start_date,
            "end_date": end_date,
        },
    )

    avg_score_row = score_result.fetchone()
    avg_score = float(avg_score_row[0]) if avg_score_row and avg_score_row[0] else None

    return ChefEarningsSummary(
        chef_id=chef_id,
        period_start=start_date,
        period_end=end_date,
        total_events=total_events,
        total_earnings_cents=total_earnings,
        total_travel_cents=total_travel,
        avg_earnings_per_event_cents=avg_per_event,
        avg_score=avg_score,
    )


# =============================================================================
# Create Earnings Record
# =============================================================================


async def create_earnings_record(
    db: AsyncSession,
    chef_id: UUID,
    booking_id: UUID,
    earnings_result: ChefEarningsResult,
    event_date: date,
    status: str = "PENDING",
) -> UUID:
    """
    Create a chef earnings record in the database.

    Called after calculating earnings to persist the record.

    Args:
        db: Database session
        chef_id: Chef who earned
        booking_id: Related booking
        earnings_result: Calculated earnings from calculate_chef_earnings()
        event_date: Date of the event
        status: PENDING, COMPLETED, PAID, DISPUTED

    Returns:
        UUID of created ChefEarnings record
    """
    result = await db.execute(
        text(
            """
            INSERT INTO ops.chef_earnings (
                chef_id, booking_id, event_date,
                base_earnings_cents, multiplier_applied, final_earnings_cents,
                adult_component_cents, kid_component_cents, toddler_component_cents,
                travel_component_cents, pay_rate_class, status
            ) VALUES (
                :chef_id, :booking_id, :event_date,
                :base_earnings, :multiplier, :final_earnings,
                :adult_comp, :kid_comp, :toddler_comp,
                :travel_comp, :pay_rate_class, :status
            )
            RETURNING id
        """
        ),
        {
            "chef_id": str(chef_id),
            "booking_id": str(booking_id),
            "event_date": event_date,
            "base_earnings": earnings_result.base_earnings_cents,
            "multiplier": earnings_result.multiplier_pct,
            "final_earnings": earnings_result.final_earnings_cents,
            "adult_comp": earnings_result.adult_component_cents,
            "kid_comp": earnings_result.kid_component_cents,
            "toddler_comp": earnings_result.toddler_component_cents,
            "travel_comp": earnings_result.travel_component_cents,
            "pay_rate_class": earnings_result.pay_rate_class,
            "status": status,
        },
    )

    row = result.fetchone()
    if row is None:
        raise ValueError(f"Failed to insert earnings record for chef {chef_id}")
    earnings_id = UUID(str(row[0]))

    await db.commit()

    logger.info(
        f"💵 Created earnings record: chef={chef_id}, "
        f"amount=${earnings_result.final_earnings_cents/100:.2f}"
    )

    return earnings_id


# =============================================================================
# Update Chef Pay Rate
# =============================================================================


async def update_chef_pay_rate_class(
    db: AsyncSession,
    chef_id: UUID,
    new_pay_rate_class: str,
    updated_by: UUID,
    reason: Optional[str] = None,
) -> bool:
    """
    Update a chef's pay rate class.

    Only Station Manager or Admin can do this.

    Args:
        db: Database session
        chef_id: Chef to update
        new_pay_rate_class: NEW_CHEF, CHEF, or SENIOR_CHEF
        updated_by: User ID making the change
        reason: Optional reason for change

    Returns:
        True if updated successfully
    """
    valid_classes = ["new_chef", "chef", "senior_chef"]
    if new_pay_rate_class not in valid_classes:
        raise ValueError(f"Invalid pay rate class. Must be one of: {valid_classes}")

    await db.execute(
        text(
            """
            UPDATE ops.chefs
            SET pay_rate_class = :pay_rate_class,
                updated_at = NOW()
            WHERE id = :chef_id
        """
        ),
        {
            "chef_id": str(chef_id),
            "pay_rate_class": new_pay_rate_class,
        },
    )

    await db.commit()

    logger.info(
        f"🔄 Updated chef pay rate: chef={chef_id}, "
        f"new_class={new_pay_rate_class}, by={updated_by}"
    )

    return True
