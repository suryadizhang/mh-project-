# MyHibachi Backend VPS Deployment Guide

> **⚠️ IMPORTANT - VPS Configuration (February 2026)**
>
> **We now use Docker for all deployments (production & staging).**
>
> - Production API: Port 8000 → `docker-compose.prod.yml`
> - Staging API: Port 8002 → `docker-compose.staging.yml`
> - Apache httpd handles reverse proxy: `/etc/httpd/conf.d/`
> - SSL: Handled by Cloudflare Tunnel (Zero Trust)
> - CI/CD: GitHub Actions with Cloudflare Access SSH
>
> **LEGACY NOTICE**: Sections mentioning systemctl/venv are deprecated.
> Docker is the current deployment method.

## Quick Reference

### Domains & Hosting

| Service           | Domain                           | Hosting                | Port |
| ----------------- | -------------------------------- | ---------------------- | ---- |
| **Production API**| `mhapi.mysticdatanode.net`       | VPS Docker (8000)      | 8000 |
| **Staging API**   | `staging-api.mysticdatanode.net` | VPS Docker (8002)      | 8002 |
| **Admin Panel**   | `admin.mysticdatanode.net`       | Vercel (auto)          | -    |
| **Customer Site** | `myhibachichef.com`              | Vercel (auto)          | -    |

### Backend VPS Configuration

| Item             | Value                    |
| ---------------- | ------------------------ |
| VPS Provider     | IONOS                    |
| IP Address       | `108.175.12.154`         |
| SSH Access       | Cloudflare Tunnel (Zero Trust) |
| Container Runtime| Docker + Compose         |
| Database         | PostgreSQL 13.22 (native)|
| Cache            | Redis (Docker container) |
| Python           | 3.11 (in container)      |

---

## 🐳 Docker Deployment (Current Method)

### Container Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    VPS (108.175.12.154)                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  docker-compose.prod.yml (Production)                    ││
│  │  ├── myhibachi-production-api (8000)                     ││
│  │  └── myhibachi-production-redis                          ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  docker-compose.staging.yml (Staging)                    ││
│  │  ├── myhibachi-staging-api (8002)                        ││
│  │  └── myhibachi-staging-redis                             ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  PostgreSQL 13.22 (Native - NOT containerized)              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Docker Commands

```bash
# SSH into VPS
ssh root@108.175.12.154

# Navigate to backend directory
cd /var/www/vhosts/myhibachichef.com/mhapi.mysticdatanode.net/backend

# ========== PRODUCTION ==========
# View status
docker compose -f docker-compose.prod.yml ps

# Start/rebuild
docker compose -f docker-compose.prod.yml up -d --build

# View logs
docker compose -f docker-compose.prod.yml logs -f production-api

# Restart
docker compose -f docker-compose.prod.yml restart production-api

# Stop
docker compose -f docker-compose.prod.yml down

# ========== STAGING ==========
# View status
docker compose -f docker-compose.staging.yml ps

# Start/rebuild
docker compose -f docker-compose.staging.yml up -d --build

# View logs
docker compose -f docker-compose.staging.yml logs -f staging-api

# Restart
docker compose -f docker-compose.staging.yml restart staging-api

# Stop
docker compose -f docker-compose.staging.yml down
```

### Health Checks

```bash
# Production health
curl http://localhost:8000/health

# Staging health
curl http://localhost:8002/health

# All containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "staging|production|NAMES"
```

---

## 🚀 CI/CD Deployment (Recommended)

**GitHub Actions automatically deploys on push:**

| Branch | Environment | Workflow File |
|--------|-------------|---------------|
| `dev`  | Staging     | `.github/workflows/deploy-backend-staging.yml` |
| `main` | Production  | `.github/workflows/deploy-backend-production.yml` |

### Required GitHub Secrets

Configure these in **GitHub → Settings → Secrets and variables → Actions**:

| Secret                   | Description                              | Example                                                                 |
| ------------------------ | ---------------------------------------- | ----------------------------------------------------------------------- |
| `CF_ACCESS_CLIENT_ID`    | Cloudflare Access Service Token ID       | `abc123.access`                                                         |
| `CF_ACCESS_CLIENT_SECRET`| Cloudflare Access Service Token Secret   | `xxxxxxxxxxxxx`                                                         |
| `CF_SSH_HOSTNAME`        | SSH hostname via Cloudflare              | `ssh.mhapi.mysticdatanode.net`                                          |
| `VPS_USER`               | SSH user                                 | `root`                                                                  |
| `VPS_STAGING_PATH`       | Staging backend path                     | `/var/www/vhosts/myhibachichef.com/mhapi.mysticdatanode.net/backend`    |
| `VPS_PRODUCTION_PATH`    | Production backend path                  | `/var/www/vhosts/myhibachichef.com/mhapi.mysticdatanode.net/backend`    |
| `STAGING_API_URL`        | Staging API URL for E2E tests            | `https://staging-api.mysticdatanode.net`                                |

### CI/CD Workflow

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Push to dev │───▶│  Run Tests   │───▶│  Deploy to   │
│   branch     │    │  (pytest)    │    │   Staging    │
└──────────────┘    └──────────────┘    └──────────────┘
                                               │
                                               ▼
                                        ┌──────────────┐
                                        │  E2E Tests   │
                                        │  on Staging  │
                                        └──────────────┘

┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Push to main │───▶│  Run Tests   │───▶│   Manual     │───▶│  Deploy to   │
│   branch     │    │  (pytest)    │    │  Approval    │    │  Production  │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                                                                   │
                                                                   ▼
                                                            ┌──────────────┐
                                                            │ Smoke Tests  │
                                                            └──────────────┘
```

### Manual Trigger

1. Go to GitHub → Actions
2. Select "Deploy Backend to Staging" or "Deploy Backend to Production"
3. Click "Run workflow"

---

## Pre-Deployment Checklist

### On Your Local Machine

- [ ] All code committed to correct branch (`dev` for staging, `main` for production)
- [ ] Tests passing locally: `cd apps/backend && pytest tests/unit -v`
- [ ] Docker builds locally: `docker build -f Dockerfile.vps -t test-build .`
- [ ] GitHub Secrets configured (see table above)

### On VPS (First-Time Setup Only)

- [ ] Docker installed
- [ ] PostgreSQL 13+ installed (native, not containerized)
- [ ] Git repository cloned
- [ ] `.env.production` and `.env.staging` files created
- [ ] Cloudflare Tunnel configured for SSH access

---

# Login to Google Cloud
gcloud auth login

# Set project
gcloud config set project my-hibachi-crm

# Authenticate application default credentials
gcloud auth application-default login
```

### Step 4: Create PostgreSQL Database

```bash
# Switch to postgres user
sudo -u postgres psql

# Run these SQL commands:
CREATE USER myhibachi_user WITH PASSWORD 'generate-secure-password-here';
CREATE DATABASE myhibachi_production OWNER myhibachi_user;
GRANT ALL PRIVILEGES ON DATABASE myhibachi_production TO myhibachi_user;

\c myhibachi_production

-- Create schemas
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS identity;
CREATE SCHEMA IF NOT EXISTS lead;
CREATE SCHEMA IF NOT EXISTS newsletter;
CREATE SCHEMA IF NOT EXISTS ai;

-- Grant privileges
GRANT ALL ON SCHEMA core, identity, lead, newsletter, ai TO myhibachi_user;

\q
```

### Step 5: Store Database URL in GSM

```bash
# Store the DATABASE_URL in Google Secret Manager
echo -n "postgresql://myhibachi_user:YOUR_PASSWORD@localhost:5432/myhibachi_production" | \
  gcloud secrets create DATABASE_URL --data-file=- --replication-policy="automatic"

# Store Redis URL
echo -n "redis://localhost:6379/0" | \
  gcloud secrets create REDIS_URL --data-file=- --replication-policy="automatic"
```

### Step 6: Clone Repository

```bash
# Create directory
mkdir -p /var/www/vhosts/mhapi.mysticdatanode.net/backend
cd /var/www/vhosts/mhapi.mysticdatanode.net/backend

# Clone repo
git clone -b nuclear-refactor-clean-architecture https://github.com/suryadizhang/mh-project-.git .

# Copy backend files
cp -r apps/backend/* .
```

### Step 7: Setup Python Environment

```bash
# Create virtual environment
python3.11 -m venv .venv

# Activate
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install google-cloud-secret-manager

# Deactivate
deactivate
```

### Step 8: Create Production .env File

```bash
cat > .env << 'EOF'
ENVIRONMENT=production
DEBUG=False

# Google Cloud
GCP_PROJECT_ID=my-hibachi-crm
GCP_ENVIRONMENT=prod
USE_GOOGLE_SECRET_MANAGER=true

# Database (fetched from GSM)
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

# URLs
FRONTEND_URL=https://myhibachichef.com
ADMIN_URL=https://admin.mysticdatanode.net
API_URL=https://mhapi.mysticdatanode.net

# CORS
CORS_ORIGINS=https://myhibachichef.com,https://admin.mysticdatanode.net

# Rate Limits
RATE_LIMIT_PUBLIC_PER_MINUTE=20
RATE_LIMIT_AUTH_PER_MINUTE=60

# OpenAI
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=1000

# Email
SMTP_HOST=smtp.ionos.com
SMTP_PORT=587
SMTP_FROM_EMAIL=cs@myhibachichef.com

# RingCentral
RC_SERVER_URL=https://platform.ringcentral.com
RC_BUSINESS_PHONE_NUMBER=+19167408768

# Sentry
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

# Feature Flags (OFF in production)
FEATURE_FLAG_AI_BOOKING_ASSISTANT=false
FEATURE_FLAG_TRAVEL_FEE_V2=false
EOF

# Set permissions
chmod 600 .env
chown www-data:www-data .env
```

### Step 9: Run Database Migrations

```bash
cd /var/www/vhosts/mhapi.mysticdatanode.net/backend
source .venv/bin/activate

# Run migrations
alembic upgrade head

deactivate
```

### Step 10: Setup Systemd Services

```bash
# Create backend service template
cat > /etc/systemd/system/myhibachi-backend@.service << 'EOF'
[Unit]
Description=MyHibachi Backend API (Instance %i)
After=network.target postgresql.service redis-server.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/vhosts/mhapi.mysticdatanode.net/backend
Environment="PORT=800%i"
EnvironmentFile=/var/www/vhosts/mhapi.mysticdatanode.net/backend/.env

ExecStart=/var/www/vhosts/mhapi.mysticdatanode.net/backend/.venv/bin/uvicorn src.main:app \
    --host 127.0.0.1 \
    --port 800%i \
    --workers 2 \
    --log-level info

Restart=always
RestartSec=10s
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

# Reload and enable
systemctl daemon-reload
systemctl enable myhibachi-backend@1.service
systemctl enable myhibachi-backend@2.service
```

### Step 11: Setup Nginx (via Plesk)

In Plesk:

1. Go to **Domains** → **mhapi.mysticdatanode.net** → **Apache & nginx
   Settings**
2. Enable **Proxy mode**
3. Add custom nginx directives:

```nginx
# Upstream configuration
upstream myhibachi_backend {
    least_conn;
    server 127.0.0.1:8001 weight=3;
    server 127.0.0.1:8002 weight=2 backup;
    keepalive 32;
}

# Proxy to backend
location /api/ {
    proxy_pass http://myhibachi_backend;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location /health {
    proxy_pass http://myhibachi_backend;
    access_log off;
}
```

### Step 12: Start Services

```bash
# Start backend instances
systemctl start myhibachi-backend@1.service
systemctl start myhibachi-backend@2.service

# Check status
systemctl status myhibachi-backend@1.service
systemctl status myhibachi-backend@2.service
```

### Step 13: Verify Deployment

```bash
# Test health endpoint
curl http://127.0.0.1:8001/health
curl http://127.0.0.1:8002/health

# Check logs
journalctl -u myhibachi-backend@1 -f
```

---

## Post-Deployment

### Create Remaining GSM Secrets

After deployment, create these manual secrets:

```bash
# Stripe LIVE keys (get from Stripe Dashboard)
echo -n "sk_live_xxx" | gcloud secrets create STRIPE_SECRET_KEY --data-file=-
echo -n "pk_live_xxx" | gcloud secrets create STRIPE_PUBLISHABLE_KEY --data-file=-
echo -n "whsec_xxx" | gcloud secrets create STRIPE_WEBHOOK_SECRET --data-file=-

# Sentry DSN (get from Sentry project)
echo -n "https://xxx@sentry.io/xxx" | gcloud secrets create SENTRY_DSN --data-file=-
```

### SSL Certificate

In Plesk:

1. Go to **SSL/TLS Certificates**
2. Install Let's Encrypt certificate for `mhapi.mysticdatanode.net`
3. Enable HTTPS redirect

---

## Useful Commands (Docker)

```bash
# View all running containers
docker ps

# View logs (follow)
docker compose -f docker-compose.prod.yml logs -f production-api

# Check container resource usage
docker stats

# Prune old images (cleanup)
docker system prune -a --volumes

# Full deploy (after code changes) - MANUAL
cd /var/www/vhosts/myhibachichef.com/mhapi.mysticdatanode.net/backend
git pull origin main
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build

# View database
sudo -u postgres psql -d myhibachi_production
```

---

## 🗃️ LEGACY: Systemd Deployment (Deprecated)

> **⚠️ DEPRECATED**: The following sections describe the old systemd-based
> deployment. We now use Docker. These are kept for reference only.

<details>
<summary>Click to expand legacy systemd documentation</summary>

### Legacy Step: Setup Python Environment

```bash
# Create virtual environment
python3.11 -m venv .venv

# Activate
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Deactivate
deactivate
```

### Legacy Step: Setup Systemd Services

```bash
# Create backend service template
cat > /etc/systemd/system/myhibachi-backend@.service << 'EOF'
[Unit]
Description=MyHibachi Backend API (Instance %i)
After=network.target postgresql.service redis-server.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/vhosts/mhapi.mysticdatanode.net/backend
Environment="PORT=800%i"
EnvironmentFile=/var/www/vhosts/mhapi.mysticdatanode.net/backend/.env

ExecStart=/var/www/vhosts/mhapi.mysticdatanode.net/backend/.venv/bin/uvicorn src.main:app \
    --host 127.0.0.1 \
    --port 800%i \
    --workers 2 \
    --log-level info

Restart=always
RestartSec=10s
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

# Reload and enable
systemctl daemon-reload
systemctl enable myhibachi-backend@1.service
```

### Legacy Commands

```bash
# View logs
journalctl -u myhibachi-backend@1 -f

# Restart service
systemctl restart myhibachi-backend@1

# Check all services
systemctl status myhibachi-backend@*
```

</details>

---

## GitHub Actions Auto-Deploy Setup (Recommended)

Instead of manual deployments, use GitHub Actions for automated CI/CD.

### Benefits

- ✅ Automatic deployment on push to `main`
- ✅ Runs tests before deploying
- ✅ Zero-downtime rolling restarts
- ✅ Automatic rollback on failure
- ✅ Full audit trail in GitHub

### Step 1: Generate SSH Key on VPS

```bash
# On your VPS, generate a deployment key
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_deploy_key -N ""

# Add the PUBLIC key to authorized_keys
cat ~/.ssh/github_deploy_key.pub >> ~/.ssh/authorized_keys

# Display the PRIVATE key (you'll copy this to GitHub)
cat ~/.ssh/github_deploy_key
```

### Step 2: Add Secrets to GitHub

Go to: **GitHub Repo → Settings → Secrets and variables → Actions →
New repository secret**

Add these secrets:

| Secret Name       | Value                                              |
| ----------------- | -------------------------------------------------- |
| `VPS_HOST`        | `108.175.12.154`                                   |
| `VPS_USER`        | `myhibachichef.com`                                |
| `VPS_SSH_KEY`     | (paste entire private key from Step 1)             |
| `VPS_DEPLOY_PATH` | `/var/www/vhosts/mhapi.mysticdatanode.net/backend` |

### Step 3: Grant sudo without password for service restart

On VPS, allow the deploy user to restart services without password:

```bash
# Edit sudoers
sudo visudo

# Add this line at the end:
myhibachichef.com ALL=(ALL) NOPASSWD: /bin/systemctl restart myhibachi-backend@*, /bin/systemctl status myhibachi-backend@*
```

### Step 4: Test the Workflow

1. Make a small change to `apps/backend/`
2. Commit and push to `main` branch
3. Go to GitHub → Actions tab
4. Watch the "Deploy Backend to VPS" workflow run

### Workflow Files Created

- `.github/workflows/deploy-backend.yml` - Production deploy (main
  branch)
- `.github/workflows/deploy-backend-staging.yml` - Staging deploy (dev
  branch)

### Manual Trigger

You can also trigger deployment manually:

1. Go to GitHub → Actions
2. Select "Deploy Backend to VPS"
3. Click "Run workflow"
4. Select environment (production/staging)

---

## Troubleshooting

### Service won't start

```bash
journalctl -u myhibachi-backend@1 -n 50
```

### Database connection issues

```bash
# Test PostgreSQL
psql -U myhibachi_user -d myhibachi_production -c "SELECT 1;"
```

### Redis issues

```bash
redis-cli ping
```

### GSM authentication

```bash
gcloud auth application-default print-access-token
```
