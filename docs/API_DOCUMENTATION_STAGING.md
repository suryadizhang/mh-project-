# My Hibachi Staging API Documentation

**Last Updated:** February 4, 2026
**API Base URL:** `https://staging-api.mysticdatanode.net`
**Environment:** Staging

---

## 📋 Table of Contents

1. [Authentication](#authentication)
2. [Admin Users Management](#admin-users-management)
3. [Stations Management](#stations-management)
4. [Public Pricing](#public-pricing)
5. [Health Checks](#health-checks)
6. [Common Response Formats](#common-response-formats)
7. [Error Codes](#error-codes)
8. [Known Issues](#known-issues)

---

## 🔐 Authentication

### Login

**Endpoint:** `POST /api/v1/auth/login`
**Auth Required:** No
**Description:** Authenticate user and receive JWT tokens

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "YourPassword123!"
}
```

**Success Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Token Payload:**

```json
{
  "sub": "8528a17e-47a4-4a02-a9c9-0e8e9e552d30",
  "email": "user@example.com",
  "role": "SUPER_ADMIN",
  "exp": 1770241281,
  "iat": 1770239481,
  "jti": "6c46b8e9-9316-4734-a590-4165fb13c096",
  "type": "access",
  "aud": "myhibachi-api",
  "iss": "myhibachi-crm"
}
```

**Error Responses:**

- `401 Unauthorized` - Invalid credentials
- `422 Unprocessable Entity` - Validation error

---

### Get Current User

**Endpoint:** `GET /api/v1/auth/me`
**Auth Required:** Yes (Bearer token)
**Description:** Get currently authenticated user information

**Success Response (200 OK):**

```json
{
  "id": "8528a17e-47a4-4a02-a9c9-0e8e9e552d30",
  "email": "user@example.com",
  "role": "SUPER_ADMIN",
  "full_name": null,
  "is_active": true
}
```

---

### Logout

**Endpoint:** `POST /api/v1/auth/logout`
**Auth Required:** Yes (Bearer token)
**Description:** Invalidate current session

**Success Response (200 OK):**

```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

## 👥 Admin Users Management

### List All Users

**Endpoint:** `GET /api/v1/admin/users`
**Auth Required:** Yes (SUPER_ADMIN or ADMIN role)
**Description:** Get paginated list of all users

**Query Parameters:**

- `page` (integer, default: 1) - Page number
- `size` (integer, default: 20) - Items per page
- `role` (string, optional) - Filter by role
- `is_active` (boolean, optional) - Filter by active status

**Success Response (200 OK):**

```json
{
  "items": [
    {
      "id": "8528a17e-47a4-4a02-a9c9-0e8e9e552d30",
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "full_name": "John Doe",
      "phone": "+1-555-0100",
      "role": "SUPER_ADMIN",
      "status": "active",
      "is_verified": true,
      "is_super_admin": true,
      "station_id": null,
      "station_name": null,
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-30T14:20:00Z",
      "last_login_at": "2026-02-04T08:15:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

---

### Create New User

**Endpoint:** `POST /api/v1/admin/users`
**Auth Required:** Yes (SUPER_ADMIN or ADMIN role)
**Description:** Create a new admin user

**Request Body:**

```json
{
  "email": "newuser@myhibachi.com",
  "password": "SecurePassword123!",
  "first_name": "Jane",
  "last_name": "Smith",
  "role": "ADMIN",
  "phone": "+1-555-0200",
  "station_id": "22222222-2222-2222-2222-222222222222",
  "is_active": true
}
```

**Field Requirements:**

- `email` (required, string) - Valid email address
- `password` (required, string) - Minimum 8 characters
- `first_name` (required, string) - 1-100 characters
- `last_name` (required, string) - 1-100 characters
- `role` (required, string) - One of: `CHEF`, `STATION_MANAGER`,
  `CUSTOMER_SUPPORT`, `ADMIN`
- `phone` (optional, string) - Max 20 characters
- `station_id` (optional, UUID) - Required for CHEF and
  STATION_MANAGER roles
- `is_active` (optional, boolean) - Default: true

**Role Restrictions:**

- Only SUPER_ADMIN can create ADMIN users
- CHEF and STATION_MANAGER roles require `station_id`

**Success Response (201 Created):**

```json
{
  "id": "new-user-uuid",
  "email": "newuser@myhibachi.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "full_name": "Jane Smith",
  "phone": "+1-555-0200",
  "role": "ADMIN",
  "status": "active",
  "is_verified": false,
  "is_super_admin": false,
  "station_id": "22222222-2222-2222-2222-222222222222",
  "station_name": "Station Name",
  "created_at": "2026-02-04T10:00:00Z",
  "updated_at": "2026-02-04T10:00:00Z",
  "last_login_at": null
}
```

**Error Responses:**

- `400 Bad Request` - Invalid role or missing required fields
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Station not found
- `409 Conflict` - Email already exists
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error (⚠️ Known issue with
  audit logging)

---

### Get User by ID

**Endpoint:** `GET /api/v1/admin/users/{user_id}`
**Auth Required:** Yes (SUPER_ADMIN or ADMIN role)
**Description:** Get detailed information about a specific user

**Path Parameters:**

- `user_id` (UUID, required) - User identifier

**Success Response (200 OK):**

```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "phone": "+1-555-0100",
  "role": "ADMIN",
  "status": "active",
  "is_verified": true,
  "is_super_admin": false,
  "station_id": "station-uuid",
  "station_name": "Station Name",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2026-02-04T10:00:00Z",
  "last_login_at": "2026-02-04T08:15:00Z"
}
```

---

### Update User

**Endpoint:** `PUT /api/v1/admin/users/{user_id}`
**Auth Required:** Yes (SUPER_ADMIN or ADMIN role)
**Description:** Update user information

**Request Body (all fields optional):**

```json
{
  "first_name": "UpdatedFirst",
  "last_name": "UpdatedLast",
  "phone": "+1-555-0300",
  "role": "CUSTOMER_SUPPORT",
  "station_id": "new-station-uuid",
  "is_active": false
}
```

**Success Response (200 OK):**

```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "first_name": "UpdatedFirst",
  "last_name": "UpdatedLast",
  "full_name": "UpdatedFirst UpdatedLast",
  "phone": "+1-555-0300",
  "role": "CUSTOMER_SUPPORT",
  "status": "active",
  "is_verified": true,
  "is_super_admin": false,
  "station_id": "new-station-uuid",
  "station_name": "New Station Name",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2026-02-04T10:15:00Z",
  "last_login_at": "2026-02-04T08:15:00Z"
}
```

---

### Delete User (Soft Delete)

**Endpoint:** `DELETE /api/v1/admin/users/{user_id}`
**Auth Required:** Yes (SUPER_ADMIN only)
**Description:** Soft delete a user (sets status to inactive)

**Success Response (204 No Content)**

---

## 🏢 Stations Management

### List All Stations

**Endpoint:** `GET /api/v1/stations`
**Auth Required:** Yes (⚠️ Currently requires session-based auth - see
Known Issues)
**Description:** Get list of all active stations

**Query Parameters:**

- `include_inactive` (boolean, default: false) - Include inactive
  stations (SUPER_ADMIN only)

**Success Response (200 OK):**

```json
[
  {
    "id": "station-uuid",
    "name": "Fremont Station (Main)",
    "address": "47481 Towhee St, Fremont, CA 94539",
    "city": "Fremont",
    "state": "CA",
    "postal_code": "94539",
    "latitude": 37.5485,
    "longitude": -121.9886,
    "timezone": "America/Los_Angeles",
    "email": "bay-area@myhibachi.com",
    "status": "active",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-15T10:00:00Z"
  }
]
```

**Current Issues:**

- ⚠️ Returns `500 Internal Server Error` - Station middleware expects
  `session_id` in JWT token
- 🔧 Needs refactoring to use standard JWT auth like admin users
  endpoints

---

## 💰 Public Pricing

### Get Current Pricing

**Endpoint:** `GET /api/v1/pricing/current`
**Auth Required:** No (public endpoint)
**Description:** Get comprehensive pricing information including base
pricing, travel fees, menu items, and add-ons

**Success Response (200 OK):**

```json
{
  "base_pricing": {
    "adult_price": 55.0,
    "child_price": 30.0,
    "child_free_under_age": 5,
    "party_minimum": 550.0,
    "deposit_amount": 100.0,
    "deposit_refundable_days": 4
  },
  "travel_fee_config": {
    "free_miles": 30,
    "price_per_mile": 2.0
  },
  "travel_fee_stations": [
    {
      "id": 1,
      "station_name": "Fremont Station (Main)",
      "station_address": "47481 Towhee St, Fremont, CA 94539",
      "city": "Fremont",
      "state": "CA",
      "postal_code": "94539",
      "latitude": null,
      "longitude": null,
      "free_miles": 30.0,
      "price_per_mile": 2.0,
      "max_service_distance": null,
      "is_active": true,
      "notes": "Main station covering Bay Area and Sacramento regions",
      "display_order": 1
    }
  ],
  "menu_items": [
    {
      "id": 1,
      "name": "Chicken",
      "category": "poultry",
      "price": 0.0,
      "description": "Tender grilled chicken with teriyaki glaze",
      "is_active": true,
      "is_included": true,
      "display_order": 1
    }
  ],
  "addon_items": [
    {
      "id": 1,
      "name": "Salmon",
      "category": "protein_upgrade",
      "price": 7.0,
      "description": "Wild-caught Atlantic salmon with teriyaki glaze",
      "is_active": true,
      "display_order": 1
    }
  ],
  "config_source": "database_dynamic_variables"
}
```

**Pricing Details:**

- **Base Pricing:**
  - Adults (13+): $55/person
  - Children (6-12): $30/person
  - Children under 5: FREE
  - Party minimum: $550
  - Deposit: $100
  - Refundable deposit period: 4 days

- **Protein Upgrades (per serving):**
  - Salmon: +$7
  - Scallops: +$9
  - Filet Mignon: +$10
  - Lobster Tail: +$20

- **Add-ons (per serving):**
  - Yakisoba Noodles: $5
  - Extra Fried Rice: $5
  - Extra Vegetables: $5
  - Edamame: $5
  - Gyoza: $10
  - Extra Protein: $10

- **Travel Fee:**
  - First 30 miles: FREE
  - After 30 miles: $2/mile

---

### Calculate Quote

**Endpoint:** `POST /api/v1/pricing/calculate`
**Auth Required:** No (public endpoint)
**Description:** Calculate a party quote with all fees and upgrades

**Request Body:**

```json
{
  "adults": 10,
  "children": 2,
  "salmon": 2,
  "lobster_tail": 1,
  "yakisoba_noodles": 5,
  "venue_address": "123 Main St, San Jose, CA 95123"
}
```

**Request Fields:**

- `adults` (required, integer) - Number of adults (13+), range: 0-100
- `children` (optional, integer) - Number of children (6-12), range:
  0-50

**Upgrade Proteins:**

- `salmon` (optional, integer) - Number of salmon upgrades
- `scallops` (optional, integer) - Number of scallop upgrades
- `filet_mignon` (optional, integer) - Number of filet mignon upgrades
- `lobster_tail` (optional, integer) - Number of lobster tail upgrades
- `extra_proteins` (optional, integer) - Number of extra protein
  additions

**Add-ons:**

- `yakisoba_noodles` (optional, integer) - Yakisoba noodle portions
- `extra_fried_rice` (optional, integer) - Extra fried rice portions
- `extra_vegetables` (optional, integer) - Extra vegetable portions
- `edamame` (optional, integer) - Edamame portions
- `gyoza` (optional, integer) - Gyoza portions

**Location (for travel fee):**

- `venue_address` (optional, string) - Full venue address
- `zip_code` (optional, string) - ZIP code for fallback
- `venue_lat` (optional, float) - Pre-geocoded latitude
- `venue_lng` (optional, float) - Pre-geocoded longitude

**Success Response (200 OK):**

```json
{
  "subtotal": 660.0,
  "travel_fee": 10.0,
  "total": 670.0,
  "deposit": 100.0,
  "balance_due": 570.0,
  "breakdown": {
    "adults": {
      "count": 10,
      "price_per_person": 55.0,
      "subtotal": 550.0
    },
    "children": {
      "count": 2,
      "price_per_person": 30.0,
      "subtotal": 60.0
    },
    "upgrades": {
      "salmon": {
        "count": 2,
        "price_per_item": 7.0,
        "subtotal": 14.0
      },
      "lobster_tail": {
        "count": 1,
        "price_per_item": 20.0,
        "subtotal": 20.0
      }
    },
    "addons": {
      "yakisoba_noodles": {
        "count": 5,
        "price_per_item": 5.0,
        "subtotal": 25.0
      }
    },
    "travel": {
      "distance_miles": 35,
      "free_miles": 30,
      "billable_miles": 5,
      "price_per_mile": 2.0,
      "subtotal": 10.0
    }
  },
  "party_minimum_met": true
}
```

**Error Responses:**

- `422 Unprocessable Entity` - Invalid request data

**Current Issues:**

- ⚠️ Returns `422 Unprocessable Entity` with valid request (needs
  investigation)

---

## 🏥 Health Checks

### API Health

**Endpoint:** `GET /health`
**Auth Required:** No
**Description:** Basic health check

**Success Response (200 OK):**

```json
{
  "status": "healthy",
  "timestamp": "2026-02-04T10:00:00Z"
}
```

---

### Detailed Health Check

**Endpoint:** `GET /api/v1/health`
**Auth Required:** No
**Description:** Detailed service status including database
connectivity

**Success Response (200 OK):**

```json
{
  "status": "healthy",
  "timestamp": "2026-02-04T10:00:00Z",
  "services": {
    "database": "connected",
    "redis": "connected"
  },
  "version": "1.0.0"
}
```

---

## 📊 Common Response Formats

### Success Response Structure

```json
{
  "success": true,
  "data": {
    /* ... */
  }
}
```

### Error Response Structure

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {},
    "correlation_id": "uuid-for-tracking"
  }
}
```

---

## ❌ Error Codes

| HTTP Status                 | Meaning                  | Common Causes                                |
| --------------------------- | ------------------------ | -------------------------------------------- |
| `400 Bad Request`           | Invalid request format   | Missing required fields, invalid data format |
| `401 Unauthorized`          | Authentication required  | Missing or invalid token                     |
| `403 Forbidden`             | Insufficient permissions | User role doesn't have access                |
| `404 Not Found`             | Resource doesn't exist   | Invalid user ID, station ID, etc.            |
| `409 Conflict`              | Resource conflict        | Duplicate email, existing record             |
| `422 Unprocessable Entity`  | Validation error         | Field validation failed                      |
| `500 Internal Server Error` | Server error             | Application error (see Known Issues)         |

---

## ⚠️ Known Issues

### 1. Station Endpoints Return 500 Error

**Affected Endpoints:**

- `GET /api/v1/stations`
- `GET /api/v1/stations/{station_id}`

**Issue:** Station middleware expects `session_id` in JWT token, but
standard login doesn't provide it.

**Error Log:**

```
KeyError: 'session_id'
ERROR:core.auth.station_middleware:Authentication error: 'session_id'
```

**Workaround:** None currently available.

**Fix Required:** Update station router to use standard JWT auth
dependencies like admin users endpoints:

- Replace `require_station_permission` with
  `get_current_user_from_token`
- Add appropriate permission checks using `require_super_admin`,
  `require_admin_or_super_admin`, etc.

**Priority:** HIGH - Blocking Postman tests and E2E tests

---

### 2. Create User Returns 500 Error

**Affected Endpoints:**

- `POST /api/v1/admin/users`

**Issue:** Audit logging middleware error - `user_id` is NULL when
trying to log user creation.

**Root Cause:** Audit middleware `audit_log_action` is currently
commented out with TODO markers.

**Workaround:** None - user creation currently fails.

**Fix Required:** Re-implement audit logging with proper user context.

**Priority:** HIGH - Blocking user management functionality

---

### 3. Pricing Calculate Returns 422

**Affected Endpoints:**

- `POST /api/v1/pricing/calculate`

**Issue:** Returns validation error with valid request payload.

**Requires Investigation:** Need to check request payload validation
logic.

**Priority:** MEDIUM - Public endpoint but has workaround (manual
calculation)

---

## 📝 Testing

### E2E Test Results (Staging)

**Last Run:** February 4, 2026
**Results:** 63 passing, 15 skipped, 0 failures

**Passing Tests:**

- ✅ Authentication (login, logout, get current user)
- ✅ Admin users list endpoint
- ✅ Public pricing endpoint
- ✅ Health checks
- ✅ Agreements API (templates, slot holds, signing)
- ✅ Bookings API (auth protection)
- ✅ Payments API (Stripe endpoints)
- ✅ Scheduling API (availability, travel time, chef assignment)
- ✅ Stripe webhooks (signature verification, event handling)

**Skipped Tests:**

- Admin users CRUD (create, update, delete) - 500 errors
- Stations endpoints - 500 errors
- Some admin analytics endpoints - not yet implemented

### Postman Test Results

**Last Run:** February 4, 2026
**Results:** 14 requests, 27 assertions, 14 passed (52%), 13 failed
(48%)

**Passing:**

- ✅ Authentication (login, current user, logout)
- ✅ Admin users list with pagination
- ✅ Health checks
- ✅ Public pricing endpoint

**Failing:**

- ❌ Admin users create (500 error)
- ❌ Admin users get/update/delete (depends on create)
- ❌ Stations endpoints (500 error - auth issue)
- ❌ Pricing calculate (422 error - validation issue)

---

## 🔧 Development Notes

### Authentication Flow

1. User sends credentials to `/api/v1/auth/login`
2. Backend validates credentials
3. Backend generates JWT access token (30 minutes) and refresh token
4. Client stores tokens
5. Client includes `Authorization: Bearer {access_token}` header in
   subsequent requests
6. Backend validates token on protected endpoints
7. When access token expires, client uses refresh token to get new
   access token

### JWT Token Structure

**Standard Token (Admin Users, Auth endpoints):**

- Contains: `sub` (user_id), `email`, `role`, `exp`, `iat`, `jti`,
  `type`, `aud`, `iss`
- Does NOT contain: `session_id` (not needed for standard auth)

**Session Token (Station-aware endpoints - legacy):**

- Contains: All standard fields PLUS `session_id`
- Used by: Station endpoints (currently broken)
- Issue: Standard login doesn't create session tokens

### Role-Based Access Control (RBAC)

**Roles (in order of privilege):**

1. `SUPER_ADMIN` - Full system access
2. `ADMIN` - Station-scoped admin access
3. `CUSTOMER_SUPPORT` - Customer-facing operations
4. `STATION_MANAGER` - Station-specific management
5. `CHEF` - Self-service, assigned events only

**Permission Patterns:**

- Super Admin can do everything
- Admins can manage users/stations they're assigned to
- Customer Support can view/edit customer-facing data
- Station Managers can manage their station's operations
- Chefs can view/update their own schedule and assignments

---

## 📚 Additional Resources

- **Source Code:** `apps/backend/src/routers/v1/`
- **Database Models:** `apps/backend/src/db/models/`
- **E2E Tests:** `e2e/api/`
- **Postman Collection:**
  `MyHibachi_Batch1_Tests.postman_collection.json`
- **Environment File:** `Staging.postman_environment.json`

---

**Document Version:** 1.0
**Generated:** February 4, 2026
**Status:** Living document - updated as API evolves
