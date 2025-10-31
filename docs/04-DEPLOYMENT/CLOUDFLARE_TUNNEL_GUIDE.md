# 🚀 Quick Start: Cloudflare Tunnel for Webhook Testing

## Why Cloudflare Tunnel?
- ✅ **FREE** - No account needed
- ✅ **Fast** - Very low latency
- ✅ **Secure** - HTTPS by default
- ✅ **No Installation Issues** - Direct exe download
- ✅ **No Time Limits** - Run as long as you need

---

## 🎯 Quick Setup (2 Steps)

### Step 1: Download Cloudflare Tunnel
```powershell
# Create directory
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\cloudflared"

# Download cloudflared
Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -OutFile "$env:USERPROFILE\cloudflared\cloudflared.exe"
```

### Step 2: Start Your Tunnel
```powershell
# Make sure your backend is running on port 8000 first!
cd "$env:USERPROFILE\cloudflared"
.\cloudflared.exe tunnel --url http://localhost:8000
```

You'll see output like:
```
Your quick Tunnel has been created! Visit it at (it may take some time to be reachable):
https://random-words-1234.trycloudflare.com
```

**Copy that URL** - that's your temporary webhook URL!

---

## 🎬 Complete Testing Workflow

### Terminal 1: Start Backend
```powershell
cd "c:\Users\surya\projects\MH webapps\apps\backend"
..\..\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2: Start Cloudflare Tunnel
```powershell
cd "$env:USERPROFILE\cloudflared"
.\cloudflared.exe tunnel --url http://localhost:8000
```

### Terminal 3: Run Tests
```powershell
# Once you have your tunnel URL, test the API:
$TUNNEL_URL = "https://YOUR-TUNNEL-URL.trycloudflare.com"

# Test health check
Invoke-WebRequest -Uri "$TUNNEL_URL/health" | Select-Object StatusCode, Content

# Test your endpoints
curl "$TUNNEL_URL/api/v1/health"
```

---

## 📋 Webhook URLs to Configure

Once you have your Cloudflare Tunnel URL (e.g., `https://abc-xyz.trycloudflare.com`), update these:

### 1. Stripe
- Dashboard: https://dashboard.stripe.com/test/webhooks
- URL: `https://YOUR-TUNNEL-URL.trycloudflare.com/api/v1/webhooks/stripe`

### 2. RingCentral
- Dashboard: https://developers.ringcentral.com/my-account.html#/applications
- URL: `https://YOUR-TUNNEL-URL.trycloudflare.com/api/v1/webhooks/ringcentral`

### 3. Meta (Facebook/Instagram)
- Dashboard: https://developers.facebook.com/apps/1839409339973429/webhooks/
- URL: `https://YOUR-TUNNEL-URL.trycloudflare.com/api/v1/webhooks/meta`
- Verify Token: `myhibachi-meta-webhook-verify-token-2025`

---

## 🧪 Testing Each Integration

### Test RingCentral SMS
```powershell
# Send SMS to test number
# Watch your backend logs
# Should receive webhook
# AI should auto-reply
```

### Test Stripe Payment
```powershell
# Create test payment in Stripe dashboard
# Webhook should trigger
# Check database for payment record
```

### Test Meta Messenger
```powershell
# Send message to Facebook Page
# Webhook should trigger
# AI should auto-reply
```

---

## ⚠️ Important Notes

- 🔄 **URL Changes:** Cloudflare Tunnel gives you a new URL each time you restart
- ⏱️ **No Time Limit:** Unlike ngrok free, no 2-hour timeout
- 🔒 **Security:** Don't commit tunnel URLs to git
- 🛑 **Stop When Done:** Press Ctrl+C to stop the tunnel

---

## 🎯 After Testing

Once all tests pass:
1. ✅ Document what works
2. ✅ Note any issues
3. ✅ Prepare for production deployment
4. ✅ Update webhook URLs to production domain

---

**Ready to start?** Run the commands above! 🚀
