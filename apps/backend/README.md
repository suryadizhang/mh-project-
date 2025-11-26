# 🍱 MyHibachi Backend - Clean Architecture

**Production-Ready FastAPI Backend with Clean Architecture**
**Version**: 2.0 (Post Nuclear Refactor) **Status**: ✅ Production
Ready

> 🎉 **November 2025**: Successfully completed nuclear refactor to
> clean architecture! See
> [MIGRATION_SUMMARY.md](./MIGRATION_SUMMARY.md) for complete
> migration details.

---

## 📚 Documentation

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Complete architecture
  documentation (890 lines)
- **[MIGRATION_SUMMARY.md](./MIGRATION_SUMMARY.md)** - Nuclear
  refactor migration summary (755 lines)
- **[README_API.md](./README_API.md)** - Stripe API integration guide
- **[DATABASE_MIGRATIONS.md](./DATABASE_MIGRATIONS.md)** - Database
  migration guide
- **[HEALTH_CHECKS.md](./HEALTH_CHECKS.md)** - Health check
  documentation

---

## 🚀 Quick Start

### Prerequisites

- **Python**: 3.11+
- **PostgreSQL**: 12+
- **Redis**: (optional, for caching)
- **Stripe Account**: For payment processing

### Installation

```bash
# Navigate to backend directory
cd apps/backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows CMD:
venv\Scripts\activate.bat
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# See "Environment Variables" section below
```

### Database Setup

```bash
# Create database
createdb myhibachi_db

# Run migrations
alembic upgrade head

# (Optional) Setup Stripe products for development
python -c "from utils.stripe_setup import setup_stripe_products; import asyncio; asyncio.run(setup_stripe_products())"
```

### Start Development Server

```bash
# Start FastAPI server
uvicorn src.main:app --reload --port 8000

# API Documentation available at:
# - Swagger UI: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
```

---

## 🏗️ Architecture Overview

MyHibachi backend follows **Clean Architecture** principles with clear
separation of concerns across 4 layers:

```
┌─────────────────────────────────────────────────────┐
│                    PRESENTATION                     │
│              (Routers / API Endpoints)              │
│                   routers/v1/                       │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│                  APPLICATION                        │
│         (CQRS Handlers / Use Cases)                 │
│                     cqrs/                           │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│                    DOMAIN                           │
│         (Services / Business Logic)                 │
│                   services/                         │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│              INFRASTRUCTURE                         │
│    (Models / Database / External Services)          │
│              models/, core/                         │
└─────────────────────────────────────────────────────┘
```

**📖 For detailed architecture documentation, see
[ARCHITECTURE.md](./ARCHITECTURE.md)**

---

## 📁 Directory Structure

```
apps/backend/src/
├── routers/              # 🌐 API Routes (Presentation Layer)
│   └── v1/              # API Version 1
│       ├── admin/       # Admin-only routes
│       ├── webhooks/    # External service webhooks
│       └── *.py         # Core routes (23 files total)
│
├── cqrs/                # 📋 Command/Query Handlers (Application Layer)
│   └── social/         # Social media domain (9 files total)
│
├── services/            # 🔧 Business Logic (Domain Layer)
│   └── social/         # Social services (26 files total)
│
├── models/              # 🗄️ Data Models (Infrastructure Layer)
│   └── legacy_*.py     # Database models (13 files with legacy_ prefix)
│
├── schemas/             # 📝 Request/Response Schemas
│   └── *.py            # Pydantic schemas (5 files)
│
├── core/                # ⚙️ Core Infrastructure
│   ├── auth/           # Authentication & Authorization (7 files)
│   ├── database.py     # Database configuration
│   ├── config.py       # Application configuration
│   └── ...             # Other core services
│
├── workers/             # 🔄 Background Workers
│   └── social/         # Social media workers (2 files)
│
├── middleware/          # 🛡️ Request/Response Middleware
├── utils/               # 🔨 Utility Functions
├── ai/                  # 🤖 AI Services & Orchestration
├── integrations/        # 🔌 Third-party Integrations
└── main.py             # 🚀 Application Entry Point
```

**Key Metrics:**

- **250 API Routes** registered
- **23 Router Files** organized in `/api/v1/`
- **26 Services** implementing business logic
- **13 Database Models** (all with `legacy_` prefix)
- **7 Auth Files** consolidated in `core/auth/`

---

## 🎯 Features

### Core Features

- ✅ **RESTful API** - 250 endpoints with versioned routes
  (`/api/v1/`)
- ✅ **Clean Architecture** - Clear layer separation
- ✅ **CQRS Pattern** - Command/Query separation
- ✅ **Authentication** - JWT-based auth with multi-tenant support
- ✅ **Database** - PostgreSQL with async SQLAlchemy
- ✅ **Migrations** - Alembic database migrations
- ✅ **Validation** - Pydantic v2.5.0 schemas
- ✅ **Documentation** - Auto-generated OpenAPI docs

### Domain Features

- 🎫 **Booking Management** - Full booking lifecycle
- 💳 **Payment Processing** - Stripe integration
- ⭐ **Review System** - Customer review management
- 📧 **Lead Management** - AI-powered lead scoring
- 📱 **Social Media** - Social media integration & AI tools
- 📊 **Analytics** - Comprehensive analytics dashboard
- 🔔 **Notifications** - Multi-channel notification system
- 🏢 **Multi-Tenant** - Station-based authentication

---

## 📦 Import Patterns

### ✅ Correct Import Patterns (Use These)

```python
# Routers
from services.lead_service import LeadService
from cqrs.command_handlers import CreateBookingHandler
from schemas.booking import BookingCreate, BookingResponse
from core.auth.middleware import require_auth
from core.database import get_db

# Services
from models.legacy_core import Customer, Station
from core.database import Database
from utils.station_code_generator import generate_code

# Models
from models.legacy_declarative_base import Base
from models.legacy_booking_models import Booking
```

### ❌ Old Import Patterns (DEPRECATED - Never Use)

```python
# ❌ NEVER USE THESE ANYMORE
from api.app.models.booking import Booking
from api.app.services.lead_service import LeadService
from api.app.cqrs.handlers import CommandHandler
```

> **Note**: The OLD `api/app/` structure has been deprecated. Always
> use the NEW import patterns above.

---

## 🔧 Environment Variables

### Required Configuration

```bash
# Database
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/myhibachi_db
DATABASE_URL_SYNC=postgresql://username:password@localhost:5432/myhibachi_db

# Security
SECRET_KEY=your-super-secret-jwt-key-change-in-production
ENVIRONMENT=development  # or production

# Stripe
STRIPE_SECRET_KEY=sk_test_your_test_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_test_publishable_key_here

# Redis (Optional)
REDIS_URL=redis://localhost:6379/0

# Email (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Optional Configuration

```bash
# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# AI Services
OPENAI_API_KEY=sk-your-openai-api-key

# External Integrations
RINGCENTRAL_CLIENT_ID=your-client-id
RINGCENTRAL_CLIENT_SECRET=your-client-secret
```

---

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_bookings.py

# Run with verbose output
pytest -v
```

### Test Health Endpoints

```bash
# Basic health check
curl http://localhost:8000/health

# Readiness check
curl http://localhost:8000/ready

# Database health
curl http://localhost:8000/health/db
```

### Stripe Testing

```bash
# Install Stripe CLI
# https://stripe.com/docs/stripe-cli

# Login to Stripe
stripe login

# Forward webhooks to local server
stripe listen --forward-to localhost:8000/api/v1/stripe/webhook

# Trigger test events
stripe trigger payment_intent.succeeded
stripe trigger customer.created
```

**Test Cards:**

- **Success**: 4242 4242 4242 4242
- **Decline**: 4000 0000 0000 0002
- **3D Secure**: 4000 0027 6000 3184

---

## 🔑 API Endpoints

### Health & Monitoring

```
GET  /health         - Basic health check
GET  /ready          - Readiness check
GET  /health/db      - Database health check
```

### Authentication

```
POST /api/v1/auth/login            - User login
POST /api/v1/auth/register         - User registration
GET  /api/v1/auth/me               - Current user info
POST /api/v1/auth/refresh          - Refresh token
```

### Bookings

```
GET    /api/v1/bookings           - List bookings
POST   /api/v1/bookings           - Create booking
GET    /api/v1/bookings/{id}      - Get booking
PUT    /api/v1/bookings/{id}      - Update booking
DELETE /api/v1/bookings/{id}      - Delete booking
```

### Payments (Stripe)

> **📚 For comprehensive Stripe integration details, see
> [STRIPE_INTEGRATION.md](./STRIPE_INTEGRATION.md)**

We leverage **Stripe's native features** for all payment processing:

- ✅ Stripe Dashboard for analytics
- ✅ Stripe Reporting API for exports
- ✅ Stripe Webhooks for real-time events
- ✅ Stripe Customer Portal for self-service
- ✅ Stripe Checkout for PCI-compliant payments

**API Endpoints:**

```
POST /api/v1/stripe/create-checkout-session  - Create Checkout session
POST /api/v1/stripe/create-payment-intent    - Create Payment Intent
POST /api/v1/stripe/portal-link              - Customer portal
POST /api/v1/stripe/webhook                  - Webhook handler
GET  /api/v1/stripe/payments                 - List payments
POST /api/v1/stripe/refund                   - Process refund (admin)
```

### Reviews

```
GET    /api/v1/reviews           - List reviews
POST   /api/v1/reviews           - Create review
GET    /api/v1/reviews/{id}      - Get review
PUT    /api/v1/reviews/{id}      - Update review
DELETE /api/v1/reviews/{id}      - Delete review (admin)
```

### Leads

```
GET    /api/v1/leads             - List leads
POST   /api/v1/leads             - Create lead
GET    /api/v1/leads/{id}        - Get lead
PUT    /api/v1/leads/{id}        - Update lead
POST   /api/v1/leads/{id}/score  - AI lead scoring
```

**📖 For complete API documentation, visit:
http://localhost:8000/docs**

---

## 🛠️ Development Tools

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Show current version
alembic current

# Show migration history
alembic history
```

### Code Quality

```bash
# Format code with Black
black src/

# Lint with Flake8
flake8 src/

# Type checking with MyPy
mypy src/

# Sort imports
isort src/
```

### CLI Utilities

```bash
# Setup Stripe products (development)
python -c "from utils.stripe_setup import setup_stripe_products; import asyncio; asyncio.run(setup_stripe_products())"

# Create test data
python -c "from utils.stripe_setup import create_test_data; print(create_test_data())"

# Generate station code
python -c "from utils.station_code_generator import generate_code; print(generate_code())"
```

---

## 🚀 Deployment

### Production Checklist

#### Environment Setup

- [ ] Set `ENVIRONMENT=production`
- [ ] Update `SECRET_KEY` with strong random value
- [ ] Use production database credentials
- [ ] Configure production Stripe keys (live mode)
- [ ] Set up production webhook endpoint
- [ ] Configure email service (SMTP)
- [ ] Set up Redis for caching
- [ ] Configure CORS for production domains

#### Security

- [ ] Enable HTTPS only
- [ ] Set up rate limiting
- [ ] Configure firewall rules
- [ ] Enable database connection pooling
- [ ] Set up backup strategy
- [ ] Configure monitoring and alerts
- [ ] Review and update security headers

#### Testing

- [ ] Run all tests in production mode
- [ ] Test all payment flows
- [ ] Verify webhook delivery
- [ ] Test authentication flows
- [ ] Verify email delivery
- [ ] Load testing
- [ ] Security audit

### Deployment Commands

```bash
# Install production dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start production server with Gunicorn
gunicorn src.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Or with Uvicorn
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 🎓 Learning Resources

### Architecture Documentation

1. **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Complete architecture
   guide
   - Clean Architecture principles
   - Layer responsibilities
   - Design patterns (CQRS, DDD)
   - Import patterns
   - Best practices

2. **[STRIPE_INTEGRATION.md](./STRIPE_INTEGRATION.md)** - Stripe
   integration architecture ⭐ **NEW**
   - Architecture decision (November 2025)
   - Stripe native features we use
   - Code removed vs benefits gained
   - Migration summary and analytics workflow

3. **[MIGRATION_SUMMARY.md](./MIGRATION_SUMMARY.md)** - Migration
   history
   - Phase 1-3 timeline
   - 74 files migrated
   - 65 files updated
   - 5 critical bugs fixed
   - Lessons learned

### Code Examples

```python
# Example: Creating a new service
# File: services/my_new_service.py

from models.legacy_core import Customer
from core.database import Database

class MyNewService:
    """Business logic for my new feature."""

    def __init__(self, db: Database):
        self.db = db

    async def do_something(self, customer_id: int):
        """Implement business logic here."""
        customer = await self.db.get(Customer, customer_id)
        # Business logic...
        return result
```

```python
# Example: Creating a new router
# File: routers/v1/my_new_router.py

from fastapi import APIRouter, Depends
from services.my_new_service import MyNewService
from schemas.my_schema import MyResponse

router = APIRouter(prefix="/api/v1/my-feature", tags=["my-feature"])

@router.get("/", response_model=MyResponse)
async def get_data(service: MyNewService = Depends()):
    """Handle GET request."""
    return await service.do_something()
```

### External Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [CQRS Pattern](https://martinfowler.com/bliki/CQRS.html)

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Import Errors

```
ModuleNotFoundError: No module named 'api.app'
```

**Solution**: Update imports to use NEW structure (no `api.app.*`)

```python
# ❌ OLD (causes error)
from api.app.models.booking import Booking

# ✅ NEW (correct)
from models.legacy_booking_models import Booking
```

#### 2. Database Connection Issues

```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solution**: Check database is running and credentials are correct

```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# Test connection
psql $DATABASE_URL_SYNC
```

#### 3. Stripe Webhook Verification Failed

```
stripe.error.SignatureVerificationError: Invalid signature
```

**Solution**: Verify webhook secret matches

```bash
# Get webhook secret from Stripe CLI
stripe listen --print-secret

# Update .env file
STRIPE_WEBHOOK_SECRET=whsec_...
```

#### 4. Application Won't Start

```
ModuleNotFoundError: No module named 'main'
```

**Solution**: Make sure to run from correct directory

```bash
# Must be in apps/backend directory
cd apps/backend

# Start with src.main (not just main)
uvicorn src.main:app --reload
```

---

## 📞 Support & Contributing

### Getting Help

1. **Check Documentation**: Review architecture and migration docs
2. **Check API Docs**: Visit http://localhost:8000/docs
3. **Review Logs**: Check application logs for errors
4. **Verify Environment**: Ensure all environment variables are set

### Contributing Guidelines

#### Code Style

- Follow **PEP 8** style guide
- Use **type hints** for all functions
- Write **docstrings** for public APIs
- Format code with **Black**
- Sort imports with **isort**

#### Architecture Rules

1. **Follow Layer Pattern**: Don't skip layers or reverse dependencies
2. **Use Correct Imports**: Never import from `api.app.*`
3. **Add Tests**: Test at appropriate layer
4. **Document Changes**: Update docs when adding new patterns
5. **No Business Logic in Routers**: Keep routers thin

#### Pull Request Checklist

- [ ] Code follows PEP 8 style guide
- [ ] Type hints added
- [ ] Docstrings for public APIs
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No breaking changes (or versioned properly)
- [ ] Correct import patterns used
- [ ] Follows clean architecture principles

---

## 📊 Project Metrics

### Current Status (November 2025)

- **Total Files**: 314 Python files
- **API Routes**: 250 registered routes
- **Services**: 26 business logic services
- **Models**: 13 database models
- **Test Coverage**: In progress
- **Documentation**: ✅ Complete (2,279 lines across 3 docs)

### Code Quality

- ✅ **Clean Architecture**: Implemented
- ✅ **SOLID Principles**: Followed
- ✅ **Type Hints**: Comprehensive coverage
- ✅ **Docstrings**: All public APIs documented
- ✅ **Import Patterns**: 100% NEW structure (0 OLD imports)
- ✅ **Zero Regressions**: All tests passing

---

## 🎉 Recent Updates

### November 2025 - Nuclear Refactor Complete

Successfully completed nuclear refactor to clean architecture:

- ✅ **74 files migrated** from OLD `api/app/` to NEW structure
- ✅ **65 files updated** with new import patterns
- ✅ **5 critical bugs fixed** during migration
- ✅ **0 OLD imports** remaining in production code
- ✅ **250 API routes** verified working
- ✅ **Zero data loss**, **zero feature loss**
- ✅ **2,279 lines** of documentation created

**📖 See [MIGRATION_SUMMARY.md](./MIGRATION_SUMMARY.md) for complete
details**

---

## 📄 License

Copyright © 2025 MyHibachi. All rights reserved.

---

**Built with ❤️ using FastAPI and Clean Architecture principles**

For questions or issues, please review the documentation or contact
the development team.
