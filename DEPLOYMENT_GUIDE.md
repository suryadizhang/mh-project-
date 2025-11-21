# 🚀 My Hibachi Deployment Guide

This guide provides step-by-step instructions for deploying the My
Hibachi platform safely and efficiently.

## ⚡ Quick Start

```bash
# 1. Test deployment readiness
gh workflow run deployment-testing.yml -f test_scope=full

# 2. Run health monitoring
./scripts/deployment-monitor.sh single

# 3. Deploy (when ready)
gh workflow run ci-deploy.yml -f force_deploy=true
```

## 📋 Pre-Deployment Checklist

### 🔐 Security Requirements

- [ ] **No hardcoded secrets** in repository
- [ ] All secrets in Google Secret Manager (23 total)
- [ ] `.gitignore` blocks secret files
- [ ] Template files use placeholders only

### 🏗️ Infrastructure Requirements

- [ ] **Customer Website**: Vercel deployment configured
- [ ] **Admin Panel**: Vercel deployment configured
- [ ] **Backend API**: VPS/Plesk deployment configured
- [ ] **Database**: PostgreSQL connection ready
- [ ] **Redis**: Cache connection ready

### 🧪 Testing Requirements

- [ ] **Unit tests**: All passing
- [ ] **Integration tests**: All passing
- [ ] **Health checks**: All endpoints responding
- [ ] **GSM integration**: Secrets loading correctly

---

## 📍 Application Overview

The My Hibachi platform consists of three coordinated applications:

### 🛍️ Customer Website (Next.js)

- **URL**: https://myhibachichef.com
- **Deployment**: Vercel (auto-deploy from `main` branch)
- **Health Check**: `/api/health`
- **Purpose**: Public booking and marketing site

### 👥 Admin Panel (Next.js)

- **URL**: https://admin.mysticdatanode.net
- **Deployment**: Vercel (auto-deploy from `main` branch)
- **Health Check**: `/api/health`
- **Purpose**: Internal operations and management

### 🔧 Backend API (FastAPI)

- **URL**: https://api.myhibachichef.com
- **Deployment**: VPS/Plesk (manual or automated)
- **Health Check**: `/health`, `/health/config`,
  `/health/dependencies`
- **Purpose**: Business logic, data, and integrations

---

## 🚀 Deployment Process

### Phase 1: Validation & Testing

#### Step 1: Run Deployment Tests

```bash
# Full test suite (recommended)
gh workflow run deployment-testing.yml -f test_scope=full

# Quick validation
gh workflow run deployment-testing.yml -f test_scope=quick

# Check specific components
gh workflow run deployment-testing.yml -f test_scope=health
gh workflow run deployment-testing.yml -f test_scope=gsm
```

#### Step 2: Monitor Test Results

```bash
# Check workflow status
gh run list --workflow=deployment-testing.yml --limit=5

# View detailed logs
gh run view <run-id> --log
```

#### Step 3: Validate Security

```bash
# Run security scan
./scripts/security-scan.sh  # If available

# Verify no secrets in git
git log --grep="secret\|key\|password" --oneline
```

### Phase 2: Infrastructure Deployment

#### Step 4: Deploy Backend (Critical First)

```bash
# Backend deployment (VPS/Plesk)
# This is typically manual or via SSH

# SSH to VPS
ssh user@your-vps

# Pull latest code
cd /path/to/backend
git pull origin main

# Install dependencies
pip install -r requirements.txt

# Run with GSM integration
python src/start_with_gsm.py

# Verify backend health
curl https://api.myhibachichef.com/health
```

#### Step 5: Deploy Frontend Applications

```bash
# Customer website (Vercel auto-deploys on push to main)
git push origin main

# Admin panel (Vercel auto-deploys on push to main)
# Already deployed with customer site

# Verify frontend deployments
curl https://myhibachichef.com/api/health
curl https://admin.mysticdatanode.net/api/health
```

### Phase 3: Verification & Monitoring

#### Step 6: Run Post-Deployment Health Checks

```bash
# Full health check
./scripts/deployment-monitor.sh single

# Continuous monitoring (optional)
./scripts/deployment-monitor.sh continuous 300
```

#### Step 7: Verify GSM Integration

```bash
# Check GSM status via API
curl https://api.myhibachichef.com/health/config | jq '.gsm_available'

# Should return: true
```

#### Step 8: Test Critical User Flows

- [ ] **Customer booking flow** (end-to-end)
- [ ] **Admin panel access** (authentication)
- [ ] **API endpoints** (key business logic)
- [ ] **Payment processing** (Stripe integration)
- [ ] **SMS notifications** (RingCentral integration)

---

## 🏥 Health Monitoring

### Automated Monitoring

```bash
# Single health check
./scripts/deployment-monitor.sh single

# Continuous monitoring (every 5 minutes)
./scripts/deployment-monitor.sh continuous 300

# Quick check (main apps only)
./scripts/deployment-monitor.sh quick
```

### Windows PowerShell

```powershell
# Single health check
.\scripts\deployment-monitor.ps1 -Mode single

# Continuous monitoring
.\scripts\deployment-monitor.ps1 -Mode continuous -Interval 300

# Quick check
.\scripts\deployment-monitor.ps1 -Mode quick
```

### Manual Health Checks

```bash
# Customer website
curl -s https://myhibachichef.com/api/health | jq '.'

# Admin panel
curl -s https://admin.mysticdatanode.net/api/health | jq '.'

# Backend API
curl -s https://api.myhibachichef.com/health | jq '.'
curl -s https://api.myhibachichef.com/health/config | jq '.'
curl -s https://api.myhibachichef.com/health/dependencies | jq '.'
```

### Expected Health Check Responses

```json
// /health - Basic health
{
  "status": "healthy",
  "timestamp": "2025-01-XX...",
  "uptime": "1d 2h 15m"
}

// /health/config - Configuration status
{
  "status": "healthy",
  "gsm_available": true,
  "config_loaded": true,
  "secrets_count": 23,
  "environment": "production"
}

// /health/dependencies - External services
{
  "status": "checked",
  "dependencies": {
    "database": {"status": "healthy"},
    "redis": {"status": "healthy"},
    "external_apis": {
      "openai": {"configured": true},
      "stripe": {"configured": true},
      "ringcentral": {"configured": true}
    }
  }
}
```

---

## 🔧 Troubleshooting

### Common Issues & Solutions

#### 🚨 Backend Not Starting

```bash
# Check GSM secrets loading
python apps/backend/src/start_with_gsm.py

# Check configuration
python -c "from apps.backend.src.core.config import get_settings; print(get_settings())"

# Check logs
tail -f logs/deployment/deployment-monitor.log
```

#### 🚨 Frontend Build Failures

```bash
# Check Vercel deployment logs
vercel logs https://myhibachichef.com

# Local build test
cd apps/customer
npm run build

cd ../admin
npm run build
```

#### 🚨 GSM Integration Failures

```bash
# Check Google Cloud authentication
gcloud auth list

# Verify project access
gcloud projects list

# Test secret access manually
gcloud secrets list --project=my-hibachi-crm
```

#### 🚨 Health Check Failures

```bash
# Debug specific endpoint
curl -v https://api.myhibachichef.com/health

# Check DNS resolution
nslookup api.myhibachichef.com

# Check SSL certificate
openssl s_client -connect api.myhibachichef.com:443
```

### Emergency Rollback

```bash
# Quick rollback (if needed)
git revert <commit-hash>
git push origin main

# Or restore from backup
# (Follow your backup restoration procedure)
```

---

## 🎛️ Feature Flags & Gradual Rollout

### Enable New Features Safely

```bash
# Backend feature flags (via admin API - requires authentication)
curl -X POST https://api.myhibachichef.com/admin/feature-flags \
  -H "Authorization: Bearer <admin-token>" \
  -d '{"flag": "FEATURE_FLAG_NEW_BOOKING_VALIDATION", "enabled": true}'

# Environment variable approach (for gradual rollout)
export FEATURE_FLAG_NEW_BOOKING_VALIDATION=true
```

### Monitoring Feature Flag Status

```bash
# Check enabled flags (admin only)
curl -H "Authorization: Bearer <admin-token>" \
  https://api.myhibachichef.com/health/config/detailed | \
  jq '.feature_flags'
```

---

## 📊 Performance & Metrics

### Key Metrics to Monitor

- **Response Time**: < 500ms for health checks
- **Uptime**: > 99.9% availability target
- **Error Rate**: < 0.1% of requests
- **GSM Secret Load Time**: < 2 seconds

### Monitoring Tools

```bash
# Real-time monitoring
watch -n 30 './scripts/deployment-monitor.sh quick'

# Log analysis
grep -E "(ERROR|CRITICAL)" logs/deployment/deployment-monitor.log

# Performance tracking
curl -w "@curl-format.txt" -o /dev/null -s https://api.myhibachichef.com/health
```

---

## 🔐 Security Considerations

### Post-Deployment Security Checklist

- [ ] **Rotate any exposed secrets** immediately
- [ ] **Enable security headers** (HTTPS, CSP, etc.)
- [ ] **Configure rate limiting** on API endpoints
- [ ] **Set up monitoring alerts** for suspicious activity
- [ ] **Verify backup procedures** are working
- [ ] **Test incident response** procedures

### Security Monitoring

```bash
# Check for unauthorized access attempts
grep -E "(401|403|429)" /var/log/nginx/access.log | tail -20

# Monitor API usage patterns
curl https://api.myhibachichef.com/metrics | grep -E "(requests|errors)"
```

---

## 📞 Support & Escalation

### Immediate Support Contacts

- **Technical Lead**: [Your contact info]
- **DevOps/Infrastructure**: [Your contact info]
- **Security**: [Your contact info]

### Escalation Process

1. **Level 1**: Check logs and restart services
2. **Level 2**: Contact technical lead
3. **Level 3**: Implement emergency rollback
4. **Level 4**: Contact infrastructure provider

### Emergency Procedures

- **Critical outage**: Run `./scripts/deployment-monitor.sh quick`
  every minute
- **Data concerns**: Stop all writes immediately, contact security
- **Security incident**: Rotate all secrets, contact security team

---

## 📚 Additional Resources

- [Feature Flag Standard](.github/FEATURE_FLAG_STANDARD.md)
- [Security Audit Report](SECURITY_AUDIT_CRITICAL.md)
- [GSM Secret Management](GSM_IMPLEMENTATION_COMPLETE.md)
- [GitHub Actions Workflows](.github/workflows/)

---

_This deployment guide is continuously updated. Last revision: January
2025_
