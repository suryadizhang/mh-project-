# 🚀 My Hibachi VPS Deployment - 6-Batch Enterprise Strategy

**Created:** November 22, 2025 **Updated:** December 6, 2025
**Status:** ✅ APPROVED - Ready for Implementation **Purpose:**
Enterprise-grade deployment strategy with quality gates

> 📌 **See Also:**
>
> - [CONSOLIDATED_MASTER_ROADMAP.md](../CONSOLIDATED_MASTER_ROADMAP.md) -
>   **ALL plans consolidated into single doc**
> - [ENTERPRISE_AI_DEPLOYMENT_MASTER_PLAN.md](../ENTERPRISE_AI_DEPLOYMENT_MASTER_PLAN.md) -
>   Full AI architecture
> - [BATCH_CHECKLISTS.md](./BATCH_CHECKLISTS.md) - Per-batch
>   implementation checklists
> - [BRANCH_PROTECTION_SETUP.md](../../.github/BRANCH_PROTECTION_SETUP.md) -
>   GitHub branch protection setup guide
> - [QUALITY_GATES.md](../../.github/QUALITY_GATES.md) - Quality gates
>   & E2E testing standards

---

## 🔒 ENTERPRISE DEVOPS STANDARDS (ALL BATCHES)

> **CRITICAL:** These standards apply to ALL batches and must be
> followed before any production deployment.

### Branch Protection Rules (Apply in GitHub UI)

| Branch      | Protection Level | Requirements                                      |
| ----------- | ---------------- | ------------------------------------------------- |
| `main`      | 🔴 **STRICT**    | PR required, 1+ approval, status checks must pass |
| `dev`       | 🟠 **MODERATE**  | PR required, status checks must pass              |
| `feature/*` | 🟢 **NONE**      | Developers have flexibility                       |

**Setup Guide:** See `.github/BRANCH_PROTECTION_SETUP.md`

### CI/CD Pipeline (Per Environment)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT PIPELINE                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  FEATURE BRANCH (feature/*)                                         │
│  ─────────────────────────────────────────────────────────────────  │
│  • Local development only                                           │
│  • Run tests locally before PR                                      │
│  • No auto-deploy                                                   │
│                                                                      │
│                    ▼ Pull Request                                   │
│                                                                      │
│  DEV BRANCH (Staging Environment)                                   │
│  ─────────────────────────────────────────────────────────────────  │
│  • Auto-deploy to staging (deploy-backend-staging.yml)              │
│  • Unit tests + integration tests                                   │
│  • E2E tests against staging                                        │
│  • 24-48 hour stability observation                                 │
│                                                                      │
│                    ▼ Pull Request (after staging passes)            │
│                                                                      │
│  MAIN BRANCH (Production Environment)                               │
│  ─────────────────────────────────────────────────────────────────  │
│  • Auto-deploy to production (deploy-backend.yml)                   │
│  • Rolling restart (zero-downtime)                                  │
│  • Smoke tests                                                      │
│  • Auto-rollback on failure                                         │
│  • 48-72 hour monitoring period                                     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Quality Gates (Mandatory for All PRs)

| Gate                        | Blocking? | Tool               |
| --------------------------- | --------- | ------------------ |
| Unit tests pass             | ✅ Yes    | pytest             |
| Integration tests pass      | ⚠️ 95%+   | pytest             |
| E2E tests pass (staging)    | ✅ Yes    | Playwright         |
| Code review approved        | ✅ Yes    | GitHub PR          |
| No security vulnerabilities | ✅ Yes    | npm audit / safety |
| Feature flag configured     | ✅ Yes    | Manual check       |

**Full Details:** See `.github/QUALITY_GATES.md`

### Workflow Files

| File                         | Trigger        | Purpose                  |
| ---------------------------- | -------------- | ------------------------ |
| `deploy-backend.yml`         | Push to `main` | Production deployment    |
| `deploy-backend-staging.yml` | Push to `dev`  | Staging deployment + E2E |
| `sync-gsm-to-vercel.yml`     | Manual         | Sync secrets to Vercel   |

---

## ⚡ PERFORMANCE BUDGETS (Mandatory All Batches)

> **CRITICAL:** These performance targets are BLOCKING requirements.
> Code that exceeds budgets must be optimized before merge.

### Core Web Vitals Targets

| Metric                             | Target | Warning | Critical | Blocking?  |
| ---------------------------------- | ------ | ------- | -------- | ---------- |
| **LCP (Largest Contentful Paint)** | <2.5s  | >2.5s   | >4.0s    | ✅ Yes     |
| **FID (First Input Delay)**        | <100ms | >100ms  | >300ms   | ✅ Yes     |
| **CLS (Cumulative Layout Shift)**  | <0.1   | >0.1    | >0.25    | ✅ Yes     |
| **FCP (First Contentful Paint)**   | <1.8s  | >1.8s   | >3.0s    | ⚠️ Warning |
| **TTI (Time to Interactive)**      | <3.8s  | >3.8s   | >7.3s    | ⚠️ Warning |
| **TTFB (Time to First Byte)**      | <600ms | >600ms  | >1.8s    | ⚠️ Warning |

### Bundle Size Budgets

| Page/Route                 | First Load JS | Total Bundle | Blocking?  |
| -------------------------- | ------------- | ------------ | ---------- |
| **Homepage** (`/`)         | <150KB        | <300KB       | ✅ Yes     |
| **Menu** (`/menu`)         | <120KB        | <250KB       | ✅ Yes     |
| **Quote** (`/quote`)       | <130KB        | <280KB       | ✅ Yes     |
| **BookUs** (`/BookUs`)     | <180KB        | <350KB       | ✅ Yes     |
| **Payment** (`/payment/*`) | <150KB        | <300KB       | ✅ Yes     |
| **Blog** (`/blog`)         | <140KB        | <280KB       | ⚠️ Warning |
| **Admin Dashboard**        | <200KB        | <400KB       | ⚠️ Warning |
| **Shared Chunks**          | <100KB        | -            | ✅ Yes     |

### API Response Time Budgets (P95)

| Endpoint Category          | Target | Warning | Critical | Blocking?  |
| -------------------------- | ------ | ------- | -------- | ---------- |
| **Health Checks**          | <50ms  | >100ms  | >200ms   | ✅ Yes     |
| **Auth Endpoints**         | <200ms | >500ms  | >1s      | ✅ Yes     |
| **Quote Calculation**      | <300ms | >600ms  | >1s      | ✅ Yes     |
| **Booking CRUD**           | <200ms | >500ms  | >1s      | ✅ Yes     |
| **List Endpoints (paged)** | <500ms | >1s     | >2s      | ✅ Yes     |
| **AI Chat**                | <3s    | >5s     | >10s     | ⚠️ Warning |
| **File Upload**            | <5s    | >10s    | >30s     | ⚠️ Warning |

### Database Query Budgets

| Query Type              | Target | Warning | Critical |
| ----------------------- | ------ | ------- | -------- |
| **Simple SELECT**       | <10ms  | >50ms   | >100ms   |
| **JOIN (2-3 tables)**   | <50ms  | >100ms  | >200ms   |
| **Complex Aggregation** | <200ms | >500ms  | >1s      |
| **Full-Text Search**    | <100ms | >200ms  | >500ms   |
| **Bulk INSERT/UPDATE**  | <500ms | >1s     | >3s      |

### Lighthouse Score Targets

| Metric             | Target | Minimum | Blocking?    |
| ------------------ | ------ | ------- | ------------ |
| **Performance**    | >90    | >70     | ✅ Yes (>70) |
| **Accessibility**  | >95    | >90     | ✅ Yes (>90) |
| **Best Practices** | >95    | >90     | ⚠️ Warning   |
| **SEO**            | >95    | >90     | ⚠️ Warning   |

### Performance Testing Commands

```bash
# Run Lighthouse audit (install: npm i -g lighthouse)
lighthouse https://myhibachichef.com --output=json --output-path=./lighthouse-report.json

# Check bundle size
npm run build -- --profile
npx @next/bundle-analyzer

# API load test (install: npm i -g autocannon)
autocannon -c 100 -d 30 https://api.myhibachichef.com/api/v1/health

# Database query analysis
EXPLAIN ANALYZE SELECT * FROM bookings WHERE ...;
```

### Performance Budget Enforcement

```yaml
# .github/workflows/performance-check.yml (Add to CI)
- name: Lighthouse CI
  uses: treosh/lighthouse-ci-action@v9
  with:
    budgetPath: ./lighthouse-budget.json
    uploadArtifacts: true
    temporaryPublicStorage: true

# lighthouse-budget.json
{
  "ci": {
    "assert": {
      "assertions": {
        "first-contentful-paint": ["error", {"maxNumericValue": 1800}],
        "largest-contentful-paint": ["error", {"maxNumericValue": 2500}],
        "cumulative-layout-shift": ["error", {"maxNumericValue": 0.1}],
        "total-blocking-time": ["warn", {"maxNumericValue": 300}]
      }
    }
  }
}
```

---

## Executive Summary

This document defines a **6-batch deployment strategy** following
enterprise standards:

- **Slower, safer approach** - each batch fully tested before next
- **Quality gates** - mandatory checks before production
- **Feature flags** - granular control over rollouts
- **Rollback procedures** - immediate recovery capability

### Current State

- **Backend:** FastAPI with 394 routes (338 unique) - LOADS
  SUCCESSFULLY ✅
- **Branch:** `nuclear-refactor-clean-architecture`
- **Git Strategy:** feature/batch-X → dev → main (only when 100%
  tested)

### Plans Consolidated Into This Strategy

| Source Document                                | Key Content         | Batch Assigned |
| ---------------------------------------------- | ------------------- | -------------- |
| `4_TIER_RBAC_IMPLEMENTATION_PLAN.md`           | 4-tier role system  | **Batch 1**    |
| `FAILED_BOOKING_LEAD_CAPTURE.md`               | Auto lead capture   | **Batch 1**    |
| `DYNAMIC_PRICING_MANAGEMENT_SYSTEM.md`         | Admin pricing       | **Batch 2**    |
| `SMART_AI_ESCALATION_SYSTEM.md`                | 80% AI handling     | **Batch 3**    |
| `PHASE_2_2_RINGCENTRAL_WEBHOOK_ANALYSIS.md`    | Webhook pipeline    | **Batch 4**    |
| `PHASE_2_3_RINGCENTRAL_NATIVE_RECORDING.md`    | RC native recording | **Batch 4**    |
| `ENTERPRISE_FEATURES_ROADMAP.md`               | Review system       | **Batch 5**    |
| `FULL_SELF_LEARNING_IMPLEMENTATION_ROADMAP.md` | 20 AI improvements  | **Batch 5-6**  |
| `LOYALTY_PROGRAM_EXPLANATION.md`               | Points/tiers        | **Batch 6**    |
| `FUTURE_SCALING_PLAN.md`                       | Llama 3, Neo4j      | **Batch 6+**   |

---

## 🏗️ DATABASE & AI FOUNDATION STRATEGY

### Database Migration Order

Each batch requires specific database migrations. **Run in this
order:**

| Phase          | Migration                            | Batch | Purpose                              |
| -------------- | ------------------------------------ | ----- | ------------------------------------ |
| **Foundation** | `setup_db_enums.sql`                 | Pre-1 | Create all PostgreSQL enums          |
| **Foundation** | `create_all_missing_enums.sql`       | Pre-1 | Ensure no missing enums              |
| **Batch 1**    | `add_security_tables.sql`            | 1     | Login history, MFA columns           |
| **Batch 1**    | `add_login_history_table.sql`        | 1     | Audit login attempts                 |
| **Batch 1**    | `001_create_performance_indexes.sql` | 1     | Core table indexes                   |
| **Batch 1**    | `create_ai_tables.sql`               | 1     | **AI schema foundation (529 lines)** |
| **Batch 2**    | Stripe tables (Alembic)              | 2     | Payment models                       |
| **Batch 3**    | `create_feedback_review_status.sql`  | 3     | AI feedback enums                    |
| **Batch 5**    | `007_add_customer_reviews.sql`       | 5     | Customer review tables               |
| **Batch 6**    | Loyalty tables (new migration)       | 6     | Points, tiers, referrals             |

### AI Schema Tables (Deployed in Batch 1)

The `create_ai_tables.sql` creates these critical tables:

```
ai.conversations           - Unified conversation tracking
ai.messages               - Message storage + emotion scores
ai.customer_engagement_followups - Scheduled AI follow-ups
ai.kb_chunks              - RAG knowledge base chunks
ai.conversation_summaries - AI-generated summaries
ai.escalation_records     - Human escalation tracking
ai.model_metrics          - AI model performance
ai.training_data          - Fine-tuning data collection
```

**Why in Batch 1?** AI tables must exist before Batch 3 (Core AI) can
function.

### Vector Database Strategy

| Phase       | Component          | Location               |
| ----------- | ------------------ | ---------------------- |
| **Batch 3** | pgvector extension | PostgreSQL (built-in)  |
| **Batch 5** | Pinecone/Qdrant    | External service (RAG) |

```sql
-- Batch 3: Enable pgvector for basic embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column to kb_chunks
ALTER TABLE ai.kb_chunks ADD COLUMN IF NOT EXISTS embedding vector(1536);
```

---

## 🚀 SCALING FOUNDATION (All Batches)

> **CRITICAL:** Build scaling foundations EARLY so future growth
> doesn't require rewrites. These patterns are cheap to implement now,
> expensive later.

### Database Scaling Foundation

| Component                | Batch   | Status   | Notes                                          |
| ------------------------ | ------- | -------- | ---------------------------------------------- |
| **Connection Pooling**   | ✅ Done | ✅ Built | `pool_size=10`, `max_overflow=20` via env vars |
| **Pool Monitoring**      | ✅ Done | ✅ Built | Health checks + monitoring dashboard           |
| **Read Replica Ready**   | Batch 1 | 🔧 Add   | Config pattern for read/write splitting        |
| **PgBouncer Ready**      | Batch 1 | 🔧 Add   | External pooler support (for >100 connections) |
| **Table Partitioning**   | Batch 1 | 🔧 Add   | Time-based partitioning for bookings/audit_log |
| **AI Schema Separation** | Batch 3 | 🔧 Add   | Separate connection for AI-heavy queries       |

### Redis/Cache Scaling Foundation

| Component                 | Batch   | Status   | Notes                           |
| ------------------------- | ------- | -------- | ------------------------------- |
| **Redis Single Instance** | ✅ Done | ✅ Built | Session, rate limiting, cache   |
| **Redis Cluster Config**  | Batch 3 | 🔧 Add   | Config pattern for cluster mode |
| **Cache Key Namespacing** | Batch 1 | 🔧 Add   | Prefix keys for multi-instance  |

### AI/Vector Database Scaling Foundation

| Component                      | Batch   | Status | Notes                             |
| ------------------------------ | ------- | ------ | --------------------------------- |
| **pgvector Extension**         | Batch 3 | 🔧 Add | PostgreSQL native vectors         |
| **HNSW Index Strategy**        | Batch 5 | 🔧 Add | Fast ANN search for embeddings    |
| **External Vector DB Ready**   | Batch 5 | 🔧 Add | Pinecone/Qdrant abstraction layer |
| **Embedding Batch Processing** | Batch 5 | 🔧 Add | Async embedding generation        |

### Scaling-Ready Code Patterns

**1. Read Replica Support (Add to Batch 1):**

```python
# apps/backend/src/core/database.py - Add read replica support
import os

# Write operations (master)
WRITE_DATABASE_URL = os.getenv("DATABASE_URL")

# Read operations (replica - falls back to master if not set)
READ_DATABASE_URL = os.getenv("DATABASE_URL_READ", WRITE_DATABASE_URL)

# Create separate engines
write_engine = create_async_engine(WRITE_DATABASE_URL, ...)
read_engine = create_async_engine(READ_DATABASE_URL, ...)

# Usage pattern:
async def get_write_db(): ...  # For INSERT/UPDATE/DELETE
async def get_read_db(): ...   # For SELECT queries
```

**2. Table Partitioning (Add to Batch 1):**

```sql
-- Partition bookings by created_at (quarterly)
-- Keeps queries fast as data grows
CREATE TABLE booking.bookings (
    id UUID NOT NULL,
    created_at TIMESTAMP NOT NULL,
    ...
) PARTITION BY RANGE (created_at);

-- Create partitions
CREATE TABLE booking.bookings_2025_q1 PARTITION OF booking.bookings
    FOR VALUES FROM ('2025-01-01') TO ('2025-04-01');
CREATE TABLE booking.bookings_2025_q2 PARTITION OF booking.bookings
    FOR VALUES FROM ('2025-04-01') TO ('2025-07-01');
-- ... add more as needed

-- Partition audit_log by created_at (monthly - high volume)
CREATE TABLE core.audit_log (
    id UUID NOT NULL,
    created_at TIMESTAMP NOT NULL,
    ...
) PARTITION BY RANGE (created_at);
```

**3. Cache Key Namespacing (Add to Batch 1):**

```python
# apps/backend/src/core/cache.py
import os

CACHE_PREFIX = os.getenv("CACHE_PREFIX", "mh")  # myhibachi
ENV = os.getenv("ENV", "dev")

def cache_key(key: str) -> str:
    """Generate namespaced cache key for multi-instance support."""
    return f"{CACHE_PREFIX}:{ENV}:{key}"

# Usage:
await redis.set(cache_key("booking:123"), data)
await redis.get(cache_key("booking:123"))
```

**4. Vector Index Strategy (Add to Batch 5):**

```sql
-- HNSW index for fast approximate nearest neighbor search
-- Use when you have >10,000 embeddings
CREATE INDEX IF NOT EXISTS idx_kb_chunks_embedding_hnsw
ON ai.kb_chunks
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- For smaller datasets (<10,000), use exact search
CREATE INDEX IF NOT EXISTS idx_kb_chunks_embedding_ivfflat
ON ai.kb_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

### Scaling Triggers (When to Upgrade)

| Metric             | Current   | Trigger           | Action                    |
| ------------------ | --------- | ----------------- | ------------------------- |
| **DB Connections** | 10 pool   | >50 concurrent    | Add PgBouncer             |
| **Read Load**      | Single DB | >70% read queries | Add Read Replica          |
| **Table Size**     | <1M rows  | >1M rows          | Enable partitioning       |
| **AI Embeddings**  | <10K      | >50K vectors      | Switch to Pinecone/Qdrant |
| **Redis Memory**   | <1GB      | >4GB              | Switch to Redis Cluster   |
| **API Costs**      | <$500/mo  | >$500/mo          | Add Local Llama 3         |

### Environment Variables for Scaling

```env
# Database Scaling (add to .env.production)
DATABASE_URL=postgresql+asyncpg://...          # Master (write)
DATABASE_URL_READ=postgresql+asyncpg://...     # Replica (read) - optional
DB_POOL_SIZE=10                                # Base pool size
DB_MAX_OVERFLOW=20                             # Burst capacity
DB_POOL_TIMEOUT=30                             # Connection timeout

# Redis Scaling
REDIS_URL=redis://localhost:6379/0
REDIS_CLUSTER_MODE=false                       # Set true for cluster
CACHE_PREFIX=mh                                # Key namespace

# Vector DB Scaling (Batch 5+)
VECTOR_DB_PROVIDER=pgvector                    # pgvector | pinecone | qdrant
PINECONE_API_KEY=xxx                           # If using Pinecone
PINECONE_INDEX=myhibachi-embeddings
QDRANT_URL=http://localhost:6333               # If using Qdrant

# AI Scaling (Batch 6+)
AI_PRIMARY_PROVIDER=openai                     # openai | anthropic | local
LOCAL_LLAMA_ENABLED=false                      # Enable when API >$500/mo
LOCAL_LLAMA_URL=http://localhost:11434         # Ollama endpoint
```

---

## 📊 SCALING MEASUREMENT SYSTEM (16 Hours Total)

> **Implementation:** Full monitoring dashboard with Admin UI +
> WhatsApp alerts. **Spread across:** Batch 1 (core), Batch 3 (AI
> metrics), Batch 6 (forecasting).

### Implementation Breakdown by Batch

| Batch       | Components                                           | Hours | Notes       |
| ----------- | ---------------------------------------------------- | ----- | ----------- |
| **Batch 1** | Core metrics API, Dashboard UI, WhatsApp alerts      | 8 hrs | Foundation  |
| **Batch 3** | AI metrics, token tracking, cost monitoring          | 4 hrs | AI-specific |
| **Batch 6** | Historical trends, forecasting, auto-recommendations | 4 hrs | Advanced    |

### Metrics to Monitor

#### 1. Database Metrics

| Metric                     | Current | ⚠️ Warning | 🔴 Critical | Scale Action        |
| -------------------------- | ------- | ---------- | ----------- | ------------------- |
| Connection Pool Usage      | 10/30   | >70%       | >90%        | Add PgBouncer       |
| Query Response Time (p95)  | <50ms   | >200ms     | >500ms      | Add read replica    |
| Active Connections         | ~5      | >30        | >50         | Increase pool size  |
| Table Row Count (bookings) | <100K   | >500K      | >1M         | Enable partitioning |
| Database Size              | <5GB    | >20GB      | >50GB       | Archive old data    |
| Slow Queries/hour          | <5      | >20        | >50         | Index optimization  |

#### 2. Redis/Cache Metrics

| Metric            | Current | ⚠️ Warning | 🔴 Critical | Scale Action          |
| ----------------- | ------- | ---------- | ----------- | --------------------- |
| Memory Usage      | <500MB  | >2GB       | >4GB        | Redis Cluster         |
| Hit Rate          | >90%    | <80%       | <60%        | Review cache strategy |
| Connected Clients | ~5      | >50        | >100        | Connection pooling    |
| Evicted Keys/hour | 0       | >100       | >1000       | Increase memory       |

#### 3. AI/Vector Metrics (Batch 3+)

| Metric                | Current | ⚠️ Warning | 🔴 Critical | Scale Action         |
| --------------------- | ------- | ---------- | ----------- | -------------------- |
| API Cost/Month        | <$100   | >$300      | >$500       | Activate Local Llama |
| Vector Count          | <10K    | >30K       | >50K        | Switch to Pinecone   |
| Embedding Search Time | <50ms   | >100ms     | >200ms      | Add HNSW index       |
| AI Response Time      | <2s     | >3s        | >5s         | Add caching          |
| Tokens/Day            | <100K   | >500K      | >1M         | Review prompts       |

#### 4. Application Metrics

| Metric                  | Current | ⚠️ Warning | 🔴 Critical | Scale Action       |
| ----------------------- | ------- | ---------- | ----------- | ------------------ |
| API Response Time (p95) | <200ms  | >500ms     | >1000ms     | Optimize/scale     |
| Error Rate              | <1%     | >2%        | >5%         | Investigate        |
| Concurrent Users        | ~10     | >50        | >100        | Horizontal scale   |
| Memory Usage            | <70%    | >80%       | >90%        | Increase resources |
| CPU Usage               | <50%    | >70%       | >85%        | Increase resources |

### Backend API Endpoints (Batch 1)

```python
# apps/backend/src/routers/v1/scaling_metrics.py

@router.get("/api/v1/admin/scaling/metrics")
async def get_scaling_metrics():
    """Get current scaling metrics for dashboard."""
    return {
        "database": {
            "pool_usage_percent": 27,
            "pool_used": 8,
            "pool_max": 30,
            "query_time_p95_ms": 45,
            "active_connections": 5,
            "table_rows": {"bookings": 156234, "customers": 8921},
            "database_size_gb": 2.1,
            "slow_queries_hour": 2,
            "status": "healthy"  # healthy | warning | critical
        },
        "redis": {
            "memory_used_mb": 512,
            "memory_max_mb": 4096,
            "memory_percent": 12.5,
            "hit_rate_percent": 94,
            "connected_clients": 8,
            "evicted_keys_hour": 0,
            "status": "healthy"
        },
        "ai": {  # Batch 3+
            "cost_month_usd": 247,
            "cost_trend_percent": 15,  # +15% vs last month
            "vector_count": 8234,
            "embedding_search_ms": 35,
            "response_time_avg_s": 1.8,
            "tokens_today": 89000,
            "status": "healthy"
        },
        "application": {
            "response_time_p95_ms": 180,
            "error_rate_percent": 0.3,
            "concurrent_users": 12,
            "memory_percent": 65,
            "cpu_percent": 42,
            "status": "healthy"
        },
        "recommendations": [
            {
                "id": "redis-memory-warning",
                "severity": "warning",
                "title": "Redis Memory at 80%",
                "message": "Consider Redis Cluster when >4GB",
                "action": "redis-cluster",
                "snoozed_until": None
            }
        ],
        "forecast": {  # Batch 6+
            "redis_cluster_needed": "~3 months",
            "read_replica_needed": "~6 months",
            "local_llama_needed": "~4 months"
        }
    }

@router.get("/api/v1/admin/scaling/history")
async def get_scaling_history(days: int = 30):
    """Get historical metrics for trend analysis (Batch 6)."""
    pass

@router.post("/api/v1/admin/scaling/snooze/{recommendation_id}")
async def snooze_recommendation(recommendation_id: str, days: int = 7):
    """Snooze a scaling recommendation."""
    pass

@router.post("/api/v1/admin/scaling/acknowledge/{recommendation_id}")
async def acknowledge_recommendation(recommendation_id: str):
    """Mark recommendation as acknowledged/resolved."""
    pass
```

### Admin Panel Dashboard UI (Batch 1)

```
┌─────────────────────────────────────────────────────────────────────┐
│  🚀 SCALING HEALTH DASHBOARD                        [Last: 30s ago] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  OVERALL STATUS: 🟢 HEALTHY (No immediate scaling needed)           │
│                                                                      │
├──────────────────────┬──────────────────────┬───────────────────────┤
│   📊 DATABASE        │   🔴 REDIS           │   🤖 AI SERVICES      │
│   ───────────────    │   ───────────────    │   ───────────────     │
│   Pool: 8/30 (27%)   │   Memory: 3.2GB ⚠️   │   Cost: $247/mo       │
│   🟢 Healthy         │   🟡 Warning         │   🟢 Healthy          │
│                      │                      │                       │
│   Queries: 45ms avg  │   Hit Rate: 92%      │   Vectors: 8,234      │
│   Rows: 156,234      │   Clients: 12        │   Response: 1.8s      │
│   Size: 2.1GB        │   Evictions: 0       │   Tokens: 89K/day     │
├──────────────────────┴──────────────────────┴───────────────────────┤
│                                                                      │
│  📈 SCALING RECOMMENDATIONS                                         │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                      │
│  ⚠️  REDIS MEMORY at 80% (3.2GB/4GB)                                │
│      Recommendation: Consider Redis Cluster when >4GB               │
│      [📖 View Guide] [⏰ Snooze 7 days] [✅ Mark Resolved]          │
│                                                                      │
│  ℹ️  AI COSTS trending up (+15% this month)                         │
│      Current: $247/mo | Trigger: $500/mo                            │
│      If trend continues: Local Llama needed in ~3 months            │
│      [📖 View Guide] [📊 See Trend]                                 │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│  📅 SCALING TIMELINE FORECAST (Batch 6)                             │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                      │
│  Now ──────●────────────────────────────────────────────────► 12mo  │
│            │    [~3mo]           [~6mo]           [~4mo]            │
│            │    Redis            Read             Local             │
│            │    Cluster          Replica          Llama             │
└─────────────────────────────────────────────────────────────────────┘
```

### WhatsApp Alert System (Batch 1)

```python
# apps/backend/src/services/scaling_alerts.py

from services.whatsapp import WhatsAppService

class ScalingAlertService:
    """Send scaling alerts via WhatsApp to admins."""

    ALERT_TEMPLATES = {
        "warning": """
🟡 *SCALING WARNING - My Hibachi*

*{title}*
Current: {current_value}
Threshold: {threshold}

📊 Status: {status}
📈 Trend: {trend}

*Recommended Action:*
{recommendation}

View Dashboard: {dashboard_url}
        """,
        "critical": """
🔴 *SCALING CRITICAL - My Hibachi*

*{title}*
Current: {current_value}
Threshold: {threshold}

⚠️ *IMMEDIATE ACTION REQUIRED*

*Recommended Action:*
{recommendation}

*Quick Guide:*
{guide_url}

View Dashboard: {dashboard_url}
        """
    }

    async def check_and_alert(self):
        """Check metrics and send alerts if thresholds breached."""
        metrics = await self.get_current_metrics()

        for alert in self.evaluate_thresholds(metrics):
            if not self.is_snoozed(alert["id"]):
                await self.send_whatsapp_alert(alert)

    async def send_whatsapp_alert(self, alert: dict):
        """Send WhatsApp alert to admin numbers."""
        admin_numbers = await self.get_admin_phone_numbers()

        message = self.ALERT_TEMPLATES[alert["severity"]].format(
            title=alert["title"],
            current_value=alert["current"],
            threshold=alert["threshold"],
            status=alert["status"],
            trend=alert["trend"],
            recommendation=alert["recommendation"],
            guide_url=f"https://admin.myhibachi.com/scaling/guides/{alert['action']}",
            dashboard_url="https://admin.myhibachi.com/scaling"
        )

        for number in admin_numbers:
            await WhatsAppService.send_message(number, message)
```

### Cron Job for Metric Checks (Batch 1)

```python
# apps/backend/src/tasks/scaling_monitor.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

# Check metrics every 5 minutes
@scheduler.scheduled_job('interval', minutes=5)
async def check_scaling_metrics():
    """Periodic check of scaling metrics."""
    alert_service = ScalingAlertService()
    await alert_service.check_and_alert()

# Daily summary at 9 AM
@scheduler.scheduled_job('cron', hour=9)
async def daily_scaling_summary():
    """Send daily scaling health summary."""
    metrics = await get_scaling_metrics()
    await send_daily_summary_whatsapp(metrics)
```

### Feature Flags for Scaling System

```env
# Scaling Measurement System
FEATURE_SCALING_DASHBOARD=true           # Batch 1
FEATURE_SCALING_WHATSAPP_ALERTS=true     # Batch 1
FEATURE_SCALING_AI_METRICS=true          # Batch 3
FEATURE_SCALING_FORECASTING=true         # Batch 6
FEATURE_SCALING_AUTO_RECOMMENDATIONS=true # Batch 6

# Alert Configuration
SCALING_ALERT_ADMIN_PHONES=+1234567890,+0987654321
SCALING_ALERT_CHECK_INTERVAL_MINUTES=5
SCALING_ALERT_SNOOZE_DEFAULT_DAYS=7
```

---

## 📚 SCALING IMPLEMENTATION GUIDES

> **One-click access from dashboard alerts.** Each guide provides
> step-by-step instructions for the specific scaling action.

### Guide 1: Add PgBouncer (Connection Pooling)

**When:** DB connections >50 concurrent **Time:** ~2 hours
**Downtime:** Zero (rolling deployment)

```bash
# Step 1: Install PgBouncer on VPS
sudo apt-get update
sudo apt-get install pgbouncer

# Step 2: Configure PgBouncer
sudo nano /etc/pgbouncer/pgbouncer.ini
```

```ini
# /etc/pgbouncer/pgbouncer.ini
[databases]
myhibachi = host=localhost port=5432 dbname=myhibachi

[pgbouncer]
listen_addr = 127.0.0.1
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 200
default_pool_size = 20
min_pool_size = 5
reserve_pool_size = 5
```

```bash
# Step 3: Create auth file
echo '"myhibachi_user" "password_hash"' | sudo tee /etc/pgbouncer/userlist.txt

# Step 4: Start PgBouncer
sudo systemctl enable pgbouncer
sudo systemctl start pgbouncer

# Step 5: Update application config
# Change DATABASE_URL port from 5432 to 6432
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:6432/myhibachi

# Step 6: Verify
psql -h localhost -p 6432 -U myhibachi_user -d myhibachi -c "SELECT 1"
```

**Verification Checklist:**

- [ ] PgBouncer running on port 6432
- [ ] Application connecting through PgBouncer
- [ ] Connection pool stats visible: `SHOW POOLS;`
- [ ] No connection errors in logs

---

### Guide 2: Add Read Replica

**When:** >70% read queries, high DB load **Time:** ~4 hours
**Downtime:** Zero

```bash
# Step 1: Create read replica (depends on hosting)

# For DigitalOcean Managed DB:
doctl databases replica create <db-id> --name myhibachi-replica --region sfo3

# For AWS RDS:
aws rds create-db-instance-read-replica \
    --db-instance-identifier myhibachi-replica \
    --source-db-instance-identifier myhibachi-primary

# For self-hosted PostgreSQL:
# On primary:
sudo -u postgres psql -c "SELECT pg_create_physical_replication_slot('replica1');"

# On replica:
pg_basebackup -h primary-host -D /var/lib/postgresql/14/main -U replicator -P -R
```

```python
# Step 2: Update application code
# apps/backend/src/core/database.py

import os

# Existing write connection
WRITE_DATABASE_URL = os.getenv("DATABASE_URL")

# New read connection (falls back to write if not set)
READ_DATABASE_URL = os.getenv("DATABASE_URL_READ", WRITE_DATABASE_URL)

write_engine = create_async_engine(WRITE_DATABASE_URL, ...)
read_engine = create_async_engine(READ_DATABASE_URL, ...)

async def get_write_db():
    """Use for INSERT, UPDATE, DELETE."""
    async with AsyncSessionLocal(bind=write_engine) as session:
        yield session

async def get_read_db():
    """Use for SELECT queries."""
    async with AsyncSessionLocal(bind=read_engine) as session:
        yield session
```

```python
# Step 3: Update routes to use read replica
@router.get("/bookings")
async def list_bookings(db: AsyncSession = Depends(get_read_db)):  # READ
    ...

@router.post("/bookings")
async def create_booking(db: AsyncSession = Depends(get_write_db)):  # WRITE
    ...
```

```env
# Step 4: Add environment variable
DATABASE_URL_READ=postgresql+asyncpg://user:pass@replica-host:5432/myhibachi
```

**Verification Checklist:**

- [ ] Replica syncing (check replication lag)
- [ ] Read queries going to replica
- [ ] Write queries going to primary
- [ ] No replication lag >1 second

---

### Guide 3: Enable Table Partitioning

**When:** Table >1M rows, slow queries **Time:** ~3 hours
**Downtime:** Brief (during migration)

```sql
-- Step 1: Create new partitioned table
CREATE TABLE booking.bookings_partitioned (
    LIKE booking.bookings INCLUDING ALL
) PARTITION BY RANGE (created_at);

-- Step 2: Create partitions (quarterly)
CREATE TABLE booking.bookings_2024_q4 PARTITION OF booking.bookings_partitioned
    FOR VALUES FROM ('2024-10-01') TO ('2025-01-01');
CREATE TABLE booking.bookings_2025_q1 PARTITION OF booking.bookings_partitioned
    FOR VALUES FROM ('2025-01-01') TO ('2025-04-01');
CREATE TABLE booking.bookings_2025_q2 PARTITION OF booking.bookings_partitioned
    FOR VALUES FROM ('2025-04-01') TO ('2025-07-01');
CREATE TABLE booking.bookings_2025_q3 PARTITION OF booking.bookings_partitioned
    FOR VALUES FROM ('2025-07-01') TO ('2025-10-01');
CREATE TABLE booking.bookings_2025_q4 PARTITION OF booking.bookings_partitioned
    FOR VALUES FROM ('2025-10-01') TO ('2026-01-01');

-- Step 3: Migrate data (during low traffic)
INSERT INTO booking.bookings_partitioned SELECT * FROM booking.bookings;

-- Step 4: Swap tables
BEGIN;
ALTER TABLE booking.bookings RENAME TO bookings_old;
ALTER TABLE booking.bookings_partitioned RENAME TO bookings;
COMMIT;

-- Step 5: Verify and cleanup
-- After verification:
DROP TABLE booking.bookings_old;
```

```python
# Step 6: Add partition maintenance cron job
@scheduler.scheduled_job('cron', day=1, hour=2)  # 1st of each month at 2 AM
async def create_future_partitions():
    """Create partitions 6 months ahead."""
    # Auto-create next quarter's partition if doesn't exist
    ...
```

**Verification Checklist:**

- [ ] All data migrated correctly
- [ ] Queries hitting correct partitions (EXPLAIN ANALYZE)
- [ ] No missing data
- [ ] Auto-partition creation working

---

### Guide 4: Redis Cluster Migration

**When:** Redis memory >4GB **Time:** ~3 hours **Downtime:** Brief
(during switchover)

```bash
# Step 1: Set up Redis Cluster (3 masters minimum)
# Using Docker Compose for simplicity:

# docker-compose.redis-cluster.yml
version: '3'
services:
  redis-1:
    image: redis:7
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf --cluster-node-timeout 5000
    ports:
      - "7001:6379"
  redis-2:
    image: redis:7
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf --cluster-node-timeout 5000
    ports:
      - "7002:6379"
  redis-3:
    image: redis:7
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf --cluster-node-timeout 5000
    ports:
      - "7003:6379"
```

```bash
# Step 2: Create cluster
docker-compose -f docker-compose.redis-cluster.yml up -d
redis-cli --cluster create \
    127.0.0.1:7001 127.0.0.1:7002 127.0.0.1:7003 \
    --cluster-replicas 0
```

```python
# Step 3: Update application to use cluster
# apps/backend/src/core/cache.py

from redis.cluster import RedisCluster

if os.getenv("REDIS_CLUSTER_MODE") == "true":
    redis_client = RedisCluster(
        startup_nodes=[
            {"host": "127.0.0.1", "port": 7001},
            {"host": "127.0.0.1", "port": 7002},
            {"host": "127.0.0.1", "port": 7003},
        ],
        decode_responses=True
    )
else:
    redis_client = Redis.from_url(os.getenv("REDIS_URL"))
```

```env
# Step 4: Update environment
REDIS_CLUSTER_MODE=true
REDIS_CLUSTER_NODES=127.0.0.1:7001,127.0.0.1:7002,127.0.0.1:7003
```

**Verification Checklist:**

- [ ] Cluster healthy: `redis-cli --cluster check`
- [ ] Application connecting to cluster
- [ ] Data distributed across nodes
- [ ] No memory pressure on any single node

---

### Guide 5: Activate Local Llama 3

**When:** AI API costs >$500/mo **Time:** ~4 hours **Downtime:** Zero
(shadow mode first)

```bash
# Step 1: Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Step 2: Pull Llama 3 model
ollama pull llama3:8b  # 8B parameter model (~5GB)
# OR for better quality:
ollama pull llama3:70b  # 70B parameter model (~40GB, needs GPU)

# Step 3: Verify
ollama run llama3:8b "Hello, what is hibachi?"
```

```python
# Step 4: Add Ollama provider to AI service
# apps/backend/src/services/ai/providers/ollama.py

import httpx

class OllamaProvider:
    def __init__(self):
        self.base_url = os.getenv("LOCAL_LLAMA_URL", "http://localhost:11434")

    async def generate(self, prompt: str, model: str = "llama3:8b") -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False}
            )
            return response.json()["response"]
```

```python
# Step 5: Add to AI router with fallback
# apps/backend/src/services/ai/router.py

class AIRouter:
    async def route_request(self, request: AIRequest) -> AIResponse:
        if os.getenv("LOCAL_LLAMA_ENABLED") == "true":
            try:
                # Try local first (free)
                return await self.ollama.generate(request.prompt)
            except Exception:
                # Fallback to OpenAI
                return await self.openai.generate(request.prompt)
        else:
            return await self.openai.generate(request.prompt)
```

```env
# Step 6: Enable in production (after shadow testing)
LOCAL_LLAMA_ENABLED=true
LOCAL_LLAMA_URL=http://localhost:11434
LOCAL_LLAMA_MODEL=llama3:8b
```

**Verification Checklist:**

- [ ] Ollama running and responsive
- [ ] Shadow mode comparing outputs (Batch 6)
- [ ] Response quality acceptable (>80% match)
- [ ] Latency acceptable (<3s)
- [ ] Cost savings visible in dashboard

---

### Guide 6: Switch to Pinecone (Vector DB)

**When:** >50K vectors, slow embedding search **Time:** ~3 hours
**Downtime:** Zero (gradual migration)

```bash
# Step 1: Create Pinecone account and index
pip install pinecone-client

# Create index via Pinecone console or API:
# - Name: myhibachi-embeddings
# - Dimension: 1536 (OpenAI embeddings)
# - Metric: cosine
```

```python
# Step 2: Add Pinecone provider
# apps/backend/src/services/vector/pinecone_provider.py

import pinecone

class PineconeProvider:
    def __init__(self):
        pinecone.init(
            api_key=os.getenv("PINECONE_API_KEY"),
            environment=os.getenv("PINECONE_ENV", "us-west1-gcp")
        )
        self.index = pinecone.Index(os.getenv("PINECONE_INDEX"))

    async def upsert(self, id: str, embedding: list, metadata: dict):
        self.index.upsert([(id, embedding, metadata)])

    async def search(self, embedding: list, top_k: int = 5) -> list:
        results = self.index.query(embedding, top_k=top_k, include_metadata=True)
        return results["matches"]
```

```python
# Step 3: Create vector DB abstraction layer
# apps/backend/src/services/vector/factory.py

class VectorDBFactory:
    @staticmethod
    def get_provider():
        provider = os.getenv("VECTOR_DB_PROVIDER", "pgvector")

        if provider == "pinecone":
            return PineconeProvider()
        elif provider == "qdrant":
            return QdrantProvider()
        else:
            return PgVectorProvider()  # Default
```

```python
# Step 4: Migrate existing vectors
async def migrate_vectors_to_pinecone():
    """One-time migration script."""
    pgvector = PgVectorProvider()
    pinecone = PineconeProvider()

    async for chunk in pgvector.get_all_chunks():
        await pinecone.upsert(
            id=str(chunk.id),
            embedding=chunk.embedding,
            metadata={"content": chunk.content, "source": chunk.source}
        )
        print(f"Migrated {chunk.id}")
```

```env
# Step 5: Switch provider
VECTOR_DB_PROVIDER=pinecone
PINECONE_API_KEY=xxx
PINECONE_INDEX=myhibachi-embeddings
PINECONE_ENV=us-west1-gcp
```

**Verification Checklist:**

- [ ] All vectors migrated
- [ ] Search results match pgvector
- [ ] Search latency <100ms
- [ ] No missing embeddings

---

## 🖥️ FRONTEND DEPLOYMENT STRATEGY

### Frontend Apps Overview

| App               | Path             | Framework  | Deployment |
| ----------------- | ---------------- | ---------- | ---------- |
| **Customer Site** | `apps/customer/` | Next.js 14 | Vercel     |
| **Admin Panel**   | `apps/admin/`    | Next.js 14 | Vercel     |

### Frontend Tasks Per Batch

**Frontends deploy to Vercel automatically**, but UI components must
be built per batch:

---

## 🔄 CI/CD & SECRETS INFRASTRUCTURE (Already Built!)

### ✅ What's Already Configured

| Component                       | Status    | How It Works                                                        |
| ------------------------------- | --------- | ------------------------------------------------------------------- |
| **Frontend Auto-Deploy**        | ✅ Active | Vercel auto-deploys on push to `main`                               |
| **Backend Auto-Deploy**         | ✅ Active | GitHub Actions → SSH → VPS (`.github/workflows/deploy-backend.yml`) |
| **GSM (Google Secret Manager)** | ✅ Active | All secrets centralized, loaded on startup                          |
| **Rolling Restart**             | ✅ Active | Zero-downtime: Instance 2 → health check → Instance 1               |
| **Auto-Rollback**               | ✅ Active | If health check fails, auto-rollback to previous commit             |
| **Smoke Tests**                 | ✅ Active | Post-deploy health check on production URL                          |

### 🚀 Backend Auto-Deploy Flow

```
Push to main (apps/backend/**)
         │
         ▼
┌─────────────────────────────────────┐
│  GitHub Actions: Test Job           │
│  ├── Setup Python 3.11              │
│  ├── Install dependencies           │
│  └── Run unit tests                 │
└─────────────────┬───────────────────┘
                  │ Tests Pass
                  ▼
┌─────────────────────────────────────┐
│  GitHub Actions: Deploy Job         │
│  ├── SSH into VPS                   │
│  ├── git pull origin main           │
│  ├── pip install -r requirements.txt│
│  ├── alembic upgrade head           │
│  └── Rolling restart (2 instances)  │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│  GitHub Actions: Smoke Test         │
│  ├── curl /api/health               │
│  └── curl /docs                     │
└─────────────────────────────────────┘
```

### 🔐 GSM (Google Secret Manager) Integration

All secrets are managed via GSM and loaded on backend startup:

```python
# apps/backend/src/start_with_gsm.py
async def startup_with_gsm():
    """Load configuration from GSM and start the application"""
    # Loads all secrets: DB, Redis, API keys, etc.
```

**Secrets in GSM:**

- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `OPENAI_API_KEY` - AI services
- `STRIPE_SECRET_KEY` - Payments
- `RINGCENTRAL_*` - Voice/SMS
- All other API keys...

### 📝 What "Manual" Means in This Context

When we say "manual deploy per batch", we mean:

1. **Code changes** - You write the code manually (obviously)
2. **Feature flags** - You manually enable flags when ready
3. **Database migrations** - You verify migrations work before
   enabling auto-deploy
4. **Batch verification** - You manually test batch before moving to
   next

**The deployment itself is AUTOMATIC once you push to `main`!**

### 🎯 Batch Deployment Workflow (Corrected)

```
1. Develop on feature/batch-X branch
2. Test locally + staging
3. Merge to dev (staging auto-deploys to Vercel preview)
4. Test on staging
5. Merge to main
   └── 🤖 AUTO: Backend deploys via GitHub Actions
   └── 🤖 AUTO: Frontend deploys via Vercel
   └── 🤖 AUTO: GSM secrets loaded automatically
6. Monitor for 48 hours (manual)
7. Enable feature flags (manual)
8. Start next batch
```

---

## 🔄 Git Workflow (Enterprise Standard)

```
BRANCHING STRATEGY
══════════════════

                    main (production)
                         │
                         │ ← merge only when 100% tested
                         │
    ┌────────────────────┴────────────────────┐
    │                                         │
    │                  dev                    │
    │           (staging/testing)             │
    │                   │                     │
    │     ┌─────────────┼─────────────┐       │
    │     │             │             │       │
    │  feature/     feature/     feature/     │
    │  batch-1      batch-2      batch-3      │
    │                                         │
    └─────────────────────────────────────────┘

MERGE FLOW:
1. feature/batch-X → dev (PR + code review)
2. Test on staging (full QA)
3. dev → main (only when 100% ready)
4. Tag release: v1.0.0-batch1
5. Deploy to production
6. Monitor 48-72 hours
7. Start next batch
```

---

## 📦 7-BATCH DEPLOYMENT PLAN (Including Batch 0)

> **Note:** Batch 0 is a prerequisite phase for repository cleanup and
> branch strategy setup. All subsequent batches depend on Batch 0.

### Batch Dependencies Diagram

```
                    ┌─────────────────┐
                    │    BATCH 0      │
                    │  Repo Cleanup   │
                    │ Branch Strategy │
                    │   (Pre-work)    │
                    └────────┬────────┘
                             │ REQUIRED
                             ▼
                    ┌─────────────────┐
                    │    BATCH 1      │
                    │  Core Booking   │
                    │   + Security    │
                    │   (Week 1-2)    │
                    └────────┬────────┘
                             │ REQUIRED
                             ▼
                    ┌─────────────────┐
                    │    BATCH 2      │
                    │    Payments     │
                    │   (Week 3-4)    │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │ REQUIRED                     │ REQUIRED
              ▼                              ▼
      ┌─────────────────┐          ┌─────────────────┐
      │    BATCH 3      │          │    BATCH 4      │
      │    Core AI      │          │ Communications  │
      │   (Week 5-6)    │          │   (Week 7-8)    │
      └────────┬────────┘          └────────┬────────┘
               │                             │
               │ REQUIRED                    │
               ▼                             │
      ┌─────────────────┐                    │
      │    BATCH 5      │◀───────────────────┘
      │  Advanced AI +  │     RECOMMENDED
      │   Marketing     │
      │   (Week 9-10)   │
      └────────┬────────┘
               │ RECOMMENDED
               ▼
      ┌─────────────────┐
      │    BATCH 6      │
      │ AI Training &   │
      │    Scaling      │
      │  (Week 11-12)   │
      └─────────────────┘
```

---

## 🟢 BATCH 0: Repository Cleanup & Branch Strategy (Pre-requisite)

**Priority:** CRITICAL **Branch:**
`nuclear-refactor-clean-architecture` → `main` **Duration:** 1-2 days
**Status:** 🔄 IN PROGRESS

> **Purpose:** Establish clean repository foundation before
> implementing features. This batch MUST complete before any feature
> batch can begin.

### Why Batch 0 is Required

| Issue                         | Impact                        | Resolution             |
| ----------------------------- | ----------------------------- | ---------------------- |
| 229 uncommitted files         | Cannot track changes properly | Commit all             |
| Main branch 32 commits behind | Stale production baseline     | Merge nuclear-refactor |
| No dev branch                 | No staging environment        | Create from main       |
| No branch protection          | Risk of accidental pushes     | Configure GitHub       |
| 8,000+ line deployment doc    | Hard to maintain              | Split into hierarchy   |
| Duplicate instruction files   | Conflicting rules             | Consolidate            |

### Phase 0.1: Instruction Files Restructure (COMPLETE)

| Task                           | Status  | Notes                                                      |
| ------------------------------ | ------- | ---------------------------------------------------------- |
| Delete duplicate files         | ✅ Done | Removed `01-AGENT_RULES.md`, `02-AGENT_AUDIT_STANDARDS.md` |
| Delete placeholder stubs       | ✅ Done | Removed 6 empty files                                      |
| Create enterprise instructions | ✅ Done | 10 new structured files                                    |
| Create CURRENT_BATCH_STATUS.md | ✅ Done | Root-level batch tracking                                  |

**New Instruction File Structure:**

```
.github/instructions/
├── 00-BOOTSTRAP.instructions.md         # Master loader
├── 01-CORE_PRINCIPLES.instructions.md   # Non-negotiables
├── 02-ARCHITECTURE.instructions.md      # System structure
├── 03-BRANCH_GIT_WORKFLOW.instructions.md  # Branch rules
├── 04-BATCH_DEPLOYMENT.instructions.md  # Batch context
├── 05-AUDIT_STANDARDS.instructions.md   # A-H methodology
├── 06-DOCUMENTATION.instructions.md     # Doc standards
├── 07-TESTING_QA.instructions.md        # Test requirements
├── 08-FEATURE_FLAGS.instructions.md     # Flag rules
└── 09-ROLLBACK_SAFETY.instructions.md   # Emergency procedures
```

### Phase 0.2: Git Cleanup

| Task                           | Status     | Effort | Notes               |
| ------------------------------ | ---------- | ------ | ------------------- |
| Audit uncommitted changes      | ⏳ Pending | 30 min | Review 229 files    |
| Stage all valid changes        | ⏳ Pending | 15 min | git add -A          |
| Commit with meaningful message | ⏳ Pending | 15 min | Split if needed     |
| Push to remote                 | ⏳ Pending | 5 min  | Backup current work |

**Uncommitted Files Summary:**

- **167 deleted** - Cleanup of backup files, temp scripts, old docs
  (SAFE)
- **33 untracked** - Important new files (migrations, services, docs)
- **29 modified** - Valid code changes (config, models, routers)

### Phase 0.3: Branch Strategy Setup

| Task                               | Status     | Effort | Notes                        |
| ---------------------------------- | ---------- | ------ | ---------------------------- |
| Create PR: nuclear-refactor → main | ⏳ Pending | 30 min | 32 commits to merge          |
| Review and merge PR                | ⏳ Pending | 1 hr   | May need conflict resolution |
| Create `dev` branch from main      | ⏳ Pending | 5 min  | Staging environment          |
| Apply branch protection (main)     | ⏳ Pending | 15 min | Strict protection            |
| Apply branch protection (dev)      | ⏳ Pending | 10 min | Moderate protection          |
| Update CI/CD triggers              | ⏳ Pending | 30 min | Add dev → staging deploy     |

**Branch Protection Settings:**

```yaml
# Main Branch (Production)
require_pull_request: true
required_approvals: 1
require_status_checks: true
require_branches_up_to_date: true
restrict_pushes: true

# Dev Branch (Staging)
require_pull_request: true
required_approvals: 0  # Expedited flow
require_status_checks: true
```

### Phase 0.4: Documentation Hierarchy (Optional)

| Task                    | Status      | Effort | Notes          |
| ----------------------- | ----------- | ------ | -------------- |
| Add Batch 0 to this doc | ✅ Done     | 30 min | This section   |
| Create batches/ folder  | ⏳ Optional | 2 hrs  | Per-batch docs |
| Split large sections    | ⏳ Optional | 3 hrs  | If needed      |
| Update docs/README.md   | ⏳ Pending  | 15 min | Index update   |

### Phase 0.5: Repository Hygiene

| Task                               | Status     | Effort | Notes              |
| ---------------------------------- | ---------- | ------ | ------------------ |
| Delete `apps/backend_backup_*.zip` | ⏳ Pending | 5 min  | Old backup         |
| Verify .gitignore complete         | ⏳ Pending | 15 min | Check all patterns |
| Clean archives folder              | ⏳ Pending | 10 min | Verify structure   |
| Final security audit               | ⏳ Pending | 30 min | No secrets in code |

### Feature Flags (Batch 0)

```env
# No new feature flags in Batch 0
# This batch is infrastructure-only
```

### Success Criteria (Batch 0)

- [ ] All 229 uncommitted files committed
- [ ] PR merged: nuclear-refactor → main
- [ ] `dev` branch created from main
- [ ] Branch protection applied to main and dev
- [ ] CURRENT_BATCH_STATUS.md created and tracked
- [ ] All 10 instruction files in place
- [ ] No backup/temp files in repo
- [ ] Clean git status (no uncommitted changes)

### Rollback Plan (Batch 0)

Since Batch 0 is cleanup-only:

1. **If merge fails:** Keep working on nuclear-refactor branch
2. **If branch protection breaks CI:** Temporarily disable protection
3. **If instruction files cause issues:** Revert to previous versions
   from git history

### Estimated Time

| Phase                 | Effort             |
| --------------------- | ------------------ |
| 0.1 Instruction Files | ✅ Complete        |
| 0.2 Git Cleanup       | 1 hour             |
| 0.3 Branch Strategy   | 2 hours            |
| 0.4 Documentation     | 3 hours (optional) |
| 0.5 Repo Hygiene      | 1 hour             |
| **Total**             | **4-7 hours**      |

---

## 🔴 BATCH 1: Core Booking Engine + Security (Week 1-2)

**Priority:** CRITICAL **Branch:** `feature/batch-1-core`
**Duration:** 2 weeks **Prerequisite:** Batch 0 complete

### Components

| Component        | Status   | Routes   | Notes                          |
| ---------------- | -------- | -------- | ------------------------------ |
| Customer CRUD    | ✅ Ready | ~20      | Create, read, update customers |
| Chef CRUD        | ✅ Ready | ~15      | Chef profiles, availability    |
| Booking CRUD     | ✅ Ready | ~30      | Core booking operations        |
| Quote/Pricing    | ✅ Ready | ~15      | Price calculations             |
| Calendar         | ✅ Ready | ~10      | Scheduling system              |
| Authentication   | ✅ Ready | ~15      | JWT + API keys                 |
| Health endpoints | ✅ Ready | ~5       | K8s/monitoring ready           |
| **Total**        |          | **~150** |                                |

### 4-Tier RBAC System (From `RBAC_IMPLEMENTATION_COMPLETE_SUMMARY.md`)

| Role             | Permissions                               | Status   |
| ---------------- | ----------------------------------------- | -------- |
| SUPER_ADMIN      | Full access + user management             | ✅ Built |
| ADMIN            | Most operations except user management    | ✅ Built |
| CUSTOMER_SUPPORT | Read + limited write (bookings, messages) | ✅ Built |
| STATION_MANAGER  | Station-specific CRUD                     | ✅ Built |
| CHEF             | Own profile + assigned bookings only      | ✅ Built |

#### RBAC Tables Ready

- `roles` table - Role definitions
- `permissions` table - Permission definitions
- `role_permissions` table - Many-to-many mapping
- `user_roles` table - User role assignments
- Station-based multi-tenancy via `station_id` FK

### Audit Trail System (From Migration 004)

| Feature                    | Status     | Notes                   |
| -------------------------- | ---------- | ----------------------- |
| `audit_log` table          | ✅ Created | Tracks all data changes |
| Soft Delete                | ✅ Ready   | 30-day restore window   |
| Delete Reason Tracking     | ✅ Ready   | Mandatory 10-500 chars  |
| `deleted_at`, `deleted_by` | ✅ Ready   | Auto-populated          |

### Failed Booking Lead Capture (From `FAILED_BOOKING_LEAD_CAPTURE.md`)

| Feature                         | Status   | Notes                       |
| ------------------------------- | -------- | --------------------------- |
| Auto-capture on booking failure | ✅ Built | Saves customer info         |
| Lead source tracking            | ✅ Built | Tracks where lead came from |
| AI follow-up trigger            | ✅ Built | Auto-initiates nurture      |
| Admin lead queue                | ✅ Built | CRM integration ready       |

### Security (Cloudflare)

| Feature                 | Priority | Effort  |
| ----------------------- | -------- | ------- |
| Cloudflare Tunnel       | HIGH     | 2 hours |
| Cloudflare Access (SSH) | HIGH     | 2 hours |
| WAF Rules               | HIGH     | 3 hours |
| Admin Panel Protection  | HIGH     | 2 hours |
| SSL/TLS Full Strict     | HIGH     | 1 hour  |

### Feature Flags

```env
FEATURE_CORE_API=true
FEATURE_AUTH=true
FEATURE_CLOUDFLARE_TUNNEL=true
FEATURE_RBAC=true
FEATURE_AUDIT_TRAIL=true
FEATURE_SOFT_DELETE=true
FEATURE_FAILED_BOOKING_LEAD_CAPTURE=true
FEATURE_SCALING_DASHBOARD=true
FEATURE_SCALING_WHATSAPP_ALERTS=true
```

### Backend Tasks (Batch 1 - Scaling Measurement)

> **8 hours** | Core metrics API, Dashboard endpoints, WhatsApp alerts

| Task                        | Status   | Effort | Notes                                    |
| --------------------------- | -------- | ------ | ---------------------------------------- |
| **Scaling Metrics API**     | 🔧 Build | 3 hrs  | `/api/v1/admin/scaling/metrics` endpoint |
| **Database Pool Metrics**   | 🔧 Build | 1 hr   | Query pool usage, connection count       |
| **Redis Metrics Collector** | 🔧 Build | 1 hr   | Memory, hit rate, clients                |
| **WhatsApp Alert Service**  | 🔧 Build | 2 hrs  | `ScalingAlertService` class              |
| **Cron Job (5-min check)**  | 🔧 Build | 30 min | APScheduler periodic checks              |
| **Daily Summary (9 AM)**    | 🔧 Build | 30 min | Daily health summary via WhatsApp        |

**Files to Create:**

- `apps/backend/src/routers/v1/scaling_metrics.py` - API endpoints
- `apps/backend/src/services/scaling_alerts.py` - Alert service
- `apps/backend/src/tasks/scaling_monitor.py` - Scheduled tasks

**See:** `📊 SCALING MEASUREMENT SYSTEM` section above for full
implementation code.

### Database Migrations (Batch 1)

```bash
# Run in order:
psql -d myhibachi -f database/migrations/setup_db_enums.sql
psql -d myhibachi -f database/migrations/create_all_missing_enums.sql
psql -d myhibachi -f database/migrations/add_security_tables.sql
psql -d myhibachi -f apps/backend/migrations/add_login_history_table.sql
psql -d myhibachi -f database/migrations/001_create_performance_indexes.sql
psql -d myhibachi -f database/migrations/create_ai_tables.sql  # AI foundation!
```

### Frontend Tasks (Batch 1)

| App               | Component                            | Status    | Effort  | Notes                                               |
| ----------------- | ------------------------------------ | --------- | ------- | --------------------------------------------------- |
| **Customer Site** | Booking form                         | ✅ Exists | -       | Verify works with new API                           |
| **Customer Site** | Quote calculator                     | ✅ Exists | -       | Test pricing endpoint                               |
| **Customer Site** | Login/Register                       | ✅ Exists | -       | Test JWT auth flow                                  |
| **Customer Site** | **Contact info protection**          | 🔧 Build  | 1.5 hrs | JS decode for phone, /contact links for email       |
| **Customer Site** | **Remove Yelp & Google from Footer** | 🔧 Build  | 15 min  | Keep Google/Yelp only on /contact, /BookUs, /review |
| **Admin Panel**   | Dashboard                            | ✅ Exists | -       | Connect to new API                                  |
| **Admin Panel**   | Bookings list                        | ✅ Exists | -       | Test CRUD operations                                |
| **Admin Panel**   | Chef management                      | ✅ Exists | -       | Test assignments                                    |
| **Admin Panel**   | RBAC UI                              | 🔧 Build  | 6 hrs   | Role/permission management                          |
| **Admin Panel**   | Audit log viewer                     | 🔧 Build  | 4 hrs   | View data changes                                   |
| **Admin Panel**   | **Scaling Health Dashboard**         | 🔧 Build  | 4 hrs   | Real-time metrics, alerts, guides                   |

#### Scaling Dashboard Admin UI (Batch 1)

> **4 hours** | Part of the 8-hour Scaling Measurement System backend
> work

**Components to Build:**

- `apps/admin/src/app/(dashboard)/scaling/page.tsx` - Main dashboard
- `apps/admin/src/components/scaling/MetricCard.tsx` - Status
  indicator card
- `apps/admin/src/components/scaling/RecommendationList.tsx` - Alert
  list
- `apps/admin/src/components/scaling/ScalingGuideModal.tsx` - Guide
  viewer

**Dashboard Features:**

- Overall status indicator (Healthy/Warning/Critical)
- 4 metric panels: Database, Redis, AI, Application
- Scaling recommendations with snooze/acknowledge actions
- Links to step-by-step scaling guides
- Refresh interval: 30 seconds (configurable)

**See:** `📊 SCALING MEASUREMENT SYSTEM` section above for dashboard
wireframe.

#### Contact Info Protection (Anti-Scraper/Anti-Spam)

> **CRITICAL:** Remove all hardcoded phone numbers and emails to
> prevent scraping, spam, and scam calls.

**Strategy:**

- **Phone Numbers:** JavaScript decode (client-side only) - scrapers
  see nothing
- **Emails:** Replace with `/contact` page links - no email exposed

**Files to Update:**

| File                       | Issue                              | Fix                                    |
| -------------------------- | ---------------------------------- | -------------------------------------- |
| `Footer.tsx`               | Hardcoded phone `(916) 740-8768`   | Use `<ProtectedPhone />` component     |
| `Footer.tsx`               | Yelp link in social icons          | **REMOVE** - keep only on /contact     |
| `ContactPageClient.tsx`    | Hardcoded phone + email            | Use `<ProtectedPhone />`, link to form |
| `not-found.tsx`            | Hardcoded phone                    | Use `<ProtectedPhone />` component     |
| `terms/page.tsx`           | Hardcoded phone + email (2 places) | Use components                         |
| `privacy/page.tsx`         | Hardcoded phone + email            | Use components                         |
| `allergens/page.tsx`       | Hardcoded phone + email (2 places) | Use components                         |
| `booking-success/page.tsx` | Hardcoded phone + email            | Use components, link to /contact       |
| `BookUs/page.tsx`          | Hardcoded email                    | Link to /contact form                  |
| Blog posts (MDX)           | Hardcoded `info@myhibachi.com`     | Use `/contact` page link               |

**JavaScript Decode Implementation:**

```tsx
// apps/customer/src/components/ui/ProtectedPhone.tsx
'use client';

import { useEffect, useState } from 'react';

interface ProtectedPhoneProps {
  className?: string;
  showIcon?: boolean;
}

// Base64 encoded phone number (encode: btoa('916-740-8768'))
const ENCODED_PHONE = 'OTE2LTc0MC04NzY4';
const ENCODED_TEL = 'KzE5MTY3NDA4NzY4'; // btoa('+19167408768')

export function ProtectedPhone({
  className,
  showIcon = true,
}: ProtectedPhoneProps) {
  const [phone, setPhone] = useState<string | null>(null);
  const [tel, setTel] = useState<string | null>(null);

  useEffect(() => {
    // Decode only on client-side - scrapers see nothing
    try {
      setPhone(atob(ENCODED_PHONE));
      setTel(atob(ENCODED_TEL));
    } catch {
      // Fallback for SSR or decode errors
      setPhone(null);
    }
  }, []);

  if (!phone || !tel) {
    // SSR/Loading: Show nothing to scrapers
    return (
      <span className={className} aria-label="Phone number loading">
        {showIcon && '📞 '}Call Us
      </span>
    );
  }

  return (
    <a
      href={`tel:${tel}`}
      className={className}
      aria-label={`Call us at ${phone}`}
    >
      {showIcon && '📞 '}({phone.slice(0, 3)}) {phone.slice(4, 7)}-
      {phone.slice(8)}
    </a>
  );
}

// For places that need just the formatted number (no link)
export function useProtectedPhone() {
  const [phone, setPhone] = useState<string | null>(null);
  const [tel, setTel] = useState<string | null>(null);

  useEffect(() => {
    try {
      setPhone(atob(ENCODED_PHONE));
      setTel(atob(ENCODED_TEL));
    } catch {
      setPhone(null);
    }
  }, []);

  return {
    phone, // "916-740-8768"
    tel, // "+19167408768"
    formatted: phone
      ? `(${phone.slice(0, 3)}) ${phone.slice(4, 7)}-${phone.slice(8)}`
      : null,
    isLoaded: !!phone,
  };
}
```

**Usage Examples:**

```tsx
// Simple phone link
import { ProtectedPhone } from '@/components/ui/ProtectedPhone';
<ProtectedPhone className="text-primary" />

// In Footer (replace hardcoded)
<li>
  <Phone size={18} className={styles.contactIcon} />
  <ProtectedPhone showIcon={false} />
</li>

// For custom formatting
import { useProtectedPhone } from '@/components/ui/ProtectedPhone';
const { formatted, tel, isLoaded } = useProtectedPhone();
{isLoaded && <a href={`tel:${tel}`}>{formatted}</a>}
```

**Email Protection (No Email Shown):**

```tsx
// Instead of showing email, link to contact form
// Before:
<a href="mailto:cs@myhibachichef.com">cs@myhibachichef.com</a>

// After:
<Link href="/contact#email-us">
  <Mail size={18} /> Email Us
</Link>
```

**Why This Works:**

- Server-side scrapers see: `"Call Us"` (no phone number)
- Google sees: `tel:+19167408768` in href after JS executes (for
  mobile click-to-call)
- Users see: `(916) 740-8768` after JS loads (~100ms)
- Accessibility: `aria-label` provides screen reader support

#### Google/Yelp Link Visibility Rules

| Page                           | Google Link    | Yelp Link      | Reason                                |
| ------------------------------ | -------------- | -------------- | ------------------------------------- |
| Homepage (`/`)                 | ❌ Hide        | ❌ Hide        | First impression - focus on booking   |
| Menu (`/menu`)                 | ❌ Hide        | ❌ Hide        | Focus on food, not reviews            |
| Quote (`/quote`)               | ❌ Hide        | ❌ Hide        | Focus on quote flow                   |
| Blog posts                     | ❌ Hide        | ❌ Hide        | SEO content - link to /contact        |
| **Footer (all pages)**         | ❌ **REMOVE**  | ❌ **REMOVE**  | Remove both review platform icons     |
| **Contact (`/contact`)**       | ✅ Show        | ✅ Show        | Appropriate placement                 |
| **Book Us (`/BookUs`)**        | ✅ Show        | ✅ Show        | Decision support                      |
| **Review pages (`/review/*`)** | ✅ Show        | ✅ Show        | After positive rating only            |
| **Booking Success**            | ⚠️ Conditional | ⚠️ Conditional | Part of review request flow (Batch 5) |

### 🚀 Performance Optimization (Batch 1)

> **Total: 18 hours** | Frontend + Backend performance foundations

#### Frontend Performance Tasks

| Task                             | Status   | Effort | Impact            | Notes                         |
| -------------------------------- | -------- | ------ | ----------------- | ----------------------------- |
| **Lazy DatePicker**              | 🔧 Build | 2 hrs  | ~250KB savings    | BookUs page optimization      |
| **API Response Caching Headers** | 🔧 Build | 2 hrs  | 30% faster loads  | Middleware for cache headers  |
| **Client-Side Data Caching**     | 🔧 Build | 4 hrs  | Reduced API calls | SWR/React Query pattern       |
| **Link Prefetching**             | 🔧 Build | 2 hrs  | Faster navigation | Next.js prefetch optimization |
| **Image Preloading**             | 🔧 Build | 1 hr   | Faster LCP        | Critical images above fold    |

**Lazy DatePicker Implementation:**

```tsx
// apps/customer/src/components/lazy/LazyDatePicker.tsx
import dynamic from 'next/dynamic';
import { Skeleton } from '@/components/ui/skeleton';

export const LazyDatePicker = dynamic(
  () => import('react-datepicker').then(mod => mod.default),
  {
    loading: () => <Skeleton className="h-10 w-full" />,
    ssr: false, // DatePicker doesn't need SSR
  }
);

// Usage in BookUs page:
// Before: import DatePicker from 'react-datepicker'; // ~250KB
// After: import { LazyDatePicker } from '@/components/lazy/LazyDatePicker';
```

**Client-Side Caching Service:**

```tsx
// apps/customer/src/lib/cache/CacheService.ts
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

class CacheService {
  private cache = new Map<string, CacheEntry<unknown>>();
  private maxSize = 100;

  set<T>(key: string, data: T, ttlMs: number = 5 * 60 * 1000): void {
    if (this.cache.size >= this.maxSize) {
      const oldestKey = this.cache.keys().next().value;
      this.cache.delete(oldestKey);
    }
    this.cache.set(key, { data, timestamp: Date.now(), ttl: ttlMs });
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key) as CacheEntry<T> | undefined;
    if (!entry) return null;
    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return null;
    }
    return entry.data;
  }

  invalidate(pattern: string): void {
    for (const key of this.cache.keys()) {
      if (key.includes(pattern)) this.cache.delete(key);
    }
  }
}

export const cacheService = new CacheService();

// Usage:
// const cached = cacheService.get<Menu[]>('menu');
// if (!cached) { fetch and cacheService.set('menu', data, 10 * 60 * 1000); }
```

**API Caching Headers Middleware:**

```tsx
// apps/customer/src/middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const response = NextResponse.next();
  const path = request.nextUrl.pathname;

  // Static assets - cache aggressively (1 year)
  if (path.startsWith('/_next/static/')) {
    response.headers.set(
      'Cache-Control',
      'public, max-age=31536000, immutable'
    );
  }

  // Images - cache for 1 week
  if (path.match(/\.(jpg|jpeg|png|webp|avif|svg|ico)$/)) {
    response.headers.set(
      'Cache-Control',
      'public, max-age=604800, stale-while-revalidate=86400'
    );
  }

  // API responses - cache briefly with revalidation
  if (path.startsWith('/api/')) {
    response.headers.set(
      'Cache-Control',
      'private, max-age=60, stale-while-revalidate=120'
    );
  }

  // HTML pages - no cache (dynamic)
  if (!path.includes('.')) {
    response.headers.set(
      'Cache-Control',
      'no-cache, no-store, must-revalidate'
    );
  }

  return response;
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
```

#### Backend Performance Tasks

| Task                           | Status   | Effort | Impact               | Notes                            |
| ------------------------------ | -------- | ------ | -------------------- | -------------------------------- |
| **Query Result Caching**       | 🔧 Build | 3 hrs  | 50% faster reads     | Redis cache for frequent queries |
| **N+1 Query Prevention**       | 🔧 Build | 4 hrs  | 80% faster lists     | Eager loading patterns           |
| **Response Compression**       | 🔧 Build | 1 hr   | 60% smaller payloads | GZIP/Brotli middleware           |
| **Database Query Logging**     | 🔧 Build | 2 hrs  | Debug slow queries   | SQLAlchemy event listeners       |
| **Connection Pool Monitoring** | 🔧 Build | 1 hr   | Prevent exhaustion   | Pool stats endpoint              |

**Query Result Caching:**

```python
# apps/backend/src/core/cache_decorator.py
import hashlib
import json
from functools import wraps
from typing import Callable, Optional
from redis import Redis

redis_client = Redis.from_url(os.getenv("REDIS_URL"))

def cached(ttl_seconds: int = 300, key_prefix: str = ""):
    """Cache function results in Redis."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and args
            key_data = f"{func.__name__}:{args}:{sorted(kwargs.items())}"
            cache_key = f"{key_prefix}:{hashlib.md5(key_data.encode()).hexdigest()}"

            # Try cache first
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # Execute function and cache result
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, ttl_seconds, json.dumps(result, default=str))
            return result
        return wrapper
    return decorator

# Usage:
# @cached(ttl_seconds=300, key_prefix="menu")
# async def get_menu_items(category: str): ...
```

**N+1 Prevention with Eager Loading:**

```python
# apps/backend/src/repositories/booking_repository.py
from sqlalchemy.orm import selectinload, joinedload

class BookingRepository:
    async def get_bookings_with_relations(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20
    ) -> list[Booking]:
        """Prevent N+1 by eager loading related entities."""
        query = (
            select(Booking)
            .options(
                selectinload(Booking.customer),      # Load customer in 1 query
                selectinload(Booking.chef),          # Load chef in 1 query
                selectinload(Booking.menu_items),    # Load menu items in 1 query
                joinedload(Booking.venue),           # JOIN for single venue
            )
            .offset(skip)
            .limit(limit)
            .order_by(Booking.created_at.desc())
        )
        result = await db.execute(query)
        return result.scalars().unique().all()
```

**Response Compression Middleware:**

```python
# apps/backend/src/middleware/compression.py
from fastapi import FastAPI
from starlette.middleware.gzip import GZipMiddleware

def add_compression(app: FastAPI):
    """Add GZIP compression for responses >500 bytes."""
    app.add_middleware(GZipMiddleware, minimum_size=500)

# In main.py:
# add_compression(app)
```

**Database Query Logging:**

```python
# apps/backend/src/core/query_logger.py
import logging
import time
from sqlalchemy import event
from sqlalchemy.engine import Engine

logger = logging.getLogger("sqlalchemy.slow_queries")

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault("query_start_time", []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info["query_start_time"].pop(-1)
    if total > 0.1:  # Log queries >100ms
        logger.warning(f"SLOW QUERY ({total:.3f}s): {statement[:200]}")

# Enable in development/staging:
# if settings.ENVIRONMENT != "production":
#     import core.query_logger  # noqa
```

### 🎨 UI/UX Polish (Batch 1)

> **Total: 24 hours** | Core user experience foundations

#### UI Component Tasks

| Task                            | Status   | Effort | Impact                | Notes                     |
| ------------------------------- | -------- | ------ | --------------------- | ------------------------- |
| **Global Skeleton Loaders**     | 🔧 Build | 4 hrs  | Better perceived perf | Consistent loading states |
| **Error Boundary System**       | 🔧 Build | 3 hrs  | No blank screens      | Graceful error handling   |
| **Toast Notification System**   | 🔧 Build | 3 hrs  | User feedback         | Success/error/info toasts |
| **Loading Progress Indicators** | 🔧 Build | 2 hrs  | User knows status     | Top bar + spinners        |
| **Form Auto-Save**              | 🔧 Build | 4 hrs  | Prevent data loss     | BookUs form persistence   |
| **Accessibility Audit**         | 🔧 Audit | 6 hrs  | A11y compliance       | WCAG 2.1 AA               |
| **Focus Management**            | 🔧 Build | 2 hrs  | Keyboard navigation   | Focus traps, skip links   |

**Global Skeleton Loader Component:**

```tsx
// apps/customer/src/components/ui/skeleton.tsx
import { cn } from '@/lib/utils';

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular' | 'card';
  lines?: number;
  animate?: boolean;
}

export function Skeleton({
  className,
  variant = 'rectangular',
  lines = 1,
  animate = true,
}: SkeletonProps) {
  const baseClasses = cn(
    'bg-gray-200 dark:bg-gray-700',
    animate && 'animate-pulse',
    {
      rounded: variant === 'text',
      'rounded-full': variant === 'circular',
      'rounded-lg': variant === 'rectangular' || variant === 'card',
    },
    className
  );

  if (variant === 'card') {
    return (
      <div className={cn('p-4 space-y-3', baseClasses)}>
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  if (lines > 1) {
    return (
      <div className="space-y-2">
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={cn(
              baseClasses,
              'h-4',
              i === lines - 1 ? 'w-3/4' : 'w-full'
            )}
          />
        ))}
      </div>
    );
  }

  return <div className={baseClasses} />;
}

// Page-level skeleton
export function PageSkeleton() {
  return (
    <div className="container mx-auto p-4 space-y-6">
      <Skeleton className="h-8 w-1/3" /> {/* Title */}
      <Skeleton className="h-4 w-2/3" /> {/* Subtitle */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Skeleton variant="card" className="h-48" />
        <Skeleton variant="card" className="h-48" />
        <Skeleton variant="card" className="h-48" />
      </div>
    </div>
  );
}

// Booking form skeleton
export function BookingFormSkeleton() {
  return (
    <div className="space-y-4 p-6">
      <Skeleton className="h-10 w-full" /> {/* Date picker */}
      <Skeleton className="h-10 w-full" /> {/* Time picker */}
      <Skeleton className="h-10 w-full" /> {/* Guest count */}
      <Skeleton className="h-24 w-full" /> {/* Address */}
      <Skeleton className="h-12 w-full" /> {/* Submit button */}
    </div>
  );
}
```

**Error Boundary System:**

```tsx
// apps/customer/src/components/error/ErrorBoundary.tsx
'use client';

import { Component, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
    this.props.onError?.(error, errorInfo);

    // Send to error tracking (Sentry, etc.)
    // captureException(error, { extra: errorInfo });
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div className="min-h-[400px] flex items-center justify-center p-8">
          <div className="text-center space-y-4 max-w-md">
            <AlertTriangle className="h-16 w-16 text-yellow-500 mx-auto" />
            <h2 className="text-2xl font-bold text-gray-900">
              Something went wrong
            </h2>
            <p className="text-gray-600">
              We're sorry, but something unexpected happened. Please
              try again.
            </p>
            <div className="flex gap-4 justify-center">
              <Button
                onClick={() => this.setState({ hasError: false })}
                variant="outline"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again
              </Button>
              <Button asChild>
                <Link href="/">
                  <Home className="h-4 w-4 mr-2" />
                  Go Home
                </Link>
              </Button>
            </div>
            {process.env.NODE_ENV === 'development' &&
              this.state.error && (
                <details className="mt-4 text-left">
                  <summary className="cursor-pointer text-sm text-gray-500">
                    Error Details
                  </summary>
                  <pre className="mt-2 p-4 bg-gray-100 rounded text-xs overflow-auto">
                    {this.state.error.stack}
                  </pre>
                </details>
              )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Wrap in layout.tsx:
// <ErrorBoundary>
//   {children}
// </ErrorBoundary>
```

**Toast Notification System:**

```tsx
// apps/customer/src/components/ui/toast/ToastProvider.tsx
'use client';

import {
  createContext,
  useContext,
  useState,
  useCallback,
  ReactNode,
} from 'react';
import {
  X,
  CheckCircle,
  AlertCircle,
  Info,
  AlertTriangle,
} from 'lucide-react';
import { cn } from '@/lib/utils';

type ToastType = 'success' | 'error' | 'warning' | 'info';

interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
}

interface ToastContextType {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
  success: (title: string, message?: string) => void;
  error: (title: string, message?: string) => void;
  warning: (title: string, message?: string) => void;
  info: (title: string, message?: string) => void;
}

const ToastContext = createContext<ToastContextType | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  const addToast = useCallback(
    (toast: Omit<Toast, 'id'>) => {
      const id = Math.random().toString(36).substring(7);
      const newToast = { ...toast, id };
      setToasts(prev => [...prev, newToast]);

      // Auto-remove after duration
      setTimeout(() => removeToast(id), toast.duration ?? 5000);
    },
    [removeToast]
  );

  const success = (title: string, message?: string) =>
    addToast({ type: 'success', title, message });
  const error = (title: string, message?: string) =>
    addToast({ type: 'error', title, message, duration: 8000 });
  const warning = (title: string, message?: string) =>
    addToast({ type: 'warning', title, message });
  const info = (title: string, message?: string) =>
    addToast({ type: 'info', title, message });

  return (
    <ToastContext.Provider
      value={{
        toasts,
        addToast,
        removeToast,
        success,
        error,
        warning,
        info,
      }}
    >
      {children}
      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </ToastContext.Provider>
  );
}

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context)
    throw new Error('useToast must be used within ToastProvider');
  return context;
};

function ToastContainer({
  toasts,
  removeToast,
}: {
  toasts: Toast[];
  removeToast: (id: string) => void;
}) {
  const icons = {
    success: <CheckCircle className="h-5 w-5 text-green-500" />,
    error: <AlertCircle className="h-5 w-5 text-red-500" />,
    warning: <AlertTriangle className="h-5 w-5 text-yellow-500" />,
    info: <Info className="h-5 w-5 text-blue-500" />,
  };

  const colors = {
    success: 'border-green-200 bg-green-50',
    error: 'border-red-200 bg-red-50',
    warning: 'border-yellow-200 bg-yellow-50',
    info: 'border-blue-200 bg-blue-50',
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 space-y-2 max-w-sm">
      {toasts.map(toast => (
        <div
          key={toast.id}
          className={cn(
            'p-4 rounded-lg border shadow-lg flex items-start gap-3 animate-slide-up',
            colors[toast.type]
          )}
        >
          {icons[toast.type]}
          <div className="flex-1">
            <p className="font-medium text-gray-900">{toast.title}</p>
            {toast.message && (
              <p className="text-sm text-gray-600 mt-1">
                {toast.message}
              </p>
            )}
          </div>
          <button
            onClick={() => removeToast(toast.id)}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ))}
    </div>
  );
}

// Usage:
// const { success, error } = useToast();
// success('Booking confirmed!', 'Check your email for details.');
// error('Booking failed', 'Please try again or contact support.');
```

**Form Auto-Save Hook:**

```tsx
// apps/customer/src/hooks/useFormAutoSave.ts
'use client';

import { useEffect, useCallback, useRef } from 'react';
import { useToast } from '@/components/ui/toast/ToastProvider';

interface UseFormAutoSaveOptions<T> {
  key: string;
  data: T;
  enabled?: boolean;
  debounceMs?: number;
  onRestore?: (data: T) => void;
}

export function useFormAutoSave<T>({
  key,
  data,
  enabled = true,
  debounceMs = 2000,
  onRestore,
}: UseFormAutoSaveOptions<T>) {
  const { info } = useToast();
  const timeoutRef = useRef<NodeJS.Timeout>();
  const storageKey = `autosave:${key}`;

  // Save data with debounce
  useEffect(() => {
    if (!enabled) return;

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      try {
        const saveData = {
          data,
          timestamp: Date.now(),
        };
        localStorage.setItem(storageKey, JSON.stringify(saveData));
      } catch (e) {
        console.error('Auto-save failed:', e);
      }
    }, debounceMs);

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [data, enabled, debounceMs, storageKey]);

  // Check for saved data on mount
  const checkSavedData = useCallback(() => {
    try {
      const saved = localStorage.getItem(storageKey);
      if (!saved) return null;

      const { data: savedData, timestamp } = JSON.parse(saved);
      const age = Date.now() - timestamp;

      // Only restore if <24 hours old
      if (age < 24 * 60 * 60 * 1000) {
        return savedData as T;
      }

      // Clear old data
      localStorage.removeItem(storageKey);
      return null;
    } catch {
      return null;
    }
  }, [storageKey]);

  // Restore saved data
  const restoreSavedData = useCallback(() => {
    const saved = checkSavedData();
    if (saved && onRestore) {
      onRestore(saved);
      info(
        'Form restored',
        'Your previous progress has been restored.'
      );
    }
  }, [checkSavedData, onRestore, info]);

  // Clear saved data (call on successful submit)
  const clearSavedData = useCallback(() => {
    localStorage.removeItem(storageKey);
  }, [storageKey]);

  return {
    checkSavedData,
    restoreSavedData,
    clearSavedData,
    hasSavedData: !!checkSavedData(),
  };
}

// Usage in BookUs form:
// const { restoreSavedData, clearSavedData, hasSavedData } = useFormAutoSave({
//   key: 'bookus-form',
//   data: formData,
//   onRestore: (data) => setFormData(data),
// });
```

**Accessibility Checklist (WCAG 2.1 AA):**

| Requirement             | Check                              | Files to Update      |
| ----------------------- | ---------------------------------- | -------------------- |
| **Keyboard Navigation** | All interactive elements focusable | All forms, buttons   |
| **Focus Visible**       | Clear focus indicators             | globals.css          |
| **Skip Links**          | Skip to main content               | Layout.tsx           |
| **Alt Text**            | All images have alt                | All Image components |
| **ARIA Labels**         | Buttons/icons have labels          | Icon buttons         |
| **Color Contrast**      | 4.5:1 text ratio                   | Theme colors         |
| **Form Labels**         | All inputs labeled                 | Forms                |
| **Error Messages**      | Announced to screen readers        | Form validation      |
| **Heading Hierarchy**   | Logical h1-h6 structure            | All pages            |
| **Language Attribute**  | `lang="en"` on html                | RootLayout           |

### 🧪 QA & Testing (Batch 1)

> **Total: 25 hours** | Testing infrastructure foundations

#### Testing Tasks

| Task                        | Status   | Effort | Impact            | Notes                   |
| --------------------------- | -------- | ------ | ----------------- | ----------------------- |
| **Visual Regression Tests** | 🔧 Build | 4 hrs  | Catch UI breaks   | Percy/Chromatic setup   |
| **Mobile Device Testing**   | 🔧 Build | 4 hrs  | Mobile bugs       | BrowserStack/Playwright |
| **Cross-Browser Testing**   | 🔧 Build | 4 hrs  | Browser bugs      | Chrome, Firefox, Safari |
| **API Contract Tests**      | 🔧 Build | 4 hrs  | API compatibility | OpenAPI validation      |
| **Test Data Management**    | 🔧 Build | 3 hrs  | Reliable tests    | Fixtures + factories    |
| **E2E Test Coverage**       | 🔧 Build | 6 hrs  | Critical paths    | Booking, payment flows  |

**Visual Regression Testing Setup:**

```typescript
// e2e/visual/visual.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Visual Regression Tests', () => {
  const pages = [
    { name: 'homepage', path: '/' },
    { name: 'menu', path: '/menu' },
    { name: 'bookus', path: '/BookUs' },
    { name: 'contact', path: '/contact' },
    { name: 'quote', path: '/quote' },
  ];

  for (const page of pages) {
    test(`${page.name} - desktop`, async ({ page: browserPage }) => {
      await browserPage.setViewportSize({
        width: 1920,
        height: 1080,
      });
      await browserPage.goto(page.path);
      await browserPage.waitForLoadState('networkidle');

      // Wait for any animations to complete
      await browserPage.waitForTimeout(1000);

      await expect(browserPage).toHaveScreenshot(
        `${page.name}-desktop.png`,
        {
          fullPage: true,
          threshold: 0.1, // Allow 10% pixel difference
        }
      );
    });

    test(`${page.name} - mobile`, async ({ page: browserPage }) => {
      await browserPage.setViewportSize({ width: 375, height: 812 }); // iPhone X
      await browserPage.goto(page.path);
      await browserPage.waitForLoadState('networkidle');
      await browserPage.waitForTimeout(1000);

      await expect(browserPage).toHaveScreenshot(
        `${page.name}-mobile.png`,
        {
          fullPage: true,
          threshold: 0.1,
        }
      );
    });
  }
});

// playwright.config.ts additions:
// {
//   expect: {
//     toHaveScreenshot: {
//       maxDiffPixels: 100,
//       animations: 'disabled',
//     },
//   },
// }
```

**API Contract Testing:**

```typescript
// e2e/api/contract.spec.ts
import { test, expect } from '@playwright/test';
import Ajv from 'ajv';

const ajv = new Ajv();

// Define expected response schemas
const schemas = {
  booking: {
    type: 'object',
    required: [
      'id',
      'customer_id',
      'event_date',
      'status',
      'created_at',
    ],
    properties: {
      id: { type: 'string', format: 'uuid' },
      customer_id: { type: 'string', format: 'uuid' },
      event_date: { type: 'string', format: 'date-time' },
      status: {
        type: 'string',
        enum: ['pending', 'confirmed', 'cancelled', 'completed'],
      },
      guest_count: { type: 'integer', minimum: 1 },
      total_price: { type: 'number', minimum: 0 },
      created_at: { type: 'string', format: 'date-time' },
    },
  },
  bookingList: {
    type: 'object',
    required: ['items', 'total', 'page', 'limit'],
    properties: {
      items: {
        type: 'array',
        items: { $ref: '#/definitions/booking' },
      },
      total: { type: 'integer' },
      page: { type: 'integer' },
      limit: { type: 'integer' },
    },
  },
};

test.describe('API Contract Tests', () => {
  test('GET /api/v1/bookings matches schema', async ({ request }) => {
    const response = await request.get(
      '/api/v1/bookings?page=1&limit=10',
      {
        headers: {
          Authorization: `Bearer ${process.env.TEST_JWT_TOKEN}`,
        },
      }
    );

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    const validate = ajv.compile(schemas.bookingList);
    const valid = validate(data);

    if (!valid) {
      console.error('Schema validation errors:', validate.errors);
    }
    expect(valid).toBeTruthy();
  });

  test('POST /api/v1/bookings returns valid booking', async ({
    request,
  }) => {
    const response = await request.post('/api/v1/bookings', {
      headers: {
        Authorization: `Bearer ${process.env.TEST_JWT_TOKEN}`,
      },
      data: {
        customer_id: 'test-customer-id',
        event_date: '2025-01-15T18:00:00Z',
        guest_count: 10,
        // ... other required fields
      },
    });

    expect(response.status()).toBe(201);
    const booking = await response.json();

    const validate = ajv.compile(schemas.booking);
    expect(validate(booking)).toBeTruthy();
  });
});
```

**Test Data Factory:**

```typescript
// e2e/fixtures/factories.ts
import { faker } from '@faker-js/faker';

export const factories = {
  customer: (overrides = {}) => ({
    id: faker.string.uuid(),
    first_name: faker.person.firstName(),
    last_name: faker.person.lastName(),
    email: faker.internet.email(),
    phone: faker.phone.number('+1##########'),
    created_at: faker.date.past().toISOString(),
    ...overrides,
  }),

  booking: (overrides = {}) => ({
    id: faker.string.uuid(),
    customer_id: faker.string.uuid(),
    event_date: faker.date.future().toISOString(),
    event_time: '18:00',
    guest_count: faker.number.int({ min: 10, max: 50 }),
    venue_address: faker.location.streetAddress(),
    venue_city: faker.location.city(),
    venue_state: faker.location.state({ abbreviated: true }),
    venue_zip: faker.location.zipCode(),
    status: 'pending',
    total_price: faker.number.float({
      min: 500,
      max: 2000,
      fractionDigits: 2,
    }),
    created_at: faker.date.past().toISOString(),
    ...overrides,
  }),

  chef: (overrides = {}) => ({
    id: faker.string.uuid(),
    name: faker.person.fullName(),
    email: faker.internet.email(),
    phone: faker.phone.number('+1##########'),
    bio: faker.lorem.paragraph(),
    profile_image: faker.image.avatar(),
    is_active: true,
    ...overrides,
  }),
};

// Usage in tests:
// const testCustomer = factories.customer({ email: 'test@example.com' });
// const testBooking = factories.booking({ customer_id: testCustomer.id });
```

**Mobile Testing Configuration:**

```typescript
// playwright.config.ts - Mobile devices
import { devices } from '@playwright/test';

export default {
  projects: [
    // Desktop
    { name: 'Desktop Chrome', use: { ...devices['Desktop Chrome'] } },
    {
      name: 'Desktop Firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    { name: 'Desktop Safari', use: { ...devices['Desktop Safari'] } },

    // Mobile
    { name: 'Mobile Chrome', use: { ...devices['Pixel 5'] } },
    { name: 'Mobile Safari', use: { ...devices['iPhone 12'] } },
    { name: 'Mobile Safari Mini', use: { ...devices['iPhone SE'] } },

    // Tablet
    { name: 'iPad', use: { ...devices['iPad Pro 11'] } },
    { name: 'Android Tablet', use: { ...devices['Galaxy Tab S4'] } },
  ],
};
```

### Success Criteria

**Core API & Security:**

- [ ] All 150 routes responding correctly
- [ ] Create booking flow works end-to-end
- [ ] Edit booking flow works
- [ ] Chef assignment works
- [ ] Authentication/authorization working
- [ ] RBAC permissions enforced correctly
- [ ] Audit trail recording all changes
- [ ] Failed booking captures lead info
- [ ] Health checks passing
- [ ] Cloudflare Tunnel active (VPS IP hidden)
- [ ] WAF blocking test attacks
- [ ] No critical errors for 48 hours
- [ ] Load test passed (100 concurrent users)

**Contact Info Protection (Anti-Scraper):**

- [ ] `ProtectedPhone.tsx` component created in
      `apps/customer/src/components/ui/`
- [ ] `useProtectedPhone` hook exported for custom usage
- [ ] All hardcoded phone numbers replaced with `<ProtectedPhone />`
- [ ] All email links replaced with `/contact` page links
- [ ] Yelp AND Google removed from Footer social icons
- [ ] Google/Yelp links only visible on: /contact, /BookUs, /review
      pages
- [ ] Blog posts link to /contact instead of hardcoded email
- [ ] Phone number invisible to server-side scrapers (verified with
      curl)

**Scaling Foundation (Batch 1):**

- [ ] Read replica config pattern added to `database.py` (uses master
      if no replica)
- [ ] Cache key namespacing implemented (`cache_key()` helper)
- [ ] `DATABASE_URL_READ` env var documented
- [ ] `CACHE_PREFIX` env var documented
- [ ] Table partitioning SQL scripts ready (not applied yet - apply
      when needed)

**Scaling Measurement System (Batch 1):**

- [ ] `/api/v1/admin/scaling/metrics` endpoint responding with all
      metrics
- [ ] Database pool usage metrics collecting correctly
- [ ] Redis memory/hit-rate metrics collecting correctly
- [ ] WhatsApp alert service sending test message successfully
- [ ] 5-minute cron job running (`scaling_monitor.py`)
- [ ] Daily summary sending at 9 AM
- [ ] Admin UI dashboard showing current metrics
- [ ] Warning thresholds triggering WhatsApp alerts
- [ ] Snooze functionality working (7-day default)

**⚡ Performance Optimization (Batch 1):**

- [ ] LCP < 2.5s on Homepage (measured via Lighthouse CI)
- [ ] LCP < 2.5s on BookUs page (measured via Lighthouse CI)
- [ ] Homepage bundle < 150KB gzipped (verified in build output)
- [ ] BookUs bundle < 180KB gzipped (verified in build output)
- [ ] Lazy DatePicker implemented (~250KB removed from initial load)
- [ ] API caching headers configured (static: 1yr, images: 7d, API:
      no-cache)
- [ ] Client-side cache service working (quote caching verified)
- [ ] Prefetching implemented on homepage (BookUs page preloaded on
      hover)
- [ ] Backend query caching decorator working (`@cached_query` tested)
- [ ] N+1 queries eliminated (eager loading verified via query logs)
- [ ] GZIP compression enabled (response headers verified)
- [ ] Slow query logging active (>100ms queries logged)
- [ ] Health endpoint < 50ms (verified in monitoring)
- [ ] Quote calculation < 300ms (verified in monitoring)
- [ ] Lighthouse Performance score > 70 (CI check passing)

**🎨 UI/UX Polish (Batch 1):**

- [ ] Skeleton loader component created
      (`apps/customer/src/components/ui/skeleton.tsx`)
- [ ] Skeleton variants working: `card`, `text`, `avatar`, `button`,
      `form`
- [ ] ErrorBoundary component created
      (`apps/customer/src/components/error-boundary.tsx`)
- [ ] ErrorBoundary wraps critical sections (booking form, payment)
- [ ] Error recovery "Try Again" button working
- [ ] Toast provider created
      (`apps/customer/src/components/ui/toast-provider.tsx`)
- [ ] Toast notifications working: success, error, warning, info
- [ ] Toast auto-dismiss after 5s (configurable per toast)
- [ ] Form auto-save hook created
      (`apps/customer/src/hooks/useFormAutoSave.ts`)
- [ ] Booking form data persists on page reload (verified)
- [ ] 24-hour recovery window working (old data auto-clears)
- [ ] WCAG 2.1 AA audit completed (critical issues fixed)
- [ ] Skip link added to main content
- [ ] Keyboard navigation working on booking form
- [ ] Focus trap working in modals
- [ ] Form validation messages announced by screen readers
- [ ] Color contrast ratios passing (4.5:1 minimum)

**🧪 QA & Testing (Batch 1):**

- [ ] Visual regression tests created (`tests/visual/`)
- [ ] Desktop baseline screenshots captured (5 critical pages)
- [ ] Mobile baseline screenshots captured (5 critical pages)
- [ ] Visual diff threshold configured (0.1%)
- [ ] API contract tests created (`tests/contracts/`)
- [ ] Health endpoint contract validated
- [ ] Quote endpoint contract validated
- [ ] Booking create endpoint contract validated
- [ ] Cross-browser testing matrix configured (Chrome, Firefox,
      Safari)
- [ ] Mobile browser testing configured (Chrome Android, Safari iOS)
- [ ] Tablet testing configured (iPad Pro, Galaxy Tab)
- [ ] Test data factory created (`tests/factories/factories.ts`)
- [ ] Customer factory working
- [ ] Booking factory working
- [ ] Chef factory working
- [ ] Test isolation verified (no data pollution between tests)

### Rollback Plan

```bash
# If critical issues detected:
git checkout main~1  # Revert to previous tag
docker-compose down && docker-compose up -d
# Alert team via Slack
```

---

## 🔴 BATCH 2: Payment Processing (Week 3-4)

**Priority:** CRITICAL **Branch:** `feature/batch-2-payments`
**Duration:** 2 weeks **Prerequisite:** Batch 1 stable for 48+ hours

### Components

| Component          | Status         | Notes                          |
| ------------------ | -------------- | ------------------------------ |
| Stripe Integration | ✅ Model Ready | `StripeCustomer` model created |
| Payment Intents    | ✅ Ready       | Create payment sessions        |
| Deposit Collection | ✅ Ready       | Booking deposits               |
| Invoice Generation | ✅ Ready       | PDF invoices                   |
| Refund Processing  | ✅ Ready       | Cancel/refund flow             |
| Webhook Handling   | ✅ Ready       | Stripe events                  |
| **Total Routes**   |                | **~40**                        |

### Dynamic Pricing Management (From `DYNAMIC_PRICING_MANAGEMENT_SYSTEM.md`)

| Feature                      | Status       | Effort  | Notes                        |
| ---------------------------- | ------------ | ------- | ---------------------------- |
| `price_change_history` table | 🔧 Build     | 1 hour  | Track all price changes      |
| Admin Pricing API            | 🔧 Build     | 4 hours | `/api/v1/admin/pricing`      |
| Pricing Admin UI             | 🔧 Build     | 6 hours | Update prices in admin panel |
| Price Change Notifications   | 🔧 Build     | 2 hours | Alert when prices change     |
| Database as Source of Truth  | 🔧 Configure | 1 hour  | Remove hardcoded prices      |
| Price Validation Rules       | 🔧 Build     | 2 hours | Min/max, no negative         |

### Tipping/Gratuity System (✅ EXISTS - Update Needed)

| Feature             | Status    | Effort | Notes                                                  |
| ------------------- | --------- | ------ | ------------------------------------------------------ |
| Tip Percentages     | 🔧 Update | 1 hour | Change from 15/18/20/25% to **20%, 25%, 30% + Custom** |
| Tip UI Component    | ✅ Exists | -      | `apps/customer/src/components/payment/`                |
| Tip Applied to Base | ✅ Exists | -      | Tips calculated on subtotal before fees                |

### 3% Credit Card Processing Fee

| Feature        | Status    | Effort       | Notes                                                |
| -------------- | --------- | ------------ | ---------------------------------------------------- |
| Processing Fee | ✅ Exists | 2 hrs verify | 3% fee on `subtotal + tax + tip` for Stripe payments |
| Fee Display    | 🔧 Verify | 1 hour       | Ensure fee shown clearly at checkout                 |
| Zelle/Venmo    | ✅ Exists | -            | No processing fee (manual payments)                  |

### Internal Tax Collection System (Accounting & Reporting)

> **IMPORTANT:** Customer prices are **TAX-INCLUSIVE**. Customers see
> final prices only (no tax line items). This system is for **internal
> accounting and tax reporting** to comply with state/county
> requirements.

| Feature                  | Status   | Effort  | Notes                                   |
| ------------------------ | -------- | ------- | --------------------------------------- |
| Tax Rates Table          | 🔧 Build | 3 hours | State → County → Rate mapping           |
| ZIP → County Auto-Detect | 🔧 Build | 2 hours | Silently detect county from venue ZIP   |
| Admin Tax Management UI  | 🔧 Build | 4 hours | SUPER_ADMIN/ADMIN can manage tax rates  |
| Tax Calculation Service  | 🔧 Build | 2 hours | Back-calculate tax from inclusive price |
| Tax Reporting Dashboard  | 🔧 Build | 4 hours | Monthly/quarterly reports by county     |
| Multi-State Support      | 🔧 Build | 2 hours | Scalable schema for expansion           |

**Database Schema (Internal Tax Tracking):**

```sql
CREATE TABLE core.tax_rates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    state_code VARCHAR(2) NOT NULL,           -- 'CA', 'TX', 'FL'
    county_name VARCHAR(100) NOT NULL,        -- 'Alameda', 'Santa Clara'
    city_name VARCHAR(100),                   -- Optional city-level
    zip_codes TEXT[],                         -- Array of ZIP codes
    tax_rate DECIMAL(5,4) NOT NULL,           -- 0.0925 = 9.25%
    effective_date DATE NOT NULL,
    expiry_date DATE,                         -- NULL = currently active
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES core.users(id),
    updated_by UUID REFERENCES core.users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(state_code, county_name, effective_date)
);

-- California County Tax Rates (Examples):
-- Alameda County: 10.25%
-- Santa Clara County: 9.125%
-- San Francisco County: 8.625%
-- Contra Costa County: 9.25%
-- San Mateo County: 9.375%
-- Sacramento County: 8.75%

-- Store tax info on each booking for reporting
ALTER TABLE booking.bookings ADD COLUMN IF NOT EXISTS
    tax_jurisdiction JSONB;  -- {"state": "CA", "county": "Santa Clara", "rate": 0.09125}
ALTER TABLE booking.bookings ADD COLUMN IF NOT EXISTS
    tax_amount_calculated DECIMAL(10,2);  -- Back-calculated from inclusive price
```

**Internal Tax Calculation (Back-Calculate from Inclusive Price):**

```python
# Customer pays $851.18 (tax-inclusive price)
# System knows venue is in Santa Clara County (9.125% tax rate)

total_paid = 851.18
tax_rate = 0.09125

# Back-calculate tax portion
pre_tax_amount = total_paid / (1 + tax_rate)  # = $780.00
tax_amount = total_paid - pre_tax_amount      # = $71.18

# Store for accounting
booking.tax_jurisdiction = {
    "state": "CA",
    "county": "Santa Clara",
    "rate": 0.09125
}
booking.tax_amount_calculated = 71.18
```

**Admin Panel Tax Management (SUPER_ADMIN/ADMIN Only):**

```
┌─────────────────────────────────────────────────────────────────────┐
│ 🔧 ADMIN PANEL > TAX MANAGEMENT                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Active Tax Rates                                   [+ Add New Rate] │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                      │
│  State  │ County         │ Rate   │ Effective   │ Actions          │
│  ───────┼────────────────┼────────┼─────────────┼──────────────    │
│  CA     │ Alameda        │ 10.25% │ 2024-01-01  │ [Edit] [Archive] │
│  CA     │ Santa Clara    │ 9.125% │ 2024-01-01  │ [Edit] [Archive] │
│  CA     │ San Francisco  │ 8.625% │ 2024-01-01  │ [Edit] [Archive] │
│  CA     │ Contra Costa   │ 9.25%  │ 2024-01-01  │ [Edit] [Archive] │
│  CA     │ San Mateo      │ 9.375% │ 2024-01-01  │ [Edit] [Archive] │
│                                                                      │
│  [📥 Import Rates CSV]  [📤 Export Rates]  [📊 View Rate History]  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ ➕ ADD/EDIT TAX RATE                                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  State Code:  [CA ▼]                                                │
│  County Name: [________________]                                     │
│  City (opt):  [________________]                                     │
│  Tax Rate %:  [____]                                                 │
│  ZIP Codes:   [95112, 95113, 95116, ...] (comma separated)          │
│  Effective:   [2025-01-01]                                          │
│  Expires:     [________] (leave blank for no expiry)                │
│                                                                      │
│                              [Cancel]  [Save Rate]                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Internal Tax Reporting Dashboard (SUPER_ADMIN Only):**

```
┌─────────────────────────────────────────────────────────────────────┐
│ 📊 TAX REPORTING DASHBOARD                          [Export to CSV] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Period: [Q4 2025 ▼]    State: [California ▼]    [Generate Report] │
│                                                                      │
│  ═══════════════════════════════════════════════════════════════   │
│                                                                      │
│  SUMMARY BY COUNTY (Q4 2025)                                        │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                      │
│  County          │ # Orders │ Total Revenue │ Tax Collected │ Rate  │
│  ────────────────┼──────────┼───────────────┼───────────────┼─────  │
│  Santa Clara     │    47    │   $38,240.00  │   $3,188.92   │ 9.125%│
│  Alameda         │    32    │   $26,112.00  │   $2,436.75   │ 10.25%│
│  San Francisco   │    28    │   $22,876.00  │   $1,815.86   │ 8.625%│
│  Contra Costa    │    19    │   $15,523.00  │   $1,325.52   │ 9.25% │
│  San Mateo       │    15    │   $12,255.00  │   $1,070.61   │ 9.375%│
│  ────────────────┼──────────┼───────────────┼───────────────┼─────  │
│  TOTAL           │   141    │  $115,006.00  │   $9,837.66   │       │
│                                                                      │
│  [📄 Download for CPA]  [📧 Email Report]  [🖨️ Print Summary]      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**How It Works (End-to-End):**

```
┌─────────────────────────────────────────────────────────────────────┐
│ CUSTOMER EXPERIENCE (NO TAX LINE ITEMS)                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Quote Calculator → Customer sees: "Total: $851.18"                 │
│  Order Confirmation → Customer sees: "Total: $851.18"               │
│  Balance Payment → Customer sees: "Balance Due: $751.18"            │
│  Receipt → Customer sees: "Total Paid: $851.18"                     │
│                                                                      │
│  ✅ Clean, simple pricing. Tax included. No surprises.              │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│ INTERNAL SYSTEM (BEHIND THE SCENES)                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. Customer enters venue: "123 Main St, San Jose, CA 95112"        │
│                                                                      │
│  2. System auto-detects:                                            │
│     └── ZIP 95112 → Santa Clara County → 9.125% tax rate            │
│                                                                      │
│  3. On booking creation, system stores:                             │
│     └── tax_jurisdiction = {"state":"CA","county":"Santa Clara"}    │
│     └── tax_amount_calculated = $71.18                              │
│                                                                      │
│  4. Admin reports show:                                             │
│     └── "Santa Clara County: 47 orders, $3,188.92 tax collected"    │
│                                                                      │
│  5. End of quarter: Export report for CPA/tax filing                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Multi-State Expansion:**

```
Current: California counties only
Future:  Add TX, FL, NV rows to tax_rates table when expanding
```

### Promo Code System

| Feature              | Status   | Effort  | Notes                               |
| -------------------- | -------- | ------- | ----------------------------------- |
| Promo Code Table     | 🔧 Build | 3 hours | Code, discount type, amount, expiry |
| Promo Validation API | 🔧 Build | 2 hours | `/api/v1/payments/validate-promo`   |
| Promo UI Component   | 🔧 Build | 2 hours | Input field at checkout             |
| First-Time Customer  | 🔧 Build | 1 hour  | Auto-detect new customers           |

### Enable Stripe Router

```python
# main.py - Uncomment lines 838-871
router.include_router(stripe_router, prefix="/api/v1/stripe", tags=["stripe"])
```

### Feature Flags

```env
FEATURE_STRIPE=true
FEATURE_PAYMENTS=true
FEATURE_DYNAMIC_PRICING=true
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
```

### Frontend Tasks (Batch 2)

| App               | Component            | Status   | Notes                  |
| ----------------- | -------------------- | -------- | ---------------------- |
| **Customer Site** | Stripe checkout      | 🔧 Build | Payment flow UI        |
| **Customer Site** | Payment confirmation | 🔧 Build | Success/failure pages  |
| **Customer Site** | Invoice download     | 🔧 Build | PDF invoice viewer     |
| **Admin Panel**   | Payments dashboard   | 🔧 Build | View all payments      |
| **Admin Panel**   | Refund management    | 🔧 Build | Process refunds        |
| **Admin Panel**   | Dynamic pricing UI   | 🔧 Build | Edit prices (from doc) |
| **Admin Panel**   | Price history viewer | 🔧 Build | Audit price changes    |

---

### ⚡ Performance Optimization (Batch 2)

**Total Estimate:** 14 hours

#### Load Testing Infrastructure (6 hrs)

| Task                       | Effort | Notes                           |
| -------------------------- | ------ | ------------------------------- |
| k6 Load Testing Setup      | 2 hrs  | Install and configure k6        |
| Payment Flow Load Scripts  | 2 hrs  | Test Stripe checkout under load |
| Load Test CI Integration   | 1 hr   | Run on staging before prod      |
| Load Test Results Reporter | 1 hr   | HTML/JSON reports               |

**k6 Load Test Configuration:**

```javascript
// tests/load/k6.config.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const failureRate = new Rate('failed_requests');

export const options = {
  stages: [
    { duration: '30s', target: 20 }, // Ramp up to 20 users
    { duration: '1m', target: 50 }, // Stay at 50 users
    { duration: '2m', target: 100 }, // Ramp up to 100 users
    { duration: '1m', target: 100 }, // Stay at 100 users
    { duration: '30s', target: 0 }, // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% requests < 500ms
    http_req_failed: ['rate<0.01'], // <1% failure rate
    failed_requests: ['rate<0.01'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  // Health check
  const healthRes = http.get(`${BASE_URL}/api/v1/health`);
  check(healthRes, {
    'health status is 200': r => r.status === 200,
    'health response time < 100ms': r => r.timings.duration < 100,
  });

  // Quote calculation (common flow)
  const quoteRes = http.post(
    `${BASE_URL}/api/v1/bookings/quote`,
    JSON.stringify({
      guest_count: 10,
      venue_zip: '95112',
      event_type: 'birthday',
      addons: ['sake_bar'],
    }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  check(quoteRes, {
    'quote status is 200': r => r.status === 200,
    'quote response time < 300ms': r => r.timings.duration < 300,
  });

  failureRate.add(quoteRes.status !== 200);

  sleep(1); // Think time between requests
}

// Payment flow load test
export function paymentFlow() {
  // Create payment intent
  const intentRes = http.post(
    `${BASE_URL}/api/v1/stripe/create-payment-intent`,
    JSON.stringify({
      booking_id: 'test-booking-123',
      amount: 10000, // $100.00
    }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  check(intentRes, {
    'payment intent created': r => r.status === 200,
    'payment intent < 500ms': r => r.timings.duration < 500,
  });
}
```

**Load Test Script Runner:**

```bash
#!/bin/bash
# tests/load/run-load-tests.sh

set -e

echo "🏋️ Running Load Tests..."

# Install k6 if not present
if ! command -v k6 &> /dev/null; then
    echo "Installing k6..."
    # For Ubuntu/Debian
    sudo gpg -k
    sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
    echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
    sudo apt-get update
    sudo apt-get install k6
fi

# Run load tests
BASE_URL=${BASE_URL:-"https://staging.myhibachi.io"}

k6 run \
  --out json=tests/load/results/$(date +%Y%m%d_%H%M%S).json \
  --summary-trend-stats="avg,min,med,max,p(90),p(95),p(99)" \
  -e BASE_URL=$BASE_URL \
  tests/load/k6.config.js

echo "✅ Load tests complete. Results saved to tests/load/results/"
```

#### Performance Regression Tests (4 hrs)

| Task                     | Effort | Notes                       |
| ------------------------ | ------ | --------------------------- |
| Performance Baseline CI  | 2 hrs  | Lighthouse CI in pipeline   |
| Regression Alert System  | 1 hr   | Alert on 10%+ degradation   |
| Performance Budget Check | 1 hr   | Fail build on budget exceed |

**Lighthouse CI Configuration:**

```javascript
// lighthouserc.js
module.exports = {
  ci: {
    collect: {
      url: [
        'http://localhost:3000/',
        'http://localhost:3000/BookUs',
        'http://localhost:3000/contact',
      ],
      numberOfRuns: 3,
      settings: {
        preset: 'desktop',
        throttling: {
          rttMs: 40,
          throughputKbps: 10240,
          cpuSlowdownMultiplier: 1,
        },
      },
    },
    assert: {
      assertions: {
        'categories:performance': ['error', { minScore: 0.7 }],
        'categories:accessibility': ['error', { minScore: 0.9 }],
        'first-contentful-paint': [
          'error',
          { maxNumericValue: 1800 },
        ],
        'largest-contentful-paint': [
          'error',
          { maxNumericValue: 2500 },
        ],
        'cumulative-layout-shift': [
          'error',
          { maxNumericValue: 0.1 },
        ],
        'total-blocking-time': ['error', { maxNumericValue: 200 }],
      },
    },
    upload: {
      target: 'temporary-public-storage',
    },
  },
};
```

**GitHub Actions Performance Job:**

```yaml
# .github/workflows/performance.yml
name: Performance Regression

on:
  pull_request:
    branches: [main, dev]

jobs:
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci
        working-directory: apps/customer

      - name: Build
        run: npm run build
        working-directory: apps/customer

      - name: Start server
        run: npm run start &
        working-directory: apps/customer

      - name: Wait for server
        run: npx wait-on http://localhost:3000

      - name: Run Lighthouse CI
        run: |
          npm install -g @lhci/cli
          lhci autorun
        env:
          LHCI_GITHUB_APP_TOKEN: ${{ secrets.LHCI_GITHUB_APP_TOKEN }}

      - name: Upload results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: lighthouse-results
          path: .lighthouseci/
```

#### Database Query Performance (4 hrs)

| Task                        | Effort | Notes                       |
| --------------------------- | ------ | --------------------------- |
| Query Performance Monitor   | 2 hrs  | Track p95 query times       |
| Index Optimization Review   | 1 hr   | Analyze slow query patterns |
| Query Performance Dashboard | 1 hr   | Grafana/admin panel view    |

**Query Performance Monitor:**

```python
# apps/backend/src/core/query_performance.py
import time
import logging
from typing import Dict, Any
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import statistics

logger = logging.getLogger(__name__)

@dataclass
class QueryStats:
    """Statistics for a single query pattern."""
    execution_times: list = field(default_factory=list)
    last_executed: datetime = None

    @property
    def count(self) -> int:
        return len(self.execution_times)

    @property
    def avg_time(self) -> float:
        return statistics.mean(self.execution_times) if self.execution_times else 0

    @property
    def p95_time(self) -> float:
        if not self.execution_times:
            return 0
        sorted_times = sorted(self.execution_times)
        idx = int(len(sorted_times) * 0.95)
        return sorted_times[min(idx, len(sorted_times) - 1)]

    @property
    def max_time(self) -> float:
        return max(self.execution_times) if self.execution_times else 0


class QueryPerformanceMonitor:
    """Monitor and report on database query performance."""

    def __init__(self, window_minutes: int = 60):
        self._stats: Dict[str, QueryStats] = defaultdict(QueryStats)
        self._window = timedelta(minutes=window_minutes)
        self._slow_threshold_ms = 100  # Log queries > 100ms

    def record_query(self, query_pattern: str, execution_time_ms: float):
        """Record a query execution."""
        stats = self._stats[query_pattern]
        stats.execution_times.append(execution_time_ms)
        stats.last_executed = datetime.utcnow()

        # Keep only recent data (last hour)
        self._cleanup_old_data()

        # Log slow queries
        if execution_time_ms > self._slow_threshold_ms:
            logger.warning(
                f"Slow query ({execution_time_ms:.1f}ms): {query_pattern[:100]}..."
            )

    def get_report(self) -> Dict[str, Any]:
        """Generate performance report."""
        self._cleanup_old_data()

        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "window_minutes": self._window.total_seconds() / 60,
            "total_queries": sum(s.count for s in self._stats.values()),
            "slow_queries": [],
            "top_queries": [],
        }

        # Find slow queries (p95 > threshold)
        slow = [
            {
                "pattern": pattern[:100],
                "count": stats.count,
                "avg_ms": round(stats.avg_time, 2),
                "p95_ms": round(stats.p95_time, 2),
                "max_ms": round(stats.max_time, 2),
            }
            for pattern, stats in self._stats.items()
            if stats.p95_time > self._slow_threshold_ms
        ]
        report["slow_queries"] = sorted(slow, key=lambda x: x["p95_ms"], reverse=True)[:10]

        # Top queries by count
        top = [
            {
                "pattern": pattern[:100],
                "count": stats.count,
                "avg_ms": round(stats.avg_time, 2),
            }
            for pattern, stats in self._stats.items()
        ]
        report["top_queries"] = sorted(top, key=lambda x: x["count"], reverse=True)[:10]

        return report

    def _cleanup_old_data(self):
        """Remove data older than window."""
        cutoff = datetime.utcnow() - self._window
        for stats in self._stats.values():
            # Simple approach: keep only recent entries
            if stats.last_executed and stats.last_executed < cutoff:
                stats.execution_times = stats.execution_times[-100:]  # Keep last 100


# Global instance
query_monitor = QueryPerformanceMonitor()
```

---

### 🎨 UI/UX Polish (Batch 2)

**Total Estimate:** 12 hours

#### Payment UI Enhancements (8 hrs)

| Task                       | Effort | Notes                           |
| -------------------------- | ------ | ------------------------------- |
| Optimistic Payment Updates | 3 hrs  | Instant UI feedback             |
| Payment Loading States     | 2 hrs  | Progress indicators             |
| Payment Error UX           | 2 hrs  | Clear error messages + recovery |
| Receipt Animation          | 1 hr   | Success celebration             |

**Optimistic Payment Update Pattern:**

```typescript
// apps/customer/src/hooks/useOptimisticPayment.ts
import { useState, useCallback } from 'react';
import { toast } from '@/components/ui/toast-provider';

interface PaymentState {
  status: 'idle' | 'processing' | 'confirming' | 'success' | 'error';
  message: string;
  progress: number;
}

export function useOptimisticPayment() {
  const [state, setState] = useState<PaymentState>({
    status: 'idle',
    message: '',
    progress: 0,
  });

  const processPayment = useCallback(
    async (
      paymentIntentId: string,
      confirmFn: () => Promise<void>
    ) => {
      try {
        // Optimistically show processing
        setState({
          status: 'processing',
          message: 'Processing payment...',
          progress: 25,
        });

        // Simulate brief delay for UX
        await new Promise(r => setTimeout(r, 300));
        setState({
          status: 'processing',
          message: 'Verifying card...',
          progress: 50,
        });

        // Actually confirm payment
        await confirmFn();

        setState({
          status: 'confirming',
          message: 'Confirming with bank...',
          progress: 75,
        });

        // Brief delay then success
        await new Promise(r => setTimeout(r, 500));
        setState({
          status: 'success',
          message: 'Payment successful!',
          progress: 100,
        });

        toast.success('Payment processed successfully!', {
          description:
            'You will receive a confirmation email shortly.',
        });

        return { success: true };
      } catch (error: any) {
        setState({
          status: 'error',
          message:
            error.message || 'Payment failed. Please try again.',
          progress: 0,
        });

        toast.error('Payment failed', {
          description:
            error.message ||
            'Please check your card details and try again.',
          action: {
            label: 'Try Again',
            onClick: () =>
              setState({ status: 'idle', message: '', progress: 0 }),
          },
        });

        return { success: false, error };
      }
    },
    []
  );

  const reset = useCallback(() => {
    setState({ status: 'idle', message: '', progress: 0 });
  }, []);

  return { state, processPayment, reset };
}
```

**Payment Progress Component:**

```tsx
// apps/customer/src/components/payment/PaymentProgress.tsx
'use client';

import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckCircle,
  XCircle,
  Loader2,
  CreditCard,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface PaymentProgressProps {
  status: 'idle' | 'processing' | 'confirming' | 'success' | 'error';
  message: string;
  progress: number;
}

const statusConfig = {
  idle: {
    icon: CreditCard,
    color: 'text-gray-400',
    bg: 'bg-gray-100',
  },
  processing: {
    icon: Loader2,
    color: 'text-blue-500',
    bg: 'bg-blue-50',
  },
  confirming: {
    icon: Loader2,
    color: 'text-amber-500',
    bg: 'bg-amber-50',
  },
  success: {
    icon: CheckCircle,
    color: 'text-green-500',
    bg: 'bg-green-50',
  },
  error: { icon: XCircle, color: 'text-red-500', bg: 'bg-red-50' },
};

export function PaymentProgress({
  status,
  message,
  progress,
}: PaymentProgressProps) {
  const config = statusConfig[status];
  const Icon = config.icon;
  const isAnimating =
    status === 'processing' || status === 'confirming';

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={status}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        className={cn(
          'rounded-lg p-4 flex items-center gap-3',
          config.bg
        )}
      >
        <Icon
          className={cn(
            'w-6 h-6',
            config.color,
            isAnimating && 'animate-spin'
          )}
        />
        <div className="flex-1">
          <p className={cn('font-medium', config.color)}>{message}</p>
          {progress > 0 && progress < 100 && (
            <div className="mt-2 h-1 bg-gray-200 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-blue-500"
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
```

**Success Celebration Animation:**

```tsx
// apps/customer/src/components/payment/PaymentSuccess.tsx
'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import confetti from 'canvas-confetti';
import { CheckCircle, Download, Mail } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface PaymentSuccessProps {
  bookingId: string;
  amount: number;
  onDownloadReceipt: () => void;
}

export function PaymentSuccess({
  bookingId,
  amount,
  onDownloadReceipt,
}: PaymentSuccessProps) {
  const [confettiTriggered, setConfettiTriggered] = useState(false);

  useEffect(() => {
    if (!confettiTriggered) {
      // Trigger confetti celebration
      confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 },
        colors: ['#10B981', '#3B82F6', '#F59E0B', '#EF4444'],
      });
      setConfettiTriggered(true);
    }
  }, [confettiTriggered]);

  return (
    <motion.div
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className="text-center py-8"
    >
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: 'spring', stiffness: 200, damping: 15 }}
        className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-green-100 mb-6"
      >
        <CheckCircle className="w-10 h-10 text-green-500" />
      </motion.div>

      <motion.h2
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="text-2xl font-bold text-gray-900 mb-2"
      >
        Payment Successful!
      </motion.h2>

      <motion.p
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="text-gray-600 mb-6"
      >
        Your deposit of{' '}
        <span className="font-semibold">
          ${(amount / 100).toFixed(2)}
        </span>{' '}
        has been received.
      </motion.p>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="space-y-3"
      >
        <p className="text-sm text-gray-500">
          Booking Reference:{' '}
          <code className="font-mono bg-gray-100 px-2 py-1 rounded">
            {bookingId}
          </code>
        </p>

        <div className="flex justify-center gap-3">
          <Button
            onClick={onDownloadReceipt}
            variant="outline"
            size="sm"
          >
            <Download className="w-4 h-4 mr-2" />
            Download Receipt
          </Button>
          <Button variant="outline" size="sm">
            <Mail className="w-4 h-4 mr-2" />
            Email Receipt
          </Button>
        </div>
      </motion.div>
    </motion.div>
  );
}
```

#### Invoice/Receipt Polish (4 hrs)

| Task                     | Effort | Notes                       |
| ------------------------ | ------ | --------------------------- |
| PDF Invoice Template     | 2 hrs  | Professional branded design |
| Receipt Email Template   | 1 hr   | Responsive email template   |
| Invoice Download Loading | 1 hr   | Progress indicator          |

---

### 🧪 QA & Testing (Batch 2)

**Total Estimate:** 14 hours

#### Load/Stress Testing (8 hrs)

| Task                      | Effort | Notes                      |
| ------------------------- | ------ | -------------------------- |
| Payment Load Test Scripts | 3 hrs  | Stripe flow under load     |
| Concurrent Booking Tests  | 2 hrs  | Race condition detection   |
| Database Stress Test      | 2 hrs  | Connection pool limits     |
| Stress Test Report System | 1 hr   | Generate load test reports |

**Concurrent Booking Race Test:**

```typescript
// tests/load/concurrent-booking.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Concurrent Booking Prevention', () => {
  test('should prevent double-booking same time slot', async ({
    browser,
  }) => {
    // Create two parallel browser contexts
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();

    const page1 = await context1.newPage();
    const page2 = await context2.newPage();

    // Both users navigate to booking
    await Promise.all([page1.goto('/BookUs'), page2.goto('/BookUs')]);

    // Both fill same date/time
    const targetDate = '2025-03-15';
    const targetTime = '6:00 PM';

    await Promise.all([
      page1.fill('[data-testid="event-date"]', targetDate),
      page2.fill('[data-testid="event-date"]', targetDate),
    ]);

    await Promise.all([
      page1.selectOption('[data-testid="event-time"]', targetTime),
      page2.selectOption('[data-testid="event-time"]', targetTime),
    ]);

    // Fill required fields
    const fillForm = async (page: any, email: string) => {
      await page.fill('[data-testid="guest-count"]', '10');
      await page.fill('[data-testid="email"]', email);
      await page.fill('[data-testid="phone"]', '555-0100');
      await page.fill('[data-testid="venue-address"]', '123 Test St');
      await page.fill('[data-testid="venue-zip"]', '95112');
    };

    await Promise.all([
      fillForm(page1, 'user1@test.com'),
      fillForm(page2, 'user2@test.com'),
    ]);

    // Both submit simultaneously
    const [result1, result2] = await Promise.allSettled([
      page1.click('[data-testid="submit-booking"]'),
      page2.click('[data-testid="submit-booking"]'),
    ]);

    // Wait for results
    await Promise.all([
      page1.waitForSelector('[data-testid="booking-result"]', {
        timeout: 10000,
      }),
      page2.waitForSelector('[data-testid="booking-result"]', {
        timeout: 10000,
      }),
    ]);

    // Check results - ONE should succeed, ONE should fail
    const success1 = await page1
      .locator('[data-testid="booking-success"]')
      .isVisible();
    const success2 = await page2
      .locator('[data-testid="booking-success"]')
      .isVisible();

    // Exactly one should succeed (XOR)
    expect(success1 !== success2).toBe(true);

    // The failed one should show conflict message
    if (!success1) {
      await expect(
        page1.locator('[data-testid="booking-conflict"]')
      ).toBeVisible();
    }
    if (!success2) {
      await expect(
        page2.locator('[data-testid="booking-conflict"]')
      ).toBeVisible();
    }

    // Cleanup
    await context1.close();
    await context2.close();
  });
});
```

#### Payment Integration Tests (6 hrs)

| Task                   | Effort | Notes                          |
| ---------------------- | ------ | ------------------------------ |
| Stripe Test Mode Suite | 2 hrs  | All payment scenarios          |
| Webhook Handling Tests | 2 hrs  | All event types                |
| Refund Flow Tests      | 1 hr   | Full/partial refunds           |
| Payment Error Recovery | 1 hr   | Declined cards, network errors |

**Stripe Payment Test Suite:**

```typescript
// tests/integration/payments/stripe.spec.ts
import { test, expect } from '@playwright/test';

// Stripe test card numbers
const TEST_CARDS = {
  success: '4242424242424242',
  declined: '4000000000000002',
  insufficientFunds: '4000000000009995',
  expiredCard: '4000000000000069',
  processingError: '4000000000000119',
  requires3DS: '4000002500003155',
};

test.describe('Stripe Payment Integration', () => {
  test.beforeEach(async ({ page }) => {
    // Login and navigate to payment
    await page.goto('/checkout/test-booking-123');
  });

  test('successful payment with valid card', async ({ page }) => {
    // Fill Stripe Elements
    const stripeFrame = page
      .frameLocator('iframe[name^="__privateStripeFrame"]')
      .first();
    await stripeFrame
      .locator('[placeholder="Card number"]')
      .fill(TEST_CARDS.success);
    await stripeFrame
      .locator('[placeholder="MM / YY"]')
      .fill('12/28');
    await stripeFrame.locator('[placeholder="CVC"]').fill('123');
    await stripeFrame.locator('[placeholder="ZIP"]').fill('95112');

    // Submit payment
    await page.click('[data-testid="pay-button"]');

    // Should show success
    await expect(
      page.locator('[data-testid="payment-success"]')
    ).toBeVisible({ timeout: 15000 });
  });

  test('declined card shows appropriate error', async ({ page }) => {
    const stripeFrame = page
      .frameLocator('iframe[name^="__privateStripeFrame"]')
      .first();
    await stripeFrame
      .locator('[placeholder="Card number"]')
      .fill(TEST_CARDS.declined);
    await stripeFrame
      .locator('[placeholder="MM / YY"]')
      .fill('12/28');
    await stripeFrame.locator('[placeholder="CVC"]').fill('123');

    await page.click('[data-testid="pay-button"]');

    // Should show declined error
    await expect(
      page.locator('[data-testid="payment-error"]')
    ).toContainText(/declined/i);

    // Try again button should be visible
    await expect(
      page.locator('[data-testid="try-again-button"]')
    ).toBeVisible();
  });

  test('insufficient funds shows helpful message', async ({
    page,
  }) => {
    const stripeFrame = page
      .frameLocator('iframe[name^="__privateStripeFrame"]')
      .first();
    await stripeFrame
      .locator('[placeholder="Card number"]')
      .fill(TEST_CARDS.insufficientFunds);
    await stripeFrame
      .locator('[placeholder="MM / YY"]')
      .fill('12/28');
    await stripeFrame.locator('[placeholder="CVC"]').fill('123');

    await page.click('[data-testid="pay-button"]');

    await expect(
      page.locator('[data-testid="payment-error"]')
    ).toContainText(/insufficient funds/i);
  });

  test('3DS authentication flow completes', async ({ page }) => {
    const stripeFrame = page
      .frameLocator('iframe[name^="__privateStripeFrame"]')
      .first();
    await stripeFrame
      .locator('[placeholder="Card number"]')
      .fill(TEST_CARDS.requires3DS);
    await stripeFrame
      .locator('[placeholder="MM / YY"]')
      .fill('12/28');
    await stripeFrame.locator('[placeholder="CVC"]').fill('123');

    await page.click('[data-testid="pay-button"]');

    // 3DS modal should appear
    const threeDSFrame = page.frameLocator(
      'iframe[name="stripe-challenge-frame"]'
    );

    // Complete 3DS (in test mode, click "Complete authentication")
    await threeDSFrame
      .locator('[data-testid="complete-authentication"]')
      .click();

    // Should succeed after 3DS
    await expect(
      page.locator('[data-testid="payment-success"]')
    ).toBeVisible({ timeout: 20000 });
  });
});
```

**Webhook Handler Tests:**

```python
# tests/integration/test_stripe_webhooks.py
import pytest
import stripe
from unittest.mock import patch, MagicMock
from apps.backend.src.api.stripe.webhooks import handle_webhook
from apps.backend.src.core.config import settings

class TestStripeWebhooks:
    """Test Stripe webhook handling."""

    @pytest.fixture
    def mock_event_payment_succeeded(self):
        """Mock payment_intent.succeeded event."""
        return {
            "id": "evt_test_123",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test_123",
                    "amount": 10000,  # $100.00
                    "metadata": {
                        "booking_id": "booking_test_123",
                        "payment_type": "deposit",
                    },
                },
            },
        }

    @pytest.fixture
    def mock_event_payment_failed(self):
        """Mock payment_intent.payment_failed event."""
        return {
            "id": "evt_test_456",
            "type": "payment_intent.payment_failed",
            "data": {
                "object": {
                    "id": "pi_test_456",
                    "last_payment_error": {
                        "code": "card_declined",
                        "message": "Your card was declined.",
                    },
                    "metadata": {
                        "booking_id": "booking_test_456",
                    },
                },
            },
        }

    @pytest.mark.asyncio
    async def test_payment_succeeded_updates_booking(
        self,
        mock_event_payment_succeeded,
        db_session,
    ):
        """Payment success should update booking status."""
        # Create test booking
        booking = await create_test_booking(db_session, "booking_test_123")
        assert booking.deposit_status == "pending"

        # Process webhook
        with patch("stripe.Webhook.construct_event") as mock_construct:
            mock_construct.return_value = mock_event_payment_succeeded

            result = await handle_webhook(
                payload=b"test_payload",
                sig_header="test_sig",
            )

        # Verify booking updated
        await db_session.refresh(booking)
        assert booking.deposit_status == "paid"
        assert booking.deposit_amount == 10000
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_payment_failed_logs_error(
        self,
        mock_event_payment_failed,
        db_session,
        caplog,
    ):
        """Payment failure should log error and update booking."""
        booking = await create_test_booking(db_session, "booking_test_456")

        with patch("stripe.Webhook.construct_event") as mock_construct:
            mock_construct.return_value = mock_event_payment_failed

            result = await handle_webhook(
                payload=b"test_payload",
                sig_header="test_sig",
            )

        # Should log the failure
        assert "card_declined" in caplog.text

        # Booking should be marked as payment failed
        await db_session.refresh(booking)
        assert booking.deposit_status == "failed"

    @pytest.mark.asyncio
    async def test_refund_processed_updates_booking(self, db_session):
        """Refund should update booking and log."""
        event = {
            "id": "evt_test_789",
            "type": "charge.refunded",
            "data": {
                "object": {
                    "id": "ch_test_789",
                    "amount_refunded": 5000,  # $50.00 partial refund
                    "metadata": {
                        "booking_id": "booking_test_789",
                    },
                },
            },
        }

        booking = await create_test_booking(db_session, "booking_test_789")
        booking.deposit_status = "paid"
        booking.deposit_amount = 10000
        await db_session.commit()

        with patch("stripe.Webhook.construct_event") as mock_construct:
            mock_construct.return_value = event
            await handle_webhook(b"test", "sig")

        await db_session.refresh(booking)
        assert booking.refund_amount == 5000
        assert booking.deposit_status == "partially_refunded"

    @pytest.mark.asyncio
    async def test_invalid_signature_rejected(self):
        """Invalid webhook signature should be rejected."""
        with patch("stripe.Webhook.construct_event") as mock_construct:
            mock_construct.side_effect = stripe.error.SignatureVerificationError(
                "Invalid signature", "test_sig"
            )

            with pytest.raises(Exception) as exc_info:
                await handle_webhook(b"test", "invalid_sig")

            assert "signature" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_idempotency_prevents_duplicate_processing(
        self,
        mock_event_payment_succeeded,
        db_session,
    ):
        """Same event ID should not be processed twice."""
        booking = await create_test_booking(db_session, "booking_test_123")

        with patch("stripe.Webhook.construct_event") as mock_construct:
            mock_construct.return_value = mock_event_payment_succeeded

            # Process first time
            await handle_webhook(b"test", "sig")

            # Process second time with same event ID
            result = await handle_webhook(b"test", "sig")

        # Should indicate already processed
        assert result.get("status") == "already_processed" or result.get("idempotent") == True
```

### Success Criteria

- [ ] Accept payment via Stripe checkout
- [ ] Deposit collection working
- [ ] Invoice generation working
- [ ] Refund processing working
- [ ] Webhooks receiving and processing events
- [ ] Dynamic pricing admin UI functional
- [ ] Price changes recorded in history table
- [ ] No payment errors for 72 hours (money involved!)
- [ ] Test transactions successful (use Stripe test mode first)

**⚡ Performance (Batch 2):**

- [ ] Load tests passing (100 concurrent users, p95 < 500ms)
- [ ] Payment flow load test passing (50 concurrent checkouts)
- [ ] Lighthouse CI integration working (blocks on regression)
- [ ] Query performance monitor deployed and collecting data
- [ ] No slow queries (p95 > 200ms) in payment flow

**🎨 UI/UX (Batch 2):**

- [ ] Optimistic payment updates implemented
- [ ] Payment progress component working (processing → confirming →
      success)
- [ ] Payment error messages clear and actionable
- [ ] Success celebration animation working (confetti)
- [ ] Receipt download with loading indicator

**🧪 QA (Batch 2):**

- [ ] Load tests scripts created (k6)
- [ ] Concurrent booking race condition test passing
- [ ] All Stripe test cards scenarios covered
- [ ] Webhook handler tests passing
- [ ] 3DS authentication flow tested

### Rollback Plan

```bash
# If payment issues:
FEATURE_STRIPE=false  # Disable immediately
# Queue payments for manual processing
# Alert finance team
```

---

## 🟠 BATCH 3: Core AI (Week 5-6)

**Priority:** HIGH **Branch:** `feature/batch-3-core-ai` **Duration:**
2 weeks **Prerequisite:** Batch 2 stable for 48+ hours

### Components

| Component            | Status   | Notes                   |
| -------------------- | -------- | ----------------------- |
| Intent Router        | ✅ Built | Semantic classification |
| LeadNurturingAgent   | ✅ Built | Sales, pricing          |
| CustomerCareAgent    | ✅ Built | Support                 |
| OperationsAgent      | ✅ Built | Bookings                |
| KnowledgeAgent       | ✅ Built | FAQs                    |
| DistanceAgent        | ✅ Built | Travel fees             |
| MenuAgent            | ✅ Built | Recommendations         |
| AllergenAgent        | ✅ Built | Dietary                 |
| OpenAI Integration   | ✅ Ready | GPT-4                   |
| Basic Chat Endpoint  | ✅ Ready | `/api/v1/ai/chat`       |
| Conversation History | ✅ Ready | Context tracking        |
| Smart Escalation     | ✅ Ready | Human handoff           |
| **Total Routes**     |          | **~30**                 |

### Smart AI Escalation System (From `SMART_AI_ESCALATION_SYSTEM.md`)

| Feature                   | Status    | Target   | Notes                         |
| ------------------------- | --------- | -------- | ----------------------------- |
| Keyword-based auto-resume | ✅ Built  | -        | 30+ AI-handleable keywords    |
| Human-only detection      | ✅ Built  | -        | 15+ escalation keywords       |
| Manual resume button      | ✅ Built  | -        | Always visible in admin       |
| GTM Analytics tracking    | ✅ Built  | -        | All escalation events tracked |
| AI handling rate          | ✅ Target | **80%+** | Reduce human workload         |

#### AI-Handleable Keywords (Auto-Resume)

```
price, cost, book, schedule, menu, date, time, chef,
location, area, serve, available, availability, guests,
dietary, allergy, vegan, vegetarian, halal, kosher,
setup, equipment, cancel, reschedule, travel, fee, distance
```

#### Human-Only Keywords (Escalate)

```
manager, supervisor, complaint, lawsuit, attorney, lawyer,
human, person, agent, representative, speak to someone,
frustrated, angry, unacceptable, refund dispute
```

### Feature Flags

```env
FEATURE_AI_CORE=true
FEATURE_OPENAI=true
FEATURE_SMART_ESCALATION=true
FEATURE_SCALING_AI_METRICS=true
OPENAI_API_KEY=sk-xxx
```

### Backend Tasks (Batch 3 - AI Metrics)

> **4 hours** | AI cost tracking, token monitoring, vector metrics

| Task                       | Status   | Effort  | Notes                                  |
| -------------------------- | -------- | ------- | -------------------------------------- |
| **AI Cost Tracker**        | 🔧 Build | 1.5 hrs | Track OpenAI spend by day/month        |
| **Token Counter**          | 🔧 Build | 1 hr    | Log tokens per request                 |
| **Vector Count Metrics**   | 🔧 Build | 30 min  | Track pgvector row counts              |
| **Embedding Search Timer** | 🔧 Build | 30 min  | Measure vector search latency          |
| **Add to Scaling API**     | 🔧 Build | 30 min  | Extend `/api/v1/admin/scaling/metrics` |

**Integration with Batch 1 Scaling System:**

- Extends existing metrics API with `ai` section
- AI cost warnings: >$300 warning, >$500 critical
- Token warnings: >500K/day warning, >1M critical
- WhatsApp alerts for cost thresholds

### Database Setup (Batch 3)

```sql
-- Enable pgvector for future RAG (prepare early)
CREATE EXTENSION IF NOT EXISTS vector;

-- Run feedback enum migration
psql -d myhibachi -f database/migrations/create_feedback_review_status.sql
```

### Frontend Tasks (Batch 3)

| App               | Component        | Status   | Notes                              |
| ----------------- | ---------------- | -------- | ---------------------------------- |
| **Customer Site** | Chat widget      | 🔧 Build | Floating chat bubble               |
| **Customer Site** | Chat interface   | 🔧 Build | Message history, typing indicators |
| **Customer Site** | Escalation UI    | 🔧 Build | "Talk to human" button             |
| **Admin Panel**   | AI conversations | 🔧 Build | View all AI chats                  |
| **Admin Panel**   | Escalation queue | 🔧 Build | Handle escalated chats             |
| **Admin Panel**   | AI performance   | 🔧 Build | Accuracy metrics dashboard         |
| **Admin Panel**   | Manual resume    | 🔧 Build | Resume AI after escalation         |

---

### ⚡ Performance Optimization (Batch 3)

**Total Estimate:** 10 hours

#### Lazy Chat Widget Loading (1 hr)

| Task                      | Effort | Notes                    |
| ------------------------- | ------ | ------------------------ |
| Dynamic Import ChatWidget | 30 min | Load on user interaction |
| Chat Skeleton Placeholder | 30 min | Show loading state       |

**Lazy ChatWidget Implementation:**

```tsx
// apps/customer/src/components/chat/LazyChatWidget.tsx
'use client';

import dynamic from 'next/dynamic';
import { useState, useCallback } from 'react';
import { MessageCircle } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

// Dynamic import - only loads when chat is opened
const ChatWidget = dynamic(
  () => import('./ChatWidget').then(mod => mod.ChatWidget),
  {
    loading: () => (
      <div className="fixed bottom-4 right-4 w-80 h-96 bg-white rounded-lg shadow-xl border">
        <div className="p-4 border-b">
          <Skeleton variant="text" className="h-6 w-32" />
        </div>
        <div className="p-4 space-y-4">
          <Skeleton variant="text" className="h-16 w-full" />
          <Skeleton variant="text" className="h-16 w-3/4" />
          <Skeleton variant="text" className="h-16 w-full" />
        </div>
      </div>
    ),
    ssr: false, // Chat doesn't need SSR
  }
);

export function LazyChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [hasInteracted, setHasInteracted] = useState(false);

  const handleOpen = useCallback(() => {
    setHasInteracted(true);
    setIsOpen(true);
  }, []);

  return (
    <>
      {/* Chat bubble button - always visible */}
      {!isOpen && (
        <button
          onClick={handleOpen}
          aria-label="Open chat"
          className="fixed bottom-4 right-4 w-14 h-14 rounded-full bg-primary text-white shadow-lg hover:shadow-xl transition-all hover:scale-105 flex items-center justify-center z-50"
        >
          <MessageCircle className="w-6 h-6" />
          <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full animate-pulse" />
        </button>
      )}

      {/* Only load ChatWidget after first interaction */}
      {hasInteracted && (
        <ChatWidget
          isOpen={isOpen}
          onClose={() => setIsOpen(false)}
        />
      )}
    </>
  );
}
```

#### Background Task Queue (6 hrs)

| Task                      | Effort | Notes                     |
| ------------------------- | ------ | ------------------------- |
| Celery Configuration      | 2 hrs  | Redis broker setup        |
| AI Task Workers           | 2 hrs  | Async OpenAI calls        |
| Task Monitoring Dashboard | 1 hr   | Queue depth, failed tasks |
| Retry/Dead Letter Queue   | 1 hr   | Handle failed tasks       |

**Celery Configuration for AI Tasks:**

```python
# apps/backend/src/core/celery_config.py
from celery import Celery
from kombu import Queue, Exchange
from datetime import timedelta

# Initialize Celery
celery_app = Celery(
    'myhibachi',
    broker='redis://localhost:6379/1',
    backend='redis://localhost:6379/2',
)

# Celery Configuration
celery_app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # Task routing
    task_routes={
        'tasks.ai.*': {'queue': 'ai_tasks'},
        'tasks.email.*': {'queue': 'email_tasks'},
        'tasks.notifications.*': {'queue': 'notification_tasks'},
    },

    # Queue definitions
    task_queues=(
        Queue('default', Exchange('default'), routing_key='default'),
        Queue('ai_tasks', Exchange('ai'), routing_key='ai.#'),
        Queue('email_tasks', Exchange('email'), routing_key='email.#'),
        Queue('notification_tasks', Exchange('notifications'), routing_key='notification.#'),
    ),

    # Retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,

    # Rate limiting
    task_annotations={
        'tasks.ai.process_chat': {'rate_limit': '30/m'},  # Max 30 AI calls/minute
        'tasks.ai.generate_embedding': {'rate_limit': '100/m'},
    },

    # Result expiry
    result_expires=timedelta(hours=24),

    # Worker settings
    worker_prefetch_multiplier=4,
    worker_concurrency=4,
)


# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'cleanup-old-conversations': {
        'task': 'tasks.ai.cleanup_old_conversations',
        'schedule': timedelta(hours=24),
    },
    'update-ai-metrics': {
        'task': 'tasks.ai.update_metrics',
        'schedule': timedelta(minutes=5),
    },
}
```

**AI Task Workers:**

```python
# apps/backend/src/tasks/ai_tasks.py
import logging
from celery import shared_task
from typing import Dict, Any
from datetime import datetime, timedelta

from src.core.celery_config import celery_app
from src.services.ai.chat_service import ChatService
from src.services.ai.embedding_service import EmbeddingService
from src.core.database import SessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(
    name='tasks.ai.process_chat',
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
)
def process_chat_async(self, conversation_id: str, message: str, context: Dict[str, Any]):
    """Process chat message asynchronously."""
    try:
        logger.info(f"Processing chat for conversation {conversation_id}")

        with SessionLocal() as db:
            chat_service = ChatService(db)
            result = chat_service.process_message(
                conversation_id=conversation_id,
                message=message,
                context=context,
            )

        return {
            'success': True,
            'conversation_id': conversation_id,
            'response': result.response,
            'intent': result.intent,
            'tokens_used': result.tokens_used,
        }
    except Exception as e:
        logger.error(f"Chat processing failed: {e}", exc_info=True)
        # Will auto-retry due to autoretry_for
        raise


@celery_app.task(
    name='tasks.ai.generate_embedding',
    bind=True,
    rate_limit='100/m',  # Max 100 embeddings per minute
)
def generate_embedding_async(self, text: str, metadata: Dict[str, Any]):
    """Generate embedding for text asynchronously."""
    try:
        embedding_service = EmbeddingService()
        embedding = embedding_service.generate(text)

        with SessionLocal() as db:
            embedding_service.store(db, embedding, metadata)

        return {'success': True, 'dimensions': len(embedding)}
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise self.retry(exc=e, countdown=30)


@celery_app.task(name='tasks.ai.cleanup_old_conversations')
def cleanup_old_conversations():
    """Clean up conversations older than 30 days."""
    cutoff = datetime.utcnow() - timedelta(days=30)

    with SessionLocal() as db:
        result = db.execute(
            "DELETE FROM ai.conversations WHERE updated_at < :cutoff",
            {'cutoff': cutoff}
        )
        db.commit()

        logger.info(f"Cleaned up {result.rowcount} old conversations")
        return {'deleted': result.rowcount}


@celery_app.task(name='tasks.ai.update_metrics')
def update_ai_metrics():
    """Update AI metrics for dashboard."""
    from src.services.scaling.ai_metrics_service import AIMetricsService

    with SessionLocal() as db:
        service = AIMetricsService(db)
        metrics = service.calculate_current_metrics()
        service.store_metrics(metrics)

        return {'updated': True, 'metrics': metrics}
```

**Task Monitoring Endpoint:**

```python
# apps/backend/src/api/admin/endpoints/celery_tasks.py
from fastapi import APIRouter, Depends
from typing import Dict, Any
from celery import current_app as celery_app
from celery.app.control import Inspect

from src.core.auth import require_admin

router = APIRouter(prefix="/admin/tasks", tags=["Admin - Tasks"])


@router.get("/status")
async def get_task_status(_: dict = Depends(require_admin)) -> Dict[str, Any]:
    """Get Celery task queue status."""
    inspect = Inspect(app=celery_app)

    return {
        "active": inspect.active() or {},
        "reserved": inspect.reserved() or {},
        "scheduled": inspect.scheduled() or {},
        "stats": inspect.stats() or {},
        "queues": {
            "ai_tasks": get_queue_length("ai_tasks"),
            "email_tasks": get_queue_length("email_tasks"),
            "notification_tasks": get_queue_length("notification_tasks"),
        },
    }


@router.get("/failed")
async def get_failed_tasks(_: dict = Depends(require_admin)) -> Dict[str, Any]:
    """Get failed tasks from dead letter queue."""
    # Get from Redis dead letter queue
    from src.core.redis import redis_client

    failed = redis_client.lrange("celery:dead_letter", 0, 100)
    return {
        "count": len(failed),
        "tasks": [json.loads(t) for t in failed[:50]],  # Limit to 50
    }


@router.post("/retry/{task_id}")
async def retry_failed_task(task_id: str, _: dict = Depends(require_admin)):
    """Retry a specific failed task."""
    from celery.result import AsyncResult

    result = AsyncResult(task_id, app=celery_app)
    if result.state == 'FAILURE':
        result.retry()
        return {"status": "retrying", "task_id": task_id}

    return {"status": "not_failed", "current_state": result.state}


def get_queue_length(queue_name: str) -> int:
    """Get number of tasks in a queue."""
    from src.core.redis import redis_client
    return redis_client.llen(f"celery:{queue_name}")
```

#### AI Response Caching (3 hrs)

| Task               | Effort | Notes                          |
| ------------------ | ------ | ------------------------------ |
| FAQ Response Cache | 1 hr   | Cache common questions         |
| Semantic Cache Key | 1 hr   | Similar questions hit cache    |
| Cache Invalidation | 1 hr   | Clear on knowledge base update |

**AI Response Cache Service:**

```python
# apps/backend/src/services/ai/response_cache.py
import hashlib
import json
from typing import Optional, Dict, Any
from datetime import timedelta

from src.core.redis import redis_client
from src.services.ai.embedding_service import EmbeddingService


class AIResponseCache:
    """Cache for AI responses with semantic similarity matching."""

    def __init__(self, ttl_hours: int = 24):
        self.ttl = timedelta(hours=ttl_hours)
        self.embedding_service = EmbeddingService()
        self.similarity_threshold = 0.95  # 95% similar = cache hit

    def get_cache_key(self, message: str) -> str:
        """Generate deterministic cache key from message."""
        normalized = message.lower().strip()
        return f"ai:response:{hashlib.sha256(normalized.encode()).hexdigest()[:16]}"

    async def get(self, message: str) -> Optional[Dict[str, Any]]:
        """Get cached response for message."""
        # Try exact match first
        key = self.get_cache_key(message)
        cached = redis_client.get(key)

        if cached:
            return json.loads(cached)

        # Try semantic similarity match
        return await self._get_similar(message)

    async def _get_similar(self, message: str) -> Optional[Dict[str, Any]]:
        """Find semantically similar cached response."""
        # Get embedding for incoming message
        embedding = await self.embedding_service.generate_async(message)

        # Search cache index for similar embeddings
        # Using Redis Vector Search if available, else skip
        try:
            results = redis_client.execute_command(
                'FT.SEARCH', 'idx:ai_cache',
                f'*=>[KNN 1 @embedding $vec AS score]',
                'PARAMS', '2', 'vec', embedding.tobytes(),
                'RETURN', '2', 'response', 'score',
                'DIALECT', '2'
            )

            if results and len(results) > 1:
                score = float(results[1][3])  # Similarity score
                if score >= self.similarity_threshold:
                    return json.loads(results[1][1])
        except Exception:
            # Redis Vector Search not available, skip semantic matching
            pass

        return None

    async def set(
        self,
        message: str,
        response: str,
        intent: str,
        metadata: Dict[str, Any] = None
    ):
        """Cache AI response."""
        key = self.get_cache_key(message)

        data = {
            'response': response,
            'intent': intent,
            'metadata': metadata or {},
            'cached_at': datetime.utcnow().isoformat(),
        }

        redis_client.setex(
            key,
            int(self.ttl.total_seconds()),
            json.dumps(data)
        )

        # Also store embedding for semantic search
        await self._store_embedding(message, data)

    async def _store_embedding(self, message: str, data: Dict[str, Any]):
        """Store embedding for semantic cache lookup."""
        try:
            embedding = await self.embedding_service.generate_async(message)
            key = self.get_cache_key(message)

            redis_client.hset(
                f"ai:cache:embeddings:{key}",
                mapping={
                    'embedding': embedding.tobytes(),
                    'response': json.dumps(data),
                }
            )
            redis_client.expire(f"ai:cache:embeddings:{key}", int(self.ttl.total_seconds()))
        except Exception:
            pass  # Embedding storage is optional

    def invalidate_all(self):
        """Clear all cached responses (use after knowledge base update)."""
        keys = redis_client.keys("ai:response:*")
        if keys:
            redis_client.delete(*keys)

        embedding_keys = redis_client.keys("ai:cache:embeddings:*")
        if embedding_keys:
            redis_client.delete(*embedding_keys)


# Singleton instance
ai_response_cache = AIResponseCache()
```

---

### 🎨 UI/UX Polish (Batch 3)

**Total Estimate:** 10 hours

#### Chat Widget UX (6 hrs)

| Task                       | Effort | Notes                           |
| -------------------------- | ------ | ------------------------------- |
| Typing Indicator Animation | 1 hr   | Animated dots while AI thinks   |
| Message Streaming UI       | 2 hrs  | Stream AI response word-by-word |
| Chat Sound Effects         | 1 hr   | Optional notification sounds    |
| Chat Minimize/Maximize     | 1 hr   | Smooth transitions              |
| Mobile-Optimized Chat      | 1 hr   | Full-screen on mobile           |

**Typing Indicator Component:**

```tsx
// apps/customer/src/components/chat/TypingIndicator.tsx
'use client';

import { motion } from 'framer-motion';

export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 p-3 bg-gray-100 rounded-lg w-fit">
      {[0, 1, 2].map(i => (
        <motion.span
          key={i}
          className="w-2 h-2 bg-gray-400 rounded-full"
          animate={{
            y: [0, -5, 0],
            opacity: [0.5, 1, 0.5],
          }}
          transition={{
            duration: 0.6,
            repeat: Infinity,
            delay: i * 0.2,
            ease: 'easeInOut',
          }}
        />
      ))}
      <span className="sr-only">AI is typing...</span>
    </div>
  );
}
```

**Message Streaming Component:**

```tsx
// apps/customer/src/components/chat/StreamingMessage.tsx
'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface StreamingMessageProps {
  content: string;
  isStreaming: boolean;
  onComplete?: () => void;
}

export function StreamingMessage({
  content,
  isStreaming,
  onComplete,
}: StreamingMessageProps) {
  const [displayedContent, setDisplayedContent] = useState('');
  const [cursorVisible, setCursorVisible] = useState(true);
  const contentRef = useRef(content);
  const indexRef = useRef(0);

  useEffect(() => {
    if (!isStreaming) {
      setDisplayedContent(content);
      return;
    }

    contentRef.current = content;

    // Stream effect - reveal characters progressively
    const interval = setInterval(() => {
      if (indexRef.current < contentRef.current.length) {
        setDisplayedContent(
          contentRef.current.slice(0, indexRef.current + 1)
        );
        indexRef.current++;
      } else {
        clearInterval(interval);
        setCursorVisible(false);
        onComplete?.();
      }
    }, 20); // 20ms per character = fast but readable

    return () => clearInterval(interval);
  }, [content, isStreaming, onComplete]);

  // Cursor blink effect
  useEffect(() => {
    if (!isStreaming) return;

    const blink = setInterval(() => {
      setCursorVisible(v => !v);
    }, 500);

    return () => clearInterval(blink);
  }, [isStreaming]);

  return (
    <div className="relative">
      <p className="text-gray-800 whitespace-pre-wrap">
        {displayedContent}
        <AnimatePresence>
          {cursorVisible && isStreaming && (
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="inline-block w-0.5 h-4 bg-primary ml-0.5 align-middle"
            />
          )}
        </AnimatePresence>
      </p>
    </div>
  );
}
```

**Mobile Full-Screen Chat:**

```tsx
// apps/customer/src/components/chat/MobileChatWrapper.tsx
'use client';

import { useMediaQuery } from '@/hooks/useMediaQuery';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Minimize2 } from 'lucide-react';

interface MobileChatWrapperProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
}

export function MobileChatWrapper({
  isOpen,
  onClose,
  children,
}: MobileChatWrapperProps) {
  const isMobile = useMediaQuery('(max-width: 640px)');

  // Desktop: floating window
  if (!isMobile) {
    return (
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed bottom-4 right-4 w-96 h-[500px] bg-white rounded-xl shadow-2xl border overflow-hidden z-50"
          >
            <ChatHeader onClose={onClose} />
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    );
  }

  // Mobile: full-screen overlay
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ y: '100%' }}
          animate={{ y: 0 }}
          exit={{ y: '100%' }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          className="fixed inset-0 bg-white z-50 flex flex-col"
        >
          <ChatHeader onClose={onClose} isMobile />
          <div className="flex-1 overflow-hidden">{children}</div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function ChatHeader({
  onClose,
  isMobile = false,
}: {
  onClose: () => void;
  isMobile?: boolean;
}) {
  return (
    <div className="flex items-center justify-between p-4 border-b bg-primary text-white">
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
        <span className="font-medium">My Hibachi Assistant</span>
      </div>
      <button
        onClick={onClose}
        className="p-1 hover:bg-white/10 rounded transition-colors"
        aria-label="Close chat"
      >
        {isMobile ? (
          <X className="w-5 h-5" />
        ) : (
          <Minimize2 className="w-5 h-5" />
        )}
      </button>
    </div>
  );
}
```

#### Escalation UX (4 hrs)

| Task                       | Effort | Notes                       |
| -------------------------- | ------ | --------------------------- |
| "Talk to Human" Button     | 1 hr   | Prominent but not intrusive |
| Escalation Confirmation    | 1 hr   | Explain wait time           |
| Human Agent Joined Message | 1 hr   | Clear handoff indication    |
| Post-Escalation Survey     | 1 hr   | Quick satisfaction rating   |

**Escalation UI Components:**

```tsx
// apps/customer/src/components/chat/EscalationButton.tsx
'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { User, Clock, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface EscalationButtonProps {
  onEscalate: () => Promise<void>;
  disabled?: boolean;
}

export function EscalationButton({
  onEscalate,
  disabled,
}: EscalationButtonProps) {
  const [showConfirm, setShowConfirm] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleEscalate = async () => {
    setIsLoading(true);
    try {
      await onEscalate();
    } finally {
      setIsLoading(false);
      setShowConfirm(false);
    }
  };

  return (
    <div className="relative">
      {!showConfirm ? (
        <button
          onClick={() => setShowConfirm(true)}
          disabled={disabled}
          className="text-sm text-gray-500 hover:text-primary underline disabled:opacity-50"
        >
          Talk to a human
        </button>
      ) : (
        <AnimatePresence>
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="absolute bottom-full right-0 mb-2 p-4 bg-white rounded-lg shadow-lg border w-72"
          >
            <div className="space-y-3">
              <div className="flex items-start gap-2">
                <User className="w-5 h-5 text-primary mt-0.5" />
                <div>
                  <p className="font-medium text-gray-900">
                    Connect with an agent
                  </p>
                  <p className="text-sm text-gray-500">
                    A team member will join this conversation
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2 text-sm text-amber-600 bg-amber-50 p-2 rounded">
                <Clock className="w-4 h-4" />
                <span>Typical wait: 2-5 minutes</span>
              </div>

              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowConfirm(false)}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button
                  size="sm"
                  onClick={handleEscalate}
                  disabled={isLoading}
                  className="flex-1"
                >
                  {isLoading ? 'Connecting...' : 'Connect Now'}
                </Button>
              </div>
            </div>
          </motion.div>
        </AnimatePresence>
      )}
    </div>
  );
}
```

**Human Agent Joined Message:**

```tsx
// apps/customer/src/components/chat/AgentJoinedMessage.tsx
'use client';

import { motion } from 'framer-motion';
import { UserCheck } from 'lucide-react';

interface AgentJoinedMessageProps {
  agentName: string;
}

export function AgentJoinedMessage({
  agentName,
}: AgentJoinedMessageProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="flex items-center justify-center gap-2 py-3 px-4 bg-green-50 text-green-700 rounded-lg mx-4 my-2"
    >
      <UserCheck className="w-5 h-5" />
      <span className="font-medium">
        {agentName} has joined the conversation
      </span>
    </motion.div>
  );
}
```

---

### 🧪 QA & Testing (Batch 3)

**Total Estimate:** 10 hours

#### AI Response Testing (6 hrs)

| Task                        | Effort | Notes                      |
| --------------------------- | ------ | -------------------------- |
| Intent Classification Tests | 2 hrs  | 50+ test cases             |
| Response Quality Tests      | 2 hrs  | Check for accuracy/tone    |
| Escalation Trigger Tests    | 1 hr   | Verify escalation keywords |
| Edge Case Testing           | 1 hr   | Empty, long, special chars |

**AI Intent Classification Test Suite:**

```python
# tests/ai/test_intent_classification.py
import pytest
from src.services.ai.intent_router import IntentRouter

class TestIntentClassification:
    """Test AI intent classification accuracy."""

    @pytest.fixture
    def router(self):
        return IntentRouter()

    # Pricing Intent Tests
    @pytest.mark.parametrize("message,expected_intent", [
        ("How much does it cost?", "pricing"),
        ("What are your prices?", "pricing"),
        ("How much for 20 guests?", "pricing"),
        ("Price for a birthday party", "pricing"),
        ("What's the cost per person?", "pricing"),
        ("Do you have any deals?", "pricing"),
        ("Is there a minimum?", "pricing"),
    ])
    def test_pricing_intent(self, router, message, expected_intent):
        result = router.classify(message)
        assert result.intent == expected_intent

    # Booking Intent Tests
    @pytest.mark.parametrize("message,expected_intent", [
        ("I want to book a party", "booking"),
        ("Can I schedule for next Saturday?", "booking"),
        ("I'd like to make a reservation", "booking"),
        ("Book for March 15th", "booking"),
        ("Available dates?", "booking"),
        ("Do you have openings?", "booking"),
    ])
    def test_booking_intent(self, router, message, expected_intent):
        result = router.classify(message)
        assert result.intent == expected_intent

    # Menu Intent Tests
    @pytest.mark.parametrize("message,expected_intent", [
        ("What's on the menu?", "menu"),
        ("Do you have salmon?", "menu"),
        ("What do you serve?", "menu"),
        ("Can you make vegetarian?", "menu"),
        ("Tell me about the food", "menu"),
    ])
    def test_menu_intent(self, router, message, expected_intent):
        result = router.classify(message)
        assert result.intent == expected_intent

    # Escalation Intent Tests (should route to human)
    @pytest.mark.parametrize("message,should_escalate", [
        ("I want to speak to a manager", True),
        ("This is unacceptable", True),
        ("I need a human agent", True),
        ("Get me a supervisor", True),
        ("I'm going to sue you", True),
        ("What's your pricing?", False),  # Should NOT escalate
        ("Book for Saturday", False),
    ])
    def test_escalation_detection(self, router, message, should_escalate):
        result = router.classify(message)
        assert result.should_escalate == should_escalate

    # Edge Case Tests
    @pytest.mark.parametrize("message", [
        "",  # Empty
        "   ",  # Whitespace only
        "a" * 10000,  # Very long
        "🎉🎂🍣",  # Emoji only
        "SELECT * FROM users;",  # SQL injection attempt
        "<script>alert('xss')</script>",  # XSS attempt
    ])
    def test_edge_cases_no_crash(self, router, message):
        """Edge cases should not crash, may return unknown intent."""
        result = router.classify(message)
        assert result is not None
        assert result.intent is not None  # Some intent assigned


class TestResponseQuality:
    """Test AI response quality and appropriateness."""

    @pytest.fixture
    def chat_service(self):
        from src.services.ai.chat_service import ChatService
        return ChatService()

    @pytest.mark.asyncio
    async def test_response_contains_relevant_info(self, chat_service):
        """Response should contain relevant information."""
        response = await chat_service.get_response("How much for 10 guests?")

        # Should mention pricing or ask for more details
        assert any(word in response.lower() for word in ['price', 'cost', '$', 'guest', 'person'])

    @pytest.mark.asyncio
    async def test_response_professional_tone(self, chat_service):
        """Response should be professional and friendly."""
        response = await chat_service.get_response("What do you offer?")

        # Should not contain inappropriate content
        inappropriate = ['damn', 'hell', 'stupid']
        assert not any(word in response.lower() for word in inappropriate)

    @pytest.mark.asyncio
    async def test_response_length_reasonable(self, chat_service):
        """Response should be reasonable length."""
        response = await chat_service.get_response("Tell me about your service")

        # Not too short (unhelpful) or too long (overwhelming)
        assert 50 < len(response) < 2000

    @pytest.mark.asyncio
    async def test_no_hallucination_about_prices(self, chat_service):
        """AI should not make up specific prices."""
        response = await chat_service.get_response("Exactly how much is it?")

        # Should direct to quote calculator or say prices vary
        # Should NOT make up specific dollar amounts
        assert 'quote' in response.lower() or 'varies' in response.lower() or 'depends' in response.lower()
```

#### Chat E2E Tests (4 hrs)

| Task                   | Effort | Notes                         |
| ---------------------- | ------ | ----------------------------- |
| Full Chat Flow Tests   | 2 hrs  | Open → send → receive → close |
| Escalation E2E Tests   | 1 hr   | Request → connect → resolve   |
| Chat Persistence Tests | 1 hr   | Refresh → history preserved   |

**Chat E2E Test Suite:**

```typescript
// tests/e2e/chat.spec.ts
import { test, expect } from '@playwright/test';

test.describe('AI Chat Widget', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('opens chat widget on click', async ({ page }) => {
    // Click chat bubble
    await page.click('[aria-label="Open chat"]');

    // Chat window should be visible
    await expect(
      page.locator('[data-testid="chat-window"]')
    ).toBeVisible();
  });

  test('sends message and receives AI response', async ({ page }) => {
    await page.click('[aria-label="Open chat"]');

    // Type and send message
    await page.fill(
      '[data-testid="chat-input"]',
      'What are your prices?'
    );
    await page.click('[data-testid="send-button"]');

    // User message should appear
    await expect(
      page.locator('[data-testid="user-message"]').last()
    ).toContainText('What are your prices?');

    // Typing indicator should appear
    await expect(
      page.locator('[data-testid="typing-indicator"]')
    ).toBeVisible();

    // AI response should appear (wait up to 10s)
    await expect(
      page.locator('[data-testid="ai-message"]').last()
    ).toBeVisible({ timeout: 10000 });
  });

  test('escalates to human agent', async ({ page }) => {
    await page.click('[aria-label="Open chat"]');

    // Send message that triggers escalation option
    await page.fill(
      '[data-testid="chat-input"]',
      'I want to speak to a manager'
    );
    await page.click('[data-testid="send-button"]');

    // Escalation button should appear
    await expect(
      page.locator('[data-testid="escalate-button"]')
    ).toBeVisible({ timeout: 5000 });

    // Click escalate
    await page.click('[data-testid="escalate-button"]');
    await page.click('[data-testid="confirm-escalate"]');

    // Should show escalation status
    await expect(
      page.locator('[data-testid="escalation-status"]')
    ).toContainText(/connecting|waiting|queue/i);
  });

  test('preserves chat history on page refresh', async ({ page }) => {
    await page.click('[aria-label="Open chat"]');

    // Send a message
    await page.fill(
      '[data-testid="chat-input"]',
      'Hello, test message'
    );
    await page.click('[data-testid="send-button"]');

    // Wait for AI response
    await expect(
      page.locator('[data-testid="ai-message"]')
    ).toBeVisible({ timeout: 10000 });

    // Refresh page
    await page.reload();

    // Reopen chat
    await page.click('[aria-label="Open chat"]');

    // Previous message should still be there
    await expect(
      page.locator('[data-testid="user-message"]')
    ).toContainText('Hello, test message');
  });

  test('mobile: chat opens full screen', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    await page.click('[aria-label="Open chat"]');

    // Chat should be full screen on mobile
    const chatWindow = page.locator('[data-testid="chat-window"]');
    const boundingBox = await chatWindow.boundingBox();

    expect(boundingBox?.width).toBeCloseTo(375, 5);
    expect(boundingBox?.height).toBeCloseTo(667, 50);
  });
});
```

### Success Criteria

**Core AI Functionality:**

- [ ] Chat responds correctly 80%+ of time
- [ ] Intent routing working (correct agent selected)
- [ ] Smart escalation auto-resume functional
- [ ] 80%+ conversations handled by AI without human
- [ ] Admin review queue receiving flagged items
- [ ] Response time <3 seconds average
- [ ] No AI crashes for 48 hours

**AI Scaling Foundation (Batch 3):**

- [ ] pgvector extension enabled in PostgreSQL
- [ ] AI schema (`ai.*`) tables using separate connection pool
      (optional)
- [ ] Redis cluster config pattern documented
- [ ] Embedding storage ready for future growth
- [ ] AI metrics collecting for cost monitoring

**AI Scaling Measurement (Batch 3):**

- [ ] AI cost tracker logging OpenAI spend per request
- [ ] Token counter tracking daily/monthly usage
- [ ] Vector count metrics in scaling dashboard
- [ ] Embedding search latency tracked
- [ ] `/api/v1/admin/scaling/metrics` returns AI section
- [ ] WhatsApp alert triggers at $300/mo warning, $500/mo critical
- [ ] Admin dashboard shows AI cost trend chart

**⚡ Performance (Batch 3):**

- [ ] Chat widget lazy-loaded (only loads on first interaction)
- [ ] Celery task queue operational for AI tasks
- [ ] AI task monitoring endpoint working (`/admin/tasks/status`)
- [ ] FAQ response caching implemented (cache hit rate > 30%)
- [ ] AI response time < 3s (p95)

**🎨 UI/UX (Batch 3):**

- [ ] Typing indicator animation working
- [ ] Message streaming UI implemented (word-by-word reveal)
- [ ] Mobile chat opens full-screen with smooth transition
- [ ] "Talk to Human" button with confirmation dialog
- [ ] Human agent joined notification visible
- [ ] Chat state persists across page refresh

**🧪 QA (Batch 3):**

- [ ] Intent classification tests passing (50+ test cases)
- [ ] Response quality tests passing (no hallucinations)
- [ ] Escalation trigger tests passing (all keywords detected)
- [ ] Chat E2E tests passing (full flow tested)
- [ ] Edge case tests passing (empty, long, special chars)

### Rollback Plan

```bash
FEATURE_AI_CORE=false  # Disable AI
# Route all inquiries to human agents
```

---

## 🟠 BATCH 4: Communications (Week 7-8)

**Priority:** HIGH **Branch:** `feature/batch-4-communications`
**Duration:** 2 weeks **Prerequisite:** Batch 2 stable (payments
needed for some flows)

### Components

| Component                | Status       | Notes                      |
| ------------------------ | ------------ | -------------------------- |
| RingCentral SMS          | ✅ Ready     | `CallStatus` enum added    |
| RingCentral Voice        | ✅ Ready     | `CallDirection` enum added |
| Deepgram Transcription   | ✅ Ready     | Phase 2.1 Complete         |
| Meta WhatsApp            | 🔧 Configure | Production API             |
| Meta Facebook            | 🔧 Configure | Comments + Messenger       |
| Meta Instagram           | 🔧 Configure | Comments + DMs             |
| Google Business Messages | 🔧 Configure | Business Profile           |
| Email Service            | ✅ Ready     | SMTP                       |
| **Total Routes**         |              | **~35**                    |

### RingCentral Webhook Analysis (From `PHASE_2_2_RINGCENTRAL_WEBHOOK_ANALYSIS.md`)

| Task                                | Status       | Effort | Notes                         |
| ----------------------------------- | ------------ | ------ | ----------------------------- |
| Create `RingCentralVoiceAI` service | 🔧 Build     | 1 hour | Core voice AI handler         |
| Webhook signature validation        | 🔧 Build     | 30 min | Security verification         |
| AI Orchestrator integration         | 🔧 Build     | 1 hour | Connect to multi-agent system |
| End-to-end testing                  | 🔧 Build     | 30 min | Test suite                    |
| Environment configuration           | 🔧 Configure | 10 min | `RC_WEBHOOK_SECRET` etc       |

### RingCentral Native Recording (From `PHASE_2_3_RINGCENTRAL_NATIVE_RECORDING.md`)

| Task                  | Status   | Effort      | Notes                                       |
| --------------------- | -------- | ----------- | ------------------------------------------- |
| Database model update | 🔧 Build | 10 min      | Add `rc_recording_id`, `rc_transcript`      |
| RC service methods    | 🔧 Build | 20 min      | `fetch_recording()`, `get_transcript()`     |
| Webhook enhancement   | 🔧 Build | 15 min      | Handle recording events                     |
| Celery task for async | 🔧 Build | 20 min      | Background processing                       |
| API endpoints         | 🔧 Build | 30 min      | Playback, transcript retrieval              |
| Testing               | 🔧 Build | 15 min      | Unit + integration tests                    |
| **Total Phase 2.3**   |          | **2 hours** | Uses RC built-in (FREE vs $1-2/hr Deepgram) |

#### Why RC Native Recording?

- **Cost:** $0/month (included with RC plan) vs $1-2/hour with
  Deepgram
- **Simplicity:** No external API calls, data stays in RC
- **Compliance:** RC handles recording consent automatically
- **Quality:** RC's own transcription is production-tested

### Meta/Social Channels

| Channel                  | Source Doc                             | Status       |
| ------------------------ | -------------------------------------- | ------------ |
| WhatsApp Business API    | `WHATSAPP_BUSINESS_API_SETUP_GUIDE.md` | 🔧 Configure |
| Facebook Messenger       | `API_INTEGRATIONS_TODO_PRODUCTION.md`  | 🔧 Configure |
| Instagram DMs            | `API_INTEGRATIONS_TODO_PRODUCTION.md`  | 🔧 Configure |
| Google Business Messages | `API_INTEGRATIONS_TODO_PRODUCTION.md`  | 🔧 Configure |

### Feature Flags

```env
FEATURE_RINGCENTRAL=true
FEATURE_VOICE_AI=true
FEATURE_DEEPGRAM=true
FEATURE_RC_NATIVE_RECORDING=true
FEATURE_META_WHATSAPP=true
FEATURE_META_FACEBOOK=true
FEATURE_META_INSTAGRAM=true
FEATURE_GOOGLE_BUSINESS=true

RINGCENTRAL_CLIENT_ID=xxx
RINGCENTRAL_CLIENT_SECRET=xxx
RC_WEBHOOK_SECRET=xxx
DEEPGRAM_API_KEY=xxx
META_ACCESS_TOKEN=xxx
```

### Customizable Message Templates System

| Feature               | Status   | Effort  | Notes                                       |
| --------------------- | -------- | ------- | ------------------------------------------- |
| Template Table        | 🔧 Build | 2 hours | Store templates with placeholders           |
| Template Categories   | 🔧 Build | 1 hour  | Booking, Payment, Reminder, Follow-up       |
| Variable Placeholders | 🔧 Build | 2 hours | `{{customer_name}}`, `{{event_date}}`, etc. |
| Template Editor UI    | 🔧 Build | 3 hours | Admin can create/edit templates             |
| User Content Merge    | 🔧 Build | 2 hours | Customize message per context               |
| Quick Insert          | 🔧 Build | 1 hour  | Dropdown in composer to insert template     |

**Template Variables Available:**

```
{{customer_name}}     - Customer full name
{{event_date}}        - Event date formatted
{{event_time}}        - Event time
{{guest_count}}       - Number of guests
{{chef_name}}         - Assigned chef name
{{total_amount}}      - Total booking amount
{{deposit_amount}}    - Deposit amount
{{balance_due}}       - Remaining balance
{{booking_id}}        - Booking reference ID
{{payment_link}}      - Direct payment URL
```

### Frontend Tasks (Batch 4)

| App             | Component         | Status   | Notes                         |
| --------------- | ----------------- | -------- | ----------------------------- |
| **Admin Panel** | Unified inbox     | 🔧 Build | All channels in one view      |
| **Admin Panel** | SMS composer      | 🔧 Build | Send SMS from admin           |
| **Admin Panel** | Call history      | 🔧 Build | View call recordings          |
| **Admin Panel** | Recording player  | 🔧 Build | Play RC recordings            |
| **Admin Panel** | Transcript viewer | 🔧 Build | View RC transcripts           |
| **Admin Panel** | WhatsApp view     | 🔧 Build | WhatsApp conversations        |
| **Admin Panel** | Facebook/IG view  | 🔧 Build | Social media messages         |
| **Admin Panel** | Channel analytics | 🔧 Build | Messages per channel          |
| **Admin Panel** | Template Manager  | 🔧 Build | Create/edit message templates |

---

### ⚡ Performance Optimization (Batch 4)

**Total Estimate:** 8 hours

#### Admin Dashboard Performance (4 hrs)

| Task                         | Effort | Notes                              |
| ---------------------------- | ------ | ---------------------------------- |
| Unified Inbox Virtualization | 2 hrs  | Virtual list for 1000s of messages |
| Channel Lazy Loading         | 1 hr   | Load channels on demand            |
| Message Prefetching          | 1 hr   | Preload next page on scroll        |

**Virtual List Implementation:**

```tsx
// apps/admin/src/components/inbox/VirtualInbox.tsx
'use client';

import { useVirtualizer } from '@tanstack/react-virtual';
import { useRef, useCallback } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';

interface Message {
  id: string;
  channel: string;
  content: string;
  timestamp: Date;
  sender: string;
}

interface VirtualInboxProps {
  channelFilter?: string;
}

export function VirtualInbox({ channelFilter }: VirtualInboxProps) {
  const parentRef = useRef<HTMLDivElement>(null);

  const { data, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useInfiniteQuery({
      queryKey: ['inbox', channelFilter],
      queryFn: async ({ pageParam = 0 }) => {
        const res = await fetch(
          `/api/v1/admin/inbox?page=${pageParam}&channel=${channelFilter || ''}`
        );
        return res.json();
      },
      getNextPageParam: (lastPage, pages) => {
        return lastPage.hasMore ? pages.length : undefined;
      },
      initialPageParam: 0,
    });

  const allMessages =
    data?.pages.flatMap(page => page.messages) ?? [];

  const virtualizer = useVirtualizer({
    count: hasNextPage ? allMessages.length + 1 : allMessages.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 80, // Estimated row height
    overscan: 5,
  });

  const virtualItems = virtualizer.getVirtualItems();

  // Prefetch next page when scrolling near bottom
  const lastItem = virtualItems[virtualItems.length - 1];
  if (
    lastItem &&
    lastItem.index >= allMessages.length - 1 &&
    hasNextPage &&
    !isFetchingNextPage
  ) {
    fetchNextPage();
  }

  return (
    <div ref={parentRef} className="h-[600px] overflow-auto">
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualItems.map(virtualRow => {
          const isLoaderRow = virtualRow.index >= allMessages.length;
          const message = allMessages[virtualRow.index];

          return (
            <div
              key={virtualRow.key}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: `${virtualRow.size}px`,
                transform: `translateY(${virtualRow.start}px)`,
              }}
            >
              {isLoaderRow ? (
                <div className="p-4 text-center text-gray-500">
                  Loading more...
                </div>
              ) : (
                <MessageRow message={message} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function MessageRow({ message }: { message: Message }) {
  return (
    <div className="flex items-center gap-3 p-3 border-b hover:bg-gray-50 cursor-pointer">
      <ChannelIcon channel={message.channel} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <span className="font-medium truncate">
            {message.sender}
          </span>
          <span className="text-xs text-gray-500">
            {formatTime(message.timestamp)}
          </span>
        </div>
        <p className="text-sm text-gray-600 truncate">
          {message.content}
        </p>
      </div>
    </div>
  );
}
```

#### Message Queue Optimization (4 hrs)

| Task                        | Effort | Notes                           |
| --------------------------- | ------ | ------------------------------- |
| Redis Pub/Sub for Real-time | 2 hrs  | Push new messages instantly     |
| WebSocket Connection Pool   | 1 hr   | Efficient connection management |
| Message Batching            | 1 hr   | Batch multiple messages         |

**WebSocket Message Service:**

```python
# apps/backend/src/services/realtime/message_service.py
import asyncio
import json
from typing import Dict, Set, Any
from fastapi import WebSocket
from redis.asyncio import Redis

from src.core.redis import get_redis_async

class MessageRealtimeService:
    """Real-time message delivery via WebSocket + Redis Pub/Sub."""

    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = {}  # user_id -> connections
        self._pubsub = None
        self._redis: Redis = None

    async def connect(self, websocket: WebSocket, user_id: str):
        """Register a new WebSocket connection."""
        await websocket.accept()

        if user_id not in self._connections:
            self._connections[user_id] = set()
        self._connections[user_id].add(websocket)

        # Subscribe to user's message channel if first connection
        if len(self._connections[user_id]) == 1:
            await self._subscribe_user(user_id)

    async def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove a WebSocket connection."""
        if user_id in self._connections:
            self._connections[user_id].discard(websocket)

            # Unsubscribe if no more connections
            if not self._connections[user_id]:
                del self._connections[user_id]
                await self._unsubscribe_user(user_id)

    async def broadcast_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send message to all of user's connections."""
        # Publish to Redis for cross-server delivery
        if self._redis is None:
            self._redis = await get_redis_async()

        await self._redis.publish(
            f"messages:{user_id}",
            json.dumps(message)
        )

    async def _subscribe_user(self, user_id: str):
        """Subscribe to user's Redis channel."""
        if self._redis is None:
            self._redis = await get_redis_async()

        if self._pubsub is None:
            self._pubsub = self._redis.pubsub()

        await self._pubsub.subscribe(f"messages:{user_id}")
        asyncio.create_task(self._listen_for_messages(user_id))

    async def _unsubscribe_user(self, user_id: str):
        """Unsubscribe from user's Redis channel."""
        if self._pubsub:
            await self._pubsub.unsubscribe(f"messages:{user_id}")

    async def _listen_for_messages(self, user_id: str):
        """Listen for messages and forward to WebSocket connections."""
        async for message in self._pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])

                # Send to all user's connections
                if user_id in self._connections:
                    dead_connections = set()

                    for ws in self._connections[user_id]:
                        try:
                            await ws.send_json(data)
                        except Exception:
                            dead_connections.add(ws)

                    # Remove dead connections
                    self._connections[user_id] -= dead_connections


# Singleton
message_realtime = MessageRealtimeService()
```

---

### 🎨 UI/UX Polish (Batch 4)

**Total Estimate:** 10 hours

#### Unified Inbox UX (6 hrs)

| Task                  | Effort | Notes                        |
| --------------------- | ------ | ---------------------------- |
| Channel Indicators    | 1 hr   | Color-coded channel badges   |
| Unread Count Badges   | 1 hr   | Real-time unread count       |
| Quick Reply Templates | 2 hrs  | One-click template insertion |
| Keyboard Shortcuts    | 2 hrs  | j/k navigate, r reply, etc.  |

**Channel Badge Component:**

```tsx
// apps/admin/src/components/inbox/ChannelBadge.tsx
import {
  MessageSquare,
  Phone,
  Mail,
  MessageCircle,
  Instagram,
  Facebook,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const channelConfig = {
  sms: {
    icon: MessageSquare,
    color: 'bg-green-100 text-green-700',
    label: 'SMS',
  },
  voice: {
    icon: Phone,
    color: 'bg-blue-100 text-blue-700',
    label: 'Call',
  },
  email: {
    icon: Mail,
    color: 'bg-purple-100 text-purple-700',
    label: 'Email',
  },
  whatsapp: {
    icon: MessageCircle,
    color: 'bg-emerald-100 text-emerald-700',
    label: 'WhatsApp',
  },
  instagram: {
    icon: Instagram,
    color: 'bg-pink-100 text-pink-700',
    label: 'Instagram',
  },
  facebook: {
    icon: Facebook,
    color: 'bg-indigo-100 text-indigo-700',
    label: 'Facebook',
  },
};

interface ChannelBadgeProps {
  channel: keyof typeof channelConfig;
  showLabel?: boolean;
  size?: 'sm' | 'md';
}

export function ChannelBadge({
  channel,
  showLabel = false,
  size = 'md',
}: ChannelBadgeProps) {
  const config = channelConfig[channel] || channelConfig.email;
  const Icon = config.icon;

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1 rounded-full',
        config.color,
        size === 'sm' ? 'px-1.5 py-0.5' : 'px-2 py-1'
      )}
    >
      <Icon className={cn(size === 'sm' ? 'w-3 h-3' : 'w-4 h-4')} />
      {showLabel && (
        <span
          className={cn(
            'font-medium',
            size === 'sm' ? 'text-xs' : 'text-sm'
          )}
        >
          {config.label}
        </span>
      )}
    </div>
  );
}
```

**Keyboard Shortcuts Hook:**

```tsx
// apps/admin/src/hooks/useInboxShortcuts.ts
import { useEffect, useCallback } from 'react';

interface ShortcutHandlers {
  onNext: () => void;
  onPrevious: () => void;
  onReply: () => void;
  onArchive: () => void;
  onMarkRead: () => void;
  onEscalate: () => void;
}

export function useInboxShortcuts(handlers: ShortcutHandlers) {
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      // Don't trigger if typing in input
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return;
      }

      switch (e.key) {
        case 'j':
          handlers.onNext();
          break;
        case 'k':
          handlers.onPrevious();
          break;
        case 'r':
          e.preventDefault();
          handlers.onReply();
          break;
        case 'e':
          handlers.onArchive();
          break;
        case 'u':
          handlers.onMarkRead();
          break;
        case 'x':
          handlers.onEscalate();
          break;
      }
    },
    [handlers]
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);
}

// Usage:
// const { selectedIndex, setSelectedIndex, messages } = useInboxState();
// useInboxShortcuts({
//   onNext: () => setSelectedIndex(i => Math.min(i + 1, messages.length - 1)),
//   onPrevious: () => setSelectedIndex(i => Math.max(i - 1, 0)),
//   onReply: () => openReplyModal(),
//   ...
// });
```

#### Audio Player UX (4 hrs)

| Task                       | Effort | Notes                           |
| -------------------------- | ------ | ------------------------------- |
| Recording Waveform Display | 2 hrs  | Visual waveform during playback |
| Playback Speed Control     | 1 hr   | 0.5x, 1x, 1.5x, 2x              |
| Transcript Sync            | 1 hr   | Highlight text as audio plays   |

**Audio Player with Waveform:**

```tsx
// apps/admin/src/components/recordings/AudioPlayer.tsx
'use client';

import { useState, useRef, useEffect } from 'react';
import WaveSurfer from 'wavesurfer.js';
import { Play, Pause, SkipBack, SkipForward } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';

interface AudioPlayerProps {
  src: string;
  transcript?: Array<{ start: number; end: number; text: string }>;
  onTimeUpdate?: (time: number) => void;
}

export function AudioPlayer({
  src,
  transcript,
  onTimeUpdate,
}: AudioPlayerProps) {
  const waveformRef = useRef<HTMLDivElement>(null);
  const wavesurfer = useRef<WaveSurfer | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1);

  useEffect(() => {
    if (!waveformRef.current) return;

    wavesurfer.current = WaveSurfer.create({
      container: waveformRef.current,
      waveColor: '#94a3b8',
      progressColor: '#3b82f6',
      cursorColor: '#1e40af',
      barWidth: 2,
      barGap: 1,
      barRadius: 3,
      height: 60,
    });

    wavesurfer.current.load(src);

    wavesurfer.current.on('ready', () => {
      setDuration(wavesurfer.current?.getDuration() || 0);
    });

    wavesurfer.current.on('audioprocess', () => {
      const time = wavesurfer.current?.getCurrentTime() || 0;
      setCurrentTime(time);
      onTimeUpdate?.(time);
    });

    wavesurfer.current.on('play', () => setIsPlaying(true));
    wavesurfer.current.on('pause', () => setIsPlaying(false));

    return () => {
      wavesurfer.current?.destroy();
    };
  }, [src, onTimeUpdate]);

  const togglePlayPause = () => {
    wavesurfer.current?.playPause();
  };

  const skip = (seconds: number) => {
    const current = wavesurfer.current?.getCurrentTime() || 0;
    wavesurfer.current?.seekTo(
      Math.max(0, Math.min(1, (current + seconds) / duration))
    );
  };

  const changeSpeed = () => {
    const speeds = [0.5, 1, 1.5, 2];
    const nextIndex =
      (speeds.indexOf(playbackRate) + 1) % speeds.length;
    const newRate = speeds[nextIndex];
    setPlaybackRate(newRate);
    wavesurfer.current?.setPlaybackRate(newRate);
  };

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <div ref={waveformRef} className="mb-4" />

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => skip(-10)}
          >
            <SkipBack className="w-4 h-4" />
          </Button>
          <Button onClick={togglePlayPause} size="icon">
            {isPlaying ? (
              <Pause className="w-4 h-4" />
            ) : (
              <Play className="w-4 h-4" />
            )}
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => skip(10)}
          >
            <SkipForward className="w-4 h-4" />
          </Button>
        </div>

        <div className="text-sm text-gray-600">
          {formatTime(currentTime)} / {formatTime(duration)}
        </div>

        <Button variant="outline" size="sm" onClick={changeSpeed}>
          {playbackRate}x
        </Button>
      </div>
    </div>
  );
}
```

---

### 🧪 QA & Testing (Batch 4)

**Total Estimate:** 8 hours

#### Multi-Channel Integration Tests (4 hrs)

| Task                    | Effort | Notes                      |
| ----------------------- | ------ | -------------------------- |
| RingCentral Mock Tests  | 1 hr   | Mock RC API responses      |
| WhatsApp Webhook Tests  | 1 hr   | Test all event types       |
| Email Delivery Tests    | 1 hr   | SMTP test suite            |
| Channel Switching Tests | 1 hr   | Customer switches channels |

#### WebSocket Tests (4 hrs)

| Task                        | Effort | Notes                          |
| --------------------------- | ------ | ------------------------------ |
| Connection Management Tests | 2 hrs  | Connect, disconnect, reconnect |
| Message Delivery Tests      | 1 hr   | Real-time message delivery     |
| Load Testing WebSocket      | 1 hr   | 100+ concurrent connections    |

**WebSocket Test Suite:**

```typescript
// tests/integration/websocket.spec.ts
import { test, expect } from '@playwright/test';
import WebSocket from 'ws';

test.describe('WebSocket Real-time Messaging', () => {
  let ws: WebSocket;
  const wsUrl = 'ws://localhost:8000/ws/inbox';

  test.afterEach(() => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.close();
    }
  });

  test('connects successfully with auth token', async () => {
    const token = await getAuthToken();

    ws = new WebSocket(`${wsUrl}?token=${token}`);

    await new Promise<void>((resolve, reject) => {
      ws.onopen = () => resolve();
      ws.onerror = err => reject(err);
      setTimeout(() => reject(new Error('Connection timeout')), 5000);
    });

    expect(ws.readyState).toBe(WebSocket.OPEN);
  });

  test('receives real-time message when new SMS arrives', async ({
    request,
  }) => {
    const token = await getAuthToken();
    ws = new WebSocket(`${wsUrl}?token=${token}`);

    await new Promise<void>(resolve => {
      ws.onopen = () => resolve();
    });

    // Listen for messages
    const messagePromise = new Promise<any>(resolve => {
      ws.onmessage = event => {
        resolve(JSON.parse(event.data));
      };
    });

    // Simulate incoming SMS via webhook
    await request.post('/api/v1/webhooks/ringcentral/sms', {
      data: {
        type: 'sms.received',
        from: '+15551234567',
        to: '+15559876543',
        message: 'Test message',
      },
    });

    // Should receive the message via WebSocket
    const message = await messagePromise;
    expect(message.type).toBe('new_message');
    expect(message.channel).toBe('sms');
    expect(message.content).toBe('Test message');
  });

  test('handles reconnection gracefully', async () => {
    const token = await getAuthToken();
    let connectCount = 0;

    const connect = () => {
      ws = new WebSocket(`${wsUrl}?token=${token}`);
      ws.onopen = () => {
        connectCount++;
        if (connectCount === 1) {
          // Force disconnect after first connection
          ws.close();
        }
      };
      ws.onclose = () => {
        if (connectCount < 2) {
          // Reconnect
          setTimeout(connect, 100);
        }
      };
    };

    connect();

    // Wait for reconnection
    await new Promise(resolve => setTimeout(resolve, 500));

    expect(connectCount).toBe(2);
    expect(ws.readyState).toBe(WebSocket.OPEN);
  });
});

async function getAuthToken(): Promise<string> {
  // Get auth token for WebSocket connection
  const response = await fetch(
    'http://localhost:8000/api/v1/auth/login',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: 'admin@myhibachi.io',
        password: 'testpass',
      }),
    }
  );
  const data = await response.json();
  return data.access_token;
}
```

### Success Criteria

- [ ] SMS sends successfully via RingCentral
- [ ] Voice calls connect and record
- [ ] RC native recording saving to database
- [ ] RC native transcripts retrievable
- [ ] Webhook signature validation working
- [ ] WhatsApp messages send via Meta API
- [ ] Facebook comments/DMs received
- [ ] Instagram comments/DMs received
- [ ] Google Business messages received
- [ ] Email delivery rate >95%
- [ ] No communication failures for 48 hours

**⚡ Performance (Batch 4):**

- [ ] Virtual inbox handles 10,000+ messages without lag
- [ ] Channel lazy loading implemented (channels load on demand)
- [ ] WebSocket real-time messaging working (<100ms latency)
- [ ] Message prefetching working (next page preloaded)
- [ ] Redis Pub/Sub operational for cross-server messaging

**🎨 UI/UX (Batch 4):**

- [ ] Channel badges color-coded and recognizable
- [ ] Unread count badges updating in real-time
- [ ] Quick reply templates working (one-click insert)
- [ ] Keyboard shortcuts documented and functional
- [ ] Audio player waveform displaying correctly
- [ ] Playback speed control working (0.5x, 1x, 1.5x, 2x)
- [ ] Transcript sync highlighting active text

**🧪 QA (Batch 4):**

- [ ] RingCentral mock tests passing
- [ ] WhatsApp webhook tests passing
- [ ] Email delivery tests passing
- [ ] WebSocket connection tests passing
- [ ] WebSocket reconnection tests passing
- [ ] Multi-channel switching tests passing

### Rollback Plan

```bash
FEATURE_RINGCENTRAL=false
FEATURE_META_WHATSAPP=false
# Fallback to email-only communication
```

---

## 🟡 BATCH 5: Advanced AI + Marketing Intelligence (Week 9-10)

**Priority:** MEDIUM **Branch:**
`feature/batch-5-advanced-ai-marketing` **Duration:** 2 weeks
**Prerequisite:** Batch 3 (Core AI) stable

### Components

#### Advanced AI (From `FULL_SELF_LEARNING_IMPLEMENTATION_ROADMAP.md`)

| Component                | Status    | Effort   | Notes                  |
| ------------------------ | --------- | -------- | ---------------------- |
| Emotion Detection        | 🔧 Build  | 4 hours  | Sentiment analysis     |
| EmpathyAgent             | 🔧 Build  | 4 hours  | De-escalation          |
| ComplaintResolutionAgent | 🔧 Build  | 4 hours  | Hospitality psychology |
| AnxietyReliefAgent       | 🔧 Build  | 4 hours  | Reassurance            |
| WinbackAgent             | 🔧 Build  | 4 hours  | Retention              |
| AdminAssistantAgent      | 🔧 Build  | 12 hours | Dashboard queries      |
| CRMWriterAgent           | 🔧 Build  | 8 hours  | Auto-notes             |
| KnowledgeSyncAgent       | 🔧 Build  | 4 hours  | KB updates             |
| RAGRetrievalAgent        | 🔧 Build  | 6 hours  | Doc search             |
| Tool Calling             | 🔧 Enable | 8 hours  | AI creates bookings    |
| RAG/Knowledge Base       | 🔧 Setup  | 6 hours  | Vector search          |
| Feedback Collection      | 🔧 Build  | 4 hours  | Thumbs up/down         |

#### Customer Review System (COMPREHENSIVE - One-Time Link Design)

> **Strategy:** Control WHEN and HOW customers see Google/Yelp links.
> We don't hide external review platforms - we strategically show them
> only to verified, satisfied customers through one-time use review
> links.

##### One-Time Review Link System

```
┌─────────────────────────────────────────────────────────────────────┐
│                    REVIEW LINK LIFECYCLE                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. BOOKING COMPLETED                                               │
│     └─► 24-hour delay (let experience settle)                       │
│                                                                      │
│  2. GENERATE ONE-TIME LINK                                          │
│     └─► UUID: abc123-def456-ghi789                                  │
│     └─► Stored in customer_reviews table                            │
│     └─► Status: 'pending'                                           │
│     └─► Expires: 30 days                                            │
│                                                                      │
│  3. SEND REVIEW REQUEST                                             │
│     └─► Email/SMS with link: /review/abc123-def456-ghi789           │
│     └─► Day 1: Initial request                                      │
│     └─► Day 3: Gentle reminder (if not used)                        │
│     └─► Day 7: Final reminder (if not used)                         │
│                                                                      │
│  4. CUSTOMER CLICKS LINK                                            │
│     └─► Validate UUID exists and status='pending'                   │
│     └─► Load booking context (chef name, date, etc.)                │
│     └─► Show multi-step review flow                                 │
│                                                                      │
│  5. REVIEW SUBMITTED                                                │
│     └─► Status: 'completed'                                         │
│     └─► Link becomes INVALID (one-time use)                         │
│     └─► Route based on rating (see below)                           │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

##### Rating-Based Routing (Backend: `review_service.py`)

| Rating                             | Customer Sees                                | Action                             |
| ---------------------------------- | -------------------------------------------- | ---------------------------------- |
| 😍 **Great** (5 stars)             | "Thank you! Would you share on Google/Yelp?" | Show external links                |
| 😊 **Good** (4 stars)              | "Thank you! Would you share on Google/Yelp?" | Show external links                |
| 😐 **Okay** (3 stars)              | "Thanks! What could we improve?"             | AI follow-up, NO external links    |
| 😔 **Could be better** (1-2 stars) | "We're sorry. Tell us more..."               | Escalation + AI + potential coupon |

##### Multi-Step Review Flow (Frontend)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CUSTOMER REVIEW FLOW                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  STEP 1: EMOJI RATING                                               │
│  ─────────────────────────────────────────────────────────────────  │
│  "How was your hibachi experience with [Chef Name]?"                │
│                                                                      │
│     😍          😊          😐          😔          😢              │
│    Great       Good       Okay      Could be    Very                │
│                                      better     unhappy             │
│                                                                      │
│  STEP 2: CONTEXTUAL FEEDBACK                                        │
│  ─────────────────────────────────────────────────────────────────  │
│  IF rating = Great/Good:                                            │
│    "What made it great?" (optional text)                            │
│    "Would you like to add photos or videos?" (optional)             │
│    • Photos: JPG, PNG, WEBP (max 10MB each, up to 5)                │
│    • Videos: MP4, MOV (max 30 seconds, max 50MB)                    │
│                                                                      │
│  IF rating = Okay:                                                  │
│    "What could we improve?" (text input)                            │
│    → AI follow-up generated                                         │
│                                                                      │
│  IF rating = Could be better/Very unhappy:                          │
│    "We're sorry. Please tell us more..." (required text)            │
│    → Escalation to admin                                            │
│    → AI generates empathetic response                               │
│    → Potential compensation coupon                                  │
│                                                                      │
│  STEP 3: THANK YOU + CONDITIONAL EXTERNAL LINKS                     │
│  ─────────────────────────────────────────────────────────────────  │
│  IF rating = Great/Good:                                            │
│    "Thank you! 🎉 Your feedback means the world to us."             │
│    "Would you share your experience on Google or Yelp?"             │
│    [Google Review Button] [Yelp Review Button]                      │
│    "No thanks, I'm done" (small link)                               │
│                                                                      │
│  IF rating = Okay/Could be better:                                  │
│    "Thank you for your feedback. We'll use it to improve."          │
│    "A team member will reach out shortly."                          │
│    (NO external review links shown)                                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

##### Database Schema (One-Time Links)

```sql
-- customer_reviews table (add/modify columns)
ALTER TABLE core.customer_reviews ADD COLUMN IF NOT EXISTS
    review_uuid UUID UNIQUE DEFAULT gen_random_uuid();  -- The one-time link token

ALTER TABLE core.customer_reviews ADD COLUMN IF NOT EXISTS
    status VARCHAR(20) DEFAULT 'pending';  -- pending, completed, expired

ALTER TABLE core.customer_reviews ADD COLUMN IF NOT EXISTS
    link_expires_at TIMESTAMP;  -- 30 days from creation

ALTER TABLE core.customer_reviews ADD COLUMN IF NOT EXISTS
    reminder_count INTEGER DEFAULT 0;  -- 0, 1, 2, 3 (max)

ALTER TABLE core.customer_reviews ADD COLUMN IF NOT EXISTS
    last_reminder_at TIMESTAMP;

ALTER TABLE core.customer_reviews ADD COLUMN IF NOT EXISTS
    external_review_clicked VARCHAR(20);  -- 'google', 'yelp', null

-- Status values:
-- 'pending' = Link sent, not yet used
-- 'completed' = Review submitted
-- 'expired' = 30 days passed without use
-- 'cancelled' = Admin cancelled
```

##### Backend API Endpoints

| Endpoint                                     | Method | Purpose                                       |
| -------------------------------------------- | ------ | --------------------------------------------- |
| `/api/v1/reviews/generate-link/{booking_id}` | POST   | Generate one-time review link (internal/cron) |
| `/api/v1/reviews/validate/{uuid}`            | GET    | Validate link and get booking context         |
| `/api/v1/reviews/submit/{uuid}`              | POST   | Submit review (marks link as used)            |
| `/api/v1/reviews/send-reminder/{uuid}`       | POST   | Send reminder email/SMS                       |
| `/api/v1/reviews/analytics`                  | GET    | Review analytics dashboard data               |
| `/api/v1/reviews/admin/list`                 | GET    | Admin: List all reviews                       |
| `/api/v1/reviews/admin/{id}/moderate`        | PATCH  | Admin: Approve/reject review                  |

##### Automated Review Request Flow

```python
# Cron job: runs daily at 10 AM
async def process_review_requests():
    # 1. Generate links for bookings completed 24+ hours ago
    recent_bookings = await get_completed_bookings_without_review_link(
        completed_after=now - timedelta(hours=24),
        completed_before=now - timedelta(hours=48)
    )
    for booking in recent_bookings:
        await generate_and_send_review_link(booking)

    # 2. Send Day 3 reminders
    day3_pending = await get_pending_reviews(
        created_after=now - timedelta(days=4),
        created_before=now - timedelta(days=3),
        reminder_count=0
    )
    for review in day3_pending:
        await send_reminder(review, reminder_number=1)

    # 3. Send Day 7 final reminders
    day7_pending = await get_pending_reviews(
        created_after=now - timedelta(days=8),
        created_before=now - timedelta(days=7),
        reminder_count=1
    )
    for review in day7_pending:
        await send_reminder(review, reminder_number=2)

    # 4. Expire old links (30 days)
    await expire_old_review_links(older_than=timedelta(days=30))
```

##### Review Analytics Dashboard (Admin)

| Metric                     | Description                                         |
| -------------------------- | --------------------------------------------------- |
| **Response Rate**          | % of review links that were used                    |
| **Rating Distribution**    | Great/Good/Okay/Could be better breakdown           |
| **External Conversion**    | % of Great/Good reviews that clicked Google/Yelp    |
| **Reminder Effectiveness** | Which reminder day has best conversion              |
| **Chef Performance**       | Average rating per chef                             |
| **Time to Response**       | Average days between link sent and review submitted |
| **Escalation Rate**        | % of reviews that triggered escalation              |

##### Dedicated /reviews Page (Customer Site)

```
URL: myhibachi.com/reviews

┌─────────────────────────────────────────────────────────────────────┐
│                    PUBLIC REVIEWS PAGE                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  HERO SECTION                                                       │
│  ─────────────────────────────────────────────────────────────────  │
│  "What Our Customers Say"                                           │
│  ⭐⭐⭐⭐⭐ 4.9 average from 500+ reviews                           │
│                                                                      │
│  CURATED INTERNAL REVIEWS                                           │
│  ─────────────────────────────────────────────────────────────────  │
│  [Review Card with photo, text, chef name, date]                    │
│  [Review Card with photo, text, chef name, date]                    │
│  [Review Card with photo, text, chef name, date]                    │
│  ... (moderated reviews only)                                       │
│                                                                      │
│  EXTERNAL REVIEW LINKS (Bottom of page)                             │
│  ─────────────────────────────────────────────────────────────────  │
│  "See us on:"                                                       │
│  [Google Reviews Badge] [Yelp Badge]                                │
│  (Links open in new tab)                                            │
│                                                                      │
│  NOTE: Google/Yelp links are NOT hidden. They're just placed        │
│  strategically at the bottom of the page, after showing our         │
│  curated reviews first.                                             │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

##### Implementation Checklist

| Component                            | Status    | Effort        | Priority |
| ------------------------------------ | --------- | ------------- | -------- |
| One-time link generation API         | 🔧 Build  | 4 hours       | P0       |
| Link validation API                  | 🔧 Build  | 2 hours       | P0       |
| Review submission API (with routing) | ✅ Exists | -             | -        |
| Multi-step review form (frontend)    | 🔧 Build  | 8 hours       | P0       |
| 24-hour delay cron job               | 🔧 Build  | 2 hours       | P0       |
| Reminder sequence (Day 1,3,7)        | 🔧 Build  | 4 hours       | P0       |
| Review analytics dashboard           | 🔧 Build  | 6 hours       | P1       |
| Public /reviews page                 | 🔧 Build  | 4 hours       | P1       |
| Photo/video upload integration       | 🔧 Build  | 3 hours       | P1       |
| Admin moderation UI                  | 🔧 Build  | 4 hours       | P1       |
| Chef public profile with reviews     | 🔧 Build  | 4 hours       | P2       |
| **Total New Work**                   |           | **~40 hours** |          |

#### Marketing Intelligence (Google Integration - FULL Scope)

| Component              | Status   | Notes                       |
| ---------------------- | -------- | --------------------------- |
| Google Search Console  | 🔧 Build | SEO monitoring              |
| Google Ads API         | 🔧 Build | Full management             |
| ├─ Performance Metrics |          | ROAS, CPA, CTR              |
| ├─ Keyword Analysis    |          | Quality scores, bids        |
| ├─ Location Breakdown  |          | City-level performance      |
| ├─ Device Analysis     |          | Mobile/Desktop/Tablet       |
| ├─ Time Analysis       |          | Best hours/days             |
| ├─ Search Terms Report |          | Actual queries              |
| ├─ Budget Pacing       |          | Daily spend tracking        |
| ├─ A/B Test Tracking   |          | Ad copy experiments         |
| └─ Automated Alerts    |          | CPA threshold notifications |
| Google Analytics 4     | 🔧 Build | Traffic, conversions        |
| AI Recommendations     | 🔧 Build | OpenAI-powered insights     |
| **Total Routes**       |          | **~50**                     |

### Feature Flags

```env
# Review System (One-Time Link)
FEATURE_CUSTOMER_REVIEWS=true
FEATURE_REVIEW_ONE_TIME_LINKS=true
FEATURE_REVIEW_REMINDERS=true
FEATURE_REVIEW_ANALYTICS=true
FEATURE_REVIEW_MEDIA_UPLOAD=true  # Photos + Videos (30s max)

# Advanced AI
FEATURE_ADVANCED_AI=true
FEATURE_EMOTION_DETECTION=true
FEATURE_PSYCHOLOGY_AGENTS=true
FEATURE_TOOL_CALLING=true
FEATURE_RAG=true
FEATURE_FEEDBACK_COLLECTION=true

# Marketing Intelligence
FEATURE_MARKETING_INTELLIGENCE=true
FEATURE_GOOGLE_SEARCH_CONSOLE=true
FEATURE_GOOGLE_ADS=true
FEATURE_GOOGLE_ANALYTICS=true
```

### Database Setup (Batch 5)

```sql
-- ============================================
-- CUSTOMER REVIEWS (One-Time Link System)
-- ============================================

-- Add one-time link columns to customer_reviews
ALTER TABLE core.customer_reviews ADD COLUMN IF NOT EXISTS
    review_uuid UUID UNIQUE DEFAULT gen_random_uuid();

ALTER TABLE core.customer_reviews ADD COLUMN IF NOT EXISTS
    status VARCHAR(20) DEFAULT 'pending';
    -- Values: 'pending', 'completed', 'expired', 'cancelled'

ALTER TABLE core.customer_reviews ADD COLUMN IF NOT EXISTS
    link_expires_at TIMESTAMP;

ALTER TABLE core.customer_reviews ADD COLUMN IF NOT EXISTS
    reminder_count INTEGER DEFAULT 0;

ALTER TABLE core.customer_reviews ADD COLUMN IF NOT EXISTS
    last_reminder_at TIMESTAMP;

ALTER TABLE core.customer_reviews ADD COLUMN IF NOT EXISTS
    external_review_clicked VARCHAR(20);
    -- Values: 'google', 'yelp', null

-- Index for fast UUID lookup
CREATE INDEX IF NOT EXISTS idx_customer_reviews_uuid
    ON core.customer_reviews(review_uuid);

-- Index for reminder cron job
CREATE INDEX IF NOT EXISTS idx_customer_reviews_status_reminder
    ON core.customer_reviews(status, reminder_count, created_at);
```

```bash
# Run review system migration
psql -d myhibachi -f apps/backend/migrations/007_add_customer_reviews.sql

# Vector database for RAG (choose one):
# Option A: Pinecone (recommended for production)
pip install pinecone-client

# Option B: Qdrant (self-hosted alternative)
docker run -p 6333:6333 qdrant/qdrant

# Option C: pgvector (already enabled in Batch 3)
# Just add embedding column to kb_chunks
```

### Frontend Tasks (Batch 5)

| App               | Component                    | Status   | Effort | Notes                                |
| ----------------- | ---------------------------- | -------- | ------ | ------------------------------------ |
| **Customer Site** | Multi-step review form       | 🔧 Build | 8 hrs  | Emoji picker → feedback → thank you  |
| **Customer Site** | Review link landing page     | 🔧 Build | 4 hrs  | `/review/[uuid]` route               |
| **Customer Site** | Public /reviews page         | 🔧 Build | 4 hrs  | Curated reviews + Google/Yelp badges |
| **Customer Site** | Photo/video upload in review | 🔧 Build | 3 hrs  | S3/Cloudinary, max 30s video         |
| **Customer Site** | Chef profiles with reviews   | 🔧 Build | 4 hrs  | Public chef pages                    |
| **Admin Panel**   | Review moderation UI         | 🔧 Build | 4 hrs  | Approve/reject reviews               |
| **Admin Panel**   | Review analytics dashboard   | 🔧 Build | 6 hrs  | Response rate, ratings, conversions  |
| **Admin Panel**   | Search Console dashboard     | 🔧 Build | 4 hrs  | SEO metrics                          |
| **Admin Panel**   | Google Ads dashboard         | 🔧 Build | 8 hrs  | Full ad performance                  |
| **Admin Panel**   | Analytics dashboard          | 🔧 Build | 4 hrs  | GA4 metrics                          |
| **Admin Panel**   | AI recommendations           | 🔧 Build | 4 hrs  | Marketing insights                   |
| **Admin Panel**   | Emotion analytics            | 🔧 Build | 4 hrs  | Customer sentiment                   |
| **Admin Panel**   | Feedback viewer              | 🔧 Build | 2 hrs  | Thumbs up/down results               |

---

### ⚡ Performance Optimization (Batch 5)

**Total Estimate:** 12 hours

#### Service Worker & PWA Foundation (4 hrs)

| Task                  | Effort | Notes                      |
| --------------------- | ------ | -------------------------- |
| Service Worker Setup  | 2 hrs  | Cache API, offline support |
| PWA Manifest          | 1 hr   | Install prompt, icons      |
| Offline Booking Draft | 1 hr   | Save drafts offline        |

**Service Worker Configuration:**

```typescript
// apps/customer/public/sw.js
const CACHE_NAME = 'myhibachi-v1';
const OFFLINE_URL = '/offline';

// Assets to cache immediately
const PRECACHE_ASSETS = [
  '/',
  '/BookUs',
  '/contact',
  '/offline',
  '/manifest.json',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
];

// Cache strategies
const CACHE_STRATEGIES = {
  // Cache first, then network (static assets)
  cacheFirst: [
    /\/_next\/static\//,
    /\.(?:png|jpg|jpeg|svg|gif|webp|woff2?)$/,
  ],
  // Network first, fallback to cache (API)
  networkFirst: [/\/api\//],
  // Stale while revalidate (HTML pages)
  staleWhileRevalidate: [/^\/(?!api)/],
};

// Install event - precache assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(PRECACHE_ASSETS);
    })
  );
  self.skipWaiting();
});

// Activate event - cleanup old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames
          .filter(name => name !== CACHE_NAME)
          .map(name => caches.delete(name))
      );
    })
  );
  self.clients.claim();
});

// Fetch event - apply caching strategies
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') return;

  // Determine strategy
  if (
    CACHE_STRATEGIES.cacheFirst.some(pattern =>
      pattern.test(url.pathname)
    )
  ) {
    event.respondWith(cacheFirst(request));
  } else if (
    CACHE_STRATEGIES.networkFirst.some(pattern =>
      pattern.test(url.pathname)
    )
  ) {
    event.respondWith(networkFirst(request));
  } else {
    event.respondWith(staleWhileRevalidate(request));
  }
});

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;

  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    return caches.match(OFFLINE_URL);
  }
}

async function networkFirst(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    return caches.match(request);
  }
}

async function staleWhileRevalidate(request) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(request);

  const fetchPromise = fetch(request)
    .then(response => {
      if (response.ok) {
        cache.put(request, response.clone());
      }
      return response;
    })
    .catch(() => cached);

  return cached || fetchPromise;
}
```

**PWA Manifest:**

```json
// apps/customer/public/manifest.json
{
  "name": "My Hibachi",
  "short_name": "MyHibachi",
  "description": "Book your private hibachi experience",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#dc2626",
  "icons": [
    {
      "src": "/icons/icon-72.png",
      "sizes": "72x72",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ],
  "screenshots": [
    {
      "src": "/screenshots/home.png",
      "sizes": "1280x720",
      "type": "image/png",
      "form_factor": "wide"
    },
    {
      "src": "/screenshots/booking-mobile.png",
      "sizes": "390x844",
      "type": "image/png",
      "form_factor": "narrow"
    }
  ],
  "shortcuts": [
    {
      "name": "Book Now",
      "url": "/BookUs",
      "icons": [
        { "src": "/icons/book-shortcut.png", "sizes": "96x96" }
      ]
    },
    {
      "name": "Contact Us",
      "url": "/contact",
      "icons": [
        { "src": "/icons/contact-shortcut.png", "sizes": "96x96" }
      ]
    }
  ]
}
```

#### Image Optimization Pipeline (4 hrs)

| Task                       | Effort | Notes                           |
| -------------------------- | ------ | ------------------------------- |
| Image CDN Configuration    | 2 hrs  | Cloudflare Images or Cloudinary |
| Responsive Image Component | 1 hr   | srcset for all viewports        |
| Lazy Image Loading         | 1 hr   | IntersectionObserver            |

**Optimized Image Component:**

```tsx
// apps/customer/src/components/ui/OptimizedImage.tsx
'use client';

import { useState } from 'react';
import Image from 'next/image';
import { cn } from '@/lib/utils';
import { Skeleton } from '@/components/ui/skeleton';

interface OptimizedImageProps {
  src: string;
  alt: string;
  width: number;
  height: number;
  priority?: boolean;
  className?: string;
  sizes?: string;
}

export function OptimizedImage({
  src,
  alt,
  width,
  height,
  priority = false,
  className,
  sizes = '(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw',
}: OptimizedImageProps) {
  const [isLoading, setIsLoading] = useState(true);

  // Transform src for CDN if needed
  const optimizedSrc = transformImageSrc(src);

  return (
    <div className={cn('relative overflow-hidden', className)}>
      {isLoading && (
        <Skeleton
          className="absolute inset-0"
          style={{ aspectRatio: `${width}/${height}` }}
        />
      )}
      <Image
        src={optimizedSrc}
        alt={alt}
        width={width}
        height={height}
        priority={priority}
        sizes={sizes}
        className={cn(
          'transition-opacity duration-300',
          isLoading ? 'opacity-0' : 'opacity-100'
        )}
        onLoad={() => setIsLoading(false)}
        placeholder="blur"
        blurDataURL={generateBlurDataURL(width, height)}
      />
    </div>
  );
}

function transformImageSrc(src: string): string {
  // If already using CDN, return as-is
  if (
    src.includes('cloudinary.com') ||
    src.includes('imagedelivery.net')
  ) {
    return src;
  }

  // Transform local images to use CDN
  if (src.startsWith('/images/')) {
    return `${process.env.NEXT_PUBLIC_CDN_URL}${src}`;
  }

  return src;
}

function generateBlurDataURL(width: number, height: number): string {
  // Generate tiny placeholder
  const canvas =
    typeof window !== 'undefined'
      ? document.createElement('canvas')
      : null;
  if (!canvas) return '';

  canvas.width = 10;
  canvas.height = Math.round(10 * (height / width));

  const ctx = canvas.getContext('2d');
  if (ctx) {
    ctx.fillStyle = '#f3f4f6';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }

  return canvas.toDataURL();
}
```

#### Vector Search Optimization (4 hrs)

| Task                    | Effort | Notes                    |
| ----------------------- | ------ | ------------------------ |
| HNSW Index Tuning       | 2 hrs  | Optimize ef_construction |
| Vector Batch Processing | 1 hr   | Bulk embed updates       |
| Search Result Caching   | 1 hr   | Cache frequent queries   |

**Vector Search Service Optimization:**

```python
# apps/backend/src/services/ai/vector_search.py
from typing import List, Dict, Any, Optional
import numpy as np
from dataclasses import dataclass

from src.core.database import SessionLocal
from src.core.redis import redis_client


@dataclass
class SearchResult:
    id: str
    content: str
    score: float
    metadata: Dict[str, Any]


class OptimizedVectorSearch:
    """Optimized vector search with caching and batching."""

    def __init__(self, cache_ttl: int = 3600):
        self.cache_ttl = cache_ttl
        self._search_cache_prefix = "vector:search:"

    async def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
    ) -> List[SearchResult]:
        """
        Search for similar vectors with optional caching.

        Uses HNSW index for fast approximate nearest neighbor search.
        """
        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(query_embedding, top_k, filter_metadata)
            cached = redis_client.get(cache_key)
            if cached:
                return [SearchResult(**r) for r in json.loads(cached)]

        # Perform search using pgvector with HNSW
        results = await self._execute_search(query_embedding, top_k, filter_metadata)

        # Cache results
        if use_cache and results:
            redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps([r.__dict__ for r in results])
            )

        return results

    async def _execute_search(
        self,
        query_embedding: np.ndarray,
        top_k: int,
        filter_metadata: Optional[Dict[str, Any]],
    ) -> List[SearchResult]:
        """Execute vector search against pgvector."""
        embedding_str = f"[{','.join(str(x) for x in query_embedding)}]"

        # Build filter clause
        filter_clause = ""
        params = {"embedding": embedding_str, "top_k": top_k}

        if filter_metadata:
            conditions = []
            for i, (key, value) in enumerate(filter_metadata.items()):
                conditions.append(f"metadata->>'{key}' = :filter_{i}")
                params[f"filter_{i}"] = str(value)
            filter_clause = "WHERE " + " AND ".join(conditions)

        query = f"""
            SELECT
                id,
                content,
                metadata,
                1 - (embedding <=> :embedding::vector) as similarity
            FROM ai.knowledge_embeddings
            {filter_clause}
            ORDER BY embedding <=> :embedding::vector
            LIMIT :top_k
        """

        async with SessionLocal() as db:
            result = await db.execute(query, params)
            rows = result.fetchall()

        return [
            SearchResult(
                id=row.id,
                content=row.content,
                score=row.similarity,
                metadata=row.metadata,
            )
            for row in rows
        ]

    async def batch_embed_and_store(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        batch_size: int = 100,
    ):
        """Batch process embeddings for efficiency."""
        from src.services.ai.embedding_service import EmbeddingService

        embedding_service = EmbeddingService()

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_meta = metadatas[i:i + batch_size]

            # Generate embeddings in batch
            embeddings = await embedding_service.generate_batch(batch_texts)

            # Store in database
            await self._store_batch(embeddings, batch_texts, batch_meta)

    async def _store_batch(
        self,
        embeddings: List[np.ndarray],
        texts: List[str],
        metadatas: List[Dict[str, Any]],
    ):
        """Store batch of embeddings."""
        async with SessionLocal() as db:
            for embedding, text, metadata in zip(embeddings, texts, metadatas):
                await db.execute(
                    """
                    INSERT INTO ai.knowledge_embeddings (content, embedding, metadata)
                    VALUES (:content, :embedding::vector, :metadata::jsonb)
                    """,
                    {
                        "content": text,
                        "embedding": f"[{','.join(str(x) for x in embedding)}]",
                        "metadata": json.dumps(metadata),
                    }
                )
            await db.commit()

    def _get_cache_key(
        self,
        embedding: np.ndarray,
        top_k: int,
        filter_metadata: Optional[Dict[str, Any]],
    ) -> str:
        """Generate cache key from search parameters."""
        import hashlib

        # Hash embedding (first 8 floats for speed)
        emb_hash = hashlib.md5(embedding[:8].tobytes()).hexdigest()[:8]

        # Hash filters
        filter_hash = ""
        if filter_metadata:
            filter_hash = hashlib.md5(
                json.dumps(filter_metadata, sort_keys=True).encode()
            ).hexdigest()[:8]

        return f"{self._search_cache_prefix}{emb_hash}:{top_k}:{filter_hash}"
```

---

### 🎨 UI/UX Polish (Batch 5)

**Total Estimate:** 12 hours

#### Animations & Transitions (4 hrs)

| Task               | Effort | Notes                      |
| ------------------ | ------ | -------------------------- |
| Page Transitions   | 2 hrs  | Smooth route changes       |
| Micro-interactions | 1 hr   | Button hover, focus states |
| Loading Animations | 1 hr   | Branded loading spinners   |

**Page Transition Component:**

```tsx
// apps/customer/src/components/layout/PageTransition.tsx
'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { usePathname } from 'next/navigation';

interface PageTransitionProps {
  children: React.ReactNode;
}

const variants = {
  hidden: { opacity: 0, y: 20 },
  enter: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 },
};

export function PageTransition({ children }: PageTransitionProps) {
  const pathname = usePathname();

  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={pathname}
        variants={variants}
        initial="hidden"
        animate="enter"
        exit="exit"
        transition={{ duration: 0.3, ease: 'easeInOut' }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}
```

**Branded Loading Spinner:**

```tsx
// apps/customer/src/components/ui/LoadingSpinner.tsx
'use client';

import { motion } from 'framer-motion';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function LoadingSpinner({
  size = 'md',
  className,
}: LoadingSpinnerProps) {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  return (
    <div className={`flex items-center justify-center ${className}`}>
      <motion.div
        className={`${sizes[size]} relative`}
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
      >
        {/* Hibachi flame-inspired spinner */}
        <svg viewBox="0 0 24 24" className="w-full h-full">
          <motion.path
            d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeDasharray="40 60"
            className="text-primary"
          />
          <motion.circle
            cx="12"
            cy="12"
            r="3"
            fill="currentColor"
            className="text-primary/30"
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 0.5, repeat: Infinity }}
          />
        </svg>
      </motion.div>
    </div>
  );
}
```

#### Review Form UX (4 hrs)

| Task                   | Effort | Notes                        |
| ---------------------- | ------ | ---------------------------- |
| Emoji Rating Animation | 1 hr   | Playful emoji selection      |
| Photo Upload Preview   | 2 hrs  | Drag-drop, preview, crop     |
| Video Upload Progress  | 1 hr   | Upload progress with preview |

**Emoji Rating Component:**

```tsx
// apps/customer/src/components/reviews/EmojiRating.tsx
'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useState } from 'react';

interface EmojiRatingProps {
  onSelect: (rating: number) => void;
  selected?: number;
}

const emojis = [
  { emoji: '😢', label: 'Very unhappy', rating: 1 },
  { emoji: '😔', label: 'Could be better', rating: 2 },
  { emoji: '😐', label: 'Okay', rating: 3 },
  { emoji: '😊', label: 'Good', rating: 4 },
  { emoji: '😍', label: 'Great!', rating: 5 },
];

export function EmojiRating({
  onSelect,
  selected,
}: EmojiRatingProps) {
  const [hovering, setHovering] = useState<number | null>(null);

  return (
    <div className="flex justify-center gap-4">
      {emojis.map(({ emoji, label, rating }) => (
        <motion.button
          key={rating}
          onClick={() => onSelect(rating)}
          onMouseEnter={() => setHovering(rating)}
          onMouseLeave={() => setHovering(null)}
          whileHover={{ scale: 1.2 }}
          whileTap={{ scale: 0.9 }}
          className={`relative p-2 rounded-full transition-colors ${
            selected === rating
              ? 'bg-primary/10 ring-2 ring-primary'
              : 'hover:bg-gray-100'
          }`}
        >
          <span className="text-4xl">{emoji}</span>

          <AnimatePresence>
            {(hovering === rating || selected === rating) && (
              <motion.span
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 5 }}
                className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-xs font-medium whitespace-nowrap text-gray-600"
              >
                {label}
              </motion.span>
            )}
          </AnimatePresence>
        </motion.button>
      ))}
    </div>
  );
}
```

#### Dark Mode Foundation (4 hrs)

| Task                        | Effort | Notes                 |
| --------------------------- | ------ | --------------------- |
| CSS Variables Setup         | 2 hrs  | Theme color variables |
| Component Dark Variants     | 1 hr   | Update all components |
| System Preference Detection | 1 hr   | Respect OS preference |

**Theme Provider:**

```tsx
// apps/customer/src/components/providers/ThemeProvider.tsx
'use client';

import {
  createContext,
  useContext,
  useEffect,
  useState,
} from 'react';

type Theme = 'light' | 'dark' | 'system';

interface ThemeContextValue {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  resolvedTheme: 'light' | 'dark';
}

const ThemeContext = createContext<ThemeContextValue | undefined>(
  undefined
);

export function ThemeProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [theme, setTheme] = useState<Theme>('system');
  const [resolvedTheme, setResolvedTheme] = useState<
    'light' | 'dark'
  >('light');

  useEffect(() => {
    // Load from localStorage
    const stored = localStorage.getItem('theme') as Theme | null;
    if (stored) setTheme(stored);
  }, []);

  useEffect(() => {
    const root = document.documentElement;

    const updateTheme = () => {
      let resolved: 'light' | 'dark';

      if (theme === 'system') {
        resolved = window.matchMedia('(prefers-color-scheme: dark)')
          .matches
          ? 'dark'
          : 'light';
      } else {
        resolved = theme;
      }

      setResolvedTheme(resolved);
      root.classList.remove('light', 'dark');
      root.classList.add(resolved);
    };

    updateTheme();

    // Listen for system preference changes
    const mediaQuery = window.matchMedia(
      '(prefers-color-scheme: dark)'
    );
    mediaQuery.addEventListener('change', updateTheme);

    return () =>
      mediaQuery.removeEventListener('change', updateTheme);
  }, [theme]);

  const handleSetTheme = (newTheme: Theme) => {
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
  };

  return (
    <ThemeContext.Provider
      value={{ theme, setTheme: handleSetTheme, resolvedTheme }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
}
```

**CSS Variables:**

```css
/* apps/customer/src/app/globals.css */
:root {
  /* Light mode (default) */
  --background: 0 0% 100%;
  --foreground: 222.2 47.4% 11.2%;
  --card: 0 0% 100%;
  --card-foreground: 222.2 47.4% 11.2%;
  --primary: 0 72% 51%;
  --primary-foreground: 0 0% 100%;
  --secondary: 210 40% 96%;
  --secondary-foreground: 222.2 47.4% 11.2%;
  --muted: 210 40% 96%;
  --muted-foreground: 215.4 16.3% 46.9%;
  --accent: 210 40% 96%;
  --accent-foreground: 222.2 47.4% 11.2%;
  --border: 214.3 31.8% 91.4%;
  --input: 214.3 31.8% 91.4%;
  --ring: 0 72% 51%;
}

.dark {
  /* Dark mode */
  --background: 224 71% 4%;
  --foreground: 213 31% 91%;
  --card: 224 71% 4%;
  --card-foreground: 213 31% 91%;
  --primary: 0 72% 51%;
  --primary-foreground: 0 0% 100%;
  --secondary: 222.2 47.4% 11.2%;
  --secondary-foreground: 210 40% 98%;
  --muted: 223 47% 11%;
  --muted-foreground: 215.4 16.3% 56.9%;
  --accent: 216 34% 17%;
  --accent-foreground: 210 40% 98%;
  --border: 216 34% 17%;
  --input: 216 34% 17%;
  --ring: 0 72% 51%;
}
```

---

### 🧪 QA & Testing (Batch 5)

**Total Estimate:** 10 hours

#### Review System E2E Tests (4 hrs)

| Task                 | Effort | Notes                    |
| -------------------- | ------ | ------------------------ |
| One-Time Link Tests  | 2 hrs  | Generate, use, expire    |
| Rating Routing Tests | 1 hr   | Verify routing by rating |
| Media Upload Tests   | 1 hr   | Photo/video upload flow  |

**Review System Test Suite:**

```typescript
// tests/e2e/reviews.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Review System', () => {
  let reviewLink: string;

  test.beforeAll(async ({ request }) => {
    // Generate a review link for testing
    const response = await request.post(
      '/api/v1/reviews/generate-link/test-booking-123'
    );
    const data = await response.json();
    reviewLink = data.link;
  });

  test('one-time review link works', async ({ page }) => {
    await page.goto(reviewLink);

    // Should show review form
    await expect(
      page.locator('[data-testid="emoji-rating"]')
    ).toBeVisible();
    await expect(
      page.locator('text=How was your hibachi experience')
    ).toBeVisible();
  });

  test('great rating shows external review links', async ({
    page,
  }) => {
    await page.goto(reviewLink);

    // Select great rating (5 stars)
    await page.click('[data-testid="emoji-5"]');

    // Submit review
    await page.fill(
      '[data-testid="feedback-text"]',
      'Amazing experience!'
    );
    await page.click('[data-testid="submit-review"]');

    // Should show Google/Yelp buttons
    await expect(
      page.locator('[data-testid="google-review-button"]')
    ).toBeVisible();
    await expect(
      page.locator('[data-testid="yelp-review-button"]')
    ).toBeVisible();
  });

  test('okay rating does NOT show external links', async ({
    page,
    request,
  }) => {
    // Get fresh link
    const res = await request.post(
      '/api/v1/reviews/generate-link/test-booking-456'
    );
    const { link } = await res.json();

    await page.goto(link);

    // Select okay rating (3 stars)
    await page.click('[data-testid="emoji-3"]');

    // Fill required feedback
    await page.fill(
      '[data-testid="improvement-text"]',
      'Could improve timing'
    );
    await page.click('[data-testid="submit-review"]');

    // Should NOT show external review buttons
    await expect(
      page.locator('[data-testid="google-review-button"]')
    ).not.toBeVisible();
    await expect(
      page.locator('[data-testid="yelp-review-button"]')
    ).not.toBeVisible();

    // Should show thank you with follow-up message
    await expect(
      page.locator("text=We'll use it to improve")
    ).toBeVisible();
  });

  test('used link cannot be reused', async ({ page, request }) => {
    // Get and use a link
    const res = await request.post(
      '/api/v1/reviews/generate-link/test-booking-789'
    );
    const { link } = await res.json();

    // Use the link
    await page.goto(link);
    await page.click('[data-testid="emoji-5"]');
    await page.click('[data-testid="submit-review"]');

    // Try to use again
    await page.goto(link);

    // Should show link expired/used message
    await expect(
      page.locator('text=link has already been used')
    ).toBeVisible();
  });

  test('photo upload works', async ({ page, request }) => {
    const res = await request.post(
      '/api/v1/reviews/generate-link/test-booking-photo'
    );
    const { link } = await res.json();

    await page.goto(link);
    await page.click('[data-testid="emoji-5"]');

    // Upload photo
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.click('[data-testid="upload-photo-button"]');
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles('./tests/fixtures/test-image.jpg');

    // Should show preview
    await expect(
      page.locator('[data-testid="photo-preview"]')
    ).toBeVisible();

    // Submit
    await page.click('[data-testid="submit-review"]');
    await expect(
      page.locator('[data-testid="review-success"]')
    ).toBeVisible();
  });
});
```

#### PWA Tests (3 hrs)

| Task                 | Effort | Notes                 |
| -------------------- | ------ | --------------------- |
| Service Worker Tests | 1 hr   | Registration, caching |
| Offline Mode Tests   | 1 hr   | Offline page shows    |
| Install Prompt Tests | 1 hr   | PWA install flow      |

#### Performance Tests (3 hrs)

| Task                     | Effort | Notes                  |
| ------------------------ | ------ | ---------------------- |
| Image Loading Tests      | 1 hr   | Lazy load verification |
| Animation Performance    | 1 hr   | No jank on transitions |
| Vector Search Benchmarks | 1 hr   | <100ms for 50K vectors |

### Success Criteria

**Review System (One-Time Link):**

- [ ] One-time review links generated 24 hours after booking
      completion
- [ ] Links expire after use (status = 'completed')
- [ ] Reminder sequence working (Day 1, 3, 7)
- [ ] Multi-step review form functional (emoji → feedback → thank you)
- [ ] Rating-based routing working:
  - [ ] Great/Good → Shows Google/Yelp buttons
  - [ ] Okay → AI follow-up, no external links
  - [ ] Could be better → Escalation + AI + potential coupon
- [ ] Photo/video upload functional (images + videos up to 30 seconds)
- [ ] Review analytics dashboard showing metrics
- [ ] Public /reviews page displaying curated reviews
- [ ] Admin moderation UI functional

**Advanced AI:**

- [ ] Emotion detection working (85%+ accuracy)
- [ ] Psychology agents responding appropriately
- [ ] Tool calling creates bookings correctly
- [ ] RAG retrieves relevant documents
- [ ] Feedback collection functional

**Marketing Intelligence:**

- [ ] Google Search Console dashboard showing data
- [ ] Google Ads dashboard showing all metrics (ROAS, CPA, keywords,
      etc.)
- [ ] AI recommendations generating actionable insights
- [ ] Budget pacing alerts working
- [ ] A/B test tracking functional
- [ ] Automated CPA alerts triggering

**Vector DB Scaling Foundation (Batch 5):**

- [ ] Vector DB abstraction layer implemented (swap
      pgvector↔Pinecone↔Qdrant)
- [ ] HNSW index created for embeddings (if >10K vectors)
- [ ] Embedding batch processing implemented
- [ ] Vector search performance <100ms for 50K vectors

**⚡ Performance (Batch 5):**

- [ ] Service Worker registered and caching assets
- [ ] PWA manifest valid (Lighthouse PWA audit passing)
- [ ] Offline page showing when network unavailable
- [ ] Images lazy-loaded with blur placeholder
- [ ] Image CDN serving optimized formats (WebP)
- [ ] Vector search <100ms (p95) for 50K vectors

**🎨 UI/UX (Batch 5):**

- [ ] Page transitions smooth (no jank)
- [ ] Emoji rating animation playful and responsive
- [ ] Photo upload with drag-drop preview
- [ ] Video upload with progress indicator
- [ ] Dark mode foundation CSS variables set up
- [ ] Theme toggle respects system preference
- [ ] Branded loading spinner implemented

**🧪 QA (Batch 5):**

- [ ] One-time link E2E tests passing
- [ ] Rating routing tests passing
- [ ] Photo/video upload tests passing
- [ ] Service worker tests passing
- [ ] Offline mode tests passing
- [ ] Animation performance tests passing (no dropped frames)

### Rollback Plan

```bash
FEATURE_ADVANCED_AI=false
FEATURE_MARKETING_INTELLIGENCE=false
# Fallback to Batch 3 basic AI
```

---

## 🟡 BATCH 6: AI Training & Scaling (Week 11-12)

**Priority:** MEDIUM **Branch:** `feature/batch-6-ai-training`
**Duration:** 2 weeks **Prerequisite:** Batch 5 stable

### Components

| Component                   | Status   | Notes                                      |
| --------------------------- | -------- | ------------------------------------------ |
| Multi-LLM Discussion System | 🔧 Build | OpenAI + Anthropic + Grok classroom debate |
| Shadow Learning Activation  | 🔧 Build | Local Llama parallel                       |
| Training Data Pipeline      | 🔧 Build | Export & format                            |
| GPU Training Foundation     | 🔧 Build | Tier 1 (Colab/Kaggle)                      |
| Readiness Dashboard         | 🔧 Build | Confidence metrics UI                      |
| Agent Management UI         | 🔧 Build | Admin controls                             |
| Google Calendar API         | 🔧 Build | Chef scheduling sync                       |
| Google Business Profile     | 🔧 Build | Reviews, posts, hours                      |
| Vertex AI Foundation        | 🔧 Build | Future ML services                         |
| **Total Routes**            |          | **~30**                                    |

### Loyalty Program (From `LOYALTY_PROGRAM_EXPLANATION.md`)

| Phase       | Feature            | Effort    | Notes                             |
| ----------- | ------------------ | --------- | --------------------------------- |
| **Phase 1** | Points Engine      | 1-2 weeks | Core earning/redemption           |
| **Phase 1** | Tier System        | 1 week    | Bronze → Silver → Gold → Platinum |
| **Phase 1** | Referral Program   | 1 week    | Friend referrals earn points      |
| **Phase 2** | Gamification       | Optional  | Challenges, badges                |
| **Phase 2** | Seasonal Campaigns | Optional  | Holiday bonus points              |

#### Loyalty Tier Benefits

| Tier     | Threshold | Perks                         |
| -------- | --------- | ----------------------------- |
| Bronze   | 0 pts     | Base earning (1 pt/$1)        |
| Silver   | 500 pts   | 1.5x points, priority booking |
| Gold     | 1000 pts  | 2x points, free setup upgrade |
| Platinum | 2500 pts  | 3x points, VIP chef access    |

### Multi-LLM Discussion System (From `COMPREHENSIVE_AI_AND_DEPLOYMENT_MASTER_PLAN.md`)

| Feature                 | Status   | Effort   | Notes                       |
| ----------------------- | -------- | -------- | --------------------------- |
| Multi-LLM debate        | 🔧 Build | 16 hours | GPT-4 + Claude + Grok       |
| Classroom voting        | 🔧 Build | 8 hours  | Best response selection     |
| Teacher-Student pattern | 🔧 Build | 12 hours | GPT-4 teaches, Llama learns |
| Confidence router       | 🔧 Build | 4 hours  | 75%/40% thresholds          |

### Future Scaling Triggers (From `FUTURE_SCALING_PLAN.md`)

| Feature            | Trigger            | Status     |
| ------------------ | ------------------ | ---------- |
| Local Llama 3      | API costs >$500/mo | 🔮 Ready   |
| Neo4j Graph Memory | Customers >1,000   | 🔮 Ready   |
| Full Option 2      | Series A funding   | 🔮 Planned |

### Feature Flags

```env
FEATURE_MULTI_LLM=true
FEATURE_SHADOW_LEARNING=true
FEATURE_TRAINING_PIPELINE=true
FEATURE_LOYALTY_PROGRAM=true
FEATURE_GOOGLE_CALENDAR=true
FEATURE_GOOGLE_BUSINESS_PROFILE=true
FEATURE_SCALING_FORECASTING=true
FEATURE_SCALING_AUTO_RECOMMENDATIONS=true

ANTHROPIC_API_KEY=xxx
XAI_API_KEY=xxx  # Grok
```

### Backend Tasks (Batch 6 - Advanced Scaling Forecasting)

> **4 hours** | Historical trends, forecasting, auto-recommendations

| Task                           | Status   | Effort  | Notes                      |
| ------------------------------ | -------- | ------- | -------------------------- |
| **Historical Metrics Storage** | 🔧 Build | 1 hr    | Store daily snapshots      |
| **Trend Analysis Service**     | 🔧 Build | 1.5 hrs | Calculate growth rate      |
| **Forecasting Engine**         | 🔧 Build | 1 hr    | Predict when scale needed  |
| **Auto-Recommendations**       | 🔧 Build | 30 min  | Generate actionable alerts |

**Features Added:**

- 30-day rolling history for all metrics
- Growth rate calculations (% change vs last week/month)
- Forecasting: "Redis Cluster needed in ~3 months" based on trends
- Auto-recommendations based on current trajectory
- Timeline visualization in admin dashboard

**Files to Create/Update:**

- `apps/backend/src/models/scaling_history.py` - History model
- `apps/backend/src/services/scaling_forecast.py` - Forecasting
  service
- `apps/backend/src/routers/v1/scaling_metrics.py` - Add `/history`
  endpoint

**Integration with Batch 1/3 Scaling System:**

- Extends existing metrics API with `forecast` and `history` sections
- Historical trends visible in dashboard timeline
- Forecasts update daily based on 30-day rolling window

### Database Setup (Batch 6)

```sql
-- Loyalty program tables (new migration)
CREATE TABLE IF NOT EXISTS core.loyalty_points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES core.customers(id),
    total_points INTEGER DEFAULT 0,
    lifetime_points INTEGER DEFAULT 0,
    tier VARCHAR(20) DEFAULT 'bronze',
    tier_updated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS core.loyalty_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES core.customers(id),
    points INTEGER NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,  -- 'earn', 'redeem', 'expire', 'bonus'
    description TEXT,
    booking_id UUID REFERENCES core.bookings(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS core.referral_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES core.customers(id),
    code VARCHAR(20) UNIQUE NOT NULL,
    uses_count INTEGER DEFAULT 0,
    max_uses INTEGER DEFAULT 100,
    points_per_referral INTEGER DEFAULT 500,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Frontend Tasks (Batch 6)

| App               | Component                     | Status   | Notes                    |
| ----------------- | ----------------------------- | -------- | ------------------------ |
| **Customer Site** | Loyalty dashboard             | 🔧 Build | Points balance, tier     |
| **Customer Site** | Points history                | 🔧 Build | Transaction log          |
| **Customer Site** | Referral page                 | 🔧 Build | Share referral code      |
| **Customer Site** | Tier benefits                 | 🔧 Build | What each tier gets      |
| **Customer Site** | Redeem points                 | 🔧 Build | Apply to booking         |
| **Admin Panel**   | Loyalty management            | 🔧 Build | Manage tiers, rules      |
| **Admin Panel**   | Referral analytics            | 🔧 Build | Track referrals          |
| **Admin Panel**   | Multi-LLM viewer              | 🔧 Build | Watch AI debates         |
| **Admin Panel**   | Shadow learning               | 🔧 Build | Compare outputs          |
| **Admin Panel**   | Readiness dashboard           | 🔧 Build | Llama confidence         |
| **Admin Panel**   | Training data export          | 🔧 Build | Export for fine-tuning   |
| **Admin Panel**   | Calendar sync status          | 🔧 Build | Chef calendar sync       |
| **Admin Panel**   | **Scaling Timeline Forecast** | 🔧 Build | Visual timeline + trends |

#### Scaling Forecasting Dashboard (Batch 6)

> **Extends Batch 1 Scaling Dashboard** with historical trends and
> forecasting

**Components to Add:**

- `apps/admin/src/components/scaling/TimelineForecast.tsx` - Visual
  timeline
- `apps/admin/src/components/scaling/TrendChart.tsx` - Historical
  trend chart
- `apps/admin/src/components/scaling/ForecastCard.tsx` - Individual
  forecasts

**Features:**

- Timeline showing forecasted scaling events (Redis Cluster ~3mo,
  etc.)
- 30-day historical trend charts for each metric
- Week-over-week and month-over-month growth rates
- Forecasting accuracy indicator
- "What-if" scenarios (e.g., "If traffic doubles, scale in X weeks")

---

### ⚡ Performance Optimization (Batch 6)

**Total Estimate:** 10 hours

#### Production Performance Regression Suite (4 hrs)

| Task                     | Effort | Notes                  |
| ------------------------ | ------ | ---------------------- |
| Automated Lighthouse CI  | 2 hrs  | Run on every PR        |
| Bundle Size Budget       | 1 hr   | Fail CI if over budget |
| API Response Time Alerts | 1 hr   | Alert if p95 >200ms    |

**Lighthouse CI Configuration:**

```yaml
# .lighthouserc.json
{
  'ci':
    {
      'collect':
        {
          'url':
            [
              'http://localhost:3000/',
              'http://localhost:3000/BookUs',
              'http://localhost:3000/contact',
            ],
          'numberOfRuns': 3,
          'settings': { 'preset': 'desktop' },
        },
      'assert':
        {
          'assertions':
            {
              'categories:performance':
                ['error', { 'minScore': 0.9 }],
              'categories:accessibility':
                ['error', { 'minScore': 0.9 }],
              'categories:best-practices':
                ['error', { 'minScore': 0.9 }],
              'categories:seo': ['error', { 'minScore': 0.9 }],
              'first-contentful-paint':
                ['error', { 'maxNumericValue': 1500 }],
              'largest-contentful-paint':
                ['error', { 'maxNumericValue': 2500 }],
              'cumulative-layout-shift':
                ['error', { 'maxNumericValue': 0.1 }],
              'interactive': ['error', { 'maxNumericValue': 3500 }],
            },
        },
      'upload': { 'target': 'temporary-public-storage' },
    },
}
```

**GitHub Action for Lighthouse:**

```yaml
# .github/workflows/lighthouse.yml
name: Lighthouse CI

on: [push, pull_request]

jobs:
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci
        working-directory: apps/customer

      - name: Build
        run: npm run build
        working-directory: apps/customer

      - name: Start server
        run: npm run start &
        working-directory: apps/customer

      - name: Wait for server
        run: npx wait-on http://localhost:3000

      - name: Run Lighthouse CI
        run: |
          npm install -g @lhci/cli
          lhci autorun
```

#### Memory Leak Detection (3 hrs)

| Task                       | Effort | Notes                    |
| -------------------------- | ------ | ------------------------ |
| React DevTools Profiler CI | 1 hr   | Automated memory checks  |
| Backend Memory Monitoring  | 1 hr   | Heap size alerts         |
| WebSocket Leak Detection   | 1 hr   | Connection cleanup tests |

**Memory Monitoring Script:**

```python
# apps/backend/scripts/memory_monitor.py
import psutil
import asyncio
from datetime import datetime
from typing import Optional

from src.core.database import SessionLocal
from src.services.notifications import NotificationService


class MemoryMonitor:
    """Monitor memory usage and alert on anomalies."""

    def __init__(
        self,
        warning_threshold_mb: int = 500,
        critical_threshold_mb: int = 800,
        check_interval_seconds: int = 60,
    ):
        self.warning_threshold = warning_threshold_mb * 1024 * 1024
        self.critical_threshold = critical_threshold_mb * 1024 * 1024
        self.check_interval = check_interval_seconds
        self.notification_service = NotificationService()
        self._last_alert: Optional[datetime] = None
        self._alert_cooldown = 300  # 5 minutes between alerts

    async def start(self):
        """Start continuous monitoring."""
        while True:
            await self.check_memory()
            await asyncio.sleep(self.check_interval)

    async def check_memory(self):
        """Check current memory usage."""
        process = psutil.Process()
        memory_info = process.memory_info()
        rss = memory_info.rss

        # Log to database
        async with SessionLocal() as db:
            await db.execute(
                """
                INSERT INTO monitoring.memory_snapshots (rss_bytes, vms_bytes, timestamp)
                VALUES (:rss, :vms, :timestamp)
                """,
                {
                    "rss": rss,
                    "vms": memory_info.vms,
                    "timestamp": datetime.utcnow(),
                }
            )
            await db.commit()

        # Check thresholds
        if rss > self.critical_threshold:
            await self._alert(
                level="critical",
                message=f"CRITICAL: Memory usage at {rss / 1024 / 1024:.0f}MB",
            )
        elif rss > self.warning_threshold:
            await self._alert(
                level="warning",
                message=f"WARNING: Memory usage at {rss / 1024 / 1024:.0f}MB",
            )

    async def _alert(self, level: str, message: str):
        """Send alert with cooldown."""
        now = datetime.utcnow()

        if self._last_alert:
            time_since = (now - self._last_alert).total_seconds()
            if time_since < self._alert_cooldown:
                return

        self._last_alert = now

        await self.notification_service.send_admin_alert(
            title=f"Memory Alert ({level.upper()})",
            message=message,
            level=level,
        )


# Usage in main.py:
# memory_monitor = MemoryMonitor()
# asyncio.create_task(memory_monitor.start())
```

#### Chaos Engineering Foundation (3 hrs)

| Task                       | Effort | Notes                 |
| -------------------------- | ------ | --------------------- |
| Network Failure Simulation | 1 hr   | Test timeout handling |
| Database Failover Test     | 1 hr   | Read replica fallback |
| Redis Failover Test        | 1 hr   | Session recovery      |

**Chaos Test Script:**

```python
# tests/chaos/chaos_tests.py
import asyncio
import pytest
from unittest.mock import patch
from httpx import ReadTimeout

from src.services.booking_service import BookingService
from src.services.payment_service import PaymentService


class TestChaosResilience:
    """Chaos engineering tests for system resilience."""

    @pytest.mark.chaos
    async def test_stripe_timeout_graceful_degradation(self):
        """Verify system handles Stripe timeout gracefully."""
        payment_service = PaymentService()

        # Simulate Stripe timeout
        with patch.object(
            payment_service._stripe_client,
            'payment_intents',
            side_effect=ReadTimeout("Stripe timeout"),
        ):
            result = await payment_service.create_payment_intent(
                amount=10000,
                customer_id="cus_test123",
            )

        # Should return graceful error, not crash
        assert result.success is False
        assert result.error_code == "PAYMENT_PROVIDER_TIMEOUT"
        assert result.retry_after_seconds > 0

    @pytest.mark.chaos
    async def test_database_connection_pool_exhaustion(self):
        """Verify system handles DB pool exhaustion."""
        booking_service = BookingService()

        # Exhaust connection pool by holding connections
        held_connections = []
        try:
            for _ in range(100):  # Exceed pool size
                conn = await booking_service._db_pool.acquire()
                held_connections.append(conn)
        except Exception:
            pass  # Expected to fail

        # New requests should queue or fail gracefully
        result = await booking_service.get_booking("test-123")

        # Should return graceful error
        assert result is None or result.error_code == "DATABASE_UNAVAILABLE"

        # Cleanup
        for conn in held_connections:
            await conn.close()

    @pytest.mark.chaos
    async def test_redis_failover_session_recovery(self):
        """Verify session recovery when Redis fails."""
        from src.core.redis import redis_client

        # Simulate Redis failure
        original_get = redis_client.get
        redis_client.get = lambda _: None  # Simulate miss

        try:
            # Session lookup should fail gracefully
            from src.auth.session import get_session
            session = await get_session("test-session-id")

            # Should return None, not crash
            assert session is None
        finally:
            redis_client.get = original_get

    @pytest.mark.chaos
    async def test_concurrent_booking_same_slot(self):
        """Test race condition handling for same time slot."""
        booking_service = BookingService()

        # Attempt 10 concurrent bookings for same slot
        tasks = [
            booking_service.create_booking(
                date="2024-03-15",
                time="18:00",
                customer_id=f"cust_{i}",
                chef_id="chef_test",
            )
            for i in range(10)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Exactly one should succeed
        successes = [r for r in results if not isinstance(r, Exception) and r.success]
        assert len(successes) == 1

        # Others should fail with proper error
        failures = [r for r in results if not isinstance(r, Exception) and not r.success]
        for failure in failures:
            assert failure.error_code in ["SLOT_UNAVAILABLE", "BOOKING_CONFLICT"]
```

---

### 🎨 UI/UX Polish (Batch 6)

**Total Estimate:** 10 hours

#### Full Dark Mode Implementation (6 hrs)

| Task                    | Effort | Notes                    |
| ----------------------- | ------ | ------------------------ |
| Customer Site Dark Mode | 3 hrs  | All pages and components |
| Admin Panel Dark Mode   | 2 hrs  | Dashboard and forms      |
| Dark Mode Toggle UI     | 1 hr   | Settings + header toggle |

**Dark Mode Toggle Component:**

```tsx
// apps/customer/src/components/ui/ThemeToggle.tsx
'use client';

import { Moon, Sun, Monitor } from 'lucide-react';
import { useTheme } from '@/components/providers/ThemeProvider';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

export function ThemeToggle() {
  const { theme, setTheme, resolvedTheme } = useTheme();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon">
          {resolvedTheme === 'dark' ? (
            <Moon className="h-5 w-5" />
          ) : (
            <Sun className="h-5 w-5" />
          )}
          <span className="sr-only">Toggle theme</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => setTheme('light')}>
          <Sun className="mr-2 h-4 w-4" />
          Light
          {theme === 'light' && <span className="ml-auto">✓</span>}
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme('dark')}>
          <Moon className="mr-2 h-4 w-4" />
          Dark
          {theme === 'dark' && <span className="ml-auto">✓</span>}
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme('system')}>
          <Monitor className="mr-2 h-4 w-4" />
          System
          {theme === 'system' && <span className="ml-auto">✓</span>}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
```

#### Loyalty Program UI Polish (4 hrs)

| Task               | Effort | Notes                        |
| ------------------ | ------ | ---------------------------- |
| Points Animation   | 1 hr   | Animated counter on earn     |
| Tier Progress Bar  | 1 hr   | Visual progress to next tier |
| Referral Share UI  | 1 hr   | Copy link, share buttons     |
| Achievement Badges | 1 hr   | Unlocked achievements        |

**Animated Points Counter:**

```tsx
// apps/customer/src/components/loyalty/AnimatedPoints.tsx
'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles } from 'lucide-react';

interface AnimatedPointsProps {
  points: number;
  previousPoints?: number;
}

export function AnimatedPoints({
  points,
  previousPoints,
}: AnimatedPointsProps) {
  const [displayPoints, setDisplayPoints] = useState(
    previousPoints || points
  );
  const [showSparkle, setShowSparkle] = useState(false);

  useEffect(() => {
    if (previousPoints !== undefined && points > previousPoints) {
      // Animate from previous to current
      const difference = points - previousPoints;
      const duration = Math.min(2000, difference * 50); // Cap at 2 seconds
      const startTime = Date.now();

      setShowSparkle(true);

      const animate = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Ease out
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = Math.round(
          previousPoints + difference * eased
        );

        setDisplayPoints(current);

        if (progress < 1) {
          requestAnimationFrame(animate);
        } else {
          setTimeout(() => setShowSparkle(false), 1000);
        }
      };

      requestAnimationFrame(animate);
    } else {
      setDisplayPoints(points);
    }
  }, [points, previousPoints]);

  return (
    <div className="relative inline-flex items-center gap-2">
      <motion.span
        key={displayPoints}
        initial={{ scale: 1 }}
        animate={{ scale: showSparkle ? [1, 1.1, 1] : 1 }}
        className="text-3xl font-bold tabular-nums"
      >
        {displayPoints.toLocaleString()}
      </motion.span>

      <span className="text-lg text-muted-foreground">pts</span>

      <AnimatePresence>
        {showSparkle && (
          <motion.div
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0 }}
            className="absolute -top-2 -right-2"
          >
            <Sparkles className="w-5 h-5 text-yellow-500" />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
```

**Tier Progress Component:**

```tsx
// apps/customer/src/components/loyalty/TierProgress.tsx
'use client';

import { motion } from 'framer-motion';

interface TierProgressProps {
  currentTier: 'bronze' | 'silver' | 'gold' | 'platinum';
  currentPoints: number;
  nextTierPoints: number;
  nextTier?: string;
}

const tierColors = {
  bronze: 'from-amber-600 to-amber-400',
  silver: 'from-gray-400 to-gray-300',
  gold: 'from-yellow-500 to-yellow-300',
  platinum: 'from-purple-500 to-purple-300',
};

export function TierProgress({
  currentTier,
  currentPoints,
  nextTierPoints,
  nextTier,
}: TierProgressProps) {
  const progress = nextTier
    ? Math.min((currentPoints / nextTierPoints) * 100, 100)
    : 100;

  return (
    <div className="w-full">
      <div className="flex justify-between text-sm mb-2">
        <span className="font-medium capitalize">{currentTier}</span>
        {nextTier && (
          <span className="text-muted-foreground">
            {nextTierPoints - currentPoints} pts to {nextTier}
          </span>
        )}
      </div>

      <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 1, ease: 'easeOut' }}
          className={`h-full bg-gradient-to-r ${tierColors[currentTier]} rounded-full`}
        />
      </div>

      {!nextTier && (
        <p className="text-center text-sm mt-2 text-muted-foreground">
          🎉 You&apos;ve reached the highest tier!
        </p>
      )}
    </div>
  );
}
```

---

### 🧪 QA & Testing (Batch 6)

**Total Estimate:** 10 hours

#### Chaos Engineering Tests (4 hrs)

| Task                    | Effort | Notes                          |
| ----------------------- | ------ | ------------------------------ |
| Network Failure Tests   | 1 hr   | Timeout, disconnect scenarios  |
| Database Failover Tests | 1 hr   | Connection recovery            |
| Payment Provider Tests  | 1 hr   | Stripe/Square failure handling |
| Race Condition Tests    | 1 hr   | Concurrent booking tests       |

#### Full Regression Suite (4 hrs)

| Task                  | Effort | Notes                         |
| --------------------- | ------ | ----------------------------- |
| E2E Booking Flow      | 1 hr   | Complete booking journey      |
| E2E Payment Flow      | 1 hr   | All payment scenarios         |
| E2E Admin Flow        | 1 hr   | Admin critical paths          |
| Cross-Browser Testing | 1 hr   | Chrome, Safari, Firefox, Edge |

**Cross-Browser Test Configuration:**

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',

  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    video: 'on-first-retry',
  },

  projects: [
    // Desktop browsers
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'edge',
      use: { ...devices['Desktop Edge'] },
    },

    // Mobile viewports
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'mobile-safari',
      use: { ...devices['iPhone 13'] },
    },

    // Tablet
    {
      name: 'tablet',
      use: { ...devices['iPad Pro 11'] },
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

#### Performance Regression Tests (2 hrs)

| Task                      | Effort | Notes                 |
| ------------------------- | ------ | --------------------- |
| Lighthouse CI Integration | 1 hr   | Fail on regression    |
| Bundle Size Monitoring    | 30 min | Alert on increase >5% |
| API Latency Benchmarks    | 30 min | p95 must stay <200ms  |

### Success Criteria

**Core Batch 6 Features:**

- [ ] Multi-LLM discussions generating quality responses
- [ ] Training data collecting to database
- [ ] Shadow mode running parallel (no customer exposure)
- [ ] Readiness dashboard showing metrics
- [ ] Loyalty program points engine functional
- [ ] Tier progression working correctly
- [ ] Referral tracking active
- [ ] Google Calendar syncing chef availability
- [ ] Google Business reviews being monitored
- [ ] Training data quality score >80%

**Full Scaling Infrastructure (Batch 6):**

- [ ] Local Llama 3 ready to activate (config complete, not deployed)
- [ ] Multi-LLM provider abstraction layer working
- [ ] AI cost monitoring dashboard showing spend by provider
- [ ] Shadow learning comparing outputs without customer impact
- [ ] Training data pipeline ready for fine-tuning export
- [ ] Database partitioning scripts tested (ready to apply when
      needed)
- [ ] Read replica config tested (ready to add when needed)

**Scaling Forecasting System (Batch 6):**

- [ ] Historical metrics storing daily snapshots (30-day rolling)
- [ ] `/api/v1/admin/scaling/history` endpoint returning trend data
- [ ] Trend analysis calculating week-over-week growth rates
- [ ] Forecasting engine predicting scale-up timelines
- [ ] Admin dashboard timeline showing forecasted scaling events
- [ ] Auto-recommendations generating based on trajectory
- [ ] Forecast accuracy >70% (validated retroactively)

**⚡ Performance (Batch 6):**

- [ ] Lighthouse CI integrated (blocks PR on regression)
- [ ] Bundle size budget enforced (<300KB initial JS)
- [ ] Memory leak detection running in CI
- [ ] Chaos tests passing (timeout handling, failover)
- [ ] API p95 latency <200ms across all endpoints

**🎨 UI/UX (Batch 6):**

- [ ] Full dark mode implemented (customer + admin)
- [ ] Theme toggle working with system preference
- [ ] Animated points counter functional
- [ ] Tier progress visualization implemented
- [ ] Referral share UI with copy/share buttons
- [ ] All animations smooth (60fps, no jank)

**🧪 QA (Batch 6):**

- [ ] Chaos engineering tests passing
- [ ] Network failure recovery tests passing
- [ ] Database failover tests passing
- [ ] Race condition tests passing (no double bookings)
- [ ] Cross-browser tests passing (Chrome, Safari, Firefox, Edge)
- [ ] Mobile E2E tests passing (iOS Safari, Android Chrome)
- [ ] Full regression suite green

### Rollback Plan

```bash
FEATURE_MULTI_LLM=false
FEATURE_SHADOW_LEARNING=false
# Continue with OpenAI-only production
```

---

## ✅ QUALITY GATES

### Pre-Merge Checklist (feature → dev)

```markdown
□ All unit tests pass (100%) □ Integration tests pass (95%+) □ Code
review approved (2+ reviewers) □ No critical/high security issues (npm
audit, safety check) □ No console.log/print debug statements □
Documentation updated □ Feature flags configured in all environments □
Error handling complete (no unhandled exceptions) □ TypeScript/Python
type hints complete
```

### Pre-Production Checklist (dev → main)

```markdown
□ Full regression test suite passes □ Performance benchmarks met
(<200ms API response) □ Load testing passed (expected traffic + 2x
buffer) □ Security scan passed (OWASP, SQLi, XSS) □ Manager sign-off
obtained □ Rollback plan documented and tested □ Monitoring alerts
configured □ Environment variables verified in production □ Database
migrations tested on staging □ Backup verified before deployment
```

### Post-Deployment Checklist

```markdown
□ Health checks passing (all endpoints) □ No error rate spike (monitor
4 hours) □ Key user flows manually verified □ Performance metrics
within baseline □ No memory leaks detected □ 48-72 hour stability
period completed □ Post-deployment review meeting held □ Documentation
finalized
```

---

## 🔙 Rollback Decision Matrix

| Condition                                   | Action                               | Timeline       |
| ------------------------------------------- | ------------------------------------ | -------------- |
| Error rate >5%                              | Immediate rollback                   | <5 minutes     |
| Critical flow broken (booking/payment/auth) | Immediate rollback                   | <5 minutes     |
| Error rate >2%                              | Investigate, hotfix or rollback      | 30 minutes max |
| Performance >50% degraded                   | Investigate, rollback if not fixable | 1 hour max     |
| Error rate 1-2%                             | Monitor closely, prepare rollback    | 4 hours        |
| Minor issues                                | Log, fix in next release             | Next sprint    |

### Rollback Commands

```bash
# Quick rollback to previous version
git checkout v1.0.X-batchY  # Previous stable tag
docker-compose down
docker-compose up -d

# Verify rollback successful
curl https://api.myhibachi.com/health

# Notify team
# Post to #deployments Slack channel
```

---

## 📅 Timeline Summary

| Batch | Weeks | Dates        | Focus                   |
| ----- | ----- | ------------ | ----------------------- |
| **1** | 1-2   | Dec 3-15     | Core Booking + Security |
| **2** | 3-4   | Dec 16-29    | Payments                |
| **3** | 5-6   | Jan 1-12     | Core AI                 |
| **4** | 7-8   | Jan 13-26    | Communications          |
| **5** | 9-10  | Jan 27-Feb 9 | Advanced AI + Marketing |
| **6** | 11-12 | Feb 10-23    | AI Training & Scaling   |

---

## 📊 Feature Flag Reference

### Batch 1 - Core Booking + Security

```env
FEATURE_CORE_API=true
FEATURE_AUTH=true
FEATURE_CLOUDFLARE_TUNNEL=true
FEATURE_RBAC=true
FEATURE_AUDIT_TRAIL=true
FEATURE_SOFT_DELETE=true
FEATURE_FAILED_BOOKING_LEAD_CAPTURE=true
```

### Batch 2 - Payments

```env
FEATURE_STRIPE=true
FEATURE_PAYMENTS=true
FEATURE_DYNAMIC_PRICING=true
```

### Batch 3 - Core AI

```env
FEATURE_AI_CORE=true
FEATURE_OPENAI=true
FEATURE_SMART_ESCALATION=true
```

### Batch 4 - Communications

```env
FEATURE_RINGCENTRAL=true
FEATURE_VOICE_AI=true
FEATURE_DEEPGRAM=true
FEATURE_RC_NATIVE_RECORDING=true
FEATURE_META_WHATSAPP=true
FEATURE_META_FACEBOOK=true
FEATURE_META_INSTAGRAM=true
FEATURE_GOOGLE_BUSINESS=true
```

### Batch 5 - Advanced AI + Marketing

```env
FEATURE_ADVANCED_AI=true
FEATURE_EMOTION_DETECTION=true
FEATURE_PSYCHOLOGY_AGENTS=true
FEATURE_TOOL_CALLING=true
FEATURE_RAG=true
FEATURE_FEEDBACK_COLLECTION=true
FEATURE_CUSTOMER_REVIEWS=true
FEATURE_MARKETING_INTELLIGENCE=true
FEATURE_GOOGLE_SEARCH_CONSOLE=true
FEATURE_GOOGLE_ADS=true
FEATURE_GOOGLE_ANALYTICS=true
```

### Batch 6 - AI Training & Scaling

```env
FEATURE_MULTI_LLM=true
FEATURE_SHADOW_LEARNING=true
FEATURE_TRAINING_PIPELINE=true
FEATURE_LOYALTY_PROGRAM=true
FEATURE_GOOGLE_CALENDAR=true
FEATURE_GOOGLE_BUSINESS_PROFILE=true
```

---

## 🔮 FUTURE SCALABILITY NOTES

### Marketing Intelligence Upgrade Path

```
📝 FUTURE ENHANCEMENT NOTES
═══════════════════════════

CURRENT (Phase 1 - Option A): ~52 hours, $0/month
├── Google Search Console integration
├── Google Ads API (FULL scope)
├── Google Analytics 4 integration
├── AI recommendations (OpenAI)
└── All dashboards in admin panel

READY TO ADD (Phase 2 - Option B): +28 hours, $50-150/month
├── SEMrush or SpyFu API integration
├── Competitor keyword tracking
├── Competitor ad analysis
├── Market share estimates
└── Trigger: Monthly ad spend > $5,000

READY TO ADD (Phase 3 - Option C): +70 hours, $100-200/month total
├── Automated budget optimization
├── Predictive trend analysis
├── AI-generated ad copy
├── Multi-channel attribution
└── Trigger: Data volume > 1000 conversions/month
```

### Architecture Designed for Scale

The marketing intelligence system uses pluggable service interfaces:

```python
class MarketingDataProvider(ABC):
    async def fetch_data() -> MarketingData
    async def get_performance() -> PerformanceMetrics

# Current: GoogleAdsService, GoogleSearchConsoleService
# Future: SEMrushService, SpyFuService (same interface)
```

---

## 🗑️ Cleanup Completed

| Item                 | Status     | Notes                       |
| -------------------- | ---------- | --------------------------- |
| QR Tracking files    | ✅ DELETED | Not needed for business     |
| StripeCustomer model | ✅ ADDED   | `db/models/stripe.py`       |
| CallStatus enum      | ✅ ADDED   | `support_communications.py` |
| CallDirection enum   | ✅ ADDED   | `support_communications.py` |

---

## 📚 Related Documentation

- [ENTERPRISE_AI_DEPLOYMENT_MASTER_PLAN.md](../ENTERPRISE_AI_DEPLOYMENT_MASTER_PLAN.md) -
  Full architecture
- [QUALITY_GATES.md](./QUALITY_GATES.md) - Detailed quality gate
  documentation

---

**Document Status:** ✅ APPROVED **Last Updated:** December 4, 2025
**Next Action:** Begin Batch 1 implementation
