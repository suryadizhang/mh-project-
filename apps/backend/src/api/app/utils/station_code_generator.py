"""
Station Code Generator Utility
Auto-generates unique station codes in format: STATION-{STATE}-{CITY}-{###}
Example: STATION-CA-BAY-001, STATION-TX-AUSTIN-002
"""

import re

from api.app.auth.station_models import Station
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


def normalize_location_part(text: str, max_length: int = 10) -> str:
    """
    Normalize city/state text for station code.

    Args:
        text: City or state name
        max_length: Maximum length for the normalized part

    Returns:
        Uppercase normalized string (e.g., "Bay Area" -> "BAY", "Austin" -> "AUSTIN")
    """
    if not text:
        return "UNK"

    # Remove special characters, keep only alphanumeric and spaces
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", text)

    # Convert to uppercase
    cleaned = cleaned.upper().strip()

    # If it's a two-word city (like "Bay Area"), take first letters of each word
    words = cleaned.split()
    if len(words) > 1:
        # Take first significant word or abbreviate
        if len(words[0]) >= 3:
            result = words[0][:max_length]
        else:
            # Concatenate first letters: "Bay Area" -> "BA" or full: "BAYAREA"
            result = "".join(word[:3] for word in words if word)[:max_length]
    else:
        result = cleaned[:max_length]

    return result if result else "UNK"


async def generate_station_code(
    db: AsyncSession, city: str, state: str, country: str = "US"
) -> str:
    """
    Generate unique station code in format: STATION-{STATE}-{CITY}-{###}

    Examples:
        - California Bay Area -> STATION-CA-BAY-001
        - Texas Austin -> STATION-TX-AUSTIN-002
        - New York Manhattan -> STATION-NY-MANHATTAN-001
        - Florida Miami -> STATION-FL-MIAMI-001

    Args:
        db: Database session
        city: City name (e.g., "Bay Area", "Austin", "Manhattan")
        state: State code (e.g., "CA", "TX", "NY") - should be 2-letter US state code
        country: Country code (default: "US")

    Returns:
        Unique station code string
    """
    # Normalize state (should already be 2-letter code like "CA", "TX")
    state_code = state.upper().strip()[:2] if state else "XX"

    # Normalize city name
    city_part = normalize_location_part(city, max_length=10)

    # Build prefix: STATION-{STATE}-{CITY}
    prefix = f"STATION-{state_code}-{city_part}"

    # Find the highest existing number for this location
    result = await db.execute(
        select(func.max(Station.code)).where(Station.code.like(f"{prefix}-%"))
    )
    max_code = result.scalar_one_or_none()

    # Extract the number from the last code, or start at 1
    if max_code:
        # Extract last 3 digits from code like "STATION-CA-BAY-001"
        match = re.search(r"-(\d+)$", max_code)
        next_number = int(match.group(1)) + 1 if match else 1
    else:
        next_number = 1

    # Format with leading zeros (001, 002, ...)
    number_part = f"{next_number:03d}"

    # Final code
    station_code = f"{prefix}-{number_part}"

    # Verify uniqueness (should always be unique, but double-check)
    result = await db.execute(select(func.count(Station.id)).where(Station.code == station_code))
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

    Format: STATION-{STATE}-{CITY}-{###}
    Examples: STATION-CA-BAY-001, STATION-TX-AUSTIN-002

    Args:
        code: Station code to validate

    Returns:
        True if valid format, False otherwise
    """
    # Pattern: STATION-{2 letters}-{1-10 letters}-{3 digits}
    pattern = r"^STATION-[A-Z]{2}-[A-Z]{1,10}-\d{3}$"
    return bool(re.match(pattern, code))


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
            return f"STATION-XX-NEW-{next_number:03d}"

    return "STATION-XX-NEW-001"


# Example usage and test cases
async def _test_code_generator(db: AsyncSession):
    """Test the station code generator."""
    test_cases = [
        ("Bay Area", "CA", "STATION-CA-BAY-001"),
        ("Austin", "TX", "STATION-TX-AUSTIN-001"),
        ("Manhattan", "NY", "STATION-NY-MANHATTAN-001"),
        ("Miami", "FL", "STATION-FL-MIAMI-001"),
        ("San Francisco", "CA", "STATION-CA-SAN-001"),
    ]

    for city, state, _expected_pattern in test_cases:
        code = await generate_station_code(db, city, state)
        await validate_station_code_format(code)


__all__ = [
    "generate_station_code",
    "normalize_location_part",
    "suggest_station_code",
    "validate_station_code_format",
]
