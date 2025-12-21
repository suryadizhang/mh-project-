---
applyTo: '**'
---

# My Hibachi – Smart Scheduling System Technical Specification

**Version:** 1.0 **Created:** 2024-12-20 **Status:** Implementation
Ready

---

## 📋 Executive Summary

This document specifies the Smart Scheduling System for My Hibachi
Chef booking platform. The system optimizes chef assignments, manages
travel time between parties, handles slot adjustments, and provides
intelligent booking suggestions.

---

## 🎯 Core Requirements

### Business Rules

| Rule                    | Value                               | Notes                                   |
| ----------------------- | ----------------------------------- | --------------------------------------- |
| **Event Duration**      | 90-120 minutes                      | Based on party size                     |
| **Duration Formula**    | `60 + (guests × 3)` min, max 120    | 10 guests = 90 min, 20 guests = 120 min |
| **Time Slots**          | 12:00 PM, 3:00 PM, 6:00 PM, 9:00 PM | 4 slots per day                         |
| **Slot Adjustment**     | ±60 minutes                         | Can shift earlier or later              |
| **Buffer Time**         | 15 minutes                          | Between event end and travel start      |
| **Rush Hour**           | Mon-Fri 3:00 PM - 7:00 PM           | Travel time × 1.5                       |
| **Min Advance Booking** | 48 hours                            | Existing rule                           |
| **Max Future Booking**  | 90 days                             | Existing rule                           |

### Priority Order for Adjustments

1. **Customer-requested chef** takes priority over optimization
2. **Newer booking adjusts first** when conflicts arise
3. **Earlier slots have less flexibility** (12 PM can only shift
   later)
4. **Later slots have more flexibility** (6 PM can shift either way)

---

## 🏗️ Implementation Phases

### Phase 0: Core Foundation (PRIORITY 1) ⭐

**Focus:** Complete core Batch 1 features that everything else depends
on.

| Task                              | Status                  | Dependencies  |
| --------------------------------- | ----------------------- | ------------- |
| **0.1 JWT Authentication**        | 🔄 Exists, verify       | None          |
| **0.2 API Key Auth**              | 🔄 Check implementation | None          |
| **0.3 4-Tier RBAC**               | ⏳ Needs implementation | Auth complete |
| **0.4 Audit Trail**               | 🔄 Basic exists         | RBAC complete |
| **0.5 Booking CRUD Enhancements** | ⏳ Add chef assignment  | RBAC complete |

### Phase 1: Database Schema & Address-First Flow (PRIORITY 2) ⭐

**Focus:** Restructure booking flow to collect address first, add
location fields.

| Task                                     | Status | Dependencies         |
| ---------------------------------------- | ------ | -------------------- |
| **1.1 Database Schema Updates**          | ⏳     | Phase 0 complete     |
| **1.2 Frontend Address-First (Quote)**   | ⏳     | Schema ready         |
| **1.3 Frontend Address-First (Booking)** | ⏳     | Schema ready         |
| **1.4 Geocoding Service**                | ⏳     | Address fields exist |
| **1.5 Travel Time Cache Table**          | ⏳     | Geocoding works      |

### Phase 2: Smart Availability & Suggestions (PRIORITY 3)

**Focus:** When slot unavailable, suggest alternatives.

| Task                           | Status | Dependencies        |
| ------------------------------ | ------ | ------------------- |
| **2.1 Availability Engine**    | ⏳     | Phase 1 complete    |
| **2.2 Suggestion Algorithm**   | ⏳     | Availability engine |
| **2.3 Frontend Suggestion UI** | ⏳     | Algorithm ready     |

### Phase 3: Travel Time Integration (PRIORITY 4)

**Focus:** Google Maps API for travel estimates.

| Task                        | Status | Dependencies         |
| --------------------------- | ------ | -------------------- |
| **3.1 Google Maps Service** | ⏳     | Address geocoded     |
| **3.2 Rush Hour Logic**     | ⏳     | Travel service works |
| **3.3 Travel Time Caching** | ⏳     | API integrated       |

### Phase 4: Dynamic Slot Adjustment (PRIORITY 5)

**Focus:** Auto-adjust booking times for travel feasibility.

| Task                              | Status | Dependencies           |
| --------------------------------- | ------ | ---------------------- |
| **4.1 Slot Adjustment Engine**    | ⏳     | Travel times available |
| **4.2 Conflict Resolution Logic** | ⏳     | Adjustment engine      |
| **4.3 Booking Chain Validation**  | ⏳     | Conflict resolution    |

### Phase 5: Chef Assignment Optimization (PRIORITY 6)

**Focus:** Suggest optimal chef based on location, skills,
preferences.

| Task                             | Status | Dependencies     |
| -------------------------------- | ------ | ---------------- |
| **5.1 Chef Availability Matrix** | ⏳     | Phase 4 complete |
| **5.2 Optimization Algorithm**   | ⏳     | Matrix available |
| **5.3 Station Manager UI**       | ⏳     | Algorithm ready  |

### Phase 6: Negotiation System (PRIORITY 7)

**Focus:** Politely ask existing customers to shift times.

| Task                              | Status | Dependencies       |
| --------------------------------- | ------ | ------------------ |
| **6.1 Negotiation Request Model** | ⏳     | Phase 5 complete   |
| **6.2 Notification Templates**    | ⏳     | Model exists       |
| **6.3 Response Tracking**         | ⏳     | Notifications work |
| **6.4 Auto-Adjustment on Accept** | ⏳     | Response tracked   |

---

## 📊 Database Schema

### New Tables

```sql
-- ============================================
-- PHASE 1: Location & Configuration Tables
-- ============================================

-- Chef home locations for travel optimization
CREATE TABLE ops.chef_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chef_id UUID NOT NULL REFERENCES ops.chefs(id) ON DELETE CASCADE,
    home_address TEXT,                    -- Full address (encrypted in app)
    home_lat DECIMAL(10, 8),              -- Latitude
    home_lng DECIMAL(11, 8),              -- Longitude
    preferred_radius_km DECIMAL(6, 2) DEFAULT 50,  -- Max travel preference
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(chef_id)
);

-- Booking venue geocoded location
-- (Added as columns to existing core.bookings table)
ALTER TABLE core.bookings ADD COLUMN IF NOT EXISTS venue_lat DECIMAL(10, 8);
ALTER TABLE core.bookings ADD COLUMN IF NOT EXISTS venue_lng DECIMAL(11, 8);
ALTER TABLE core.bookings ADD COLUMN IF NOT EXISTS venue_address_normalized TEXT;
ALTER TABLE core.bookings ADD COLUMN IF NOT EXISTS event_duration_minutes INT DEFAULT 90;
ALTER TABLE core.bookings ADD COLUMN IF NOT EXISTS preferred_chef_id UUID REFERENCES ops.chefs(id);
ALTER TABLE core.bookings ADD COLUMN IF NOT EXISTS is_chef_preference_required BOOLEAN DEFAULT FALSE;

-- Slot configuration (adjustable time windows)
CREATE TABLE ops.slot_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slot_name VARCHAR(10) NOT NULL,       -- '12PM', '3PM', '6PM', '9PM'
    base_time TIME NOT NULL,              -- 12:00, 15:00, 18:00, 21:00
    min_adjust_minutes INT DEFAULT -30,   -- Can start 30 min earlier
    max_adjust_minutes INT DEFAULT 60,    -- Can start 60 min later
    min_event_duration INT DEFAULT 90,    -- Minimum event length
    max_event_duration INT DEFAULT 120,   -- Maximum event length
    is_active BOOLEAN DEFAULT TRUE,
    station_id UUID REFERENCES identity.stations(id),  -- Per-station config
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(slot_name, station_id)
);

-- Insert default slot configurations
INSERT INTO ops.slot_configurations (slot_name, base_time, min_adjust_minutes, max_adjust_minutes) VALUES
    ('12PM', '12:00', 0, 60),      -- 12PM can only shift later (not before noon)
    ('3PM', '15:00', -30, 60),     -- 3PM can shift 2:30-4:00
    ('6PM', '18:00', -60, 60),     -- 6PM can shift 5:00-7:00
    ('9PM', '21:00', -60, 30);     -- 9PM can shift earlier, limited later

-- ============================================
-- PHASE 3: Travel Time Cache
-- ============================================

CREATE TABLE ops.travel_time_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    origin_lat DECIMAL(10, 8) NOT NULL,
    origin_lng DECIMAL(11, 8) NOT NULL,
    dest_lat DECIMAL(10, 8) NOT NULL,
    dest_lng DECIMAL(11, 8) NOT NULL,
    departure_hour INT,                   -- 0-23
    day_of_week INT,                      -- 0=Sun, 6=Sat
    is_rush_hour BOOLEAN DEFAULT FALSE,
    base_duration_minutes INT NOT NULL,   -- Without traffic
    traffic_duration_minutes INT,         -- With traffic
    distance_km DECIMAL(8, 2),
    route_summary TEXT,                   -- "via I-95 N"
    cached_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '7 days'),

    -- Index for lookups (rounded to ~1km precision)
    UNIQUE(
        ROUND(origin_lat::numeric, 2),
        ROUND(origin_lng::numeric, 2),
        ROUND(dest_lat::numeric, 2),
        ROUND(dest_lng::numeric, 2),
        departure_hour,
        day_of_week
    )
);

-- ============================================
-- PHASE 5: Chef Assignment Tracking
-- ============================================

CREATE TABLE ops.chef_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID NOT NULL REFERENCES core.bookings(id) ON DELETE CASCADE,
    chef_id UUID NOT NULL REFERENCES ops.chefs(id),
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    assigned_by UUID REFERENCES identity.users(id),
    assignment_type VARCHAR(20) NOT NULL DEFAULT 'manual',
        -- 'customer_requested', 'auto_optimized', 'manual'

    -- Travel chain tracking
    previous_booking_id UUID REFERENCES core.bookings(id),
    travel_time_minutes INT,
    travel_distance_km DECIMAL(8, 2),

    -- Optimization metadata
    optimization_score DECIMAL(5, 2),     -- 0-100 efficiency score
    alternatives_considered INT,           -- How many chefs were evaluated

    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(booking_id)  -- One chef per booking
);

-- ============================================
-- PHASE 6: Negotiation System
-- ============================================

CREATE TABLE core.booking_negotiations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- The existing booking we're asking to move
    existing_booking_id UUID NOT NULL REFERENCES core.bookings(id),

    -- The new booking that needs the slot
    requesting_booking_id UUID REFERENCES core.bookings(id),

    -- Time shift proposal
    original_time TIME NOT NULL,
    proposed_time TIME NOT NULL,
    shift_minutes INT NOT NULL,           -- +30 = 30 min later, -30 = earlier

    -- Reason and status
    reason TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
        -- 'pending', 'sent', 'accepted', 'declined', 'expired', 'cancelled'

    -- Communication tracking
    notification_method VARCHAR(20),      -- 'sms', 'email', 'both'
    notification_sent_at TIMESTAMPTZ,
    reminder_sent_at TIMESTAMPTZ,
    customer_response_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,               -- Auto-expire if no response

    -- Incentive offered (if any)
    incentive_offered TEXT,               -- "10% discount on next booking"
    incentive_accepted BOOLEAN,

    created_by UUID REFERENCES identity.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

CREATE INDEX idx_bookings_venue_location ON core.bookings(venue_lat, venue_lng)
    WHERE venue_lat IS NOT NULL;

CREATE INDEX idx_chef_assignments_chef_date ON ops.chef_assignments(chef_id, assigned_at);

CREATE INDEX idx_travel_cache_lookup ON ops.travel_time_cache(
    ROUND(origin_lat::numeric, 2),
    ROUND(origin_lng::numeric, 2),
    departure_hour
) WHERE expires_at > NOW();

CREATE INDEX idx_negotiations_status ON core.booking_negotiations(status, expires_at)
    WHERE status IN ('pending', 'sent');
```

---

## 🔧 Service Layer Architecture

### Directory Structure

```
apps/backend/src/services/
├── scheduling/
│   ├── __init__.py
│   ├── travel_time_service.py      # Google Maps integration
│   ├── slot_manager_service.py     # Slot configuration & adjustment
│   ├── suggestion_engine.py        # Alternative time suggestions
│   ├── chef_optimizer_service.py   # Chef assignment optimization
│   ├── negotiation_service.py      # Customer time shift requests
│   └── scheduling_orchestrator.py  # Coordinates all services
├── geocoding/
│   ├── __init__.py
│   └── geocoding_service.py        # Address → lat/lng conversion
└── booking_service.py              # Enhanced with scheduling integration
```

### Service Contracts

#### 1. TravelTimeService

```python
class TravelTimeService:
    """Calculate travel time between locations using Google Maps API."""

    async def get_travel_time(
        self,
        origin: Coordinates,
        destination: Coordinates,
        departure_time: datetime,
    ) -> TravelTimeResult:
        """
        Returns travel time considering:
        - Base duration (no traffic)
        - Traffic duration (with traffic)
        - Rush hour multiplier (Mon-Fri 3-7 PM = ×1.5)
        - Distance in km
        """
        pass

    def is_rush_hour(self, dt: datetime) -> bool:
        """Check if datetime falls in rush hour (Mon-Fri 3-7 PM)."""
        pass

    async def get_cached_or_fetch(
        self,
        origin: Coordinates,
        destination: Coordinates,
        departure_time: datetime,
    ) -> TravelTimeResult:
        """Use cache if available, otherwise fetch from Google Maps."""
        pass
```

#### 2. SlotManagerService

```python
class SlotManagerService:
    """Manage time slots and their adjustability."""

    def calculate_event_duration(self, guest_count: int) -> int:
        """
        Calculate event duration based on party size.
        Formula: min(60 + (guests × 3), 120)
        Examples:
        - 10 guests = 90 min
        - 15 guests = 105 min
        - 20+ guests = 120 min
        """
        pass

    async def get_adjusted_slot_time(
        self,
        base_slot: str,  # '12PM', '3PM', '6PM', '9PM'
        required_start_after: datetime,
        station_id: UUID,
    ) -> Optional[datetime]:
        """
        Find adjusted slot time that starts after required time.
        Returns None if adjustment not possible within limits.
        """
        pass

    async def get_slot_flexibility(
        self,
        slot: str,
        station_id: UUID,
    ) -> SlotFlexibility:
        """Get min/max adjustment allowed for a slot."""
        pass
```

#### 3. SuggestionEngine

```python
class SuggestionEngine:
    """Generate alternative booking suggestions when requested slot unavailable."""

    async def get_suggestions(
        self,
        requested_date: date,
        requested_slot: str,
        venue_location: Coordinates,
        preferred_chef_id: Optional[UUID],
        guest_count: int,
        max_suggestions: int = 5,
    ) -> List[BookingSuggestion]:
        """
        Returns suggestions in priority order:
        1. Same day, different slot
        2. Same slot, next available day
        3. Same slot, next week same day
        4. Any available slot within ±3 days
        """
        pass

    async def check_availability_with_travel(
        self,
        date: date,
        slot: str,
        venue_location: Coordinates,
        chef_id: Optional[UUID],
    ) -> AvailabilityResult:
        """
        Check if slot is available considering:
        - Chef has no conflicting booking
        - Travel time from previous booking is feasible
        - Slot adjustment can accommodate travel if needed
        """
        pass
```

#### 4. ChefOptimizerService

```python
class ChefOptimizerService:
    """Optimize chef assignments for efficiency."""

    async def get_optimal_chef(
        self,
        booking: Booking,
        available_chefs: List[Chef],
    ) -> ChefAssignmentSuggestion:
        """
        Score and rank chefs based on:
        1. Customer preference (highest priority)
        2. Travel distance from previous booking
        3. Chef experience for party size
        4. Chef rating
        5. Workload balance
        """
        pass

    async def get_chef_suggestions(
        self,
        date: date,
        slot: str,
        venue_location: Coordinates,
        guest_count: int,
        preferred_chef_id: Optional[UUID],
    ) -> List[ChefAssignmentSuggestion]:
        """
        Returns ranked list of available chefs with:
        - Travel time from previous booking
        - Efficiency score
        - Whether customer requested
        """
        pass

    async def validate_chef_chain(
        self,
        chef_id: UUID,
        date: date,
    ) -> ChainValidationResult:
        """
        Validate that chef's booking chain for the day is feasible.
        Returns any conflicts or required adjustments.
        """
        pass
```

#### 5. NegotiationService

```python
class NegotiationService:
    """Manage polite requests to shift existing bookings."""

    async def create_shift_request(
        self,
        existing_booking_id: UUID,
        requesting_booking_id: UUID,
        proposed_shift_minutes: int,
        reason: str,
        incentive: Optional[str] = None,
    ) -> BookingNegotiation:
        """Create a time shift request."""
        pass

    async def send_notification(
        self,
        negotiation_id: UUID,
        method: str = 'both',  # 'sms', 'email', 'both'
    ) -> NotificationResult:
        """Send polite request to customer."""
        pass

    async def process_response(
        self,
        negotiation_id: UUID,
        accepted: bool,
    ) -> NegotiationResult:
        """
        Handle customer response:
        - If accepted: Auto-adjust booking time
        - If declined: Mark and consider alternatives
        """
        pass

    def get_notification_template(
        self,
        shift_minutes: int,
        incentive: Optional[str],
    ) -> NotificationTemplate:
        """Get polite SMS/email template."""
        pass
```

---

## 🖥️ Frontend Changes

### Address-First Flow Redesign

#### Current Flow:

```
1. Customer Info → 2. Date/Time → 3. Venue Address → 4. Submit
```

#### New Flow:

```
1. Venue Address → 2. Customer Info → 3. Date/Time (with suggestions) → 4. Submit
```

### Quote Calculator Changes (QuoteCalculator.tsx)

```tsx
// BEFORE: Steps order
const steps = [
  'Contact Information', // Step 1
  'Event Details', // Step 2
  'Location', // Step 3
  'Venue Address', // Step 4
  'Premium Upgrades', // Step 5
];

// AFTER: Reordered steps
const steps = [
  'Venue Address', // Step 1 - MOVED FIRST
  'Contact Information', // Step 2
  'Event Details', // Step 3
  'Premium Upgrades', // Step 4
];
```

### Booking Form Changes (BookUs/page.tsx)

```tsx
// BEFORE: Form sections order
<CustomerInfoSection />
<DateTimeSection />
<VenueAddressSection />
<BillingAddressSection />

// AFTER: Reordered sections
<VenueAddressSection />       {/* MOVED FIRST */}
<CustomerInfoSection />
<DateTimeSection
  venueLocation={venueCoordinates}  // NEW: Pass location for suggestions
  onSlotUnavailable={handleSuggestions}  // NEW: Handle suggestions
/>
<BillingAddressSection />
```

### New Suggestion UI Component

```tsx
// src/components/booking/SlotSuggestions.tsx

interface SlotSuggestion {
  date: string;
  slot: string;
  adjustedTime?: string; // If slot is adjusted
  availableChefs: number;
  travelNote?: string; // "Chef arriving from nearby location"
}

export function SlotSuggestions({
  suggestions,
  onSelect,
}: {
  suggestions: SlotSuggestion[];
  onSelect: (suggestion: SlotSuggestion) => void;
}) {
  return (
    <div className="slot-suggestions">
      <h3>That time isn't available, but we have these options:</h3>
      <div className="suggestions-grid">
        {suggestions.map(suggestion => (
          <SuggestionCard
            key={`${suggestion.date}-${suggestion.slot}`}
            suggestion={suggestion}
            onSelect={() => onSelect(suggestion)}
          />
        ))}
      </div>
    </div>
  );
}
```

---

## 📡 API Endpoints

### New Endpoints

```yaml
# Availability with suggestions
GET /api/v1/bookings/availability/smart
  Query:
    - date: string (YYYY-MM-DD)
    - slot: string (12PM, 3PM, 6PM, 9PM)
    - venue_lat: number
    - venue_lng: number
    - guest_count: number
    - preferred_chef_id?: UUID
  Response:
    - available: boolean
    - suggestions?: BookingSuggestion[]
    - adjusted_time?: string  # If slot needs adjustment

# Chef assignment suggestions
GET /api/v1/admin/bookings/{id}/chef-suggestions
  Response:
    - suggestions: ChefAssignmentSuggestion[]
    - customer_requested?: Chef  # If customer requested specific chef

# Assign chef to booking
POST /api/v1/admin/bookings/{id}/assign-chef
  Body:
    - chef_id: UUID
    - override_customer_preference?: boolean
  Response:
    - assignment: ChefAssignment
    - travel_info: TravelInfo

# Request time shift
POST /api/v1/admin/bookings/{id}/request-shift
  Body:
    - shift_minutes: number  # +30, -30, +60, -60
    - reason: string
    - incentive?: string
    - requesting_booking_id?: UUID
  Response:
    - negotiation: BookingNegotiation
    - notification_preview: string

# Respond to shift request (public link)
POST /api/v1/public/booking-shift/{token}
  Body:
    - accepted: boolean
    - decline_reason?: string
  Response:
    - success: boolean
    - new_time?: string

# Validate chef's day schedule
GET /api/v1/admin/chefs/{id}/schedule/{date}/validate
  Response:
    - valid: boolean
    - bookings: BookingWithTravel[]
    - conflicts?: ScheduleConflict[]
    - suggested_adjustments?: SlotAdjustment[]
```

---

## 🔐 RBAC Permissions

### New Permissions for Scheduling Features

| Permission                        | Super Admin | Admin | Staff | Customer |
| --------------------------------- | :---------: | :---: | :---: | :------: |
| View chef assignments             |     ✅      |  ✅   |  ✅   |    ❌    |
| Assign chef to booking            |     ✅      |  ✅   |  ✅   |    ❌    |
| Override customer chef preference |     ✅      |  ✅   |  ❌   |    ❌    |
| Request booking time shift        |     ✅      |  ✅   |  ✅   |    ❌    |
| View travel time data             |     ✅      |  ✅   |  ✅   |    ❌    |
| Configure slot settings           |     ✅      |  ✅   |  ❌   |    ❌    |
| View optimization scores          |     ✅      |  ✅   |  ❌   |    ❌    |
| Request preferred chef            |     ❌      |  ❌   |  ❌   |    ✅    |
| Respond to shift request          |     ❌      |  ❌   |  ❌   |    ✅    |

---

## 📋 Implementation Checklist

### Phase 0: Core Foundation ⭐ (Do First)

- [ ] **0.1** Verify JWT authentication implementation
- [ ] **0.2** Verify API key authentication for services
- [ ] **0.3** Implement 4-tier RBAC system
  - [ ] Create permission definitions
  - [ ] Add permission checking middleware
  - [ ] Update all protected endpoints
- [ ] **0.4** Enhance audit trail
  - [ ] Log all booking changes
  - [ ] Log chef assignments
  - [ ] Log negotiation actions
- [ ] **0.5** Booking CRUD enhancements
  - [ ] Add chef assignment endpoint
  - [ ] Add preferred chef field to booking form
  - [ ] Add event duration calculation

### Phase 1: Address-First & Location

- [ ] **1.1** Run database migration for new columns
- [ ] **1.2** Update QuoteCalculator.tsx - reorder steps
- [ ] **1.3** Update BookUs/page.tsx - reorder sections
- [ ] **1.4** Create GeocodingService for address → coordinates
- [ ] **1.5** Auto-geocode on booking creation
- [ ] **1.6** Create slot_configurations table and defaults

### Phase 2: Smart Availability

- [ ] **2.1** Create SuggestionEngine service
- [ ] **2.2** Implement `/availability/smart` endpoint
- [ ] **2.3** Create SlotSuggestions UI component
- [ ] **2.4** Integrate suggestions into booking flow

### Phase 3: Travel Time

- [ ] **3.1** Set up Google Maps API credentials
- [ ] **3.2** Create TravelTimeService
- [ ] **3.3** Implement travel time caching
- [ ] **3.4** Add rush hour logic
- [ ] **3.5** Store travel time in chef_assignments

### Phase 4: Slot Adjustment

- [ ] **4.1** Create SlotManagerService
- [ ] **4.2** Implement event duration calculation
- [ ] **4.3** Build slot adjustment algorithm
- [ ] **4.4** Add adjustment validation to booking flow

### Phase 5: Chef Optimization

- [ ] **5.1** Create ChefOptimizerService
- [ ] **5.2** Implement scoring algorithm
- [ ] **5.3** Build chef suggestion API
- [ ] **5.4** Create Station Manager UI for suggestions
- [ ] **5.5** Handle customer chef preferences

### Phase 6: Negotiation System

- [ ] **6.1** Create booking_negotiations table
- [ ] **6.2** Create NegotiationService
- [ ] **6.3** Build notification templates (polite language)
- [ ] **6.4** Create public response endpoint
- [ ] **6.5** Implement auto-adjustment on acceptance
- [ ] **6.6** Add negotiation tracking UI

---

## 🧪 Testing Strategy

### Unit Tests

```python
# tests/services/test_travel_time_service.py
def test_rush_hour_detection():
    """Mon-Fri 3-7 PM should be rush hour."""

def test_rush_hour_multiplier():
    """Rush hour travel time should be 1.5x base."""

def test_weekend_no_rush_hour():
    """Weekends should not have rush hour multiplier."""

# tests/services/test_slot_manager_service.py
def test_event_duration_small_party():
    """10 guests should be 90 minutes."""

def test_event_duration_large_party():
    """25 guests should cap at 120 minutes."""

def test_slot_adjustment_limits():
    """12 PM slot cannot adjust earlier than noon."""

# tests/services/test_suggestion_engine.py
def test_same_day_suggestions():
    """Should suggest other slots on same day first."""

def test_next_day_suggestions():
    """Should suggest next available day for same slot."""
```

### Integration Tests

```python
# tests/integration/test_booking_flow.py
def test_address_first_booking():
    """Booking should accept address before date selection."""

def test_chef_assignment_with_travel():
    """Chef assignment should consider travel time."""

def test_slot_adjustment_for_travel():
    """System should adjust slot when travel requires it."""
```

---

## 📊 Metrics & Monitoring

### Key Metrics to Track

| Metric                     | Target  | Alert Threshold |
| -------------------------- | ------- | --------------- |
| Booking completion rate    | >80%    | <60%            |
| Suggestion acceptance rate | >40%    | <20%            |
| Chef utilization           | >70%    | <50%            |
| Average travel time        | <45 min | >60 min         |
| Negotiation success rate   | >50%    | <30%            |
| Slot adjustment frequency  | <20%    | >40%            |

---

## 🚀 Deployment Notes

### Environment Variables Needed

```env
# Google Maps
GOOGLE_MAPS_API_KEY=your_key_here
GOOGLE_MAPS_RATE_LIMIT=50  # requests per second

# Scheduling defaults
DEFAULT_EVENT_DURATION=90
MAX_EVENT_DURATION=120
RUSH_HOUR_START=15  # 3 PM
RUSH_HOUR_END=19    # 7 PM
RUSH_HOUR_MULTIPLIER=1.5
TRAVEL_BUFFER_MINUTES=15
```

### Feature Flags

```python
FEATURE_FLAGS = {
    'smart_scheduling': True,
    'travel_time_calculation': True,
    'auto_slot_adjustment': False,  # Enable after testing
    'negotiation_system': False,    # Enable after Phase 5
}
```

---

## 📚 Related Documents

- [16-INFRASTRUCTURE_DEPLOYMENT.instructions.md](./16-INFRASTRUCTURE_DEPLOYMENT.instructions.md) -
  Server setup
- [08-BACKEND_DATABASE.instructions.md](./08-BACKEND_DATABASE.instructions.md) -
  Database patterns
- [06-CUSTOMER_APP.instructions.md](./06-CUSTOMER_APP.instructions.md) -
  Frontend patterns

---

_Last Updated: 2024-12-20_
