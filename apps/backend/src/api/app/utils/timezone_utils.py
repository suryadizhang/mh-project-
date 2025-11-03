"""
Timezone utilities for handling station-specific timezones.

MyHibachi operates across multiple timezones based on station locations.
This module provides utilities for timezone-aware datetime handling.
"""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

# Default timezone if station timezone is not specified
DEFAULT_TIMEZONE = "America/New_York"

# Common US timezones for hibachi chef services
COMMON_TIMEZONES = {
    "EST": "America/New_York",
    "CST": "America/Chicago",
    "MST": "America/Denver",
    "PST": "America/Los_Angeles",
    "HST": "Pacific/Honolulu",
    "AKST": "America/Anchorage",
}


def get_station_timezone(station_timezone: str | None = None) -> ZoneInfo:
    """
    Get timezone object for a station.

    Args:
        station_timezone: IANA timezone string (e.g., "America/New_York")
                         If None, returns default timezone

    Returns:
        ZoneInfo object for the timezone

    Examples:
        >>> tz = get_station_timezone("America/Los_Angeles")
        >>> tz = get_station_timezone()  # Returns default timezone
    """
    if not station_timezone:
        station_timezone = DEFAULT_TIMEZONE

    try:
        return ZoneInfo(station_timezone)
    except Exception:
        # Fallback to default if invalid timezone
        return ZoneInfo(DEFAULT_TIMEZONE)


def now_in_timezone(station_timezone: str | None = None) -> datetime:
    """
    Get current datetime in station's timezone.

    Args:
        station_timezone: IANA timezone string (e.g., "America/Chicago")
                         If None, uses default timezone

    Returns:
        Timezone-aware datetime in station's timezone

    Examples:
        >>> current_time = now_in_timezone("America/Chicago")
        >>> current_time = now_in_timezone()  # Default timezone
    """
    tz = get_station_timezone(station_timezone)
    return datetime.now(tz)


def utc_now() -> datetime:
    """
    Get current UTC time (for database storage and JWT tokens).

    Returns:
        Timezone-aware datetime in UTC

    Note:
        Use this for:
        - Database timestamp fields
        - JWT token timestamps (iat, exp)
        - API response timestamps that need to be timezone-agnostic
    """
    return datetime.now(UTC)


def to_station_timezone(dt: datetime, station_timezone: str | None = None) -> datetime:
    """
    Convert a datetime to station's timezone.

    Args:
        dt: Datetime to convert (can be naive or timezone-aware)
        station_timezone: Target timezone (IANA string)

    Returns:
        Datetime converted to station's timezone

    Examples:
        >>> utc_time = datetime.now(timezone.utc)
        >>> local_time = to_station_timezone(utc_time, "America/New_York")
    """
    tz = get_station_timezone(station_timezone)

    # If naive datetime, assume it's UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)

    return dt.astimezone(tz)


def to_utc(dt: datetime) -> datetime:
    """
    Convert a datetime to UTC.

    Args:
        dt: Datetime to convert (can be naive or timezone-aware)

    Returns:
        Datetime converted to UTC

    Examples:
        >>> local_time = now_in_timezone("America/Chicago")
        >>> utc_time = to_utc(local_time)
    """
    # If naive datetime, assume it's in default timezone
    if dt.tzinfo is None:
        tz = get_station_timezone()
        dt = dt.replace(tzinfo=tz)

    return dt.astimezone(UTC)


def format_for_display(dt: datetime, station_timezone: str | None = None) -> str:
    """
    Format datetime for user display in station's timezone.

    Args:
        dt: Datetime to format
        station_timezone: Station's timezone for display

    Returns:
        Formatted string like "Oct 23, 2025 3:30 PM EST"

    Examples:
        >>> utc_time = utc_now()
        >>> display = format_for_display(utc_time, "America/New_York")
        "Oct 23, 2025 7:30 PM EDT"
    """
    local_dt = to_station_timezone(dt, station_timezone)
    return local_dt.strftime("%b %d, %Y %I:%M %p %Z")


def get_date_range_for_station(
    days: int, station_timezone: str | None = None
) -> tuple[datetime, datetime]:
    """
    Get date range in station's timezone for analytics queries.

    Args:
        days: Number of days to go back
        station_timezone: Station's timezone

    Returns:
        Tuple of (start_datetime, end_datetime) in UTC for database queries

    Examples:
        >>> start, end = get_date_range_for_station(30, "America/Chicago")
        # Returns UTC timestamps for last 30 days in Chicago timezone
    """
    # Get end time as current moment in station's timezone (end of "today")
    tz = get_station_timezone(station_timezone)
    end_local = datetime.now(tz)

    # Go back N days
    from datetime import timedelta

    start_local = end_local - timedelta(days=days)

    # Convert to UTC for database queries
    return to_utc(start_local), to_utc(end_local)
