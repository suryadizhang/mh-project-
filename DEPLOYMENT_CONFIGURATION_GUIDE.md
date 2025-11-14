# Deployment Configuration Guide - MyHibachi Project

**Date**: November 12, 2025  
**Project**: MyHibachi Multi-Domain Deployment  
**Architecture**: Backend (VPS) + Admin Frontend (Vercel) + Customer Frontend (Vercel)

---

## 📋 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PRODUCTION ARCHITECTURE                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────┐      ┌────────────────┐                │
│  │  Customer App  │      │   Admin App    │                │
│  │  (Vercel)      │      │   (Vercel)     │                │
│  │ customer.com   │      │  admin.com     │                │
│  └───────┬────────┘      └───────┬────────┘                │
│          │                       │                           │
│          │         API           │                           │
│          └───────────┬───────────┘                           │
│                      │                                       │
│               ┌──────▼──────┐                                │
│               │   Backend   │                                │
│               │    (VPS)    │                                │
│               │  api.com    │                                │
│               └──────┬──────┘                                │
│                      │                                       │
│          ┌───────────┴───────────┐                           │
│          │                       │                           │
│    ┌─────▼─────┐          ┌─────▼─────┐                     │
│    │ PostgreSQL│          │   Redis   │                     │
│    └───────────┘          └───────────┘                     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🖥️ 1. Backend Deployment (VPS - Ubuntu/Debian)

### **Server Requirements**
- **OS**: Ubuntu 22.04 LTS or Debian 12
- **RAM**: Minimum 4GB (8GB recommended for production)
- **CPU**: 2+ cores
- **Storage**: 50GB+ SSD
- **Python**: 3.11+
- **PostgreSQL**: 15+
- **Redis**: 7+

### **Installation Steps**

#### Step 1: System Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip \
  postgresql postgresql-contrib redis-server nginx \
  git curl supervisor certbot python3-certbot-nginx

# Create app user
sudo useradd -m -s /bin/bash myhibachi
sudo usermod -aG sudo myhibachi
```

#### Step 2: PostgreSQL Setup
```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL shell:
CREATE DATABASE myhibachi_prod;
CREATE USER myhibachi_user WITH PASSWORD 'STRONG_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON DATABASE myhibachi_prod TO myhibachi_user;

# Enable pgvector extension
\c myhibachi_prod
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
\q
```

#### Step 3: Redis Setup
```bash
# Configure Redis
sudo nano /etc/redis/redis.conf

# Set these values:
# maxmemory 2gb
# maxmemory-policy allkeys-lru
# requirepass REDIS_STRONG_PASSWORD

# Restart Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

#### Step 4: Application Deployment
```bash
# Switch to app user
sudo su - myhibachi

# Clone repository
git clone https://github.com/your-org/myhibachi-project.git
cd myhibachi-project/apps/backend

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Create .env file
nano .env
```

**Backend `.env` File**:
```bash
# Database
DATABASE_URL=postgresql://myhibachi_user:PASSWORD@localhost:5432/myhibachi_prod
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# Redis
REDIS_URL=redis://:REDIS_PASSWORD@localhost:6379/0

# Security
SECRET_KEY=<generate-with-openssl-rand-hex-32>
JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# API Keys
OPENAI_API_KEY=sk-...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
RINGCENTRAL_CLIENT_ID=...
RINGCENTRAL_CLIENT_SECRET=...
DEEPGRAM_API_KEY=...
SENDGRID_API_KEY=...

# CORS Origins (important!)
CORS_ORIGINS=["https://customer.myhibachi.com","https://admin.myhibachi.com"]

# Environment
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=INFO

# Sentry (optional but recommended)
SENTRY_DSN=https://...@sentry.io/...
```

#### Step 5: Database Migration
```bash
# Run migrations
alembic upgrade head

# Seed initial data (if needed)
python scripts/seed_data.py
```

#### Step 6: Supervisor Configuration
```bash
# Create supervisor config
sudo nano /etc/supervisor/conf.d/myhibachi.conf
```

**Supervisor Config**:
```ini
[program:myhibachi-api]
command=/home/myhibachi/myhibachi-project/apps/backend/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
directory=/home/myhibachi/myhibachi-project/apps/backend
user=myhibachi
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/myhibachi/api.err.log
stdout_logfile=/var/log/myhibachi/api.out.log
environment=PATH="/home/myhibachi/myhibachi-project/apps/backend/.venv/bin"

[program:myhibachi-celery]
command=/home/myhibachi/myhibachi-project/apps/backend/.venv/bin/celery -A celery_worker.celery worker --loglevel=info
directory=/home/myhibachi/myhibachi-project/apps/backend
user=myhibachi
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/myhibachi/celery.err.log
stdout_logfile=/var/log/myhibachi/celery.out.log
```

```bash
# Create log directory
sudo mkdir -p /var/log/myhibachi
sudo chown myhibachi:myhibachi /var/log/myhibachi

# Start services
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start myhibachi-api
sudo supervisorctl start myhibachi-celery
```

#### Step 7: Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/myhibachi-api
```

**Nginx Config**:
```nginx
upstream myhibachi_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.myhibachi.com;

    # Redirect to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.myhibachi.com;

    # SSL certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/api.myhibachi.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.myhibachi.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;

    # Client body size
    client_max_body_size 10M;

    # Proxy settings
    location / {
        proxy_pass http://myhibachi_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_request_buffering off;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://myhibachi_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }

    # Health check endpoint
    location /healthz {
        proxy_pass http://myhibachi_backend;
        access_log off;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/myhibachi-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Get SSL certificate
sudo certbot --nginx -d api.myhibachi.com
```

---

## 🌐 2. Admin Frontend Deployment (Vercel)

### **Vercel Configuration**

#### Step 1: Project Setup
1. **Login to Vercel**: https://vercel.com
2. **Import Repository**: Connect GitHub/GitLab repo
3. **Root Directory**: `apps/admin`
4. **Framework Preset**: Next.js
5. **Domain**: `admin.myhibachi.com`

#### Step 2: Build Settings
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "installCommand": "npm ci",
  "framework": "nextjs",
  "nodeVersion": "20.x"
}
```

#### Step 3: Environment Variables (Vercel Dashboard)
```bash
# API Configuration
NEXT_PUBLIC_API_URL=https://api.myhibachi.com
NEXT_PUBLIC_WS_URL=wss://api.myhibachi.com/ws

# OAuth
NEXT_PUBLIC_GOOGLE_CLIENT_ID=...

# Stripe (Admin)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...

# Sentry (optional)
NEXT_PUBLIC_SENTRY_DSN=https://...@sentry.io/...

# Analytics (optional)
NEXT_PUBLIC_GA_TRACKING_ID=UA-...
```

#### Step 4: vercel.json Configuration
Create `apps/admin/vercel.json`:
```json
{
  "version": 2,
  "regions": ["iad1"],
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/next"
    }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        },
        {
          "key": "Referrer-Policy",
          "value": "strict-origin-when-cross-origin"
        }
      ]
    }
  ],
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://api.myhibachi.com/:path*"
    }
  ]
}
```

#### Step 5: Domain Configuration
1. Go to Vercel Dashboard → Project Settings → Domains
2. Add custom domain: `admin.myhibachi.com`
3. Update DNS records:
   ```
   Type: CNAME
   Name: admin
   Value: cname.vercel-dns.com
   ```

---

## 👥 3. Customer Frontend Deployment (Vercel)

### **Vercel Configuration** (Similar to Admin)

#### Step 1: Project Setup
1. **Root Directory**: `apps/customer`
2. **Framework Preset**: Next.js
3. **Domain**: `www.myhibachi.com` or `myhibachi.com`

#### Step 2: Environment Variables
```bash
# API Configuration
NEXT_PUBLIC_API_URL=https://api.myhibachi.com
NEXT_PUBLIC_WS_URL=wss://api.myhibachi.com/ws

# Stripe (Customer)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...

# Analytics
NEXT_PUBLIC_GA_TRACKING_ID=UA-...
NEXT_PUBLIC_HOTJAR_ID=...

# Feature Flags (optional)
NEXT_PUBLIC_ENABLE_BLOG=true
NEXT_PUBLIC_ENABLE_AI_CHAT=true
```

#### Step 3: vercel.json Configuration
Create `apps/customer/vercel.json`:
```json
{
  "version": 2,
  "regions": ["iad1"],
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/next"
    }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "SAMEORIGIN"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        }
      ]
    }
  ]
}
```

---

## 🔒 4. Security Configuration

### **CORS Settings (Backend)**
Update `apps/backend/core/config.py`:
```python
CORS_ORIGINS = [
    "https://myhibachi.com",
    "https://www.myhibachi.com",
    "https://admin.myhibachi.com",
    "https://api.myhibachi.com"
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
CORS_ALLOW_HEADERS = ["*"]
```

### **API Rate Limiting**
Backend already includes SlowAPI for rate limiting:
```python
# Default: 100 requests per minute per IP
# Override in routes:
@limiter.limit("10/minute")  # Stricter for sensitive endpoints
async def login(...):
    pass
```

### **Environment Variables Security**
- ✅ **Never commit** `.env` files
- ✅ Use **Vercel Environment Variables** for frontends
- ✅ Use **system environment** or **Docker secrets** for backend
- ✅ Rotate secrets **every 90 days**
- ✅ Use **different keys** for dev/staging/prod

---

## 📦 5. Dependencies Management

### **Backend (Python)**
**File**: `apps/backend/requirements.txt`

**Production Dependencies** (minimal set):
```requirements
# Core
fastapi==0.116.1
uvicorn[standard]==0.35.0
pydantic==2.11.7
pydantic-settings==2.0.3

# Database
sqlalchemy==2.0.42
psycopg2-binary==2.9.10
asyncpg==0.30.0
alembic==1.16.4
pgvector==0.4.1

# Redis
redis==7.0.0

# Security
python-jose==3.3.0
passlib==1.7.4
bcrypt==4.1.2
python-multipart==0.0.20
PyJWT==2.8.0

# HTTP & Async
httpx==0.26.0
requests==2.32.4

# AI & ML
openai==1.12.0
sentence-transformers==5.1.2
spacy==3.8.8
faiss-cpu==1.12.0
torch==2.6.0

# Integrations
stripe==7.0.0
twilio==9.8.5
sendgrid==6.12.4
ringcentral==0.9.2
deepgram-sdk==5.3.0

# Background Tasks
celery==5.5.3
flower==2.0.1

# Monitoring
prometheus-client==0.23.1
sentry-sdk==1.39.2

# Utils
python-dotenv==1.0.0
python-dateutil==2.9.0
pytz==2025.2
```

**Development Dependencies** (install separately):
```requirements
pytest==8.4.2
pytest-asyncio==1.2.0
pytest-cov==6.2.1
black==25.1.0
ruff==0.12.11
mypy==1.17.1
pre-commit==4.3.0
```

### **Admin Frontend (Node.js)**
**File**: `apps/admin/package.json` (already complete - see above)

### **Customer Frontend (Node.js)**
**File**: `apps/customer/package.json` (already complete - see above)

---

## 🚀 6. Deployment Workflow

### **Automated Deployment (CI/CD)**

#### GitHub Actions (Recommended)
Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy MyHibachi

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  # Backend Tests
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: cd apps/backend && pip install -r requirements.txt
      - run: cd apps/backend && pytest

  # Admin Frontend Tests
  test-admin:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - run: cd apps/admin && npm ci
      - run: cd apps/admin && npm run lint
      - run: cd apps/admin && npm run typecheck
      - run: cd apps/admin && npm test

  # Customer Frontend Tests
  test-customer:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - run: cd apps/customer && npm ci
      - run: cd apps/customer && npm run lint
      - run: cd apps/customer && npm test

  # Deploy Backend
  deploy-backend:
    needs: [test-backend]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to VPS
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            cd /home/myhibachi/myhibachi-project
            git pull origin main
            cd apps/backend
            source .venv/bin/activate
            pip install -r requirements.txt
            alembic upgrade head
            sudo supervisorctl restart myhibachi-api
            sudo supervisorctl restart myhibachi-celery

  # Deploy Vercel (automatic on push)
```

### **Manual Deployment**

#### Backend
```bash
# SSH to VPS
ssh myhibachi@your-vps-ip

# Pull latest code
cd ~/myhibachi-project
git pull origin main

# Update dependencies
cd apps/backend
source .venv/bin/activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Restart services
sudo supervisorctl restart myhibachi-api
sudo supervisorctl restart myhibachi-celery

# Check status
sudo supervisorctl status
```

#### Frontend (Vercel Auto-Deploy)
Vercel automatically deploys on:
- Push to `main` branch → Production
- Pull request → Preview deployment

---

## 📊 7. Monitoring & Logging

### **Backend Monitoring**

#### Prometheus Metrics
Already integrated in backend:
```python
# Access metrics at: https://api.myhibachi.com/metrics
```

#### Logs
```bash
# View live logs
sudo tail -f /var/log/myhibachi/api.out.log
sudo tail -f /var/log/myhibachi/api.err.log
sudo tail -f /var/log/myhibachi/celery.out.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

#### Sentry Integration
Already configured in backend. Set `SENTRY_DSN` in `.env`.

### **Frontend Monitoring**

#### Vercel Analytics
Enable in Vercel Dashboard → Analytics

#### Sentry (Frontend)
Add to `apps/admin/src/app/layout.tsx` and `apps/customer/src/app/layout.tsx`:
```typescript
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NODE_ENV,
});
```

---

## 🔧 8. Troubleshooting

### **Backend Issues**

#### API Not Responding
```bash
# Check service status
sudo supervisorctl status myhibachi-api

# Check logs
sudo tail -100 /var/log/myhibachi/api.err.log

# Restart service
sudo supervisorctl restart myhibachi-api
```

#### Database Connection Errors
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U myhibachi_user -d myhibachi_prod
```

#### High Memory Usage
```bash
# Check memory
free -h
htop

# Reduce Uvicorn workers in supervisor config
# workers=2 instead of workers=4
```

### **Frontend Issues**

#### Build Failures
```bash
# Check build logs in Vercel Dashboard
# Common issues:
# - Missing environment variables
# - TypeScript errors
# - Missing dependencies

# Test locally
cd apps/admin  # or apps/customer
npm run build
```

#### CORS Errors
- Verify `CORS_ORIGINS` in backend `.env`
- Check browser console for exact error
- Ensure frontend URL matches backend CORS config

---

## ✅ 9. Post-Deployment Checklist

### **Backend**
- [ ] PostgreSQL running and accessible
- [ ] Redis running and password-protected
- [ ] Alembic migrations applied (`alembic current`)
- [ ] Supervisor services running (`supervisorctl status`)
- [ ] Nginx configured with SSL
- [ ] API health check working (`curl https://api.myhibachi.com/healthz`)
- [ ] Logs rotating properly (`/etc/logrotate.d/myhibachi`)
- [ ] Backups configured (PostgreSQL daily backups)
- [ ] Firewall configured (ufw: allow 80, 443, 22 only)
- [ ] Fail2ban configured for SSH protection

### **Admin Frontend**
- [ ] Build succeeds without errors
- [ ] Environment variables set in Vercel
- [ ] Custom domain configured
- [ ] SSL certificate active
- [ ] API calls working (check Network tab)
- [ ] Authentication working
- [ ] Role-based access working

### **Customer Frontend**
- [ ] Build succeeds without errors
- [ ] Environment variables set
- [ ] Custom domain configured
- [ ] SSL certificate active
- [ ] Stripe integration working
- [ ] Blog loading correctly
- [ ] Contact form working

---

## 📞 Support & Maintenance

### **Update Schedule**
- **Security patches**: Weekly
- **Dependency updates**: Monthly
- **Database backups**: Daily (automated)
- **SSL certificate renewal**: Automatic (Let's Encrypt)

### **Contacts**
- DevOps Lead: devops@myhibachi.com
- Backend Issues: backend-team@myhibachi.com
- Frontend Issues: frontend-team@myhibachi.com

---

**Last Updated**: November 12, 2025  
**Version**: 1.0.0  
**Maintained By**: MyHibachi DevOps Team
