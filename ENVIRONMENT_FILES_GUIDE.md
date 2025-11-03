# Environment Files Management Guide

## 📋 Overview

This guide documents the consolidated environment file structure for the My Hibachi Chef CRM monorepo. We've streamlined from **14 files to 8 files** by removing duplicates and organizing by purpose.

---

## 🗂️ Current Structure (8 Files)

### Backend (3 files)
```
apps/backend/
├── .env                # ✅ Active development secrets (gitignored)
├── .env.example        # ✅ Template for developers (committed to git)
└── .env.test           # ✅ Testing environment (gitignored)
```

### Customer Frontend (2 files)
```
apps/customer/
├── .env.local          # ✅ Active development secrets (gitignored)
└── .env.example        # ✅ Template for developers (committed to git)
```

### Admin Frontend (2 files)
```
apps/admin/
├── .env.local          # ✅ Active development secrets (gitignored)
└── .env.example        # ✅ Template for developers (committed to git)
```

### Docker (1 file)
```
root/
└── .env.docker         # ✅ Docker Compose development (gitignored)
```

---

## 🔑 File Purposes

### Backend Files

**`.env` (Active Development)**
- **Purpose:** Contains real API keys and credentials for local development
- **Git Status:** ❌ Gitignored
- **Usage:** Automatically loaded by Python's `python-dotenv`
- **Example Keys:**
  ```bash
  DATABASE_URL=postgresql://postgres:password@localhost:5432/myhibachi_dev
  OPENAI_API_KEY=sk-proj-your-real-key
  STRIPE_SECRET_KEY=sk_test_your-real-key
  SECRET_KEY=your-secret-key-for-jwt
  ```

**`.env.example` (Developer Template)**
- **Purpose:** Template showing all required variables without real secrets
- **Git Status:** ✅ Committed to repository
- **Usage:** Copy to `.env` and fill in your own values
- **Example Keys:**
  ```bash
  DATABASE_URL=postgresql://postgres:your_password@localhost:5432/myhibachi_dev
  OPENAI_API_KEY=sk-proj-your-openai-key-here
  STRIPE_SECRET_KEY=sk_test_your-stripe-test-key
  SECRET_KEY=your-secret-key-replace-in-production
  ```

**`.env.test` (Testing)**
- **Purpose:** Configuration for running tests (separate test database, mock keys)
- **Git Status:** ❌ Gitignored
- **Usage:** Loaded during test execution
- **Example Keys:**
  ```bash
  DATABASE_URL=postgresql://postgres:password@localhost:5432/myhibachi_test
  ENVIRONMENT=test
  DEBUG=true
  ```

### Frontend Files

**`.env.local` (Active Development)**
- **Purpose:** Contains API keys for local Next.js development
- **Git Status:** ❌ Gitignored
- **Usage:** Automatically loaded by Next.js (no import needed)
- **Example Keys (Customer):**
  ```bash
  NEXT_PUBLIC_API_URL=http://localhost:8000
  NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=AIzaSyYourRealKey
  NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your-real-key
  ```
- **Example Keys (Admin):**
  ```bash
  NEXT_PUBLIC_API_URL=http://localhost:8000
  NEXT_PUBLIC_APP_ENV=development
  ```

**`.env.example` (Developer Template)**
- **Purpose:** Template for developers setting up the project
- **Git Status:** ✅ Committed to repository
- **Usage:** Copy to `.env.local` and fill in your own values
- **Example Keys:**
  ```bash
  NEXT_PUBLIC_API_URL=http://localhost:8000
  NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your-google-maps-api-key
  NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your-stripe-key
  ```

### Docker Files

**`.env.docker` (Docker Compose Development)**
- **Purpose:** Environment variables for Docker Compose local development
- **Git Status:** ❌ Gitignored
- **Usage:** Used by `docker-compose.yml` via `env_file: .env.docker`
- **Example Keys:**
  ```bash
  ENVIRONMENT=development
  DB_PASSWORD=myhibachi_dev_123
  SECRET_KEY=dev_secret_key_replace_in_production
  GRAFANA_PASSWORD=grafana_dev_123
  POSTGRES_PASSWORD=myhibachi_dev_123
  ```

---

## 🗑️ Deleted Files (Why They Were Removed)

### ❌ Root `/.env`
**Why Deleted:** 
- Conflicted with app-specific `.env` files
- Contained real secrets that should be in `apps/backend/.env`
- Python's `load_dotenv()` searches parent directories, causing confusion

### ❌ `config/environments/.env.development.template`
**Why Deleted:**
- Complete duplicate of `apps/backend/.env.example`
- No code referenced `config/environments/` directory
- Added unnecessary complexity

### ❌ `config/environments/.env.production.template`
**Why Deleted:**
- Complete duplicate of `apps/backend/.env.example`
- Production environments use deployment-specific secrets (Railway, Vercel, etc.)
- Not used in any active code

### ❌ `apps/customer/.env.local.example`
**Why Deleted:**
- Duplicate of `apps/customer/.env.example`
- Having both caused confusion about which to use
- Standard Next.js convention is `.env.example`

### ❌ `apps/customer/.env.production.example`
**Why Deleted:**
- Production deployments (Vercel) use their own environment variable management
- Not used in deployment scripts
- `.env.example` covers all needed variables

### ❌ Root `/.env.production.template`
**Why Deleted:**
- Only used for Docker production builds
- GitHub Actions uses secrets directly, doesn't need this file
- Can be regenerated if Docker production deployment is needed

---

## 🔄 How Environment Loading Works

### Backend (Python/FastAPI)

**Development:**
```python
from dotenv import load_dotenv
load_dotenv()  # Auto-finds apps/backend/.env
```
- Python searches for `.env` in:
  1. Current directory (`apps/backend/`)
  2. Parent directories (stops at workspace root)
- Uses first `.env` file found

**Testing:**
```python
from dotenv import load_dotenv
load_dotenv(".env.test")  # Explicit test environment
```

### Frontend (Next.js/React)

**Development:**
- Next.js **automatically** loads `.env.local` (no import needed)
- Variables must start with `NEXT_PUBLIC_` to be available in browser
- Loading order:
  1. `.env.local` (highest priority, gitignored)
  2. `.env` (not used in our setup)
  3. `.env.production` (production builds)

**Production (Vercel):**
- Environment variables set in Vercel dashboard
- No `.env` files deployed

### Docker Compose

**Development:**
```yaml
services:
  backend:
    env_file: .env.docker
```
- `docker-compose.yml` explicitly references `.env.docker`
- Used for all containerized services (database, backend, grafana, etc.)

---

## 📚 Best Practices

### ✅ DO

1. **Keep secrets out of git:**
   ```bash
   # Always gitignore these
   .env
   .env.local
   .env.test
   .env.docker
   ```

2. **Use templates for sharing:**
   - Commit `.env.example` files to repository
   - Document all required variables
   - Use placeholder values (never real secrets)

3. **Name consistently:**
   - Backend: `.env`, `.env.example`, `.env.test`
   - Frontend: `.env.local`, `.env.example`
   - Docker: `.env.docker`

4. **Document variable purposes:**
   ```bash
   # Required: OpenAI API key for AI features
   OPENAI_API_KEY=sk-proj-your-key-here
   
   # Optional: Redis URL (defaults to localhost:6379)
   REDIS_URL=redis://localhost:6379
   ```

### ❌ DON'T

1. **Don't commit real secrets:**
   - Never commit files with real API keys
   - Use templates with placeholders instead

2. **Don't create duplicate templates:**
   - One `.env.example` per app is enough
   - Don't create `.env.local.example`, `.env.development.example`, etc.

3. **Don't hardcode file paths:**
   ```python
   # ❌ Bad
   load_dotenv("/absolute/path/to/.env")
   
   # ✅ Good
   load_dotenv()  # Auto-finds file
   ```

4. **Don't mix app configurations:**
   - Backend secrets in `apps/backend/.env`
   - Customer frontend in `apps/customer/.env.local`
   - Admin frontend in `apps/admin/.env.local`
   - Don't create a shared root `.env`

---

## 🚀 Setup Instructions

### For New Developers

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd "MH webapps"
   ```

2. **Setup backend environment:**
   ```bash
   cd apps/backend
   cp .env.example .env
   # Edit .env and add your real API keys
   ```

3. **Setup customer frontend:**
   ```bash
   cd apps/customer
   cp .env.example .env.local
   # Edit .env.local and add your real API keys
   ```

4. **Setup admin frontend:**
   ```bash
   cd apps/admin
   cp .env.example .env.local
   # Edit .env.local and add your real API keys
   ```

5. **Setup Docker (optional):**
   ```bash
   cd ../..  # Back to root
   cp .env.docker.example .env.docker  # If example exists
   # Or create .env.docker with Docker-specific configs
   ```

### For Deployment

**Vercel (Frontend):**
- Add environment variables in Vercel dashboard
- Don't commit `.env.production`

**Railway/Render (Backend):**
- Add environment variables in platform dashboard
- Don't commit production secrets

**Docker Production:**
- Use GitHub Secrets or platform-specific secrets management
- Generate `.env` files during CI/CD pipeline

---

## 🔍 Troubleshooting

### Issue: "Environment variables not loading"

**Backend:**
```bash
# Check if .env exists
ls apps/backend/.env

# Test loading
cd apps/backend
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('DATABASE_URL'))"
```

**Frontend:**
```bash
# Check if .env.local exists
ls apps/customer/.env.local

# Restart dev server (Next.js loads env on startup)
npm run dev
```

### Issue: "Wrong environment being loaded"

**Check file precedence:**
```bash
# Backend: Python searches from current dir upward
cd apps/backend
ls .env  # This should be the only .env in path

# Frontend: Next.js loads in order
ls .env.local           # Highest priority
ls .env.development     # Second (not used in our setup)
ls .env                 # Third (not used in our setup)
```

### Issue: "Variables available in server but not browser"

**Next.js browser variables must have `NEXT_PUBLIC_` prefix:**
```bash
# ✅ Available in browser
NEXT_PUBLIC_API_URL=http://localhost:8000

# ❌ Only available on server
API_SECRET_KEY=secret123
```

---

## 📖 Related Documentation

- [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) - API endpoints and authentication
- [DATABASE_SETUP_GUIDE.md](./DATABASE_SETUP_GUIDE.md) - Database configuration
- [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md) - Production deployment steps
- [EMAIL_SERVICE_SETUP_GUIDE.md](./EMAIL_SERVICE_SETUP_GUIDE.md) - Email provider setup
- [COMPLETE_ENVIRONMENT_VARIABLES_GUIDE.md](./COMPLETE_ENVIRONMENT_VARIABLES_GUIDE.md) - Detailed variable descriptions

---

## 📝 Change Log

### 2025-01-XX - Environment Consolidation
- Reduced from 14 files to 8 files
- Removed duplicate templates
- Deleted root `.env` (moved to app-specific)
- Removed `config/environments/` folder
- Standardized naming conventions
- Updated all documentation

---

## ✅ Validation Checklist

After consolidation, verify:

- [ ] Backend loads environment: `cd apps/backend && python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('✅ Loaded' if os.getenv('DATABASE_URL') else '❌ Failed')"`
- [ ] Customer frontend loads: `cd apps/customer && npm run dev` (check for API_URL in console)
- [ ] Admin frontend loads: `cd apps/admin && npm run dev`
- [ ] Docker Compose works: `docker-compose up -d`
- [ ] No files committed to git: `git status` (should not show `.env` files except `.example`)
- [ ] Templates documented: All `.env.example` files have comments
- [ ] Old references removed: No code references `config/environments/`

---

**Last Updated:** 2025-01-XX  
**Maintained By:** Development Team  
**Status:** ✅ Active
