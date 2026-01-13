"""
Integration Tests for Auth Token Refresh Endpoint
=================================================

Tests the token refresh flow end-to-end to ensure:
1. /api/v1/auth/refresh returns valid tokens (not 501)
2. Token rotation works correctly
3. Invalid tokens are rejected with proper error codes
4. Blacklisted tokens cannot be reused

These tests were added after discovering a routing issue where
/api/v1/auth/refresh was returning 501 Not Implemented because
it was routed to a stub instead of the real implementation.

See: commit 4b79201 for the fix
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timedelta
import jwt
from pathlib import Path
import sys

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from main import app
from core.security import create_access_token, create_refresh_token
from core.config import settings


@pytest_asyncio.fixture
async def client():
    """Create async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def valid_refresh_token():
    """Create a valid refresh token for testing."""
    token_data = {
        "sub": "test-user-123",
        "email": "test@myhibachi.com",
        "role": "admin",
        "type": "refresh",
    }
    return create_refresh_token(token_data)


@pytest_asyncio.fixture
async def valid_access_token():
    """Create a valid access token for testing."""
    token_data = {
        "sub": "test-user-123",
        "email": "test@myhibachi.com",
        "role": "admin",
    }
    return create_access_token(token_data)


class TestRefreshEndpointAvailability:
    """
    Critical: Ensure the refresh endpoint is properly implemented.

    These tests verify that /api/v1/auth/refresh does NOT return 501,
    which would indicate routing to a stub instead of real implementation.
    """

    @pytest.mark.asyncio
    async def test_refresh_endpoint_not_501(self, client: AsyncClient):
        """
        CRITICAL: Refresh endpoint must NOT return 501 Not Implemented.

        This was the root cause of WebSocket authentication failures.
        The endpoint was routing to a stub that returned 501.
        """
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token_for_test"}
        )

        # Should return 401 (invalid token) NOT 501 (not implemented)
        assert response.status_code != 501, (
            "CRITICAL: /api/v1/auth/refresh is returning 501 Not Implemented! "
            "This indicates the endpoint is routed to a stub. "
            "Check api/v1/endpoints/auth.py - it should delegate to routers/v1/auth.py"
        )

        # Should be 401 for invalid token
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_endpoint_returns_proper_error_structure(self, client: AsyncClient):
        """Verify error response has proper structure."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "malformed_token"}
        )

        assert response.status_code == 401
        data = response.json()

        # Should have error structure, not stub message
        assert "error" in data or "detail" in data or "message" in data
        assert "Not Implemented" not in str(data), (
            "Response contains 'Not Implemented' - endpoint is a stub!"
        )


class TestRefreshTokenValidation:
    """Test token validation logic in the refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_with_empty_token(self, client: AsyncClient):
        """Empty token should return 422 validation error."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": ""}
        )

        # Empty string should fail validation
        assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_refresh_with_missing_token_field(self, client: AsyncClient):
        """Missing refresh_token field should return 422."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={}
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_refresh_with_malformed_jwt(self, client: AsyncClient):
        """Malformed JWT should return 401."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "not.a.valid.jwt.token"}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_with_expired_token(self, client: AsyncClient):
        """Expired refresh token should return 401."""
        # Create an expired token
        expired_token_data = {
            "sub": "test-user-123",
            "email": "test@myhibachi.com",
            "type": "refresh",
            "exp": datetime.utcnow() - timedelta(hours=1),  # Expired 1 hour ago
        }
        expired_token = jwt.encode(
            expired_token_data,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )

        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": expired_token}
        )

        assert response.status_code == 401


class TestRefreshTokenFlow:
    """Test the full token refresh flow (requires database)."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires database setup with valid user")
    async def test_successful_token_refresh(self, client: AsyncClient, valid_refresh_token: str):
        """
        Test successful token refresh returns new access and refresh tokens.

        Note: This test requires a valid user in the database.
        Enable when running against a test database with fixtures.
        """
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": valid_refresh_token}
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires database setup with valid user")
    async def test_token_rotation(self, client: AsyncClient, valid_refresh_token: str):
        """
        Test that refresh token is rotated (old token can't be reused).

        Note: This test requires a valid user in the database.
        """
        # First refresh
        response1 = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": valid_refresh_token}
        )
        assert response1.status_code == 200

        # Try to use the old token again (should fail due to rotation)
        response2 = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": valid_refresh_token}
        )

        # Should fail because the old token was rotated out
        assert response2.status_code == 401


class TestLegacyEndpointCompatibility:
    """
    Test legacy /api/auth endpoints for backwards compatibility.

    These endpoints should either:
    1. Work identically to /api/v1/auth
    2. Redirect to /api/v1/auth
    3. Return deprecation warnings
    """

    @pytest.mark.asyncio
    async def test_legacy_auth_refresh_exists(self, client: AsyncClient):
        """Legacy /api/auth/refresh should exist (for backwards compat)."""
        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": "test"}
        )

        # Should return 401 (not 404 - endpoint exists) or redirect
        assert response.status_code in [401, 307, 308], (
            f"Legacy endpoint /api/auth/refresh returned {response.status_code}. "
            "It should either handle the request or redirect to /api/v1/auth/refresh"
        )


class TestConcurrentRefreshHandling:
    """Test handling of concurrent refresh requests."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires database setup")
    async def test_concurrent_refresh_race_condition(self, client: AsyncClient):
        """
        Test that concurrent refresh requests don't cause issues.

        With token rotation, if two refresh requests come in simultaneously
        with the same token, one should succeed and one should fail gracefully.
        """
        import asyncio

        # Create a valid refresh token
        token_data = {
            "sub": "test-user-123",
            "email": "test@myhibachi.com",
            "type": "refresh",
        }
        refresh_token = create_refresh_token(token_data)

        # Send multiple concurrent requests
        async def make_refresh_request():
            return await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh_token}
            )

        responses = await asyncio.gather(
            make_refresh_request(),
            make_refresh_request(),
            make_refresh_request(),
            return_exceptions=True
        )

        # At least one should succeed, others might fail
        status_codes = [r.status_code for r in responses if not isinstance(r, Exception)]

        # At most one should succeed (due to token rotation)
        success_count = sum(1 for code in status_codes if code == 200)
        assert success_count <= 1, "Multiple concurrent refreshes succeeded - token rotation may not be working"
