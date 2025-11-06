# 🗺️ API Endpoint Mapping for Frontend Team

**Document Version**: 1.0  
**Last Updated**: November 5, 2025  
**Backend Version**: 2.0 (Post Nuclear Refactor)  
**Status**: ✅ Production Ready

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Base URLs](#base-urls)
3. [Authentication](#authentication)
4. [Endpoint Categories](#endpoint-categories)
5. [Complete Endpoint List](#complete-endpoint-list)
6. [Request/Response Examples](#requestresponse-examples)
7. [Error Handling](#error-handling)
8. [Rate Limiting](#rate-limiting)
9. [Versioning](#versioning)

---

## 🎯 Overview

This document provides a comprehensive mapping of all backend API
endpoints for frontend integration. All endpoints are tested and
production-ready.

### Quick Stats

- **Total Endpoints**: 250+
- **API Version**: v1
- **Base Prefix**: `/api`
- **Authentication**: JWT Bearer Token
- **Content-Type**: `application/json`

---

## 🌐 Base URLs

### Development

```
http://localhost:8000
```

### Production

```
https://api.myhibachi.com
```

### API Documentation

```
http://localhost:8000/docs        # Swagger UI
http://localhost:8000/redoc       # ReDoc
```

---

## 🔐 Authentication

### Headers Required

```typescript
headers: {
  'Authorization': 'Bearer <jwt_token>',
  'Content-Type': 'application/json'
}
```

### Authentication Endpoints

| Method | Endpoint             | Description       | Auth Required |
| ------ | -------------------- | ----------------- | ------------- |
| POST   | `/api/auth/login`    | User login        | ❌ No         |
| POST   | `/api/auth/register` | User registration | ❌ No         |
| GET    | `/api/auth/me`       | Get current user  | ✅ Yes        |
| POST   | `/api/auth/refresh`  | Refresh token     | ✅ Yes        |
| POST   | `/api/auth/logout`   | Logout user       | ✅ Yes        |

---

## 📂 Endpoint Categories

### 1. Health & Monitoring

| Method | Endpoint         | Description           | Auth |
| ------ | ---------------- | --------------------- | ---- |
| GET    | `/health`        | Basic health check    | ❌   |
| GET    | `/ready`         | Readiness probe (K8s) | ❌   |
| GET    | `/api/health/db` | Database health       | ❌   |
| GET    | `/info`          | App information       | ❌   |

---

### 2. Booking Management

**Base Path**: `/api/bookings` or `/api/v1/bookings`

| Method | Endpoint                        | Description        | Auth | Role        |
| ------ | ------------------------------- | ------------------ | ---- | ----------- |
| GET    | `/api/v1/bookings`              | List all bookings  | ✅   | Any         |
| POST   | `/api/v1/bookings`              | Create new booking | ✅   | Customer    |
| GET    | `/api/v1/bookings/{id}`         | Get booking by ID  | ✅   | Owner/Admin |
| PUT    | `/api/v1/bookings/{id}`         | Update booking     | ✅   | Owner/Admin |
| DELETE | `/api/v1/bookings/{id}`         | Delete booking     | ✅   | Admin       |
| GET    | `/api/v1/bookings/booked-dates` | Get booked dates   | ✅   | Any         |
| GET    | `/api/v1/bookings/availability` | Check availability | ❌   | Public      |
| GET    | `/api/admin/bookings/stats`     | Booking statistics | ✅   | Admin       |
| GET    | `/api/admin/kpis`               | KPI dashboard      | ✅   | Admin       |
| GET    | `/api/admin/customer-analytics` | Customer analytics | ✅   | Admin       |

**Frontend Usage Examples**:

```typescript
// From: apps/admin/src/hooks/booking/useBooking.ts
const bookedDates = await apiFetch('/api/v1/bookings/booked-dates');
const availability = await apiFetch(
  `/api/v1/bookings/availability?date=${dateStr}`
);
```

---

### 3. Payment Processing (Stripe)

**Base Path**: `/api/stripe`

| Method | Endpoint                              | Description            | Auth | Role     |
| ------ | ------------------------------------- | ---------------------- | ---- | -------- |
| POST   | `/api/stripe/create-checkout-session` | Create Stripe Checkout | ✅   | Customer |
| POST   | `/api/stripe/create-payment-intent`   | Create Payment Intent  | ✅   | Customer |
| POST   | `/api/stripe/portal-link`             | Customer portal link   | ✅   | Customer |
| POST   | `/api/stripe/webhook`                 | Stripe webhook handler | ❌   | Stripe   |
| GET    | `/api/stripe/payments`                | List payments          | ✅   | Admin    |
| POST   | `/api/stripe/refund`                  | Process refund         | ✅   | Admin    |
| GET    | `/api/stripe/invoices`                | List invoices          | ✅   | Admin    |
| GET    | `/api/stripe/analytics/payments`      | Payment analytics      | ✅   | Admin    |

**Alternative Paths (Backward Compatibility)**:

```typescript
// Both paths work:
POST / api / stripe / create - payment - intent;
POST / api / stripe / v1 / payments / create - intent; // Legacy path
```

**Frontend Usage Examples**:

```typescript
// From: apps/admin/src/components/PaymentManagement.tsx
const payments = await fetch(`/api/stripe/payments?${params}`);
const analytics = await fetch(
  `/api/stripe/analytics/payments?${params}`
);
const refund = await fetch('/api/stripe/refund', {
  method: 'POST',
  body: refundData,
});
```

---

### 4. Lead Management

**Base Path**: `/api/leads`

| Method | Endpoint                           | Description          | Auth | Role  |
| ------ | ---------------------------------- | -------------------- | ---- | ----- |
| GET    | `/api/leads`                       | List all leads       | ✅   | Admin |
| POST   | `/api/leads`                       | Create new lead      | ✅   | Any   |
| GET    | `/api/leads/{id}`                  | Get lead by ID       | ✅   | Admin |
| PUT    | `/api/leads/{id}`                  | Update lead          | ✅   | Admin |
| DELETE | `/api/leads/{id}`                  | Delete lead          | ✅   | Admin |
| POST   | `/api/leads/{id}/events`           | Add lead event       | ✅   | Admin |
| POST   | `/api/leads/{id}/ai-analysis`      | AI lead analysis     | ✅   | Admin |
| GET    | `/api/leads/{id}/nurture-sequence` | Get nurture sequence | ✅   | Admin |
| GET    | `/api/leads/social-threads`        | List social threads  | ✅   | Admin |
| POST   | `/api/leads/social-threads`        | Create social thread | ✅   | Admin |

**Frontend Usage Examples**:

```typescript
// From: apps/admin/src/services/api.ts
const leads = await api.get(`/api/leads?${params.toString()}`);
const lead = await api.post('/api/leads', data);
const analysis = await api.post(
  `/api/leads/${leadId}/ai-analysis`,
  {}
);
```

---

### 5. Review System

**Base Path**: `/api/reviews`

| Method | Endpoint                              | Description           | Auth | Role        |
| ------ | ------------------------------------- | --------------------- | ---- | ----------- |
| GET    | `/api/reviews`                        | List reviews          | ❌   | Public      |
| POST   | `/api/reviews`                        | Create review         | ✅   | Customer    |
| GET    | `/api/reviews/{id}`                   | Get review by ID      | ❌   | Public      |
| PUT    | `/api/reviews/{id}`                   | Update review         | ✅   | Owner/Admin |
| DELETE | `/api/reviews/{id}`                   | Delete review         | ✅   | Admin       |
| GET    | `/api/reviews/admin/escalated`        | Escalated reviews     | ✅   | Admin       |
| POST   | `/api/reviews/{id}/resolve`           | Resolve review issue  | ✅   | Admin       |
| POST   | `/api/reviews/ai/issue-coupon`        | AI issue coupon       | ✅   | Admin       |
| GET    | `/api/reviews/admin/analytics`        | Review analytics      | ✅   | Admin       |
| GET    | `/api/reviews/customers/{id}/reviews` | Customer reviews      | ✅   | Admin       |
| POST   | `/api/reviews/track-external`         | Track external review | ✅   | Admin       |
| POST   | `/api/reviews/coupons/validate`       | Validate coupon       | ✅   | Any         |
| POST   | `/api/reviews/coupons/apply`          | Apply coupon          | ✅   | Customer    |

**Frontend Usage Examples**:

```typescript
// From: apps/admin/src/services/api.ts
const reviews = await api.get(`/api/reviews?${params.toString()}`);
const escalated = await api.get('/api/reviews/admin/escalated');
const resolve = await api.post(
  `/api/reviews/${reviewId}/resolve`,
  resolution
);
```

---

### 6. Newsletter & Campaigns

**Base Path**: `/api/newsletter`

| Method | Endpoint                               | Description      | Auth | Role   |
| ------ | -------------------------------------- | ---------------- | ---- | ------ |
| GET    | `/api/newsletter/subscribers`          | List subscribers | ✅   | Admin  |
| POST   | `/api/newsletter/subscribe`            | Subscribe email  | ❌   | Public |
| POST   | `/api/newsletter/unsubscribe`          | Unsubscribe      | ❌   | Public |
| GET    | `/api/newsletter/campaigns`            | List campaigns   | ✅   | Admin  |
| POST   | `/api/newsletter/campaigns`            | Create campaign  | ✅   | Admin  |
| GET    | `/api/newsletter/campaigns/{id}`       | Get campaign     | ✅   | Admin  |
| POST   | `/api/newsletter/campaigns/{id}/send`  | Send campaign    | ✅   | Admin  |
| GET    | `/api/newsletter/campaigns/{id}/stats` | Campaign stats   | ✅   | Admin  |

---

### 7. Customer Management

**Base Path**: `/api/v1/customers`

| Method | Endpoint                               | Description            | Auth | Role     |
| ------ | -------------------------------------- | ---------------------- | ---- | -------- |
| POST   | `/api/v1/customers/create-or-update`   | Create/update customer | ✅   | Admin    |
| GET    | `/api/v1/customers/{id}/preferences`   | Get preferences        | ✅   | Customer |
| GET    | `/api/v1/customers/{id}/analytics`     | Customer analytics     | ✅   | Admin    |
| POST   | `/api/v1/customers/{id}/track-payment` | Track payment          | ✅   | Admin    |
| GET    | `/api/v1/customers/find-by-email`      | Find by email          | ✅   | Admin    |
| POST   | `/api/v1/customers/{id}/portal`        | Customer portal        | ✅   | Customer |
| GET    | `/api/v1/customers/dashboard`          | Customer dashboard     | ✅   | Customer |

**Frontend Usage Examples**:

```typescript
// From: apps/admin/src/lib/server/stripeCustomerService.ts
const customer = await apiFetch(
  '/api/v1/customers/create-or-update',
  { method: 'POST', body }
);
const analytics = await apiFetch(
  `/api/v1/customers/${stripeCustomerId}/analytics`
);
const dashboard = await apiFetch(
  `/api/v1/customers/dashboard?customer_id=${customerId}`
);
```

---

### 8. AI & Unified Inbox

**Base Path**: `/api/v1/inbox` and `/api/v1/ai`

| Method | Endpoint                              | Description         | Auth | Role  |
| ------ | ------------------------------------- | ------------------- | ---- | ----- |
| GET    | `/api/v1/inbox/messages`              | List messages       | ✅   | Admin |
| POST   | `/api/v1/inbox/threads/{id}/messages` | Send message        | ✅   | Admin |
| GET    | `/api/v1/inbox/threads/{id}`          | Get thread          | ✅   | Admin |
| POST   | `/api/v1/ai/chat`                     | AI chat endpoint    | ✅   | Any   |
| POST   | `/api/v1/ai/multi-channel/email`      | AI email handling   | ✅   | Admin |
| POST   | `/api/v1/ai/multi-channel/sms`        | AI SMS handling     | ✅   | Admin |
| GET    | `/api/v1/ai/readiness`                | AI readiness status | ✅   | Admin |

**Frontend Usage Examples**:

```typescript
// From: apps/admin/src/services/api.ts
const messages = await api.get(`/api/v1/inbox/messages?${query}`);
const response = await api.post(
  `/api/v1/inbox/threads/${threadId}/messages`,
  { content }
);
```

---

### 9. Admin Analytics

**Base Path**: `/api/admin` and `/api/payments`

| Method | Endpoint                           | Description                | Auth | Role  |
| ------ | ---------------------------------- | -------------------------- | ---- | ----- |
| GET    | `/api/admin/analytics/dashboard`   | Main dashboard             | ✅   | Admin |
| GET    | `/api/admin/analytics/revenue`     | Revenue analytics          | ✅   | Admin |
| GET    | `/api/admin/analytics/customers`   | Customer analytics         | ✅   | Admin |
| GET    | `/api/admin/analytics/bookings`    | Booking analytics          | ✅   | Admin |
| GET    | `/api/admin/kpis`                  | Key performance indicators | ✅   | Admin |
| GET    | `/api/payments/analytics/payments` | Payment analytics          | ✅   | Admin |

---

### 10. Station Management (Multi-Tenant)

**Base Path**: `/api/station` and `/api/admin/stations`

| Method | Endpoint                     | Description          | Auth | Role        |
| ------ | ---------------------------- | -------------------- | ---- | ----------- |
| POST   | `/api/station/auth/login`    | Station login        | ❌   | Public      |
| POST   | `/api/station/auth/register` | Station registration | ❌   | Public      |
| GET    | `/api/station/auth/me`       | Current station      | ✅   | Station     |
| GET    | `/api/admin/stations`        | List all stations    | ✅   | Super Admin |
| POST   | `/api/admin/stations`        | Create station       | ✅   | Super Admin |
| PUT    | `/api/admin/stations/{id}`   | Update station       | ✅   | Super Admin |
| DELETE | `/api/admin/stations/{id}`   | Delete station       | ✅   | Super Admin |

---

### 11. QR Code Tracking

**Base Path**: `/api/qr`

| Method | Endpoint                           | Description        | Auth | Role   |
| ------ | ---------------------------------- | ------------------ | ---- | ------ |
| POST   | `/api/qr/campaigns`                | Create QR campaign | ✅   | Admin  |
| GET    | `/api/qr/campaigns`                | List campaigns     | ✅   | Admin  |
| GET    | `/api/qr/campaigns/{id}`           | Get campaign       | ✅   | Admin  |
| GET    | `/api/qr/campaigns/{id}/analytics` | Campaign analytics | ✅   | Admin  |
| POST   | `/api/qr/track/{code}`             | Track QR scan      | ❌   | Public |

---

### 12. Payment Email Monitoring

**Base Path**: `/api/v1/payments/email-notifications`

| Method | Endpoint                                            | Description          | Auth | Role  |
| ------ | --------------------------------------------------- | -------------------- | ---- | ----- |
| GET    | `/api/v1/payments/email-notifications/recent`       | Recent notifications | ✅   | Admin |
| GET    | `/api/v1/payments/email-notifications/unmatched`    | Unmatched payments   | ✅   | Admin |
| GET    | `/api/v1/payments/email-notifications/status`       | System status        | ✅   | Admin |
| POST   | `/api/v1/payments/email-notifications/process`      | Trigger processing   | ✅   | Admin |
| POST   | `/api/v1/payments/email-notifications/manual-match` | Manual matching      | ✅   | Admin |

**Frontend Usage Examples**:

```typescript
// From: apps/admin/src/app/payments/email-monitoring/page.tsx
const recent = await fetch(
  '/api/v1/payments/email-notifications/recent?since_hours=48&limit=20'
);
const unmatched = await fetch(
  '/api/v1/payments/email-notifications/unmatched?since_hours=48'
);
const process = await fetch(
  '/api/v1/payments/email-notifications/process',
  { method: 'POST' }
);
```

---

### 13. Webhooks

**Base Path**: `/api/webhooks` or `/api/<service>`

| Method | Endpoint                        | Description             | Auth | Role        |
| ------ | ------------------------------- | ----------------------- | ---- | ----------- |
| POST   | `/api/stripe/webhook`           | Stripe webhook          | ❌   | Stripe      |
| POST   | `/api/ringcentral/webhook`      | RingCentral webhook     | ❌   | RingCentral |
| POST   | `/api/webhooks/meta`            | Meta/Facebook webhook   | ❌   | Meta        |
| POST   | `/api/webhooks/google-business` | Google Business webhook | ❌   | Google      |

---

### 14. Admin Error Logs

**Base Path**: `/api/admin/error-logs`

| Method | Endpoint                             | Description      | Auth | Role  |
| ------ | ------------------------------------ | ---------------- | ---- | ----- |
| GET    | `/api/admin/error-logs`              | List error logs  | ✅   | Admin |
| GET    | `/api/admin/error-logs/{id}`         | Get error log    | ✅   | Admin |
| POST   | `/api/admin/error-logs/{id}/resolve` | Resolve error    | ✅   | Admin |
| DELETE | `/api/admin/error-logs/{id}`         | Delete error log | ✅   | Admin |

---

### 15. Notification Groups

**Base Path**: `/api/admin/notification-groups`

| Method | Endpoint                              | Description  | Auth | Role  |
| ------ | ------------------------------------- | ------------ | ---- | ----- |
| GET    | `/api/admin/notification-groups`      | List groups  | ✅   | Admin |
| POST   | `/api/admin/notification-groups`      | Create group | ✅   | Admin |
| PUT    | `/api/admin/notification-groups/{id}` | Update group | ✅   | Admin |
| DELETE | `/api/admin/notification-groups/{id}` | Delete group | ✅   | Admin |

---

## 📝 Request/Response Examples

### Example 1: Create Booking

**Request**:

```http
POST /api/v1/bookings
Authorization: Bearer <token>
Content-Type: application/json

{
  "date": "2025-12-25",
  "time": "18:00",
  "guests": 8,
  "menu": "adult",
  "location": "123 Main St, San Jose, CA",
  "customer_email": "customer@example.com",
  "customer_name": "John Doe",
  "customer_phone": "+1234567890"
}
```

**Response**:

```json
{
  "id": "booking-123",
  "status": "pending",
  "date": "2025-12-25",
  "time": "18:00",
  "guests": 8,
  "menu": "adult",
  "location": "123 Main St, San Jose, CA",
  "total_amount": 800.0,
  "deposit_amount": 100.0,
  "created_at": "2025-11-05T10:30:00Z"
}
```

---

### Example 2: Create Payment Intent

**Request**:

```http
POST /api/stripe/create-payment-intent
Authorization: Bearer <token>
Content-Type: application/json

{
  "booking_id": "booking-123",
  "amount": 10000,
  "payment_type": "deposit",
  "customer_email": "customer@example.com"
}
```

**Response**:

```json
{
  "client_secret": "pi_xxx_secret_xxx",
  "payment_intent_id": "pi_xxx",
  "amount": 10000,
  "currency": "usd",
  "status": "requires_payment_method"
}
```

---

### Example 3: List Leads with Filtering

**Request**:

```http
GET /api/leads?status=new&source=instagram&limit=20
Authorization: Bearer <token>
```

**Response**:

```json
{
  "data": [
    {
      "id": "lead-123",
      "name": "Jane Smith",
      "email": "jane@example.com",
      "phone": "+1234567890",
      "status": "new",
      "source": "instagram",
      "score": 85,
      "created_at": "2025-11-05T09:00:00Z"
    }
  ],
  "total": 45,
  "page": 1,
  "limit": 20
}
```

---

## ❌ Error Handling

### Standard Error Response Format

```json
{
  "error": "Error message",
  "detail": "Detailed error description",
  "status_code": 400,
  "timestamp": "2025-11-05T10:30:00Z",
  "path": "/api/bookings"
}
```

### HTTP Status Codes

| Code | Meaning               | Usage                               |
| ---- | --------------------- | ----------------------------------- |
| 200  | OK                    | Successful GET/PUT/DELETE           |
| 201  | Created               | Successful POST                     |
| 204  | No Content            | Successful DELETE (no body)         |
| 400  | Bad Request           | Invalid request data                |
| 401  | Unauthorized          | Missing/invalid token               |
| 403  | Forbidden             | Insufficient permissions            |
| 404  | Not Found             | Resource doesn't exist              |
| 409  | Conflict              | Resource conflict (e.g., duplicate) |
| 422  | Unprocessable Entity  | Validation error                    |
| 429  | Too Many Requests     | Rate limit exceeded                 |
| 500  | Internal Server Error | Server error                        |
| 503  | Service Unavailable   | Service temporarily down            |

---

## 🚦 Rate Limiting

### Rate Limit Headers

Every response includes rate limit information:

```http
X-RateLimit-Tier: premium
X-RateLimit-Remaining-Minute: 95
X-RateLimit-Remaining-Hour: 950
X-RateLimit-Reset-Minute: 1699185600
X-RateLimit-Reset-Hour: 1699189200
X-RateLimit-Backend: redis
```

### Rate Limit Tiers

| Tier              | Requests/Minute | Requests/Hour |
| ----------------- | --------------- | ------------- |
| **Public**        | 30              | 300           |
| **Authenticated** | 100             | 1,000         |
| **Premium**       | 200             | 2,000         |
| **Admin**         | 500             | 5,000         |

### Rate Limit Exceeded Response

```json
{
  "error": "Rate limit exceeded",
  "tier": "authenticated",
  "limit_type": "minute",
  "limit_value": 100,
  "current": 101,
  "retry_after_seconds": 45
}
```

**HTTP Headers**:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 45
```

---

## 📌 Versioning

### Current API Version

- **Version**: v1
- **Released**: November 2025
- **Status**: Stable

### Version Strategy

- Major version in URL path: `/api/v1/`
- Backward compatibility maintained within major version
- Deprecated endpoints marked in documentation
- 6-month deprecation notice before removal

### Deprecated Paths (Still Supported)

These old paths still work but should be migrated to new paths:

| Old Path                                | New Path                            | Status        |
| --------------------------------------- | ----------------------------------- | ------------- |
| `/api/stripe/v1/payments/create-intent` | `/api/stripe/create-payment-intent` | ⚠️ Deprecated |
| `/api/app/bookings`                     | `/api/v1/bookings`                  | ⚠️ Deprecated |

---

## 🔧 Integration Tips

### 1. TypeScript Types

Generate types from OpenAPI schema:

```bash
npm install openapi-typescript-codegen
openapi --input http://localhost:8000/openapi.json --output ./src/api/generated
```

### 2. API Client Setup

```typescript
// api-client.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth interceptor
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default apiClient;
```

### 3. Error Handling

```typescript
// error-handler.ts
export const handleApiError = (error: any) => {
  if (error.response) {
    // Server responded with error
    switch (error.response.status) {
      case 401:
        // Redirect to login
        router.push('/login');
        break;
      case 403:
        // Show permission error
        toast.error('You do not have permission');
        break;
      case 429:
        // Rate limited
        const retryAfter = error.response.headers['retry-after'];
        toast.error(`Rate limited. Retry in ${retryAfter}s`);
        break;
      default:
        toast.error(error.response.data.error || 'An error occurred');
    }
  } else if (error.request) {
    // Network error
    toast.error('Network error. Please check your connection.');
  }
};
```

### 4. Retry Logic

```typescript
// retry-logic.ts
export const fetchWithRetry = async (
  url: string,
  options: RequestInit,
  maxRetries = 3
) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url, options);
      if (response.status === 429) {
        const retryAfter = response.headers.get('retry-after');
        await new Promise(resolve =>
          setTimeout(resolve, Number(retryAfter) * 1000)
        );
        continue;
      }
      return response;
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve =>
        setTimeout(resolve, 1000 * (i + 1))
      );
    }
  }
};
```

---

## 📚 Additional Resources

- **OpenAPI Spec**: http://localhost:8000/openapi.json
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Architecture Docs**: `ARCHITECTURE.md`
- **Migration Guide**: `MIGRATION_SUMMARY.md`

---

## 🆘 Support

For API questions or issues:

1. Check OpenAPI documentation at `/docs`
2. Review error logs in admin panel
3. Check rate limit headers
4. Verify authentication token
5. Contact backend team

---

**Document Status**: ✅ Complete and Verified  
**Last Reviewed**: November 5, 2025  
**Maintained By**: Backend Engineering Team
