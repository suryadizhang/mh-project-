---
applyTo: 'apps/admin/**'
---

# My Hibachi – Token Authentication Standards

**Priority: CRITICAL** – Follow these rules to prevent "Not
authenticated" errors. **Version:** 1.0.0 **Created:** 2025-01-30

---

## 🔴 THE GOLDEN RULE

> **NEVER use `localStorage.getItem()` or `sessionStorage.getItem()`
> directly for tokens.** **ALWAYS use `tokenManager` from
> `@/services/api`.**

---

## 🎯 Why This Matters

The admin app uses a centralized `tokenManager` that stores tokens in
`sessionStorage`. If you manually access `localStorage`, you will get
`null` because the token isn't there.

**This has caused multiple production bugs:**

- January 2025: 38 instances of direct localStorage access caused "Not
  authenticated" errors
- Every API call failed because the token was being retrieved from the
  wrong storage

---

## ✅ CORRECT Pattern (Always Use This)

```typescript
// 1. Import tokenManager at the top of your file
import { tokenManager } from '@/services/api';

// 2. Use tokenManager.getToken() to get the token
const response = await fetch('/api/v1/endpoint', {
  headers: {
    Authorization: `Bearer ${tokenManager.getToken()}`,
  },
});

// 3. For conditional checks
const token = tokenManager.getToken();
if (!token) {
  // Handle unauthenticated state
  router.push('/login');
  return;
}
```

---

## ❌ WRONG Patterns (NEVER Use These)

```typescript
// ❌ WRONG - localStorage is NOT where tokens are stored!
const token = localStorage.getItem('admin_token');
const token = localStorage.getItem('access_token');

// ❌ WRONG - Direct sessionStorage access bypasses tokenManager
const token = sessionStorage.getItem('admin_token');

// ❌ WRONG - Hardcoded token keys
headers: {
  Authorization: `Bearer ${localStorage.getItem('admin_token')}`,
}

// ❌ WRONG - Any variation of direct storage access
const adminToken = window.localStorage.getItem('admin_token');
```

---

## 🔧 Token Manager API Reference

**Location:** `apps/admin/src/services/api.ts` (exported at ~line 648)

```typescript
// Available methods
tokenManager.getToken(): string | null   // Get current token
tokenManager.setToken(token: string)     // Set token (used by login)
tokenManager.clearToken()                // Remove token (used by logout)
```

---

## 📋 Pre-Commit Checklist for Authentication

Before committing any code that makes API calls:

- [ ] Does this file import `tokenManager` from `@/services/api`?
- [ ] Are ALL `Authorization` headers using `tokenManager.getToken()`?
- [ ] NO instances of `localStorage.getItem('admin_token')`?
- [ ] NO instances of `localStorage.getItem('access_token')`?
- [ ] NO instances of `sessionStorage.getItem('admin_token')`?

---

## 🔍 Verification Commands

Run these before every commit to check for violations:

```bash
# Check for direct localStorage access to tokens
grep -rn "localStorage.getItem('admin_token')" apps/admin/src/
grep -rn "localStorage.getItem('access_token')" apps/admin/src/
grep -rn "sessionStorage.getItem('admin_token')" apps/admin/src/

# All three should return NO MATCHES
```

---

## 📁 Files That Commonly Need Token Access

When creating or modifying these file types, ensure proper token
handling:

| File Type        | Example                | Token Usage               |
| ---------------- | ---------------------- | ------------------------- |
| API calls        | `services/*.ts`        | `tokenManager.getToken()` |
| Page components  | `app/**/page.tsx`      | `tokenManager.getToken()` |
| Protected routes | Any authenticated page | Check token exists        |
| Superadmin pages | `app/superadmin/**`    | Must use tokenManager     |
| Newsletter pages | `app/newsletter/**`    | Must use tokenManager     |
| Inbox/comms      | `app/inbox/**`         | Must use tokenManager     |

---

## 🔄 How Token Flow Works

```
Login Page                     API Service                    Storage
    │                              │                            │
    │ 1. User enters credentials   │                            │
    │ ─────────────────────────►   │                            │
    │                              │ 2. POST /auth/login        │
    │                              │ ────────────────────────►  │
    │                              │                            │
    │                              │ 3. Receive JWT token       │
    │                              │ ◄────────────────────────  │
    │                              │                            │
    │ 4. tokenManager.setToken()   │ ────────────────────────►  │
    │                              │     sessionStorage         │
    │                              │                            │
    └──────────────────────────────┘                            │
                                                                │
Other Pages                    API Calls                        │
    │                              │                            │
    │ tokenManager.getToken()      │ ◄────────────────────────  │
    │ ◄────────────────────────    │     sessionStorage         │
    │                              │                            │
    │ Use token in Authorization   │                            │
    │ header for API requests      │                            │
    └──────────────────────────────┘
```

---

## 🚨 Common Mistakes & Fixes

### Mistake 1: Copying code from examples that use localStorage

**Wrong:**

```typescript
// Copied from Stack Overflow or old examples
fetch('/api', {
  headers: {
    Authorization: `Bearer ${localStorage.getItem('token')}`,
  },
});
```

**Fix:**

```typescript
import { tokenManager } from '@/services/api';

fetch('/api', {
  headers: {
    Authorization: `Bearer ${tokenManager.getToken()}`,
  },
});
```

### Mistake 2: Using the `apiFetch` helper without understanding it

**The `apiFetch` function in `@/lib/api` already handles
authentication!**

```typescript
import { apiFetch } from '@/lib/api';

// apiFetch automatically includes the Authorization header
const response = await apiFetch<ResponseType>('/api/v1/endpoint');
```

If you're already using `apiFetch`, you don't need to add headers
manually.

### Mistake 3: Checking token existence with wrong storage

**Wrong:**

```typescript
const token = localStorage.getItem('admin_token');
if (!token) {
  // This will ALWAYS be true because token is in sessionStorage!
}
```

**Fix:**

```typescript
import { tokenManager } from '@/services/api';

const token = tokenManager.getToken();
if (!token) {
  // Now correctly checks sessionStorage
}
```

---

## 📝 Template for New Pages with API Calls

```typescript
'use client';

import { useEffect, useState } from 'react';
import { tokenManager } from '@/services/api';
// OR use apiFetch which handles auth automatically:
// import { apiFetch } from '@/lib/api';

export default function MyNewPage() {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Option 1: Using tokenManager with fetch
        const response = await fetch('/api/v1/my-endpoint', {
          headers: {
            Authorization: `Bearer ${tokenManager.getToken()}`,
          },
        });

        // Option 2: Using apiFetch (recommended - handles auth automatically)
        // const response = await apiFetch<MyDataType>('/api/v1/my-endpoint');

        if (!response.ok) throw new Error('Failed to fetch');
        const result = await response.json();
        setData(result);
      } catch (err) {
        console.error('Fetch error:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  // ... rest of component
}
```

---

## 🔗 Related Files

- **Token Manager:** `apps/admin/src/services/api.ts`
- **API Fetch Helper:** `apps/admin/src/lib/api.ts`
- **Auth Context:** `apps/admin/src/context/auth-context.tsx`
- **Login Page:** `apps/admin/src/app/login/page.tsx`

---

## 📜 Historical Context

**January 30, 2025 Bug Fix:**

- Issue 1: Fixed 13 instances of
  `localStorage.getItem('access_token')` (commit 9175bcb)
- Issue 2: Fixed 25 instances of `localStorage.getItem('admin_token')`
  (this fix)
- Total: 38 authentication bugs prevented by this documentation

**Root Cause:** Developers (and AI assistants) were copying patterns
that directly accessed localStorage, not realizing the admin app uses
sessionStorage via tokenManager.

---

**Remember:** When in doubt, use `tokenManager.getToken()`. Never
access storage directly.
