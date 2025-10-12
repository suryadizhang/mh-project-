# API Response Validation - Research & Analysis

**Issue**: HIGH PRIORITY #13 - API Response Validation  
**Date**: October 12, 2025  
**Status**: Research Phase Complete  

---

## Executive Summary

### Current State
- ✅ Zod 4.1.11 **already installed**
- ✅ Basic schemas exist in `packages/types/src/index.ts`
- ❌ No runtime validation on API responses
- ❌ Type safety only at compile time (TypeScript)
- ❌ No protection against malformed server responses
- ❌ No validation error handling in components

### Identified Pain Points
1. **Runtime Type Mismatch**: Server returns unexpected data shape → runtime errors
2. **Missing Fields**: Optional fields not handled gracefully → undefined errors
3. **Type Coercion**: Dates as strings, numbers as strings → parsing failures
4. **Error Handling**: Generic error messages, no validation feedback
5. **No Fail-Safe**: Malformed responses crash components instead of degrading gracefully

---

## 📊 API Endpoint Inventory

### Analyzed Endpoints (27 API calls found)

#### **Booking Endpoints (12 calls)**
| Endpoint | Method | Usage | Current Type | Needs Schema |
|----------|--------|-------|--------------|--------------|
| `/api/v1/bookings/booked-dates` | GET | Fetch unavailable dates | `any` | ✅ Yes |
| `/api/v1/bookings/availability` | GET | Check date availability | `any` | ✅ Yes |
| `/api/v1/bookings/available-times` | GET | Get time slots | `any` | ✅ Yes |
| `/api/v1/bookings/submit` | POST | Create booking | `ApiResponse` | ✅ Yes |
| `/api/v1/bookings` | POST | Create booking (alt) | `ApiResponse` | ✅ Yes |

**Files Using Booking APIs:**
- `apps/customer/src/hooks/booking/useBooking.ts`
- `apps/customer/src/components/booking/BookingFormContainer.tsx`
- `apps/customer/src/components/booking/BookingForm.tsx`
- `apps/customer/src/app/BookUs/BookUsPageClient.tsx`
- `apps/customer/src/app/BookUs/page.tsx`

#### **Payment Endpoints (5 calls)**
| Endpoint | Method | Usage | Current Type | Needs Schema |
|----------|--------|-------|--------------|--------------|
| `/api/v1/payments/create-intent` | POST | Stripe payment intent | `any` | ✅ Yes |
| `/api/v1/payments/checkout-session` | POST | Create checkout | `any` | ✅ Yes |
| `/api/v1/payments/checkout-session` | GET | Verify session | `any` | ✅ Yes |
| `/api/v1/payments/alternative-payment` | POST | Alternative payment | `any` | ✅ Yes |

**Files Using Payment APIs:**
- `apps/customer/src/app/payment/page.tsx`
- `apps/customer/src/app/checkout/page.tsx`
- `apps/customer/src/app/checkout/success/page.tsx`
- `apps/customer/src/components/payment/AlternativePaymentOptions.tsx`

#### **Dashboard/Customer Endpoints (1 call)**
| Endpoint | Method | Usage | Current Type | Needs Schema |
|----------|--------|-------|--------------|--------------|
| `/api/v1/customers/dashboard` | GET | Customer stats | `any` | ✅ Yes |

**Files Using Customer APIs:**
- `apps/customer/src/components/CustomerSavingsDisplay.tsx`

---

## 🔍 Existing Type Definitions

### In `packages/types/src/index.ts`

**Interfaces:**
- `User` - User account data
- `Booking` - Booking entity
- `MenuItem` - Menu item entity
- `BookingLocation` - Location data
- `PaymentInfo` - Payment details
- `ApiResponse<T>` - Generic API response wrapper
- `PaginatedResponse<T>` - Paginated list wrapper

**Zod Schemas (Already Defined):**
- `UserSchema` ✅
- `BookingSchema` ✅
- `BookingLocationSchema` ✅
- `MenuItemSchema` ✅
- `PaymentInfoSchema` ✅

**Missing Schemas:**
- Response wrappers (ApiResponse with Zod)
- Booking availability response
- Booked dates response
- Available times response
- Payment intent response (Stripe-specific)
- Checkout session response
- Dashboard stats response

---

## 🎯 Implementation Strategy

### Phase 1: Create Response Schemas (High Priority)

#### 1.1 Booking Response Schemas
```typescript
// packages/types/src/schemas/booking-responses.ts

// GET /api/v1/bookings/booked-dates
export const BookedDatesResponseSchema = z.object({
  success: z.boolean(),
  data: z.object({
    dates: z.array(z.string().regex(/^\d{4}-\d{2}-\d{2}$/)), // YYYY-MM-DD format
    count: z.number().int().nonnegative(),
  }),
  timestamp: z.string().datetime(),
  requestId: z.string().uuid(),
});

// GET /api/v1/bookings/availability?date=YYYY-MM-DD
export const AvailabilityResponseSchema = z.object({
  success: z.boolean(),
  data: z.object({
    date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
    available: z.boolean(),
    reason: z.string().optional(),
    availableSlots: z.number().int().nonnegative().optional(),
  }),
  timestamp: z.string().datetime(),
  requestId: z.string().uuid(),
});

// GET /api/v1/bookings/available-times?date=YYYY-MM-DD
export const AvailableTimesResponseSchema = z.object({
  success: z.boolean(),
  data: z.object({
    date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
    times: z.array(
      z.object({
        time: z.string().regex(/^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/),
        available: z.boolean(),
        booked: z.boolean(),
      })
    ),
  }),
  timestamp: z.string().datetime(),
  requestId: z.string().uuid(),
});

// POST /api/v1/bookings/submit
export const BookingSubmitResponseSchema = z.object({
  success: z.boolean(),
  data: z.object({
    bookingId: z.string().uuid(),
    status: z.enum(['pending', 'confirmed']),
    booking: BookingSchema,
  }),
  message: z.string().optional(),
  timestamp: z.string().datetime(),
  requestId: z.string().uuid(),
});
```

#### 1.2 Payment Response Schemas
```typescript
// packages/types/src/schemas/payment-responses.ts

// POST /api/v1/payments/create-intent
export const PaymentIntentResponseSchema = z.object({
  success: z.boolean(),
  data: z.object({
    clientSecret: z.string(),
    publishableKey: z.string(),
    amount: z.number().positive(),
    currency: z.string().length(3), // USD, EUR, etc.
  }),
  timestamp: z.string().datetime(),
  requestId: z.string().uuid(),
});

// POST /api/v1/payments/checkout-session
export const CheckoutSessionResponseSchema = z.object({
  success: z.boolean(),
  data: z.object({
    sessionId: z.string(),
    sessionUrl: z.string().url(),
    expiresAt: z.string().datetime(),
  }),
  timestamp: z.string().datetime(),
  requestId: z.string().uuid(),
});

// GET /api/v1/payments/checkout-session?session_id=xxx
export const CheckoutSessionVerifyResponseSchema = z.object({
  success: z.boolean(),
  data: z.object({
    sessionId: z.string(),
    paymentStatus: z.enum(['paid', 'unpaid', 'no_payment_required']),
    customerEmail: z.string().email().optional(),
    amountTotal: z.number().nonnegative(),
    currency: z.string().length(3),
  }),
  timestamp: z.string().datetime(),
  requestId: z.string().uuid(),
});

// POST /api/v1/payments/alternative-payment
export const AlternativePaymentResponseSchema = z.object({
  success: z.boolean(),
  data: z.object({
    paymentId: z.string().uuid(),
    method: z.enum(['zelle', 'venmo']),
    status: z.enum(['pending', 'completed']),
    instructions: z.string(),
    qrCode: z.string().url().optional(),
  }),
  message: z.string().optional(),
  timestamp: z.string().datetime(),
  requestId: z.string().uuid(),
});
```

#### 1.3 Customer Response Schemas
```typescript
// packages/types/src/schemas/customer-responses.ts

// GET /api/v1/customers/dashboard
export const CustomerDashboardResponseSchema = z.object({
  success: z.boolean(),
  data: z.object({
    totalBookings: z.number().int().nonnegative(),
    completedBookings: z.number().int().nonnegative(),
    upcomingBookings: z.number().int().nonnegative(),
    totalSpent: z.number().nonnegative(),
    averageBookingValue: z.number().nonnegative(),
    lastBookingDate: z.string().datetime().optional(),
    loyaltyPoints: z.number().int().nonnegative().optional(),
  }),
  timestamp: z.string().datetime(),
  requestId: z.string().uuid(),
});
```

### Phase 2: Create Validation Utilities

#### 2.1 Validation Helper Functions
```typescript
// packages/types/src/validators/index.ts

import { ZodSchema, ZodError } from 'zod';
import { logger } from '@/lib/logger'; // Assuming logger exists

export interface ValidationResult<T> {
  success: boolean;
  data?: T;
  error?: string;
  zodError?: ZodError;
}

/**
 * Validate API response data against a Zod schema
 * Returns validated, type-safe data or error details
 */
export function validateResponse<T>(
  schema: ZodSchema<T>,
  data: unknown,
  context?: string
): ValidationResult<T> {
  try {
    const validated = schema.parse(data);
    return {
      success: true,
      data: validated,
    };
  } catch (error) {
    if (error instanceof ZodError) {
      const errorMessage = formatZodError(error);
      
      logger.error('API response validation failed', {
        context: context || 'unknown',
        error: errorMessage,
        zodIssues: error.issues,
        receivedData: JSON.stringify(data).substring(0, 500), // Truncate large data
      });

      return {
        success: false,
        error: errorMessage,
        zodError: error,
      };
    }

    // Non-Zod error (shouldn't happen, but handle it)
    logger.error('Unexpected validation error', {
      context: context || 'unknown',
      error: String(error),
    });

    return {
      success: false,
      error: 'Unexpected validation error',
    };
  }
}

/**
 * Format Zod error for user-friendly display
 */
function formatZodError(error: ZodError): string {
  const issues = error.issues.map((issue) => {
    const path = issue.path.join('.');
    return `${path}: ${issue.message}`;
  });

  if (issues.length === 1) {
    return issues[0];
  }

  return `Multiple validation errors:\n${issues.join('\n')}`;
}

/**
 * Safe parse with detailed logging
 * Use for debugging or development environments
 */
export function safeValidateResponse<T>(
  schema: ZodSchema<T>,
  data: unknown,
  context?: string
): T | null {
  const result = validateResponse(schema, data, context);
  
  if (result.success && result.data) {
    return result.data;
  }

  // Return null on error (graceful degradation)
  return null;
}

/**
 * Validate array of items
 */
export function validateArray<T>(
  itemSchema: ZodSchema<T>,
  data: unknown,
  context?: string
): ValidationResult<T[]> {
  if (!Array.isArray(data)) {
    return {
      success: false,
      error: 'Expected an array',
    };
  }

  const validated: T[] = [];
  const errors: string[] = [];

  data.forEach((item, index) => {
    const result = validateResponse(itemSchema, item, `${context}[${index}]`);
    if (result.success && result.data) {
      validated.push(result.data);
    } else {
      errors.push(`Item ${index}: ${result.error}`);
    }
  });

  if (errors.length > 0) {
    return {
      success: false,
      error: errors.join('; '),
    };
  }

  return {
    success: true,
    data: validated,
  };
}
```

### Phase 3: Integrate into API Client

#### 3.1 Enhanced apiFetch Function
```typescript
// apps/customer/src/lib/api.ts

import { ZodSchema } from 'zod';
import { validateResponse } from '@myhibachi/types/validators';

export interface ApiRequestOptions extends RequestInit {
  timeout?: number;
  retry?: boolean;
  maxRetries?: number;
  retryDelay?: number;
  schema?: ZodSchema; // NEW: Optional validation schema
}

export async function apiFetch<T = unknown>(
  path: string,
  options: ApiRequestOptions = {}
): Promise<ApiResponse<T>> {
  const {
    timeout,
    retry = false,
    maxRetries = 3,
    retryDelay = 1000,
    schema, // NEW: Extract schema
    ...fetchOptions
  } = options;

  // ... existing rate limiting, timeout, fetch logic ...

  // After successful response parsing
  const data = await response.json();

  // NEW: Validate response if schema provided
  if (schema) {
    const validation = validateResponse(schema, data, path);
    
    if (!validation.success) {
      logger.error('API response validation failed', {
        path,
        error: validation.error,
        zodError: validation.zodError,
      });

      // Emit validation error event for monitoring
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('api-validation-error', {
          detail: {
            endpoint: path,
            error: validation.error,
          },
        }));
      }

      return {
        error: 'Invalid response format from server. Please try again.',
        success: false,
      };
    }

    // Return validated, type-safe data
    return {
      data: validation.data as T,
      success: true,
    };
  }

  // Fallback: Return unvalidated data (backward compatible)
  return {
    data: data as T,
    success: true,
  };
}
```

### Phase 4: Update Component Usage

#### 4.1 Example: Booking Component
```typescript
// apps/customer/src/components/booking/BookingFormContainer.tsx

import { apiFetch } from '@/lib/api';
import {
  BookedDatesResponseSchema,
  AvailableTimesResponseSchema,
  BookingSubmitResponseSchema,
} from '@myhibachi/types/schemas/booking-responses';
import type { z } from 'zod';

// Type-safe response types
type BookedDatesResponse = z.infer<typeof BookedDatesResponseSchema>;
type AvailableTimesResponse = z.infer<typeof AvailableTimesResponseSchema>;
type BookingSubmitResponse = z.infer<typeof BookingSubmitResponseSchema>;

// Usage
const result = await apiFetch<BookedDatesResponse>(
  '/api/v1/bookings/booked-dates',
  {
    schema: BookedDatesResponseSchema, // Validate response
  }
);

if (result.success && result.data) {
  // result.data is type-safe and validated!
  const dates = result.data.data.dates;
  setBookedDates(dates);
} else {
  // Handle validation error gracefully
  setError(result.error || 'Failed to fetch booked dates');
}
```

---

## 📁 Proposed File Structure

```
packages/
└── types/
    ├── src/
    │   ├── index.ts                  (existing - main exports)
    │   ├── schemas/
    │   │   ├── index.ts              (NEW - re-export all schemas)
    │   │   ├── booking-responses.ts  (NEW - booking API schemas)
    │   │   ├── payment-responses.ts  (NEW - payment API schemas)
    │   │   ├── customer-responses.ts (NEW - customer API schemas)
    │   │   └── common.ts             (NEW - shared schemas)
    │   └── validators/
    │       ├── index.ts              (NEW - validation utilities)
    │       └── error-formatter.ts    (NEW - error formatting)
    └── package.json
```

---

## 🎯 Migration Plan

### Step 1: Create Schemas (No Breaking Changes)
- Create all response schemas in packages/types
- Export from index.ts
- No changes to existing code yet

### Step 2: Add Optional Schema Parameter (Backward Compatible)
- Enhance apiFetch to accept optional schema parameter
- If no schema provided, works exactly as before
- Zero breaking changes

### Step 3: Migrate Components Incrementally
- Start with high-traffic endpoints (booking, payment)
- Add schema validation one component at a time
- Test thoroughly after each migration
- Monitor for validation errors in production

### Step 4: Make Validation Required (Future)
- After all components migrated and tested
- Change schema parameter from optional to required
- Remove fallback unvalidated path
- Full type safety enforced

---

## 🚨 Risk Mitigation

### Potential Issues

1. **Schema Mismatch with Backend**
   - **Risk**: Backend changes response format
   - **Mitigation**: Version API responses, add backward compatibility
   - **Fallback**: Log error but allow through (graceful degradation)

2. **Performance Impact**
   - **Risk**: Zod validation adds latency
   - **Mitigation**: Zod is very fast (<1ms for typical responses)
   - **Monitoring**: Track validation time in logs

3. **Over-Strict Validation**
   - **Risk**: Schema too strict, blocks valid data
   - **Mitigation**: Use .optional() liberally, allow unknown keys
   - **Solution**: Start with loose schemas, tighten over time

4. **Breaking Changes During Migration**
   - **Risk**: Existing code breaks when adding validation
   - **Mitigation**: Schema parameter is optional (backward compatible)
   - **Testing**: Extensive testing before production

---

## ✅ Success Criteria

### Must-Have
- ✅ All 27 API calls have defined schemas
- ✅ API client enhanced with optional validation
- ✅ Zero breaking changes (backward compatible)
- ✅ TypeScript compiles with 0 errors
- ✅ Comprehensive documentation

### Nice-to-Have
- ✅ Validation error monitoring/analytics
- ✅ Auto-generated TypeScript types from schemas
- ✅ Developer-friendly error messages
- ✅ Performance benchmarks (<5ms validation time)

---

## 📊 Estimated Impact

### Bundle Size
- Zod already installed: 0 KB additional
- New schemas: ~5-10 KB (minified + gzipped)
- Validators: ~2-3 KB (minified + gzipped)
- **Total**: ~7-13 KB increase (acceptable)

### Performance
- Validation time: <1ms per response (typical)
- Network overhead: 0 (client-side only)
- CPU impact: Negligible (<0.1% CPU)

### Development Experience
- **Improved**: Type-safe API responses (autocomplete, intellisense)
- **Improved**: Catch errors at runtime (not just compile time)
- **Improved**: Better error messages for debugging
- **Cost**: Slightly more verbose code (adding schema parameter)

---

## 🏁 Next Steps

1. ✅ **Research Complete** (this document)
2. ⏳ Install/verify Zod (already done - v4.1.11)
3. ⏳ Create schema architecture
4. ⏳ Implement booking response schemas
5. ⏳ Implement payment response schemas
6. ⏳ Implement customer response schemas
7. ⏳ Create validation utilities
8. ⏳ Enhance API client with validation
9. ⏳ Migrate booking components
10. ⏳ Migrate payment components
11. ⏳ Documentation & testing
12. ⏳ Commit & push

---

**Status**: ✅ Research Phase Complete  
**Next**: Create Schema Architecture  
**Estimated Total Time**: 14 hours (as planned)  
**Risk Level**: Low (backward compatible approach)
