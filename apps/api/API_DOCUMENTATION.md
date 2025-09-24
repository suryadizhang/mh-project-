# MyHibachi AI Sales CRM - API Documentation

## 🚀 Complete API Reference

### Overview

This document provides comprehensive API documentation for the
MyHibachi AI Sales CRM system with CQRS architecture, OAuth 2.1 + MFA
authentication, and complete booking management.

## 🔐 Authentication

### Base URL

```
Production: https://api.myhibachichef.com
Development: http://localhost:8000
```

### Authentication Flow

#### 1. Login

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "role": "ADMIN",
    "mfa_enabled": true
  }
}
```

#### 2. MFA Setup (if required)

```http
POST /api/auth/mfa/setup
Authorization: Bearer {access_token}
```

**Response:**

```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "backup_codes": ["123456789", "987654321", ...]
}
```

#### 3. MFA Verification

```http
POST /api/auth/mfa/verify
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "token": "123456"
}
```

### Authorization Header

Include in all authenticated requests:

```http
Authorization: Bearer {access_token}
```

## 👥 User Management API

### List Users

```http
GET /api/users
Authorization: Bearer {access_token}
```

**Query Parameters:**

- `page` (int): Page number (default: 1)
- `limit` (int): Items per page (default: 50)
- `role` (string): Filter by role
- `active` (boolean): Filter by active status

**Response:**

```json
{
  "data": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "email": "user@example.com",
      "role": "ADMIN",
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z",
      "last_login": "2024-01-15T15:45:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 100,
    "pages": 2
  }
}
```

### Create User

```http
POST /api/users
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "SecurePassword123!",
  "role": "STAFF",
  "full_name": "John Doe"
}
```

### Update User

```http
PUT /api/users/{user_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "role": "MANAGER",
  "is_active": false
}
```

### Delete User

```http
DELETE /api/users/{user_id}
Authorization: Bearer {access_token}
```

## 📅 Booking Management API

### List Bookings

```http
GET /api/bookings
Authorization: Bearer {access_token}
```

**Query Parameters:**

- `page` (int): Page number
- `limit` (int): Items per page
- `status` (string): Filter by status (PENDING, CONFIRMED, CANCELLED)
- `date_from` (date): Start date filter
- `date_to` (date): End date filter
- `customer_id` (uuid): Filter by customer

**Response:**

```json
{
  "data": [
    {
      "id": "booking-123",
      "customer": {
        "id": "customer-456",
        "name": "John Smith",
        "email": "john@example.com",
        "phone": "+1234567890"
      },
      "event_date": "2024-02-15",
      "event_time": "18:00:00",
      "location": {
        "address": "123 Main St",
        "city": "Sacramento",
        "state": "CA",
        "zip_code": "95814"
      },
      "guest_count": 8,
      "total_amount": 360.0,
      "deposit_amount": 90.0,
      "status": "CONFIRMED",
      "menu_items": ["Hibachi Chicken", "Fried Rice"],
      "special_requests": "No onions please",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T11:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 50,
    "pages": 3
  }
}
```

### Create Booking

```http
POST /api/bookings
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "customer": {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "phone": "+1987654321"
  },
  "event_date": "2024-02-20",
  "event_time": "19:00",
  "location": {
    "address": "456 Oak Ave",
    "city": "Sacramento",
    "state": "CA",
    "zip_code": "95825"
  },
  "guest_count": 6,
  "menu_items": ["Hibachi Steak", "Vegetables"],
  "special_requests": "Birthday celebration"
}
```

### Update Booking

```http
PUT /api/bookings/{booking_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "status": "CONFIRMED",
  "guest_count": 8,
  "special_requests": "Updated requirements"
}
```

### Cancel Booking

```http
DELETE /api/bookings/{booking_id}
Authorization: Bearer {access_token}
```

## 👤 Customer Management API

### List Customers

```http
GET /api/customers
Authorization: Bearer {access_token}
```

**Query Parameters:**

- `page` (int): Page number
- `limit` (int): Items per page
- `search` (string): Search by name, email, or phone

### Create Customer

```http
POST /api/customers
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "Alice Johnson",
  "email": "alice@example.com",
  "phone": "+1555123456",
  "address": {
    "street": "789 Pine St",
    "city": "Sacramento",
    "state": "CA",
    "zip_code": "95816"
  },
  "dietary_restrictions": ["vegetarian"],
  "notes": "Prefers early evening events"
}
```

### Get Customer

```http
GET /api/customers/{customer_id}
Authorization: Bearer {access_token}
```

### Update Customer

```http
PUT /api/customers/{customer_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "phone": "+1555987654",
  "notes": "Updated contact information"
}
```

## 📋 Waitlist Management API

### List Waitlist Entries

```http
GET /api/waitlist
Authorization: Bearer {access_token}
```

### Add to Waitlist

```http
POST /api/waitlist
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "customer": {
    "name": "Bob Wilson",
    "email": "bob@example.com",
    "phone": "+1444555666"
  },
  "preferred_date": "2024-02-25",
  "preferred_time": "18:00",
  "guest_count": 4,
  "location": {
    "city": "Sacramento",
    "state": "CA"
  }
}
```

### Convert Waitlist to Booking

```http
POST /api/waitlist/{waitlist_id}/convert
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "event_date": "2024-02-25",
  "event_time": "18:30",
  "location": {
    "address": "123 Main St",
    "city": "Sacramento",
    "state": "CA",
    "zip_code": "95814"
  }
}
```

## 💰 Payment Management API

### Process Payment

```http
POST /api/payments/process
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "booking_id": "booking-123",
  "amount": 90.00,
  "payment_method": "stripe",
  "stripe_token": "tok_1234567890"
}
```

### List Payments

```http
GET /api/payments
Authorization: Bearer {access_token}
```

### Refund Payment

```http
POST /api/payments/{payment_id}/refund
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "amount": 45.00,
  "reason": "Customer cancellation"
}
```

## 🤖 AI Booking Tools API

### AI Availability Check

```http
POST /api/ai/availability
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "date": "2024-02-20",
  "guest_count": 6,
  "location": {
    "city": "Sacramento",
    "state": "CA"
  }
}
```

**Response:**

```json
{
  "available": true,
  "available_slots": ["17:00", "18:00", "19:00"],
  "price_estimate": {
    "base_price": 270.0,
    "deposit_required": 67.5,
    "total_estimate": 270.0
  },
  "alternative_dates": [
    {
      "date": "2024-02-21",
      "available_slots": ["17:30", "18:30", "19:30"]
    }
  ]
}
```

### AI Booking Creation

```http
POST /api/ai/create-booking
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "customer_info": "John Smith, john@example.com, +1234567890",
  "event_details": "February 20th at 7pm for 6 people at 123 Main St Sacramento",
  "special_requests": "Birthday celebration with extra fried rice"
}
```

### AI Quote Generation

```http
POST /api/ai/generate-quote
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "guest_count": 8,
  "location": "Folsom, CA",
  "date": "2024-03-15",
  "special_requests": "Corporate event with premium menu"
}
```

## 📊 Analytics & Reporting API

### Booking Statistics

```http
GET /api/analytics/bookings
Authorization: Bearer {access_token}
```

**Query Parameters:**

- `start_date` (date): Statistics start date
- `end_date` (date): Statistics end date
- `group_by` (string): Group by day, week, month

**Response:**

```json
{
  "total_bookings": 150,
  "confirmed_bookings": 120,
  "cancelled_bookings": 30,
  "total_revenue": 15000.0,
  "average_booking_value": 125.0,
  "popular_times": ["18:00", "19:00", "18:30"],
  "top_locations": [
    { "city": "Sacramento", "count": 80 },
    { "city": "Folsom", "count": 40 },
    { "city": "Roseville", "count": 30 }
  ]
}
```

### Revenue Report

```http
GET /api/analytics/revenue
Authorization: Bearer {access_token}
```

### Customer Analytics

```http
GET /api/analytics/customers
Authorization: Bearer {access_token}
```

## 🔔 Notification Management API

### Send SMS

```http
POST /api/notifications/sms
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "to": "+1234567890",
  "message": "Your hibachi booking for Feb 20th is confirmed!",
  "booking_id": "booking-123"
}
```

### Send Email

```http
POST /api/notifications/email
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "to": "customer@example.com",
  "subject": "Booking Confirmation",
  "template": "booking_confirmation",
  "data": {
    "booking_id": "booking-123",
    "customer_name": "John Smith",
    "event_date": "2024-02-20"
  }
}
```

### Notification History

```http
GET /api/notifications/history
Authorization: Bearer {access_token}
```

## 🏥 Health Check API

### API Health

```http
GET /health
```

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "environment": "production"
}
```

### Database Health

```http
GET /health/db
```

### Workers Health

```http
GET /health/workers
```

### Features Status

```http
GET /health/features
```

**Response:**

```json
{
  "status": "healthy",
  "features": {
    "authentication": "enabled",
    "mfa": "enabled",
    "workers": "running",
    "email_service": "connected",
    "sms_service": "connected",
    "payment_service": "connected",
    "encryption": "enabled",
    "audit_logging": "enabled"
  }
}
```

## 📈 Rate Limiting

### Rate Limits

- **Authentication**: 5 requests/minute
- **Booking Operations**: 10 requests/minute
- **General API**: 100 requests/minute
- **SMS Notifications**: 30 requests/minute

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248000
```

## 🚨 Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The provided data is invalid",
    "details": {
      "field": "email",
      "issue": "Invalid email format"
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_123456789"
  }
}
```

### Common Error Codes

- `AUTHENTICATION_REQUIRED` (401): No valid authentication token
- `INSUFFICIENT_PERMISSIONS` (403): User lacks required permissions
- `RESOURCE_NOT_FOUND` (404): Requested resource doesn't exist
- `VALIDATION_ERROR` (422): Request data validation failed
- `RATE_LIMIT_EXCEEDED` (429): Too many requests
- `INTERNAL_SERVER_ERROR` (500): Server error

## 🔒 Security Features

### RBAC Permissions

- **SUPER_ADMIN**: Full system access
- **ADMIN**: User and booking management
- **MANAGER**: Booking and customer management
- **STAFF**: Basic booking operations
- **VIEWER**: Read-only access
- **AI_SYSTEM**: AI booking tool access

### Data Encryption

- **Field-Level Encryption**: Sensitive customer data encrypted at
  rest
- **In-Transit Encryption**: All API communication over HTTPS
- **JWT Tokens**: Secure authentication with expiration

### Audit Logging

All API operations are logged with:

- User identification
- Action performed
- Timestamp
- IP address
- Request/response data (sanitized)

## 📱 Webhook Events

### Stripe Webhooks

```http
POST /api/stripe/webhook
Content-Type: application/json
Stripe-Signature: t=1234567890,v1=...

{
  "type": "payment_intent.succeeded",
  "data": {
    "object": {
      "id": "pi_1234567890",
      "amount": 9000,
      "currency": "usd",
      "metadata": {
        "booking_id": "booking-123"
      }
    }
  }
}
```

## 🧪 Testing

### Authentication Test

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@myhibachi.com", "password": "ChangeThisPassword123!"}'
```

### Create Booking Test

```bash
curl -X POST http://localhost:8000/api/bookings \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "customer": {
      "name": "Test Customer",
      "email": "test@example.com",
      "phone": "+1234567890"
    },
    "event_date": "2024-03-01",
    "event_time": "18:00",
    "guest_count": 4,
    "location": {
      "address": "123 Test St",
      "city": "Sacramento",
      "state": "CA",
      "zip_code": "95814"
    }
  }'
```

## 📞 Support

For API support:

- **Documentation**: This guide and OpenAPI/Swagger docs at `/docs`
- **Health Checks**: Monitor system status via health endpoints
- **Error Logging**: Detailed error information in logs
- **Rate Limiting**: Respect rate limits to avoid throttling

## 🚀 API Versioning

Current version: **v1**

- Base path: `/api/`
- Versioned path: `/api/v1/`
- Backward compatibility maintained for major versions

Your MyHibachi AI Sales CRM API is now fully documented and ready for
integration! 🎉
