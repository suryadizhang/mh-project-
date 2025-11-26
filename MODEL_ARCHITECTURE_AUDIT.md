# 🔍 Model Architecture Audit - Complete Analysis

**Date:** November 25, 2025 **Status:** CRITICAL DUPLICATES FOUND
**Priority:** HIGH - Needs immediate decision

---

## 🚨 CRITICAL ISSUES FOUND

### **Issue 1: DUPLICATE TABLE MODELS - Same Table, Multiple ORM Classes**

These models create **SQLAlchemy mapper conflicts** because multiple
ORM classes try to map to the same database table:

#### **1.1 Booking Models (3 DUPLICATES!)**

- ✅ **`models/booking.py`** → `bookings` table (37 columns)
- ⚠️ **`db/models/core.py`** → `bookings` table (Booking class)
- **CONFLICT:** Two different models for same table!

**Database Reality:** `bookings` table has these columns (needs
verification)

**Recommendation:**

- **KEEP:** `models/booking.py` (appears to be active, has
  relationships to reminders)
- **DEPRECATE:** `db/models/core.py` Booking model
- **ACTION:** Choose ONE canonical model

---

#### **1.2 Customer Models (2 DUPLICATES)**

- ✅ **`models/customer.py`** → `customers` table
- ⚠️ **`db/models/core.py`** → `customers` table (Customer class)

**Recommendation:**

- **KEEP:** `models/customer.py` (has escalations relationship)
- **DEPRECATE:** `db/models/core.py` Customer model

---

#### **1.3 Escalation Models (3 DUPLICATES!)**

- ✅ **`models/escalation.py`** → `escalations` table
- ⚠️ **`db/models/support_communications.py`** → `escalations` table
- **CONFLICT:** Two different models for same table!

**Recommendation:**

- **KEEP:** `models/escalation.py` (active in current codebase)
- **DEPRECATE:** `db/models/support_communications.py` Escalation

---

#### **1.4 Call Recording Models (2 DUPLICATES)**

- ✅ **`models/call_recording.py`** → `call_recordings` table
- ⚠️ **`db/models/support_communications.py`** → `call_recordings`
  table

**Recommendation:**

- **KEEP:** `models/call_recording.py`
- **DEPRECATE:** `db/models/support_communications.py` CallRecording

---

#### **1.5 Review Models (3 DUPLICATES!)**

- ✅ **`models/review.py`** → `customer_review_blog_posts` table
- ⚠️ **`models/social.py`** → `reviews` table
- ⚠️ **`models/social.py`** → `customer_reviews` table
- ⚠️ **`db/models/core.py`** → `reviews` table
- ⚠️ **`db/models/feedback_marketing.py`** → `customer_reviews` table

**MAJOR CONFUSION:** Multiple review-related tables with different
purposes

**Recommendation:**

- **CLARIFY:** Are these different types of reviews?
  - Blog-published reviews vs internal reviews?
  - Need to map business logic to tables

---

#### **1.6 Lead Models (2 DUPLICATES)**

- ✅ **`models/lead.py`** → `leads` table
- ⚠️ **`db/models/lead.py`** → `leads` table

**Recommendation:**

- **KEEP:** ONE lead model (prefer `db/models/lead.py` - more
  comprehensive)
- **DEPRECATE:** `models/lead.py`

---

#### **1.7 Social Account Models (3 DUPLICATES!)**

- ✅ **`models/social.py`** → `social_accounts` table
- ⚠️ **`db/models/lead.py`** → `social_accounts` table
  (BusinessSocialAccount)
- ⚠️ **`db/models/identity.py`** → `social_accounts` table
  (OAuthAccount)

**CRITICAL:** Three different concepts using same table name!

- OAuth accounts (Google/Microsoft login)
- Business social media accounts (Instagram/Facebook pages)
- User social identities

**Recommendation:**

- **RENAME TABLES** to match business logic:
  - `identity.oauth_accounts` - User authentication via Google/OAuth
  - `public.business_social_accounts` - Company Instagram/Facebook
    pages
  - `public.customer_social_identities` - Customer social profiles

---

#### **1.8 Social Thread Models (2 DUPLICATES)**

- ✅ **`models/social.py`** → `social_threads` table
- ⚠️ **`db/models/lead.py`** → `social_threads` table
  (LeadSocialThread)

**Recommendation:**

- **MERGE:** Decide if leads and customers use same thread model
- **OR SEPARATE:** `lead_social_threads` vs `customer_social_threads`

---

#### **1.9 Social Identity Models (2 DUPLICATES)**

- ✅ **`models/social.py`** → `social_identities` table
- ⚠️ **`db/models/lead.py`** → `social_identities` table

**Recommendation:**

- **KEEP:** ONE model (prefer `db/models/lead.py` - more
  comprehensive)

---

#### **1.10 Newsletter/Campaign Models (2 DUPLICATES)**

- ✅ **`models/newsletter.py`** → Multiple tables
- ⚠️ **`db/models/newsletter.py`** → Multiple tables (more
  comprehensive)

**Recommendation:**

- **KEEP:** `db/models/newsletter.py` (has full campaign/SMS
  infrastructure)
- **DEPRECATE:** `models/newsletter.py`

---

#### **1.11 Pricing Tier Models (2 DUPLICATES)**

- ✅ **`models/knowledge_base.py`** → `pricing_tiers` table
- ⚠️ **`db/models/core.py`** → `pricing_tiers` table

**Recommendation:**

- **KEEP:** ONE model (decide based on usage)

---

#### **1.12 Role/Permission Models (2 DUPLICATES)**

- ✅ **`models/role.py`** → `roles`/`permissions` tables
- ⚠️ **`db/models/identity.py`** → `roles`/`permissions` tables

**Recommendation:**

- **KEEP:** `db/models/identity.py` (modern SQLAlchemy 2.0 with Mapped
  types)
- **DEPRECATE:** `models/role.py`

---

#### **1.13 Discount Coupon Models (2 DUPLICATES)**

- ✅ **`models/social.py`** → `discount_coupons` table
- ⚠️ **`db/models/feedback_marketing.py`** → `discount_coupons` table

**Recommendation:**

- **KEEP:** `db/models/feedback_marketing.py` (more comprehensive)

---

#### **1.14 Domain Events Models (2 DUPLICATES)**

- ✅ **`models/events.py`** → `domain_events` table
- ⚠️ **`db/models/events.py`** → `domain_events` table

**Recommendation:**

- **KEEP:** ONE model (prefer `db/models/events.py`)

---

#### **1.15 Message/Thread Models (MULTIPLE DUPLICATES)**

- ✅ **`db/models/core.py`** → `messages` and `message_threads` tables
- ⚠️ **`api/v1/inbox/models.py`** → `Message` and `Thread` classes
- ⚠️ **`api/ai/endpoints/models.py`** → `Message` class

**CRITICAL CONFUSION:** Multiple messaging systems!

- Customer messaging
- Email inbox threads
- AI conversation messages

**Recommendation:**

- **CLARIFY TABLE NAMES:**
  - `customer_messages` / `customer_threads` - Customer support
    messages
  - `email_messages` / `email_threads` - Email inbox (already exist!)
  - `ai_messages` / `ai_conversations` - AI chat (already exist!)

---

#### **1.16 Station/Auth Models (PARTIALLY FIXED)**

- ✅ **`db/models/identity.py`** → `stations`, `station_users`,
  `station_access_tokens`, `station_audit_logs`
- ⚠️ **`core/auth/station_models.py`** → Same tables (DUPLICATES)
- ⚠️ **`core/auth/models.py`** → `auth_users` table (DOESN'T EXIST IN
  DB!)

**Status:** We just fixed User imports, but Station models still
duplicated

**Recommendation:**

- **DEPRECATE:** `core/auth/station_models.py` - use
  `db/models/identity` as canonical
- **REMOVE:** `core/auth/models.StationUser` references to
  non-existent `auth_users` table
- **OR CREATE MIGRATION:** If `auth_users` is actually needed

---

### **Issue 2: TABLE NAME COLLISIONS**

Tables that share names across schemas:

#### **2.1 `social_accounts` (Collision!)**

- `identity.social_accounts` - OAuth accounts (db/models/identity.py)
- `public.social_accounts` - Business social media (db/models/lead.py)

**Fix:** Rename to:

- `identity.oauth_accounts`
- `public.business_social_accounts`

---

#### **2.2 `social_threads` (Potential Collision)**

- Multiple models reference this table
- Need to clarify: customer vs lead social threads

---

### **Issue 3: MISSING TABLES (Models exist but no DB table)**

Based on check_schema.py output:

#### **3.1 `identity.auth_users`**

- **Model:** `core/auth/models.py` StationUser class
- **Status:** ❌ Table DOES NOT EXIST
- **Action:** Either create migration OR remove model

#### **3.2 `identity.user_station_assignments`**

- **Model:** `core/auth/station_models.py` UserStationAssignment class
  (OLD name)
- **Status:** ❌ Table DOES NOT EXIST (uses `station_users` instead)
- **Action:** ✅ ALREADY FIXED - renamed `__tablename__` to
  `station_users`

---

### **Issue 4: ORPHANED MODELS (No active usage)**

Models that may not be used in current codebase:

- `monitoring/alert_rule_model.py` - AlertRule (duplicate of
  monitoring/models.py AlertRule)
- `models/business.py` - Business model (not connected to main app)
- `models/system_event.py` - SystemEvent (unclear usage)
- `models/terms_acknowledgment.py` - TermsAcknowledgment (unclear
  usage)

---

## 📊 STATISTICS

- **Total Model Files:** 30+
- **Total Model Classes:** 100+
- **Duplicate Table Mappings:** 15+ cases
- **Table Name Collisions:** 2 confirmed
- **Missing Tables:** 1 confirmed (auth_users)
- **Orphaned Models:** 4+ potential

---

## 🎯 RECOMMENDED ACTION PLAN

### **Phase 1: IMMEDIATE (Before production)**

1. **Resolve Station/Auth Duplicates:**

   ```
   KEEP: db/models/identity.py (Station, StationUser, StationAccessToken, StationAuditLog)
   DEPRECATE: core/auth/station_models.py (entire file)
   REMOVE: core/auth/models.py StationUser OR create auth_users migration
   ```

2. **Fix Table Name Collisions:**

   ```sql
   -- Rename tables to be explicit
   ALTER TABLE identity.social_accounts RENAME TO oauth_accounts;
   ALTER TABLE public.social_accounts RENAME TO business_social_accounts;
   ```

3. **Resolve Booking/Customer Duplicates:**
   ```
   KEEP: models/booking.py, models/customer.py
   DEPRECATE: db/models/core.py Booking and Customer classes
   ```

### **Phase 2: ARCHITECTURAL (Next sprint)**

4. **Consolidate Lead Models:**

   ```
   KEEP: db/models/lead.py (comprehensive)
   REMOVE: models/lead.py
   ```

5. **Consolidate Newsletter Models:**

   ```
   KEEP: db/models/newsletter.py
   REMOVE: models/newsletter.py
   ```

6. **Clarify Review System:**
   ```
   DOCUMENT: Different review types and their purposes
   ENSURE: One model per table
   ```

### **Phase 3: CLEANUP (Future refactor)**

7. **Remove Orphaned Models:**
   - Verify usage with grep search
   - Move to `deprecated/` folder
   - Update imports

8. **Standardize Model Location:**
   ```
   STRATEGY: Choose ONE model directory structure
   OPTION A: Keep db/models/ as canonical (modern SQLAlchemy 2.0)
   OPTION B: Keep models/ as canonical (simpler structure)
   RECOMMENDED: OPTION A (db/models/) - better organized by domain
   ```

---

## 🔧 PROPOSED CANONICAL MODEL STRUCTURE

```
db/models/
├── identity.py          # Users, OAuth, Stations, Roles, Permissions
├── core.py              # Bookings, Customers, Messages (REMOVE duplicates)
├── lead.py              # Leads, Social identities, Business accounts
├── newsletter.py        # Campaigns, Subscribers, SMS
├── feedback_marketing.py # Reviews, Coupons, QR codes
├── support_communications.py # Escalations, Calls (REMOVE duplicates)
├── integra.py           # Payment events, Call sessions, Social inbox
└── events.py            # Domain events, Outbox, Inbox

models/ (TO BE DEPRECATED)
├── booking.py           # MOVE to db/models/core.py OR keep if different
├── customer.py          # MOVE to db/models/core.py OR keep if different
├── escalation.py        # REMOVE (use db/models/support_communications.py)
├── knowledge_base.py    # KEEP (unique business logic tables)
├── email.py             # KEEP (email-specific tables)
├── contact.py           # KEEP (CRM contacts)
└── [other unique models]

api/v1/inbox/models.py   # KEEP (email inbox specific)
api/ai/endpoints/models.py # KEEP (AI conversation specific)
core/auth/               # DEPRECATE (use db/models/identity.py)
```

---

## ❓ QUESTIONS FOR YOU TO DECIDE

### **Q1: Booking & Customer Models**

- Do `models/booking.py` and `db/models/core.py` Booking represent
  different business logic?
- Or are they duplicates that should be merged?
- **Same question for Customer model**

### **Q2: Review System Architecture**

- Are these different review types?
  - `customer_review_blog_posts` (published to website)
  - `customer_reviews` (internal feedback)
  - `reviews` (general reviews)
- Should they be separate tables or unified?

### **Q3: Social Accounts Clarification**

- Confirm business logic:
  - OAuth accounts = User login via Google/Microsoft →
    `identity.oauth_accounts`
  - Business social accounts = Company Instagram/Facebook pages →
    `business_social_accounts`
  - Customer social identities = Customer's social profiles →
    `customer_social_identities`
- Should we rename tables to match this?

### **Q4: Station Auth System**

- Do you actually need `identity.auth_users` table?
- Or should Station staff just use `identity.users` table?
- Current database has NO `auth_users` table

### **Q5: Model Directory Strategy**

- Keep `db/models/` as canonical (modern SQLAlchemy 2.0)?
- Or keep `models/` as canonical (simpler)?
- Or hybrid approach?

### **Q6: Message/Thread Systems**

- Clarify different messaging systems:
  - Customer support messages
  - Email inbox threads
  - AI conversation messages
- Should table names be more explicit?

---

## 🚀 NEXT STEPS

1. **REVIEW THIS AUDIT**
2. **ANSWER DECISION QUESTIONS (Q1-Q6)**
3. **APPROVE ACTION PLAN**
4. **I WILL IMPLEMENT FIXES**

---

## 📝 NOTES

- Backend currently WORKS despite duplicates (SQLAlchemy resolves
  first model found)
- BUT this is **fragile** and can cause mapper errors
- Production deployment should have CLEAN, unambiguous model
  architecture
- Current duplicates are **technical debt** from evolutionary
  development

**Priority:** Fix before production deployment to avoid runtime mapper
conflicts.
