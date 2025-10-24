"""
Pytest Configuration
Adds src to sys.path for proper imports and provides test fixtures
"""
import sys
import os
from pathlib import Path
import asyncio
import time
import random
from datetime import datetime, timedelta
from typing import AsyncGenerator
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import text
from faker import Faker

# Fix for Windows event loop issues with pytest-asyncio
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Configure pytest-asyncio to use function scope by default
pytest_plugins = ('pytest_asyncio',)

@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy for Windows."""
    if sys.platform == 'win32':
        policy = asyncio.WindowsSelectorEventLoopPolicy()
        asyncio.set_event_loop_policy(policy)
        return policy
    return asyncio.get_event_loop_policy()

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

backend_path = Path(__file__).parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from api.app.main import app
from api.app.database import engine
from api.app.utils.auth import create_access_token
from api.app.models.booking_models import LegacyUser, UserRole  # LegacyUser from booking_models (public.users)
from api.app.models.core import Booking, Customer, Payment  # Use core models for bookings/payments
from uuid import UUID, uuid4

fake = Faker()

@pytest.fixture
def test_auth_token():
    """Create a test authentication token."""
    token_data = {
        "sub": "admin-123-456",
        "email": "admin@myhibachi.com",
        "role": "admin",  # lowercase to match admin_required check
        "is_verified": True
    }
    return create_access_token(token_data)

@pytest.fixture
def performance_tracker():
    """Track test performance metrics."""
    class Tracker:
        def __init__(self):
            self.timings = {}
            self.start_times = {}
        
        def measure(self, name):
            return self._timer(name, self)
        
        class _timer:
            def __init__(self, name, parent):
                self.name = name
                self.parent = parent
            
            def __enter__(self):
                self.start = time.perf_counter()
                return self
            
            def __exit__(self, *args):
                end = time.perf_counter()
                self.parent.timings[self.name] = end - self.start
        
        def get_duration_ms(self, name):
            return self.timings.get(name, 0) * 1000
        
        def reset(self):
            self.timings.clear()
    
    return Tracker()

@pytest.fixture
def benchmark_results():
    """Collect and display benchmark results."""
    class BenchmarkCollector:
        def __init__(self):
            self.results = []
        
        def add(self, name, actual_ms, target_ms):
            """Add a benchmark result."""
            passed = actual_ms < target_ms
            self.results.append({
                'name': name,
                'actual_ms': actual_ms,
                'target_ms': target_ms,
                'passed': passed
            })
        
        def summary(self):
            """Print summary of all results."""
            print(f"\n{'='*80}")
            print(f"BENCHMARK RESULTS SUMMARY")
            print(f"{'='*80}")
            for result in self.results:
                status = "✅ PASS" if result['passed'] else "❌ FAIL"
                print(f"{result['name']:30} {result['actual_ms']:6.2f}ms / {result['target_ms']:6.2f}ms {status}")
            print(f"{'='*80}\n")
    
    collector = BenchmarkCollector()
    yield collector
    collector.summary()

@pytest_asyncio.fixture(scope="function")
async def async_client(test_auth_token) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for testing with authentication."""
    transport = ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {test_auth_token}"}
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers, follow_redirects=True) as client:
        yield client

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create database session for testing with multi-schema search path."""
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_maker() as session:
        try:
            # Set search_path to include core (bookings/payments), identity (stations), and public (users)
            await session.execute(text("SET search_path TO core, identity, public"))
            yield session
        finally:
            # Ensure session is properly closed
            await session.close()

@pytest_asyncio.fixture
async def test_admin_user(db_session):
    """Create admin user for testing that matches JWT token.
    
    In development mode, the auth system returns a mock user based on JWT token alone,
    so we don't need to actually create a database user. This fixture just provides
    the user ID for other fixtures that might need it.
    """
    yield "admin-123-456"  # Return the admin ID that matches the JWT token

@pytest_asyncio.fixture
async def create_test_bookings(db_session, test_admin_user):
    """Fixture to create test bookings using core models with guaranteed unique IDs."""
    async def _create(count=10):
        try:
            await db_session.execute(text("DELETE FROM core.payments WHERE TRUE"))
            await db_session.execute(text("DELETE FROM core.bookings WHERE TRUE"))
            await db_session.execute(text("DELETE FROM core.customers WHERE TRUE"))
            await db_session.execute(text("DELETE FROM identity.stations WHERE code LIKE 'TEST-%'"))
            await db_session.execute(text("DELETE FROM users WHERE id LIKE 'test-user-%'"))
            await db_session.commit()
        except Exception as e:
            await db_session.rollback()
        
        bookings = []
        base_date = datetime.now()
        timestamp = int(time.time() * 1000)
        
        # Import Station model to use ORM (avoids manual field mapping)
        from api.app.auth.station_models import Station
        
        # Create test station using ORM
        test_station = Station(
            name="Test Station",
            code=f"TEST-{timestamp}",
            display_name="Test Station for Tests",
            timezone="America/New_York",
            status="active"
        )
        db_session.add(test_station)
        await db_session.flush()
        test_station_id = test_station.id
        
        # Create test user in public.users for authentication
        test_user = LegacyUser(
            id=f"test-user-{timestamp}",
            email=f"testuser{timestamp}@example.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5XGvA8qBYMwBK",
            first_name="Test",
            last_name="User",
            phone="+1234567890",
            role=UserRole.CUSTOMER,
            is_active=True,
            is_verified=True
        )
        db_session.add(test_user)
        await db_session.flush()
        
        # Create test customer in core.customers
        test_customer = Customer(
            station_id=test_station_id,
            email_encrypted=f"testuser{timestamp}@example.com",  # Plaintext for testing
            name_encrypted="Test User",  # Plaintext for testing
            phone_encrypted="+1234567890",  # Plaintext for testing
            source="website"
        )
        db_session.add(test_customer)
        await db_session.flush()
        
        # Create bookings linked to customer
        for i in range(count):
            event_datetime = base_date + timedelta(days=random.randint(0, 365))
            slots = ["11:00 AM", "3:00 PM", "6:00 PM", "9:00 PM"]
            statuses = ["confirmed", "completed"]
            
            booking = Booking(
                station_id=test_station_id,
                customer_id=test_customer.id,
                date=event_datetime,
                slot=random.choice(slots),
                total_guests=random.randint(4, 20),
                price_per_person_cents=random.randint(5000, 10000),  # $50-$100 per person
                total_due_cents=random.randint(20000, 200000),  # $200-$2000 total
                deposit_due_cents=10000,  # $100 deposit
                balance_due_cents=random.randint(0, 190000),
                status=random.choice(statuses),
                payment_status=random.choice(["pending", "deposit_paid", "paid"]),
                source="website"
            )
            bookings.append(booking)
            db_session.add(booking)
        
        await db_session.commit()
        return bookings
    
    return _create

@pytest_asyncio.fixture
async def create_test_payments(db_session):
    """Fixture to create test payment records using core.Payment model."""
    async def _create(booking_ids, count=None):
        if count is None:
            count = len(booking_ids)
        
        payments = []
        timestamp = int(time.time() * 1000)
        for i in range(min(count, len(booking_ids))):
            payment = Payment(
                booking_id=booking_ids[i],
                amount_cents=random.randint(5000, 50000),  # $50-$500
                payment_method=random.choice(["stripe", "cash", "check"]),
                payment_reference=f"pi_test_{timestamp}_{i}",
                status=random.choice(["completed", "pending"]),
                notes="Test payment for booking",
                processed_by="system"
            )
            payments.append(payment)
            db_session.add(payment)
        
        await db_session.commit()
        return payments
    
    return _create
