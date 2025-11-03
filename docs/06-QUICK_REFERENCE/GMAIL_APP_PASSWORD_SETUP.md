# Gmail App Password Setup Guide

## Step-by-Step Instructions for Payment Email Monitoring

### Prerequisites
- Gmail account: **myhibachichef@gmail.com**
- **2-Factor Authentication (2FA) must be enabled**

---

## Step 1: Enable 2-Factor Authentication (If Not Already Enabled)

1. Go to: https://myaccount.google.com/security
2. Scroll to **"2-Step Verification"**
3. Click **"Get Started"**
4. Follow prompts to add phone number
5. Verify with SMS code
6. ✅ 2FA is now enabled

---

## Step 2: Generate App Password

1. **Go to App Passwords page:**
   - URL: https://myaccount.google.com/apppasswords
   - Or: Google Account → Security → 2-Step Verification → App passwords

2. **Sign in** (if prompted)

3. **Select app and device:**
   - App: Select **"Mail"**
   - Device: Select **"Other (Custom name)"**
   - Enter name: `My Hibachi Payment Monitor`

4. **Click "Generate"**

5. **Copy the 16-character password:**
   ```
   Example: abcd efgh ijkl mnop
   ```
   - ⚠️ **Save this password immediately** - you can't view it again!
   - Remove spaces when adding to `.env`: `abcdefghijklmnop`

---

## Step 3: Add to Backend Environment

1. **Open:** `apps/backend/.env`

2. **Add these lines:**
   ```bash
   # Gmail Integration (Payment Notifications)
   GMAIL_USER=myhibachichef@gmail.com
   GMAIL_APP_PASSWORD=abcdefghijklmnop  # Replace with your 16-char password
   
   # Scheduler Settings
   PAYMENT_EMAIL_CHECK_INTERVAL_MINUTES=5
   PAYMENT_EMAIL_LOOKBACK_DAYS=7
   ```

3. **Save the file**

---

## Step 4: Test the Connection

### Option A: Test Script (Standalone)

```bash
cd apps/backend
python -c "
from services.payment_email_monitor import PaymentEmailMonitor
import os

monitor = PaymentEmailMonitor(
    email_address='myhibachichef@gmail.com',
    app_password=os.getenv('GMAIL_APP_PASSWORD')
)

if monitor.connect():
    print('✅ Successfully connected to Gmail!')
    print('📧 Checking for payment emails...')
    emails = monitor.get_unread_payment_emails()
    print(f'Found {len(emails)} payment notification(s)')
    monitor.disconnect()
else:
    print('❌ Failed to connect - check your credentials')
"
```

### Option B: Test via API (After Backend Starts)

```bash
# Start backend
cd apps/backend
uvicorn main:app --reload

# In another terminal, test the status endpoint
curl http://localhost:8000/api/v1/payments/email-notifications/status
```

**Expected Response:**
```json
{
  "status": "connected",
  "email_address": "myhibachichef@gmail.com",
  "imap_server": "imap.gmail.com",
  "configured": true,
  "last_checked": "2025-10-29T10:30:00Z"
}
```

---

## Step 5: Verify Scheduler is Running

After backend starts, check logs for:

```
✅ Payment email monitoring scheduler started
🔍 Starting scheduled payment email check (run #1)
✅ Email check complete: 0 payment(s) confirmed, 0 email(s) found
```

---

## Troubleshooting

### Error: "Username and password not accepted"
- ❌ **Wrong password** - Regenerate App Password
- ❌ **Spaces in password** - Remove all spaces from 16-char code
- ❌ **Using regular password** - Must use App Password, not Gmail password

### Error: "2-Step Verification required"
- ❌ **2FA not enabled** - Follow Step 1 to enable 2FA first

### Error: "IMAP access disabled"
- Go to: https://mail.google.com/mail/u/0/#settings/fwdandpop
- Enable IMAP access
- Save changes

### Error: "Connection timeout"
- Check firewall settings
- Ensure port 993 is not blocked
- Try different network (not corporate firewall)

---

## Security Best Practices

✅ **DO:**
- Store App Password in `.env` file (never commit to git)
- Revoke old App Passwords if regenerating new ones
- Use different App Passwords for different services

❌ **DON'T:**
- Share App Password with anyone
- Commit `.env` file to version control
- Use regular Gmail password instead of App Password
- Store password in plain text in code

---

## Revoking App Password (If Compromised)

1. Go to: https://myaccount.google.com/apppasswords
2. Find "My Hibachi Payment Monitor"
3. Click **"Remove"**
4. Generate new password and update `.env`

---

## Alternative: OAuth 2.0 (More Secure, More Complex)

If you want even better security, we can implement OAuth 2.0 instead of App Passwords:

**Pros:**
- ✅ More secure (token-based, can be revoked)
- ✅ No password storage
- ✅ Fine-grained permissions

**Cons:**
- ❌ More complex setup
- ❌ Requires Google Cloud Console project
- ❌ Requires browser authentication flow

Let me know if you want to implement OAuth 2.0 instead!

---

## Next Steps

After setup:
1. ✅ Start backend server
2. ✅ Scheduler auto-starts (checks every 5 minutes)
3. ✅ Make a test payment
4. ✅ Wait up to 5 minutes
5. ✅ Payment auto-confirmed!

**Support:** If you encounter issues, check logs in `apps/backend/logs/` or contact your dev team.
