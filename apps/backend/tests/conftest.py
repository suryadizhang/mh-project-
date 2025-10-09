"""
Test configuration for the unified API
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from typing import AsyncGenerator

from main import app
from core.database import get_db

# Test client
client = TestClient(app)

# Mock database session for testing
class MockAsyncSession:
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def commit(self):
        pass
    
    async def rollback(self):
        pass
    
    async def close(self):
        pass

async def get_test_db() -> AsyncGenerator[AsyncSession, None]:
    """Mock database session for testing"""
    yield MockAsyncSession()

# Override database dependency for testing
app.dependency_overrides[get_db] = get_test_db

@pytest.fixture
def test_client():
    """Test client fixture"""
    return client

@pytest.fixture
def admin_token():
    """Get admin token for testing"""
    response = client.post("/v1/auth/login", json={
        "email": "admin@myhibachichef.com",
        "password": "admin123"
    })
    assert response.status_code == 200
    return response.json()["access_token"]

@pytest.fixture
def owner_token():
    """Get owner token for testing"""
    response = client.post("/v1/auth/login", json={
        "email": "owner@myhibachichef.com", 
        "password": "owner123"
    })
    assert response.status_code == 200
    return response.json()["access_token"]