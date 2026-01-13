# My Hibachi - Logging & Audit Architecture

**Created:** 2025-01-30
**Version:** 2.0.0
**Status:** Active
**Relates To:** [Security](../../apps/backend/src/core/security/), [Audit Service](../../apps/backend/src/services/audit_service.py)

---

## Overview

This document describes the unified logging and audit trail architecture for the My Hibachi platform. The system provides comprehensive tracking of all business-critical operations, security events, and data changes.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       LOGGING ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐     ┌──────────────────┐     ┌───────────────────┐   │
│  │  API Layer   │────▶│  Audit Service   │────▶│  security.audit   │   │
│  │  (Routers)   │     │ audit_service.py │     │     _logs table   │   │
│  └──────────────┘     └──────────────────┘     └───────────────────┘   │
│         │                      │                        │               │
│         │                      │                        │               │
│         ▼                      ▼                        ▼               │
│  ┌──────────────┐     ┌──────────────────┐     ┌───────────────────┐   │
│  │   Security   │────▶│  Log Security    │────▶│security.security  │   │
│  │   Module     │     │     Events       │     │   _events table   │   │
│  └──────────────┘     └──────────────────┘     └───────────────────┘   │
│         │                      │                                        │
│         │                      │                                        │
│         ▼                      ▼                                        │
│  ┌──────────────┐     ┌──────────────────┐                             │
│  │   Python     │     │   File Logging   │                             │
│  │   Logging    │────▶│  (logs/*.log)    │                             │
│  │   (structlog)│     │   + Cloud Logs   │                             │
│  └──────────────┘     └──────────────────┘                             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Database Tables

### 1. `security.audit_logs` (Primary Audit Trail)

This table stores ALL audit trail entries for business operations.

```sql
CREATE TABLE security.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Action metadata
    action VARCHAR(100) NOT NULL,              -- 'create', 'update', 'delete', etc.
    entity_type VARCHAR(100) NOT NULL,         -- 'booking', 'customer', 'payment', etc.
    entity_id UUID,                            -- ID of affected entity

    -- Actor information
    user_id UUID REFERENCES identity.users(id),
    user_email VARCHAR(255),
    user_role VARCHAR(50),

    -- Change details
    old_values JSONB,                          -- State before change
    new_values JSONB,                          -- State after change
    changed_fields TEXT[],                     -- List of fields that changed

    -- Context
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(100),

    -- Metadata
    details JSONB,                             -- Additional context
    severity VARCHAR(20) DEFAULT 'info',       -- 'info', 'warning', 'error', 'critical'

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Indexes for performance
    CONSTRAINT audit_logs_action_check CHECK (action IN (
        'create', 'update', 'delete', 'view', 'login', 'logout',
        'failed_login', 'password_change', 'permission_change', 'export'
    ))
);

-- Performance indexes
CREATE INDEX idx_audit_logs_entity ON security.audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_user ON security.audit_logs(user_id);
CREATE INDEX idx_audit_logs_created ON security.audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_action ON security.audit_logs(action);
```

### 2. `security.security_events` (Security-Specific Events)

This table tracks security-critical events (login attempts, access violations, etc).

```sql
CREATE TABLE security.security_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Event classification
    event_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'info',

    -- Actor information
    user_id UUID,
    ip_address INET,
    user_agent TEXT,

    -- Event details
    details JSONB NOT NULL DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for querying recent security events
CREATE INDEX idx_security_events_created ON security.security_events(created_at DESC);
CREATE INDEX idx_security_events_type ON security.security_events(event_type);
CREATE INDEX idx_security_events_severity ON security.security_events(severity);
```

---

## Backend Services

### 1. `audit_service.py` - Business Audit Service

**Location:** `apps/backend/src/services/audit_service.py`

**Purpose:** Centralized service for all business audit logging.

**Key Methods:**

```python
# Log business entity changes (CRUD operations)
async def log_change(
    db: AsyncSession,
    action: str,           # 'create', 'update', 'delete'
    entity_type: str,      # 'booking', 'customer', 'payment'
    entity_id: UUID,
    user_id: Optional[UUID] = None,
    user_email: Optional[str] = None,
    old_values: Optional[Dict] = None,
    new_values: Optional[Dict] = None,
    details: Optional[Dict] = None,
    request: Optional[Request] = None,
) -> UUID

# Log security events (login, logout, access violations)
async def log_security_event(
    db: AsyncSession,
    event_type: str,       # 'login_success', 'login_failed', 'access_denied'
    user_id: Optional[UUID] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    details: Optional[Dict] = None,
    severity: str = 'info',
) -> UUID

# Generic action logging (non-change operations)
async def log_action(
    db: AsyncSession,
    action: str,           # 'view', 'export', 'search'
    entity_type: str,
    entity_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    details: Optional[Dict] = None,
    request: Optional[Request] = None,
) -> UUID

# Query audit trail with filters
async def get_audit_trail(
    db: AsyncSession,
    entity_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    action: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict]
```

### 2. `core/security/audit.py` - Security Audit Layer

**Location:** `apps/backend/src/core/security/audit.py`

**Purpose:** Low-level security event logging with file + database persistence.

**Key Functions:**

```python
# Log security event with DB persistence
async def log_security_event(
    db: AsyncSession,
    event_type: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[Dict] = None,
    severity: str = "info",
) -> None

# Query security events
async def get_security_events(
    db: AsyncSession,
    event_type: Optional[str] = None,
    user_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    severity: Optional[str] = None,
    limit: int = 100,
) -> List[Dict]
```

---

## Usage Examples

### Logging a Booking Creation

```python
from services.audit_service import log_change

# After creating a booking
await log_change(
    db=db,
    action='create',
    entity_type='booking',
    entity_id=booking.id,
    user_id=current_user.id,
    user_email=current_user.email,
    new_values={
        'customer_id': str(booking.customer_id),
        'event_date': booking.event_date.isoformat(),
        'guest_count': booking.guest_count,
        'status': booking.status,
    },
    details={'source': 'api', 'booking_type': 'hibachi'},
    request=request,
)
```

### Logging a Failed Login

```python
from services.audit_service import log_security_event

await log_security_event(
    db=db,
    event_type='login_failed',
    ip_address=request.client.host,
    user_agent=request.headers.get('user-agent'),
    details={'email': email, 'reason': 'invalid_password'},
    severity='warning',
)
```

### Querying Audit Trail

```python
from services.audit_service import get_audit_trail

# Get all booking-related actions for the last 7 days
trail = await get_audit_trail(
    db=db,
    entity_type='booking',
    start_date=datetime.now() - timedelta(days=7),
    limit=50,
)

# Get actions by a specific user
user_actions = await get_audit_trail(
    db=db,
    user_id=user_id,
    limit=100,
)
```

---

## Frontend Logging Standards

### ✅ ALLOWED: Operational Logs (with prefixes)

These logs are intentional and provide visibility into system operations:

```typescript
// Good: Operational log with clear prefix
console.log('[EMAIL SCHEDULER] Processing 5 scheduled emails');
console.log('[EMAIL AUTOMATION] Automation initialized');
console.log('[PAYMENT TRACKING] Customer preference saved');
```

### ❌ FORBIDDEN: Debug Logs

These should be removed before committing:

```typescript
// Bad: Debug logs for development only
console.log('Calling API:', path);
console.log('Response data:', data);
console.log('here');
```

### Files with Intentional Operational Logs

| File | Purpose | Keep |
|------|---------|------|
| `email-automation-init.ts` | Email automation startup | ✅ Yes |
| `email-scheduler.ts` | Scheduled email processing | ✅ Yes |
| `advancedAutomation.ts` | GMB/Directory automation | ✅ Yes |
| `logger.ts` | Centralized logging utility | ✅ Yes |

---

## Severity Levels

| Level | Use Case | Example |
|-------|----------|---------|
| `info` | Normal operations | User logged in, booking created |
| `warning` | Unusual but not critical | Failed login attempt, rate limit hit |
| `error` | Operation failed | Payment processing error, API failure |
| `critical` | Security/data integrity issue | Multiple failed logins, data corruption |

---

## Retention Policy

| Table | Retention | Notes |
|-------|-----------|-------|
| `security.audit_logs` | 7 years | Legal compliance requirement |
| `security.security_events` | 2 years | Security analysis |
| File logs (`logs/*.log`) | 90 days | Disk space management |

---

## Migration File

**File:** `database/migrations/015_create_audit_logs_table.sql`

This migration creates both audit tables if they don't exist. Run this on any new environment.

---

## Best Practices

1. **Always log entity changes** - Create, update, delete operations on business entities
2. **Include old/new values** - For update operations, capture what changed
3. **Capture request context** - IP address, user agent, request ID when available
4. **Use appropriate severity** - Don't overuse 'critical' or underuse 'warning'
5. **Don't log sensitive data** - Never log passwords, full credit card numbers, PII
6. **Be consistent with entity types** - Use snake_case: `booking`, `customer`, `payment`
7. **Test audit logging** - Include audit trail verification in integration tests

---

## Related Documents

- [Security Architecture](../security/)
- [API Standards](./API_DESIGN.md)
- [Database Schema](./DATABASE_ARCHITECTURE.md)
