# 🌐 Webhook Testing Guide - Temporary Public URL Setup

## Overview
Before production deployment, we need to test all webhook integrations using a temporary public URL.

---

## 🚀 Option 1: ngrok (Recommended - FREE)

### Installation

**Method 1: Direct Download**
1. Go to: https://ngrok.com/download
2. Download Windows version
3. Extract `ngrok.exe` to a folder (e.g., `C:\ngrok`)
4. Add to PATH or run from that folder

**Method 2: Using Chocolatey**
```powershell
choco install ngrok
```

**Method 3: Using Scoop**
```powershell
scoop install ngrok
```

### Setup & Usage

#### 1. Sign up for free account (optional but recommended)
- Go to: https://dashboard.ngrok.com/signup
- Get your auth token from: https://dashboard.ngrok.com/get-started/your-authtoken

#### 2. Authenticate ngrok (if you signed up)
```powershell
ngrok config add-authtoken YOUR_AUTH_TOKEN_HERE
```

#### 3. Start your backend server
```powershell
cd "c:\Users\surya\projects\MH webapps\apps\backend"
# Activate virtual environment first
..\..\.venv\Scripts\Activate.ps1
# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 4. In a NEW terminal, start ngrok
```powershell
ngrok http 8000
```

#### 5. You'll see output like:
```
Session Status                online
Account                       Your Name (Plan: Free)
Version                       3.3.1
Region                        United States (us)
Latency                       -
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123.ngrok-free.app -> http://localhost:8000
```

**Your temporary URL:** `https://abc123.ngrok-free.app`

#### 6. Update webhook URLs (temporarily)
Use this URL for all webhook configurations:
- RingCentral: `https://abc123.ngrok-free.app/api/v1/webhooks/ringcentral`
- Meta: `https://abc123.ngrok-free.app/api/v1/webhooks/meta`
- Stripe: `https://abc123.ngrok-free.app/api/v1/webhooks/stripe`

---

## 🌐 Option 2: Cloudflare Tunnel (FREE, No Account Needed)

### Installation
```powershell
# Using winget
winget install Cloudflare.cloudflared

# Or download from: https://github.com/cloudflare/cloudflared/releases
```

### Usage
```powershell
# Start your backend first (port 8000)
# Then in another terminal:
cloudflared tunnel --url http://localhost:8000
```

You'll get a URL like: `https://random-words.trycloudflare.com`

**Pros:**
- ✅ No account needed
- ✅ Very fast
- ✅ No time limits

**Cons:**
- ❌ URL changes each time you restart
- ❌ Random URL (not custom)

---

## 🔧 Option 3: LocalTunnel (FREE, NPM-based)

### Installation
```powershell
npm install -g localtunnel
```

### Usage
```powershell
# Start your backend first (port 8000)
# Then:
lt --port 8000 --subdomain myhibachi
```

You'll get: `https://myhibachi.loca.lt`

**Pros:**
- ✅ Can choose subdomain
- ✅ Simple to use

**Cons:**
- ❌ Sometimes unreliable
- ❌ May require browser password

---

## 🎯 Recommended: Use ngrok

**Reasons:**
1. ✅ Most reliable
2. ✅ Great dashboard at `http://localhost:4040` to see all requests
3. ✅ Free tier is generous (no credit card needed)
4. ✅ Can replay requests for debugging
5. ✅ Widely used and trusted

---

## 📋 Testing Checklist

Once you have your public URL, test these integrations:

### ✅ 1. Stripe Webhooks
- [ ] Go to: https://dashboard.stripe.com/test/webhooks
- [ ] Update webhook endpoint to: `https://YOUR-NGROK-URL/api/v1/webhooks/stripe`
- [ ] Test events:
  - [ ] `payment_intent.succeeded`
  - [ ] `payment_intent.payment_failed`
  - [ ] `charge.refunded`

### ✅ 2. RingCentral Webhooks
- [ ] Go to: https://developers.ringcentral.com/my-account.html#/applications
- [ ] Click your app: "My Hibachi CRM"
- [ ] Update webhook URL: `https://YOUR-NGROK-URL/api/v1/webhooks/ringcentral`
- [ ] Test events:
  - [ ] Send SMS to +19167408768
  - [ ] Check if webhook receives it
  - [ ] Test AI auto-reply

### ✅ 3. Meta (Facebook/Instagram) Webhooks
- [ ] Go to: https://developers.facebook.com/apps/YOUR_APP_ID/webhooks/
- [ ] Update webhook URL: `https://YOUR-NGROK-URL/api/v1/webhooks/meta`
- [ ] Verify token: Your custom verify token from .env
- [ ] Test events:
  - [ ] Send message to Facebook Page
  - [ ] Send message to Instagram
  - [ ] Check AI auto-replies

### ✅ 4. Google Business Profile
- [ ] Test review fetching
- [ ] Test auto-responses
- [ ] Test customer verification for <3 star reviews

### ✅ 5. Plaid Banking
- [ ] Test transaction sync
- [ ] Test payment matching algorithm
- [ ] Test unmatched payment notifications

### ✅ 6. OpenAI Integration
- [ ] Test AI SMS responses
- [ ] Test AI Messenger responses
- [ ] Test human escalation triggers
- [ ] Test sentiment analysis

### ✅ 7. Google Maps Travel Fee
- [ ] Test distance calculation
- [ ] Test fee calculation
- [ ] Test various addresses
- [ ] Verify pricing rules

---

## 🔍 Debugging with ngrok Dashboard

When using ngrok, open: `http://localhost:4040`

**Features:**
- 📊 See all incoming requests in real-time
- 🔁 Replay requests for debugging
- 📝 Inspect request/response headers and body
- ⚡ Filter and search requests
- 📈 Monitor traffic patterns

---

## 🎬 Step-by-Step Testing Flow

### 1. Start Backend
```powershell
cd "c:\Users\surya\projects\MH webapps\apps\backend"
..\..\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start ngrok (New Terminal)
```powershell
ngrok http 8000
```

### 3. Copy Your Public URL
Example: `https://abc123.ngrok-free.app`

### 4. Update Each Webhook Configuration
Replace `YOUR-NGROK-URL` with your actual ngrok URL in:
- Stripe dashboard
- RingCentral developer portal
- Meta developer console

### 5. Test Each Integration
Send test events and watch:
- ✅ ngrok dashboard (`http://localhost:4040`)
- ✅ Backend logs
- ✅ Database for created records
- ✅ Response messages

### 6. Document Results
Note what works and what needs fixes

---

## ⚠️ Important Notes

### ngrok Free Plan Limits:
- ✅ Unlimited requests
- ✅ HTTPS by default
- ✅ Dashboard access
- ❌ URL changes when you restart (unless paid plan)
- ❌ Session timeout after 2 hours of inactivity

### For Paid ngrok ($8/month):
- ✅ Fixed subdomain: `https://myhibachi.ngrok.io`
- ✅ No session timeout
- ✅ Custom domains
- ✅ More concurrent tunnels

### Security:
- 🔒 ngrok URLs are temporary - don't commit them to git
- 🔒 Don't share ngrok URL publicly
- 🔒 Only use for testing, not production
- 🔒 Stop ngrok when done testing

---

## 🚀 After Testing Successfully

Once all webhooks are tested and working:

1. ✅ Deploy backend to production server
2. ✅ Get production domain (e.g., `mhapi.mysticdatanode.net`)
3. ✅ Update all webhook URLs to production
4. ✅ Re-test in production
5. ✅ Monitor for errors

---

## 📞 Support & Resources

- **ngrok Docs:** https://ngrok.com/docs
- **ngrok Dashboard:** https://dashboard.ngrok.com
- **Cloudflare Tunnel:** https://developers.cloudflare.com/cloudflare-one/connections/connect-apps
- **LocalTunnel:** https://github.com/localtunnel/localtunnel

---

**Next Steps:** 
1. Install ngrok
2. Start backend server
3. Start ngrok tunnel
4. Test all webhook integrations
5. Document results and issues

**Status:** Ready to begin webhook testing
**Last Updated:** October 27, 2025
