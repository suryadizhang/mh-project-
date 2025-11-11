# 🚀 Google OAuth Setup - Quick Start

**Your Project:** My Hibachi CRM  
**Project Number:** 28565005233  
**Project ID:** `my-hibachi-crm`  
**Status:** ✅ Ready to use (Free Trial: $300 credits, expires Jan 26, 2026)

---

## ✅ Step 1: Enable Required APIs (5 minutes)

### 1.1 Enable Google+ API
1. In your Google Cloud Console, click on the **hamburger menu** (☰) at top-left
2. Go to: **APIs & Services** → **Library**
3. Search for: `Google+ API`
4. Click **Enable**

### 1.2 Enable People API (for profile info)
1. While in **Library**, search for: `People API`
2. Click **Enable**

**✅ Done!** Your APIs are now active.

---

## 🔐 Step 2: Create OAuth 2.0 Credentials (10 minutes)

### 2.1 Configure OAuth Consent Screen (First Time Only)

1. Go to: **APIs & Services** → **OAuth consent screen**
2. Choose **External** (allows any Google account)
3. Click **Create**

**Fill in the form:**
```
App name: MyHibachi Admin
User support email: [Your email - select from dropdown]
Developer contact information: [Your email]
```

4. Click **Save and Continue**

**Add Scopes:**
5. Click **Add or Remove Scopes**
6. Select these scopes:
   - ✅ `.../auth/userinfo.email`
   - ✅ `.../auth/userinfo.profile`
   - ✅ `openid`
7. Click **Update** → **Save and Continue**

**Test Users:**
8. Click **Add Users**
9. Add your email address (and any test accounts)
10. Click **Save and Continue**

11. Review summary → Click **Back to Dashboard**

---

### 2.2 Create OAuth Client ID

1. Go to: **APIs & Services** → **Credentials**
2. Click **+ Create Credentials** → **OAuth Client ID**

**Configure:**
```
Application type: Web application
Name: MyHibachi Admin OAuth
```

**Authorized redirect URIs** - Click **+ Add URI** twice:
```
http://localhost:8000/auth/google/callback
http://localhost:3001/auth/callback
```

3. Click **Create**

**🎉 Success!** You'll see a popup with:
- **Client ID**: `something.apps.googleusercontent.com`
- **Client Secret**: `GOCSPX-xxxxxxxxxxxxx`

**⚠️ IMPORTANT: Copy both values now!**

---

## 📝 Step 3: Update Environment Variables (5 minutes)

### 3.1 Backend Configuration

Open `apps/backend/.env` and add these lines:

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=YOUR_CLIENT_ID.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=YOUR_CLIENT_SECRET
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# Frontend URL
FRONTEND_URL=http://localhost:3001
```

**Replace:**
- `YOUR_CLIENT_ID` with the Client ID you copied
- `YOUR_CLIENT_SECRET` with the Client Secret you copied

### 3.2 Frontend Configuration

Create/edit `apps/admin/.env.local`:

```bash
NEXT_PUBLIC_GOOGLE_CLIENT_ID=YOUR_CLIENT_ID.apps.googleusercontent.com
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**✅ Done!** Environment configured.

---

## 🗄️ Step 4: Run Database Migration (2 minutes)

Open PowerShell in your project:

```powershell
cd "C:\Users\surya\projects\MH webapps\apps\backend"

# Activate virtual environment (if not already active)
& "C:/Users/surya/projects/MH webapps/.venv/Scripts/Activate.ps1"

# Run migration
alembic upgrade head
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Running upgrade 004 -> 005, add users table
```

**Verify it worked:**
```powershell
python check_tables.py | Select-String "users"
```

**Should show:** `identity.users`

**✅ Done!** Database ready.

---

## 🔌 Step 5: Register OAuth Router (3 minutes)

### 5.1 Edit Router File

Open `apps/backend/src/api/v1/router.py` and find the imports section at the top.

**Add this import:**
```python
from api.v1.endpoints import google_oauth
```

**Then find where routers are registered (look for `api_router.include_router`) and add:**
```python
api_router.include_router(google_oauth.router, tags=["Authentication"])
```

**✅ Done!** OAuth endpoints registered.

---

## 🧪 Step 6: Test Backend (5 minutes)

### 6.1 Start Backend Server

```powershell
cd "C:\Users\surya\projects\MH webapps\apps\backend"

# If not already running:
python -m uvicorn main:app --reload --port 8000
```

### 6.2 Test OAuth Endpoint

Open a **new PowerShell window** and test:

```powershell
Invoke-WebRequest -Uri "http://localhost:8000/auth/google/authorize" -MaximumRedirection 0 -ErrorAction SilentlyContinue
```

**Expected:** Should show `StatusCode: 307` (redirect)

**Or test in browser:**
1. Open: http://localhost:8000/auth/google/authorize
2. Should redirect to Google login page
3. **Don't complete login yet** - we need frontend first

**✅ Done!** Backend is working.

---

## 🎨 Next Steps: Frontend Implementation

Now that backend is configured and working, you need to:

1. **Create user approval endpoints** (30 min)
2. **Install @react-oauth/google** (5 min)
3. **Build frontend pages** (2-3 hours):
   - Login page with Google button
   - OAuth callback handler
   - Pending approval page
   - User management dashboard

**📖 Full instructions:** See [GOOGLE_OAUTH_IMPLEMENTATION_GUIDE.md](GOOGLE_OAUTH_IMPLEMENTATION_GUIDE.md) starting from Step 3.

---

## 🐛 Troubleshooting

### ❌ "redirect_uri_mismatch" error
**Fix:** Go back to Google Cloud Console → Credentials → Edit your OAuth client → Make sure these URIs are **exactly** listed:
```
http://localhost:8000/auth/google/callback
http://localhost:3001/auth/callback
```

### ❌ "OAuth not configured" error
**Fix:** Check your `.env` file has `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` correctly set.

### ❌ Alembic migration error
**Fix:** Make sure you're in the backend directory and virtual environment is activated.

---

## 📋 Quick Checklist

**Google Cloud Console:**
- [ ] Google+ API enabled
- [ ] People API enabled
- [ ] OAuth consent screen configured
- [ ] OAuth Client ID created
- [ ] Client ID and Secret copied

**Backend:**
- [ ] `.env` file updated with credentials
- [ ] Database migration run successfully
- [ ] OAuth router registered in `router.py`
- [ ] Backend server running
- [ ] OAuth endpoint tested

**Frontend:**
- [ ] `.env.local` created with Client ID
- [ ] (Next: Install packages and build pages)

---

**Current Status:** Ready for frontend implementation! 🎉

**Estimated time to complete:** 3-4 hours for full frontend + testing
