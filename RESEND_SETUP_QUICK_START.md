# 🚀 Resend Email Setup - Quick Start Guide

**Status:** ✅ Code Complete | ⏳ Configuration Required **Time to
Complete:** 15-20 minutes

---

## ✅ What's Already Done

- [x] Backend code migrated to Resend API
- [x] Frontend already has Resend configured
- [x] `resend` package installed (v2.19.0)
- [x] Configuration ready in `config.py`
- [x] Environment variables prepared in `.env`

---

## 🔧 3 Steps to Complete Setup

### **Step 1: Get Resend API Key (2 minutes)**

1. Go to **https://resend.com**
2. Sign up or log in
3. Navigate to **API Keys** section
4. Click "Create API Key"
5. Name it: `MyHibachi Production`
6. Copy the key (starts with `re_`)

7. **Add to `.env` file:**
   ```bash
   # Edit: apps/backend/.env
   RESEND_API_KEY=re_your_actual_key_here  # Replace with your key
   ```

---

### **Step 2: Verify Your Domain (5-10 minutes)**

**In Resend Dashboard:**

1. Go to **Domains** section
2. Click "Add Domain"
3. Enter: `myhibachichef.com`
4. Resend will show 3 DNS records to add

**In Your Domain Registrar (GoDaddy/Namecheap/etc.):**

Add these 3 **TXT records**:

| Type | Host                 | Value                            | TTL  |
| ---- | -------------------- | -------------------------------- | ---- |
| TXT  | `@`                  | `v=spf1 include:resend.com ~all` | 3600 |
| TXT  | `resend._domainkey`  | `[Resend provides this]`         | 3600 |
| TXT  | `resend2._domainkey` | `[Resend provides this]`         | 3600 |

**Example (GoDaddy):**

```
1. Login to GoDaddy
2. My Products → Domain Name → DNS
3. Click "Add" → Select "TXT"
4. Add each record above
5. Save
```

**Wait:**

- DNS propagation: 5-60 minutes
- Check Resend dashboard for "Verified" status ✅

---

### **Step 3: Test Email Sending (5 minutes)**

**Quick Test (Python Shell):**

```bash
cd apps/backend
python
```

```python
# In Python shell:
import os
os.environ['EMAIL_ENABLED'] = 'true'
os.environ['RESEND_API_KEY'] = 'your_actual_key'

from src.services.email_service import email_service

# Test email:
result = email_service.send_welcome_email(
    email="your-email@gmail.com",  # Use your email
    full_name="Test User"
)

print(f"Email sent: {result}")
```

**Check:**

1. Your inbox (should receive welcome email)
2. Resend dashboard → **Emails** → See delivery status
3. If email not in inbox, check spam folder

---

## 🎯 That's It!

**Once all 3 steps done:**

- ✅ Emails will send via Resend
- ✅ Same email addresses (`cs@myhibachichef.com`)
- ✅ Better deliverability (99%+)
- ✅ Email analytics in Resend dashboard
- ✅ $500/year saved (no more IONOS)

---

## 📊 Monitor Email Performance

**Resend Dashboard:** https://resend.com/emails

**What you'll see:**

- ✉️ All emails sent
- ✅ Delivery status (delivered/bounced/failed)
- 👁️ Open rates (who opened emails)
- 🖱️ Click rates (which links clicked)
- 📈 Analytics graphs

---

## 🆘 Troubleshooting

### **Problem: "Email not delivered"**

**Check:**

1. Is `EMAIL_ENABLED=true` in `.env`?
2. Is `RESEND_API_KEY` correct (starts with `re_`)?
3. Is domain verified in Resend dashboard?
4. Check Resend dashboard → **Emails** for error message

**Common fixes:**

- Wait for DNS propagation (up to 1 hour)
- Check spam folder
- Verify API key is correct

---

### **Problem: "Domain not verified"**

**Check:**

1. DNS records added to **correct domain** (`myhibachichef.com`)
2. TXT records (not A or CNAME)
3. Wait 5-60 minutes for DNS propagation
4. Use DNS checker: https://dnschecker.org

---

## 📞 Support

**Resend Support:**

- Docs: https://resend.com/docs
- Support: https://resend.com/support
- Status: https://status.resend.com

**Internal:**

- Code: `apps/backend/src/services/email_service.py`
- Config: `apps/backend/src/core/config.py`
- Env: `apps/backend/.env`

---

## ✅ Success Checklist

- [ ] Step 1: RESEND_API_KEY added to `.env`
- [ ] Step 2: Domain verified in Resend
- [ ] Step 3: Test email sent and received
- [ ] Resend dashboard shows delivered emails
- [ ] Emails arrive in inbox (not spam)

**When all checked:** Migration 100% complete! 🎉

---

**Next Steps After Email Working:**

1. Google Analytics 4 (3-4 hours)
2. Cloudinary Images (2-3 hours)
3. Google Calendar API (3-4 hours)
4. Continue bug fixes (671 remaining)
