# ✅ Environment Variables Setup Checklist

**Project:** MyHibachi Full-Stack Application  
**Purpose:** Track which environment variables are configured  
**Date:** October 26, 2025

---

## 📋 Progress Overview

| Category                   | Variables | Status         |
| -------------------------- | --------- | -------------- |
| 🔴 Critical (Required)     | 11        | ⬜ Not Started |
| 🟡 Payments                | 4         | ⬜ Not Started |
| 🟡 AI Features             | 2         | ⬜ Not Started |
| 🟡 Email                   | 6         | ⬜ Not Started |
| 🟡 Images                  | 3         | ⬜ Not Started |
| 🟢 SMS (Optional)          | 5         | ⬜ Not Started |
| 🟢 Analytics (Optional)    | 2         | ⬜ Not Started |
| 🟢 Social Media (Optional) | 8         | ⬜ Not Started |

**Total:** 41 key variables (out of 84 possible)

---

## 🔴 CRITICAL - Required to Run (11 vars)

### Backend Core (6)

- [ ] `DATABASE_URL` - Database connection string
- [ ] `REDIS_URL` - Redis connection for caching
- [ ] `SECRET_KEY` - JWT signing key (32+ chars)
- [ ] `ENCRYPTION_KEY` - Data encryption key (32+ chars)
- [ ] `ENVIRONMENT` - development/staging/production
- [ ] `CORS_ORIGINS` - Allowed frontend origins

### Customer Frontend (2)

- [ ] `NEXT_PUBLIC_API_URL` - Backend API endpoint
- [ ] `NEXT_PUBLIC_APP_URL` - Customer app URL

### Admin Frontend (2)

- [ ] `NEXT_PUBLIC_API_URL` - Backend API endpoint
- [ ] `NEXT_PUBLIC_AI_API_URL` - AI API endpoint

### Testing

```bash
# Test backend config
cd apps/backend
python -c "from core.config import get_settings; settings = get_settings(); print('✅ Core config valid!')"

# Start system
npm run dev:all  # Should start without errors
```

**Status:** ⬜ Not Configured | ✅ Configured | 🧪 Tested

---

## 🟡 PAYMENTS - Stripe Integration (4 vars)

### Backend (3)

- [ ] `STRIPE_SECRET_KEY` - Server-side secret (sk*test* or sk*live*)
- [ ] `STRIPE_PUBLISHABLE_KEY` - Client-side key (pk*test* or
      pk*live*)
- [ ] `STRIPE_WEBHOOK_SECRET` - Webhook signing secret (whsec\_)

### Customer Frontend (1)

- [ ] `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` - Payment form key

### Get Keys From:

🔗 https://dashboard.stripe.com/test/apikeys

### Testing

```bash
# Test Stripe connection
curl http://localhost:8000/api/stripe/config
# Expected: {"publishableKey": "pk_test_..."}

# Test payment flow
# 1. Go to http://localhost:3000/BookUs
# 2. Use test card: 4242 4242 4242 4242
# 3. Any future date, any CVC
```

**Status:** ⬜ Not Configured | ✅ Configured | 🧪 Tested

---

## 🟡 AI FEATURES - OpenAI Integration (2 vars)

### Backend (2)

- [ ] `OPENAI_API_KEY` - OpenAI API key (sk-...)
- [ ] `OPENAI_MODEL` - Model to use (gpt-4, gpt-3.5-turbo)

### Get Key From:

🔗 https://platform.openai.com/api-keys

### Cost Estimate:

- GPT-3.5-Turbo: ~$0.002 per 1K tokens (~500 words)
- GPT-4: ~$0.03 per 1K tokens

### Testing

```bash
# Test AI endpoint
curl -X POST http://localhost:8000/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, what menu items do you have?"}'
# Expected: AI response with menu recommendations
```

**Status:** ⬜ Not Configured | ✅ Configured | 🧪 Tested

---

## 🟡 EMAIL - SMTP Integration (6 vars)

### Backend (6)

- [ ] `EMAIL_ENABLED` - Set to True
- [ ] `SMTP_HOST` - SMTP server (smtp.gmail.com, smtp.ionos.com)
- [ ] `SMTP_PORT` - Port number (587 for TLS)
- [ ] `SMTP_USER` - Email address
- [ ] `SMTP_PASSWORD` - App-specific password
- [ ] `FROM_EMAIL` - Sender email address

### Setup Gmail SMTP:

1. Enable 2-Step Verification: https://myaccount.google.com/security
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use app password in `SMTP_PASSWORD`

### Testing

```bash
# Test email sending
curl -X POST http://localhost:8000/api/test/send-email \
  -H "Content-Type: application/json" \
  -d '{"to": "your-email@example.com", "subject": "Test", "body": "Test email"}'
# Check your inbox
```

**Status:** ⬜ Not Configured | ✅ Configured | 🧪 Tested

---

## 🟡 IMAGE UPLOADS - Cloudinary (3 vars)

### Backend (3)

- [ ] `CLOUDINARY_CLOUD_NAME` - Your cloud name
- [ ] `CLOUDINARY_API_KEY` - API key
- [ ] `CLOUDINARY_API_SECRET` - API secret

### Get Credentials From:

🔗 https://cloudinary.com/console

### Free Tier:

- 25GB storage
- 25GB bandwidth/month
- 25,000 transformations/month

### Testing

```bash
# Test image upload endpoint
curl http://localhost:8000/api/cloudinary/config
# Expected: {"cloudName": "your-cloud-name"}

# Test upload (with actual image)
curl -X POST http://localhost:8000/api/customer-reviews/upload-image \
  -F "file=@test-image.jpg"
# Expected: {"url": "https://res.cloudinary.com/..."}
```

**Status:** ⬜ Not Configured | ✅ Configured | 🧪 Tested

---

## 🟢 SMS - RingCentral (5 vars) - OPTIONAL

### Backend (5)

- [ ] `RC_CLIENT_ID` - RingCentral client ID
- [ ] `RC_CLIENT_SECRET` - RingCentral client secret
- [ ] `RC_JWT_TOKEN` - JWT token for auth
- [ ] `RC_WEBHOOK_SECRET` - Webhook verification
- [ ] `RC_SMS_FROM` - Phone number to send from

### Get Credentials From:

🔗 https://developers.ringcentral.com/

### Cost:

- Sandbox: Free (limited)
- Production: ~$20-30/month + SMS costs

### Testing

```bash
# Test SMS sending
curl -X POST http://localhost:8000/api/sms/send \
  -H "Content-Type: application/json" \
  -d '{"to": "+19167408768", "message": "Test SMS from MyHibachi"}'
# Check phone for SMS
```

**Status:** ⬜ Not Configured | ⬜ Skipped | ✅ Configured | 🧪 Tested

---

## 🟢 ANALYTICS - Tracking (2 vars) - OPTIONAL

### Customer Frontend (1)

- [ ] `NEXT_PUBLIC_GA_MEASUREMENT_ID` - Google Analytics ID
      (G-XXXXXXXXXX)

### Backend (1)

- [ ] `SENTRY_DSN` - Sentry error tracking DSN

### Get Keys From:

- Google Analytics: https://analytics.google.com/
- Sentry: https://sentry.io/signup/

### Free Tiers:

- Google Analytics: Unlimited (free)
- Sentry: 5,000 errors/month (free)

### Testing

```bash
# GA - Check in browser console
# Open http://localhost:3000
# Look for gtag() calls in Network tab

# Sentry - Trigger test error
curl http://localhost:8000/api/test/error
# Check Sentry dashboard for error report
```

**Status:** ⬜ Not Configured | ⬜ Skipped | ✅ Configured | 🧪 Tested

---

## 🟢 SOCIAL MEDIA - Meta Integration (8 vars) - OPTIONAL

### Backend (8)

- [ ] `META_APP_ID` - Facebook app ID
- [ ] `META_APP_SECRET` - Facebook app secret
- [ ] `META_VERIFY_TOKEN` - Webhook verification token
- [ ] `META_PAGE_ACCESS_TOKEN` - Page access token
- [ ] `GOOGLE_CLOUD_PROJECT` - GCP project ID
- [ ] `GOOGLE_CREDENTIALS_JSON` - Service account JSON path
- [ ] `GBP_ACCOUNT_ID` - Google Business Profile account ID
- [ ] `GBP_LOCATION_ID` - Google Business Profile location ID

### Get Credentials From:

- Meta: https://developers.facebook.com/apps/
- Google: https://console.cloud.google.com/

### Testing

```bash
# Test Meta integration
curl http://localhost:8000/api/meta/page-info
# Expected: Facebook page information

# Test Google Business Profile
curl http://localhost:8000/api/google/business-info
# Expected: Business profile data
```

**Status:** ⬜ Not Configured | ⬜ Skipped | ✅ Configured | 🧪 Tested

---

## 🚀 Production Readiness Checklist

### Security

- [ ] `SECRET_KEY` changed to 64+ random characters
- [ ] `ENCRYPTION_KEY` changed to 64+ random characters
- [ ] `DEBUG=False` in production
- [ ] `ENVIRONMENT=production` set
- [ ] Using `sk_live_` Stripe keys (not `sk_test_`)
- [ ] CORS restricted to production domains only
- [ ] HTTPS enabled for all URLs
- [ ] Strong database password set

### Performance

- [ ] Using PostgreSQL (not SQLite)
- [ ] Redis configured for production
- [ ] `DB_POOL_SIZE` set appropriately (10-20)
- [ ] Rate limiting enabled
- [ ] CDN configured for static assets

### Monitoring

- [ ] Sentry DSN configured
- [ ] Google Analytics set up
- [ ] Email notifications working
- [ ] Health check endpoint accessible
- [ ] Log aggregation configured

### Business

- [ ] Stripe account verified
- [ ] Webhooks configured with production URL
- [ ] Email domain authenticated (SPF/DKIM)
- [ ] Business phone number verified
- [ ] Review URLs updated (Yelp, Google)

---

## 📊 Configuration Status

### By Environment

#### Development

```
Critical:    [___________] 0/11
Payments:    [___________] 0/4
AI:          [___________] 0/2
Email:       [___________] 0/6
Images:      [___________] 0/3
SMS:         [___________] 0/5 (optional)
Analytics:   [___________] 0/2 (optional)
Social:      [___________] 0/8 (optional)
```

#### Production

```
Critical:    [___________] 0/11
Payments:    [___________] 0/4
AI:          [___________] 0/2
Email:       [___________] 0/6
Images:      [___________] 0/3
SMS:         [___________] 0/5 (optional)
Analytics:   [___________] 0/2 (optional)
Social:      [___________] 0/8 (optional)
```

---

## 🎯 Completion Targets

### Minimum Viable (20%)

- [ ] 11 Critical variables
- **System runs locally without external services**

### Core Features (50%)

- [ ] 11 Critical + 4 Payments + 2 AI + 6 Email + 3 Images = 26 vars
- **Full booking system with payments, AI chat, and notifications**

### Full Features (80%)

- [ ] Add SMS (5 vars) and Analytics (2 vars) = 33 vars
- **Complete customer experience with SMS and tracking**

### Enterprise (100%)

- [ ] All 41 key variables configured
- **Full-featured system with social media integration**

---

## 📝 Notes Section

### Services Account Information

```
Stripe Account: _______________________
OpenAI Account: _______________________
Cloudinary Account: ___________________
Gmail SMTP: ___________________________
RingCentral: __________________________
Sentry: _______________________________
Google Analytics: _____________________
```

### Important Links

- Stripe Dashboard: https://dashboard.stripe.com/
- OpenAI Platform: https://platform.openai.com/
- Cloudinary Console: https://cloudinary.com/console
- RingCentral Developers: https://developers.ringcentral.com/
- Sentry Dashboard: https://sentry.io/
- Google Analytics: https://analytics.google.com/

### Database Connection Strings

```
Local Dev:  _______________________________________
Staging:    _______________________________________
Production: _______________________________________
```

---

## 🆘 Need Help?

| Issue                      | Solution                                                            |
| -------------------------- | ------------------------------------------------------------------- |
| Can't generate secure keys | Run: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| Stripe keys not working    | Verify format: `sk_test_` or `sk_live_` prefix                      |
| Database won't connect     | Check format: `postgresql+asyncpg://...`                            |
| Email not sending          | Use Gmail app password, not account password                        |
| Build fails                | Run: `npm run build` to see specific missing vars                   |

**Full Documentation:**

- [COMPLETE_ENVIRONMENT_VARIABLES_GUIDE.md](./COMPLETE_ENVIRONMENT_VARIABLES_GUIDE.md)
- [ENV_VARS_QUICK_REFERENCE.md](./ENV_VARS_QUICK_REFERENCE.md)
- [LOCAL_DEVELOPMENT_SETUP.md](./LOCAL_DEVELOPMENT_SETUP.md)

---

**Last Updated:** October 26, 2025  
**Next Review:** Before Production Deployment
