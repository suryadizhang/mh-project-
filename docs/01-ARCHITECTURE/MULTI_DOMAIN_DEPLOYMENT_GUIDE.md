# 🌐 Multi-Domain Deployment Guide
**Date:** October 30, 2025  
**Infrastructure:** Vercel Pro + Plesk VPS  
**Domains:** 3 separate domains for clean architecture

---

## 📋 Domain Architecture

### Your 3 Domains:

| Domain | Purpose | Hosting | IP Address | Notes |
|--------|---------|---------|------------|-------|
| **myhibachichef.com** | Customer Frontend | Vercel Pro | Vercel CDN | React/Next.js app |
| **admin.mysticdatanode.net** | Admin Panel | Vercel Pro | Vercel CDN | Admin dashboard |
| **mhapi.mysticdatanode.net** | Backend API | Plesk VPS | 108.175.12.154 | FastAPI backend |

### Why This Architecture?

**Benefits:**
- ✅ **Security**: Separate domains isolate customer/admin access
- ✅ **Performance**: Vercel CDN for frontends, dedicated VPS for API
- ✅ **Scalability**: Can scale each component independently
- ✅ **SEO**: Customer site on primary domain (myhibachichef.com)
- ✅ **Cost-effective**: Vercel FREE for frontends, single VPS for API

---

## 🎯 Deployment Overview

```
┌─────────────────────────────────────────────────────────────┐
│                       DEPLOYMENT FLOW                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  GitHub Repository (main branch)                            │
│           │                                                  │
│           ├──► Vercel (Customer Frontend)                   │
│           │    └─► myhibachichef.com                        │
│           │        ├─ Next.js app                           │
│           │        ├─ Automatic deployment                  │
│           │        ├─ SSL included                          │
│           │        └─ Global CDN                            │
│           │                                                  │
│           ├──► Vercel (Admin Frontend)                      │
│           │    └─► admin.mysticdatanode.net                 │
│           │        ├─ Next.js admin app                     │
│           │        ├─ Automatic deployment                  │
│           │        ├─ SSL included                          │
│           │        └─ Global CDN                            │
│           │                                                  │
│           └──► GitHub Actions (Backend CI/CD)               │
│                └─► Plesk VPS (108.175.12.154)               │
│                    └─► mhapi.mysticdatanode.net             │
│                        ├─ FastAPI backend                   │
│                        ├─ PostgreSQL database               │
│                        ├─ Redis cache                       │
│                        ├─ Nginx reverse proxy               │
│                        └─ Let's Encrypt SSL                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Deployment Steps

### Phase 1: Backend Deployment (VPS) - 90 minutes

#### Step 1.1: Prepare VPS and Domains

**DNS Configuration (Already Done ✅):**
```
Domain: myhibachichef.com
Type: A Record
Value: [Vercel will provide - not 108.175.12.154]

Domain: admin.mysticdatanode.net
Type: A Record
Value: [Vercel will provide - not 108.175.12.154]

Domain: mhapi.mysticdatanode.net
Type: A Record
Value: 108.175.12.154
```

**Important:** Only the API domain (mhapi.mysticdatanode.net) points to VPS!

#### Step 1.2: Login to Plesk Panel

```
URL: https://108.175.12.154:8443
Or: https://mhapi.mysticdatanode.net:8443 (after DNS propagates)
```

#### Step 1.3: Create Website in Plesk

1. Go to **Websites & Domains** → **Add Domain**
2. Domain name: `mhapi.mysticdatanode.net`
3. Document root: `/var/www/vhosts/mhapi.mysticdatanode.net/httpdocs`
4. **Enable SSL** → Let's Encrypt (automatic)
5. Click **OK**

#### Step 1.4: Setup PostgreSQL Database

1. Go to **Databases** → **Add Database**
2. Database name: `myhibachi_prod`
3. Username: `myhibachi_user`
4. Password: Generate strong password (save it!)
5. Click **OK**

**Save connection string:**
```
postgresql+asyncpg://myhibachi_user:YOUR_PASSWORD@localhost:5432/myhibachi_prod
```

#### Step 1.5: Install Python 3.11

```bash
# SSH into VPS
ssh root@108.175.12.154

# Install Python 3.11
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Verify installation
python3.11 --version
```

#### Step 1.6: Setup Backend Directory

```bash
# Create directory structure
sudo mkdir -p /var/www/vhosts/mhapi.mysticdatanode.net/httpdocs/backend
cd /var/www/vhosts/mhapi.mysticdatanode.net/httpdocs/backend

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

#### Step 1.7: Install Redis (Optional but Recommended)

```bash
# Install Redis
sudo apt install -y redis-server

# Configure Redis for security
sudo nano /etc/redis/redis.conf

# Change these lines:
bind 127.0.0.1
protected-mode yes
requirepass YOUR_STRONG_REDIS_PASSWORD

# Restart Redis
sudo systemctl restart redis
sudo systemctl enable redis
```

#### Step 1.8: Create Environment File

```bash
cd /var/www/vhosts/mhapi.mysticdatanode.net/httpdocs/backend

# Create .env file
sudo nano .env
```

**Paste this configuration:**
```bash
# ==========================================
# Production Environment Configuration
# ==========================================

# Application
APP_NAME=My Hibachi Chef CRM
DEBUG=False
ENVIRONMENT=production
API_VERSION=1.0.0

# Server
HOST=0.0.0.0
PORT=8000

# Database (UPDATE WITH YOUR ACTUAL PASSWORD)
DATABASE_URL=postgresql+asyncpg://myhibachi_user:YOUR_PASSWORD_HERE@localhost:5432/myhibachi_prod
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_ECHO=False

# Redis (UPDATE WITH YOUR REDIS PASSWORD)
REDIS_URL=redis://:YOUR_REDIS_PASSWORD@localhost:6379/0

# Security Keys (GENERATE NEW ONES - DO NOT USE THESE!)
# Generate with: openssl rand -hex 32
SECRET_KEY=GENERATE_YOUR_OWN_32_CHAR_SECRET_KEY_HERE_1234567890
ENCRYPTION_KEY=GENERATE_YOUR_OWN_32_CHAR_ENCRYPTION_KEY_HERE_1234567890
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS - CRITICAL: Update for your 3 domains
CORS_ORIGINS=https://myhibachichef.com,https://admin.mysticdatanode.net

# Frontend URLs
FRONTEND_URL=https://myhibachichef.com
ADMIN_URL=https://admin.mysticdatanode.net
CUSTOMER_APP_URL=https://myhibachichef.com

# Business Information
BUSINESS_NAME=my Hibachi LLC
BUSINESS_EMAIL=cs@myhibachichef.com
BUSINESS_PHONE=+19167408768
BUSINESS_CITY=Fremont
BUSINESS_STATE=California

# Email (IONOS)
EMAIL_ENABLED=True
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.ionos.com
SMTP_PORT=587
SMTP_USER=cs@myhibachichef.com
SMTP_PASSWORD=YOUR_IONOS_EMAIL_PASSWORD
SMTP_USE_TLS=True
FROM_EMAIL=cs@myhibachichef.com

# Stripe (GET FROM YOUR STRIPE DASHBOARD)
STRIPE_SECRET_KEY=sk_live_YOUR_LIVE_KEY_HERE
STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_LIVE_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET_HERE

# RingCentral (GET FROM YOUR RINGCENTRAL DASHBOARD)
RC_CLIENT_ID=YOUR_RC_CLIENT_ID
RC_CLIENT_SECRET=YOUR_RC_CLIENT_SECRET
RC_JWT_TOKEN=YOUR_RC_JWT_TOKEN
RC_WEBHOOK_SECRET=YOUR_RC_WEBHOOK_SECRET
RC_SMS_FROM=+19167408768
RC_SERVER_URL=https://platform.ringcentral.com

# OpenAI (GET FROM YOUR OPENAI ACCOUNT)
OPENAI_API_KEY=sk-YOUR_OPENAI_API_KEY_HERE
OPENAI_MODEL=gpt-4
OPENAI_REALTIME_MODEL=gpt-4o-realtime-preview-2024-12-17

# Plaid (GET FROM YOUR PLAID DASHBOARD)
PLAID_CLIENT_ID=YOUR_PLAID_CLIENT_ID
PLAID_SECRET=YOUR_PLAID_SECRET
PLAID_ENV=production

# Google OAuth (GET FROM GOOGLE CLOUD CONSOLE)
GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET=YOUR_GOOGLE_CLIENT_SECRET
GOOGLE_REDIRECT_URI=https://mhapi.mysticdatanode.net/api/auth/google/callback

# Cloudinary (GET FROM YOUR CLOUDINARY ACCOUNT)
CLOUDINARY_CLOUD_NAME=YOUR_CLOUD_NAME
CLOUDINARY_API_KEY=YOUR_API_KEY
CLOUDINARY_API_SECRET=YOUR_API_SECRET

# Sentry Error Tracking (GET FROM SENTRY.IO)
SENTRY_DSN=https://YOUR_SENTRY_DSN@sentry.io/YOUR_PROJECT_ID
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

# Rate Limiting (Production-optimized)
RATE_LIMIT_PUBLIC_PER_MINUTE=20
RATE_LIMIT_PUBLIC_PER_HOUR=1000
RATE_LIMIT_ADMIN_PER_MINUTE=100
RATE_LIMIT_ADMIN_PER_HOUR=5000
RATE_LIMIT_ADMIN_SUPER_PER_MINUTE=200
RATE_LIMIT_ADMIN_SUPER_PER_HOUR=10000

# Feature Flags
ENABLE_RATE_LIMITING=True
ENABLE_AUDIT_LOGGING=True
ENABLE_FIELD_ENCRYPTION=True
ENABLE_WEBSOCKETS=True
ENABLE_AI_AUTO_REPLY=True

# Alternative Payments
ZELLE_EMAIL=myhibachichef@gmail.com
ZELLE_PHONE=+19167408768
VENMO_USERNAME=@myhibachichef
```

**Secure the file:**
```bash
sudo chmod 600 .env
sudo chown www-data:www-data .env
```

#### Step 1.9: Upload Backend Code

**Option A: Manual Upload (First Time)**
```bash
# On your local machine:
cd "C:\Users\surya\projects\MH webapps\apps\backend"

# Create deployment package
tar -czf backend.tar.gz src/ requirements.txt alembic.ini alembic/

# Upload via SCP
scp backend.tar.gz root@108.175.12.154:/var/www/vhosts/mhapi.mysticdatanode.net/httpdocs/backend/

# On VPS: Extract
cd /var/www/vhosts/mhapi.mysticdatanode.net/httpdocs/backend
tar -xzf backend.tar.gz
rm backend.tar.gz
```

**Option B: Git Clone (Recommended)**
```bash
cd /var/www/vhosts/mhapi.mysticdatanode.net/httpdocs/backend

# Clone repository
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git .

# Copy only backend files
cp -r apps/backend/src ./
cp apps/backend/requirements.txt ./
cp apps/backend/alembic.ini ./
cp -r apps/backend/alembic ./
```

#### Step 1.10: Install Dependencies

```bash
cd /var/www/vhosts/mhapi.mysticdatanode.net/httpdocs/backend
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install additional production dependencies
pip install uvicorn[standard] gunicorn
```

#### Step 1.11: Run Database Migrations

```bash
cd /var/www/vhosts/mhapi.mysticdatanode.net/httpdocs/backend
source venv/bin/activate

# Run Alembic migrations
alembic upgrade head

# Verify database tables created
psql -U myhibachi_user -d myhibachi_prod -c "\dt"
```

#### Step 1.12: Setup Supervisor (Process Management)

```bash
# Install Supervisor
sudo apt install -y supervisor

# Create Supervisor config
sudo nano /etc/supervisor/conf.d/myhibachi-backend.conf
```

**Paste this configuration:**
```ini
[program:myhibachi-backend]
directory=/var/www/vhosts/mhapi.mysticdatanode.net/httpdocs/backend
command=/var/www/vhosts/mhapi.mysticdatanode.net/httpdocs/backend/venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/myhibachi-backend.log
stderr_logfile=/var/log/myhibachi-backend-error.log
environment=PYTHONPATH="/var/www/vhosts/mhapi.mysticdatanode.net/httpdocs/backend/src"
```

**Start the service:**
```bash
# Reload Supervisor
sudo supervisorctl reread
sudo supervisorctl update

# Start backend
sudo supervisorctl start myhibachi-backend

# Check status
sudo supervisorctl status myhibachi-backend

# View logs
sudo tail -f /var/log/myhibachi-backend.log
```

#### Step 1.13: Setup Nginx Reverse Proxy

**Plesk creates Nginx config automatically, but we need to customize it:**

```bash
# Edit Nginx config
sudo nano /etc/nginx/conf.d/mhapi.mysticdatanode.net.conf
```

**Add this configuration:**
```nginx
server {
    listen 80;
    listen 443 ssl http2;
    server_name mhapi.mysticdatanode.net;

    # SSL Configuration (Let's Encrypt - managed by Plesk)
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/key.pem;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # API Proxy
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Request size limit
        client_max_body_size 10M;
    }

    # Health check endpoint (for monitoring)
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
```

**Restart Nginx:**
```bash
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
```

#### Step 1.14: Test Backend API

```bash
# Test local connection
curl http://localhost:8000/health

# Test public endpoint
curl https://mhapi.mysticdatanode.net/health

# Expected response:
# {"status":"healthy","service":"unified-api","version":"1.0.0",...}
```

---

### Phase 2: Customer Frontend Deployment (Vercel) - 15 minutes

#### Step 2.1: Login to Vercel

```
URL: https://vercel.com
Login with GitHub
```

#### Step 2.2: Import GitHub Repository

1. Click **Add New Project**
2. Select your GitHub repository
3. Click **Import**

#### Step 2.3: Configure Customer Frontend

**Project Settings:**
- **Framework Preset:** Next.js
- **Root Directory:** `apps/customer`
- **Build Command:** `npm run build`
- **Output Directory:** `.next`
- **Install Command:** `npm install`

**Environment Variables:**
```bash
# Click "Environment Variables" tab
# Add these variables:

NEXT_PUBLIC_API_URL=https://mhapi.mysticdatanode.net
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_KEY_HERE
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=YOUR_GOOGLE_MAPS_KEY
NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME=YOUR_CLOUD_NAME

# Optional (for analytics)
NEXT_PUBLIC_GA_MEASUREMENT_ID=G-XXXXXXXXXX
```

#### Step 2.4: Deploy Customer Frontend

1. Click **Deploy**
2. Wait 2-3 minutes for build
3. Vercel will provide a URL: `your-project.vercel.app`

#### Step 2.5: Add Custom Domain

1. Go to **Settings** → **Domains**
2. Add domain: `myhibachichef.com`
3. Vercel will provide DNS records:
   ```
   Type: A
   Name: @
   Value: 76.76.21.21 (example - use Vercel's actual IP)
   
   Type: CNAME
   Name: www
   Value: cname.vercel-dns.com
   ```

4. Update DNS at your domain registrar
5. Wait 5-10 minutes for DNS propagation
6. Vercel will auto-configure SSL certificate

#### Step 2.6: Test Customer Frontend

```
URL: https://myhibachichef.com

Expected:
✅ Homepage loads
✅ Can browse menu
✅ Can create booking
✅ SSL certificate valid
✅ API calls work
```

---

### Phase 3: Admin Frontend Deployment (Vercel) - 15 minutes

#### Step 3.1: Create Second Vercel Project

1. In Vercel dashboard, click **Add New Project**
2. Select **same GitHub repository** (we'll use a different root directory)
3. Click **Import**

#### Step 3.2: Configure Admin Frontend

**Project Settings:**
- **Framework Preset:** Next.js
- **Root Directory:** `apps/admin`  ← **Different from customer!**
- **Build Command:** `npm run build`
- **Output Directory:** `.next`
- **Install Command:** `npm install`

**Environment Variables:**
```bash
NEXT_PUBLIC_API_URL=https://mhapi.mysticdatanode.net
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_KEY_HERE
NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME=YOUR_CLOUD_NAME
NEXT_PUBLIC_APP_ENV=production

# Optional (for admin analytics)
NEXT_PUBLIC_SENTRY_DSN=https://YOUR_SENTRY_DSN@sentry.io/PROJECT_ID
```

#### Step 3.3: Deploy Admin Frontend

1. Click **Deploy**
2. Wait 2-3 minutes for build
3. Vercel provides URL: `your-admin-project.vercel.app`

#### Step 3.4: Add Custom Domain

1. Go to **Settings** → **Domains**
2. Add domain: `admin.mysticdatanode.net`
3. Vercel provides DNS records:
   ```
   Type: CNAME
   Name: admin
   Value: cname.vercel-dns.com
   ```

4. Update DNS at your domain registrar (mysticdatanode.net)
5. Wait for DNS propagation (5-10 minutes)
6. Vercel auto-configures SSL

#### Step 3.5: Test Admin Frontend

```
URL: https://admin.mysticdatanode.net

Expected:
✅ Admin login page loads
✅ Can login with credentials
✅ Dashboard displays correctly
✅ SSL certificate valid
✅ API calls to mhapi.mysticdatanode.net work
```

---

### Phase 4: CI/CD Setup (GitHub Actions) - 15 minutes

#### Step 4.1: Configure GitHub Secrets

1. Go to GitHub repository
2. **Settings** → **Secrets and variables** → **Actions**
3. Add these secrets:

```bash
# VPS Access
VPS_SSH_KEY=<paste your SSH private key>
VPS_HOST=108.175.12.154
VPS_USER=root

# Optional (for notifications)
SLACK_WEBHOOK_URL=<your slack webhook>
```

#### Step 4.2: GitHub Workflows Already Created ✅

You already have these workflows:
- `.github/workflows/frontend-quality-check.yml` (Vercel deploys automatically)
- `.github/workflows/backend-cicd.yml` (Deploys to VPS)

**But we need to update CORS in the workflow!**

#### Step 4.3: Update Backend CI/CD for New Domains

The workflow will automatically deploy, but first update your `.env` on VPS:

```bash
# SSH into VPS
ssh root@108.175.12.154

# Update .env file
cd /var/www/vhosts/mhapi.mysticdatanode.net/httpdocs/backend
sudo nano .env

# Update CORS line:
CORS_ORIGINS=https://myhibachichef.com,https://admin.mysticdatanode.net

# Restart backend
sudo supervisorctl restart myhibachi-backend
```

#### Step 4.4: Test CI/CD Pipeline

```bash
# On your local machine:
cd "C:\Users\surya\projects\MH webapps"

# Make a small change (test commit)
echo "# Deployment test" >> README.md
git add README.md
git commit -m "test: CI/CD deployment verification"
git push origin main

# Watch GitHub Actions:
# 1. Go to GitHub repository
# 2. Click "Actions" tab
# 3. Watch workflow run
# 4. Backend should deploy automatically in ~2 minutes
```

---

## ✅ Deployment Verification Checklist

### Backend API (mhapi.mysticdatanode.net)

```bash
# Test health endpoint
curl https://mhapi.mysticdatanode.net/health

# Expected:
{"status":"healthy","service":"unified-api",...}

# Test authentication
curl -X POST https://mhapi.mysticdatanode.net/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@myhibachi.com","password":"your_password"}'

# Expected:
{"access_token":"eyJ...","token_type":"bearer"}

# Test CORS from browser console
fetch('https://mhapi.mysticdatanode.net/health')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error)

# Expected: Response without CORS error
```

### Customer Frontend (myhibachichef.com)

- [ ] Homepage loads correctly
- [ ] SSL certificate valid (green padlock)
- [ ] Can view menu items
- [ ] Can create a booking
- [ ] Form validation works
- [ ] API calls succeed (check Network tab)
- [ ] No CORS errors in console
- [ ] Mobile responsive
- [ ] Images load from Cloudinary

### Admin Frontend (admin.mysticdatanode.net)

- [ ] Login page loads
- [ ] SSL certificate valid
- [ ] Can login successfully
- [ ] Dashboard displays data
- [ ] Can create/edit bookings
- [ ] Can manage stations
- [ ] Can view analytics
- [ ] No CORS errors in console
- [ ] API authentication works
- [ ] Role-based access enforced

---

## 🔧 Troubleshooting

### Issue 1: CORS Errors

**Symptom:**
```
Access to fetch at 'https://mhapi.mysticdatanode.net/api/bookings' 
from origin 'https://myhibachichef.com' has been blocked by CORS policy
```

**Solution:**
```bash
# SSH into VPS
ssh root@108.175.12.154

# Update .env
cd /var/www/vhosts/mhapi.mysticdatanode.net/httpdocs/backend
sudo nano .env

# Ensure CORS_ORIGINS includes both domains:
CORS_ORIGINS=https://myhibachichef.com,https://admin.mysticdatanode.net

# Restart backend
sudo supervisorctl restart myhibachi-backend

# Verify change
curl https://mhapi.mysticdatanode.net/health | grep -i cors
```

### Issue 2: Backend Not Responding

**Check if backend is running:**
```bash
sudo supervisorctl status myhibachi-backend

# Should show: RUNNING

# If not running:
sudo supervisorctl start myhibachi-backend

# View logs:
sudo tail -f /var/log/myhibachi-backend.log
```

**Check if port 8000 is listening:**
```bash
sudo netstat -tulpn | grep 8000

# Should show: uvicorn listening on 0.0.0.0:8000
```

**Check Nginx:**
```bash
sudo nginx -t  # Test config
sudo systemctl status nginx  # Check status
sudo systemctl restart nginx  # Restart if needed
```

### Issue 3: SSL Certificate Issues

**Vercel SSL (automatic):**
- Vercel handles SSL automatically
- Wait 5-10 minutes after adding domain
- Check "Domains" tab for status

**VPS SSL (Let's Encrypt via Plesk):**
```bash
# In Plesk:
# 1. Go to Websites & Domains
# 2. Click on mhapi.mysticdatanode.net
# 3. Go to SSL/TLS Certificates
# 4. Click "Install" for Let's Encrypt
# 5. Check "Secure the domain" and "Redirect HTTP to HTTPS"
```

### Issue 4: Database Connection Failed

**Check PostgreSQL:**
```bash
# Test connection
psql -U myhibachi_user -d myhibachi_prod -c "SELECT 1;"

# If password fails:
# 1. Reset password in Plesk
# 2. Update .env file
# 3. Restart backend
```

### Issue 5: Environment Variables Not Loading

**Verify .env file:**
```bash
cd /var/www/vhosts/mhapi.mysticdatanode.net/httpdocs/backend
sudo cat .env | grep DATABASE_URL

# Check file permissions:
ls -la .env
# Should be: -rw------- (600)

# Fix if needed:
sudo chmod 600 .env
sudo chown www-data:www-data .env
```

---

## 📊 Monitoring Setup

### 1. UptimeRobot (FREE - Recommended)

```
URL: https://uptimerobot.com
Setup time: 5 minutes

Monitors to create:
1. API Health Check
   - URL: https://mhapi.mysticdatanode.net/health
   - Interval: Every 5 minutes
   - Alert: Email + SMS on failure

2. Customer Frontend
   - URL: https://myhibachichef.com
   - Interval: Every 5 minutes
   - Alert: Email on failure

3. Admin Frontend
   - URL: https://admin.mysticdatanode.net
   - Interval: Every 5 minutes
   - Alert: Email on failure
```

### 2. Sentry Error Tracking

**Already configured in backend!** Just need to add DSN:

```bash
# Update .env on VPS:
SENTRY_DSN=https://YOUR_SENTRY_DSN@sentry.io/YOUR_PROJECT_ID
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

# Restart backend
sudo supervisorctl restart myhibachi-backend
```

### 3. Papertrail Logs (FREE tier)

```bash
# Install remote_syslog2
cd /tmp
wget https://github.com/papertrail/remote_syslog2/releases/download/v0.20/remote_syslog_linux_amd64.tar.gz
tar xzf remote_syslog*.tar.gz
sudo cp remote_syslog/remote_syslog /usr/local/bin/

# Configure
sudo nano /etc/log_files.yml
```

**Paste:**
```yaml
files:
  - /var/log/myhibachi-backend.log
  - /var/log/nginx/access.log
  - /var/log/nginx/error.log
destination:
  host: logs.papertrailapp.com
  port: YOUR_PAPERTRAIL_PORT
  protocol: tls
```

---

## 💰 Cost Summary

| Service | Plan | Cost | Notes |
|---------|------|------|-------|
| **Vercel (Customer)** | Pro | $20/month | Per team member |
| **Vercel (Admin)** | Pro | Included | Same team |
| **VPS (Plesk)** | Standard | $15/month | Digital Ocean / Hetzner |
| **Domain (.com)** | Registration | $12/year | myhibachichef.com |
| **Domain (.net)** | Registration | $12/year | mysticdatanode.net |
| **SSL Certificates** | Let's Encrypt | FREE | Auto-renewal |
| **GitHub Actions** | Free tier | FREE | 2,000 min/month |
| **UptimeRobot** | Free tier | FREE | 50 monitors |
| **Sentry** | Free tier | FREE | 5K events/month |
| **Papertrail** | Free tier | FREE | 50MB logs/month |
| **TOTAL** | | **~$50/month** | Plus domain renewals |

---

## 🎯 Post-Deployment Tasks

### Week 1
- [ ] Monitor error rates in Sentry
- [ ] Check UptimeRobot alerts
- [ ] Review Papertrail logs daily
- [ ] Test all critical features
- [ ] Verify backups are running
- [ ] Test rate limiting under load

### Week 2
- [ ] Security audit with OWASP ZAP
- [ ] Performance testing with k6
- [ ] Load testing (100 concurrent users)
- [ ] Review and optimize slow endpoints
- [ ] Setup automated alerts
- [ ] Document any issues found

### Month 1
- [ ] Review analytics and usage patterns
- [ ] Optimize database queries if needed
- [ ] Review rate limit settings
- [ ] Security patch updates
- [ ] Backup restoration test
- [ ] Disaster recovery drill

---

## 🚨 Emergency Procedures

### Rollback Backend (if deployment fails)

**Automatic (via CI/CD):**
- GitHub Actions automatically rolls back on health check failure
- Restores previous backup
- Sends notification

**Manual Rollback:**
```bash
# SSH into VPS
ssh root@108.175.12.154

cd /var/www/vhosts/mhapi.mysticdatanode.net/httpdocs/backend

# List backups
ls -la backups/

# Restore latest backup
tar -xzf backups/backup_YYYYMMDD_HHMMSS.tar.gz

# Restart service
sudo supervisorctl restart myhibachi-backend

# Verify health
curl http://localhost:8000/health
```

### Rollback Frontend (Vercel)

```
1. Go to Vercel dashboard
2. Select project (customer or admin)
3. Go to "Deployments" tab
4. Find previous working deployment
5. Click "..." menu → "Promote to Production"
6. Done! Takes ~10 seconds
```

---

## 📞 Support Contacts

**If you encounter issues:**

1. **VPS/Server Issues**
   - Check Plesk Panel: https://108.175.12.154:8443
   - View logs: `/var/log/myhibachi-backend.log`
   - Contact VPS provider support

2. **Vercel Deployment Issues**
   - Check build logs in Vercel dashboard
   - Vercel support: https://vercel.com/support

3. **DNS Issues**
   - Check propagation: https://dnschecker.org
   - Wait 24-48 hours for full propagation
   - Contact domain registrar support

4. **SSL Certificate Issues**
   - Vercel: Automatic (wait 10 minutes)
   - VPS: Plesk Let's Encrypt (renewal automatic)

---

## 🎉 Deployment Complete!

Once all checks pass, you have:

✅ **3 domains deployed:**
- Customer frontend: https://myhibachichef.com
- Admin panel: https://admin.mysticdatanode.net  
- API backend: https://mhapi.mysticdatanode.net

✅ **Security hardened:**
- SSL certificates on all domains
- CORS properly configured
- Rate limiting active
- Security headers in place

✅ **CI/CD automated:**
- Frontend auto-deploys via Vercel
- Backend auto-deploys via GitHub Actions
- Automatic rollback on failure

✅ **Monitoring active:**
- UptimeRobot checking health
- Sentry tracking errors
- Papertrail aggregating logs

**Estimated total deployment time:** 2 hours  
**Congratulations! 🚀 Your multi-domain architecture is live!**
