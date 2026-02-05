---
applyTo: '**'
---

# My Hibachi – Local-First Development Workflow

**Priority: HIGH** – Test locally before deploying to
staging/production.

---

## 🚨 AI AGENT ENFORCEMENT (READ FIRST!)

**BEFORE running ANY backend code, the AI agent MUST:**

1. **USE DOCKER, NOT DIRECT PYTHON** - Never run `python -m uvicorn`
   directly
2. **BUILD DOCKER IMAGE FIRST** -
   `docker compose --profile development build unified-backend`
3. **RUN IN DOCKER CONTAINER** -
   `docker compose --profile development up unified-backend`
4. **TEST AGAINST DOCKER** - `curl http://localhost:8000/health` (port
   8000, not 8001)

### ❌ FORBIDDEN (AI Must NEVER Do):

```bash
# WRONG - Direct Python execution bypasses Docker environment
python -m uvicorn main:app --host 0.0.0.0 --port 8001
cd apps/backend/src && python main.py
```

### ✅ REQUIRED (AI Must ALWAYS Do):

```bash
# CORRECT - Docker execution matches staging/production
docker compose --profile development build unified-backend
docker compose --profile development up unified-backend
curl http://localhost:8000/health
```

### Why Docker, Not Direct Python?

| Direct Python (WRONG)         | Docker (CORRECT)                 |
| ----------------------------- | -------------------------------- |
| Different OS (Windows)        | Same OS (Linux Alpine)           |
| Local Python packages         | Container Python packages        |
| Local env vars                | Container env vars               |
| Works locally, fails in prod  | If works locally, works in prod  |
| Port 8001 (non-standard)      | Port 8000 (matches staging/prod) |
| Missing dependencies possible | All deps in Dockerfile           |
| No isolation                  | Full isolation                   |

### AI Self-Check Before Testing:

Before testing ANY backend endpoint, ask:

- [ ] Am I using Docker? (If no → STOP, use Docker)
- [ ] Did I build the Docker image? (If no → build first)
- [ ] Is the container running? (If no → start it)
- [ ] Am I testing on port 8000? (If 8001 → WRONG, use Docker)

---

## 🎯 Purpose

This document enforces the industry-standard development workflow:
**Local → Staging → Production**. Never skip local testing.

---

## 📊 Development Workflow (MANDATORY)

```
┌─────────────────────────────────────────────────────────────┐
│          INDUSTRY-STANDARD DEVELOPMENT WORKFLOW              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. LOCAL DEVELOPMENT                                        │
│     └─ Make code changes in your workspace                  │
│                                                              │
│  2. LOCAL DOCKER BUILD                                       │
│     └─ Build containers locally (matches production env)    │
│                                                              │
│  3. LOCAL DOCKER TESTING                                     │
│     └─ Run app in Docker, test endpoints, verify behavior   │
│                                                              │
│  4. UNIT/INTEGRATION TESTS                                   │
│     └─ Run full test suite locally (must pass 100%)         │
│                                                              │
│  5. CODE QUALITY CHECKS                                      │
│     └─ black, ruff, isort, prettier, TypeScript compile     │
│                                                              │
│  6. GIT COMMIT & PUSH                                        │
│     └─ Only after local tests pass                          │
│                                                              │
│  7. STAGING DEPLOYMENT                                       │
│     └─ Deploy to staging server                             │
│                                                              │
│  8. STAGING E2E TESTS                                        │
│     └─ Run Postman collection, E2E tests on staging         │
│                                                              │
│  9. PRODUCTION DEPLOYMENT                                    │
│     └─ Only after staging validates for 48+ hours           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚫 NEVER Do This

| ❌ WRONG APPROACH                      | Why It's Bad                        |
| -------------------------------------- | ----------------------------------- |
| Make changes → Push to staging         | Skips local validation              |
| Fix issue → Deploy to staging directly | Untested code in shared environment |
| "Quick test" on staging                | Wastes staging resources            |
| Skip Docker build locally              | Misses environment-specific bugs    |
| Deploy to production without staging   | Recipe for production disasters     |

---

## ✅ Correct Process

### Step 1: Local Development

```bash
# Make code changes in your IDE
# Fix the issue, add the feature, etc.
```

### Step 2: Local Docker Build

```bash
# Backend
cd c:\Users\surya\projects\MH webapps
docker compose --profile development build unified-backend

# Frontend (if needed)
docker compose --profile development build unified-frontend
```

### Step 3: Local Docker Testing

```bash
# Start services locally
docker compose --profile development up unified-backend postgres redis

# In another terminal, test the API
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/stations -H "Authorization: Bearer <token>"

# Or use Postman against localhost:8000
```

### Step 4: Run Tests Locally

```bash
# Backend unit tests
cd apps/backend
pytest tests/ -v

# Frontend unit tests
cd apps/customer
npm test -- --run

# E2E tests (optional - against local Docker)
cd e2e
npm test
```

### Step 5: Code Quality

```bash
# Python formatting
cd apps/backend/src/routers/v1
black *.py
ruff check --fix *.py
isort *.py

# TypeScript build
cd apps/customer
npm run build
```

### Step 6: Git Commit (Only After Local Tests Pass)

```bash
git add -A
git commit -m "fix(batch-1): description"
git push origin dev
```

### Step 7: Deploy to Staging

**Only after confirming local Docker works:**

```bash
ssh root@108.175.12.154 "cd /var/www/vhosts/myhibachichef.com/mhapi.mysticdatanode.net/backend && git pull origin dev && docker compose -f docker-compose.staging.yml build staging-api && docker compose -f docker-compose.staging.yml restart staging-api"
```

### Step 8: Staging Tests

```bash
# Run Postman collection against staging
newman run MyHibachi_Batch1_Tests.postman_collection.json --environment Staging.postman_environment.json

# Run E2E tests against staging
npm run test:e2e:staging
```

### Step 9: Production Deployment

**Only after staging validates for 48+ hours:**

```bash
# Deploy to production
ssh root@108.175.12.154 "cd /var/www/vhosts/myhibachichef.com/mhapi.mysticdatanode.net/backend && git pull origin main && docker compose -f docker-compose.vps.yml build production-api && docker compose -f docker-compose.vps.yml restart production-api"
```

---

## 🐳 Local Docker Commands Reference

### Build Commands

```bash
# Build single service
docker compose --profile development build unified-backend

# Build with no cache (force rebuild)
docker compose --profile development build --no-cache unified-backend

# Build all development services
docker compose --profile development build
```

### Run Commands

```bash
# Start all development services in background
docker compose --profile development up -d

# Start specific service
docker compose --profile development up unified-backend

# View logs
docker logs myhibachi-backend -f --tail 100

# Restart service
docker compose --profile development restart unified-backend

# Stop all services
docker compose --profile development down
```

### Testing Commands

```bash
# Check health endpoint
curl http://localhost:8000/health

# Get pricing data
curl http://localhost:8000/api/v1/pricing/current

# Test authenticated endpoint
curl http://localhost:8000/api/v1/stations \
  -H "Authorization: Bearer eyJ..."

# Run Postman collection against localhost
newman run MyHibachi_Batch1_Tests.postman_collection.json \
  --environment Local.postman_environment.json
```

---

## 📋 Pre-Deployment Checklist

**Before deploying to staging, verify:**

- [ ] Code builds successfully in Docker locally
- [ ] App starts without errors in local Docker
- [ ] Health endpoint returns 200 in local Docker
- [ ] Fixed endpoint works in local Docker
- [ ] Unit tests pass locally
- [ ] Integration tests pass locally
- [ ] No console.log/print statements
- [ ] No hardcoded values or secrets
- [ ] Code formatted (black, ruff, isort, prettier)
- [ ] Git commit created with proper message

---

## 🔍 Troubleshooting Local Docker

### Common Issues

| Problem                   | Solution                                     |
| ------------------------- | -------------------------------------------- |
| Container won't start     | Check `docker logs myhibachi-backend`        |
| Port already in use       | `docker compose down` to stop old containers |
| Database connection error | Ensure postgres service is running           |
| "Module not found" error  | Rebuild with `--no-cache`                    |
| Changes not reflected     | Rebuild container, not just restart          |

### Debug Commands

```bash
# Check running containers
docker ps

# Check all containers (including stopped)
docker ps -a

# View container logs
docker logs myhibachi-backend --tail 100

# Execute command inside container
docker exec -it myhibachi-backend /bin/sh

# Check environment variables inside container
docker exec myhibachi-backend env

# Remove all stopped containers
docker compose down --volumes --remove-orphans
```

---

## � Why This Workflow Matters

| Benefit               | Explanation                                 |
| --------------------- | ------------------------------------------- |
| **Catch bugs early**  | Find issues before shared environments      |
| **Faster iterations** | No waiting for deployment to test           |
| **Save resources**    | Staging isn't a debugging environment       |
| **Match production**  | Docker local = Docker staging = Docker prod |
| **Team efficiency**   | Staging stays stable for everyone           |
| **Confidence**        | Know it works before deploying              |

---

## 🎓 Teaching Moments (For AI Agent)

**When user reports an issue:**

1. **DO NOT** immediately deploy to staging
2. **ASK:** "Can we test this fix locally first in Docker?"
3. **EXPLAIN:** "Let's validate the fix in local Docker before
   deploying to staging. This ensures it works and saves deployment
   cycles."

**Interactive Teaching Mode:**

```
User: "Fix the stations endpoint issue"

Agent Response:
"Let's fix this properly with industry-standard workflow:

STEP 1: I'll apply the code changes locally
[Apply fixes]

STEP 2: Build and test in local Docker
docker compose --profile development build unified-backend

STEP 3: Verify it works locally
curl http://localhost:8000/api/v1/stations

STEP 4: Only THEN deploy to staging if local works

✅ This ensures we don't push broken code to shared environments.

Ready to proceed?"
```

---

## 📊 Workflow Comparison

### Old Approach (DON'T DO):

```
Make change → Git push → Deploy to staging → Test on staging →
If fails → Make change → Git push → Deploy again → ...
(Wastes time, pollutes git history, staging is unstable)
```

### New Approach (DO THIS):

```
Make change → Local Docker build → Local Docker test →
If works → Git push → Deploy to staging →
If works 48h → Deploy to production
(Efficient, clean history, staging stays stable)
```

---

## 🔗 Related Files

- `docker-compose.yml` – Local Docker setup
- `Dockerfile` – Container build definition
- `07-TESTING_QA.instructions.md` – Testing standards
- `03-BRANCH_GIT_WORKFLOW.instructions.md` – Git workflow
- `16-INFRASTRUCTURE_DEPLOYMENT.instructions.md` – Deployment

---

**Golden Rule:**

> **If it doesn't work in local Docker, don't deploy it to staging.**
