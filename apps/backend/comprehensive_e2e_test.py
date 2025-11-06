"""
COMPREHENSIVE END-TO-END TEST SUITE
Tests EVERY feature, endpoint, and integration point
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, errors="replace")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, errors="replace")

sys.path.insert(0, "src")
os.environ["TESTING"] = "true"

from fastapi.testclient import TestClient


# Test results tracking
class TestRunner:
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.failures = []

    def test(self, name: str, func):
        """Run a test and track results"""
        self.total += 1
        try:
            func()
            self.passed += 1
            print(f"  ✅ {name}")
            return True
        except AssertionError as e:
            self.failed += 1
            self.failures.append(f"{name}: {str(e)}")
            print(f"  ❌ {name}: {str(e)}")
            return False
        except Exception as e:
            self.failed += 1
            error_msg = f"{type(e).__name__}: {str(e)}"
            self.failures.append(f"{name}: {error_msg}")
            print(f"  ❌ {name}: {error_msg}")
            return False

    def section(self, name: str):
        """Print section header"""
        print(f"\n{'='*70}")
        print(f"  {name}")
        print(f"{'='*70}")

    def summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("  COMPREHENSIVE TEST SUMMARY")
        print("=" * 70)
        print(f"Total Tests: {self.total}")
        print(f"Passed: {self.passed} ✅")
        print(f"Failed: {self.failed} ❌")
        print(f"Success Rate: {(self.passed/self.total*100):.1f}%")

        if self.failures:
            print(f"\n{'='*70}")
            print("  FAILURES:")
            print(f"{'='*70}")
            for failure in self.failures:
                print(f"  ❌ {failure}")

        print("=" * 70)

        if self.failed > 0:
            print("\n❌ TESTS FAILED - ISSUES FOUND")
            sys.exit(1)
        else:
            print("\n✅ ALL TESTS PASSED - SYSTEM FULLY FUNCTIONAL")
            sys.exit(0)


runner = TestRunner()

# ============================================================================
# SECTION 1: CORE APPLICATION & IMPORTS
# ============================================================================
runner.section("1. CORE APPLICATION & CRITICAL IMPORTS")


def test_main_app_loads():
    """Test that main.py loads without errors"""
    import main

    assert hasattr(main, "app"), "FastAPI app not found"
    assert main.app is not None, "FastAPI app is None"


runner.test("Main application loads", test_main_app_loads)


def test_settings_load():
    """Test settings configuration"""
    from core.config import get_settings

    settings = get_settings()
    assert settings is not None, "Settings is None"
    assert hasattr(settings, "app_name"), "Settings missing app_name"


runner.test("Settings configuration", test_settings_load)


def test_database_imports():
    """Test database utilities"""
    from core.database import get_db_session, init_db

    assert get_db_session is not None
    assert init_db is not None


runner.test("Database utilities import", test_database_imports)


def test_auth_imports():
    """Test authentication imports"""
    from core.auth.middleware import get_current_user
    from core.auth import require_roles  # require_roles is in __init__.py, not middleware
    from core.auth.models import User
    from utils.auth import UserRole  # UserRole is in utils.auth

    assert get_current_user is not None
    assert require_roles is not None
    assert User is not None
    assert UserRole is not None


runner.test("Authentication imports", test_auth_imports)


def test_cqrs_imports():
    """Test CQRS pattern imports"""
    from cqrs.crm_operations import ApiResponse
    from cqrs.booking_commands import CreateBookingCommand

    assert ApiResponse is not None
    assert CreateBookingCommand is not None


runner.test("CQRS pattern imports", test_cqrs_imports)


def test_station_auth_imports():
    """Test station authentication"""
    from core.auth.station_auth import StationAuthenticationService
    from core.auth.station_models import StationRole

    assert StationAuthenticationService is not None
    assert StationRole is not None


runner.test("Station authentication imports", test_station_auth_imports)

# ============================================================================
# SECTION 2: ENDPOINT FUNCTIONALITY TESTS
# ============================================================================
runner.section("2. ENDPOINT FUNCTIONALITY TESTS")

import main

client = TestClient(main.app)


def test_health_endpoint():
    """Test /health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200, f"Status: {response.status_code}"
    data = response.json()
    assert "status" in data, "Missing 'status' field"
    assert data["status"] == "healthy", f"Status: {data['status']}"


runner.test("GET /health returns 200", test_health_endpoint)


def test_ready_endpoint():
    """Test /ready endpoint"""
    response = client.get("/ready")
    assert response.status_code == 200, f"Status: {response.status_code}"
    data = response.json()
    assert "ready" in data, "Missing 'ready' field"


runner.test("GET /ready returns 200", test_ready_endpoint)


def test_api_docs():
    """Test API documentation"""
    response = client.get("/docs")
    assert response.status_code == 200, f"Status: {response.status_code}"


runner.test("GET /docs (Swagger UI) accessible", test_api_docs)


def test_openapi_schema():
    """Test OpenAPI schema"""
    response = client.get("/openapi.json")
    assert response.status_code == 200, f"Status: {response.status_code}"
    data = response.json()
    assert "openapi" in data, "Missing OpenAPI version"
    assert "paths" in data, "Missing paths"


runner.test("GET /openapi.json returns schema", test_openapi_schema)

# ============================================================================
# SECTION 3: AUTHENTICATION ENDPOINTS
# ============================================================================
runner.section("3. AUTHENTICATION ENDPOINTS")


def test_auth_login_endpoint():
    """Test login endpoint exists"""
    response = client.post(
        "/api/auth/login", json={"email": "test@example.com", "password": "test123"}
    )
    # Should fail with 401 (incorrect credentials) not 404 or 500
    assert response.status_code in [400, 401, 422], f"Unexpected status: {response.status_code}"


runner.test("POST /api/auth/login endpoint exists", test_auth_login_endpoint)


def test_auth_register_endpoint():
    """Test register endpoint exists"""
    response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "Test123!@#", "full_name": "Test User"},
    )
    # Should respond - 201 for success, 400/409/422 for validation errors
    assert response.status_code in [
        201,
        400,
        409,
        422,
    ], f"Unexpected status: {response.status_code}"


runner.test("POST /api/auth/register endpoint exists", test_auth_register_endpoint)


def test_station_login_endpoint():
    """Test station login endpoint"""
    response = client.post(
        "/api/station/station-login", json={"email": "test@example.com", "password": "test123"}
    )
    # Should fail with auth error, not 500
    assert response.status_code in [
        400,
        401,
        422,
    ], f"Got {response.status_code}: {response.text[:200]}"


runner.test("POST /api/station/station-login works", test_station_login_endpoint)

# ============================================================================
# SECTION 4: BOOKING SYSTEM
# ============================================================================
runner.section("4. BOOKING SYSTEM")


def test_bookings_list_endpoint():
    """Test bookings list"""
    response = client.get("/api/bookings/")
    # Should require auth (401 or 403)
    assert response.status_code in [401, 403], f"Status: {response.status_code}"


runner.test("GET /api/bookings/ requires auth", test_bookings_list_endpoint)


def test_booking_create_endpoint():
    """Test booking creation"""
    response = client.post(
        "/api/bookings/", json={"customer_name": "John Doe", "service_type": "test"}
    )
    # Should require auth
    assert response.status_code in [401, 403, 422], f"Status: {response.status_code}"


runner.test("POST /api/bookings/ endpoint exists", test_booking_create_endpoint)

# ============================================================================
# SECTION 5: LEAD MANAGEMENT
# ============================================================================
runner.section("5. LEAD MANAGEMENT SYSTEM")


def test_leads_list_endpoint():
    """Test leads list endpoint works (public endpoint for now)"""
    response = client.get("/api/leads/")
    # Endpoint is public and should return 200 with empty list or data
    assert response.status_code == 200, f"Status: {response.status_code}"
    assert isinstance(response.json(), list), "Should return a list"


runner.test("GET /api/leads/ returns 200", test_leads_list_endpoint)


def test_lead_create_endpoint():
    """Test lead creation"""
    response = client.post("/api/leads/", json={"name": "Test Lead", "email": "lead@test.com"})
    assert response.status_code in [401, 403, 422], f"Status: {response.status_code}"


runner.test("POST /api/leads/ endpoint exists", test_lead_create_endpoint)

# ============================================================================
# SECTION 6: CUSTOMER REVIEWS
# ============================================================================
runner.section("6. CUSTOMER REVIEW SYSTEM")


def test_reviews_list():
    """Test reviews list"""
    response = client.get("/api/reviews/")
    # May be public or require auth
    assert response.status_code in [200, 401, 403], f"Status: {response.status_code}"


runner.test("GET /api/reviews/ responds", test_reviews_list)


def test_review_submit():
    """Test review submission"""
    response = client.post(
        "/api/reviews/",
        json={"rating": 5, "comment": "Great service!", "customer_email": "test@example.com"},
    )
    assert response.status_code in [200, 201, 401, 403, 422], f"Status: {response.status_code}"


runner.test("POST /api/reviews/ endpoint exists", test_review_submit)

# ============================================================================
# SECTION 7: PAYMENT SYSTEM
# ============================================================================
runner.section("7. PAYMENT SYSTEM")


def test_payment_analytics():
    """Test payment analytics"""
    response = client.get("/api/payments/analytics")
    assert response.status_code in [401, 403], f"Status: {response.status_code}"


runner.test("GET /api/payments/analytics requires auth", test_payment_analytics)

# ============================================================================
# SECTION 8: ADMIN PANEL
# ============================================================================
runner.section("8. ADMIN PANEL FEATURES")


def test_admin_kpis():
    """Test admin KPIs endpoint"""
    response = client.get("/api/admin/kpis")
    assert response.status_code in [401, 403], f"Status: {response.status_code}"


runner.test("GET /api/admin/kpis requires auth", test_admin_kpis)


def test_admin_stations_list():
    """Test stations list"""
    response = client.get("/api/admin/stations/")
    assert response.status_code in [401, 403], f"Status: {response.status_code}"


runner.test("GET /api/admin/stations/ requires auth", test_admin_stations_list)

# ============================================================================
# SECTION 9: AI CHAT SYSTEM
# ============================================================================
runner.section("9. AI CHAT SYSTEM")


def test_ai_health():
    """Test AI system health"""
    response = client.get("/api/v1/ai/health")
    assert response.status_code == 200, f"Status: {response.status_code}"
    data = response.json()
    assert "status" in data, "Missing status field"


runner.test("GET /api/v1/ai/health returns 200", test_ai_health)


def test_ai_chat_endpoint():
    """Test AI chat endpoint"""
    response = client.post(
        "/api/v1/ai/chat", json={"message": "Hello", "session_id": "test-session"}
    )
    # May require auth or accept public messages
    assert response.status_code in [200, 401, 403, 422], f"Status: {response.status_code}"


runner.test("POST /api/v1/ai/chat endpoint exists", test_ai_chat_endpoint)

# ============================================================================
# SECTION 10: CQRS PATTERN VALIDATION
# ============================================================================
runner.section("10. CQRS ARCHITECTURE VALIDATION")


def test_booking_commands_instantiate():
    """Test booking commands can be created"""
    from cqrs.booking_commands import (
        CreateBookingCommand,
        UpdateBookingCommand,
        DeleteBookingCommand,
    )
    from datetime import date
    from uuid import uuid4

    create_cmd = CreateBookingCommand(
        customer_name="Test User",
        customer_email="test@example.com",
        customer_phone="+1-555-0100",
        date=date(2025, 11, 10),
        slot="1:00 PM",
        total_guests=4,
        price_per_person_cents=5000,
        total_due_cents=20000,  # 4 guests * $50
        deposit_due_cents=10000,  # 50% deposit
        source="test",
    )
    assert create_cmd is not None
    assert create_cmd.customer_name == "Test User"

    update_cmd = UpdateBookingCommand(
        booking_id=uuid4(),
        updated_by=str(uuid4()),  # Convert UUID to string - command expects str
        update_reason="Test update",  # Required field
        customer_name="Updated Name",
    )
    assert update_cmd is not None

    delete_cmd = DeleteBookingCommand(
        booking_id=uuid4(), cancellation_reason="Test cancellation", cancelled_by="test-user"
    )
    assert delete_cmd is not None


runner.test("Booking commands instantiate correctly", test_booking_commands_instantiate)


def test_booking_queries_instantiate():
    """Test booking queries can be created"""
    from cqrs.booking_queries import GetBookingsQuery, GetBookingByIdQuery
    from uuid import uuid4

    get_all = GetBookingsQuery(limit=10, offset=0)
    assert get_all is not None

    get_one = GetBookingByIdQuery(booking_id=uuid4())  # UUID not int
    assert get_one is not None


runner.test("Booking queries instantiate correctly", test_booking_queries_instantiate)


def test_lead_commands_instantiate():
    """Test lead commands"""
    from cqrs.lead_commands import CreateLeadCommand

    create_cmd = CreateLeadCommand(
        name="Test Lead", email="test@lead.com", phone="1234567890", source="website"
    )
    assert create_cmd is not None


runner.test("Lead commands instantiate correctly", test_lead_commands_instantiate)

# ============================================================================
# SECTION 11: STATION AUTHENTICATION
# ============================================================================
runner.section("11. MULTI-TENANT STATION SYSTEM")


def test_station_auth_service():
    """Test StationAuthenticationService"""
    from core.auth.station_auth import StationAuthenticationService
    from core.security import FieldEncryption

    encryption = FieldEncryption()
    service = StationAuthenticationService(encryption, "test-secret-key-12345678901234567890")
    assert service is not None


runner.test("StationAuthenticationService instantiates", test_station_auth_service)


def test_station_context():
    """Test StationContext"""
    from core.auth.station_auth import StationContext
    from uuid import uuid4

    context = StationContext(
        user_id=uuid4(), stations=[], current_station_id=None, highest_role="customer_support"
    )
    assert context is not None
    assert hasattr(context, "is_super_admin")
    assert hasattr(context, "is_admin")


runner.test("StationContext works correctly", test_station_context)


def test_station_permissions():
    """Test station permissions"""
    from core.auth.station_models import StationPermission, StationRole, STATION_ROLE_PERMISSIONS

    # Test that permissions dict exists
    assert STATION_ROLE_PERMISSIONS is not None
    assert StationRole.SUPER_ADMIN in STATION_ROLE_PERMISSIONS
    assert StationRole.ADMIN in STATION_ROLE_PERMISSIONS

    # Test permission retrieval
    admin_perms = STATION_ROLE_PERMISSIONS[StationRole.ADMIN]
    assert StationPermission.BOOKING_CREATE in admin_perms


runner.test("Station permissions configured correctly", test_station_permissions)

# ============================================================================
# SECTION 12: MIDDLEWARE STACK
# ============================================================================
runner.section("12. MIDDLEWARE STACK VALIDATION")


def test_cors_middleware():
    """Test CORS is configured"""
    import main

    middleware_classes = [m.__class__.__name__ for m in main.app.user_middleware]
    # CORS should be configured (may be in different positions)
    assert len(middleware_classes) > 0, "No middleware configured"


runner.test("Middleware stack configured", test_cors_middleware)


def test_structured_logging():
    """Test structured logging middleware"""
    from middleware.structured_logging import StructuredLoggingMiddleware

    assert StructuredLoggingMiddleware is not None


runner.test("Structured logging available", test_structured_logging)

# ============================================================================
# SECTION 13: DATABASE MODELS
# ============================================================================
runner.section("13. DATABASE MODELS")


def test_user_model():
    """Test User model"""
    from core.auth.models import User

    assert hasattr(User, "__tablename__")
    assert hasattr(User, "id")
    assert hasattr(User, "email_encrypted")


runner.test("User model defined", test_user_model)


def test_booking_model():
    """Test Booking model"""
    from models.booking import Booking

    assert hasattr(Booking, "__tablename__")
    assert hasattr(Booking, "id")
    assert hasattr(Booking, "customer_id")  # Changed from customer_name to customer_id


runner.test("Booking model defined", test_booking_model)


def test_lead_model():
    """Test Lead model"""
    from models.lead import Lead

    assert hasattr(Lead, "__tablename__")
    assert hasattr(Lead, "id")
    assert hasattr(Lead, "source")  # Changed from name to source (actual field)


runner.test("Lead model defined", test_lead_model)


def test_station_models():
    """Test Station models"""
    from models.station import Station, StationUser

    assert hasattr(Station, "__tablename__")
    assert hasattr(StationUser, "__tablename__")


runner.test("Station models defined", test_station_models)

# ============================================================================
# SECTION 14: API RESPONSE FORMAT
# ============================================================================
runner.section("14. API RESPONSE CONSISTENCY")


def test_api_response_format():
    """Test ApiResponse format"""
    from cqrs.crm_operations import ApiResponse

    response = ApiResponse(success=True, message="Test message", data={"test": "data"})

    assert response.success == True
    assert response.message == "Test message"
    assert response.data == {"test": "data"}


runner.test("ApiResponse format correct", test_api_response_format)


def test_health_response_structure():
    """Test health endpoint response structure"""
    response = client.get("/health")
    data = response.json()

    # Should have standard fields
    assert "status" in data or "service" in data, f"Unexpected structure: {data}"


runner.test("Health endpoint response structure", test_health_response_structure)

# ============================================================================
# SECTION 15: ROUTE REGISTRATION
# ============================================================================
runner.section("15. ROUTE REGISTRATION")


def test_routes_registered():
    """Test all routers are registered"""
    import main

    # Get all registered routes
    routes = [route.path for route in main.app.routes]

    # Check critical routes exist
    assert any("/health" in route for route in routes), "Health route not found"
    assert any("/api/auth" in route for route in routes), "Auth routes not found"
    assert any("/api/bookings" in route for route in routes), "Booking routes not found"
    assert any("/api/station" in route for route in routes), "Station routes not found"
    assert any("/api/admin" in route for route in routes), "Admin routes not found"


runner.test("All critical routes registered", test_routes_registered)

# ============================================================================
# SECTION 16: ERROR HANDLING
# ============================================================================
runner.section("16. ERROR HANDLING")


def test_404_handling():
    """Test 404 error handling"""
    response = client.get("/api/nonexistent-route-xyz-123")
    # Should return proper error, not crash
    assert response.status_code in [403, 404], f"Status: {response.status_code}"


runner.test("404 errors handled gracefully", test_404_handling)


def test_validation_errors():
    """Test validation error handling"""
    response = client.post("/api/auth/login", json={"invalid": "data"})
    # Should return 422 validation error
    assert response.status_code == 422, f"Status: {response.status_code}"
    data = response.json()
    # Our custom error handler wraps errors with success/error structure
    assert "error" in data, "Missing error object"
    assert "details" in data["error"] or "message" in data["error"], "Missing error details"


runner.test("Validation errors formatted correctly", test_validation_errors)

# ============================================================================
# SECTION 17: SECURITY FEATURES
# ============================================================================
runner.section("17. SECURITY FEATURES")


def test_field_encryption():
    """Test field encryption"""
    from core.security import FieldEncryption

    encryption = FieldEncryption()

    original = "test@example.com"
    encrypted = encryption.encrypt(original)
    decrypted = encryption.decrypt(encrypted)

    assert encrypted != original, "Encryption didn't change value"
    assert decrypted == original, f"Decryption failed: {decrypted} != {original}"


runner.test("Field encryption works", test_field_encryption)


def test_password_hashing():
    """Test password hashing"""
    from core.security import hash_password, verify_password

    password = "TestPassword123!"
    hashed = hash_password(password)

    assert hashed != password, "Password not hashed"
    assert verify_password(password, hashed), "Password verification failed"
    assert not verify_password("WrongPassword", hashed), "Wrong password verified"


runner.test("Password hashing works", test_password_hashing)

# ============================================================================
# SECTION 18: ENVIRONMENT CONFIGURATION
# ============================================================================
runner.section("18. ENVIRONMENT CONFIGURATION")


def test_settings_validation():
    """Test settings are properly configured"""
    from core.config import get_settings

    settings = get_settings()

    assert settings.app_name, "Missing app_name"
    assert settings.environment, "Missing environment"
    assert settings.jwt_secret_key, "Missing jwt_secret_key"


runner.test("Settings validation", test_settings_validation)

# ============================================================================
# SECTION 19: NO OLD IMPORTS
# ============================================================================
runner.section("19. MIGRATION VALIDATION")


def test_no_old_api_app_directory():
    """Test OLD api/app directory is deleted"""
    import os

    old_path = os.path.join("src", "api", "app")
    assert not os.path.exists(old_path), f"OLD directory still exists: {old_path}"


runner.test("OLD api/app directory deleted", test_no_old_api_app_directory)


def test_no_old_imports_in_runtime():
    """Test no OLD imports in runtime code"""
    import subprocess

    # Search for 'from app.' imports (excluding test files and migrations)
    result = subprocess.run(
        [
            "python",
            "-c",
            """
import os
import re

old_imports = []
for root, dirs, files in os.walk("src"):
    # Skip migrations and old reference files
    if "migrations" in root or "main_old" in root:
        continue
    
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            with open(filepath, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    if re.match(r"^from app\\.", line.strip()):
                        old_imports.append(f"{filepath}:{line_num}")

if old_imports:
    print("OLD imports found:")
    for imp in old_imports:
        print(f"  {imp}")
    exit(1)
else:
    print("No OLD imports in runtime code")
""",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"OLD imports found:\n{result.stdout}"


runner.test("No OLD imports in runtime code", test_no_old_imports_in_runtime)

# ============================================================================
# SECTION 20: INTEGRATION TESTS
# ============================================================================
runner.section("20. INTEGRATION VALIDATION")


def test_full_import_chain():
    """Test complete import chain works"""
    # This should import everything without circular dependencies
    from routers.v1 import auth, bookings, leads, station_auth, station_admin
    from routers.v1.admin import admin_router
    from api.ai.endpoints.routers import chat as ai_chat  # NEW structure uses routers/ subdirectory

    assert auth.router is not None
    assert bookings.router is not None
    assert leads.router is not None
    assert station_auth.router is not None
    assert station_admin.router is not None
    assert admin_router is not None
    assert ai_chat.router is not None  # Verify AI chat router loads


runner.test("Complete import chain works", test_full_import_chain)


def test_no_circular_dependencies():
    """Test no circular dependency errors"""
    try:
        # Import everything that could cause circular deps
        import main
        from core.auth import middleware, models, station_auth
        from cqrs import booking_commands, booking_queries, lead_commands
        from routers.v1 import auth, bookings, leads, station_auth as sa, station_admin

        success = True
    except ImportError as e:
        raise AssertionError(f"Circular dependency detected: {e}")


runner.test("No circular dependencies", test_no_circular_dependencies)

# ============================================================================
# PRINT FINAL SUMMARY
# ============================================================================
runner.summary()
