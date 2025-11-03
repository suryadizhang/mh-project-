# 📧 IONOS Email Setup Guide for MyHibachi

**Service:** IONOS Business Email (smtp.ionos.com)  
**Purpose:** Send booking confirmations, review requests, and notifications  
**Time to Setup:** 5 minutes

---

## 🎯 What You Need from IONOS

You need **3 pieces of information** from your IONOS account:

1. **Email Address** - Your business email (e.g., `bookings@myhibachichef.com`)
2. **Email Password** - The password for this email account
3. **SMTP Settings** - Server details (usually same for all IONOS accounts)

---

## 📋 Step-by-Step: Get IONOS Credentials

### Option 1: Via IONOS Dashboard (Recommended)

1. **Log into IONOS**
   - Go to: https://www.ionos.com/
   - Click **Login** (top right)
   - Use your IONOS account credentials

2. **Navigate to Email Settings**
   - Click **Email & Office** in the main menu
   - Or go directly to: https://my.ionos.com/email

3. **Find Your Email Account**
   - Look for your business email (e.g., `bookings@myhibachichef.com`, `info@myhibachichef.com`, or `cs@myhibachichef.com`)
   - Click on it to view settings

4. **Get SMTP Settings**
   - Look for **Email Settings** or **Mail Client Configuration**
   - You should see:
     - **Outgoing Mail Server (SMTP):** smtp.ionos.com
     - **Port:** 587 (TLS) or 465 (SSL)
     - **Username:** Your full email address
     - **Authentication:** Required
     - **Encryption:** TLS/STARTTLS (port 587) or SSL (port 465)

5. **Get/Reset Password**
   - If you don't know the password, click **Change Password** or **Reset Password**
   - Set a new password and save it securely

---

### Option 2: Via IONOS Email Client

If you use IONOS webmail:

1. Go to: https://mail.ionos.com/
2. Log in with your email and password
3. If login works, that's your email password!
4. Go to **Settings → Email Accounts → Server Settings** for SMTP details

---

### Option 3: Check Existing Email Client

If you already have this email set up in Outlook, Apple Mail, or Thunderbird:

1. Open your email client
2. Go to **Account Settings**
3. Look for **Outgoing Server (SMTP)** settings
4. The password is saved there (may need to reveal it)

---

## 🔧 What to Add to Your Backend .env

Once you have your credentials, add these to `apps/backend/.env`:

```bash
# ==========================================
# IONOS Email Configuration
# ==========================================

# Enable email functionality
EMAIL_ENABLED=True
EMAIL_PROVIDER=smtp

# IONOS SMTP Server Settings (Usually the same for all IONOS accounts)
SMTP_HOST=smtp.ionos.com
SMTP_PORT=587
SMTP_USE_TLS=True

# Your Specific Credentials (GET FROM IONOS)
SMTP_USER=bookings@myhibachichef.com    # ← Your actual IONOS email
SMTP_PASSWORD=your-ionos-email-password  # ← Your email password
FROM_EMAIL=bookings@myhibachichef.com    # ← Same as SMTP_USER

# Email Display Name
EMAILS_FROM_NAME="My Hibachi Chef"

# Connection Settings
EMAIL_TIMEOUT=30

# Application URLs (for links in emails)
CUSTOMER_APP_URL=http://localhost:3000   # Development
# CUSTOMER_APP_URL=https://myhibachichef.com  # Production

# Review Platform URLs (for email links)
YELP_REVIEW_URL=https://www.yelp.com/biz/my-hibachi-chef-sacramento
GOOGLE_REVIEW_URL=https://g.page/r/YOUR_GOOGLE_PLACE_ID/review

# Review Coupon Settings
REVIEW_COUPON_DISCOUNT_PERCENTAGE=10
REVIEW_COUPON_VALIDITY_DAYS=90
REVIEW_COUPON_MINIMUM_ORDER_CENTS=5000
```

---

## 🧪 Test Your IONOS Email Setup

### Test 1: Direct SMTP Connection (Python)

```bash
cd apps/backend

# Test SMTP connection directly
python -c "
import smtplib
from email.mime.text import MIMEText

# Your IONOS credentials
smtp_host = 'smtp.ionos.com'
smtp_port = 587
smtp_user = 'bookings@myhibachichef.com'  # Your email
smtp_password = 'your-password'            # Your password

try:
    # Connect to SMTP server
    server = smtplib.SMTP(smtp_host, smtp_port)
    server.set_debuglevel(1)  # Show connection details
    server.starttls()
    server.login(smtp_user, smtp_password)
    print('\n✅ SMTP LOGIN SUCCESSFUL!')
    
    # Send test email
    msg = MIMEText('This is a test email from MyHibachi backend')
    msg['Subject'] = 'MyHibachi Test Email'
    msg['From'] = smtp_user
    msg['To'] = 'your-test-email@gmail.com'  # Your personal email
    
    server.send_message(msg)
    print('✅ TEST EMAIL SENT!')
    server.quit()
    
except Exception as e:
    print(f'\n❌ ERROR: {e}')
"
```

### Test 2: Via Backend API

```bash
# Start your backend first
cd apps/backend/src
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# In another terminal, test email endpoint
curl -X POST http://localhost:8000/api/test/send-email \
  -H "Content-Type: application/json" \
  -d '{
    "to": "your-test-email@gmail.com",
    "subject": "MyHibachi Booking Test",
    "body": "This is a test booking confirmation email from MyHibachi."
  }'

# Check your test email inbox for the message
```

### Test 3: Full Booking Flow

```bash
# 1. Start backend and frontend
cd apps/backend/src
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# In another terminal
cd apps/customer
npm run dev

# 2. Open http://localhost:3000/BookUs
# 3. Fill out booking form
# 4. Use test Stripe card: 4242 4242 4242 4242
# 5. Check your email for booking confirmation!
```

---

## 🚨 Troubleshooting

### Error: "Authentication failed"

**Causes:**
- Wrong password
- Wrong email address
- 2FA enabled (need app-specific password)

**Solutions:**
1. Reset password in IONOS dashboard
2. Verify email address is correct (full address, not just username)
3. If 2FA is enabled, generate an app-specific password in IONOS settings

---

### Error: "Connection timed out" or "Cannot connect to server"

**Causes:**
- Firewall blocking port 587
- Wrong SMTP host
- Internet connection issue

**Solutions:**
1. Try port 465 with SSL instead:
   ```bash
   SMTP_PORT=465
   SMTP_USE_TLS=False
   SMTP_USE_SSL=True
   ```
2. Check firewall settings (allow outbound port 587 or 465)
3. Test connection: `telnet smtp.ionos.com 587`

---

### Error: "Relay access denied"

**Causes:**
- SMTP authentication not enabled
- Using wrong "From" address

**Solutions:**
1. Ensure `SMTP_USER` and `FROM_EMAIL` match
2. Verify authentication is enabled in IONOS
3. Check if email account is active (not suspended)

---

### Error: "SSL/TLS handshake failed"

**Causes:**
- Wrong encryption settings
- Outdated Python SSL library

**Solutions:**
1. Try different port/encryption combo:
   ```bash
   # TLS on port 587
   SMTP_PORT=587
   SMTP_USE_TLS=True
   
   # Or SSL on port 465
   SMTP_PORT=465
   SMTP_USE_TLS=False
   ```
2. Update Python SSL: `pip install --upgrade certifi`

---

### Email sends but recipient doesn't receive

**Causes:**
- Email in spam folder
- Email blocked by recipient's server
- Email address typo

**Solutions:**
1. Check spam/junk folder
2. Whitelist sender email in recipient's settings
3. Verify recipient email address is correct
4. Check IONOS dashboard for "Sent Mail" log

---

## 📊 Common IONOS Email Addresses

Based on typical MyHibachi setup:

| Email Address | Purpose |
|---------------|---------|
| `bookings@myhibachichef.com` | Booking confirmations |
| `info@myhibachichef.com` | General inquiries |
| `cs@myhibachichef.com` | Customer service |
| `noreply@myhibachichef.com` | Automated emails |

**Which one to use?** 
- Use `bookings@` for booking-related emails (recommended)
- Use `info@` for general communications
- Use `noreply@` if you don't want customers to reply

---

## 🔐 Security Best Practices

### Password Security
- ✅ Use a strong, unique password (20+ characters)
- ✅ Store password in `.env` file (never commit to Git)
- ✅ Don't share password with anyone
- ❌ Don't use same password for multiple services

### Email Account Security
- ✅ Enable 2FA in IONOS if available
- ✅ Regularly review sent emails log
- ✅ Use separate email for automated emails vs personal use
- ✅ Monitor for suspicious activity

### Production Deployment
For production (when deploying to live server):
- Use environment variables manager (AWS Secrets Manager, Azure Key Vault)
- Rotate passwords every 90 days
- Use different credentials for production vs development
- Enable email rate limiting to prevent abuse

---

## 📋 Quick Reference Card

```
┌─────────────────────────────────────────────┐
│ IONOS SMTP Quick Reference                  │
├─────────────────────────────────────────────┤
│ Server:      smtp.ionos.com                 │
│ Port:        587 (TLS) or 465 (SSL)         │
│ Username:    your-email@myhibachichef.com   │
│ Password:    [Get from IONOS dashboard]     │
│ From:        Same as username               │
│ Auth:        Required                       │
│ Encryption:  TLS (port 587) or SSL (465)    │
└─────────────────────────────────────────────┘
```

---

## ✅ Checklist

Setup complete when you can check all these:

- [ ] Found IONOS email address
- [ ] Got/reset email password
- [ ] Confirmed SMTP settings (host, port)
- [ ] Added all values to `apps/backend/.env`
- [ ] Tested direct SMTP connection (Python test)
- [ ] Backend starts without email errors
- [ ] API test email sends successfully
- [ ] Received test email in inbox (not spam)
- [ ] Full booking flow sends confirmation email

**All checked?** 🎉 **IONOS Email Setup Complete!**

---

## 🆘 Still Having Issues?

### IONOS Support
- **Website:** https://www.ionos.com/help
- **Phone Support:** Check your IONOS dashboard for support number
- **Email Support:** Often available through IONOS control panel
- **Documentation:** https://www.ionos.com/help/email/

### Common Support Questions to Ask:
1. "What are the SMTP server settings for my email account?"
2. "How do I reset my email password?"
3. "Is my email account active and able to send emails?"
4. "Are there any rate limits on outbound emails?"
5. "Do I need to enable SMTP specifically for my account?"

---

## 📧 Example: Complete Working Configuration

Here's a real example (with fake password):

```bash
# This is what your working config should look like:
EMAIL_ENABLED=True
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.ionos.com
SMTP_PORT=587
SMTP_USER=bookings@myhibachichef.com
SMTP_PASSWORD=MySecureP@ssw0rd123!
SMTP_USE_TLS=True
FROM_EMAIL=bookings@myhibachichef.com
EMAILS_FROM_NAME="My Hibachi Chef"
EMAIL_TIMEOUT=30
CUSTOMER_APP_URL=http://localhost:3000
```

**Replace:**
- `bookings@myhibachichef.com` → Your actual IONOS email
- `MySecureP@ssw0rd123!` → Your actual IONOS password

---

**Setup Time:** 5 minutes  
**Cost:** Included with IONOS hosting (usually)  
**Difficulty:** Easy  
**Impact:** Critical for booking system functionality

**Next Step:** After setup, test with [QUICK_ACTION_CHECKLIST.md](./QUICK_ACTION_CHECKLIST.md)
