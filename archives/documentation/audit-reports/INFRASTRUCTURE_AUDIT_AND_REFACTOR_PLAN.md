# Infrastructure Audit & Refactor Plan - Dependency Injection Focus

**Date:** November 13, 2025  
**Focus:** Clean Architecture, Reusable Modules, Dependency Injection

---

## 🎯 Executive Summary

After comprehensive infrastructure audit, we have identified:

- ✅ **85% of required infrastructure exists** (webhooks, campaigns,
  referrals, testing)
- 🔧 **30% needs refactoring** for dependency injection and modularity
- ⚠️ **Multiple duplicate implementations** requiring consolidation
- 🏗️ **Missing base classes** that would enable better code reuse

**Strategy:** Refactor existing code to use dependency injection,
create reusable base classes, eliminate duplication, and organize into
clean architectural layers.

---

## 📊 Current Infrastructure Status

### ✅ EXISTING INFRASTRUCTURE

#### 1. **Social Media Webhooks** (80% Complete)

**Locations:**

- `apps/backend/src/routers/v1/webhooks/meta_webhook.py` (403 lines) -
  Instagram/Facebook
- `apps/backend/src/api/ai/endpoints/routers/webhooks.py` (partial
  Meta handler)

**Current Issues:**

```python
# ❌ PROBLEM: Direct service instantiation in route handlers
from services.ai_lead_management import get_ai_lead_manager

async def meta_webhook(..., db: Session = Depends(get_db)):
    # Creates service instances inline
    existing_lead = db.query(Lead).filter(...).first()
    lead_event = Event(...)
    db.add(lead_event)
```

**Refactor Needed:**

1. **Dependency Injection Pattern:**
   - Extract webhook processing logic into `WebhookService`
   - Inject `LeadService`, `EventService`, `NotificationService`
   - Remove direct database queries from route handlers

2. **Base Webhook Handler:**
   - Create `BaseWebhookHandler` abstract class
   - Implement signature verification, idempotency, error handling
   - Derive `MetaWebhookHandler`, `RingCentralWebhookHandler`, etc.

**Reusable Components Found:**

- ✅ Signature verification functions (`verify_meta_signature`)
- ✅ Event tracking pattern (can be extracted to `EventService`)
- ✅ Lead creation logic (can use existing `LeadService`)

---

#### 2. **Lead & Nurture Campaign System** (70% Complete)

**Locations:**

- `apps/backend/src/services/lead_service.py` (760 lines) - Core lead
  management
- `apps/backend/src/services/ai_lead_management.py` (525 lines) - AI
  scoring & nurture
- `apps/backend/src/services/newsletter_service.py` (459 lines) -
  Campaign sending

**Current Issues:**

```python
# ❌ PROBLEM: Service creates its own dependencies
class LeadService:
    def __init__(self, db: AsyncSession, cache: CacheService | None = None):
        self.db = db
        self.cache = cache
        self.compliance = ComplianceValidator()  # Hard-coded instantiation

# ❌ PROBLEM: Global function instead of dependency injection
from services.ai_lead_management import get_ai_lead_manager

async def some_route():
    ai_manager = await get_ai_lead_manager()  # Global state
```

**Refactor Needed:**

1. **Dependency Injection:**

```python
# ✅ SOLUTION: Inject all dependencies
class LeadService:
    def __init__(
        self,
        db: AsyncSession,
        compliance_validator: ComplianceValidator,
        cache_service: CacheService,
        event_service: EventService,
        notification_service: NotificationService,
    ):
        self.db = db
        self.compliance = compliance_validator
        self.cache = cache_service
        self.events = event_service
        self.notifications = notification_service
```

2. **Service Provider Pattern:**

```python
# Create dependency provider
from core.dependencies import (
    get_lead_service,
    get_compliance_validator,
    get_cache_service,
)

@router.post("/api/v1/leads")
async def create_lead(
    data: LeadCreate,
    lead_service: LeadService = Depends(get_lead_service),
):
    return await lead_service.create_lead_with_consent(...)
```

**Reusable Components Found:**

- ✅ `LeadNurtureAI` class with message templates (already
  well-structured)
- ✅ Lead scoring logic (can be extracted to `LeadScoringService`)
- ✅ Campaign sending infrastructure (needs DI refactor)

---

#### 3. **Referral Tracking System** (40% Complete)

**Locations:**

- `apps/backend/src/db/migrations/alembic/versions/90164363b9b9_add_referral_tables.py` -
  Database schema ✅
- `apps/backend/scripts/create_consent_referral_tables.sql` - Consent
  & referral tables ✅

**Missing:**

- ❌ No `ReferralService` implementation
- ❌ No API endpoints (`/api/v1/referrals`)
- ❌ No referral code generation utility

**What to Build:**

1. **ReferralService with DI:**

```python
class ReferralService:
    def __init__(
        self,
        db: AsyncSession,
        lead_service: LeadService,
        booking_service: BookingService,
        notification_service: NotificationService,
    ):
        self.db = db
        self.leads = lead_service
        self.bookings = booking_service
        self.notifications = notification_service

    async def generate_referral_code(self, customer_id: UUID) -> str:
        """Generate unique referral code using customer name"""
        # Use existing SQL function: generate_referral_code()

    async def track_referral(self, code: str, referred_lead_id: UUID):
        """Track when referred lead converts"""

    async def calculate_rewards(self, referrer_id: UUID) -> dict:
        """Calculate total rewards earned"""
```

**Reusable Components:**

- ✅ Database schema already created
- ✅ Can reuse `LeadService` for lead tracking
- ✅ Can reuse `NotificationService` for reward notifications

---

#### 4. **Testing Infrastructure** (60% Complete)

**Locations:**

- `apps/customer/src/components/forms/__tests__/QuoteRequestForm.test.tsx` -
  Form tests ✅
- `apps/admin/src/hooks/__tests__/useEscalationWebSocket.test.ts` -
  Hook tests ✅
- `apps/backend/tests/test_newsletter_integration.py` - Integration
  tests ✅

**Test Patterns Found:**

```typescript
// ✅ GOOD: Reusable test patterns
describe('Form Validation', () => {
  it('should require phone field', async () => {
    render(<QuoteRequestForm />);
    const submitButton = screen.getByRole('button', { name: /submit/i });
    fireEvent.click(submitButton);
    await waitFor(() => {
      expect(screen.getByText(/phone is required/i)).toBeInTheDocument();
    });
  });
});
```

**Missing:**

- ❌ No tests for webhook handlers
- ❌ No tests for nurture campaign system
- ❌ No tests for referral tracking
- ❌ No shared test fixtures/utilities

**What to Build:**

1. **Shared Test Utilities:**

```python
# apps/backend/tests/conftest.py (enhance existing)

@pytest.fixture
async def lead_service(db_session, mock_compliance, mock_cache):
    """Provide LeadService with mocked dependencies"""
    return LeadService(
        db=db_session,
        compliance_validator=mock_compliance,
        cache_service=mock_cache,
        event_service=mock_event_service,
    )

@pytest.fixture
def mock_webhook_payload():
    """Standard webhook payload for testing"""
    return {
        "object": "page",
        "entry": [{
            "id": "123456",
            "messaging": [{
                "sender": {"id": "7890"},
                "message": {"text": "I want to book hibachi"}
            }]
        }]
    }
```

---

#### 5. **Compliance System** (90% Complete)

**Location:**

- `apps/backend/src/core/compliance.py` (335 lines) - TCPA/CAN-SPAM
  validators ✅

**Current State:**

- ✅ ComplianceConfig with business data
- ✅ ConsentRecord model with audit trail
- ✅ ComplianceValidator with validation methods

**Already Well-Structured:**

```python
class ComplianceValidator:
    def __init__(self, config: ComplianceConfig | None = None):
        self.config = config or ComplianceConfig()

    def validate_sms_consent(...):
        """Validate TCPA SMS consent"""

    def validate_email_consent(...):
        """Validate CAN-SPAM email consent"""
```

**No Refactor Needed** - Already uses dependency injection pattern!

---

## 🏗️ Refactor Architecture

### Phase 1: Create Dependency Injection Foundation (4 hours)

#### 1.1 Create Core Dependencies Module

**File:** `apps/backend/src/core/dependencies.py`

```python
"""
Dependency Injection Providers
Central location for all service dependencies
"""

from functools import lru_cache
from typing import AsyncGenerator

from core.cache import CacheService
from core.compliance import ComplianceValidator, ComplianceConfig
from core.database import get_async_session
from services.lead_service import LeadService
from services.newsletter_service import NewsletterService
from services.event_service import EventService
from services.notification_service import NotificationService
from services.referral_service import ReferralService
from services.webhook_service import WebhookService
from sqlalchemy.ext.asyncio import AsyncSession


# Singleton instances (stateless services)
@lru_cache()
def get_compliance_validator() -> ComplianceValidator:
    """Get singleton compliance validator"""
    return ComplianceValidator(config=ComplianceConfig())


@lru_cache()
def get_cache_service() -> CacheService:
    """Get singleton cache service"""
    return CacheService()


# Database-dependent services (new instance per request)
async def get_lead_service(
    db: AsyncSession = Depends(get_async_session),
    compliance: ComplianceValidator = Depends(get_compliance_validator),
    cache: CacheService = Depends(get_cache_service),
) -> LeadService:
    """Get lead service with injected dependencies"""
    event_service = EventService(db)
    notification_service = NotificationService(db)

    return LeadService(
        db=db,
        compliance_validator=compliance,
        cache_service=cache,
        event_service=event_service,
        notification_service=notification_service,
    )


async def get_newsletter_service(
    db: AsyncSession = Depends(get_async_session),
    compliance: ComplianceValidator = Depends(get_compliance_validator),
) -> NewsletterService:
    """Get newsletter service with injected dependencies"""
    return NewsletterService(
        db=db,
        compliance_validator=compliance,
    )


async def get_referral_service(
    db: AsyncSession = Depends(get_async_session),
    lead_service: LeadService = Depends(get_lead_service),
) -> ReferralService:
    """Get referral service with injected dependencies"""
    return ReferralService(
        db=db,
        lead_service=lead_service,
    )


async def get_webhook_service(
    db: AsyncSession = Depends(get_async_session),
    lead_service: LeadService = Depends(get_lead_service),
    event_service: EventService = Depends(get_event_service),
) -> WebhookService:
    """Get webhook service with injected dependencies"""
    return WebhookService(
        db=db,
        lead_service=lead_service,
        event_service=event_service,
    )
```

**Benefits:**

- ✅ Single source of truth for all dependencies
- ✅ Easy to mock in tests
- ✅ Automatic dependency resolution
- ✅ FastAPI integration with `Depends()`

---

#### 1.2 Create Base Service Classes

**File:** `apps/backend/src/core/base_service.py`

```python
"""
Base service classes with common patterns
"""

from abc import ABC
from sqlalchemy.ext.asyncio import AsyncSession
import logging


class BaseService(ABC):
    """Base class for all services"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)

    async def commit(self):
        """Commit current transaction"""
        await self.db.commit()

    async def rollback(self):
        """Rollback current transaction"""
        await self.db.rollback()

    async def refresh(self, instance):
        """Refresh instance from database"""
        await self.db.refresh(instance)


class EventTrackingMixin:
    """Mixin for services that track events"""

    def __init__(self, event_service: EventService):
        self.events = event_service

    async def track_event(self, event_type: str, entity_type: str, entity_id: str, data: dict):
        """Track an event"""
        await self.events.create_event(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            data=data,
        )


class NotificationMixin:
    """Mixin for services that send notifications"""

    def __init__(self, notification_service: NotificationService):
        self.notifications = notification_service

    async def notify(self, recipient: str, message: str, channel: str):
        """Send notification"""
        await self.notifications.send(
            recipient=recipient,
            message=message,
            channel=channel,
        )
```

---

### Phase 2: Refactor Services with DI (8 hours)

#### 2.1 Refactor LeadService

**File:** `apps/backend/src/services/lead_service.py`

```python
# BEFORE (current):
class LeadService:
    def __init__(self, db: AsyncSession, cache: CacheService | None = None):
        self.db = db
        self.cache = cache
        self.compliance = ComplianceValidator()  # ❌ Hard-coded

# AFTER (refactored):
from core.base_service import BaseService, EventTrackingMixin, NotificationMixin

class LeadService(BaseService, EventTrackingMixin, NotificationMixin):
    """Lead management service with DI"""

    def __init__(
        self,
        db: AsyncSession,
        compliance_validator: ComplianceValidator,
        cache_service: CacheService,
        event_service: EventService,
        notification_service: NotificationService,
    ):
        BaseService.__init__(self, db)
        EventTrackingMixin.__init__(self, event_service)
        NotificationMixin.__init__(self, notification_service)

        self.compliance = compliance_validator
        self.cache = cache_service

    async def create_lead_with_consent(self, ...):
        """Create lead with full DI"""
        # Use injected compliance validator
        if consent_data.get('sms_consent'):
            self.compliance.validate_sms_consent(...)

        # Use injected event tracker
        await self.track_event(
            event_type="lead_created",
            entity_type="lead",
            entity_id=str(lead.id),
            data={"source": source},
        )

        # Use injected notification service
        await self.notify(
            recipient=lead.phone,
            message="Welcome to My Hibachi Chef!",
            channel="sms",
        )
```

---

#### 2.2 Create WebhookService (New)

**File:** `apps/backend/src/services/webhook_service.py`

```python
"""
Webhook Processing Service
Handles all webhook processing with DI
"""

from abc import ABC, abstractmethod
import hmac
import hashlib
from typing import Any

from core.base_service import BaseService
from services.lead_service import LeadService
from services.event_service import EventService


class BaseWebhookHandler(ABC):
    """Base class for webhook handlers"""

    def __init__(self, secret: str):
        self.secret = secret

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature"""
        if not signature or not self.secret:
            return False

        expected = "sha256=" + hmac.new(
            self.secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected)

    @abstractmethod
    async def process_message(self, data: dict) -> dict:
        """Process webhook message (implement in subclass)"""
        pass


class MetaWebhookHandler(BaseWebhookHandler):
    """Facebook/Instagram webhook handler"""

    def __init__(
        self,
        secret: str,
        lead_service: LeadService,
        event_service: EventService,
    ):
        super().__init__(secret)
        self.leads = lead_service
        self.events = event_service

    async def process_message(self, data: dict) -> dict:
        """Process Meta webhook message"""
        sender_id = data.get("sender", {}).get("id")
        message_text = data.get("message", {}).get("text", "")

        # Use injected lead service
        lead = await self.leads.find_or_create_from_social(
            platform="instagram",
            social_id=sender_id,
            message=message_text,
        )

        # Use injected event service
        await self.events.create_event(
            event_type="message_received",
            entity_type="lead",
            entity_id=str(lead.id),
            data={"text": message_text},
        )

        return {"lead_id": str(lead.id), "status": "processed"}


class WebhookService(BaseService):
    """Main webhook service with DI"""

    def __init__(
        self,
        db: AsyncSession,
        lead_service: LeadService,
        event_service: EventService,
    ):
        super().__init__(db)
        self.leads = lead_service
        self.events = event_service

    def get_handler(self, platform: str, secret: str) -> BaseWebhookHandler:
        """Get webhook handler for platform"""
        handlers = {
            "meta": MetaWebhookHandler,
            "ringcentral": RingCentralWebhookHandler,
        }

        handler_class = handlers.get(platform)
        if not handler_class:
            raise ValueError(f"Unknown platform: {platform}")

        return handler_class(
            secret=secret,
            lead_service=self.leads,
            event_service=self.events,
        )
```

---

#### 2.3 Refactor Webhook Routes

**File:** `apps/backend/src/routers/v1/webhooks/meta_webhook.py`

```python
# BEFORE (current - 403 lines of mixed concerns):
async def meta_webhook(request: Request, db: Session = Depends(get_db)):
    # Direct database queries
    existing_lead = db.query(Lead).filter(...).first()
    lead_event = Event(...)
    db.add(lead_event)
    # ... more mixed logic

# AFTER (refactored - clean route handler):
from core.dependencies import get_webhook_service
from services.webhook_service import WebhookService

@router.post("/webhook")
async def meta_webhook(
    request: Request,
    webhook_service: WebhookService = Depends(get_webhook_service),
    x_hub_signature: str = Header(None),
):
    """Handle Meta webhook with DI"""

    # Get raw payload
    payload = await request.body()
    webhook_data = await request.json()

    # Get handler from service
    handler = webhook_service.get_handler(
        platform="meta",
        secret=settings.meta_app_secret,
    )

    # Verify signature
    if not handler.verify_signature(payload, x_hub_signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    # Process webhook
    results = []
    for entry in webhook_data.get("entry", []):
        for messaging in entry.get("messaging", []):
            result = await handler.process_message(messaging)
            results.append(result)

    return {"status": "processed", "results": results}
```

**Benefits:**

- ✅ Route handler reduced from 403 lines to ~30 lines
- ✅ All business logic in service layer
- ✅ Easy to test (mock webhook_service)
- ✅ Reusable handler pattern for other webhooks

---

### Phase 3: Create Missing Services (6 hours)

#### 3.1 Create ReferralService

**File:** `apps/backend/src/services/referral_service.py`

```python
"""
Referral Tracking Service
Manages referral codes, tracking, and rewards
"""

from uuid import UUID
import secrets
import string

from core.base_service import BaseService
from models.referral import Referral, ReferralReward
from services.lead_service import LeadService


class ReferralService(BaseService):
    """Referral tracking service with DI"""

    def __init__(
        self,
        db: AsyncSession,
        lead_service: LeadService,
    ):
        super().__init__(db)
        self.leads = lead_service

    async def generate_referral_code(self, customer_id: UUID, name: str) -> str:
        """Generate unique referral code"""
        # Use customer name + random suffix
        base = ''.join(filter(str.isalnum, name.upper()))[:6]
        suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
        code = f"{base}{suffix}"

        # Check uniqueness
        existing = await self.db.execute(
            select(Referral).where(Referral.referral_code == code)
        )
        if existing.scalar_one_or_none():
            # Recursive retry
            return await self.generate_referral_code(customer_id, name)

        return code

    async def create_referral(self, customer_id: UUID, name: str) -> Referral:
        """Create referral record with unique code"""
        code = await self.generate_referral_code(customer_id, name)

        referral = Referral(
            customer_id=customer_id,
            referral_code=code,
            total_referrals=0,
            total_conversions=0,
        )

        self.db.add(referral)
        await self.commit()
        await self.refresh(referral)

        return referral

    async def track_referral(self, code: str, referred_lead_id: UUID):
        """Track when referred lead is created"""
        referral = await self.get_by_code(code)
        if not referral:
            raise ValueError(f"Invalid referral code: {code}")

        referral.total_referrals += 1
        await self.commit()

    async def track_conversion(self, referred_lead_id: UUID):
        """Track when referred lead converts to booking"""
        # Find referral by lead
        # Update total_conversions
        # Check if reward unlocked
        pass
```

---

#### 3.2 Create EventService

**File:** `apps/backend/src/services/event_service.py`

```python
"""
Event Tracking Service
Centralized event tracking for audit trail
"""

from uuid import UUID
from datetime import datetime

from core.base_service import BaseService
from models.legacy_core import Event


class EventService(BaseService):
    """Event tracking service"""

    async def create_event(
        self,
        event_type: str,
        entity_type: str,
        entity_id: str,
        data: dict | None = None,
        user_id: UUID | None = None,
    ) -> Event:
        """Create and persist an event"""
        event = Event(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            data=data or {},
            user_id=user_id,
            timestamp=datetime.now(),
        )

        self.db.add(event)
        await self.commit()

        return event

    async def get_events_for_entity(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 50,
    ) -> list[Event]:
        """Get event history for an entity"""
        result = await self.db.execute(
            select(Event)
            .where(
                Event.entity_type == entity_type,
                Event.entity_id == entity_id,
            )
            .order_by(Event.timestamp.desc())
            .limit(limit)
        )
        return result.scalars().all()
```

---

### Phase 4: Testing with DI (4 hours)

#### 4.1 Create Test Fixtures

**File:** `apps/backend/tests/conftest.py`

```python
"""
Shared test fixtures with DI
"""

import pytest
from unittest.mock import AsyncMock, Mock

from core.compliance import ComplianceValidator
from core.cache import CacheService
from services.lead_service import LeadService
from services.event_service import EventService
from services.webhook_service import WebhookService


@pytest.fixture
def mock_compliance():
    """Mock compliance validator"""
    compliance = Mock(spec=ComplianceValidator)
    compliance.validate_sms_consent = Mock(return_value=True)
    compliance.validate_email_consent = Mock(return_value=True)
    return compliance


@pytest.fixture
def mock_cache():
    """Mock cache service"""
    cache = Mock(spec=CacheService)
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    return cache


@pytest.fixture
def mock_event_service(db_session):
    """Mock event service"""
    return EventService(db_session)


@pytest.fixture
def lead_service(db_session, mock_compliance, mock_cache, mock_event_service):
    """Lead service with mocked dependencies"""
    mock_notification = Mock()

    return LeadService(
        db=db_session,
        compliance_validator=mock_compliance,
        cache_service=mock_cache,
        event_service=mock_event_service,
        notification_service=mock_notification,
    )


@pytest.fixture
def webhook_service(db_session, lead_service, mock_event_service):
    """Webhook service with mocked dependencies"""
    return WebhookService(
        db=db_session,
        lead_service=lead_service,
        event_service=mock_event_service,
    )


@pytest.fixture
def meta_webhook_payload():
    """Standard Meta webhook payload"""
    return {
        "object": "page",
        "entry": [{
            "id": "123456",
            "messaging": [{
                "sender": {"id": "7890"},
                "recipient": {"id": "123456"},
                "message": {
                    "mid": "msg_123",
                    "text": "I want to book hibachi for 20 people"
                }
            }]
        }]
    }
```

#### 4.2 Create Webhook Tests

**File:** `apps/backend/tests/services/test_webhook_service.py`

```python
"""
Tests for webhook service with DI
"""

import pytest
from services.webhook_service import WebhookService, MetaWebhookHandler


@pytest.mark.asyncio
class TestWebhookService:
    """Test webhook service"""

    async def test_get_handler_meta(self, webhook_service):
        """Test getting Meta webhook handler"""
        handler = webhook_service.get_handler("meta", "test_secret")

        assert isinstance(handler, MetaWebhookHandler)
        assert handler.secret == "test_secret"

    async def test_verify_signature_valid(self, webhook_service):
        """Test signature verification with valid signature"""
        handler = webhook_service.get_handler("meta", "test_secret")

        payload = b'{"test": "data"}'
        # Generate valid signature
        import hmac, hashlib
        signature = "sha256=" + hmac.new(
            b"test_secret",
            payload,
            hashlib.sha256
        ).hexdigest()

        assert handler.verify_signature(payload, signature) is True

    async def test_process_message_creates_lead(
        self,
        webhook_service,
        meta_webhook_payload,
        db_session,
    ):
        """Test processing message creates lead"""
        handler = webhook_service.get_handler("meta", "test_secret")

        messaging = meta_webhook_payload["entry"][0]["messaging"][0]
        result = await handler.process_message(messaging)

        assert "lead_id" in result
        assert result["status"] == "processed"

        # Verify lead was created
        from models.legacy_lead_newsletter import Lead
        lead = await db_session.execute(
            select(Lead).where(Lead.id == result["lead_id"])
        )
        assert lead.scalar_one_or_none() is not None
```

---

## 📋 Implementation Checklist

### Week 1: Foundation (12 hours)

- [ ] Create `core/dependencies.py` with DI providers (2h)
- [ ] Create `core/base_service.py` with base classes (2h)
- [ ] Refactor `LeadService` with DI (3h)
- [ ] Refactor `NewsletterService` with DI (2h)
- [ ] Create `EventService` (2h)
- [ ] Update all route handlers to use DI (1h)

### Week 2: Services (14 hours)

- [ ] Create `WebhookService` with base handler (4h)
- [ ] Refactor Meta webhook routes (2h)
- [ ] Create `ReferralService` (3h)
- [ ] Create referral API endpoints (2h)
- [ ] Create `NurtureCampaignService` (3h)

### Week 3: Testing (10 hours)

- [ ] Create shared test fixtures (2h)
- [ ] Write webhook service tests (3h)
- [ ] Write referral service tests (2h)
- [ ] Write nurture campaign tests (2h)
- [ ] Write integration tests (1h)

### Week 4: Compliance & Documentation (4 hours)

- [ ] Compliance audit (2h)
- [ ] Update documentation (1h)
- [ ] Final testing and validation (1h)

---

## 🎯 Benefits of This Refactor

### Performance Improvements

- ✅ **Lazy initialization** - Services only created when needed
- ✅ **Connection pooling** - Database sessions properly managed
- ✅ **Reduced imports** - Only import what's needed via DI
- ✅ **Singleton caching** - Stateless services reused across requests

### Code Quality Improvements

- ✅ **Single Responsibility** - Each service has one job
- ✅ **Testability** - Easy to mock dependencies
- ✅ **Maintainability** - Change dependencies without changing
  services
- ✅ **Reusability** - Base classes reduce duplication

### Developer Experience

- ✅ **Clear dependencies** - No hidden global state
- ✅ **Type safety** - Full type hints on all services
- ✅ **Easier debugging** - Dependencies explicit in constructor
- ✅ **Better IDE support** - Autocomplete works properly

---

## 📊 Directory Structure After Refactor

```
apps/backend/src/
├── core/
│   ├── dependencies.py          # ✨ NEW - DI providers
│   ├── base_service.py          # ✨ NEW - Base service classes
│   ├── compliance.py            # ✅ EXISTING - Already good
│   ├── database.py              # ✅ EXISTING
│   └── cache.py                 # ✅ EXISTING
│
├── services/
│   ├── lead_service.py          # 🔧 REFACTOR - Add DI
│   ├── newsletter_service.py    # 🔧 REFACTOR - Add DI
│   ├── webhook_service.py       # ✨ NEW - Unified webhook handling
│   ├── event_service.py         # ✨ NEW - Event tracking
│   ├── referral_service.py      # ✨ NEW - Referral tracking
│   ├── nurture_campaign_service.py # ✨ NEW - Nurture automation
│   └── ai_lead_management.py    # ✅ EXISTING - Already good
│
├── routers/v1/
│   ├── webhooks/
│   │   └── meta_webhook.py      # 🔧 REFACTOR - Use WebhookService
│   ├── leads.py                 # 🔧 REFACTOR - Use DI
│   ├── referrals.py             # ✨ NEW - Referral endpoints
│   └── campaigns.py             # 🔧 ENHANCE - Add nurture campaigns
│
└── tests/
    ├── conftest.py              # 🔧 ENHANCE - Add DI fixtures
    ├── services/
    │   ├── test_webhook_service.py # ✨ NEW
    │   ├── test_referral_service.py # ✨ NEW
    │   └── test_lead_service.py    # 🔧 ENHANCE
    └── integration/
        └── test_webhook_flow.py    # ✨ NEW
```

---

## 🚀 Next Steps

1. **Review this audit** - Confirm architecture decisions
2. **Start with Phase 1** - Create DI foundation
3. **Incrementally refactor** - One service at a time
4. **Test continuously** - Unit tests for each refactor
5. **Update documentation** - Keep docs in sync

**Estimated Total Time:** 40 hours (1 week full-time)
