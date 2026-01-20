# Email Configuration Guide

## Overview
The system uses **exactly 2 active email accounts**:
- **IONOS (cs@myhibachichef.com)**: Official external/customer-facing emails (provided by IONOS webmail)
- **Gmail (myhibachichef@gmail.com)**: Internal admin communications only (free Gmail account)

**Note**: These are the only two emails in use. No other email accounts are needed.

## Environment Variables

Add these to your `.env` file:

```env
# ==================== EMAIL CONFIGURATION ====================

# Enable email notifications
EMAIL_NOTIFICATIONS_ENABLED=true

# Default sender information
EMAIL_FROM_ADDRESS=cs@myhibachichef.com
EMAIL_FROM_NAME=MyHibachi Chef Team

# Frontend URL for email links
FRONTEND_URL=https://admin.mysticdatanode.net

# ==================== IONOS SMTP (Customer Emails) ====================
# For customer-facing communications (approvals, welcome, etc.)

SMTP_HOST=smtp.ionos.com
SMTP_PORT=587
SMTP_USERNAME=cs@myhibachichef.com
SMTP_PASSWORD=your_ionos_password_here
SMTP_USE_TLS=true

# ==================== GMAIL SMTP (Internal Admin) ====================
# For internal admin communications

GMAIL_USERNAME=myhibachichef@gmail.com
GMAIL_APP_PASSWORD=your_gmail_app_password_here

# Note: Gmail requires an "App Password" not your regular password
# To create an App Password:
# 1. Go to https://myaccount.google.com/security
# 2. Enable 2-Step Verification
# 3. Go to "App passwords"
# 4. Generate a new app password for "Mail"
# 5. Use that 16-character password here
```

## IONOS Email Setup

### Step 1: Get IONOS SMTP Credentials
1. Log in to IONOS Control Panel
2. Go to Email & Office → Email Accounts
3. Select cs@myhibachichef.com
4. Note the SMTP settings:
   - **Server**: smtp.ionos.com
   - **Port**: 587 (with STARTTLS) or 465 (with SSL)
   - **Username**: cs@myhibachichef.com
   - **Password**: Your email password

### Step 2: Configure Firewall
Ensure your server can access:
- smtp.ionos.com on port 587

### Step 3: Test Connection
```bash
# Test IONOS SMTP connection
python -c "
import smtplib
server = smtplib.SMTP('smtp.ionos.com', 587)
server.starttls()
server.login('cs@myhibachichef.com', 'YOUR_PASSWORD')
print('✅ IONOS SMTP connection successful!')
server.quit()
"
```

## Gmail Setup for Admin Emails

### Step 1: Enable 2-Step Verification
1. Go to https://myaccount.google.com/security
2. Click "2-Step Verification"
3. Follow the setup process

### Step 2: Generate App Password
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and "Other (Custom name)"
3. Name it "MyHibachi Backend"
4. Click "Generate"
5. Copy the 16-character password (spaces removed)

### Step 3: Test Connection
```bash
# Test Gmail SMTP connection
python -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('myhibachichef@gmail.com', 'YOUR_APP_PASSWORD')
print('✅ Gmail SMTP connection successful!')
server.quit()
"
```

## Email Routing Logic

The system automatically routes emails based on recipient:

### Customer Emails (via IONOS)
- Any email NOT ending in @myhibachichef.com or @gmail.com
- Examples:
  - customer@example.com → IONOS
  - john.doe@company.com → IONOS
  - user@outlook.com → IONOS

### Admin Emails (via Gmail)
- Emails ending in @myhibachichef.com
- Emails ending in @gmail.com
- Emails containing "admin" or "staff"
- Examples:
  - admin@myhibachichef.com → Gmail
  - staff@myhibachichef.com → Gmail
  - myhibachichef@gmail.com → Gmail

## Email Types

### 1. Welcome Email
- **Sent when**: New user registers via OAuth
- **Template**: Welcomes user, explains approval process
- **Recipient**: New user (usually customer email)

### 2. Approval Email
- **Sent when**: Super admin approves pending user
- **Template**: Account activated, link to login
- **Recipient**: Approved user

### 3. Rejection Email
- **Sent when**: Super admin rejects pending user
- **Template**: Application declined, contact info
- **Recipient**: Rejected user

### 4. Suspension Email
- **Sent when**: Super admin suspends active user
- **Template**: Account suspended, reason (if provided)
- **Recipient**: Suspended user

## Testing Email System

### Test Script
Create `test_email.py`:

```python
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# Set test mode
os.environ["EMAIL_NOTIFICATIONS_ENABLED"] = "true"

from services.email_service import email_service

async def test_emails():
    print("Testing email system...")
    
    # Test customer email (IONOS)
    print("\n1. Testing customer email via IONOS...")
    success = email_service.send_welcome_email(
        email="test.customer@example.com",
        full_name="Test Customer"
    )
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    
    # Test admin email (Gmail)
    print("\n2. Testing admin email via Gmail...")
    success = email_service.send_approval_email(
        email="admin@myhibachichef.com",
        full_name="Test Admin"
    )
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    
    print("\n✅ Email tests complete!")

if __name__ == "__main__":
    asyncio.run(test_emails())
```

Run:
```bash
cd apps/backend/src
python test_email.py
```

## Troubleshooting

### Issue: "Authentication failed"
**Solution**: 
- Check username/password are correct
- For Gmail, ensure you're using App Password, not regular password
- Verify 2-Step Verification is enabled for Gmail

### Issue: "Connection timeout"
**Solution**:
- Check firewall allows outbound connections on port 587
- Verify SMTP host is correct
- Try alternative port (465 for SSL)

### Issue: "Emails not being sent"
**Solution**:
- Check `EMAIL_NOTIFICATIONS_ENABLED=true` in `.env`
- Verify SMTP credentials are loaded
- Check backend logs for errors

### Issue: "SSL/TLS errors"
**Solution**:
- Use port 587 with STARTTLS
- Or use port 465 with SSL
- Ensure `SMTP_USE_TLS=true`

## Production Checklist

Before going live:

- [ ] IONOS SMTP credentials configured
- [ ] Gmail App Password generated
- [ ] `EMAIL_NOTIFICATIONS_ENABLED=true`
- [ ] Test emails sent successfully
- [ ] Email templates reviewed
- [ ] Sender name and address verified
- [ ] Frontend URL updated to production
- [ ] Firewall rules configured
- [ ] Email logs monitored

## Email Limits

### IONOS
- Typically 500-1000 emails per day per account
- Check your specific IONOS plan

### Gmail
- Free account: 500 emails per day
- Google Workspace: 2000 emails per day

### Current Usage (< 50/day)
- Well within both limits
- Can scale up with:
  - Additional IONOS accounts
  - Google Workspace upgrade
  - Dedicated SMTP service (SendGrid, Mailgun)

## Scaling Up

When you need more than 50 emails/day:

1. **Upgrade to Google Workspace**
   - 2000 emails/day per user
   - Better deliverability
   - Professional email

2. **Add SendGrid/Mailgun**
   - SendGrid: 100 emails/day free, then $14.95/month
   - Mailgun: 5000 emails/month free
   - Better analytics and tracking

3. **Multiple IONOS Accounts**
   - cs@myhibachichef.com (customer service)
   - info@myhibachichef.com (general info)
   - noreply@myhibachichef.com (automated emails)

## Support

For issues:
1. Check backend logs: `apps/backend/logs/email.log`
2. Test SMTP connection manually
3. Verify environment variables loaded
4. Contact IONOS support for SMTP issues
5. Contact Gmail support for App Password issues
