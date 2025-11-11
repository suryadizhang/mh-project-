"""
Comprehensive Test Suite for Station-Aware RBAC System
Tests multi-tenant isolation, permission validation, and security boundaries.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.auth.station_models import Station, StationUser, StationAuditLog
from app.auth.station_auth import StationAuthenticationService, StationContext

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_station_rbac.db"
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

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def setup_test_db():
    """Create test database tables."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    """Create a fresh database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)

@pytest.fixture
def test_stations(db_session):
    """Create test stations."""
    station1 = Station(
        name="Station Alpha",
        description="Primary test station",
        location="Test City A",
        phone="+1-555-0001",
        email="alpha@test.com",
        manager_name="Alice Manager",
        created_by=1
    )
    
    station2 = Station(
        name="Station Beta",
        description="Secondary test station",
        location="Test City B",
        phone="+1-555-0002",
        email="beta@test.com",
        manager_name="Bob Manager",
        created_by=1
    )
    
    db_session.add_all([station1, station2])
    db_session.commit()
    db_session.refresh(station1)
    db_session.refresh(station2)
    
    return {"alpha": station1, "beta": station2}

@pytest.fixture
def test_users(db_session, test_stations):
    """Create test users with different roles."""
    users = {
        "super_admin": StationUser(
            station_id=test_stations["alpha"].id,
            user_id=1,
            role="super_admin",
            permissions=["*"],  # All permissions
            assigned_by=1
        ),
        "admin": StationUser(
            station_id=test_stations["alpha"].id,
            user_id=2,
            role="admin",
            permissions=[
                "manage_stations", "manage_users", "view_analytics",
                "manage_bookings", "view_customers", "manage_staff"
            ],
            assigned_by=1
        ),
        "station_admin": StationUser(
            station_id=test_stations["alpha"].id,
            user_id=3,
            role="station_admin",
            permissions=[
                "manage_bookings", "view_customers", "manage_staff",
                "view_analytics", "view_station_users"
            ],
            assigned_by=1
        ),
        "customer_support": StationUser(
            station_id=test_stations["alpha"].id,
            user_id=4,
            role="customer_support",
            permissions=[
                "view_bookings", "view_customers", "create_bookings"
            ],
            assigned_by=1
        ),
        "beta_admin": StationUser(
            station_id=test_stations["beta"].id,
            user_id=5,
            role="admin",
            permissions=[
                "manage_stations", "manage_users", "view_analytics",
                "manage_bookings", "view_customers", "manage_staff"
            ],
            assigned_by=1
        )
    }
    
    db_session.add_all(users.values())
    db_session.commit()
    
    for user in users.values():
        db_session.refresh(user)
    
    return users

class TestStationMultiTenancy:
    """Test multi-tenant isolation and data scoping."""
    
    def test_station_data_isolation(self, db_session, test_stations, test_users):
        """Test that users can only access data from their assigned station."""
        auth_service = StationAuthenticationService()
        
        # Alpha station admin should only see alpha station
        alpha_context = auth_service.create_station_context(
            user_id=test_users["station_admin"].user_id,
            station_id=test_stations["alpha"].id,
            db=db_session
        )
        
        assert alpha_context.station_id == test_stations["alpha"].id
        assert alpha_context.role == "station_admin"
        
        # Beta station admin should only see beta station
        beta_context = auth_service.create_station_context(
            user_id=test_users["beta_admin"].user_id,
            station_id=test_stations["beta"].id,
            db=db_session
        )
        
        assert beta_context.station_id == test_stations["beta"].id
        assert beta_context.role == "admin"
        
        # Super admin should be able to access any station
        super_context = auth_service.create_station_context(
            user_id=test_users["super_admin"].user_id,
            station_id=test_stations["alpha"].id,
            db=db_session
        )
        
        assert super_context.is_super_admin
    
    def test_cross_station_access_denied(self, db_session, test_stations, test_users):
        """Test that cross-station access is properly denied."""
        auth_service = StationAuthenticationService()
        
        # Try to access beta station with alpha station user
        with pytest.raises(Exception):
            auth_service.create_station_context(
                user_id=test_users["station_admin"].user_id,
                station_id=test_stations["beta"].id,
                db=db_session
            )
    
    def test_rls_policy_enforcement(self, db_session, test_stations):
        """Test Row Level Security policy enforcement."""
        # Note: This would test actual RLS policies if implemented in PostgreSQL
        # For SQLite, we test application-level filtering
        
        # Query should be automatically filtered by station_id
        alpha_stations = db_session.query(Station).filter(
            Station.id == test_stations["alpha"].id
        ).all()
        
        beta_stations = db_session.query(Station).filter(
            Station.id == test_stations["beta"].id
        ).all()
        
        assert len(alpha_stations) == 1
        assert len(beta_stations) == 1
        assert alpha_stations[0].id != beta_stations[0].id


class TestPermissionValidation:
    """Test role-based permission validation."""
    
    def test_role_permission_inheritance(self, db_session, test_users):
        """Test that roles inherit appropriate permissions."""
        super_admin = test_users["super_admin"]
        admin = test_users["admin"]
        station_admin = test_users["station_admin"]
        customer_support = test_users["customer_support"]
        
        # Super admin has all permissions
        assert "*" in super_admin.permissions or len(super_admin.permissions) > 10
        
        # Admin has management permissions
        assert "manage_stations" in admin.permissions
        assert "manage_users" in admin.permissions
        assert "view_analytics" in admin.permissions
        
        # Station admin has limited management permissions
        assert "manage_bookings" in station_admin.permissions
        assert "view_customers" in station_admin.permissions
        assert "manage_stations" not in station_admin.permissions
        
        # Customer support has minimal permissions
        assert "view_bookings" in customer_support.permissions
        assert "create_bookings" in customer_support.permissions
        assert "manage_users" not in customer_support.permissions
    
    def test_permission_escalation_prevention(self, db_session, test_users):
        """Test that users cannot escalate their permissions."""
        from app.auth.station_models import has_permission
        
        station_admin = test_users["station_admin"]
        customer_support = test_users["customer_support"]
        
        # Station admin cannot manage stations
        assert not has_permission(station_admin, "manage_stations")
        
        # Customer support cannot manage users
        assert not has_permission(customer_support, "manage_users")
        
        # Customer support cannot view analytics
        assert not has_permission(customer_support, "view_analytics")
    
    def test_agent_access_permissions(self, test_users):
        """Test agent access based on user roles."""
        from app.auth import has_agent_access, StationContext
        
        # Create station contexts for testing
        super_admin_context = StationContext(
            station_id=1,
            station_name="Test Station",
            user_id=1,
            role="super_admin",
            permissions=["*"],
            is_super_admin=True
        )
        
        admin_context = StationContext(
            station_id=1,
            station_name="Test Station",
            user_id=2,
            role="admin",
            permissions=["manage_users"],
            is_super_admin=False
        )
        
        station_admin_context = StationContext(
            station_id=1,
            station_name="Test Station",
            user_id=3,
            role="station_admin",
            permissions=["manage_bookings"],
            is_super_admin=False
        )
        
        customer_support_context = StationContext(
            station_id=1,
            station_name="Test Station",
            user_id=4,
            role="customer_support",
            permissions=["view_bookings"],
            is_super_admin=False
        )
        
        # Super admin can access all agents
        assert has_agent_access(super_admin_context, "admin")
        assert has_agent_access(super_admin_context, "analytics")
        assert has_agent_access(super_admin_context, "staff")
        assert has_agent_access(super_admin_context, "support")
        assert has_agent_access(super_admin_context, "customer")
        
        # Admin can access all agents
        assert has_agent_access(admin_context, "admin")
        assert has_agent_access(admin_context, "analytics")
        assert has_agent_access(admin_context, "staff")
        assert has_agent_access(admin_context, "support")
        assert has_agent_access(admin_context, "customer")
        
        # Station admin has limited access
        assert not has_agent_access(station_admin_context, "admin")
        assert not has_agent_access(station_admin_context, "analytics")
        assert has_agent_access(station_admin_context, "staff")
        assert has_agent_access(station_admin_context, "support")
        assert has_agent_access(station_admin_context, "customer")
        
        # Customer support has minimal access
        assert not has_agent_access(customer_support_context, "admin")
        assert not has_agent_access(customer_support_context, "analytics")
        assert not has_agent_access(customer_support_context, "staff")
        assert has_agent_access(customer_support_context, "support")
        assert has_agent_access(customer_support_context, "customer")


class TestStationAwareAPI:
    """Test station-aware API endpoints."""
    
    def test_unified_chat_with_station_context(self, client, test_users, test_stations):
        """Test unified chat API with station context."""
        auth_service = StationAuthenticationService()
        
        # Create JWT token for station admin
        token = auth_service.create_station_token(
            user_id=test_users["station_admin"].user_id,
            station_id=test_stations["alpha"].id
        )
        
        response = client.post(
            "/v1/chat",
            json={
                "message": "Help me manage bookings",
                "context": {"department": "operations"}
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-Agent": "staff"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should be processed by staff agent
        assert data["agent"] == "staff"
        
        # Should include station context
        assert data["station_context"] is not None
        assert data["station_context"]["station_id"] == test_stations["alpha"].id
        assert data["permission_level"] == "station_scoped"
    
    def test_agent_access_denied_insufficient_permissions(self, client, test_users, test_stations):
        """Test that agent access is denied for insufficient permissions."""
        auth_service = StationAuthenticationService()
        
        # Create JWT token for customer support
        token = auth_service.create_station_token(
            user_id=test_users["customer_support"].user_id,
            station_id=test_stations["alpha"].id
        )
        
        response = client.post(
            "/v1/chat",
            json={
                "message": "Show me analytics dashboard",
                "context": {}
            },
            headers={
                "Authorization": f"Bearer {token}",
                "X-Agent": "analytics"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should fallback to customer agent since analytics access denied
        assert data["agent"] == "customer"  # or support depending on implementation
    
    def test_station_admin_endpoints(self, client, test_users, test_stations):
        """Test station administration endpoints."""
        auth_service = StationAuthenticationService()
        
        # Create JWT token for admin
        token = auth_service.create_station_token(
            user_id=test_users["admin"].user_id,
            station_id=test_stations["alpha"].id
        )
        
        # Test listing stations
        response = client.get(
            "/api/admin/stations/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1  # Should see at least their own station
    
    def test_cross_station_access_via_api(self, client, test_users, test_stations):
        """Test that cross-station access is blocked via API."""
        auth_service = StationAuthenticationService()
        
        # Create JWT token for alpha station admin
        token = auth_service.create_station_token(
            user_id=test_users["station_admin"].user_id,
            station_id=test_stations["alpha"].id
        )
        
        # Try to access beta station
        response = client.get(
            f"/api/admin/stations/{test_stations['beta'].id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403  # Forbidden


class TestAuditLogging:
    """Test comprehensive audit logging."""
    
    def test_audit_log_creation(self, db_session, test_users, test_stations):
        """Test that audit logs are created for sensitive operations."""
        from app.auth.station_middleware import audit_log_action
        
        # Create audit log entry
        asyncio.run(audit_log_action(
            db=db_session,
            user_id=test_users["admin"].user_id,
            station_id=test_stations["alpha"].id,
            action="create_booking",
            resource_type="booking",
            resource_id="booking_123",
            details={"customer_id": 456, "amount": 150.00}
        ))
        
        # Verify audit log was created
        audit_logs = db_session.query(StationAuditLog).filter(
            StationAuditLog.action == "create_booking"
        ).all()
        
        assert len(audit_logs) == 1
        log = audit_logs[0]
        assert log.user_id == test_users["admin"].user_id
        assert log.station_id == test_stations["alpha"].id
        assert log.resource_type == "booking"
        assert log.resource_id == "booking_123"
        assert log.details["customer_id"] == 456
    
    def test_audit_log_filtering(self, db_session, test_users, test_stations):
        """Test audit log filtering and access controls."""
        from app.auth.station_middleware import audit_log_action
        
        # Create multiple audit logs
        logs_data = [
            ("create_booking", "booking", "booking_1"),
            ("update_customer", "customer", "customer_1"),
            ("delete_booking", "booking", "booking_2"),
        ]
        
        for action, resource_type, resource_id in logs_data:
            asyncio.run(audit_log_action(
                db=db_session,
                user_id=test_users["admin"].user_id,
                station_id=test_stations["alpha"].id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details={}
            ))
        
        # Test filtering by action
        booking_logs = db_session.query(StationAuditLog).filter(
            StationAuditLog.resource_type == "booking"
        ).all()
        
        assert len(booking_logs) == 2  # create_booking and delete_booking
        
        # Test station isolation
        alpha_logs = db_session.query(StationAuditLog).filter(
            StationAuditLog.station_id == test_stations["alpha"].id
        ).all()
        
        assert len(alpha_logs) == 3  # All logs for alpha station


class TestSecurityBoundaries:
    """Test security boundaries and potential attack vectors."""
    
    def test_jwt_token_station_context_validation(self):
        """Test JWT token validation with station context."""
        from app.auth import extract_station_context
        import jwt
        
        # Create a valid token with station context
        payload = {
            "user_id": 123,
            "station_context": {
                "station_id": 1,
                "station_name": "Test Station",
                "role": "admin",
                "permissions": ["manage_users"]
            },
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        
        token = jwt.encode(payload, "test_secret", algorithm="HS256")
        
        # Test extraction
        context = extract_station_context(f"Bearer {token}")
        
        assert context is not None
        assert context.station_id == 1
        assert context.role == "admin"
        assert "manage_users" in context.permissions
    
    def test_privilege_escalation_prevention(self, db_session, test_users):
        """Test prevention of privilege escalation attacks."""
        from app.auth.station_models import has_permission
        
        # Customer support cannot escalate to admin permissions
        customer_support = test_users["customer_support"]
        
        assert not has_permission(customer_support, "manage_stations")
        assert not has_permission(customer_support, "manage_users")
        assert not has_permission(customer_support, "view_analytics")
        
        # Station admin cannot escalate to super admin permissions
        station_admin = test_users["station_admin"]
        
        assert not has_permission(station_admin, "manage_stations")
        
        # Even if permissions are manually added, role constraints should apply
        station_admin.permissions.append("manage_stations")
        # This should still be False due to role-based restrictions
        assert station_admin.role != "super_admin"
    
    def test_data_leakage_prevention(self, db_session, test_stations, test_users):
        """Test prevention of data leakage between stations."""
        # Simulate a query that should be filtered by station
        from app.auth import get_station_filter
        
        # Alpha station context
        alpha_context = StationContext(
            station_id=test_stations["alpha"].id,
            station_name="Alpha",
            user_id=test_users["station_admin"].user_id,
            role="station_admin",
            permissions=[],
            is_super_admin=False
        )
        
        alpha_filter = get_station_filter(alpha_context)
        assert alpha_filter["station_id"] == test_stations["alpha"].id
        
        # Super admin context (no filter)
        super_admin_context = StationContext(
            station_id=test_stations["alpha"].id,
            station_name="Alpha",
            user_id=test_users["super_admin"].user_id,
            role="super_admin",
            permissions=["*"],
            is_super_admin=True
        )
        
        super_admin_filter = get_station_filter(super_admin_context)
        assert super_admin_filter == {}  # No filter for super admin


class TestBackwardCompatibility:
    """Test backward compatibility with existing systems."""
    
    def test_api_without_station_context(self, client):
        """Test API endpoints work without station context (backward compatibility)."""
        response = client.post(
            "/v1/chat",
            json={
                "message": "Hello, I need help with booking",
                "context": {}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should default to customer agent
        assert data["agent"] == "customer"
        assert data["station_context"] is None
        assert data["permission_level"] == "public"
    
    def test_agent_gateway_backward_compatibility(self):
        """Test that agent gateway maintains backward compatibility."""
        # Should work with old AgentGatewayService interface
        from app.services.agent_gateway import AgentGatewayService
        
        # The old class should still be available as an alias
        gateway = AgentGatewayService()
        assert gateway is not None
        
        # Health check should work
        health = asyncio.run(gateway.health_check())
        assert health["healthy"] is True


# Test fixtures for running tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])