"""
Urgent Booking Calculation Service
==================================

Provides timezone-aware calculations for booking urgency tracking.
CRITICAL: All date calculations use venue timezone for flawless date monitoring.

This service is the foundation for the FAILPROOF chef assignment alert system.

Features:
- Venue timezone-aware date calculations
- Booking window classification (DISTANT/UPCOMING/URGENT)
- Days-until-event calculation from venue perspective
- Urgency flag determination using SSoT thresholds

Usage:
    from services.urgent_booking_service import (
        calculate_days_until_event,
        determine_booking_window,
        is_booking_urgent,
        update_booking_urgency,
    )

    # Calculate days until event using venue timezone
    days = calculate_days_until_event(
        event_date=booking.event_date,
        event_time=booking.event_time,
        venue_timezone="America/Los_Angeles"
    )

    # Determine booking window classification
    window = determine_booking_window(days)  # Returns "DISTANT", "UPCOMING", or "URGENT"

    # Check if booking is urgent
    is_urgent = is_booking_urgent(days, config)  # Uses SSoT threshold

Related:
- Migration: 021_urgent_booking_system.sql
- Model: core.py (Booking.is_urgent, days_until_event, booking_window)
- BusinessConfig: urgent_window_days, chef_assignment_alert_interval_hours

SSoT Dynamic Variables:
- booking.urgent_window_days: Days threshold for urgent classification (default: 7)
"""

import logging
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import Optional, Tuple
from zoneinfo import ZoneInfo

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from services.business_config_service import (
    BusinessConfig,
    get_business_config,
    get_business_config_sync,
)

logger = logging.getLogger(__name__)


class BookingWindow(str, Enum):
    """
    Booking window classification based on days until event.

    DISTANT: 8+ days away - Standard processing, no urgency
    UPCOMING: 4-7 days away - Getting closer, monitor chef assignment
    URGENT: 0-3 days away - CRITICAL, requires immediate chef assignment
    """

    DISTANT = "DISTANT"
    UPCOMING = "UPCOMING"
    URGENT = "URGENT"


# Default thresholds (overridden by SSoT dynamic_variables)
DEFAULT_URGENT_WINDOW_DAYS = 7  # Bookings within 7 days are urgent
DEFAULT_UPCOMING_THRESHOLD_DAYS = 14  # Bookings within 14 days are "upcoming"


def get_venue_now(venue_timezone: str = "America/Los_Angeles") -> datetime:
    """
    Get current datetime in venue timezone.

    CRITICAL: All urgency calculations must be from the venue's perspective.
    A booking at 6 PM in New York is different from 6 PM in Los Angeles.

    Args:
        venue_timezone: IANA timezone string (e.g., "America/Los_Angeles")

    Returns:
        Current datetime in venue timezone

    Example:
        >>> now = get_venue_now("America/New_York")
        >>> print(now.tzinfo)  # America/New_York
    """
    try:
        tz = ZoneInfo(venue_timezone)
        return datetime.now(tz)
    except Exception as e:
        logger.warning(
            f"⚠️ Invalid timezone '{venue_timezone}': {e}, falling back to America/Los_Angeles"
        )
        return datetime.now(ZoneInfo("America/Los_Angeles"))


def calculate_days_until_event(
    event_date: date,
    event_time: Optional[time] = None,
    venue_timezone: str = "America/Los_Angeles",
) -> int:
    """
    Calculate days remaining until event from venue's timezone perspective.

    CRITICAL: This function is the foundation of the urgent booking system.
    It MUST accurately calculate days based on venue local time, not server time.

    Args:
        event_date: The date of the event
        event_time: Optional time of the event (for more precise calculation)
        venue_timezone: IANA timezone string

    Returns:
        Integer days until event (can be negative if event passed)

    Example:
        # Event on Dec 30 in LA timezone
        >>> days = calculate_days_until_event(
        ...     event_date=date(2025, 12, 30),
        ...     venue_timezone="America/Los_Angeles"
        ... )
        >>> print(f"Event in {days} days")
    """
    venue_now = get_venue_now(venue_timezone)
    venue_today = venue_now.date()

    # Simple date difference (whole days)
    delta = event_date - venue_today

    logger.debug(
        f"📅 Days until event: {delta.days} "
        f"(event: {event_date}, venue today: {venue_today}, tz: {venue_timezone})"
    )

    return delta.days


def determine_booking_window(
    days_until_event: int,
    config: Optional[BusinessConfig] = None,
) -> BookingWindow:
    """
    Classify booking into window category based on days until event.

    Uses SSoT thresholds from BusinessConfig when available.

    Args:
        days_until_event: Days remaining until the event
        config: BusinessConfig with SSoT thresholds (optional)

    Returns:
        BookingWindow enum: DISTANT, UPCOMING, or URGENT

    Window Definitions:
        URGENT: 0 to urgent_window_days (default: 7)
        UPCOMING: urgent_window_days+1 to upcoming_threshold (default: 14)
        DISTANT: Beyond upcoming_threshold

    Example:
        >>> window = determine_booking_window(5)  # 5 days away
        >>> print(window)  # BookingWindow.UPCOMING
    """
    # Get thresholds from SSoT or defaults
    if config:
        urgent_threshold = config.urgent_window_days
    else:
        try:
            sync_config = get_business_config_sync()
            urgent_threshold = sync_config.urgent_window_days
        except Exception:
            urgent_threshold = DEFAULT_URGENT_WINDOW_DAYS

    # Upcoming threshold is typically 2x urgent threshold
    upcoming_threshold = urgent_threshold * 2

    if days_until_event <= urgent_threshold:
        return BookingWindow.URGENT
    elif days_until_event <= upcoming_threshold:
        return BookingWindow.UPCOMING
    else:
        return BookingWindow.DISTANT


def is_booking_urgent(
    days_until_event: int,
    config: Optional[BusinessConfig] = None,
) -> bool:
    """
    Check if booking is in the urgent window.

    A booking is urgent when:
    1. Days until event <= urgent_window_days (SSoT threshold, default: 7)
    2. No chef has been assigned yet

    Args:
        days_until_event: Days remaining until the event
        config: BusinessConfig with SSoT thresholds (optional)

    Returns:
        True if booking is urgent, False otherwise

    Note:
        This only checks the time threshold. Chef assignment status
        should be checked separately when determining alert necessity.
    """
    window = determine_booking_window(days_until_event, config)
    return window == BookingWindow.URGENT


def calculate_urgency_details(
    event_date: date,
    event_time: Optional[time] = None,
    venue_timezone: str = "America/Los_Angeles",
    config: Optional[BusinessConfig] = None,
) -> Tuple[int, str, bool]:
    """
    Calculate all urgency-related values for a booking in one call.

    Convenience function that returns all values needed for booking updates.

    Args:
        event_date: The date of the event
        event_time: Optional time of the event
        venue_timezone: IANA timezone string
        config: BusinessConfig with SSoT thresholds (optional)

    Returns:
        Tuple of (days_until_event, booking_window, is_urgent)

    Example:
        >>> days, window, urgent = calculate_urgency_details(
        ...     event_date=date(2025, 1, 5),
        ...     venue_timezone="America/Los_Angeles"
        ... )
        >>> print(f"{days} days, window: {window}, urgent: {urgent}")
    """
    days = calculate_days_until_event(event_date, event_time, venue_timezone)
    window = determine_booking_window(days, config)
    urgent = window == BookingWindow.URGENT

    return days, window.value, urgent


async def update_booking_urgency(
    db: AsyncSession,
    booking_id: str,
    event_date: date,
    event_time: Optional[time] = None,
    venue_timezone: str = "America/Los_Angeles",
    config: Optional[BusinessConfig] = None,
) -> Tuple[int, str, bool]:
    """
    Update a booking's urgency fields in the database.

    Called on:
    1. Booking creation
    2. Event date/time modification
    3. Daily urgency update job

    Args:
        db: Database session
        booking_id: UUID of the booking to update
        event_date: The date of the event
        event_time: Optional time of the event
        venue_timezone: IANA timezone string
        config: BusinessConfig with SSoT thresholds (optional)

    Returns:
        Tuple of (days_until_event, booking_window, is_urgent)

    Example:
        >>> days, window, urgent = await update_booking_urgency(
        ...     db=session,
        ...     booking_id="123e4567-e89b-12d3-a456-426614174000",
        ...     event_date=date(2025, 1, 5),
        ...     venue_timezone="America/Los_Angeles"
        ... )
    """
    # Calculate urgency values
    days, window, urgent = calculate_urgency_details(
        event_date, event_time, venue_timezone, config
    )

    # Update booking in database
    # Note: We use raw SQL to avoid circular imports with Booking model
    await db.execute(update_booking_urgency_sql(booking_id, days, window, urgent))
    await db.commit()

    logger.info(
        f"📊 Updated booking {booking_id} urgency: "
        f"days={days}, window={window}, urgent={urgent}"
    )

    return days, window, urgent


def update_booking_urgency_sql(
    booking_id: str,
    days_until_event: int,
    booking_window: str,
    is_urgent: bool,
):
    """
    Generate SQL for updating booking urgency fields.

    Used by update_booking_urgency() and daily job.
    """
    from sqlalchemy import text

    return text(
        """
        UPDATE core.bookings
        SET
            days_until_event = :days,
            booking_window = :window,
            is_urgent = :urgent,
            updated_at = NOW()
        WHERE id = :booking_id
    """
    ).bindparams(
        booking_id=booking_id,
        days=days_until_event,
        window=booking_window,
        urgent=is_urgent,
    )


async def get_urgent_bookings_without_chef(
    db: AsyncSession,
    config: Optional[BusinessConfig] = None,
) -> list:
    """
    Get all urgent bookings that don't have a chef assigned.

    CRITICAL: This is used by the chef assignment alert system.
    These bookings need immediate attention from station managers.

    Args:
        db: Database session
        config: BusinessConfig with SSoT thresholds (optional)

    Returns:
        List of booking records (id, event_date, days_until_event, customer info, etc.)
    """
    from sqlalchemy import text

    result = await db.execute(
        text(
            """
        SELECT
            b.id,
            b.event_date,
            b.event_time,
            b.days_until_event,
            b.booking_window,
            b.venue_timezone,
            b.venue_address,
            b.station_id,
            b.urgency_alert_count,
            b.urgency_alert_sent_at,
            c.first_name as customer_first_name,
            c.last_name as customer_last_name,
            c.phone as customer_phone,
            c.email as customer_email
        FROM core.bookings b
        LEFT JOIN core.customers c ON b.customer_id = c.id
        WHERE b.is_urgent = true
          AND b.status NOT IN ('cancelled', 'completed', 'deleted')
          AND b.chef_id IS NULL
        ORDER BY b.days_until_event ASC, b.event_time ASC
    """
        )
    )

    bookings = result.fetchall()

    logger.info(f"🚨 Found {len(bookings)} urgent bookings without chef assignment")

    return bookings


async def get_bookings_needing_urgency_update(
    db: AsyncSession,
) -> list:
    """
    Get all active bookings that need their urgency values recalculated.

    Used by the daily urgency update job.

    Returns:
        List of booking records (id, event_date, event_time, venue_timezone)
    """
    from sqlalchemy import text

    result = await db.execute(
        text(
            """
        SELECT
            id,
            event_date,
            event_time,
            venue_timezone
        FROM core.bookings
        WHERE status NOT IN ('cancelled', 'completed', 'deleted')
          AND event_date >= CURRENT_DATE
        ORDER BY event_date ASC
    """
        )
    )

    return result.fetchall()
