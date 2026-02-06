"""
Suggestion Engine - Alternative Time Suggestions

When requested slot is unavailable, suggests alternative times:
1. Same day, different slot (±1-2 hours)
2. Adjacent days, same time
3. Same day next week
"""

from datetime import date, time, timedelta
from typing import Dict, List, Optional
import logging

from pydantic import BaseModel

from .availability_engine import AvailabilityEngine
from .slot_manager import SlotManager, TimeSlot
from .chef_optimizer import BookingForAssignment, ChefForAssignment

logger = logging.getLogger(__name__)


# ============================================================
# Data Models
# ============================================================


class TimeSuggestion(BaseModel):
    """A suggested alternative time for booking."""

    suggested_date: date
    suggested_slot: int
    suggested_time: time
    slot_name: str
    suggestion_type: str  # 'same_day', 'adjacent_day', 'next_week'
    priority: int  # 1 = highest priority
    reason: str
    available_chefs: int = 0
    is_adjustment: bool = False  # True if slot needs time adjustment
    adjustment_minutes: int = 0


class SuggestionResult(BaseModel):
    """Result of suggestion search."""

    original_date: date
    original_time: time
    suggestions: List[TimeSuggestion]
    has_alternatives: bool
    message: str


# ============================================================
# Suggestion Engine
# ============================================================


class CheckAndSuggestResult(BaseModel):
    """Result from check_and_suggest method matching router expectations."""

    requested_date: date
    requested_time: time
    is_requested_available: bool
    conflict_reason: Optional[str] = None
    suggestions: List["SlotSuggestion"] = []
    message: str = ""


class SlotSuggestion(BaseModel):
    """A single slot suggestion matching router expectations."""

    slot_time: time
    slot_date: date
    slot_label: str = ""
    is_available: bool = True
    conflict_reason: Optional[str] = None
    adjusted_time: Optional[time] = None
    travel_time_from_prev: Optional[int] = None
    travel_time_to_next: Optional[int] = None
    score: float = 0.0


class SuggestionEngine:
    """
    Suggests alternative times when requested slot is unavailable.

    Priority order:
    1. Same day, different slot (minimal disruption)
    2. Adjacent days (Saturday/Sunday swap, or Friday/Monday)
    3. Same day next week
    """

    def __init__(
        self,
        db: Optional[object] = None,
        availability_engine: Optional[AvailabilityEngine] = None,
        slot_manager: Optional[SlotManager] = None,
    ):
        """
        Initialize suggestion engine.

        Args:
            db: Database session (passed from router)
            availability_engine: For checking availability
            slot_manager: For slot management
        """
        self.db = db
        # Create availability engine with db session if provided
        self.availability_engine = availability_engine or AvailabilityEngine(db=db)
        self.slot_manager = slot_manager or SlotManager()

    async def check_and_suggest(
        self,
        requested_date: date,
        requested_time: time,
        guest_count: int = 10,
        venue_lat: Optional[float] = None,
        venue_lng: Optional[float] = None,
        preferred_chef_id: Optional[object] = None,
    ) -> CheckAndSuggestResult:
        """
        Check if requested time is available and suggest alternatives if not.

        This is the main entry point called by the API router.

        Args:
            requested_date: The requested event date
            requested_time: The requested event time
            guest_count: Number of guests
            venue_lat: Venue latitude (optional)
            venue_lng: Venue longitude (optional)
            preferred_chef_id: Preferred chef UUID (optional)

        Returns:
            CheckAndSuggestResult with availability info and suggestions
        """
        # Check if requested slot is available
        result = await self.availability_engine.check_specific_slot(
            event_date=requested_date,
            event_time=requested_time,
            guest_count=guest_count,
            venue_lat=float(venue_lat) if venue_lat else None,
            venue_lng=float(venue_lng) if venue_lng else None,
        )

        if result.is_requested_available:
            return CheckAndSuggestResult(
                requested_date=requested_date,
                requested_time=requested_time,
                is_requested_available=True,
                message="Your requested time is available!",
                suggestions=[],
            )

        # Slot not available - get suggestions
        all_slots = await self.availability_engine.get_available_slots_for_date(
            requested_date, guest_count
        )

        suggestions: List[SlotSuggestion] = []

        # Add same-day alternatives
        for slot in all_slots:
            if slot.is_available and slot.slot_time != requested_time:
                suggestions.append(
                    SlotSuggestion(
                        slot_time=slot.slot_time,
                        slot_date=requested_date,
                        slot_label=slot.slot_name,
                        is_available=True,
                        score=1.0,
                    )
                )

        # Add next-day alternatives if needed
        if len(suggestions) < 3:
            next_day = requested_date + timedelta(days=1)
            next_day_slots = await self.availability_engine.get_available_slots_for_date(
                next_day, guest_count
            )
            for slot in next_day_slots:
                if slot.is_available:
                    suggestions.append(
                        SlotSuggestion(
                            slot_time=slot.slot_time,
                            slot_date=next_day,
                            slot_label=slot.slot_name,
                            is_available=True,
                            score=0.8,
                        )
                    )
                    if len(suggestions) >= 5:
                        break

        message = result.conflict_reason or "The requested time is not available."
        if suggestions:
            message += f" Here are {len(suggestions)} alternative options:"

        return CheckAndSuggestResult(
            requested_date=requested_date,
            requested_time=requested_time,
            is_requested_available=False,
            conflict_reason=result.conflict_reason,
            suggestions=suggestions,
            message=message,
        )

    async def get_suggestions(
        self,
        requested_date: date,
        requested_time: time,
        venue_lat: float,
        venue_lng: float,
        guest_count: int,
        existing_bookings: Optional[List[BookingForAssignment]] = None,
        available_chefs: Optional[List[ChefForAssignment]] = None,
        max_suggestions: int = 5,
    ) -> SuggestionResult:
        """
        Get alternative time suggestions.

        Args:
            requested_date: Original requested date
            requested_time: Original requested time
            venue_lat: Venue latitude
            venue_lng: Venue longitude
            guest_count: Number of guests
            existing_bookings: Current bookings
            available_chefs: Available chefs
            max_suggestions: Maximum number of suggestions to return

        Returns:
            SuggestionResult with alternatives
        """
        suggestions: List[TimeSuggestion] = []
        existing_bookings = existing_bookings or []
        available_chefs = available_chefs or []

        # Determine which slot was requested
        requested_slot = self.slot_manager.get_slot_for_time(requested_time)

        # 1. Check other slots on the same day
        same_day_suggestions = await self._get_same_day_alternatives(
            target_date=requested_date,
            requested_slot=requested_slot or TimeSlot.EARLY_EVENING,
            venue_lat=venue_lat,
            venue_lng=venue_lng,
            guest_count=guest_count,
            existing_bookings=[b for b in existing_bookings if b.event_date == requested_date],
            available_chefs=available_chefs,
        )
        suggestions.extend(same_day_suggestions)

        # 2. Check adjacent days
        adjacent_suggestions = await self._get_adjacent_day_alternatives(
            target_date=requested_date,
            requested_slot=requested_slot or TimeSlot.EARLY_EVENING,
            venue_lat=venue_lat,
            venue_lng=venue_lng,
            guest_count=guest_count,
            all_bookings=existing_bookings,
            available_chefs=available_chefs,
        )
        suggestions.extend(adjacent_suggestions)

        # 3. Check same day next week
        if len(suggestions) < max_suggestions:
            next_week = requested_date + timedelta(days=7)
            next_week_suggestions = await self._get_same_day_alternatives(
                target_date=next_week,
                requested_slot=requested_slot or TimeSlot.EARLY_EVENING,
                venue_lat=venue_lat,
                venue_lng=venue_lng,
                guest_count=guest_count,
                existing_bookings=[b for b in existing_bookings if b.event_date == next_week],
                available_chefs=available_chefs,
                suggestion_type="next_week",
                priority_offset=20,
            )
            suggestions.extend(next_week_suggestions)

        # Sort by priority and limit
        suggestions.sort(key=lambda s: s.priority)
        suggestions = suggestions[:max_suggestions]

        # Build result message
        if suggestions:
            message = (
                f"Your requested time is not available. Here are {len(suggestions)} alternatives:"
            )
        else:
            message = "Unfortunately, no alternative times are available for your party."

        return SuggestionResult(
            original_date=requested_date,
            original_time=requested_time,
            suggestions=suggestions,
            has_alternatives=len(suggestions) > 0,
            message=message,
        )

    async def _get_same_day_alternatives(
        self,
        target_date: date,
        requested_slot: int,
        venue_lat: float,
        venue_lng: float,
        guest_count: int,
        existing_bookings: List[BookingForAssignment],
        available_chefs: List[ChefForAssignment],
        suggestion_type: str = "same_day",
        priority_offset: int = 0,
    ) -> List[TimeSuggestion]:
        """Get alternative slots on the same day."""
        suggestions = []

        availability = await self.availability_engine.get_available_slots(
            target_date=target_date,
            venue_lat=venue_lat,
            venue_lng=venue_lng,
            guest_count=guest_count,
            existing_bookings=existing_bookings,
            available_chefs=available_chefs,
        )

        # Add available slots (excluding originally requested)
        priority = 1 + priority_offset
        for slot in availability.available_slots:
            if slot.slot_number != requested_slot:
                suggestions.append(
                    TimeSuggestion(
                        suggested_date=target_date,
                        suggested_slot=slot.slot_number,
                        suggested_time=slot.standard_time,
                        slot_name=slot.slot_name,
                        suggestion_type=suggestion_type,
                        priority=priority,
                        reason=f"Available on {target_date.strftime('%A')} at {slot.slot_name}",
                        available_chefs=slot.available_chefs,
                    )
                )
                priority += 1

        # Add partially available slots
        for slot in availability.partially_available_slots:
            if slot.slot_number != requested_slot:
                suggestions.append(
                    TimeSuggestion(
                        suggested_date=target_date,
                        suggested_slot=slot.slot_number,
                        suggested_time=slot.suggested_time or slot.standard_time,
                        slot_name=slot.slot_name,
                        suggestion_type=suggestion_type,
                        priority=priority + 5,  # Lower priority than standard times
                        reason=f"Available with adjusted time ({slot.notes})",
                        available_chefs=slot.available_chefs,
                        is_adjustment=True,
                        adjustment_minutes=slot.adjustment_minutes,
                    )
                )
                priority += 1

        return suggestions

    async def _get_adjacent_day_alternatives(
        self,
        target_date: date,
        requested_slot: int,
        venue_lat: float,
        venue_lng: float,
        guest_count: int,
        all_bookings: List[BookingForAssignment],
        available_chefs: List[ChefForAssignment],
    ) -> List[TimeSuggestion]:
        """Get alternatives on adjacent days (day before/after)."""
        suggestions = []

        # Check day before and day after
        adjacent_dates = [target_date - timedelta(days=1), target_date + timedelta(days=1)]

        # Filter to weekends if original was weekend
        if target_date.weekday() >= 5:  # Saturday (5) or Sunday (6)
            adjacent_dates = [d for d in adjacent_dates if d.weekday() >= 5]

        priority = 10  # Lower priority than same-day
        for adj_date in adjacent_dates:
            date_bookings = [b for b in all_bookings if b.event_date == adj_date]

            availability = await self.availability_engine.get_available_slots(
                target_date=adj_date,
                venue_lat=venue_lat,
                venue_lng=venue_lng,
                guest_count=guest_count,
                existing_bookings=date_bookings,
                available_chefs=available_chefs,
            )

            # Prefer same slot on adjacent day
            for slot in availability.available_slots:
                if slot.slot_number == requested_slot:
                    # Same slot, different day - high priority
                    suggestions.append(
                        TimeSuggestion(
                            suggested_date=adj_date,
                            suggested_slot=slot.slot_number,
                            suggested_time=slot.standard_time,
                            slot_name=slot.slot_name,
                            suggestion_type="adjacent_day",
                            priority=priority,
                            reason=f"Same time on {adj_date.strftime('%A, %B %d')}",
                            available_chefs=slot.available_chefs,
                        )
                    )
                else:
                    suggestions.append(
                        TimeSuggestion(
                            suggested_date=adj_date,
                            suggested_slot=slot.slot_number,
                            suggested_time=slot.standard_time,
                            slot_name=slot.slot_name,
                            suggestion_type="adjacent_day",
                            priority=priority + 2,
                            reason=f"Available on {adj_date.strftime('%A')} at {slot.slot_name}",
                            available_chefs=slot.available_chefs,
                        )
                    )
                priority += 1

        return suggestions

    def format_suggestion_message(self, suggestion: TimeSuggestion) -> str:
        """Format a suggestion for customer display."""
        date_str = suggestion.suggested_date.strftime("%A, %B %d")
        time_str = suggestion.suggested_time.strftime("%-I:%M %p")

        if suggestion.suggestion_type == "same_day":
            return f"{suggestion.slot_name} ({time_str}) on the same day"
        elif suggestion.suggestion_type == "adjacent_day":
            return f"{date_str} at {time_str} ({suggestion.slot_name})"
        elif suggestion.suggestion_type == "next_week":
            return f"{date_str} (same day next week) at {time_str}"
        else:
            return f"{date_str} at {time_str}"

    async def get_availability_calendar(
        self,
        start_date: date,
        end_date: date,
        guest_count: int = 10,
        venue_lat: Optional[float] = None,
        venue_lng: Optional[float] = None,
        preferred_chef_id: Optional[object] = None,
    ) -> Dict[date, List[SlotSuggestion]]:
        """
        Get availability calendar for a date range.

        Returns a dictionary mapping dates to available slots.

        Args:
            start_date: Start of date range
            end_date: End of date range
            guest_count: Number of guests
            venue_lat: Venue latitude (optional)
            venue_lng: Venue longitude (optional)
            preferred_chef_id: Preferred chef UUID (optional)

        Returns:
            Dictionary mapping dates to lists of SlotSuggestion
        """
        calendar: Dict[date, List[SlotSuggestion]] = {}
        current_date = start_date

        while current_date <= end_date:
            # Get available slots for this date
            all_slots = await self.availability_engine.get_available_slots_for_date(
                current_date, guest_count
            )

            date_slots = []
            for slot in all_slots:
                date_slots.append(
                    SlotSuggestion(
                        slot_time=slot.slot_time,
                        slot_date=current_date,
                        slot_label=slot.slot_name,
                        is_available=slot.is_available,
                        conflict_reason=getattr(slot, "conflict_reason", None),
                        score=1.0 if slot.is_available else 0.0,
                    )
                )

            calendar[current_date] = date_slots
            current_date = current_date + timedelta(days=1)

        return calendar
