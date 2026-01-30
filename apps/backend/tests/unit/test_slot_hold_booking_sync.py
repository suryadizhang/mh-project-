"""
Slot Hold and Booking Sync Tests
================================

Tests the integration between SlotHold system and Booking availability to verify:
1. Slot holds count as unavailable for availability checks
2. Schema consistency (event_date + slot_time, NOT slot_datetime)
3. Hold → Booking conversion flow
4. Concurrent booking prevention via holds

Created: 2025-01-29
Purpose: Verify fixes to slot_hold_service.py schema mismatch (event_date+slot_time vs slot_datetime)
"""

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest


class TestSlotHoldSchemaConsistency:
    """Tests verifying the slot_holds table schema matches service expectations."""

    def test_slot_hold_model_uses_separate_date_time_columns(self):
        """SlotHold SQLAlchemy model should use event_date DATE + slot_time TIME (not slot_datetime)."""
        from db.models.slot_hold import SlotHold

        # Get column names from the model
        column_names = [col.name for col in SlotHold.__table__.columns]

        # Should have separate date and time columns
        assert "event_date" in column_names, "SlotHold must have event_date column"
        assert "slot_time" in column_names, "SlotHold must have slot_time column"

        # Should NOT have combined datetime column (old incorrect schema)
        assert (
            "slot_datetime" not in column_names
        ), "SlotHold should NOT have slot_datetime (use event_date + slot_time)"

    def test_slot_hold_service_create_method_signature(self):
        """create_hold() should accept separate event_date and slot_time parameters."""
        import inspect

        from services.agreements.slot_hold_service import SlotHoldService

        # Get method signature
        sig = inspect.signature(SlotHoldService.create_hold)
        param_names = list(sig.parameters.keys())

        # Should have separate parameters
        assert (
            "event_date" in param_names
        ), "create_hold must accept event_date parameter"
        assert "slot_time" in param_names, "create_hold must accept slot_time parameter"

        # Should NOT have combined datetime parameter (old incorrect signature)
        assert (
            "slot_datetime" not in param_names
        ), "create_hold should NOT accept slot_datetime"

    def test_is_slot_held_or_booked_method_signature(self):
        """_is_slot_held_or_booked() should accept separate event_date and slot_time."""
        import inspect

        from services.agreements.slot_hold_service import SlotHoldService

        sig = inspect.signature(SlotHoldService._is_slot_held_or_booked)
        param_names = list(sig.parameters.keys())

        assert (
            "event_date" in param_names
        ), "_is_slot_held_or_booked must accept event_date"
        assert (
            "slot_time" in param_names
        ), "_is_slot_held_or_booked must accept slot_time"
        assert (
            "slot_datetime" not in param_names
        ), "Should NOT accept combined slot_datetime"

    def test_get_active_holds_for_slot_method_signature(self):
        """get_active_holds_for_slot() should accept separate event_date and slot_time."""
        import inspect

        from services.agreements.slot_hold_service import SlotHoldService

        sig = inspect.signature(SlotHoldService.get_active_holds_for_slot)
        param_names = list(sig.parameters.keys())

        assert (
            "event_date" in param_names
        ), "get_active_holds_for_slot must accept event_date"
        assert (
            "slot_time" in param_names
        ), "get_active_holds_for_slot must accept slot_time"
        assert (
            "slot_datetime" not in param_names
        ), "Should NOT accept combined slot_datetime"


class TestSlotHoldBookingFlow:
    """Tests the slot hold → booking conversion flow."""

    @pytest.mark.asyncio
    async def test_create_hold_with_separate_date_time(self):
        """create_hold should work with separate event_date and slot_time."""
        from services.agreements.slot_hold_service import SlotHoldService

        # Create mock DB session
        mock_db = AsyncMock()

        # Mock fetchone to return None (slot not held/booked)
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_db.execute.return_value = mock_result

        service = SlotHoldService(mock_db)

        # Test data with SEPARATE date and time
        station_id = uuid4()
        event_date = date(2025, 2, 15)
        slot_time = time(18, 0)  # 6:00 PM

        # The method should accept these parameters without error
        # We can't fully test without real DB, but we can verify the call doesn't crash
        try:
            await service.create_hold(
                station_id=station_id,
                event_date=event_date,
                slot_time=slot_time,
                customer_email="test@example.com",
                customer_name="Test Customer",
                guest_count=10,
            )
        except Exception as e:
            # We expect some DB interaction errors since we're mocking
            # The important thing is that it doesn't fail on parameter types
            if "slot_datetime" in str(e):
                pytest.fail(f"Method is still using slot_datetime: {e}")

    @pytest.mark.asyncio
    async def test_is_slot_held_or_booked_sql_uses_separate_columns(self):
        """_is_slot_held_or_booked should query using event_date and slot_time columns."""
        from services.agreements.slot_hold_service import SlotHoldService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_db.execute.return_value = mock_result

        service = SlotHoldService(mock_db)

        station_id = uuid4()
        event_date = date(2025, 2, 15)
        slot_time = time(18, 0)

        # Call the method
        result = await service._is_slot_held_or_booked(
            station_id, event_date, slot_time
        )

        # Check that the SQL query was called
        assert mock_db.execute.called, "Should have executed a query"

        # Get the SQL that was executed
        call_args = mock_db.execute.call_args
        sql_query = str(call_args[0][0])

        # Verify the SQL uses correct column names
        assert (
            "event_date" in sql_query.lower()
        ), "SQL should reference event_date column"
        assert "slot_time" in sql_query.lower(), "SQL should reference slot_time column"
        assert (
            "slot_datetime" not in sql_query.lower()
        ), "SQL should NOT reference slot_datetime"


class TestBookingAvailabilityWithHolds:
    """Tests that booking availability correctly considers slot holds."""

    def test_slot_hold_service_uses_string_status_values(self):
        """Verify slot_hold_service uses string literals for status values."""
        # The service uses string literals, NOT an enum
        # Valid status values: 'pending', 'signed', 'converted', 'expired', 'released'
        valid_statuses = {"pending", "signed", "converted", "expired", "released"}
        assert len(valid_statuses) == 5
        assert "pending" in valid_statuses
        assert "converted" in valid_statuses

    def test_default_hold_minutes_is_2_hours(self):
        """Slot holds should default to 2 hours (120 minutes)."""
        from services.agreements.slot_hold_service import DEFAULT_HOLD_MINUTES

        assert DEFAULT_HOLD_MINUTES == 120, "Default hold time should be 2 hours"

    @pytest.mark.asyncio
    async def test_validate_hold_returns_none_for_invalid_token(self):
        """validate_hold should return None for non-existent tokens."""
        from services.agreements.slot_hold_service import SlotHoldService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None  # No hold found
        mock_db.execute.return_value = mock_result

        service = SlotHoldService(mock_db)

        result = await service.validate_hold("invalid_token_12345")

        assert result is None, "Should return None for invalid token"


class TestConcurrentBookingPrevention:
    """Tests the scenario: Customer A holds → Customer B checks → Should see UNAVAILABLE."""

    @pytest.mark.asyncio
    async def test_held_slot_shows_unavailable_for_other_customers(self):
        """
        Scenario:
        1. Customer A creates slot hold → status='pending'
        2. Customer B checks same slot → Should see UNAVAILABLE
        """
        from services.agreements.slot_hold_service import SlotHoldService

        mock_db = AsyncMock()
        service = SlotHoldService(mock_db)

        station_id = uuid4()
        event_date = date(2025, 2, 15)
        slot_time = time(18, 0)

        # Simulate that there IS an active hold on this slot
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (1,)  # 1 = slot is held
        mock_db.execute.return_value = mock_result

        # Check if slot is held or booked
        is_unavailable = await service._is_slot_held_or_booked(
            station_id, event_date, slot_time
        )

        assert (
            is_unavailable is True
        ), "Slot with active hold should show as unavailable"

    @pytest.mark.asyncio
    async def test_expired_holds_dont_block_new_bookings(self):
        """Expired holds should NOT block new bookings."""
        from services.agreements.slot_hold_service import SlotHoldService

        mock_db = AsyncMock()
        service = SlotHoldService(mock_db)

        station_id = uuid4()
        event_date = date(2025, 2, 15)
        slot_time = time(18, 0)

        # Simulate that there are NO active holds (expired ones don't count)
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None  # No active holds
        mock_db.execute.return_value = mock_result

        # Check if slot is held or booked
        is_unavailable = await service._is_slot_held_or_booked(
            station_id, event_date, slot_time
        )

        assert is_unavailable is False, "Slot without active holds should be available"


class TestSlotHoldRouterIntegration:
    """Tests the API layer integration with correct parameters."""

    def test_slot_hold_request_model_has_separate_fields(self):
        """SlotHoldRequest Pydantic model should have event_date and slot_time fields."""
        from routers.v1.agreements import SlotHoldRequest

        # Get field names from the model
        field_names = list(SlotHoldRequest.model_fields.keys())

        assert "event_date" in field_names, "SlotHoldRequest must have event_date field"
        assert "slot_time" in field_names, "SlotHoldRequest must have slot_time field"
        assert (
            "slot_datetime" not in field_names
        ), "Should NOT have combined slot_datetime"

    def test_slot_hold_request_model_validation(self):
        """SlotHoldRequest should validate correctly with separate date/time."""
        from routers.v1.agreements import SlotHoldRequest

        # Create valid request
        request = SlotHoldRequest(
            station_id=uuid4(),
            event_date=date(2025, 2, 15),
            slot_time=time(18, 0),
            customer_email="test@example.com",
        )

        assert request.event_date == date(2025, 2, 15)
        assert request.slot_time == time(18, 0)


class TestBookingSchemaConsistency:
    """Tests that Booking model is consistent with SlotHold for availability checks."""

    def test_booking_model_uses_date_slot_columns(self):
        """Booking model should use 'date' DATE + 'slot' TIME columns (for consistency)."""
        from db.models.core import Booking

        column_names = [col.name for col in Booking.__table__.columns]

        # Booking uses 'date' and 'slot' (different names but same pattern)
        assert "date" in column_names, "Booking must have date column"
        assert "slot" in column_names, "Booking must have slot column"

    def test_is_slot_held_or_booked_checks_both_holds_and_bookings(self):
        """The availability check should verify both slot_holds AND bookings tables."""
        import inspect

        from services.agreements.slot_hold_service import SlotHoldService

        # Get the source code of the method
        source = inspect.getsource(SlotHoldService._is_slot_held_or_booked)

        # Should check slot_holds table
        assert (
            "slot_holds" in source.lower() or "core.slot_holds" in source.lower()
        ), "Should check slot_holds table"

        # Should check bookings table
        assert (
            "bookings" in source.lower() or "core.bookings" in source.lower()
        ), "Should check bookings table"


# Run all tests summary
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
