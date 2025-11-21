# Quick Start - Using Existing Environment Setup

**Status**: ✅ Environment files already exist  
**Time**: 1 hour (simplified from 2 hours)

---

## ✅ What You Already Have

- `apps/customer/.env.local` ✅
- `apps/admin/.env.local` ✅
- `apps/backend/.env` ✅

**Action**: Just verify they have the correct values, no need to
create new files!

---

## 🎯 Quick Verification & Testing (1 hour)

### Step 1: Verify Environment Files (10 min)

**Check that your existing files have these keys:**

```bash
# apps/customer/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=(your test key)
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=(your test key)

# Feature flags (add these if missing)
NEXT_PUBLIC_FEATURE_AI_BOOKING_V3=true
NEXT_PUBLIC_FEATURE_SMS_CONSENT=true

# apps/admin/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000

# apps/backend/.env
DATABASE_URL=(your database URL)
STRIPE_SECRET_KEY=(your test key)
OPENAI_API_KEY=(your test key)

# Feature flags (add these if missing)
FEATURE_FLAG_AI_BOOKING_V3=true
FEATURE_FLAG_AUDIT_LOGGING=true
```

---

### Step 2: Run Database Migrations (15 min)

```bash
# Navigate to backend
cd apps/backend

# Check current migration status
alembic current

# Apply all pending migrations
alembic upgrade head

# Verify critical tables exist
python -c "from src.db.session import engine; import asyncio; asyncio.run(engine.connect())"
```

**Success**: No errors, all migrations applied ✅

---

### Step 3: Run Backend Tests (15 min)

```bash
# Still in apps/backend
pytest tests/ -v

# Or run specific critical tests
pytest tests/services/test_booking_service.py -v
pytest tests/test_race_condition_fix.py -v
```

**Success**: All tests passing ✅

---

### Step 4: Test Frontend Builds (10 min)

```bash
# Test customer build
cd apps/customer
npm run build

# Test admin build
cd ../admin
npm run build
```

**Success**: Both build without errors ✅

---

### Step 5: Quick Smoke Test (10 min)

```bash
# Start backend
cd apps/backend
python -m uvicorn src.main:app --reload &

# Test health endpoint
curl http://localhost:8000/health
# Should return: {"status": "healthy"}

# Start customer frontend
cd apps/customer
npm run dev &
# Open http://localhost:3000

# Start admin frontend
cd apps/admin
npm run dev &
# Open http://localhost:3001
```

**Success**: All services running ✅

---

## ✅ Simplified Checklist

- [ ] Verify `.env` files have required keys (10 min)
- [ ] Run `alembic upgrade head` (15 min)
- [ ] Run `pytest tests/ -v` (15 min)
- [ ] Test `npm run build` for customer & admin (10 min)
- [ ] Quick smoke test - start all services (10 min)

**Total Time**: 1 hour

---

## 🎉 After This You'll Have

- ✅ All database tables up-to-date
- ✅ All backend tests passing
- ✅ Frontend builds working
- ✅ All services running locally
- ✅ Ready to develop new features!

---

## 📝 Notes

- **No need to create new files** - use existing `.env.local` and
  `.env`
- **Test keys are fine** - we'll rotate them before production
- **Feature flags** - just add them to existing files if missing
- **If anything fails** - check `DEV_BRANCH_IMMEDIATE_ACTIONS.md` for
  detailed troubleshooting

---

**Ready to go? Start with Step 1!** 🚀
