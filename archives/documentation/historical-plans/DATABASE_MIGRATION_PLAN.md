# Database Migration Plan - 76 Features

## 🎯 Migration Strategy

**Approach**: Incremental migrations per sprint  
**Tool**: Alembic (already configured)  
**Rollback Strategy**: Each migration reversible  
**Testing Strategy**: Test migrations on staging before production  

---

## 📋 Migration Dependencies & Conflicts

### Dependency Graph

```
Core Tables (Sprint 0-1):
  ├─ locations (Sprint 1)
  ├─ admin_users (Sprint 1)
  ├─ roles (Sprint 1)
  ├─ deposits (Sprint 1) → depends on bookings (exists)
  └─ booking_reminders (Sprint 1) → depends on bookings (exists)

Intermediate Tables (Sprint 2-5):
  ├─ loyalty_points (Sprint 2) → depends on customers, payments
  ├─ recurring_bookings (Sprint 2) → depends on bookings
  ├─ payment_history (Sprint 3) → depends on bookings, deposits
  ├─ customer_preferences (Sprint 3) → depends on customers
  └─ communication_templates (Sprint 4) → independent

Advanced Tables (Sprint 6-18):
  ├─ contact_lists (Sprint 6) → depends on customers
  ├─ opt_out_management (Sprint 6) → depends on customers
  ├─ customer_merge_log (Sprint 7) → depends on customers
  ├─ booking_waitlist (Sprint 7) → depends on bookings
  └─ ... (remaining 60+ tables)
```

### Identified Conflicts

#### ✅ NO CONFLICTS (Safe to proceed)
- **Multi-location vs Recurring Bookings**: No conflict (both add to `bookings` table)
- **Admin Users vs Admin Roles**: Designed to work together (junction table)
- **Loyalty Points vs Payment History**: Sequential dependency (payment_history first)

#### ⚠️ POTENTIAL CONFLICTS (Needs careful planning)
1. **Bookings Table Alterations**:
   - Sprint 1: Add `location_id` (multi-location)
   - Sprint 2: Add `recurrence_id` (recurring bookings)
   - Sprint 7: Add `waitlist_id` (waitlist)
   - Sprint 9: Add `group_id` (group reservations)
   - **Mitigation**: Single migration per sprint, sequential deployment

2. **Customers Table Alterations**:
   - Sprint 3: Add `preferences_json` (customer preferences)
   - Sprint 5: Add `export_history_json` (customer export)
   - Sprint 7: Add `merge_log_id` (customer merge tracking)
   - Sprint 9: Add `referral_code` (referral tracking)
   - **Mitigation**: Single migration per sprint, sequential deployment

3. **Payments/Deposits Tables**:
   - Sprint 1: Create `deposits` table (may already exist?)
   - Sprint 3: Create `payment_history` table
   - Sprint 5: Alter deposits for `payment_history_id` reference
   - Sprint 7: Add Plaid fields to `payment_methods` table
   - **Mitigation**: Check if `deposits` exists, if yes use ALTER instead of CREATE

---

## 🗂️ Migration Sequence (All 76 Features)

### Sprint 0: Infrastructure (Pre-Migration)
- [x] Set up feature flags
- [ ] Verify Alembic configuration
- [ ] Create migration template
- [ ] Test migration rollback procedure

---

### Sprint 1: Core P0 Features (4 migrations)

#### Migration 1.1: Create Locations Table
**Feature**: Multi-Location Support  
**Priority**: P0  
**Estimated Time**: 30 minutes  

```sql
-- Up Migration
CREATE TABLE locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    address_street VARCHAR(255) NOT NULL,
    address_city VARCHAR(100) NOT NULL,
    address_state VARCHAR(2) NOT NULL,
    address_zip VARCHAR(10) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(255),
    capacity INT DEFAULT 100,
    service_radius_miles DECIMAL(5,2) DEFAULT 30.0,
    base_travel_fee DECIMAL(10,2) DEFAULT 0.0,
    per_mile_fee DECIMAL(10,2) DEFAULT 2.0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_locations_active ON locations(is_active);
CREATE INDEX idx_locations_city_state ON locations(address_city, address_state);

-- Down Migration
DROP INDEX IF EXISTS idx_locations_city_state;
DROP INDEX IF EXISTS idx_locations_active;
DROP TABLE locations;
```

#### Migration 1.2: Alter Bookings Table for Locations
**Feature**: Multi-Location Support  
**Priority**: P0  
**Estimated Time**: 15 minutes  
**Depends On**: Migration 1.1  

```sql
-- Up Migration
ALTER TABLE bookings 
ADD COLUMN location_id UUID REFERENCES locations(id) ON DELETE SET NULL;

CREATE INDEX idx_bookings_location ON bookings(location_id);

-- Down Migration
DROP INDEX IF EXISTS idx_bookings_location;
ALTER TABLE bookings DROP COLUMN location_id;
```

#### Migration 1.3: Create Admin Users & Roles Tables
**Feature**: Admin User Management  
**Priority**: P0  
**Estimated Time**: 45 minutes  

```sql
-- Up Migration
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    permissions_json JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE admin_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE admin_user_roles (
    admin_user_id UUID REFERENCES admin_users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (admin_user_id, role_id)
);

CREATE INDEX idx_admin_users_email ON admin_users(email);
CREATE INDEX idx_admin_users_active ON admin_users(is_active);
CREATE INDEX idx_roles_name ON roles(name);

-- Insert default superuser role
INSERT INTO roles (name, description, permissions_json) 
VALUES ('superuser', 'Full system access', '["*"]');

-- Down Migration
DROP INDEX IF EXISTS idx_roles_name;
DROP INDEX IF EXISTS idx_admin_users_active;
DROP INDEX IF EXISTS idx_admin_users_email;
DROP TABLE admin_user_roles;
DROP TABLE admin_users;
DROP TABLE roles;
```

#### Migration 1.4: Create Booking Reminders Table
**Feature**: Booking Reminders  
**Priority**: P0  
**Estimated Time**: 30 minutes  

```sql
-- Up Migration
CREATE TABLE booking_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
    reminder_type VARCHAR(50) NOT NULL, -- 'email', 'sms', 'both'
    scheduled_for TIMESTAMP WITH TIME ZONE NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'sent', 'failed', 'cancelled'
    message TEXT,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_reminders_booking ON booking_reminders(booking_id);
CREATE INDEX idx_reminders_status ON booking_reminders(status);
CREATE INDEX idx_reminders_scheduled ON booking_reminders(scheduled_for) 
    WHERE status = 'pending';

-- Down Migration
DROP INDEX IF EXISTS idx_reminders_scheduled;
DROP INDEX IF EXISTS idx_reminders_status;
DROP INDEX IF EXISTS idx_reminders_booking;
DROP TABLE booking_reminders;
```

#### Migration 1.5: Create/Alter Deposits Table
**Feature**: Deposit CRUD API  
**Priority**: P0  
**Estimated Time**: 45 minutes  
**Action**: Check if table exists first  

```sql
-- Up Migration
-- Check if deposits table exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'deposits') THEN
        -- Create new table
        CREATE TABLE deposits (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            booking_id UUID NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
            amount DECIMAL(10,2) NOT NULL,
            currency VARCHAR(3) DEFAULT 'USD',
            status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'confirmed', 'failed', 'refunded', 'cancelled'
            stripe_payment_intent_id VARCHAR(255),
            stripe_payment_method_id VARCHAR(255),
            paid_at TIMESTAMP WITH TIME ZONE,
            refunded_at TIMESTAMP WITH TIME ZONE,
            cancelled_at TIMESTAMP WITH TIME ZONE,
            failure_reason TEXT,
            metadata_json JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        CREATE INDEX idx_deposits_booking ON deposits(booking_id);
        CREATE INDEX idx_deposits_status ON deposits(status);
        CREATE INDEX idx_deposits_stripe_intent ON deposits(stripe_payment_intent_id);
    ELSE
        -- Table exists, add missing columns if needed
        IF NOT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'deposits' AND column_name = 'metadata_json') THEN
            ALTER TABLE deposits ADD COLUMN metadata_json JSONB DEFAULT '{}';
        END IF;
        
        IF NOT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'deposits' AND column_name = 'stripe_payment_method_id') THEN
            ALTER TABLE deposits ADD COLUMN stripe_payment_method_id VARCHAR(255);
        END IF;
    END IF;
END $$;

-- Down Migration
DROP INDEX IF EXISTS idx_deposits_stripe_intent;
DROP INDEX IF EXISTS idx_deposits_status;
DROP INDEX IF EXISTS idx_deposits_booking;
DROP TABLE IF EXISTS deposits;
```

---

### Sprint 2: P0 Continued (3 migrations)

#### Migration 2.1: Create Loyalty Points Table
**Feature**: Loyalty Points System  
**Priority**: P0  
**Estimated Time**: 45 minutes  
**Depends On**: Migration 3.1 (payment_history) - **MOVE TO SPRINT 3 OR SIMPLIFY**  

```sql
-- Up Migration
CREATE TABLE loyalty_points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    points INT NOT NULL DEFAULT 0,
    points_earned INT DEFAULT 0,
    points_redeemed INT DEFAULT 0,
    tier VARCHAR(50) DEFAULT 'bronze', -- 'bronze', 'silver', 'gold', 'platinum'
    last_earned_at TIMESTAMP WITH TIME ZONE,
    last_redeemed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE loyalty_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    loyalty_points_id UUID NOT NULL REFERENCES loyalty_points(id) ON DELETE CASCADE,
    points_change INT NOT NULL, -- positive = earned, negative = redeemed
    reason VARCHAR(255) NOT NULL,
    booking_id UUID REFERENCES bookings(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_loyalty_customer ON loyalty_points(customer_id);
CREATE INDEX idx_loyalty_tier ON loyalty_points(tier);
CREATE INDEX idx_loyalty_trans_customer ON loyalty_transactions(customer_id);
CREATE INDEX idx_loyalty_trans_booking ON loyalty_transactions(booking_id);

-- Down Migration
DROP INDEX IF EXISTS idx_loyalty_trans_booking;
DROP INDEX IF EXISTS idx_loyalty_trans_customer;
DROP INDEX IF EXISTS idx_loyalty_tier;
DROP INDEX IF EXISTS idx_loyalty_customer;
DROP TABLE loyalty_transactions;
DROP TABLE loyalty_points;
```

#### Migration 2.2: Create Recurring Bookings Table
**Feature**: Recurring Bookings  
**Priority**: P0  
**Estimated Time**: 45 minutes  

```sql
-- Up Migration
CREATE TABLE recurring_bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    recurrence_pattern VARCHAR(50) NOT NULL, -- 'weekly', 'biweekly', 'monthly'
    start_date DATE NOT NULL,
    end_date DATE,
    max_occurrences INT,
    booking_template_json JSONB NOT NULL, -- stores booking details
    is_active BOOLEAN DEFAULT TRUE,
    created_bookings_count INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE bookings 
ADD COLUMN recurrence_id UUID REFERENCES recurring_bookings(id) ON DELETE SET NULL;

CREATE INDEX idx_recurring_customer ON recurring_bookings(customer_id);
CREATE INDEX idx_recurring_active ON recurring_bookings(is_active);
CREATE INDEX idx_bookings_recurrence ON bookings(recurrence_id);

-- Down Migration
DROP INDEX IF EXISTS idx_bookings_recurrence;
DROP INDEX IF EXISTS idx_recurring_active;
DROP INDEX IF EXISTS idx_recurring_customer;
ALTER TABLE bookings DROP COLUMN recurrence_id;
DROP TABLE recurring_bookings;
```

#### Migration 2.3: Create Admin Config Tables
**Feature**: Admin Config Management  
**Priority**: P0  
**Estimated Time**: 30 minutes  

```sql
-- Up Migration
CREATE TABLE admin_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_key VARCHAR(255) NOT NULL UNIQUE,
    config_value TEXT NOT NULL,
    value_type VARCHAR(50) NOT NULL, -- 'string', 'number', 'boolean', 'json'
    description TEXT,
    is_system BOOLEAN DEFAULT FALSE, -- prevents deletion
    updated_by_admin_id UUID REFERENCES admin_users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_admin_config_key ON admin_config(config_key);
CREATE INDEX idx_admin_config_system ON admin_config(is_system);

-- Down Migration
DROP INDEX IF EXISTS idx_admin_config_system;
DROP INDEX IF EXISTS idx_admin_config_key;
DROP TABLE admin_config;
```

---

### Sprint 3-18: Remaining Migrations (69 features)

**Note**: Detailed migrations for Sprints 3-18 follow the same pattern:
1. Review feature requirements from `FULL_IMPLEMENTATION_ROADMAP.md`
2. Create migration SQL (UP and DOWN)
3. Test on development database
4. Deploy to staging
5. Test thoroughly
6. Deploy to production
7. Monitor for issues

#### Sprint 3 Migrations (3 features):
- Migration 3.1: Create `payment_history` table (Payment History/Reports)
- Migration 3.2: Alter `customers` table, add `preferences_json` (Customer Preferences)
- Migration 3.3: Create `sms_templates`, `email_templates` tables (Direct SMS/Email)

#### Sprint 4 Migrations (1 feature):
- Migration 4.1: Create `audit_logs` table (Audit Logs)

#### Sprint 5 Migrations (5 features):
- Migration 5.1: Create `admin_booking_overrides` table
- Migration 5.2: Alter `customers` for export tracking
- Migration 5.3: Create `communication_templates` table
- Migration 5.4: Enhance `payment_history` with reports schema
- Migration 5.5: Create `admin_notifications` table

#### Sprints 6-18 Migrations (60 features):
*Full migration details in appendix below*

---

## 🔧 Alembic Configuration

### Current Setup Verification
```bash
# Check Alembic is configured
ls apps/backend/alembic.ini
ls apps/backend/alembic/env.py

# Check current database revision
cd apps/backend
alembic current

# Check migration history
alembic history
```

### Creating New Migrations
```bash
# Sprint 1 Example:
cd apps/backend

# Migration 1.1: Locations
alembic revision -m "create_locations_table"
# Edit the generated file with SQL above
alembic upgrade head

# Migration 1.2: Bookings location_id
alembic revision -m "alter_bookings_add_location_id"
# Edit, upgrade

# Migration 1.3: Admin users & roles
alembic revision -m "create_admin_users_and_roles_tables"
# Edit, upgrade

# Migration 1.4: Booking reminders
alembic revision -m "create_booking_reminders_table"
# Edit, upgrade

# Migration 1.5: Deposits
alembic revision -m "create_or_alter_deposits_table"
# Edit, upgrade
```

### Testing Migrations
```bash
# Test upgrade
alembic upgrade head

# Test downgrade (rollback)
alembic downgrade -1

# Test full rollback
alembic downgrade base

# Re-apply
alembic upgrade head
```

### Production Migration Workflow
```bash
# 1. Backup database
pg_dump myhibachi_prod > backup_before_sprint_X.sql

# 2. Apply migrations
alembic upgrade head

# 3. Verify data integrity
# Run data validation queries

# 4. If issues, rollback
alembic downgrade -1

# 5. Restore backup if needed
psql myhibachi_prod < backup_before_sprint_X.sql
```

---

## ⚠️ Migration Risks & Mitigation

### Risk 1: Data Loss During ALTER TABLE
**Severity**: 🔴 CRITICAL  
**Affected Migrations**: All ALTER TABLE operations  
**Mitigation**:
- Always backup before migration
- Test on staging with production-like data
- Use `ADD COLUMN` with DEFAULT values (no NULL for existing rows)
- Never `DROP COLUMN` without user confirmation

### Risk 2: Long-Running Migrations on Large Tables
**Severity**: 🟠 HIGH  
**Affected Tables**: `bookings`, `customers`, `payments`  
**Mitigation**:
- Create indexes CONCURRENTLY
- Add columns with DEFAULT USING for fast writes
- Schedule migrations during low-traffic windows
- Use `LOCK TIMEOUT` to prevent indefinite locks

```sql
-- Example: Safe index creation
CREATE INDEX CONCURRENTLY idx_bookings_location ON bookings(location_id);

-- Example: Fast column addition
ALTER TABLE bookings ADD COLUMN location_id UUID DEFAULT NULL;
-- Then update in batches
```

### Risk 3: Foreign Key Constraint Violations
**Severity**: 🟠 HIGH  
**Affected Migrations**: All FK additions  
**Mitigation**:
- Validate data before adding constraints
- Add constraints as `NOT VALID` first, then `VALIDATE`
- Clean up orphaned records before migration

```sql
-- Example: Safe FK addition
ALTER TABLE bookings ADD CONSTRAINT fk_bookings_location 
    FOREIGN KEY (location_id) REFERENCES locations(id) NOT VALID;
    
ALTER TABLE bookings VALIDATE CONSTRAINT fk_bookings_location;
```

### Risk 4: Circular Dependencies
**Severity**: 🟡 MEDIUM  
**Example**: loyalty_points ↔ payment_history  
**Mitigation**:
- Create tables without FKs first
- Add FKs in subsequent migration
- Document dependency order

---

## 📊 Migration Tracking

### Sprint 1 Migration Checklist
- [ ] Migration 1.1: Locations table created
- [ ] Migration 1.2: Bookings.location_id added
- [ ] Migration 1.3: Admin users/roles created
- [ ] Migration 1.4: Booking reminders created
- [ ] Migration 1.5: Deposits created/altered
- [ ] All migrations tested on development
- [ ] All migrations tested on staging
- [ ] All migrations rolled back successfully
- [ ] Production backup created
- [ ] Migrations applied to production
- [ ] Data integrity verified
- [ ] Feature flags enabled

### Migration Metrics
| Sprint | Migrations | Tables Created | Columns Added | Indexes Created | Time Taken |
|--------|------------|----------------|---------------|-----------------|------------|
| Sprint 1 | 5 | 6 | 5 | 15 | TBD |
| Sprint 2 | 3 | 5 | 2 | 10 | TBD |
| Sprint 3 | 3 | 3 | 1 | 8 | TBD |

---

## 📝 Appendix: Remaining Migrations (Sprints 6-18)

### Sprint 6 (2 features)
- `contact_lists` table
- `opt_out_management` table

### Sprint 7 (3 features)
- `customer_merge_log` table
- `payment_methods` (alter for Plaid)
- `booking_waitlist` table

### Sprint 8 (4 features)
- `admin_email_templates`, `admin_sms_templates` tables
- `payment_disputes` table
- `admin_api_keys` table
- `admin_rate_limits` table

### Sprint 9 (3 features)
- `communication_scheduling`, `communication_personalization` tables
- `group_reservations` table
- `customer_referrals` table

### Sprint 10 (6 features)
- `admin_db_maintenance_log` table
- `admin_backup_log` table
- `admin_security_events` table
- `admin_compliance_reports` table
- `admin_data_exports` table
- `admin_dashboard_widgets` table

### Sprints 11-14 (AI & ML features - 41 features)
*Most AI features use NoSQL/JSON storage, minimal DB migrations*
- `ai_voice_calls` table (call logs)
- `ai_embeddings` table (vector storage)
- `ml_training_jobs` table (job tracking)
- `ml_models` table (model registry)
- `ai_cache` table (response caching)
- `ai_cost_tracking` table (usage metrics)

### Sprints 15-18 (Advanced features - 8 features)
- `payment_subscriptions` table
- `payment_installments` table
- `customer_feedback_detailed` table
- `communication_ab_tests` table
- `communication_analytics` table

**Total New Tables**: ~50  
**Total Altered Tables**: ~10  
**Total Indexes**: ~150  

---

## ✅ Pre-Migration Checklist (Sprint 1)

Before running any migration:
- [ ] Alembic configured correctly
- [ ] Database connection tested
- [ ] Development database backed up
- [ ] Staging database backed up
- [ ] Production database backed up (when applicable)
- [ ] Migration SQL reviewed for safety
- [ ] Rollback SQL tested
- [ ] Data validation queries prepared
- [ ] Downtime window scheduled (if needed)
- [ ] Rollback plan documented
- [ ] Team notified (if applicable)

---

**Last Updated**: [Current Date]  
**Next Review**: Before Sprint 1 starts  
**Owner**: Development Team
