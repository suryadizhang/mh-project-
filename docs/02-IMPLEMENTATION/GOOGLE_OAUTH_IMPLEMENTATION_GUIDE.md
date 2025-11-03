# Google OAuth Implementation Guide

This guide walks through completing the Google OAuth integration for MyHibachi Admin.

---

## ⚙️ Step 1: Google Cloud Console Setup (15 min)

### 1.1 Create Project
1. Go to: https://console.cloud.google.com/
2. Click **Select a project** → **New Project**
3. Project name: `MyHibachi Admin`
4. Click **Create**

### 1.2 Enable APIs
1. Navigate to **APIs & Services** → **Library**
2. Search for "Google+ API"
3. Click **Enable**

### 1.3 Create OAuth 2.0 Credentials
1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth Client ID**
3. Configure consent screen (if not done):
   - User Type: **External**
   - App name: `MyHibachi Admin`
   - User support email: Your email
   - Developer contact: Your email
   - Scopes: Add `email`, `profile`, `openid`
   - Test users: Add your email(s)
4. Application type: **Web application**
5. Name: `MyHibachi Admin`
6. **Authorized redirect URIs**:
   ```
   http://localhost:8000/auth/google/callback
   http://localhost:3001/auth/callback
   ```
7. Click **Create**
8. **Copy** the Client ID and Client Secret

---

## 🔧 Step 2: Backend Configuration (15 min)

### 2.1 Update Environment Variables
Edit `apps/backend/.env`:

```bash
# Google OAuth
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# Frontend URL for redirects
FRONTEND_URL=http://localhost:3001
```

### 2.2 Run Database Migration
```powershell
cd apps/backend
alembic upgrade head
```

**Expected output:**
```
INFO [alembic.runtime.migration] Running upgrade 004 -> 005, add users table
```

**Verify:**
```powershell
python check_tables.py | Select-String "users"
```

You should see: `identity.users`

### 2.3 Register OAuth Router
Edit `apps/backend/src/api/v1/router.py`:

```python
from api.v1.endpoints import (
    stations,
    customers,
    bookings,
    reviews,
    # ... other imports
    google_oauth  # ← ADD THIS
)

# Add to router includes
api_router.include_router(google_oauth.router, tags=["Authentication"])
```

### 2.4 Test Backend Endpoints
```powershell
# Start backend (if not running)
cd apps/backend
uvicorn src.main:app --reload --port 8000
```

**Test authorization endpoint:**
```powershell
# PowerShell
Invoke-WebRequest -Uri "http://localhost:8000/auth/google/authorize" -MaximumRedirection 0
```

**Expected:** Redirect to Google (Status 307)

---

## 📝 Step 3: Create User Approval Endpoints (30 min)

Create `apps/backend/src/api/v1/endpoints/user_management.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime, timezone

from db.database import get_db
from models.user import User, UserStatus
from app.auth import get_current_user

router = APIRouter(prefix="/admin/users", tags=["User Management"])


@router.get("/pending", response_model=List[dict])
async def list_pending_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all users pending approval (super admin only)"""
    if not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Super admin access required")
    
    result = await db.execute(
        select(User)
        .where(User.status == UserStatus.PENDING)
        .order_by(User.created_at.desc())
    )
    pending_users = result.scalars().all()
    
    return [
        {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "avatar_url": user.avatar_url,
            "auth_provider": user.auth_provider.value,
            "created_at": user.created_at.isoformat(),
        }
        for user in pending_users
    ]


@router.post("/{user_id}/approve")
async def approve_user(
    user_id: str,
    approval_notes: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Approve a pending user (super admin only)"""
    if not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Super admin access required")
    
    # Get user to approve
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.status != UserStatus.PENDING:
        raise HTTPException(status_code=400, detail="User is not pending approval")
    
    # Approve user
    user.status = UserStatus.ACTIVE
    user.approved_by = current_user.id
    user.approved_at = datetime.now(timezone.utc)
    user.approval_notes = approval_notes
    
    await db.commit()
    await db.refresh(user)
    
    return {
        "success": True,
        "message": f"User {user.email} approved",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "status": user.status.value
        }
    }


@router.post("/{user_id}/reject")
async def reject_user(
    user_id: str,
    rejection_reason: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reject a pending user (super admin only)"""
    if not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Super admin access required")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.status != UserStatus.PENDING:
        raise HTTPException(status_code=400, detail="User is not pending approval")
    
    # Soft delete
    user.deleted_at = datetime.now(timezone.utc)
    user.approval_notes = f"Rejected: {rejection_reason}"
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"User {user.email} rejected"
    }
```

**Register in router:**
```python
# api/v1/router.py
from api.v1.endpoints import user_management

api_router.include_router(user_management.router, tags=["User Management"])
```

---

## 🎨 Step 4: Frontend Integration (2-3 hours)

### 4.1 Install Packages
```powershell
cd apps/admin
npm install @react-oauth/google
```

### 4.2 Update Environment Variables
Create/edit `apps/admin/.env.local`:

```bash
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4.3 Create Login Page
Create `apps/admin/src/app/login/page.tsx`:

```tsx
'use client';

import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  const handleGoogleLogin = () => {
    // Redirect to backend OAuth flow
    window.location.href = `${process.env.NEXT_PUBLIC_API_URL}/auth/google/authorize`;
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow">
        <div className="text-center">
          <h2 className="text-3xl font-bold">MyHibachi Admin</h2>
          <p className="mt-2 text-gray-600">Sign in to access the dashboard</p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        <div className="space-y-4">
          <button
            onClick={handleGoogleLogin}
            className="w-full flex items-center justify-center gap-3 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>
            Sign in with Google
          </button>
        </div>

        <p className="text-xs text-gray-500 text-center">
          By signing in, you agree to our Terms of Service and Privacy Policy.
          New accounts require super admin approval.
        </p>
      </div>
    </div>
  );
}
```

### 4.4 Create OAuth Callback Handler
Create `apps/admin/src/app/auth/callback/page.tsx`:

```tsx
'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

export default function AuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');

  useEffect(() => {
    const token = searchParams.get('token');
    const error = searchParams.get('error');

    if (error) {
      setStatus('error');
      setTimeout(() => router.push('/login'), 3000);
      return;
    }

    if (token) {
      // Store JWT token
      localStorage.setItem('authToken', token);
      setStatus('success');
      
      // Redirect to dashboard
      setTimeout(() => router.push('/dashboard'), 1000);
    } else {
      setStatus('error');
      setTimeout(() => router.push('/login'), 3000);
    }
  }, [searchParams, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        {status === 'loading' && (
          <>
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Completing sign-in...</p>
          </>
        )}
        {status === 'success' && (
          <>
            <svg className="w-12 h-12 text-green-600 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <p className="mt-4 text-gray-600">Sign-in successful! Redirecting...</p>
          </>
        )}
        {status === 'error' && (
          <>
            <svg className="w-12 h-12 text-red-600 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
            <p className="mt-4 text-gray-600">Sign-in failed. Redirecting to login...</p>
          </>
        )}
      </div>
    </div>
  );
}
```

### 4.5 Create Pending Approval Page
Create `apps/admin/src/app/auth/pending-approval/page.tsx`:

```tsx
'use client';

import { useSearchParams } from 'next/navigation';

export default function PendingApprovalPage() {
  const searchParams = useSearchParams();
  const email = searchParams.get('email');

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full p-8 bg-white rounded-lg shadow">
        <div className="text-center">
          <div className="mx-auto w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          
          <h2 className="mt-4 text-2xl font-bold">Account Pending Approval</h2>
          
          <p className="mt-2 text-gray-600">
            Your account {email && <span className="font-semibold">({email})</span>} is awaiting approval from a super administrator.
          </p>
          
          <p className="mt-4 text-sm text-gray-500">
            You'll receive an email notification once your account has been approved. This usually takes 1-2 business days.
          </p>
          
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-800">
              <strong>Need immediate access?</strong><br />
              Contact the administrator at support@myhibachi.com
            </p>
          </div>
          
          <button
            onClick={() => window.location.href = '/login'}
            className="mt-6 w-full px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
          >
            Back to Login
          </button>
        </div>
      </div>
    </div>
  );
}
```

### 4.6 Create User Management Page
Create `apps/admin/src/app/users/page.tsx`:

```tsx
'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';

interface PendingUser {
  id: string;
  email: string;
  full_name: string;
  avatar_url?: string;
  auth_provider: string;
  created_at: string;
}

export default function UserManagementPage() {
  const [pendingUsers, setPendingUsers] = useState<PendingUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [approvalNotes, setApprovalNotes] = useState<{ [key: string]: string }>({});

  useEffect(() => {
    fetchPendingUsers();
  }, []);

  const fetchPendingUsers = async () => {
    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/admin/users/pending`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setPendingUsers(data);
      }
    } catch (error) {
      console.error('Failed to fetch pending users:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (userId: string) => {
    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/admin/users/${userId}/approve`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            approval_notes: approvalNotes[userId] || null,
          }),
        }
      );

      if (response.ok) {
        alert('User approved successfully!');
        fetchPendingUsers(); // Refresh list
      }
    } catch (error) {
      console.error('Failed to approve user:', error);
    }
  };

  const handleReject = async (userId: string) => {
    const reason = prompt('Rejection reason (required):');
    if (!reason) return;

    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/admin/users/${userId}/reject`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ rejection_reason: reason }),
        }
      );

      if (response.ok) {
        alert('User rejected');
        fetchPendingUsers(); // Refresh list
      }
    } catch (error) {
      console.error('Failed to reject user:', error);
    }
  };

  if (loading) {
    return <div className="p-8">Loading...</div>;
  }

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">User Management</h1>

      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b">
          <h2 className="text-xl font-semibold">
            Pending Approvals ({pendingUsers.length})
          </h2>
        </div>

        {pendingUsers.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No pending approvals
          </div>
        ) : (
          <div className="divide-y">
            {pendingUsers.map((user) => (
              <div key={user.id} className="p-4 flex items-start gap-4">
                {user.avatar_url && (
                  <img
                    src={user.avatar_url}
                    alt={user.full_name}
                    className="w-12 h-12 rounded-full"
                  />
                )}
                
                <div className="flex-1">
                  <h3 className="font-semibold">{user.full_name}</h3>
                  <p className="text-sm text-gray-600">{user.email}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    Signed up: {new Date(user.created_at).toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-500">
                    Provider: {user.auth_provider}
                  </p>

                  <input
                    type="text"
                    placeholder="Approval notes (optional)"
                    className="mt-2 w-full px-3 py-2 border rounded"
                    value={approvalNotes[user.id] || ''}
                    onChange={(e) =>
                      setApprovalNotes({ ...approvalNotes, [user.id]: e.target.value })
                    }
                  />
                </div>

                <div className="flex gap-2">
                  <Button
                    onClick={() => handleApprove(user.id)}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    Approve
                  </Button>
                  <Button
                    onClick={() => handleReject(user.id)}
                    variant="destructive"
                  >
                    Reject
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
```

### 4.7 Add Navigation Link
Edit `apps/admin/src/app/AdminLayoutComponent.tsx`:

```tsx
// Add to navigation items
{
  href: '/users',
  label: 'Users',
  icon: UsersIcon,
  requiresSuperAdmin: true,  // Only show to super admins
},
```

---

## 🧪 Step 5: Testing (30 min)

### 5.1 Manual Testing

**Test 1: New User Sign-Up**
1. Navigate to `http://localhost:3001/login`
2. Click "Sign in with Google"
3. Choose Google account
4. Should redirect to `/auth/pending-approval`
5. Check database:
   ```sql
   SELECT email, status, auth_provider FROM identity.users;
   ```
   Status should be `pending`

**Test 2: Super Admin Approval**
1. Manually set a user as super admin:
   ```sql
   UPDATE identity.users 
   SET is_super_admin = true, status = 'active'
   WHERE email = 'your-email@gmail.com';
   ```
2. Log in as super admin
3. Navigate to `/users`
4. Should see pending users
5. Click "Approve"
6. Check database - status should be `active`

**Test 3: Approved User Login**
1. Log out
2. Sign in with approved Google account
3. Should redirect to `/dashboard`
4. Check `localStorage` for `authToken`

### 5.2 Error Cases

**Test: Suspended User**
```sql
UPDATE identity.users SET status = 'suspended' WHERE email = 'test@example.com';
```
Try logging in → Should show error

**Test: Invalid OAuth Config**
```bash
# Remove CLIENT_ID from .env temporarily
```
Try logging in → Should show "OAuth not configured"

---

## 🚀 Step 6: Deployment Considerations

### Production Environment Variables:
```bash
GOOGLE_CLIENT_ID=prod-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=prod-secret
GOOGLE_REDIRECT_URI=https://api.myhibachi.com/auth/google/callback
FRONTEND_URL=https://admin.myhibachi.com
```

### Google Cloud Console - Production:
1. Add production redirect URIs:
   ```
   https://api.myhibachi.com/auth/google/callback
   https://admin.myhibachi.com/auth/callback
   ```
2. Verify domain ownership
3. Submit app for OAuth verification (if needed)

---

## 📋 Checklist

**Backend:**
- [ ] Google Cloud Console OAuth credentials created
- [ ] Environment variables configured
- [ ] Database migration executed
- [ ] OAuth router registered
- [ ] User approval endpoints created
- [ ] Tested `/auth/google/authorize`
- [ ] Tested `/auth/google/callback`

**Frontend:**
- [ ] `@react-oauth/google` installed
- [ ] Environment variables configured
- [ ] Login page created
- [ ] OAuth callback handler created
- [ ] Pending approval page created
- [ ] User management page created
- [ ] Navigation updated

**Testing:**
- [ ] New user sign-up flow tested
- [ ] Super admin approval tested
- [ ] Approved user login tested
- [ ] Error cases tested
- [ ] Database indexes verified

---

## 🆘 Troubleshooting

### "redirect_uri_mismatch" Error
**Cause:** Redirect URI not whitelisted in Google Console  
**Fix:** Add exact URI to authorized redirect URIs

### "User not found" After Approval
**Cause:** Database transaction not committed  
**Fix:** Ensure `await db.commit()` after status update

### Frontend Can't Reach Backend
**Cause:** CORS not configured  
**Fix:** Add CORS middleware in FastAPI:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### JWT Token Not Working
**Cause:** Token expired or invalid secret  
**Fix:** Check `SECRET_KEY` in `.env`, verify token expiration

---

**Total Implementation Time:** 4-5 hours  
**Difficulty:** Intermediate  
**Priority:** High (Security requirement)
