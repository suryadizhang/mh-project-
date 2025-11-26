# Alembic Migration State - My Hibachi Backend

**Last Updated**: 2025-11-23 **Current Revision**: `2a1a11964b93`
(Phase 0 merge head) **Status**: ✅ **CLEAN** - Single head, all
migrations validated

---

## Current State Summary

| Metric                        | Value                                                 |
| ----------------------------- | ----------------------------------------------------- |
| **Current Database Revision** | `2a1a11964b93` (head) (mergepoint)                    |
| **Total Migrations**          | 53 migration files                                    |
| **Duplicate Revisions**       | 0 (all fixed in Phase 0)                              |
| **Missing Parents**           | 0 (all validated)                                     |
| **Empty Files**               | 0 (011_add_social_account_identity_tables.py removed) |
| **Multiple Heads**            | 0 (merged in Phase 0 Step 5)                          |
| **Import Errors**             | 0 (Base imports fixed)                                |

---

## Migration Chain Health

### ✅ Validation Tests Performed

1. **Duplicate Detection**: Audit script found and removed 2 duplicate
   `cd22216ae9d3` files
2. **Parent Reference Validation**: All 53 migrations reference valid
   parent revisions
3. **Head Merge**: Successfully merged 2 divergent heads into single
   chain
4. **Downgrade Test**: Successfully downgraded from `2a1a11964b93` →
   `6391276aefcc`
5. **Upgrade Test**: Successfully re-upgraded to `2a1a11964b93` (head)

### Migration Chain Structure

```
<... 46 earlier migrations ...>

5034d1bfa5f0 ──┐
                ├──> bd8856cf6aa0 (knowledge base tables)
                │
004_station_rbac, cafcd735e7fe ──> 6391276aefcc (RBAC merge)
                                    │
                                    ├──> 2a1a11964b93 (Phase 0 merge - CURRENT HEAD)
                                    │
bd8856cf6aa0 ───────────────────────┘
```

**Key Merges:**

- `2a1a11964b93`: Phase 0 merge (6391276aefcc + bd8856cf6aa0)
- `6391276aefcc`: RBAC merge with main chain
- `bd8856cf6aa0`: Knowledge base tables (7 tables added)

---

## Phase 0 Fixes Applied

### 1. Import Errors Fixed (3 files)

**Issue**: Missing `models.legacy_declarative_base` module **Files
Fixed**:

- `apps/backend/src/models/base.py`
- `apps/backend/src/core/auth/station_models.py`
- `apps/backend/src/core/auth/models.py`

**Solution**: Changed all to `from core.database import Base`

---

### 2. Empty Migration File Removed

**Issue**: `011_add_social_account_identity_tables.py` was 0 bytes
**Solution**: Removed file (backed up to `backups/alembic/`)

---

### 3. Duplicate Revision Fixed

**Issue**: Revision `cd22216ae9d3` appeared twice **Files Removed**:

- `cd22216ae9d3_merge_roles_migrations.py`
- `cd22216ae9d3_merge_roles_and_users_branches.py`

**Solution**: Removed both duplicates, updated
`009_payment_notifications.py` to reference `008_add_user_roles`
instead

---

### 4. Migration Chain Broken Reference Fixed

**Issue**: `009_payment_notifications.py` referenced deleted
`cd22216ae9d3` **Solution**: Updated `down_revision = 'cd22216ae9d3'`
→ `down_revision = '008_add_user_roles'`

---

### 5. Multiple Heads Merged

**Issue**: 2 divergent heads (`6391276aefcc`, `bd8856cf6aa0`)
**Solution**: Created merge migration
`2a1a11964b93_phase_0_merge_all_remaining_heads.py`

**Merge Details**:

- **Parent 1**: `6391276aefcc` (merge_station_rbac_with_main_chain)
- **Parent 2**: `bd8856cf6aa0` (create_knowledge_base_tables)
- **Result**: Single unified head for linear migration chain

---

## Database Schema Status

### Tables Created by bd8856cf6aa0 (Knowledge Base)

1. `business_rules` - Policies, pricing, travel, payment rules
2. `faq_items` - Dynamic FAQs with categories and tags
3. `training_data` - AI hospitality training examples
4. `upsell_rules` - Contextual upselling logic
5. `seasonal_offers` - Time-limited promotions
6. `availability_calendar` - Real-time booking slots
7. `customer_tone_preferences` - Learned customer tone history

**Note**: These tables existed in database but were not tracked in
Alembic history. Fixed using `alembic stamp bd8856cf6aa0` to mark
migration as applied without re-running.

---

## Tools & Scripts Created

### 1. `scripts/audit_alembic_revisions.py`

**Purpose**: Comprehensive migration chain audit **Features**:

- Two-pass revision discovery (prevents false positives)
- Duplicate detection
- Missing parent validation
- Orphaned revision detection
- Supports type-annotated revision declarations

**Usage**:

```bash
cd apps/backend
PYTHONPATH=src python scripts/audit_alembic_revisions.py
```

**Output**: `ALEMBIC_AUDIT_REPORT.txt`

---

### 2. `scripts/check_db_state.py`

**Purpose**: Compare database state vs Alembic migration history
**Usage**:

```bash
cd apps/backend
PYTHONPATH=src python scripts/check_db_state.py
```

**Checks**:

- Which migrations are applied to database
- Which tables exist but aren't tracked in Alembic
- Alembic version table state

---

### 3. `scripts/create_test_db.py`

**Purpose**: Create clean test database for migration testing
**Usage**:

```bash
cd apps/backend
PYTHONPATH=src python scripts/create_test_db.py
```

**Creates**: `myhibachi_test_migrations` database

---

## Configuration

### Environment Variables

**Production (.env)**:

```env
DATABASE_URL=postgresql+asyncpg://postgres:***@db.yuchqvpctookhjovvdwi.supabase.co:5432/postgres
DATABASE_URL_SYNC=postgresql+psycopg2://postgres:***@db.yuchqvpctookhjovvdwi.supabase.co:5432/postgres
```

**Key Points**:

- `DATABASE_URL`: Async (asyncpg) for FastAPI application
- `DATABASE_URL_SYNC`: Sync (psycopg2) for Alembic migrations
- `core.database.Base`: Single source of truth for all models

---

## Migration Workflows

### Creating New Migration

```bash
cd apps/backend
alembic revision --autogenerate -m "description_of_changes"
```

**CRITICAL**: Always wrap schema changes behind feature flags!

---

### Applying Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade to specific revision
alembic upgrade <revision_id>

# Check current state
alembic current

# View history
alembic history --verbose
```

---

### Testing Migrations (Before Production)

**Step 1: Create test database**

```bash
PYTHONPATH=src python scripts/create_test_db.py
```

**Step 2: Test on clean database**

```bash
# Set test database URL
$env:DATABASE_URL = "postgresql://...test_migrations"
$env:DATABASE_URL_SYNC = "postgresql://...test_migrations"

# Test upgrade
alembic upgrade head

# Test downgrade
alembic downgrade <previous_revision>

# Test re-upgrade
alembic upgrade head
```

**Step 3: Verify schema**

```bash
PYTHONPATH=src python scripts/check_db_state.py
```

---

## CI/CD Integration (TODO - Phase 0 Step 6)

**Planned**: `.github/workflows/alembic-check.yml`

**Tests**:

1. `alembic check` - Verify no pending autogenerate changes
2. `alembic upgrade head` - Test on clean database
3. Downgrade/upgrade cycle validation
4. Migration file syntax validation

---

## Next Steps (Post-Phase 0)

### Phase 1B: Multi-Schema Migration

- [ ] Create PostgreSQL schemas (core, ai, crm, ops, marketing,
      analytics, admin)
- [ ] Create schema-aware Base classes
- [ ] Migrate loyalty tables to `crm` schema
- [ ] Update Alembic env.py to support multiple schemas

**Estimated Time**: 16-24 hours

---

## Troubleshooting

### "Multiple classes found for path" Error

**Cause**: Multiple Base classes in codebase **Fix**: Ensure all
models import from `core.database.Base`

---

### "Ambiguous walk" on Downgrade

**Cause**: Merge migrations have multiple parents **Fix**: Use
specific revision instead of relative `-n`:

```bash
# Instead of: alembic downgrade -3
# Use:        alembic downgrade <specific_revision_id>
```

---

### "DuplicateTable" on Upgrade

**Cause**: Tables exist but not tracked in Alembic **Fix**: Use
`alembic stamp <revision>` to mark as applied:

```bash
alembic stamp bd8856cf6aa0
```

---

### "The asyncio extension requires an async driver"

**Cause**: DATABASE_URL has `postgresql://` instead of
`postgresql+asyncpg://` **Fix**: Check `.env` file:

```env
DATABASE_URL=postgresql+asyncpg://...  # For app
DATABASE_URL_SYNC=postgresql+psycopg2://...  # For Alembic
```

---

## Success Criteria ✅

- [x] Single migration head
- [x] No duplicate revisions
- [x] All parent references valid
- [x] Downgrade/upgrade cycle tested
- [x] Import errors resolved
- [x] Documentation complete
- [ ] CI/CD workflow added (pending)

---

## Contact

**Maintainers**: My Hibachi Dev Team **Last Audit**: 2025-11-23 (Phase
0 completion) **Next Audit**: Before Phase 1B (multi-schema migration)
