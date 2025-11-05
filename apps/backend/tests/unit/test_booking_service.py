"""
Unit Tests for BookingService
Test service layer business logic, caching, and validation
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta

# Phase 2B: Updated import to NEW location
from services.booking_service import BookingService

# OLD: from api.app.services.booking_service import BookingService

from core.exceptions import NotFoundException, BusinessLogicException


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


@pytest.mark.asyncio
class TestBookingServiceCRUD:
    """Test basic CRUD operations"""

    async def test_get_booking_by_id_found(self, booking_service, mock_repository):
        """Test getting booking by ID - found"""
        # Setup
        mock_booking = {"id": 1, "customer_name": "John Doe", "status": "confirmed"}
        mock_repository.find_by_id.return_value = mock_booking

        # Execute
        result = await booking_service.get_booking_by_id(1)

        # Verify
        assert result == mock_booking
        mock_repository.find_by_id.assert_called_once_with(1)

    async def test_get_booking_by_id_not_found(self, booking_service, mock_repository):
        """Test getting booking by ID - not found"""
        mock_repository.find_by_id.return_value = None

        with pytest.raises(NotFoundException) as exc:
            await booking_service.get_booking_by_id(999)

        assert "Booking with ID 999 not found" in str(exc.value)

    async def test_create_booking_success(self, booking_service, mock_repository, mock_cache):
        """Test creating booking with valid data"""
        # Setup
        booking_data = {
            "customer_name": "John Doe",
            "party_size": 4,
            "booking_date": datetime.now() + timedelta(days=1),
            "status": "pending",
        }

        created_booking = {**booking_data, "id": 1}
        mock_repository.create.return_value = created_booking

        # Execute
        result = await booking_service.create_booking(booking_data)

        # Verify
        assert result["id"] == 1
        mock_repository.create.assert_called_once()
        # Cache should be invalidated
        mock_cache.delete_pattern.assert_called()

    async def test_create_booking_invalid_party_size(self, booking_service):
        """Test creating booking with invalid party size"""
        booking_data = {
            "customer_name": "John Doe",
            "party_size": 0,  # Invalid!
            "booking_date": datetime.now() + timedelta(days=1),
        }

        with pytest.raises(BusinessLogicException) as exc:
            await booking_service.create_booking(booking_data)

        assert "Party size must be between 1 and 20" in str(exc.value)

    async def test_create_booking_past_date(self, booking_service):
        """Test creating booking with past date"""
        booking_data = {
            "customer_name": "John Doe",
            "party_size": 4,
            "booking_date": datetime.now() - timedelta(days=1),  # Past!
        }

        with pytest.raises(BusinessLogicException) as exc:
            await booking_service.create_booking(booking_data)

        assert "Cannot book in the past" in str(exc.value)


@pytest.mark.asyncio
class TestBookingServiceBusinessLogic:
    """Test business logic methods"""

    async def test_confirm_booking_success(self, booking_service, mock_repository, mock_cache):
        """Test confirming a pending booking"""
        # Setup
        pending_booking = {"id": 1, "status": "pending", "customer_name": "John Doe"}

        confirmed_booking = {**pending_booking, "status": "confirmed"}
        mock_repository.find_by_id.return_value = pending_booking
        mock_repository.update.return_value = confirmed_booking

        # Execute
        result = await booking_service.confirm_booking(1)

        # Verify
        assert result["status"] == "confirmed"
        mock_repository.update.assert_called_once()
        mock_cache.delete_pattern.assert_called()

    async def test_confirm_booking_already_confirmed(self, booking_service, mock_repository):
        """Test confirming already confirmed booking"""
        confirmed_booking = {"id": 1, "status": "confirmed"}
        mock_repository.find_by_id.return_value = confirmed_booking

        with pytest.raises(BusinessLogicException) as exc:
            await booking_service.confirm_booking(1)

        assert "already confirmed" in str(exc.value).lower()

    async def test_cancel_booking_success(self, booking_service, mock_repository, mock_cache):
        """Test canceling a booking"""
        booking = {"id": 1, "status": "confirmed", "customer_name": "John Doe"}

        cancelled_booking = {**booking, "status": "cancelled"}
        mock_repository.find_by_id.return_value = booking
        mock_repository.update.return_value = cancelled_booking

        result = await booking_service.cancel_booking(1)

        assert result["status"] == "cancelled"
        mock_cache.delete_pattern.assert_called()

    async def test_cancel_already_cancelled(self, booking_service, mock_repository):
        """Test canceling already cancelled booking"""
        cancelled_booking = {"id": 1, "status": "cancelled"}
        mock_repository.find_by_id.return_value = cancelled_booking

        with pytest.raises(BusinessLogicException) as exc:
            await booking_service.cancel_booking(1)

        assert "already cancelled" in str(exc.value).lower()


@pytest.mark.asyncio
class TestBookingServiceCaching:
    """Test caching behavior"""

    async def test_get_dashboard_stats_cached(self, booking_service, mock_repository, mock_cache):
        """Test dashboard stats are cached"""
        # Setup
        cached_stats = {"total_bookings": 100, "confirmed": 80, "pending": 20}
        mock_cache.get.return_value = cached_stats

        # Execute
        result = await booking_service.get_dashboard_stats()

        # Verify - should return cached data without hitting repository
        assert result == cached_stats
        mock_cache.get.assert_called_once()
        mock_repository.find_all.assert_not_called()

    async def test_get_dashboard_stats_cache_miss(
        self, booking_service, mock_repository, mock_cache
    ):
        """Test dashboard stats on cache miss"""
        # Setup
        mock_cache.get.return_value = None
        mock_repository.count.side_effect = [100, 80, 20]

        # Execute
        result = await booking_service.get_dashboard_stats()

        # Verify
        assert result["total_bookings"] == 100
        assert result["confirmed"] == 80
        assert result["pending"] == 20

        # Should cache the result
        mock_cache.set.assert_called_once()

    async def test_cache_invalidation_on_create(self, booking_service, mock_repository, mock_cache):
        """Test cache is invalidated on create"""
        booking_data = {
            "customer_name": "John Doe",
            "party_size": 4,
            "booking_date": datetime.now() + timedelta(days=1),
        }

        mock_repository.create.return_value = {**booking_data, "id": 1}

        await booking_service.create_booking(booking_data)

        # Verify cache invalidation
        mock_cache.delete_pattern.assert_called()
        # Should invalidate booking-related caches
        call_args = mock_cache.delete_pattern.call_args[0][0]
        assert "booking" in call_args.lower()


@pytest.mark.asyncio
class TestBookingServiceValidation:
    """Test business rule validation"""

    async def test_validate_party_size_valid(self, booking_service):
        """Test valid party sizes"""
        for size in [1, 2, 4, 8, 12, 20]:
            booking_data = {
                "customer_name": "Test",
                "party_size": size,
                "booking_date": datetime.now() + timedelta(days=1),
            }

            # Should not raise
            booking_service._validate_booking_data(booking_data)

    async def test_validate_party_size_invalid(self, booking_service):
        """Test invalid party sizes"""
        for size in [0, -1, 21, 100]:
            booking_data = {
                "customer_name": "Test",
                "party_size": size,
                "booking_date": datetime.now() + timedelta(days=1),
            }

            with pytest.raises(BusinessLogicException):
                booking_service._validate_booking_data(booking_data)

    async def test_validate_booking_date_future(self, booking_service):
        """Test future dates are valid"""
        for days in [1, 7, 30, 90]:
            booking_data = {
                "customer_name": "Test",
                "party_size": 4,
                "booking_date": datetime.now() + timedelta(days=days),
            }

            # Should not raise
            booking_service._validate_booking_data(booking_data)

    async def test_validate_booking_date_past(self, booking_service):
        """Test past dates are invalid"""
        booking_data = {
            "customer_name": "Test",
            "party_size": 4,
            "booking_date": datetime.now() - timedelta(days=1),
        }

        with pytest.raises(BusinessLogicException):
            booking_service._validate_booking_data(booking_data)


@pytest.mark.asyncio
class TestBookingServicePagination:
    """Test pagination and filtering"""

    async def test_get_bookings_paginated(self, booking_service, mock_repository):
        """Test getting paginated bookings"""
        # Setup
        mock_bookings = [{"id": 1, "customer_name": "John"}, {"id": 2, "customer_name": "Jane"}]

        mock_result = MagicMock()
        mock_result.items = mock_bookings
        mock_result.total = 10
        mock_result.page = 1
        mock_result.page_size = 2

        mock_repository.find_paginated.return_value = mock_result

        # Execute
        result = await booking_service.get_bookings_paginated(page=1, page_size=2)

        # Verify
        assert len(result.items) == 2
        assert result.total == 10
        mock_repository.find_paginated.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
