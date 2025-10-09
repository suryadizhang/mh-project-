# Full Production Deployment Analysis

## Current Architecture Overview

### Applications:
1. **Customer Frontend** (`apps/customer`) - Next.js 14 → Deploy to Vercel at `myhibachichef.com`
2. **Admin Panel** (`apps/admin`) - Next.js 14 → Deploy to Vercel subdomain 
3. **Main API** (`apps/api`) - FastAPI Python → Deploy to VPS Plesk
4. **AI API** (`apps/ai-api`) - Python AI services → Deploy to VPS Plesk (different domain)

---

## Deployment Targets

### 1. **Vercel Deployments**

#### Customer Frontend: `myhibachichef.com`
```bash
# Domain: myhibachichef.com
# Build Command: cd apps/customer && npm run build
# Output Directory: apps/customer/.next
# Install Command: npm install
```

#### Admin Panel: `admin.myhibachichef.com` or separate domain
```bash
# Domain: admin.myhibachichef.com
# Build Command: cd apps/admin && npm run build  
# Output Directory: apps/admin/.next
# Install Command: npm install
```

### 2. **VPS Plesk Deployments**

#### Main API: `api.myhibachichef.com`
```bash
# Domain: api.myhibachichef.com
# Technology: FastAPI Python
# Location: apps/api/
# Requirements: requirements.txt
```

#### AI API: `ai.myhibachichef.com`
```bash
# Domain: ai.myhibachichef.com  
# Technology: Python AI services
# Location: apps/ai-api/
# Requirements: requirements.txt
```

---

## Environment Variables Analysis

### **Customer Frontend (Vercel)**
```env
# API Configuration
NEXT_PUBLIC_API_URL=https://api.myhibachichef.com
NEXT_PUBLIC_AI_API_URL=https://ai.myhibachichef.com

# Authentication
NEXTAUTH_SECRET=<random-secret>
NEXTAUTH_URL=https://myhibachichef.com

# Payment Processing
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Communication
RINGCENTRAL_CLIENT_ID=<ringcentral-app-id>
RINGCENTRAL_CLIENT_SECRET=<ringcentral-secret>
RINGCENTRAL_JWT_TOKEN=<jwt-token>
RINGCENTRAL_SANDBOX=false

# Analytics & Marketing
GOOGLE_ANALYTICS_ID=G-...
FACEBOOK_PIXEL_ID=...
META_MESSENGER_APP_ID=...

# Database (if needed for sessions)
DATABASE_URL=postgresql://...

# Email Services
RESEND_API_KEY=re_...
FROM_EMAIL=noreply@myhibachichef.com

# SMS Services (if separate from RingCentral)
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...

# External Services
GOOGLE_MAPS_API_KEY=AIza...
CALENDAR_API_KEY=...
```

### **Admin Panel (Vercel)**
```env
# API Configuration
NEXT_PUBLIC_API_URL=https://api.myhibachichef.com
NEXT_PUBLIC_AI_API_URL=https://ai.myhibachichef.com

# Authentication (Admin)
NEXTAUTH_SECRET=<different-random-secret>
NEXTAUTH_URL=https://admin.myhibachichef.com
ADMIN_SECRET=<admin-access-secret>

# Database
DATABASE_URL=postgresql://...

# All payment and communication variables (same as customer)
STRIPE_SECRET_KEY=sk_live_...
RINGCENTRAL_CLIENT_SECRET=<ringcentral-secret>
# ... (inherit from customer)

# Admin-specific
ADMIN_EMAIL_OVERRIDE=admin@myhibachichef.com
ADMIN_NOTIFICATION_WEBHOOK=...
```

### **Main API (VPS Plesk)**
```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/myhibachi_prod
REDIS_URL=redis://localhost:6379

# Authentication
JWT_SECRET=<jwt-secret>
API_SECRET_KEY=<api-secret>

# Payment Processing
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Communication Services
RINGCENTRAL_CLIENT_ID=<ringcentral-app-id>
RINGCENTRAL_CLIENT_SECRET=<ringcentral-secret>
RINGCENTRAL_JWT_TOKEN=<jwt-token>
RINGCENTRAL_SANDBOX=false
RINGCENTRAL_WEBHOOK_SECRET=<webhook-secret>

# Email Services
RESEND_API_KEY=re_...
SMTP_HOST=smtp.resend.com
SMTP_PORT=587
SMTP_USERNAME=resend
SMTP_PASSWORD=<resend-api-key>

# SMS Services
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...

# External APIs
GOOGLE_MAPS_API_KEY=AIza...
OPENAI_API_KEY=sk-...

# File Storage
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_BUCKET=myhibachi-uploads
AWS_REGION=us-west-2

# Monitoring
SENTRY_DSN=https://...

# Environment
ENVIRONMENT=production
DEBUG=false
CORS_ORIGINS=https://myhibachichef.com,https://admin.myhibachichef.com
```

### **AI API (VPS Plesk)**
```env
# AI Services
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=...
HUGGINGFACE_API_KEY=...

# Database (shared or separate)
DATABASE_URL=postgresql://user:pass@localhost:5432/myhibachi_ai
REDIS_URL=redis://localhost:6379

# Main API Connection
MAIN_API_URL=https://api.myhibachichef.com
API_SECRET_KEY=<shared-secret>

# Authentication
JWT_SECRET=<same-as-main-api>

# File Storage (for AI processing)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_BUCKET=myhibachi-ai-data

# Monitoring
SENTRY_DSN=https://...

# Environment
ENVIRONMENT=production
DEBUG=false
CORS_ORIGINS=https://api.myhibachichef.com,https://myhibachichef.com
```

### **Local Development (.env.local)**
```env
# API Configuration (local)
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_AI_API_URL=http://localhost:8001

# Authentication (development)
NEXTAUTH_SECRET=dev-secret-key
NEXTAUTH_URL=http://localhost:3000

# Payment (Stripe Test)
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_test_...

# Database (local)
DATABASE_URL=postgresql://postgres:password@localhost:5432/myhibachi_dev
REDIS_URL=redis://localhost:6379

# Communication (Sandbox)
RINGCENTRAL_CLIENT_ID=<dev-app-id>
RINGCENTRAL_CLIENT_SECRET=<dev-secret>
RINGCENTRAL_SANDBOX=true

# Email (Development)
RESEND_API_KEY=re_dev_...
FROM_EMAIL=dev@myhibachichef.com

# External Services (Development keys)
GOOGLE_MAPS_API_KEY=AIza..._dev
OPENAI_API_KEY=sk-dev...

# Environment
ENVIRONMENT=development
DEBUG=true
```

---

## Platform-Specific Secret Variables

### **Vercel Environment Variables**

#### Customer Frontend Project:
```bash
# Production Environment
NEXT_PUBLIC_API_URL=https://api.myhibachichef.com
NEXT_PUBLIC_AI_API_URL=https://ai.myhibachichef.com
NEXTAUTH_SECRET=<32-char-secret>
NEXTAUTH_URL=https://myhibachichef.com
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
RINGCENTRAL_CLIENT_ID=<prod-id>
RINGCENTRAL_CLIENT_SECRET=<prod-secret>
GOOGLE_ANALYTICS_ID=G-...
GOOGLE_MAPS_API_KEY=AIza...

# Preview Environment  
NEXT_PUBLIC_API_URL=https://api-staging.myhibachichef.com
NEXTAUTH_URL=https://myhibachi-git-develop.vercel.app
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
RINGCENTRAL_SANDBOX=true
```

#### Admin Panel Project:
```bash
# Production Environment
NEXT_PUBLIC_API_URL=https://api.myhibachichef.com
NEXTAUTH_SECRET=<different-32-char-secret>
NEXTAUTH_URL=https://admin.myhibachichef.com
ADMIN_SECRET=<admin-access-secret>
DATABASE_URL=<production-db-url>
```

### **GitHub Secrets (for CI/CD)**
```bash
# Deployment
VERCEL_TOKEN=<vercel-api-token>
VERCEL_ORG_ID=<vercel-org-id>
VERCEL_PROJECT_ID_CUSTOMER=<customer-project-id>
VERCEL_PROJECT_ID_ADMIN=<admin-project-id>

# VPS Deployment
VPS_HOST=<plesk-server-ip>
VPS_USER=<ssh-user>
VPS_SSH_KEY=<private-ssh-key>
VPS_API_PATH=/var/www/api.myhibachichef.com
VPS_AI_PATH=/var/www/ai.myhibachichef.com

# Shared Secrets
STRIPE_SECRET_KEY=sk_live_...
RINGCENTRAL_CLIENT_SECRET=<secret>
DATABASE_URL=<production-db-url>
```

### **VPS Plesk Environment Setup**

#### Main API Domain Setup:
```bash
# Domain: api.myhibachichef.com
# Document Root: /var/www/api.myhibachichef.com
# Python Version: 3.11+
# WSGI: gunicorn
# SSL: Let's Encrypt

# Environment file: /var/www/api.myhibachichef.com/.env
DATABASE_URL=postgresql://...
STRIPE_SECRET_KEY=sk_live_...
RINGCENTRAL_CLIENT_SECRET=...
# ... (all API env vars)
```

#### AI API Domain Setup:
```bash
# Domain: ai.myhibachichef.com  
# Document Root: /var/www/ai.myhibachichef.com
# Python Version: 3.11+
# WSGI: gunicorn
# SSL: Let's Encrypt

# Environment file: /var/www/ai.myhibachichef.com/.env
OPENAI_API_KEY=sk-...
MAIN_API_URL=https://api.myhibachichef.com
# ... (all AI API env vars)
```

---

## GitIgnore Requirements

```gitignore
# Environment files
.env
.env.local
.env.development
.env.test
.env.production
.env.staging

# Environment files by app
apps/customer/.env*
apps/admin/.env*
apps/api/.env*
apps/ai-api/.env*

# Local database
*.db
*.sqlite

# Logs
logs/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Runtime data
pids/
*.pid
*.seed
*.pid.lock

# Directory for instrumented libs generated by jscoverage/JSCover
lib-cov/

# Coverage directory used by tools like istanbul
coverage/
*.lcov

# nyc test coverage
.nyc_output/

# Dependency directories
node_modules/
jspm_packages/

# Optional npm cache directory
.npm

# Optional REPL history
.node_repl_history

# Output of 'npm pack'
*.tgz

# Yarn Integrity file
.yarn-integrity

# dotenv environment variables file
.env

# parcel-bundler cache (https://parceljs.org/)
.cache
.parcel-cache

# next.js build output
.next
out/

# nuxt.js build output
.nuxt

# vuepress build output
.vuepress/dist

# Serverless directories
.serverless

# FuseBox cache
.fusebox/

# DynamoDB Local files
.dynamodb/

# TernJS port file
.tern-port

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Temporary files
temp/
tmp/
*.tmp

# Deployment
.vercel
.azure/
deployment-config.json

# Backup files
*.backup
*.bak

# Local data
uploads/
media/
static/media/

# SSL certificates
*.pem
*.key
*.crt
```

---

## Critical Issues to Fix Before Deployment

### 1. **Path Resolution Issues**
- Multiple missing `@/` path imports
- Need to fix tsconfig path mappings
- Missing data files and utilities

### 2. **TypeScript Errors** 
- 379+ compilation errors across 113 files
- Missing module declarations
- Type safety issues

### 3. **Missing Dependencies**
- Blog post data structure
- API client configuration
- Utility functions

### 4. **Environment Configuration**
- Create environment templates
- Set up proper secret management
- Configure CORS and security headers

---

## Deployment Checklist

### Pre-deployment:
- [ ] Fix all TypeScript compilation errors
- [ ] Create missing data files and modules
- [ ] Set up proper environment variable templates
- [ ] Configure proper path resolution
- [ ] Add comprehensive error handling
- [ ] Set up proper CORS configuration
- [ ] Configure SSL certificates
- [ ] Set up monitoring and logging

### Vercel Setup:
- [ ] Create customer frontend project
- [ ] Create admin panel project  
- [ ] Configure custom domains
- [ ] Set up environment variables
- [ ] Configure build settings
- [ ] Set up preview deployments

### VPS Plesk Setup:
- [ ] Create API subdomain
- [ ] Create AI API subdomain
- [ ] Configure Python environment
- [ ] Set up database connections
- [ ] Configure reverse proxy
- [ ] Set up SSL certificates
- [ ] Configure monitoring

### GitHub CI/CD:
- [ ] Set up deployment workflows
- [ ] Configure secret management
- [ ] Set up automatic testing
- [ ] Configure preview deployments

---

## Next Steps

1. **Fix TypeScript errors** - Resolve 379+ compilation issues
2. **Create missing modules** - Blog data, API clients, utilities
3. **Environment setup** - Create .env templates and configure secrets
4. **Deploy infrastructure** - Set up domains and hosting
5. **Configure CI/CD** - Automate deployment pipeline
6. **Testing & monitoring** - Ensure production readiness
