# Google OAuth Integration - Progress Report

**Status**: 🟡 **IN PROGRESS** (Backend 60% Complete)  
**Date**: October 28, 2025  
**Implementation Time So Far**: 30 minutes

---

## 🎯 Objective

Enable users to sign in with any Google account, with super admin approval workflow for new users.

---

## ✅ Completed (Backend)

### 1. **User Model** (`models/user.py`)
Created comprehensive user model with:
- ✅ Multi-provider authentication (Google, Email, Microsoft, Apple)
- ✅ User status workflow (PENDING → ACTIVE → SUSPENDED → DEACTIVATED)
- ✅ Super admin designation
- ✅ Email verification tracking
- ✅ MFA support (TOTP + backup codes)
- ✅ Security features (failed login attempts, account locking)
- ✅ Session management (last login, IP tracking)
- ✅ Approval workflow (approved_by, approved_at, approval_notes)
- ✅ Soft delete support
- ✅ JSONB settings and metadata

**Features:**
```python
class User:
    # Authentication
    email: str (unique, indexed)
    google_id: str (unique, for OAuth)
    auth_provider: Enum (google, email, microsoft, apple)
    
    # Status & Permissions
    status: Enum (pending, active, suspended, deactivated)
    is_super_admin: bool
    is_email_verified: bool
    
    # Security
    mfa_enabled: bool
    failed_login_attempts: int
    locked_until: datetime
    
    # Approval Workflow
    approved_by: UUID  # Super admin who approved
    approved_at: datetime
    approval_notes: str
```

---

### 2. **Database Migration** (`005_add_users_table.py`)
Created Alembic migration with:
- ✅ `identity.users` table with all columns
- ✅ Indexes for performance:
  - Email (case-insensitive unique)
  - Google ID (unique)
  - Status + Created date (for pending approvals)
  - Auth provider + Status (for filtering)
  - Last login (for activity tracking)
- ✅ Foreign key to `station_users` (user_id)
- ✅ Self-referencing foreign key (approved_by)
- ✅ Custom enums (AuthProvider, UserStatus)

**Performance Optimizations:**
- 8 strategic indexes
- Partial indexes (WHERE clauses) to save space
- Composite indexes for multi-column queries

---

### 3. **Google OAuth Service** (`services/google_oauth.py`)
Implemented complete OAuth 2.0 flow:
- ✅ `generate_state_token()` - CSRF protection
- ✅ `get_authorization_url()` - Build Google authorization URL
- ✅ `exchange_code_for_token()` - Convert code to access token
- ✅ `get_user_info()` - Fetch user profile from Google
- ✅ `refresh_access_token()` - Token refresh (for future use)
- ✅ `is_configured()` - Check if OAuth is set up
- ✅ Error handling with detailed logging
- ✅ Async/await with httpx

**OAuth Scopes:**
```python
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile"
]
```

---

### 4. **OAuth API Endpoints** (`api/v1/endpoints/google_oauth.py`)
Created 2 endpoints:

#### **GET /auth/google/authorize**
- ✅ Step 1 of OAuth flow
- ✅ Generates state token
- ✅ Redirects to Google authorization page
- ✅ Handles configuration check

#### **GET /auth/google/callback**
- ✅ Step 2 of OAuth flow
- ✅ Exchanges code for token
- ✅ Fetches user info from Google
- ✅ Creates or updates user in database
- ✅ Handles new user workflow (PENDING status)
- ✅ Handles existing user login
- ✅ Updates last login tracking
- ✅ Generates JWT token
- ✅ Redirects to frontend with token
- ✅ Error handling with user-friendly messages

**New User Flow:**
```
User clicks "Sign in with Google"
  ↓
Google authorization
  ↓
Callback with code
  ↓
Exchange for token
  ↓
Fetch user profile
  ↓
Create user with status=PENDING
  ↓
Redirect to /auth/pending-approval
  ↓
Super admin approves
  ↓
User can log in
```

---

## 🚧 Remaining Work

### **Backend** (40% remaining - 2 hours)

1. **User Approval Endpoints** (30 minutes)
   - GET `/api/admin/users/pending` - List pending users
   - POST `/api/admin/users/{id}/approve` - Approve user
   - POST `/api/admin/users/{id}/reject` - Reject user
   - POST `/api/admin/users/{id}/suspend` - Suspend user
   - Requires super admin permission check

2. **Environment Variables** (15 minutes)
   - Add to `.env`:
     ```
     GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
     GOOGLE_CLIENT_SECRET=your-client-secret
     GOOGLE_REDIRECT_URI=http://localhost:3001/auth/google/callback
     FRONTEND_URL=http://localhost:3001
     ```

3. **Run Database Migration** (15 minutes)
   ```bash
   cd apps/backend
   alembic upgrade head
   ```

4. **Register OAuth Endpoints** (10 minutes)
   - Add to main router in `api/v1/router.py`
   - Test endpoints with curl

5. **Create get_current_user Dependency** (30 minutes)
   - JWT token verification
   - User lookup from database
   - Permission checks

---

### **Frontend** (100% remaining - 2-3 hours)

1. **Install Packages** (5 minutes)
   ```bash
   cd apps/admin
   npm install @react-oauth/google
   ```

2. **Google OAuth Provider** (20 minutes)
   - Wrap app with `<GoogleOAuthProvider>`
   - Add client ID from env

3. **Login Page** (60 minutes)
   - "Sign in with Google" button
   - Redirect to `/auth/google/authorize`
   - Handle callback at `/auth/callback`
   - Store JWT token
   - Redirect to dashboard

4. **Pending Approval Page** (30 minutes)
   - `/auth/pending-approval` page
   - Show message: "Account pending approval"
   - Display email
   - Contact super admin button

5. **Admin User Management** (60 minutes)
   - `/admin/users` page
   - List pending users
   - Approve/Reject buttons
   - User details modal
   - Super admin only access

---

## 📋 Google Cloud Console Setup

**Required before testing:**

1. **Create Project**
   - Go to https://console.cloud.google.com
   - Create project: "MyHibachi Admin"

2. **Enable APIs**
   - Google+ API (for user info)

3. **Create OAuth Credentials**
   - Type: Web application
   - Authorized redirect URIs:
     - `http://localhost:8000/auth/google/callback` (backend)
     - `http://localhost:3001/auth/google/callback` (frontend)
   - Copy Client ID and Secret

4. **Add Test Users** (during development)
   - Add your email addresses

---

## 🔄 OAuth Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                  GOOGLE OAUTH FLOW                          │
└─────────────────────────────────────────────────────────────┘

1. User Action:
   User clicks "Sign in with Google"
   
2. Frontend → Backend:
   GET /auth/google/authorize
   
3. Backend → User:
   Redirect to Google authorization page
   (state token stored for CSRF protection)
   
4. User → Google:
   User logs in and grants permissions
   
5. Google → Backend:
   GET /auth/google/callback?code=xxx&state=yyy
   
6. Backend → Google:
   POST /oauth2/v4/token (exchange code for token)
   
7. Google → Backend:
   Returns: access_token, refresh_token, expires_in
   
8. Backend → Google:
   GET /oauth2/v2/userinfo (fetch user profile)
   
9. Google → Backend:
   Returns: id, email, name, picture, verified_email
   
10. Backend → Database:
    Check if user exists:
    - Exists → Update last_login_at
    - New → Create with status=PENDING
    
11. Backend → Frontend:
    Redirect to:
    - PENDING: /auth/pending-approval?email=xxx
    - ACTIVE: /auth/callback?token=jwt_token
```

---

## 🎨 Frontend Components (To Build)

### **Login Page** (`/login`)
```tsx
<GoogleOAuthProvider clientId={process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID}>
  <div>
    <h1>Sign in to MyHibachi Admin</h1>
    <button onClick={() => window.location.href = '/api/auth/google/authorize'}>
      <GoogleIcon /> Sign in with Google
    </button>
  </div>
</GoogleOAuthProvider>
```

### **Pending Approval Page** (`/auth/pending-approval`)
```tsx
<div>
  <AlertCircle />
  <h2>Account Pending Approval</h2>
  <p>Your account ({email}) is awaiting super admin approval.</p>
  <p>You'll receive an email once approved.</p>
</div>
```

### **User Management Page** (`/admin/users`)
```tsx
<div>
  <h1>User Management</h1>
  <Tabs>
    <Tab label="Pending Approval" count={pendingCount}>
      {pendingUsers.map(user => (
        <UserCard>
          <Avatar src={user.avatar_url} />
          <div>{user.full_name}</div>
          <div>{user.email}</div>
          <div>Signed up: {user.created_at}</div>
          <Button onClick={() => approve(user.id)}>Approve</Button>
          <Button variant="danger" onClick={() => reject(user.id)}>Reject</Button>
        </UserCard>
      ))}
    </Tab>
    <Tab label="Active Users" count={activeCount}>
      {/* Active user list */}
    </Tab>
  </Tabs>
</div>
```

---

## 🧪 Testing Plan

### **Manual Testing:**

1. **New User Sign-Up**
   ```
   1. Click "Sign in with Google"
   2. Choose Google account
   3. Verify redirect to /auth/pending-approval
   4. Check database: status should be PENDING
   5. Super admin approves user
   6. User tries login again
   7. Verify redirect to /dashboard with token
   ```

2. **Existing User Login**
   ```
   1. Approve a user manually in database
   2. User clicks "Sign in with Google"
   3. Verify redirect to /dashboard
   4. Check token is stored
   5. Verify last_login_at updated
   ```

3. **Super Admin Approval Workflow**
   ```
   1. Super admin navigates to /admin/users
   2. Sees pending users
   3. Clicks Approve
   4. Verify user status changed to ACTIVE
   5. Check approved_by and approved_at populated
   ```

### **Automated Testing:**
```bash
# Backend API tests
pytest tests/test_google_oauth.py -v

# Frontend component tests  
npm test -- GoogleLoginButton.test.tsx
```

---

## 📊 Database Schema Summary

```sql
-- New table added
CREATE TABLE identity.users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    google_id VARCHAR(255) UNIQUE,
    full_name VARCHAR(255),
    avatar_url TEXT,
    auth_provider authprovider NOT NULL DEFAULT 'email',
    status userstatus NOT NULL DEFAULT 'pending',
    is_super_admin BOOLEAN DEFAULT FALSE,
    approved_by UUID REFERENCES identity.users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 8 indexes for performance
-- 2 foreign keys (station_users.user_id, users.approved_by)
```

---

## 🔐 Security Features

✅ **CSRF Protection** - State token in OAuth flow  
✅ **Email Verification** - Google verifies emails  
✅ **Approval Workflow** - Super admin approval required  
✅ **JWT Tokens** - Secure session management  
✅ **Account Locking** - Failed login tracking  
✅ **MFA Support** - TOTP + backup codes  
✅ **Audit Logging** - Track all user actions  
✅ **Soft Delete** - Never lose user data  

---

## 📝 Next Steps

**Immediate (< 1 hour):**
1. Set up Google Cloud Console OAuth credentials
2. Add environment variables to `.env`
3. Run database migration
4. Register OAuth endpoints in router
5. Test with curl

**Short-term (2-3 hours):**
1. Build frontend login page
2. Install @react-oauth/google
3. Implement OAuth callback handler
4. Build pending approval page
5. Build admin user management page

**Future Enhancements:**
- Email notifications on approval
- Bulk user approval
- User search and filtering
- Export user list
- Activity logs per user
- Password reset flow (for email auth)
- Multi-factor authentication UI

---

**Status**: Backend 60% complete, Frontend 0% complete  
**Total Time Invested**: 30 minutes  
**Estimated Time Remaining**: 4-5 hours  
**Ready for**: Environment setup and database migration
