# MyHibachi API Documentation

**Last Updated:** January 30, 2025 **API Version:** 1.0.0 **Base URL
(Production):** `https://mhapi.mysticdatanode.net` **Base URL
(Staging):** `https://staging-api.mysticdatanode.net` (or
`http://127.0.0.1:8002` via SSH tunnel) **Base URL (Development):**
`http://localhost:8000`

> **Note:** Port 8000 is used for production backend, port 8002 for
> staging. The old `api.myhibachi.com:8003` URL is deprecated.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Rate Limiting](#rate-limiting)
4. [Error Handling](#error-handling)
5. [Public Endpoints](#public-endpoints)
6. [Authentication Endpoints](#authentication-endpoints)
7. [Booking Endpoints](#booking-endpoints)
8. [Customer Endpoints](#customer-endpoints)
9. [Lead Endpoints](#lead-endpoints)
10. [Inbox/Messaging Endpoints](#inboxmessaging-endpoints)
11. [AI Endpoints](#ai-endpoints)
12. [Admin Endpoints](#admin-endpoints)
13. [WebSocket Endpoints](#websocket-endpoints)
14. [Webhook Endpoints](#webhook-endpoints)
15. [Response Schemas](#response-schemas)
16. [Code Examples](#code-examples)

---

## Overview

### API Architecture

MyHibachi uses a unified REST API architecture combining operational
(CRM) and AI capabilities:

```
┌─────────────────────────────────────────────┐
│         MyHibachi Unified API               │
│         (FastAPI Backend)                   │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────┐    ┌─────────────────┐  │
│  │ Operational  │    │   AI Services   │  │
│  │  Endpoints   │    │   (OpenAI GPT)  │  │
│  │              │    │                 │  │
│  │ • Bookings   │    │  • Chat         │  │
│  │ • Customers  │    │  • Voice        │  │
│  │ • Leads      │    │  • Embeddings   │  │
│  │ • Auth       │    │                 │  │
│  └──────────────┘    └─────────────────┘  │
│                                             │
└─────────────────────────────────────────────┘
```

### Key Features

- **RESTful Design:** Standard HTTP methods (GET, POST, PUT, DELETE,
  PATCH)
- **JSON Responses:** All responses in JSON format
- **JWT Authentication:** Secure token-based authentication
- **Role-Based Access Control (RBAC):** Admin, Staff, Customer roles
- **Rate Limiting:** Tier-based rate limiting (Public, Admin, AI)
- **Comprehensive Error Handling:** Detailed error messages with
  status codes
- **Real-time Updates:** WebSocket support for chat and notifications
- **Webhook Support:** External integrations (Stripe, RingCentral)
- **OpenAPI Documentation:** Interactive API docs at `/docs`

### API Versions

| Version | Status     | Endpoint Prefix | Notes                   |
| ------- | ---------- | --------------- | ----------------------- |
| **v1**  | ✅ Current | `/api/v1`       | Production stable       |
| v2      | 🚧 Planned | `/api/v2`       | GraphQL support planned |

### Supported Content Types

**Request:**

- `application/json` (default)
- `multipart/form-data` (file uploads)

**Response:**

- `application/json` (default)
- `text/event-stream` (SSE for AI streaming)

---

## Authentication

### Authentication Methods

MyHibachi API supports two authentication methods:

1. **JWT Bearer Token** (Primary)
2. **API Key** (External integrations)

### JWT Bearer Authentication

**Token Format:**

```
Authorization: Bearer <jwt_token>
```

**Token Structure:**

```json
{
  "sub": "user@example.com",
  "user_id": 123,
  "role": "admin",
  "exp": 1730000000,
  "iat": 1729999000
}
```

**Token Expiration:**

- **Access Token:** 30 minutes
- **Refresh Token:** 7 days

### Obtaining Tokens

**Login Endpoint:**

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 123,
    "email": "user@example.com",
    "role": "admin",
    "full_name": "John Doe"
  }
}
```

### Refreshing Tokens

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** Same as login response with new tokens

### API Key Authentication

**For External Integrations Only**

```http
GET /api/v1/bookings
X-API-Key: your_api_key_here
```

**API Key Format:** 32+ character alphanumeric string

**Obtaining API Key:**

- Contact admin or generate via admin panel
- API keys are scoped to specific permissions

### User Roles & Permissions

| Role            | Permissions                       | Endpoints                                      |
| --------------- | --------------------------------- | ---------------------------------------------- |
| **Public**      | Read public data, create leads    | `/api/v1/public/*`                             |
| **Customer**    | View own bookings, update profile | `/api/v1/bookings`, `/api/v1/customers/{self}` |
| **Staff**       | Manage bookings, customers, leads | Most `/api/v1/*` endpoints                     |
| **Admin**       | Full access, system configuration | All endpoints                                  |
| **Super Admin** | Multi-tenant management           | `/api/v1/admin/*`                              |

---

## Rate Limiting

### Rate Limit Tiers

| Tier              | Requests/Minute | Burst Limit | Endpoints                        |
| ----------------- | --------------- | ----------- | -------------------------------- |
| **Public**        | 20              | 40          | `/api/v1/public/*`               |
| **Authenticated** | 60              | 100         | Standard authenticated endpoints |
| **Admin**         | 120             | 200         | Admin endpoints                  |
| **AI**            | 10              | 15          | `/api/v1/ai/*` (OpenAI costs)    |

### Rate Limit Headers

All responses include rate limit information:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1730000000
```

### Rate Limit Exceeded Response

**Status:** `429 Too Many Requests`

```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Try again in 30 seconds.",
  "details": {
    "limit": 60,
    "reset_at": "2025-10-25T10:30:00Z",
    "retry_after": 30
  }
}
```

### Checking Rate Limit Status

```http
GET /api/v1/monitoring/rate-limit/status
Authorization: Bearer <token>
```

**Response:**

```json
{
  "tier": "authenticated",
  "limit": 60,
  "remaining": 45,
  "reset_at": "2025-10-25T10:30:00Z",
  "requests_made": 15,
  "window_duration": 60
}
```

---

## Error Handling

### Error Response Format

All errors follow a consistent structure:

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {
    "field": "additional context",
    "validation_errors": ["list of errors"]
  },
  "request_id": "uuid-here",
  "timestamp": "2025-10-25T10:30:00Z"
}
```

### HTTP Status Codes

| Code    | Status                | Meaning                              |
| ------- | --------------------- | ------------------------------------ |
| **200** | OK                    | Request successful                   |
| **201** | Created               | Resource created successfully        |
| **204** | No Content            | Request successful, no response body |
| **400** | Bad Request           | Invalid request data                 |
| **401** | Unauthorized          | Missing or invalid authentication    |
| **403** | Forbidden             | Insufficient permissions             |
| **404** | Not Found             | Resource not found                   |
| **409** | Conflict              | Resource conflict (duplicate)        |
| **422** | Unprocessable Entity  | Validation error                     |
| **429** | Too Many Requests     | Rate limit exceeded                  |
| **500** | Internal Server Error | Server error                         |
| **503** | Service Unavailable   | Temporary service issue              |

### Common Error Codes

| Error Code            | HTTP Status | Description              |
| --------------------- | ----------- | ------------------------ |
| `invalid_request`     | 400         | Malformed request        |
| `validation_error`    | 422         | Field validation failed  |
| `unauthorized`        | 401         | Authentication required  |
| `forbidden`           | 403         | Insufficient permissions |
| `not_found`           | 404         | Resource not found       |
| `already_exists`      | 409         | Duplicate resource       |
| `rate_limit_exceeded` | 429         | Too many requests        |
| `internal_error`      | 500         | Server error             |
| `external_api_error`  | 502         | External API failure     |

### Validation Errors

**Request:**

```http
POST /api/v1/public/leads
Content-Type: application/json

{
  "name": "",
  "phone": "invalid",
  "email": "not-an-email"
}
```

**Response:** `422 Unprocessable Entity`

```json
{
  "error": "validation_error",
  "message": "Request validation failed",
  "details": {
    "name": "Field is required and cannot be empty",
    "phone": "Invalid phone number format",
    "email": "Invalid email format"
  }
}
```

---

## Public Endpoints

### Create Lead (Quote Request)

**Endpoint:** `POST /api/v1/public/leads` **Authentication:** None
required **Rate Limit:** 20/min

**Description:** Submit a quote request or general inquiry.
Automatically subscribes user to newsletter if phone provided.

**Request:**

```json
{
  "name": "John Doe",
  "phone": "555-123-4567",
  "email": "john@example.com",
  "message": "Interested in catering for 50 guests",
  "source": "website",
  "metadata": {
    "page": "homepage",
    "referrer": "google"
  },
  "honeypot": ""
}
```

**Response:** `201 Created`

```json
{
  "success": true,
  "lead_id": 12345,
  "message": "Thank you! We'll contact you within 24 hours.",
  "newsletter_subscribed": true,
  "estimated_response_time": "24 hours"
}
```

**Validation Rules:**

- `name`: Required, 2-100 characters
- `phone`: Required, valid phone format (US/International)
- `email`: Optional, valid email format
- `message`: Optional, max 1000 characters
- `honeypot`: Must be empty (spam protection)

---

### Create Booking Request

**Endpoint:** `POST /api/v1/public/bookings` **Authentication:** None
required **Rate Limit:** 20/min

**Description:** Submit a booking request with event details.

**Request:**

```json
{
  "name": "Jane Smith",
  "phone": "555-987-6543",
  "email": "jane@example.com",
  "event_date": "2025-11-15",
  "event_time": "18:00",
  "guest_count": 25,
  "event_type": "birthday",
  "location": "Los Angeles, CA",
  "message": "Outdoor birthday party",
  "source": "booking_form",
  "honeypot": ""
}
```

**Response:** `201 Created`

```json
{
  "success": true,
  "booking_id": 67890,
  "reference_number": "BK-2025-67890",
  "status": "pending",
  "estimated_cost": 1500,
  "message": "Booking request received. We'll confirm within 48 hours.",
  "next_steps": [
    "We'll review your request",
    "You'll receive a quote via email",
    "Confirm booking with $100 deposit"
  ]
}
```

**Validation Rules:**

- `name`: Required, 2-100 characters
- `phone`: Required, valid phone format
- `email`: Optional but recommended
- `event_date`: Required, future date, not Monday (restaurant closed)
- `event_time`: Optional, format HH:MM
- `guest_count`: Required, 1-500 guests
- `event_type`: Optional, one of: birthday, wedding, corporate,
  anniversary, other
- `location`: Required, city/state or address

---

### Health Check

**Endpoint:** `GET /health` **Authentication:** None **Rate Limit:**
No limit

**Description:** Check API health status.

**Response:** `200 OK`

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 86400,
  "database": "connected",
  "redis": "connected",
  "external_services": {
    "stripe": "operational",
    "openai": "operational"
  },
  "timestamp": "2025-10-25T10:30:00Z"
}
```

---

## Authentication Endpoints

### Login

**Endpoint:** `POST /api/v1/auth/login` **Authentication:** None
**Rate Limit:** 5/min (stricter for security)

**Request:**

```json
{
  "email": "admin@myhibachi.com",
  "password": "secure_password"
}
```

**Response:** `200 OK`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "email": "admin@myhibachi.com",
    "role": "admin",
    "full_name": "Admin User",
    "permissions": [
      "bookings:read",
      "bookings:write",
      "customers:read"
    ]
  }
}
```

---

### Logout

**Endpoint:** `POST /api/v1/auth/logout` **Authentication:** Required
**Rate Limit:** 60/min

**Request:**

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** `204 No Content`

---

### Refresh Token

**Endpoint:** `POST /api/v1/auth/refresh` **Authentication:** Refresh
token required **Rate Limit:** 10/min

**Request:**

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** `200 OK`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

## Booking Endpoints

### List Bookings

**Endpoint:** `GET /api/v1/bookings` **Authentication:** Required
(Staff/Admin) **Rate Limit:** 60/min

**Query Parameters:**

```
?status=confirmed              # Filter by status
&event_date_from=2025-11-01    # Date range start
&event_date_to=2025-11-30      # Date range end
&customer_id=123               # Filter by customer
&page=1                        # Page number
&limit=20                      # Items per page (max 100)
&sort=event_date               # Sort field
&order=asc                     # Sort order (asc/desc)
```

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": 67890,
      "reference_number": "BK-2025-67890",
      "customer": {
        "id": 123,
        "name": "Jane Smith",
        "email": "jane@example.com",
        "phone": "555-987-6543"
      },
      "event_date": "2025-11-15",
      "event_time": "18:00:00",
      "guest_count": 25,
      "event_type": "birthday",
      "location": "Los Angeles, CA",
      "status": "confirmed",
      "total_amount": 1500.0,
      "deposit_amount": 750.0,
      "deposit_paid": true,
      "created_at": "2025-10-25T10:30:00Z",
      "updated_at": "2025-10-25T11:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total_items": 150,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

---

### Get Booking Details

**Endpoint:** `GET /api/v1/bookings/{id}` **Authentication:** Required
(Staff/Admin or Owner) **Rate Limit:** 60/min

**Response:** `200 OK`

```json
{
  "id": 67890,
  "reference_number": "BK-2025-67890",
  "customer": {
    "id": 123,
    "name": "Jane Smith",
    "email": "jane@example.com",
    "phone": "555-987-6543"
  },
  "event_date": "2025-11-15",
  "event_time": "18:00:00",
  "guest_count": 25,
  "event_type": "birthday",
  "location": "123 Main St, Los Angeles, CA 90001",
  "status": "confirmed",
  "menu_items": [
    {
      "id": 1,
      "name": "Hibachi Chicken",
      "quantity": 15,
      "price": 25.0
    },
    {
      "id": 2,
      "name": "Hibachi Steak",
      "quantity": 10,
      "price": 35.0
    }
  ],
  "subtotal": 725.0,
  "tax": 72.5,
  "service_fee": 145.0,
  "total_amount": 942.5,
  "deposit_amount": 471.25,
  "deposit_paid": true,
  "balance_due": 471.25,
  "payment_status": "partial",
  "notes": "Customer requested outdoor setup",
  "created_at": "2025-10-25T10:30:00Z",
  "updated_at": "2025-10-25T11:00:00Z",
  "confirmed_at": "2025-10-25T11:00:00Z"
}
```

---

### Create Booking (Admin)

**Endpoint:** `POST /api/v1/bookings` **Authentication:** Required
(Staff/Admin) **Rate Limit:** 60/min

**Request:**

```json
{
  "customer_id": 123,
  "event_date": "2025-11-15",
  "event_time": "18:00",
  "guest_count": 25,
  "event_type": "birthday",
  "location": "123 Main St, Los Angeles, CA 90001",
  "menu_items": [
    { "menu_item_id": 1, "quantity": 15 },
    { "menu_item_id": 2, "quantity": 10 }
  ],
  "notes": "Customer requested outdoor setup",
  "status": "confirmed"
}
```

**Response:** `201 Created`

```json
{
  "id": 67890,
  "reference_number": "BK-2025-67890",
  "status": "confirmed",
  "total_amount": 942.5,
  "message": "Booking created successfully"
}
```

---

### Update Booking

**Endpoint:** `PUT /api/v1/bookings/{id}` **Authentication:** Required
(Staff/Admin) **Rate Limit:** 60/min

**Request:**

```json
{
  "status": "confirmed",
  "notes": "Customer confirmed attendance"
}
```

**Response:** `200 OK`

```json
{
  "id": 67890,
  "status": "confirmed",
  "updated_at": "2025-10-25T12:00:00Z",
  "message": "Booking updated successfully"
}
```

---

### Cancel Booking

**Endpoint:** `DELETE /api/v1/bookings/{id}` **Authentication:**
Required (Staff/Admin) **Rate Limit:** 60/min

**Response:** `204 No Content`

---

## Customer Endpoints

### List Customers

**Endpoint:** `GET /api/v1/customers` **Authentication:** Required
(Staff/Admin) **Rate Limit:** 60/min

**Query Parameters:**

```
?search=john                # Search by name/email/phone
&loyalty_tier=gold          # Filter by loyalty tier
&page=1
&limit=20
```

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": 123,
      "name": "Jane Smith",
      "email": "jane@example.com",
      "phone": "555-987-6543",
      "loyalty_tier": "silver",
      "total_bookings": 5,
      "total_spent": 4500.0,
      "created_at": "2024-01-15T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total_items": 500,
    "total_pages": 25
  }
}
```

---

### Get Customer Details

**Endpoint:** `GET /api/v1/customers/{id}` **Authentication:**
Required (Staff/Admin or Owner) **Rate Limit:** 60/min

**Response:** `200 OK`

```json
{
  "id": 123,
  "name": "Jane Smith",
  "email": "jane@example.com",
  "phone": "555-987-6543",
  "address": {
    "street": "123 Main St",
    "city": "Los Angeles",
    "state": "CA",
    "zip": "90001"
  },
  "loyalty_tier": "silver",
  "loyalty_points": 450,
  "total_bookings": 5,
  "total_spent": 4500.0,
  "upcoming_bookings": 2,
  "last_booking_date": "2025-09-15",
  "preferences": {
    "dietary_restrictions": ["vegetarian"],
    "preferred_contact": "email"
  },
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2025-10-20T15:30:00Z"
}
```

---

## Lead Endpoints

### List Leads

**Endpoint:** `GET /api/v1/leads` **Authentication:** Required
(Staff/Admin) **Rate Limit:** 60/min

**Query Parameters:**

```
?status=new                 # Filter by status
&source=website             # Filter by source
&date_from=2025-10-01       # Date range
&date_to=2025-10-31
&assigned_to=staff_id       # Filter by assigned staff
```

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": 12345,
      "name": "John Doe",
      "phone": "555-123-4567",
      "email": "john@example.com",
      "source": "website",
      "status": "new",
      "message": "Interested in catering",
      "assigned_to": null,
      "created_at": "2025-10-25T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total_items": 75
  }
}
```

---

### Convert Lead to Customer

**Endpoint:** `POST /api/v1/leads/{id}/convert` **Authentication:**
Required (Staff/Admin) **Rate Limit:** 60/min

**Request:**

```json
{
  "create_booking": true,
  "booking_data": {
    "event_date": "2025-11-15",
    "guest_count": 25,
    "event_type": "corporate"
  }
}
```

**Response:** `201 Created`

```json
{
  "customer_id": 234,
  "booking_id": 67891,
  "message": "Lead converted to customer successfully"
}
```

---

## AI Endpoints

### Chat with AI Assistant

**Endpoint:** `POST /api/v1/ai/chat` **Authentication:** Optional
(better experience when authenticated) **Rate Limit:** 10/min (strict
due to OpenAI costs)

**Request:**

```json
{
  "message": "I want to book a hibachi party for 25 people",
  "agent": "customer",
  "thread_id": "optional-thread-id",
  "context": {
    "page": "booking",
    "user_location": "Los Angeles"
  }
}
```

**Response:** `200 OK`

```json
{
  "response": "I'd be happy to help you book a hibachi party for 25 people! To get started, could you tell me your preferred date and location?",
  "thread_id": "thread_abc123",
  "intent": "booking_inquiry",
  "suggested_actions": [
    {
      "type": "collect_date",
      "label": "Select Date",
      "action": "open_calendar"
    },
    {
      "type": "view_menu",
      "label": "View Menu",
      "action": "navigate:/menu"
    }
  ],
  "metadata": {
    "model": "gpt-4",
    "tokens_used": 150,
    "response_time_ms": 850
  }
}
```

---

### Chat Streaming (SSE)

**Endpoint:** `POST /api/v1/ai/chat/stream` **Authentication:**
Optional **Rate Limit:** 10/min

**Description:** Returns server-sent events for real-time streaming
responses.

**Request:** Same as `/api/v1/ai/chat`

**Response:** `text/event-stream`

```
data: {"type":"start","thread_id":"thread_abc123"}

data: {"type":"token","content":"I'd"}

data: {"type":"token","content":" be"}

data: {"type":"token","content":" happy"}

data: {"type":"done","metadata":{"tokens_used":150}}
```

---

## Admin Endpoints

### Analytics Dashboard

**Endpoint:** `GET /api/v1/admin/analytics` **Authentication:**
Required (Admin) **Rate Limit:** 120/min

**Query Parameters:**

```
?date_from=2025-10-01
&date_to=2025-10-31
&metric=revenue,bookings,customers
```

**Response:** `200 OK`

```json
{
  "period": {
    "from": "2025-10-01",
    "to": "2025-10-31"
  },
  "revenue": {
    "total": 45000.0,
    "change_percent": 15.5,
    "trend": "up"
  },
  "bookings": {
    "total": 125,
    "confirmed": 100,
    "pending": 20,
    "cancelled": 5,
    "change_percent": 10.2
  },
  "customers": {
    "new": 45,
    "returning": 80,
    "total_active": 450
  },
  "charts": {
    "revenue_by_day": [
      { "date": "2025-10-01", "amount": 1500.0 },
      { "date": "2025-10-02", "amount": 1800.0 }
    ],
    "bookings_by_type": {
      "birthday": 40,
      "wedding": 25,
      "corporate": 35,
      "anniversary": 15,
      "other": 10
    }
  }
}
```

---

## WebSocket Endpoints

### Real-time Chat

**Endpoint:** `wss://mhapi.mysticdatanode.net/ws/chat/{thread_id}`
**Authentication:** Optional (include `?token=jwt_token`)
**Protocol:** WebSocket

**Connect:**

```javascript
const ws = new WebSocket(
  'wss://mhapi.mysticdatanode.net/ws/chat/thread_abc123?token=jwt_token'
);
```

**Send Message:**

```json
{
  "type": "message",
  "content": "Hello, I have a question",
  "metadata": {
    "page": "booking"
  }
}
```

**Receive Message:**

```json
{
  "type": "message",
  "content": "Hi! How can I help you today?",
  "sender": "ai_assistant",
  "timestamp": "2025-10-25T10:30:00Z"
}
```

**Typing Indicator:**

```json
{
  "type": "typing",
  "is_typing": true
}
```

---

## Webhook Endpoints

### Stripe Webhook

**Endpoint:** `POST /api/webhooks/stripe` **Authentication:** Stripe
signature verification **Rate Limit:** No limit

**Description:** Receives Stripe payment events.

**Events Handled:**

- `payment_intent.succeeded`
- `payment_intent.failed`
- `charge.refunded`
- `customer.subscription.created`

---

### RingCentral Webhook

**Endpoint:** `POST /api/webhooks/ringcentral` **Authentication:**
RingCentral signature verification **Rate Limit:** No limit

**Description:** Receives SMS/call notifications.

**Events Handled:**

- `message.received`
- `call.completed`

---

## Response Schemas

### Pagination Schema

```typescript
{
  page: number;           // Current page (1-indexed)
  limit: number;          // Items per page
  total_items: number;    // Total count
  total_pages: number;    // Total pages
  has_next: boolean;      // Has next page
  has_prev: boolean;      // Has previous page
  next_cursor?: string;   // Cursor for next page (if using cursor pagination)
  prev_cursor?: string;   // Cursor for previous page
}
```

### Error Schema

```typescript
{
  error: string;          // Error code
  message: string;        // Human-readable message
  details?: object;       // Additional error context
  request_id?: string;    // Request tracking ID
  timestamp: string;      // ISO 8601 timestamp
}
```

### Booking Schema

```typescript
{
  id: number;
  reference_number: string;
  customer: Customer;
  event_date: string; // YYYY-MM-DD
  event_time: string; // HH:MM:SS
  guest_count: number;
  event_type: string;
  location: string;
  status: 'pending' | 'confirmed' | 'completed' | 'cancelled';
  total_amount: number;
  deposit_amount: number;
  deposit_paid: boolean;
  payment_status: 'unpaid' | 'partial' | 'paid';
  created_at: string;
  updated_at: string;
}
```

---

## Code Examples

### JavaScript/TypeScript (Fetch)

**Authentication:**

```typescript
async function login(email: string, password: string) {
  const response = await fetch(
    'https://mhapi.mysticdatanode.net/api/v1/auth/login',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    }
  );

  if (!response.ok) {
    throw new Error('Login failed');
  }

  const data = await response.json();
  localStorage.setItem('access_token', data.access_token);
  return data;
}
```

**Authenticated Request:**

```typescript
async function getBookings() {
  const token = localStorage.getItem('access_token');

  const response = await fetch(
    'https://mhapi.mysticdatanode.net/api/v1/bookings?page=1&limit=20',
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    if (response.status === 401) {
      // Token expired, refresh or re-login
      throw new Error('Unauthorized');
    }
    throw new Error('Request failed');
  }

  return await response.json();
}
```

---

### Python (requests)

**Authentication:**

```python
import requests

def login(email: str, password: str) -> dict:
    response = requests.post(
        'https://mhapi.mysticdatanode.net/api/v1/auth/login',
        json={'email': email, 'password': password}
    )
    response.raise_for_status()
    data = response.json()
    return data

# Usage
auth_data = login('admin@myhibachi.com', 'password')
access_token = auth_data['access_token']
```

**Authenticated Request:**

```python
def get_bookings(access_token: str, page: int = 1, limit: int = 20):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    params = {'page': page, 'limit': limit}

    response = requests.get(
        'https://mhapi.mysticdatanode.net/api/v1/bookings',
        headers=headers,
        params=params
    )
    response.raise_for_status()
    return response.json()
```

---

### cURL

**Login:**

```bash
curl -X POST https://mhapi.mysticdatanode.net/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@myhibachi.com","password":"password"}'
```

**Get Bookings:**

```bash
curl -X GET "https://mhapi.mysticdatanode.net/api/v1/bookings?page=1&limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Create Lead:**

```bash
curl -X POST https://mhapi.mysticdatanode.net/api/v1/public/leads \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "phone": "555-123-4567",
    "email": "john@example.com",
    "message": "Interested in catering",
    "source": "website"
  }'
```

---

## Best Practices

### Security

1. **Never expose tokens in client-side code**
2. **Always use HTTPS in production**
3. **Implement token refresh logic**
4. **Store tokens securely** (HttpOnly cookies or secure storage)
5. **Validate all user input**
6. **Use rate limiting to prevent abuse**

### Performance

1. **Use pagination** for large datasets
2. **Cache responses** when appropriate
3. **Implement request debouncing** for search/autocomplete
4. **Use WebSockets** for real-time features
5. **Minimize payload size** (only request needed fields)

### Error Handling

1. **Always check HTTP status codes**
2. **Implement retry logic** with exponential backoff
3. **Log errors** for debugging
4. **Show user-friendly error messages**
5. **Handle network failures gracefully**

### Rate Limiting

1. **Monitor rate limit headers**
2. **Implement client-side rate limiting**
3. **Cache responses** to reduce API calls
4. **Use webhooks** instead of polling

---

## Interactive Documentation

### OpenAPI/Swagger

**URL:** `https://mhapi.mysticdatanode.net/docs`

Features:

- Interactive API explorer
- Try endpoints directly from browser
- View request/response schemas
- Download OpenAPI spec

### ReDoc

**URL:** `https://mhapi.mysticdatanode.net/redoc`

Features:

- Clean, readable documentation
- Search functionality
- Code samples
- Downloadable as PDF

---

## Changelog

### Version 1.0.0 (Current)

- ✅ Initial API release
- ✅ Authentication with JWT
- ✅ CRUD operations for bookings, customers, leads
- ✅ AI chat integration
- ✅ Rate limiting
- ✅ WebSocket support
- ✅ Stripe webhook integration

### Upcoming (v1.1.0)

- 🚧 GraphQL endpoint
- 🚧 Bulk operations
- 🚧 Advanced filtering
- 🚧 API key management UI
- 🚧 Enhanced analytics

---

## Support & Resources

### Documentation

- **This Guide:** Comprehensive API reference
- **OpenAPI Spec:** `/docs` (interactive)
- **Postman Collection:** Available on request

### Getting Help

- **Email:** dev@myhibachi.com
- **Slack:** #api-support (internal)
- **GitHub Issues:** For bug reports

### Rate Limit Increase

Contact admin for rate limit increase requests. Provide:

- Use case description
- Expected request volume
- Timeframe

---

**Document Version:** 1.0 **Last Updated:** January 30, 2025
**Maintained By:** Development Team

---

## Related Documentation

- [TESTING_COMPREHENSIVE_GUIDE.md](./TESTING_COMPREHENSIVE_GUIDE.md) -
  API testing procedures
- [PRODUCTION_OPERATIONS_RUNBOOK.md](./PRODUCTION_OPERATIONS_RUNBOOK.md) -
  Production operations
- [LOCAL_DEVELOPMENT_SETUP.md](./LOCAL_DEVELOPMENT_SETUP.md) - Local
  development setup
- [AUTHENTICATION_GUIDE.md](./docs/authentication/) - Detailed auth
  guide

---
