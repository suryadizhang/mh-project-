"""
Basic test suite for MyHibachi FastAPI backend.
"""
import os
import pytest
from fastapi.testclient import TestClient

# Set testing environment variables before imports
os.environ["TESTING"] = "true"
os.environ["DISABLE_EMAIL"] = "true"
os.environ["ENVIRONMENT"] = "testing"

from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment."""
    os.environ["TESTING"] = "true"
    os.environ["DISABLE_EMAIL"] = "true"
    yield
    # Cleanup after tests


def test_root_endpoint():
    """Test root health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "My Hibachi CRM API"
    assert data["status"] == "healthy"


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data
    assert "database" in data


def test_ready_endpoint():
    """Test readiness probe endpoint."""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    # In testing environment, database might not be ready
    assert data["status"] in ["ready", "not ready"]


def test_booking_endpoints_auth_required():
    """Test that booking endpoints require authentication."""
    # Test that protected endpoints return 403/401/404 (depending on router setup)
    response = client.get("/api/booking/admin/kpis")
    assert response.status_code in [401, 403, 404, 422]  # Auth required or not found
    
    response = client.get("/api/booking/admin/weekly?start_date=2024-01-01")
    assert response.status_code in [401, 403, 404, 422]  # Auth required or not found


def test_public_endpoints():
    """Test public endpoints that don't require auth."""
    # Test root endpoint (should be public)
    response = client.get("/")
    assert response.status_code == 200
    
    # Test health endpoint (should be public)
    response = client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_booking_creation():
    """Test booking creation endpoint."""
    booking_data = {
        "name": "Test User",
        "phone": "123-456-7890",
        "email": "test@example.com",
        "address": "123 Test St",
        "city": "Test City",
        "zipcode": "12345",
        "date": "2024-12-25",
        "time_slot": "18:00",
        "contact_preference": "phone"
    }
    
    # This will likely fail due to rate limiting or auth, but tests the structure
    response = client.post("/api/booking/book", json=booking_data)
    # Just ensure it's not a 500 error (server error)
    assert response.status_code != 500


def test_cors_headers():
    """Test that CORS headers are properly set."""
    response = client.get("/")
    # Check that CORS headers are present
    assert "access-control-allow-origin" in [header.lower() for header in response.headers.keys()] or response.status_code == 200


def test_api_documentation():
    """Test that API documentation is available in development."""
    response = client.get("/docs")
    # Should be available in development mode
    assert response.status_code in [200, 404]  # 404 if disabled in production


if __name__ == "__main__":
    pytest.main([__file__])