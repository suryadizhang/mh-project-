"""
Slot Manager Service

Manages time slot configuration, adjustment logic, and event duration calculation.

Business Rules:
- 4 standard slots: 12PM, 3PM, 6PM, 9PM
- Each slot adjustable within configured limits
- Event duration: 60 + (guests × 3) minutes, max 120
- 15 minute buffer between event end and next booking start
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class SlotConfig:
    """Configuration for a time slot"""

    slot_name: str
    base_time: time
    min_adjust_minutes: int  # Negative = can start earlier
    max_adjust_minutes: int  # Positive = can start later
    min_event_duration: int
    max_event_duration: int
    is_active: bool = True

    @property
    def slot_time(self) -> time:
        """Alias for base_time for API compatibility"""
        return self.base_time

    @property
    def adjust_earlier_minutes(self) -> int:
        """How many minutes earlier slot can start (positive value)"""
        return abs(self.min_adjust_minutes)

    @property
    def adjust_later_minutes(self) -> int:
        """How many minutes later slot can start"""
        return self.max_adjust_minutes


@dataclass
class SlotAdjustment:
    """Proposed slot adjustment"""

    original_time: time
    adjusted_time: time
    shift_minutes: int
    reason: str


# Default slot configurations (fallback if DB not available)
DEFAULT_SLOT_CONFIGS = {
    "12PM": SlotConfig("12PM", time(12, 0), 0, 60, 90, 120),
    "3PM": SlotConfig("3PM", time(15, 0), -30, 60, 90, 120),
    "6PM": SlotConfig("6PM", time(18, 0), -60, 60, 90, 120),
    "9PM": SlotConfig("9PM", time(21, 0), -60, 30, 90, 120),
}

# Standard slot times for quick lookup
SLOT_TIMES = {
    "12PM": time(12, 0),
    "3PM": time(15, 0),
    "6PM": time(18, 0),
    "9PM": time(21, 0),
}

BUFFER_MINUTES = 15  # Buffer between events


class SlotManagerService:
    """
    Manages time slots, adjustments, and event duration calculations.
    """

    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session

    # =========================================================================
    # EVENT DURATION
    # =========================================================================

    @staticmethod
    def calculate_event_duration(guest_count: int) -> int:
        """
        Calculate event duration based on party size.

        Formula: min(60 + (guests × 3), 120)

        Examples:
        - 10 guests = 90 minutes
        - 15 guests = 105 minutes
        - 20+ guests = 120 minutes (capped)

        Args:
            guest_count: Total number of guests (adults + children)

        Returns:
            Event duration in minutes (90-120)
        """
        if guest_count <= 0:
            return 90  # Minimum duration

        calculated = 60 + (guest_count * 3)
        return min(max(calculated, 90), 120)  # Clamp to 90-120

    # =========================================================================
    # SLOT CONFIGURATION
    # =========================================================================

    async def get_slot_config(
        self,
        slot_name: str,
        station_id: Optional[UUID] = None,
    ) -> SlotConfig:
        """
        Get slot configuration from database or use defaults.

        Args:
            slot_name: Slot identifier ('12PM', '3PM', '6PM', '9PM')
            station_id: Optional station for per-station overrides

        Returns:
            SlotConfig with adjustment limits
        """
        # If no database session, use defaults
        if not self.session:
            return DEFAULT_SLOT_CONFIGS.get(slot_name, DEFAULT_SLOT_CONFIGS["3PM"])

        try:
            # Query database for configuration
            query = """
                SELECT slot_name, base_time, min_adjust_minutes, max_adjust_minutes,
                       min_event_duration, max_event_duration
                FROM ops.slot_configurations
                WHERE slot_name = :slot_name
                  AND (station_id = :station_id OR station_id IS NULL)
                ORDER BY station_id NULLS LAST
                LIMIT 1
            """
            result = await self.session.execute(
                select("*").from_statement(query),
                {"slot_name": slot_name, "station_id": str(station_id) if station_id else None},
            )
            row = result.fetchone()

            if row:
                return SlotConfig(
                    slot_name=row.slot_name,
                    base_time=row.base_time,
                    min_adjust_minutes=row.min_adjust_minutes,
                    max_adjust_minutes=row.max_adjust_minutes,
                    min_event_duration=row.min_event_duration,
                    max_event_duration=row.max_event_duration,
                )
        except Exception:
            pass  # Fall through to defaults

        return DEFAULT_SLOT_CONFIGS.get(slot_name, DEFAULT_SLOT_CONFIGS["3PM"])

    def get_all_slot_configs(self) -> list[SlotConfig]:
        """
        Get all available slot configurations.

        Returns list of SlotConfig ordered by time.
        """
        return [
            DEFAULT_SLOT_CONFIGS["12PM"],
            DEFAULT_SLOT_CONFIGS["3PM"],
            DEFAULT_SLOT_CONFIGS["6PM"],
            DEFAULT_SLOT_CONFIGS["9PM"],
        ]

    def get_slot_name(self, t: time) -> Optional[str]:
        """
        Get slot name for a given time.

        Args:
            t: Time to find slot for

        Returns:
            Slot name or None if not a standard slot
        """
        for name, slot_time in SLOT_TIMES.items():
            if slot_time == t:
                return name
        return None

    def get_base_time(self, slot_name: str) -> Optional[time]:
        """Get base time for a slot name."""
        return SLOT_TIMES.get(slot_name)

    # =========================================================================
    # SLOT ADJUSTMENT
    # =========================================================================

    async def calculate_adjusted_time(
        self,
        slot_name: str,
        required_start_after: datetime,
        station_id: Optional[UUID] = None,
    ) -> Optional[SlotAdjustment]:
        """
        Calculate adjusted slot time to start after a required time.

        Used when chef has a previous booking and needs travel time.

        Args:
            slot_name: Target slot ('12PM', '3PM', '6PM', '9PM')
            required_start_after: Earliest possible start time
            station_id: Optional station for config lookup

        Returns:
            SlotAdjustment if adjustment possible, None if not feasible
        """
        config = await self.get_slot_config(slot_name, station_id)
        base_datetime = datetime.combine(required_start_after.date(), config.base_time)

        # Calculate required shift
        if required_start_after <= base_datetime:
            # No adjustment needed - can start at base time
            return SlotAdjustment(
                original_time=config.base_time,
                adjusted_time=config.base_time,
                shift_minutes=0,
                reason="No adjustment needed",
            )

        shift_needed = int((required_start_after - base_datetime).total_seconds() / 60)

        # Check if shift is within limits
        if shift_needed > config.max_adjust_minutes:
            return None  # Cannot adjust enough

        # Calculate adjusted time
        adjusted_datetime = base_datetime + timedelta(minutes=shift_needed)

        return SlotAdjustment(
            original_time=config.base_time,
            adjusted_time=adjusted_datetime.time(),
            shift_minutes=shift_needed,
            reason=f"Shifted +{shift_needed}min for travel time",
        )

    async def can_accommodate_travel(
        self,
        previous_booking_end: datetime,
        travel_time_minutes: int,
        target_slot: str,
        station_id: Optional[UUID] = None,
    ) -> tuple[bool, Optional[SlotAdjustment]]:
        """
        Check if a slot can accommodate travel time from previous booking.

        Args:
            previous_booking_end: When previous booking ends
            travel_time_minutes: Expected travel time
            target_slot: Slot to book
            station_id: Optional station

        Returns:
            Tuple of (can_accommodate, adjustment if needed)
        """
        # Add buffer to travel time
        total_gap_needed = travel_time_minutes + BUFFER_MINUTES
        required_start = previous_booking_end + timedelta(minutes=total_gap_needed)

        adjustment = await self.calculate_adjusted_time(target_slot, required_start, station_id)

        if adjustment is None:
            return False, None

        return True, adjustment

    # =========================================================================
    # TIME WINDOW CALCULATION
    # =========================================================================

    def get_booking_time_window(
        self,
        booking_date: date,
        slot_time: time,
        duration_minutes: int,
    ) -> tuple[datetime, datetime]:
        """
        Get start and end datetime for a booking.

        Args:
            booking_date: Date of booking
            slot_time: Start time (may be adjusted)
            duration_minutes: Event duration

        Returns:
            Tuple of (start_datetime, end_datetime)
        """
        start = datetime.combine(booking_date, slot_time)
        end = start + timedelta(minutes=duration_minutes)
        return start, end

    def get_chef_availability_window(
        self,
        booking_date: date,
        slot_time: time,
        duration_minutes: int,
        travel_buffer: int = BUFFER_MINUTES,
    ) -> tuple[datetime, datetime]:
        """
        Get the time window a chef is unavailable due to a booking.

        Includes buffer time after event for cleanup/travel prep.

        Args:
            booking_date: Date of booking
            slot_time: Event start time
            duration_minutes: Event duration
            travel_buffer: Buffer time after event

        Returns:
            Tuple of (busy_from, busy_until)
        """
        start = datetime.combine(booking_date, slot_time)
        end = start + timedelta(minutes=duration_minutes + travel_buffer)
        return start, end

    # =========================================================================
    # SLOT AVAILABILITY
    # =========================================================================

    def get_all_slots(self) -> list[str]:
        """Get list of all slot names in order."""
        return ["12PM", "3PM", "6PM", "9PM"]

    def get_next_slot(self, current_slot: str) -> Optional[str]:
        """Get the next slot after the current one."""
        slots = self.get_all_slots()
        try:
            idx = slots.index(current_slot)
            if idx < len(slots) - 1:
                return slots[idx + 1]
        except ValueError:
            pass
        return None

    def get_previous_slot(self, current_slot: str) -> Optional[str]:
        """Get the previous slot before the current one."""
        slots = self.get_all_slots()
        try:
            idx = slots.index(current_slot)
            if idx > 0:
                return slots[idx - 1]
        except ValueError:
            pass
        return None
