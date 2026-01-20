# Station Management Quick Start Guide

## 🚀 Getting Started

### 1. Seed the First Station

```bash
cd apps/backend
python seed_first_station.py
```

**Expected Output**:
```
✓ Generated station code: STATION-CA-BAY-001
✓ Station created successfully!

📋 Station Details:
   ID:           [uuid]
   Code:         STATION-CA-BAY-001
   Name:         California Bay Area
   Display Name: MyHibachi - California Bay Area
   Location:     Fremont, CA 94539
   Timezone:     America/Los_Angeles
   Status:       active
```

---

## 📡 API Endpoints

### Base URL
```
http://localhost:8000/api/stations
```

### 1. Create Station

```bash
POST /api/stations
```

**Request Body**:
```json
{
  "name": "Texas Austin",
  "display_name": "MyHibachi - Austin",
  "city": "Austin",
  "state": "TX",
  "country": "US",
  "timezone": "America/Chicago",
  "email": "austin@myhibachi.com",
  "phone": "+1-512-555-0200",
  "address": "456 Congress Ave",
  "postal_code": "78701",
  "status": "active",
  "business_hours": {
    "monday": {"open": "10:00", "close": "22:00"},
    "tuesday": {"open": "10:00", "close": "22:00"},
    "wednesday": {"open": "10:00", "close": "22:00"},
    "thursday": {"open": "10:00", "close": "22:00"},
    "friday": {"open": "10:00", "close": "23:00"},
    "saturday": {"open": "09:00", "close": "23:00"},
    "sunday": {"open": "09:00", "close": "22:00"}
  },
  "max_concurrent_bookings": 12,
  "booking_lead_time_hours": 24
}
```

**Response**: `201 Created`
```json
{
  "id": "uuid",
  "code": "STATION-TX-AUSTIN-001",  // Auto-generated!
  "name": "Texas Austin",
  "display_name": "MyHibachi - Austin",
  "city": "Austin",
  "state": "TX",
  "country": "US",
  "timezone": "America/Chicago",
  ...
}
```

---

### 2. List All Stations

```bash
GET /api/stations?skip=0&limit=20&status=active
```

**Query Parameters**:
- `skip` (int): Pagination offset (default: 0)
- `limit` (int): Results per page (default: 20, max: 100)
- `status` (string): Filter by status (active, inactive, suspended, maintenance)
- `include_stats` (bool): Include user/booking counts

**Response**: `200 OK`
```json
[
  {
    "id": "uuid",
    "code": "STATION-CA-BAY-001",
    "name": "California Bay Area",
    ...
    "user_count": 5,
    "active_booking_count": 12,
    "total_booking_count": 247
  }
]
```

---

### 3. Get Station Details

```bash
GET /api/stations/{station_id}?include_stats=true
```

**Response**: `200 OK`
```json
{
  "id": "uuid",
  "code": "STATION-CA-BAY-001",
  "name": "California Bay Area",
  "display_name": "MyHibachi - California Bay Area",
  ...
  "user_count": 5,
  "last_activity": "2025-10-28T10:30:00Z"
}
```

---

### 4. Update Station

```bash
PUT /api/stations/{station_id}
```

**Request Body** (all fields optional):
```json
{
  "name": "Updated Name",
  "status": "maintenance",
  "phone": "+1-510-555-0999",
  "max_concurrent_bookings": 20
}
```

**Response**: `200 OK`
```json
{
  "id": "uuid",
  "code": "STATION-CA-BAY-001",
  "name": "Updated Name",
  ...
}
```

---

### 5. Delete Station (with Safety Checks)

```bash
DELETE /api/stations/{station_id}?force=false
```

**Query Parameters**:
- `force` (bool): Override safety checks (super admin only, default: false)

**Scenarios**:

#### **Scenario A: Blocked (has active bookings/users)**
**Response**: `409 Conflict`
```json
{
  "detail": {
    "message": "Cannot delete station with active data",
    "blocking_issues": [
      "3 active booking(s)",
      "2 assigned user(s)"
    ],
    "active_bookings": 3,
    "assigned_users": 2,
    "total_bookings": 47,
    "hint": "Reassign users and complete/cancel bookings first, or use force=true"
  }
}
```

#### **Scenario B: Success (no active data)**
**Response**: `204 No Content`
```
(empty response)
```

#### **Scenario C: Force Delete (super admin)**
```bash
DELETE /api/stations/{station_id}?force=true
```
**Response**: `204 No Content`

---

### 6. Assign User to Station

```bash
POST /api/stations/{station_id}/users
```

**Request Body**:
```json
{
  "user_id": "uuid",
  "role": "station_admin",
  "permissions": []
}
```

**Response**: `201 Created`
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "station_id": "uuid",
  "role": "station_admin",
  "is_active": true,
  "assigned_at": "2025-10-28T10:30:00Z"
}
```

---

## 🔐 Authentication

All endpoints require authentication via Bearer token:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     https://mhapi.mysticdatanode.net/stations
```

**Permissions Required**:
- **Create**: `manage_stations` (super admin only)
- **Read**: `view_stations` (all roles)
- **Update**: `manage_stations` (super admin or station admin for own station)
- **Delete**: `manage_stations` (super admin only)

---

## 🏷️ Station Code Examples

The system auto-generates codes in this format:

```
STATION-{STATE}-{CITY}-{###}
```

**Real Examples**:
- `STATION-CA-BAY-001` - California Bay Area (1st)
- `STATION-CA-BAY-002` - California Bay Area (2nd)
- `STATION-TX-AUSTIN-001` - Texas Austin (1st)
- `STATION-FL-MIAMI-001` - Florida Miami (1st)
- `STATION-NY-MANHATTAN-001` - New York Manhattan (1st)

**City Normalization**:
- "Bay Area" → `BAY`
- "San Francisco" → `SAN`
- "Austin" → `AUSTIN`
- "New York City" → `NEW` or `NYC`

---

## ⚠️ Delete Safety Rules

### Hard Blocks (Cannot delete without force=true)
- ❌ Active bookings (status: pending, confirmed, in_progress)
- ❌ Assigned users (is_active: true)

### Warnings (Shows warning, allows deletion)
- ⚠️ Historical bookings (status: completed, cancelled)
- ⚠️ Inactive users (is_active: false)

### Force Delete (Super Admin Only)
```bash
DELETE /api/stations/{id}?force=true
```
- Bypasses all safety checks
- Creates detailed audit log entry
- Irreversible - use with caution!

---

## 🧪 Testing Scenarios

### Test 1: Create and List
```bash
# Create a station
curl -X POST http://localhost:8000/api/stations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Station",
    "display_name": "MyHibachi - Test",
    "city": "TestCity",
    "state": "CA",
    "timezone": "America/Los_Angeles"
  }'

# List all stations
curl http://localhost:8000/api/stations \
  -H "Authorization: Bearer $TOKEN"
```

### Test 2: Update Station
```bash
curl -X PUT http://localhost:8000/api/stations/{id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "maintenance"}'
```

### Test 3: Delete (Safety Check)
```bash
# Will fail if bookings/users exist
curl -X DELETE http://localhost:8000/api/stations/{id} \
  -H "Authorization: Bearer $TOKEN"

# Force delete
curl -X DELETE "http://localhost:8000/api/stations/{id}?force=true" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📊 Station Statuses

| Status | Description | Use Case |
|--------|-------------|----------|
| `active` | Fully operational | Normal operations |
| `inactive` | Temporarily closed | Seasonal closure |
| `suspended` | Admin suspended | Compliance issues |
| `maintenance` | Under maintenance | System upgrades |

---

## 🔄 Common Workflows

### Workflow 1: Opening a New Location

```bash
# 1. Create station (auto-generates code)
POST /api/stations
{
  "name": "Florida Miami",
  "city": "Miami",
  "state": "FL",
  ...
}

# Response: STATION-FL-MIAMI-001

# 2. Assign station manager
POST /api/stations/{id}/users
{
  "user_id": "manager-uuid",
  "role": "station_admin"
}

# 3. Configure business hours
PUT /api/stations/{id}
{
  "business_hours": {...}
}

# 4. Set status to active
PUT /api/stations/{id}
{
  "status": "active"
}
```

### Workflow 2: Closing a Station

```bash
# 1. Set status to inactive
PUT /api/stations/{id}
{
  "status": "inactive"
}

# 2. Reassign users to other stations
POST /api/stations/{new-station-id}/users
{
  "user_id": "uuid",
  "role": "station_admin"
}

# 3. Complete all bookings
# (handle via booking management)

# 4. Delete station (when safe)
DELETE /api/stations/{id}
```

### Workflow 3: Temporary Maintenance

```bash
# 1. Set to maintenance mode
PUT /api/stations/{id}
{
  "status": "maintenance"
}

# 2. After maintenance complete
PUT /api/stations/{id}
{
  "status": "active"
}
```

---

## 🐛 Troubleshooting

### Error: "Only super administrators can create stations"
- **Cause**: Current user lacks super_admin role
- **Solution**: Login as super admin or request super admin to create

### Error: "Cannot delete station with active data"
- **Cause**: Station has active bookings or assigned users
- **Solution**: 
  1. Complete/cancel active bookings
  2. Reassign users to other stations
  3. Then delete, or use `force=true` (super admin)

### Error: "Station not found"
- **Cause**: Invalid station ID or station was deleted
- **Solution**: Verify station ID, check if station exists via GET /api/stations

### Error: "Access denied to this station"
- **Cause**: User trying to access station they're not assigned to
- **Solution**: 
  - Super admin: No restrictions
  - Station admin: Can only access assigned station
  - Request super admin to grant access

---

## 📝 Notes

- Station codes are **immutable** once created (cannot be changed)
- Station codes are **unique** across the entire platform
- **Super admin** role required for most station management
- **Audit logs** track all station changes for compliance
- **Soft delete** not supported - deletions are permanent (with audit trail)

---

## 🔗 Related Documentation

- [Station Management Implementation Complete](./STATION_MANAGEMENT_IMPLEMENTATION_COMPLETE.md)
- [Google OAuth Integration Guide](./GOOGLE_OAUTH_INTEGRATION_GUIDE.md) (coming soon)
- [API Documentation](./API_DOCUMENTATION.md)
- [RBAC System Overview](./4_TIER_RBAC_IMPLEMENTATION_PLAN.md)

---

**Questions?** Check the full implementation guide or contact the development team.
