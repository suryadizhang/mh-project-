# Duplicate Model Analysis - Complete Scan Results

**Generated**: November 27, 2025 **Purpose**: Identify ALL duplicate
SQLAlchemy model classes causing registry conflicts

## Executive Summary

Found **40+ duplicate model classes** across the codebase in multiple
locations:

- `db/models/` - Canonical source (modular architecture)
- `db/models_generated/` - Auto-generated from database schema
  (DUPLICATES)
- `models/` - Old standalone models (DUPLICATES)
- `core/auth/` - Auth-specific models (DUPLICATES)
- `api/` - API-specific models (DUPLICATES)
- `monitoring/` - Monitoring models (DUPLICATES)
- `middleware/` - Middleware models (DUPLICATES)

## Critical Duplicates (High Priority - Breaking Tests)

### 1. Identity Schema (PARTIALLY FIXED)

**Status**: ✅ Monolithic files renamed, but core/auth/ still has
duplicates

| Model              | Canonical Source                 | Duplicates                                                            | Action                    |
| ------------------ | -------------------------------- | --------------------------------------------------------------------- | ------------------------- |
| User               | `db/models/identity/users.py`    | ~~`identity.py`~~ (renamed), `models_generated/identity_generated.py` | Delete generated          |
| Role               | `db/models/identity/roles.py`    | ~~`role.py`~~ (renamed), ~~`identity.py`~~, `models_generated/`       | Delete generated          |
| Permission         | `db/models/identity/roles.py`    | ~~`role.py`~~, ~~`identity.py`~~, `models_generated/`                 | Delete generated          |
| Station            | `db/models/identity/stations.py` | ~~`identity.py`~~, `core/auth/station_models.py`, `models_generated/` | Move enums, delete models |
| StationUser        | `db/models/identity/stations.py` | ~~`identity.py`~~, ~~`core/auth/models.py`~~ (deleted)                | ✅ Fixed                  |
| StationAccessToken | `db/models/identity/stations.py` | ~~`identity.py`~~, `core/auth/station_models.py`, `models_generated/` | Delete duplicates         |
| StationAuditLog    | `db/models/identity/stations.py` | ~~`identity.py`~~, `core/auth/station_models.py`, `models_generated/` | Delete duplicates         |
| OAuthAccount       | `db/models/identity/oauth.py`    | ~~`identity.py`~~, `models_generated/`                                | Delete generated          |
| AdminInvitation    | `db/models/identity/admin.py`    | ~~`identity.py`~~                                                     | ✅ Fixed                  |
| GoogleOAuthAccount | `db/models/identity/admin.py`    | ~~`identity.py`~~                                                     | ✅ Fixed                  |
| AdminAccessLog     | `db/models/identity/admin.py`    | ~~`identity.py`~~                                                     | ✅ Fixed                  |

**Enums Needed**:

- `StationStatus`, `StationRole`, `StationPermission` (currently only
  in `core/auth/station_models.py`)
- **Action**: Move enums to `db/models/identity/stations.py`, then
  delete `core/auth/station_models.py` models

### 2. Core Schema

**Status**: ⚠️ Multiple duplicates in different locations

| Model           | Canonical Source    | Duplicates                                                    | Action                     |
| --------------- | ------------------- | ------------------------------------------------------------- | -------------------------- |
| Booking         | `db/models/core.py` | `models_generated/core_generated.py`                          | Delete generated           |
| Customer        | `db/models/core.py` | `models_generated/core_generated.py`                          | Delete generated           |
| Chef            | `db/models/ops.py`  | ~~`core.py`~~ (deleted), `models_generated/core_generated.py` | ✅ Fixed, delete generated |
| MessageThread   | `db/models/core.py` | `models_generated/core_generated.py`                          | Delete generated           |
| CoreMessage     | `db/models/core.py` | `models_generated/core_generated.py` (as `Messages`)          | Delete generated           |
| SocialThread    | `db/models/core.py` | `models_generated/core_generated.py`                          | Delete generated           |
| Review          | `db/models/core.py` | `models_generated/core_generated.py`                          | Delete generated           |
| Payment         | `db/models/core.py` | N/A                                                           | ✅ Unique                  |
| BookingReminder | `db/models/core.py` | `models/booking_reminder.py`                                  | Delete `models/` version   |
| PricingTier     | `db/models/core.py` | `models/knowledge_base.py`, `db/models/knowledge_base.py`     | Delete from knowledge_base |

### 3. Support & Communications

**Status**: ⚠️ Duplicated in standalone files

| Model         | Canonical Source                      | Duplicates                    | Action            |
| ------------- | ------------------------------------- | ----------------------------- | ----------------- |
| Escalation    | `db/models/support_communications.py` | `db/models/escalation.py`     | Delete standalone |
| CallRecording | `db/models/support_communications.py` | `db/models/call_recording.py` | Delete standalone |

### 4. Lead & CRM

**Status**: ⚠️ Campaign has 2 different purposes, Lead duplicated

| Model    | Canonical Source          | Duplicates         | Purpose Conflict?                      |
| -------- | ------------------------- | ------------------ | -------------------------------------- |
| Lead     | `db/models/lead.py`       | `db/models/crm.py` | Same - consolidate                     |
| Campaign | `db/models/newsletter.py` | `db/models/crm.py` | **Different**: newsletter vs marketing |

**Analysis**: Campaign serves TWO different business functions:

- `newsletter.py`: Email/SMS campaigns (RingCentral integration)
- `crm.py`: Marketing campaigns (lead generation)

**Decision**: Keep both but **rename** one to avoid SQLAlchemy
conflict:

- `newsletter.Campaign` → Keep as is (email/SMS)
- `crm.Campaign` → Rename to `MarketingCampaign`

### 5. AI Models

**Status**: ⚠️ Duplicated in API layer

| Model                 | Canonical Source                | Duplicates                                                                              | Action                |
| --------------------- | ------------------------------- | --------------------------------------------------------------------------------------- | --------------------- |
| ConversationAnalytics | `db/models/ai/analytics.py`     | `api/ai/endpoints/models.py`                                                            | Delete from API       |
| AIUsage               | `db/models/ai/analytics.py`     | `api/ai/endpoints/models.py`                                                            | Delete from API       |
| TrainingData          | `db/models/ai/analytics.py`     | `api/ai/endpoints/models.py`, `models/knowledge_base.py`, `db/models/knowledge_base.py` | Delete all duplicates |
| UnifiedConversation   | `db/models/ai/conversations.py` | `api/ai/endpoints/models.py` (as `Conversation`)                                        | Delete from API       |
| UnifiedMessage        | `db/models/ai/conversations.py` | `api/ai/endpoints/models.py` (as `AIMessage`)                                           | Delete from API       |
| KnowledgeBaseChunk    | `db/models/ai/knowledge.py`     | `api/ai/endpoints/models.py`                                                            | Delete from API       |
| EscalationRule        | `db/models/ai/knowledge.py`     | `api/ai/endpoints/models.py`                                                            | Delete from API       |

### 6. Knowledge Base Models

**Status**: ⚠️ Entire file duplicated in two locations

| Model                  | Location 1                 | Location 2                                         | Action                        |
| ---------------------- | -------------------------- | -------------------------------------------------- | ----------------------------- |
| BusinessRule           | `models/knowledge_base.py` | `db/models/knowledge_base.py`                      | Delete `models/` version      |
| FAQItem                | `models/knowledge_base.py` | `db/models/knowledge_base.py`                      | Delete `models/` version      |
| TrainingData           | `models/knowledge_base.py` | `db/models/knowledge_base.py`                      | Delete `models/` version      |
| UpsellRule             | `models/knowledge_base.py` | `db/models/knowledge_base.py`                      | Delete `models/` version      |
| SeasonalOffer          | `models/knowledge_base.py` | `db/models/knowledge_base.py`                      | Delete `models/` version      |
| AvailabilityCalendar   | `models/knowledge_base.py` | `db/models/knowledge_base.py`                      | Delete `models/` version      |
| CustomerTonePreference | `models/knowledge_base.py` | `db/models/knowledge_base.py`                      | Delete `models/` version      |
| MenuItem               | `models/knowledge_base.py` | `db/models/knowledge_base.py`, `db/models/ops.py`  | Keep `ops.py`, delete others  |
| PricingTier            | `models/knowledge_base.py` | `db/models/knowledge_base.py`, `db/models/core.py` | Keep `core.py`, delete others |
| AddonItem              | `models/knowledge_base.py` | `db/models/knowledge_base.py`                      | Delete `models/` version      |
| SyncHistory            | `models/knowledge_base.py` | `db/models/knowledge_base.py`                      | Delete `models/` version      |

### 7. Monitoring Models

**Status**: ⚠️ AlertRule duplicated

| Model      | Canonical Source       | Duplicates                       | Action            |
| ---------- | ---------------------- | -------------------------------- | ----------------- |
| AlertModel | `monitoring/models.py` | N/A                              | ✅ Unique         |
| AlertRule  | `monitoring/models.py` | `monitoring/alert_rule_model.py` | Delete standalone |

### 8. Inbox/Email Models

**Status**: ⚠️ Standalone files, check if used

| Model               | Location                 | Status                    | Action                                |
| ------------------- | ------------------------ | ------------------------- | ------------------------------------- |
| EmailMessage        | `db/models/email.py`     | Not in db/models/**init** | Check usage, add to exports or delete |
| EmailThread         | `db/models/email.py`     | Not in db/models/**init** | Check usage, add to exports or delete |
| EmailSyncStatus     | `db/models/email.py`     | Not in db/models/**init** | Check usage, add to exports or delete |
| InboxMessage        | `api/v1/inbox/models.py` | API-specific              | Keep (API layer)                      |
| Thread              | `api/v1/inbox/models.py` | API-specific              | Keep (API layer)                      |
| TCPAOptStatus       | `api/v1/inbox/models.py` | API-specific              | Keep (API layer)                      |
| WebSocketConnection | `api/v1/inbox/models.py` | API-specific              | Keep (API layer)                      |

### 9. Generated Models (CRITICAL)

**Status**: 🔴 Entire directory is duplicates

**Location**: `db/models_generated/`

**Files**:

- `identity_generated.py` - 11 classes (ALL duplicates of
  `db/models/identity/`)
- `core_generated.py` - 11 classes (ALL duplicates of
  `db/models/core.py`)

**Classes in identity_generated.py**:

- Businesses, Permissions, Stations, Users, StationAccessTokens,
  StationAuditLogs, Users\_, Roles, StationUsers, RolePermissions,
  UserRoles

**Classes in core_generated.py**:

- Chefs, SocialAccounts, SocialIdentities, Stations, Customers,
  Bookings, MessageThreads, SocialThreads, Messages, Reviews,
  SocialMessages

**Action**: 🗑️ **DELETE ENTIRE `db/models_generated/` DIRECTORY**

These are auto-generated from database schema but conflict with
hand-written models in `db/models/`. The hand-written models have
proper relationships, business logic, and documentation.

### 10. Middleware/Misc Models

**Status**: ⚠️ Orphaned models

| Model                   | Location                           | Status                    | Action                                    |
| ----------------------- | ---------------------------------- | ------------------------- | ----------------------------------------- |
| ErrorLog                | `middleware/structured_logging.py` | Not in db/models          | Check if should be in db/models or delete |
| Contact                 | `models/contact.py`                | Orphaned                  | Check usage, consolidate or delete        |
| NotificationGroup       | `db/models/notification.py`        | Not in db/models/**init** | Add to exports or delete                  |
| NotificationGroupMember | `db/models/notification.py`        | Not in db/models/**init** | Add to exports or delete                  |
| NotificationGroupEvent  | `db/models/notification.py`        | Not in db/models/**init** | Add to exports or delete                  |

## Consolidation Strategy

### Phase 1: Delete Auto-Generated Duplicates (IMMEDIATE)

1. ✅ Delete/Rename `db/models/identity.py` (monolithic file)
2. ✅ Delete/Rename `db/models/role.py`
3. 🔴 **DELETE** `db/models_generated/` directory entirely
4. 🔴 **DELETE** `models/knowledge_base.py` (keep
   `db/models/knowledge_base.py`)

### Phase 2: Consolidate Standalone Model Files

1. Delete `db/models/escalation.py` (use `support_communications.py`)
2. Delete `db/models/call_recording.py` (use
   `support_communications.py`)
3. Delete `models/booking_reminder.py` (use `core.py`)
4. Delete `monitoring/alert_rule_model.py` (use
   `monitoring/models.py`)

### Phase 3: Fix core/auth/ Duplicates

1. Copy enums from `core/auth/station_models.py` to
   `db/models/identity/stations.py`
2. Delete model classes from `core/auth/station_models.py` (keep only
   enums temporarily)
3. Update imports in `core/auth/station_auth.py` and
   `station_middleware.py`
4. Eventually delete `core/auth/station_models.py` when enums moved

### Phase 4: Rename Campaign Conflict

1. Rename `db/models/crm.py::Campaign` → `MarketingCampaign`
2. Update all imports and references

### Phase 5: Clean AI Model Duplicates

1. Delete all models from `api/ai/endpoints/models.py`
2. Update imports to use `db/models/ai/`

### Phase 6: Fix Import Statements (CRITICAL)

Search and replace ALL imports across codebase:

- `from models.knowledge_base import` →
  `from db.models.knowledge_base import`
- `from db.models.escalation import` →
  `from db.models.support_communications import`
- `from db.models.call_recording import` →
  `from db.models.support_communications import`
- `from models.booking_reminder import` → `from db.models.core import`
- `from monitoring.alert_rule_model import` →
  `from monitoring.models import`
- `from api.ai.endpoints.models import` → `from db.models.ai.* import`
- `from core.auth.station_models import Station` →
  `from db.models.identity import Station`

### Phase 7: Update db/models/**init**.py

Add missing exports for:

- Email models (if used)
- Notification models (if used)
- System events
- Monitoring models (if should be in db layer)

## Files to DELETE (Complete List)

### Immediate Deletion (Breaking Tests)

```
db/models_generated/identity_generated.py
db/models_generated/core_generated.py
db/models_generated/__init__.py
models/knowledge_base.py
db/models/escalation.py
db/models/call_recording.py
models/booking_reminder.py
monitoring/alert_rule_model.py
```

### After Enum Migration

```
core/auth/station_models.py (after moving enums)
```

### Already Renamed (Safe)

```
db/models/_deprecated_identity_monolithic.py.txt
db/models/_deprecated_role.py.txt
```

## Files to MODIFY

### Update Imports

- All files importing from deleted modules
- `core/auth/station_auth.py`
- `core/auth/station_middleware.py`
- Any file importing from `models/knowledge_base.py`
- Any file importing from `api/ai/endpoints/models.py`

### Add Enums

- `db/models/identity/stations.py` - Add StationStatus, StationRole,
  StationPermission

### Rename Classes

- `db/models/crm.py` - Campaign → MarketingCampaign

## Verification Steps

1. Run duplicate finder script (should show 0 duplicates)
2. Run tests: `pytest tests/test_api_load.py` (should pass 12/12)
3. Check imports: `python -c "from db.models import *"` (should
   succeed)
4. Verify no SQLAlchemy registry conflicts
5. Run full test suite

## Estimated Impact

- **Files to delete**: 8-10 files
- **Import statements to update**: 50-100 locations
- **Test files affected**: Unknown (need to check)
- **Risk level**: Medium-High (breaking changes)
- **Benefit**: Eliminate 40+ duplicate classes, fix SQLAlchemy
  conflicts, achieve 100% test pass

## Recommendation

**Execute in order** (Phases 1-7) to minimize breakage. Each phase
should be committed separately for easy rollback.

**Priority**: Phase 1 (delete generated models) is CRITICAL and safe -
these are never imported.
