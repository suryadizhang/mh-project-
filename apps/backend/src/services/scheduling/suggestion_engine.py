"""
Suggestion Engine

Provides smart alternative time slot suggestions when requested time is unavailable.
Takes into account travel time, chef availability, and booking density.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from db.models.core import Booking
except ImportError:
    from models.booking import Booking
from .slot_manager import SlotManagerService
from .travel_time_service import TravelTimeService


# Compatibility helper for different Booking model schemas
# Production uses: date, slot
# Legacy uses: event_date, event_time
def get_booking_date_column():
    """Get the date column from Booking model (handles different schemas)."""
    if hasattr(Booking, "date"):
        return Booking.date
    return Booking.event_date


def get_booking_time_column():
    """Get the time/slot column from Booking model (handles different schemas)."""
    if hasattr(Booking, "slot"):
        return Booking.slot
    return Booking.event_time


def get_booking_date(booking) -> date:
    """Get the date from a booking instance (handles different schemas)."""
    if hasattr(booking, "date"):
        return booking.date
    return booking.event_date


def get_booking_time(booking) -> time:
    """Get the time/slot from a booking instance (handles different schemas)."""
    if hasattr(booking, "slot"):
        return booking.slot
    return booking.event_time


# Standard time slots
STANDARD_SLOTS = [
    time(12, 0),  # 12:00 PM
    time(15, 0),  # 3:00 PM
    time(18, 0),  # 6:00 PM
    time(21, 0),  # 9:00 PM
]

# How many days forward to search for alternatives
SUGGESTION_WINDOW_DAYS = 14

# Maximum number of suggestions to return
MAX_SUGGESTIONS = 5


@dataclass
class SlotAvailability:
    """Availability status for a specific time slot"""

    slot_time: time
    slot_date: date
    is_available: bool
    conflict_reason: Optional[str] = None
    adjusted_time: Optional[time] = None  # If slot can be adjusted
    travel_time_from_prev: Optional[int] = None  # Minutes
    travel_time_to_next: Optional[int] = None  # Minutes
    score: float = 0.0  # Higher = better fit


@dataclass
class SuggestionResult:
    """Result containing alternative time suggestions"""

    requested_date: date
    requested_time: time
    is_requested_available: bool
    conflict_reason: Optional[str] = None
    suggestions: list[SlotAvailability] = field(default_factory=list)
    message: str = ""


class SuggestionEngine:
    """
    Generates smart alternative time slot suggestions.

    Features:
    - Checks availability considering existing bookings
    - Accounts for travel time between venues
    - Respects chef assignments
    - Scores alternatives by convenience
    - Looks forward in time for options
    """

    def __init__(
        self,
        session: AsyncSession,
        slot_manager: Optional[SlotManagerService] = None,
        travel_service: Optional[TravelTimeService] = None,
    ):
        self.session = session
        self.slot_manager = slot_manager or SlotManagerService()
        self.travel_service = travel_service or TravelTimeService(session)

    async def check_and_suggest(
        self,
        requested_date: date,
        requested_time: time,
        guest_count: int,
        venue_lat: Optional[Decimal] = None,
        venue_lng: Optional[Decimal] = None,
        preferred_chef_id: Optional[UUID] = None,
    ) -> SuggestionResult:
        """
        Check if requested slot is available and provide alternatives if not.

        Args:
            requested_date: Desired event date
            requested_time: Desired time slot
            guest_count: Number of guests (affects duration)
            venue_lat: Venue latitude
            venue_lng: Venue longitude
            preferred_chef_id: Customer's preferred chef (if any)

        Returns:
            SuggestionResult with availability and alternatives
        """
        # Calculate event duration
        duration = self.slot_manager.calculate_event_duration(guest_count)

        # Check if the exact requested slot is available
        is_available, conflict_reason = await self._check_slot_availability(
            requested_date,
            requested_time,
            duration,
            venue_lat,
            venue_lng,
            preferred_chef_id,
        )

        if is_available:
            return SuggestionResult(
                requested_date=requested_date,
                requested_time=requested_time,
                is_requested_available=True,
                message="Your requested time is available!",
                suggestions=[],
            )

        # Find alternatives
        suggestions = await self._find_alternatives(
            requested_date,
            requested_time,
            duration,
            venue_lat,
            venue_lng,
            preferred_chef_id,
        )

        # Build result message
        if suggestions:
            message = f"The {requested_time.strftime('%I:%M %p')} slot on {requested_date.strftime('%B %d')} is not available. Here are some alternatives:"
        else:
            message = "Unfortunately, we're fully booked around your requested time. Please try a different date or call us directly."

        return SuggestionResult(
            requested_date=requested_date,
            requested_time=requested_time,
            is_requested_available=False,
            conflict_reason=conflict_reason,
            suggestions=suggestions,
            message=message,
        )

    async def _check_slot_availability(
        self,
        check_date: date,
        check_time: time,
        duration_minutes: int,
        venue_lat: Optional[Decimal],
        venue_lng: Optional[Decimal],
        preferred_chef_id: Optional[UUID],
    ) -> tuple[bool, Optional[str]]:
        """
        Check if a specific slot is available.

        Returns:
            Tuple of (is_available, conflict_reason)
        """
        # Convert to datetime for time window calculation
        start_dt = datetime.combine(check_date, check_time)
        end_dt = start_dt + timedelta(minutes=duration_minutes)

        # Buffer time needed
        buffer_minutes = 15
        window_start = start_dt - timedelta(minutes=buffer_minutes)
        window_end = end_dt + timedelta(minutes=buffer_minutes)

        # Query for conflicting bookings - use compatibility helpers
        date_col = get_booking_date_column()
        query = select(Booking).where(
            and_(
                date_col == check_date,
                Booking.status.in_(["confirmed", "pending"]),
            )
        )

        # Add chef filter if preferred chef specified
        if preferred_chef_id:
            # Check for bookings with this chef or unassigned
            query = query.where(
                or_(
                    Booking.preferred_chef_id == preferred_chef_id,
                    Booking.preferred_chef_id.is_(None),
                )
            )

        result = await self.session.execute(query)
        existing_bookings = result.scalars().all()

        for booking in existing_bookings:
            # Use compatibility helpers for date/time access
            booking_date = get_booking_date(booking)
            booking_time = get_booking_time(booking)

            # Get start time - use effective_start_time if available, else slot/event_time
            if hasattr(booking, "effective_start_time") and booking.effective_start_time:
                start_time = booking.effective_start_time
            else:
                start_time = booking_time

            booking_start = datetime.combine(booking_date, start_time)

            # Calculate duration - use calculated_duration if available, else estimate
            if hasattr(booking, "calculated_duration") and booking.calculated_duration:
                duration = booking.calculated_duration
            elif hasattr(booking, "party_adults") and hasattr(booking, "party_kids"):
                # Estimate from guest count
                guest_count = (booking.party_adults or 0) + (booking.party_kids or 0)
                duration = min(60 + (guest_count * 3), 120)
            else:
                duration = 90  # Default duration

            booking_end = booking_start + timedelta(minutes=duration)

            # Check for time overlap
            if not (end_dt <= booking_start or start_dt >= booking_end):
                # Check if we can adjust this slot
                can_adjust = await self._can_adjust_slot(check_date, check_time, booking)
                if can_adjust:
                    return True, None
                return (
                    False,
                    f"Conflicts with existing booking at {booking_time.strftime('%I:%M %p')}",
                )

            # Check travel time feasibility
            has_location = hasattr(booking, "venue_lat") and booking.venue_lat is not None
            if venue_lat and venue_lng and has_location:
                travel_time = await self.travel_service.get_travel_time(
                    float(booking.venue_lat),
                    float(booking.venue_lng),
                    float(venue_lat),
                    float(venue_lng),
                    booking_end,
                )

                if travel_time:
                    # Time gap between events
                    gap = abs((start_dt - booking_end).total_seconds() / 60)
                    if gap < travel_time + buffer_minutes:
                        return False, "Insufficient travel time from nearby booking"

        return True, None

    async def _can_adjust_slot(
        self,
        check_date: date,
        check_time: time,
        conflicting_booking: Booking,
    ) -> bool:
        """
        Check if the slot can be adjusted to avoid conflict.
        Uses slot adjustment limits from SlotManagerService.
        """
        slot_config = self.slot_manager.get_slot_config(check_time)
        if not slot_config:
            return False

        # Check if there's room in the adjustment window
        max_adjustment = max(
            abs(slot_config.adjust_earlier_minutes), abs(slot_config.adjust_later_minutes)
        )

        return max_adjustment > 30  # At least 30 min flexibility

    async def _find_alternatives(
        self,
        original_date: date,
        original_time: time,
        duration_minutes: int,
        venue_lat: Optional[Decimal],
        venue_lng: Optional[Decimal],
        preferred_chef_id: Optional[UUID],
    ) -> list[SlotAvailability]:
        """
        Find alternative time slots when requested time is unavailable.

        Strategy:
        1. Check other slots on same day (closest times first)
        2. Check same slot on nearby days
        3. Score and rank all options
        """
        alternatives = []

        # 1. Same day, different times
        for slot in STANDARD_SLOTS:
            if slot == original_time:
                continue

            is_available, reason = await self._check_slot_availability(
                original_date,
                slot,
                duration_minutes,
                venue_lat,
                venue_lng,
                preferred_chef_id,
            )

            if is_available:
                # Score by proximity to requested time
                time_diff = abs(
                    (
                        datetime.combine(original_date, slot)
                        - datetime.combine(original_date, original_time)
                    ).seconds
                    / 3600
                )
                score = 10 - time_diff  # Higher score for closer times

                alternatives.append(
                    SlotAvailability(
                        slot_time=slot,
                        slot_date=original_date,
                        is_available=True,
                        score=score + 5,  # Bonus for same day
                    )
                )

        # 2. Same time, different days (up to 7 days)
        for day_offset in range(1, 8):
            alt_date = original_date + timedelta(days=day_offset)

            is_available, reason = await self._check_slot_availability(
                alt_date,
                original_time,
                duration_minutes,
                venue_lat,
                venue_lng,
                preferred_chef_id,
            )

            if is_available:
                # Score decreases with distance from requested date
                score = 8 - (day_offset * 0.5)

                alternatives.append(
                    SlotAvailability(
                        slot_time=original_time,
                        slot_date=alt_date,
                        is_available=True,
                        score=score,
                    )
                )

        # 3. Check nearby days with nearby times (lower priority)
        for day_offset in range(1, 4):
            alt_date = original_date + timedelta(days=day_offset)
            for slot in STANDARD_SLOTS:
                if slot == original_time:
                    continue

                # Skip if we already have enough alternatives
                if len(alternatives) >= MAX_SUGGESTIONS * 2:
                    break

                is_available, reason = await self._check_slot_availability(
                    alt_date,
                    slot,
                    duration_minutes,
                    venue_lat,
                    venue_lng,
                    preferred_chef_id,
                )

                if is_available:
                    time_diff = abs(
                        (
                            datetime.combine(original_date, slot)
                            - datetime.combine(original_date, original_time)
                        ).seconds
                        / 3600
                    )
                    score = 5 - day_offset - (time_diff * 0.3)

                    alternatives.append(
                        SlotAvailability(
                            slot_time=slot,
                            slot_date=alt_date,
                            is_available=True,
                            score=score,
                        )
                    )

        # Sort by score (highest first) and return top N
        alternatives.sort(key=lambda x: x.score, reverse=True)
        return alternatives[:MAX_SUGGESTIONS]

    async def get_availability_calendar(
        self,
        start_date: date,
        end_date: date,
        guest_count: int,
        venue_lat: Optional[Decimal] = None,
        venue_lng: Optional[Decimal] = None,
        preferred_chef_id: Optional[UUID] = None,
    ) -> dict[date, list[SlotAvailability]]:
        """
        Get availability for all slots across a date range.

        Useful for displaying a calendar view of available slots.

        Returns:
            Dict mapping dates to list of SlotAvailability
        """
        duration = self.slot_manager.calculate_event_duration(guest_count)
        calendar = {}

        current_date = start_date
        while current_date <= end_date:
            day_slots = []

            for slot in STANDARD_SLOTS:
                is_available, reason = await self._check_slot_availability(
                    current_date,
                    slot,
                    duration,
                    venue_lat,
                    venue_lng,
                    preferred_chef_id,
                )

                day_slots.append(
                    SlotAvailability(
                        slot_time=slot,
                        slot_date=current_date,
                        is_available=is_available,
                        conflict_reason=reason,
                    )
                )

            calendar[current_date] = day_slots
            current_date += timedelta(days=1)

        return calendar
