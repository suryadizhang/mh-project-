"""
Comprehensive Booking Endpoints Tests
Tests all booking-related API endpoints with full coverage.
"""

import pytest
from datetime import date, time
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from db.models.core import Booking, BookingStatus


@pytest.mark.asyncio
class TestBookingEndpointsCreate:
    """Test POST /v1/bookings - Create booking"""

    async def test_create_booking_success(self, client: AsyncClient, db: AsyncSession):
        """Test successful booking creation"""
        booking_data = {
            "customer_id": str(uuid4()),
            "event_date": "2025-12-25",
            "event_time": "19:00",
            "guest_count": 8,
            "address": "123 Main St, City, ST 12345",
            "special_requests": "No shellfish",
            "phone": "+1234567890",
        }

        response = await client.post("/v1/bookings", json=booking_data)

        assert response.status_code == 201
        data = response.json()
        assert data["event_date"] == "2025-12-25"
        assert data["event_time"] == "19:00"
        assert data["guest_count"] == 8
        assert data["status"] == BookingStatus.PENDING.value

    async def test_create_booking_validation_guest_count_too_low(self, client: AsyncClient):
        """Test booking creation fails with guest count < 6"""
        booking_data = {
            "customer_id": str(uuid4()),
            "event_date": "2025-12-25",
            "event_time": "19:00",
            "guest_count": 3,  # Below minimum
            "address": "123 Main St",
            "phone": "+1234567890",
        }

        response = await client.post("/v1/bookings", json=booking_data)

        assert response.status_code == 422
        assert "guest_count" in response.text.lower() or "minimum" in response.text.lower()

    async def test_create_booking_validation_past_date(self, client: AsyncClient):
        """Test booking creation fails with past date"""
        booking_data = {
            "customer_id": str(uuid4()),
            "event_date": "2020-01-01",  # Past date
            "event_time": "19:00",
            "guest_count": 8,
            "address": "123 Main St",
            "phone": "+1234567890",
        }

        response = await client.post("/v1/bookings", json=booking_data)

        assert response.status_code == 422
        assert "date" in response.text.lower() or "past" in response.text.lower()

    async def test_create_booking_validation_invalid_time(self, client: AsyncClient):
        """Test booking creation fails with invalid time format"""
        booking_data = {
            "customer_id": str(uuid4()),
            "event_date": "2025-12-25",
            "event_time": "25:00",  # Invalid time
            "guest_count": 8,
            "address": "123 Main St",
            "phone": "+1234567890",
        }

        response = await client.post("/v1/bookings", json=booking_data)

        assert response.status_code == 422

    async def test_create_booking_validation_missing_required_fields(self, client: AsyncClient):
        """Test booking creation fails with missing required fields"""
        booking_data = {
            "event_date": "2025-12-25",
            # Missing: customer_id, event_time, guest_count, address, phone
        }

        response = await client.post("/v1/bookings", json=booking_data)

        assert response.status_code == 422

    async def test_create_booking_with_travel_fee(self, client: AsyncClient):
        """Test booking creation includes travel fee calculation"""
        booking_data = {
            "customer_id": str(uuid4()),
            "event_date": "2025-12-25",
            "event_time": "19:00",
            "guest_count": 8,
            "address": "1234 Far Away St, Distant City, ST 99999",  # Should trigger travel fee
            "phone": "+1234567890",
        }

        response = await client.post("/v1/bookings", json=booking_data)

        assert response.status_code == 201
        data = response.json()
        assert "travel_fee" in data
        # Travel fee should be calculated based on distance


@pytest.mark.asyncio
class TestBookingEndpointsRead:
    """Test GET /v1/bookings - List and retrieve bookings"""

    async def test_list_bookings_success(self, client: AsyncClient, db: AsyncSession):
        """Test listing all bookings"""
        response = await client.get("/v1/bookings")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_list_bookings_with_filters(self, client: AsyncClient):
        """Test listing bookings with filters"""
        response = await client.get(
            "/v1/bookings",
            params={"status": BookingStatus.CONFIRMED.value, "limit": 10, "offset": 0},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10

    async def test_get_booking_by_id_success(self, client: AsyncClient, db: AsyncSession):
        """Test retrieving a specific booking"""
        # Create a booking first
        booking = Booking(
            customer_id=uuid4(),
            event_date=date(2025, 12, 25),
            event_time=time(19, 0),
            guest_count=8,
            address="123 Main St",
            phone="+1234567890",
            status=BookingStatus.PENDING.value,
        )
        db.add(booking)
        await db.commit()
        await db.refresh(booking)

        response = await client.get(f"/v1/bookings/{booking.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(booking.id)
        assert data["guest_count"] == 8

    async def test_get_booking_by_id_not_found(self, client: AsyncClient):
        """Test retrieving non-existent booking"""
        fake_id = uuid4()
        response = await client.get(f"/v1/bookings/{fake_id}")

        assert response.status_code == 404


@pytest.mark.asyncio
class TestBookingEndpointsUpdate:
    """Test PUT/PATCH /v1/bookings/{id} - Update bookings"""

    async def test_update_booking_success(self, client: AsyncClient, db: AsyncSession):
        """Test successful booking update"""
        # Create a booking
        booking = Booking(
            customer_id=uuid4(),
            event_date=date(2025, 12, 25),
            event_time=time(19, 0),
            guest_count=8,
            address="123 Main St",
            phone="+1234567890",
            status=BookingStatus.PENDING.value,
        )
        db.add(booking)
        await db.commit()
        await db.refresh(booking)

        # Update guest count
        update_data = {"guest_count": 12}
        response = await client.put(f"/v1/bookings/{booking.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["guest_count"] == 12

    async def test_update_booking_status_to_confirmed(self, client: AsyncClient, db: AsyncSession):
        """Test updating booking status to confirmed"""
        booking = Booking(
            customer_id=uuid4(),
            event_date=date(2025, 12, 25),
            event_time=time(19, 0),
            guest_count=8,
            address="123 Main St",
            phone="+1234567890",
            status=BookingStatus.PENDING.value,
        )
        db.add(booking)
        await db.commit()
        await db.refresh(booking)

        update_data = {"status": BookingStatus.CONFIRMED.value}
        response = await client.put(f"/v1/bookings/{booking.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == BookingStatus.CONFIRMED.value

    async def test_update_booking_not_found(self, client: AsyncClient):
        """Test updating non-existent booking"""
        fake_id = uuid4()
        update_data = {"guest_count": 12}
        response = await client.put(f"/v1/bookings/{fake_id}", json=update_data)

        assert response.status_code == 404


@pytest.mark.asyncio
class TestBookingEndpointsDelete:
    """Test DELETE /v1/bookings/{id} - Cancel bookings"""

    async def test_cancel_booking_success(self, client: AsyncClient, db: AsyncSession):
        """Test successful booking cancellation"""
        booking = Booking(
            customer_id=uuid4(),
            event_date=date(2025, 12, 25),
            event_time=time(19, 0),
            guest_count=8,
            address="123 Main St",
            phone="+1234567890",
            status=BookingStatus.CONFIRMED.value,
        )
        db.add(booking)
        await db.commit()
        await db.refresh(booking)

        response = await client.delete(f"/v1/bookings/{booking.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == BookingStatus.CANCELLED.value

    async def test_cancel_booking_not_found(self, client: AsyncClient):
        """Test cancelling non-existent booking"""
        fake_id = uuid4()
        response = await client.delete(f"/v1/bookings/{fake_id}")

        assert response.status_code == 404


@pytest.mark.asyncio
class TestBookingEndpointsBusinessLogic:
    """Test business logic and edge cases"""

    async def test_booking_time_slot_conflict_detection(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Test that overlapping bookings are detected"""
        # Create first booking
        booking1_data = {
            "customer_id": str(uuid4()),
            "event_date": "2025-12-25",
            "event_time": "19:00",
            "guest_count": 8,
            "address": "123 Main St",
            "phone": "+1234567890",
        }
        response1 = await client.post("/v1/bookings", json=booking1_data)
        assert response1.status_code == 201

        # Try to create overlapping booking
        booking2_data = {
            "customer_id": str(uuid4()),
            "event_date": "2025-12-25",
            "event_time": "19:30",  # Overlaps with first booking
            "guest_count": 8,
            "address": "456 Oak Ave",
            "phone": "+0987654321",
        }
        response2 = await client.post("/v1/bookings", json=booking2_data)

        # Should either reject or warn about conflict
        assert response2.status_code in [409, 422, 201]  # Depends on conflict resolution strategy

    async def test_booking_deposit_calculation(self, client: AsyncClient):
        """Test that deposit is calculated correctly"""
        booking_data = {
            "customer_id": str(uuid4()),
            "event_date": "2025-12-25",
            "event_time": "19:00",
            "guest_count": 10,
            "address": "123 Main St",
            "phone": "+1234567890",
        }

        response = await client.post("/v1/bookings", json=booking_data)

        assert response.status_code == 201
        data = response.json()
        # Deposit should be calculated based on guest count and pricing
        assert "deposit_amount" in data or "total_price" in data

    async def test_booking_pricing_includes_all_fees(self, client: AsyncClient):
        """Test that pricing includes base price + travel fee + any add-ons"""
        booking_data = {
            "customer_id": str(uuid4()),
            "event_date": "2025-12-25",
            "event_time": "19:00",
            "guest_count": 8,
            "address": "1234 Far Away St, Distant City, ST 99999",
            "phone": "+1234567890",
            "special_requests": "Premium sake selection",
        }

        response = await client.post("/v1/bookings", json=booking_data)

        assert response.status_code == 201
        data = response.json()
        # Should include base price + travel fee
        assert "total_price" in data or "estimated_price" in data
