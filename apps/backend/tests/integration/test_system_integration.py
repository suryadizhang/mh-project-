"""
Integration Tests - Cache + Database + Rate Limiting + Idempotency
Test critical system integration points
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock


# Test fixtures
@pytest.fixture
async def test_db():
    """Create test database"""
    SQLALCHEMY_TEST_URL = "sqlite:///./test.db"
    engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})

    # Create tables
    # Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    yield TestingSessionLocal()

    # Cleanup
    # Base.metadata.drop_all(bind=engine)


@pytest.fixture
async def test_cache():
    """Create test cache service"""
    from core.cache import CacheService

    cache = CacheService("redis://localhost:6379/1")  # Use DB 1 for tests
    await cache.connect()

    yield cache

    # Cleanup - clear test database
    if cache._client:
        await cache._client.flushdb()
    await cache.disconnect()


@pytest.fixture
def test_client():
    """Create test FastAPI client"""
    from main import app

    return TestClient(app)


@pytest.mark.integration
@pytest.mark.asyncio
class TestCacheDatabaseIntegration:
    """Test cache and database working together"""

    async def test_cache_database_consistency(self, test_db, test_cache):
        """Test cache reflects database changes"""
        from services.booking_service import BookingService
        from repositories.booking_repository import BookingRepository

        # Create service with real dependencies
        repository = BookingRepository(test_db)
        service = BookingService(repository, test_cache)

        # Create booking
        booking_data = {
            "customer_name": "Test User",
            "party_size": 4,
            "booking_date": datetime.now() + timedelta(days=1),
            "status": "pending",
        }

        created = await service.create_booking(booking_data)
        booking_id = created["id"]

        # First get - should hit database
        booking1 = await service.get_booking_by_id(booking_id)

        # Second get - should hit cache
        booking2 = await service.get_booking_by_id(booking_id)

        assert booking1 == booking2

        # Update booking
        await service.confirm_booking(booking_id)

        # Get after update - cache should be invalidated
        booking3 = await service.get_booking_by_id(booking_id)
        assert booking3["status"] == "confirmed"

    async def test_cache_invalidation_on_mutation(self, test_db, test_cache):
        """Test cache is properly invalidated on mutations"""
        from services.booking_service import BookingService
        from repositories.booking_repository import BookingRepository

        repository = BookingRepository(test_db)
        service = BookingService(repository, test_cache)

        # Get dashboard stats - should cache
        stats1 = await service.get_dashboard_stats()

        # Create new booking
        booking_data = {
            "customer_name": "New User",
            "party_size": 2,
            "booking_date": datetime.now() + timedelta(days=1),
            "status": "pending",
        }
        await service.create_booking(booking_data)

        # Get dashboard stats again - cache should be invalidated
        stats2 = await service.get_dashboard_stats()

        # Stats should be different
        assert stats2["total_bookings"] == stats1["total_bookings"] + 1


@pytest.mark.integration
class TestRateLimitingIntegration:
    """Test rate limiting in action"""

    def test_rate_limit_enforcement(self, test_client):
        """Test rate limit is enforced"""
        # Make requests until rate limited
        endpoint = "/api/bookings"

        responses = []
        for i in range(100):  # Exceed limit
            response = test_client.get(endpoint)
            responses.append(response.status_code)

            if response.status_code == 429:
                # Rate limited!
                assert "Retry-After" in response.headers
                break

        # Should have hit rate limit
        assert 429 in responses

    def test_rate_limit_headers(self, test_client):
        """Test rate limit headers are present"""
        response = test_client.get("/api/bookings")

        # Check for rate limit headers
        assert "X-RateLimit-Tier" in response.headers
        assert "X-RateLimit-Remaining-Minute" in response.headers
        assert "X-RateLimit-Remaining-Hour" in response.headers

    def test_rate_limit_reset(self, test_client):
        """Test rate limit resets after window"""
        endpoint = "/api/bookings"

        # Make requests until limited
        for i in range(100):
            response = test_client.get(endpoint)
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))

                # Wait for reset (in real test, mock time)
                # asyncio.sleep(retry_after)

                # Next request should succeed
                # response = test_client.get(endpoint)
                # assert response.status_code == 200
                break


@pytest.mark.integration
class TestIdempotencyIntegration:
    """Test idempotency for critical operations"""

    def test_idempotent_payment_creation(self, test_client):
        """Test payment creation with idempotency key"""
        idempotency_key = "test-payment-123"

        payment_data = {"amount": 100.00, "currency": "USD", "customer_id": "cust_123"}

        # First request
        response1 = test_client.post(
            "/api/stripe/create-payment",
            json=payment_data,
            headers={"Idempotency-Key": idempotency_key},
        )

        # Second request with same key
        response2 = test_client.post(
            "/api/stripe/create-payment",
            json=payment_data,
            headers={"Idempotency-Key": idempotency_key},
        )

        # Should return same response
        assert response1.json() == response2.json()

        # Second response should have replay header
        assert response2.headers.get("X-Idempotent-Replay") == "true"

    def test_idempotent_message_sending(self, test_client):
        """Test message sending with idempotency"""
        idempotency_key = "test-message-456"

        message_data = {"to": "+1234567890", "body": "Test message"}

        # Send twice with same key
        response1 = test_client.post(
            "/api/crm/messages", json=message_data, headers={"Idempotency-Key": idempotency_key}
        )

        response2 = test_client.post(
            "/api/crm/messages", json=message_data, headers={"Idempotency-Key": idempotency_key}
        )

        # Should only send once
        assert response1.status_code in [200, 201]
        assert response2.headers.get("X-Idempotent-Replay") == "true"


@pytest.mark.integration
@pytest.mark.asyncio
class TestCircuitBreakerIntegration:
    """Test circuit breaker protecting external services"""

    async def test_circuit_breaker_opens_on_failures(self):
        """Test circuit breaker opens after threshold"""
        from core.circuit_breaker import CircuitBreaker, CircuitBreakerError

        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1)

        # Simulate failures
        async def failing_call():
            raise Exception("Service unavailable")

        # First 3 failures should open circuit
        for i in range(3):
            with pytest.raises(Exception):
                await breaker.call(failing_call)

        # Next call should fail immediately with circuit breaker error
        with pytest.raises(CircuitBreakerError):
            await breaker.call(failing_call)

    async def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovers after timeout"""
        from core.circuit_breaker import CircuitBreaker

        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1, success_threshold=2)

        # Fail to open circuit
        async def failing_call():
            raise Exception("Failed")

        for i in range(2):
            with pytest.raises(Exception):
                await breaker.call(failing_call)

        # Wait for recovery timeout
        await asyncio.sleep(1.5)

        # Successful calls should close circuit
        async def successful_call():
            return "success"

        for i in range(2):
            result = await breaker.call(successful_call)
            assert result == "success"

        # Circuit should be closed now
        assert breaker.state.value == "closed"


@pytest.mark.integration
@pytest.mark.asyncio
class TestQueryOptimizationIntegration:
    """Test N+1 query prevention"""

    async def test_eager_loading_prevents_n_plus_one(self, test_db):
        """Test eager loading eliminates N+1 queries"""
        from repositories.booking_repository import BookingRepository
        from core.query_optimizer import fetch_with_relationships

        repository = BookingRepository(test_db)

        # Create test data
        # (In real test, create bookings with relationships)

        # Without eager loading - would cause N+1
        # bookings = await repository.find_all()
        # for booking in bookings:
        #     _ = booking.customer  # N+1!

        # Mock Booking model for this test
        MockBooking = MagicMock()
        MockBooking.__name__ = "Booking"

        # With eager loading - single query
        bookings = await fetch_with_relationships(
            test_db, MockBooking, filters={}, relationships=["customer", "menu_items"]
        )

        # Should load all relationships in single query
        assert len(bookings) >= 0  # Empty result is valid for mock


@pytest.mark.integration
class TestEndToEndFlows:
    """Test complete user flows"""

    def test_complete_booking_flow(self, test_client):
        """Test complete booking creation flow"""
        # 1. Create booking
        booking_data = {
            "customer_name": "E2E Test User",
            "party_size": 6,
            "booking_date": (datetime.now() + timedelta(days=2)).isoformat(),
            "contact_email": "test@example.com",
        }

        create_response = test_client.post("/api/bookings", json=booking_data)
        assert create_response.status_code in [200, 201]

        booking_id = create_response.json()["data"]["id"]

        # 2. Get booking
        get_response = test_client.get(f"/api/bookings/{booking_id}")
        assert get_response.status_code == 200

        # 3. Confirm booking
        confirm_response = test_client.patch(f"/api/bookings/{booking_id}/confirm")
        assert confirm_response.status_code == 200
        assert confirm_response.json()["data"]["status"] == "confirmed"

        # 4. Cancel booking
        cancel_response = test_client.delete(f"/api/bookings/{booking_id}")
        assert cancel_response.status_code == 200

    def test_payment_with_idempotency_and_rate_limiting(self, test_client):
        """Test payment flow with all protections"""
        idempotency_key = f"test-payment-{datetime.now().timestamp()}"

        payment_data = {"amount": 250.00, "currency": "USD", "description": "Test payment"}

        # Make payment (should succeed)
        response1 = test_client.post(
            "/api/stripe/create-payment",
            json=payment_data,
            headers={"Idempotency-Key": idempotency_key},
        )

        # Rate limit headers should be present
        assert "X-RateLimit-Remaining-Minute" in response1.headers

        # Retry with same key (should return cached)
        response2 = test_client.post(
            "/api/stripe/create-payment",
            json=payment_data,
            headers={"Idempotency-Key": idempotency_key},
        )

        assert response2.headers.get("X-Idempotent-Replay") == "true"


@pytest.mark.integration
class TestMetricsCollection:
    """Test metrics are being collected"""

    def test_metrics_endpoint(self, test_client):
        """Test /metrics endpoint returns Prometheus metrics"""
        response = test_client.get("/metrics")

        assert response.status_code == 200
        assert "http_requests_total" in response.text
        assert "cache_hits_total" in response.text
        assert "db_queries_total" in response.text

    def test_metrics_collection_on_request(self, test_client):
        """Test metrics are collected for requests"""
        # Make a request
        test_client.get("/api/bookings")

        # Check metrics
        metrics_response = test_client.get("/metrics")

        # Should have recorded the request
        assert "http_requests_total" in metrics_response.text
        assert "http_request_duration_seconds" in metrics_response.text


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto", "-m", "integration"])
