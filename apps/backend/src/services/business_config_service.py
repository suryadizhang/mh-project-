"""
Business Configuration Service
==============================

Centralizes all dynamic business configuration values.
Fetches from database (business_rules table) with environment fallbacks.

NEVER hardcode business values - always use this service!

Data Sources:
1. business_rules table (primary) - Admin-managed via UI
2. Environment variables (fallback) - For when DB unavailable
3. PricingService defaults (last resort) - Hardcoded minimums

Usage:
    from services.business_config_service import get_business_config

    config = await get_business_config(db)
    deposit = config.deposit_amount_cents  # 10000 ($100)
    adult_price = config.adult_price_cents  # 5500 ($55)

Admin UI:
    - Super Admin can modify these values via /admin/settings/pricing
    - Changes take effect immediately (no restart required)
    - All changes are logged for audit trail

Related Tables:
    - business_rules: General policies (deposit, cancellation, etc.)
    - core.travel_fee_configurations: Station-based travel fees
    - pricing.menu_items: Menu item prices
    - pricing.addon_items: Addon prices
"""

import logging
import os
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class BusinessConfig:
    """
    Business configuration values (all amounts in cents for precision).

    NOTE: These values are DYNAMIC and loaded from database.
    Use get_business_config() to fetch current values.

    See: apps/backend/scripts/seed_business_rules.sql for source data
    See: apps/customer/src/data/policies.json for customer-facing display
    """

    # Pricing (cents to avoid floating point issues)
    adult_price_cents: int = 5500  # $55.00 per adult (13+)
    child_price_cents: int = 3000  # $30.00 per child (6-12)
    child_free_under_age: int = 5  # Free for under 5
    party_minimum_cents: int = 55000  # $550.00 minimum

    # Deposit
    deposit_amount_cents: int = 10000  # $100.00 fixed deposit
    deposit_refundable_days: int = 7  # Refundable if canceled 7+ days before

    # Travel
    travel_free_miles: int = 30  # First 30 miles free
    travel_per_mile_cents: int = 200  # $2.00 per mile after free miles

    # Booking Rules
    min_advance_hours: int = 48  # Minimum 48 hours advance booking

    # Default Station (Fremont, CA - Main)
    # Format: CA-FREMONT-001 (human-readable station code)
    default_station_id: str = "CA-FREMONT-001"
    default_station_uuid: str = "22222222-2222-2222-2222-222222222222"
    default_station_name: str = "Fremont, CA (Main)"
    default_station_timezone: str = "America/Los_Angeles"
    default_station_address: str = "47481 Towhee St, Fremont, CA 94539"

    # Base location for travel fee calculations
    base_location_zipcode: str = "94539"  # Fremont, CA

    # Source tracking (for debugging)
    source: str = "defaults"  # "database" | "environment" | "defaults"


async def get_business_config(db: AsyncSession) -> BusinessConfig:
    """
    Fetch current business configuration from database with fallbacks.

    Priority:
    1. Database (business_rules table) - Primary source
    2. Environment variables - Fallback for dev/testing
    3. Hardcoded defaults - Last resort

    Args:
        db: Database session

    Returns:
        BusinessConfig with current values

    Example:
        config = await get_business_config(db)
        print(f"Deposit: ${config.deposit_amount_cents / 100}")
    """
    config = BusinessConfig()

    try:
        # Query business_rules table for pricing and policies
        result = await db.execute(
            text(
                """
            SELECT rule_type, title, value
            FROM business_rules
            WHERE is_active = true
            AND rule_type IN ('PRICING', 'PAYMENT', 'BOOKING')
        """
            )
        )
        rules = result.fetchall()

        if rules:
            config.source = "database"

            for rule in rules:
                rule_type, title, value = rule

                # Parse JSON value
                if isinstance(value, dict):
                    rule_value = value
                else:
                    import json

                    rule_value = json.loads(value) if value else {}

                # Extract values based on rule type and title
                if rule_type == "PAYMENT" and "Deposit" in title:
                    if "deposit_amount" in rule_value:
                        # Convert dollars to cents
                        config.deposit_amount_cents = int(
                            rule_value["deposit_amount"] * 100
                        )

                elif rule_type == "PRICING":
                    if (
                        "Party Minimum" in title
                        or "minimum_amount" in rule_value
                    ):
                        if "minimum_amount" in rule_value:
                            config.party_minimum_cents = int(
                                rule_value["minimum_amount"] * 100
                            )

                    if "Travel Fee" in title:
                        if "free_miles" in rule_value:
                            config.travel_free_miles = int(
                                rule_value["free_miles"]
                            )
                        if "per_mile_rate" in rule_value:
                            config.travel_per_mile_cents = int(
                                rule_value["per_mile_rate"] * 100
                            )

                elif rule_type == "BOOKING":
                    if "Advance" in title and "minimum_hours" in rule_value:
                        config.min_advance_hours = int(
                            rule_value["minimum_hours"]
                        )

            logger.info(
                f"✅ Loaded business config from database: deposit=${config.deposit_amount_cents/100}"
            )
        else:
            # Fall back to environment variables
            config = _load_from_environment()

    except Exception as e:
        logger.warning(
            f"⚠️ Failed to load business config from DB: {e}, using environment fallback"
        )
        config = _load_from_environment()

    return config


def _load_from_environment() -> BusinessConfig:
    """
    Load configuration from environment variables (fallback).

    Environment Variables:
        DEPOSIT_AMOUNT: Fixed deposit in dollars (default: 100)
        ADULT_PRICE: Adult price in dollars (default: 55)
        CHILD_PRICE: Child price in dollars (default: 30)
        PARTY_MINIMUM: Minimum total in dollars (default: 550)
        TRAVEL_FREE_MILES: Free travel distance (default: 30)
        TRAVEL_PER_MILE: Per mile rate in dollars (default: 2)
        MIN_ADVANCE_HOURS: Minimum booking advance (default: 48)
    """
    config = BusinessConfig()
    config.source = "environment"

    try:
        # Deposit (fixed $100, not percentage!)
        deposit = float(os.getenv("DEPOSIT_AMOUNT", "100"))
        config.deposit_amount_cents = int(deposit * 100)

        # Pricing
        adult = float(os.getenv("ADULT_PRICE", "55"))
        config.adult_price_cents = int(adult * 100)

        child = float(os.getenv("CHILD_PRICE", "30"))
        config.child_price_cents = int(child * 100)

        minimum = float(os.getenv("PARTY_MINIMUM", "550"))
        config.party_minimum_cents = int(minimum * 100)

        # Travel
        config.travel_free_miles = int(os.getenv("TRAVEL_FREE_MILES", "30"))
        per_mile = float(os.getenv("TRAVEL_PER_MILE", "2"))
        config.travel_per_mile_cents = int(per_mile * 100)

        # Booking
        config.min_advance_hours = int(os.getenv("MIN_ADVANCE_HOURS", "48"))

        # Station
        config.default_station_id = os.getenv(
            "DEFAULT_STATION_ID", "11111111-1111-1111-1111-111111111111"
        )

        logger.info(
            f"📋 Loaded business config from environment: deposit=${config.deposit_amount_cents/100}"
        )

    except ValueError as e:
        logger.error(
            f"❌ Invalid environment variable value: {e}, using hardcoded defaults"
        )
        config = BusinessConfig()
        config.source = "defaults"

    return config


# Synchronous version for places where async isn't available
def get_business_config_sync() -> BusinessConfig:
    """
    Get business configuration synchronously (environment-only).

    Use this ONLY when async is not available (e.g., in validators).
    Prefer get_business_config() for full database support.
    """
    return _load_from_environment()
