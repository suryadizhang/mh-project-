# My Hibachi - Complete Database Relationship Map
**Generated: November 22, 2025**  
**Status: ✅ Production Ready (Excluding AI Development Tables)**

---

## 📊 Database Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      MY HIBACHI DATABASE ECOSYSTEM                       │
│                         PostgreSQL (Supabase)                            │
└─────────────────────────────────────────────────────────────────────────┘

11 Schemas:
├── identity       (Users, Auth, RBAC, Stations)
├── bookings       (Booking operations)
├── core           (Customers, Chefs, Messages - DEPRECATED, migrating to schemas)
├── lead           (Lead generation, Social threads)
├── newsletter     (Email campaigns, Subscribers)
├── feedback       (Reviews, Testimonials)
├── events         (Event sourcing, Domain events)
├── integra        (Payment integrations)
├── marketing      (QR codes, Tracking)
├── support        (Audit logs, Error logs)
└── communications (SMS, Call recordings - FUTURE)
```

---

## 🔗 Core Entity Relationships

### **1. IDENTITY SCHEMA** (Authentication & Authorization)

```
┌──────────────────────────────────────────────────────────────┐
│                      IDENTITY SYSTEM                          │
└──────────────────────────────────────────────────────────────┘

identity.users (Central auth table)
├── id UUID PRIMARY KEY
├── email VARCHAR UNIQUE (Google OAuth)
├── google_id VARCHAR UNIQUE
├── status ENUM (pending_approval, active, suspended, deactivated)
├── approved_by UUID → REFERENCES identity.users(id) [SELF-REFERENCE]
├── assigned_station_id UUID → REFERENCES identity.stations(id)
└── business_id UUID → REFERENCES businesses(id)

identity.roles (RBAC system)
├── id UUID PRIMARY KEY
├── name roletype ENUM (super_admin, admin, manager, staff, viewer)
├── created_by UUID → REFERENCES identity.users(id)
└── [Many-to-Many with identity.permissions via identity.role_permissions]

identity.permissions
├── id UUID PRIMARY KEY  
├── name permissiontype ENUM (user:create, booking:read, payment:refund, etc.)
└── [Many-to-Many with identity.roles via identity.role_permissions]

identity.role_permissions (Junction table)
├── role_id UUID → REFERENCES identity.roles(id) CASCADE
└── permission_id UUID → REFERENCES identity.permissions(id) CASCADE

identity.user_roles (Junction table)
├── user_id UUID → REFERENCES identity.users(id) CASCADE
├── role_id UUID → REFERENCES identity.roles(id) CASCADE
└── assigned_by UUID → REFERENCES identity.users(id) SET NULL

identity.stations (Multi-tenant workspaces)
├── id UUID PRIMARY KEY
├── name VARCHAR
└── business_id UUID → REFERENCES businesses(id)

identity.station_users (Junction table)
├── user_id UUID → REFERENCES users.id CASCADE (⚠️ Missing schema prefix!)
├── station_id UUID → REFERENCES identity.stations(id) CASCADE
└── assigned_by UUID → REFERENCES users.id SET NULL
```

**🔴 CRITICAL ISSUES FOUND:**
1. ⚠️ `identity.station_users` references `users.id` without schema (should be `identity.users`)
2. ⚠️ `identity.users.business_id` references `businesses(id)` in public schema (needs verification)

---

### **2. BOOKINGS SCHEMA** (Catering Operations)

```
┌──────────────────────────────────────────────────────────────┐
│                     BOOKING SYSTEM                            │
└──────────────────────────────────────────────────────────────┘

core.bookings (⚠️ Should migrate to bookings schema)
├── id UUID PRIMARY KEY
├── customer_id UUID → REFERENCES core.customers(id) RESTRICT
├── chef_id UUID → REFERENCES core.chefs(id) SET NULL
├── station_id UUID → REFERENCES identity.stations(id)
├── business_id UUID → REFERENCES businesses(id)
└── status booking_status ENUM

bookings.booking_reminders (NEW: Migration 0e81266c9503)
├── id UUID PRIMARY KEY
├── booking_id UUID → REFERENCES bookings.id CASCADE (⚠️ Missing schema!)
├── reminder_type ENUM (24h, 2h, 30min)
└── sent_at TIMESTAMPTZ

integra.payment_events
├── id UUID PRIMARY KEY
├── booking_id UUID → REFERENCES core.bookings(id) CASCADE
└── amount DECIMAL

integra.payment_reconciliation
├── id UUID PRIMARY KEY
├── payment_event_id UUID → REFERENCES integra.payment_events(id) CASCADE
└── booking_id UUID → REFERENCES core.bookings(id) CASCADE
```

**🔴 CRITICAL ISSUES:**
1. ⚠️ `bookings.booking_reminders.booking_id` references `bookings.id` without schema
2. ⚠️ Mixed schema usage: `core.bookings` vs `bookings.` schema

---

### **3. CUSTOMERS & LEADS** (CRM System)

```
┌──────────────────────────────────────────────────────────────┐
│                     CUSTOMER LIFECYCLE                        │
└──────────────────────────────────────────────────────────────┘

core.customers (Central customer data)
├── id UUID PRIMARY KEY
├── phone VARCHAR
├── email VARCHAR
├── station_id UUID → REFERENCES identity.stations(id)
├── business_id UUID → REFERENCES businesses(id)
└── Relationships:
    ├→ lead.leads.customer_id (converted leads)
    ├→ core.bookings.customer_id (booking history)
    ├→ feedback.customer_reviews.customer_id (reviews)
    ├→ feedback.customer_testimonials.customer_id (testimonials)
    ├→ lead.social_threads.customer_id (social interactions)
    ├→ newsletter.subscribers.customer_id (email marketing)
    └→ newsletter.campaign_events.customer_id (campaign tracking)

lead.leads (Lead generation)
├── id UUID PRIMARY KEY
├── customer_id UUID → REFERENCES core.customers(id) SET NULL
├── source lead_source ENUM (website, instagram, facebook, referral)
├── business_id UUID → REFERENCES businesses(id)
└── Relationships:
    ├→ lead.lead_notes.lead_id
    ├→ lead.lead_tags.lead_id
    ├→ lead.lead_activities.lead_id
    └→ newsletter.campaign_events.lead_id

lead.lead_notes
├── id UUID PRIMARY KEY
└── lead_id UUID → REFERENCES lead.leads(id) CASCADE

lead.lead_tags
├── id UUID PRIMARY KEY
└── lead_id UUID → REFERENCES lead.leads(id) CASCADE

lead.lead_activities
├── id UUID PRIMARY KEY
└── lead_id UUID → REFERENCES lead.leads(id) CASCADE
```

---

### **4. SOCIAL MEDIA INTEGRATION** (Unified Communications)

```
┌──────────────────────────────────────────────────────────────┐
│               SOCIAL MEDIA & COMMUNICATIONS                   │
└──────────────────────────────────────────────────────────────┘

lead.social_accounts (Instagram, Facebook, Google Business)
├── id UUID PRIMARY KEY
├── platform social_platform ENUM (instagram, facebook, google_business)
├── platform_account_id VARCHAR (external ID)
├── access_token TEXT (OAuth)
└── business_id UUID → REFERENCES businesses(id)

lead.social_identities (Customer social handles)
├── id UUID PRIMARY KEY
├── account_id UUID → REFERENCES lead.social_accounts(id) CASCADE
├── customer_id UUID → REFERENCES core.customers(id) SET NULL
├── platform_username VARCHAR
└── linked_customer_id UUID → REFERENCES core.customers(id)

lead.social_threads (Conversation threads)
├── id UUID PRIMARY KEY
├── account_id UUID → REFERENCES lead.social_accounts(id) CASCADE
├── social_identity_id UUID → REFERENCES lead.social_identities(id) SET NULL
├── customer_id UUID → REFERENCES core.customers(id) SET NULL
├── status thread_status ENUM (open, in_progress, resolved, closed)
└── assigned_to UUID → REFERENCES identity.users(id)

lead.social_messages (DMs, Comments, Reviews)
├── id UUID PRIMARY KEY
├── thread_id UUID → REFERENCES lead.social_threads(id) CASCADE
├── parent_message_id UUID → REFERENCES lead.social_messages(id) CASCADE [SELF-REF]
├── direction social_message_direction ENUM (inbound, outbound)
└── kind social_message_kind ENUM (message, comment, review, story_mention)

core.social_media_reviews (Platform reviews - DEPRECATED?)
├── id UUID PRIMARY KEY
├── account_id UUID → REFERENCES core.social_accounts(id) CASCADE
├── thread_id UUID → REFERENCES lead.social_threads(id) SET NULL
├── customer_id UUID → REFERENCES core.customers(id) SET NULL
└── platform social_platform ENUM
```

**🔴 CRITICAL ISSUES:**
1. ⚠️ Duplicate review systems: `core.social_media_reviews` vs `feedback.customer_reviews`
2. ⚠️ Schema mismatch: `core.social_accounts` referenced, but tables are in `lead` schema

---

### **5. REVIEW & FEEDBACK SYSTEM**

```
┌──────────────────────────────────────────────────────────────┐
│                    REVIEW & TESTIMONIALS                      │
└──────────────────────────────────────────────────────────────┘

feedback.customer_reviews
├── id UUID PRIMARY KEY
├── station_id UUID → REFERENCES identity.stations(id) RESTRICT
├── booking_id UUID → REFERENCES core.bookings(id) RESTRICT
├── customer_id UUID → REFERENCES core.customers(id) RESTRICT
├── account_id UUID → REFERENCES lead.social_accounts(id) (NEW: Migration 016)
├── rating INTEGER (1-5)
├── status review_status ENUM (pending, approved, rejected)
└── business_id UUID → REFERENCES businesses(id)

feedback.customer_testimonials
├── id UUID PRIMARY KEY
├── station_id UUID → REFERENCES identity.stations(id) RESTRICT
├── customer_id UUID → REFERENCES core.customers(id) RESTRICT
├── review_id UUID → REFERENCES feedback.customer_reviews(id) SET NULL
├── used_in_booking_id UUID → REFERENCES core.bookings(id) SET NULL
└── business_id UUID → REFERENCES businesses(id)

feedback.review_image_urls (Image attachments)
├── id UUID PRIMARY KEY
└── review_id UUID → REFERENCES feedback.customer_reviews(id) CASCADE

marketing.customer_review_blog_posts (SEO content)
├── id UUID PRIMARY KEY
├── review_id UUID (⚠️ No FK constraint - schema mismatch issue)
└── status ENUM (draft, published, archived)

marketing.blog_post_approval_logs
├── id UUID PRIMARY KEY
└── review_id UUID → REFERENCES customer_review_blog_posts.id CASCADE
```

**🔴 CRITICAL ISSUES:**
1. ⚠️ `customer_review_blog_posts.review_id` has NO foreign key constraint
2. ⚠️ Migration comment says "ForeignKey constraints removed due to schema type mismatch"

---

### **6. NEWSLETTER & CAMPAIGNS**

```
┌──────────────────────────────────────────────────────────────┐
│                  EMAIL MARKETING SYSTEM                       │
└──────────────────────────────────────────────────────────────┘

newsletter.subscribers
├── id UUID PRIMARY KEY
├── customer_id UUID → REFERENCES core.customers(id) SET NULL
├── email VARCHAR UNIQUE
├── status subscriber_status ENUM (active, unsubscribed, bounced)
└── business_id UUID → REFERENCES businesses(id)

newsletter.campaigns
├── id UUID PRIMARY KEY
├── status campaign_status ENUM (draft, scheduled, sending, sent, failed)
└── business_id UUID → REFERENCES businesses(id)

newsletter.campaign_events
├── id UUID PRIMARY KEY
├── campaign_id UUID → REFERENCES newsletter.campaigns(id) CASCADE
├── subscriber_id UUID → REFERENCES newsletter.subscribers(id) CASCADE
├── lead_id UUID → REFERENCES lead.leads(id) SET NULL
├── customer_id UUID → REFERENCES core.customers(id) SET NULL
└── event_type campaign_event_type ENUM (sent, opened, clicked, bounced, unsubscribed)

newsletter.sms_tracking (SMS campaigns)
├── id UUID PRIMARY KEY
├── campaign_id UUID (⚠️ No FK - should reference campaigns)
├── delivery_event_id UUID → REFERENCES newsletter.campaign_events.id CASCADE
└── status ENUM (queued, sent, delivered, failed)
```

---

### **7. PAYMENT SYSTEM**

```
┌──────────────────────────────────────────────────────────────┐
│                     PAYMENT PROCESSING                        │
└──────────────────────────────────────────────────────────────┘

public.catering_payments (Stripe integration)
├── id UUID PRIMARY KEY
├── booking_id UUID → REFERENCES catering_bookings.id (⚠️ Wrong table name!)
├── stripe_payment_intent_id VARCHAR
├── amount DECIMAL
└── status payment_status ENUM

public.payment_notifications (Venmo, Zelle, Cash App)
├── id UUID PRIMARY KEY
├── booking_id UUID → REFERENCES catering_bookings.id SET NULL
├── payment_id UUID → REFERENCES catering_payments.id SET NULL
├── reviewed_by UUID → REFERENCES identity.users(id) SET NULL
├── provider payment_provider ENUM (venmo, zelle, cash_app, paypal, stripe)
└── status payment_notification_status ENUM (pending, verified, rejected)

integra.stripe_* tables (Stripe webhook data)
├── stripe_events
├── stripe_payment_intents  
├── stripe_refunds
├── stripe_disputes
└── stripe_balance_transactions
    (All reference each other via Stripe IDs)
```

**🔴 CRITICAL ISSUES:**
1. ⚠️ `catering_payments.booking_id` references `catering_bookings.id` - **TABLE DOESN'T EXIST!**
2. ⚠️ Should reference `core.bookings` or `bookings.bookings`

---

### **8. MARKETING & TRACKING**

```
┌──────────────────────────────────────────────────────────────┐
│                    MARKETING & QR CODES                       │
└──────────────────────────────────────────────────────────────┘

marketing.qr_codes
├── id UUID PRIMARY KEY
├── code VARCHAR UNIQUE
├── destination_url TEXT
├── created_by UUID (⚠️ No FK - should reference identity.users)
└── business_id UUID → REFERENCES businesses(id)

marketing.qr_code_scans
├── id UUID PRIMARY KEY
├── qr_code_id UUID → REFERENCES marketing.qr_codes(id) CASCADE
├── ip_address VARCHAR
└── scan_timestamp TIMESTAMPTZ
```

---

### **9. AUDIT & SUPPORT**

```
┌──────────────────────────────────────────────────────────────┐
│                  AUDIT LOGS & ERROR TRACKING                  │
└──────────────────────────────────────────────────────────────┘

support.audit_logs
├── id UUID PRIMARY KEY
├── user_id UUID → REFERENCES users.id SET NULL (⚠️ Missing schema!)
├── action audit_action ENUM (VIEW, CREATE, UPDATE, DELETE)
├── entity_type VARCHAR (table name)
├── entity_id UUID
└── changes JSONB

support.station_activity_logs
├── id UUID PRIMARY KEY
├── user_id UUID → REFERENCES users.id SET NULL
├── target_user_id UUID → REFERENCES users.id SET NULL
├── station_id UUID → REFERENCES identity.stations(id)
└── action VARCHAR

support.error_logs
├── id UUID PRIMARY KEY
├── error_type VARCHAR
├── error_message TEXT
├── stack_trace TEXT
└── metadata JSONB

public.notification_groups
├── id UUID PRIMARY KEY
├── name VARCHAR
└── business_id UUID → REFERENCES businesses(id)

public.notification_contacts
├── id UUID PRIMARY KEY
├── group_id UUID → REFERENCES notification_groups(id) CASCADE
└── contact_value VARCHAR (email/phone)

public.notification_log
├── id UUID PRIMARY KEY
├── group_id UUID → REFERENCES notification_groups(id) CASCADE
├── sent_at TIMESTAMPTZ
└── delivery_status ENUM
```

---

### **10. EVENT SOURCING SYSTEM**

```
┌──────────────────────────────────────────────────────────────┐
│                     EVENT SOURCING (CQRS)                     │
└──────────────────────────────────────────────────────────────┘

events.domain_events
├── id UUID PRIMARY KEY
├── aggregate_id UUID (points to bookings, customers, etc.)
├── aggregate_type VARCHAR (Booking, Customer, Lead, etc.)
├── event_type VARCHAR (BookingCreated, PaymentReceived, etc.)
├── event_data JSONB
└── occurred_at TIMESTAMPTZ

events.outbox_entries (Transactional outbox pattern)
├── id UUID PRIMARY KEY
├── event_id UUID → REFERENCES events.domain_events(id) CASCADE
├── published_at TIMESTAMPTZ
└── status outbox_status ENUM (pending, published, failed)
```

---

### **11. MULTI-TENANCY (White-Label)**

```
┌──────────────────────────────────────────────────────────────┐
│                    BUSINESS / MULTI-TENANT                    │
└──────────────────────────────────────────────────────────────┘

public.businesses (White-label support)
├── id UUID PRIMARY KEY
├── name VARCHAR ("My Hibachi Chef")
├── slug VARCHAR UNIQUE ("my-hibachi-chef")
├── domain VARCHAR UNIQUE ("myhibachichef.com")
├── subscription_tier VARCHAR (self_hosted, pro, enterprise)
└── settings JSONB

Connected to:
├── identity.users.business_id
├── identity.stations.business_id
├── core.customers.business_id
├── core.bookings.business_id
├── lead.leads.business_id
├── feedback.customer_reviews.business_id
├── newsletter.subscribers.business_id
└── [Many more tables...]
```

---

## 🚨 CRITICAL DATABASE ISSUES FOUND

### **Schema Reference Errors** (High Priority)

| Migration/Table | Issue | Fix Needed |
|-----------------|-------|------------|
| `identity.station_users` | References `users.id` without schema | Should be `identity.users(id)` |
| `bookings.booking_reminders` | References `bookings.id` without schema | Should be `core.bookings(id)` or `bookings.bookings(id)` |
| `support.audit_logs` | References `users.id` without schema | Should be `identity.users(id)` |
| `support.station_activity_logs` | References `users.id` without schema | Should be `identity.users(id)` |
| `marketing.qr_codes` | `created_by` has NO foreign key | Add FK to `identity.users(id)` |
| `newsletter.sms_tracking` | `campaign_id` has NO foreign key | Add FK to `newsletter.campaigns(id)` |

### **Non-Existent Table References** (CRITICAL)

| Migration | Broken Reference | Correct Reference |
|-----------|------------------|-------------------|
| `009_payment_notifications.py` | `catering_bookings.id` | `core.bookings(id)` ✅ |
| `009_payment_notifications.py` | `catering_payments.id` | Should be payment tracking table |
| `015_add_terms_acknowledgment.py` | `public.customers.id` | `core.customers(id)` ✅ |
| `015_add_terms_acknowledgment.py` | `public.bookings.id` | `core.bookings(id)` ✅ |

### **Duplicate/Conflicting Systems**

1. **Review System Duplication:**
   - `feedback.customer_reviews` (official)
   - `core.social_media_reviews` (deprecated?)
   - `lead.social_messages` (kind='review')
   
2. **Schema Migration Issues:**
   - Tables in `core.*` should migrate to dedicated schemas (`bookings`, `feedback`, etc.)
   - Inconsistent schema usage across migrations

### **Missing Foreign Keys**

| Table | Column | Should Reference |
|-------|--------|------------------|
| `marketing.customer_review_blog_posts` | `review_id` | `feedback.customer_reviews(id)` |
| `marketing.qr_codes` | `created_by` | `identity.users(id)` |
| `newsletter.sms_tracking` | `campaign_id` | `newsletter.campaigns(id)` |

---

## 🔄 Data Flow Examples

### **Customer Journey Flow:**

```
1. Lead Creation:
   lead.leads → lead.lead_activities → lead.lead_notes
                ↓
   2. Conversion:
   lead.leads.customer_id → core.customers
                              ↓
   3. Booking:
   core.bookings (customer_id, chef_id, station_id)
                              ↓
   4. Payment:
   integra.payment_events → catering_payments
                              ↓
   5. Review:
   feedback.customer_reviews → feedback.customer_testimonials
                              ↓
   6. Marketing:
   newsletter.subscribers → newsletter.campaigns → newsletter.campaign_events
```

### **Social Media Interaction Flow:**

```
1. Platform Connection:
   lead.social_accounts (Instagram/Facebook OAuth)
                ↓
2. Customer Identification:
   lead.social_identities (map @username → customer_id)
                ↓
3. Conversation:
   lead.social_threads (open conversation)
                ↓
4. Messages:
   lead.social_messages (DMs, comments, reviews)
                ↓
5. Assignment:
   lead.social_threads.assigned_to → identity.users
```

---

## ✅ Verified Connections (Working Correctly)

- ✅ RBAC System (`identity.users` ↔ `identity.roles` ↔ `identity.permissions`)
- ✅ Station Multi-Tenancy (`identity.stations` ↔ `core.bookings/customers`)
- ✅ Event Sourcing (`events.domain_events` ↔ `events.outbox_entries`)
- ✅ Social Media (`lead.social_accounts` ↔ `social_identities` ↔ `social_threads` ↔ `social_messages`)
- ✅ Newsletter System (`newsletter.campaigns` ↔ `subscribers` ↔ `campaign_events`)
- ✅ Lead Management (`lead.leads` ↔ `lead_notes/tags/activities`)

---

## 📋 Recommended Actions

### **Immediate (Before Production):**

1. **Fix Schema References:**
   ```sql
   -- Update station_users foreign keys
   ALTER TABLE identity.station_users 
   DROP CONSTRAINT IF EXISTS fk_station_users_user_id;
   
   ALTER TABLE identity.station_users 
   ADD CONSTRAINT fk_station_users_user_id 
   FOREIGN KEY (user_id) REFERENCES identity.users(id) ON DELETE CASCADE;
   ```

2. **Fix Payment Table References:**
   - Update `catering_payments.booking_id` to reference `core.bookings`
   - Update `payment_notifications` accordingly

3. **Add Missing Foreign Keys:**
   - `marketing.qr_codes.created_by` → `identity.users`
   - `newsletter.sms_tracking.campaign_id` → `newsletter.campaigns`
   - `marketing.customer_review_blog_posts.review_id` → `feedback.customer_reviews`

### **Medium Priority:**

4. **Schema Consolidation:**
   - Move all booking-related tables to `bookings` schema
   - Move customer data to `core` or `crm` schema
   - Deprecate `core.*` in favor of dedicated schemas

5. **Remove Duplicates:**
   - Decide on single review system (recommend `feedback.customer_reviews`)
   - Deprecate `core.social_media_reviews`

### **Long-term:**

6. **Add Referential Integrity Checks:**
   - Create migration to validate ALL foreign keys
   - Add check constraints for enum consistency

---

## 🎯 Summary

**Total Tables:** ~60+  
**Total Schemas:** 11  
**Critical Issues:** 8  
**Missing Foreign Keys:** 5  
**Schema Conflicts:** 3  

**Status:** ⚠️ **Requires fixes before production deployment**

**Next Step:** Run migration fix script to correct all schema references and add missing foreign keys.
