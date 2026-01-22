"""
Business Configuration Service
==============================

Centralizes all dynamic business configuration values.
Fetches from database (dynamic_variables table) with environment fallbacks.

NEVER hardcode business values - always use this service!

Data Sources (Priority Order):
1. Redis cache (if available) - Fastest, 15 min TTL
2. dynamic_variables table (primary) - Admin-managed via UI
3. business_rules table (legacy fallback) - Old format
4. Environment variables (fallback) - For when DB unavailable
5. Hardcoded defaults (last resort) - Safety net

Usage:
    from services.business_config_service import get_business_config

    config = await get_business_config(db)
    deposit = config.deposit_amount_cents  # 10000 ($100)
    adult_price = config.adult_price_cents  # 5500 ($55)

    # For individual variable access:
    value = await get_dynamic_variable(db, 'pricing', 'adult_price_cents')

Admin UI:
    - Super Admin can modify these values via /admin/settings/pricing
    - Changes take effect immediately (no restart required)
    - All changes are logged in config_audit_log

Related Tables:
    - public.dynamic_variables: NEW SSoT table for all configurable values
    - public.config_audit_log: Immutable audit trail for changes
    - business_rules: Legacy policies (deprecated, for migration)
    - core.travel_fee_configurations: Station-based travel fees

Caching:
    - Redis-cached for 15 minutes to reduce DB load
    - Invalidate cache when admin updates any dynamic variable

SSoT Architecture:
    See: 20-SINGLE_SOURCE_OF_TRUTH.instructions.md
    See: database/migrations/004_dynamic_variables_ssot.sql
"""

import json
import logging
import os
import time
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from core.cache import CacheService

logger = logging.getLogger(__name__)

# Cache settings
BUSINESS_CONFIG_CACHE_KEY = "config:business"
BUSINESS_CONFIG_CACHE_TTL = 900  # 15 minutes

# Dynamic variables category keys (must match database)
CATEGORY_PRICING = "pricing"
CATEGORY_TRAVEL = "travel"
CATEGORY_BOOKING = "booking"
CATEGORY_DEPOSIT = "deposit"
CATEGORY_TIMING = "timing"
CATEGORY_SERVICE = "service"
CATEGORY_POLICY = "policy"
CATEGORY_CONTACT = "contact"


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
    deposit_refundable_days: int = 4  # Refundable if canceled 4+ days before

    # Travel
    travel_free_miles: int = 30  # First 30 miles free
    travel_per_mile_cents: int = 200  # $2.00 per mile after free miles

    # Booking Rules
    min_advance_hours: int = 48  # Minimum 48 hours advance booking

    # Timing (deadlines/cutoffs in hours)
    menu_change_cutoff_hours: int = 12  # No menu changes within 12 hours of event
    guest_count_finalize_hours: int = (
        24  # Guest count must be finalized 24 hours before
    )
    free_reschedule_hours: int = 24  # Free reschedule allowed with 24+ hours notice

    # Service (duration and logistics)
    standard_duration_minutes: int = 90  # Standard service duration
    extended_duration_minutes: int = 150  # Max duration for large parties (20+ guests)
    chef_arrival_minutes_before: int = 20  # Chef arrives 15-30 min early

    # Policy (fees and limits)
    reschedule_fee_cents: int = 20000  # $200 fee for late reschedules
    free_reschedule_count: int = 1  # One free reschedule allowed

    # Contact (business info)
    business_phone: str = "(916) 740-8768"
    business_email: str = "cs@myhibachichef.com"

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


# Module-level cache for sync fallback (tiered approach)
# This gets populated by async get_business_config() and used by get_business_config_sync()
_CACHED_CONFIG: Optional[BusinessConfig] = None
_CACHED_CONFIG_TIMESTAMP: Optional[float] = None
_SYNC_CACHE_TTL = 300  # 5 minutes for in-memory sync cache


async def get_business_config(
    db: AsyncSession, cache: "CacheService | None" = None
) -> BusinessConfig:
    """
    Fetch current business configuration from database with fallbacks.

    Supports optional Redis caching for 15 minutes to reduce DB load.

    Priority:
    1. Redis cache (if available) - Fastest
    2. dynamic_variables table (NEW SSoT) - Primary source
    3. business_rules table (legacy) - Fallback for migration
    4. Environment variables - Fallback for dev/testing
    5. Hardcoded defaults - Last resort

    Args:
        db: Database session
        cache: Optional CacheService for Redis caching

    Returns:
        BusinessConfig with current values

    Example:
        config = await get_business_config(db)
        print(f"Deposit: ${config.deposit_amount_cents / 100}")

        # With caching (recommended in hot paths)
        config = await get_business_config(db, cache=app.state.cache)
    """
    # Try cache first if available
    if cache:
        try:
            cached_data = await cache.get(BUSINESS_CONFIG_CACHE_KEY)
            if cached_data:
                logger.debug("📦 Business config loaded from cache")
                config = BusinessConfig(**cached_data)
                config.source = "cache"
                return config
        except Exception as e:
            logger.warning(f"Cache read failed: {e}, falling back to DB")

    config = BusinessConfig()

    try:
        # PRIORITY 1: Query NEW dynamic_variables table (SSoT)
        result = await db.execute(
            text(
                """
            SELECT category, key, value
            FROM dynamic_variables
            WHERE is_active = true
            AND (effective_from IS NULL OR effective_from <= NOW())
            AND (effective_to IS NULL OR effective_to > NOW())
        """
            )
        )
        variables = result.fetchall()

        if variables:
            config.source = "database_dynamic_variables"
            config = _map_dynamic_variables_to_config(variables, config)
            logger.info(
                f"✅ Loaded business config from dynamic_variables: deposit=${config.deposit_amount_cents/100}"
            )
        else:
            # PRIORITY 2: Fallback to legacy business_rules table
            logger.warning(
                "⚠️ No dynamic_variables found, falling back to business_rules"
            )
            config = await _load_from_business_rules(db, config)

        # Cache the result for future requests
        if cache:
            try:
                await cache.set(
                    BUSINESS_CONFIG_CACHE_KEY,
                    asdict(config),
                    ttl=BUSINESS_CONFIG_CACHE_TTL,
                )
                logger.debug("📦 Business config cached for 15 minutes")
            except Exception as e:
                logger.warning(f"Failed to cache business config: {e}")

    except Exception as e:
        logger.warning(
            f"⚠️ Failed to load business config from DB: {e}, using environment fallback"
        )
        config = _load_from_environment()

    # Populate module-level cache for sync fallback
    global _CACHED_CONFIG, _CACHED_CONFIG_TIMESTAMP
    _CACHED_CONFIG = config
    _CACHED_CONFIG_TIMESTAMP = time.time()

    return config


def _map_dynamic_variables_to_config(
    variables: list, config: BusinessConfig
) -> BusinessConfig:
    """
    Map dynamic_variables rows to BusinessConfig dataclass.

    Type is inferred from the JSONB value structure.
    """
    for row in variables:
        category, key, value = row

        # Parse value (type is inferred from JSONB structure)
        parsed_value = _parse_variable_value(value)

        # Map to config fields
        if category == CATEGORY_PRICING:
            if key == "adult_price_cents":
                config.adult_price_cents = int(parsed_value)
            elif key == "child_price_cents":
                config.child_price_cents = int(parsed_value)
            elif key == "child_free_under_age":
                config.child_free_under_age = int(parsed_value)
            elif key == "party_minimum_cents":
                config.party_minimum_cents = int(parsed_value)

        elif category == CATEGORY_DEPOSIT:
            if key == "deposit_amount_cents":
                config.deposit_amount_cents = int(parsed_value)
            elif key == "deposit_refundable_days":
                config.deposit_refundable_days = int(parsed_value)

        elif category == CATEGORY_TRAVEL:
            if key == "travel_free_miles":
                config.travel_free_miles = int(parsed_value)
            elif key == "travel_per_mile_cents":
                config.travel_per_mile_cents = int(parsed_value)

        elif category == CATEGORY_BOOKING:
            if key == "min_advance_hours":
                config.min_advance_hours = int(parsed_value)

        elif category == CATEGORY_TIMING:
            if key == "menu_change_cutoff_hours":
                config.menu_change_cutoff_hours = int(parsed_value)
            elif key == "guest_count_finalize_hours":
                config.guest_count_finalize_hours = int(parsed_value)
            elif key == "free_reschedule_hours":
                config.free_reschedule_hours = int(parsed_value)

        elif category == CATEGORY_SERVICE:
            if key == "standard_duration_minutes":
                config.standard_duration_minutes = int(parsed_value)
            elif key == "extended_duration_minutes":
                config.extended_duration_minutes = int(parsed_value)
            elif key == "chef_arrival_minutes_before":
                config.chef_arrival_minutes_before = int(parsed_value)

        elif category == CATEGORY_POLICY:
            if key == "reschedule_fee_cents":
                config.reschedule_fee_cents = int(parsed_value)
            elif key == "free_reschedule_count":
                config.free_reschedule_count = int(parsed_value)

        elif category == CATEGORY_CONTACT:
            if key == "business_phone":
                config.business_phone = str(parsed_value)
            elif key == "business_email":
                config.business_email = str(parsed_value)

    return config


def _parse_variable_value(value: Any) -> Any:
    """
    Parse a dynamic variable value from JSONB storage.

    Handles multiple formats:
    - Direct values: 5500, "string", true
    - Wrapped values: {"amount": 5500}, {"value": 30}, {"list": [...]}

    Returns the unwrapped value for further processing.
    """
    if value is None:
        return None

    # Handle JSONB storage (value might be wrapped in a dict)
    if isinstance(value, dict):
        # Extract the actual value if wrapped - support multiple keys
        if "value" in value:
            return value["value"]
        elif "amount" in value:
            return value["amount"]
        elif "list" in value:
            return value["list"]
        # If it's a dict but not wrapped, return as-is (for complex config objects)
        return value

    # Direct values (int, float, str, bool) - return as-is
    return value


async def _load_from_business_rules(
    db: AsyncSession, config: BusinessConfig
) -> BusinessConfig:
    """
    Fallback: Load configuration from legacy business_rules table.

    This is for backwards compatibility during migration.
    Will be deprecated once all data is in dynamic_variables.
    """
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
        config.source = "database_business_rules"

        for rule in rules:
            rule_type, title, value = rule

            # Parse JSON value
            if isinstance(value, dict):
                rule_value = value
            else:
                rule_value = json.loads(value) if value else {}

            # Extract values based on rule type and title
            if rule_type == "PAYMENT" and "Deposit" in title:
                if "deposit_amount" in rule_value:
                    # Convert dollars to cents
                    config.deposit_amount_cents = int(
                        rule_value["deposit_amount"] * 100
                    )

            elif rule_type == "PRICING":
                if "Party Minimum" in title or "minimum_amount" in rule_value:
                    if "minimum_amount" in rule_value:
                        config.party_minimum_cents = int(
                            rule_value["minimum_amount"] * 100
                        )

                if "Travel Fee" in title:
                    if "free_miles" in rule_value:
                        config.travel_free_miles = int(rule_value["free_miles"])
                    if "per_mile_rate" in rule_value:
                        config.travel_per_mile_cents = int(
                            rule_value["per_mile_rate"] * 100
                        )

            elif rule_type == "BOOKING":
                if "Advance" in title and "minimum_hours" in rule_value:
                    config.min_advance_hours = int(rule_value["minimum_hours"])

        logger.info(
            f"✅ Loaded business config from business_rules: deposit=${config.deposit_amount_cents/100}"
        )
    else:
        # Fall back to environment variables
        config = _load_from_environment()

    return config


async def invalidate_business_config_cache(cache: "CacheService") -> bool:
    """
    Invalidate the business config cache.

    Call this after admin updates business rules.

    Args:
        cache: CacheService instance

    Returns:
        True if invalidated, False on error
    """
    try:
        await cache.delete(BUSINESS_CONFIG_CACHE_KEY)
        logger.info("🗑️ Business config cache invalidated")
        return True
    except Exception as e:
        logger.error(f"Failed to invalidate business config cache: {e}")
        return False


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
    Get business configuration synchronously with tiered fallback.

    Priority:
    1. Module-level cache (populated by async get_business_config) - if < 5 min old
    2. Environment variables - fallback
    3. Hardcoded defaults - last resort

    Use this ONLY when async is not available (e.g., in validators, Pydantic models).
    Prefer get_business_config() for full database support with Redis caching.
    """
    global _CACHED_CONFIG, _CACHED_CONFIG_TIMESTAMP

    # Check if module-level cache is valid (< 5 minutes old)
    if _CACHED_CONFIG is not None and _CACHED_CONFIG_TIMESTAMP is not None:
        cache_age = time.time() - _CACHED_CONFIG_TIMESTAMP
        if cache_age < _SYNC_CACHE_TTL:
            logger.debug(f"📦 Using module-level cached config (age: {cache_age:.1f}s)")
            return _CACHED_CONFIG
        else:
            logger.debug(
                f"⏰ Module-level cache expired (age: {cache_age:.1f}s), using environment"
            )

    return _load_from_environment()
