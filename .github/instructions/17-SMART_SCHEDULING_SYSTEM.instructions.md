---
applyTo: '**'
---

# My Hibachi – Smart Scheduling System Technical Specification

**Version:** 1.0.0 **Created:** 2024-12-20 **Priority:** REFERENCE –
Use for all booking, scheduling, and chef assignment operations.

---

## 📋 Executive Summary

The Smart Scheduling System is an intelligent booking management
solution that optimizes:

1. **Slot availability** with travel time awareness
2. **Chef assignments** based on location efficiency
3. **Dynamic time adjustments** to maximize bookings
4. **Customer negotiations** for optimal scheduling

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SMART SCHEDULING SYSTEM                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   FRONTEND (Address First Flow)                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │ Step 1: Venue Address → Step 2: Date/Time → Step 3: Contact     │   │
│   │         (With Google Places Autocomplete + Geocoding)           │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    BOOKING API                                   │   │
│   │  POST /api/v1/bookings/check-availability                       │   │
│   │  • Receives: venue_lat, venue_lng, date, guest_count            │   │
│   │  • Returns: available_slots[], suggestions[], travel_info       │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│       ┌──────────────────────┼──────────────────────┐                  │
│       ▼                      ▼                      ▼                  │
│   ┌───────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│   │  SLOT     │    │   TRAVEL TIME   │    │    CHEF         │         │
│   │  MANAGER  │    │   CALCULATOR    │    │   OPTIMIZER     │         │
│   │           │    │                 │    │                 │         │
│   │ • 4 slots │    │ • Google Maps   │    │ • Availability  │         │
│   │ • ±60 min │    │ • Rush hour x1.5│    │ • Skills match  │         │
│   │ • Duration│    │ • Cache 24h     │    │ • Preferences   │         │
│   └───────────┘    └─────────────────┘    └─────────────────┘         │
│                              │                                          │
│                              ▼                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                 SUGGESTION ENGINE                                │   │
│   │  When requested slot unavailable:                                │   │
│   │  • Find closest available times (same day)                       │   │
│   │  • Suggest next available day                                    │   │
│   │  • Suggest same slot next week                                   │   │
│   │  • Score by travel efficiency                                    │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                 NEGOTIATION SYSTEM                               │   │
│   │  When new booking conflicts with existing:                       │   │
│   │  • Identify which booking can shift                              │   │
│   │  • Send polite request (SMS/Email)                               │   │
│   │  • Track response and auto-adjust                                │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📅 Implementation Phases (Priority Order)

### Phase 1: Foundation ✅ COMPLETE

| Task                              | Priority | Dependencies | Status  |
| --------------------------------- | -------- | ------------ | ------- |
| 1A. Database schema for locations | 🔴 HIGH  | None         | ✅ DONE |
| 1B. Frontend address-first flow   | 🔴 HIGH  | 1A           | ✅ DONE |
| 1C. Google Maps geocoding service | 🔴 HIGH  | 1A           | ✅ DONE |
| 1D. Slot configuration table      | 🟡 MED   | 1A           | ✅ DONE |

**Implementation:** `geocoding_service.py` - Full Google Maps API
integration with caching

### Phase 2: Core Auth & RBAC ✅ COMPLETE

| Task                           | Priority | Dependencies | Status  |
| ------------------------------ | -------- | ------------ | ------- |
| 2A. Verify JWT authentication  | 🔴 HIGH  | None         | ✅ DONE |
| 2B. API key authentication     | 🔴 HIGH  | 2A           | ✅ DONE |
| 2C. 4-tier RBAC implementation | 🔴 HIGH  | 2A           | ✅ DONE |
| 2D. Permission decorators      | 🟡 MED   | 2C           | ✅ DONE |

**Implementation:** 4-tier RBAC (Super Admin → Admin → Staff →
Customer) in `core/security.py`

### Phase 3: Chef Management ✅ COMPLETE

| Task                        | Priority | Dependencies | Status  |
| --------------------------- | -------- | ------------ | ------- |
| 3A. Chef locations table    | 🔴 HIGH  | 1A           | ✅ DONE |
| 3B. Chef availability API   | 🔴 HIGH  | 3A           | ✅ DONE |
| 3C. Chef assignment API     | 🔴 HIGH  | 3B           | ✅ DONE |
| 3D. Preferred chef handling | 🟡 MED   | 3C           | ✅ DONE |

**Implementation:** `chef_optimizer.py` - Full scoring algorithm with:

- Travel Score (40%): Distance/time to venue
- Skill Score (20%): Match specialty to party size
- Workload Score (15%): Balance bookings across chefs
- Rating Score (15%): Chef's average rating
- Preference Score (10% + 50 bonus): Customer requested chef

### Phase 4: Travel Time Integration ✅ COMPLETE

| Task                            | Priority | Dependencies | Status  |
| ------------------------------- | -------- | ------------ | ------- |
| 4A. Google Maps Distance Matrix | 🔴 HIGH  | 1C           | ✅ DONE |
| 4B. Travel time cache table     | 🟡 MED   | 4A           | ✅ DONE |
| 4C. Rush hour multiplier logic  | 🟡 MED   | 4A           | ✅ DONE |
| 4D. Travel-aware slot checker   | 🟡 MED   | 4C           | ✅ DONE |

**Implementation:** `travel_time_service.py` - Google Maps API, 7-day
cache, rush hour 1.5x (Mon-Fri 3-7PM)

### Phase 5: Smart Suggestions ✅ COMPLETE

| Task                            | Priority | Dependencies | Status  |
| ------------------------------- | -------- | ------------ | ------- |
| 5A. Suggestion engine service   | 🟡 MED   | 4D           | ✅ DONE |
| 5B. Alternative time finder     | 🟡 MED   | 5A           | ✅ DONE |
| 5C. Next day/week suggestions   | 🟡 MED   | 5A           | ✅ DONE |
| 5D. Frontend suggestion display | 🟡 MED   | 5C           | ✅ DONE |

**Implementation:** `suggestion_engine.py` - Same-day alternatives,
next-day, next-week suggestions

### Phase 6: Dynamic Slot Adjustment ✅ COMPLETE

| Task                          | Priority | Dependencies | Status  |
| ----------------------------- | -------- | ------------ | ------- |
| 6A. Slot flexibility config   | 🟡 MED   | 1D           | ✅ DONE |
| 6B. Auto-adjust algorithm     | 🟡 MED   | 6A, 4D       | ✅ DONE |
| 6C. Last-booked-adjusts rule  | 🟡 MED   | 6B           | ✅ DONE |
| 6D. Conflict resolution logic | 🟡 MED   | 6C           | ✅ DONE |

**Implementation:** `slot_manager.py` - 4 slots (12PM, 3PM, 6PM, 9PM)
with ±30min preferred / ±60min max adjustment

### Phase 7: Chef Optimizer ✅ COMPLETE

| Task                               | Priority | Dependencies | Status     |
| ---------------------------------- | -------- | ------------ | ---------- |
| 7A. Optimizer service              | 🔴 HIGH  | 3C, 4D       | ✅ DONE    |
| 7B. Guest count skill matching     | 🔴 HIGH  | 7A           | ✅ DONE    |
| 7C. Efficiency scoring             | 🔴 HIGH  | 7B           | ✅ DONE    |
| 7D. Station manager suggestions UI | 🟡 MED   | 7C           | ⏳ PENDING |

**Implementation:** `chef_optimizer.py` fully implemented with scoring
algorithm. **Next:** Station Manager UI for viewing and overriding
chef suggestions.

### Phase 8: Negotiation System ✅ COMPLETE

| Task                              | Priority | Dependencies | Status  |
| --------------------------------- | -------- | ------------ | ------- |
| 8A. Negotiation request table     | 🟢 LOW   | None         | ✅ DONE |
| 8B. Polite notification templates | 🟢 LOW   | 8A           | ✅ DONE |
| 8C. Response tracking             | 🟢 LOW   | 8B           | ✅ DONE |
| 8D. Auto-adjustment on acceptance | 🟢 LOW   | 8C           | ✅ DONE |

**Implementation:** `negotiation_service.py` - Full workflow with
SMS/email notifications, incentives, auto-update on acceptance

---

## 🗄️ Database Schema

### Phase 1: Location Schema

```sql
-- =====================================================
-- PHASE 1A: Add location fields to existing bookings
-- =====================================================

-- Add geocoding columns to bookings
ALTER TABLE core.bookings
ADD COLUMN IF NOT EXISTS venue_lat DECIMAL(10,8),
ADD COLUMN IF NOT EXISTS venue_lng DECIMAL(11,8),
ADD COLUMN IF NOT EXISTS venue_address_normalized TEXT,
ADD COLUMN IF NOT EXISTS venue_geocoded_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS estimated_duration_minutes INT DEFAULT 90;

-- Comment for context
COMMENT ON COLUMN core.bookings.venue_lat IS 'Latitude from Google Geocoding API';
COMMENT ON COLUMN core.bookings.venue_lng IS 'Longitude from Google Geocoding API';
COMMENT ON COLUMN core.bookings.venue_address_normalized IS 'Standardized address from Google';
COMMENT ON COLUMN core.bookings.estimated_duration_minutes IS 'Event duration: 90-120 min based on party size';

-- Index for geospatial queries
CREATE INDEX IF NOT EXISTS idx_bookings_geo
ON core.bookings (venue_lat, venue_lng)
WHERE venue_lat IS NOT NULL;
```

### Phase 1D: Slot Configuration

```sql
-- =====================================================
-- PHASE 1D: Slot configuration table
-- =====================================================

CREATE TABLE IF NOT EXISTS ops.slot_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slot_name VARCHAR(20) NOT NULL,        -- '12PM', '3PM', '6PM', '9PM'
    slot_time TIME NOT NULL,               -- 12:00, 15:00, 18:00, 21:00
    min_adjust_minutes INT DEFAULT -60,    -- Can start up to 60 min earlier
    max_adjust_minutes INT DEFAULT 60,     -- Can start up to 60 min later
    min_event_duration INT DEFAULT 90,     -- Minimum event length
    max_event_duration INT DEFAULT 120,    -- Maximum event length
    buffer_before_minutes INT DEFAULT 30,  -- Travel/setup buffer
    buffer_after_minutes INT DEFAULT 15,   -- Cleanup buffer
    max_bookings_per_slot INT DEFAULT 10,  -- Per slot across all chefs
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert default slots
INSERT INTO ops.slot_configurations
    (slot_name, slot_time, min_event_duration, max_event_duration)
VALUES
    ('12PM', '12:00:00', 90, 120),
    ('3PM', '15:00:00', 90, 120),
    ('6PM', '18:00:00', 90, 120),
    ('9PM', '21:00:00', 90, 120)
ON CONFLICT DO NOTHING;
```

### Phase 3A: Chef Locations

```sql
-- =====================================================
-- PHASE 3A: Chef locations table
-- =====================================================

CREATE TABLE IF NOT EXISTS ops.chef_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chef_id UUID NOT NULL REFERENCES ops.chefs(id) ON DELETE CASCADE,
    home_address_encrypted BYTEA,          -- Encrypted for PII protection
    home_lat DECIMAL(10,8) NOT NULL,
    home_lng DECIMAL(11,8) NOT NULL,
    service_radius_km DECIMAL(5,2) DEFAULT 50.0,
    is_primary BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(chef_id, is_primary)
);

-- Index for location lookups
CREATE INDEX IF NOT EXISTS idx_chef_locations_geo
ON ops.chef_locations (home_lat, home_lng);
```

### Phase 3C: Chef Assignments

```sql
-- =====================================================
-- PHASE 3C: Chef assignment tracking
-- =====================================================

CREATE TABLE IF NOT EXISTS ops.chef_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID NOT NULL REFERENCES core.bookings(id) ON DELETE CASCADE,
    chef_id UUID NOT NULL REFERENCES ops.chefs(id),
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    assigned_by UUID REFERENCES identity.users(id),
    assignment_type VARCHAR(20) NOT NULL CHECK (
        assignment_type IN ('auto', 'manual', 'customer_requested')
    ),
    travel_time_minutes INT,
    travel_distance_km DECIMAL(8,2),
    previous_booking_id UUID REFERENCES core.bookings(id),
    is_customer_requested BOOLEAN DEFAULT FALSE,
    customer_request_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(booking_id)  -- One chef per booking
);

CREATE INDEX IF NOT EXISTS idx_chef_assignments_chef_date
ON ops.chef_assignments (chef_id, assigned_at);
```

### Phase 4B: Travel Time Cache

```sql
-- =====================================================
-- PHASE 4B: Travel time cache (Google Maps results)
-- =====================================================

CREATE TABLE IF NOT EXISTS ops.travel_time_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    origin_lat DECIMAL(10,8) NOT NULL,
    origin_lng DECIMAL(11,8) NOT NULL,
    dest_lat DECIMAL(10,8) NOT NULL,
    dest_lng DECIMAL(11,8) NOT NULL,
    departure_hour INT NOT NULL CHECK (departure_hour BETWEEN 0 AND 23),
    day_of_week INT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    is_rush_hour BOOLEAN DEFAULT FALSE,
    base_duration_minutes INT NOT NULL,
    traffic_duration_minutes INT,
    distance_km DECIMAL(8,2) NOT NULL,
    cached_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '24 hours')
);

-- Unique constraint for cache lookups
CREATE UNIQUE INDEX IF NOT EXISTS idx_travel_cache_lookup
ON ops.travel_time_cache (
    ROUND(origin_lat::numeric, 3),
    ROUND(origin_lng::numeric, 3),
    ROUND(dest_lat::numeric, 3),
    ROUND(dest_lng::numeric, 3),
    departure_hour,
    day_of_week
);

-- Auto-cleanup expired cache entries
CREATE INDEX IF NOT EXISTS idx_travel_cache_expires
ON ops.travel_time_cache (expires_at);
```

### Phase 8A: Negotiation Requests

```sql
-- =====================================================
-- PHASE 8A: Booking negotiation requests
-- =====================================================

CREATE TABLE IF NOT EXISTS core.booking_negotiations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    existing_booking_id UUID NOT NULL REFERENCES core.bookings(id),
    new_booking_request_id UUID,  -- Pending booking that needs the slot
    original_time TIME NOT NULL,
    proposed_time TIME NOT NULL,
    shift_direction VARCHAR(10) CHECK (shift_direction IN ('earlier', 'later')),
    shift_minutes INT NOT NULL,
    reason TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (
        status IN ('pending', 'sent', 'accepted', 'declined', 'expired')
    ),
    notification_method VARCHAR(20),  -- 'sms', 'email', 'both'
    notification_sent_at TIMESTAMPTZ,
    customer_response TEXT,
    responded_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '24 hours'),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES identity.users(id)
);

CREATE INDEX IF NOT EXISTS idx_negotiations_booking
ON core.booking_negotiations (existing_booking_id, status);
```

---

## 🔧 Business Rules

### Event Duration Calculation

```python
def calculate_event_duration(guest_count: int) -> int:
    """
    Calculate event duration based on party size.

    Rules:
    - 1-10 guests: 90 minutes
    - 11-20 guests: 100 minutes
    - 21-30 guests: 110 minutes
    - 31+ guests: 120 minutes
    """
    if guest_count <= 10:
        return 90
    elif guest_count <= 20:
        return 100
    elif guest_count <= 30:
        return 110
    else:
        return 120
```

### Rush Hour Traffic Multiplier

```python
def get_traffic_multiplier(departure_time: datetime) -> float:
    """
    Apply traffic multiplier for rush hour.

    Rules:
    - Monday-Friday 3PM-7PM (15:00-19:00): 1.5x
    - All other times: 1.0x
    """
    weekday = departure_time.weekday()  # 0=Mon, 6=Sun
    hour = departure_time.hour

    is_weekday = weekday < 5  # Mon-Fri
    is_rush_hour = 15 <= hour < 19  # 3PM-7PM

    if is_weekday and is_rush_hour:
        return 1.5
    return 1.0
```

### Slot Adjustment Priority

```python
def determine_adjustment_priority(booking1: Booking, booking2: Booking) -> Booking:
    """
    Determine which booking should adjust when there's a travel conflict.

    Rules:
    1. Newer booking adjusts (last booked = first to adjust)
    2. Customer-requested chef takes priority (don't adjust)
    3. Smaller party adjusts over larger party
    """
    # Customer request takes priority
    if booking1.is_chef_requested and not booking2.is_chef_requested:
        return booking2  # booking2 adjusts
    if booking2.is_chef_requested and not booking1.is_chef_requested:
        return booking1  # booking1 adjusts

    # Newer booking adjusts
    if booking1.created_at > booking2.created_at:
        return booking1
    return booking2
```

### Chef Assignment Scoring

```python
def score_chef_assignment(
    chef: Chef,
    booking: Booking,
    existing_assignments: List[Assignment]
) -> float:
    """
    Score a chef for a booking assignment (higher = better).

    Factors:
    - Travel time from previous location (40% weight)
    - Chef rating (30% weight)
    - Experience with party size (20% weight)
    - Customer preference match (10% weight + 50 bonus if requested)
    """
    score = 0.0

    # Travel time score (inverse - shorter is better)
    travel_time = calculate_travel_time(chef, booking)
    max_travel = 90  # minutes
    travel_score = max(0, (max_travel - travel_time) / max_travel) * 40
    score += travel_score

    # Rating score
    rating_score = (chef.average_rating / 5.0) * 30
    score += rating_score

    # Experience score
    if booking.guest_count <= 15 and chef.specialty == 'intimate':
        score += 20
    elif booking.guest_count > 30 and chef.specialty == 'large_party':
        score += 20
    else:
        score += 10

    # Customer preference
    if booking.preferred_chef_id == chef.id:
        score += 60  # Major bonus for customer request

    return score
```

---

## 🖥️ Frontend Flow Change

### Current Flow:

```
Contact Info → Date/Time → Venue Address → Billing → Submit
```

### New Flow (Address First):

```
Venue Address (with geocoding) → Date/Time (with availability) → Contact Info → Billing → Submit
```

### Reason for Change:

Collecting the venue address FIRST allows us to:

1. Check chef availability based on location
2. Calculate travel times before showing available slots
3. Show slots that are actually feasible (not blocked by travel)
4. Pre-validate service area coverage

### Implementation:

```typescript
// apps/customer/src/app/BookUs/page.tsx

// Step indicator component
const BookingSteps = () => (
  <div className="booking-steps">
    <Step number={1} label="Event Venue" active={step === 1} />
    <Step number={2} label="Date & Time" active={step === 2} />
    <Step number={3} label="Your Details" active={step === 3} />
    <Step number={4} label="Confirm" active={step === 4} />
  </div>
);

// New state for step-based flow
const [step, setStep] = useState(1);
const [venueGeocoded, setVenueGeocoded] = useState(false);
const [venueCoordinates, setVenueCoordinates] = useState<{lat: number, lng: number} | null>(null);

// Geocode venue address before allowing date selection
const handleVenueSubmit = async () => {
  const address = `${venueStreet}, ${venueCity}, ${venueState} ${venueZipcode}`;

  try {
    const geocodeResult = await geocodeAddress(address);
    setVenueCoordinates(geocodeResult);
    setVenueGeocoded(true);
    setStep(2); // Move to date/time selection

    // Fetch availability with location context
    await fetchAvailabilityWithLocation(geocodeResult.lat, geocodeResult.lng);
  } catch (error) {
    setGeocodingError('Unable to verify address. Please check and try again.');
  }
};
```

---

## 🔌 API Endpoints

### New Endpoints to Create

```yaml
# Phase 1: Location-aware availability
POST /api/v1/bookings/check-availability-v2:
  description: Check availability with location context
  request:
    venue_lat: number
    venue_lng: number
    date: string (YYYY-MM-DD)
    guest_count: number
    preferred_chef_id?: UUID
  response:
    available_slots:
      - slot_time: "12PM"
        is_available: true
        available_chefs: 3
        estimated_duration: 90
    suggestions:
      - slot_date: "2025-01-15"
        slot_time: "3PM"
        reason: "Next available same-day slot"
    service_area:
      is_covered: true
      nearest_chef_distance_km: 15.2

# Phase 3: Chef Management
GET /api/v1/chefs/available:
  description: Get available chefs for a date/time/location
  query:
    date: string
    time_slot: string
    venue_lat: number
    venue_lng: number
  response:
    chefs:
      - id: UUID
        name: string
        rating: number
        travel_time_minutes: number
        is_customer_preferred: boolean

POST /api/v1/bookings/{id}/assign-chef:
  description: Assign a chef to a booking
  request:
    chef_id: UUID
    assignment_type: "auto" | "manual" | "customer_requested"
  response:
    assignment:
      id: UUID
      chef_id: UUID
      travel_time_minutes: number

# Phase 4: Travel Time
GET /api/v1/travel-time:
  description: Calculate travel time between two locations
  query:
    origin_lat: number
    origin_lng: number
    dest_lat: number
    dest_lng: number
    departure_time: datetime
  response:
    duration_minutes: number
    duration_with_traffic: number
    distance_km: number
    is_rush_hour: boolean

# Phase 7: Chef Optimizer
GET /api/v1/bookings/{date}/chef-suggestions:
  description: Get optimized chef assignments for a day
  response:
    assignments:
      - booking_id: UUID
        suggested_chef_id: UUID
        score: number
        travel_time: number
        reasoning: string

# Phase 8: Negotiation
POST /api/v1/negotiations/request-shift:
  description: Request an existing customer to shift their time
  request:
    existing_booking_id: UUID
    proposed_time: string
    reason: string
  response:
    negotiation_id: UUID
    notification_sent: boolean
```

---

## 📁 Service Layer Structure

```
apps/backend/src/services/
├── scheduling/
│   ├── __init__.py
│   ├── geocoding_service.py        # Google Geocoding API
│   ├── travel_time_service.py      # Google Distance Matrix API
│   ├── slot_manager_service.py     # 4 slots/day management
│   ├── suggestion_engine.py        # Alternative time suggestions
│   ├── chef_optimizer_service.py   # Best chef assignment
│   ├── negotiation_service.py      # Ask customers to shift
│   └── scheduling_orchestrator.py  # Coordinates all services
│
├── auth/
│   ├── __init__.py
│   ├── jwt_service.py              # JWT token handling (exists)
│   ├── api_key_service.py          # API key validation (NEW)
│   └── rbac_service.py             # 4-tier permissions (NEW)
```

---

## 🔐 4-Tier RBAC System

### Role Hierarchy

```
Super Admin (Level 1)
    ├── Full system access
    ├── Manage all stations
    ├── View all data
    └── System configuration
        │
        ▼
Admin (Level 2)
    ├── Manage own station
    ├── Manage staff and chefs
    ├── View station reports
    └── Cannot access other stations
        │
        ▼
Staff (Level 3)
    ├── Create/modify bookings
    ├── Assign chefs
    ├── View station bookings
    └── Cannot manage users
        │
        ▼
Customer (Level 4)
    ├── Create own bookings
    ├── View own bookings
    ├── Modify own profile
    └── Request specific chef
```

### Permission Decorators

```python
# apps/backend/src/core/auth/rbac.py

from functools import wraps
from enum import Enum

class Role(Enum):
    SUPER_ADMIN = 1
    ADMIN = 2
    STAFF = 3
    CUSTOMER = 4

class Permission(Enum):
    # Booking permissions
    BOOKING_CREATE = "booking:create"
    BOOKING_READ_OWN = "booking:read:own"
    BOOKING_READ_STATION = "booking:read:station"
    BOOKING_READ_ALL = "booking:read:all"
    BOOKING_UPDATE_OWN = "booking:update:own"
    BOOKING_UPDATE_STATION = "booking:update:station"
    BOOKING_UPDATE_ALL = "booking:update:all"
    BOOKING_DELETE = "booking:delete"

    # Chef permissions
    CHEF_ASSIGN = "chef:assign"
    CHEF_MANAGE = "chef:manage"

    # User permissions
    USER_MANAGE_STATION = "user:manage:station"
    USER_MANAGE_ALL = "user:manage:all"

    # System permissions
    SYSTEM_CONFIG = "system:config"

ROLE_PERMISSIONS = {
    Role.SUPER_ADMIN: [Permission.ALL],  # Wildcard
    Role.ADMIN: [
        Permission.BOOKING_READ_STATION,
        Permission.BOOKING_UPDATE_STATION,
        Permission.CHEF_ASSIGN,
        Permission.CHEF_MANAGE,
        Permission.USER_MANAGE_STATION,
    ],
    Role.STAFF: [
        Permission.BOOKING_CREATE,
        Permission.BOOKING_READ_STATION,
        Permission.BOOKING_UPDATE_STATION,
        Permission.CHEF_ASSIGN,
    ],
    Role.CUSTOMER: [
        Permission.BOOKING_CREATE,
        Permission.BOOKING_READ_OWN,
        Permission.BOOKING_UPDATE_OWN,
    ],
}

def require_permission(permission: Permission):
    """Decorator to check user has required permission."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not has_permission(current_user, permission):
                raise HTTPException(403, "Insufficient permissions")
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

---

## ✅ Implementation Checklist

### Today's Focus: Phase 1A (Database Schema)

- [ ] Create migration file for booking location fields
- [ ] Add venue_lat, venue_lng columns
- [ ] Add estimated_duration_minutes column
- [ ] Create slot_configurations table
- [ ] Create indexes for geospatial queries

### Next: Phase 1B (Frontend Address First)

- [ ] Refactor BookingPage to step-based flow
- [ ] Move venue address to Step 1
- [ ] Add geocoding on venue complete
- [ ] Pass coordinates to availability API

### Following: Phase 2 (Auth & RBAC)

- [ ] Verify existing JWT implementation
- [ ] Add API key authentication
- [ ] Implement 4-tier RBAC
- [ ] Add permission decorators

---

## 🔗 Related Documentation

- [16-INFRASTRUCTURE_DEPLOYMENT.instructions.md](./16-INFRASTRUCTURE_DEPLOYMENT.instructions.md) -
  Server setup
- [02-DATABASE_ARCHITECTURE.instructions.md](./02-DATABASE_ARCHITECTURE.instructions.md) -
  Database design
- [03-CODING_STYLE.instructions.md](./03-CODING_STYLE.instructions.md) -
  Coding standards

---

## 📝 Change Log

| Date       | Version | Changes                       |
| ---------- | ------- | ----------------------------- |
| 2024-12-20 | 1.0.0   | Initial specification created |
