# 🚀 CRITICAL SYSTEM OVERHAUL - Real Data Integration
**Date**: October 31, 2025  
**Priority**: URGENT - All existing AI quote calculations are WRONG  
**Impact**: High - Customer-facing pricing must be accurate

---

## 🔴 Problem Identified

### **INCORRECT HARDCODED PRICES**:
```python
# ❌ WRONG (What AI was using)
adult_price = $75/person
child_price = $50/person
filet_upgrade = $15/person

# ✅ CORRECT (From your webpage/FAQ)
adult_price = $55/person
child_price = $30/person
filet_upgrade = $5/person
```

### **Impact on Customer Emails**:
- **Malia's Quote**: AI said $675, SHOULD BE $495 (9 × $55)
- **Debbie's Quote**: AI said $1,300, SHOULD BE $850 (14×$55 + 2×$30 + 10×$5 + travel)

**This is a 36-52% overcharge!** 😱

---

## ✅ Solution Implemented

### **1. Real Pricing Service** ✅ CREATED
**File**: `apps/backend/src/api/ai/endpoints/services/pricing_service.py`

**Features**:
- Pulls prices from database (`menu_items`, `addon_items` tables)
- Falls back to FAQ data if DB empty
- **REAL PRICES**:
  - Adults (13+): **$55** (not $75)
  - Children (6-12): **$30** (not $50)
  - Under 5: **FREE**
  - Party minimum: **$550**
  - Filet Mignon: **+$5** (not $15)
  - Lobster Tail: **+$15** ✓
  - Salmon/Scallops: **+$5**
- Travel fees: First 30 miles free, then $2/mile
- Gratuity guidance: 20-35% (not included in total)

**API**:
```python
from services.pricing_service import get_pricing_service

pricing = get_pricing_service(db)

# Get current prices
adult_price = pricing.get_adult_price()  # $55
child_price = pricing.get_child_price()  # $30
filet_price = pricing.get_upgrade_price("filet_mignon")  # $5

# Calculate complete quote
quote = pricing.calculate_party_quote(
    adults=14,
    children=2,
    upgrades={"filet_mignon": 10},
    travel_miles=45
)
# Returns: Detailed breakdown with REAL prices
```

---

### **2. Chef Availability Service** ✅ CREATED
**File**: `apps/backend/src/api/ai/endpoints/services/chef_availability_service.py`

**Features**:
- **Dynamic slot availability** based on chef count
- **Christmas Eve example**: Only 1 chef → max 1 booking per slot
- **Multi-chef scheduling**: 
  - Dec 24: 4 slots (12pm/3pm/6pm/9pm)
  - 3 chefs normally, but only 2 at 6pm
  - Result: 3 bookings at 12/3/9pm, only 2 at 6pm
- **Real-time checking**: Queries `bookings` table for current capacity
- **Suggest alternatives**: If slot full, suggest next available

**API**:
```python
from services.chef_availability_service import get_availability_service

availability = get_availability_service(db)

# Check specific slot
slot_check = availability.check_slot_available(
    target_date=date(2025, 12, 24),
    slot_time="18:00"  # 6 PM
)
# Returns: {"available": False, "capacity": 2, "booked": 2, "remaining": 0}

# Get all slots for a date
day_slots = availability.get_available_slots(date(2025, 12, 24))
# Returns: List of all 4 slots with availability

# Suggest alternatives if requested slot unavailable
alternatives = availability.suggest_alternative_dates(
    requested_date=date(2025, 12, 24),
    requested_time="18:00",
    alternatives_count=3
)
# Returns: Same day different time, next week same time, or next available
```

---

## 📋 Implementation Checklist

### **Phase 1: Update AI to Use Real Pricing** ⏳ NEXT
- [ ] Update `multi_channel_ai_handler.py` to import `pricing_service`
- [ ] Update `customer_booking_ai.py` system prompts with real prices
- [ ] Replace all hardcoded prices with `pricing.get_*_price()` calls
- [ ] Recalculate Malia's and Debbie's quotes with correct prices
- [ ] Update `AI_EMAIL_RESPONSES_FOR_REVIEW.md` with corrected quotes

### **Phase 2: Integrate Availability Checking** ⏳ TODO
- [ ] Update multi-channel AI to check availability for date requests
- [ ] Add "slot full" detection in quote responses
- [ ] Suggest alternative dates/times if requested slot unavailable
- [ ] Update email templates to include availability disclaimers

### **Phase 3: Database Schema for Chef Scheduling** ⏳ TODO
Create tables for super admin & station manager features:

```sql
-- Table 1: Chef Schedules
CREATE TABLE chef_schedules (
    id UUID PRIMARY KEY,
    station_id UUID REFERENCES stations(id),
    date DATE NOT NULL,
    time_slot VARCHAR(5) NOT NULL,  -- "12:00", "15:00", etc.
    chef_count INTEGER NOT NULL DEFAULT 3,
    notes TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Table 2: Chef Profiles
CREATE TABLE chefs (
    id UUID PRIMARY KEY,
    station_id UUID REFERENCES stations(id),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    skills JSONB,  -- ["hibachi", "sushi", "teppanyaki"]
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table 3: Chef Assignments
CREATE TABLE booking_chef_assignments (
    id UUID PRIMARY KEY,
    booking_id UUID REFERENCES bookings(id),
    chef_id UUID REFERENCES chefs(id),
    assigned_at TIMESTAMP DEFAULT NOW(),
    assigned_by UUID REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_chef_schedules_date_time ON chef_schedules(date, time_slot);
CREATE INDEX idx_chef_schedules_station ON chef_schedules(station_id);
CREATE INDEX idx_booking_assignments ON booking_chef_assignments(booking_id, chef_id);
```

### **Phase 4: Admin UI for Chef Scheduling** ⏳ TODO
**Route**: `/super-admin/chef-scheduling`

**Features**:
- Calendar view with date picker
- Add/edit chef count per slot
- Bulk operations (set entire week, copy schedule)
- Holiday templates (Christmas Eve = 1 chef, New Year's = 2 chefs)
- Real-time availability preview
- Override individual slots

**Route**: `/station-manager/availability`

**Features** (for station managers):
- View their station's schedule
- Add/remove chef availability
- Cannot modify other stations
- View upcoming bookings by chef
- Assign chefs to bookings

### **Phase 5: AI Confidence-Based Auto-Reply** ⏳ TODO
**Route**: `/super-admin/ai-settings`

**Configuration Options**:
```typescript
interface AISettings {
  email: {
    auto_reply_enabled: boolean;  // Default: FALSE
    confidence_threshold: number;  // 0-100% (ignored for email)
    require_human_review: boolean; // Default: TRUE
  };
  
  sms: {
    auto_reply_enabled: boolean;  // Default: TRUE
    confidence_threshold: number;  // Default: 70%
    escalate_if_below: boolean;   // Default: TRUE
  };
  
  instagram: {
    auto_reply_enabled: boolean;  // Default: TRUE
    confidence_threshold: number;  // Default: 70%
    escalate_if_below: boolean;   // Default: TRUE
  };
  
  facebook: {
    auto_reply_enabled: boolean;  // Default: TRUE
    confidence_threshold: number;  // Default: 70%
    escalate_if_below: boolean;   // Default: TRUE
  };
  
  web_chat: {
    auto_reply_enabled: boolean;  // Default: TRUE
    confidence_threshold: number;  // Default: 70%
    escalate_if_below: boolean;   // Default: TRUE
  };
  
  escalation_rules: {
    high_value_threshold: number;  // Quotes above this = always escalate (e.g., $1000)
    holiday_bookings: boolean;     // Always escalate holiday bookings
    complaints: boolean;           // Always escalate complaints
    custom_requests: boolean;      // Escalate complex custom requests
  };
}
```

**AI Performance Tracking**:
- Track confidence scores over time
- Approval rate per channel
- Response time metrics
- Customer satisfaction correlation
- **Goal**: When AI reaches 75%+ approval rate → enable email auto-reply

### **Phase 6: WhatsApp Admin Notifications** ⏳ TODO
**Integration**: WhatsApp Business API (or Twilio)

**Trigger Events**:
1. New email arrives → Send WhatsApp to admin
2. AI confidence < 70% → Escalate to admin
3. High-value quote (>$1000) → Notify admin
4. Holiday booking → Notify admin
5. Complaint detected → URGENT notification

**Message Format**:
```
🚨 New Inquiry Needs Review

Customer: Debbie Plummer
Channel: Email
Type: Quote Request
Amount: $850
Priority: HIGH (Holiday - Dec 24)

👉 Review now: https://admin.myhibachichef.com/emails/pending/abc123
```

**Admin Actions**:
- Click link → Open email review dashboard
- Approve/Edit/Reject from dashboard
- Or reply via WhatsApp: "APPROVE abc123" for quick approval

---

## 🔥 Corrected Customer Quotes

### **Malia Nakamura** (9 guests, Sonoma, August 2026)

**Previous (WRONG)**:
```
9 adults × $75 = $675 ❌
```

**Corrected (RIGHT)**:
```
9 adults × $55 = $495 ✅
Travel (Sonoma ~60 miles): (60-30) × $2 = $60
TOTAL: $555 ✅

Meets minimum: YES ($555 > $550)
```

**Savings**: $180 less than AI originally quoted!

---

### **Debbie Plummer** (14 adults, 2 children, 10 filet upgrades, Antioch, Dec 24)

**Previous (WRONG)**:
```
14 adults × $75 = $1,050 ❌
2 children × $50 = $100 ❌
10 filet × $15 = $150 ❌
TOTAL: $1,300 ❌
```

**Corrected (RIGHT)**:
```
14 adults × $55 = $770 ✅
2 children × $30 = $60 ✅
10 filet × $5 = $50 ✅
Subtotal: $880
Travel (Antioch ~45 miles): (45-30) × $2 = $30
TOTAL: $910 ✅

Meets minimum: YES ($910 > $550)
```

**Savings**: $390 less than AI originally quoted!

**Christmas Eve Availability**:
```
Date: December 24, 2025
Chef capacity: 1 (reduced for holiday)
Time slots: 12pm, 3pm, 6pm, 9pm
Max bookings: 4 (one per slot)

AI should check availability:
- "We have limited availability on Christmas Eve (only 1 chef working)"
- "Available slots: [check real-time]"
- "Would you like to secure one of these slots?"
```

---

## 🎯 Next Steps (Your Decisions Needed)

### **1. Approve Corrected Quotes**:
- **Malia**: $555 (was $675) → Approve?
- **Debbie**: $910 (was $1,300) → Approve?

### **2. Christmas Eve Availability**:
- Do you work December 24, 2025? YES / NO
- If YES, how many chefs available? ___ chefs
- Which time slots operational? [12pm] [3pm] [6pm] [9pm]

### **3. Implementation Priority**:
```
[ ] A. Update AI with real pricing NOW (send corrected emails)
[ ] B. Build chef scheduling UI first
[ ] C. Setup WhatsApp notifications first
[ ] D. Build admin email review dashboard UI first
```

### **4. Super Admin Access**:
- Who should have super admin access? (emails)
- Who should have station manager access? (emails)

---

## 📊 System Architecture (Updated)

```
┌─────────────────────────────────────────────────────────────┐
│                     CUSTOMER INQUIRY                         │
│  (Email, SMS, Instagram, Facebook, Phone, Web Chat)         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              MULTI-CHANNEL AI HANDLER                        │
│  - Extract info (name, party size, date, location)          │
│  - Detect inquiry type (quote, booking, FAQ, complaint)     │
│  - Calculate sentiment & urgency                             │
└────────────────────┬────────────────────────────────────────┘
                     │
      ┌──────────────┼──────────────┐
      │              │               │
      ▼              ▼               ▼
┌──────────┐  ┌──────────┐   ┌──────────────┐
│ PRICING  │  │   CHEF   │   │ AI RESPONSE  │
│ SERVICE  │  │AVAILABILITY│   │  GENERATOR   │
│          │  │  SERVICE │   │              │
│ • Query  │  │          │   │ • GPT-3.5    │
│   real   │  │ • Check  │   │   (simple)   │
│   prices │  │   slots  │   │ • GPT-4      │
│ • $55/$30│  │ • Suggest│   │   (complex)  │
│ • +$5/$15│  │   dates  │   │              │
└──────────┘  └──────────┘   └──────────────┘
      │              │               │
      └──────────────┴───────────────┘
                     │
                     ▼
          ┌─────────────────────┐
          │  AI CONFIDENCE      │
          │  SCORING            │
          │  (0-100%)           │
          └──────┬──────────────┘
                 │
         ┌───────┴────────┐
         │                │
    < 70%│           ≥ 70%│
         ▼                ▼
 ┌──────────────┐  ┌─────────────────┐
 │  ESCALATE    │  │  CHANNEL CHECK  │
 │  TO ADMIN    │  │                 │
 │              │  │ Email: Review   │
 │ • WhatsApp   │  │ SMS/Chat: Send  │
 │   notif      │  │ Social: Send    │
 │ • Dashboard  │  └─────────────────┘
 │   queue      │
 └──────────────┘
         │
         ▼
 ┌──────────────────────────┐
 │  ADMIN REVIEW DASHBOARD  │
 │  • View AI response      │
 │  • Edit/Approve/Reject   │
 │  • Add personal touch    │
 │  • Send or schedule      │
 └──────────────────────────┘
```

---

## ⚠️ Critical Reminders

1. **NEVER hardcode prices again** - Always use `pricing_service`
2. **ALWAYS check availability** - Use `availability_service` before quoting dates
3. **Email = human review required** - SMS/Social can auto-reply if confident
4. **High-value quotes** - Always escalate quotes >$1000 to admin
5. **Holiday bookings** - Always check chef capacity, warn if limited
6. **Travel fees** - Include in quote if customer >30 miles away
7. **Gratuity** - Never include in quote total, always mention as separate
8. **Minimum** - Warn if party doesn't meet $550 minimum

---

## 📝 Implementation Timeline

**Week 1** (Now - Nov 7):
- [x] Day 1: Create pricing service ✅
- [x] Day 1: Create availability service ✅
- [ ] Day 2: Update AI handlers with real pricing
- [ ] Day 2: Recalculate customer quotes
- [ ] Day 3: Build admin email review UI
- [ ] Day 4: Setup WhatsApp notifications
- [ ] Day 5: Test end-to-end with real emails

**Week 2** (Nov 8-14):
- [ ] Create database tables (chef_schedules, chefs, assignments)
- [ ] Build super admin chef scheduling UI
- [ ] Build station manager availability UI
- [ ] Migrate historical chef data
- [ ] Test multi-chef slot allocation

**Week 3** (Nov 15-21):
- [ ] Implement AI confidence tracking
- [ ] Build AI performance dashboard
- [ ] Configure auto-reply thresholds per channel
- [ ] Test escalation workflows
- [ ] Train AI on corrected data

**Week 4** (Nov 22-28):
- [ ] Full system integration testing
- [ ] Load testing (100+ concurrent inquiries)
- [ ] Security audit
- [ ] Documentation & training
- [ ] PRODUCTION LAUNCH 🚀

---

**READY TO PROCEED?** Which phase should I implement first?

1. ✅ Update AI with real pricing (send corrected quotes)
2. 🏗️ Build admin email review UI
3. 📅 Build chef scheduling system
4. 📱 Setup WhatsApp notifications

**Tell me your choice and any corrections to the pricing/availability assumptions!**
