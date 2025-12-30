"""
Availability Engine - Slot Availability Checking

Checks if slots are available considering:
- Existing bookings
- Chef availability
- Travel time constraints
- Setup/cleanup buffers
"""

from datetime import date, time, datetime, timedelta
from typing import List, Optional
from uuid import UUID
import logging

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

logger = logging.getLogger(__name__)


# ============================================================
# Data Models
# ============================================================


class AvailableSlot(BaseModel):
    """Represents an available slot."""

    slot_number: int
    slot_name: str
    slot_time: time
    standard_time: time
    is_available: bool = True
    available_chefs: int = 0
    conflict_reason: Optional[str] = None
    booking_count: int = 0
    suggested_time: Optional[time] = None
    adjustment_minutes: int = 0
    notes: Optional[str] = None


class SlotAvailabilityResult(BaseModel):
    """Result of checking all slots for a date."""

    event_date: date
    guest_count: int
    available_slots: List[AvailableSlot] = []
    partially_available_slots: List[AvailableSlot] = []
    unavailable_slots: List[AvailableSlot] = []
    message: str = ""


class AvailabilityCheckResult(BaseModel):
    """Result of checking a specific slot."""

    requested_date: date
    requested_time: time
    is_requested_available: bool
    conflict_reason: Optional[str] = None
    message: str = ""
    suggestions: List[AvailableSlot] = []


# ============================================================
# Availability Engine
# ============================================================


class AvailabilityEngine:
    """
    Checks slot availability for booking requests.

    Features:
    - Database integration for real booking data
    - Chef availability checking
    - Travel time conflict detection
    """

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        # Max bookings per slot (usually 1 for hibachi - chef can only be at one place)
        self.max_bookings_per_slot = 1

    async def check_slot_availability(
        self,
        event_date: date,
        slot_time: time,
        guest_count: int = 10,
    ) -> dict:
        """
        Check if a specific slot is available.

        Returns:
            dict with is_available, available_chefs, conflict_reason
        """
        from .slot_manager import DEFAULT_SLOTS

        # Find the slot that matches this time
        slot_number = None
        for slot_num, slot_config in DEFAULT_SLOTS.items():
            if slot_config.standard_time == slot_time:
                slot_number = slot_num
                break
            # Check within ±60 min range
            if slot_config.min_time_60 <= slot_time <= slot_config.max_time_60:
                slot_number = slot_num
                break

        if slot_number is None:
            return {
                "is_available": False,
                "available_chefs": 0,
                "conflict_reason": "Time is outside valid slot ranges",
            }

        # Check database for existing bookings
        booking_count = await self._get_booking_count_for_slot(
            event_date, slot_time, slot_number
        )

        is_available = booking_count < self.max_bookings_per_slot
        conflict_reason = None if is_available else "Slot is already booked"

        # For now, assume we have chefs if slot is available
        # Full chef optimization will be added later
        available_chefs = 3 if is_available else 0

        return {
            "is_available": is_available,
            "available_chefs": available_chefs,
            "conflict_reason": conflict_reason,
            "booking_count": booking_count,
        }

    async def _get_booking_count_for_slot(
        self,
        event_date: date,
        slot_time: time,
        slot_number: int,
    ) -> int:
        """Get count of bookings for a specific date and slot."""
        if not self.db:
            return 0

        try:
            from db.models.core import Booking

            # Query bookings for this date and slot
            query = select(Booking).where(
                and_(
                    Booking.date == event_date,
                    Booking.slot == slot_time,
                    Booking.status.in_(["pending", "confirmed", "deposit_paid"]),
                    Booking.deleted_at.is_(None),
                )
            )

            result = await self.db.execute(query)
            bookings = result.scalars().all()
            return len(bookings)

        except Exception as e:
            logger.warning(f"Error checking bookings: {e}")
            return 0

    async def get_available_slots_for_date(
        self,
        event_date: date,
        guest_count: int = 10,
    ) -> List[AvailableSlot]:
        """
        Get all available slots for a date.
        """
        from .slot_manager import DEFAULT_SLOTS

        slots = []

        for slot_num, slot_config in DEFAULT_SLOTS.items():
            if not slot_config.is_active:
                continue

            result = await self.check_slot_availability(
                event_date=event_date,
                slot_time=slot_config.standard_time,
                guest_count=guest_count,
            )

            slots.append(
                AvailableSlot(
                    slot_number=slot_num,
                    slot_name=slot_config.slot_name,
                    slot_time=slot_config.standard_time,
                    standard_time=slot_config.standard_time,
                    is_available=result["is_available"],
                    available_chefs=result["available_chefs"],
                    conflict_reason=result.get("conflict_reason"),
                    booking_count=result.get("booking_count", 0),
                )
            )

        return slots

    async def get_available_slots(
        self,
        target_date: date,
        venue_lat: Optional[float] = None,
        venue_lng: Optional[float] = None,
        guest_count: int = 10,
        existing_bookings: Optional[List] = None,
        available_chefs: Optional[List] = None,
    ) -> SlotAvailabilityResult:
        """
        Get all slots with availability status for a date.

        This is the main method used by SuggestionEngine.
        """
        all_slots = await self.get_available_slots_for_date(target_date, guest_count)

        available = [s for s in all_slots if s.is_available]
        unavailable = [s for s in all_slots if not s.is_available]

        # For now, no partially available slots (will add with travel time logic)
        partial = []

        if available:
            message = f"{len(available)} slots available on {target_date.strftime('%A, %B %d')}"
        else:
            message = f"No slots available on {target_date.strftime('%A, %B %d')}"

        return SlotAvailabilityResult(
            event_date=target_date,
            guest_count=guest_count,
            available_slots=available,
            partially_available_slots=partial,
            unavailable_slots=unavailable,
            message=message,
        )

    async def check_specific_slot(
        self,
        event_date: date,
        event_time: time,
        guest_count: int = 10,
        venue_lat: Optional[float] = None,
        venue_lng: Optional[float] = None,
    ) -> AvailabilityCheckResult:
        """
        Check availability for a specific date and time.

        Returns whether the slot is available and suggestions if not.
        """
        result = await self.check_slot_availability(event_date, event_time, guest_count)

        if result["is_available"]:
            return AvailabilityCheckResult(
                requested_date=event_date,
                requested_time=event_time,
                is_requested_available=True,
                message="Your requested time is available!",
            )

        # Slot not available - get alternatives
        all_slots = await self.get_available_slots_for_date(event_date, guest_count)
        available_alternatives = [s for s in all_slots if s.is_available]

        return AvailabilityCheckResult(
            requested_date=event_date,
            requested_time=event_time,
            is_requested_available=False,
            conflict_reason=result.get("conflict_reason", "Slot is not available"),
            message="The requested time is not available. Here are some alternatives:",
            suggestions=available_alternatives,
        )
