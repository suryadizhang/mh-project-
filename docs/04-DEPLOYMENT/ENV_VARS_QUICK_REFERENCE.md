# 🔐 Environment Variables - Quick Reference

**For complete details, see:** [COMPLETE_ENVIRONMENT_VARIABLES_GUIDE.md](./COMPLETE_ENVIRONMENT_VARIABLES_GUIDE.md)

---

## ⚡ Minimum Setup (5 minutes)

### Backend (`apps/backend/.env`)
```bash
DATABASE_URL=sqlite+aiosqlite:///./test_myhibachi.db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=dev-secret-key-at-least-32-characters-long-for-security
ENCRYPTION_KEY=dev-encryption-key-at-least-32-characters-long
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

### Customer Frontend (`apps/customer/.env.local`)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### Admin Frontend (`apps/admin/.env.local`)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_AI_API_URL=http://localhost:8002
```

**Result:** System runs locally (no payments, AI, or email).

---

## 💰 Add Payments (3 minutes)

### Backend
```bash
STRIPE_SECRET_KEY=sk_test_YOUR_KEY_HERE
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_YOUR_SECRET_HERE
```

### Customer Frontend
```bash
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_KEY_HERE
```

**Get keys:** https://dashboard.stripe.com/test/apikeys

---

## 🤖 Add AI Features (2 minutes)

### Backend
```bash
OPENAI_API_KEY=sk-YOUR_OPENAI_KEY_HERE
OPENAI_MODEL=gpt-4
```

**Get key:** https://platform.openai.com/api-keys

---

## 📧 Add Email Notifications (3 minutes)

### Backend
```bash
EMAIL_ENABLED=True
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-gmail@gmail.com
SMTP_PASSWORD=your-app-specific-password
FROM_EMAIL=your-gmail@gmail.com
```

**Setup Gmail App Password:**
1. Enable 2-Step Verification
2. Generate App Password at https://myaccount.google.com/apppasswords

---

## 🖼️ Add Image Uploads (2 minutes)

### Backend
```bash
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

**Get credentials:** https://cloudinary.com/console

---

## 🚀 Production Checklist

### 🔴 CRITICAL Security Changes

```bash
# Backend
SECRET_KEY=<64-random-characters>  # Generate with: openssl rand -hex 32
ENCRYPTION_KEY=<64-random-characters>
DEBUG=False
ENVIRONMENT=production
CORS_ORIGINS=https://myhibachichef.com,https://admin.mysticdatanode.net

# Stripe - Use LIVE keys
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...

# Database - Use PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/myhibachi
```

### 🟡 Recommended Additions

```bash
# Error Tracking
SENTRY_DSN=https://your-dsn@sentry.io/project-id

# Analytics
NEXT_PUBLIC_GA_MEASUREMENT_ID=G-XXXXXXXXXX
```

---

## 📊 Variable Count Summary

| Component | Total Vars | Required | Optional |
|-----------|-----------|----------|----------|
| **Backend** | 49 | 6 | 43 |
| **Customer Frontend** | 13 | 2 | 11 |
| **Admin Frontend** | 10 | 2 | 8 |
| **AI API** | 12 | 1 | 11 |
| **TOTAL** | **84** | **11** | **73** |

---

## 🎯 By Feature

### Core System (6 vars) - REQUIRED
- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`
- `ENCRYPTION_KEY`
- `NEXT_PUBLIC_API_URL` (both frontends)

### Payments (4 vars) - IMPORTANT
- `STRIPE_SECRET_KEY`
- `STRIPE_PUBLISHABLE_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`

### AI Features (2 vars) - IMPORTANT
- `OPENAI_API_KEY`
- `OPENAI_MODEL`

### Email (6 vars) - IMPORTANT
- `EMAIL_ENABLED`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `FROM_EMAIL`

### Images (3 vars) - IMPORTANT
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`

### SMS (5 vars) - OPTIONAL
- `RC_CLIENT_ID`
- `RC_CLIENT_SECRET`
- `RC_JWT_TOKEN`
- `RC_WEBHOOK_SECRET`
- `RC_SMS_FROM`

### Analytics (2 vars) - OPTIONAL
- `NEXT_PUBLIC_GA_MEASUREMENT_ID`
- `SENTRY_DSN`

---

## 🔑 Where to Get Keys

| Service | URL | Free Tier? |
|---------|-----|------------|
| **Stripe** | https://dashboard.stripe.com/register | ✅ Yes |
| **OpenAI** | https://platform.openai.com/signup | ⚠️ Paid ($5+ credit) |
| **Cloudinary** | https://cloudinary.com/users/register/free | ✅ Yes (25GB) |
| **Gmail SMTP** | https://myaccount.google.com/apppasswords | ✅ Yes |
| **RingCentral** | https://developers.ringcentral.com/ | ⚠️ Paid (after sandbox) |
| **Sentry** | https://sentry.io/signup/ | ✅ Yes (5K errors/mo) |

---

## ✅ Quick Test Commands

```bash
# Test Backend Config
cd apps/backend
python -c "from core.config import get_settings; print('✅ Valid')"

# Test Frontends Build
cd apps/customer && npm run build
cd apps/admin && npm run build

# Test API Health
curl http://localhost:8000/health

# Test Stripe Connection
curl http://localhost:8000/api/stripe/config
```

---

## 🆘 Common Issues

### "SECRET_KEY must be at least 32 characters"
```bash
# Generate secure key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### "Database connection failed"
```bash
# Check format (must include +asyncpg for async)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dbname
```

### "Stripe key invalid"
```bash
# Must start with correct prefix
sk_test_... # Test secret key
pk_test_... # Test publishable key
sk_live_... # Live secret key
pk_live_... # Live publishable key
```

---

## 📁 File Locations

```
MyHibachi/
├── apps/backend/.env                    ← 49 variables
├── apps/customer/.env.local             ← 13 variables
├── apps/admin/.env.local                ← 10 variables
└── apps/ai-api/.env (optional)          ← 12 variables
```

---

## 🎓 Next Steps

1. **Start with minimum setup** (6 variables)
2. **Add payments** for booking functionality
3. **Add AI** for chat features
4. **Add email** for customer notifications
5. **Add images** for review photos
6. **Add analytics** for tracking

---

**📚 Full Documentation:** [COMPLETE_ENVIRONMENT_VARIABLES_GUIDE.md](./COMPLETE_ENVIRONMENT_VARIABLES_GUIDE.md)

**Last Updated:** October 26, 2025
