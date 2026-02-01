---
applyTo: '**'
---

# My Hibachi – Rollback & Safety Procedures

**Priority: CRITICAL** – Know how to recover from failures.

---

## 🚨 When to Rollback

### Immediate Rollback Triggers:

| Trigger          | Action                    |
| ---------------- | ------------------------- |
| Production down  | Rollback immediately      |
| Data corruption  | Rollback + restore backup |
| Security breach  | Rollback + investigate    |
| Payment failures | Rollback + notify Stripe  |
| 500 errors > 1%  | Rollback + investigate    |

### Investigate First (Don't Panic):

| Symptom            | Action                            |
| ------------------ | --------------------------------- |
| Slow performance   | Check logs, may not need rollback |
| Single user issue  | May be user-specific              |
| Intermittent error | May be external service           |

---

## 🔄 Rollback Methods

### Method 1: Feature Flag (Fastest - Seconds)

```bash
# Disable the problematic feature
# In .env or environment config:
FEATURE_NEW_BOOKING_FLOW=false

# No redeployment needed
# App reads flag on each request
```

### Method 2: Git Revert (Minutes)

```bash
# 1. Find the bad commit
git log --oneline -10

# 2. Create revert commit
git revert <commit-hash>

# 3. Push to trigger deployment
git push origin main
```

### Method 3: Deploy Previous Version (Minutes)

```bash
# 1. Find last good commit
git log --oneline -10

# 2. Reset to that commit
git checkout <good-commit-hash>

# 3. Create hotfix branch
git checkout -b hotfix/rollback-<date>

# 4. PR to main (expedited)
```

### Method 4: Database Restore (Last Resort)

```bash
# 1. Stop application with Docker (PRIMARY)
docker compose -f docker-compose.prod.yml stop production-api

# 2. Restore from backup (PostgreSQL is VPS-native)
pg_restore -d myhibachi_production backup_YYYYMMDD.sql

# 3. Restart application with Docker
docker compose -f docker-compose.prod.yml up -d production-api
```

**LEGACY FALLBACK (if Docker unavailable):**

```bash
# 1. Stop application
sudo systemctl stop myhibachi-backend.service

# 2. Restore from backup
pg_restore -d myhibachi_production backup_YYYYMMDD.sql

# 3. Restart application
sudo systemctl start myhibachi-backend.service
```

---

## 📊 Rollback Decision Matrix

| Impact      | User-Facing? | Data Risk? | Action                       |
| ----------- | ------------ | ---------- | ---------------------------- |
| 🟢 Low      | No           | No         | Monitor, fix in next release |
| 🟡 Medium   | Some users   | No         | Feature flag OFF             |
| 🟠 High     | Many users   | No         | Git revert                   |
| 🔴 Critical | All users    | Yes        | Full rollback + restore      |

---

## 🛡️ Pre-Deployment Safety

### Before Deploying:

- [ ] All tests passing
- [ ] Staging verified 48+ hours
- [ ] Feature flags configured
- [ ] Rollback plan documented
- [ ] On-call person identified
- [ ] Backup verified

### Deployment Checklist:

```bash
# 1. Take database backup
pg_dump myhibachi_prod > backup_$(date +%Y%m%d_%H%M).sql

# 2. Note current version
git log -1 --format="%H %s"

# 3. Deploy
git push origin main

# 4. Verify health
curl https://api.myhibachi.com/health

# 5. Monitor for 30 minutes
# Watch logs, error rates, response times
```

---

## 📋 Incident Response Steps

### 1. Detect (0-5 minutes)

```
- Alert from monitoring
- User report
- Error spike in logs
```

### 2. Assess (5-10 minutes)

```
- Is it affecting users?
- Is it causing data issues?
- What changed recently?
```

### 3. Decide (10-15 minutes)

```
- Feature flag disable?
- Git revert?
- Full rollback?
```

### 4. Execute (15-30 minutes)

```
- Apply chosen rollback method
- Verify recovery
- Notify stakeholders
```

### 5. Communicate (Ongoing)

```
- Update status page
- Notify affected users
- Send internal update
```

### 6. Post-Mortem (24-48 hours)

```
- Document what happened
- Root cause analysis
- Prevention measures
- Update runbook
```

---

## 🔧 Emergency Commands

### Check System Health:

```bash
# Backend health (production)
curl https://mhapi.mysticdatanode.net/health

# Backend health (staging)
curl https://staging-api.mysticdatanode.net/health

# Docker container status (PRIMARY)
docker compose -f docker-compose.prod.yml ps

# Database connections
psql -c "SELECT count(*) FROM pg_stat_activity;"

# Redis status (Docker)
docker compose -f docker-compose.prod.yml exec redis redis-cli ping

# Disk space
df -h

# Memory usage
free -m
```

### View Logs:

```bash
# Backend logs (Docker - PRIMARY)
docker compose -f docker-compose.prod.yml logs -f production-api

# Backend logs (systemd - LEGACY FALLBACK)
sudo journalctl -u myhibachi-backend.service -f

# Nginx logs
sudo tail -f /var/log/nginx/error.log

# Database logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

### Restart Services:

```bash
# Backend with Docker (PRIMARY)
docker compose -f docker-compose.prod.yml restart production-api

# Backend with systemd (LEGACY FALLBACK)
sudo systemctl restart myhibachi-backend.service

# Nginx
sudo systemctl restart nginx

# Redis (Docker)
docker compose -f docker-compose.prod.yml restart redis

# PostgreSQL (VPS-native - NOT containerized)
sudo systemctl restart postgresql
```

---

## 📱 Emergency Contacts

| Role           | Contact Method  |
| -------------- | --------------- |
| On-Call Dev    | Slack #on-call  |
| Backend Lead   | Direct message  |
| DevOps         | Slack #devops   |
| Database Admin | Slack #database |

---

## ✅ Post-Rollback Checklist

After rolling back:

- [ ] Verify service restored
- [ ] Check error rates back to normal
- [ ] Verify no data corruption
- [ ] Update status page
- [ ] Notify stakeholders
- [ ] Create post-mortem ticket
- [ ] Document lessons learned

---

## 🔗 Related Docs

- `docs/05-OPERATIONS/INCIDENT_RESPONSE.md` – Full runbook
- `docs/05-OPERATIONS/PRODUCTION_RUNBOOK.md` – Operations guide
- `docs/04-DEPLOYMENT/checklists/` – Deployment checklists
