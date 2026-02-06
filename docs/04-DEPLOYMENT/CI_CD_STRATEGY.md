# 🚀 CI/CD Strategy Overview - My Hibachi Project

## Executive Summary

**Frontend**: Vercel handles deployment automatically ✅ **Backend**:
GitHub Actions → Plesk VPS with full automation 🚀

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    GitHub Repository                     │
│                   (main branch push)                     │
└─────────────────┬───────────────────────┬───────────────┘
                  │                       │
                  │                       │
    ┌─────────────▼────────────┐   ┌─────▼──────────────────┐
    │  Frontend CI/CD          │   │  Backend CI/CD          │
    │  (Quality Checks Only)   │   │  (Full Deployment)      │
    └─────────────┬────────────┘   └─────┬──────────────────┘
                  │                       │
                  │                       │
    ┌─────────────▼────────────┐   ┌─────▼──────────────────┐
    │  Vercel Deployment       │   │  VPS (Plesk)            │
    │  - Auto Deploy           │   │  - SSH Deploy           │
    │  - CDN Distribution      │   │  - Supervisor           │
    │  - Preview URLs          │   │  - Nginx Proxy          │
    └──────────────────────────┘   └─────────────────────────┘
```

---

## Frontend CI/CD (Customer + Admin)

### What Vercel Handles Automatically ✅

1. **Automatic Deployment**
   - Push to `main` → Production deploy
   - Push to `develop` → Staging deploy
   - Pull Request → Preview deploy with unique URL

2. **Build Optimization**
   - Next.js optimization
   - Code splitting
   - Image optimization
   - Static generation

3. **CDN Distribution**
   - Global edge network
   - Auto-caching
   - Fast response times worldwide

4. **SSL Certificates**
   - Automatic SSL for all deployments
   - Auto-renewal
   - Custom domains supported

### What GitHub Actions Adds 🔍

**Purpose**: Quality checks BEFORE Vercel deploys

**Workflow**: `.github/workflows/frontend-quality-check.yml`

**Steps**:

```yaml
1. 🔍 ESLint - Check code quality 2. 🎨 Prettier - Check formatting 3.
🏗️ Build - Ensure builds successfully 4. 🧪 Tests - Run unit tests (if
available) 5. 📊 Report - Build size and metrics
```

**Triggers**:

- Push to `main` or `develop`
- Pull request to `main` or `develop`
- Only when frontend files change

**Result**: If checks fail, you'll know before Vercel deploys ✅

**Configuration Needed**: None! Vercel handles everything else

---

## Backend CI/CD (FastAPI)

### What GitHub Actions Handles 🚀

**Workflow**: `.github/workflows/backend-cicd.yml`

**Full CI/CD Pipeline**:

#### 1. Test Stage 🧪

```yaml
- Setup Python 3.11
- Install dependencies
- Run linting (flake8)
- Run unit tests with coverage
- Test against PostgreSQL & Redis
```

**Triggers when**:

- Push to `main` or `develop`
- Pull request to `main` or `develop`
- Backend files change

#### 2. Build Stage 🏗️

```yaml
- Install dependencies
- Security check (Safety)
- Validate database migrations
- Create deployment package
```

#### 3. Deploy Stage 🚀 (main branch only)

```yaml
- Upload code to VPS via SSH
- Backup current version
- Extract new version
- Install/update dependencies
- Run database migrations
- Restart application (Supervisor)
- Health check verification
```

#### 4. Rollback Stage 🔄 (if deployment fails)

```yaml
- Restore from latest backup
- Restart application
- Verify health
- Send notification
```

---

## Deployment Comparison

| Feature                  | Frontend (Vercel)         | Backend (VPS + CI/CD)     |
| ------------------------ | ------------------------- | ------------------------- |
| **Automatic Deployment** | ✅ Built-in               | ✅ Via GitHub Actions     |
| **Preview Deployments**  | ✅ Auto PR previews       | ❌ Production only        |
| **Rollback**             | ✅ One-click in Vercel    | ✅ Automated in CI/CD     |
| **SSL Certificate**      | ✅ Automatic              | ✅ Let's Encrypt (Plesk)  |
| **CDN**                  | ✅ Global edge network    | ❌ Single server          |
| **Monitoring**           | ✅ Vercel Analytics       | 🔧 Manual setup needed    |
| **Logs**                 | ✅ Real-time in dashboard | ✅ Supervisor + file logs |
| **Scaling**              | ✅ Auto-scaling           | 🔧 Manual VPS upgrade     |
| **Cost**                 | $ Vercel plan             | $ VPS hosting             |
| **Setup Complexity**     | ⭐ Easy (5 min)           | ⭐⭐⭐ Medium (1 hour)    |

---

## Do You Need Frontend CI/CD? 🤔

### ❌ You DON'T Need if:

- Vercel deployment is working fine
- You trust your local testing
- Team is small (1-3 developers)
- Fixes are easy to deploy quickly

### ✅ You DO Need if:

- Multiple developers pushing code
- Want automated quality gates
- Need pre-deployment validation
- Want build size monitoring
- Planning to scale team

### ✅ Recommendation: **YES, Use It!**

**Why?**

1. **Catches errors early** - Before Vercel deploys
2. **Team protection** - Prevents bad code from reaching production
3. **No extra cost** - GitHub Actions free tier (2,000 min/month)
4. **Low overhead** - Runs in 2-3 minutes
5. **Peace of mind** - Automated quality checks

---

## Backend CI/CD - **Required!** ✅

### Why Backend Needs Full CI/CD:

1. **Complex Deployment**
   - Database migrations
   - Dependency management
   - Service restarts
   - Environment configuration

2. **Risk Management**
   - Automated backups before deploy
   - Health checks after deploy
   - Automatic rollback on failure
   - Zero downtime deployments

3. **Consistency**
   - Same deployment process every time
   - No manual SSH commands
   - No forgotten steps
   - Documented in code

4. **Time Savings**
   - Manual deploy: ~10 minutes
   - Automated: ~2 minutes
   - No human errors
   - Deploy from anywhere

---

## Setup Timeline

### Frontend (Vercel + Quality Checks)

**Step 1**: Vercel Setup (5 minutes)

```
1. Connect GitHub repo to Vercel
2. Configure build settings
3. Deploy!
```

**Step 2**: GitHub Actions Setup (10 minutes)

```
1. Files already created ✅
2. Push to GitHub
3. Workflows run automatically
```

**Total Time**: **15 minutes** ⏱️

### Backend (VPS + CI/CD)

**Step 1**: Plesk VPS Setup (30 minutes)

```
1. Create domain/subdomain
2. Create database
3. Configure Python environment
4. Install dependencies
5. Configure Nginx proxy
6. Install Supervisor
7. Test manual deployment
```

**Step 2**: GitHub Actions Setup (15 minutes)

```
1. Generate SSH keys
2. Add secrets to GitHub
3. Create production environment
4. Test deployment pipeline
```

**Step 3**: Monitoring Setup (15 minutes)

```
1. Configure backups
2. Set up log rotation
3. Create health check monitoring
```

**Total Time**: **60 minutes** ⏱️

---

## Cost Analysis

### Frontend (Vercel)

| Plan           | Price     | Includes                                 |
| -------------- | --------- | ---------------------------------------- |
| **Hobby**      | FREE      | 100GB bandwidth, 1 team member           |
| **Pro**        | $20/month | Unlimited bandwidth, password protection |
| **Enterprise** | Custom    | Advanced features, SLA                   |

**Recommendation**: Start with **FREE** Hobby plan ✅

### Backend (VPS)

| Provider         | Plan          | Price       | Specs             |
| ---------------- | ------------- | ----------- | ----------------- |
| **DigitalOcean** | Droplet       | $12/month   | 2GB RAM, 50GB SSD |
| **Linode**       | Shared        | $12/month   | 2GB RAM, 50GB SSD |
| **Vultr**        | Cloud Compute | $12/month   | 2GB RAM, 55GB SSD |
| **Hetzner**      | Cloud         | €4.50/month | 2GB RAM, 40GB SSD |

**Recommendation**: Hetzner (best value) or DigitalOcean (best
support) ✅

### GitHub Actions

| Plan     | Price    | Includes            |
| -------- | -------- | ------------------- |
| **Free** | FREE     | 2,000 minutes/month |
| **Pro**  | $4/month | 3,000 minutes/month |

**Your Usage** (estimated):

- Frontend checks: ~3 min/deploy × 30 deploys = 90 min/month
- Backend deploy: ~2 min/deploy × 20 deploys = 40 min/month
- **Total**: ~130 min/month

**Recommendation**: **FREE** plan is plenty ✅

---

## Security Best Practices

### Frontend (Vercel)

✅ **Already Secure**:

- HTTPS everywhere
- Environment variables encrypted
- DDoS protection
- Automatic security updates

**You Need To**:

- [ ] Set up environment variables in Vercel dashboard
- [ ] Enable branch protection in GitHub
- [ ] Use preview deployments for testing

### Backend (VPS)

**You Need To**:

- [x] SSH key authentication (no passwords)
- [x] Firewall configured (UFW or Plesk firewall)
- [x] SSL certificate (Let's Encrypt)
- [ ] Regular security updates
- [ ] Database backups automated
- [ ] Fail2ban for brute force protection
- [ ] Rate limiting enabled (already done ✅)
- [ ] Environment secrets secured

---

## Monitoring & Alerts

### Frontend (Vercel)

**Built-in Monitoring**:

- ✅ Deployment status
- ✅ Build logs
- ✅ Analytics (visitors, performance)
- ✅ Error tracking (with integration)

**Recommended Additions**:

- [ ] Sentry for error tracking
- [ ] Google Analytics for user behavior
- [ ] Vercel Analytics ($10/month, optional)

### Backend (VPS)

**Required Monitoring**:

- [x] Health check endpoints (implemented today ✅)
- [ ] Uptime monitoring (UptimeRobot - FREE)
- [ ] Log aggregation (Papertrail - FREE tier)
- [ ] Performance monitoring (optional)
- [ ] Error tracking with Sentry (optional)

**Setup UptimeRobot** (5 minutes):

1. Sign up at https://uptimerobot.com
2. Add monitor: `https://mhapi.mysticdatanode.net/health`
3. Set check interval: 5 minutes
4. Add email alert

---

## Rollback Procedures

### Frontend (Vercel) - **Easy** ⭐

**Option 1: Vercel Dashboard (Instant)**

```
1. Go to Vercel Dashboard
2. Select deployment
3. Click "Promote to Production"
4. Done in 10 seconds!
```

**Option 2: Git Revert**

```powershell
git revert HEAD
git push origin main
# Vercel auto-deploys previous version
```

### Backend (VPS) - **Automated** 🤖

**Option 1: CI/CD Automatic Rollback**

- If health check fails → Auto-rollback to previous version
- No manual intervention needed

**Option 2: Manual Rollback** (if needed)

```bash
ssh user@vps
cd /var/www/vhosts/myhibachi.com/httpdocs/backend
ls backups/  # List available backups
cp -r backups/backup_20251030_143022/src .
sudo supervisorctl restart myhibachi-backend
```

**Time to Rollback**:

- Automatic: ~30 seconds
- Manual: ~2 minutes

---

## Testing Strategy

### Frontend Testing

**Local Testing** (before push):

```powershell
cd apps/customer
npm run lint
npm run build
npm run test
```

**CI Testing** (automatic):

- Runs on every push
- Runs on every PR
- Blocks merge if fails

### Backend Testing

**Local Testing**:

```powershell
cd apps/backend
pytest tests/ -v
python run_backend.py  # Manual test
```

**CI Testing** (automatic):

- Unit tests with PostgreSQL & Redis
- Linting and security checks
- Build validation
- Migration checks

**Production Testing** (after deploy):

- Automatic health checks
- Smoke tests on critical endpoints
- Response time verification

---

## Summary & Recommendations

### ✅ What You Should Do

**Frontend (Vercel)**:

1. ✅ Use Vercel for automatic deployment
2. ✅ Add GitHub Actions for quality checks (already created)
3. ✅ Set up Sentry for error tracking (optional but recommended)
4. ✅ Enable preview deployments for PRs

**Backend (VPS + Plesk)**:

1. ✅ Use GitHub Actions for full CI/CD (already created)
2. ✅ Follow Plesk setup guide (PLESK_DEPLOYMENT_SETUP_GUIDE.md)
3. ✅ Set up automated backups
4. ✅ Configure health monitoring (UptimeRobot)
5. ✅ Test rollback procedure

### ⏱️ Time Investment

| Task             | Time        | Priority    |
| ---------------- | ----------- | ----------- |
| Vercel setup     | 15 min      | 🔥 Critical |
| Frontend CI/CD   | 10 min      | ⭐ High     |
| Plesk VPS setup  | 60 min      | 🔥 Critical |
| Backend CI/CD    | 15 min      | 🔥 Critical |
| Monitoring setup | 20 min      | ⭐ High     |
| **Total**        | **2 hours** |             |

### 💰 Monthly Costs

| Service                 | Cost          | Required     |
| ----------------------- | ------------- | ------------ |
| Vercel (Hobby)          | FREE          | ✅ Yes       |
| GitHub Actions          | FREE          | ✅ Yes       |
| VPS (Hetzner)           | €4.50         | ✅ Yes       |
| Plesk (if not included) | $10-15        | ⚠️ Check VPS |
| Domain                  | $12/year      | ✅ Yes       |
| **Total**               | **~$8/month** |              |

**Plus optional**:

- Sentry (FREE tier) - Error tracking
- UptimeRobot (FREE) - Uptime monitoring
- Papertrail (FREE tier) - Log aggregation

---

## Docker Deployment (Future Migration)

> 📋 **Full Reference**: See [`DOCKER_GUIDE.md`](./DOCKER_GUIDE.md)
> for comprehensive Docker commands and configurations.

### Overview

Docker deployment is planned as a future migration path for the My
Hibachi backend. This will provide:

- **Consistent environments** across development, staging, and
  production
- **Easier scaling** with container orchestration
- **Simplified dependencies** (no more Python version conflicts)
- **Better resource isolation** between services

### Current Status

| Component       | Current         | Docker Target        |
| --------------- | --------------- | -------------------- |
| **Backend API** | Plesk + uvicorn | Docker container     |
| **Database**    | VPS PostgreSQL  | PostgreSQL container |
| **Cache**       | VPS Redis       | Redis container      |
| **Monitoring**  | Basic           | Prometheus + Grafana |

### Docker Profiles

The `docker-compose.yml` supports multiple profiles:

```bash
# Development (includes hot-reload)
docker compose --profile development up

# Production (optimized, no dev tools)
docker compose --profile production up -d

# Monitoring (Prometheus + Grafana)
docker compose --profile monitoring up -d
```

### Service Access Points (Docker)

| Service         | Port | URL                   |
| --------------- | ---- | --------------------- |
| **Backend API** | 8000 | http://localhost:8000 |
| **PostgreSQL**  | 5432 | localhost:5432        |
| **Redis**       | 6379 | localhost:6379        |
| **PgAdmin**     | 5050 | http://localhost:5050 |
| **Prometheus**  | 9090 | http://localhost:9090 |
| **Grafana**     | 3001 | http://localhost:3001 |

### Migration Timeline

| Phase       | Target  | Description                          |
| ----------- | ------- | ------------------------------------ |
| **Phase 1** | Q2 2025 | Docker local development (done ✅)   |
| **Phase 2** | Q3 2025 | Docker staging environment           |
| **Phase 3** | Q4 2025 | Docker production with orchestration |

### CI/CD with Docker

When Docker deployment is active, the CI/CD pipeline will:

1. **Build**: Create Docker image on push to `dev`
2. **Test**: Run tests inside container
3. **Push**: Upload image to container registry (GitHub Container
   Registry)
4. **Deploy**: Pull and restart containers on VPS

```yaml
# Future .github/workflows/docker-deploy.yml
- name: Build and push Docker image
  uses: docker/build-push-action@v5
  with:
    context: ./apps/backend
    push: true
    tags: ghcr.io/myhibachi/backend:${{ github.sha }}
```

### Environment Configuration for Docker

Use `.env.vps.example` as template for Docker environment:

```bash
# Copy template
cp .env.vps.example .env.docker

# Modify for Docker networking
# Change DATABASE_URL host from localhost to postgres
# Change REDIS_URL host from localhost to redis
```

---

## Next Actions

### Immediate (Today)

1. **Review workflow files** (already created ✅)
   - `.github/workflows/frontend-quality-check.yml`
   - `.github/workflows/backend-cicd.yml`

2. **Review setup guide**
   - `PLESK_DEPLOYMENT_SETUP_GUIDE.md`

3. **Plan deployment timeline**
   - Schedule 2 hours for VPS setup
   - Choose VPS provider
   - Purchase domain (if not done)

### This Week

1. **Frontend**:
   - [ ] Connect GitHub repo to Vercel
   - [ ] Configure build settings
   - [ ] Test deployment
   - [ ] Set up environment variables

2. **Backend**:
   - [ ] Set up VPS with Plesk
   - [ ] Configure database
   - [ ] Complete initial manual deployment
   - [ ] Add GitHub secrets for CI/CD
   - [ ] Test automated deployment

3. **Monitoring**:
   - [ ] Set up UptimeRobot
   - [ ] Configure backup automation
   - [ ] Test rollback procedure

---

**CI/CD Strategy Document** **Version**: 1.0 **Date**: October 30,
2025 **Status**: Ready for Implementation 🚀
