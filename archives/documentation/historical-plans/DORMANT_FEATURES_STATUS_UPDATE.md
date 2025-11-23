# Dormant Features Status Update - Critical Findings

**Date**: November 21, 2025  
**Status**: ⚠️ **PARTIAL BLOCKAGE DISCOVERED**

---

## 🔴 CRITICAL DISCOVERY

During activation of Social Media Admin Panel, discovered that CQRS code expects models that **DO NOT EXIST** in our migrated codebase:

### Missing Models:
1. ❌ `SocialAccount` - Not in `models/social.py`
2. ❌ `SocialIdentity` - Not in `models/social.py`

### Migrated Models (Existing):
1. ✅ `SocialThread` - ✅ EXISTS
2. ✅ `SocialMessage` - ✅ EXISTS
3. ✅ `Review` - ✅ EXISTS
4. ✅ `CustomerReview` - ✅ EXISTS
5. ✅ `DiscountCoupon` - ✅ EXISTS

---

## Root Cause Analysis

The nuclear cleanup **deleted** some social models that CQRS handlers depend on:
- `SocialAccount`: Represents connected social media pages (Instagram Business, Facebook Page)
- `SocialIdentity`: Links customer records to social media handles

**Impact**: Social Admin CQRS cannot function without these models.

---

## Revised Activation Plan

### ✅ CAN ACTIVATE IMMEDIATELY (No Blockers):

#### 1. SMS Campaign Management ✅
**Files**: `routers/v1/sms_campaigns.py`  
**Status**: ✅ **READY TO ACTIVATE**  
**Models Needed**: Campaign, Subscriber (✅ ALL EXIST)  
**Action**: Fix imports + register router  
**Time**: 10 minutes

#### 2. RingCentral AI Webhooks ✅
**Files**: `routers/v1/ringcentral_ai_webhooks.py`  
**Status**: ✅ **READY TO ACTIVATE**  
**Models Needed**: Lead (✅ EXISTS)  
**Action**: Fix imports (line 296)  
**Time**: 5 minutes

#### 3. Event Sourcing (CQRS) ✅
**Files**: `cqrs/command_handlers.py`  
**Status**: ✅ **READY TO ACTIVATE**  
**Models Needed**: DomainEvent, OutboxEntry (✅ ALL EXIST)  
**Action**: Fix imports  
**Time**: 5 minutes

---

### ❌ CANNOT ACTIVATE (Missing Models):

#### 4. Social Media Admin Panel ❌
**Files**:
- `routers/v1/admin/social.py` (519 lines)
- `cqrs/social/*.py` (4 files, 1,619 lines total)

**Status**: ❌ **BLOCKED - MISSING MODELS**

**Missing Models**:
```python
# Need to CREATE these:
class SocialAccount(BaseModel):
    """Connected social media business pages."""
    __tablename__ = "social_accounts"
    __table_args__ = {"schema": "lead"}
    
    id: UUID
    platform: SocialPlatform  # instagram, facebook
    page_id: str  # External platform page ID
    page_name: str
    access_token_encrypted: str  # For API calls
    is_active: bool
    # ... more fields
    
class SocialIdentity(BaseModel):
    """Links customers to their social media handles."""
    __tablename__ = "social_identities"
    __table_args__ = {"schema": "lead"}
    
    id: UUID
    customer_id: UUID  # FK to customers
    platform: SocialPlatform
    handle: str  # @username
    profile_url: str
    # ... more fields
```

**Options**:
1. **Create missing models** (4-6 hours work):
   - Write model classes
   - Create Alembic migration
   - Test CQRS handlers
   - Activate feature
   
2. **Simplify CQRS handlers** (6-8 hours work):
   - Rewrite to work with simpler models
   - Remove SocialAccount/SocialIdentity dependencies
   - Use SocialThread as primary model
   
3. **Defer Social Admin** (recommended):
   - Activate other 3 features NOW
   - Plan Social Admin as Phase 2

---

#### 5. QR Code Tracking ❌
**Status**: ❌ **BLOCKED - MISSING MODELS**  
**Same issue**: Models don't exist, need to create

---

## Recommended Action Plan

### 🟢 PROCEED NOW (30 minutes total):

**Phase 1: SMS Campaigns** (10 min)
```bash
1. Fix routers/v1/sms_campaigns.py imports
2. Register router in main.py
3. Test: POST /api/v1/sms-campaigns
```

**Phase 2: RingCentral AI** (5 min)  
```bash
1. Fix routers/v1/ringcentral_ai_webhooks.py line 296
2. Verify router registration
3. Test: POST /api/v1/ringcentral/webhooks/sms
```

**Phase 3: Event Sourcing** (5 min)
```bash
1. Fix cqrs/command_handlers.py imports
2. No router changes needed
3. Test: Create booking → check events table
```

**Phase 4: Validation** (10 min)
```bash
1. Restart server
2. Check /docs for new endpoints
3. Test each feature
4. Document success
```

---

### 🔴 DEFER TO PHASE 2 (Need model creation):

1. **Social Media Admin Panel** - 6-8 hours
   - Create `SocialAccount` model
   - Create `SocialIdentity` model
   - Migration
   - CQRS handler updates

2. **QR Code Tracking** - 4-6 hours
   - Create `QRCode` model
   - Create `QRScan` model
   - Migration
   - Service updates

---

## Revised Success Metrics

### Immediate Win (Today):
- ✅ 3 major features activated (SMS, RC AI, Event Sourcing)
- ✅ ~800 lines of code brought back to life
- ✅ Zero new models required
- ✅ Low risk activation

### Phase 2 (Future):
- 📋 2 features require model creation
- 📋 ~2,000 lines of code
- 📋 Requires database migrations
- 📋 Higher complexity

---

## User Decision Required

**Question**: Do you want to:

**Option A (Recommended)**: ✅
- Activate SMS Campaigns, RingCentral AI, Event Sourcing NOW (30 min)
- Plan Social Admin + QR Tracking as separate projects

**Option B**: ⏸️
- Pause everything
- Create missing models first (SocialAccount, SocialIdentity)
- Then activate all features together (8-10 hours total)

**Option C**: 🔍
- Proceed with Option A
- Let me analyze if we can simplify Social CQRS to work without missing models

---

**Waiting for user directive...**
