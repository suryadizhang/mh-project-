---
applyTo: '**'
---

# My Hibachi – System Architecture

**Priority: HIGH** – Understand the system before making changes.

---

## 🏗️ System Overview

My Hibachi is a **monorepo** with 3 coordinated applications:

```
┌─────────────────────────────────────────────────────────────┐
│                    MY HIBACHI ECOSYSTEM                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  CUSTOMER   │    │   ADMIN     │    │   BACKEND   │     │
│  │   SITE      │    │   PANEL     │    │    API      │     │
│  │  (Next.js)  │    │  (Next.js)  │    │  (FastAPI)  │     │
│  │   Vercel    │    │   Vercel    │    │  VPS/Plesk  │     │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘     │
│         │                  │                  │             │
│         └──────────────────┴──────────────────┘             │
│                         │                                   │
│                    Shared API                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Directory Structure

```
MH webapps/
├── apps/
│   ├── customer/          # Next.js - Public booking site
│   │   ├── src/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── lib/
│   │   │   ├── app/       # App Router pages
│   │   │   └── features/
│   │   └── package.json
│   │
│   ├── admin/             # Next.js - Internal admin panel
│   │   ├── src/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── lib/
│   │   │   ├── app/
│   │   │   └── features/
│   │   └── package.json
│   │
│   └── backend/           # FastAPI - Python API
│       ├── src/
│       │   ├── api/       # API layer (endpoints)
│       │   ├── routers/   # Route definitions
│       │   ├── services/  # Business logic
│       │   ├── repositories/  # Data access
│       │   ├── schemas/   # Pydantic models
│       │   ├── db/        # Database models
│       │   ├── core/      # Config, security, exceptions
│       │   └── workers/   # Background tasks
│       └── requirements.txt
│
├── docs/                  # Documentation (hierarchical)
│   ├── 00-ONBOARDING/
│   ├── 01-ARCHITECTURE/
│   ├── 02-IMPLEMENTATION/
│   ├── 03-FEATURES/
│   ├── 04-DEPLOYMENT/
│   ├── 05-OPERATIONS/
│   └── 06-QUICK_REFERENCE/
│
├── database/              # SQL migrations
├── e2e/                   # End-to-end tests
├── scripts/               # Utility scripts
└── .github/               # CI/CD, instructions
```

---

## 🖥️ Application Details

### Customer Site (apps/customer/)

| Aspect          | Detail                                     |
| --------------- | ------------------------------------------ |
| **Purpose**     | Public booking, marketing, customer portal |
| **Framework**   | Next.js 14+ (App Router)                   |
| **Hosting**     | Vercel                                     |
| **Audience**    | Public customers                           |
| **Criticality** | 🔴 CRITICAL – Revenue-generating           |

**Key Features:**

- Booking flow
- Price calculator
- Menu display
- Customer account
- Payment processing

### Admin Panel (apps/admin/)

| Aspect          | Detail                          |
| --------------- | ------------------------------- |
| **Purpose**     | Internal operations, management |
| **Framework**   | Next.js 14+ (App Router)        |
| **Hosting**     | Vercel                          |
| **Audience**    | Staff only                      |
| **Criticality** | 🟠 HIGH – Operations            |

**Key Features:**

- Booking management
- Chef scheduling
- Customer CRM
- Pricing management
- AI dashboard

### Backend API (apps/backend/)

| Aspect          | Detail                                |
| --------------- | ------------------------------------- |
| **Purpose**     | API, business logic, data persistence |
| **Framework**   | FastAPI (Python 3.11+)                |
| **Hosting**     | VPS via Plesk                         |
| **Database**    | PostgreSQL                            |
| **Cache**       | Redis                                 |
| **Criticality** | 🔴 CRITICAL – Core logic              |

**Key Modules:**

- `/api/v1/` – REST endpoints
- `/services/` – Business logic
- `/db/models/` – SQLAlchemy models
- `/core/config.py` – Feature flags

---

## 🗄️ Database Architecture

### Schemas

| Schema    | Purpose                           |
| --------- | --------------------------------- |
| `core`    | Users, roles, permissions         |
| `booking` | Bookings, payments, invoices      |
| `menu`    | Menu items, categories, allergens |
| `crm`     | Customers, leads, communications  |
| `ai`      | AI conversations, training data   |
| `audit`   | Audit logs, change tracking       |

### Key Tables

- `core.users` – All user accounts
- `booking.bookings` – Booking records
- `booking.payments` – Payment transactions
- `crm.customers` – Customer profiles
- `ai.conversations` – AI chat history

---

## 🔌 External Integrations

| Service               | Purpose              | Batch   |
| --------------------- | -------------------- | ------- |
| Stripe                | Payments             | Batch 2 |
| Google Maps           | Address autocomplete | Batch 1 |
| RingCentral           | Voice/SMS            | Batch 4 |
| OpenAI                | AI responses         | Batch 3 |
| Deepgram              | Transcription        | Batch 4 |
| Resend                | Email                | Batch 1 |
| Meta (WhatsApp/FB/IG) | Messaging            | Batch 4 |

---

## 🔄 Data Flow

```
Customer Action
      │
      ▼
┌─────────────┐
│  Frontend   │ (Next.js)
│  Customer/  │
│   Admin     │
└──────┬──────┘
       │ API Call
       ▼
┌─────────────┐
│   Backend   │ (FastAPI)
│    API      │
└──────┬──────┘
       │
       ├──────────┐
       ▼          ▼
┌──────────┐ ┌─────────┐
│PostgreSQL│ │  Redis  │
│ (Data)   │ │ (Cache) │
└──────────┘ └─────────┘
```

---

## 📝 Architecture Rules

1. **Frontend calls Backend only** – Never direct DB access
2. **Backend owns business logic** – Frontends are presentational
3. **Schemas isolate domains** – No cross-schema direct access
4. **Services encapsulate logic** – Routers are thin
5. **Repositories handle data** – Services don't write SQL
6. **API is single source of truth** – All pricing, rules, validation
   lives in backend
7. **No local calculations** – Frontend NEVER calculates business
   values (prices, fees, etc.)
8. **Unified system** – Admin, Customer, and API are ONE synchronized
   system

> **See Rule #14 in `01-CORE_PRINCIPLES.instructions.md` for full
> Unified System Architecture details.**

---

## 🔗 Related Docs

- `docs/01-ARCHITECTURE/` – Detailed architecture docs
- `docs/DATABASE_ARCHITECTURE_BUSINESS_MODEL.md` – DB details
- `docs/DATABASE_RELATIONSHIP_MAP.md` – Table relationships
