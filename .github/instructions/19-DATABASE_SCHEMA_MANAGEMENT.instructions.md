---
applyTo: '**'
---

# My Hibachi – Database Schema Management

**Priority: CRITICAL** – SQLAlchemy models MUST match production
database.

---

## 🔴 DATABASE ENVIRONMENT RULES (CRITICAL!)

**NEVER mix environments. NEVER use production for testing.**

| Environment    | Database               | Purpose                        | Can Write Test Data? |
| -------------- | ---------------------- | ------------------------------ | -------------------- |
| **Local Dev**  | `myhibachi_staging`    | Local dev via SSH tunnel       | ✅ YES               |
| **Staging**    | `myhibachi_staging`    | Testing, QA, migration testing | ✅ YES               |
| **Production** | `myhibachi_production` | Real customer data ONLY        | ❌ NEVER             |

**🚫 DEPRECATED:** Supabase and local SQLite are NO LONGER USED. Local
development now uses SSH tunnel to VPS staging database.

### Local Development Database Setup (SSH Tunnel)

**Why SSH Tunnel:**

- ✅ Real PostgreSQL 13.22 (matches VPS production)
- ✅ Same schema as production
- ✅ No DNS resolution issues (Supabase DNS was failing)
- ✅ No SQLite/PostgreSQL compatibility issues
- ✅ Test data stays on staging (never production)

**Before running tests or dev server, start the SSH tunnel:**

```powershell
# Option 1: Use helper script (RECOMMENDED)
.\scripts\start-db-tunnel.ps1

# Option 2: Manual command
ssh -f -N -L 5433:localhost:5432 root@108.175.12.154
```

**Local .env Configuration:**

```dotenv
# Get <STAGING_DB_PASSWORD> from team lead or secure password manager
DATABASE_URL=postgresql+asyncpg://myhibachi_staging_user:<STAGING_DB_PASSWORD>@127.0.0.1:5433/myhibachi_staging
DATABASE_URL_SYNC=postgresql+psycopg2://myhibachi_staging_user:<STAGING_DB_PASSWORD>@127.0.0.1:5433/myhibachi_staging
```

### The Golden Rules:

1. **Production database = REAL CUSTOMER DATA ONLY**
   - Never insert test bookings
   - Never create fake customers
   - Never run destructive tests

2. **All testing happens on staging**
   - API integration tests → staging (local via SSH tunnel or on VPS)
   - Migration testing → staging first
   - Load testing → staging
   - New feature testing → staging

3. **48-hour staging rule**
   - All migrations run on staging for 48+ hours before production
   - Monitor for errors before production deployment

### Quick Environment Check:

```bash
# Check which database you're connected to
psql -c "SELECT current_database();"

# Production should show: myhibachi_production
# Staging should show: myhibachi_staging
```

### Environment Connection Strings:

```bash
# Local Development (via SSH tunnel - port 5433)
# Get <STAGING_DB_PASSWORD> from team lead
DATABASE_URL=postgresql+asyncpg://myhibachi_staging_user:<STAGING_DB_PASSWORD>@127.0.0.1:5433/myhibachi_staging

# Staging on VPS (direct - port 5432)
DATABASE_URL=postgresql+asyncpg://myhibachi_staging_user:<STAGING_DB_PASSWORD>@localhost:5432/myhibachi_staging

# Production (REAL DATA ONLY - port 5432)
DATABASE_URL=postgresql+asyncpg://myhibachi_user:<PROD_DB_PASSWORD>@localhost:5432/myhibachi_production
```

---

## 🔴 THE ROOT CAUSE (LEARN FROM THIS!)

**Problem:** SQLAlchemy models can define columns that don't exist in
production. The app runs fine locally (with up-to-date DB), but FAILS
in production when those columns are accessed.

**Example (December 2024):**

```python
# Model defined 5 columns:
class Customer(Base):
    contact_preference: Mapped[str] = mapped_column(...)  # DIDN'T EXIST IN PROD!
    ai_contact_ok: Mapped[bool] = mapped_column(...)      # DIDN'T EXIST IN PROD!
    flexibility_score: Mapped[int] = mapped_column(...)   # DIDN'T EXIST IN PROD!
    # ... etc
```

**Result:** Booking API returned 503 with
`column customers.contact_preference does not exist`

---

## 🎯 The Golden Rule

> **EVERY SQLAlchemy column MUST have a corresponding migration that
> creates it in production.**

---

## 📋 Pre-Deployment Schema Checklist (MANDATORY)

Before deploying ANY code that touches database models:

### 1. Check Model Changes

```bash
# Find all model files changed
git diff origin/main --name-only | grep -E "db/models/.*\.py"

# For each changed model, list new columns
git diff origin/main apps/backend/src/db/models/
```

### 2. Verify Migrations Exist

```bash
# Check migrations directory
ls -la database/migrations/
ls -la apps/backend/src/db/migrations/

# For each new column, find corresponding migration
grep -r "ADD COLUMN column_name" database/migrations/
```

### 3. Run Schema Comparison

**Local vs Model:**

```bash
cd apps/backend
python -c "
from db.base_class import Base
from db.models import *  # Import all models
for table in Base.metadata.tables.values():
    print(f'{table.schema}.{table.name}: {[c.name for c in table.columns]}')"
```

**Production vs Model:**

```bash
# SSH to VPS and compare
ssh root@108.175.12.154 "sudo -u postgres psql -d myhibachi_production -c \"
SELECT table_schema, table_name, column_name
FROM information_schema.columns
WHERE table_schema IN ('core', 'identity', 'lead', 'ops', 'newsletter', 'ai', 'crm', 'security')
ORDER BY table_schema, table_name, ordinal_position;\""
```

### 4. Apply Missing Migrations

```bash
# Copy migration to VPS
scp database/migrations/XXX_migration.sql root@108.175.12.154:/tmp/

# Run on STAGING first (always!)
ssh root@108.175.12.154 "cd /tmp && sudo -u postgres psql -d myhibachi_staging -f /tmp/XXX_migration.sql"

# Verify staging works for 48 hours

# Then run on PRODUCTION
ssh root@108.175.12.154 "cd /tmp && sudo -u postgres psql -d myhibachi_production -f /tmp/XXX_migration.sql"
```

---

## 📁 Migration File Standards

### Location

```
database/migrations/           # Primary location for SQL migrations
apps/backend/src/db/migrations/  # Alternative location (avoid duplicates!)
```

### Naming Convention

```
[YYYYMMDDHHMMSS]_[description].sql

Examples:
002_smart_scheduling_phase1.sql
20251126220831_add_travel_fee_configurations.sql
BATCH_1_COMBINED_MIGRATION.sql
```

### Required Structure

```sql
-- =====================================================
-- Migration: [Description]
-- Created: [Date]
-- Purpose: [What this migration does]
-- =====================================================

BEGIN;

-- Idempotent checks (ALWAYS!)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'core'
        AND table_name = 'tablename'
        AND column_name = 'new_column'
    ) THEN
        ALTER TABLE core.tablename ADD COLUMN new_column TYPE;
        RAISE NOTICE 'Added new_column';
    END IF;
END $$;

-- Always add comments
COMMENT ON COLUMN core.tablename.new_column IS 'Description of the column';

-- Add indexes if needed
CREATE INDEX IF NOT EXISTS idx_table_column ON core.tablename (new_column);

COMMIT;

-- =====================================================
-- ROLLBACK SCRIPT (required for all migrations!)
-- =====================================================
-- ALTER TABLE core.tablename DROP COLUMN IF EXISTS new_column;
```

---

## 🔍 Schema Audit Query (Use This!)

Run this query to get complete schema snapshot:

```sql
SELECT
    table_schema,
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema IN ('core', 'identity', 'lead', 'ops', 'newsletter', 'ai', 'crm', 'security')
ORDER BY table_schema, table_name, ordinal_position;
```

---

## ⚠️ Common Schema Issues

### Issue 1: Column in Model, Not in Production

**Symptom:** `column X does not exist` errors in production

**Cause:** Model was updated but migration wasn't run

**Fix:**

```sql
ALTER TABLE schema.table ADD COLUMN IF NOT EXISTS column_name TYPE;
```

### Issue 2: Table in Model, Not in Production

**Symptom:** `relation schema.table does not exist`

**Cause:** CREATE TABLE migration never ran

**Fix:** Run the full table creation migration

### Issue 3: Enum Value Missing

**Symptom:** `invalid input value for enum type_name`

**Cause:** New enum value added to Python but not to PostgreSQL

**Fix:**

```sql
ALTER TYPE enum_name ADD VALUE 'new_value';
```

### Issue 4: Foreign Key Reference Missing

**Symptom:** `relation schema.table does not exist` on FK constraint

**Cause:** Parent table migration didn't run

**Fix:** Run parent table migration first, then child table

---

## 📊 Schema Inventory (Last Updated: December 2024)

### Core Schema (core.\*)

| Table                       | Purpose                | Key Columns                 |
| --------------------------- | ---------------------- | --------------------------- |
| `bookings`                  | Customer bookings      | 41 columns (inc. venue_lat) |
| `customers`                 | Customer profiles      | 20 columns                  |
| `addresses`                 | Venue addresses        | 27 columns                  |
| `payments`                  | Payment records        | 17 columns                  |
| `message_threads`           | Support threads        | 10 columns                  |
| `messages`                  | Thread messages        | 8 columns                   |
| `travel_fee_configurations` | Travel fee rules       | 15+ columns                 |
| `booking_reminders`         | Reminder scheduling    | 10 columns                  |
| `pricing_tiers`             | Price tier definitions | 12 columns                  |
| `social_threads`            | Social media threads   | 10 columns                  |
| `reviews`                   | Customer reviews       | 8+ columns                  |

### Identity Schema (identity.\*)

| Table               | Purpose              | Key Columns |
| ------------------- | -------------------- | ----------- |
| `users`             | User accounts        | 23 columns  |
| `stations`          | Business locations   | 21 columns  |
| `roles`             | Role definitions     | 8 columns   |
| `user_roles`        | User-role mapping    | -           |
| `permissions`       | Permission defs      | -           |
| `admin_invitations` | Admin invites        | 15 columns  |
| `station_users`     | Station-user mapping | -           |

### Ops Schema (ops.\*)

| Table                 | Purpose             | Key Columns |
| --------------------- | ------------------- | ----------- |
| `chefs`               | Chef profiles       | 16 columns  |
| `chef_availability`   | Weekly schedules    | 7 columns   |
| `chef_timeoff`        | Time-off requests   | -           |
| `chef_locations`      | Chef home locations | 9 columns   |
| `chef_assignments`    | Booking assignments | 14 columns  |
| `slot_configurations` | Booking slots       | 12 columns  |
| `travel_time_cache`   | Travel time cache   | -           |
| `menu_items`          | Menu items          | 11 columns  |
| `pricing_rules`       | Dynamic pricing     | 11 columns  |
| `travel_zones`        | Service areas       | 10 columns  |

### AI Schema (ai.\*)

| Table              | Purpose           | Key Columns |
| ------------------ | ----------------- | ----------- |
| `conversations`    | AI conversations  | 27 columns  |
| `messages`         | Conversation msgs | 25 columns  |
| `training_data`    | Training examples | 13 columns  |
| `kb_chunks`        | Knowledge base    | 13 columns  |
| `escalation_rules` | Escalation config | -           |

---

## 🛡️ Automated Schema Validation (Future)

### GitHub Action Check (TODO)

```yaml
name: Schema Validation

on: [pull_request]

jobs:
  check-schema:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Compare model columns to migrations
        run: |
          # Script to check all model columns have migrations
          python scripts/validate_schema.py
```

### Pre-commit Hook (TODO)

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check if any model files changed
if git diff --cached --name-only | grep -q "db/models/"; then
  echo "⚠️ Model files changed - verify migrations exist!"
  echo "Run: python scripts/validate_schema.py"
fi
```

---

## 📋 When Adding New Model Columns

### Step-by-Step Process:

1. **Add column to SQLAlchemy model**

   ```python
   # apps/backend/src/db/models/core.py
   new_column: Mapped[str] = mapped_column(String(100), nullable=True)
   ```

2. **Create migration file**

   ```bash
   # Create migration with timestamp
   cat > database/migrations/$(date +%Y%m%d%H%M%S)_add_new_column.sql << 'EOF'
   -- Migration: Add new_column to table
   ALTER TABLE schema.table ADD COLUMN IF NOT EXISTS new_column VARCHAR(100);
   COMMENT ON COLUMN schema.table.new_column IS 'Description';
   EOF
   ```

3. **Test locally**

   ```bash
   psql -d myhibachi_local -f database/migrations/XXX.sql
   # Run app and verify column works
   ```

4. **Run on staging**

   ```bash
   ssh root@VPS "sudo -u postgres psql -d myhibachi_staging -f /tmp/XXX.sql"
   ```

5. **Wait 48 hours and verify**

6. **Run on production**

   ```bash
   ssh root@VPS "sudo -u postgres psql -d myhibachi_production -f /tmp/XXX.sql"
   ```

7. **Restart backend**
   ```bash
   ssh root@VPS "systemctl restart myhibachi-backend"
   ```

---

## 🔗 Related Docs

- `07-TESTING_QA.instructions.md` – Database migration safety section
- `16-INFRASTRUCTURE_DEPLOYMENT.instructions.md` – VPS/DB access
- `docs/04-DEPLOYMENT/DATABASE_SETUP_GUIDE.md` – Full DB setup
