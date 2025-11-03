# 🚀 PRODUCTION DEPLOYMENT CHECKLIST
## Phase 2A+2C Performance Optimization

**Deployment Date:** _____________  
**Deployed By:** _____________  
**PR:** #3 (feature/tool-calling-phase-1)  
**Expected Duration:** 30-45 minutes  

---

## ⚠️ PRE-DEPLOYMENT CHECKLIST

### 1. Code Review & Approval
- [ ] PR #3 reviewed and approved by team lead
- [ ] All CI/CD checks passed (tests, builds, linting)
- [ ] No merge conflicts with main branch
- [ ] All 9/9 tests passing locally
- [ ] Documentation reviewed and accurate

### 2. Database Readiness
- [ ] **Verify indexes deployed** (45/45 performance indexes)
  ```sql
  -- Run in Supabase SQL Editor:
  SELECT COUNT(*) FROM pg_indexes 
  WHERE indexname LIKE 'idx_%' 
  AND schemaname IN ('core', 'identity', 'lead', 'newsletter', 'integra', 'feedback');
  -- Expected: 14+ indexes
  ```
- [ ] Database backup completed (timestamp: _________)
- [ ] Tables exist: `ai_conversations`, `ai_messages`, `emotion_history`
- [ ] Database connection pool configured (pool_size=20, max_overflow=10)

### 3. Environment Variables
- [ ] `.env` file backed up
- [ ] All required environment variables present:
  - [ ] `DATABASE_URL` (Supabase connection string)
  - [ ] `OPENAI_API_KEY` (for emotion detection)
  - [ ] `REDIS_URL` (if using Redis caching)
  - [ ] `TWILIO_ACCOUNT_SID` (properly in .env, not committed)
  - [ ] `TWILIO_AUTH_TOKEN` (properly in .env, not committed)

### 4. Backup Current Production
- [ ] Create git tag for current production: `git tag v1.0-pre-phase2`
- [ ] Backup current backend code: `cp -r apps/backend apps/backend.backup.$(date +%Y%m%d)`
- [ ] Export current environment: `cp .env .env.backup.$(date +%Y%m%d)`
- [ ] Document current performance baseline (if not already done)

### 5. Dependencies Check
- [ ] Python dependencies updated: `pip install -r requirements.txt`
- [ ] No conflicting package versions
- [ ] All imports working: `python -c "from api.ai.memory import postgresql_memory"`
- [ ] No missing packages

---

## 🚀 DEPLOYMENT STEPS

### Step 1: Merge to Main (5 minutes)
- [ ] Final review of PR #3
- [ ] Merge PR using **"Squash and merge"** or **"Merge commit"** (your preference)
- [ ] Verify merge successful on GitHub
- [ ] Pull latest main branch locally:
  ```bash
  git checkout main
  git pull origin main
  ```

### Step 2: Deploy Backend to VPS (15-20 minutes)

#### Option A: Using Plesk Git Integration
- [ ] Login to Plesk panel
- [ ] Navigate to Git section
- [ ] Click "Pull Updates" or "Deploy"
- [ ] Select main branch
- [ ] Wait for deployment to complete
- [ ] Check deployment logs for errors

#### Option B: Manual SSH Deployment
```bash
# SSH into VPS
ssh user@your-vps-ip

# Navigate to project directory
cd /path/to/myhibachi-backend

# Stash any local changes
git stash

# Pull latest changes
git checkout main
git pull origin main

# Install/update dependencies
pip install -r requirements.txt

# Restart the application
# (Method depends on your setup: systemd, supervisor, etc.)
sudo systemctl restart myhibachi-api
# OR
sudo supervisorctl restart myhibachi-api
# OR via Plesk
# Plesk > Domains > your-domain > Restart Application
```

### Step 3: Verify Deployment (5 minutes)
- [ ] Check application is running:
  ```bash
  curl https://your-api-domain.com/health
  # Expected: {"status": "healthy"}
  ```
- [ ] Check logs for startup errors:
  ```bash
  tail -f /var/log/myhibachi-api/error.log
  # OR via Plesk: Plesk > Logs > Error Log
  ```
- [ ] Verify database connection working
- [ ] Check no import errors in logs

### Step 4: Smoke Tests (5 minutes)
- [ ] **Test 1: Health Check**
  ```bash
  curl https://your-api-domain.com/health
  ```
- [ ] **Test 2: AI Chat Message Storage**
  ```bash
  curl -X POST https://your-api-domain.com/api/ai/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "Hello, test message", "customer_id": "test-123"}'
  ```
  Expected: Response in <1000ms ✅
  
- [ ] **Test 3: Booking Creation**
  ```bash
  # Use your existing booking API endpoint
  # Expected: Response in <500ms ✅
  ```
  
- [ ] **Test 4: Background Tasks**
  - Check emotion_history table for new entries (should populate async)
  - Check logs for "Background task completed" messages

---

## 📊 POST-DEPLOYMENT MONITORING (First 2 Hours)

### Immediate Checks (0-15 minutes)
- [ ] **Response Times** (every 5 minutes for first 30 min)
  - [ ] API health endpoint: <100ms
  - [ ] store_message: <1000ms (target 745ms)
  - [ ] Booking creation: <500ms (target 367ms)
  
- [ ] **Error Rates**
  - [ ] Check application logs for errors
  - [ ] Monitor error tracking (Sentry, etc. if configured)
  - [ ] Expected: 0 errors related to new code

- [ ] **Database Performance**
  ```sql
  -- Check query performance
  SELECT query, mean_exec_time, calls 
  FROM pg_stat_statements 
  WHERE query LIKE '%ai_messages%' OR query LIKE '%emotion_history%'
  ORDER BY mean_exec_time DESC 
  LIMIT 10;
  ```

### First Hour Monitoring
- [ ] **Memory Usage**
  ```bash
  # Check application memory
  ps aux | grep python | grep myhibachi
  # Should be stable, not increasing rapidly
  ```

- [ ] **Background Tasks**
  - [ ] Verify emotion stats updating in emotion_history table
  - [ ] Verify follow-up scheduler creating tasks
  - [ ] Check for any task failures in logs

- [ ] **API Response Distribution**
  - Monitor P50, P95, P99 response times
  - Expected P95: <850ms (store_message)
  - Expected P95: <420ms (booking)

### First 2 Hours Monitoring
- [ ] **User Impact**
  - [ ] No user complaints
  - [ ] No increase in support tickets
  - [ ] Booking conversion rate stable or improved

- [ ] **System Stability**
  - [ ] No memory leaks
  - [ ] CPU usage normal (<70%)
  - [ ] Database connections stable (<50% of pool)

---

## 📈 PERFORMANCE VALIDATION (24-48 Hours)

### Metrics to Track

#### Performance Metrics (Compare to Baseline)
```
Baseline (Before Phase 2):
├─ store_message: 2000ms average
├─ Booking creation: 305ms average  
├─ Total user journey: 4281ms
└─ Background tasks: Blocking (1931ms)

Expected (After Phase 2):
├─ store_message: 745ms average ✅ (62.8% faster)
├─ Booking creation: 305ms average ✅ (unchanged, already optimal)
├─ Total user journey: 1105ms ✅ (74.2% faster)
└─ Background tasks: 0ms blocking ✅ (100% async)
```

#### Success Metrics
- [ ] **Response Time:** P95 < 850ms (store_message)
- [ ] **Response Time:** P95 < 420ms (booking)
- [ ] **Background Task Success Rate:** >99%
- [ ] **Error Rate:** <0.1%
- [ ] **Database Query Time:** <270ms per query average

#### Business Metrics
- [ ] **Booking Conversion Rate:** Stable or improved
- [ ] **User Satisfaction:** No decline in ratings
- [ ] **System Uptime:** >99.9%

### Monitoring Queries (Run Daily)

**1. Average Response Times:**
```sql
-- If using application logging table
SELECT 
    DATE(created_at) as date,
    AVG(response_time_ms) as avg_response_time,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95_response_time
FROM api_logs
WHERE endpoint = '/api/ai/chat'
    AND created_at >= NOW() - INTERVAL '24 hours'
GROUP BY DATE(created_at);
```

**2. Background Task Success Rate:**
```sql
-- Check emotion_history entries (should match ai_messages count)
SELECT 
    DATE(created_at) as date,
    COUNT(*) as emotion_records
FROM emotion_history
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY DATE(created_at);

-- Compare to message count
SELECT 
    DATE(created_at) as date,
    COUNT(*) as message_count
FROM ai_messages
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY DATE(created_at);

-- Success rate should be ~100%
```

**3. Database Performance:**
```sql
-- Query execution times
SELECT 
    substring(query from 1 for 50) as query_start,
    calls,
    mean_exec_time,
    max_exec_time
FROM pg_stat_statements
WHERE query LIKE '%ai_messages%' OR query LIKE '%ai_conversations%'
ORDER BY mean_exec_time DESC
LIMIT 10;
```

---

## 🔄 ROLLBACK PROCEDURES

### When to Rollback
Trigger rollback if ANY of these occur:
- [ ] P95 response time >1500ms (worse than baseline)
- [ ] Error rate >5%
- [ ] Database connection failures
- [ ] Memory leak detected (memory growing >500MB/hour)
- [ ] Critical bugs affecting bookings
- [ ] Multiple user complaints (>3 in first hour)

### Rollback Steps (15-20 minutes)

#### Step 1: Stop Current Deployment
```bash
# SSH into VPS
ssh user@your-vps-ip

# Stop the application
sudo systemctl stop myhibachi-api
# OR via Plesk
```

#### Step 2: Restore Previous Code
```bash
# Navigate to project directory
cd /path/to/myhibachi-backend

# Checkout previous version tag
git checkout v1.0-pre-phase2

# OR restore from backup
rm -rf apps/backend
cp -r apps/backend.backup.YYYYMMDD apps/backend

# Restore environment if needed
cp .env.backup.YYYYMMDD .env
```

#### Step 3: Reinstall Dependencies (if needed)
```bash
# If requirements.txt changed
pip install -r requirements.txt
```

#### Step 4: Restart Application
```bash
# Restart with previous version
sudo systemctl start myhibachi-api
# OR via Plesk

# Verify it's running
curl https://your-api-domain.com/health
```

#### Step 5: Verify Rollback Success
- [ ] Application responding normally
- [ ] Response times back to baseline (2000ms for store_message is OK)
- [ ] No errors in logs
- [ ] Users can book normally

#### Step 6: Document & Communicate
- [ ] Document what went wrong
- [ ] Notify team of rollback
- [ ] Create GitHub issue with rollback details
- [ ] Plan fix and re-deployment

---

## 🎯 SUCCESS CRITERIA

Deployment is considered **SUCCESSFUL** if after 48 hours:

### Performance ✅
- [x] store_message P95 < 850ms
- [x] Booking creation P95 < 420ms  
- [x] Overall journey < 1500ms
- [x] Background tasks 100% async (0ms blocking)

### Stability ✅
- [x] Error rate < 0.1%
- [x] No memory leaks
- [x] Database connections stable
- [x] Background task success rate >99%

### Business ✅
- [x] No increase in support tickets
- [x] Booking conversion rate stable/improved
- [x] User satisfaction maintained
- [x] System uptime >99.9%

---

## 📞 EMERGENCY CONTACTS

**If issues occur:**
1. **Immediate:** Trigger rollback (see above)
2. **Notify:** Team lead / On-call engineer
3. **Document:** Create incident report
4. **Follow-up:** Schedule post-mortem meeting

**Key Contacts:**
- Developer: _____________
- DevOps: _____________  
- On-Call: _____________
- Database Admin: _____________

---

## 📝 DEPLOYMENT NOTES

**Deployment Start Time:** _____________  
**Deployment End Time:** _____________  
**Total Duration:** _____________

**Issues Encountered:**
- [ ] None ✅
- [ ] Minor (list below)
- [ ] Major (rollback required)

**Notes:**
```
[Add any observations, warnings, or notes here]
```

**Final Status:**
- [ ] ✅ Deployment Successful
- [ ] ⚠️ Deployment Successful with Minor Issues
- [ ] ❌ Deployment Failed - Rolled Back

**Signed Off By:** _____________  
**Date:** _____________

---

## 📚 REFERENCE DOCUMENTATION

- **Performance Optimization Report:** `PERFORMANCE_OPTIMIZATION_FINAL_REPORT.md`
- **Deep Performance Analysis:** `DEEP_PERFORMANCE_ANALYSIS.md`
- **Project Status Report:** `PROJECT_STATUS_NOVEMBER_2025.md`
- **SQL Indexes Guide:** `database/INDEX_DEPLOYMENT_GUIDE.md`
- **Rollback Procedures:** This document (section above)
- **Monitoring Queries:** This document (section above)

---

**Last Updated:** November 2, 2025  
**Version:** 1.0  
**Status:** Ready for Production Deployment ✅
