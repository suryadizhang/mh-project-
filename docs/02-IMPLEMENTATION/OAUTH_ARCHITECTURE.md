# OAuth & Social Login Architecture

**Last Updated:** 2025-01-31 **Status:** Active **Batch:** 1 **Related
Tables:** `identity.users`, `identity.social_accounts`,
`identity.oauth_accounts`

---

## Overview

My Hibachi uses a **dual OAuth architecture** to support different
authentication flows for customers and admin users:

| System             | Table                      | Model                           | Purpose                                   |
| ------------------ | -------------------------- | ------------------------------- | ----------------------------------------- |
| **Customer OAuth** | `identity.social_accounts` | `OAuthAccount` (oauth.py)       | Customer social logins (optional)         |
| **Admin OAuth**    | `identity.oauth_accounts`  | `GoogleOAuthAccount` (admin.py) | Admin Google login with approval workflow |

---

## Current OAuth Providers

### Implemented ✅

| Provider           | Customer App | Admin App | Auth Flow                     |
| ------------------ | ------------ | --------- | ----------------------------- |
| **Google**         | ✅ Planned   | ✅ Active | OAuth 2.0 + approval workflow |
| **Email/Password** | ✅ Active    | ✅ Active | JWT with refresh tokens       |

### Ready for Future Implementation 🔮

These columns exist in `identity.users` and are ready for use:

| Provider      | Column         | Status   | Notes                        |
| ------------- | -------------- | -------- | ---------------------------- |
| **Google**    | `google_id`    | ✅ Ready | Unique Google sub identifier |
| **Microsoft** | `microsoft_id` | ✅ Ready | Azure AD / Microsoft Account |
| **Apple**     | `apple_id`     | ✅ Ready | Sign in with Apple           |

---

## Architecture Diagrams

### Customer OAuth Flow (social_accounts)

```
┌─────────────┐     ┌─────────────┐     ┌──────────────────────┐
│  Customer   │────▶│   Google    │────▶│  social_accounts     │
│   Website   │     │   OAuth     │     │  (10 columns)        │
└─────────────┘     └─────────────┘     │                      │
                                        │  - provider          │
                                        │  - provider_user_id  │
                                        │  - access_token      │
                                        │  - refresh_token     │
                                        │  - token_expires_at  │
                                        └──────────┬───────────┘
                                                   │
                                                   ▼
                                        ┌──────────────────────┐
                                        │      users           │
                                        │  (single user record)│
                                        └──────────────────────┘
```

### Admin OAuth Flow (oauth_accounts)

```
┌─────────────┐     ┌─────────────┐     ┌──────────────────────┐
│   Admin     │────▶│   Google    │────▶│  oauth_accounts      │
│   Panel     │     │   OAuth     │     │  (21 columns)        │
└─────────────┘     └─────────────┘     │                      │
                                        │  - google_id         │
                                        │  - email             │
                                        │  - approval_status   │◀─┐
                                        │  - requested_role    │  │
                                        │  - approved_by       │  │
                                        │  - approved_at       │  │
                                        └──────────┬───────────┘  │
                                                   │              │
                                                   ▼              │
                                        ┌──────────────────────┐  │
                                        │      users           │  │
                                        │  (linked after       │  │
                                        │   approval)          │  │
                                        └──────────────────────┘  │
                                                                  │
                                        ┌──────────────────────┐  │
                                        │   Super Admin        │──┘
                                        │   Approves Request   │
                                        └──────────────────────┘
```

---

## Database Schema Reference

### 1. identity.users (OAuth columns)

```sql
-- OAuth provider identifiers (for direct linking)
google_id       VARCHAR(255) UNIQUE  -- Google 'sub' claim
microsoft_id    VARCHAR(255) UNIQUE  -- Microsoft 'oid' claim
apple_id        VARCHAR(255) UNIQUE  -- Apple 'sub' claim

-- Unified auth metadata
auth_provider   VARCHAR(20)          -- 'email', 'google', 'microsoft', 'apple'
full_name       VARCHAR(255)         -- Full name from OAuth provider
is_email_verified BOOLEAN            -- Email verification status
```

### 2. identity.social_accounts (Customer OAuth)

```sql
CREATE TABLE identity.social_accounts (
    id              UUID PRIMARY KEY,
    user_id         UUID REFERENCES identity.users(id),
    provider        VARCHAR(50) NOT NULL,      -- 'google', 'facebook', 'apple'
    provider_user_id VARCHAR(255) NOT NULL,    -- Provider's unique user ID
    email           VARCHAR(255),
    access_token    TEXT,
    refresh_token   TEXT,
    token_expires_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ,
    updated_at      TIMESTAMPTZ,

    UNIQUE(provider, provider_user_id)
);
```

### 3. identity.oauth_accounts (Admin OAuth)

```sql
CREATE TABLE identity.oauth_accounts (
    id                  UUID PRIMARY KEY,
    google_id           VARCHAR(255) UNIQUE NOT NULL,
    email               VARCHAR(255) NOT NULL,
    name                VARCHAR(255),
    picture_url         TEXT,

    -- Approval workflow
    approval_status     VARCHAR(20) DEFAULT 'pending',  -- pending, approved, rejected
    requested_role      VARCHAR(50) DEFAULT 'admin',
    requested_station_ids UUID[],
    rejection_reason    TEXT,
    approved_by         UUID REFERENCES identity.users(id),
    approved_at         TIMESTAMPTZ,

    -- Link to users table (after approval)
    user_id             UUID REFERENCES identity.users(id),

    -- Tokens
    access_token        TEXT,
    refresh_token       TEXT,
    token_expires_at    TIMESTAMPTZ,

    -- Audit
    last_login_at       TIMESTAMPTZ,
    login_count         INTEGER DEFAULT 0,
    created_at          TIMESTAMPTZ,
    updated_at          TIMESTAMPTZ
);
```

---

## Adding New OAuth Providers

### Step 1: Database Migration

Create a new migration file:

```sql
-- database/migrations/XXX_add_{provider}_oauth.sql

-- Add provider ID column to users table
ALTER TABLE identity.users
ADD COLUMN IF NOT EXISTS {provider}_id VARCHAR(255) UNIQUE;

COMMENT ON COLUMN identity.users.{provider}_id IS
    '{Provider} OAuth unique identifier (sub/oid claim)';

-- Add index for lookups
CREATE INDEX IF NOT EXISTS idx_users_{provider}_id
ON identity.users ({provider}_id)
WHERE {provider}_id IS NOT NULL;
```

### Step 2: Update User Model

In `apps/backend/src/db/models/identity/users.py`:

```python
class User(Base):
    # ... existing columns ...

    # Add new provider column
    {provider}_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        comment="{Provider} OAuth unique identifier"
    )
```

### Step 3: Create OAuth Handler

In `apps/backend/src/routers/v1/auth/`:

```python
# {provider}_oauth.py

from fastapi import APIRouter, Depends
from httpx import AsyncClient

router = APIRouter()

@router.get("/auth/{provider}/login")
async def {provider}_login():
    """Redirect to {Provider} OAuth consent screen."""
    pass

@router.get("/auth/{provider}/callback")
async def {provider}_callback(code: str):
    """Handle OAuth callback and create/link user."""
    pass
```

### Step 4: Update AuthProvider Enum

In `apps/backend/src/db/models/identity/users.py`:

```python
class AuthProvider(str, Enum):
    EMAIL = "email"
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    APPLE = "apple"
    {PROVIDER} = "{provider}"  # Add new provider
```

### Step 5: Environment Variables

Add to `.env` and GSM:

```env
{PROVIDER}_CLIENT_ID=your_client_id
{PROVIDER}_CLIENT_SECRET=your_client_secret
{PROVIDER}_REDIRECT_URI=https://api.myhibachichef.com/auth/{provider}/callback
```

---

## Provider-Specific Implementation Notes

### Google OAuth

**Scopes Used:**

- `openid` - Required for OIDC
- `email` - User's email address
- `profile` - User's name and picture

**ID Token Claims:**

- `sub` - Unique Google user ID (stored in `google_id`)
- `email` - User's email
- `email_verified` - Email verification status
- `name` - Full name
- `picture` - Profile picture URL

**Configuration:**

```python
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
```

### Microsoft OAuth (Future)

**Scopes Needed:**

- `openid`
- `email`
- `profile`
- `User.Read`

**ID Token Claims:**

- `oid` - Object ID (stored in `microsoft_id`)
- `preferred_username` - Email/UPN
- `name` - Display name

### Apple Sign In (Future)

**Scopes Needed:**

- `name`
- `email`

**Notes:**

- Apple only sends name/email on FIRST login
- Must store name from initial response
- Uses JWT for ID token

---

## Security Considerations

### Token Storage

| Token Type    | Storage    | Encryption                      |
| ------------- | ---------- | ------------------------------- |
| Access Token  | Database   | At rest (column-level)          |
| Refresh Token | Database   | At rest (column-level)          |
| ID Token      | Not stored | N/A (validated, then discarded) |

### Session Management

- JWT access tokens: 15 minutes expiry
- Refresh tokens: 7 days expiry
- OAuth tokens: Per-provider expiry (stored)

### MFA Integration

The User model includes MFA columns that work with OAuth:

```python
# MFA columns in users table
mfa_enabled: bool
mfa_secret: str (encrypted)
mfa_backup_codes: list (encrypted)
mfa_recovery_email: str
```

OAuth users can optionally enable MFA as additional security layer.

---

## Testing OAuth

### Local Development

1. Use ngrok or similar for callback URL:

   ```bash
   ngrok http 8000
   ```

2. Set callback URL in provider console:

   ```
   https://xxx.ngrok.io/api/v1/auth/google/callback
   ```

3. Update `.env`:
   ```env
   GOOGLE_REDIRECT_URI=https://xxx.ngrok.io/api/v1/auth/google/callback
   ```

### Staging

- Callbacks use: `https://staging-api.myhibachichef.com/...`
- Separate OAuth app credentials for staging

### Production

- Callbacks use: `https://api.myhibachichef.com/...`
- Production OAuth app credentials in GSM

---

## Troubleshooting

### Common Errors

| Error                                    | Cause                | Solution                  |
| ---------------------------------------- | -------------------- | ------------------------- |
| `User has no attribute 'google_id'`      | Missing column in DB | Run migration 007         |
| `social_accounts does not exist`         | Missing table        | Check identity schema     |
| `oauth_accounts approval_status invalid` | Wrong enum value     | Check ApprovalStatus enum |

### Verification Queries

```sql
-- Check OAuth columns exist
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'identity'
AND table_name = 'users'
AND column_name IN ('google_id', 'microsoft_id', 'apple_id', 'auth_provider');

-- Check OAuth tables exist
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'identity'
AND table_name IN ('social_accounts', 'oauth_accounts');

-- Check admin OAuth pending approvals
SELECT email, approval_status, requested_role, created_at
FROM identity.oauth_accounts
WHERE approval_status = 'pending'
ORDER BY created_at DESC;
```

---

## Related Documentation

- [19-DATABASE_SCHEMA_MANAGEMENT.instructions.md](/.github/instructions/19-DATABASE_SCHEMA_MANAGEMENT.instructions.md) -
  Migration procedures
- [Migration 007](../../database/migrations/007_add_oauth_columns_to_users.sql) -
  OAuth columns for users table
- [User Model](../../apps/backend/src/db/models/identity/users.py) -
  SQLAlchemy User model
- [Admin OAuth Model](../../apps/backend/src/db/models/identity/admin.py) -
  GoogleOAuthAccount model

---

## Changelog

| Date       | Change                                            | Author        |
| ---------- | ------------------------------------------------- | ------------- |
| 2025-01-31 | Initial documentation created                     | Copilot Agent |
| 2025-01-31 | Added Microsoft/Apple future implementation notes | Copilot Agent |
