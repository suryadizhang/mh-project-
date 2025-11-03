# 🔑 Google Maps API Key - Final Configuration Checklist

**API Key:** `AIzaSyCxdQ9eZCYwWKcr4j1DHX4rvv02H_KIvhs`

---

## ✅ Complete Configuration Checklist

### 1. Application Restrictions ⚠️ CHANGE THIS!

**Current (WRONG):**
- ❌ IP address restrictions
  - 127.0.0.1
  - 2601:646:9900:e5a0:c9d3:f1d4:1c71:2422

**Should Be:**
- ✅ **HTTP referrers (web sites)**

**Add These 7 Referrers:**
```
http://localhost:3000/*
http://localhost:3001/*
http://127.0.0.1:3000/*
http://127.0.0.1:3001/*
https://myhibachichef.com/*
https://www.myhibachichef.com/*
https://admin.mysticdatanode.net/*
```

---

### 2. API Restrictions - Add 1 More API

**Current (3 APIs):**
- ✅ Distance Matrix API
- ✅ Geocoding API
- ✅ Places API

**Add This One:**
- ➕ **Maps JavaScript API** ⭐ (REQUIRED!)

**Final List (4 APIs):**
- ✅ Distance Matrix API - Backend travel fee calculation
- ✅ Geocoding API - Address validation (optional but good)
- ✅ **Maps JavaScript API** - Load Google Maps script in frontend
- ✅ Places API - Address autocomplete

---

### 3. Enable Maps JavaScript API

**Go to:**
https://console.cloud.google.com/apis/library/maps-javascript-api

**Click:** "ENABLE"

---

## 🎯 Step-by-Step Instructions

### Go to: https://console.cloud.google.com/apis/credentials

1. **Find your API key** in the list
2. **Click on the key name** to open edit page
3. **Under "Application restrictions":**
   - Select: **"HTTP referrers (web sites)"**
   - Clear any existing IP addresses
4. **Click "Add an item"** 7 times and add each referrer:
   ```
   http://localhost:3000/*
   http://localhost:3001/*
   http://127.0.0.1:3000/*
   http://127.0.0.1:3001/*
   https://myhibachichef.com/*
   https://www.myhibachichef.com/*
   https://admin.mysticdatanode.net/*
   ```
5. **Under "API restrictions":**
   - Select: **"Restrict key"**
   - Click "Select APIs"
   - Find and check: **"Maps JavaScript API"** (if not already checked)
   - Make sure these 4 are checked:
     - ✅ Distance Matrix API
     - ✅ Geocoding API
     - ✅ Maps JavaScript API
     - ✅ Places API
6. **Click "SAVE"** at the bottom
7. **Wait 1-5 minutes** for changes to take effect

---

## 🧪 Test After Configuration

### Test 1: Frontend Address Autocomplete

```powershell
cd apps/customer
npm run dev
```

**Test:**
1. Go to: http://localhost:3000/quote
2. Click in "Full Venue Address" field
3. Type: "123 Main St"
4. **Expected:** Google autocomplete dropdown appears with suggestions

**Common Errors:**
- `RefererNotAllowedMapError` → Check HTTP referrer list
- `ApiNotActivatedMapError` → Enable Maps JavaScript API
- `RequestDenied` → Wait 2-3 minutes for restrictions to update

### Test 2: Backend Travel Fee Calculation

```powershell
# In a NEW terminal
cd apps/backend
python -m uvicorn src.main:app --reload
```

**Test:**
1. Fill out entire quote form
2. Use autocomplete to select a full address
3. Click "Calculate Quote"
4. **Check backend terminal** for logs

**Expected Log:**
```
INFO: Calculating travel fee for: 123 Main St, Sacramento, CA 95814
INFO: Distance from station: 18.5 miles
INFO: Travel fee: $0.00 (within 30 mile radius)
```

---

## 🚨 Why Switch from IP to HTTP Referrers?

**IP Restrictions:**
- ❌ Only work for server-to-server calls
- ❌ Don't work for browsers (customers have different IPs)
- ❌ Won't work when customers access your site

**HTTP Referrer Restrictions:**
- ✅ Work for web browsers
- ✅ Browser sends website URL in request
- ✅ Google checks if domain is in your allowed list
- ✅ Customers can access from any IP address
- ✅ More flexible and secure for public websites

---

## 📊 Configuration Summary

| Setting | Before | After |
|---------|--------|-------|
| **Restriction Type** | IP addresses | **HTTP referrers** |
| **Allowed Sources** | 2 IPs | **7 domains** |
| **APIs Enabled** | 3 APIs | **4 APIs** (+Maps JS) |
| **Maps JavaScript API** | Not enabled | **Enabled** |

---

## ✅ Final Checklist

Before testing, make sure:

- [ ] Changed from IP restrictions to HTTP referrers
- [ ] Added all 7 referrer domains (including admin.mysticdatanode.net)
- [ ] Added Maps JavaScript API to restrictions (4 APIs total)
- [ ] Enabled Maps JavaScript API in APIs library
- [ ] Clicked SAVE in credentials page
- [ ] Waited 2-5 minutes for changes to propagate
- [ ] API key is in apps/backend/.env
- [ ] API key is in apps/customer/.env.local
- [ ] Ready to test!

---

## 🎯 Your Domains

**Customer Site:**
- https://myhibachichef.com
- https://www.myhibachichef.com

**Admin Panel:**
- https://admin.mysticdatanode.net

**Local Development:**
- http://localhost:3000 (customer)
- http://localhost:3001 (admin)
- http://127.0.0.1:3000 (customer)
- http://127.0.0.1:3001 (admin)

All domains are now configured in your API key restrictions! 🎉

---

**After Configuration:** Test address autocomplete immediately to verify it works!
