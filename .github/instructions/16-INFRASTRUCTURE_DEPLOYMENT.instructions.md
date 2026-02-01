---
applyTo: 'scripts/**,docker/**,.github/workflows/**,configs/**,database/migrations/**,Dockerfile,docker-compose.yml,*.conf'
---

# My Hibachi – Infrastructure & Deployment Guide

**Priority: REFERENCE** – Use for all deployment, server, and database
operations.

> **Note:** This file only loads when editing deployment-related
> files. For manual reference, read
> `16-INFRASTRUCTURE_DEPLOYMENT.instructions.md`.

---

## 🏗️ Infrastructure Overview

**Last Updated:** 2024-12-20

```
┌─────────────────────────────────────────────────────────────────┐
│                   MY HIBACHI INFRASTRUCTURE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────┐               │
│  │           IONOS VPS Linux M                  │               │
│  │  ┌─────────────────┬─────────────────┐      │               │
│  │  │  Production     │    Staging      │      │               │
│  │  │  Port 8000      │    Port 8002    │      │               │
│  │  │  4 workers      │    2 workers    │      │               │
│  │  └─────────────────┴─────────────────┘      │               │
│  │  • PostgreSQL 13.22 (2 databases)           │               │
│  │  • Redis                                     │               │
│  │  • IONOS Backup Agent → Cloud Storage       │               │
│  └─────────────────────────────────────────────┘               │
│           │                                                     │
│           │  Cloudflare Tunnel                                  │
│           ▼                                                     │
│  ┌─────────────────────┐    ┌─────────────────────┐            │
│  │    Cloudflare       │    │      Vercel         │            │
│  │  (CDN + Security)   │    │   (Frontend)        │            │
│  │                     │    │                     │            │
│  │  • WAF Protection   │    │  • Customer Site    │            │
│  │  • DDoS Protection  │    │  • Admin Panel      │            │
│  │  • SSL/TLS Full     │    │  • Auto Deploy      │            │
│  │  • Zero Trust Access│    │                     │            │
│  └─────────────────────┘    └─────────────────────┘            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🖥️ Server Details

### Production VPS (IONOS VPS Linux M)

| Property       | Value                         |
| -------------- | ----------------------------- |
| **Provider**   | IONOS                         |
| **Contract**   | 107136891                     |
| **IP Address** | `108.175.12.154`              |
| **SSH User**   | `root` or `myhibachichef.com` |
| **SSH Port**   | `22`                          |
| **OS**         | Linux (Plesk managed)         |
| **Plesk URL**  | `https://108.175.12.154:8443` |

**Services Running:**

- FastAPI Production (port 8000, 4 workers)
- FastAPI Staging (port 8002, 2 workers)
- PostgreSQL 13.22
- Redis
- Nginx (reverse proxy via Plesk)
- IONOS Backup Agent (Acronis)

**Paths:**

```
/var/www/vhosts/myhibachichef.com/mhapi.mysticdatanode.net/backend/api/  # Production API
/var/www/vhosts/myhibachichef.com/mhapi.mysticdatanode.net/staging/      # Staging API
```

### Staging Environment (Same VPS)

**Last Updated:** 2024-12-20

| Property            | Value                        |
| ------------------- | ---------------------------- |
| **Port**            | 8002                         |
| **Workers**         | 2 (vs 4 for production)      |
| **Service**         | `myhibachi-staging.service`  |
| **Database**        | `myhibachi_staging`          |
| **DB User**         | `myhibachi_staging_user`     |
| **Resource Limits** | CPUQuota=25%, MemoryMax=768M |
| **Status**          | ✅ Running                   |

**Staging Commands:**

```bash
# Check staging status
systemctl status myhibachi-staging

# View staging logs
journalctl -u myhibachi-staging -f

# Restart staging
systemctl restart myhibachi-staging

# Test staging health
curl http://127.0.0.1:8002/health
```

---

## 🌐 Domain Configuration

### DNS Registrar: IONOS

| Domain                     | Purpose        | Points To        |
| -------------------------- | -------------- | ---------------- |
| `myhibachichef.com`        | Customer site  | Vercel           |
| `mysticdatanode.net`       | Infrastructure | Various          |
| `mhapi.mysticdatanode.net` | Backend API    | `108.175.12.154` |
| `admin.mysticdatanode.net` | Admin panel    | Vercel           |

### Vercel Deployments

| App               | Domain                     | Branch |
| ----------------- | -------------------------- | ------ |
| **Customer Site** | `myhibachichef.com`        | `main` |
| **Admin Panel**   | `admin.mysticdatanode.net` | `main` |

---

## 🗄️ Database Configuration

### 🔴 CRITICAL: Database Environment Separation

**NEVER mix environments. Production = real customer data ONLY.**

| Environment    | Database               | Port | Purpose                 |
| -------------- | ---------------------- | ---- | ----------------------- |
| **Staging**    | `myhibachi_staging`    | 8002 | Testing, QA, migrations |
| **Production** | `myhibachi_production` | 8000 | Real customer data ONLY |

**Rules:**

- ✅ Run all tests against `myhibachi_staging`
- ✅ Run migrations on staging first (48+ hours)
- ✅ Create test data in staging only
- ❌ NEVER insert test data into production
- ❌ NEVER run destructive tests on production
- ❌ NEVER use production for API testing

### Production Database (VPS)

| Property     | Value                           |
| ------------ | ------------------------------- |
| **Type**     | PostgreSQL 15                   |
| **Host**     | `localhost` (from VPS)          |
| **Port**     | `5432`                          |
| **Database** | `myhibachi_production`          |
| **User**     | `myhibachi_user`                |
| **Password** | Stored in Google Secret Manager |

**Connection String Format:**

```
postgresql+asyncpg://myhibachi_user:<PASSWORD>@localhost:5432/myhibachi_production
```

**Schemas:**

- `public` – Default tables
- `core` – Core business entities
- `identity` – Users, authentication
- `lead` – Lead management
- `newsletter` – Newsletter subscriptions
- `ai` – AI conversations, messages
- `security` – Security events, alerts

### Staging Database (VPS - ACTIVE)

| Property     | Value                    |
| ------------ | ------------------------ |
| **Type**     | PostgreSQL 13.22         |
| **Host**     | `localhost` (from VPS)   |
| **Port**     | `5432`                   |
| **Database** | `myhibachi_staging`      |
| **User**     | `myhibachi_staging_user` |
| **Password** | `***REMOVED***`          |

**Connection String (on VPS):**

```
postgresql+asyncpg://myhibachi_staging_user:***REMOVED***@localhost:5432/myhibachi_staging
```

### Local Development (SSH Tunnel to Staging) ⭐ PREFERRED

**🚫 DEPRECATED:** Supabase and local SQLite are NO LONGER USED. We
now use an SSH tunnel to connect to the VPS staging database.

| Property       | Value                          |
| -------------- | ------------------------------ |
| **Type**       | PostgreSQL 13.22 (VPS via SSH) |
| **Local Port** | `5433` (tunneled to VPS:5432)  |
| **Database**   | `myhibachi_staging`            |
| **User**       | `myhibachi_staging_user`       |
| **Password**   | `***REMOVED***`                |

**Why SSH Tunnel:**

- ✅ Real PostgreSQL 13.22 (matches production)
- ✅ Same schema as production
- ✅ No DNS resolution issues (Supabase DNS was failing)
- ✅ No SQLite/PostgreSQL compatibility issues
- ✅ All test data stays on staging (never production)

**SSH Tunnel Setup (Required for local dev/tests):**

```powershell
# Option 1: Use the helper script (RECOMMENDED)
.\scripts\start-db-tunnel.ps1          # Start tunnel
.\scripts\start-db-tunnel.ps1 -Status  # Check status
.\scripts\start-db-tunnel.ps1 -Stop    # Stop tunnel

# Option 2: Manual SSH tunnel command
ssh -f -N -L 5433:localhost:5432 root@108.175.12.154
# This forwards localhost:5433 -> VPS:5432
```

**Local .env Configuration:**

```dotenv
DATABASE_URL=postgresql+asyncpg://myhibachi_staging_user:***REMOVED***@127.0.0.1:5433/myhibachi_staging
DATABASE_URL_SYNC=postgresql+psycopg2://myhibachi_staging_user:***REMOVED***@127.0.0.1:5433/myhibachi_staging
```

**Verify Connection:**

```powershell
# Check tunnel is running
netstat -an | Select-String "5433.*LISTENING"

# Test database connection
python -c "from sqlalchemy import create_engine; e = create_engine('postgresql+psycopg2://myhibachi_staging_user:***REMOVED***@127.0.0.1:5433/myhibachi_staging'); print('Connected to:', e.execute('SELECT current_database()').scalar())"
```

**⚠️ Important:** Always start the SSH tunnel before running:

- Backend dev server (`python src/main.py`)
- pytest tests (`python -m pytest tests/`)
- Any database migrations

---

## 🔐 Secrets Management

### Google Secret Manager (GSM)

**Project ID:** `my-hibachi-crm`

**Stored Secrets:** | Secret Name | Purpose |
|-------------|---------| | `DATABASE_URL` | Production DB connection
| | `REDIS_URL` | Redis connection | | `JWT_SECRET` | JWT signing key
| | `STRIPE_SECRET_KEY` | Stripe API key | | `STRIPE_PUBLISHABLE_KEY`
| Stripe public key | | `STRIPE_WEBHOOK_SECRET` | Stripe webhook
validation | | `OPENAI_API_KEY` | OpenAI API key | | `SENTRY_DSN` |
Error tracking |

**Access GSM from VPS:**

```bash
# Authenticate
gcloud auth application-default login

# Read a secret
gcloud secrets versions access latest --secret="DATABASE_URL"
```

### GitHub Actions Secrets

| Secret            | Purpose                                            |
| ----------------- | -------------------------------------------------- |
| `VPS_HOST`        | `108.175.12.154`                                   |
| `VPS_USER`        | SSH username                                       |
| `VPS_SSH_KEY`     | SSH private key                                    |
| `VPS_DEPLOY_PATH` | `/var/www/vhosts/mhapi.mysticdatanode.net/backend` |

### Local Development

**File:** `apps/backend/.env` (gitignored)

⚠️ **NEVER commit actual secrets to Git!**

---

## 🔄 Deployment Workflows

### Backend Deployment (GitHub Actions)

**Trigger:** Push to `main` branch (apps/backend changes)

**Workflow:** `.github/workflows/deploy-backend.yml`

```yaml
# Simplified flow:
1. SSH into VPS 2. Pull latest code 3. Install dependencies 4. Run
migrations 5. Restart services
```

### Frontend Deployment (Vercel)

**Trigger:** Push to `main` branch

**Process:** Automatic via Vercel Git integration

---

## 📦 Database Migrations

### Migration File Location

```
database/migrations/BATCH_1_COMBINED_MIGRATION.sql
```

### Running Migrations

**On Staging (ALWAYS FIRST):**

```bash
# SSH to staging server
ssh root@<staging-ip>

# Backup first
pg_dump myhibachi_staging > backup_$(date +%Y%m%d_%H%M).sql

# Run migration
psql -h localhost -U myhibachi_staging_user -d myhibachi_staging \
  -f BATCH_1_COMBINED_MIGRATION.sql

# Verify
psql -h localhost -U myhibachi_staging_user -d myhibachi_staging \
  -c "SELECT * FROM information_schema.tables WHERE table_schema = 'security';"
```

**On Production (AFTER STAGING VERIFIED):**

```bash
# SSH to production VPS
ssh root@108.175.12.154

# Backup CRITICAL
pg_dump myhibachi_production > backup_$(date +%Y%m%d_%H%M).sql

# Run migration
psql -h localhost -U myhibachi_user -d myhibachi_production \
  -f BATCH_1_COMBINED_MIGRATION.sql
```

---

## 🔒 Security Infrastructure

### Cloudflare Configuration Summary

| Setting           | Value               | Last Updated   |
| ----------------- | ------------------- | -------------- |
| **SSL Mode**      | Full (Strict)       | 2024-12-18     |
| **DDoS**          | Enabled (default)   | Automatic      |
| **Rate Limiting** | 20 req/10sec per IP | Pre-configured |
| **Custom Rules**  | 2/5 active          | 2024-12-18     |

---

### Cloudflare Tunnel (Backend Protection)

**Purpose:** Hide VPS origin IP from public

| Property        | Value                                  |
| --------------- | -------------------------------------- |
| **Tunnel Name** | `myhibachi`                            |
| **Tunnel ID**   | `82034f96-98f7-41a8-b5bf-6976e383113d` |
| **Status**      | Running (4 connections)                |
| **Config Path** | `/etc/cloudflared/config.yml`          |

**Ingress Rules:**

```yaml
ingress:
  - hostname: mhapi.mysticdatanode.net
    service: http://localhost:8000
  - hostname: ssh.mhapi.mysticdatanode.net
    service: ssh://localhost:22
  - service: http_status:404
```

**Tunnel Commands:**

```bash
# Check tunnel status
cloudflared tunnel list

# View tunnel config
cat /etc/cloudflared/config.yml

# Restart tunnel
sudo systemctl restart cloudflared
```

---

### Cloudflare Access (Zero Trust)

**Team Name:** myhibachi (or alternative if taken)

**Application:** MyHibachi Admin Panel

**Protected Paths:** | Path | Purpose | |------|--------| |
`/superadmin` | Super Admin UI | | `/docs` | FastAPI Swagger docs | |
`/redoc` | FastAPI ReDoc |

**Policy:** Super Admin Access

| Setting              | Value     |
| -------------------- | --------- |
| **Action**           | Allow     |
| **Session Duration** | 24 hours  |
| **Authentication**   | Email OTP |

**Authorized Emails:**

- `suryadizhang86@gmail.com`
- `suryadizhang.swe@gmail.com`
- `suryadizhang.chef@gmail.com`

**Note:** Regular Staff/Admin access is via JWT authentication, NOT
Cloudflare Access.

---

### Custom Security Rules (WAF)

**Rule 1: Block SQL Injection** (Active)

```
(http.request.uri.query contains "UNION SELECT") or
(http.request.uri.query contains "DROP TABLE") or
(http.request.uri.query contains "; DELETE") or
(http.request.uri.query contains "1=1")
→ Action: Block
```

**Rule 2: Block XSS Attempts** (Active)

```
(http.request.uri.query contains "<script") or
(http.request.uri.query contains "javascript:") or
(http.request.uri.query contains "onerror=") or
(http.request.uri.query contains "onload=")
→ Action: Block
```

**Rule 3: API Rate Limit** (Pre-existing)

```
Hostname equals mhapi.mysticdatanode.net
→ Action: Block after 20 requests/10 seconds
```

**Remaining Slots:** 3/5 custom rules available

---

### Security Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Layer 1: Cloudflare Edge                                       │
│  ├── DDoS Protection (automatic)                                │
│  ├── Rate Limiting (20 req/10sec)                              │
│  ├── SQL Injection Block (custom rule)                         │
│  ├── XSS Block (custom rule)                                   │
│  └── SSL/TLS Full Strict                                       │
│                                                                  │
│  Layer 2: Cloudflare Access (Zero Trust)                        │
│  ├── /superadmin → Email OTP required                          │
│  ├── /docs → Email OTP required                                │
│  └── /redoc → Email OTP required                               │
│                                                                  │
│  Layer 3: Cloudflare Tunnel                                     │
│  └── VPS IP hidden, traffic via encrypted tunnel               │
│                                                                  │
│  Layer 4: Application (FastAPI)                                 │
│  ├── JWT Authentication                                        │
│  ├── RBAC (5-tier: Super Admin → Admin → Customer Support     │
│  │        → Station Manager → Chef) with role-specific views  │
│  └── Input validation & sanitization                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Backup Strategy

### IONOS Backup (Acronis Cloud)

**Last Updated:** 2024-12-20

| Setting         | Value                             |
| --------------- | --------------------------------- |
| **Agent**       | Acronis Cyber Protect 25.11.41347 |
| **Service**     | `acronis_mms.service` (running)   |
| **Console**     | US Region - NGCS_46682_0935.admin |
| **Plan Name**   | Mh api database                   |
| **Backup Type** | Files/folders                     |
| **Schedule**    | Daily at 2:00 AM                  |
| **Retention**   | 90 backups                        |
| **Storage**     | IONOS Cloud Storage               |
| **Encryption**  | ✅ Enabled (password in GSM)      |
| **Status**      | ✅ Active                         |

**Paths Backed Up:**

- `/var/www/vhosts/myhibachichef.com/` (all application code)
- `/etc/` (system configuration)

**Backup Console Access:**

1. Go to: https://my.ionos.com/ → Server & Cloud → Backups
2. Click "Access to Backup Console" (United States)
3. Login: `NGCS_46682_0935.admin`

**Backup Agent Commands:**

```bash
# Check agent status
systemctl status acronis_mms

# List backup activities
acrocmd list activities

# View agent logs
journalctl -u acronis_mms -f
```

**Recovery Process:**

1. Log into IONOS Backup Console
2. Select `localhost.local`
3. Click "Recover"
4. Choose backup point and files to restore

**Encryption Password:** Stored in Google Secret Manager as
`IONOS_BACKUP_PASSWORD`

### Database Backups (Manual/Cron)

**For point-in-time recovery, use pg_dump:**

```bash
# Manual database backup
pg_dump -U myhibachi_user myhibachi_production | gzip > backup_$(date +%Y%m%d_%H%M).sql.gz

# Restore from backup
gunzip -c backup_file.sql.gz | psql -U myhibachi_user myhibachi_production
```

### Backup Verification

**Weekly:** Restore to staging and verify data integrity

---

## 🚀 SSH Quick Reference

### Connect to Production VPS

```powershell
# From local machine
ssh root@108.175.12.154

# Or with specific key
ssh -i ~/.ssh/myhibachi_deploy root@108.175.12.154
```

### Common SSH Operations

```bash
# Check backend status
sudo systemctl status myhibachi-backend@8001

# View backend logs
sudo journalctl -u myhibachi-backend@8001 -f

# Restart backend
sudo systemctl restart myhibachi-backend@8001

# Check PostgreSQL
sudo systemctl status postgresql

# Check Redis
redis-cli ping
```

---

## 🔧 Service Management

### Backend Service (systemd)

**Service File:** `/etc/systemd/system/myhibachi-backend@.service`

```ini
[Unit]
Description=MyHibachi Backend on port %i
After=network.target postgresql.service redis.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/vhosts/mhapi.mysticdatanode.net/backend
EnvironmentFile=/var/www/vhosts/mhapi.mysticdatanode.net/backend/.env
ExecStart=/var/www/vhosts/mhapi.mysticdatanode.net/backend/.venv/bin/uvicorn \
    src.main:app --host 0.0.0.0 --port %i
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Commands:**

```bash
# Start
sudo systemctl start myhibachi-backend@8001

# Stop
sudo systemctl stop myhibachi-backend@8001

# Restart
sudo systemctl restart myhibachi-backend@8001

# Enable on boot
sudo systemctl enable myhibachi-backend@8001
```

---

## 📋 Environment-Specific Configuration

### Production (.env.production)

```env
ENVIRONMENT=production
DEBUG=False
USE_GOOGLE_SECRET_MANAGER=true
GCP_PROJECT_ID=my-hibachi-crm

# URLs
FRONTEND_URL=https://myhibachichef.com
ADMIN_URL=https://admin.mysticdatanode.net
API_URL=https://mhapi.mysticdatanode.net

# CORS
CORS_ORIGINS=https://myhibachichef.com,https://admin.mysticdatanode.net
```

### Staging (.env.staging)

```env
ENVIRONMENT=staging
DEBUG=False

# Database (staging server)
DATABASE_URL=postgresql+asyncpg://myhibachi_staging_user:<PASSWORD>@<staging-ip>:5432/myhibachi_staging

# URLs
FRONTEND_URL=https://staging.myhibachichef.com
API_URL=https://staging-api.mysticdatanode.net
```

### Development (.env)

```env
ENVIRONMENT=development
DEBUG=True

# Database (Supabase temporary)
DATABASE_URL=postgresql+asyncpg://postgres:<PASSWORD>@db.yuchqvpctookhjovvdwi.supabase.co:5432/postgres
```

---

## ✅ Deployment Checklist

### Before Deploying to Production

- [ ] All tests passing locally
- [ ] Migrations tested on staging (48+ hours)
- [ ] Feature flags configured
- [ ] Backup taken
- [ ] Rollback plan ready
- [ ] On-call person notified

### Post-Deployment Verification

- [ ] Health check: `curl https://mhapi.mysticdatanode.net/health`
- [ ] Check logs for errors
- [ ] Verify database connectivity
- [ ] Test critical paths (booking, auth)
- [ ] Monitor for 30 minutes

---

## 🚨 Emergency Procedures

### Backend Down

```bash
# 1. Check service status
ssh root@108.175.12.154
sudo systemctl status myhibachi-backend@8001

# 2. Check logs
sudo journalctl -u myhibachi-backend@8001 -n 100

# 3. Restart service
sudo systemctl restart myhibachi-backend@8001

# 4. If still failing, check dependencies
sudo systemctl status postgresql
sudo systemctl status redis
```

### Database Connection Issues

```bash
# Check PostgreSQL
sudo systemctl status postgresql
sudo -u postgres psql -c "SELECT 1;"

# Check connections
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"

# Restart if needed
sudo systemctl restart postgresql
```

### Rollback Deployment

```bash
# On VPS
cd /var/www/vhosts/mhapi.mysticdatanode.net/backend

# Revert to previous release
git log --oneline -5  # Find good commit
git checkout <good-commit>

# Restart
sudo systemctl restart myhibachi-backend@8001
```

---

## 🔗 Related Documentation

- `VPS_DEPLOYMENT_GUIDE.md` – Detailed VPS setup
- `docs/04-DEPLOYMENT/PLESK_DEPLOYMENT_SETUP_GUIDE.md` – Plesk
  specifics
- `docs/04-DEPLOYMENT/CLOUDFLARE_TUNNEL_GUIDE.md` – Cloudflare setup
- `docs/04-DEPLOYMENT/DATABASE_SETUP_GUIDE.md` – Database setup
- `GSM_IMPLEMENTATION_COMPLETE.md` – Google Secret Manager

---

## � Future: GPU Server Migration (PREPARATION ONLY)

**Status:** ⏳ PREPARING (NOT provisioned yet) **Target:** When shadow
learning reaches 50K+ pairs AND company revenue supports

### Why GPU Server?

Current VPS (IONOS VPS Linux M):

- 2 vCPU, 4GB RAM, 120GB NVMe
- ❌ NO GPU - Cannot run local LLMs efficiently
- ✅ Fine for API + Database workloads

GPU Server Benefits:

- Run DeepSeek R1 32B, Qwen3 32B locally (no API costs!)
- Fine-tune custom models with collected data
- Single server for everything (API, DB, AI)
- Save $500+/month on API calls after 50K+ conversations

### GPU Cloud Provider Comparison

**Last Updated:** 2024-12-21

| Provider         | RTX 3090 | RTX 4090 | A100 80GB | Notes                  |
| ---------------- | -------- | -------- | --------- | ---------------------- |
| **Vast.ai**      | $0.13/hr | $0.31/hr | $0.65/hr  | Cheapest, peer-to-peer |
| **RunPod**       | $0.22/hr | $0.34/hr | $1.19/hr  | More reliable          |
| **Paperspace**   | N/A      | N/A      | ~$3.00/hr | Enterprise features    |
| **Google Cloud** | N/A      | N/A      | ~$3.50/hr | Per-second billing     |

**Recommended for My Hibachi:**

- **Vast.ai RTX 4090** - $0.31/hr × 24hr × 30 days = **~$223/month**
- Can run: DeepSeek R1 32B, Qwen3 32B, PostgreSQL, Redis, FastAPI
- 24GB VRAM sufficient for inference + light training

### Unified GPU Server Architecture (FUTURE)

```
┌─────────────────────────────────────────────────────────────────┐
│              FUTURE: UNIFIED GPU SERVER                          │
│              (When ready to migrate)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────┐               │
│  │        Vast.ai RTX 4090 GPU Server           │               │
│  │  ┌─────────────────────────────────────┐    │               │
│  │  │           LOCAL AI MODELS            │    │               │
│  │  │  • DeepSeek R1 32B (reasoning)       │    │               │
│  │  │  • Qwen3 32B (function calling)      │    │               │
│  │  │  • Phi-4 14B (fast FAQ)              │    │               │
│  │  │  • Custom LoRA adapters              │    │               │
│  │  └─────────────────────────────────────┘    │               │
│  │                                              │               │
│  │  ┌───────────┬───────────┬───────────┐     │               │
│  │  │  FastAPI  │PostgreSQL │   Redis   │     │               │
│  │  │  Port 8000│  Port 5432│ Port 6379 │     │               │
│  │  └───────────┴───────────┴───────────┘     │               │
│  │                                              │               │
│  │  Specs: RTX 4090 24GB | 64GB RAM | 16 cores │               │
│  └─────────────────────────────────────────────┘               │
│           │                                                     │
│           │  Cloudflare Tunnel (keep existing)                  │
│           ▼                                                     │
│  ┌─────────────────────────────────────────────┐               │
│  │    Same Cloudflare setup (no change)         │               │
│  └─────────────────────────────────────────────┘               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Migration Checklist (FOR FUTURE - DO NOT DO YET)

```markdown
PRE-MIGRATION REQUIREMENTS □ Shadow learning has collected 50,000+
training pairs □ Local model achieves 90%+ similarity to GPT-4 □
Monthly API costs exceed $300 (break-even threshold) OR company
revenue supports ~$250/month extra server cost □ Current VPS contract
can be cancelled or downgraded

$300/MONTH API COST THRESHOLD RULE: ├─ If API costs < $300/mo → STAY
ON API (OpenAI, Mistral, Claude) ├─ If API costs > $300/mo → Consider
GPU server (~$223/mo) └─ Break-even: $300 API - $223 GPU = $77/mo
savings + unlimited usage

MIGRATION STEPS (WHEN READY) □ Step 1: Provision GPU server (Vast.ai
or RunPod) □ Step 2: Install Docker + docker-compose □ Step 3: Set up
PostgreSQL + Redis + Ollama + FastAPI □ Step 4: Migrate database from
VPS to GPU server □ Step 5: Update Cloudflare Tunnel to point to new
server □ Step 6: Pull AI models: ollama pull deepseek-r1:32b □ Step 7:
Test all endpoints □ Step 8: Update DNS records □ Step 9: Monitor for
48 hours □ Step 10: Terminate old VPS

KEEP CURRENT VPS UNTIL □ Shadow learning data collection complete (50K
pairs) □ Free-tier training proves model quality (90%+ accuracy) □ GPU
server stable for 1+ week □ All endpoints tested in production
```

### Free-Tier Training Platforms

**Use these FIRST before investing in GPU server:**

| Platform         | GPU       | Free Hours       | VRAM | Use For                |
| ---------------- | --------- | ---------------- | ---- | ---------------------- |
| **Kaggle**       | P100/T4x2 | 30 hrs/week      | 16GB | LoRA training          |
| **Google Colab** | T4        | Limited sessions | 16GB | Experiments            |
| **HF ZeroGPU**   | H200      | Dynamic          | 70GB | Inference testing      |
| **Colab Pro**    | A100      | 100 units        | 40GB | Full training ($10/mo) |

**Training Workflow (Free Tier):**

1. Export cleaned training data (50K+ pairs)
2. Upload to Kaggle dataset
3. Run LoRA training in Kaggle notebook
4. Download LoRA adapter weights
5. Test with Ollama locally
6. If 90%+ accuracy → deploy to production

---

## 📝 Quick Commands Cheat Sheet

### 🌐 API URLs (Copy-Paste Ready)

| Environment             | URL                                | Access                  |
| ----------------------- | ---------------------------------- | ----------------------- |
| **Production External** | `https://mhapi.mysticdatanode.net` | Public (via Cloudflare) |
| **Production Internal** | `http://127.0.0.1:8000`            | VPS only                |
| **Staging Internal**    | `http://127.0.0.1:8002`            | VPS only                |
| **Customer Site**       | `https://myhibachichef.com`        | Public (Vercel)         |
| **Admin Panel**         | `https://admin.mysticdatanode.net` | Public (Vercel)         |

### 🔑 SSH Access

```bash
# SSH to VPS (from any terminal)
ssh root@108.175.12.154

# SSH with specific key (if needed)
ssh -i ~/.ssh/myhibachi_deploy root@108.175.12.154
```

### 💚 Health Checks (PowerShell - Windows)

```powershell
# Production API health check (external via Cloudflare)
Invoke-RestMethod -Uri "https://mhapi.mysticdatanode.net/health" -Method GET

# Alternative with Invoke-WebRequest
Invoke-WebRequest -Uri "https://mhapi.mysticdatanode.net/health" -Method GET

# Check API docs endpoint
Invoke-RestMethod -Uri "https://mhapi.mysticdatanode.net/docs" -Method GET
```

### 💚 Health Checks (Bash/Linux/VPS)

```bash
# External production health (from anywhere)
curl https://mhapi.mysticdatanode.net/health

# Internal production health (from VPS only)
curl http://127.0.0.1:8000/health

# Internal staging health (from VPS only)
curl http://127.0.0.1:8002/health

# Verbose health check (shows HTTP status)
curl -v http://127.0.0.1:8000/health
```

### � Service Management with Docker (PRIMARY - Run on VPS after SSH)

```bash
# ═══════════════════════════════════════════════════════════
# DOCKER DEPLOYMENT (RECOMMENDED)
# We now use Docker for all environments
# ═══════════════════════════════════════════════════════════

# Navigate to project directory
cd /var/www/vhosts/myhibachichef.com/mhapi.mysticdatanode.net/backend/api

# ═══════════════════════════════════════════════════════════
# PRODUCTION SERVICE (docker-compose.prod.yml)
# ═══════════════════════════════════════════════════════════

# Check production status
docker compose -f docker-compose.prod.yml ps

# Start/restart production (rebuilds if needed)
docker compose -f docker-compose.prod.yml up -d --build

# Restart production only
docker compose -f docker-compose.prod.yml restart production-api

# Stop production
docker compose -f docker-compose.prod.yml stop production-api

# View production logs (last 50 lines)
docker compose -f docker-compose.prod.yml logs --tail=50 production-api

# Follow production logs live
docker compose -f docker-compose.prod.yml logs -f production-api

# ═══════════════════════════════════════════════════════════
# STAGING SERVICE (docker-compose.yml with profile)
# ═══════════════════════════════════════════════════════════

# Check staging status
docker compose ps

# Start/restart staging
docker compose --profile development up -d --build

# Restart staging only
docker compose restart unified-backend

# View staging logs
docker compose logs --tail=50 unified-backend

# Follow staging logs live
docker compose logs -f unified-backend
```

### 🔧 Legacy Service Management (FALLBACK ONLY - If Docker unavailable)

```bash
# ═══════════════════════════════════════════════════════════
# PRODUCTION SERVICE (myhibachi-backend.service) - LEGACY
# ═══════════════════════════════════════════════════════════

# Check production status
sudo systemctl status myhibachi-backend.service

# Restart production
sudo systemctl restart myhibachi-backend.service

# View production logs (last 50 lines)
sudo journalctl -u myhibachi-backend.service -n 50

# Follow production logs live
sudo journalctl -u myhibachi-backend.service -f

# ═══════════════════════════════════════════════════════════
# STAGING SERVICE (myhibachi-staging.service) - LEGACY
# ═══════════════════════════════════════════════════════════

# Check staging status
sudo systemctl status myhibachi-staging.service

# Restart staging
sudo systemctl restart myhibachi-staging.service

# View staging logs (last 50 lines)
sudo journalctl -u myhibachi-staging.service -n 50

# Follow staging logs live
sudo journalctl -u myhibachi-staging.service -f
```

### 📦 Git Deployment with Docker (PRIMARY - Run on VPS after SSH)

```bash
# Navigate to backend directory
cd /var/www/vhosts/myhibachichef.com/mhapi.mysticdatanode.net/backend/api

# Pull latest code from main
git pull origin main

# Rebuild and restart with Docker (preferred)
docker compose -f docker-compose.prod.yml up -d --build

# Verify health after restart
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8002/health
```

### 📦 Git Deployment with systemd (LEGACY FALLBACK)

```bash
# Navigate to backend directory
cd /var/www/vhosts/myhibachichef.com/mhapi.mysticdatanode.net/backend/api

# Pull latest code from main
git pull origin main

# Activate virtual environment
source .venv/bin/activate

# Install/update dependencies
pip install -r requirements.txt

# Restart services after deployment
sudo systemctl restart myhibachi-backend.service
sudo systemctl restart myhibachi-staging.service

# Verify health after restart
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8002/health
```

### 🗄️ Database Commands (Run on VPS after SSH)

```bash
# Backup production database
pg_dump -U myhibachi_user myhibachi_production > backup_$(date +%Y%m%d_%H%M).sql

# Backup staging database
pg_dump -U myhibachi_staging_user myhibachi_staging > staging_backup_$(date +%Y%m%d_%H%M).sql

# Run migration on staging (ALWAYS FIRST!)
sudo -u postgres psql -d myhibachi_staging -f /path/to/migration.sql

# Run migration on production (after staging verified)
sudo -u postgres psql -d myhibachi_production -f /path/to/migration.sql

# Check PostgreSQL status (NOTE: PostgreSQL stays VPS-native for data safety)
sudo systemctl status postgresql

# Check Redis status (Docker or VPS-native)
docker compose -f docker-compose.prod.yml exec redis redis-cli ping  # Docker
redis-cli ping  # VPS-native fallback
```

### 🔥 Emergency Commands with Docker (PRIMARY)

```bash
# Quick restart production service
docker compose -f docker-compose.prod.yml restart production-api

# Check if container is running
docker compose -f docker-compose.prod.yml ps

# View last errors in production
docker compose -f docker-compose.prod.yml logs --tail=50 production-api | grep -i error

# Kill and restart if frozen
docker compose -f docker-compose.prod.yml stop production-api
docker compose -f docker-compose.prod.yml up -d production-api

# Full stack restart (nuclear option)
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build
```

### 🔥 Emergency Commands with systemd (LEGACY FALLBACK)

```bash
# Quick restart both services
sudo systemctl restart myhibachi-backend.service && sudo systemctl restart myhibachi-staging.service

# Check if services are running
sudo systemctl is-active myhibachi-backend.service
sudo systemctl is-active myhibachi-staging.service

# View last errors in production
sudo journalctl -u myhibachi-backend.service -p err -n 20

# Kill and restart if frozen
sudo systemctl stop myhibachi-backend.service
sudo systemctl start myhibachi-backend.service
```

### 📋 Full Deployment Workflow with Docker (RECOMMENDED)

**Step 1: From Local Machine (PowerShell)**

```powershell
# Navigate to project
cd "C:\Users\surya\projects\MH webapps"

# Check status and commit
git status
git add .
git commit -m "feat(batch-X): your message"
git push origin main
```

**Step 2: On VPS (After SSH) - Docker Deployment**

```bash
# Full Docker deployment sequence
cd /var/www/vhosts/myhibachichef.com/mhapi.mysticdatanode.net/backend/api
git pull origin main
docker compose -f docker-compose.prod.yml up -d --build
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8002/health
```

**Step 3: Verify from Local (PowerShell)**

```powershell
Invoke-RestMethod -Uri "https://mhapi.mysticdatanode.net/health" -Method GET
```

---

**Remember:**

- Always test on staging first. Never deploy directly to production
  without staging verification.
- **Docker is now the PRIMARY deployment method.** systemd commands
  are kept as fallback only.
- PostgreSQL remains VPS-native (not containerized) for production
  data safety.
