"""
MINIMAL isolated test for BookingService to verify test infrastructure works
This avoids ORM model conflicts by using pure mocks
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


@pytest.fixture
def mock_repository():
    """Mock repository with all methods (synchronous, not async)"""
    repo = MagicMock()
    # Repository methods are SYNC, not async
    repo.create = MagicMock()
    repo.get_by_id = MagicMock()
    repo.find_by_date_range = MagicMock(return_value=[])
    repo.update = MagicMock()
    repo.delete = MagicMock()
    repo.db = MagicMock()
    return repo


@pytest.fixture
def mock_cache():
    """Mock cache service"""
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    cache.delete = AsyncMock()
    return cache


@pytest.fixture
def booking_service(mock_repository, mock_cache):
    """Create BookingService with mocked dependencies"""
    from services.booking_service import BookingService

    return BookingService(
        repository=mock_repository, cache=mock_cache, lead_service=None, audit_service=None
    )


class TestBookingServiceInfrastructure:
    """Test that service can be instantiated and basic mocking works"""

    def test_service_instantiation(self, booking_service, mock_repository):
        """Test: Service instantiates correctly"""
        assert booking_service is not None
        assert booking_service.repository == mock_repository

    @pytest.mark.asyncio
    async def test_get_dashboard_stats_calls_repository(self, booking_service, mock_repository):
        """Test: Dashboard stats calls repository with correct parameters"""
        # Arrange
        mock_repository.find_by_date_range.return_value = []

        # Act
        result = await booking_service.get_dashboard_stats()

        # Assert
        assert mock_repository.find_by_date_range.called
        assert result is not None
        assert isinstance(result, dict)
        assert "total_bookings" in result
        assert result["total_bookings"] == 0

    @pytest.mark.asyncio
    async def test_get_booking_by_id_not_found(self, booking_service, mock_repository):
        """Test: get_booking_by_id raises NotFoundException when booking doesn't exist"""
        from core.exceptions import NotFoundException

        # Arrange
        mock_repository.get_by_id.return_value = None
        booking_id = uuid4()

        # Act & Assert
        with pytest.raises(NotFoundException):
            await booking_service.get_booking_by_id(booking_id)
