# 🔧 Model Consolidation Implementation Plan

**Date:** November 25, 2025 **Based On:** Your answers to Q1-Q6
**Strategy:** Option A - Use `db/models/` as canonical (modern
SQLAlchemy 2.0)

---

## ✅ YOUR BUSINESS LOGIC DECISIONS

### **Q1: Booking & Customer - MERGE** ✅

- **Action:** Consolidate into `db/models/core.py`
- **Reason:** Same business entities, no need for duplicates

### **Q2: Reviews - DIFFERENT SYSTEMS** ✅

**Two separate review systems:**

1. **Blog Reviews** (`models/review.py`) →
   `customer_review_blog_posts`
   - Purpose: Published testimonials on marketing website
   - Features: Approval workflow, SEO metadata, blog integration

2. **Event Reviews** (`db/models/feedback_marketing.py`) →
   `customer_reviews`
   - Purpose: Post-event feedback from customers
   - Features: Star ratings, escalation, coupon rewards
   - Integration: Google Reviews sync, admin escalation

**Action:** Keep both, rename tables for clarity

### **Q3: Social Accounts - THREE SEPARATE SYSTEMS** ✅

1. **OAuth Accounts** (`db/models/identity.py`) →
   `identity.oauth_accounts`
   - Purpose: Admin login via Google OAuth
   - Users: Admin staff only

2. **Business Social Accounts** (`db/models/lead.py`) →
   `public.business_social_accounts`
   - Purpose: Manage company Instagram/Facebook/social media
   - Features: Chat monitoring, lead generation, multi-channel
     messaging

3. **Customer Social Identities** (`db/models/lead.py`) →
   `public.customer_social_identities`
   - Purpose: Track customer social profiles across channels
   - Features: Unified conversation history, cross-channel customer
     matching

**Action:** Rename tables to be explicit

### **Q4: Station Auth - MULTI-TENANT STATION MANAGER SYSTEM** ✅

- **Purpose:** Station managers authenticate and manage their assigned
  stations
- **Architecture:** Multi-tenant RBAC system
- **Tables:**
  - `identity.users` - All users (including station managers)
  - `identity.stations` - Physical locations
  - `identity.station_users` - User↔Station assignments with roles
  - `identity.station_access_tokens` - Station-specific auth tokens
  - `identity.station_audit_logs` - Station access audit trail

**Action:** Keep station auth system, deprecate `core/auth/models.py`
duplicate

### **Q5: Model Directory - OPTION A** ✅

- **Canonical:** `db/models/` (modern SQLAlchemy 2.0)
- **Reason:** Better organized, type-safe, future-proof

### **Q6: Message Systems - RENAME FOR CLARITY** ✅

- **Customer Support:** `customer_messages` /
  `customer_message_threads`
- **Email Inbox:** `email_messages` / `email_threads` ✅ (already
  correct!)
- **AI Chat:** `ai_messages` / `ai_conversations` ✅ (already
  correct!)

---

## 🎯 IMPLEMENTATION PLAN

### **Phase 1: IMMEDIATE FIXES (2-4 hours)**

#### **1.1 Deprecate Duplicate Auth Models** ✅

**Files to deprecate:**

- `apps/backend/src/core/auth/station_models.py` (ENTIRE FILE - use
  db/models/identity.py)
- `apps/backend/src/core/auth/models.py` StationUser class
  (non-existent table)

**Action:**

```python
# Add deprecation warnings
import warnings
warnings.warn(
    "core.auth.station_models is deprecated. Use db.models.identity instead.",
    DeprecationWarning,
    stacklevel=2
)
```

**Update all imports:**

```python
# OLD (165 files may import this!)
from core.auth.station_models import Station, UserStationAssignment

# NEW
from db.models.identity import Station, StationUser  # StationUser is the junction table
```

---

#### **1.2 Merge Booking/Customer Models** ✅

**Keep:** `db/models/core.py` Booking and Customer classes
**Deprecate:** `models/booking.py` and `models/customer.py`

**Migration needed:**

```python
# Check if db/models/core.py matches database
# Update relationships to use db.models.core imports
```

**Imports to update:**

```python
# OLD
from models.booking import Booking
from models.customer import Customer

# NEW
from db.models.core import Booking, Customer
```

---

#### **1.3 Consolidate Lead/Newsletter Models** ✅

**Keep:**

- `db/models/lead.py` - Comprehensive lead system
- `db/models/newsletter.py` - Full campaign/SMS system

**Deprecate:**

- `models/lead.py`
- `models/newsletter.py`

---

### **Phase 2: TABLE RENAMING (4-6 hours)**

#### **2.1 Rename Social Account Tables**

**Migration: `rename_social_account_tables.py`**

```sql
-- 1. OAuth accounts (admin login)
ALTER TABLE identity.social_accounts RENAME TO oauth_accounts;

-- 2. Business social media accounts
ALTER TABLE public.social_accounts RENAME TO business_social_accounts;

-- 3. Customer social profiles (already correct naming in lead.py)
-- public.social_identities → public.customer_social_identities
ALTER TABLE public.social_identities RENAME TO customer_social_identities;
```

**Update model table names:**

```python
# db/models/identity.py - OAuthAccount
__tablename__ = "oauth_accounts"  # Changed from social_accounts

# db/models/lead.py - BusinessSocialAccount
__tablename__ = "business_social_accounts"  # Changed from social_accounts

# db/models/lead.py - SocialIdentity → CustomerSocialIdentity
class CustomerSocialIdentity(Base):
    __tablename__ = "customer_social_identities"  # Changed from social_identities
```

---

#### **2.2 Rename Review Tables**

**Migration: `rename_review_tables.py`**

```sql
-- Blog reviews (already correctly named)
-- customer_review_blog_posts ✅

-- Event reviews
-- customer_reviews → event_customer_reviews (for clarity)
ALTER TABLE customer_reviews RENAME TO event_customer_reviews;
```

**Update model:**

```python
# db/models/feedback_marketing.py - CustomerReview
__tablename__ = "event_customer_reviews"  # Make purpose explicit
```

---

#### **2.3 Rename Message/Thread Tables**

**Migration: `rename_message_tables.py`**

```sql
-- Customer support messages
ALTER TABLE messages RENAME TO customer_messages;
ALTER TABLE message_threads RENAME TO customer_message_threads;

-- Email inbox (already correct!)
-- email_messages ✅
-- email_threads ✅

-- AI conversations (already correct!)
-- ai_messages ✅
-- ai_conversations ✅
```

**Update models:**

```python
# db/models/core.py
class Message(Base):
    __tablename__ = "customer_messages"  # Changed from messages

class MessageThread(Base):
    __tablename__ = "customer_message_threads"  # Changed from message_threads
```

---

#### **2.4 Rename Social Thread Tables**

**Migration: `rename_social_thread_tables.py`**

```sql
-- Lead social threads
ALTER TABLE social_threads RENAME TO lead_social_threads;
```

**Update models:**

```python
# db/models/lead.py - LeadSocialThread
__tablename__ = "lead_social_threads"  # Changed from social_threads
```

---

### **Phase 3: REMOVE DUPLICATES (2-3 hours)**

#### **3.1 Deprecate Duplicate Models**

**Create: `apps/backend/src/models/DEPRECATED/`**

Move these files:

```
models/booking.py          → models/DEPRECATED/booking.py
models/customer.py         → models/DEPRECATED/customer.py
models/lead.py            → models/DEPRECATED/lead.py
models/newsletter.py      → models/DEPRECATED/newsletter.py
models/escalation.py      → models/DEPRECATED/escalation.py
models/call_recording.py  → models/DEPRECATED/call_recording.py
models/role.py            → models/DEPRECATED/role.py
models/social.py          → models/DEPRECATED/social.py (most models)
```

**Update imports across codebase:**

```bash
# Find all imports
grep -r "from models.booking import" apps/backend/src/
grep -r "from models.customer import" apps/backend/src/

# Replace with db.models imports
```

---

#### **3.2 Remove Duplicate Classes from db/models/core.py**

**Keep in `db/models/core.py`:**

- Booking ✅
- Customer ✅
- Chef ✅
- MessageThread → (renamed to customer_message_threads)
- Message → (renamed to customer_messages)

**Remove from `db/models/core.py` (duplicates):**

- PricingTier (keep in `models/knowledge_base.py` - business rules)
- SocialThread (moved to `db/models/lead.py` as LeadSocialThread)
- Review (keep blog reviews in `models/review.py`, event reviews in
  `db/models/feedback_marketing.py`)

---

### **Phase 4: UPDATE IMPORTS (4-6 hours)**

#### **4.1 Create Import Map**

```python
# IMPORT_MAP.md - Reference for migration

OLD IMPORTS → NEW IMPORTS

# Booking/Customer
from models.booking import Booking → from db.models.core import Booking
from models.customer import Customer → from db.models.core import Customer

# Station/Auth
from core.auth.station_models import Station → from db.models.identity import Station
from core.auth.station_models import UserStationAssignment → from db.models.identity import StationUser

# Lead/Social
from models.lead import Lead → from db.models.lead import Lead
from models.social import SocialAccount → from db.models.lead import BusinessSocialAccount
from models.social import SocialIdentity → from db.models.lead import CustomerSocialIdentity

# Newsletter
from models.newsletter import Campaign → from db.models.newsletter import Campaign
from models.newsletter import Subscriber → from db.models.newsletter import Subscriber

# Reviews
from models.review import CustomerReviewBlogPost → (keep as is)
from models.social import CustomerReview → from db.models.feedback_marketing import CustomerReview

# Escalation
from models.escalation import Escalation → from db.models.support_communications import Escalation

# Call Recording
from models.call_recording import CallRecording → from db.models.support_communications import CallRecording

# Roles/Permissions
from models.role import Role → from db.models.identity import Role
from models.role import Permission → from db.models.identity import Permission
```

---

#### **4.2 Automated Import Replacement**

**Script: `fix_imports.py`**

```python
#!/usr/bin/env python3
"""
Fix all imports to use canonical db/models/
"""
import os
import re
from pathlib import Path

IMPORT_MAP = {
    "from models.booking import": "from db.models.core import",
    "from models.customer import": "from db.models.core import",
    "from core.auth.station_models import Station": "from db.models.identity import Station",
    "from core.auth.station_models import UserStationAssignment": "from db.models.identity import StationUser",
    # ... add all mappings
}

def fix_imports(file_path):
    with open(file_path, 'r') as f:
        content = f.read()

    modified = False
    for old, new in IMPORT_MAP.items():
        if old in content:
            content = content.replace(old, new)
            modified = True

    if modified:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✅ Fixed: {file_path}")

# Run on all .py files
backend_src = Path("apps/backend/src")
for py_file in backend_src.rglob("*.py"):
    fix_imports(py_file)
```

---

### **Phase 5: TESTING & VALIDATION (4-8 hours)**

#### **5.1 Test Database Schema Alignment**

```bash
# Run schema check
cd apps/backend
python check_schema.py

# Verify all tables exist
# Verify all relationships work
```

---

#### **5.2 Test Import Changes**

```python
# Test all critical imports
from db.models.core import Booking, Customer
from db.models.identity import User, Station, StationUser, Role, Permission
from db.models.lead import Lead, BusinessSocialAccount, CustomerSocialIdentity
from db.models.newsletter import Campaign, Subscriber
from db.models.feedback_marketing import CustomerReview, DiscountCoupon
from db.models.support_communications import Escalation, CallRecording

# All should import without errors
```

---

#### **5.3 Run Backend**

```bash
cd apps/backend
python -m uvicorn main:app --reload --port 8003 --app-dir src

# Should start without SQLAlchemy mapper errors
# No "duplicate mapper" warnings
# No "table not found" errors
```

---

#### **5.4 Run Tests**

```bash
# Unit tests
pytest tests/

# Integration tests
pytest tests/integration/

# API tests
pytest tests/api/
```

---

## 📊 MIGRATION SUMMARY

### **Database Migrations to Create:**

1. ✅ `rename_social_account_tables.py` - OAuth vs Business vs
   Customer social
2. ✅ `rename_review_tables.py` - Blog vs Event reviews
3. ✅ `rename_message_tables.py` - Customer support vs Email vs AI
4. ✅ `rename_social_thread_tables.py` - Lead social threads

### **Files to Deprecate:**

- `core/auth/station_models.py` (use `db/models/identity.py`)
- `core/auth/models.py` StationUser class (non-existent table)
- `models/booking.py` → `db/models/core.py`
- `models/customer.py` → `db/models/core.py`
- `models/lead.py` → `db/models/lead.py`
- `models/newsletter.py` → `db/models/newsletter.py`
- `models/escalation.py` → `db/models/support_communications.py`
- `models/call_recording.py` → `db/models/support_communications.py`
- `models/role.py` → `db/models/identity.py`
- `models/social.py` (most models) → various `db/models/`

### **Import Changes Required:**

- **Estimated files to update:** 150-200 Python files
- **Automated script:** `fix_imports.py`
- **Manual review:** Critical business logic files

---

## ⏱️ TIME ESTIMATES

| Phase     | Task                         | Time            | Priority    |
| --------- | ---------------------------- | --------------- | ----------- |
| 1         | Deprecate auth models        | 1-2h            | 🔴 Critical |
| 1         | Merge Booking/Customer       | 1-2h            | 🔴 Critical |
| 2         | Rename social account tables | 2-3h            | 🟠 High     |
| 2         | Rename review tables         | 1h              | 🟠 High     |
| 2         | Rename message tables        | 1-2h            | 🟠 High     |
| 3         | Move deprecated models       | 1h              | 🟡 Medium   |
| 4         | Update imports (automated)   | 2-3h            | 🔴 Critical |
| 4         | Manual review                | 2-3h            | 🟠 High     |
| 5         | Testing & validation         | 4-8h            | 🔴 Critical |
| **TOTAL** |                              | **15-25 hours** |             |

---

## 🚦 EXECUTION ORDER

### **Step 1: Deprecate Auth Duplicates** (IMMEDIATE)

- Add deprecation warnings
- Update critical imports
- Test backend starts

### **Step 2: Create Migrations** (NEXT)

- Create all 4 rename migrations
- Test on staging database
- Document changes

### **Step 3: Update Imports** (BULK)

- Run automated script
- Manual review critical files
- Test incrementally

### **Step 4: Remove Deprecated** (FINAL)

- Move files to DEPRECATED/
- Add import shims (compatibility layer)
- Full regression testing

---

## ✅ SUCCESS CRITERIA

- [ ] Backend starts without SQLAlchemy mapper errors
- [ ] All table names match business logic
- [ ] No duplicate ORM models for same table
- [ ] All imports use `db/models/` canonical path
- [ ] Station auth system works (multi-tenant RBAC)
- [ ] Review systems work (blog + event reviews)
- [ ] Social account systems work (OAuth + Business + Customer)
- [ ] Message systems work (Customer + Email + AI)
- [ ] All tests pass
- [ ] Documentation updated

---

## 🎯 READY TO START?

**Confirm you're ready, then I'll begin with:**

1. ✅ **Phase 1.1:** Deprecate `core/auth/station_models.py`
2. ✅ **Phase 1.2:** Merge Booking/Customer models
3. ✅ **Phase 2.1:** Create social account table rename migration

**Or tell me which specific part to start with!**
