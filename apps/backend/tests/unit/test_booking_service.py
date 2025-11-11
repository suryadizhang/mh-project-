"""
Unit Tests for BookingService
Test service layer business logic, caching, and validation
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date, datetime, timedelta
from uuid import uuid4

# Phase 2B: Updated import to NEW location
from services.booking_service import BookingService
from models.booking import Booking, BookingStatus
from schemas.booking import BookingCreate
from core.exceptions import (
    NotFoundException,
    BusinessLogicException,
    ConflictException,
)


@pytest.fixture
def mock_repository():
    """Create mock booking repository"""
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_cache():
    """Create mock cache service"""
    cache = AsyncMock()
    return cache


@pytest.fixture
def booking_service(mock_repository, mock_cache):
    """Create booking service with mocks"""
    return BookingService(mock_repository, mock_cache)


@pytest.fixture
def sample_customer_id():
    """Sample customer UUID"""
    return uuid4()


@pytest.fixture
def sample_booking(sample_customer_id):
    """Create mock Booking object with correct field names matching Booking model"""
    booking = MagicMock(spec=Booking)
    booking.id = uuid4()
    booking.customer_id = sample_customer_id
    # Booking model uses booking_datetime (not event_date/event_time)
    booking.booking_datetime = datetime.now() + timedelta(days=7, hours=18)
    booking.party_size = 4
    booking.status = BookingStatus.PENDING
    booking.contact_phone = "+15551234567"
    booking.contact_email = "john@example.com"
    booking.special_requests = "Window seat preferred"
    booking.created_at = datetime.now()
    booking.updated_at = datetime.now()
    booking.confirmed_at = None
    booking.seated_at = None
    booking.completed_at = None
    booking.cancelled_at = None
    booking.cancellation_reason = None
    booking.table_number = None
    booking.internal_notes = None

    # Add event_date and event_time for compatibility with service methods that use these
    booking.event_date = booking.booking_datetime.date()
    booking.event_time = booking.booking_datetime.strftime("%H:%M")

    return booking


@pytest.fixture
def sample_booking_create(sample_customer_id):
    """Create sample BookingCreate schema"""
    return BookingCreate(
        customer_id=sample_customer_id,
        event_date=date.today() + timedelta(days=7),
        event_time="18:00",
        party_size=4,
        contact_phone="+15551234567",
        contact_email="john@example.com",
        special_requests="Window seat preferred",
        duration_hours=2,
    )


@pytest.mark.asyncio
class TestBookingServiceCRUD:
    """Test basic CRUD operations"""

    async def test_get_booking_by_id_found(
        self, booking_service, mock_repository, sample_booking
    ):
        """Test getting booking by ID - found"""
        # Setup
        mock_repository.get_by_id = AsyncMock(return_value=sample_booking)

        # Execute
        result = await booking_service.get_booking_by_id(sample_booking.id)

        # Verify
        assert result == sample_booking
        assert result.id == sample_booking.id
        assert result.status == BookingStatus.PENDING
        mock_repository.get_by_id.assert_called_once_with(sample_booking.id)

    async def test_get_booking_by_id_not_found(
        self, booking_service, mock_repository
    ):
        """Test getting booking by ID - not found"""
        test_id = uuid4()
        mock_repository.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(NotFoundException) as exc:
            await booking_service.get_booking_by_id(test_id)

        assert str(test_id) in str(exc.value)
        assert "Booking" in str(exc.value)

    async def test_create_booking_success(
        self,
        booking_service,
        mock_repository,
        mock_cache,
        sample_booking_create,
        sample_booking,
    ):
        """Test creating booking with valid data"""
        # Setup - mock availability check and repository create
        mock_repository.check_availability = AsyncMock(return_value=True)
        mock_repository.find_by_customer_and_date = AsyncMock(return_value=[])
        mock_repository.create = AsyncMock(return_value=sample_booking)

        # Execute
        with patch(
            "services.lead_service.LeadService"
        ) as mock_lead_service_class:
            mock_lead_instance = AsyncMock()
            mock_lead_service_class.return_value = mock_lead_instance
            result = await booking_service.create_booking(
                sample_booking_create
            )

        # Verify
        assert result.id == sample_booking.id
        assert result.status == BookingStatus.PENDING
        assert result.party_size == 4
        mock_repository.check_availability.assert_called_once()
        mock_repository.create.assert_called_once()
        # Cache should be invalidated
        mock_cache.delete_pattern.assert_called_with("booking:*")

    async def test_create_booking_slot_not_available(
        self, booking_service, mock_repository, sample_booking_create
    ):
        """Test creating booking when time slot is not available"""
        # Setup
        mock_repository.check_availability = AsyncMock(return_value=False)

        # Execute & Verify
        with patch(
            "services.lead_service.LeadService"
        ) as mock_lead_service_class:
            mock_lead_instance = AsyncMock()
            mock_lead_service_class.return_value = mock_lead_instance
            with pytest.raises(ConflictException) as exc:
                await booking_service.create_booking(sample_booking_create)

        assert "not available" in str(exc.value).lower()
        assert sample_booking_create.event_time in str(exc.value)

    async def test_create_booking_duplicate(
        self,
        booking_service,
        mock_repository,
        sample_booking_create,
        sample_booking,
    ):
        """Test creating duplicate booking (same customer, date, time)"""
        # Setup
        mock_repository.check_availability = AsyncMock(return_value=True)
        # Return list with existing booking (service checks for non-empty list)
        mock_repository.find_by_customer_and_date = AsyncMock(
            return_value=[sample_booking]
        )

        # Mock _check_duplicate_booking to return the existing booking
        async def mock_check_duplicate(customer_id, event_date, event_time):
            return sample_booking  # Return existing booking

        booking_service._check_duplicate_booking = mock_check_duplicate

        # Execute & Verify
        with patch(
            "services.lead_service.LeadService"
        ) as mock_lead_service_class:
            mock_lead_instance = AsyncMock()
            mock_lead_service_class.return_value = mock_lead_instance
            with pytest.raises(ConflictException) as exc:
                await booking_service.create_booking(sample_booking_create)

        assert "already exists" in str(exc.value).lower()


@pytest.mark.asyncio
class TestBookingServiceBusinessLogic:
    """Test business logic methods"""

    async def test_confirm_booking_success(
        self, booking_service, mock_repository, mock_cache, sample_booking
    ):
        """Test confirming a pending booking"""
        # Setup
        sample_booking.status = BookingStatus.PENDING

        # Create confirmed booking instance (not AsyncMock, actual mock with attributes)
        confirmed_booking = MagicMock(spec=Booking)
        confirmed_booking.id = sample_booking.id
        confirmed_booking.customer_id = sample_booking.customer_id
        confirmed_booking.booking_datetime = sample_booking.booking_datetime
        confirmed_booking.party_size = sample_booking.party_size
        confirmed_booking.status = BookingStatus.CONFIRMED
        confirmed_booking.confirmed_at = datetime.now()
        confirmed_booking.contact_phone = sample_booking.contact_phone
        confirmed_booking.contact_email = sample_booking.contact_email
        confirmed_booking.special_requests = sample_booking.special_requests

        mock_repository.get_by_id = AsyncMock(return_value=sample_booking)
        mock_repository.update = AsyncMock(return_value=confirmed_booking)

        # Execute
        result = await booking_service.confirm_booking(sample_booking.id)

        # Verify
        assert result.status == BookingStatus.CONFIRMED
        mock_repository.update.assert_called_once()
        mock_cache.delete_pattern.assert_called_with("booking:*")

    async def test_confirm_booking_already_confirmed(
        self, booking_service, mock_repository, sample_booking
    ):
        """Test confirming already confirmed booking"""
        sample_booking.status = BookingStatus.CONFIRMED
        mock_repository.get_by_id = AsyncMock(return_value=sample_booking)

        with pytest.raises(BusinessLogicException) as exc:
            await booking_service.confirm_booking(sample_booking.id)

        assert "cannot confirm" in str(exc.value).lower()

    async def test_cancel_booking_success(
        self, booking_service, mock_repository, mock_cache, sample_booking
    ):
        """Test canceling a booking"""
        sample_booking.status = BookingStatus.CONFIRMED

        # Create cancelled booking instance (not AsyncMock, actual mock with attributes)
        cancelled_booking = MagicMock(spec=Booking)
        cancelled_booking.id = sample_booking.id
        cancelled_booking.customer_id = sample_booking.customer_id
        cancelled_booking.booking_datetime = sample_booking.booking_datetime
        cancelled_booking.party_size = sample_booking.party_size
        cancelled_booking.status = BookingStatus.CANCELLED
        cancelled_booking.cancelled_at = datetime.now()
        cancelled_booking.contact_phone = sample_booking.contact_phone
        cancelled_booking.contact_email = sample_booking.contact_email
        # Add event_date and event_time for compatibility
        cancelled_booking.event_date = (
            cancelled_booking.booking_datetime.date()
        )
        cancelled_booking.event_time = (
            cancelled_booking.booking_datetime.strftime("%H:%M")
        )

        mock_repository.get_by_id = AsyncMock(return_value=sample_booking)
        mock_repository.update = AsyncMock(return_value=cancelled_booking)

        result = await booking_service.cancel_booking(sample_booking.id)

        assert result.status == BookingStatus.CANCELLED
        mock_cache.delete_pattern.assert_called_with("booking:*")

    async def test_cancel_already_cancelled(
        self, booking_service, mock_repository, sample_booking
    ):
        """Test canceling already cancelled booking"""
        sample_booking.status = BookingStatus.CANCELLED
        mock_repository.get_by_id = AsyncMock(return_value=sample_booking)

        with pytest.raises(BusinessLogicException) as exc:
            await booking_service.cancel_booking(sample_booking.id)

        assert (
            "cannot cancel" in str(exc.value).lower()
            or "already" in str(exc.value).lower()
        )


@pytest.mark.asyncio
class TestBookingServiceCaching:
    """Test caching behavior"""

    async def test_get_dashboard_stats_cached(
        self, booking_service, mock_repository, mock_cache
    ):
        """Test dashboard stats are cached - decorator handles caching"""
        # Setup - mock repository to return bookings (use MagicMock to avoid SQLAlchemy)
        sample_bookings = []
        for _ in range(10):
            booking = MagicMock(spec=Booking)
            booking.id = uuid4()
            booking.customer_id = uuid4()
            booking.booking_datetime = datetime.now() + timedelta(days=7)
            booking.party_size = 4
            booking.status = BookingStatus.CONFIRMED
            # Service uses total_amount (not total_spent)
            booking.total_amount = 100.0  # Use total_amount
            sample_bookings.append(booking)

        # Mock the repository method
        mock_repository.find_by_date_range = AsyncMock(
            return_value=sample_bookings
        )

        # Mock cache to return None (cache miss, so service computes stats)
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock(return_value=None)

        # Execute
        result = await booking_service.get_dashboard_stats()

        # Verify - the result should be a dictionary with stats
        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        assert "total_bookings" in result
        assert "confirmed_bookings" in result or "total_revenue" in result
        # The service should have called the repository
        mock_repository.find_by_date_range.assert_called_once()

    async def test_cache_invalidation_on_create(
        self,
        booking_service,
        mock_repository,
        mock_cache,
        sample_booking_create,
        sample_booking,
    ):
        """Test cache is invalidated on create"""
        # Setup
        mock_repository.check_availability = AsyncMock(return_value=True)
        mock_repository.find_by_customer_and_date = AsyncMock(return_value=[])
        mock_repository.create = AsyncMock(return_value=sample_booking)

        # Execute
        with patch(
            "services.lead_service.LeadService"
        ) as mock_lead_service_class:
            mock_lead_instance = AsyncMock()
            mock_lead_service_class.return_value = mock_lead_instance
            await booking_service.create_booking(sample_booking_create)

        # Verify cache invalidation
        mock_cache.delete_pattern.assert_called_with("booking:*")


@pytest.mark.asyncio
class TestBookingServiceValidation:
    """Test input validation with validators"""

    async def test_validate_phone_invalid_format(
        self, booking_service, mock_repository, sample_customer_id
    ):
        """Test invalid phone format is rejected"""
        # Create booking with invalid phone (not E.164)
        booking_data = BookingCreate(
            customer_id=sample_customer_id,
            event_date=date.today() + timedelta(days=7),
            event_time="18:00",
            party_size=4,
            contact_phone="123-456-7890",  # Not E.164 format (no +)
            contact_email="john@example.com",
        )

        mock_repository.check_availability = AsyncMock(return_value=True)

        with patch(
            "services.lead_service.LeadService"
        ) as mock_lead_service_class:
            mock_lead_instance = AsyncMock()
            mock_lead_service_class.return_value = mock_lead_instance
            with pytest.raises(BusinessLogicException) as exc:
                await booking_service.create_booking(booking_data)

        assert "phone" in str(exc.value).lower()

    async def test_validate_email_invalid_format(
        self, booking_service, mock_repository, sample_customer_id
    ):
        """Test invalid email format is rejected"""
        # Pydantic will catch this at schema level, but test it anyway
        with pytest.raises(Exception):  # Pydantic ValidationError
            BookingCreate(
                customer_id=sample_customer_id,
                event_date=date.today() + timedelta(days=7),
                event_time="18:00",
                party_size=4,
                contact_phone="+15551234567",
                contact_email="not-an-email",  # Invalid
            )

    async def test_validate_guest_count_valid(
        self,
        booking_service,
        mock_repository,
        sample_customer_id,
        sample_booking,
    ):
        """Test valid guest counts are accepted"""
        for count in [1, 4, 10, 25, 50]:
            booking_data = BookingCreate(
                customer_id=sample_customer_id,
                event_date=date.today() + timedelta(days=7),
                event_time="18:00",
                party_size=count,
                contact_phone="+15551234567",
            )

            mock_repository.check_availability = AsyncMock(return_value=True)
            mock_repository.find_by_customer_and_date = AsyncMock(
                return_value=[]
            )
            mock_repository.create = AsyncMock(return_value=sample_booking)

            with patch(
                "services.lead_service.LeadService"
            ) as mock_lead_service_class:
                mock_lead_instance = AsyncMock()
                mock_lead_service_class.return_value = mock_lead_instance
                result = await booking_service.create_booking(booking_data)

            assert result is not None

    async def test_validate_guest_count_invalid(self, sample_customer_id):
        """Test invalid guest counts are rejected by schema"""
        # Test party size too small
        with pytest.raises(Exception):  # Pydantic ValidationError
            BookingCreate(
                customer_id=sample_customer_id,
                event_date=date.today() + timedelta(days=7),
                event_time="18:00",
                party_size=0,  # Invalid
            )

        # Test party size too large
        with pytest.raises(Exception):  # Pydantic ValidationError
            BookingCreate(
                customer_id=sample_customer_id,
                event_date=date.today() + timedelta(days=7),
                event_time="18:00",
                party_size=100,  # Invalid (max is 50)
            )

    async def test_validate_past_date_rejected(self, sample_customer_id):
        """Test booking with past date is rejected"""
        with pytest.raises(Exception):  # Pydantic ValidationError
            BookingCreate(
                customer_id=sample_customer_id,
                event_date=date.today() - timedelta(days=1),  # Past date
                event_time="18:00",
                party_size=4,
            )


@pytest.mark.asyncio
class TestBookingServiceCustomerBookings:
    """Test customer booking queries"""

    async def test_get_customer_bookings(
        self, booking_service, mock_repository, sample_customer_id
    ):
        """Test getting all bookings for a customer"""
        # Setup - use MagicMock to avoid SQLAlchemy init
        bookings = []
        for i in range(1, 4):
            booking = MagicMock(spec=Booking)
            booking.id = uuid4()
            booking.customer_id = sample_customer_id
            booking.booking_datetime = datetime.now() + timedelta(
                days=i, hours=18
            )
            booking.party_size = 4
            booking.status = BookingStatus.CONFIRMED
            # Add event_date and event_time for compatibility
            booking.event_date = booking.booking_datetime.date()
            booking.event_time = booking.booking_datetime.strftime("%H:%M")
            bookings.append(booking)

        mock_repository.find_by_customer = AsyncMock(return_value=bookings)

        # Execute
        result = await booking_service.get_customer_bookings(
            sample_customer_id
        )

        # Verify
        assert len(result) == 3
        assert all(b.customer_id == sample_customer_id for b in result)
        mock_repository.find_by_customer.assert_called_once_with(
            customer_id=sample_customer_id, include_cancelled=False
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
