# Model Migration Strategy - Restore All Features

**Goal**: Migrate all legacy models to restore full functionality of all routers/endpoints

**Status**: Server crashes on NotificationGroup import - need to migrate models ASAP

---

## IMMEDIATE - BLOCKING SERVER STARTUP

### 1. NotificationGroup Models (CRITICAL - blocks server)
**File to create**: `models/notification.py`  
**Source**: `backups/pre-nuclear-cleanup-20251120_220938/legacy_notification_groups.py`  
**Models needed**:
- NotificationGroup
- NotificationGroupMember
- NotificationGroupEvent

**Affected routers** (currently loading):
- routers/v1/admin/notification_groups.py ← **CAUSES CRASH**

**Services using**:
- services/notification_group_service.py
- services/station_notification_sync.py

**Action**: Migrate FIRST to unblock server startup

---

## HIGH PRIORITY - DISABLED ROUTERS (Restore Features)

### 2. Lead/Newsletter Models  
**File to create**: `models/lead.py` and `models/newsletter.py`  
**Source**: `backups/pre-nuclear-cleanup-20251120_220938/legacy_lead_newsletter.py`  
**Models needed**:
- Lead, LeadContact, LeadQuality, LeadSource, LeadStatus
- Campaign, Subscriber, CampaignEvent, EmailTemplate, SubscriberTag

**Affected routers** (currently disabled):
- routers/v1/leads.py (ENABLED but may have issues)
- routers/v1/newsletter.py ← DISABLED
- routers/v1/campaigns.py ← DISABLED
- routers/v1/referrals.py ← DISABLED

**Services using**:
- services/lead_service.py
- services/newsletter_service.py
- services/newsletter_analytics_service.py
- services/nurture_campaign_service.py
- services/referral_service.py

### 3. Social/Review Models
**File to create**: `models/social.py`  
**Source**: `backups/pre-nuclear-cleanup-20251120_220938/legacy_social.py`  
**Models needed**:
- SocialThread, SocialMessage, SocialAccount, Review, ReviewSource

**Affected routers** (currently disabled):
- routers/v1/reviews.py ← DISABLED

**Services using**:
- services/review_service.py
- services/social/social_service.py
- services/social/social_ai_generator.py
- services/social/social_ai_tools.py

### 4. Feedback Models
**File to create**: `models/feedback.py`  
**Source**: `backups/pre-nuclear-cleanup-20251120_220938/legacy_feedback.py`  
**Models needed**:
- CustomerReview, DiscountCoupon

**Affected routers** (currently disabled):
- routers/v1/reviews.py ← DISABLED (same as #3)

**Services using**:
- services/review_service.py
- services/coupon_reminder_service.py

### 5. QR Tracking Models
**File to create**: `models/qr_tracking.py`  
**Source**: `backups/pre-nuclear-cleanup-20251120_220938/legacy_qr_tracking.py`  
**Models needed**:
- QRCode, QRCodeType, QRScan

**Affected routers** (currently disabled):
- routers/v1/qr_tracking.py ← DISABLED

**Services using**:
- services/qr_tracking_service.py

### 6. Stripe Models
**File to create**: `models/stripe.py`  
**Source**: `backups/pre-nuclear-cleanup-20251120_220938/legacy_stripe_models.py`  
**Models needed**:
- StripeCustomer, StripePaymentIntent, StripeRefund, etc.

**Affected routers** (currently disabled):
- routers/v1/stripe.py ← DISABLED

**Services using**:
- services/stripe_service.py

---

## MIGRATION PROCESS (Per Model File)

1. **Copy from backup**:
   ```bash
   # Example for notification models
   cp "backups/pre-nuclear-cleanup-20251120_220938/legacy_notification_groups.py" \
      "apps/backend/src/models/notification.py"
   ```

2. **Clean up imports**:
   - Change `from models.legacy_base import` → `from models.base import Base`
   - Change `from models.legacy_declarative_base import` → `from models.base import Base`
   - Remove `extend_existing=True` if not needed

3. **Update model exports** in `models/__init__.py`:
   ```python
   from models.notification import NotificationGroup, NotificationGroupMember, NotificationGroupEvent
   ```

4. **Update service imports**:
   - Uncomment the `from models.X import Y` lines
   - Remove `# TODO:` comments

5. **Test import**:
   ```python
   python -c "from models.notification import NotificationGroup; print('✅ Import OK')"
   ```

6. **Restart server** and verify

---

## EXECUTION ORDER

1. ✅ **NotificationGroup** (IMMEDIATE - blocks server)
2. **Lead/Newsletter** (restores 4 routers)
3. **Social/Feedback** (restores reviews router)
4. **QR Tracking** (restores QR router)
5. **Stripe** (restores Stripe router)

---

## ESTIMATED TIME

- NotificationGroup: 10 minutes
- Lead/Newsletter: 30 minutes (complex - many models)
- Social/Feedback: 20 minutes
- QR Tracking: 10 minutes
- Stripe: 15 minutes

**Total**: ~1.5 hours to restore all features

---

## SUCCESS CRITERIA

- ✅ Server starts without errors
- ✅ All routers enabled in main.py
- ✅ All endpoints accessible in Swagger UI
- ✅ No "TODO: Legacy models not migrated" comments
- ✅ All imports using `from models.X import Y` (not legacy_)
- ✅ Feature 1 (Booking Reminders) still works

---

**Next Action**: Migrate NotificationGroup models IMMEDIATELY to unblock server
