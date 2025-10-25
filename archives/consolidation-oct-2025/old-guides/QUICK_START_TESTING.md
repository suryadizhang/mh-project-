# 🎯 Quick Start: Lead Generation Testing

## ⚡ **TL;DR** - What You Need to Know

**Status**: ✅ Phase 1 & 2 CODE COMPLETE, ⏳ Testing Required  
**Time to Test**: 40 minutes  
**What Works**: Database ✅, Code ✅, Git ✅  
**What's Needed**: Backend server + API testing

---

## 🚀 **Quick Test (5 Commands)**

### **1. Fix Backend Dependencies**
```powershell
cd "C:\Users\surya\projects\MH webapps\apps\backend"
# Open pyproject.toml, change line: ringcentral==1.0.0 → ringcentral==0.9.2
python -m pip install -e .
```

### **2. Start Backend**
```powershell
cd "C:\Users\surya\projects\MH webapps\apps\backend\src"
$env:PYTHONPATH = "C:\Users\surya\projects\MH webapps\apps\backend\src"
python -m uvicorn main:app --reload --port 8000
```

### **3. Test API**
```powershell
# In NEW PowerShell window:
$body = @{name="Test";email="test@test.com";guest_count=10;source="quote"} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/public/leads" -Method POST -Body $body -ContentType "application/json"
```

### **4. Check Database**
```powershell
# In NEW PowerShell window:
cd "C:\Users\surya\projects\MH webapps\apps\backend"
python check_db_schema.py
# Should show: ✅ Table 'lead.leads' exists (1 rows)
```

### **5. Test Website**
```powershell
# In NEW PowerShell window:
cd "C:\Users\surya\projects\MH webapps\apps\customer"
npm run dev
# Visit: http://localhost:3000/quote
# Fill form, submit, see success message
```

---

## 📊 **What We Built** (Phase 1 & 2)

### **Backend** (Python FastAPI)
- ✅ `LeadService` - 700+ lines, 10+ methods
- ✅ `POST /api/v1/public/leads` - No auth required
- ✅ Failed booking auto-capture
- ✅ Automatic scoring (0-100)
- ✅ Quality classification (HOT/WARM/COLD)

### **Frontend** (Next.js React)
- ✅ `QuoteRequestForm` - 355 lines
- ✅ `ContactForm` - 270 lines
- ✅ Integrated into /quote page
- ✅ Integrated into /contact page

### **Database** (PostgreSQL)
- ✅ Schema `lead` with 4 tables
- ✅ All tables exist (0 rows initially)
- ✅ Ready for data

---

## 🐛 **Quick Fixes**

### **Problem: Backend won't start**
```powershell
# Solution 1: Set PYTHONPATH
$env:PYTHONPATH = "C:\Users\surya\projects\MH webapps\apps\backend\src"
cd "C:\Users\surya\projects\MH webapps\apps\backend\src"
python -m uvicorn main:app --reload --port 8000

# Solution 2: Fix ringcentral version
# Edit pyproject.toml: ringcentral==1.0.0 → ringcentral==0.9.2
cd "C:\Users\surya\projects\MH webapps\apps\backend"
python -m pip install -e .
```

### **Problem: API returns 404**
```
Check:
1. Server started? (look for "Uvicorn running on http://127.0.0.1:8000")
2. Correct URL? (http://localhost:8000/api/v1/public/leads)
3. Router registered? (check main.py, should have public_leads_router)
```

### **Problem: No data in database**
```
Check:
1. API returned success? (look for lead_id in response)
2. Database connected? (run check_db_schema.py)
3. Backend logs? (check for errors in terminal)
```

---

## ✅ **Success Indicators**

When everything works, you'll see:

**Backend Terminal:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
INFO:     POST /api/v1/public/leads HTTP/1.1 201 Created
```

**API Response:**
```json
{
  "success": true,
  "message": "Thank you! We've received your request...",
  "lead_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Database Check:**
```
✅ Table 'lead.leads' exists (1 rows)
✅ Table 'lead.lead_contacts' exists (1 rows)
✅ Table 'lead.lead_context' exists (1 rows)
✅ Table 'lead.lead_events' exists (1 rows)
```

**Website:**
```
✅ Green checkmark appears
✅ "Thank you! We've received your request" message
✅ Form resets after 3 seconds
```

---

## 📚 **Full Documentation**

For complete details, see:
- **`TESTING_PHASE_1_2_COMPLETE.md`** - Step-by-step testing guide
- **`LEAD_GENERATION_PHASE_1_COMPLETE.md`** - Full implementation docs

---

## 🎯 **Next Actions**

**Option 1: Test Now** (40 min)
- Follow the 5 commands above
- Verify everything works
- Mark Phase 1 & 2 as 100% complete

**Option 2: Continue Building** (Phase 3)
- Add admin UI to view leads
- Email notifications
- Lead management interface

**Option 3: Deploy to Production**
- Test locally first (recommended)
- Then deploy to staging/production

---

## 💡 **Key Files**

```
Testing Files:
  apps/backend/check_db_schema.py         - Verify database
  apps/backend/TEST_INSTRUCTIONS.py       - Test commands
  
Implementation:
  apps/backend/src/services/lead_service.py         - Business logic
  apps/backend/src/api/v1/endpoints/public_leads.py - API endpoint
  apps/customer/src/components/forms/QuoteRequestForm.tsx
  apps/customer/src/components/forms/ContactForm.tsx

Documentation:
  TESTING_PHASE_1_2_COMPLETE.md          - Full testing guide
  LEAD_GENERATION_PHASE_1_COMPLETE.md    - Implementation details
```

---

**🚀 Ready to test? Run the 5 commands above!**
