---
applyTo: '**'
---

# My Hibachi – Quick Reference (ALWAYS LOADED)

**Purpose:** Critical info that AI must NEVER forget. Minimal tokens,
maximum memory.

---

## 🌐 DOMAINS & INFRASTRUCTURE

| Service                   | Domain                             | Location   |
| ------------------------- | ---------------------------------- | ---------- |
| **Customer Site**         | `myhibachichef.com`                | Vercel     |
| **Admin Panel (Prod)**    | `admin.mysticdatanode.net`         | Vercel     |
| **Admin Panel (Staging)** | `admin-staging.mysticdatanode.net` | Vercel     |
| **Production API**        | `mhapi.mysticdatanode.net`         | Docker/VPS |
| **Staging API**           | `staging-api.mysticdatanode.net`   | Docker/VPS |

## 🖥️ VPS ACCESS

| Property              | Value                                  |
| --------------------- | -------------------------------------- |
| **IP**                | `108.175.12.154`                       |
| **SSH**               | `ssh root@108.175.12.154`              |
| **Plesk**             | `https://108.175.12.154:8443`          |
| **Cloudflare Tunnel** | `82034f96-98f7-41a8-b5bf-6976e383113d` |

## 🔌 KEY API ENDPOINTS

| Endpoint                      | Purpose                |
| ----------------------------- | ---------------------- |
| `GET /api/v1/health`          | Health check           |
| `GET /api/v1/pricing/current` | Current pricing (SSoT) |
| `GET /api/v1/config/all`      | All dynamic config     |
| `POST /api/v1/bookings`       | Create booking         |
| `GET /api/v1/bookings/{id}`   | Get booking            |
| `POST /api/v1/auth/login`     | Authentication         |

## 🐳 DOCKER CONTAINERS

```bash
# Production
docker compose -f configs/docker-compose.vps.yml up -d production-api production-redis

# Staging
docker compose -f configs/docker-compose.vps.yml up -d staging-api staging-redis

# Check health
docker ps --format 'table {{.Names}}\t{{.Status}}'
curl http://localhost:8000/health  # Production
curl http://localhost:8002/health  # Staging
```

## 🗄️ DATABASES

| Environment    | Database               | User                     |
| -------------- | ---------------------- | ------------------------ |
| **Production** | `myhibachi_production` | `myhibachi_user`         |
| **Staging**    | `myhibachi_staging`    | `myhibachi_staging_user` |

**PostgreSQL:** Native on VPS (not containerized)

## 💰 PRICING (SSoT - Dynamic Variables)

| Item          | Value | Source                                     |
| ------------- | ----- | ------------------------------------------ |
| Adult (13+)   | $55   | `dynamic_variables.adult_price_cents`      |
| Child (6-12)  | $30   | `dynamic_variables.child_price_cents`      |
| Under 5       | FREE  | `dynamic_variables.child_free_under_age`   |
| Party Minimum | $550  | `dynamic_variables.party_minimum_cents`    |
| Deposit       | $100  | `dynamic_variables.deposit_amount_cents`   |
| Free Miles    | 30    | `travel_fee_configurations.free_miles`     |
| Per Mile      | $2    | `travel_fee_configurations.per_mile_cents` |

**⚠️ NEVER hardcode prices. Use `usePricing()` hook or API.**

## 🍖 BUSINESS MODEL

- **Each guest gets 2 PROTEINS** (not 1!)
- Base proteins: Chicken, NY Strip, Shrimp, Calamari, Tofu
- Upgrades: Salmon (+$5), Scallops (+$5), Filet (+$5), Lobster (+$15)

## 🔀 GIT BRANCHES

| Branch      | Purpose     | Deploy       |
| ----------- | ----------- | ------------ |
| `main`      | Production  | Auto-deploys |
| `dev`       | Staging     | Auto-deploys |
| `feature/*` | Development | Preview      |

## 📁 PROJECT STRUCTURE

```
apps/
├── customer/  → Next.js (Vercel: myhibachichef.com)
├── admin/     → Next.js (Vercel: admin.mysticdatanode.net)
└── backend/   → FastAPI (Docker: mhapi.mysticdatanode.net)
```

## ⚡ COMMON COMMANDS

```bash
# Build & test before commit
cd apps/customer && npm run build && npm test -- --run
cd apps/admin && npm run build
cd apps/backend/src && python -c "from main import app; print('OK')"

# Deploy to VPS
ssh root@108.175.12.154 "cd /var/www/vhosts/myhibachichef.com/mhapi.mysticdatanode.net/backend && git pull origin dev"

# Restart containers
docker compose -f configs/docker-compose.vps.yml restart production-api
```

---

**For detailed info:** Read
`16-INFRASTRUCTURE_DEPLOYMENT.instructions.md`

## 🔐 SECRETS (Never in Code!)

| Secret Type                     | Location                                                                 |
| ------------------------------- | ------------------------------------------------------------------------ |
| API Keys (Stripe, OpenAI, etc.) | `.env` files (gitignored)                                                |
| Database passwords              | `.env` / Google Secret Manager                                           |
| Vercel Project IDs              | GitHub Secrets (`VERCEL_PROJECT_ID_CUSTOMER`, `VERCEL_PROJECT_ID_ADMIN`) |
| JWT/Encryption keys             | `.env` / GSM                                                             |

**Reference:** `.env.example` files in each app folder
