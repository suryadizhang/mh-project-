# My Hibachi – Data Dictionary

**Last Updated:** December 16, 2025 **Purpose:** Define every table
and field in the database **Database:** PostgreSQL 15

---

## 📋 Table of Contents

1. [Core Schema](#core-schema)
2. [CRM Schema](#crm-schema)
3. [Lead Schema](#lead-schema)
4. [Ops Schema](#ops-schema)
5. [Identity Schema](#identity-schema)
6. [Pricing Schema](#pricing-schema)
7. [AI Schema](#ai-schema)
8. [Audit Schema](#audit-schema)

---

## Core Schema

### `core.bookings`

Main booking/reservation table.

| Column                      | Type         | Nullable | Default           | Description                       |
| --------------------------- | ------------ | -------- | ----------------- | --------------------------------- |
| `id`                        | UUID         | NO       | gen_random_uuid() | Primary key                       |
| `customer_id`               | UUID         | NO       | -                 | FK to core.customers              |
| `chef_id`                   | UUID         | YES      | NULL              | FK to ops.chefs (assigned chef)   |
| `station_id`                | UUID         | NO       | -                 | FK to identity.stations           |
| `date`                      | DATE         | NO       | -                 | Event date                        |
| `slot`                      | TIME         | NO       | -                 | Event start time                  |
| `address_encrypted`         | TEXT         | NO       | -                 | Encrypted venue address           |
| `zone`                      | VARCHAR(50)  | NO       | -                 | Service zone (e.g., "fremont")    |
| `party_adults`              | INTEGER      | NO       | -                 | Number of adults (min 10)         |
| `party_kids`                | INTEGER      | NO       | -                 | Number of kids 5-12               |
| `deposit_due_cents`         | INTEGER      | NO       | -                 | Required deposit in cents         |
| `total_due_cents`           | INTEGER      | NO       | -                 | Total event cost in cents         |
| `status`                    | ENUM         | NO       | 'pending'         | Booking status                    |
| `source`                    | VARCHAR(50)  | NO       | -                 | Booking source (web, phone, etc.) |
| `sms_consent`               | BOOLEAN      | NO       | false             | TCPA SMS consent                  |
| `sms_consent_timestamp`     | TIMESTAMPTZ  | YES      | NULL              | When consent given                |
| `version`                   | INTEGER      | NO       | 1                 | Optimistic locking                |
| `customer_deposit_deadline` | TIMESTAMP    | YES      | NULL              | Customer-facing deadline          |
| `internal_deadline`         | TIMESTAMP    | YES      | NULL              | Internal cancellation deadline    |
| `deposit_confirmed_at`      | TIMESTAMP    | YES      | NULL              | Manual deposit confirmation       |
| `deposit_confirmed_by`      | VARCHAR(255) | YES      | NULL              | Who confirmed deposit             |
| `hold_on_request`           | BOOLEAN      | NO       | false             | Admin hold flag                   |
| `held_by`                   | VARCHAR(255) | YES      | NULL              | Who placed hold                   |
| `held_at`                   | TIMESTAMP    | YES      | NULL              | When hold placed                  |
| `hold_reason`               | TEXT         | YES      | NULL              | Reason for hold                   |
| `menu_items`                | JSONB        | YES      | NULL              | Selected menu items               |
| `special_requests`          | TEXT         | YES      | NULL              | Customer special requests         |
| `notes`                     | TEXT         | YES      | NULL              | Internal notes                    |
| `metadata`                  | JSONB        | YES      | NULL              | Additional metadata               |
| `deleted_at`                | TIMESTAMPTZ  | YES      | NULL              | Soft delete timestamp             |
| `created_at`                | TIMESTAMPTZ  | NO       | now()             | Record creation                   |
| `updated_at`                | TIMESTAMPTZ  | NO       | now()             | Last update                       |

**Indexes:**

- `idx_booking_date_slot_active` - Unique on (date, slot) where not
  cancelled
- `ix_core_bookings_status` - Status lookups
- `ix_core_bookings_customer_id` - Customer lookups
- `ix_core_bookings_chef_slot_unique` - Prevent chef double-booking

**Constraints:**

- `check_party_adults_positive` - party_adults > 0
- `check_party_kids_non_negative` - party_kids >= 0
- `check_deposit_non_negative` - deposit_due_cents >= 0
- `check_total_gte_deposit` - total_due_cents >= deposit_due_cents

---

### `core.customers`

Customer profiles.

| Column                  | Type         | Nullable | Default           | Description         |
| ----------------------- | ------------ | -------- | ----------------- | ------------------- |
| `id`                    | UUID         | NO       | gen_random_uuid() | Primary key         |
| `first_name`            | VARCHAR(100) | NO       | -                 | First name          |
| `last_name`             | VARCHAR(100) | NO       | -                 | Last name           |
| `email`                 | VARCHAR(255) | NO       | -                 | Email (unique)      |
| `phone`                 | VARCHAR(20)  | YES      | NULL              | Phone number        |
| `phone_verified`        | BOOLEAN      | NO       | false             | Phone verified      |
| `sms_consent`           | BOOLEAN      | NO       | false             | TCPA consent        |
| `sms_consent_timestamp` | TIMESTAMPTZ  | YES      | NULL              | Consent timestamp   |
| `booking_count`         | INTEGER      | NO       | 0                 | Total bookings      |
| `total_spend_cents`     | INTEGER      | NO       | 0                 | Lifetime spend      |
| `last_booking_date`     | DATE         | YES      | NULL              | Most recent booking |
| `notes`                 | TEXT         | YES      | NULL              | Internal notes      |
| `tags`                  | VARCHAR[]    | YES      | NULL              | Customer tags       |
| `metadata`              | JSONB        | YES      | NULL              | Additional data     |
| `deleted_at`            | TIMESTAMPTZ  | YES      | NULL              | Soft delete         |
| `created_at`            | TIMESTAMPTZ  | NO       | now()             | Created             |
| `updated_at`            | TIMESTAMPTZ  | NO       | now()             | Updated             |

**Indexes:**

- `uq_customers_email` - Unique email
- `ix_core_customers_phone` - Phone lookups

---

### `core.payments`

Payment transaction records.

| Column                     | Type         | Nullable | Default           | Description         |
| -------------------------- | ------------ | -------- | ----------------- | ------------------- |
| `id`                       | UUID         | NO       | gen_random_uuid() | Primary key         |
| `booking_id`               | UUID         | NO       | -                 | FK to core.bookings |
| `stripe_payment_intent_id` | VARCHAR(255) | YES      | NULL              | Stripe PI ID        |
| `stripe_charge_id`         | VARCHAR(255) | YES      | NULL              | Stripe charge ID    |
| `amount_cents`             | INTEGER      | NO       | -                 | Payment amount      |
| `currency`                 | VARCHAR(3)   | NO       | 'usd'             | Currency code       |
| `status`                   | ENUM         | NO       | 'pending'         | Payment status      |
| `payment_method`           | VARCHAR(50)  | YES      | NULL              | card, bank, etc.    |
| `receipt_url`              | TEXT         | YES      | NULL              | Stripe receipt URL  |
| `failure_reason`           | TEXT         | YES      | NULL              | If failed           |
| `refunded_at`              | TIMESTAMPTZ  | YES      | NULL              | Refund timestamp    |
| `refund_amount_cents`      | INTEGER      | YES      | NULL              | Refund amount       |
| `metadata`                 | JSONB        | YES      | NULL              | Additional data     |
| `created_at`               | TIMESTAMPTZ  | NO       | now()             | Created             |
| `updated_at`               | TIMESTAMPTZ  | NO       | now()             | Updated             |

---

## CRM Schema

### `crm.leads`

Lead/prospect tracking.

| Column              | Type         | Nullable | Default           | Description                   |
| ------------------- | ------------ | -------- | ----------------- | ----------------------------- |
| `id`                | UUID         | NO       | gen_random_uuid() | Primary key                   |
| `source`            | ENUM         | NO       | -                 | Lead source (WEB_QUOTE, etc.) |
| `status`            | ENUM         | NO       | 'new'             | Lead status                   |
| `quality`           | ENUM         | YES      | NULL              | hot/warm/cold                 |
| `score`             | NUMERIC(5,2) | NO       | 0                 | Lead score 0-100              |
| `assigned_to`       | VARCHAR(100) | YES      | NULL              | Assigned staff                |
| `customer_id`       | UUID         | YES      | NULL              | FK if converted               |
| `last_contact_date` | TIMESTAMPTZ  | YES      | NULL              | Last contact                  |
| `follow_up_date`    | TIMESTAMPTZ  | YES      | NULL              | Next follow-up                |
| `conversion_date`   | TIMESTAMPTZ  | YES      | NULL              | When converted                |
| `lost_reason`       | TEXT         | YES      | NULL              | Why lost                      |
| `utm_source`        | VARCHAR(100) | YES      | NULL              | UTM source                    |
| `utm_medium`        | VARCHAR(100) | YES      | NULL              | UTM medium                    |
| `utm_campaign`      | VARCHAR(100) | YES      | NULL              | UTM campaign                  |
| `deleted_at`        | TIMESTAMPTZ  | YES      | NULL              | Soft delete                   |
| `created_at`        | TIMESTAMPTZ  | NO       | now()             | Created                       |
| `updated_at`        | TIMESTAMPTZ  | NO       | now()             | Updated                       |

**Indexes:**

- `idx_crm_leads_status` - Status filtering
- `idx_crm_leads_source` - Source analytics
- `idx_crm_leads_score` - Score sorting
- `idx_crm_leads_followup` - Follow-up queue

**Constraints:**

- `check_lead_score_range` - score BETWEEN 0 AND 100

---

### `crm.campaigns`

Marketing campaign tracking.

| Column         | Type         | Nullable | Default           | Description       |
| -------------- | ------------ | -------- | ----------------- | ----------------- |
| `id`           | UUID         | NO       | gen_random_uuid() | Primary key       |
| `name`         | VARCHAR(200) | NO       | -                 | Campaign name     |
| `channel`      | ENUM         | NO       | -                 | EMAIL, SMS, etc.  |
| `status`       | ENUM         | NO       | 'draft'           | Campaign status   |
| `subject`      | VARCHAR(200) | YES      | NULL              | Email subject     |
| `content`      | JSONB        | NO       | -                 | Campaign content  |
| `scheduled_at` | TIMESTAMPTZ  | YES      | NULL              | Send time         |
| `sent_at`      | TIMESTAMPTZ  | YES      | NULL              | Actual send time  |
| `segment_id`   | UUID         | YES      | NULL              | Target segment    |
| `stats`        | JSONB        | YES      | NULL              | Performance stats |
| `created_at`   | TIMESTAMPTZ  | NO       | now()             | Created           |
| `updated_at`   | TIMESTAMPTZ  | NO       | now()             | Updated           |

---

## Lead Schema

### `lead.lead_contacts`

Multi-channel contact methods for leads.

| Column              | Type        | Nullable | Default           | Description      |
| ------------------- | ----------- | -------- | ----------------- | ---------------- |
| `id`                | UUID        | NO       | gen_random_uuid() | Primary key      |
| `lead_id`           | UUID        | NO       | -                 | FK to crm.leads  |
| `channel`           | ENUM        | NO       | -                 | SMS, EMAIL, etc. |
| `handle_or_address` | TEXT        | NO       | -                 | Contact value    |
| `verified`          | BOOLEAN     | NO       | false             | Is verified      |
| `created_at`        | TIMESTAMPTZ | NO       | now()             | Created          |

**Indexes:**

- `ix_lead_contacts_lead` - Lead lookups
- `ix_lead_contacts_channel` - Channel + handle lookups

---

### `lead.lead_context`

Event preferences captured with lead.

| Column                   | Type        | Nullable | Default | Description          |
| ------------------------ | ----------- | -------- | ------- | -------------------- |
| `id`                     | UUID        | NO       | -       | PK & FK to crm.leads |
| `party_size_adults`      | INTEGER     | YES      | NULL    | Preferred adults     |
| `party_size_kids`        | INTEGER     | YES      | NULL    | Preferred kids       |
| `estimated_budget_cents` | INTEGER     | YES      | NULL    | Budget in cents      |
| `event_date_pref`        | DATE        | YES      | NULL    | Preferred date       |
| `event_date_range_start` | DATE        | YES      | NULL    | Date range start     |
| `event_date_range_end`   | DATE        | YES      | NULL    | Date range end       |
| `zip_code`               | VARCHAR(10) | YES      | NULL    | Event zip code       |
| `service_type`           | VARCHAR(50) | YES      | NULL    | Service preference   |
| `notes`                  | TEXT        | YES      | NULL    | Additional notes     |

---

### `lead.lead_events`

Funnel event tracking (event sourcing).

| Column        | Type        | Nullable | Default           | Description     |
| ------------- | ----------- | -------- | ----------------- | --------------- |
| `id`          | UUID        | NO       | gen_random_uuid() | Primary key     |
| `lead_id`     | UUID        | NO       | -                 | FK to crm.leads |
| `event_type`  | VARCHAR(50) | NO       | -                 | Event type      |
| `payload`     | JSONB       | YES      | NULL              | Event data      |
| `occurred_at` | TIMESTAMPTZ | NO       | now()             | Event timestamp |

**Event Types:**

- `lead_created` - Initial lead capture
- `lead_updated` - Lead info changed
- `status_changed` - Status transition
- `funnel_checked_availability` - Checked dates
- `funnel_started_booking` - Clicked book
- `funnel_completed_booking` - Submitted form
- `funnel_dropped` - Abandoned

**Indexes:**

- `ix_lead_events_lead` - Lead + occurred_at

---

## Ops Schema

### `ops.chefs`

Hibachi chef records.

| Column       | Type         | Nullable | Default           | Description             |
| ------------ | ------------ | -------- | ----------------- | ----------------------- |
| `id`         | UUID         | NO       | gen_random_uuid() | Primary key             |
| `station_id` | UUID         | NO       | -                 | FK to identity.stations |
| `name`       | VARCHAR(100) | NO       | -                 | Chef display name       |
| `email`      | VARCHAR(255) | YES      | NULL              | Chef email              |
| `phone`      | VARCHAR(20)  | NO       | -                 | Chef phone              |
| `is_active`  | BOOLEAN      | NO       | true              | Available for work      |
| `rating`     | NUMERIC(2,1) | YES      | NULL              | Performance rating      |
| `hire_date`  | DATE         | YES      | NULL              | Start date              |
| `notes`      | TEXT         | YES      | NULL              | Internal notes          |
| `metadata`   | JSONB        | YES      | NULL              | Additional data         |
| `created_at` | TIMESTAMPTZ  | NO       | now()             | Created                 |
| `updated_at` | TIMESTAMPTZ  | NO       | now()             | Updated                 |

---

## Identity Schema

### `identity.stations`

Service location/station records.

| Column       | Type         | Nullable | Default               | Description        |
| ------------ | ------------ | -------- | --------------------- | ------------------ |
| `id`         | UUID         | NO       | gen_random_uuid()     | Primary key        |
| `name`       | VARCHAR(100) | NO       | -                     | Station name       |
| `address`    | TEXT         | NO       | -                     | Base address       |
| `city`       | VARCHAR(100) | NO       | -                     | City               |
| `state`      | VARCHAR(2)   | NO       | -                     | State code         |
| `zip_code`   | VARCHAR(10)  | NO       | -                     | ZIP code           |
| `phone`      | VARCHAR(20)  | YES      | NULL                  | Station phone      |
| `email`      | VARCHAR(255) | YES      | NULL                  | Station email      |
| `timezone`   | VARCHAR(50)  | NO       | 'America/Los_Angeles' | Timezone           |
| `is_active`  | BOOLEAN      | NO       | true                  | Accepting bookings |
| `created_at` | TIMESTAMPTZ  | NO       | now()                 | Created            |
| `updated_at` | TIMESTAMPTZ  | NO       | now()                 | Updated            |

---

### `identity.users`

System user accounts.

| Column          | Type         | Nullable | Default           | Description          |
| --------------- | ------------ | -------- | ----------------- | -------------------- |
| `id`            | UUID         | NO       | gen_random_uuid() | Primary key          |
| `email`         | VARCHAR(255) | NO       | -                 | Login email (unique) |
| `password_hash` | VARCHAR(255) | NO       | -                 | Hashed password      |
| `first_name`    | VARCHAR(100) | YES      | NULL              | First name           |
| `last_name`     | VARCHAR(100) | YES      | NULL              | Last name            |
| `is_active`     | BOOLEAN      | NO       | true              | Can login            |
| `is_verified`   | BOOLEAN      | NO       | false             | Email verified       |
| `last_login_at` | TIMESTAMPTZ  | YES      | NULL              | Last login           |
| `mfa_enabled`   | BOOLEAN      | NO       | false             | 2FA enabled          |
| `mfa_secret`    | VARCHAR(255) | YES      | NULL              | TOTP secret          |
| `created_at`    | TIMESTAMPTZ  | NO       | now()             | Created              |
| `updated_at`    | TIMESTAMPTZ  | NO       | now()             | Updated              |

---

### `identity.roles`

RBAC role definitions.

| Column        | Type        | Nullable | Default           | Description             |
| ------------- | ----------- | -------- | ----------------- | ----------------------- |
| `id`          | UUID        | NO       | gen_random_uuid() | Primary key             |
| `name`        | VARCHAR(50) | NO       | -                 | Role name (unique)      |
| `tier`        | INTEGER     | NO       | -                 | Permission tier 0-3     |
| `description` | TEXT        | YES      | NULL              | Role description        |
| `permissions` | JSONB       | NO       | '[]'              | Permission list         |
| `is_system`   | BOOLEAN     | NO       | false             | System role (no delete) |
| `created_at`  | TIMESTAMPTZ | NO       | now()             | Created                 |

**Default Roles:** | Name | Tier | Description |
|------|------|-------------| | guest | 0 | No login, public access |
| staff | 1 | Basic operations | | admin | 2 | Full operations | |
super_admin | 3 | System configuration |

---

## Pricing Schema

### `pricing.travel_fee_configuration`

Station-based travel fee rules.

| Column                 | Type         | Nullable | Default           | Description             |
| ---------------------- | ------------ | -------- | ----------------- | ----------------------- |
| `id`                   | UUID         | NO       | gen_random_uuid() | Primary key             |
| `station_id`           | UUID         | NO       | -                 | FK to identity.stations |
| `name`                 | VARCHAR(100) | NO       | -                 | Config name             |
| `free_miles`           | INTEGER      | NO       | 30                | Free miles included     |
| `price_per_mile_cents` | INTEGER      | NO       | 200               | Per-mile rate           |
| `is_active`            | BOOLEAN      | NO       | true              | Config active           |
| `created_at`           | TIMESTAMPTZ  | NO       | now()             | Created                 |
| `updated_at`           | TIMESTAMPTZ  | NO       | now()             | Updated                 |

---

### `pricing.menu_items`

Menu item definitions.

| Column          | Type         | Nullable | Default           | Description             |
| --------------- | ------------ | -------- | ----------------- | ----------------------- |
| `id`            | UUID         | NO       | gen_random_uuid() | Primary key             |
| `name`          | VARCHAR(100) | NO       | -                 | Item name               |
| `category`      | ENUM         | NO       | -                 | APPETIZER, ENTREE, etc. |
| `description`   | TEXT         | YES      | NULL              | Item description        |
| `price_cents`   | INTEGER      | NO       | -                 | Price in cents          |
| `is_active`     | BOOLEAN      | NO       | true              | Available               |
| `display_order` | INTEGER      | NO       | 0                 | Sort order              |
| `created_at`    | TIMESTAMPTZ  | NO       | now()             | Created                 |

---

### `pricing.addon_items`

Premium upgrade items.

| Column                   | Type         | Nullable | Default           | Description      |
| ------------------------ | ------------ | -------- | ----------------- | ---------------- |
| `id`                     | UUID         | NO       | gen_random_uuid() | Primary key      |
| `name`                   | VARCHAR(100) | NO       | -                 | Addon name       |
| `description`            | TEXT         | YES      | NULL              | Description      |
| `price_per_person_cents` | INTEGER      | NO       | -                 | Per-person price |
| `is_active`              | BOOLEAN      | NO       | true              | Available        |
| `created_at`             | TIMESTAMPTZ  | NO       | now()             | Created          |

**Current Addons:** | Name | Price/Person | |------|--------------| |
Filet Mignon | $15 | | Lobster Tail | $25 |

---

## Enums Reference

### Booking Status

```sql
CREATE TYPE booking_status AS ENUM (
  'pending', 'deposit_pending', 'deposit_paid',
  'confirmed', 'in_progress', 'completed',
  'cancelled', 'no_show'
);
```

### Lead Source

```sql
CREATE TYPE lead_source AS ENUM (
  'WEB_QUOTE', 'WEB_CONTACT', 'CHAT', 'PHONE', 'SMS',
  'INSTAGRAM', 'FACEBOOK', 'GOOGLE', 'YELP', 'REFERRAL', 'EVENT'
);
```

### Lead Status

```sql
CREATE TYPE lead_status AS ENUM (
  'new', 'contacted', 'qualified', 'negotiating', 'converted', 'lost'
);
```

### Lead Quality

```sql
CREATE TYPE lead_quality AS ENUM ('hot', 'warm', 'cold');
```

### Contact Channel

```sql
CREATE TYPE contact_channel AS ENUM (
  'EMAIL', 'SMS', 'INSTAGRAM', 'FACEBOOK', 'GOOGLE', 'YELP', 'WEB'
);
```

---

## 🔗 Related Documents

- [ERD](../01-ARCHITECTURE/ERD.md) - Visual relationships
- [Glossary](../00-ONBOARDING/GLOSSARY.md) - Business terms
- [API Contracts](../01-ARCHITECTURE/API_CONTRACTS.md) - API specs
