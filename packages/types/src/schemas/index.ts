/**
 * API Response Validation Schemas
 * 
 * This module exports all Zod schemas for validating API responses
 * across the MyHibachi application. These schemas provide runtime
 * validation and TypeScript type safety for all API endpoints.
 * 
 * @module @myhibachi/types/schemas
 * 
 * @example
 * // Import specific schemas
 * import { BookedDatesResponseSchema, PaymentIntentResponseSchema } from '@myhibachi/types/schemas';
 * 
 * // Import grouped schemas
 * import { BookingResponseSchemas, PaymentResponseSchemas } from '@myhibachi/types/schemas';
 * 
 * // Validate a response
 * const result = BookedDatesResponseSchema.safeParse(apiResponse);
 * if (result.success) {
 *   console.log('Valid response:', result.data);
 * } else {
 *   console.error('Validation error:', result.error);
 * }
 */

// Export all booking response schemas
export {
  BookedDatesResponseSchema,
  AvailabilityResponseSchema,
  AvailableTimesResponseSchema,
  BookingSubmitResponseSchema,
  BookingListResponseSchema,
  BookingDetailResponseSchema,
  BookingResponseSchemas,
  type BookedDatesResponse,
  type AvailabilityResponse,
  type AvailableTimesResponse,
  type BookingSubmitResponse,
  type BookingListResponse,
  type BookingDetailResponse,
} from './booking-responses';

// Export all payment response schemas
export {
  PaymentIntentResponseSchema,
  CheckoutSessionResponseSchema,
  CheckoutSessionVerifyResponseSchema,
  PaymentResponseSchemas,
  type PaymentIntentResponse,
  type CheckoutSessionResponse,
  type CheckoutSessionVerifyResponse,
} from './payment-responses';

// Export all customer response schemas
export {
  CustomerDashboardResponseSchema,
  CustomerResponseSchemas,
  type CustomerDashboardResponse,
} from './customer-responses';

// Export all common response schemas
export {
  BaseResponseSchema,
  ApiResponseSchema,
  ErrorResponseSchema,
  PaginatedResponseSchema,
  SuccessResponseSchema,
  EmptyResponseSchema,
  MetadataSchema,
  ResponseWithMetadataSchema,
  ValidationErrorResponseSchema,
  CommonResponseSchemas,
  type BaseResponse,
  type ErrorResponse,
  type SuccessResponse,
  type EmptyResponse,
  type Metadata,
  type ValidationErrorResponse,
} from './common';

/**
 * All Response Schemas
 * Grouped by category for easy access
 */
export const AllResponseSchemas = {
  Booking: {
    BookedDates: 'BookedDatesResponseSchema',
    Availability: 'AvailabilityResponseSchema',
    AvailableTimes: 'AvailableTimesResponseSchema',
    BookingSubmit: 'BookingSubmitResponseSchema',
    BookingList: 'BookingListResponseSchema',
    BookingDetail: 'BookingDetailResponseSchema',
  },
  Payment: {
    PaymentIntent: 'PaymentIntentResponseSchema',
    CheckoutSession: 'CheckoutSessionResponseSchema',
    CheckoutSessionVerify: 'CheckoutSessionVerifyResponseSchema',
  },
  Customer: {
    Dashboard: 'CustomerDashboardResponseSchema',
  },
  Common: {
    Base: 'BaseResponseSchema',
    ApiResponse: 'ApiResponseSchema',
    Error: 'ErrorResponseSchema',
    Paginated: 'PaginatedResponseSchema',
    Success: 'SuccessResponseSchema',
    Empty: 'EmptyResponseSchema',
    Metadata: 'MetadataSchema',
    ResponseWithMetadata: 'ResponseWithMetadataSchema',
    ValidationError: 'ValidationErrorResponseSchema',
  },
} as const;

/**
 * Schema Registry
 * Maps endpoint paths to their corresponding schemas
 * Useful for dynamic validation based on API endpoint
 */
export const SCHEMA_REGISTRY = {
  // Booking endpoints
  'GET /api/v1/bookings/booked-dates': 'BookedDatesResponseSchema',
  'GET /api/v1/bookings/availability': 'AvailabilityResponseSchema',
  'GET /api/v1/bookings/available-times': 'AvailableTimesResponseSchema',
  'POST /api/v1/bookings/submit': 'BookingSubmitResponseSchema',
  'GET /api/v1/bookings': 'BookingListResponseSchema',
  'GET /api/v1/bookings/:id': 'BookingDetailResponseSchema',
  
  // Payment endpoints
  'POST /api/v1/payments/create-intent': 'PaymentIntentResponseSchema',
  'POST /create-checkout-session': 'CheckoutSessionResponseSchema',
  'POST /api/v1/payments/checkout-session': 'CheckoutSessionVerifyResponseSchema',
  
  // Customer endpoints
  'GET /api/v1/customers/dashboard': 'CustomerDashboardResponseSchema',
} as const;

/**
 * Quick reference table for schema usage
 * 
 * | Endpoint | Schema | Usage |
 * |----------|--------|-------|
 * | GET /api/v1/bookings/booked-dates | BookedDatesResponseSchema | useBooking, BookingFormContainer, BookUs/page |
 * | GET /api/v1/bookings/availability | AvailabilityResponseSchema | useBooking, BookUs/page |
 * | GET /api/v1/bookings/available-times | AvailableTimesResponseSchema | BookingFormContainer, BookUsPageClient |
 * | POST /api/v1/bookings/submit | BookingSubmitResponseSchema | BookingFormContainer, BookUsPageClient |
 * | GET /api/v1/bookings | BookingListResponseSchema | BookingForm (future) |
 * | GET /api/v1/bookings/:id | BookingDetailResponseSchema | Booking detail pages (future) |
 * | POST /api/v1/payments/create-intent | PaymentIntentResponseSchema | payment/page |
 * | POST /create-checkout-session | CheckoutSessionResponseSchema | checkout/page |
 * | POST /api/v1/payments/checkout-session | CheckoutSessionVerifyResponseSchema | checkout/page, checkout/success/page (⚠️ NOT IMPLEMENTED) |
 * | GET /api/v1/customers/dashboard | CustomerDashboardResponseSchema | CustomerSavingsDisplay |
 */
