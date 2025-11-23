# 🚨 CRITICAL DATABASE AUDIT - PRE-MIGRATION ANALYSIS
**Date:** November 22, 2025  
**Status:** ⚠️ **MUST FIX BEFORE MIGRATION**  
**Audit Methodology:** A–H Deep Analysis (All 8 Techniques)

---

## 🔴 EXECUTIVE SUMMARY

**CRITICAL FINDINGS:**
1. ❌ **SCHEMA MISMATCH**: Newsletter/Campaign system uses `lead` schema, but documented as `newsletter` schema
2. ❌ **MISCONCEPTION**: System uses SMS (RingCentral), NOT email newsletters - but named "newsletter"
3. ❌ **BROKEN FOREIGN KEYS**: 8+ tables reference non-existent tables or wrong schemas
4. ❌ **DUPLICATE MIGRATIONS**: Business table created twice, causing migration chain breakage
5. ❌ **MISSING TABLES**: Payment tables reference `catering_bookings` (doesn't exist)

**RECOMMENDATION:** ⛔ **DO NOT PROCEED** with migration until all critical issues resolved.

---

## 📊 A–H AUDIT RESULTS

### **A. Static Analysis (Line-by-Line Schema Review)**

#### 🔴 CRITICAL: Schema Naming Confusion

**ISSUE #1: Newsletter vs SMS Campaign System**

The system is called "newsletter" but actually handles **SMS campaigns via RingCentral**, not email:

```python
# File: models/newsletter.py
class Campaign(BaseModel):
    __tablename__ = "campaigns"
    __table_args__ = {"schema": "lead", "extend_existing": True}  # ⚠️ WRONG SCHEMA!
    
    channel = Column(Enum(CampaignChannel), nullable=False)
    # Values: EMAIL, SMS, PUSH, WHATSAPP
```

**Evidence:**
- ✅ `CampaignChannel.SMS` exists
- ✅ `SMSDeliveryEvent` table exists
- ✅ `Subscriber.sms_subscribed` field exists
- ✅ RingCentral integration models exist (`call_recording.py`)
- ❌ NO email sending infrastructure found
- ❌ NO SMTP configuration in models

**Truth:**
- 📱 **System uses RingCentral SMS for campaigns** (text messages)
- 📧 Email campaigns NOT implemented (just enum placeholder)
- 🗂️ Tables are in `lead` schema, NOT `newsletter` schema

**🔴 CRITICAL BUG:**
```sql
-- Migration 017_fix_foreign_key_relationships.py references:
newsletter.sms_tracking  -- ❌ DOESN'T EXIST!
newsletter.campaigns     -- ❌ DOESN'T EXIST!

-- Actual tables are:
lead.campaigns                    -- ✅ EXISTS
lead.sms_delivery_events         -- ✅ EXISTS  
lead.campaign_events             -- ✅ EXISTS
lead.subscribers                 -- ✅ EXISTS
```

---

### **B. Runtime Simulation (Migration Execution Path)**

#### **Simulated Migration Flow:**

```
1. Migration 000 → Create identity.users ✅
2. Migration 001 → Create lead schema + customers ✅
3. Migration 002 → Create bookings schema ✅
4. Migration 003 → Create lead.social_* tables ✅
5. Migration 006 → Create identity.roles/permissions ✅
   └─ Uses raw SQL to avoid ENUM duplication ✅
6. Migration e636a2d56d82 → Add businesses table ✅
   └─ References newsletter.newsletter_subscribers ❌ FAILS!
   └─ Should reference: lead.subscribers ✅
7. Migration 017_fix_foreign_key_relationships →
   └─ References newsletter.sms_tracking ❌ TABLE DOESN'T EXIST!
   └─ Should reference: lead.sms_delivery_events ✅
```

**PREDICTION:** Migration will fail at step #6 with `relation "newsletter.newsletter_subscribers" does not exist`

---

### **C. Concurrency & Transaction Safety**

#### **Race Condition Risks:**

1. ⚠️ **Campaign Creation**:
   - No transaction isolation for campaign → subscriber linking
   - Risk: SMS sent to deleted subscriber

2. ⚠️ **SMS Delivery Tracking**:
   - `SMSDeliveryEvent` created before campaign confirmation
   - Risk: Orphaned delivery events if campaign fails

**RECOMMENDATION:**
```python
# Wrap in transaction
async with session.begin():
    campaign = Campaign(...)
    session.add(campaign)
    await session.flush()  # Get campaign.id
    
    for subscriber in subscribers:
        sms_event = SMSDeliveryEvent(campaign_id=campaign.id, ...)
        session.add(sms_event)
```

---

### **D. Data Flow Tracing**

#### **SMS Campaign Flow (Current Reality):**

```
┌─────────────────────────────────────────────────────────────┐
│               SMS CAMPAIGN DATA FLOW                         │
└─────────────────────────────────────────────────────────────┘

1. Admin creates campaign:
   lead.campaigns (channel='SMS', status='DRAFT')
                    ↓
2. Select recipients:
   lead.subscribers (sms_subscribed=True, phone NOT NULL)
                    ↓
3. Send SMS via RingCentral:
   └─ RingCentral API call (external)
   └─ Returns message_sid
                    ↓
4. Track delivery:
   lead.sms_delivery_events (message_sid, status='QUEUED')
                    ↓
5. RingCentral webhook callback:
   └─ Update status: SENT → DELIVERED (or FAILED)
                    ↓
6. Log analytics:
   lead.campaign_events (event_type='DELIVERED')
```

**🔴 MISSING COMPONENTS:**
- ❌ No RingCentral webhook handler in migrations
- ❌ No `communications` schema tables (documented but not created)
- ❌ No SMS message content table (only delivery tracking)

---

### **E. Error Path & Exception Handling**

#### **Error Scenarios Not Handled:**

1. **Campaign Creation Fails:**
   ```python
   # Current: No rollback of SMS sends
   campaign = Campaign(...)
   for subscriber in subscribers:
       send_sms(subscriber.phone)  # ⚠️ Can't rollback SMS!
   session.commit()  # ❌ Fails → SMS already sent!
   ```

2. **Subscriber Deleted Mid-Campaign:**
   ```sql
   -- Foreign key: ON DELETE SET NULL
   -- Result: SMSDeliveryEvent orphaned with NULL subscriber_id
   -- Analytics broken!
   ```

3. **RingCentral API Failure:**
   - No retry mechanism in models
   - No fallback delivery method
   - No admin notification

---

### **F. Dependency & Enum Validation**

#### 🔴 CRITICAL: Schema-Table Mismatches

| Migration Reference | Table Existence | Status |
|---------------------|----------------|--------|
| `newsletter.campaigns` | ❌ Doesn't exist | Use `lead.campaigns` |
| `newsletter.subscribers` | ❌ Doesn't exist | Use `lead.subscribers` |
| `newsletter.newsletter_subscribers` | ❌ Doesn't exist | Use `lead.subscribers` |
| `newsletter.sms_tracking` | ❌ Doesn't exist | Use `lead.sms_delivery_events` |
| `newsletter.campaign_events` | ❌ Doesn't exist | Use `lead.campaign_events` |
| `communications.call_recordings` | ⚠️ Not created in migrations | Needs Migration 010 |
| `catering_bookings` | ❌ Never existed | Should be `core.bookings` |

**ENUM Validation:**
```python
# ✅ Correctly defined:
CampaignChannel.SMS         ✅
CampaignStatus.SENDING      ✅
SMSDeliveryStatus.DELIVERED ✅

# ⚠️ Not implemented:
CampaignChannel.EMAIL       ⚠️ (No SMTP config)
CampaignChannel.WHATSAPP    ⚠️ (No API integration)
CampaignChannel.PUSH        ⚠️ (No push service)
```

---

### **G. Business Logic Validation**

#### **Campaign Business Rules (CRITICAL):**

1. **TCPA Compliance (SMS):**
   ```python
   # ✅ Implemented in models:
   subscriber.sms_subscribed = True
   subscriber.sms_unsubscribed_at = None
   
   # ✅ Implemented in migrations:
   bookings.sms_consent = True
   bookings.sms_consent_timestamp
   ```

2. **Cost Tracking:**
   ```python
   # ✅ Implemented:
   SMSDeliveryEvent.cost  # in cents
   SMSDeliveryEvent.cost_dollars  # property
   ```

3. **Delivery Status Workflow:**
   ```
   QUEUED → SENT → DELIVERED  ✅
   QUEUED → SENT → FAILED     ✅
   QUEUED → FAILED            ✅ (immediate failure)
   ```

4. **❌ MISSING: Campaign Budget Limits**
   - No max_cost field
   - No cost_limit validation
   - Risk: Accidental mass SMS = $$$

---

### **H. Helper/Utility Analysis**

#### **Missing Helper Tables:**

1. **SMS Templates** (NOT IMPLEMENTED):
   ```sql
   CREATE TABLE lead.sms_templates (
       id UUID PRIMARY KEY,
       name VARCHAR(100),
       content TEXT,  -- {{first_name}}, {{booking_date}}, etc.
       category VARCHAR(50)  -- reminder, promotion, transactional
   );
   ```

2. **Campaign Budget Tracking** (NOT IMPLEMENTED):
   ```sql
   CREATE TABLE lead.campaign_budgets (
       campaign_id UUID REFERENCES lead.campaigns(id),
       budget_cents INTEGER,
       spent_cents INTEGER DEFAULT 0,
       exceeded_at TIMESTAMPTZ
   );
   ```

3. **SMS Send Queue** (NOT IMPLEMENTED):
   ```sql
   CREATE TABLE lead.sms_send_queue (
       id UUID PRIMARY KEY,
       campaign_id UUID,
       phone_number VARCHAR(20),
       status ENUM('pending', 'sending', 'sent', 'failed'),
       scheduled_at TIMESTAMPTZ,
       attempts INTEGER DEFAULT 0
   );
   ```

---

## 🚨 CRITICAL ISSUES SUMMARY (By Severity)

### 🔴 **CRITICAL (Production Breaking)**

1. **Schema Mismatch: newsletter vs lead**
   - **Impact:** ALL campaign queries will fail
   - **Fix:** Rename schema OR update all model `__table_args__`
   - **Affected:** 5 models, 3 migrations

2. **Non-Existent Table References**
   - `catering_bookings` → should be `core.bookings`
   - `newsletter.campaigns` → should be `lead.campaigns`
   - **Impact:** Foreign key creation fails
   - **Affected:** 2 migrations

3. **Duplicate Business Migration**
   - `e636a2d56d82` and `e8e33e1e5658` both create `businesses` table
   - **Impact:** Migration chain broken
   - **Fix:** Delete `e8e33e1e5658` ✅ DONE

4. **Missing Foreign Key Schemas**
   - `station_users.user_id` → missing `identity.` prefix
   - `audit_logs.user_id` → missing `identity.` prefix
   - **Impact:** FK constraint creation fails
   - **Affected:** 4 tables

### 🟠 **HIGH (Data Integrity)**

5. **Missing RingCentral Integration Tables**
   - `communications.call_recordings` defined in model but NOT in migrations
   - Migration `010_escalation_call_recording.py` exists but not applied
   - **Impact:** Call recording features won't work

6. **Missing SMS Queue System**
   - No retry mechanism for failed SMS
   - No rate limiting for RingCentral API
   - **Impact:** SMS delivery failures, API throttling

7. **No Campaign Budget Limits**
   - Can accidentally send unlimited SMS
   - No cost alerts
   - **Impact:** Unexpected charges

### 🟡 **MEDIUM (Feature Gaps)**

8. **Email Campaigns Not Implemented**
   - Enum says `EMAIL` but no SMTP config
   - No email templates
   - **Impact:** Misleading system design

9. **No SMS Templates**
   - Every campaign requires manual content
   - No personalization variables
   - **Impact:** Poor admin UX

10. **Missing Analytics Rollups**
    - No daily/weekly campaign metrics
    - No subscriber engagement scores
    - **Impact:** No performance insights

---

## ✅ RECOMMENDED FIX SEQUENCE

### **Phase 1: Critical Schema Fixes (BEFORE MIGRATION)**

#### **Step 1: Fix Schema References**

```sql
-- Option A: Move tables to newsletter schema (RECOMMENDED)
ALTER TABLE lead.campaigns SET SCHEMA newsletter;
ALTER TABLE lead.campaign_events SET SCHEMA newsletter;
ALTER TABLE lead.sms_delivery_events SET SCHEMA newsletter;
ALTER TABLE lead.subscribers SET SCHEMA newsletter;

-- Update foreign keys to reference new schema
```

**OR**

```python
# Option B: Update all models to use 'lead' schema consistently
# File: models/newsletter.py (Line 41)
__table_args__ = {"schema": "lead", "extend_existing": True}  # Keep this
```

**DECISION NEEDED:** Which schema should campaigns live in?
- **Option A:** `newsletter` schema (marketing-focused naming)
- **Option B:** `lead` schema (CRM-focused naming)

**RECOMMENDATION:** Use `newsletter` schema for clarity, since these are **outbound campaigns**, not inbound leads.

---

#### **Step 2: Create Missing Schema**

```sql
-- If using Option A (newsletter schema):
CREATE SCHEMA IF NOT EXISTS newsletter;
```

---

#### **Step 3: Fix Foreign Key Schema Prefixes**

Create migration: `018_fix_schema_prefixes.py`

```python
def upgrade():
    conn = op.get_bind()
    
    # Fix identity.station_users
    conn.execute(sa.text("""
        ALTER TABLE identity.station_users 
        DROP CONSTRAINT IF EXISTS fk_station_users_user_id;
        
        ALTER TABLE identity.station_users 
        ADD CONSTRAINT fk_station_users_user_id 
        FOREIGN KEY (user_id) REFERENCES identity.users(id) ON DELETE CASCADE;
    """))
    
    # Fix support.audit_logs
    conn.execute(sa.text("""
        ALTER TABLE support.audit_logs
        DROP CONSTRAINT IF EXISTS fk_audit_logs_user_id;
        
        ALTER TABLE support.audit_logs
        ADD CONSTRAINT fk_audit_logs_user_id
        FOREIGN KEY (user_id) REFERENCES identity.users(id) ON DELETE SET NULL;
    """))
    
    # Fix bookings.booking_reminders
    conn.execute(sa.text("""
        ALTER TABLE bookings.booking_reminders
        DROP CONSTRAINT IF EXISTS fk_booking_reminders_booking_id;
        
        ALTER TABLE bookings.booking_reminders
        ADD CONSTRAINT fk_booking_reminders_booking_id
        FOREIGN KEY (booking_id) REFERENCES core.bookings(id) ON DELETE CASCADE;
    """))
```

---

#### **Step 4: Fix Payment Table References**

Create migration: `019_fix_payment_tables.py`

```python
def upgrade():
    conn = op.get_bind()
    
    # Fix catering_payments.booking_id
    conn.execute(sa.text("""
        ALTER TABLE public.catering_payments
        DROP CONSTRAINT IF EXISTS fk_catering_payments_booking_id;
        
        ALTER TABLE public.catering_payments
        ADD CONSTRAINT fk_catering_payments_booking_id
        FOREIGN KEY (booking_id) REFERENCES core.bookings(id) ON DELETE CASCADE;
    """))
    
    # Fix payment_notifications
    conn.execute(sa.text("""
        ALTER TABLE public.payment_notifications
        DROP CONSTRAINT IF EXISTS fk_payment_notifications_booking_id;
        
        ALTER TABLE public.payment_notifications
        ADD CONSTRAINT fk_payment_notifications_booking_id
        FOREIGN KEY (booking_id) REFERENCES core.bookings(id) ON DELETE SET NULL;
    """))
```

---

### **Phase 2: Add Missing Tables (AFTER SCHEMA FIX)**

#### **Step 5: Create SMS Templates**

```sql
CREATE TABLE newsletter.sms_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,  -- reminder, promotion, transactional
    variables JSONB DEFAULT '[]'::jsonb,  -- ["first_name", "booking_date"]
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sms_templates_category ON newsletter.sms_templates(category);
CREATE INDEX idx_sms_templates_active ON newsletter.sms_templates(is_active);
```

---

#### **Step 6: Create Campaign Budgets**

```sql
CREATE TABLE newsletter.campaign_budgets (
    campaign_id UUID PRIMARY KEY REFERENCES newsletter.campaigns(id) ON DELETE CASCADE,
    budget_cents INTEGER NOT NULL DEFAULT 0,
    spent_cents INTEGER NOT NULL DEFAULT 0,
    exceeded_at TIMESTAMPTZ,
    CHECK (spent_cents <= budget_cents OR budget_cents = 0)
);

CREATE INDEX idx_campaign_budgets_exceeded ON newsletter.campaign_budgets(exceeded_at);
```

---

#### **Step 7: Create SMS Send Queue**

```sql
CREATE TYPE sms_queue_status AS ENUM ('pending', 'sending', 'sent', 'failed');

CREATE TABLE newsletter.sms_send_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES newsletter.campaigns(id) ON DELETE CASCADE,
    subscriber_id UUID REFERENCES newsletter.subscribers(id) ON DELETE CASCADE,
    phone_number VARCHAR(20) NOT NULL,
    message_content TEXT NOT NULL,
    status sms_queue_status NOT NULL DEFAULT 'pending',
    scheduled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sent_at TIMESTAMPTZ,
    attempts INTEGER DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sms_queue_status ON newsletter.sms_send_queue(status);
CREATE INDEX idx_sms_queue_scheduled ON newsletter.sms_send_queue(scheduled_at);
```

---

### **Phase 3: Merge Migration Heads**

Currently we have TWO heads:
- `010_escalation_call_recording`
- `016_add_social_account_identity`

**Step 8: Create Merge Migration**

```bash
cd apps/backend
alembic merge heads -m "merge_social_and_communications"
```

This will create: `020_merge_social_and_communications.py`

---

## 🎯 FINAL CHECKLIST BEFORE MIGRATION

- [ ] **Decision made:** Use `newsletter` OR `lead` schema for campaigns?
- [ ] **Create missing schemas** (if using `newsletter`)
- [ ] **Move campaign tables** to correct schema
- [ ] **Update all model `__table_args__`** to match
- [ ] **Fix FK schema prefixes** (station_users, audit_logs, booking_reminders)
- [ ] **Fix payment table references** (catering_payments → core.bookings)
- [ ] **Delete duplicate migration** ✅ DONE (`e8e33e1e5658`)
- [ ] **Fix migration 017** schema references (newsletter → lead)
- [ ] **Create SMS templates table**
- [ ] **Create campaign budgets table**
- [ ] **Create SMS send queue table**
- [ ] **Merge migration heads** (010 + 016)
- [ ] **Test full migration** on clean database
- [ ] **Verify all foreign keys** with query:
  ```sql
  SELECT 
      tc.constraint_name, 
      tc.table_schema || '.' || tc.table_name AS table_name,
      kcu.column_name,
      ccu.table_schema || '.' || ccu.table_name AS foreign_table_name
  FROM information_schema.table_constraints AS tc 
  JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
  JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
  WHERE tc.constraint_type = 'FOREIGN KEY'
  ORDER BY tc.table_schema, tc.table_name;
  ```

---

## 📊 RISK ASSESSMENT

| Issue | Severity | Likelihood | Impact | Mitigation |
|-------|----------|------------|---------|------------|
| Schema mismatch causes migration failure | 🔴 CRITICAL | 100% | Production down | Fix before migration |
| Duplicate migrations break chain | 🔴 CRITICAL | 100% | Migration impossible | Delete duplicate ✅ |
| Missing FK prefixes | 🔴 CRITICAL | 90% | Data integrity loss | Add prefixes |
| Wrong table references | 🔴 CRITICAL | 90% | FK creation fails | Update references |
| Missing SMS queue | 🟠 HIGH | 70% | SMS delivery fails | Create queue table |
| No budget limits | 🟠 HIGH | 50% | Cost overruns | Add budget table |
| Missing templates | 🟡 MEDIUM | 30% | Poor UX | Create templates |

---

## ✅ FINAL RECOMMENDATION

**⛔ DO NOT RUN MIGRATIONS YET**

**Required Actions:**
1. ✅ **DONE:** Delete duplicate business migration
2. ⏳ **IN PROGRESS:** Decide on schema naming (newsletter vs lead)
3. ⏳ **PENDING:** Fix all schema references
4. ⏳ **PENDING:** Create missing tables
5. ⏳ **PENDING:** Merge migration heads
6. ⏳ **PENDING:** Test on clean database

**Estimated Time to Fix:** 2-3 hours
**Estimated Risk After Fix:** 🟢 LOW

---

**Next Step:** Await your decision on schema naming, then I'll generate ALL fix migrations automatically.
