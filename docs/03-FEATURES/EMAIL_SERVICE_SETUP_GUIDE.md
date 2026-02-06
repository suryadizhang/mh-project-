# 🔐 Email Service Configuration Guide

## IONOS Business Email Setup

Your MH Webapps project is configured to use IONOS Business Email SMTP
for transactional emails (booking confirmations, receipts, admin
notifications).

---

## ✅ What You Need

Before deployment, you'll need these IONOS email credentials:

1. **Email Address**: Your IONOS business email (e.g.,
   `bookings@myhibachichef.com`)
2. **SMTP Password**: Your IONOS email password or app-specific
   password
3. **SMTP Server**: Usually `smtp.ionos.com` or `smtp.1and1.com`
4. **SMTP Port**: `587` (recommended) or `465` (SSL)

---

## 🔒 Security: Never Commit Secrets!

### ✅ What IS safe (already in repo):

- `.env.example` files with placeholder values
- Configuration code without actual credentials
- Email templates (HTML files)

### ❌ What is NEVER committed:

- `.env` files with real credentials
- Any file containing actual passwords
- SMTP credentials in code

**Your `.gitignore` already protects you!** ✅

---

## 📝 Local Development Setup

### Step 1: Create `.env` file

```bash
# In: apps/backend/.env
cd apps/backend
copy .env.example .env
```

### Step 2: Add your IONOS credentials

Edit `apps/backend/.env` and replace placeholders:

```bash
# ==========================================
# Email Configuration (SMTP)
# ==========================================
EMAIL_ENABLED=True
EMAIL_PROVIDER=smtp

# IONOS SMTP Settings
SMTP_HOST=smtp.ionos.com
SMTP_PORT=587
SMTP_USER=bookings@myhibachichef.com    # ← Your IONOS email
SMTP_PASSWORD=YourSecurePassword123!     # ← Your IONOS password
SMTP_USE_TLS=True

# From Email (must match SMTP_USER)
FROM_EMAIL=bookings@myhibachichef.com    # ← Same as SMTP_USER
EMAILS_FROM_NAME=My Hibachi Chef

# Email Settings
DISABLE_EMAIL=False
EMAIL_TIMEOUT=30
```

### Step 3: Test locally

```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux

# Run backend
cd apps/backend
uvicorn src.api.app.main:app --reload

# Backend will log:
# ✅ Email service initialized: smtp.ionos.com:587 (User: bookings@myhibachichef.com)
```

---

## 🚀 Production Deployment

### Option 1: Vercel (Frontend Apps)

Frontend apps don't need email credentials (backend handles emails).

**No action needed for Vercel!** ✅

---

### Option 2: VPS with Plesk (Backend)

#### Method A: Plesk Environment Variables (Recommended)

1. **Login to Plesk**
2. **Go to**: Websites & Domains → Your Domain → Environment Variables
3. **Add variables**:

   ```
   SMTP_HOST=smtp.ionos.com
   SMTP_PORT=587
   SMTP_USER=bookings@myhibachichef.com
   SMTP_PASSWORD=YourSecurePassword123!
   SMTP_USE_TLS=True
   FROM_EMAIL=bookings@myhibachichef.com
   EMAILS_FROM_NAME=My Hibachi Chef
   ```

4. **Restart application** (Plesk will load env vars automatically)

#### Method B: .env file on VPS (Alternative)

1. **SSH into VPS**:

   ```bash
   ssh your-user@your-vps-ip
   ```

2. **Navigate to app directory**:

   ```bash
   cd /var/www/vhosts/myhibachichef.com/apps/backend
   ```

3. **Create .env file** (never commit this!):

   ```bash
   nano .env
   ```

4. **Add credentials** (same format as local dev)

5. **Set secure permissions**:

   ```bash
   chmod 600 .env
   chown www-data:www-data .env
   ```

6. **Restart application**:
   ```bash
   systemctl restart myhibachi-backend
   ```

---

### Option 3: GitHub Actions CI/CD

#### Step 1: Add Secrets to GitHub

1. **Go to**: GitHub → Your Repo → Settings → Secrets and variables →
   Actions
2. **Click**: "New repository secret"
3. **Add each secret**:

   ```
   Name: SMTP_HOST
   Value: smtp.ionos.com

   Name: SMTP_PORT
   Value: 587

   Name: SMTP_USER
   Value: bookings@myhibachichef.com

   Name: SMTP_PASSWORD
   Value: YourSecurePassword123!

   Name: SMTP_USE_TLS
   Value: True

   Name: FROM_EMAIL
   Value: bookings@myhibachichef.com

   Name: EMAILS_FROM_NAME
   Value: My Hibachi Chef
   ```

#### Step 2: Update GitHub Actions Workflow

Create/update `.github/workflows/deploy.yml`:

```yaml
name: Deploy Backend

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Deploy to VPS
        env:
          # Email secrets from GitHub
          SMTP_HOST: ${{ secrets.SMTP_HOST }}
          SMTP_PORT: ${{ secrets.SMTP_PORT }}
          SMTP_USER: ${{ secrets.SMTP_USER }}
          SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}
          SMTP_USE_TLS: ${{ secrets.SMTP_USE_TLS }}
          FROM_EMAIL: ${{ secrets.FROM_EMAIL }}
          EMAILS_FROM_NAME: ${{ secrets.EMAILS_FROM_NAME }}
        run: |
          # Your deployment script here
          echo "Deploying with email configuration..."
          # Secrets are now available as environment variables
```

---

## 🧪 Testing Email Configuration

### Test 1: Check Configuration

```python
# Run in backend Python shell
from api.app.services.email_service import email_service

# Check if enabled
print(f"Email enabled: {email_service.enabled}")
print(f"SMTP Host: {email_service.smtp_host}")
print(f"SMTP User: {email_service.smtp_user}")
print(f"From Email: {email_service.from_email}")

# Should output:
# ✅ Email enabled: True
# ✅ SMTP Host: smtp.ionos.com
# ✅ SMTP User: bookings@myhibachichef.com
# ✅ From Email: bookings@myhibachichef.com
```

### Test 2: Send Test Email

```python
# Send test booking confirmation
import asyncio
from api.app.services.email_service import send_booking_confirmation

test_booking = {
    'name': 'Test Customer',
    'email': 'your-test-email@gmail.com',  # Use YOUR email
    'date': '2025-11-01',
    'time_slot': '6:00 PM',
    'party_size': 10,
    'address': '123 Test St',
    'city': 'Sacramento',
    'zipcode': '95814',
    'phone': '(916) 123-4567',
    'contact_preference': 'text'
}

asyncio.run(send_booking_confirmation(test_booking))

# Check logs:
# ✅ Email sent successfully: '🍱 Booking Confirmed...' to ['your-test-email@gmail.com']
```

### Test 3: Check Your Inbox

1. **Check inbox** for "Booking Confirmed - My Hibachi Chef"
2. **Verify**:
   - ✅ Email arrives within 30 seconds
   - ✅ Professional HTML template displays correctly
   - ✅ All booking details are correct
   - ✅ Email doesn't go to spam folder

---

## ⚠️ Troubleshooting

### Error: "SMTP Authentication failed"

**Cause**: Wrong credentials or IONOS requires app-specific password

**Solution**:

1. Verify username/password in IONOS control panel
2. Try generating app-specific password in IONOS
3. Check if 2FA is enabled (may require app password)

### Error: "Connection timeout"

**Cause**: Firewall blocking port 587 or wrong SMTP server

**Solution**:

1. Verify SMTP host: `smtp.ionos.com` or `smtp.1and1.com`
2. Try port 465 with SSL instead of 587 with TLS
3. Check VPS firewall allows outbound on ports 587/465

### Error: "Sender address rejected"

**Cause**: FROM_EMAIL doesn't match SMTP_USER

**Solution**:

```bash
# IONOS requires these to match exactly:
SMTP_USER=bookings@myhibachichef.com
FROM_EMAIL=bookings@myhibachichef.com  # ← Must be identical!
```

### Emails going to spam

**Causes**: SPF, DKIM, DMARC not configured

**Solution**:

1. **Add SPF record** in DNS:

   ```
   TXT @ "v=spf1 include:_spf.ionos.com ~all"
   ```

2. **Enable DKIM** in IONOS control panel (email settings)

3. **Add DMARC record**:

   ```
   TXT _dmarc "v=DMARC1; p=quarantine; rua=mailto:postmaster@myhibachichef.com"
   ```

4. **Wait 24-48 hours** for DNS propagation

---

## 📊 Monitoring & Logs

### Check Email Logs

```bash
# Backend logs show all email activity
tail -f /var/log/myhibachi-backend/app.log

# Look for:
# ✅ Email sent successfully: ...
# ⚠️  SMTP error (attempt 1/3): ...
# ❌ Failed to send email after 3 attempts: ...
```

### Email Metrics to Monitor

1. **Success Rate**: Should be >99% after setup
2. **Delivery Time**: Usually <5 seconds
3. **Error Rate**: <1% is normal (invalid emails, etc.)
4. **Spam Reports**: Should be 0%

---

## 🎯 Quick Reference

### IONOS SMTP Settings

```
Host: smtp.ionos.com (or smtp.1and1.com)
Port: 587 (TLS) or 465 (SSL)
Auth: Required (username + password)
From: Must match username
```

### Environment Variables

```bash
# Required for all deployments
SMTP_HOST=smtp.ionos.com
SMTP_PORT=587
SMTP_USER=your-email@yourdomain.com
SMTP_PASSWORD=your-password
SMTP_USE_TLS=True
FROM_EMAIL=your-email@yourdomain.com
```

### Files to Never Commit

```
❌ .env
❌ .env.local
❌ .env.production
❌ Any file with real passwords
✅ .env.example (safe - no real values)
```

---

## 📞 Support

**IONOS Email Issues**: Contact IONOS support (they're very
responsive) **Code Issues**: Check logs at
`apps/backend/src/api/app/services/email_service.py`
**Configuration**: See this guide or `.env.example`

---

**Last Updated**: October 25, 2025  
**Maintained by**: MH Webapps DevOps Team
