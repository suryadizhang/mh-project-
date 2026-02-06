"""
Slot Manager - 4-Slot Daily Time Management

Manages the 4 daily time slots for hibachi bookings:
- Slot 1: Lunch (12:00 PM, adjustable 11:00 AM - 1:00 PM)
- Slot 2: Afternoon (3:00 PM, adjustable 2:00 PM - 4:00 PM)
- Slot 3: Early Evening (6:00 PM, adjustable 5:00 PM - 7:00 PM)
- Slot 4: Prime Time (9:00 PM, adjustable 8:00 PM - 10:00 PM)
"""

from datetime import date, time
from enum import IntEnum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel

# ============================================================
# Constants & Enums
# ============================================================


class TimeSlot(IntEnum):
    """4 daily time slots."""

    LUNCH = 1  # 12:00 PM
    AFTERNOON = 2  # 3:00 PM
    EARLY_EVENING = 3  # 6:00 PM
    PRIME_TIME = 4  # 9:00 PM


# ============================================================
# Data Models
# ============================================================


class SlotConfiguration(BaseModel):
    """Configuration for a single time slot."""

    slot_number: int
    slot_name: str
    standard_time: time
    # ±30 minute adjustment range (preferred)
    min_time_30: time
    max_time_30: time
    # ±60 minute adjustment range (maximum)
    min_time_60: time
    max_time_60: time
    # Buffer times
    # NOTE: Increased from 30 to 60 min to account for traffic between venues
    setup_minutes: int = 60
    cleanup_minutes: int = 15
    is_active: bool = True


class SlotStatus(BaseModel):
    """Status of a slot for a specific date."""

    slot_number: int
    slot_name: str
    date: date
    standard_time: time
    adjusted_time: Optional[time] = None
    is_available: bool = True
    is_booked: bool = False
    booking_id: Optional[UUID] = None
    chef_id: Optional[UUID] = None
    adjustment_reason: Optional[str] = None


class SlotAdjustment(BaseModel):
    """Proposed slot time adjustment."""

    slot_number: int
    original_time: time
    proposed_time: time
    shift_minutes: int  # Positive = later, negative = earlier
    reason: str
    is_within_30_min: bool  # Preferred adjustment
    is_within_60_min: bool  # Maximum adjustment


# ============================================================
# Default Slot Configurations
# ============================================================

DEFAULT_SLOTS: Dict[int, SlotConfiguration] = {
    TimeSlot.LUNCH: SlotConfiguration(
        slot_number=TimeSlot.LUNCH,
        slot_name="Lunch",
        standard_time=time(12, 0),
        min_time_30=time(11, 30),
        max_time_30=time(12, 30),
        min_time_60=time(11, 0),
        max_time_60=time(13, 0),
    ),
    TimeSlot.AFTERNOON: SlotConfiguration(
        slot_number=TimeSlot.AFTERNOON,
        slot_name="Afternoon",
        standard_time=time(15, 0),
        min_time_30=time(14, 30),
        max_time_30=time(15, 30),
        min_time_60=time(14, 0),
        max_time_60=time(16, 0),
    ),
    TimeSlot.EARLY_EVENING: SlotConfiguration(
        slot_number=TimeSlot.EARLY_EVENING,
        slot_name="Early Evening",
        standard_time=time(18, 0),
        min_time_30=time(17, 30),
        max_time_30=time(18, 30),
        min_time_60=time(17, 0),
        max_time_60=time(19, 0),
    ),
    TimeSlot.PRIME_TIME: SlotConfiguration(
        slot_number=TimeSlot.PRIME_TIME,
        slot_name="Prime Time",
        standard_time=time(21, 0),
        min_time_30=time(20, 30),
        max_time_30=time(21, 30),
        min_time_60=time(20, 0),
        max_time_60=time(22, 0),
    ),
}


# ============================================================
# Slot Manager Service
# ============================================================


class SlotManager:
    """
    Manages 4-slot daily scheduling system.

    Features:
    - Standard slot times with ±30/60 min adjustment ranges
    - Slot availability checking
    - Time adjustment suggestions
    - Conflict detection
    """

    def __init__(self, custom_slots: Optional[Dict[int, SlotConfiguration]] = None):
        """
        Initialize slot manager with default or custom slot configurations.

        Args:
            custom_slots: Override default slot configurations
        """
        self.slots = custom_slots or DEFAULT_SLOTS

    def get_slot_config(self, slot_number: int) -> SlotConfiguration:
        """Get configuration for a specific slot."""
        if slot_number not in self.slots:
            raise ValueError(f"Invalid slot number: {slot_number}. Must be 1-4.")
        return self.slots[slot_number]

    def get_all_slots(self) -> List[SlotConfiguration]:
        """Get all slot configurations."""
        return [self.slots[i] for i in sorted(self.slots.keys())]

    def get_slot_for_time(self, requested_time: time) -> Optional[int]:
        """
        Determine which slot a requested time falls into.

        Args:
            requested_time: Time customer wants

        Returns:
            Slot number (1-4) or None if outside all slot ranges
        """
        for slot_num, config in self.slots.items():
            if config.min_time_60 <= requested_time <= config.max_time_60:
                return slot_num
        return None

    def snap_to_nearest_slot(self, requested_time: time) -> tuple[int, time]:
        """
        Snap any customer-requested time to the nearest slot.

        Option C+E Hybrid Implementation:
        - Customer picks ANY time (flexible UX)
        - System snaps to nearest slot internally (chef scheduling)
        - Used for conflict detection and chef assignment

        Time Ranges (midpoint-based snapping):
        - Before 10:30 AM → LUNCH (12:00 PM)
        - 10:30 AM - 1:30 PM → LUNCH (12:00 PM)
        - 1:31 PM - 4:30 PM → AFTERNOON (3:00 PM)
        - 4:31 PM - 7:30 PM → EARLY_EVENING (6:00 PM)
        - 7:31 PM - 10:30 PM → PRIME_TIME (9:00 PM)
        - After 10:30 PM → PRIME_TIME (9:00 PM)

        Args:
            requested_time: Any time the customer requested

        Returns:
            Tuple of (slot_number, slot_standard_time)

        Example:
            >>> slot_manager.snap_to_nearest_slot(time(14, 45))
            (2, time(15, 0))  # AFTERNOON slot
            >>> slot_manager.snap_to_nearest_slot(time(17, 0))
            (3, time(18, 0))  # EARLY_EVENING slot
        """
        # Convert to minutes since midnight for easier comparison
        minutes = requested_time.hour * 60 + requested_time.minute

        # Midpoints between slots (in minutes since midnight):
        # LUNCH center: 12:00 (720 min)
        # AFTERNOON center: 15:00 (900 min)
        # EARLY_EVENING center: 18:00 (1080 min)
        # PRIME_TIME center: 21:00 (1260 min)

        # Midpoint LUNCH-AFTERNOON: 13:30 (810 min)
        # Midpoint AFTERNOON-EARLY_EVENING: 16:30 (990 min)
        # Midpoint EARLY_EVENING-PRIME_TIME: 19:30 (1170 min)

        # Before LUNCH starts (before 10:30 = 630 min) → snap to LUNCH
        # This handles early morning requests gracefully
        if minutes < 630:  # Before 10:30 AM
            slot_num = TimeSlot.LUNCH
        # LUNCH zone: 10:30 AM - 1:30 PM (630 - 810 min)
        elif minutes <= 810:  # Until 1:30 PM
            slot_num = TimeSlot.LUNCH
        # AFTERNOON zone: 1:31 PM - 4:30 PM (811 - 990 min)
        elif minutes <= 990:  # Until 4:30 PM
            slot_num = TimeSlot.AFTERNOON
        # EARLY_EVENING zone: 4:31 PM - 7:30 PM (991 - 1170 min)
        elif minutes <= 1170:  # Until 7:30 PM
            slot_num = TimeSlot.EARLY_EVENING
        # PRIME_TIME zone: 7:31 PM onwards (1171+ min)
        else:
            slot_num = TimeSlot.PRIME_TIME

        config = self.slots[slot_num]
        return (slot_num, config.standard_time)

    def get_standard_time(self, slot_number: int) -> time:
        """Get the standard (default) time for a slot."""
        return self.get_slot_config(slot_number).standard_time

    def is_time_in_slot_range(
        self, requested_time: time, slot_number: int, allow_60_min_range: bool = False
    ) -> bool:
        """
        Check if a time falls within a slot's adjustment range.

        Args:
            requested_time: Time to check
            slot_number: Slot to check against
            allow_60_min_range: If True, use ±60 min range; otherwise ±30 min

        Returns:
            True if time is within the slot's range
        """
        config = self.get_slot_config(slot_number)

        if allow_60_min_range:
            return config.min_time_60 <= requested_time <= config.max_time_60
        else:
            return config.min_time_30 <= requested_time <= config.max_time_30

    def calculate_adjustment(self, slot_number: int, requested_time: time) -> SlotAdjustment:
        """
        Calculate adjustment needed from standard time.

        Args:
            slot_number: Target slot
            requested_time: Requested booking time

        Returns:
            SlotAdjustment with shift details
        """
        config = self.get_slot_config(slot_number)

        # Calculate minutes from midnight for comparison
        standard_minutes = config.standard_time.hour * 60 + config.standard_time.minute
        requested_minutes = requested_time.hour * 60 + requested_time.minute
        shift_minutes = requested_minutes - standard_minutes

        # Check ranges
        is_within_30 = config.min_time_30 <= requested_time <= config.max_time_30
        is_within_60 = config.min_time_60 <= requested_time <= config.max_time_60

        return SlotAdjustment(
            slot_number=slot_number,
            original_time=config.standard_time,
            proposed_time=requested_time,
            shift_minutes=shift_minutes,
            reason=self._get_adjustment_reason(shift_minutes),
            is_within_30_min=is_within_30,
            is_within_60_min=is_within_60,
        )

    def suggest_adjustment(
        self, slot_number: int, required_shift_minutes: int, prefer_earlier: bool = True
    ) -> Optional[SlotAdjustment]:
        """
        Suggest a slot time adjustment.

        Args:
            slot_number: Slot to adjust
            required_shift_minutes: How many minutes to shift (negative = earlier)
            prefer_earlier: If True, prefer earlier times when possible

        Returns:
            SlotAdjustment if valid adjustment exists, None otherwise
        """
        config = self.get_slot_config(slot_number)

        # Calculate proposed time
        standard_minutes = config.standard_time.hour * 60 + config.standard_time.minute
        proposed_minutes = standard_minutes + required_shift_minutes

        # Convert back to time
        proposed_hour = proposed_minutes // 60
        proposed_minute = proposed_minutes % 60

        # Validate hour range
        if proposed_hour < 0 or proposed_hour >= 24:
            return None

        proposed_time = time(proposed_hour, proposed_minute)

        # Check if within allowed range
        if not (config.min_time_60 <= proposed_time <= config.max_time_60):
            return None

        adjustment = self.calculate_adjustment(slot_number, proposed_time)
        return adjustment

    def get_available_adjustments(
        self, slot_number: int, increment_minutes: int = 30
    ) -> List[SlotAdjustment]:
        """
        Get all valid adjustment options for a slot.

        Args:
            slot_number: Target slot
            increment_minutes: Time increments (default 30 min)

        Returns:
            List of valid adjustments (e.g., -60, -30, 0, +30, +60)
        """
        adjustments = []

        for shift in range(-60, 61, increment_minutes):
            adjustment = self.suggest_adjustment(slot_number, shift)
            if adjustment and adjustment.is_within_60_min:
                adjustments.append(adjustment)

        return adjustments

    def can_slots_conflict(self, slot1: int, slot2: int, event_duration_minutes: int = 120) -> bool:
        """
        Check if two slots could potentially conflict.

        Slots conflict if even with maximum adjustments and event duration,
        they might overlap.

        Args:
            slot1: First slot number
            slot2: Second slot number
            event_duration_minutes: Duration of events

        Returns:
            True if slots could conflict
        """
        if slot1 == slot2:
            return True

        config1 = self.get_slot_config(slot1)
        config2 = self.get_slot_config(slot2)

        # Get the latest possible end time for slot1
        latest_start1 = config1.max_time_60
        latest_start1_minutes = latest_start1.hour * 60 + latest_start1.minute
        latest_end1_minutes = (
            latest_start1_minutes + event_duration_minutes + config1.cleanup_minutes
        )

        # Get the earliest possible start time for slot2
        earliest_start2 = config2.min_time_60
        earliest_start2_minutes = earliest_start2.hour * 60 + earliest_start2.minute
        # Account for setup time
        earliest_arrival2_minutes = earliest_start2_minutes - config2.setup_minutes

        # They conflict if slot1's latest end overlaps with slot2's earliest arrival
        return latest_end1_minutes > earliest_arrival2_minutes

    def get_minimum_gap_minutes(
        self, from_slot: int, to_slot: int, event_duration_minutes: int = 90
    ) -> int:
        """
        Calculate minimum time gap between two consecutive bookings.

        Args:
            from_slot: First booking's slot
            to_slot: Second booking's slot
            event_duration_minutes: Duration of first event

        Returns:
            Minimum minutes between events (for travel calculation)
        """
        config1 = self.get_slot_config(from_slot)
        config2 = self.get_slot_config(to_slot)

        # Standard times
        start1_minutes = config1.standard_time.hour * 60 + config1.standard_time.minute
        start2_minutes = config2.standard_time.hour * 60 + config2.standard_time.minute

        # End of first event + cleanup
        end1_minutes = start1_minutes + event_duration_minutes + config1.cleanup_minutes

        # Arrival time for second event (start - setup)
        arrival2_minutes = start2_minutes - config2.setup_minutes

        # Gap available for travel
        gap = arrival2_minutes - end1_minutes

        return max(0, gap)

    def _get_adjustment_reason(self, shift_minutes: int) -> str:
        """Generate a human-readable reason for the adjustment."""
        if shift_minutes == 0:
            return "Standard time"
        elif shift_minutes > 0:
            return f"Shifted {shift_minutes} minutes later for travel logistics"
        else:
            return f"Shifted {abs(shift_minutes)} minutes earlier for travel logistics"

    def format_slot_display(self, slot_number: int) -> str:
        """Format slot for display to customers."""
        config = self.get_slot_config(slot_number)
        formatted_time = config.standard_time.strftime("%-I:%M %p")
        return f"{config.slot_name} ({formatted_time})"

    def get_slot_options_for_display(self) -> List[Dict]:
        """Get all slots formatted for frontend dropdown."""
        return [
            {
                "value": slot.slot_number,
                "label": self.format_slot_display(slot.slot_number),
                "time": slot.standard_time.strftime("%H:%M"),
                "name": slot.slot_name,
            }
            for slot in self.get_all_slots()
            if slot.is_active
        ]


# Alias for backward compatibility with scheduling router
SlotManagerService = SlotManager
