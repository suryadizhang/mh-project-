# My Hibachi – API Contracts

**Last Updated:** December 16, 2025 **Purpose:** Define API
request/response specifications **Base URL:**
`https://mhapi.mysticdatanode.net` (prod) / `http://localhost:8000`
(dev)

---

## 🔐 Authentication

### JWT Authentication (User Sessions)

```http
Authorization: Bearer <jwt_token>
```

### API Key Authentication (Service-to-Service)

```http
X-API-Key: <api_key>
```

---

## 📚 API Endpoints

### Public Endpoints (No Auth Required)

#### Calculate Quote

```http
POST /api/v1/public/quote/calculate
Content-Type: application/json
```

**Request:**

```json
{
  "adults": 15,
  "kids": 5,
  "zip_code": "94539",
  "upgrades": {
    "filet_mignon": true,
    "lobster": false
  }
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "base_total_cents": 97500,
    "upgrades_cents": 22500,
    "travel_fee_cents": 0,
    "subtotal_cents": 120000,
    "gratuity_cents": 24000,
    "total_cents": 144000,
    "deposit_required_cents": 36000,
    "breakdown": {
      "adults": {
        "count": 15,
        "rate_cents": 5500,
        "total_cents": 82500
      },
      "kids": {
        "count": 5,
        "rate_cents": 3000,
        "total_cents": 15000
      },
      "filet_upgrade": {
        "count": 20,
        "rate_cents": 1500,
        "total_cents": 30000
      },
      "travel": {
        "miles": 12,
        "free_miles": 30,
        "billable_miles": 0,
        "rate_cents": 200
      }
    }
  }
}
```

---

#### Check Availability

```http
GET /api/v1/bookings/availability?date=2025-01-15
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "date": "2025-01-15",
    "available_slots": [
      { "time": "11:00", "available": true },
      { "time": "12:00", "available": true },
      { "time": "13:00", "available": false },
      { "time": "17:00", "available": true },
      { "time": "18:00", "available": true },
      { "time": "19:00", "available": false }
    ]
  }
}
```

---

#### Create Booking

```http
POST /api/v1/public/bookings
Content-Type: application/json
```

**Request:**

```json
{
  "customer": {
    "first_name": "John",
    "last_name": "Smith",
    "email": "john@example.com",
    "phone": "+14155551234",
    "sms_consent": true
  },
  "event": {
    "date": "2025-01-15",
    "slot": "18:00",
    "party_adults": 15,
    "party_kids": 5,
    "address": {
      "street": "123 Main St",
      "city": "Fremont",
      "state": "CA",
      "zip": "94539"
    }
  },
  "menu": {
    "upgrades": ["filet_mignon"],
    "special_requests": "Nut allergy for 2 guests"
  },
  "source": "web_booking"
}
```

**Response (201 Created):**

```json
{
  "success": true,
  "data": {
    "booking_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending",
    "deposit_due_cents": 36000,
    "total_due_cents": 144000,
    "customer_deposit_deadline": "2025-01-12T23:59:59Z",
    "payment_url": "https://checkout.stripe.com/pay/cs_xxx"
  }
}
```

---

### Lead Endpoints (Public/Protected)

#### Submit Quote Lead

```http
POST /api/leads
Content-Type: application/json
```

**Request:**

```json
{
  "source": "WEB_QUOTE",
  "contacts": [
    {
      "channel": "SMS",
      "handle_or_address": "+14155551234",
      "verified": false
    },
    {
      "channel": "EMAIL",
      "handle_or_address": "john@example.com",
      "verified": false
    }
  ],
  "context": {
    "party_size_adults": 15,
    "party_size_kids": 5,
    "event_date_pref": "2025-01-15",
    "zip_code": "94539",
    "estimated_budget_dollars": 1500
  },
  "utm_source": "google",
  "utm_medium": "cpc",
  "utm_campaign": "bay_area_catering"
}
```

**Response (201 Created):**

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "source": "WEB_QUOTE",
    "status": "new",
    "quality": null,
    "score": 0,
    "created_at": "2025-01-10T15:30:00Z"
  }
}
```

---

#### Add Lead Event (Funnel Tracking)

```http
POST /api/v1/leads/{lead_id}/events
Content-Type: application/json
Authorization: Bearer <token>
```

**Request:**

```json
{
  "event_type": "funnel_checked_availability",
  "payload": {
    "date_selected": "2025-01-15",
    "time_slot": "18:00",
    "source_page": "/quote"
  }
}
```

**Response (201 Created):**

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "lead_id": "550e8400-e29b-41d4-a716-446655440001",
    "event_type": "funnel_checked_availability",
    "payload": {
      "date_selected": "2025-01-15",
      "time_slot": "18:00"
    },
    "occurred_at": "2025-01-10T15:35:00Z"
  }
}
```

---

### Booking Management (Protected)

#### Get Booking Details

```http
GET /api/v1/bookings/{booking_id}
Authorization: Bearer <token>
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "deposit_paid",
    "date": "2025-01-15",
    "slot": "18:00",
    "party_adults": 15,
    "party_kids": 5,
    "deposit_due_cents": 36000,
    "total_due_cents": 144000,
    "customer": {
      "id": "...",
      "name": "John Smith",
      "email": "john@example.com",
      "phone": "+14155551234"
    },
    "chef": {
      "id": "...",
      "name": "Chef Mike"
    },
    "zone": "fremont",
    "created_at": "2025-01-10T15:30:00Z"
  }
}
```

---

#### Update Booking Status

```http
PATCH /api/v1/bookings/{booking_id}/status
Authorization: Bearer <token>
Content-Type: application/json
```

**Request:**

```json
{
  "status": "confirmed",
  "notes": "Customer confirmed via phone"
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "confirmed",
    "updated_at": "2025-01-10T16:00:00Z"
  }
}
```

---

### Health & Monitoring

#### Health Check

```http
GET /api/v1/health
```

**Response (200 OK):**

```json
{
  "status": "healthy",
  "timestamp": "2025-01-10T15:30:00Z",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "redis": "connected",
    "stripe": "connected"
  }
}
```

---

## ❌ Error Responses

### Standard Error Format

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "details": [
      { "field": "party_adults", "message": "Must be at least 10" }
    ]
  }
}
```

### Error Codes

| Code               | HTTP Status | Meaning                                  |
| ------------------ | ----------- | ---------------------------------------- |
| `VALIDATION_ERROR` | 400         | Invalid request data                     |
| `UNAUTHORIZED`     | 401         | Missing or invalid auth                  |
| `FORBIDDEN`        | 403         | Insufficient permissions                 |
| `NOT_FOUND`        | 404         | Resource doesn't exist                   |
| `CONFLICT`         | 409         | Resource conflict (e.g., double booking) |
| `RATE_LIMITED`     | 429         | Too many requests                        |
| `INTERNAL_ERROR`   | 500         | Server error                             |

---

## 📊 Rate Limits

| Endpoint Category            | Limit | Window   |
| ---------------------------- | ----- | -------- |
| Public (quote, availability) | 100   | 1 minute |
| Authenticated                | 1000  | 1 minute |
| Admin                        | 5000  | 1 minute |

---

## 🔗 Related Documents

- [Data Flow](./DATA_FLOW.md) - How requests flow through system
- [ERD](./ERD.md) - Database structure
- [Glossary](../00-ONBOARDING/GLOSSARY.md) - Term definitions
