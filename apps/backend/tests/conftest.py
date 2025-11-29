"""
Pytest Configuration
Adds src to sys.path for proper imports and provides test fixtures
"""

import sys
from pathlib import Path
import asyncio
import time
import random
import uuid
from datetime import datetime, timedelta
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import text
from faker import Faker
from dotenv import load_dotenv

# Force load real .env file (not .env.test)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# Fix for Windows event loop issues with pytest-asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Configure pytest-asyncio to use function scope by default
pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy for Windows."""
    if sys.platform == "win32":
        policy = asyncio.WindowsSelectorEventLoopPolicy()
        asyncio.set_event_loop_policy(policy)
        return policy
    return asyncio.get_event_loop_policy()


# Remove session-scoped event_loop fixture - let pytest-asyncio handle it per function
# This fixes "Future attached to a different loop" errors


# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

backend_path = Path(__file__).parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Import from src package (unified architecture)
from src.main import app
from src.core.security import create_access_token
from src.core.config import UserRole

# Import NEW db.models (unified architecture)
from db.models.identity import User, Station
from db.models.core import Customer, Booking, Payment

from unittest.mock import AsyncMock, MagicMock
from src.services.event_service import EventService
from src.services.lead_service import LeadService
from src.services.newsletter_service import SubscriberService
from src.services.referral_service import ReferralService
from src.services.nurture_campaign_service import NurtureCampaignService
from src.core.compliance import ComplianceValidator

fake = Faker()


@pytest.fixture
def test_auth_token():
    """Create a test authentication token."""
    token_data = {
        "sub": "admin-123-456",
        "email": "admin@myhibachi.com",
        "role": "admin",  # lowercase to match admin_required check
        "is_verified": True,
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
            self.results.append(
                {
                    "name": name,
                    "actual_ms": actual_ms,
                    "target_ms": target_ms,
                    "passed": passed,
                }
            )

        def summary(self):
            """Print summary of all results."""
            print(f"\n{'='*80}")
            print("BENCHMARK RESULTS SUMMARY")
            print(f"{'='*80}")
            for result in self.results:
                status = "✅ PASS" if result["passed"] else "❌ FAIL"
                print(
                    f"{result['name']:30} {result['actual_ms']:6.2f}ms / {result['target_ms']:6.2f}ms {status}"
                )
            print(f"{'='*80}\n")

    collector = BenchmarkCollector()
    yield collector
    collector.summary()


@pytest_asyncio.fixture(scope="function")
async def async_client(test_auth_token) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for testing with authentication."""
    transport = ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {test_auth_token}"}
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers=headers,
        follow_redirects=True,
    ) as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create database session for testing with multi-schema search path."""
    from src.core.database import engine

    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_maker() as session:
        try:
            # Set search_path to include core (bookings/payments), identity (stations), and public (users)
            await session.execute(text("SET search_path TO core, identity, public"))
            yield session
        finally:
            # Ensure session is properly closed
            await session.close()


@pytest.fixture(scope="function")
def sync_db_session():
    """Create synchronous database session for testing with sync repositories."""
    from src.core.database import get_sync_db
    from sqlalchemy.orm import Session

    session: Session = next(get_sync_db())
    try:
        # Set search_path to include core (bookings/payments), identity (stations), and public (users)
        session.execute(text("SET search_path TO core, identity, public"))
        session.commit()
        yield session
    finally:
        session.rollback()  # Rollback any uncommitted changes
        session.close()


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
        except Exception:
            await db_session.rollback()

        bookings = []
        base_date = datetime.now()
        timestamp = int(time.time() * 1000)

        # Create test station using ORM (already imported at top)
        test_station = Station(
            name="Test Station",
            code=f"TEST-{timestamp}",
            display_name="Test Station for Tests",
            timezone="America/New_York",
            status="active",
        )
        db_session.add(test_station)
        await db_session.flush()
        test_station_id = test_station.id

        # Create test user in identity.users for authentication
        test_user = User(
            id=f"test-user-{timestamp}",
            email=f"testuser{timestamp}@example.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5XGvA8qBYMwBK",
            first_name="Test",
            last_name="User",
            phone="+1234567890",
            role=UserRole.CUSTOMER,
            is_active=True,
            is_verified=True,
        )
        db_session.add(test_user)
        await db_session.flush()

        # Create test customer in core.customers
        test_customer = Customer(
            station_id=test_station_id,
            email_encrypted=f"testuser{timestamp}@example.com",
            name_encrypted="Test User",
            phone_encrypted="+1234567890",
            source="website",
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
                source="website",
            )
            bookings.append(booking)
            db_session.add(booking)

        await db_session.commit()
        return bookings

    return _create


@pytest_asyncio.fixture
async def create_test_payments(db_session, create_test_bookings):
    """Fixture to create test payment records using core.Payment model."""

    async def _create(booking_ids=None, count=None):
        # If no booking_ids provided, create test bookings
        if booking_ids is None:
            if count is None:
                count = 10
            bookings = await create_test_bookings(count=count)
            booking_ids = [b.id for b in bookings]

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
                processed_by="system",
            )
            payments.append(payment)
            db_session.add(payment)

        await db_session.commit()
        return payments

    return _create


# ============================================================================
# FIXTURE ALIASES FOR COMPREHENSIVE ENDPOINT TESTS
# ============================================================================


@pytest_asyncio.fixture
async def client(async_client) -> AsyncGenerator[AsyncClient, None]:
    """Alias for async_client - used by comprehensive endpoint tests."""
    yield async_client


@pytest_asyncio.fixture
async def auth_client(async_client) -> AsyncGenerator[AsyncClient, None]:
    """Alias for async_client with authentication - used by load tests."""
    yield async_client


@pytest_asyncio.fixture
async def db(db_session) -> AsyncGenerator[AsyncSession, None]:
    """Alias for db_session - used by comprehensive endpoint tests."""
    yield db_session


# ============================================================================
# DEPENDENCY INJECTION MOCKS - Phase 4 Test Suite
# ============================================================================


@pytest.fixture
def mock_compliance_validator():
    """Mock ComplianceValidator for testing."""
    mock = MagicMock(spec=ComplianceValidator)
    mock.validate_consent.return_value = {"valid": True, "warnings": []}
    mock.validate_email.return_value = True
    mock.validate_phone.return_value = True
    return mock


@pytest_asyncio.fixture
async def mock_event_service(db_session):
    """Mock EventService with database session."""
    service = EventService(db_session)
    # Wrap methods with AsyncMock to track calls
    service.log_event = AsyncMock(wraps=service.log_event)
    service.log_lead_event = AsyncMock(wraps=service.log_lead_event)
    service.log_booking_event = AsyncMock(wraps=service.log_booking_event)
    return service


@pytest_asyncio.fixture
async def mock_lead_service(db_session, mock_compliance_validator, mock_event_service):
    """Create real LeadService with mocked dependencies for testing."""
    service = LeadService(
        db=db_session,
        compliance_validator=mock_compliance_validator,
        event_service=mock_event_service,
    )
    return service


@pytest_asyncio.fixture
async def mock_newsletter_service(db_session, mock_compliance_validator, mock_event_service):
    """Create real SubscriberService with mocked dependencies for testing."""
    service = SubscriberService(
        db=db_session,
        compliance_validator=mock_compliance_validator,
        event_service=mock_event_service,
    )
    return service


@pytest_asyncio.fixture
async def mock_referral_service(db_session, mock_event_service, test_lead):
    """Create real ReferralService with mocked dependencies for testing."""
    # Mock notification service
    mock_notification = AsyncMock()

    service = ReferralService(
        db=db_session,
        event_service=mock_event_service,
        notification_service=mock_notification,
    )
    service.notification_service = mock_notification

    # Mock _get_lead to bypass database enum issues and return test_lead
    async def mock_get_lead(lead_id):
        if str(lead_id) == str(test_lead.id):
            return test_lead
        return None

    service._get_lead = AsyncMock(side_effect=mock_get_lead)

    return service


@pytest_asyncio.fixture
async def mock_campaign_service(db_session, mock_event_service):
    """Create real NurtureCampaignService with mocked dependencies for testing."""
    # Mock notification service
    mock_notification = AsyncMock()

    service = NurtureCampaignService(
        db=db_session,
        event_service=mock_event_service,
        notification_service=mock_notification,
    )
    service.notification_service = mock_notification
    return service


@pytest_asyncio.fixture
async def test_lead(db_session):
    """Create a test lead in the database using raw SQL to avoid declarative_base conflicts.

    Note: Lead model uses legacy_declarative_base which conflicts with models.base.Base.
    Using raw SQL insertion to bypass SQLAlchemy model conflicts.
    """
    lead_id = uuid.uuid4()

    # Insert minimal test lead using raw SQL (only required columns)
    await db_session.execute(
        text(
            """
            INSERT INTO lead.leads (
                id, source, status, score, created_at, updated_at
            ) VALUES (
                :id, :source, :status, :score, :created_at, :updated_at
            )
        """
        ),
        {
            "id": lead_id,
            "source": "web_quote",  # Use actual enum VALUE (web_quote) not name (WEB_QUOTE)
            "status": "new",  # Valid LeadStatus enum value
            "score": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        },
    )
    await db_session.commit()

    # Return a simple object with just the ID (that's all tests need)
    class MockLead:
        def __init__(self):
            self.id = lead_id

    return MockLead()


@pytest_asyncio.fixture
async def test_subscriber(db_session):
    """Create a test subscriber in the database using raw SQL to avoid declarative_base conflicts.

    Note: Subscriber model uses legacy_declarative_base which conflicts with models.base.Base.
    Using raw SQL insertion to bypass SQLAlchemy model conflicts.
    Subscriber email/phone are encrypted, so we need to handle that properly.
    """
    subscriber_id = uuid.uuid4()
    subscriber_email = f"testsub{int(time.time())}@example.com"

    # Import CryptoUtil to encrypt email (required field)
    from src.models.legacy_encryption import CryptoUtil

    email_encrypted = CryptoUtil.encrypt_text(subscriber_email)

    # Insert test subscriber using raw SQL
    await db_session.execute(
        text(
            """
            INSERT INTO newsletter.subscribers (
                id, email_enc, subscribed, sms_consent, email_consent,
                engagement_score, total_emails_sent, total_emails_opened, total_clicks,
                created_at, updated_at
            ) VALUES (
                :id, :email_enc, :subscribed, :sms_consent, :email_consent,
                :engagement_score, :total_emails_sent, :total_emails_opened, :total_clicks,
                :created_at, :updated_at
            )
        """
        ),
        {
            "id": subscriber_id,
            "email_enc": email_encrypted,
            "subscribed": True,
            "sms_consent": False,
            "email_consent": True,
            "engagement_score": 0,
            "total_emails_sent": 0,
            "total_emails_opened": 0,
            "total_clicks": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        },
    )
    await db_session.commit()

    # Return a simple object with ID
    class MockSubscriber:
        def __init__(self):
            self.id = subscriber_id
            self.email = subscriber_email

    return MockSubscriber()
