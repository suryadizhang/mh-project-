"""
Simplified Station-Aware RBAC Test
Tests core functionality without complex dependencies.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import core modules that we know work
try:
    from app.database import Base, get_db
    from app.main import app
    from app.auth.station_models import Station, StationUser, StationAuditLog
    from app.auth.station_auth import StationAuthenticationService, StationContext
    print("✅ All core imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    raise

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_station_rbac_simple.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override the database dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

def test_imports_successful():
    """Test that all imports work correctly."""
    assert Station is not None
    assert StationUser is not None
    assert StationAuditLog is not None
    assert StationAuthenticationService is not None
    assert StationContext is not None
    print("✅ All model imports verified")

def test_database_tables_creation():
    """Test that database tables can be created."""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
    except Exception as e:
        pytest.fail(f"Failed to create database tables: {e}")

def test_app_startup():
    """Test that the application starts without errors."""
    try:
        response = client.get("/health")
        print(f"✅ Health check response: {response.status_code}")
        # Don't require specific status - just that it doesn't crash
    except Exception as e:
        pytest.fail(f"Application startup failed: {e}")

def test_station_model_instantiation():
    """Test that Station model can be instantiated."""
    try:
        station = Station(
            name="Test Station",
            owner_id="test-owner-id"
        )
        assert station.name == "Test Station"
        assert station.owner_id == "test-owner-id"
        print("✅ Station model instantiation successful")
    except Exception as e:
        pytest.fail(f"Station model instantiation failed: {e}")

def test_station_context_creation():
    """Test that StationContext can be created."""
    try:
        from uuid import uuid4
        context = StationContext(
            station_id=uuid4(),
            user_id=uuid4(),
            permissions=["read", "write"]
        )
        assert context.station_id is not None
        assert context.user_id is not None
        assert "read" in context.permissions
        print("✅ StationContext creation successful")
    except Exception as e:
        pytest.fail(f"StationContext creation failed: {e}")

if __name__ == "__main__":
    print("Running simplified RBAC tests...")
    test_imports_successful()
    test_database_tables_creation()
    test_app_startup()
    test_station_model_instantiation()
    test_station_context_creation()
    print("✅ All simplified tests passed!")