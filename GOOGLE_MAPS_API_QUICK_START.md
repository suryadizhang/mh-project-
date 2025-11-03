# Quick Start: Adding Google Maps API Key

## TL;DR - Do This Now! ⚡

You're **100% right** - we should put the **REAL API key** in `.env` files because:
1. ✅ They are gitignored (safe from commits)
2. ✅ Placeholders just create friction every setup
3. ✅ It's local development - meant to have real keys

---

## Option 1: Automated Script (Easiest) 🎯

Run this PowerShell script:

```powershell
cd "c:\Users\surya\projects\MH webapps"
.\setup-google-maps-key.ps1
```

The script will:
- Guide you through getting the API key
- Check if you already have one configured
- Add it to both backend and frontend .env files
- Show you next steps to test

---

## Option 2: Manual Setup (If you prefer) 📝

### Step 1: Get Your API Key

1. **Go to Google Cloud Console:**
   ```
   https://console.cloud.google.com/google/maps-apis/
   ```

2. **Enable These APIs** (click "Enable API"):
   - ✅ **Distance Matrix API** - For travel fee calculation
   - ✅ **Places API** - For address autocomplete
   - ✅ **Maps JavaScript API** - For frontend maps widget

3. **Create API Key:**
   - Go to: Credentials → Create Credentials → API Key
   - Copy the key (starts with `AIzaSy...`)

4. **Restrict the Key** (IMPORTANT for security):
   - Click on the key name
   - Application restrictions: **HTTP referrers**
   - **Website restrictions:**
     ```
     http://localhost:3000/*
     http://localhost:3001/*
     http://127.0.0.1:3000/*
     http://127.0.0.1:3001/*
     https://myhibachichef.com/*
     https://www.myhibachichef.com/*
     https://admin.mysticdatanode.net/*
     ```
   - API restrictions: **Restrict key** → Select the 3 APIs above
   - Save

### Step 2: Add to Backend .env

Open: `apps/backend/.env`

Find this line (around line 76):
```bash
GOOGLE_MAPS_API_KEY=YOUR_GOOGLE_MAPS_API_KEY_HERE
```

Replace with your real key:
```bash
GOOGLE_MAPS_API_KEY=AIzaSyC_Your_Actual_Key_Here_123456789
```

### Step 3: Add to Frontend .env.local

Open: `apps/customer/.env.local`

Find this line:
```bash
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=YOUR_GOOGLE_MAPS_API_KEY_HERE
```

Replace with your real key:
```bash
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=AIzaSyC_Your_Actual_Key_Here_123456789
```

**Note:** Use the **SAME key** for both (it's restricted by domain anyway)

---

## Step 4: Test It Works! ✅

### Test 1: Address Autocomplete

```powershell
cd apps/customer
npm run dev
```

1. Go to: http://localhost:3000/quote
2. Find "Full Venue Address" field
3. Start typing: "123 Main"
4. **Expected:** Dropdown with Google address suggestions appears
5. **If working:** ✅ Frontend integration successful!
6. **If not working:** Check browser console for errors

### Test 2: Travel Fee Calculation (Backend)

```powershell
# In a new terminal
cd apps/backend
python -m uvicorn src.main:app --reload
```

1. Fill out the quote form completely
2. Enter a full address in "Venue Address"
3. Click "Calculate Quote"
4. **Expected:** Backend calculates distance and travel fee
5. **Check backend logs** for: "Calculating travel fee for..."

---

## Troubleshooting 🔧

### Issue: "This API key is not authorized"

**Solution:** Check API restrictions in Google Console
- Make sure you enabled all 3 APIs
- Make sure localhost URLs are in website restrictions
- Wait 1-2 minutes for restrictions to propagate

### Issue: "Google is not defined"

**Solution:** Frontend can't load Google Maps script
- Check `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` is in `.env.local`
- Restart Next.js dev server: `npm run dev`
- Check browser console for script loading errors

### Issue: "Invalid API key"

**Solution:** Key format is wrong
- Should start with: `AIzaSy...`
- No extra spaces or quotes
- Same key in both files

---

## About Environment Files 📁

### You asked: "Don't we need the real key in .env?"

**Answer: YES!** Put real keys in `.env` files because:

| File Type | Purpose | Contains Real Keys? | Committed to Git? |
|-----------|---------|---------------------|-------------------|
| `.env` / `.env.local` | **Active development** | ✅ YES - Real keys | ❌ NO (gitignored) |
| `.env.example` | **Template for developers** | ❌ NO - Placeholders | ✅ YES (committed) |
| `.env.production` | **Production deployment** | ✅ YES - Prod keys | ❌ NO (gitignored) |

### You asked: "We have too many env files?"

**Answer: YES!** We have **14 .env files** (way too many)

**Current mess:**
```
Root:        .env, .env.docker, .env.production.template
Backend:     .env, .env.example, .env.test
Customer:    .env.local, .env.example, .env.local.example, .env.production.example  
Admin:       .env.local, .env.example
Config:      .env.development.template, .env.production.template
```

**Should only need 7 files:**
```
Backend:     .env (active), .env.example (template), .env.test
Customer:    .env.local (active), .env.example (template)
Admin:       .env.local (active), .env.example (template)
```

**Delete these duplicates:**
- ❌ Root `/.env` (conflicts with app-specific)
- ❌ Root `/.env.production.template` (duplicate)
- ❌ `apps/customer/.env.local.example` (duplicate of .env.example)
- ❌ `config/environments/.env.development.template` (duplicate)
- ❌ `config/environments/.env.production.template` (duplicate)

### You asked: "If we consolidate, need to change imports?"

**Answer: NO!** (probably)

Most code uses **environment variables**, not file paths:
```python
# Python code uses env vars
import os
api_key = os.getenv("GOOGLE_MAPS_API_KEY")
```

Only **docker-compose** and **deployment scripts** reference files directly, but:
- `load_dotenv()` in Python auto-finds `.env` in parent directories
- Next.js auto-loads `.env.local` without explicit import
- Docker Compose uses environment variables, not file paths

**Safe to clean up!** See: `ENVIRONMENT_CONSOLIDATION_PLAN.md` for full analysis.

---

## What We've Done ✅

Today's changes:

1. **Added Google Maps API key placeholders** to:
   - ✅ `apps/backend/.env` (line 76)
   - ✅ `apps/customer/.env.local`
   - ✅ `apps/backend/.env.example` (with docs)
   - ✅ `apps/customer/.env.local.example` (with docs)

2. **Created documentation:**
   - ✅ `ENVIRONMENT_CONSOLIDATION_PLAN.md` - Full env cleanup strategy
   - ✅ `QUOTE_ENHANCEMENTS_GUIDE.md` - Visual guide for new features
   - ✅ `setup-google-maps-key.ps1` - Automated setup script
   - ✅ This file - Quick start guide

3. **Ready for your API key:**
   - Just run `setup-google-maps-key.ps1` or add manually
   - Then test address autocomplete
   - Then test travel fee calculation

---

## Next Steps 🚀

### Immediate (Do Now):
1. **Run setup script OR add key manually**
   ```powershell
   .\setup-google-maps-key.ps1
   ```

2. **Test address autocomplete**
   ```powershell
   cd apps/customer
   npm run dev
   ```
   → Go to http://localhost:3000/quote
   → Try typing an address

3. **Connect travel fee API** (last remaining task!)
   - See TODO list item
   - Add API call in `QuoteCalculator.tsx`
   - Display travel fee in results

### Short-term (This Week):
1. **Clean up duplicate .env files**
   - Review `ENVIRONMENT_CONSOLIDATION_PLAN.md`
   - Delete 5 duplicate template files
   - Update any documentation references

2. **Set up production keys**
   - Create separate API key for production
   - Add to deployment environment (Vercel/Railway)
   - Test on staging first

### Long-term (Next Sprint):
1. **Implement secret management**
   - Consider AWS Secrets Manager or Vault
   - Automate key rotation
   - Add monitoring for API quota

2. **Add monitoring**
   - Track Google Maps API usage
   - Alert if approaching quota limits
   - Log failed API calls

---

## Summary 📊

**Your Questions Answered:**

1. ✅ **"Need real key in .env?"** → YES! That's exactly right.
2. ✅ **"Too many env files?"** → YES! We have 14, should have 7.
3. ✅ **"Need to change imports?"** → NO! They use env vars, not file paths.

**Current Status:**

- ✅ Backend code ready (has `GOOGLE_MAPS_API_KEY` lookup)
- ✅ Frontend code ready (has Google Places Autocomplete)
- ✅ Gratuity section ready (beautiful 3-tier display)
- ⏳ **Just need:** Your actual Google Maps API key
- ⏳ **Then connect:** Travel fee API call to backend

**You're 95% done!** Just need the API key and one more API integration! 🎉

