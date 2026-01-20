# 📐 Architecture Guide

> **Last Updated:** November 5, 2025  
> **Status:** Production Ready - Clean Architecture Implementation

## Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [Database Architecture](#database-architecture)
3. [Multi-Domain Architecture](#multi-domain-architecture)
4. [AI Architecture](#ai-architecture)
5. [Webhook Architecture](#webhook-architecture)
6. [Quick Deployment Guide](#quick-deployment-guide)

---

## System Architecture Overview

### Clean Architecture Pattern (CQRS + DDD)

```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                       │
│  /api/v1/* - RESTful endpoints with OpenAPI documentation   │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                 Application Layer                            │
│  • Routers (API endpoints)                                   │
│  • CQRS Commands & Queries                                   │
│  • Dependency Injection                                      │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                   Domain Layer                               │
│  • Business Logic (Services)                                 │
│  • Domain Models (Pydantic v2)                              │
│  • Business Rules & Validation                               │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│              Infrastructure Layer                            │
│  • Database (PostgreSQL + SQLAlchemy 2.0)                   │
│  • External APIs (Stripe, RingCentral, Google, Meta)        │
│  • Message Queue (Background tasks)                          │
│  • Cache Layer (Redis - optional)                            │
└─────────────────────────────────────────────────────────────┘
```

### Key Architectural Decisions

**✅ Clean Architecture Benefits:**

- Separation of concerns (API ≠ Business Logic ≠ Data)
- Testable (96.9% test coverage achieved)
- Maintainable (SOLID principles enforced)
- Scalable (Circular imports prevented)

**✅ Technology Stack:**

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.0, Pydantic v2
- **Database:** PostgreSQL 14+ with optimized indexes
- **Frontend:** Next.js 14, React 18, TypeScript, Tailwind CSS
- **Authentication:** JWT + OAuth2 (Google, Session-based)
- **APIs:** Stripe, RingCentral, Google Maps, Meta (WhatsApp)

---

## Database Architecture

### Schema Design

**Core Entities:**

- `stations` - Multi-tenant stations with RBAC
- `bookings` - Event bookings with status tracking
- `customers` - Customer data with privacy controls
- `payments` - Payment tracking with Stripe integration
- `leads` - Lead generation and conversion tracking
- `reviews` - Customer reviews from multiple platforms
- `inbox_messages` - Unified inbox for all channels

**Performance Optimizations:**

```sql
-- Critical Indexes for Production
CREATE INDEX CONCURRENTLY idx_bookings_station_date ON bookings(station_id, booking_date);
CREATE INDEX CONCURRENTLY idx_payments_booking_stripe ON payments(booking_id, stripe_payment_intent_id);
CREATE INDEX CONCURRENTLY idx_leads_station_status ON leads(station_id, status);
CREATE INDEX CONCURRENTLY idx_reviews_station_rating ON reviews(station_id, rating);
CREATE INDEX CONCURRENTLY idx_inbox_station_unread ON inbox_messages(station_id, is_read);
```

**Database Migration Strategy:**

```bash
# Apply migrations
cd apps/backend
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Rollback if needed
alembic downgrade -1
```

### Database Deployment Checklist

**Pre-Deployment:**

1. ✅ Backup existing database
2. ✅ Test migrations in staging
3. ✅ Verify index performance
4. ✅ Check connection pooling settings

**Deployment:**

```bash
# Deploy indexes (low traffic period)
psql -U postgres -d mh_webapps -f deploy_indexes.sql

# Monitor performance
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

---

## Multi-Domain Architecture

### Domain Separation Strategy

**Production Domains:**

- `myhibachichef.com` - Customer-facing booking site
- `admin.mysticdatanode.net` - Admin panel (this codebase)
- `mhapi.mysticdatanode.net` - Backend API

**Architecture Benefits:**

- ✅ Separate scaling (admin vs public traffic)
- ✅ Security isolation (admin behind auth wall)
- ✅ Independent deployments (admin updates don't affect public)
- ✅ CDN optimization (static vs dynamic content)

### CORS Configuration

```python
# apps/backend/src/main.py
origins = [
    "http://localhost:3000",  # Local development
    "https://admin.mysticdatanode.net",  # Production admin
    "https://myhibachichef.com",  # Production public (if needed)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Deployment Options

**Option 1: Single Server (Current)**

- Admin + API on same Plesk server
- `admin.mysticdatanode.net` → Next.js app
- `admin.mysticdatanode.net/api` → FastAPI backend

**Option 2: Separate Servers (Scalable)**

- Admin on Vercel/Netlify
- API on dedicated Plesk/AWS
- Cloudflare in front for DDoS protection

**Option 3: Cloudflare Tunnel (Recommended for Development)**

```bash
# Expose local backend to internet
cloudflared tunnel --url http://localhost:8000
```

---

## AI Architecture

### AI System Decision Matrix

**Current Implementation:**

- **Model:** GPT-4o (OpenAI) - Best accuracy for customer-facing
  responses
- **Use Cases:** Email drafting, booking inquiries, review responses,
  lead qualification
- **Fallback:** GPT-3.5-turbo for non-critical tasks (cost
  optimization)

**Future Considerations:**

- **Claude 3.5 Sonnet:** Better instruction following, longer context
- **Llama 3.1:** Self-hosted option for data privacy requirements
- **Specialized Models:** Fine-tuned models for domain-specific tasks

### AI Integration Points

```python
# apps/backend/src/services/openai_service.py
class OpenAIService:
    async def generate_email_response(
        self,
        customer_inquiry: str,
        context: dict
    ) -> str:
        # AI-powered email generation
        # Used in: inbox responses, booking confirmations
        pass

    async def qualify_lead(
        self,
        lead_data: dict
    ) -> LeadQualification:
        # AI lead scoring
        # Used in: lead generation, sales prioritization
        pass
```

**AI Escalation System:**

- Level 1: Auto-respond to common inquiries (80% of messages)
- Level 2: AI drafts response, human approval required (15%)
- Level 3: Human-only for complex/sensitive issues (5%)

### AI Safety & Compliance

✅ **Data Privacy:** Customer data never used for model training ✅
**Rate Limiting:** 50 requests/minute per station ✅ **Cost
Controls:** Monthly budget limits per station ✅ **Audit Trail:** All
AI interactions logged for review

---

## Webhook Architecture

### Stripe Webhook Flow

```
┌─────────────┐
│   Stripe    │
│  (Payment)  │
└──────┬──────┘
       │ POST /api/v1/webhooks/stripe
       │ sig: stripe-signature header
       ▼
┌─────────────────────────────────────┐
│     FastAPI Webhook Endpoint        │
│  • Verify signature (CRITICAL!)     │
│  • Parse event type                 │
│  • Route to handler                 │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│      Event Handler (CQRS)           │
│  • payment_intent.succeeded         │
│  • payment_intent.payment_failed    │
│  • charge.refunded                  │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│     Database Update                 │
│  • Update payment record            │
│  • Update booking status            │
│  • Trigger notifications            │
└─────────────────────────────────────┘
```

**Webhook Security:**

```python
# Verify Stripe signature (REQUIRED)
def verify_stripe_webhook(payload: bytes, sig_header: str) -> dict:
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        return event
    except ValueError:
        raise HTTPException(400, "Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(400, "Invalid signature")
```

### Other Webhooks

**RingCentral (SMS):** `/api/v1/webhooks/ringcentral`
**Meta/WhatsApp:** `/api/v1/webhooks/meta` **Google Business:**
`/api/v1/webhooks/google`

**Common Pattern:**

1. Verify signature/token
2. Parse event
3. Queue for background processing (if heavy)
4. Return 200 OK immediately (within 5 seconds)

---

## Quick Deployment Guide

### Pre-Deployment Checklist

**Infrastructure:**

- [ ] PostgreSQL 14+ installed and accessible
- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed
- [ ] SSL certificates configured
- [ ] Environment variables set

**Database:**

- [ ] Database created: `mh_webapps`
- [ ] Database user with permissions
- [ ] Migrations tested in staging
- [ ] Backup strategy in place

**Security:**

- [ ] JWT secret generated (32+ chars)
- [ ] Stripe webhook secret configured
- [ ] API keys secured (not in code)
- [ ] CORS origins configured
- [ ] Rate limiting enabled

### Deployment Steps

**1. Backend Deployment:**

```bash
cd apps/backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**2. Frontend Deployment:**

```bash
cd apps/admin
npm install
npm run build
npm start  # or deploy to Vercel
```

**3. Verify Deployment:**

```bash
# Health check
curl https://admin.mysticdatanode.net/api/health

# Expected response:
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0"
}
```

### Production Monitoring

**Key Metrics:**

- Response time < 500ms (p95)
- Database connections < 80% of pool
- Error rate < 1%
- Webhook processing < 3 seconds

**Monitoring Tools:**

- Application logs: Check FastAPI logs
- Database: `pg_stat_statements`
- Uptime: External monitoring (UptimeRobot, Pingdom)
- Errors: Sentry or similar

---

## Architecture Comparison

### Before Nuclear Refactor vs After

| Aspect               | Before                      | After                    |
| -------------------- | --------------------------- | ------------------------ |
| **Structure**        | Monolithic, tightly coupled | Clean Architecture, CQRS |
| **Testing**          | ~30% coverage               | 96.9% coverage           |
| **Circular Imports** | 50+ circular dependencies   | 0 (prevented by design)  |
| **API Organization** | Mixed `/api/app/*`          | Clean `/api/v1/*`        |
| **Database**         | Direct SQLAlchemy calls     | Repository pattern       |
| **Business Logic**   | In routers                  | Separate service layer   |
| **Scalability**      | Difficult to scale          | Horizontally scalable    |
| **Maintainability**  | Hard to modify              | Easy to extend           |

---

## Next Steps

**For New Developers:**

1. Read this architecture guide
2. Review [Backend README](../../apps/backend/README.md)
3. Check [API Documentation](../../apps/backend/README_API.md)
4. Run tests: `pytest apps/backend/tests/`

**For DevOps:**

1. Review deployment checklist above
2. Configure monitoring and alerts
3. Set up backup strategy
4. Plan scaling strategy

**For Product:**

1. Understand multi-domain capabilities
2. Review AI integration points
3. Plan feature rollout strategy

---

**📚 Related Documentation:**

- [Backend Architecture Details](../../apps/backend/ARCHITECTURE.md)
- [Database Migrations Guide](../../apps/backend/DATABASE_MIGRATIONS.md)
- [Deployment Checklist](../04-DEPLOYMENT/DEPLOYMENT.md)
- [API Reference](../../apps/backend/README_API.md)
