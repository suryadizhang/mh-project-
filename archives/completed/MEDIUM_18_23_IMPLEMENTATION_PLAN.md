# MEDIUM Issues #18-23 Implementation Plan

**Date**: October 19, 2025  
**Status**: 🔄 IN PROGRESS  
**Total Estimated Time**: 14-19 hours  
**Priority**: MEDIUM (Production Readiness & Operational Excellence)

---

## 📋 OVERVIEW

These 6 issues focus on **production readiness**, **security**, **observability**, and **operational excellence**:

| # | Issue | Time | Impact |
|---|-------|------|--------|
| 18 | API Documentation | 2-3h | Developer Experience |
| 19 | Security Headers | 2h | Security Posture |
| 20 | CORS Configuration | 1-2h | API Security |
| 21 | Request Logging | 2-3h | Observability |
| 22 | Error Tracking | 2-3h | Debugging |
| 23 | Performance Monitoring | 3-4h | Operations |

---

## 🎯 MEDIUM #18: API Documentation

**Status**: 🔄 IN PROGRESS  
**Time**: 2-3 hours  
**Files to Update**: ~15 router files

### Phase 1: Bookings API (30 min)

#### File: `apps/backend/src/api/app/routers/bookings.py`

**Current State**: Basic docstrings, no examples, no error documentation

**Updates Needed**:
```python
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional

# 1. Add comprehensive Pydantic schemas
class BookingCreate(BaseModel):
    """Create booking request schema."""
    date: str = Field(..., description="Booking date (YYYY-MM-DD)", example="2024-12-25")
    time: str = Field(..., description="Booking time (HH:MM)", example="18:00")
    guests: int = Field(..., ge=1, le=50, description="Number of guests", example=8)
    location_address: str = Field(..., min_length=10, example="123 Main St, San Jose, CA 95123")
    customer_name: str = Field(..., min_length=2, example="John Doe")
    customer_email: EmailStr = Field(..., example="john@example.com")
    customer_phone: str = Field(..., pattern=r'^\+?1?\d{10,15}$', example="+14155551234")
    special_requests: Optional[str] = Field(None, max_length=500)

class BookingResponse(BaseModel):
    """Booking response schema."""
    id: str = Field(..., description="Booking unique identifier")
    user_id: str
    date: str
    time: str
    guests: int
    status: str = Field(..., description="Booking status", example="confirmed")
    total_amount: float = Field(..., description="Total cost in USD")
    created_at: str

# 2. Add comprehensive endpoint documentation
@router.post(
    "/",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new booking",
    description="""
    Create a new hibachi catering booking.
    
    ## Requirements:
    - Valid authentication token
    - Date must be at least 48 hours in the future
    - Guest count between 1-50
    - Valid US phone number
    
    ## Process:
    1. Validates booking data
    2. Checks availability for date/time
    3. Calculates pricing based on guests and location
    4. Creates booking with 'pending' status
    5. Sends confirmation email
    
    ## Pricing:
    - Base price: $45/adult, $25/child
    - Travel fee: $2/mile beyond 20 miles
    - Deposit: 20% of total
    """,
    responses={
        201: {
            "description": "Booking created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "booking-abc123",
                        "user_id": "user-xyz789",
                        "date": "2024-12-25",
                        "time": "18:00",
                        "guests": 8,
                        "status": "pending",
                        "total_amount": 450.00,
                        "deposit_paid": False,
                        "created_at": "2024-10-19T10:30:00Z"
                    }
                }
            }
        },
        400: {
            "description": "Invalid booking data",
            "content": {
                "application/json": {
                    "examples": {
                        "past_date": {
                            "summary": "Date in the past",
                            "value": {"detail": "Booking date must be at least 48 hours in the future"}
                        },
                        "invalid_guests": {
                            "summary": "Invalid guest count",
                            "value": {"detail": "Guest count must be between 1 and 50"}
                        }
                    }
                }
            }
        },
        401: {
            "description": "Authentication required",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            }
        },
        409: {
            "description": "Time slot not available",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Time slot already booked",
                        "available_times": ["17:00", "19:00", "20:00"]
                    }
                }
            }
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "customer_email"],
                                "msg": "value is not a valid email address",
                                "type": "value_error.email"
                            }
                        ]
                    }
                }
            }
        }
    },
    tags=["bookings"]
)
async def create_booking(
    booking_data: BookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> BookingResponse:
    """
    Create a new hibachi catering booking.
    
    Args:
        booking_data: Booking details including date, time, location, guest count
        db: Database session
        current_user: Authenticated user from JWT token
        
    Returns:
        Created booking with assigned ID and calculated pricing
        
    Raises:
        HTTPException(400): Invalid booking data (past date, invalid guests, etc.)
        HTTPException(401): User not authenticated
        HTTPException(409): Time slot already booked
        HTTPException(422): Validation error in request data
        
    Example:
        ```python
        # Request
        POST /api/v1/bookings
        Authorization: Bearer eyJhbGc...
        {
            "date": "2024-12-25",
            "time": "18:00",
            "guests": 8,
            "location_address": "123 Main St, San Jose, CA 95123",
            "customer_name": "John Doe",
            "customer_email": "john@example.com",
            "customer_phone": "+14155551234",
            "special_requests": "Vegetarian option for 2 guests"
        }
        
        # Response (201 Created)
        {
            "id": "booking-abc123",
            "user_id": "user-xyz789",
            "date": "2024-12-25",
            "time": "18:00",
            "guests": 8,
            "status": "pending",
            "total_amount": 450.00,
            "deposit_paid": false,
            "created_at": "2024-10-19T10:30:00Z"
        }
        ```
    """
    # Implementation...
    pass
```

### Phase 2: Auth API (20 min)

#### File: `apps/backend/src/api/app/routers/auth.py`

**Add documentation for**:
- `/login` - User authentication
- `/register` - New user registration
- `/refresh` - Token refresh
- `/logout` - Session termination
- `/reset-password` - Password reset

### Phase 3: Stripe/Payments API (20 min)

#### File: `apps/backend/src/api/app/routers/stripe.py`

**Add documentation for**:
- `/create-payment-intent` - Initialize payment
- `/confirm-payment` - Confirm payment
- `/refund` - Process refund
- `/webhook` - Stripe webhook handler

### Phase 4: Webhooks API (15 min)

#### Files: 
- `apps/backend/src/api/app/routers/webhooks.py`
- `apps/backend/src/api/app/routers/ringcentral_webhooks.py`

### Phase 5: Health & Monitoring (15 min)

#### File: `apps/backend/src/api/app/routers/health.py`

### Phase 6: OpenAPI Configuration (30 min)

#### File: `apps/backend/src/api/app/openapi_config.py`

**Update OpenAPI metadata**:
```python
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="MyHibachi Catering API",
        version="1.0.0",
        description="""
        # MyHibachi Catering API
        
        ## Overview
        RESTful API for hibachi catering booking platform.
        
        ## Authentication
        All endpoints require JWT bearer token:
        ```
        Authorization: Bearer <your_token_here>
        ```
        
        Get token from `/api/v1/auth/login` endpoint.
        
        ## Rate Limits
        - 100 requests/minute per IP
        - 1000 requests/hour per user
        
        ## Error Codes
        - 400: Bad Request - Invalid input data
        - 401: Unauthorized - Missing or invalid authentication
        - 403: Forbidden - Insufficient permissions
        - 404: Not Found - Resource doesn't exist
        - 409: Conflict - Resource conflict (e.g., time slot taken)
        - 422: Validation Error - Request validation failed
        - 429: Too Many Requests - Rate limit exceeded
        - 500: Internal Server Error - Server error
        
        ## Support
        - Email: dev@myhibachi.com
        - Docs: https://docs.myhibachi.com
        """,
        routes=app.routes,
        contact={
            "name": "MyHibachi API Support",
            "email": "dev@myhibachi.com",
            "url": "https://myhibachi.com/support"
        },
        license_info={
            "name": "Proprietary",
            "url": "https://myhibachi.com/license"
        },
        servers=[
            {
                "url": "https://api.myhibachi.com",
                "description": "Production server"
            },
            {
                "url": "https://staging-api.myhibachi.com",
                "description": "Staging server"
            },
            {
                "url": "http://localhost:8000",
                "description": "Development server"
            }
        ],
        tags=[
            {
                "name": "auth",
                "description": "Authentication and authorization operations"
            },
            {
                "name": "bookings",
                "description": "Booking management operations"
            },
            {
                "name": "payments",
                "description": "Payment processing via Stripe"
            },
            {
                "name": "webhooks",
                "description": "External service webhooks"
            },
            {
                "name": "health",
                "description": "Health check and monitoring endpoints"
            }
        ]
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token"
        }
    }
    
    # Apply security globally
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

---

## 🎯 MEDIUM #19: Security Headers

**Status**: ⏳ NOT STARTED  
**Time**: 2 hours  
**Target**: A+ rating on securityheaders.com

### Phase 1: Customer App Security Headers (45 min)

#### File: `apps/customer/next.config.ts`

```typescript
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // ... existing config ...
  
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-eval' 'unsafe-inline' https://www.googletagmanager.com https://www.google-analytics.com https://js.stripe.com",
              "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
              "font-src 'self' https://fonts.gstatic.com",
              "img-src 'self' data: https: blob:",
              "connect-src 'self' https://api.myhibachi.com https://api.stripe.com https://www.google-analytics.com",
              "frame-src 'self' https://js.stripe.com https://www.google.com",
              "object-src 'none'",
              "base-uri 'self'",
              "form-action 'self'",
              "frame-ancestors 'none'",
              "upgrade-insecure-requests"
            ].join('; ')
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=31536000; includeSubDomains; preload'
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block'
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin'
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=(self), interest-cohort=()'
          }
        ],
      },
      // Static assets caching
      {
        source: '/_next/static/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      {
        source: '/images/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
    ];
  },
};

export default nextConfig;
```

### Phase 2: Admin App Security Headers (30 min)

Same implementation for `apps/admin/next.config.ts`

### Phase 3: Backend Security Middleware (45 min)

#### File: `apps/backend/src/api/app/middleware/security.py`

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        response = await call_next(request)
        
        # HSTS
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )
        
        # CSP for API (restrictive)
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; "
            "frame-ancestors 'none'; "
            "base-uri 'none'"
        )
        
        return response

# Register in main.py
from api.app.middleware.security import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)
```

---

## 🎯 MEDIUM #20: CORS Configuration

**Status**: ⏳ NOT STARTED  
**Time**: 1-2 hours

### Implementation

#### File: `apps/backend/src/api/app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings

app = FastAPI()

# Configure CORS
origins = [
    "http://localhost:3000",  # Customer app dev
    "http://localhost:3001",  # Admin app dev
    "https://myhibachi.com",  # Production customer
    "https://www.myhibachi.com",
    "https://admin.myhibachi.com",  # Production admin
    "https://staging.myhibachi.com",  # Staging
    "https://staging-admin.myhibachi.com"
]

# Add additional origins from environment
if settings.ADDITIONAL_CORS_ORIGINS:
    origins.extend(settings.ADDITIONAL_CORS_ORIGINS.split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Type",
        "Authorization",
        "X-Request-ID",
        "X-CSRF-Token"
    ],
    expose_headers=[
        "X-Request-ID",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset"
    ],
    max_age=3600,  # Cache preflight for 1 hour
)
```

#### File: `apps/backend/src/core/config.py`

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # CORS
    ADDITIONAL_CORS_ORIGINS: str = Field(
        default="",
        description="Comma-separated additional CORS origins"
    )
    
    # Environment
    ENVIRONMENT: str = Field(
        default="development",
        description="Environment: development, staging, production"
    )
```

---

## 🎯 MEDIUM #21: Request Logging

**Status**: ⏳ NOT STARTED  
**Time**: 2-3 hours

### Implementation

#### File: `apps/backend/src/api/app/middleware/logging_middleware.py`

```python
import logging
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable
import json

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests with structured logging."""
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        # Generate or extract request ID
        request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timer
        start_time = time.time()
        
        # Extract user info (if authenticated)
        user_id = None
        if hasattr(request.state, 'user'):
            user_id = request.state.user.get('id')
        
        # Log request
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "user_id": user_id,
                "client_ip": request.client.host,
                "user_agent": request.headers.get('user-agent'),
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log error
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration * 1000, 2),
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Add headers to response
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        
        # Log response
        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "user_id": user_id
            }
        )
        
        return response
```

#### File: `apps/backend/src/core/logging_config.py`

```python
import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logging():
    """Configure structured JSON logging."""
    
    # Create JSON formatter
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s',
        rename_fields={
            'asctime': 'timestamp',
            'name': 'logger',
            'levelname': 'level'
        }
    )
    
    # Configure root logger
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    
    # Set library log levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
```

---

## 🎯 MEDIUM #22: Error Tracking Integration

**Status**: ⏳ NOT STARTED  
**Time**: 2-3 hours

### Implementation (Sentry)

#### File: `apps/backend/src/api/app/main.py`

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from core.config import settings

# Initialize Sentry
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        before_send=filter_sensitive_data,
        release=settings.APP_VERSION,
    )

def filter_sensitive_data(event, hint):
    """Remove sensitive data from error reports."""
    # Remove passwords
    if 'request' in event:
        if 'data' in event['request']:
            data = event['request']['data']
            if isinstance(data, dict):
                for key in ['password', 'token', 'secret', 'api_key']:
                    if key in data:
                        data[key] = '[REDACTED]'
    
    return event
```

#### File: `apps/customer/src/app/layout.tsx`

```typescript
import * as Sentry from "@sentry/nextjs";

if (process.env.NEXT_PUBLIC_SENTRY_DSN) {
  Sentry.init({
    dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
    environment: process.env.NODE_ENV,
    tracesSampleRate: 0.1,
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
    beforeSend(event, hint) {
      // Filter PII
      if (event.user) {
        delete event.user.email;
        delete event.user.ip_address;
      }
      return event;
    },
  });
}
```

---

## 🎯 MEDIUM #23: Performance Monitoring

**Status**: ⏳ NOT STARTED  
**Time**: 3-4 hours

### Implementation

#### File: `apps/backend/src/api/app/middleware/metrics.py`

```python
from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'http_requests_active',
    'Active HTTP requests'
)

DB_QUERY_DURATION = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['query_type']
)

CACHE_HITS = Counter(
    'cache_hits_total',
    'Cache hits',
    ['cache_name']
)

CACHE_MISSES = Counter(
    'cache_misses_total',
    'Cache misses',
    ['cache_name']
)
```

---

## 📊 IMPLEMENTATION SCHEDULE

### Day 1 (Today - 4 hours)
- ✅ Create implementation plan
- 🔄 MEDIUM #18: API Documentation (2-3h)
  - Bookings API
  - Auth API
  - OpenAPI config

### Day 2 (4 hours)
- MEDIUM #18: Complete remaining APIs
- MEDIUM #19: Security Headers (2h)

### Day 3 (3 hours)
- MEDIUM #20: CORS Configuration (1-2h)
- MEDIUM #21: Start Request Logging

### Day 4 (4 hours)
- MEDIUM #21: Complete Request Logging
- MEDIUM #22: Error Tracking Integration (2-3h)

### Day 5 (4 hours)
- MEDIUM #23: Performance Monitoring (3-4h)
- Testing & documentation

**Total**: ~19 hours over 5 days

---

## ✅ SUCCESS CRITERIA

- [ ] All API endpoints have comprehensive documentation
- [ ] Swagger UI shows examples for all endpoints
- [ ] Security headers get A+ rating on securityheaders.com
- [ ] CORS properly configured for all environments
- [ ] All requests logged with structured JSON format
- [ ] Sentry integrated and capturing errors
- [ ] Prometheus metrics exposed at `/metrics`
- [ ] All changes committed and pushed
- [ ] Documentation updated

---

**Next Action**: Start implementing MEDIUM #18 - API Documentation for bookings.py
