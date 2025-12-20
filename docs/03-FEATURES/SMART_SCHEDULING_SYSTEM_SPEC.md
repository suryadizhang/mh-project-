# Smart Scheduling System - Technical Specification

**Version:** 1.0 **Created:** 2024-12-20 **Status:** APPROVED FOR
IMPLEMENTATION **Batch:** 1 (Core) + Extensions

---

## 📋 Executive Summary

This document defines the Smart Scheduling System for My Hibachi,
enabling:

1. **Address-first booking** - Capture venue before date/time for
   service area validation
2. **Travel time optimization** - Google Maps integration for chef
   travel estimates
3. **Dynamic slot adjustment** - Auto-shift bookings ±30-60 min for
   travel logistics
4. **Chef assignment optimization** - Suggest best chef based on
   location/skills
5. **Booking negotiation** - Politely request existing customers to
   shift times

---

## 🎯 Business Rules

### Event Duration

| Party Size   | Duration     | Notes            |
| ------------ | ------------ | ---------------- |
| 1-10 guests  | 90 minutes   | Standard party   |
| 11-20 guests | 105 minutes  | Medium party     |
| 21-30 guests | 120 minutes  | Large party      |
| 31+ guests   | 120+ minutes | May need 2 chefs |

### Time Slots (4 per day)

| Slot   | Standard Time | ±30 min Range       | ±60 min Range (Max) |
| ------ | ------------- | ------------------- | ------------------- |
| Slot 1 | 12:00 PM      | 11:30 AM - 12:30 PM | 11:00 AM - 1:00 PM  |
| Slot 2 | 3:00 PM       | 2:30 PM - 3:30 PM   | 2:00 PM - 4:00 PM   |
| Slot 3 | 6:00 PM       | 5:30 PM - 6:30 PM   | 5:00 PM - 7:00 PM   |
| Slot 4 | 9:00 PM       | 8:30 PM - 9:30 PM   | 8:00 PM - 10:00 PM  |

**Adjustment Logic:**

- Try ±30 min first (minimal disruption)
- Only use ±60 min if travel time requires it
- Adjustment increments: 30 minutes

### Rush Hour Traffic

| Day     | Rush Period       | Travel Time Multiplier |
| ------- | ----------------- | ---------------------- |
| Mon-Fri | 3:00 PM - 7:00 PM | 1.5x (50% increase)    |
| Sat-Sun | No rush           | 1.0x (normal)          |

### Buffer Times

| Between                       | Buffer             |
| ----------------------------- | ------------------ |
| Event end → Chef travel start | 15 minutes         |
| Chef arrival → Event start    | 30 minutes (setup) |

### Adjustment Priority

- **Last booked** booking adjusts first
- Customer-requested chef takes **priority** over optimization
- **Try ±30 minutes first** (minimal customer disruption)
- **Use ±60 minutes only if** travel time requires it
- Maximum adjustment: ±60 minutes per slot

---

## 🔢 Implementation Priority Order

### Priority 1: Core Foundation (Batch 1 - MUST HAVE)

| #   | Feature                                           | Estimated Time | Dependencies |
| --- | ------------------------------------------------- | -------------- | ------------ |
| 1.1 | Database schema updates (locations, travel cache) | 2 hours        | None         |
| 1.2 | Core Booking CRUD enhancements                    | 3 hours        | 1.1          |
| 1.3 | Authentication (JWT + API keys)                   | 2 hours        | 1.2          |
| 1.4 | 6-tier RBAC system (see existing matrix)          | 3 hours        | 1.3          |
| 1.5 | Audit trail enhancement                           | 2 hours        | 1.4          |

### Priority 2: Frontend Flow & Address First (Batch 1 - HIGH)

| #   | Feature                                      | Estimated Time | Dependencies |
| --- | -------------------------------------------- | -------------- | ------------ |
| 2.1 | Refactor BookUs page - address first         | 3 hours        | 1.1          |
| 2.2 | Refactor Quote page - address first          | 2 hours        | 2.1          |
| 2.3 | Service area validation on address           | 1 hour         | 2.2          |
| 2.4 | Geocoding integration (lat/lng from address) | 2 hours        | 2.3          |

### Priority 3: Travel Time Integration (Batch 1 - HIGH)

| #   | Feature                               | Estimated Time | Dependencies |
| --- | ------------------------------------- | -------------- | ------------ |
| 3.1 | Google Maps Distance Matrix API setup | 2 hours        | 2.4          |
| 3.2 | Travel time service with caching      | 3 hours        | 3.1          |
| 3.3 | Rush hour awareness logic             | 1 hour         | 3.2          |
| 3.4 | Chef location management              | 2 hours        | 3.3          |

### Priority 4: Smart Suggestions (Batch 1 - MEDIUM)

| #   | Feature                              | Estimated Time | Dependencies |
| --- | ------------------------------------ | -------------- | ------------ |
| 4.1 | Availability engine with travel gaps | 3 hours        | 3.4          |
| 4.2 | Alternative time suggestion API      | 2 hours        | 4.1          |
| 4.3 | Frontend suggestion display          | 2 hours        | 4.2          |

### Priority 5: Chef Optimization (Batch 2 - MEDIUM)

| #   | Feature                                 | Estimated Time | Dependencies |
| --- | --------------------------------------- | -------------- | ------------ |
| 5.1 | Chef assignment optimizer algorithm     | 4 hours        | 4.3          |
| 5.2 | Google Calendar integration (chef sync) | 4 hours        | 5.1          |
| 5.3 | Station manager suggestion UI           | 3 hours        | 5.2          |
| 5.4 | Customer chef preference handling       | 2 hours        | 5.3          |
| 5.5 | Guest count skill matching              | 1 hour         | 5.4          |

### Priority 6: Dynamic Adjustment (Batch 2 - MEDIUM)

| #   | Feature                   | Estimated Time | Dependencies |
| --- | ------------------------- | -------------- | ------------ |
| 6.1 | Slot adjustment algorithm | 4 hours        | 5.4          |
| 6.2 | Conflict resolution logic | 3 hours        | 6.1          |
| 6.3 | Admin adjustment UI       | 2 hours        | 6.2          |

### Priority 7: Negotiation System (Batch 3 - LOW)

| #   | Feature                                  | Estimated Time | Dependencies |
| --- | ---------------------------------------- | -------------- | ------------ |
| 7.1 | Negotiation request model                | 2 hours        | 6.3          |
| 7.2 | SMS/Email notification for shift request | 2 hours        | 7.1          |
| 7.3 | Response tracking and auto-apply         | 2 hours        | 7.2          |
| 7.4 | Customer response UI                     | 2 hours        | 7.3          |

---

## 🗄️ Database Schema

### New Tables

```sql
-- ============================================================
-- SCHEMA: ops (Operations)
-- ============================================================

-- Chef home locations for travel calculation
CREATE TABLE IF NOT EXISTS ops.chef_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chef_id UUID NOT NULL REFERENCES ops.chefs(id) ON DELETE CASCADE,
    home_address TEXT,
    home_address_encrypted BYTEA,  -- For PII protection
    home_lat DECIMAL(10, 8),
    home_lng DECIMAL(11, 8),
    service_radius_km DECIMAL(6, 2) DEFAULT 50.00,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(chef_id)
);

-- Slot configuration (adjustable time slots)
CREATE TABLE IF NOT EXISTS ops.slot_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slot_number INT NOT NULL CHECK (slot_number BETWEEN 1 AND 4),
    standard_time TIME NOT NULL,
    -- ±30 minute adjustment range (preferred)
    min_start_time_30 TIME NOT NULL,
    max_start_time_30 TIME NOT NULL,
    -- ±60 minute adjustment range (maximum)
    min_start_time_60 TIME NOT NULL,
    max_start_time_60 TIME NOT NULL,
    adjustment_increment_minutes INT DEFAULT 30,  -- Adjust in 30-min steps
    min_duration_minutes INT DEFAULT 90,
    max_duration_minutes INT DEFAULT 120,
    buffer_before_minutes INT DEFAULT 30,  -- Setup time
    buffer_after_minutes INT DEFAULT 15,   -- Cleanup + travel prep
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(slot_number)
);

-- Default slot configuration
-- ±30 min = preferred adjustment, ±60 min = maximum adjustment
INSERT INTO ops.slot_configurations (
    slot_number, standard_time,
    min_start_time_30, max_start_time_30,
    min_start_time_60, max_start_time_60
) VALUES
    (1, '12:00:00', '11:30:00', '12:30:00', '11:00:00', '13:00:00'),
    (2, '15:00:00', '14:30:00', '15:30:00', '14:00:00', '16:00:00'),
    (3, '18:00:00', '17:30:00', '18:30:00', '17:00:00', '19:00:00'),
    (4, '21:00:00', '20:30:00', '21:30:00', '20:00:00', '22:00:00');

-- Travel time cache (Google Maps results)
CREATE TABLE IF NOT EXISTS ops.travel_time_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    origin_lat DECIMAL(10, 8) NOT NULL,
    origin_lng DECIMAL(11, 8) NOT NULL,
    dest_lat DECIMAL(10, 8) NOT NULL,
    dest_lng DECIMAL(11, 8) NOT NULL,
    departure_hour INT NOT NULL CHECK (departure_hour BETWEEN 0 AND 23),
    day_of_week INT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    is_rush_hour BOOLEAN DEFAULT FALSE,
    base_duration_seconds INT,
    traffic_duration_seconds INT,
    distance_meters INT,
    cached_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '24 hours',
    UNIQUE(origin_lat, origin_lng, dest_lat, dest_lng, departure_hour, day_of_week)
);

-- Chef assignments with travel tracking
CREATE TABLE IF NOT EXISTS ops.chef_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID NOT NULL REFERENCES core.bookings(id) ON DELETE CASCADE,
    chef_id UUID NOT NULL REFERENCES ops.chefs(id),
    assignment_type VARCHAR(20) NOT NULL CHECK (assignment_type IN ('auto', 'manual', 'customer_requested')),
    assigned_by UUID REFERENCES identity.users(id),
    assigned_at TIMESTAMPTZ DEFAULT NOW(),

    -- Travel from previous booking
    previous_booking_id UUID REFERENCES core.bookings(id),
    travel_time_minutes INT,
    travel_distance_km DECIMAL(8, 2),

    -- Customer preference
    is_customer_requested BOOLEAN DEFAULT FALSE,
    customer_notes TEXT,

    -- Status
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'declined', 'completed')),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(booking_id)
);

-- ============================================================
-- SCHEMA: core (Core business)
-- ============================================================

-- Booking negotiation requests
CREATE TABLE IF NOT EXISTS core.booking_negotiations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- The existing booking we're asking to shift
    existing_booking_id UUID NOT NULL REFERENCES core.bookings(id),

    -- The new booking that needs this slot
    new_booking_id UUID REFERENCES core.bookings(id),

    -- Time change request
    original_time TIME NOT NULL,
    proposed_time TIME NOT NULL,
    proposed_date DATE,  -- If suggesting different day
    shift_minutes INT NOT NULL,  -- +30, -60, etc.

    -- Request details
    reason TEXT NOT NULL,
    incentive_offered TEXT,  -- e.g., "10% discount on next booking"

    -- Status tracking
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN (
        'pending', 'sent', 'viewed', 'accepted', 'declined', 'expired', 'cancelled'
    )),

    -- Communication tracking
    notification_channel VARCHAR(20),  -- 'sms', 'email', 'both'
    notification_sent_at TIMESTAMPTZ,
    reminder_sent_at TIMESTAMPTZ,
    customer_viewed_at TIMESTAMPTZ,
    customer_response_at TIMESTAMPTZ,

    -- Auto-expiry
    expires_at TIMESTAMPTZ NOT NULL,

    created_by UUID REFERENCES identity.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- ALTER EXISTING TABLES
-- ============================================================

-- Add location fields to bookings
ALTER TABLE core.bookings
    ADD COLUMN IF NOT EXISTS venue_lat DECIMAL(10, 8),
    ADD COLUMN IF NOT EXISTS venue_lng DECIMAL(11, 8),
    ADD COLUMN IF NOT EXISTS venue_address_normalized TEXT,
    ADD COLUMN IF NOT EXISTS venue_place_id TEXT,  -- Google Place ID
    ADD COLUMN IF NOT EXISTS event_duration_minutes INT DEFAULT 90,
    ADD COLUMN IF NOT EXISTS adjusted_start_time TIME,  -- If shifted from standard
    ADD COLUMN IF NOT EXISTS adjustment_reason TEXT,
    ADD COLUMN IF NOT EXISTS preferred_chef_id UUID REFERENCES ops.chefs(id),
    ADD COLUMN IF NOT EXISTS chef_preference_notes TEXT;

-- Add indexes for travel queries
CREATE INDEX IF NOT EXISTS idx_bookings_venue_location
    ON core.bookings (venue_lat, venue_lng)
    WHERE venue_lat IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_bookings_date_time
    ON core.bookings (event_date, event_time);

CREATE INDEX IF NOT EXISTS idx_travel_cache_lookup
    ON ops.travel_time_cache (origin_lat, origin_lng, dest_lat, dest_lng, expires_at);

CREATE INDEX IF NOT EXISTS idx_chef_assignments_date
    ON ops.chef_assignments (assigned_at);
```

---

## 🔧 Service Layer Architecture

### Directory Structure

```
apps/backend/src/services/
├── booking_service.py           # Existing - enhance
├── scheduling/
│   ├── __init__.py
│   ├── travel_time_service.py   # Google Maps integration
│   ├── slot_manager.py          # 4-slot management
│   ├── availability_engine.py   # Availability with travel gaps
│   ├── suggestion_engine.py     # Alternative time suggestions
│   ├── chef_optimizer.py        # Chef assignment algorithm
│   ├── adjustment_service.py    # Dynamic slot adjustment
│   ├── negotiation_service.py   # Booking shift requests
│   └── scheduling_orchestrator.py  # Coordinates all services
```

### Key Service Interfaces

#### TravelTimeService

```python
class TravelTimeService:
    """Calculates travel time between locations using Google Maps."""

    async def get_travel_time(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        departure_time: datetime
    ) -> TravelTimeResult:
        """
        Returns travel time considering traffic.
        Uses cache if available, otherwise calls Google Maps.
        """

    def is_rush_hour(self, dt: datetime) -> bool:
        """Mon-Fri 3PM-7PM = rush hour."""

    def apply_rush_hour_multiplier(
        self,
        base_minutes: int,
        dt: datetime
    ) -> int:
        """Apply 1.5x multiplier during rush hour."""
```

#### AvailabilityEngine

```python
class AvailabilityEngine:
    """Checks slot availability considering travel time."""

    async def get_available_slots(
        self,
        date: date,
        venue_lat: float,
        venue_lng: float,
        guest_count: int,
        preferred_chef_id: Optional[UUID] = None
    ) -> List[AvailableSlot]:
        """
        Returns available slots for a date.
        Considers:
        - Existing bookings
        - Chef availability
        - Travel time from previous booking
        - Event duration based on guest count
        """

    async def check_slot_feasibility(
        self,
        chef_id: UUID,
        date: date,
        slot: int,
        venue_lat: float,
        venue_lng: float
    ) -> SlotFeasibility:
        """
        Checks if a chef can do this slot.
        Returns adjustment needed if not directly feasible.
        """
```

#### SuggestionEngine

```python
class SuggestionEngine:
    """Suggests alternative times when requested slot unavailable."""

    async def get_suggestions(
        self,
        requested_date: date,
        requested_time: time,
        venue_lat: float,
        venue_lng: float,
        guest_count: int,
        max_suggestions: int = 5
    ) -> List[TimeSuggestion]:
        """
        Returns alternative options:
        1. Same day, different time (±1-2 hours)
        2. Adjacent days, same time
        3. Same day next week
        """
```

#### ChefOptimizer

```python
class ChefOptimizer:
    """Optimizes chef assignment for efficiency."""

    async def get_optimal_chef(
        self,
        booking: Booking,
        available_chefs: List[Chef]
    ) -> ChefRecommendation:
        """
        Ranks chefs by:
        1. Customer preference (highest priority)
        2. Travel time from previous booking
        3. Skill match for party size
        4. Overall rating
        5. Workload balance
        """

    async def suggest_assignments(
        self,
        date: date,
        bookings: List[Booking]
    ) -> List[AssignmentSuggestion]:
        """
        For station manager: optimal assignments for all bookings.
        Shows total travel time, efficiency score.
        """
```

#### NegotiationService

```python
class NegotiationService:
    """Manages booking shift requests."""

    async def request_time_shift(
        self,
        existing_booking_id: UUID,
        new_booking_id: UUID,
        proposed_shift_minutes: int,
        reason: str,
        incentive: Optional[str] = None
    ) -> NegotiationRequest:
        """
        Creates a polite request for customer to shift.
        Sends SMS/email notification.
        """

    async def process_response(
        self,
        negotiation_id: UUID,
        accepted: bool,
        customer_notes: Optional[str] = None
    ) -> NegotiationResult:
        """
        Handles customer response.
        If accepted, automatically adjusts the booking.
        """
```

---

## 🖥️ Frontend Changes

### BookUs Page - New Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    NEW BOOKING FLOW (4 STEPS)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  STEP 1: 📍 Venue Address (FIRST!)                              │
│  ├── Google Places Autocomplete                                 │
│  ├── Auto-fill city, state, ZIP                                 │
│  ├── Service area validation                                    │
│  └── Travel fee estimate shown                                  │
│                                                                  │
│  STEP 2: 👤 Customer Information                                │
│  ├── Name, Email, Phone                                         │
│  ├── Preferred communication method                             │
│  └── SMS consent                                                 │
│                                                                  │
│  STEP 3: 📅 Date & Time Selection                               │
│  ├── Calendar with availability                                 │
│  ├── Time slots (filtered by availability + travel)            │
│  ├── Guest count → Event duration shown                         │
│  ├── Preferred chef selection (optional)                        │
│  └── If unavailable: Show suggestions!                          │
│                                                                  │
│  STEP 4: 💳 Billing & Confirmation                              │
│  ├── Same as venue? checkbox                                    │
│  ├── Order summary with travel fee                              │
│  └── Submit booking                                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Component Refactoring

```typescript
// apps/customer/src/components/booking/
booking/
├── steps/
│   ├── VenueStep.tsx           // Step 1 - Address FIRST
│   ├── ContactStep.tsx         // Step 2 - Customer info
│   ├── DateTimeStep.tsx        // Step 3 - Date/time/guests
│   └── BillingStep.tsx         // Step 4 - Payment
├── shared/
│   ├── AddressAutocomplete.tsx // Google Places
│   ├── SlotPicker.tsx          // Time slot selection
│   ├── ChefPreference.tsx      // Optional chef selection
│   └── SuggestionModal.tsx     // Alternative times
├── BookingWizard.tsx           // Multi-step orchestrator
├── useBookingForm.ts           // Form state hook
└── types.ts                    // Shared types
```

---

## 🔌 API Endpoints

### New Endpoints Needed

```
# Availability with travel consideration
GET  /api/v1/scheduling/availability
     ?date=2025-01-15
     &venue_lat=33.7490
     &venue_lng=-84.3880
     &guest_count=15
     &preferred_chef_id=uuid (optional)

# Alternative time suggestions
GET  /api/v1/scheduling/suggestions
     ?date=2025-01-15
     &time=18:00
     &venue_lat=33.7490
     &venue_lng=-84.3880
     &guest_count=15

# Travel time estimate
GET  /api/v1/scheduling/travel-time
     ?origin_lat=33.7490
     &origin_lng=-84.3880
     &dest_lat=33.8490
     &dest_lng=-84.4880
     &departure_time=2025-01-15T17:00:00

# Chef optimization suggestions (admin)
GET  /api/v1/scheduling/chef-suggestions
     ?date=2025-01-15

# Assign chef to booking (admin)
POST /api/v1/bookings/{id}/assign-chef
     {
       "chef_id": "uuid",
       "assignment_type": "manual|customer_requested",
       "notes": "Customer requested this chef"
     }

# Request booking time shift (admin)
POST /api/v1/bookings/{id}/request-shift
     {
       "shift_minutes": 30,
       "reason": "To accommodate another booking",
       "incentive": "10% off next booking"
     }

# Customer responds to shift request
POST /api/v1/negotiations/{id}/respond
     {
       "accepted": true,
       "notes": "That works for me"
     }
```

---

## 🔐 Security & RBAC

### Role Hierarchy (6 Tiers)

| Tier | Role                 | Primary Responsibility                                            |
| ---- | -------------------- | ----------------------------------------------------------------- |
| 1    | **SUPER_ADMIN**      | Platform owner, all access                                        |
| 2    | **ADMIN**            | Station admin (multi-station assignment)                          |
| 3    | **CUSTOMER_SUPPORT** | Customer-facing ops, booking edits, time shift requests           |
| 4    | **STATION_MANAGER**  | Internal ops, chef assignment, scheduling (may also work as chef) |
| 5    | **CHEF**             | Own availability only                                             |
| 6    | **CUSTOMER**         | Book parties, view own bookings                                   |

### Scheduling Permission Matrix

| Action                         | Customer | Chef | Customer Support | Station Manager | Admin | Super Admin |
| ------------------------------ | :------: | :--: | :--------------: | :-------------: | :---: | :---------: |
| Create own booking             |    ✅    |  ✅  |        ✅        |       ✅        |  ✅   |     ✅      |
| View own bookings              |    ✅    |  ✅  |        ✅        |       ✅        |  ✅   |     ✅      |
| View all bookings              |    ❌    |  ❌  |        ✅        |       📍        |  📍   |     ✅      |
| Update own availability        |    ❌    |  ✅  |        ❌        |       ✅        |  ✅   |     ✅      |
| View chef availability         |    ❌    |  ❌  |        ❌        |       📍        |  📍   |     ✅      |
| Assign chef to booking         |    ❌    |  ❌  |        ❌        |       📍        |  📍   |     ✅      |
| Request time shift to customer |    ❌    |  ❌  |        ✅        |       ❌        |  ✅   |     ✅      |
| View chef home locations       |    ❌    |  ❌  |        ❌        |       📍        |  📍   |     ✅      |
| View travel time estimates     |    ❌    |  ❌  |        ❌        |       📍        |  📍   |     ✅      |
| Adjust booking slot times      |    ❌    |  ❌  |        ⚠️        |       📍        |  📍   |     ✅      |
| Manage slot configuration      |    ❌    |  ❌  |        ❌        |       ❌        |  ❌   |     ✅      |
| View travel analytics          |    ❌    |  ❌  |        ❌        |       📍        |  ✅   |     ✅      |

**Legend:** ✅ = Full access | 📍 = Station-scoped only | ⚠️ = With
confirmation modal | ❌ = No access

### Role-Specific Clarifications

**CUSTOMER_SUPPORT (Customer-Facing):**

- ✅ Can request time shifts (send polite messages to customers asking
  to move times)
- ✅ Can edit booking details (customer info, special requests)
- ⚠️ Can adjust slot times **with confirmation modal** (alert popup
  before saving)
- ❌ Cannot assign chefs (internal operation - station manager only)
- ❌ Cannot see chef home addresses (privacy)

**STATION_MANAGER (Internal Operations):**

- ✅ Assigns chefs to bookings for their station
- ✅ **Google Calendar integration** - chef assignments sync to shared
  calendar
- ✅ Schedules chefs and manages availability
- ✅ Can work as a chef themselves (update own availability)
- ✅ Can adjust slot times for travel logistics (no confirmation
  needed)
- ❌ Cannot contact customers for time shifts (customer support does
  this)
- ❌ Cannot edit customer booking details

**CHEF:**

- ✅ View own schedule (synced from Google Calendar)
- ✅ Update own availability (mark days off, preferred slots)
- ❌ Cannot see other chefs' schedules
- ❌ Cannot modify bookings

### Google Calendar Integration (Station Manager)

```
┌─────────────────────────────────────────────────────────────────┐
│                 CHEF ASSIGNMENT + CALENDAR SYNC                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Station Manager assigns chef to booking                        │
│                    │                                             │
│                    ▼                                             │
│  ┌─────────────────────────────────────┐                        │
│  │  1. Save assignment to database     │                        │
│  │  2. Create Google Calendar event    │                        │
│  │     - Chef's calendar               │                        │
│  │     - Station shared calendar       │                        │
│  │  3. Send notification to chef       │                        │
│  └─────────────────────────────────────┘                        │
│                    │                                             │
│                    ▼                                             │
│  Chef sees FULL event details in Google Calendar                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Chef Calendar Event Details

The chef collects payment at the event, so they need ALL details:

```
┌─────────────────────────────────────────────────────────────────┐
│  📅 Google Calendar Event: "MyHibachi - [Customer Name]"        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📍 LOCATION:                                                   │
│     123 Main Street, Atlanta, GA 30301                          │
│                                                                  │
│  ⏰ TIME:                                                        │
│     Saturday, Jan 15, 2025                                      │
│     6:00 PM - 8:00 PM (120 min)                                 │
│     Arrive by: 5:30 PM (30 min setup)                           │
│                                                                  │
│  👥 GUESTS: 40 Adults, 8 Children (6-12), 2 Toddlers (FREE)     │
│                                                                  │
│  📋 CUSTOMER INFO:                                               │
│     Name: John Smith                                            │
│     Phone: (404) 555-1234                                       │
│     Email: john@example.com                                     │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  🍱 ORDER BREAKDOWN:                                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  BASE PRICING:                                                  │
│  ─────────────────────────────────────────────────────          │
│     40 Adults × $55/person                        $2,200.00     │
│     8 Children (6-12) × $30/person                  $240.00     │
│     2 Toddlers (5 & under)                            FREE      │
│                                                                  │
│  PROTEIN SELECTIONS (2 per guest included):                     │
│  ─────────────────────────────────────────────────────          │
│     Base Proteins (FREE):                                       │
│       • 25x Chicken                                   $0.00     │
│       • 20x NY Strip Steak                            $0.00     │
│       • 15x Shrimp                                    $0.00     │
│       • 8x Tofu (vegetarian guests)                   $0.00     │
│                                                                  │
│     Premium Upgrades:                                           │
│       • 15x Filet Mignon (+$5/person)                $75.00     │
│       • 10x Lobster Tail (+$15/person)              $150.00     │
│       • 5x Salmon (+$5/person)                       $25.00     │
│                                                                  │
│     Extra Protein Additions:                                    │
│       • 5x Extra Chicken ($10 each)                  $50.00     │
│       • 3x Extra Filet Mignon ($10 + $5 = $15 each)  $45.00     │
│       • 2x Extra Lobster Tail ($10 + $15 = $25 each) $50.00     │
│                                                                  │
│  ADD-ONS (per person ordered):                                  │
│  ─────────────────────────────────────────────────────          │
│     • 50x Yakisoba Noodles (+$5)                    $250.00     │
│     • 20x Gyoza (+$10)                              $200.00     │
│     • 10x Extra Fried Rice (+$5)                     $50.00     │
│     • 10x Edamame (+$5)                              $50.00     │
│                                                                  │
│  📝 SPECIAL REQUESTS:                                            │
│     - 3 guests allergic to shellfish (no shrimp/lobster)        │
│     - Extra fried rice for kids                                 │
│     - Birthday celebration for Sarah - bring candles            │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  💰 PAYMENT BREAKDOWN (Chef Collects):                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Base (40 Adults + 8 Children):               $2,440.00         │
│  Premium Protein Upgrades:                      + $250.00       │
│  Extra Protein Additions:                       + $145.00       │
│  Add-ons (Noodles, Gyoza, etc.):                + $550.00       │
│  ─────────────────────────────────────────────────────          │
│  Order Subtotal:                                $3,385.00       │
│  Travel Fee (45 miles: 15 × $2):                  + $30.00      │
│  ─────────────────────────────────────────────────────          │
│  TOTAL ORDER VALUE:                             $3,415.00       │
│                                                                  │
│  Deposit Paid (online):                          - $500.00      │
│  (Minimum required: $100, customer paid extra)                  │
│  ─────────────────────────────────────────────────────          │
│  REMAINING BALANCE:                             $2,915.00       │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  💵 SUGGESTED TIPS (on $3,415.00 total):                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  20% Tip:  $683.00  →  Total with tip: $3,598.00                │
│  25% Tip:  $853.75  →  Total with tip: $3,768.75                │
│  30% Tip:  $1,024.50 → Total with tip: $3,939.50                │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  💳 PAYMENT OPTIONS (show to customer):                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CASH PAYMENT:                                                  │
│  ─────────────────────────────────────────────────────          │
│  Remaining Balance:             $2,915.00                       │
│  + 20% Tip:                       $683.00                       │
│  ═══════════════════════════════════════════════════            │
│  TOTAL CASH:                    $3,598.00                       │
│                                                                  │
│  ─────────────────────────────────────────────────────          │
│                                                                  │
│  CREDIT CARD PAYMENT (+3% processing fee):                      │
│  ─────────────────────────────────────────────────────          │
│  Remaining Balance:             $2,915.00                       │
│  + 20% Tip:                       $683.00                       │
│  Subtotal:                      $3,598.00                       │
│  + 3% Card Fee:                   + $107.94                     │
│  ═══════════════════════════════════════════════════            │
│  TOTAL CREDIT CARD:             $3,705.94                       │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  📊 QUICK REFERENCE - TOTAL DUE BY TIP %:                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Tip %  │  Cash Total  │  Card Total (+3%)                      │
│  ───────┼──────────────┼─────────────────                       │
│   20%   │  $3,598.00   │   $3,705.94                            │
│   25%   │  $3,768.75   │   $3,881.81                            │
│   30%   │  $3,939.50   │   $4,057.69                            │
│   Custom│  $2,915 + tip│   (balance + tip) × 1.03               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Menu Pricing Reference (from Dynamic Variables)

**Source of Truth:** `BusinessConfig` table + Menu page
(`apps/customer/src/app/menu/page.tsx`)

| Category             | Item                                                      | Price                    | Notes                                         |
| -------------------- | --------------------------------------------------------- | ------------------------ | --------------------------------------------- |
| **Base Pricing**     | Adult (13+)                                               | $55/person               | Includes 2 proteins, rice, veggies, salad     |
|                      | Child (6-12)                                              | $30/person               | Same 2 proteins, kid portions                 |
|                      | Toddler (5 & under)                                       | FREE                     | 1 protein, small portion, with adult purchase |
| **Party Minimum**    | Order Total                                               | $550                     | ≈ 10 adults minimum                           |
| **Base Proteins**    | Chicken                                                   | Included                 | FREE choice                                   |
|                      | NY Strip Steak                                            | Included                 | FREE choice                                   |
|                      | Shrimp                                                    | Included                 | FREE choice                                   |
|                      | Calamari                                                  | Included                 | FREE choice                                   |
|                      | Tofu                                                      | Included                 | FREE choice (vegetarian)                      |
| **Premium Upgrades** | Salmon                                                    | +$5/person               | Replaces one base protein                     |
|                      | Scallops                                                  | +$5/person               | Replaces one base protein                     |
|                      | Filet Mignon                                              | +$5/person               | Replaces one base protein                     |
|                      | Lobster Tail                                              | +$15/person              | Replaces one base protein                     |
| **Extra Protein**    | Base proteins (Chicken, NY Strip, Shrimp, Calamari, Tofu) | +$10/protein             | Each additional protein beyond included 2     |
|                      | Premium proteins (Salmon, Scallops, Filet Mignon)         | +$10 + $5 = $15/protein  | Extra protein fee + upgrade price             |
|                      | Lobster Tail                                              | +$10 + $15 = $25/protein | Extra protein fee + upgrade price             |
| **Add-ons**          | Yakisoba Noodles                                          | +$5/person               | Japanese lo mein                              |
|                      | Extra Fried Rice                                          | +$5/person               | Additional portion                            |
|                      | Extra Vegetables                                          | +$5/person               | Additional portion                            |
|                      | Edamame                                                   | +$5/person               | Steamed soybeans                              |
|                      | Gyoza                                                     | +$10/person              | Pan-fried dumplings                           |
| **Travel**           | First 30 miles                                            | FREE                     | From base location                            |
|                      | After 30 miles                                            | $2/mile                  | Each additional mile                          |

### ⚠️ AI Agent Data Integrity Instructions

**CRITICAL: Never use imaginary values. Always verify against real
data sources.**

| Data Type            | Source of Truth                                                  | How to Verify                                                         |
| -------------------- | ---------------------------------------------------------------- | --------------------------------------------------------------------- |
| **Base Pricing**     | `BusinessConfig` table                                           | Query `SELECT * FROM core.business_config WHERE key LIKE 'pricing.%'` |
| **Menu Items**       | `menu.menu_items` table                                          | Query `SELECT name, price FROM menu.menu_items`                       |
| **Protein Upgrades** | `apps/backend/src/routers/v1/public_quote.py` → `UPGRADE_PRICES` | Check constant values in code                                         |
| **Add-on Prices**    | `apps/backend/src/routers/v1/public_quote.py` → `ADDON_PRICES`   | Check constant values in code                                         |
| **Travel Fee**       | `BusinessConfig` table                                           | `pricing.travel_free_miles`, `pricing.travel_per_mile`                |
| **Deposit Rules**    | `BusinessConfig` table                                           | `booking.deposit_minimum`                                             |
| **Party Minimum**    | `BusinessConfig` table                                           | `pricing.party_minimum`                                               |

**Before Creating Examples or Documentation:**

1. ✅ **Search the codebase** for actual values (`grep_search`,
   `semantic_search`)
2. ✅ **Read the source files** (`menu/page.tsx`, `public_quote.py`,
   `pricing_service.py`)
3. ✅ **Verify against database** if available (seed files,
   migrations)
4. ❌ **NEVER assume or make up** prices, percentages, or business
   rules
5. ❌ **NEVER use placeholder values** like "$X" or "TBD" - find real
   data

**Key Files to Check:**

```
apps/customer/src/app/menu/page.tsx          # Customer-facing prices
apps/backend/src/routers/v1/public_quote.py  # UPGRADE_PRICES, ADDON_PRICES
apps/backend/src/api/ai/endpoints/services/pricing_service.py  # BASE_PRICING
scripts/seed_menu_data.sql                    # Database seed values
```

### Deposit Rules

| Rule                  | Value                                                      |
| --------------------- | ---------------------------------------------------------- |
| **Minimum Deposit**   | $100                                                       |
| **Maximum Deposit**   | No limit (customer can pay full amount upfront if desired) |
| **Deposit Collected** | Online at time of booking                                  |
| **Remaining Balance** | Collected by chef at event                                 |

### Payment Calculation Formula

```python
# Payment breakdown for chef collection
class PaymentBreakdown:
    order_subtotal: Decimal      # Sum of menu items
    travel_fee: Decimal          # Based on distance
    total_order_value: Decimal   # subtotal + travel_fee
    deposit_paid: Decimal        # Collected online at booking
    remaining_balance: Decimal   # total_order_value - deposit_paid

    # Tip suggestions (based on TOTAL order, not remaining)
    tip_20_percent: Decimal      # total_order_value * 0.20
    tip_25_percent: Decimal      # total_order_value * 0.25
    tip_30_percent: Decimal      # total_order_value * 0.30

    # Cash totals
    cash_total_20: Decimal       # remaining_balance + tip_20
    cash_total_25: Decimal       # remaining_balance + tip_25
    cash_total_30: Decimal       # remaining_balance + tip_30

    # Credit card totals (+3% on remaining + tip)
    card_fee_rate: Decimal = 0.03
    card_total_20: Decimal       # (remaining + tip_20) * 1.03
    card_total_25: Decimal       # (remaining + tip_25) * 1.03
    card_total_30: Decimal       # (remaining + tip_30) * 1.03

def calculate_payment_breakdown(booking: Booking) -> PaymentBreakdown:
    """Calculate all payment options for chef collection."""

    total = booking.order_subtotal + booking.travel_fee
    remaining = total - booking.deposit_paid

    tip_20 = total * Decimal('0.20')
    tip_25 = total * Decimal('0.25')
    tip_30 = total * Decimal('0.30')

    return PaymentBreakdown(
        order_subtotal=booking.order_subtotal,
        travel_fee=booking.travel_fee,
        total_order_value=total,
        deposit_paid=booking.deposit_paid,
        remaining_balance=remaining,

        tip_20_percent=tip_20,
        tip_25_percent=tip_25,
        tip_30_percent=tip_30,

        cash_total_20=remaining + tip_20,
        cash_total_25=remaining + tip_25,
        cash_total_30=remaining + tip_30,

        card_total_20=(remaining + tip_20) * Decimal('1.03'),
        card_total_25=(remaining + tip_25) * Decimal('1.03'),
        card_total_30=(remaining + tip_30) * Decimal('1.03'),
    )
```

---

## 📊 Event Duration Calculator

```python
def calculate_event_duration(guest_count: int) -> int:
    """
    Calculate event duration based on party size.

    Returns duration in minutes.
    """
    if guest_count <= 10:
        return 90  # Standard 1.5 hours
    elif guest_count <= 20:
        return 105  # 1 hour 45 minutes
    elif guest_count <= 30:
        return 120  # 2 hours
    else:
        return 120  # 2 hours (may need 2 chefs)
```

---

## 🧪 Testing Requirements

### Unit Tests

- [ ] TravelTimeService - rush hour detection
- [ ] TravelTimeService - cache hit/miss
- [ ] AvailabilityEngine - slot conflicts
- [ ] ChefOptimizer - ranking algorithm
- [ ] Event duration calculation

### Integration Tests

- [ ] Google Maps API integration
- [ ] Full booking flow with travel
- [ ] Chef assignment workflow
- [ ] Negotiation flow

### E2E Tests

- [ ] Customer books with address first
- [ ] Customer sees suggestions when unavailable
- [ ] Admin assigns chef with travel info
- [ ] Customer accepts shift request

---

## 📈 Success Metrics

| Metric                   | Target | Measurement |
| ------------------------ | ------ | ----------- |
| Booking completion rate  | +15%   | Analytics   |
| Average chef travel time | -20%   | Database    |
| Slot utilization         | +25%   | Database    |
| Customer satisfaction    | 4.5+   | Surveys     |
| Shift acceptance rate    | 60%+   | Database    |

---

## 🔗 Related Documents

- `docs/DATABASE_ARCHITECTURE_BUSINESS_MODEL.md` - Full DB schema
- `.github/instructions/02-ARCHITECTURE.instructions.md` - System
  architecture
- `apps/backend/src/services/booking_service.py` - Existing booking
  logic

---

## ✅ Implementation Checklist

### Phase 1: Core (Batch 1)

- [ ] 1.1 Database schema migration
- [ ] 1.2 Booking CRUD enhancements
- [ ] 1.3 JWT + API key auth
- [ ] 1.4 6-tier RBAC (scheduling permissions)
- [ ] 1.5 Audit trail

### Phase 2: Address First (Batch 1)

- [ ] 2.1 BookUs page refactor
- [ ] 2.2 Quote page refactor
- [ ] 2.3 Service area validation
- [ ] 2.4 Geocoding integration

### Phase 3: Travel Time (Batch 1)

- [ ] 3.1 Google Maps setup
- [ ] 3.2 Travel time service
- [ ] 3.3 Rush hour logic
- [ ] 3.4 Chef locations

### Phase 4: Smart Features (Batch 2)

- [ ] 4.1 Availability engine
- [ ] 4.2 Suggestion API
- [ ] 4.3 Chef optimizer
- [ ] 4.4 Dynamic adjustment

### Phase 5: Negotiation (Batch 3)

- [ ] 5.1 Negotiation model
- [ ] 5.2 Notification system
- [ ] 5.3 Response handling
- [ ] 5.4 Customer UI
