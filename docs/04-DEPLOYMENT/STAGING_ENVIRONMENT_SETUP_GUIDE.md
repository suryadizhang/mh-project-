# Staging Environment Setup Guide

**Created:** December 31, 2025 **Purpose:** Step-by-step guide for
setting up full staging environment **Applies To:** Batch 2+
deployments (MANDATORY)

---

## 🎯 Overview

This guide covers the complete setup of the staging environment with
**full isolation** from production:

- **Staging API:** `staging-api.mysticdatanode.net` → Port 8002 →
  `myhibachi_staging`
- **Production API:** `mhapi.mysticdatanode.net` → Port 8000 →
  `myhibachi_production`

---

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] Cloudflare account access (DNS management)
- [ ] VPS SSH access (`ssh root@108.175.12.154`)
- [ ] Vercel account access (frontend deployments)
- [ ] Staging database already exists (`myhibachi_staging`)

---

## Step 1: DNS Setup in Cloudflare

### 1.1 Add A Records

Navigate to: **Cloudflare Dashboard → Domain → DNS → Records**

Add these A records:

| Type | Name            | Content (IPv4)   | Proxy Status |
| ---- | --------------- | ---------------- | ------------ |
| A    | `staging-api`   | `108.175.12.154` | ☁️ Proxied   |
| A    | `staging`       | `76.76.21.21`    | ☁️ Proxied   |
| A    | `admin-staging` | `76.76.21.21`    | ☁️ Proxied   |

> **Note:** `76.76.21.21` is Vercel's IP for custom domains.

### 1.2 Verify DNS Propagation

Wait 2-5 minutes, then test:

```bash
# Test DNS resolution
nslookup staging-api.mysticdatanode.net
nslookup staging.myhibachichef.com

# Expected: Should resolve to the correct IPs
```

---

## Step 2: VPS Backend Setup

### 2.1 Create Staging Directory Structure

```bash
ssh root@108.175.12.154

# Create staging directory
mkdir -p /var/www/vhosts/myhibachichef.com/mhapi.mysticdatanode.net/staging
cd /var/www/vhosts/myhibachichef.com/mhapi.mysticdatanode.net/staging

# Clone the repo or copy from production
git clone https://github.com/your-org/mh-webapps.git .
# OR copy from production
cp -r ../apps/backend ./apps/

# Create Python virtual environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r apps/backend/requirements.txt
```

### 2.2 Create Staging Environment File

Create `.env.staging`:

```bash
nano /var/www/vhosts/myhibachichef.com/mhapi.mysticdatanode.net/staging/apps/backend/.env
```

Content:

```env
# Staging Environment Configuration
ENVIRONMENT=staging
DEBUG=true

# Staging Database (ISOLATED from production!)
# Get <STAGING_DB_PASSWORD> from team lead or secure password manager
DATABASE_URL=postgresql+asyncpg://myhibachi_staging_user:<STAGING_DB_PASSWORD>@localhost:5432/myhibachi_staging
DATABASE_URL_SYNC=postgresql+psycopg2://myhibachi_staging_user:<STAGING_DB_PASSWORD>@localhost:5432/myhibachi_staging

# Staging API runs on port 8002
PORT=8002

# Redis (shared, but use different key prefix)
REDIS_URL=redis://localhost:6379/1

# CORS for staging frontends
CORS_ORIGINS=https://staging.myhibachichef.com,https://admin-staging.mysticdatanode.net,http://localhost:3000

# Stripe TEST mode for staging
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_staging_xxx
STRIPE_MODE=test

# JWT (can share with production or use different)
JWT_SECRET=your-staging-jwt-secret-here

# Google Maps (same key, different quota tracking)
GOOGLE_MAPS_API_KEY=xxx

# Feature flags (enable all for testing)
FEATURE_STRIPE_ENABLED=true
FEATURE_AI_CHAT_ENABLED=true
```

### 2.3 Create Systemd Service for Staging

Create the service file:

```bash
sudo nano /etc/systemd/system/myhibachi-staging.service
```

Content:

```ini
[Unit]
Description=MyHibachi Staging API (FastAPI + Uvicorn)
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/vhosts/myhibachichef.com/mhapi.mysticdatanode.net/staging/apps/backend
Environment="PATH=/var/www/vhosts/myhibachichef.com/mhapi.mysticdatanode.net/staging/venv/bin"
Environment="PYTHONPATH=/var/www/vhosts/myhibachichef.com/mhapi.mysticdatanode.net/staging/apps/backend/src"

# Run on port 8002 (staging)
ExecStart=/var/www/vhosts/myhibachichef.com/mhapi.mysticdatanode.net/staging/venv/bin/uvicorn \
    src.main:app \
    --host 0.0.0.0 \
    --port 8002 \
    --workers 2 \
    --log-level info

# Reduced resources for staging (vs production)
MemoryMax=768M
CPUQuota=25%

Restart=always
RestartSec=5

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=myhibachi-staging

[Install]
WantedBy=multi-user.target
```

### 2.4 Enable and Start Staging Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable on boot
sudo systemctl enable myhibachi-staging

# Start the service
sudo systemctl start myhibachi-staging

# Check status
sudo systemctl status myhibachi-staging

# View logs
sudo journalctl -u myhibachi-staging -f
```

### 2.5 Verify Staging API is Running

```bash
# Test locally on VPS
curl http://localhost:8002/health

# Expected response:
# {"status": "healthy", "environment": "staging"}
```

---

## Step 3: Apache Reverse Proxy Configuration (RHEL/CentOS)

> **IMPORTANT:** Our VPS uses RHEL/CentOS with Apache httpd (NOT
> Debian/Ubuntu apache2 or nginx). Cloudflare handles SSL termination,
> so we only configure port 80 on the server.

### 3.1 Create Apache VirtualHost for Staging API

**ACTUAL IMPLEMENTATION (January 2025):**

The staging API config is located at
`/etc/httpd/conf.d/staging-api.conf`:

```bash
sudo nano /etc/httpd/conf.d/staging-api.conf
```

Content (currently deployed):

```apache
<VirtualHost *:80>
    ServerName staging-api.mysticdatanode.net
    ServerAlias staging-api.mysticdatanode.net

    # Proxy to staging FastAPI (port 8002)
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8002/
    ProxyPassReverse / http://127.0.0.1:8002/

    # WebSocket support
    RewriteEngine On
    RewriteCond %{HTTP:Upgrade} websocket [NC]
    RewriteCond %{HTTP:Connection} upgrade [NC]
    RewriteRule ^/?(.*) ws://127.0.0.1:8002/$1 [P,L]

    # Extended timeout for long API calls
    ProxyTimeout 300
</VirtualHost>
```

Enable and reload Apache:

```bash
# Test configuration syntax
sudo apachectl configtest

# Reload Apache (httpd on RHEL/CentOS)
sudo systemctl reload httpd
```

### 3.2 Production API Config Reference

For reference, the production API config is at
`/etc/httpd/conf.d/myhibachi-api.conf`:

- Points to `mhapi.mysticdatanode.net`
- Proxies to `127.0.0.1:8000`

### 3.3 Why Cloudflare Handles SSL

With Cloudflare proxy enabled (☁️):

1. Client → Cloudflare: HTTPS (SSL/TLS)
2. Cloudflare → Server: HTTP (port 80)

This is called "Flexible" or "Full" SSL mode in Cloudflare. We don't
need SSL certificates on the server.

### 3.4 Alternative: Nginx Configuration (NOT CURRENTLY USED)

If using Nginx instead:

```bash
sudo nano /etc/nginx/conf.d/staging-api.conf
```

```nginx
server {
    listen 80;
    server_name staging-api.mysticdatanode.net;

    location / {
        proxy_pass http://127.0.0.1:8002;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo nginx -t
sudo systemctl reload nginx
```

> **Note:** Our VPS uses Apache httpd, NOT nginx. Nginx is not in use.

### 3.3 Alternative: Cloudflare Tunnel (Recommended)

If using Cloudflare Tunnel, update `/etc/cloudflared/config.yml`:

```yaml
tunnel: your-tunnel-id
credentials-file: /root/.cloudflared/your-tunnel-id.json

ingress:
  # Production API
  - hostname: mhapi.mysticdatanode.net
    service: http://localhost:8000

  # Staging API
  - hostname: staging-api.mysticdatanode.net
    service: http://localhost:8002

  # Catch-all
  - service: http_status:404
```

Restart tunnel:

```bash
sudo systemctl restart cloudflared
```

---

## Step 4: Vercel Frontend Staging Setup

### 4.1 Customer App Staging Domain

1. Go to **Vercel Dashboard → customer app project**
2. Navigate to **Settings → Domains**
3. Click **Add Domain**
4. Enter: `staging.myhibachichef.com`
5. Vercel will provide verification instructions

### 4.2 Admin App Staging Domain

1. Go to **Vercel Dashboard → admin app project**
2. Navigate to **Settings → Domains**
3. Click **Add Domain**
4. Enter: `admin-staging.mysticdatanode.net`
5. Verify domain ownership

### 4.3 Configure Staging Environment Variables in Vercel

For each staging deployment, set these environment variables:

**Customer App (staging.myhibachichef.com):**

```
NEXT_PUBLIC_API_URL=https://staging-api.mysticdatanode.net
NEXT_PUBLIC_ENVIRONMENT=staging
```

**Admin App (admin-staging.mysticdatanode.net):**

```
NEXT_PUBLIC_API_URL=https://staging-api.mysticdatanode.net
NEXT_PUBLIC_ENVIRONMENT=staging
```

### 4.4 Create Staging Branch (Optional)

For automatic staging deployments:

1. Create a `staging` branch in your repo
2. In Vercel, go to **Settings → Git**
3. Set production branch: `main`
4. Set preview/staging branch: `staging`

---

## Step 5: Verify Complete Staging Setup

### 5.1 Backend Health Check

```bash
# From your local machine
curl https://staging-api.mysticdatanode.net/health

# Expected: {"status": "healthy", "environment": "staging"}
```

### 5.2 Database Isolation Check

```bash
# SSH to VPS
ssh root@108.175.12.154

# Check production database
sudo -u postgres psql -d myhibachi_production -c "SELECT COUNT(*) FROM core.bookings;"

# Check staging database
sudo -u postgres psql -d myhibachi_staging -c "SELECT COUNT(*) FROM core.bookings;"

# They should show DIFFERENT counts (staging may be empty or have test data)
```

### 5.3 Frontend Connection Check

1. Open `https://staging.myhibachichef.com` in browser
2. Open DevTools → Network tab
3. Verify API calls go to `staging-api.mysticdatanode.net`
4. NOT to `mhapi.mysticdatanode.net`

---

## 📊 Staging vs Production Comparison

| Aspect          | Staging                            | Production                 |
| --------------- | ---------------------------------- | -------------------------- |
| API URL         | `staging-api.mysticdatanode.net`   | `mhapi.mysticdatanode.net` |
| API Port        | 8002                               | 8000                       |
| Database        | `myhibachi_staging`                | `myhibachi_production`     |
| Systemd Service | `myhibachi-staging`                | `myhibachi-api`            |
| Workers         | 2                                  | 4                          |
| Memory Limit    | 768M                               | 2G                         |
| CPU Quota       | 25%                                | 80%                        |
| Stripe Mode     | TEST                               | LIVE                       |
| Customer Site   | `staging.myhibachichef.com`        | `myhibachichef.com`        |
| Admin Site      | `admin-staging.mysticdatanode.net` | `admin.mysticdatanode.net` |

---

## 🚨 Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u myhibachi-staging -n 50

# Check if port 8002 is in use
sudo lsof -i :8002

# Verify Python path
ls -la /var/www/vhosts/.../staging/venv/bin/uvicorn
```

### Database Connection Issues

```bash
# Test database connection
psql -U myhibachi_staging_user -h localhost -d myhibachi_staging

# Check PostgreSQL is running
sudo systemctl status postgresql
```

### 502 Bad Gateway

1. Check if staging service is running:
   `sudo systemctl status myhibachi-staging`
2. Check if port 8002 is listening: `sudo netstat -tlnp | grep 8002`
3. Check Apache/Nginx proxy config

### DNS Not Resolving

1. Wait 5-10 minutes for propagation
2. Clear local DNS cache: `ipconfig /flushdns` (Windows)
3. Check Cloudflare DNS settings

---

## 📋 Quick Reference Commands

```bash
# Staging service management
sudo systemctl start myhibachi-staging
sudo systemctl stop myhibachi-staging
sudo systemctl restart myhibachi-staging
sudo systemctl status myhibachi-staging

# View staging logs
sudo journalctl -u myhibachi-staging -f

# Test staging API
curl https://staging-api.mysticdatanode.net/health

# Check staging database
sudo -u postgres psql -d myhibachi_staging

# Deploy to staging
cd /var/www/.../staging
git pull origin dev
source venv/bin/activate
pip install -r apps/backend/requirements.txt
sudo systemctl restart myhibachi-staging
```

---

## 🔗 Related Documents

- [16-INFRASTRUCTURE_DEPLOYMENT.instructions.md](../../.github/instructions/16-INFRASTRUCTURE_DEPLOYMENT.instructions.md)
- [04-BATCH_DEPLOYMENT.instructions.md](../../.github/instructions/04-BATCH_DEPLOYMENT.instructions.md)
- [CURRENT_BATCH_STATUS.md](../../CURRENT_BATCH_STATUS.md)

---

## 🧪 E2E Testing on Staging

### Overview

The staging environment supports automated E2E testing via Playwright.
This allows testing the full stack (frontend + API + database) in an
isolated environment before production deployment.

### Playwright Configuration Files

| Config File                    | Target Environment     | Command                    |
| ------------------------------ | ---------------------- | -------------------------- |
| `playwright.config.ts`         | Local (localhost:3000) | `npm run test:e2e`         |
| `playwright.staging.config.ts` | Staging                | `npm run test:e2e:staging` |
| `playwright.prod.config.ts`    | Production             | `npm run test:e2e:prod`    |

### Available npm Scripts

```bash
# Run all staging E2E tests
npm run test:e2e:staging

# Run specific project tests
npm run test:e2e:staging:customer  # Customer site desktop
npm run test:e2e:staging:admin     # Admin site desktop
npm run test:e2e:staging:api       # API tests only
npm run test:e2e:staging:mobile    # Customer site mobile

# Production tests (use with caution!)
npm run test:e2e:prod
```

### Staging E2E Test URLs

| Project          | URL                                                      |
| ---------------- | -------------------------------------------------------- |
| Customer Desktop | `https://staging.myhibachichef.com`                      |
| Customer Mobile  | `https://staging.myhibachichef.com` (iPhone 13 viewport) |
| Admin Desktop    | `https://admin-staging.mysticdatanode.net`               |
| API Tests        | `https://staging-api.mysticdatanode.net`                 |

### Environment Variables for E2E

You can override default URLs via environment variables:

```bash
# Override staging URLs
STAGING_URL=https://staging.myhibachichef.com \
STAGING_ADMIN_URL=https://admin-staging.mysticdatanode.net \
STAGING_API_URL=https://staging-api.mysticdatanode.net \
npm run test:e2e:staging
```

### Test Reports

After running staging tests, reports are generated at:

- **HTML Report:** `playwright-report-staging/index.html`
- **JSON Results:** `test-results/staging-results.json`

View the HTML report:

```bash
npx playwright show-report playwright-report-staging
```

---

## 🔒 Vercel Deployment Protection

### The Problem

Vercel's **Deployment Protection** requires authentication for
preview/staging deployments. This blocks:

- ❌ Playwright E2E tests (can't authenticate)
- ❌ AI agents (can't authenticate)
- ❌ CI/CD automated testing

### Solution: Protection Bypass for Automation (Recommended)

**Use Vercel's built-in bypass mechanism for automated testing. This
keeps protection enabled while allowing Playwright tests to pass.**

### Step-by-Step: Create Bypass Secret

#### 1. Create Bypass in Vercel Dashboard

For each project (customer, admin):

1. Go to **Vercel Dashboard** → Select project
2. Click **Settings** → **Deployment Protection**
3. Scroll to **"Protection Bypass for Automation"** section
4. Click **"Add Secret"**
5. Leave secret field **blank** (Vercel auto-generates)
6. Add note: `Playwright E2E staging tests`
7. Click **Add**
8. **Copy the generated secret** (you'll need this!)

#### 2. Configure Local Environment

Add the secret to your local `.env` file (root of project):

```env
# Vercel Deployment Protection bypass (for E2E testing)
VERCEL_AUTOMATION_BYPASS_SECRET=your_generated_secret_here
```

> ⚠️ **Security:** This secret is for development/testing only. Do NOT
> commit to git. It's already in `.gitignore`.

#### 3. How It Works

The Playwright staging config automatically sends the bypass header:

```typescript
// playwright.staging.config.ts (already configured)
extraHTTPHeaders: {
  'X-Test-Environment': 'staging',
  'x-vercel-protection-bypass': process.env.VERCEL_AUTOMATION_BYPASS_SECRET,
},
```

### Protection Matrix

| Environment | Branch     | Vercel Protection | Bypass Header  | Automated Testing  |
| ----------- | ---------- | ----------------- | -------------- | ------------------ |
| Production  | `main`     | ✅ Enabled        | Not used       | ❌ Not recommended |
| Staging     | `dev`      | ✅ Enabled        | ✅ Uses bypass | ✅ Works           |
| Preview     | feature/\* | ✅ Enabled        | Optional       | ⚠️ If bypass set   |

### Security Considerations

**Q: Is bypass safer than disabling protection?**

A: Yes! Bypass keeps protection active for:

- Manual browser visits (still need Vercel login)
- Crawlers and bots
- Unauthorized access attempts

Only requests with the correct header bypass protection.

**Q: What if the secret is leaked?**

A: You can regenerate it in Vercel dashboard anytime. Just update your
local `.env`.

**Q: Should I add this to GSM (Google Secret Manager)?**

A: Not required. This is a development/testing secret:

- Only used in local Playwright tests
- Not needed in production
- Can be regenerated easily

For CI/CD pipelines, add as a GitHub Actions secret:
`VERCEL_AUTOMATION_BYPASS_SECRET`

---

## 🤖 AI Agent Access to Staging

### Overview

AI agents (like Copilot) may need to access staging for:

- Testing API endpoints
- Verifying deployment health
- Running automated checks

### Requirements for AI Access

1. **Vercel Bypass Secret** configured in `.env`
2. **Staging API publicly accessible** (via Cloudflare)
3. **No IP restrictions** on staging endpoints

### Verifying Access

After configuring the bypass secret:

```bash
# Test API access (should work immediately)
curl https://staging-api.mysticdatanode.net/health

# Test frontend access with bypass header
curl -H "x-vercel-protection-bypass: YOUR_SECRET" https://staging.myhibachichef.com
# Should return 200, NOT 401/403

# Run E2E tests
npm run test:e2e:staging
```

### Test Credentials for Staging

See `TEST_CREDENTIALS.local.md` for staging test accounts:

- Admin user credentials
- Customer test accounts
- API keys for testing
