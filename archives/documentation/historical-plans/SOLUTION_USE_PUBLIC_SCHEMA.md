# 🎯 SOLUTION: Use PUBLIC Schema (Production Database)

## Critical Finding

**PRODUCTION USES `public` schema WITH DATA:**
- ✅ `public.customers` - **1 customer** (has data!)
- ✅ `public.bookings` - **7 bookings** (has data!)
- ✅ `public.booking_reminders` - ready for Feature 1

**LEGACY UNUSED `core` schema:**
- ❌ `core.customers` - **0 rows** (empty!)
- ❌ `core.bookings` - **0 rows** (empty!)

---

## The Problem

### `public.customers` Structure (ACTUAL PRODUCTION):
```sql
id                    VARCHAR      -- NOT Integer!
user_id               VARCHAR
email                 VARCHAR
stripe_customer_id    VARCHAR
name                  VARCHAR      -- NOT first_name/last_name!
phone                 VARCHAR
```

### But `src/models/customer.py` expects:
```python
id                    Integer      -- ❌ MISMATCH!
first_name            String       -- ❌ DOESN'T EXIST!
last_name             String       -- ❌ DOESN'T EXIST!
email                 String       -- ✅ Match
```

---

## Solution

**Use the ACTUAL production schema (public) and fix the model to match!**

### Why Public Not Core:
1. ✅ **Has real data** (1 customer, 7 bookings)
2. ✅ **Used by production** (not empty)
3. ✅ **booking_reminders already there** (Feature 1)
4. ✅ **Simpler structure** (no multi-tenant)

### Why Not Core:
1. ❌ **Zero data** (completely empty)
2. ❌ **Over-engineered** (multi-tenant, encryption)
3. ❌ **Not used** (legacy only)

---

## Action Plan

### Step 1: Fix Customer Model to Match Production

**Change**: `src/models/customer.py`

```python
# OLD (doesn't match DB):
class Customer(BaseModel):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)

# NEW (matches production DB):
class Customer(BaseModel):
    __tablename__ = "customers"
    
    id = Column(String, primary_key=True)  # VARCHAR in DB
    user_id = Column(String, nullable=False, unique=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    stripe_customer_id = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=True)  # Single name field
    phone = Column(String, nullable=True)
    preferred_payment_method = Column(String, nullable=True)
    total_spent = Column(Numeric(10, 2), default=0)
    total_bookings = Column(Integer, default=0)
    zelle_savings = Column(Numeric(10, 2), default=0)
    loyalty_tier = Column(String, nullable=True)
```

### Step 2: Fix Booking Model to Match Production

**Change**: `src/models/booking.py`

```python
# Booking.customer_id should be String (not Integer)
customer_id = Column(String, ForeignKey("customers.id"), nullable=True)  # Nullable in DB!
```

### Step 3: Delete All Legacy Models

```bash
rm src/models/legacy_*.py
```

### Step 4: Create Test Data

```sql
-- Use actual production structure
INSERT INTO customers (id, user_id, email, stripe_customer_id, name, phone)
VALUES 
  ('cust_001', 'user_001', 'test@example.com', 'stripe_001', 'Test User', '+15550001'),
  ('cust_002', 'user_002', 'john@example.com', 'stripe_002', 'John Doe', '+15550002');

-- Already have 7 bookings, just need to update customer_id if needed
```

---

## Files Created

1. ✅ `inspect_database.py` - shows actual DB structure
2. ✅ `MODEL_DUPLICATION_AUDIT_CRITICAL.md` - full analysis
3. ⏳ Next: Fix customer.py and booking.py to match production

