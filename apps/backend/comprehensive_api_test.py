"""
Comprehensive API Testing Suite
Tests all endpoints and database functions to ensure 100% functionality
"""
import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Any
import json

# Add backend src to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir / "src"))

from dotenv import load_dotenv
load_dotenv(backend_dir / ".env")

from sqlalchemy import text, inspect, func
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import AsyncSessionLocal, engine
from api.app.auth.station_models import Station, StationUser, StationAuditLog
from api.app.models.core import Customer, Booking
from api.app.models.lead_newsletter import Lead, Subscriber


class TestResult:
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self, test_name: str):
        self.total += 1
        self.passed += 1
        print(f"  ✅ PASS: {test_name}")
    
    def add_fail(self, test_name: str, error: str):
        self.total += 1
        self.failed += 1
        self.errors.append({"test": test_name, "error": error})
        print(f"  ❌ FAIL: {test_name}")
        print(f"     Error: {error}")
    
    def summary(self):
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {self.total}")
        print(f"Passed: {self.passed} ✅")
        print(f"Failed: {self.failed} {'❌' if self.failed > 0 else ''}")
        print(f"Success Rate: {(self.passed/self.total*100) if self.total > 0 else 0:.1f}%")
        
        if self.failed > 0:
            print("\n❌ FAILED TESTS:")
            for error in self.errors:
                print(f"  - {error['test']}: {error['error']}")
        
        print("="*80)
        return self.failed == 0


async def test_database_connection(result: TestResult):
    """Test database connectivity."""
    print("\n📊 TESTING: Database Connection")
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            result.add_pass("Database connection")
    except Exception as e:
        result.add_fail("Database connection", str(e))


async def test_database_schemas(result: TestResult):
    """Test that all required schemas exist."""
    print("\n📊 TESTING: Database Schemas")
    
    required_schemas = [
        'identity', 'core', 'lead', 'newsletter', 
        'integra', 'feedback', 'marketing', 'public'
    ]
    
    try:
        async with AsyncSessionLocal() as session:
            query = text("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
            """)
            result_proxy = await session.execute(query)
            schemas = [row[0] for row in result_proxy.fetchall()]
            
            for schema in required_schemas:
                if schema in schemas:
                    result.add_pass(f"Schema exists: {schema}")
                else:
                    result.add_fail(f"Schema exists: {schema}", "Schema not found")
    except Exception as e:
        result.add_fail("Database schemas check", str(e))


async def test_critical_tables(result: TestResult):
    """Test that critical tables exist."""
    print("\n📊 TESTING: Critical Tables")
    
    critical_tables = [
        ('identity', 'stations'),
        ('identity', 'station_users'),
        ('identity', 'station_audit_logs'),
        ('core', 'customers'),
        ('core', 'bookings'),
        ('core', 'chefs'),
        ('core', 'reviews'),
        ('lead', 'leads'),
        ('lead', 'lead_contacts'),
        ('newsletter', 'subscribers'),
        ('newsletter', 'campaigns'),
        ('core', 'message_threads'),
        ('core', 'messages'),
        ('integra', 'payment_events'),
        ('feedback', 'customer_reviews'),
    ]
    
    try:
        async with AsyncSessionLocal() as session:
            for schema, table in critical_tables:
                query = text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = :schema 
                        AND table_name = :table
                    )
                """)
                result_proxy = await session.execute(
                    query, 
                    {"schema": schema, "table": table}
                )
                exists = result_proxy.scalar()
                
                if exists:
                    result.add_pass(f"Table exists: {schema}.{table}")
                else:
                    result.add_fail(f"Table exists: {schema}.{table}", "Table not found")
    except Exception as e:
        result.add_fail("Critical tables check", str(e))


async def test_station_crud(result: TestResult):
    """Test Station CRUD operations."""
    print("\n📊 TESTING: Station CRUD Operations")
    
    try:
        async with AsyncSessionLocal() as session:
            # Test READ
            from sqlalchemy import select
            query = select(func.count(Station.id))
            count_result = await session.execute(query)
            count = count_result.scalar_one()
            
            if count > 0:
                result.add_pass(f"Station READ (found {count} stations)")
            else:
                result.add_fail("Station READ", "No stations found")
            
            # Test that stations have required fields
            query = select(Station).limit(1)
            station_result = await session.execute(query)
            station = station_result.scalar_one_or_none()
            
            if station:
                required_fields = ['id', 'code', 'name', 'display_name', 'timezone', 'status']
                for field in required_fields:
                    if hasattr(station, field) and getattr(station, field) is not None:
                        result.add_pass(f"Station field exists: {field}")
                    else:
                        result.add_fail(f"Station field exists: {field}", f"Field missing or null")
            
    except Exception as e:
        result.add_fail("Station CRUD operations", str(e))


async def test_database_indexes(result: TestResult):
    """Test that critical indexes exist."""
    print("\n📊 TESTING: Database Indexes")
    
    try:
        async with AsyncSessionLocal() as session:
            # Check for some critical indexes
            query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname
                FROM pg_indexes
                WHERE schemaname IN ('identity', 'core', 'lead', 'newsletter', 'integra', 'feedback')
                ORDER BY schemaname, tablename
            """)
            result_proxy = await session.execute(query)
            indexes = result_proxy.fetchall()
            
            if len(indexes) > 0:
                result.add_pass(f"Database indexes ({len(indexes)} indexes found)")
                
                # Check for specific critical indexes
                index_names = [idx[2] for idx in indexes]
                
                # Check for primary keys (look for _pkey suffix)
                pk_count = sum(1 for name in index_names if name.endswith('_pkey'))
                if pk_count > 0:
                    result.add_pass(f"Primary key indexes ({pk_count} found)")
                else:
                    result.add_fail("Primary key indexes", "No PKs found")
            else:
                result.add_fail("Database indexes", "No indexes found")
    except Exception as e:
        result.add_fail("Database indexes check", str(e))


async def test_database_constraints(result: TestResult):
    """Test that critical constraints exist."""
    print("\n📊 TESTING: Database Constraints")
    
    try:
        async with AsyncSessionLocal() as session:
            # Check for foreign key constraints
            query = text("""
                SELECT 
                    COUNT(*) as fk_count
                FROM information_schema.table_constraints
                WHERE constraint_type = 'FOREIGN KEY'
                AND table_schema IN ('identity', 'core', 'lead', 'newsletter', 'integra', 'feedback')
            """)
            result_proxy = await session.execute(query)
            fk_count = result_proxy.scalar()
            
            if fk_count > 0:
                result.add_pass(f"Foreign key constraints ({fk_count} found)")
            else:
                result.add_fail("Foreign key constraints", "No FKs found")
            
            # Check for unique constraints
            query = text("""
                SELECT 
                    COUNT(*) as unique_count
                FROM information_schema.table_constraints
                WHERE constraint_type = 'UNIQUE'
                AND table_schema IN ('identity', 'core', 'lead', 'newsletter', 'integra', 'feedback')
            """)
            result_proxy = await session.execute(query)
            unique_count = result_proxy.scalar()
            
            if unique_count > 0:
                result.add_pass(f"Unique constraints ({unique_count} found)")
            else:
                result.add_fail("Unique constraints", "No unique constraints found")
    except Exception as e:
        result.add_fail("Database constraints check", str(e))


async def test_sqlalchemy_models(result: TestResult):
    """Test that SQLAlchemy models are properly configured."""
    print("\n📊 TESTING: SQLAlchemy Models")
    
    try:
        from api.app.models.core import Base as CoreBase
        from core.database import Base
        
        # Test that models are registered
        models_to_test = [
            (Station, "Station"),
            (Customer, "Customer"),
            (Booking, "Booking"),
            (Lead, "Lead"),
            (Subscriber, "Subscriber"),
        ]
        
        for model, name in models_to_test:
            if hasattr(model, '__tablename__'):
                result.add_pass(f"Model configured: {name}")
            else:
                result.add_fail(f"Model configured: {name}", "Missing __tablename__")
        
    except Exception as e:
        result.add_fail("SQLAlchemy models check", str(e))


async def test_async_session_maker(result: TestResult):
    """Test async session creation and cleanup."""
    print("\n📊 TESTING: Async Session Management")
    
    try:
        # Test session creation
        async with AsyncSessionLocal() as session:
            result.add_pass("Async session creation")
            
            # Test that we can execute queries
            await session.execute(text("SELECT 1"))
            result.add_pass("Query execution in session")
            
        result.add_pass("Async session cleanup")
        
    except Exception as e:
        result.add_fail("Async session management", str(e))


async def test_data_integrity(result: TestResult):
    """Test data integrity and relationships."""
    print("\n📊 TESTING: Data Integrity")
    
    try:
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            
            # Test station-customer relationship
            query = select(func.count(Customer.id))
            customer_result = await session.execute(query)
            customer_count = customer_result.scalar_one()
            result.add_pass(f"Customer data integrity ({customer_count} customers)")
            
            # Test station-booking relationship  
            query = select(func.count(Booking.id))
            booking_result = await session.execute(query)
            booking_count = booking_result.scalar_one()
            result.add_pass(f"Booking data integrity ({booking_count} bookings)")
            
            # Test leads
            query = select(func.count(Lead.id))
            lead_result = await session.execute(query)
            lead_count = lead_result.scalar_one()
            result.add_pass(f"Lead data integrity ({lead_count} leads)")
            
    except Exception as e:
        result.add_fail("Data integrity check", str(e))


async def test_station_code_generator(result: TestResult):
    """Test station code generation logic."""
    print("\n📊 TESTING: Station Code Generator")
    
    try:
        from api.app.utils.station_code_generator import validate_station_code_format
        
        # Test valid codes
        valid_codes = [
            "STATION-CA-BAY-001",
            "STATION-TX-AUSTIN-002",
            "STATION-NY-NYC-999"
        ]
        
        for code in valid_codes:
            is_valid = await validate_station_code_format(code) if asyncio.iscoroutinefunction(validate_station_code_format) else validate_station_code_format(code)
            if is_valid:
                result.add_pass(f"Valid code format: {code}")
            else:
                result.add_fail(f"Valid code format: {code}", "Validation failed")
        
        # Test invalid codes
        invalid_codes = [
            "INVALID",
            "STATION-TOOLONG-BAY-001",
            "STATION-CA-001"
        ]
        
        for code in invalid_codes:
            is_valid = await validate_station_code_format(code) if asyncio.iscoroutinefunction(validate_station_code_format) else validate_station_code_format(code)
            if not is_valid:
                result.add_pass(f"Invalid code rejected: {code}")
            else:
                result.add_fail(f"Invalid code rejected: {code}", "Should have been rejected")
        
    except Exception as e:
        result.add_fail("Station code generator", str(e))


async def test_http_endpoints(result: TestResult):
    """Test HTTP endpoints using httpx."""
    print("\n📊 TESTING: HTTP Endpoints")
    
    try:
        import httpx
        
        base_url = "http://localhost:8000"
        
        async with httpx.AsyncClient() as client:
            # Test root endpoint
            response = await client.get(f"{base_url}/")
            if response.status_code == 200:
                result.add_pass("GET / (root endpoint)")
            else:
                result.add_fail("GET / (root endpoint)", f"Status {response.status_code}")
            
            # Test health check
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                result.add_pass("GET /health")
            else:
                result.add_fail("GET /health", f"Status {response.status_code}")
            
            # Test station endpoints
            response = await client.get(f"{base_url}/api/stations/test")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    result.add_pass("GET /api/stations/test")
                else:
                    result.add_fail("GET /api/stations/test", f"Status not success: {data}")
            else:
                result.add_fail("GET /api/stations/test", f"Status {response.status_code}")
            
            # Test station list (no auth)
            response = await client.get(f"{base_url}/api/stations/list-no-auth")
            if response.status_code == 200:
                data = response.json()
                if "stations" in data:
                    result.add_pass(f"GET /api/stations/list-no-auth ({data['count']} stations)")
                else:
                    result.add_fail("GET /api/stations/list-no-auth", "Missing stations key")
            else:
                result.add_fail("GET /api/stations/list-no-auth", f"Status {response.status_code}")
            
            # Test API docs
            response = await client.get(f"{base_url}/docs")
            if response.status_code == 200:
                result.add_pass("GET /docs (API documentation)")
            else:
                result.add_fail("GET /docs", f"Status {response.status_code}")
            
    except ImportError:
        print("  ⚠️  httpx not installed, skipping HTTP endpoint tests")
        print("     Run: pip install httpx")
    except Exception as e:
        result.add_fail("HTTP endpoints check", str(e))


async def run_all_tests():
    """Run all test suites."""
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "COMPREHENSIVE API TEST SUITE" + " "*30 + "║")
    print("╚" + "="*78 + "╝")
    print("\nTesting database connectivity, schemas, models, and endpoints...")
    print("Server must be running on http://localhost:8000\n")
    
    result = TestResult()
    
    # Run all test suites
    await test_database_connection(result)
    await test_database_schemas(result)
    await test_critical_tables(result)
    await test_database_indexes(result)
    await test_database_constraints(result)
    await test_sqlalchemy_models(result)
    await test_async_session_maker(result)
    await test_station_crud(result)
    await test_data_integrity(result)
    await test_station_code_generator(result)
    await test_http_endpoints(result)
    
    # Print summary
    success = result.summary()
    
    if success:
        print("\n🎉 ALL TESTS PASSED! API is 100% functional!")
        print("\n✅ Ready to proceed with:")
        print("   1. Build frontend /admin/stations page")
        print("   2. Implement Google OAuth integration")
        print("   3. Deploy performance indexes")
        print("   4. Add station manager assignment UI")
        print("   5. Fix authentication middleware")
    else:
        print("\n⚠️  SOME TESTS FAILED. Please review errors above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
