# Production Operations Runbook

**Last Updated:** October 25, 2025  
**Version:** 1.0  
**Status:** ✅ Production Ready

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Deployment Procedures](#deployment-procedures)
4. [Monitoring & Alerting](#monitoring--alerting)
5. [Incident Response](#incident-response)
6. [Rollback Procedures](#rollback-procedures)
7. [Health Checks](#health-checks)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Maintenance Windows](#maintenance-windows)
10. [Disaster Recovery](#disaster-recovery)
11. [On-Call Procedures](#on-call-procedures)
12. [Escalation Matrix](#escalation-matrix)

---

## Overview

### Purpose

This runbook provides comprehensive operational procedures for the MyHibachi production environment. It covers deployment, monitoring, incident response, and disaster recovery for all system components.

### Scope

**Covered Services:**
- ✅ FastAPI Backend (mhapi.mysticdatanode.net)
- ✅ Customer Frontend (myhibachichef.com) - Vercel
- ✅ Admin Frontend (admin.mysticdatanode.net) - Vercel
- ✅ PostgreSQL Database
- ✅ Redis Cache
- ✅ Load Balancer (Apache httpd)

**Infrastructure:**
- VPS Plesk (Backend services)
- Vercel (Frontend services)
- External APIs (Stripe, OpenAI, RingCentral)

### Service Level Objectives (SLOs)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Uptime** | 99.9% | Monthly |
| **API Response Time** | <200ms (P95) | Real-time |
| **AI Response Time** | <1s (P95) | Real-time |
| **Error Rate** | <0.1% | Per hour |
| **Page Load Time** | <2s | Weekly average |
| **Database Query** | <50ms (P95) | Real-time |

---

## System Architecture

### Production Environment Topology

```
┌─────────────────────────────────────────────────────────────┐
│                        INTERNET                              │
└───────────────┬─────────────────────┬───────────────────────┘
                │                     │
        ┌───────▼─────┐       ┌──────▼────────┐
        │   Vercel    │       │   VPS Plesk   │
        │   CDN       │       │  Load Balancer│
        │             │       │    (Nginx)    │
        └───────┬─────┘       └───────┬───────┘
                │                     │
    ┌───────────┴────────┐    ┌──────┴───────────────┐
    │                    │    │                      │
┌───▼────┐       ┌──────▼┐  ┌▼────────┐  ┌─────────▼┐
│Customer│       │ Admin │  │FastAPI  │  │ AI API  │
│Frontend│       │Panel  │  │Backend  │  │Backend  │
│Next.js │       │Next.js│  │:8003    │  │:8002    │
└────────┘       └───────┘  └────┬────┘  └────┬────┘
                                  │            │
                            ┌─────▼────────────▼────┐
                            │                       │
                        ┌───▼────────┐  ┌──────────▼──┐
                        │PostgreSQL  │  │   Redis     │
                        │Database    │  │   Cache     │
                        └────────────┘  └─────────────┘
```

### Component Details

#### Frontend Services (Vercel)

**Customer App** (`https://myhibachichef.com`)
- **Framework:** Next.js 15.5.4 (App Router)
- **Deployment:** Automatic on `main` branch push
- **Build Time:** ~2-3 minutes
- **CDN:** Global edge network
- **Environment:** Production
- **SSL:** Auto-managed by Vercel

**Admin App** (`https://admin.mysticdatanode.net`)
- **Framework:** Next.js 15.5.4 (App Router)
- **Deployment:** Automatic on `main` branch push
- **Build Time:** ~1-2 minutes
- **CDN:** Global edge network
- **Environment:** Production
- **SSL:** Auto-managed by Vercel

#### Backend Services (VPS Plesk)

**Main API** (`https://mhapi.mysticdatanode.net`)
- **Framework:** FastAPI 0.109+
- **Runtime:** Python 3.11.0
- **WSGI:** Gunicorn (4 workers)
- **Dependencies:** 53+ packages
- **Database:** PostgreSQL (asyncpg)
- **Cache:** Redis
- **Health Check:** `/health`
- **Metrics:** `/metrics`
- **Note:** AI endpoints integrated into main API (no separate AI service)
- **Port:** 8000 (reverse proxied via Apache httpd)
- **Rate Limit:** 60 req/min

#### Database Services

**PostgreSQL 14**
- **Version:** 14.x
- **Connection Pool:** 20 max connections
- **Backup:** Daily automated
- **Replication:** None (single instance)
- **Location:** VPS local
- **Monitoring:** Active

**Redis 7**
- **Version:** 7.x
- **Max Memory:** 512MB
- **Eviction Policy:** LRU
- **Persistence:** RDB + AOF
- **Location:** VPS local

---

## Deployment Procedures

### Pre-Deployment Checklist

**Code Review:**
- [ ] All PR reviews completed and approved
- [ ] CI/CD pipeline passing (all tests green)
- [ ] No critical security vulnerabilities (Snyk/Dependabot)
- [ ] Database migrations reviewed and tested
- [ ] API documentation updated
- [ ] Environment variables verified

**Testing:**
- [ ] Unit tests: >85% coverage
- [ ] Integration tests: All passing
- [ ] E2E tests: Critical flows validated
- [ ] Performance tests: Within targets
- [ ] Security scan: No high/critical issues
- [ ] Manual QA: Sign-off completed

**Communication:**
- [ ] Deployment announcement sent (30 min before)
- [ ] On-call engineer identified
- [ ] Rollback plan documented
- [ ] Stakeholders notified (if major release)

**Backup:**
- [ ] Database backup completed (<1 hour old)
- [ ] Configuration files backed up
- [ ] Current production version tagged

### Deployment Steps

#### Backend Deployment (VPS Plesk)

**1. Pre-Deployment Backup**

```bash
# SSH into VPS
ssh myhibachi@vps.myhibachi.com

# Backup database
cd /opt/myhibachi/app
python3 ops/backup_db.py

# Verify backup
ls -lh /var/backups/myhibachi/

# Expected: backup-YYYY-MM-DD-HHMMSS.sql
```

**2. Stop Services (Zero-Downtime Alternative)**

```bash
# Option A: Rolling deployment (recommended)
# No service stop required, uses health checks

# Option B: Full stop (if schema changes require it)
cd /opt/myhibachi/app
docker compose -f docker-compose.prod.yml stop
```

**3. Pull Latest Code**

```bash
cd /opt/myhibachi/app
git fetch origin
git checkout main
git pull origin main

# Verify version
git log -1 --oneline
```

**4. Update Dependencies**

```bash
# Backend dependencies
cd apps/api
pip install -r requirements.txt --upgrade

cd ../ai-api
pip install -r requirements.txt --upgrade
```

**5. Run Database Migrations**

```bash
cd /opt/myhibachi/app/apps/backend

# Dry-run to check migrations
alembic current
alembic check

# Apply migrations
alembic upgrade head

# Verify
alembic current
```

**6. Restart Services**

```bash
cd /opt/myhibachi/app

# Restart with new code
docker compose -f docker-compose.prod.yml up -d --build

# Monitor startup
docker compose -f docker-compose.prod.yml logs -f --tail=100
```

**7. Health Check Verification**

```bash
# Wait 30 seconds for services to start
sleep 30

# Check Main API
curl -f https://mhapi.mysticdatanode.net/health || echo "FAILED"

# NOTE: AI endpoints are integrated into main API, no separate AI service

# Check database connection
docker compose -f docker-compose.prod.yml exec fastapi-backend python -c "
from app.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('Database: OK')
"
```

**8. Smoke Tests**

```bash
# Test critical endpoints
curl -X POST https://mhapi.mysticdatanode.net/api/v1/public/leads \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","phone":"5551234567","email":"test@example.com","source":"test"}'

# Expected: {"success": true, ...}

# Test AI endpoint (integrated into main API)
curl -X POST https://mhapi.mysticdatanode.net/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello","agent":"customer"}'

# Expected: {"response": "...", ...}
```

#### Frontend Deployment (Vercel)

**Automatic Deployment:**

Vercel automatically deploys on push to `main` branch.

**Manual Deployment (if needed):**

```bash
# From local machine
cd apps/customer
vercel --prod

# Or for admin
cd apps/admin
vercel --prod
```

**Deployment Verification:**

```bash
# Check customer app
curl -I https://myhibachichef.com
# Expected: HTTP/2 200

# Check admin app
curl -I https://admin.mysticdatanode.net
# Expected: HTTP/2 200

# Check build status
vercel ls --scope=myhibachi
```

### Post-Deployment Validation

**1. Health Check Dashboard**

Visit internal monitoring dashboard:
- Backend: https://mhapi.mysticdatanode.net/metrics
- NOTE: AI endpoints are integrated into main backend (no separate AI service)

**2. Functional Tests (5 minutes)**

| Test | Endpoint | Expected Result |
|------|----------|-----------------|
| Quote Form | POST /api/v1/public/leads | 200 OK |
| Booking Form | POST /api/v1/public/bookings | 200 OK |
| AI Chat | POST /api/chat | 200 OK |
| Admin Login | POST /api/auth/login | 200 OK + JWT |
| Payment | POST /api/v1/bookings/{id}/payment | 200 OK |

**3. Performance Validation**

```bash
# Run performance tests
cd apps/backend
pytest tests/test_api_performance.py -v

# Expected: All tests PASS, response times within targets
```

**4. Error Monitoring**

Check error tracking (Sentry/CloudWatch):
- Error rate: <0.1%
- No new critical errors
- Response times: Within SLOs

**5. User Acceptance**

- [ ] Critical user flows tested manually
- [ ] No customer complaints within 15 minutes
- [ ] Analytics showing normal traffic patterns

### Deployment Rollout Strategy

**1. Canary Deployment (Recommended for Major Changes)**

```bash
# Deploy to 10% of traffic
vercel --prod --alias canary.myhibachi.com

# Monitor for 30 minutes
# If no issues, promote to 100%
vercel alias set myhibachi.com canary.myhibachi.com
```

**2. Blue-Green Deployment (For Database Changes)**

```bash
# Maintain two identical environments
# Switch traffic via load balancer DNS
# Requires manual configuration in Plesk/Nginx
```

**3. Rolling Deployment (Default for Backend)**

- Deploy to one backend instance at a time
- Health checks route traffic to healthy instances
- Automatic with Docker Compose restart

---

## Monitoring & Alerting

### Monitoring Stack

**Tools in Use:**
- **Application Monitoring:** Sentry (errors), Custom metrics
- **Infrastructure Monitoring:** System health monitor script
- **Uptime Monitoring:** UptimeRobot, Pingdom
- **Log Aggregation:** Structured logging to files
- **APM:** FastAPI built-in metrics

### Key Metrics to Monitor

#### Application Metrics

**API Performance:**
```
api_request_duration_seconds (P50, P95, P99)
api_requests_total (by endpoint, status)
api_errors_total (by type)
api_active_requests (gauge)
```

**AI Backend:**
```
ai_request_duration_seconds (P95)
ai_tokens_used_total
ai_errors_total
ai_rate_limit_hits_total
```

**Database:**
```
db_connection_pool_size (gauge)
db_query_duration_seconds (P95)
db_connections_active (gauge)
db_errors_total
```

**Cache:**
```
redis_hit_rate (%)
redis_memory_usage_bytes (gauge)
redis_evictions_total
redis_commands_total
```

#### Infrastructure Metrics

**System Health:**
```
cpu_usage_percent (gauge)
memory_usage_percent (gauge)
disk_usage_percent (gauge)
network_io_bytes (counter)
```

**Service Health:**
```
service_up (gauge, 1=up, 0=down)
service_restart_count (counter)
service_response_time (gauge)
```

### Alert Thresholds

| Alert | Severity | Threshold | Action |
|-------|----------|-----------|--------|
| **Service Down** | P1 | Health check fails 3x | Immediate page |
| **High Error Rate** | P2 | >5% errors for 5 min | Page on-call |
| **Slow Response** | P3 | P95 >500ms for 10 min | Investigate |
| **Database Slow** | P2 | P95 >100ms for 5 min | Check queries |
| **Disk Space Low** | P2 | >85% used | Free space |
| **Memory High** | P3 | >90% for 10 min | Restart service |
| **CPU High** | P3 | >90% for 15 min | Scale up |
| **SSL Expiring** | P3 | <7 days | Renew cert |

### Alert Routing

**Severity Levels:**
- **P1 (Critical):** Page on-call immediately, escalate after 5 min
- **P2 (High):** Notify on-call via Slack, escalate after 15 min
- **P3 (Medium):** Email + Slack, handle within 1 hour
- **P4 (Low):** Email, handle within 24 hours

**Notification Channels:**
- **PagerDuty/OnCall Phone:** P1 alerts only
- **Slack #alerts:** P1, P2, P3 alerts
- **Email:** All alerts (for records)
- **Sentry:** Errors only

### Health Check Endpoints

**Backend Health Check:**

```bash
GET https://mhapi.mysticdatanode.net/health

Response (200 OK):
{
  "status": "healthy",
  "version": "1.2.3",
  "uptime_seconds": 86400,
  "database": "connected",
  "redis": "connected",
  "timestamp": "2025-10-25T10:30:00Z"
}
```

**NOTE:** AI endpoints are integrated into main API. No separate AI backend service.

**Frontend Health Check:**

```bash
GET https://myhibachichef.com/api/health

Response (200 OK):
{
  "status": "healthy",
  "build_id": "abc123...",
  "deployment_url": "myhibachi-xyz.vercel.app"
}
```

### Monitoring Dashboard URLs

**Internal Dashboards:**
- **API Metrics:** https://mhapi.mysticdatanode.net/metrics
- **System Health:** Run `/opt/myhibachi/app/ops/system_health_monitor.py`

**External Services:**
- **Vercel Dashboard:** https://vercel.com/myhibachi/dashboard
- **Sentry:** https://sentry.io/organizations/myhibachi/
- **UptimeRobot:** https://uptimerobot.com/dashboard

---

## Incident Response

### Incident Severity Levels

| Severity | Definition | Response Time | Examples |
|----------|-----------|---------------|----------|
| **P1 (Critical)** | Complete service outage | Immediate | All services down, data loss |
| **P2 (High)** | Major degradation | <15 minutes | API errors >10%, DB down |
| **P3 (Medium)** | Partial degradation | <1 hour | Slow responses, cache issues |
| **P4 (Low)** | Minor issues | <24 hours | UI glitch, log warnings |

### Incident Response Process

#### 1. Detection & Alert

**Alert Received:**
- PagerDuty page
- Slack notification
- Monitoring dashboard

**Initial Actions (60 seconds):**
1. Acknowledge alert
2. Check monitoring dashboard
3. Verify issue (not false alarm)
4. Create incident ticket

#### 2. Assessment (5 minutes)

**Quick Checks:**

```bash
# SSH into VPS
ssh root@108.175.12.154

# Check service status
cd /opt/myhibachi/app
docker compose -f docker-compose.prod.yml ps

# Check logs (last 100 lines)
docker compose -f docker-compose.prod.yml logs --tail=100

# Check system resources
htop
df -h
free -m

# Check health endpoint
curl https://mhapi.mysticdatanode.net/health
```

**Determine Severity:**
- P1: Customer-facing services down
- P2: Partial functionality impaired
- P3: Non-critical issues
- P4: Minor, no customer impact

#### 3. Communication

**Stakeholder Notification:**

```
Subject: [P1] Production Incident - [Service Name] Down

Status: INVESTIGATING
Started: 2025-10-25 10:30 UTC
Impact: [Brief description]
Affected: [User percentage/features]

Current Actions:
- Investigating root cause
- [Specific steps being taken]

Next Update: In 15 minutes
Incident Manager: [Name]
```

**Communication Channels:**
- **P1/P2:** Slack #incidents, Email to stakeholders
- **P3/P4:** Slack #alerts only

**Update Frequency:**
- **P1:** Every 15 minutes
- **P2:** Every 30 minutes
- **P3/P4:** As significant progress is made

#### 4. Mitigation

**Common Mitigation Strategies:**

**Service Restart:**
```bash
cd /opt/myhibachi/app
docker compose -f docker-compose.prod.yml restart [service]

# Wait and verify
sleep 30
curl https://mhapi.mysticdatanode.net/health
```

**Database Issues:**
```bash
# Check connections
docker compose exec postgres psql -U myhibachi -c "
SELECT count(*) FROM pg_stat_activity;
"

# Kill long-running queries
docker compose exec postgres psql -U myhibachi -c "
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'active' 
AND query_start < NOW() - INTERVAL '5 minutes';
"

# Restart database (last resort)
docker compose -f docker-compose.prod.yml restart postgres
```

**High CPU/Memory:**
```bash
# Identify process
htop

# Restart service
docker compose -f docker-compose.prod.yml restart fastapi-backend

# Scale workers (if applicable)
# Edit docker-compose.prod.yml, increase replicas
docker compose -f docker-compose.prod.yml up -d --scale fastapi-backend=4
```

**Cache Issues:**
```bash
# Clear Redis cache
docker compose exec redis redis-cli FLUSHDB

# Restart Redis
docker compose -f docker-compose.prod.yml restart redis
```

#### 5. Resolution & Recovery

**Verify Service Restored:**

```bash
# Run health checks
./ops/system_health_monitor.py --once

# Run smoke tests
pytest tests/test_smoke.py -v

# Monitor for 15 minutes
# Check error rates, response times, user reports
```

**Post-Incident Communication:**

```
Subject: [RESOLVED] Production Incident - [Service Name]

Status: RESOLVED
Started: 2025-10-25 10:30 UTC
Duration: 27 minutes
Resolved: 2025-10-25 10:57 UTC

Root Cause: [Brief explanation]
Resolution: [Actions taken]

Impact Summary:
- Affected users: ~500 (estimated)
- Transactions lost: 0
- Data integrity: Intact

Next Steps:
- Post-mortem scheduled: [Date/Time]
- Follow-up actions: [List]

Incident Report: [Link]
```

#### 6. Post-Mortem

**Within 48 Hours:**

Create incident report documenting:
1. Timeline of events
2. Root cause analysis
3. Resolution steps taken
4. Impact assessment
5. Lessons learned
6. Action items (with owners and deadlines)

**Template:** See `incident-postmortem-template.md`

### Common Incidents & Playbooks

#### Incident: Service Completely Down

**Symptoms:**
- Health check: Connection refused
- All endpoints returning 5xx errors
- No response from service

**Investigation:**
```bash
# Check if service is running
docker compose -f docker-compose.prod.yml ps

# Check recent logs
docker compose logs --tail=200 fastapi-backend

# Check system resources
htop
df -h
```

**Resolution:**
1. Restart service: `docker compose restart fastapi-backend`
2. If fails, check logs for error messages
3. If disk full, free space: `docker system prune -a`
4. If memory issue, restart VPS (last resort)

**Prevention:**
- Set up disk space monitoring
- Configure memory limits in docker-compose
- Enable auto-restart policy

---

#### Incident: Database Connection Pool Exhausted

**Symptoms:**
- API returning "database connection" errors
- Slow queries timing out
- Pool size at maximum

**Investigation:**
```bash
# Check active connections
docker compose exec postgres psql -U myhibachi -c "
SELECT count(*), state 
FROM pg_stat_activity 
GROUP BY state;
"

# Check long-running queries
docker compose exec postgres psql -U myhibachi -c "
SELECT pid, now() - query_start as duration, query 
FROM pg_stat_activity 
WHERE state = 'active' 
ORDER BY duration DESC;
"
```

**Resolution:**
1. Kill long-running queries (>5 min):
```bash
docker compose exec postgres psql -U myhibachi -c "
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'active' 
AND query_start < NOW() - INTERVAL '5 minutes';
"
```
2. Increase pool size in `DATABASE_URL` (e.g., `?pool_size=30`)
3. Optimize slow queries (see logs)
4. Restart backend service

**Prevention:**
- Monitor connection pool usage
- Add connection pool metrics
- Optimize database queries
- Implement connection timeout

---

#### Incident: High API Error Rate

**Symptoms:**
- >5% of requests returning 5xx errors
- Sentry reporting many errors
- Users reporting issues

**Investigation:**
```bash
# Check recent errors in logs
docker compose logs --tail=500 fastapi-backend | grep "ERROR"

# Check Sentry dashboard
# Identify common error pattern

# Check if specific endpoint
# Review monitoring metrics by endpoint
```

**Resolution:**
1. Identify error type (database, external API, code bug)
2. If external API (Stripe, OpenAI), check status pages
3. If database, follow database playbook
4. If code bug, deploy hotfix or rollback
5. If load-related, scale up resources

**Prevention:**
- Comprehensive error handling
- Circuit breakers for external APIs
- Retry logic with exponential backoff
- Better test coverage

---

#### Incident: Slow API Response Times

**Symptoms:**
- P95 response time >500ms
- Users reporting slow page loads
- Timeout errors

**Investigation:**
```bash
# Check system resources
htop
df -h

# Check database query times
docker compose exec postgres psql -U myhibachi -c "
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 20;
"

# Check cache hit rate
docker compose exec redis redis-cli INFO stats | grep hit_rate

# Check network latency
ping mhapi.mysticdatanode.net
```

**Resolution:**
1. If database slow, run `VACUUM ANALYZE`
2. If cache issues, clear and warm cache
3. If high CPU, reduce worker load or scale up
4. If network issues, contact hosting provider
5. If code inefficiency, optimize hot paths

**Prevention:**
- Database query optimization
- Implement caching strategy
- Performance testing in CI/CD
- Auto-scaling policies

---

#### Incident: SSL Certificate Expired

**Symptoms:**
- HTTPS connections failing
- Browser showing "Not secure" warning
- SSL error in logs

**Investigation:**
```bash
# Check certificate expiry
echo | openssl s_client -connect mhapi.mysticdatanode.net:443 2>/dev/null | openssl x509 -noout -dates

# Check Let's Encrypt renewal
sudo certbot certificates
```

**Resolution:**
```bash
# Renew certificate manually
sudo certbot renew

# Reload Nginx
sudo systemctl reload nginx

# Verify
curl -I https://mhapi.mysticdatanode.net
```

**Prevention:**
- Enable certbot auto-renewal: `certbot renew --dry-run`
- Set up renewal monitoring alert (7 days before expiry)
- Document manual renewal procedure

---

## Rollback Procedures

### When to Rollback

**Rollback Triggers:**
- Deployment causes critical bugs (P1/P2 incidents)
- Error rate increases significantly (>10%)
- Performance degrades beyond acceptable (P95 >1s)
- Data integrity issues detected
- Unable to resolve issue within 30 minutes

**Rollback Decision:**
- On-call engineer can rollback for P1 incidents
- Engineering lead approval for P2/P3
- Document reason for rollback

### Rollback Steps

#### Backend Rollback

**1. Identify Previous Version**

```bash
cd /opt/myhibachi/app

# Check git log
git log --oneline -10

# Identify last stable version (e.g., abc1234)
```

**2. Rollback Code**

```bash
# Checkout previous version
git checkout abc1234

# Or if tagged
git checkout v1.2.3
```

**3. Rollback Database (if needed)**

**⚠️ CAUTION: Only rollback if migration caused issues**

```bash
# Check current migration
cd apps/backend
alembic current

# Downgrade one revision
alembic downgrade -1

# Or downgrade to specific revision
alembic downgrade abc1234

# Verify
alembic current
```

**4. Restart Services**

```bash
cd /opt/myhibachi/app

# Rebuild and restart
docker compose -f docker-compose.prod.yml up -d --build

# Monitor startup
docker compose logs -f --tail=100
```

**5. Verify Rollback**

```bash
# Health checks
curl https://mhapi.mysticdatanode.net/health

# Smoke tests
pytest tests/test_smoke.py -v

# Monitor error rates for 15 minutes
```

#### Frontend Rollback (Vercel)

**Option 1: Redeploy Previous Version (Recommended)**

```bash
# From Vercel dashboard
# 1. Go to Deployments
# 2. Find previous successful deployment
# 3. Click "..." → "Promote to Production"
```

**Option 2: Git Revert**

```bash
# On local machine
git revert HEAD
git push origin main

# Vercel auto-deploys
```

**Option 3: CLI Rollback**

```bash
# List recent deployments
vercel ls

# Promote specific deployment
vercel promote <deployment-url> --scope=myhibachi
```

### Rollback Verification

**Checklist:**
- [ ] Service health checks passing
- [ ] Error rate back to normal (<0.1%)
- [ ] Response times within SLOs
- [ ] Smoke tests passing
- [ ] User reports confirm resolution
- [ ] Monitor for 30 minutes for stability

**Post-Rollback Actions:**
1. Update incident ticket with rollback details
2. Communicate rollback to stakeholders
3. Investigate root cause in development
4. Create fix and test thoroughly
5. Schedule re-deployment with fix

---

## Health Checks

### Automated Health Checks

**System Health Monitor Script:**

Location: `/opt/myhibachi/app/ops/system_health_monitor.py`

**Runs Every:** 5 minutes (via systemd timer)

**Checks:**
- Service status (Docker containers)
- API health endpoints
- Database connectivity
- Redis connectivity
- Disk space usage
- Memory usage
- CPU load
- SSL certificate expiry
- External API status (Stripe, OpenAI)

**Run Manually:**

```bash
cd /opt/myhibachi/app
python3 ops/system_health_monitor.py --once

# Expected output:
# ✅ Backend API: Healthy (includes integrated AI)
# ✅ Database: Connected
# ✅ Redis: Connected
# ✅ Disk Space: 45% used
# ✅ Memory: 62% used
# ⚠️ CPU Load: 85% (WARNING)
```

### Manual Health Check Procedure

**Daily Health Check (5 minutes):**

```bash
# 1. Check service status
ssh root@108.175.12.154
cd /opt/myhibachi/app
docker compose -f docker-compose.prod.yml ps

# All services should show "Up"

# 2. Check health endpoint
curl https://mhapi.mysticdatanode.net/health

# 3. Check frontend
curl -I https://myhibachichef.com
curl -I https://admin.mysticdatanode.net

# 4. Check error logs (last hour)
docker compose logs --since 1h | grep "ERROR"

# 5. Check Sentry dashboard
# Visit https://sentry.io and check error count

# 6. Check uptime monitor
# Visit https://uptimerobot.com dashboard

# 7. Review metrics
curl https://mhapi.mysticdatanode.net/metrics | grep "error"
```

**Weekly Health Check (30 minutes):**

All daily checks plus:

```bash
# 1. Database performance
docker compose exec postgres psql -U myhibachi -c "
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
"

# 2. Slow queries review
docker compose exec postgres psql -U myhibachi -c "
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 20;
"

# 3. Cache performance
docker compose exec redis redis-cli INFO stats

# 4. Disk usage trends
df -h

# 5. SSL certificate check
sudo certbot certificates

# 6. Backup verification
ls -lh /var/backups/myhibachi/ | tail -7

# 7. Run performance tests
cd apps/backend
pytest tests/test_api_performance.py -v
```

### Health Check Thresholds

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| **API Response** | 200 OK | Non-200 | Connection refused |
| **Response Time** | <200ms | 200-500ms | >500ms |
| **Error Rate** | <0.1% | 0.1-1% | >1% |
| **CPU Usage** | <70% | 70-90% | >90% |
| **Memory Usage** | <80% | 80-95% | >95% |
| **Disk Space** | <70% | 70-85% | >85% |
| **DB Connections** | <15 | 15-20 | >20 |
| **SSL Expiry** | >30 days | 7-30 days | <7 days |

---

## Troubleshooting Guide

### Service Won't Start

**Problem:** Service fails to start after restart

**Investigation:**
```bash
# Check container logs
docker compose logs fastapi-backend --tail=100

# Check if port is in use
sudo lsof -i :8003

# Check if enough memory
free -m

# Check if enough disk space
df -h
```

**Common Causes & Solutions:**

1. **Port already in use:**
```bash
# Kill process using port
sudo kill -9 $(sudo lsof -t -i:8003)

# Restart service
docker compose restart fastapi-backend
```

2. **Environment variable missing:**
```bash
# Check .env file
cat /opt/myhibachi/config/.env

# Verify all required variables present
# DATABASE_URL, JWT_SECRET_KEY, STRIPE_SECRET_KEY, etc.
```

3. **Database migration failed:**
```bash
# Check migration status
cd apps/backend
alembic current

# Downgrade if needed
alembic downgrade -1

# Re-apply
alembic upgrade head
```

### Database Connection Errors

**Problem:** "Unable to connect to database" errors

**Investigation:**
```bash
# Check if PostgreSQL is running
docker compose ps postgres

# Test connection
docker compose exec postgres psql -U myhibachi -c "SELECT 1;"

# Check connection string
echo $DATABASE_URL
```

**Solutions:**

1. **PostgreSQL not running:**
```bash
docker compose restart postgres
```

2. **Wrong credentials:**
```bash
# Verify credentials in .env
cat /opt/myhibachi/config/.env | grep DATABASE_URL

# Reset password if needed
docker compose exec postgres psql -U postgres -c "
ALTER USER myhibachi WITH PASSWORD 'new_secure_password';
"

# Update .env file
```

3. **Connection pool exhausted:**
```bash
# Kill idle connections
docker compose exec postgres psql -U myhibachi -c "
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE datname = 'myhibachi' 
AND state = 'idle' 
AND state_change < NOW() - INTERVAL '30 minutes';
"

# Restart backend to reset pool
docker compose restart fastapi-backend
```

### High Memory Usage

**Problem:** System running out of memory

**Investigation:**
```bash
# Check memory usage
free -m
htop

# Check per-service memory
docker stats

# Check for memory leaks
docker compose exec fastapi-backend ps aux --sort=-%mem
```

**Solutions:**

1. **Clear cache:**
```bash
docker compose exec redis redis-cli FLUSHDB
```

2. **Restart services:**
```bash
docker compose restart
```

3. **Increase memory limits:**
```bash
# Edit docker-compose.prod.yml
# Add under service:
  mem_limit: 2g
  memswap_limit: 2g

# Restart
docker compose up -d
```

4. **Upgrade VPS** (if persistent issue)

### Slow Database Queries

**Problem:** Queries taking too long

**Investigation:**
```bash
# Find slow queries
docker compose exec postgres psql -U myhibachi -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
FROM pg_stat_activity 
WHERE state = 'active' 
AND now() - pg_stat_activity.query_start > interval '1 second'
ORDER BY duration DESC;
"

# Check query performance
docker compose exec postgres psql -U myhibachi -c "
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 20;
"
```

**Solutions:**

1. **Run VACUUM:**
```bash
docker compose exec postgres psql -U myhibachi -c "VACUUM ANALYZE;"
```

2. **Add missing indexes:**
```bash
# Check for missing indexes
docker compose exec postgres psql -U myhibachi -c "
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY abs(correlation) DESC;
"

# Add indexes as needed
```

3. **Optimize queries:**
```bash
# Use EXPLAIN ANALYZE
docker compose exec postgres psql -U myhibachi -c "
EXPLAIN ANALYZE SELECT * FROM bookings WHERE ...;
"

# Rewrite inefficient queries
```

### External API Failures

**Problem:** Stripe, OpenAI, or RingCentral API calls failing

**Investigation:**
```bash
# Check service status pages
# Stripe: https://status.stripe.com
# OpenAI: https://status.openai.com

# Check API keys
cat /opt/myhibachi/config/.env | grep "API_KEY"

# Check logs for error messages
docker compose logs | grep "API"
```

**Solutions:**

1. **API key expired:**
```bash
# Update API key in .env
nano /opt/myhibachi/config/.env

# Restart services
docker compose restart
```

2. **Rate limit exceeded:**
```bash
# Reduce request rate
# Implement exponential backoff
# Upgrade API plan if needed
```

3. **Service outage:**
```bash
# Enable graceful degradation
# Show user-friendly error message
# Monitor for service restoration
```

### SSL/HTTPS Issues

**Problem:** SSL certificate errors

**Investigation:**
```bash
# Check certificate
echo | openssl s_client -connect mhapi.mysticdatanode.net:443 2>/dev/null | openssl x509 -noout -dates

# Check Nginx config
sudo nginx -t

# Check certbot status
sudo certbot certificates
```

**Solutions:**

1. **Certificate expired:**
```bash
# Renew certificate
sudo certbot renew

# Reload Nginx
sudo systemctl reload nginx
```

2. **Wrong certificate:**
```bash
# Check Nginx config
sudo nano /etc/nginx/sites-available/default

# Fix certificate paths
# ssl_certificate /path/to/cert;
# ssl_certificate_key /path/to/key;

# Reload
sudo nginx -t && sudo systemctl reload nginx
```

---

## Maintenance Windows

### Scheduled Maintenance

**Standard Maintenance Window:**
- **Day:** Sunday
- **Time:** 02:00 - 04:00 UTC (off-peak)
- **Frequency:** Monthly (first Sunday)
- **Duration:** Up to 2 hours
- **Notice:** 7 days advance notice

**Emergency Maintenance:**
- Critical security patches
- Data corruption risk mitigation
- Infrastructure failures
- Notice: As soon as possible (minimum 1 hour if feasible)

### Maintenance Procedures

#### Pre-Maintenance Checklist

**7 Days Before:**
- [ ] Schedule announced to stakeholders
- [ ] Maintenance plan documented
- [ ] Rollback plan prepared
- [ ] Team availability confirmed

**24 Hours Before:**
- [ ] Final maintenance plan review
- [ ] Customer notification sent
- [ ] Backup completed and verified
- [ ] On-call schedule confirmed

**1 Hour Before:**
- [ ] Team ready on Slack/video call
- [ ] All tools and access verified
- [ ] Final go/no-go decision
- [ ] Maintenance mode enabled (if applicable)

#### Maintenance Execution

**1. Enable Maintenance Mode (Optional)**

```bash
# Create maintenance page
# Served by Nginx when backend is down
sudo nano /var/www/html/maintenance.html

# Configure Nginx to serve maintenance page
sudo nano /etc/nginx/sites-available/default
# Add: error_page 502 503 504 /maintenance.html;

# Reload
sudo systemctl reload nginx
```

**2. Stop Services**

```bash
cd /opt/myhibachi/app
docker compose -f docker-compose.prod.yml stop
```

**3. Perform Maintenance**

Examples:
- Database schema changes
- Major version upgrades
- Server configuration changes
- Security patches
- Infrastructure changes

**4. Restart Services**

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

**5. Verify Services**

```bash
# Run health checks
./ops/system_health_monitor.py --once

# Run smoke tests
pytest tests/test_smoke.py -v

# Monitor for 30 minutes
```

**6. Disable Maintenance Mode**

```bash
# Remove maintenance page configuration
sudo nano /etc/nginx/sites-available/default
# Remove error_page directive

sudo systemctl reload nginx
```

#### Post-Maintenance

- [ ] All services confirmed healthy
- [ ] Customer notification: "Maintenance complete"
- [ ] Incident ticket closed
- [ ] Post-maintenance report created
- [ ] Lessons learned documented

---

## Disaster Recovery

### Backup Strategy

**Automated Backups:**

**Database:**
- **Frequency:** Daily at 03:00 UTC
- **Retention:** 30 days
- **Location:** `/var/backups/myhibachi/`
- **Method:** `pg_dump` via backup script
- **Verification:** Automated restore test weekly

**Configuration:**
- **Frequency:** On every change (Git)
- **Location:** GitHub repository
- **Method:** Version control

**User Uploads (if applicable):**
- **Frequency:** Daily
- **Location:** External storage (S3/Cloud)
- **Method:** Rsync or cloud sync

**Backup Script Location:**
`/opt/myhibachi/app/ops/backup_db.py`

**Manual Backup:**

```bash
cd /opt/myhibachi/app
python3 ops/backup_db.py

# Verify backup
ls -lh /var/backups/myhibachi/
```

### Restore Procedures

#### Database Restore

**Full Database Restore:**

```bash
# Stop backend services
cd /opt/myhibachi/app
docker compose -f docker-compose.prod.yml stop fastapi-backend

# List available backups
ls -lh /var/backups/myhibachi/

# Restore from backup
docker compose exec postgres psql -U postgres -c "DROP DATABASE myhibachi;"
docker compose exec postgres psql -U postgres -c "CREATE DATABASE myhibachi;"
cat /var/backups/myhibachi/backup-2025-10-25-030000.sql | \
  docker compose exec -T postgres psql -U myhibachi -d myhibachi

# Verify restore
docker compose exec postgres psql -U myhibachi -c "
SELECT count(*) FROM bookings;
SELECT count(*) FROM customers;
"

# Restart backend
docker compose -f docker-compose.prod.yml start fastapi-backend

# Verify service
curl https://mhapi.mysticdatanode.net/health
```

**Point-in-Time Restore:**

Not currently supported. Requires WAL archiving setup.

**To implement:**
```bash
# Enable WAL archiving in PostgreSQL
# Edit postgresql.conf:
# wal_level = replica
# archive_mode = on
# archive_command = 'cp %p /var/lib/postgresql/archive/%f'
```

#### Application Code Restore

```bash
# Restore from Git
cd /opt/myhibachi/app
git fetch origin
git checkout [commit-hash]

# Rebuild and restart
docker compose -f docker-compose.prod.yml up -d --build

# Verify
curl https://mhapi.mysticdatanode.net/health
```

### Disaster Scenarios

#### Scenario 1: Complete Server Failure

**Recovery Steps:**

1. **Provision New Server**
   - Same specifications as original
   - Install OS (Ubuntu 22.04)
   - Run `/opt/myhibachi/app/deploy.sh`

2. **Restore Database**
   - Copy backup from external storage
   - Run restore procedure

3. **Deploy Application**
   - Clone repository
   - Configure environment
   - Start services

4. **Update DNS**
   - Point domain to new server IP
   - Wait for DNS propagation (up to 24h)

**RTO (Recovery Time Objective):** 4 hours  
**RPO (Recovery Point Objective):** 24 hours (last backup)

#### Scenario 2: Database Corruption

**Recovery Steps:**

1. **Stop Backend Services**
2. **Assess Corruption**
   ```bash
   docker compose exec postgres psql -U postgres -c "
   SELECT * FROM pg_database WHERE datname = 'myhibachi';
   "
   ```
3. **Attempt Repair**
   ```bash
   docker compose exec postgres psql -U postgres -c "
   REINDEX DATABASE myhibachi;
   VACUUM FULL myhibachi;
   "
   ```
4. **If Repair Fails, Restore from Backup**
5. **Verify Data Integrity**
6. **Restart Services**

**RTO:** 2 hours  
**RPO:** 24 hours

#### Scenario 3: Accidental Data Deletion

**Recovery Steps:**

1. **Stop Writes** (if possible)
2. **Identify Deleted Data**
   ```bash
   # Check recent database logs
   docker compose exec postgres tail -100 /var/log/postgresql/postgresql.log
   ```
3. **Restore from Backup to Temporary Database**
   ```bash
   docker compose exec postgres psql -U postgres -c "CREATE DATABASE myhibachi_temp;"
   cat /var/backups/myhibachi/backup-latest.sql | \
     docker compose exec -T postgres psql -U myhibachi -d myhibachi_temp
   ```
4. **Extract Deleted Data**
   ```bash
   docker compose exec postgres psql -U myhibachi -d myhibachi_temp -c "
   SELECT * FROM [table] WHERE [conditions];
   " > recovered_data.sql
   ```
5. **Import to Production**
   ```bash
   cat recovered_data.sql | \
     docker compose exec -T postgres psql -U myhibachi -d myhibachi
   ```
6. **Verify Data Integrity**
7. **Resume Normal Operations**

**RTO:** 1 hour  
**RPO:** 24 hours

---

## On-Call Procedures

### On-Call Schedule

**Rotation:** Weekly (Monday 09:00 UTC - Monday 09:00 UTC)  
**Coverage:** 24/7  
**Team Size:** Minimum 2 engineers (primary + backup)

**Responsibilities:**
- Respond to production alerts within 5 minutes
- Investigate and resolve P1/P2 incidents
- Perform deployments (if scheduled)
- Coordinate with team for escalations
- Document incidents and resolutions

### On-Call Handoff

**Outgoing Engineer:**
- [ ] Brief incoming engineer on current issues
- [ ] Share ongoing incident tickets
- [ ] Highlight any scheduled maintenance
- [ ] Ensure incoming engineer has access to all tools
- [ ] Update on-call schedule in PagerDuty

**Incoming Engineer:**
- [ ] Test alert reception (PagerDuty test alert)
- [ ] Verify access to production systems
- [ ] Review recent incidents
- [ ] Check monitoring dashboards
- [ ] Confirm backup engineer availability

### On-Call Tools Access

**Required Access:**
- VPS SSH (key-based authentication)
- Vercel Dashboard
- Sentry
- PagerDuty
- Slack #incidents channel
- GitHub (for deployments/rollbacks)
- Documentation (this runbook)

### Escalation Path

**Level 1: On-Call Engineer** (Primary responder)
- Respond within 5 minutes
- Investigate and attempt resolution
- Escalate if unable to resolve in 30 minutes (P1) or 1 hour (P2)

**Level 2: Engineering Lead**
- Escalate via phone call + Slack
- Provide technical guidance
- Approve major decisions (rollback, extended maintenance)
- Escalate to CTO if business-critical

**Level 3: CTO**
- Escalate via phone call
- Major system-wide outages
- Data breach or security incident
- Customer communication approval

**External Escalation:**
- **Hosting Provider:** VPS outages, network issues
- **Vercel Support:** Frontend deployment issues
- **Database Consultant:** Complex database issues
- **Security Team:** Security incidents

---

## Escalation Matrix

| Issue Type | Severity | First Response | Escalation (if unresolved) |
|-----------|----------|----------------|---------------------------|
| **Complete Outage** | P1 | On-Call Engineer (5 min) | Engineering Lead (30 min) → CTO (1 hour) |
| **API Errors >10%** | P2 | On-Call Engineer (15 min) | Engineering Lead (1 hour) |
| **Database Issues** | P2 | On-Call Engineer (15 min) | Engineering Lead (1 hour) → DBA (2 hours) |
| **Security Breach** | P1 | On-Call Engineer (immediate) | Security Lead (immediate) → CTO (immediate) |
| **Data Loss** | P1 | On-Call Engineer (immediate) | Engineering Lead (15 min) → CTO (30 min) |
| **Performance Degradation** | P3 | On-Call Engineer (1 hour) | Engineering Lead (next business day) |
| **External API Down** | P3 | On-Call Engineer (1 hour) | Engineering Lead (4 hours) |

---

## Appendices

### Appendix A: Environment Variables Reference

**Required Variables:**

```env
# Database
DATABASE_URL=postgresql://user:password@host:port/database
REDIS_URL=redis://host:port/db

# Security
JWT_SECRET_KEY=<strong-secret-key>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=["https://myhibachichef.com","https://admin.mysticdatanode.net"]

# External APIs
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
OPENAI_API_KEY=sk-...
RINGCENTRAL_CLIENT_ID=...
RINGCENTRAL_CLIENT_SECRET=...

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=...
SMTP_PASSWORD=...
EMAIL_FROM=noreply@myhibachi.com

# Monitoring
SENTRY_DSN=https://...
LOG_LEVEL=INFO

# Features
ENABLE_ADMIN_API=true
ENABLE_ANALYTICS=true
```

### Appendix B: Port Reference

| Port | Service | Protocol | Access |
|------|---------|----------|--------|
| 80 | HTTP (redirect to HTTPS) | HTTP | Public |
| 443 | HTTPS (Nginx) | HTTPS | Public |
| 8003 | FastAPI Backend | HTTP | Internal/Public |
| 8002 | AI Backend | HTTP | Internal/Public |
| 5432 | PostgreSQL | TCP | Internal only |
| 6379 | Redis | TCP | Internal only |
| 22 | SSH | TCP | Admin only |

### Appendix C: Key File Locations

| File/Directory | Purpose |
|---------------|---------|
| `/opt/myhibachi/app` | Application root |
| `/opt/myhibachi/config/.env` | Environment variables |
| `/var/backups/myhibachi/` | Database backups |
| `/var/log/myhibachi/` | Application logs |
| `/etc/nginx/sites-available/default` | Nginx configuration |
| `/etc/systemd/system/myhibachi-*.service` | Systemd services |
| `/var/lib/myhibachi/monitoring/` | Monitoring data |

### Appendix D: Useful Commands Cheat Sheet

```bash
# Service management
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml restart [service]
docker compose -f docker-compose.prod.yml logs -f [service]

# Health checks
curl https://mhapi.mysticdatanode.net/health
./ops/system_health_monitor.py --once

# Database
docker compose exec postgres psql -U myhibachi
docker compose exec postgres psql -U myhibachi -c "SELECT count(*) FROM bookings;"

# Redis
docker compose exec redis redis-cli
docker compose exec redis redis-cli INFO
docker compose exec redis redis-cli FLUSHDB

# Backups
python3 ops/backup_db.py
ls -lh /var/backups/myhibachi/

# Logs
docker compose logs --since 1h
docker compose logs -f --tail=100 fastapi-backend

# System
htop
df -h
free -m
top

# Git
git log --oneline -10
git checkout [commit-hash]
git status
```

---

**Document Version:** 1.0  
**Last Updated:** October 25, 2025  
**Maintained By:** DevOps Team  
**Review Schedule:** Quarterly  
**Next Review:** January 25, 2026

---

## Related Documentation

- [TESTING_COMPREHENSIVE_GUIDE.md](./TESTING_COMPREHENSIVE_GUIDE.md) - Testing procedures
- [FINAL_PRODUCTION_DEPLOYMENT_GUIDE.md](./FINAL_PRODUCTION_DEPLOYMENT_GUIDE.md) - Deployment guide
- [DATABASE_SETUP_GUIDE.md](./DATABASE_SETUP_GUIDE.md) - Database setup
- [LOCAL_DEVELOPMENT_SETUP.md](./LOCAL_DEVELOPMENT_SETUP.md) - Local development

---
