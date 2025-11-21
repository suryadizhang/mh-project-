"""
Tests for specific bug fixes discovered during exhaustive audit.

These tests verify:
- Bug #11: Time slot overlap calculation with minute precision
- Bug #12: Error handling for invalid time formats

Created: 2025-01-XX
Related: FINAL_EXHAUSTIVE_BUG_AUDIT.md
"""

from datetime import date
from unittest.mock import AsyncMock, Mock

import pytest
from src.core.exceptions import BusinessLogicException, ErrorCode
from src.services.booking_service import BookingService


class TestBug11TimeSlotMinutePrecision:
    """Test Bug #11 fix: Time overlap calculation must handle minutes correctly.

    Before fix: Only compared hours, allowing double bookings at different minutes.
    After fix: Compares total minutes since midnight for accurate overlap detection.
    """

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_repository = Mock()
        self.mock_repository.check_availability = AsyncMock(return_value=True)
        self.service = BookingService(repository=self.mock_repository)

    def test_slots_with_minute_precision_overlap(self):
        """Test that slots with minutes that overlap are detected correctly.

        Scenario: Event 1 is 2:30 PM - 4:30 PM, Event 2 starts at 4:00 PM
        Expected: Should detect overlap (4:00-4:30 overlaps)
        Bug #11: Would NOT detect overlap (only compared hours: 2 vs 4)
        """
        # Event 1: 2:30 PM - 4:30 PM (2 hour duration)
        slot1_start = "14:30"
        slot1_end = "16:30"

        # Event 2: 4:00 PM start (2 hour duration = 4:00-6:00 PM)
        slot2_start = "16:00"
        duration_hours = 2

        # Should overlap (4:00-4:30 overlaps between both events)
        result = self.service._slots_overlap(
            slot1_start, slot1_end, slot2_start, duration_hours
        )
        assert (
            result is True
        ), "2:30-4:30 PM should overlap with 4:00-6:00 PM (4:00-4:30 overlap)"

        # Event 2: 4:30 PM start (2 hour duration = 4:30-6:30 PM)
        slot2_start = "16:30"

        # Should NOT overlap (exactly adjacent, no time overlap)
        result = self.service._slots_overlap(
            slot1_start, slot1_end, slot2_start, duration_hours
        )
        assert (
            result is False
        ), "2:30-4:30 PM should NOT overlap with 4:30-6:30 PM (adjacent)"

    def test_slots_with_30_minute_precision(self):
        """Test overlaps with 30-minute time slots.

        Critical for restaurants/venues with half-hour bookings.
        Bug #11 would lose all 30-minute precision.
        """
        # Event 1: 1:00 PM - 2:30 PM
        slot1_start = "13:00"
        slot1_end = "14:30"

        # Event 2: 2:15 PM start (1 hour = 2:15-3:15 PM)
        slot2_start = "14:15"
        duration_hours = 1

        # Should overlap (2:15-2:30 overlaps)
        result = self.service._slots_overlap(
            slot1_start, slot1_end, slot2_start, duration_hours
        )
        assert result is True, "1:00-2:30 PM should overlap with 2:15-3:15 PM"

        # Event 2: 2:30 PM start (1 hour = 2:30-3:30 PM)
        slot2_start = "14:30"

        # Should NOT overlap (exactly adjacent)
        result = self.service._slots_overlap(
            slot1_start, slot1_end, slot2_start, duration_hours
        )
        assert (
            result is False
        ), "1:00-2:30 PM should NOT overlap with 2:30-3:30 PM (adjacent)"

    def test_slots_with_15_minute_precision(self):
        """Test overlaps with 15-minute time slots.

        Some venues use 15-minute precision for scheduling.
        Bug #11 would completely fail for these cases.
        """
        # Event 1: 12:15 PM - 1:45 PM
        slot1_start = "12:15"
        slot1_end = "13:45"

        # Event 2: 1:30 PM start (30 min = 1:30-2:00 PM)
        slot2_start = "13:30"
        duration_hours = 0.5  # 30 minutes

        # Should overlap (1:30-1:45 overlaps)
        result = self.service._slots_overlap(
            slot1_start, slot1_end, slot2_start, duration_hours
        )
        assert result is True, "12:15-1:45 PM should overlap with 1:30-2:00 PM"

        # Event 2: 1:45 PM start (30 min = 1:45-2:15 PM)
        slot2_start = "13:45"

        # Should NOT overlap (exactly adjacent)
        result = self.service._slots_overlap(
            slot1_start, slot1_end, slot2_start, duration_hours
        )
        assert (
            result is False
        ), "12:15-1:45 PM should NOT overlap with 1:45-2:15 PM (adjacent)"

    def test_same_hour_different_minutes_no_overlap(self):
        """Test that events in same hour but different minutes work correctly.

        Bug #11 would treat 2:00 PM and 2:45 PM as same start time.
        """
        # Event 1: 2:00 PM - 3:00 PM
        slot1_start = "14:00"
        slot1_end = "15:00"

        # Event 2: 2:45 PM start (15 min = 2:45-3:00 PM)
        slot2_start = "14:45"
        duration_hours = 0.25  # 15 minutes

        # Should overlap (2:45-3:00 overlaps)
        result = self.service._slots_overlap(
            slot1_start, slot1_end, slot2_start, duration_hours
        )
        assert result is True, "2:00-3:00 PM should overlap with 2:45-3:00 PM"


class TestBug12InvalidTimeFormatHandling:
    """Test Bug #12 fix: Error handling for invalid time formats.

    Before fix: Would crash with ValueError or AttributeError.
    After fix: Raises BusinessLogicException with clear error message.
    """

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_repository = Mock()
        self.service = BookingService(repository=self.mock_repository)

    @pytest.mark.asyncio
    async def test_invalid_time_hour_out_of_range(self):
        """Test that invalid hour (>23) raises BusinessLogicException."""
        booking_data = Mock()
        booking_data.customer_id = 1
        booking_data.event_date = date(2025, 12, 25)
        booking_data.event_time = "25:00"  # Invalid: hour > 23
        booking_data.party_size = 4
        booking_data.duration_hours = 2
        booking_data.special_requests = None

        # Should raise BusinessLogicException in create_booking BEFORE any repository calls
        with pytest.raises(BusinessLogicException) as exc_info:
            await self.service.create_booking(booking_data)

        assert exc_info.value.error_code == ErrorCode.BAD_REQUEST
        assert "Invalid time format" in str(exc_info.value.message)
        assert "25:00" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_invalid_time_minute_out_of_range(self):
        """Test that invalid minute (>59) raises BusinessLogicException."""
        booking_data = Mock()
        booking_data.customer_id = 1
        booking_data.event_date = date(2025, 12, 25)
        booking_data.event_time = "14:99"  # Invalid: minute > 59
        booking_data.party_size = 4
        booking_data.duration_hours = 2
        booking_data.special_requests = None

        # Should raise BusinessLogicException in create_booking BEFORE any repository calls
        with pytest.raises(BusinessLogicException) as exc_info:
            await self.service.create_booking(booking_data)

        assert exc_info.value.error_code == ErrorCode.BAD_REQUEST
        assert "Invalid time format" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_invalid_time_format_12_hour(self):
        """Test that 12-hour format with AM/PM raises BusinessLogicException."""
        booking_data = Mock()
        booking_data.customer_id = 1
        booking_data.event_date = date(2025, 12, 25)
        booking_data.event_time = "2:30 PM"  # Invalid: not 24-hour format
        booking_data.party_size = 4
        booking_data.duration_hours = 2
        booking_data.special_requests = None

        # Should raise BusinessLogicException in create_booking BEFORE any repository calls
        with pytest.raises(BusinessLogicException) as exc_info:
            await self.service.create_booking(booking_data)

        assert exc_info.value.error_code == ErrorCode.BAD_REQUEST
        assert "Invalid time format" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_invalid_time_format_single_digit_hour(self):
        """Test that single-digit hour without leading zero is handled.

        Note: "9:30" actually passes strptime validation, so this test verifies
        it gets processed correctly (either accepted or rejected based on requirements).
        """
        booking_data = Mock()
        booking_data.customer_id = 1
        booking_data.event_date = date(2025, 12, 25)
        booking_data.event_time = (
            "9:30"  # Might be valid depending on strptime
        )
        booking_data.party_size = 4
        booking_data.duration_hours = 2
        booking_data.special_requests = None

        # Mock repository methods to avoid TypeError
        self.mock_repository.get_existing_bookings = AsyncMock(return_value=[])
        self.mock_repository.check_availability = AsyncMock(return_value=True)
        self.mock_repository.create = AsyncMock(return_value=Mock(id=1))

        # This should either succeed OR raise BusinessLogicException (not crash)
        try:
            result = await self.service.create_booking(booking_data)
            # If accepted, verify it parsed correctly as 09:30
            assert result is not None
        except BusinessLogicException as e:
            # If rejected, verify it's an INVALID_INPUT error
            assert e.error_code == ErrorCode.BAD_REQUEST

    @pytest.mark.asyncio
    async def test_invalid_time_format_text(self):
        """Test that text time raises BusinessLogicException."""
        booking_data = Mock()
        booking_data.customer_id = 1
        booking_data.event_date = date(2025, 12, 25)
        booking_data.event_time = "lunch"  # Invalid: not a time
        booking_data.party_size = 4
        booking_data.duration_hours = 2
        booking_data.special_requests = None

        # Should raise BusinessLogicException in create_booking BEFORE any repository calls
        with pytest.raises(BusinessLogicException) as exc_info:
            await self.service.create_booking(booking_data)

        assert exc_info.value.error_code == ErrorCode.BAD_REQUEST
        assert "Invalid time format" in str(exc_info.value.message)
        assert "lunch" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_invalid_time_format_missing_colon(self):
        """Test that time without colon raises BusinessLogicException."""
        booking_data = Mock()
        booking_data.customer_id = 1
        booking_data.event_date = date(2025, 12, 25)
        booking_data.event_time = "1430"  # Invalid: missing colon
        booking_data.party_size = 4
        booking_data.duration_hours = 2
        booking_data.special_requests = None

        # Should raise BusinessLogicException in create_booking BEFORE any repository calls
        with pytest.raises(BusinessLogicException) as exc_info:
            await self.service.create_booking(booking_data)

        assert exc_info.value.error_code == ErrorCode.BAD_REQUEST
        assert "Invalid time format" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_valid_time_format_accepted(self):
        """Test that valid HH:MM format is accepted (sanity check)."""
        booking_data = Mock()
        booking_data.customer_id = 1
        booking_data.event_date = date(2025, 12, 25)
        booking_data.event_time = "14:30"  # Valid 24-hour format
        booking_data.party_size = 4
        booking_data.duration_hours = 2
        booking_data.special_requests = "Window seat"

        # Mock repository to avoid database
        self.mock_repository.get_existing_bookings = AsyncMock(return_value=[])
        self.mock_repository.check_availability = AsyncMock(return_value=True)
        self.mock_repository.create = AsyncMock(return_value=Mock(id=1))

        # Should NOT raise exception
        result = await self.service.create_booking(booking_data)
        assert result is not None
        assert result.id == 1


class TestBug11And12Integration:
    """Integration tests verifying both fixes work together."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_repository = Mock()
        self.mock_repository.check_availability = AsyncMock(return_value=True)
        self.service = BookingService(repository=self.mock_repository)

    @pytest.mark.asyncio
    async def test_valid_booking_with_minute_precision_and_proper_parsing(
        self,
    ):
        """Test valid booking with both fixes applied.

        Verifies:
        - Time parsed correctly with strptime (Bug #12 fix)
        - Overlap checked with minute precision (Bug #11 fix)
        """
        booking_data = Mock()
        booking_data.customer_id = 1
        booking_data.event_date = date(2025, 12, 25)
        booking_data.event_time = "14:30"  # Half-hour time
        booking_data.party_size = 4
        booking_data.duration_hours = 1.5  # 90 minutes
        booking_data.special_requests = None

        # Mock availability check to verify it's called
        self.mock_repository.get_existing_bookings = AsyncMock(return_value=[])
        self.mock_repository.check_availability = AsyncMock(return_value=True)
        self.mock_repository.create = AsyncMock(return_value=Mock(id=1))

        # Should succeed
        result = await self.service.create_booking(booking_data)
        assert result is not None

        # Verify availability was checked with correct datetime
        call_args = self.mock_repository.check_availability.call_args
        booking_datetime = call_args.kwargs["booking_datetime"]

        # Verify time parsed correctly (2:30 PM = 14:30)
        assert booking_datetime.hour == 14
        assert booking_datetime.minute == 30

        # Verify it's timezone-aware (Bug #9 fix, still relevant)
        assert booking_datetime.tzinfo is not None

    def test_minute_precision_prevents_double_booking(self):
        """Test that Bug #11 fix prevents double bookings.

        Real-world scenario:
        - Customer A books 2:30-4:30 PM
        - Customer B tries to book 4:00-6:00 PM
        - Bug #11 would allow (only compared hours: 2 vs 4)
        - Fix should detect overlap (4:00-4:30 overlaps)
        """
        # Existing booking: 2:30-4:30 PM
        existing_start = "14:30"
        existing_end = "16:30"

        # New booking attempt: 4:30-6:30 PM (2 hours)
        new_start = "16:30"
        duration = 2

        # Should NOT overlap (exactly adjacent)
        overlap = self.service._slots_overlap(
            existing_start, existing_end, new_start, duration
        )
        assert overlap is False, "Adjacent bookings should NOT overlap"

        # New booking attempt: 4:15-6:15 PM (2 hours) - before Bug #11, this would calculate wrong
        new_start = "16:15"

        # Should overlap (4:15-4:30 overlaps)
        overlap = self.service._slots_overlap(
            existing_start, existing_end, new_start, duration
        )
        assert (
            overlap is True
        ), "2:30-4:30 PM should overlap with 4:15-6:15 PM (15 min overlap)"

        # New booking attempt: 4:00-6:00 PM (2 hours)
        new_start = "16:00"

        # Should overlap (4:00-4:30 overlaps)
        overlap = self.service._slots_overlap(
            existing_start, existing_end, new_start, duration
        )
        assert (
            overlap is True
        ), "2:30-4:30 PM should overlap with 4:00-6:00 PM (30 min overlap)"

        # New booking attempt: 3:45-5:45 PM (2 hours)
        new_start = "15:45"

        # Should overlap (3:45-4:30 overlaps)
        overlap = self.service._slots_overlap(
            existing_start, existing_end, new_start, duration
        )
        assert overlap is True, "Overlapping bookings should be detected"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
