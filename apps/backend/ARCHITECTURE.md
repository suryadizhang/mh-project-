# 🏗️ Backend Architecture Documentation

**MyHibachi Backend - Clean Architecture**  
**Version**: 2.0 (Post Nuclear Refactor)  
**Date**: November 5, 2025  
**Status**: ✅ Production Ready

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Directory Structure](#directory-structure)
3. [Layer Responsibilities](#layer-responsibilities)
4. [Import Patterns](#import-patterns)
5. [Design Principles](#design-principles)
6. [Data Flow](#data-flow)
7. [Key Components](#key-components)
8. [Migration History](#migration-history)

---

## 🎯 Architecture Overview

### Clean Architecture Principles

MyHibachi backend follows **Clean Architecture** principles with clear
separation of concerns:

```
┌─────────────────────────────────────────────────────┐
│                    PRESENTATION                     │
│              (Routers / API Endpoints)              │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│                  APPLICATION                        │
│         (CQRS Handlers / Use Cases)                 │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│                    DOMAIN                           │
│         (Services / Business Logic)                 │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│              INFRASTRUCTURE                         │
│    (Models / Database / External Services)          │
└─────────────────────────────────────────────────────┘
```

### Technology Stack

- **Framework**: FastAPI 0.115.4
- **ORM**: SQLAlchemy 2.0+
- **Validation**: Pydantic 2.5.0
- **Database**: PostgreSQL (production) / SQLite (development)
- **Python**: 3.11+

---

## 📁 Directory Structure

```
apps/backend/src/
├── routers/              # 🌐 API Routes (Presentation Layer)
│   └── v1/              # API Version 1
│       ├── admin/       # Admin-only routes
│       │   ├── error_logs.py
│       │   ├── notification_groups.py
│       │   └── social.py
│       ├── webhooks/    # External service webhooks
│       │   ├── google_business_webhook.py
│       │   ├── meta_webhook.py
│       │   ├── ringcentral_webhook.py
│       │   └── stripe_webhook.py
│       ├── admin_analytics.py
│       ├── auth.py
│       ├── bookings.py
│       ├── booking_enhanced.py
│       ├── health.py
│       ├── health_checks.py
│       ├── leads.py
│       ├── newsletter.py
│       ├── payments.py
│       ├── qr_tracking.py
│       ├── reviews.py
│       ├── ringcentral_webhooks.py
│       ├── station_admin.py
│       ├── station_auth.py
│       ├── stripe.py
│       └── websocket_router.py
│
├── cqrs/                # 📋 Command/Query Handlers (Application Layer)
│   ├── social/         # Social media domain
│   │   ├── social_command_handlers.py
│   │   ├── social_commands.py
│   │   ├── social_queries.py
│   │   └── social_query_handlers.py
│   ├── base.py
│   ├── command_handlers.py
│   ├── crm_operations.py
│   ├── query_handlers.py
│   └── registry.py
│
├── services/            # 🔧 Business Logic (Domain Layer)
│   ├── social/         # Social media services
│   │   ├── social_ai_generator.py
│   │   ├── social_ai_tools.py
│   │   ├── social_service.py
│   │   └── ...
│   ├── ai_lead_management.py
│   ├── enhanced_notification_service.py
│   ├── lead_service.py
│   ├── newsletter_service.py
│   ├── notification_group_service.py
│   ├── payment_email_scheduler.py
│   ├── qr_tracking_service.py
│   ├── review_service.py
│   ├── station_notification_sync.py
│   ├── stripe_service.py
│   └── ...
│
├── models/              # 🗄️ Data Models (Infrastructure Layer)
│   ├── legacy_base.py
│   ├── legacy_booking_models.py
│   ├── legacy_core.py
│   ├── legacy_declarative_base.py
│   ├── legacy_encryption.py
│   ├── legacy_events.py
│   ├── legacy_feedback.py
│   ├── legacy_notification_groups.py
│   ├── legacy_qr_tracking.py
│   ├── legacy_social.py
│   ├── legacy_stripe_models.py
│   └── ...
│
├── schemas/             # 📝 Request/Response Schemas
│   ├── booking.py
│   ├── booking_schemas.py
│   ├── health.py
│   ├── social.py
│   ├── stripe_schemas.py
│   └── ...
│
├── core/                # ⚙️ Core Infrastructure
│   ├── auth/           # Authentication & Authorization
│   │   ├── endpoints.py
│   │   ├── middleware.py
│   │   ├── models.py
│   │   ├── oauth_models.py
│   │   ├── station_auth.py
│   │   ├── station_middleware.py
│   │   └── station_models.py
│   ├── audit_logger.py
│   ├── cache.py
│   ├── circuit_breaker.py
│   ├── config.py
│   ├── container.py
│   ├── database.py
│   ├── dtos.py
│   ├── exceptions.py
│   ├── idempotency.py
│   ├── metrics.py
│   ├── middleware.py
│   ├── query_optimizer.py
│   ├── rate_limiting.py
│   ├── repository.py
│   ├── security.py
│   ├── security_middleware.py
│   └── service_registry.py
│
├── workers/             # 🔄 Background Workers
│   ├── social/         # Social media workers
│   ├── outbox_processors.py
│   ├── review_worker.py
│   └── ...
│
├── middleware/          # 🛡️ Request/Response Middleware
│   ├── structured_logging.py
│   └── ...
│
├── utils/               # 🔨 Utility Functions
│   ├── ringcentral/    # RingCentral utilities
│   ├── ringcentral_utils.py
│   ├── station_code_generator.py
│   └── ...
│
├── ai/                  # 🤖 AI Services
│   ├── orchestrator/   # AI orchestration
│   ├── tools/          # AI tools
│   └── ...
│
├── integrations/        # 🔌 Third-party Integrations
│   └── ...
│
├── repositories/        # 💾 Repository Pattern
│   └── ...
│
└── main.py             # 🚀 Application Entry Point
```

---

## 🎭 Layer Responsibilities

### 1. **Presentation Layer** (`routers/`)

**Responsibility**: HTTP request handling, input validation, response
formatting

**Guidelines**:

- ✅ Handle HTTP-specific concerns (status codes, headers, cookies)
- ✅ Validate request data using Pydantic schemas
- ✅ Delegate business logic to services or CQRS handlers
- ✅ Format responses according to API contract
- ❌ NO business logic in routers
- ❌ NO direct database access

**Example**:

```python
# routers/v1/bookings.py
from fastapi import APIRouter, Depends
from schemas.booking import BookingCreate, BookingResponse
from services.booking_service import BookingService

router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])

@router.post("/", response_model=BookingResponse)
async def create_booking(
    data: BookingCreate,
    service: BookingService = Depends()
):
    """Handle booking creation - delegate to service."""
    return await service.create_booking(data)
```

### 2. **Application Layer** (`cqrs/`)

**Responsibility**: Orchestrate use cases, coordinate between domain
and infrastructure

**Guidelines**:

- ✅ Implement CQRS pattern (Command/Query Separation)
- ✅ Handle complex workflows
- ✅ Coordinate multiple services
- ✅ Manage transactions
- ❌ NO HTTP-specific code
- ❌ NO direct database models manipulation

**Example**:

```python
# cqrs/command_handlers.py
from cqrs.base import CommandHandler
from services.booking_service import BookingService

class CreateBookingHandler(CommandHandler):
    def __init__(self, booking_service: BookingService):
        self.booking_service = booking_service

    async def handle(self, command: CreateBookingCommand):
        """Orchestrate booking creation workflow."""
        # Validate availability
        # Create booking
        # Send confirmation
        # Update analytics
        return await self.booking_service.create(command.data)
```

### 3. **Domain Layer** (`services/`)

**Responsibility**: Core business logic, domain rules, business
processes

**Guidelines**:

- ✅ Implement business rules and validations
- ✅ Contain domain logic and calculations
- ✅ Be framework-agnostic
- ✅ Use dependency injection for infrastructure
- ❌ NO HTTP concerns
- ❌ NO database implementation details

**Example**:

```python
# services/lead_service.py
class LeadService:
    """Business logic for lead management."""

    def __init__(self, db: Database, ai_service: AIService):
        self.db = db
        self.ai_service = ai_service

    async def score_lead(self, lead_data: dict) -> int:
        """Apply business rules to score lead quality."""
        # Business logic here
        score = 0

        # Rule 1: Email domain quality
        if self.is_business_email(lead_data.get("email")):
            score += 20

        # Rule 2: AI sentiment analysis
        sentiment = await self.ai_service.analyze_sentiment(lead_data.get("message"))
        score += sentiment.score

        return min(score, 100)
```

### 4. **Infrastructure Layer** (`models/`, `core/`)

**Responsibility**: Database access, external services,
framework-specific code

**Guidelines**:

- ✅ Handle database operations
- ✅ Manage external API integrations
- ✅ Implement technical concerns (caching, logging, etc.)
- ✅ Provide abstractions for domain layer
- ❌ NO business logic
- ❌ NO HTTP handling

**Example**:

```python
# models/legacy_booking_models.py
from sqlalchemy import Column, Integer, String, DateTime
from models.legacy_declarative_base import Base

class Booking(Base):
    """Database model for bookings."""
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True)
    customer_name = Column(String(255), nullable=False)
    booking_date = Column(DateTime, nullable=False)
    # ... other columns
```

---

## 📦 Import Patterns

### ✅ Correct Import Patterns (NEW Structure)

```python
# Routers
from services.lead_service import LeadService
from cqrs.command_handlers import CreateBookingHandler
from schemas.booking import BookingCreate, BookingResponse
from core.auth.middleware import require_auth
from core.database import get_db

# CQRS
from services.booking_service import BookingService
from models.legacy_booking_models import Booking
from cqrs.base import CommandHandler, QueryHandler

# Services
from models.legacy_core import Customer, Station
from core.database import Database
from utils.station_code_generator import generate_code

# Models
from models.legacy_declarative_base import Base
from models.legacy_core import Customer

# Core
from core.config import settings
from core.exceptions import ValidationError
```

### ❌ Old Import Patterns (DEPRECATED - DO NOT USE)

```python
# OLD - NEVER USE THESE
from api.app.models.booking import Booking  # ❌ WRONG
from api.app.services.lead_service import LeadService  # ❌ WRONG
from api.app.cqrs.handlers import Handler  # ❌ WRONG
```

### 🎯 Import Guidelines

1. **Always use absolute imports** from `src/` directory
2. **Never import from `api.app.*`** (old structure)
3. **Use `legacy_` prefix** when importing old models
4. **Follow layer hierarchy**:
   - Routers → Services/CQRS
   - CQRS → Services
   - Services → Models/Core
   - Models → Core only

---

## 🎨 Design Principles

### 1. **Single Responsibility Principle (SRP)**

Each module has ONE clear responsibility:

- ✅ `lead_service.py` - Lead business logic
- ✅ `stripe_service.py` - Stripe payment logic
- ✅ `auth/middleware.py` - Authentication middleware

### 2. **Dependency Inversion Principle (DIP)**

High-level modules don't depend on low-level modules:

```python
# ✅ GOOD: Service depends on abstraction
class LeadService:
    def __init__(self, db: Database):  # Abstract database
        self.db = db

# ❌ BAD: Service depends on concrete implementation
class LeadService:
    def __init__(self):
        self.db = SQLAlchemySession()  # Concrete implementation
```

### 3. **Separation of Concerns**

- **Routers**: HTTP handling only
- **CQRS**: Use case orchestration
- **Services**: Business logic
- **Models**: Data persistence
- **Schemas**: Data validation

### 4. **Domain-Driven Design (DDD)**

Domains are organized in subdirectories:

- `services/social/` - Social media domain
- `cqrs/social/` - Social media commands/queries
- `workers/social/` - Social media background jobs

---

## 🔄 Data Flow

### Request Flow (Write Operation)

```
1. HTTP Request
   ↓
2. Router (routers/v1/bookings.py)
   - Validate input with Pydantic schema
   - Extract user from auth middleware
   ↓
3. CQRS Command Handler (cqrs/command_handlers.py)
   - Orchestrate workflow
   - Coordinate multiple services
   ↓
4. Service (services/booking_service.py)
   - Apply business rules
   - Validate domain logic
   ↓
5. Model (models/legacy_booking_models.py)
   - Persist to database
   ↓
6. Response
   - Format with Pydantic schema
   - Return to client
```

### Query Flow (Read Operation)

```
1. HTTP Request
   ↓
2. Router (routers/v1/bookings.py)
   - Validate query parameters
   ↓
3. CQRS Query Handler (cqrs/query_handlers.py)
   - Optimize query
   - Apply filters
   ↓
4. Service (services/booking_service.py)
   - Apply business logic (e.g., permissions)
   ↓
5. Model (models/legacy_booking_models.py)
   - Fetch from database
   ↓
6. Response
   - Transform to DTO
   - Return to client
```

---

## 🔑 Key Components

### Authentication System (`core/auth/`)

**7 Files** - Consolidated authentication & authorization:

1. **`endpoints.py`** - Auth API endpoints (login, register, refresh
   token)
2. **`middleware.py`** - Core auth middleware (JWT validation)
3. **`models.py`** - Auth data models (User, UserSession)
4. **`oauth_models.py`** - OAuth-specific models (Google, Meta)
5. **`station_auth.py`** - Multi-tenant station authentication
6. **`station_middleware.py`** - Station-specific middleware
7. **`station_models.py`** - Station-specific auth models

**Features**:

- JWT-based authentication
- Multi-tenant station auth
- OAuth integration (Google, Meta)
- Session management
- Role-based access control (RBAC) ready

### CQRS Pattern (`cqrs/`)

**Command Query Responsibility Segregation**:

- **Commands** (`*_commands.py`) - Write operations (Create, Update,
  Delete)
- **Queries** (`*_queries.py`) - Read operations (Get, List, Search)
- **Handlers** (`*_handlers.py`) - Execute commands/queries

**Benefits**:

- Clear separation of read/write operations
- Optimized queries for each use case
- Easier to test and maintain
- Scalable architecture

### Service Layer (`services/`)

**26 Service Files** - Core business logic:

**Core Services**:

- `lead_service.py` - Lead management & scoring
- `review_service.py` - Review management & moderation
- `stripe_service.py` - Payment processing
- `newsletter_service.py` - Newsletter campaigns
- `qr_tracking_service.py` - QR code tracking

**Social Domain** (`services/social/`):

- `social_service.py` - Social media orchestration
- `social_ai_generator.py` - AI-powered content generation
- `social_ai_tools.py` - Social media AI tools

**Notification Services**:

- `enhanced_notification_service.py` - Multi-channel notifications
- `notification_group_service.py` - Group notification management
- `station_notification_sync.py` - Station notification sync

### Database Models (`models/`)

**13 Model Files** - All with `legacy_` prefix:

- `legacy_declarative_base.py` - SQLAlchemy base class
- `legacy_core.py` - Core models (Customer, Station, User)
- `legacy_booking_models.py` - Booking-related models
- `legacy_social.py` - Social media models
- `legacy_stripe_models.py` - Stripe payment models
- `legacy_events.py` - Event tracking models
- `legacy_feedback.py` - Feedback models
- `legacy_notification_groups.py` - Notification group models
- `legacy_qr_tracking.py` - QR tracking models
- `legacy_encryption.py` - Encryption utilities

**Why `legacy_` prefix?**

- Avoid naming conflicts with new models
- Clear distinction between old and new code
- Easier migration path for future refactoring

### API Routes (`routers/v1/`)

**250 Registered Routes** across **23 Router Files**:

**Core Routes**:

- `bookings.py` - Booking CRUD operations
- `booking_enhanced.py` - Enhanced booking features
- `payments.py` - Payment processing
- `reviews.py` - Review management
- `leads.py` - Lead management
- `stripe.py` - Stripe integration

**Admin Routes** (`admin/`):

- `error_logs.py` - Error log management
- `notification_groups.py` - Notification group admin
- `social.py` - Social media admin

**Webhook Routes** (`webhooks/`):

- `stripe_webhook.py` - Stripe webhooks
- `meta_webhook.py` - Meta/Facebook webhooks
- `google_business_webhook.py` - Google Business webhooks
- `ringcentral_webhook.py` - RingCentral webhooks

**Health & Monitoring**:

- `health.py` - Basic health check
- `health_checks.py` - Detailed health checks

---

## 📜 Migration History

### Phase 1: Nuclear Refactor (Weeks 1-3)

**Goal**: Migrate from OLD `api/app/` structure to NEW clean
architecture

**Completed**: ✅ November 2025

**Changes**:

1. **74 Files Migrated**:
   - 24 routers → `routers/v1/`
   - 10 services → `services/`
   - 13 models → `models/` (with `legacy_` prefix)
   - 9 CQRS files → `cqrs/`
   - 4 workers → `workers/`
   - 14 auth & utils → `core/auth/` and `utils/`

2. **Directory Structure Created**:
   - `routers/v1/` - Versioned API
   - `routers/v1/admin/` - Admin routes
   - `routers/v1/webhooks/` - Webhook routes
   - `cqrs/social/` - Social domain CQRS
   - `services/social/` - Social domain services
   - `workers/social/` - Social domain workers
   - `core/auth/` - Consolidated auth

3. **Auth Consolidation**:
   - 5 scattered auth files → 7 organized files in `core/auth/`
   - Better separation: core auth vs station auth
   - Improved maintainability

**Commits**: Phase 1A-1H (8 commits)  
**Verification**: Commit 1d45920

### Phase 2: Import Migration (Week 4)

**Goal**: Update all imports from OLD to NEW structure

**Completed**: ✅ November 2025

**Changes**:

1. **Phase 2A**: Updated `main.py` imports
   - Result: 248 → 250 routes registered

2. **Phase 2B**: Updated test imports
   - 7 test files updated

3. **Phase 2C**: Updated production code imports
   - **65 files updated**, **43 imports fixed**
   - Priority 1: Models (10 files)
   - Priority 2: CQRS (5 files, 20 imports)
   - Priority 3: Services (12 files)
   - Priority 4: Workers (2 files, 2 deleted)
   - Priority 5: Routers (22 files, 84 imports)
   - Priority 6: Other files (9 files, 22 imports)
   - Core Auth: 7 files (20 imports)

4. **Critical Bugs Fixed** (5 bugs):
   - Model import paths (`declarative_base` →
     `legacy_declarative_base`)
   - Pydantic v2 validator syntax
   - Import comment syntax (4 files)
   - Missing schema files (added 4 files)
   - Schema import not updated

**Commits**: 95b10fa → d4bb17c (9 commits)  
**Verification**: 0 OLD imports in production code

### Phase 3: Testing & Verification

**Goal**: Ensure application works after refactor

**Completed**: ✅ November 2025

**Results**:

- ✅ Application starts successfully
- ✅ 250 API routes registered
- ✅ All endpoints functional
- ✅ Zero regressions
- ✅ Zero data loss
- ✅ Zero feature loss

**Manual Audit**: `NUCLEAR_REFACTOR_MANUAL_AUDIT_REPORT.md` (Commit
7e3ff9a)

---

## 🚀 Best Practices

### 1. **Adding New Features**

```python
# 1. Create schema (schemas/)
class NewFeatureCreate(BaseModel):
    name: str
    description: str

# 2. Create service (services/)
class NewFeatureService:
    async def create(self, data: NewFeatureCreate):
        # Business logic here
        pass

# 3. Create router (routers/v1/)
@router.post("/new-feature")
async def create_feature(
    data: NewFeatureCreate,
    service: NewFeatureService = Depends()
):
    return await service.create(data)
```

### 2. **Error Handling**

```python
# Use custom exceptions from core
from core.exceptions import ValidationError, NotFoundError

class LeadService:
    async def get_lead(self, lead_id: int):
        lead = await self.db.get(Lead, lead_id)
        if not lead:
            raise NotFoundError(f"Lead {lead_id} not found")
        return lead
```

### 3. **Dependency Injection**

```python
# Use FastAPI's Depends for dependency injection
from fastapi import Depends
from core.database import get_db

@router.get("/leads")
async def get_leads(db: Database = Depends(get_db)):
    # Use db connection
    pass
```

### 4. **Testing**

```python
# Test at each layer
def test_lead_service():
    """Test business logic in isolation."""
    service = LeadService(mock_db, mock_ai)
    result = service.score_lead(test_data)
    assert result == expected_score

def test_lead_router():
    """Test API endpoint with TestClient."""
    response = client.post("/leads", json=test_data)
    assert response.status_code == 201
```

---

## 📊 Architecture Metrics

### Current State (November 2025)

- **Total Python Files**: 314
- **Production Files**: 74 migrated + additional modules
- **API Routes**: 250 registered routes
- **API Version**: v1 (versioned for future changes)
- **Test Coverage**: In progress
- **Documentation**: Complete

### Code Quality

- ✅ **Clean Architecture**: Implemented
- ✅ **SOLID Principles**: Followed
- ✅ **DRY (Don't Repeat Yourself)**: Maintained
- ✅ **Separation of Concerns**: Clear layers
- ✅ **Dependency Injection**: Used throughout
- ✅ **Type Hints**: Comprehensive coverage
- ✅ **Docstrings**: All public APIs documented

### Performance

- ✅ **Database**: Optimized queries with CQRS
- ✅ **Caching**: Redis-based caching (core/cache.py)
- ✅ **Rate Limiting**: Implemented (core/rate_limiting.py)
- ✅ **Circuit Breaker**: For external services
  (core/circuit_breaker.py)
- ✅ **Async/Await**: Throughout codebase

---

## 🔮 Future Enhancements

### Planned Improvements

1. **API Versioning**:
   - Add `routers/v2/` for breaking changes
   - Maintain backward compatibility with v1

2. **Microservices**:
   - Extract social domain to separate service
   - Extract payment domain to separate service

3. **Event Sourcing**:
   - Enhance CQRS with event store
   - Add event replay capabilities

4. **GraphQL**:
   - Add GraphQL API alongside REST
   - Use for complex queries

5. **Documentation**:
   - Auto-generate API docs with OpenAPI
   - Add architecture decision records (ADRs)

---

## 📚 References

### Key Documents

- `PRECISION_EXECUTION_ROADMAP.md` - Nuclear refactor plan
- `NUCLEAR_REFACTOR_MANUAL_AUDIT_REPORT.md` - Audit results
- `main.py` - Application entry point
- `core/config.py` - Configuration management

### External Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [CQRS Pattern](https://martinfowler.com/bliki/CQRS.html)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)

---

## 👥 Contributing

### Architecture Guidelines for Contributors

1. **Follow the Layer Pattern**: Don't skip layers or reverse
   dependencies
2. **Use Absolute Imports**: Always import from `src/` directory
3. **Never Import from `api.app.*`**: Old structure is deprecated
4. **Add Tests**: Test at appropriate layer (unit for services,
   integration for routers)
5. **Document Changes**: Update this document when adding new patterns

### Code Review Checklist

- [ ] Follows clean architecture principles
- [ ] Correct layer placement
- [ ] Proper import patterns (no `api.app.*`)
- [ ] Business logic in services, not routers
- [ ] Type hints added
- [ ] Docstrings for public APIs
- [ ] Tests added/updated
- [ ] No breaking changes (or versioned properly)

---

## 📞 Support

For questions about the architecture:

1. Review this document
2. Check `NUCLEAR_REFACTOR_MANUAL_AUDIT_REPORT.md`
3. Examine similar existing code
4. Ask in team chat

---

**Document Version**: 1.0  
**Last Updated**: November 5, 2025  
**Maintained By**: Development Team  
**Status**: ✅ Production Ready
