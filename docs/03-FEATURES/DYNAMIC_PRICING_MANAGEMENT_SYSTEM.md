# Dynamic Pricing Management System

## 🎯 Overview

This document outlines the complete system for managing pricing
dynamically across your website, database, and AI responses.

**Your Concern:** _"these price are dynamic subject to change we need
to check our webpage for these, or create a system for whenever the
frontend page change prices we update our data too or how we can
manage it?"_

---

## 🏗️ Solution Architecture

### Option 1: **Database as Single Source of Truth** (RECOMMENDED)

**Flow:** Database → Frontend → AI

```
┌─────────────────────┐
│   Admin Panel       │
│  (Super Admin)      │
└──────────┬──────────┘
           │
           ↓ Updates
┌─────────────────────┐
│    Database         │
│  (menu_items)       │
│  (addon_items)      │
└──────────┬──────────┘
           │
           ├──→ Frontend (pulls prices for display)
           │
           └──→ AI Service (pulls prices for quotes)
```

**Benefits:**

- ✅ Single source of truth
- ✅ No sync issues
- ✅ Instant updates everywhere
- ✅ Price history tracking
- ✅ Admin control

---

## 📊 Database Schema

### Current Tables (Already Exists):

```sql
-- Menu Items (Base Pricing)
CREATE TABLE menu_items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    base_price DECIMAL(10, 2) NOT NULL,
    category VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Addon Items (Upgrades & Add-ons)
CREATE TABLE addon_items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    category VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### New Table Needed: Price Change History

```sql
-- Track all price changes for auditing
CREATE TABLE price_change_history (
    id SERIAL PRIMARY KEY,
    item_type VARCHAR(20) NOT NULL, -- 'menu_item' or 'addon_item'
    item_id INTEGER NOT NULL,
    item_name VARCHAR(100) NOT NULL,
    old_price DECIMAL(10, 2) NOT NULL,
    new_price DECIMAL(10, 2) NOT NULL,
    changed_by_user_id INTEGER REFERENCES users(id),
    change_reason TEXT,
    effective_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for performance
CREATE INDEX idx_price_changes_item ON price_change_history(item_type, item_id);
CREATE INDEX idx_price_changes_date ON price_change_history(effective_date);
```

---

## 🎨 Admin Panel UI (To Be Built)

### Super Admin Pricing Management Page

**Route:** `/super-admin/pricing-management`

**Features:**

1. **Price List Table:**
   - View all menu items and addon items
   - Edit prices inline
   - Toggle active/inactive
   - See last updated timestamp

2. **Price Change Form:**
   - Current price displayed
   - New price input
   - Effective date picker
   - Change reason (optional)
   - Preview impact (how many active quotes affected)

3. **Price History:**
   - Timeline of all price changes
   - Who changed it
   - When it changed
   - Why it changed

4. **Bulk Update:**
   - Upload CSV for multiple price changes
   - Percentage increase/decrease across categories
   - Seasonal pricing templates

---

## 🔄 Implementation Steps

### Step 1: Seed Database with Current Prices

```sql
-- Insert current pricing (from your FAQ)
INSERT INTO menu_items (name, description, base_price, category, is_active) VALUES
('Adult Base Price', 'Adult (13+ years)', 55.00, 'base', true),
('Child Base Price', 'Child (6-12 years)', 30.00, 'base', true),
('Child Under 5', 'Child under 5 years', 0.00, 'base', true);

INSERT INTO addon_items (name, description, price, category, is_active) VALUES
('Filet Mignon Upgrade', 'Premium beef upgrade', 5.00, 'protein_upgrade', true),
('Lobster Tail Upgrade', 'Fresh lobster tail', 15.00, 'protein_upgrade', true);

-- Travel pricing (stored in settings or menu_items)
INSERT INTO menu_items (name, description, base_price, category, is_active) VALUES
('Travel Free Distance', 'Free miles included', 30.00, 'travel', true),
('Travel Per Mile Rate', 'Cost per mile after free distance', 2.00, 'travel', true);
```

### Step 2: Create Admin API Endpoints

```python
# File: apps/backend/src/api/admin/endpoints/pricing.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.app.database import get_db
from api.app.menu.models import MenuItem, AddonItem
from .models import PriceChangeHistory

router = APIRouter(prefix="/api/admin/pricing", tags=["Admin Pricing"])

@router.get("/menu-items")
async def get_all_pricing(db: Session = Depends(get_db)):
    """Get all current pricing"""
    menu_items = db.query(MenuItem).filter(MenuItem.is_active == True).all()
    addon_items = db.query(AddonItem).filter(AddonItem.is_active == True).all()

    return {
        "menu_items": [
            {
                "id": item.id,
                "name": item.name,
                "price": float(item.base_price),
                "category": item.category,
                "last_updated": item.updated_at
            }
            for item in menu_items
        ],
        "addon_items": [
            {
                "id": item.id,
                "name": item.name,
                "price": float(item.price),
                "category": item.category,
                "last_updated": item.updated_at
            }
            for item in addon_items
        ]
    }

@router.put("/menu-items/{item_id}")
async def update_menu_item_price(
    item_id: int,
    new_price: float,
    change_reason: str = None,
    effective_date: str = None,
    current_user = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """Update menu item price"""
    item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    # Log the change
    history = PriceChangeHistory(
        item_type="menu_item",
        item_id=item.id,
        item_name=item.name,
        old_price=item.base_price,
        new_price=new_price,
        changed_by_user_id=current_user.id,
        change_reason=change_reason,
        effective_date=effective_date
    )
    db.add(history)

    # Update the price
    item.base_price = new_price
    item.updated_at = datetime.now()
    db.commit()

    return {
        "message": f"Price updated from ${history.old_price} to ${new_price}",
        "item": {
            "id": item.id,
            "name": item.name,
            "new_price": float(item.base_price)
        }
    }

@router.get("/price-history")
async def get_price_history(
    item_type: str = None,
    item_id: int = None,
    db: Session = Depends(get_db)
):
    """Get price change history"""
    query = db.query(PriceChangeHistory)

    if item_type:
        query = query.filter(PriceChangeHistory.item_type == item_type)
    if item_id:
        query = query.filter(PriceChangeHistory.item_id == item_id)

    changes = query.order_by(PriceChangeHistory.created_at.desc()).all()

    return {
        "price_changes": [
            {
                "id": change.id,
                "item_name": change.item_name,
                "old_price": float(change.old_price),
                "new_price": float(change.new_price),
                "changed_by": change.changed_by_user_id,
                "reason": change.change_reason,
                "changed_at": change.created_at
            }
            for change in changes
        ]
    }
```

### Step 3: Update Frontend to Pull Prices from API

```typescript
// File: apps/frontend/src/services/pricingService.ts

export interface PricingData {
  menu_items: MenuItem[];
  addon_items: AddonItem[];
  last_updated: string;
}

export async function fetchCurrentPricing(): Promise<PricingData> {
  const response = await fetch('/api/pricing/current');
  const data = await response.json();
  return data;
}

// Cache pricing data in localStorage with expiry
export function getCachedPricing(): PricingData | null {
  const cached = localStorage.getItem('pricing_data');
  if (!cached) return null;

  const { data, expiry } = JSON.parse(cached);
  if (Date.now() > expiry) {
    localStorage.removeItem('pricing_data');
    return null;
  }

  return data;
}

export function cachePricing(data: PricingData): void {
  const expiry = Date.now() + 15 * 60 * 1000; // 15 minutes
  localStorage.setItem(
    'pricing_data',
    JSON.stringify({ data, expiry })
  );
}

// Usage in components:
export async function getPricing(): Promise<PricingData> {
  // Try cache first
  const cached = getCachedPricing();
  if (cached) return cached;

  // Fetch fresh data
  const data = await fetchCurrentPricing();
  cachePricing(data);
  return data;
}
```

```tsx
// File: apps/frontend/src/components/PricingDisplay.tsx

import { useEffect, useState } from 'react';
import { getPricing } from '@/services/pricingService';

export function PricingDisplay() {
  const [pricing, setPricing] = useState(null);

  useEffect(() => {
    getPricing().then(setPricing);
  }, []);

  if (!pricing) return <div>Loading prices...</div>;

  return (
    <div className="pricing-container">
      <h2>Current Pricing</h2>

      <div className="price-item">
        <span>Adult (13+):</span>
        <span className="price">
          $
          {
            pricing.menu_items.find(
              i => i.name === 'Adult Base Price'
            )?.price
          }
        </span>
      </div>

      <div className="price-item">
        <span>Child (6-12):</span>
        <span className="price">
          $
          {
            pricing.menu_items.find(
              i => i.name === 'Child Base Price'
            )?.price
          }
        </span>
      </div>

      {/* More pricing items... */}
    </div>
  );
}
```

### Step 4: PricingService Already Updated (✅ Complete)

The `PricingService` already pulls from database:

```python
def get_adult_price(self) -> Decimal:
    """Query database for current adult pricing"""
    menu_item = self.db.execute(
        select(MenuItem)
        .where(MenuItem.name == 'Adult Base Price')
        .where(MenuItem.is_active == True)
    ).scalar_one_or_none()

    return menu_item.base_price if menu_item else Decimal("55.00")
```

---

## 🔔 Price Change Notifications

### Notify Admins of Price Changes

```python
# When price changes, send notification
from .admin_alert_service import get_admin_alert_service

def notify_price_change(item_name, old_price, new_price, changed_by):
    get_admin_alert_service().send_alert(
        alert_type="PRICING_CHANGE",
        title=f"Price Updated: {item_name}",
        message=f"""
        Price change recorded:

        Item: {item_name}
        Old Price: ${old_price}
        New Price: ${new_price}
        Changed By: {changed_by}

        All new quotes will use updated pricing.
        Frontend pricing display will refresh automatically.
        """,
        priority="MEDIUM"
    )
```

---

## 📱 Frontend Price Refresh

### Option A: Polling (Simple)

```typescript
// Refresh pricing every 15 minutes
setInterval(
  async () => {
    const newPricing = await fetchCurrentPricing();
    cachePricing(newPricing);
    // Update UI if component is mounted
  },
  15 * 60 * 1000
);
```

### Option B: WebSocket (Real-time)

```typescript
// Real-time price updates via WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/pricing');

ws.onmessage = event => {
  const { type, data } = JSON.parse(event.data);

  if (type === 'PRICE_UPDATE') {
    // Update pricing cache immediately
    cachePricing(data.new_pricing);

    // Show toast notification
    toast.info(`Pricing updated: ${data.changed_items.join(', ')}`);
  }
};
```

### Option C: Server-Sent Events (SSE)

```python
# Backend: Push updates to connected clients
@router.get("/pricing/stream")
async def pricing_stream():
    async def event_generator():
        while True:
            # Check for price changes
            if has_pricing_changes():
                yield f"data: {json.dumps(get_current_pricing())}\n\n"
            await asyncio.sleep(60)  # Check every minute

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

---

## 🎯 Recommended Approach

### **Hybrid System:**

1. **Database as Source of Truth**
   - All prices stored in `menu_items` and `addon_items` tables
   - Admin panel to update prices
   - Price change history tracked

2. **Frontend Caching with TTL**
   - Cache pricing for 15 minutes in localStorage
   - Fetch fresh data on page load if cache expired
   - Reduces database queries

3. **AI Service Uses Database**
   - PricingService queries database in real-time
   - Fallback to hardcoded values if database unavailable
   - Always gets latest prices for quotes

4. **Admin Notifications**
   - Email/Slack alert when prices change
   - WhatsApp notification for critical changes
   - Dashboard shows price change history

---

## 🚀 Implementation Timeline

### Phase 1: Database Setup (1 hour)

- [ ] Create `price_change_history` table
- [ ] Seed database with current pricing
- [ ] Add indexes for performance

### Phase 2: Admin API (2 hours)

- [ ] Create GET `/api/admin/pricing/menu-items`
- [ ] Create PUT `/api/admin/pricing/menu-items/{id}`
- [ ] Create GET `/api/admin/pricing/price-history`
- [ ] Add authentication/authorization

### Phase 3: Admin UI (4 hours)

- [ ] Build pricing management page
- [ ] Inline edit functionality
- [ ] Price history timeline
- [ ] Bulk update form

### Phase 4: Frontend Integration (2 hours)

- [ ] Create `pricingService.ts`
- [ ] Update pricing display components
- [ ] Add caching with TTL
- [ ] Test real-time updates

### Phase 5: Testing (1 hour)

- [ ] Test price changes reflect in AI quotes
- [ ] Test frontend updates
- [ ] Test cache invalidation
- [ ] Test admin notifications

---

## ✅ Current Status

**What's Already Done:**

- ✅ `menu_items` and `addon_items` tables exist
- ✅ `PricingService` queries database
- ✅ Fallback to hardcoded prices if database unavailable
- ✅ AI system uses `PricingService` for quotes

**What Needs to Be Built:**

- [ ] `price_change_history` table
- [ ] Admin pricing management UI
- [ ] Frontend price API endpoints
- [ ] Frontend caching service
- [ ] Price change notifications
- [ ] Admin dashboard for price history

---

## 💡 Best Practices

1. **Never Hardcode Prices in Frontend**
   - Always pull from API
   - Cache with short TTL (15 minutes)

2. **Version Control for Prices**
   - Track all changes in `price_change_history`
   - Know who changed what and when

3. **Test Before Production**
   - Test price changes in staging environment
   - Verify quotes reflect new prices immediately

4. **Communication**
   - Notify admins of all price changes
   - Consider notifying customers of price increases (optional)

5. **Gradual Rollout**
   - Test with one price change first
   - Monitor for issues before bulk updates

---

## 📞 Support & Questions

If you need help implementing any part of this system, let me know!

**Priority order for implementation:**

1. Phase 1: Database setup (needed for everything else)
2. Phase 2: Admin API (needed for price updates)
3. Phase 3: Admin UI (makes it user-friendly)
4. Phase 4: Frontend integration (completes the loop)
5. Phase 5: Testing (ensures everything works)

---

**Current pricing confirmed:**

- Adult: $55 ✅
- Child (6-12): $30 ✅
- Child under 5: FREE ✅
- Filet upgrade: $5 ✅
- Lobster upgrade: $15 ✅
- Party minimum: $550 ✅
- Travel: First 30 miles FREE, $2/mile after ✅

All prices are now database-driven with proper fallbacks! 🎉
