# My Hibachi Web App – Project Overview

**Read Time:** 5 minutes **Audience:** New developers, AI agents,
stakeholders

---

## 🍳 What is My Hibachi?

My Hibachi is a **premium hibachi catering service** in the San
Francisco Bay Area. We bring the full hibachi restaurant experience to
customers' homes, offices, and events.

This repository contains the **complete web platform** that powers:

- Customer booking website
- Admin operations panel
- Backend API and business logic
- AI-powered customer assistance

---

## 🏗️ Tech Stack

| Layer        | Technology                             | Notes                    |
| ------------ | -------------------------------------- | ------------------------ |
| **Frontend** | Next.js 15, React 19, TypeScript       | App Router, RSC          |
| **Styling**  | Tailwind CSS v4                        | Custom design system     |
| **Backend**  | FastAPI, Python 3.11+                  | mhapi.mysticdatanode.net |
| **Database** | PostgreSQL 15 (Plesk VPS)              | Multi-schema design      |
| **Cache**    | Redis                                  | Session, rate limiting   |
| **Payments** | Stripe                                 | Intents, webhooks        |
| **AI**       | OpenAI GPT-4                           | Chat, voice processing   |
| **Voice**    | RingCentral                            | SMS, phone calls         |
| **Hosting**  | Vercel (frontend), Plesk VPS (backend) | Cloudflare DNS           |

---

## 📁 Repository Structure

```
MH webapps/
├── apps/
│   ├── customer/          # Next.js – Public booking site
│   │   ├── src/app/       # Pages (App Router)
│   │   ├── src/components # React components
│   │   └── src/lib/       # Utilities, API client
│   │
│   ├── admin/             # Next.js – Internal admin panel
│   │   ├── src/app/       # Admin pages
│   │   └── src/components # Admin components
│   │
│   └── backend/           # FastAPI – Python API
│       ├── src/api/       # API layer
│       ├── src/routers/   # Route definitions
│       ├── src/services/  # Business logic
│       ├── src/db/models/ # SQLAlchemy models
│       └── src/core/      # Config, security
│
├── docs/                  # Documentation (you are here)
├── database/              # SQL migrations
├── e2e/                   # Playwright tests
└── .github/               # CI/CD, Copilot instructions
```

---

## 🚀 Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/myhibachi/mh-webapps.git
cd mh-webapps

# 2. Install frontend dependencies
cd apps/customer && npm install
cd ../admin && npm install

# 3. Install backend dependencies
cd ../backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env.local  # Edit with your values

# 5. Run development servers
# Terminal 1: Customer site
cd apps/customer && npm run dev

# Terminal 2: Admin panel
cd apps/admin && npm run dev

# Terminal 3: Backend API
cd apps/backend/src && uvicorn main:app --reload
```

---

## 🔑 Key Concepts

### Database Schemas

The database is organized into logical schemas:

| Schema     | Purpose                | Key Tables                 |
| ---------- | ---------------------- | -------------------------- |
| `core`     | Core business entities | bookings, customers, chefs |
| `crm`      | Customer relationship  | leads, campaigns, segments |
| `lead`     | Lead tracking details  | lead_contacts, lead_events |
| `ops`      | Operations             | chefs, stations            |
| `ai`       | AI conversations       | conversations, messages    |
| `identity` | Auth & access          | users, roles, stations     |

### Feature Flags

New features are controlled by flags in
`apps/backend/src/core/config.py`:

```python
FEATURE_STRIPE_ENABLED = False      # Batch 2
FEATURE_AI_CHAT_ENABLED = False     # Batch 3
FEATURE_RINGCENTRAL_ENABLED = False # Batch 4
```

### Batch Deployment

Features are deployed in batches. Check `CURRENT_BATCH_STATUS.md` for
active batch.

---

## 👥 Team Roles

| Role               | Responsibility                    |
| ------------------ | --------------------------------- |
| **Owner**          | Product decisions, business rules |
| **Full-Stack Dev** | Frontend + backend implementation |
| **DevOps**         | Cloudflare, VPS, CI/CD            |
| **AI Agent**       | Code assistance, documentation    |

---

## 📚 Next Steps

1. Read the [PRD](./PRD.md) for product requirements
2. Review the [Architecture](../01-ARCHITECTURE/ARCHITECTURE.md)
3. Check [CURRENT_BATCH_STATUS.md](../../CURRENT_BATCH_STATUS.md) for
   active work
4. Explore the [Glossary](./GLOSSARY.md) for business terms

---

## 🆘 Getting Help

- **Docs:** Start in this `/docs` folder
- **Instructions:** Check `.github/instructions/` for Copilot rules
- **Issues:** Create GitHub issues for bugs/features
- **Questions:** Ask in team chat or code comments
