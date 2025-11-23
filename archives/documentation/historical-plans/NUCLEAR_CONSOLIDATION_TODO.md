# Nuclear Consolidation - Remaining Tasks

**Created**: November 20, 2025  
**Status**: Server validation in progress  
**Branch**: nuclear-refactor-clean-architecture

---

## ✅ COMPLETED

### Phase 1-5: Initial Nuclear Consolidation
- ✅ Deleted 13 legacy_*.py files
- ✅ Fixed 49 files with automated import replacements
- ✅ Comprehensive duplicate audit (found 2 more duplicates)
- ✅ Removed duplicate Customer and TrainingData from api/ai/endpoints/models.py
- ✅ Deleted db/models/ directory (5 files)
- ✅ Deleted models/audit.py, models/user.py, models/station.py
- ✅ Created models/events.py (DomainEvent, OutboxEntry for CQRS)
- ✅ Fixed all broken imports (76 files total)
- ✅ Confirmed ZERO duplicate tables (57 unique tables)
- ✅ Extended core/auth/models.py with AuthProvider and UserStatus enums

### Phase 6: Broken Import Pattern Fixes
- ✅ Discovered 34 broken TODO import patterns
- ✅ Created scripts/find_broken_imports.py
- ✅ Created scripts/fix_broken_imports.py
- ✅ Fixed 27 files with orphaned import lines

### Phase 7: Server Startup Issues
- ✅ Identified QRScan/QRCode models causing import errors
- ✅ Disabled QR tracking router in main.py (non-critical feature)
- ✅ Audited all imports - found 6 legacy imports in unused files (not blocking startup)

---

## 🔴 CRITICAL - IMMEDIATE (Blocks Feature 1)

### 1. Server Validation (Next Step)
- [ ] Restart server after QR tracking router disabled
- [ ] Verify server starts successfully (no import errors)
- [ ] Test health endpoint: `curl http://localhost:8000/health`
- [ ] Confirm Swagger UI accessible: http://localhost:8000/docs

**Expected Result**: Server starts with warning: "⚠️ QR Code Tracking System temporarily disabled (models not migrated)"

---

## 🟠 HIGH PRIORITY - SPRINT 1

### 2. Feature 1: Booking Reminders Testing (After Server Validated)
**Time Estimate**: 15 minutes

Test endpoints via Swagger UI:
- [ ] POST /api/v1/bookings/{booking_id}/reminders
- [ ] GET /api/v1/bookings/{booking_id}/reminders
- [ ] GET /api/v1/bookings/{booking_id}/reminders/{reminder_id}
- [ ] PUT /api/v1/bookings/{booking_id}/reminders/{reminder_id}
- [ ] DELETE /api/v1/bookings/{booking_id}/reminders/{reminder_id}

**Test Data**: Use one of 7 existing booking IDs from public.bookings table

**Success Criteria**: At least one successful CRUD operation

### 3. Features 2-4 Implementation (After Feature 1 Validated)
**Time Estimate**: 1 hour

- [ ] Feature 2: Multi-Location Support
- [ ] Feature 3: Admin User Management
- [ ] Feature 4: Deposit CRUD API

**Pattern**: Inspect DB → Create model → Service → Endpoints → Test

### 4. Full Test Suite (After All Features)
**Time Estimate**: 30 minutes

- [ ] Run: `pytest tests/`
- [ ] Expected: 89 baseline + 25 Sprint 1 = 114 passing tests
- [ ] Fix any failing tests

---

## 🟡 MEDIUM PRIORITY - MODEL MIGRATION

### 5. Unmigrated Models Review
**Time Estimate**: 2 hours

**Files with TODO comments**: 27 files

**Unmigrated Model Categories**:

#### A. Lead/Newsletter Models (15 files affected)
- [ ] Lead
- [ ] LeadContact
- [ ] LeadQuality
- [ ] LeadSource
- [ ] Campaign
- [ ] Subscriber
- [ ] CampaignEvent
- [ ] EmailTemplate

**Files**:
- services/lead_service.py
- services/newsletter_service.py
- routers/v1/leads.py
- routers/v1/newsletter.py
- schemas/newsletter.py
- repositories/newsletter_analytics.py

**Decision Required**:
- Check if tables exist in production DB
- Check if endpoints actively used
- **A**: Migrate to modern models, OR
- **B**: Mark deprecated, create new implementations, OR
- **C**: Remove if unused in production

#### B. Social/Review Models (9 files affected)
- [ ] SocialThread
- [ ] SocialMessage
- [ ] SocialAccount
- [ ] Review
- [ ] ReviewSource

**Files**:
- services/social/thread_service.py
- services/social/message_service.py
- services/review_service.py
- routers/v1/admin/social.py
- cqrs/social/* (4 files)
- workers/review_worker.py

**Decision Required**: Same as Lead/Newsletter

#### C. QR Tracking Models (1 file affected) 🔴 BLOCKS QR ROUTER
- [ ] QRCode
- [ ] QRCodeType
- [ ] QRScan

**Files**:
- services/qr_tracking_service.py
- routers/v1/qr_tracking.py (CURRENTLY DISABLED)

**Location**: Backup in `backups/pre-nuclear-cleanup-20251120_220938/legacy_qr_tracking.py`

**Action Required**:
1. Check if qr_codes and qr_scans tables exist in production
2. If YES: Migrate models to models/qr_tracking.py
3. If NO: Create new tables or remove feature
4. Re-enable router in main.py (line 861-873)

**Migration Checklist**:
- [ ] Create models/qr_tracking.py with QRCode, QRScan, QRCodeType
- [ ] Update services/qr_tracking_service.py imports
- [ ] Update routers/v1/qr_tracking.py imports
- [ ] Uncomment router in main.py
- [ ] Test QR endpoints via Swagger UI
- [ ] Run tests: `pytest tests/test_qr_tracking.py`

#### D. Notification Models (3 files affected)
- [ ] NotificationGroup
- [ ] NotificationEvent

**Files**:
- services/notification_service.py
- routers/v1/notifications.py

**Decision Required**: Same as Lead/Newsletter

#### E. Feedback Models (2 files affected)
- [ ] CustomerReview
- [ ] DiscountCoupon

**Files**:
- services/feedback_service.py
- routers/v1/feedback.py

**Decision Required**: Same as Lead/Newsletter

#### F. Legacy Imports in Non-Critical Files (6 files - NOT blocking startup)
**These files have legacy imports but are not loaded by main.py**:

1. **api/ai/endpoints/services/chef_availability_service.py**
   - Import: `from api.app.models.core import Booking`
   - Status: Not imported by main.py
   - Action: Fix when AI endpoints are activated

2. **routers/v1/webhooks/google_business_webhook.py**
   - Import: `from models.legacy_core import Event`
   - Status: Webhook router not included in main.py
   - Action: Fix before enabling webhook endpoints

3. **routers/v1/webhooks/stripe_webhook.py**
   - Import: `from models.legacy_core import Event`
   - Status: Webhook router not included in main.py
   - Action: Fix before enabling webhook endpoints

4. **routers/v1/webhooks/meta_webhook.py**
   - Import: `from models.legacy_core import Event`
   - Status: Webhook router not included in main.py
   - Action: Fix before enabling webhook endpoints

5. **api/v1/endpoints/leads.py**
   - Import: `from api.app.models.lead_newsletter import LeadSource, LeadStatus`
   - Status: Not imported by main.py
   - Action: Fix when lead models migrated (Category A)

6. **cqrs/command_handlers.py**
   - Import: `from models.legacy_core import Booking, Customer, Message, MessageThread, Payment`
   - Status: Not imported by main.py
   - Action: Fix when CQRS command handlers are activated

**Priority**: LOW (does not block server startup or Feature 1 testing)

---

## 🟢 LOW PRIORITY - DOCUMENTATION

### 6. Create Final Cleanup Summary
**Time Estimate**: 30 minutes

**File**: NUCLEAR_CONSOLIDATION_COMPLETE.md

**Contents**:
- Before/After metrics (26→13 models, duplicates eliminated)
- Files deleted (18 total)
- Files fixed (76 total)
- Single source of truth map (57 tables)
- Lessons learned
- Prevention guidelines

### 7. Update Architecture Diagrams
**Time Estimate**: 1 hour

- [ ] Update database schema diagram
- [ ] Update service dependency diagram
- [ ] Update authentication flow diagram
- [ ] Document new CQRS event sourcing (models/events.py)

---

## 📊 METRICS

### Code Health
- **Total Files Deleted**: 18
  - 13 legacy_*.py
  - 5 from db/models/
- **Total Files Fixed**: 76
  - 49 initial import fixes
  - 8 comprehensive cleanup
  - 27 broken TODO patterns
  - (Some overlap)
- **Duplicate Tables**: 0 (confirmed)
- **Unique Tables**: 57

### Backups
- `backups/pre-nuclear-cleanup-20251120_220938/` (13 legacy files)
- `backups/comprehensive-cleanup-20251120_224014/` (db/models/, audit.py, user.py, station.py)

### Models Status
- ✅ **Production Ready**: 57 unique tables
- ✅ **Event Sourcing**: DomainEvent, OutboxEntry (models/events.py)
- ⚠️ **Unmigrated**: ~40 models in 5 categories (Lead, Social, QR, Notification, Feedback)
- 🔴 **Blocking Router**: QR tracking (disabled in main.py line 861-873)

---

## 🎯 NEXT ACTION

**IMMEDIATE**: Restart server and validate startup

```bash
cd c:\Users\surya\projects\MH webapps\apps\backend
python run_backend.py
```

**Expected Output**:
```
✅ Application startup complete
⚠️ QR Code Tracking System temporarily disabled (models not migrated)
INFO:     Uvicorn running on http://localhost:8000
```

**If Success**: Proceed to Feature 1 testing  
**If Error**: Identify new error, fix, restart, iterate

---

## 📝 NOTES

### Key Learnings
1. **Always check production DB schema first** before creating models
2. **Type annotations evaluated at import time** - even commented code in type hints causes errors
3. **Try-except blocks don't catch import-time errors** - must comment out entire import
4. **TODO comments with orphaned imports** create syntax errors
5. **Nuclear consolidation requires iterative testing** - can't fix everything at once

### Prevention Guidelines
1. **Single source of truth** - one model per table
2. **No legacy_* files** - migrate or delete immediately
3. **No duplicate __tablename__** - run scripts/find_duplicate_tables.py regularly
4. **Proper TODO comments** - comment out entire import blocks, not just parts
5. **Feature flags for new code** - never merge experimental features to main

---

**Last Updated**: November 20, 2025 (after QR tracking router disabled)
