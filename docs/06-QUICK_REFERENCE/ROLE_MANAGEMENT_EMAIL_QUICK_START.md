# Role Management & Email System - Quick Start Guide

## 🚀 What We Built

### 1. **Role Management System**
- **Backend**: 6 API endpoints for role assignment/management
- **Frontend**: Complete UI at `/superadmin/roles`
- **Features**:
  - View all roles and permissions
  - Assign/remove roles from users
  - View effective permissions
  - Permission matrix grouped by resource
  - Super admin authorization required

### 2. **Dual SMTP Email System**
- **IONOS SMTP**: Customer-facing emails (cs@myhibachichef.com)
- **Gmail SMTP**: Internal admin communications (myhibachichef@gmail.com)
- **Automatic Routing**: Based on recipient email pattern
- **Email Templates**: Welcome, Approval, Rejection, Suspension

---

## 📋 Prerequisites

### For Email System
1. **IONOS SMTP Credentials**
   - Username: cs@myhibachichef.com
   - Password: Already in `.env`
   - Server: smtp.ionos.com:587

2. **Gmail App Password** (Required!)
   - Visit: https://myaccount.google.com/apppasswords
   - Enable 2-Step Verification first
   - Generate App Password for "Mail"
   - Add to `.env`: `GMAIL_APP_PASSWORD=your_16_char_password`

---

## 🔧 Setup Steps

### Step 1: Configure Gmail App Password

1. Open: https://myaccount.google.com/security
2. Enable **2-Step Verification**
3. Go to: https://myaccount.google.com/apppasswords
4. Select "Mail" → "Other (Custom name)" → "MyHibachi Backend"
5. Click **Generate**
6. Copy the 16-character password (remove spaces)
7. Update `.env`:
   ```env
   GMAIL_APP_PASSWORD=your_16_character_password_here
   ```

### Step 2: Enable Email Notifications

Ensure `.env` has:
```env
EMAIL_NOTIFICATIONS_ENABLED=true
```

### Step 3: Restart Backend Server

```powershell
# Stop current server (Ctrl+C)
# Restart to load new environment variables
cd "C:\Users\surya\projects\MH webapps\apps\backend"
python -m uvicorn src.main:app --reload --port 8000
```

---

## 🧪 Testing

### Test 1: Email Configuration
```powershell
cd "C:\Users\surya\projects\MH webapps\apps\backend"
python test_email_system.py
```

**Expected Output:**
```
✅ SMTP Configuration: PASSED
✅ Email Routing Logic: PASSED
✅ Customer Email: PASSED
✅ Admin Email: PASSED
```

### Test 2: Role Management UI

1. Visit: http://localhost:3001/superadmin
2. Click **"Role Management"** button
3. Select a user from dropdown (ACTIVE users only)
4. **Assign Role**:
   - Click "Assign" button next to a role
   - Role appears in "Current Roles" section
   - Effective permissions update
5. **Remove Role**:
   - Click "Remove" button on a role
   - Role disappears from "Current Roles"
   - Permissions recalculated
6. **Verify Backend**:
   - Check console logs for API calls
   - Look for "Routing email to..." messages

### Test 3: Email Routing

1. **Approve a customer user** (email like user@gmail.com):
   - Backend logs: `Routing email to user@gmail.com via IONOS SMTP`
   - Email sent from: cs@myhibachichef.com

2. **Approve an admin user** (email like admin@myhibachichef.com):
   - Backend logs: `Routing email to admin@myhibachichef.com via GMAIL SMTP`
   - Email sent from: myhibachichef@gmail.com

---

## 📝 API Endpoints

### Role Management (Super Admin Only)

```http
GET /api/v1/admin/roles
# List all roles with permissions

GET /api/v1/admin/roles/{role_id}
# Get specific role details

GET /api/v1/admin/roles/permissions/all
# List all 27 permissions

POST /api/v1/admin/roles/users/{user_id}/roles
# Assign role to user
Body: { "role_id": 2 }

DELETE /api/v1/admin/roles/users/{user_id}/roles/{role_id}
# Remove role from user

GET /api/v1/admin/roles/users/{user_id}/permissions
# Get user's effective permissions
```

### Authorization
All endpoints require:
```http
Authorization: Bearer {super_admin_token}
```

---

## 🔍 Troubleshooting

### Issue: "Email not sending"
**Check:**
1. `EMAIL_NOTIFICATIONS_ENABLED=true` in `.env`
2. Gmail App Password is correct (16 characters)
3. Backend logs for error messages
4. IONOS password is correct

**Solution:**
```powershell
# Test SMTP connection manually
python test_email_system.py
```

### Issue: "Gmail authentication failed"
**Cause:** Using regular password instead of App Password

**Solution:**
1. Generate App Password: https://myaccount.google.com/apppasswords
2. Update `.env`: `GMAIL_APP_PASSWORD=your_app_password`
3. Restart backend server

### Issue: "Role assignment not working"
**Check:**
1. User is ACTIVE status (not PENDING/SUSPENDED)
2. You're logged in as super admin
3. Backend server is running
4. Network tab shows 200 OK response

### Issue: "Permissions not updating"
**Solution:**
- Refresh the page after assigning/removing roles
- Check backend logs for effective permission calculation
- Verify role has permissions in database

---

## 📊 Email Routing Logic

```
┌─────────────────────────────────────┐
│      Incoming Email Request         │
└────────────────┬────────────────────┘
                 │
                 ▼
        ┌────────────────┐
        │ Check Recipient │
        └────────┬────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
┌──────────────┐   ┌──────────────┐
│ Is Admin?    │   │ Is Customer? │
│ @myhibachi.. │   │ Other emails │
│ @gmail.com   │   │              │
│ "admin"      │   │              │
└──────┬───────┘   └──────┬───────┘
       │                  │
       ▼                  ▼
┌──────────────┐   ┌──────────────┐
│ Gmail SMTP   │   │ IONOS SMTP   │
│ Port 587     │   │ Port 587     │
│ myhibachi@.. │   │ cs@myhibachi │
└──────────────┘   └──────────────┘
```

---

## 📈 Next Steps

### 1. Create Custom Roles UI
**File**: `apps/admin/src/app/superadmin/roles/create/page.tsx`

**Features**:
- Role name input
- Role description textarea
- Permission multi-select (grouped by resource)
- System role toggle
- Save button

**Backend Endpoint Needed**:
```http
POST /api/v1/admin/roles
Body: {
  "name": "Station Manager",
  "description": "Manages station operations",
  "permissions": [1, 2, 3, 4],
  "is_system": false
}
```

### 2. Edit Role Permissions
**File**: `apps/admin/src/app/superadmin/roles/[id]/edit/page.tsx`

**Features**:
- Load current permissions
- Add/remove individual permissions
- Save changes

**Backend Endpoint Needed**:
```http
PATCH /api/v1/admin/roles/{role_id}
Body: {
  "name": "Updated Name",
  "permissions": [1, 2, 3, 5, 7]
}
```

### 3. Role Templates
**Features**:
- Pre-configured role templates
- One-click role creation
- Common permission sets

**Templates**:
- **Station Manager**: station.* + booking.read
- **Customer Support**: customer.* + booking.read
- **Marketing Manager**: analytics.* + customer.read
- **Finance**: payment.* + analytics.*

---

## 📚 Documentation

- **Full Email Setup**: `EMAIL_SETUP_GUIDE.md`
- **API Documentation**: `API_DOCUMENTATION.md`
- **RBAC Implementation**: `4_TIER_RBAC_IMPLEMENTATION_PLAN.md`

---

## ✅ Checklist

### Email System
- [x] SMTP implementation (IONOS + Gmail)
- [x] Automatic routing logic
- [x] Email templates (4 types)
- [x] Environment configuration
- [ ] Gmail App Password configured
- [ ] Email system tested
- [ ] Production email limits checked

### Role Management
- [x] Backend API (6 endpoints)
- [x] Frontend UI (/superadmin/roles)
- [x] Role assignment
- [x] Permission matrix
- [x] Super admin authorization
- [ ] UI tested end-to-end
- [ ] Custom role creation (future)
- [ ] Role templates (future)

---

## 🎯 Current Status

**Backend Server**: ✅ Running on port 8000
- Role Management endpoints loaded
- Email service with SMTP ready
- Auto-reload working

**Frontend**: ✅ Running on localhost:3001
- Role Management UI compiled
- No errors in code
- Ready to test

**Configuration**: ⏳ Partial
- IONOS SMTP: ✅ Configured
- Gmail SMTP: ⏳ Need App Password
- Email Enabled: ✅ Yes

**Next Actions**:
1. Generate Gmail App Password
2. Update `.env` with `GMAIL_APP_PASSWORD`
3. Restart backend server
4. Run `test_email_system.py`
5. Test Role Management UI
6. Verify email routing

---

## 💡 Tips

- **Email Volume**: Currently <50/day, well within IONOS/Gmail limits
- **Scaling**: When >50/day, consider SendGrid/Mailgun
- **Security**: Gmail App Password is more secure than regular password
- **Testing**: Use test_email_system.py before production
- **Monitoring**: Check backend logs for email routing decisions
- **Backup**: Keep both SMTP providers configured for redundancy

---

## 🆘 Support

If you encounter issues:

1. **Check Logs**: `apps/backend/logs/app.log`
2. **Test SMTP**: `python test_email_system.py`
3. **Verify Config**: Print environment variables
4. **Review Guide**: `EMAIL_SETUP_GUIDE.md`

Common log patterns:
```
✅ Good: "Routing email to user@example.com via IONOS SMTP"
✅ Good: "Email sent successfully via IONOS"
❌ Bad: "SMTP authentication failed"
❌ Bad: "Connection timeout to smtp.ionos.com"
```
