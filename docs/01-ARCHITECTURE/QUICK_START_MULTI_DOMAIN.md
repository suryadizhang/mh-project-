# 🚀 Quick Start: Multi-Domain Deployment Action Plan
**Date:** October 30, 2025  
**Time to Complete:** 2 hours  
**Difficulty:** Medium

---

## 📋 Pre-Flight Checklist

Before you start, ensure you have:

- [x] VPS with Plesk Panel (108.175.12.154)
- [x] 3 domains ready:
  - `myhibachichef.com` (customer)
  - `admin.mysticdatanode.net` (admin)
  - `mhapi.mysticdatanode.net` (API)
- [x] DNS A records configured
- [ ] Vercel Pro account (or FREE tier)
- [ ] GitHub repository access
- [ ] All API keys ready (Stripe, OpenAI, RingCentral, etc.)

---

## 🎯 Deployment Sequence

### Phase 1: Backend API (60 minutes) ⚡

**Step 1: Update CORS Configuration (5 minutes)**

```bash
# Local machine - update configuration
cd "C:\Users\surya\projects\MH webapps\apps\backend\src\core"
# Open config.py and update line 64:

# OLD:
CORS_ORIGINS: str = "https://myhibachichef.com,https://admin.myhibachichef.com"

# NEW:
CORS_ORIGINS: str = "https://myhibachichef.com,https://admin.mysticdatanode.net"
```

**Step 2: Add Security Headers (10 minutes)**

Create file: `apps/backend/src/core/security_middleware.py`

```python
"""Security headers middleware for production"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # HSTS - Force HTTPS
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https: http:; "
            "connect-src 'self' https://mhapi.mysticdatanode.net https://api.stripe.com; "
            "frame-src 'self' https://js.stripe.com;"
        )
        
        return response
```

**Step 3: Update main.py to use security middleware (5 minutes)**

```python
# Add after line 7 in main.py:
from core.security_middleware import SecurityHeadersMiddleware

# Add after line 172 (after CORS middleware):
app.add_middleware(SecurityHeadersMiddleware)
```

**Step 4: Commit and Push Changes (5 minutes)**

```bash
cd "C:\Users\surya\projects\MH webapps"

git add .
git commit -m "feat: update CORS for multi-domain + add security headers"
git push origin main

# GitHub Actions will automatically deploy to VPS!
# Watch progress: https://github.com/YOUR_USERNAME/YOUR_REPO/actions
```

**Step 5: Deploy to VPS (35 minutes)**

Follow **MULTI_DOMAIN_DEPLOYMENT_GUIDE.md** Phase 1 (Steps 1.1 - 1.14)

Key tasks:
- Create website in Plesk for `mhapi.mysticdatanode.net`
- Setup PostgreSQL database
- Create .env file with production secrets
- Install dependencies
- Run database migrations
- Configure Supervisor + Nginx
- Enable Let's Encrypt SSL

---

### Phase 2: Customer Frontend (20 minutes) 🎨

**Step 6: Deploy to Vercel (15 minutes)**

```bash
# 1. Login to Vercel
Go to: https://vercel.com
Login with GitHub

# 2. Import Repository
Click "Add New Project"
Select your GitHub repository
Click "Import"

# 3. Configure Project
Framework: Next.js
Root Directory: apps/customer
Build Command: npm run build
Output Directory: .next

# 4. Add Environment Variables:
NEXT_PUBLIC_API_URL=https://mhapi.mysticdatanode.net
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_KEY
NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME=YOUR_CLOUD_NAME

# 5. Click "Deploy" - wait 2-3 minutes
```

**Step 7: Add Custom Domain (5 minutes)**

```bash
# In Vercel project:
Settings → Domains → Add Domain

Domain: myhibachichef.com

# Vercel will provide DNS records
# Update at your domain registrar

Type: A
Name: @
Value: [Vercel's IP - they will provide]

Type: CNAME
Name: www
Value: cname.vercel-dns.com

# Wait 5-10 minutes for DNS propagation
# Vercel will auto-configure SSL
```

---

### Phase 3: Admin Frontend (20 minutes) 👨‍💼

**Step 8: Deploy Admin to Vercel (15 minutes)**

```bash
# 1. In Vercel Dashboard
Click "Add New Project" (again)
Select SAME GitHub repository

# 2. Configure Admin Project
Framework: Next.js
Root Directory: apps/admin  ← DIFFERENT!
Build Command: npm run build
Output Directory: .next

# 3. Add Environment Variables:
NEXT_PUBLIC_API_URL=https://mhapi.mysticdatanode.net
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_KEY
NEXT_PUBLIC_APP_ENV=production

# 4. Click "Deploy"
```

**Step 9: Add Admin Custom Domain (5 minutes)**

```bash
# In Vercel project (Admin):
Settings → Domains → Add Domain

Domain: admin.mysticdatanode.net

# Vercel provides:
Type: CNAME
Name: admin
Value: cname.vercel-dns.com

# Update DNS at mysticdatanode.net registrar
# Wait 5-10 minutes for propagation
```

---

### Phase 4: Verification & Testing (20 minutes) ✅

**Step 10: Test All 3 Domains (15 minutes)**

```bash
# Test 1: Backend API
curl https://mhapi.mysticdatanode.net/health
# Expected: {"status":"healthy",...}

# Test 2: Customer Frontend
Open: https://myhibachichef.com
Check:
- [ ] Homepage loads
- [ ] SSL certificate valid (green padlock)
- [ ] Can browse menu
- [ ] Can create booking
- [ ] No CORS errors in browser console (F12)

# Test 3: Admin Frontend
Open: https://admin.mysticdatanode.net
Check:
- [ ] Login page loads
- [ ] SSL certificate valid
- [ ] Can login
- [ ] Dashboard displays
- [ ] No CORS errors

# Test 4: API Authentication
curl -X POST https://mhapi.mysticdatanode.net/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@myhibachi.com","password":"your_password"}'
# Expected: {"access_token":"eyJ..."}
```

**Step 11: Setup Monitoring (5 minutes)**

```bash
# 1. UptimeRobot (FREE)
Go to: https://uptimerobot.com
Create account

Add 3 monitors:
1. API: https://mhapi.mysticdatanode.net/health (every 5 min)
2. Customer: https://myhibachichef.com (every 5 min)
3. Admin: https://admin.mysticdatanode.net (every 5 min)

# 2. Update Sentry DSN in VPS .env
SSH into VPS:
ssh root@108.175.12.154

cd /var/www/vhosts/mhapi.mysticdatanode.net/httpdocs/backend
sudo nano .env

# Add:
SENTRY_DSN=https://YOUR_SENTRY_DSN@sentry.io/PROJECT_ID

sudo supervisorctl restart myhibachi-backend
```

---

## ⚡ Critical Configuration Updates

### 1. CORS Origins (CRITICAL!)

**File:** `apps/backend/src/core/config.py` (Line 64)

```python
# BEFORE:
CORS_ORIGINS: str = "https://myhibachichef.com,https://admin.myhibachichef.com"

# AFTER:
CORS_ORIGINS: str = "https://myhibachichef.com,https://admin.mysticdatanode.net"
```

### 2. Environment Variables (.env on VPS)

**File:** `/var/www/vhosts/mhapi.mysticdatanode.net/httpdocs/backend/.env`

```bash
# Update these lines:
CORS_ORIGINS=https://myhibachichef.com,https://admin.mysticdatanode.net
FRONTEND_URL=https://myhibachichef.com
ADMIN_URL=https://admin.mysticdatanode.net
CUSTOMER_APP_URL=https://myhibachichef.com

# Security
DEBUG=False
ENVIRONMENT=production

# Sentry
SENTRY_DSN=https://YOUR_SENTRY_DSN@sentry.io/PROJECT_ID
SENTRY_ENVIRONMENT=production
```

### 3. Frontend Environment Variables (Vercel)

**Customer App:**
```bash
NEXT_PUBLIC_API_URL=https://mhapi.mysticdatanode.net
```

**Admin App:**
```bash
NEXT_PUBLIC_API_URL=https://mhapi.mysticdatanode.net
```

---

## 🔥 Common Issues & Quick Fixes

### Issue 1: CORS Error

**Symptom:**
```
Access blocked by CORS policy
```

**Fix:**
```bash
# SSH into VPS
ssh root@108.175.12.154

# Update .env
cd /var/www/vhosts/mhapi.mysticdatanode.net/httpdocs/backend
sudo nano .env

# Ensure CORS_ORIGINS has both domains:
CORS_ORIGINS=https://myhibachichef.com,https://admin.mysticdatanode.net

# Restart
sudo supervisorctl restart myhibachi-backend
```

### Issue 2: Backend Not Responding

**Fix:**
```bash
# Check status
sudo supervisorctl status myhibachi-backend

# If not running:
sudo supervisorctl start myhibachi-backend

# View logs:
sudo tail -f /var/log/myhibachi-backend.log
```

### Issue 3: SSL Certificate Not Working

**Vercel (automatic):**
- Wait 10 minutes after adding domain
- Check Domains tab for status

**VPS (Plesk):**
- Go to Plesk Panel → SSL/TLS Certificates
- Install Let's Encrypt certificate
- Enable "Redirect HTTP to HTTPS"

### Issue 4: Frontend Can't Connect to API

**Check:**
1. CORS configured correctly (see Issue 1)
2. API is running: `curl https://mhapi.mysticdatanode.net/health`
3. Environment variables set in Vercel
4. No typos in API URL

---

## 📊 Deployment Checklist

### Backend (VPS) ✅
- [ ] Plesk website created for `mhapi.mysticdatanode.net`
- [ ] PostgreSQL database created
- [ ] `.env` file configured with all secrets
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Database migrations run (`alembic upgrade head`)
- [ ] Supervisor configured and service running
- [ ] Nginx reverse proxy configured
- [ ] Let's Encrypt SSL certificate installed
- [ ] Health endpoint responding: `/health`
- [ ] CORS updated for new domains

### Customer Frontend (Vercel) ✅
- [ ] GitHub repository imported
- [ ] Root directory set to `apps/customer`
- [ ] Environment variables configured
- [ ] Deployed successfully
- [ ] Custom domain `myhibachichef.com` added
- [ ] DNS records updated
- [ ] SSL certificate active
- [ ] Can load homepage
- [ ] API calls work (no CORS errors)

### Admin Frontend (Vercel) ✅
- [ ] Separate project created (same repo)
- [ ] Root directory set to `apps/admin`
- [ ] Environment variables configured
- [ ] Deployed successfully
- [ ] Custom domain `admin.mysticdatanode.net` added
- [ ] DNS records updated
- [ ] SSL certificate active
- [ ] Can login to admin panel
- [ ] API calls work (no CORS errors)

### Monitoring ✅
- [ ] UptimeRobot monitoring all 3 domains
- [ ] Sentry error tracking configured
- [ ] Papertrail log aggregation (optional)
- [ ] Alerts configured for downtime

### Security ✅
- [ ] All domains use HTTPS
- [ ] Security headers added to API
- [ ] CORS properly restricted
- [ ] Rate limiting active
- [ ] Firewall configured (UFW)
- [ ] Database not exposed publicly
- [ ] Redis not exposed publicly
- [ ] SSH key-only authentication

---

## 🎉 Success Criteria

Your deployment is complete when:

✅ **Backend API**
```bash
curl https://mhapi.mysticdatanode.net/health
# Returns: {"status":"healthy",...}
```

✅ **Customer Frontend**
- Opens: https://myhibachichef.com
- SSL certificate valid
- Can create bookings
- API calls succeed

✅ **Admin Frontend**
- Opens: https://admin.mysticdatanode.net
- SSL certificate valid
- Can login and manage data
- API calls succeed

✅ **No CORS Errors**
```javascript
// In browser console (F12) on either frontend:
fetch('https://mhapi.mysticdatanode.net/health')
  .then(r => r.json())
  .then(console.log)
// Returns data without error
```

---

## 📞 Next Steps After Deployment

### Immediate (Day 1)
1. Test all critical user flows
2. Verify monitoring alerts work
3. Check error tracking in Sentry
4. Review logs for any issues

### Week 1
1. Monitor uptime and response times
2. Check rate limiting under load
3. Review Sentry error reports
4. Optimize slow API endpoints

### Month 1
1. Security audit with OWASP ZAP
2. Performance testing
3. Review analytics
4. Plan feature improvements

---

## 📚 Reference Documentation

- **Full Deployment Guide:** `MULTI_DOMAIN_DEPLOYMENT_GUIDE.md`
- **Security Audit:** `SECURITY_AUDIT_REPORT_OCT_30_2025.md`
- **CI/CD Strategy:** `CI_CD_STRATEGY.md`
- **Plesk Setup:** `PLESK_DEPLOYMENT_SETUP_GUIDE.md`

---

**Estimated Time:** 2 hours  
**Difficulty:** Medium  
**Cost:** ~$50/month

**Ready to deploy? Let's go! 🚀**
