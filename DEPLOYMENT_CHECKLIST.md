# 🚀 Quick Deployment Checklist

**My Hibachi CRM - Production Deployment**  
**Date:** October 27, 2025  
**Status:** ✅ Ready for Deployment

---

## ✅ Pre-Deployment Status

### API Integrations: 8/8 PASSING ✅
- ✅ Google Maps API - Travel fee calculator working
- ✅ RingCentral API - SMS/Voice with JWT authentication
- ✅ OpenAI API - AI chatbot ready
- ✅ Stripe API - Payments configured
- ✅ Plaid API - Bank connections ready
- ✅ Meta API - Facebook/Instagram connected
- ✅ Cloudinary API - Image/video uploads ready
- ✅ Environment Variables - All configured

### Backend Server
- ✅ FastAPI application tested
- ✅ All dependencies installed
- ✅ Database schema ready
- ✅ API endpoints verified

---

## 🔧 Deployment Steps

### 1. Deploy Backend
```bash
# Choose your deployment platform:
# - Railway.app
# - Render.com  
# - DigitalOcean
# - AWS/GCP/Azure
# - Vercel (with Python runtime)

# Set environment variables (copy from .env)
# Start backend server
```

### 2. Deploy Frontend
```bash
cd apps/customer
npm run build
# Deploy to Vercel/Netlify/CloudFlare Pages
```

### 3. Configure Webhooks (AFTER deployment)
See: `WEBHOOK_CONFIGURATION_PRODUCTION.md`

**Required webhooks:**
- [ ] Stripe payment webhooks
- [ ] Meta (Facebook/Instagram) message webhooks  
- [ ] RingCentral SMS webhooks (optional)

**Get your production URLs first:**
- Backend: `https://api.yourdomain.com`
- Frontend: `https://yourdomain.com`

---

## 📋 Environment Variables for Production

Copy these to your production environment:

### Critical (Required)
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Backend URL
BACKEND_URL=https://api.yourdomain.com
FRONTEND_URL=https://yourdomain.com

# JWT Secret (generate new for production!)
JWT_SECRET=your-super-secret-key-here

# Stripe (PRODUCTION keys!)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_... (get after webhook setup)

# Email (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### API Integrations (Copy from .env)
```bash
# Google Maps
GOOGLE_MAPS_API_KEY=AIzaSyCx...Ivhs
GOOGLE_CLOUD_PROJECT=my-hibachi-crm
GOOGLE_CLIENT_ID=28565005233-...
GOOGLE_CLIENT_SECRET=GOCSPX-...bayC

# RingCentral
RC_CLIENT_ID=3ADYc6Nv8qxeddtHygnfIK
RC_CLIENT_SECRET=V665HVqP...54Cy
RC_JWT_TOKEN=your-jwt-token
RC_USERNAME=suryadizhang.chef@gmail.com
RC_EXTENSION=101
RC_SMS_FROM=+19167408768

# OpenAI
OPENAI_API_KEY=sk-svcac...eCoA
OPENAI_MODEL=gpt-4

# Plaid
PLAID_CLIENT_ID=68ffbe986a1a5500222404db
PLAID_SECRET=5216f623...e24c
PLAID_ENV=production  # Change from 'sandbox'!

# Meta (Facebook/Instagram)
META_APP_ID=1839409339973429
META_APP_SECRET=f128b977...acc3
META_PAGE_ACCESS_TOKEN=EAAaI7tx...s8ZD
META_VERIFY_TOKEN=myhibachi-meta-webhook-verify-token-2025
META_PAGE_ID=664861203383602
META_INSTAGRAM_ID=17841475429729945

# Cloudinary
CLOUDINARY_CLOUD_NAME=dlubugier
CLOUDINARY_API_KEY=65291356...7941
CLOUDINARY_API_SECRET=XWmGc5BZ...oKRg

# Business Info
BUSINESS_ADDRESS=47481 Towhee Street, Fremont, CA 94539
BUSINESS_LATITUDE=37.4863
BUSINESS_LONGITUDE=-121.9342
TRAVEL_FREE_DISTANCE_MILES=30
TRAVEL_FEE_PER_MILE_CENTS=200
```

---

## ⚠️ Important Changes for Production

### 1. Use Production API Keys
- [ ] Stripe: Switch from `sk_test_...` to `sk_live_...`
- [ ] Plaid: Change `PLAID_ENV` from `sandbox` to `production`
- [ ] All other APIs: Already using production keys ✅

### 2. Security
- [ ] Generate new `JWT_SECRET` (don't use dev secret!)
- [ ] Enable CORS only for your domain
- [ ] Set `DEBUG=False` in production
- [ ] Use HTTPS only (no HTTP)

### 3. Database
- [ ] Run migrations: `alembic upgrade head`
- [ ] Backup database regularly
- [ ] Set up connection pooling

---

## 🧪 Post-Deployment Testing

### Test Checklist
- [ ] Homepage loads correctly
- [ ] Booking form submits successfully
- [ ] Payment processing works (test with small amount)
- [ ] SMS notifications sent correctly
- [ ] Facebook/Instagram messages trigger AI replies
- [ ] Admin dashboard accessible
- [ ] Travel fee calculator accurate
- [ ] Image uploads work (Cloudinary)

### Monitoring
- [ ] Set up error tracking (Sentry.io)
- [ ] Configure uptime monitoring (UptimeRobot)
- [ ] Set up log aggregation
- [ ] Monitor API rate limits

---

## 📞 Support & Resources

### Documentation
- API Integration Tests: `apps/backend/test_all_integrations.py`
- Webhook Configuration: `WEBHOOK_CONFIGURATION_PRODUCTION.md`
- Environment Setup: `ENV_SETUP_CHECKLIST.md`

### Quick Links
- Stripe Dashboard: https://dashboard.stripe.com
- Meta Developer Console: https://developers.facebook.com/apps/1839409339973429
- RingCentral Console: https://developers.ringcentral.com
- Cloudinary Dashboard: https://cloudinary.com/console

---

## 🎯 Next Steps After Deployment

1. **Configure webhooks** (see WEBHOOK_CONFIGURATION_PRODUCTION.md)
2. **Test all features** with real data
3. **Monitor logs** for 24-48 hours
4. **Set up backup** and disaster recovery
5. **Configure domain** and SSL certificate
6. **Enable CDN** for static assets
7. **Set up monitoring** and alerts

---

**Status:** ✅ All integrations tested and verified  
**Ready for Production:** YES  
**Last Updated:** October 27, 2025
