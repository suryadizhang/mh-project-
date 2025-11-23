# 🎯 Prioritized Next Steps - What to Work On NOW

**Created:** November 23, 2025
**Based on:** COMPLETE_SKIPPED_DEVELOPMENT_ANALYSIS.md

---

## 🚨 CRITICAL DECISION NEEDED

### The Big Question

**Do we want to:**

**Option A: Ship to Production ASAP** (1 week)
- Fix failing tests
- Deploy to staging
- Get real customers using the system
- Generate revenue NOW

**Option B: Build Features First** (3 weeks)
- Customer Review System
- Loyalty Program
- Lead Scoring
- Then deploy

**Option C: Hybrid** (4 weeks - RECOMMENDED)
- Week 1: Deploy to production
- Week 2-4: Build features while live

---

## 📋 CRITICAL PATH: OPTION A (Production First)

**Goal:** Get My Hibachi live and generating revenue in 7 days

### Day 1: Security Setup (8 hours)

**Morning (4 hours):**
```bash
# 1. Rotate Stripe API Keys
# Go to: https://dashboard.stripe.com/test/apikeys
# Create new keys, update in .env files

# 2. Rotate OpenAI API Key
# Go to: https://platform.openai.com/api-keys
# Create new key, update in backend config

# 3. Rotate Google Maps API Key
# Go to: https://console.cloud.google.com/apis/credentials
# Create new key with restrictions
```

**Afternoon (4 hours):**
```bash
# 4. Set up Google Secret Manager
gcloud auth login
gcloud projects list
gcloud secrets create stripe-secret-key --data-file=-
gcloud secrets create openai-api-key --data-file=-

# 5. Configure Vercel environment variables
# Go to: https://vercel.com/my-hibachi/settings/environment-variables
# Add all production secrets

# 6. Set up database backups
# Configure automated PostgreSQL backups on VPS
# Test restore process
```

**Deliverable:** ✅ All secrets rotated, GSM configured

---

### Day 2-3: Fix Failing Tests (16 hours)

**Priority 1: Production Safety Tests (4 hours)**

```bash
cd apps/backend
pytest tests/services/test_production_safety.py -vv --tb=long

# Fix these 4 tests:
# 1. test_double_booking_prevention
# 2. test_payment_idempotency
# 3. test_race_condition_handling
# 4. test_data_integrity

# Root causes (from previous audits):
# - Missing database locks
# - No optimistic locking (version columns)
# - TOCTOU race conditions
```

**Priority 2: Integration Tests (8 hours)**

```bash
pytest tests/integration/ -vv --tb=long

# Fix these 18 tests:
# - Cache-database sync (2 tests)
# - Rate limiting (2 tests)
# - Idempotency (2 tests)
# - E2E booking flow (4 tests)
# - Payment processing (4 tests)
# - Email/SMS notifications (2 tests)
# - Metrics collection (2 tests)
```

**Priority 3: Service Tests (4 hours)**

```bash
pytest tests/services/ -vv --tb=long

# Fix remaining 7 service test failures
```

**Deliverable:** ✅ All 222 tests passing (100% pass rate)

---

### Day 4: Backend Deployment (8 hours)

**Morning (4 hours): VPS Setup**

```bash
# 1. SSH into VPS
ssh root@your-vps-ip

# 2. Create production directory
mkdir -p /var/www/myhibachi-backend
cd /var/www/myhibachi-backend

# 3. Clone repository (main branch)
git clone https://github.com/your-org/myhibachi.git .
git checkout main

# 4. Set up Python environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r apps/backend/requirements.txt

# 5. Configure environment variables
cp .env.example .env.production
# Edit with production values

# 6. Run database migrations
cd apps/backend
alembic upgrade head
```

**Afternoon (4 hours): Systemd Service**

```bash
# 7. Create systemd service
sudo nano /etc/systemd/system/myhibachi-backend.service

# Paste:
[Unit]
Description=My Hibachi FastAPI Backend
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/myhibachi-backend/apps/backend
ExecStart=/var/www/myhibachi-backend/venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target

# 8. Start service
sudo systemctl daemon-reload
sudo systemctl start myhibachi-backend
sudo systemctl enable myhibachi-backend
sudo systemctl status myhibachi-backend

# 9. Configure Nginx reverse proxy
sudo nano /etc/nginx/sites-available/myhibachi-backend

# Paste:
server {
    listen 80;
    server_name api.myhibachi.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

sudo ln -s /etc/nginx/sites-available/myhibachi-backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 10. Set up SSL with Let's Encrypt
sudo certbot --nginx -d api.myhibachi.com
```

**Deliverable:** ✅ Backend API live at https://api.myhibachi.com

---

### Day 5: Frontend Deployments (6 hours)

**Customer Site (3 hours):**

```bash
# 1. Configure Vercel project
cd apps/customer
vercel login
vercel link

# 2. Set environment variables in Vercel dashboard
NEXT_PUBLIC_API_URL=https://api.myhibachi.com
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_xxx
# ... all other variables

# 3. Deploy to production
vercel --prod

# 4. Configure custom domain
# In Vercel dashboard: Settings > Domains
# Add: www.myhibachi.com and myhibachi.com

# 5. Test production site
curl https://www.myhibachi.com
# Verify booking flow works
```

**Admin Panel (3 hours):**

```bash
# Same process for admin
cd apps/admin
vercel link
# Set environment variables
vercel --prod

# Configure domain: admin.myhibachi.com
```

**Deliverable:** ✅ Both frontends live

---

### Day 6: Monitoring & Observability (4 hours)

**Set up monitoring stack:**

```bash
# 1. Install Sentry for error tracking
pip install sentry-sdk
npm install @sentry/nextjs

# Configure in backend:
# apps/backend/src/core/config.py
SENTRY_DSN = "https://xxx@sentry.io/xxx"

# Configure in frontends:
# apps/customer/next.config.js
# apps/admin/next.config.js

# 2. Set up health checks
# Create: apps/backend/src/api/health.py
# Endpoint: GET /health
# Check: Database, Redis, external APIs

# 3. Configure uptime monitoring (UptimeRobot or similar)
# Add endpoints:
# - https://api.myhibachi.com/health
# - https://www.myhibachi.com
# - https://admin.myhibachi.com

# 4. Set up log aggregation (CloudWatch, Papertrail, or Loki)
# Configure log shipping from VPS

# 5. Create alerts
# - API response time > 2s
# - Error rate > 1%
# - Database connections > 80%
# - Disk usage > 85%
```

**Deliverable:** ✅ Full observability stack

---

### Day 7: Smoke Testing & Go-Live (4 hours)

**Morning (2 hours): Smoke Tests**

```bash
# Test critical user flows:

1. Customer Booking Flow
   - Visit www.myhibachi.com
   - Browse menu
   - Select date/time
   - Enter guest info
   - Process payment (use Stripe test mode)
   - Verify confirmation email

2. Admin Operations
   - Login to admin.myhibachi.com
   - View dashboard
   - Check upcoming bookings
   - Modify booking
   - Send notification

3. API Health
   - GET /health (should return 200)
   - GET /api/bookings (with auth)
   - POST /api/bookings (create test booking)
   - GET /api/admin/analytics

4. Payment Processing
   - Test successful payment
   - Test declined card
   - Test refund flow
   - Verify Stripe webhook handling

5. Email/SMS Notifications
   - Booking confirmation email
   - Reminder SMS (24h before)
   - Admin notification email
```

**Afternoon (2 hours): Final Checklist**

```bash
# Production Readiness Checklist:
✅ All 222 tests passing
✅ All API keys rotated
✅ Secrets in GSM
✅ Database backups configured
✅ SSL certificates valid
✅ Custom domains configured
✅ Monitoring alerts set up
✅ Error tracking enabled
✅ Health checks passing
✅ Smoke tests passed
✅ Payment processing works
✅ Email/SMS delivery works

# Go-Live:
1. Update DNS records (if needed)
2. Announce on social media
3. Send email to beta users
4. Monitor logs for first 24 hours
5. Be ready for hotfixes
```

**Deliverable:** ✅ My Hibachi is LIVE! 🎉

---

## 📋 AGGRESSIVE PATH: OPTION C (Hybrid)

**Goal:** Production in Week 1, then build features Weeks 2-4

### Week 1: Production Deployment

(Same as Option A above)

---

### Week 2: Customer Review System (14-20 hours)

**Day 8-9: Backend (8 hours)**

```bash
cd apps/backend

# 1. Create database migration
alembic revision -m "add_customer_reviews"

# Edit migration file:
# - Create customer_reviews table
# - Create review_images table
# - Add indexes

alembic upgrade head

# 2. Create models
# File: src/models/customer_review.py
class CustomerReview(Base):
    id: int
    booking_id: int
    customer_name: str
    rating: int
    comment: str
    images: List[str]
    status: str  # pending, approved, rejected
    created_at: datetime

# 3. Create image upload service
# File: src/services/image_service.py
# - Upload to S3/Cloudinary
# - Resize to thumbnails
# - Optimize for web

# 4. Create API endpoints
# File: src/api/customer_reviews/router.py
# POST /api/reviews (customer submission)
# GET /api/reviews (approved reviews)
# POST /api/admin/reviews/{id}/approve
# POST /api/admin/reviews/{id}/reject

# 5. Test with Postman
pytest tests/api/test_customer_reviews.py -vv
```

**Day 10: Admin UI (6 hours)**

```bash
cd apps/admin

# 1. Create moderation component
# File: src/components/reviews/PendingReviewsList.tsx
# - Fetch pending reviews
# - Display review cards
# - Approve/reject buttons
# - Bulk actions

# 2. Add to admin dashboard
# File: src/app/reviews/page.tsx
# - Pending reviews count badge
# - Quick moderation panel

# 3. Test admin flow
npm run dev
# Navigate to /admin/reviews
# Test approve/reject actions
```

**Day 11: Customer UI (6 hours)**

```bash
cd apps/customer

# 1. Create review page
# File: src/app/reviews/page.tsx
# - Infinite scroll
# - Filter by rating
# - Sort by date/helpful

# 2. Create review components
# File: src/components/reviews/ReviewCard.tsx
# - Display rating stars
# - Show images in gallery
# - Like/helpful button

# File: src/components/reviews/ImageGallery.tsx
# - Lightbox for full-size images
# - Swipe gestures

# 3. Add to homepage
# File: src/app/page.tsx
# - "Recent Reviews" section
# - Link to full reviews page

# 4. Test customer flow
npm run dev
# Visit /reviews
# Test image gallery
# Test infinite scroll
```

**Deliverable:** ✅ Customer Review System LIVE

---

### Week 3: Loyalty Program (20-28 hours)

**Day 12-13: Database & Backend (10 hours)**

```bash
# 1. Design points system
# - 1 booking = 100 points
# - $100 spent = 10 bonus points
# - Tier 1 (0-500 pts): 5% discount
# - Tier 2 (501-1500 pts): 10% discount
# - Tier 3 (1501+ pts): 15% discount

# 2. Create migration
alembic revision -m "add_loyalty_program"

# Tables:
# - customer_points (balance, tier, history)
# - rewards_catalog (items, costs)
# - point_transactions (earned, redeemed, expired)

# 3. Create services
# File: src/services/loyalty_service.py
# - accrue_points(booking_id, amount)
# - redeem_points(customer_id, reward_id)
# - calculate_tier(points_balance)

# 4. Create API
# File: src/api/loyalty/router.py
# GET /api/loyalty/balance
# GET /api/loyalty/rewards
# POST /api/loyalty/redeem
# GET /api/loyalty/history
```

**Day 14-15: Customer Portal (10 hours)**

```bash
cd apps/customer

# 1. Points dashboard
# File: src/app/account/loyalty/page.tsx
# - Display current balance
# - Show current tier
# - Progress to next tier

# 2. Rewards catalog
# File: src/components/loyalty/RewardsCatalog.tsx
# - Browse available rewards
# - Filter by points cost
# - Redeem button

# 3. Transaction history
# File: src/components/loyalty/PointsHistory.tsx
# - List all point transactions
# - Show earned/redeemed/expired

# 4. Integration with booking
# File: src/app/booking/checkout/page.tsx
# - Show points that will be earned
# - Option to use points for discount
```

**Day 16: Admin Management (8 hours)**

```bash
cd apps/admin

# 1. Create rewards management
# File: src/app/loyalty/rewards/page.tsx
# - Add/edit/delete rewards
# - Set point costs
# - Upload reward images

# 2. Customer loyalty dashboard
# File: src/app/customers/[id]/loyalty.tsx
# - View customer's points
# - Manually adjust points
# - View redemption history

# 3. Analytics
# File: src/app/analytics/loyalty.tsx
# - Total points issued
# - Redemption rate
# - Most popular rewards
```

**Deliverable:** ✅ Loyalty Program LIVE

---

### Week 4: Lead Scoring + Analytics + Polish (26-32 hours)

**Day 17-18: Lead Scoring (12 hours)**

```bash
# Backend already exists (8 endpoints)
# Just need admin UI:

cd apps/admin

# 1. Lead scoring dashboard
# File: src/app/leads/page.tsx
# - List all leads with scores
# - Sort by score (hot/warm/cold)
# - Filter by source

# 2. Lead detail view
# File: src/app/leads/[id]/page.tsx
# - Show scoring breakdown
# - Display activity timeline
# - Quick actions (call, email, convert)

# 3. Automated rules
# File: src/app/leads/rules/page.tsx
# - Create follow-up automation
# - Set score thresholds
# - Configure notifications
```

**Day 19-20: Analytics Completion (10 hours)**

```bash
cd apps/admin

# 1. Revenue analytics
# File: src/components/analytics/RevenueChart.tsx
# - Monthly revenue trends
# - Booking trends
# - Payment method breakdown

# 2. Customer analytics
# File: src/components/analytics/CustomerMetrics.tsx
# - Customer lifetime value
# - Retention rate
# - Acquisition sources

# 3. Real-time monitoring
# File: src/components/analytics/LiveFeed.tsx
# - Live booking notifications
# - Active sessions count
# - API health status
```

**Day 21: Smart Re-render (4-6 hours)**

```bash
cd apps/admin

# 1. Install React Query
npm install @tanstack/react-query

# 2. Configure QueryClient
# File: src/lib/queryClient.ts

# 3. Convert fetch() to useQuery
# Update all data-fetching components

# 4. Add manual refresh button
# File: src/components/layout/AdminHeader.tsx
# - Button to invalidate all queries
# - Loading state
```

**Deliverable:** ✅ Lead Scoring + Analytics + Smart Re-render LIVE

---

## 📊 TIMELINE COMPARISON

### Option A: Production First (7 days)

```
Week 1: [████████████████████] PRODUCTION LIVE ✅
Week 2: [                    ] (no features)
Week 3: [                    ] (no features)
Week 4: [                    ] (no features)

Result: ✅ Revenue generating
        ❌ Missing features
```

---

### Option B: Features First (3 weeks)

```
Week 1: [                    ] (no production)
Week 2: [████████████████████] Customer Reviews + Loyalty
Week 3: [████████████████████] Lead Scoring + Analytics
Week 4: [████████████████████] Production deployment

Result: ❌ No revenue yet
        ✅ Full featured
```

---

### Option C: Hybrid (4 weeks) ⭐ RECOMMENDED

```
Week 1: [████████████████████] PRODUCTION LIVE ✅
Week 2: [████████████████████] Customer Reviews ✅
Week 3: [████████████████████] Loyalty Program ✅
Week 4: [████████████████████] Lead Scoring + Analytics ✅

Result: ✅ Revenue generating from Week 1
        ✅ New features every week
        ✅ Continuous improvement
```

---

## 🎯 RECOMMENDED DECISION

**Choose Option C (Hybrid)** because:

1. ✅ **Revenue starts Week 1** (production live)
2. ✅ **Customer value every week** (new features)
3. ✅ **Reduces risk** (smaller deployments)
4. ✅ **Real user feedback** (guide feature development)
5. ✅ **Business momentum** (show progress to stakeholders)

**Alternative:**

If you need features immediately (e.g., loyalty program for launch campaign):
- Choose **Option B** (Features First)
- Launch with full feature set
- Make bigger splash

---

## ✅ WHAT TO DO RIGHT NOW

**Step 1: Make the decision**

```
[ ] Option A: Production in 7 days (then build features)
[ ] Option B: Features in 3 weeks (then deploy)
[✓] Option C: Hybrid - Production Week 1, Features Week 2-4 (RECOMMENDED)
```

**Step 2: Clear your calendar**

- Block 8 hours/day for next 4 weeks
- Minimize meetings
- Focus mode ON

**Step 3: Start Day 1 (Security Setup)**

```bash
# Right now, open a terminal and run:
cd apps/backend
git checkout main
git pull origin main

# Then follow Day 1 checklist above ⬆️
```

**Step 4: Track progress**

Create a Kanban board:
- Column 1: TO DO
- Column 2: IN PROGRESS
- Column 3: DONE

Move tasks as you complete them.

---

## 🏁 SUCCESS METRICS

### Week 1 Success:
- ✅ All 222 tests passing
- ✅ Production URL live (https://www.myhibachi.com)
- ✅ First real booking completed
- ✅ Payment processed successfully
- ✅ Zero critical errors in Sentry

### Week 2 Success:
- ✅ Customer Review System deployed
- ✅ First customer review submitted
- ✅ Admin can moderate reviews
- ✅ 10+ reviews approved and visible

### Week 3 Success:
- ✅ Loyalty Program live
- ✅ Points accruing for bookings
- ✅ First reward redeemed
- ✅ 50+ customers enrolled

### Week 4 Success:
- ✅ Lead Scoring operational
- ✅ Analytics dashboard complete
- ✅ Smart re-render implemented
- ✅ All high-priority features shipped

---

**Now: What do you want to do first?**

1. Review the plan and ask questions?
2. Make the Option A/B/C decision?
3. Start Day 1 (Security Setup) immediately?
4. Something else?
