# Database Schema Cleanup - Future Task

**Status**: TRACKED (Not blocking current work) **Priority**: Medium
(cleanup/tech debt) **Created**: 2025-11-25

---

## Issue: Schema-Prefixed Foreign Keys

Several models use schema prefixes (`lead.*`, `events.*`, `public.*`)
in foreign keys and `__table_args__`. This pattern will fail if those
schemas don't exist in the database.

### ✅ Already Fixed (2025-11-25):

1. **CallRecording** - Removed `communications` schema, fixed FKs to
   identity.users
2. **Escalation** - Removed `support` schema, fixed FKs to
   ai.conversations, bookings.customers, identity.users
3. **Role** - Removed `identity` schema
4. **Permission** - Removed `identity` schema
5. **PaymentNotification** - Removed FK to non-existent users table
6. **CustomerTonePreference** - Removed `public` schema prefix from
   customers FK

### ❌ Still Need Fixing:

#### Lead Models (lead.py)

- **Lines affected**: 146, 150, 168, 171, 206, 210
- **Issues**:
  ```python
  __table_args__ = {"schema": "lead", ...}  # 3 models
  ForeignKey("lead.leads.id", ...)          # 3 FKs
  ```
- **Models**: LeadContact, LeadContext, LeadEvent

#### Newsletter Models (newsletter.py)

- **Lines affected**: 42, 73, 77, 80, 98, 102, 105, 144
- **Issues**:
  ```python
  __table_args__ = {"schema": "lead", ...}  # 4 models
  ForeignKey("lead.campaigns.id", ...)      # 2 FKs
  ForeignKey("lead.subscribers.id", ...)    # 2 FKs
  ```
- **Models**: Campaign, CampaignEvent, SMSDeliveryEvent, Subscriber

#### Social Models (social.py)

- **Lines affected**: 305, 312, 397, 473, 550, 587
- **Issues**:
  ```python
  __table_args__ = {"schema": "public", ...}  # 2 models
  ForeignKey("lead.social_accounts.id", ...) # 2 FKs
  ForeignKey("lead.social_identities.id", ...)
  ForeignKey("lead.social_threads.id", ...)
  ```
- **Models**: SocialThread, SocialMessage, ReviewSource,
  ReviewSubmission

#### Events Models (events.py)

- **Lines affected**: 36, 97
- **Issues**:
  ```python
  __table_args__ = {"schema": "events", ...}
  ForeignKey("events.domain_events.id", ...)
  ```
- **Models**: DomainEvent, OutboxEntry

---

## Recommended Fix (When Ready)

**Option A - If schemas exist in DB:** Keep current structure (no
changes needed)

**Option B - If schemas DON'T exist:** Remove schema declarations and
fix FKs:

```python
# Before:
__table_args__ = {"schema": "lead", ...}
ForeignKey("lead.campaigns.id", ...)

# After:
__table_args__ = {"extend_existing": True}
ForeignKey("campaigns.id", ...)
```

---

## Testing Strategy

Before fixing:

1. Check if schemas exist:
   `SELECT schema_name FROM information_schema.schemata;`
2. If schemas exist: No action needed
3. If schemas DON'T exist: Apply fixes above

---

## Integration with Master Plan

**Add to Phase**: Database Cleanup & Optimization (after core features
stable) **Related Docs**:

- `FINAL_INTEGRATED_MASTER_PLAN.md` - Add to Phase 3 (Infrastructure)
- `DATABASE_MIGRATION_PLAN.md` - Note schema validation needed

---

## Notes

- Migration file `1f01e3015618_add_email_labels_table.py` was
  successfully generated despite these issues
- This suggests either:
  1. Schemas exist in current DB (migration succeeded)
  2. Alembic only validates model definitions, not DB state
- **Action**: Verify schema existence before fixing
- **Blocker**: None (email labels migration can proceed)

---

**Next Session Action**: Check database schemas, then decide fix
approach
