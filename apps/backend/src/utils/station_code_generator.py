"""
Station Code Generator Utility
Auto-generates unique station codes in simplified human-readable format

FORMAT: {STATE}-{CITY}-{###}
Examples:
  - CA-FREMONT-001 (Fremont, California - Station 1)
  - TX-AUSTIN-001 (Austin, Texas - Station 1)
  - NY-MANHATTAN-001 (Manhattan, New York - Station 1)

The format is designed to be:
  - Human readable (easy to understand at a glance)
  - Sortable (alphabetically by state, then city)
  - Unique (3-digit number suffix ensures uniqueness within city)
"""

import re

# Phase 1.1: Use canonical db.models.identity instead of deprecated station_models
from db.models.identity import Station
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


def normalize_location_part(text: str, max_length: int = 12) -> str:
    """
    Normalize city/state text for station code.

    Args:
        text: City or state name
        max_length: Maximum length for the normalized part

    Returns:
        Uppercase normalized string (e.g., "Bay Area" -> "BAYAREA", "Fremont" -> "FREMONT")
    """
    if not text:
        return "UNK"

    # Remove special characters, keep only alphanumeric
    cleaned = re.sub(r"[^a-zA-Z0-9]", "", text)

    # Convert to uppercase
    cleaned = cleaned.upper().strip()

    return cleaned[:max_length] if cleaned else "UNK"


async def generate_station_code(
    db: AsyncSession, city: str, state: str, country: str = "US"
) -> str:
    """
    Generate unique station code in simplified format: {STATE}-{CITY}-{###}

    Examples:
        - Fremont, California -> CA-FREMONT-001
        - Austin, Texas -> TX-AUSTIN-001
        - Manhattan, New York -> NY-MANHATTAN-001
        - Miami, Florida -> FL-MIAMI-001

    Args:
        db: Database session
        city: City name (e.g., "Fremont", "Austin", "Manhattan")
        state: State code (e.g., "CA", "TX", "NY") - should be 2-letter US state code
        country: Country code (default: "US")

    Returns:
        Unique station code string (e.g., "CA-FREMONT-001")
    """
    # Normalize state (should already be 2-letter code like "CA", "TX")
    state_code = state.upper().strip()[:2] if state else "XX"

    # Normalize city name (remove spaces and special chars)
    city_part = normalize_location_part(city, max_length=12)

    # Build prefix: {STATE}-{CITY}
    prefix = f"{state_code}-{city_part}"

    # Find the highest existing number for this location
    result = await db.execute(
        select(func.max(Station.code)).where(Station.code.like(f"{prefix}-%"))
    )
    max_code = result.scalar_one_or_none()

    # Extract the number from the last code, or start at 1
    if max_code:
        # Extract last 3 digits from code like "CA-FREMONT-001"
        match = re.search(r"-(\d+)$", max_code)
        next_number = int(match.group(1)) + 1 if match else 1
    else:
        next_number = 1

    # Format with leading zeros (001, 002, ...)
    number_part = f"{next_number:03d}"

    # Final code
    station_code = f"{prefix}-{number_part}"

    # Verify uniqueness (should always be unique, but double-check)
    result = await db.execute(
        select(func.count(Station.id)).where(Station.code == station_code)
    )
    exists = result.scalar_one() > 0

    if exists:
        # Extremely rare collision, increment number
        next_number += 1
        number_part = f"{next_number:03d}"
        station_code = f"{prefix}-{number_part}"

    return station_code


async def validate_station_code_format(code: str) -> bool:
    """
    Validate that a station code follows the required format.

    Format: {STATE}-{CITY}-{###}
    Examples: CA-FREMONT-001, TX-AUSTIN-002, NY-MANHATTAN-001

    Args:
        code: Station code to validate

    Returns:
        True if valid format, False otherwise
    """
    # Pattern: {2 letters}-{1-12 letters}-{3 digits}
    pattern = r"^[A-Z]{2}-[A-Z]{1,12}-\d{3}$"
    return bool(re.match(pattern, code))


def parse_station_code(code: str) -> dict | None:
    """
    Parse a station code into its components.

    Args:
        code: Station code (e.g., "CA-FREMONT-001")

    Returns:
        Dict with state, city, number or None if invalid
    """
    pattern = r"^([A-Z]{2})-([A-Z]{1,12})-(\d{3})$"
    match = re.match(pattern, code)

    if match:
        return {
            "state": match.group(1),
            "city": match.group(2),
            "number": int(match.group(3)),
            "display": f"{match.group(2).title()}, {match.group(1)} (#{match.group(3)})",
        }
    return None


async def suggest_station_code(
    db: AsyncSession, city: str | None = None, state: str | None = None
) -> str:
    """
    Suggest next available station code based on location.

    Args:
        db: Database session
        city: Optional city name hint
        state: Optional state code hint

    Returns:
        Suggested station code
    """
    if city and state:
        return await generate_station_code(db, city, state)

    # No location provided, find global next number
    result = await db.execute(select(func.max(Station.code)))
    max_code = result.scalar_one_or_none()

    if max_code:
        # Extract highest number across all stations
        match = re.search(r"-(\d+)$", max_code)
        if match:
            next_number = int(match.group(1)) + 1
            return f"XX-NEW-{next_number:03d}"

    return "XX-NEW-001"


# Pre-defined station codes for common locations
KNOWN_STATIONS = {
    "CA-FREMONT-001": {
        "name": "Fremont Station",
        "display_name": "Fremont, CA (Main)",
        "city": "Fremont",
        "state": "CA",
        "timezone": "America/Los_Angeles",
        "address": "47481 Towhee St, Fremont, CA 94539",
    },
}


# Example usage and test cases
async def _test_code_generator(db: AsyncSession):
    """Test the station code generator."""
    test_cases = [
        ("Fremont", "CA", "CA-FREMONT-001"),
        ("Austin", "TX", "TX-AUSTIN-001"),
        ("Manhattan", "NY", "NY-MANHATTAN-001"),
        ("Miami", "FL", "FL-MIAMI-001"),
        ("San Francisco", "CA", "CA-SANFRANCISCO-001"),
    ]

    for city, state, expected_prefix in test_cases:
        code = await generate_station_code(db, city, state)
        is_valid = await validate_station_code_format(code)
        print(f"Generated: {code} (valid: {is_valid})")


__all__ = [
    "generate_station_code",
    "normalize_location_part",
    "parse_station_code",
    "suggest_station_code",
    "validate_station_code_format",
    "KNOWN_STATIONS",
]
