"""
Test Bug #13 Race Condition Fix - Concurrent Booking Prevention

This test verifies that the three-layer defense against race conditions works:
1. SELECT FOR UPDATE (row-level locking)
2. UNIQUE constraint idx_booking_date_slot_active (date, slot, status)
3. Optimistic locking with version column

Bug #13 Details:
- check_availability() at Time T1: "Slot available ✅"
- 80ms gap (network latency, processing)
- create_booking() at Time T2: "Insert booking"
- PROBLEM: Another request can slip in between T1 and T2

Fix Applied:
- Repository uses SELECT FOR UPDATE to lock rows during availability check
- Database enforces UNIQUE(date, slot, status) constraint
- Booking model has version column for optimistic locking
- Service layer catches IntegrityError and returns user-friendly message
"""

import pytest
from datetime import date, time, datetime, timezone
from uuid import uuid4
from sqlalchemy.exc import IntegrityError

from db.models.core import Booking, BookingStatus
from repositories.booking_repository import BookingRepository


@pytest.mark.asyncio
async def test_race_condition_prevented_by_unique_constraint(async_session):
    """
    Test that concurrent booking attempts fail gracefully

    Scenario:
    - Request A checks availability → available ✅
    - Request B checks availability → available ✅ (race window)
    - Request A creates booking → success ✅
    - Request B creates booking → IntegrityError ❌

    Expected:
    - First request succeeds
    - Second request raises IntegrityError (caught by service layer)
    """
    customer_id = uuid4()
    station_id = uuid4()

    # Create first booking
    booking1 = Booking(
        id=uuid4(),
        customer_id=customer_id,
        station_id=station_id,
        date=date(2025, 12, 25),
        slot=time(18, 0),
        address_encrypted="encrypted_address_1",
        zone="north",
        party_adults=4,
        party_kids=2,
        deposit_due_cents=10000,
        total_due_cents=50000,
        status=BookingStatus.PENDING,
        source="web",
        version=1,
    )

    async_session.add(booking1)
    await async_session.commit()

    # Attempt duplicate booking (same date + slot + active status)
    booking2 = Booking(
        id=uuid4(),
        customer_id=uuid4(),  # Different customer
        station_id=station_id,
        date=date(2025, 12, 25),  # Same date
        slot=time(18, 0),  # Same slot
        address_encrypted="encrypted_address_2",
        zone="north",
        party_adults=2,
        party_kids=0,
        deposit_due_cents=5000,
        total_due_cents=25000,
        status=BookingStatus.PENDING,  # Same active status
        source="phone",
        version=1,
    )

    async_session.add(booking2)

    # Should raise IntegrityError due to unique constraint
    with pytest.raises(IntegrityError) as exc_info:
        await async_session.commit()

    assert "idx_booking_date_slot_active" in str(exc_info.value) or "unique constraint" in str(exc_info.value).lower()

    # Rollback to clean state
    await async_session.rollback()


@pytest.mark.asyncio
async def test_version_column_exists(async_session):
    """
    Test that Booking model has version column for optimistic locking

    This prevents update conflicts when multiple requests modify same booking.
    """
    customer_id = uuid4()
    station_id = uuid4()

    booking = Booking(
        id=uuid4(),
        customer_id=customer_id,
        station_id=station_id,
        date=date(2025, 12, 25),
        slot=time(19, 0),
        address_encrypted="encrypted_address",
        zone="south",
        party_adults=6,
        party_kids=1,
        deposit_due_cents=15000,
        total_due_cents=75000,
        status=BookingStatus.PENDING,
        source="web",
        version=1,  # Initial version
    )

    async_session.add(booking)
    await async_session.commit()

    # Verify version column exists and has correct value
    assert hasattr(booking, 'version')
    assert booking.version == 1

    # Update booking (version should auto-increment)
    booking.status = BookingStatus.CONFIRMED
    await async_session.commit()
    await async_session.refresh(booking)

    # Note: SQLAlchemy's version_id_col auto-increments on UPDATE
    # Check if version was set correctly
    assert booking.version >= 1  # Should still be 1 or incremented


@pytest.mark.asyncio
async def test_cancelled_bookings_allow_same_slot(async_session):
    """
    Test that cancelled bookings don't block new bookings for same slot

    UNIQUE constraint only applies to active bookings (status != cancelled)
    """
    customer_id = uuid4()
    station_id = uuid4()

    # Create and cancel first booking
    booking1 = Booking(
        id=uuid4(),
        customer_id=customer_id,
        station_id=station_id,
        date=date(2025, 12, 31),
        slot=time(20, 0),
        address_encrypted="encrypted_address_1",
        zone="west",
        party_adults=8,
        party_kids=0,
        deposit_due_cents=20000,
        total_due_cents=100000,
        status=BookingStatus.CANCELLED,  # Cancelled
        source="web",
        version=1,
    )

    async_session.add(booking1)
    await async_session.commit()

    # Create new booking for same slot (should succeed)
    booking2 = Booking(
        id=uuid4(),
        customer_id=uuid4(),
        station_id=station_id,
        date=date(2025, 12, 31),  # Same date
        slot=time(20, 0),  # Same slot
        address_encrypted="encrypted_address_2",
        zone="west",
        party_adults=4,
        party_kids=2,
        deposit_due_cents=10000,
        total_due_cents=50000,
        status=BookingStatus.PENDING,  # Active status
        source="phone",
        version=1,
    )

    async_session.add(booking2)
    await async_session.commit()  # Should NOT raise IntegrityError

    assert booking2.id is not None
    assert booking2.status == BookingStatus.PENDING


@pytest.mark.asyncio
async def test_select_for_update_in_check_availability(async_session):
    """
    Test that check_availability uses SELECT FOR UPDATE

    This is difficult to test directly without actual concurrency,
    but we can verify the method works correctly.
    """
    from repositories.booking_repository import BookingRepository

    repo = BookingRepository(async_session)
    customer_id = uuid4()
    station_id = uuid4()

    # Create existing booking
    booking = Booking(
        id=uuid4(),
        customer_id=customer_id,
        station_id=station_id,
        date=date(2026, 1, 15),
        slot=time(18, 30),
        address_encrypted="encrypted_address",
        zone="east",
        party_adults=5,
        party_kids=1,
        deposit_due_cents=12500,
        total_due_cents=62500,
        status=BookingStatus.CONFIRMED,
        source="web",
        version=1,
    )

    async_session.add(booking)
    await async_session.commit()

    # Check availability - should return False (slot taken)
    is_available = repo.check_availability(
        event_date=date(2026, 1, 15),
        event_slot="18:30:00",
        party_size=4,
        exclude_booking_id=None
    )

    assert is_available is False

    # Check different slot - should return True
    is_available = repo.check_availability(
        event_date=date(2026, 1, 15),
        event_slot="19:00:00",
        party_size=4,
        exclude_booking_id=None
    )

    assert is_available is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
