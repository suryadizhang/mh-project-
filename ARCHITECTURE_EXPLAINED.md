# 🏗️ Backend Architecture Explained

**Date**: November 4, 2025

---

## 📊 Current Architecture: 3 Main.py Files

### **File 1: `/src/main.py` (37 KB) - PRIMARY UNIFIED SERVER** ✅

**Purpose**: Single unified FastAPI application serving EVERYTHING  
**Runs on**: Port 8000 via `run_backend.py`  
**Status**: ✅ **ACTIVE - This is what's running**

**What it includes:**

```
┌─────────────────────────────────────────────────────┐
│         src/main.py (PRIMARY SERVER)                │
│                                                     │
│  📦 Core System (Database & Business Logic)        │
│     • Bookings, Customers, Payments                │
│     • Leads, Newsletter, Reviews                   │
│     • Stripe integration                           │
│     • Email & SMS services                         │
│     • Admin panels & Analytics                     │
│                                                     │
│  🤖 AI System (Embedded)                           │
│     • AI Chat endpoints (/api/v1/ai/*)             │
│     • AI Orchestrator                              │
│     • Multi-channel AI (email, SMS, Instagram)     │
│     • Intent routing & emotion detection           │
│     • Self-learning AI                             │
│                                                     │
│  🔧 Enterprise Features                            │
│     • Sentry monitoring                            │
│     • Prometheus metrics (/metrics)                │
│     • CQRS + Event Sourcing                        │
│     • Outbox workers (background jobs)             │
│     • Multi-layer rate limiting                    │
│     • K8s health checks (/ready, /info)            │
│     • Station Management (Multi-tenant RBAC)       │
│                                                     │
│  🌐 All Routers (30+)                              │
│     /api/auth, /api/bookings, /api/stripe          │
│     /api/leads, /api/reviews, /api/crm             │
│     /api/v1/ai/*, /api/admin/*                     │
│     /api/station/*, /api/qr/*                      │
└─────────────────────────────────────────────────────┘
```

**How it works:**

```bash
# Start command
python run_backend.py

# run_backend.py executes:
uvicorn.run("main:app", port=8000)
         ↓
# Loads src/main.py which includes EVERYTHING
```

---

### **File 2: `/src/api/ai/endpoints/main.py` (4.8 KB) - AI MICROSERVICE** ⚠️

**Purpose**: Standalone AI-only FastAPI app (if you want to run AI
separately)  
**Runs on**: Port 8002 (if started manually)  
**Status**: ⚠️ **NOT CURRENTLY RUNNING** (AI is embedded in primary
main.py)

**What it includes:**

```
┌─────────────────────────────────────────────────────┐
│    api/ai/endpoints/main.py (AI STANDALONE)         │
│                                                     │
│  🤖 AI-Only Endpoints                              │
│     • /api/chat/* - Chat endpoints                 │
│     • /api/admin/* - AI admin                      │
│     • /webhooks/* - AI webhooks                    │
│     • WebSocket support                            │
│                                                     │
│  📊 Minimal Setup                                  │
│     • Basic health check                           │
│     • OpenAI configuration                         │
│     • No database (relies on external DB)          │
│     • No business logic                            │
└─────────────────────────────────────────────────────┘
```

**When to use:**

- If you want to run AI as a separate microservice
- For horizontal scaling (AI service on different servers)
- For testing AI features in isolation

**To start separately:**

```bash
cd apps/backend/src/api/ai/endpoints
python main.py  # Runs on port 8002
```

---

### **File 3: `/src/api/app/main.py` (20 KB) - LEGACY** ❌

**Purpose**: Old main.py from before consolidation  
**Status**: ❌ **DEPRECATED - Should be deleted**

**What it had:**

- Sentry, Prometheus, CQRS, Workers (now merged into primary)
- Station management (now merged into primary)
- Old router structure (now merged into primary)

**Why it exists:**

- Historical artifact from before Phase 1 consolidation
- Some tests still import from it (need to fix)
- Will be deleted after Phase 2 complete

---

## 🎯 Answer to Your Question

### **Do Database and AI use the same main.py?**

**YES! Currently: UNIFIED ARCHITECTURE** ✅

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│               src/main.py (ONE SERVER)               │
│               Running on Port 8000                   │
│                                                      │
│  ┌─────────────────┐      ┌──────────────────┐     │
│  │  Database System│      │    AI System     │     │
│  │                 │      │                  │     │
│  │ • PostgreSQL    │      │ • OpenAI API     │     │
│  │ • Redis cache   │      │ • Chat service   │     │
│  │ • SQLAlchemy    │      │ • Intent router  │     │
│  │ • Alembic       │      │ • Orchestrator   │     │
│  │                 │      │ • Self-learning  │     │
│  └────────┬────────┘      └────────┬─────────┘     │
│           │                        │               │
│           └────────┬───────────────┘               │
│                    │                               │
│           ┌────────▼──────────┐                    │
│           │  Shared Resources │                    │
│           ├───────────────────┤                    │
│           │ • Auth/JWT        │                    │
│           │ • Rate limiting   │                    │
│           │ • Logging         │                    │
│           │ • Monitoring      │                    │
│           │ • Middleware      │                    │
│           └───────────────────┘                    │
│                                                      │
└──────────────────────────────────────────────────────┘

         ↓
    All requests to: http://localhost:8000
         ↓
    • Business endpoints: /api/bookings, /api/leads
    • AI endpoints: /api/v1/ai/chat
    • Admin endpoints: /api/admin/*
```

---

## 🔄 Architecture Options

### **Option 1: UNIFIED (Current)** ✅

```
Single Server: src/main.py
├── Database operations
├── Business logic
├── AI features
└── All routers

Pros:
✅ Simple deployment (one service)
✅ Shared auth, logging, monitoring
✅ No network latency between components
✅ Easier development & debugging

Cons:
❌ Can't scale AI independently
❌ Larger memory footprint
❌ Single point of failure
```

### **Option 2: MICROSERVICES (Available but not active)**

```
Server 1: src/main.py (Port 8000)
├── Database operations
├── Business logic
└── Core routers

Server 2: api/ai/endpoints/main.py (Port 8002)
├── AI chat
├── AI orchestrator
└── AI-only endpoints

Pros:
✅ Independent scaling (AI needs more resources)
✅ Isolated failures (AI down ≠ business down)
✅ Different deployment schedules

Cons:
❌ More complex deployment
❌ Need service-to-service auth
❌ Network latency between services
❌ Duplicate middleware/monitoring
```

---

## 📁 File Structure Mapping

```
apps/backend/
│
├── run_backend.py              # Starts primary server
│
└── src/
    │
    ├── main.py                 # ✅ PRIMARY (37 KB)
    │                           # Runs everything (DB + AI + Enterprise)
    │                           # Port 8000
    │
    ├── core/                   # Shared by main.py
    │   ├── database.py         # PostgreSQL + SQLAlchemy
    │   ├── config.py           # Settings
    │   ├── auth.py             # JWT authentication
    │   └── rate_limiting.py    # Rate limiter
    │
    ├── services/               # Business services (used by main.py)
    │   ├── booking_service.py
    │   ├── email_service.py
    │   ├── lead_service.py
    │   └── ...
    │
    ├── api/
    │   │
    │   ├── ai/
    │   │   ├── routers/        # AI routers (imported by main.py)
    │   │   ├── services/       # AI services (imported by main.py)
    │   │   └── endpoints/
    │   │       └── main.py     # ⚠️ STANDALONE AI (4.8 KB)
    │   │                       # Optional separate AI server
    │   │                       # Port 8002 (if started)
    │   │
    │   └── app/
    │       ├── routers/        # Business routers (imported by main.py)
    │       ├── services/       # ⚠️ DUPLICATES (to be deleted)
    │       └── main.py         # ❌ LEGACY (20 KB)
    │                           # Old server (to be deleted)
    │
    └── models/                 # Database models (used by main.py)
        ├── booking.py
        ├── user.py
        └── ...
```

---

## 🚀 Current Runtime

```
Terminal: powershell (separate window)
Command: python run_backend.py

↓

Process: uvicorn running "main:app"
PID: [varies]
Port: 8000
Memory: ~300 MB (includes AI models)

↓

What's loaded in memory:
✅ PostgreSQL connection pool
✅ Redis connection (rate limiting, cache)
✅ OpenAI client (AI features)
✅ All 30+ routers
✅ DI container with repositories
✅ AI Orchestrator with scheduler
✅ Outbox workers (background jobs)
✅ Sentry monitoring
✅ Prometheus metrics collector
```

---

## 🎯 Recommendation

**Keep the UNIFIED architecture (current setup)** ✅

**Reasons:**

1. **Simpler**: One deployment, one service, one config
2. **Faster**: No network calls between DB and AI
3. **Cheaper**: One server vs two servers
4. **Easier debugging**: All logs in one place
5. **Better for small/medium scale**: You're not at Netflix scale yet

**When to switch to microservices:**

- AI queries take too long and slow down bookings
- Need to scale AI independently (add more AI servers)
- AI crashes and takes down the whole system
- Team grows and different teams own different services

**Current scale**: UNIFIED is perfect ✅

---

## 🔍 What Should We Do?

### **Phase 2 Plan:**

1. ✅ **Keep**: `src/main.py` (primary unified server)
2. ✅ **Keep**: `api/ai/endpoints/main.py` (option for future
   microservice)
3. ❌ **Delete**: `api/app/main.py` (legacy, now redundant)
4. 🔄 **Cleanup**: Remove duplicate services in `api/app/services/`
5. 🔄 **Update imports**: Point all imports to canonical locations

**Result**: Clean unified architecture with option to split later if
needed.

---

## 💡 Summary

**Question**: Do database and AI use the same main.py?

**Answer**: **YES!** They both use `src/main.py` (37 KB)

**Why**:

- Simpler architecture
- Better performance (no network latency)
- Easier to maintain
- Shared authentication & monitoring

**The AI-only main.py exists** (`api/ai/endpoints/main.py`) but is
**NOT running**. It's there as an option if you want to split into
microservices later.

**Current setup**:

```
ONE SERVER = Database + AI + Everything
Port 8000 = All your APIs (business + AI)
```

This is the RIGHT architecture for your current scale! ✅
