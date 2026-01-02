/**
 * Error Codes
 * ===========
 *
 * Descriptive string error codes for the entire application.
 *
 * Design Decision: Using descriptive strings (SLOT_HOLD_EXPIRED)
 * instead of numeric codes for better developer experience and debugging.
 *
 * @module @myhibachi/types/errors
 */

import { z } from 'zod';

// ===========================================================
// SLOT HOLD ERROR CODES
// ===========================================================

export const SLOT_HOLD_ERROR = {
  // Token/Access errors
  INVALID_TOKEN: 'SLOT_HOLD_INVALID_TOKEN',
  TOKEN_EXPIRED: 'SLOT_HOLD_TOKEN_EXPIRED',
  HOLD_NOT_FOUND: 'SLOT_HOLD_NOT_FOUND',

  // Status errors
  ALREADY_SIGNED: 'SLOT_HOLD_ALREADY_SIGNED',
  ALREADY_PAID: 'SLOT_HOLD_ALREADY_PAID',
  ALREADY_EXPIRED: 'SLOT_HOLD_ALREADY_EXPIRED',
  ALREADY_CANCELLED: 'SLOT_HOLD_ALREADY_CANCELLED',
  ALREADY_COMPLETED: 'SLOT_HOLD_ALREADY_COMPLETED',

  // Deadline errors
  SIGNING_DEADLINE_PASSED: 'SLOT_HOLD_SIGNING_DEADLINE_PASSED',
  PAYMENT_DEADLINE_PASSED: 'SLOT_HOLD_PAYMENT_DEADLINE_PASSED',

  // Prerequisite errors
  MUST_SIGN_FIRST: 'SLOT_HOLD_MUST_SIGN_FIRST',
  SLOT_UNAVAILABLE: 'SLOT_HOLD_SLOT_UNAVAILABLE',

  // Validation errors
  INVALID_SIGNATURE: 'SLOT_HOLD_INVALID_SIGNATURE',
  INVALID_PAYMENT_METHOD: 'SLOT_HOLD_INVALID_PAYMENT_METHOD',
  INVALID_PAYMENT_AMOUNT: 'SLOT_HOLD_INVALID_PAYMENT_AMOUNT',
} as const;

export type SlotHoldErrorCode =
  (typeof SLOT_HOLD_ERROR)[keyof typeof SLOT_HOLD_ERROR];

// ===========================================================
// AGREEMENT ERROR CODES
// ===========================================================

export const AGREEMENT_ERROR = {
  // Template errors
  TEMPLATE_NOT_FOUND: 'AGREEMENT_TEMPLATE_NOT_FOUND',
  TEMPLATE_INACTIVE: 'AGREEMENT_TEMPLATE_INACTIVE',
  TEMPLATE_EXPIRED: 'AGREEMENT_TEMPLATE_EXPIRED',

  // Signing errors
  INVALID_SIGNATURE: 'AGREEMENT_INVALID_SIGNATURE',
  SIGNATURE_REQUIRED: 'AGREEMENT_SIGNATURE_REQUIRED',
  CONSENT_REQUIRED: 'AGREEMENT_CONSENT_REQUIRED',
  ALREADY_SIGNED: 'AGREEMENT_ALREADY_SIGNED',

  // Access errors
  AGREEMENT_NOT_FOUND: 'AGREEMENT_NOT_FOUND',
  UNAUTHORIZED: 'AGREEMENT_UNAUTHORIZED',

  // PDF errors
  PDF_GENERATION_FAILED: 'AGREEMENT_PDF_GENERATION_FAILED',
  PDF_NOT_FOUND: 'AGREEMENT_PDF_NOT_FOUND',
} as const;

export type AgreementErrorCode =
  (typeof AGREEMENT_ERROR)[keyof typeof AGREEMENT_ERROR];

// ===========================================================
// BOOKING ERROR CODES
// ===========================================================

export const BOOKING_ERROR = {
  // Not found
  NOT_FOUND: 'BOOKING_NOT_FOUND',
  CUSTOMER_NOT_FOUND: 'BOOKING_CUSTOMER_NOT_FOUND',

  // Status errors
  ALREADY_CANCELLED: 'BOOKING_ALREADY_CANCELLED',
  ALREADY_COMPLETED: 'BOOKING_ALREADY_COMPLETED',
  CANNOT_MODIFY: 'BOOKING_CANNOT_MODIFY',

  // Slot errors
  SLOT_UNAVAILABLE: 'BOOKING_SLOT_UNAVAILABLE',
  SLOT_CONFLICT: 'BOOKING_SLOT_CONFLICT',
  INVALID_DATE: 'BOOKING_INVALID_DATE',
  INVALID_TIME: 'BOOKING_INVALID_TIME',
  TOO_SOON: 'BOOKING_TOO_SOON', // Less than 48 hours advance

  // Guest count errors
  BELOW_MINIMUM: 'BOOKING_BELOW_MINIMUM',
  ABOVE_MAXIMUM: 'BOOKING_ABOVE_MAXIMUM',

  // Payment errors
  DEPOSIT_REQUIRED: 'BOOKING_DEPOSIT_REQUIRED',
  DEPOSIT_INSUFFICIENT: 'BOOKING_DEPOSIT_INSUFFICIENT',
  PAYMENT_FAILED: 'BOOKING_PAYMENT_FAILED',

  // Validation errors
  INVALID_ADDRESS: 'BOOKING_INVALID_ADDRESS',
  INVALID_PHONE: 'BOOKING_INVALID_PHONE',
  INVALID_EMAIL: 'BOOKING_INVALID_EMAIL',
  MISSING_ALLERGEN_DISCLOSURE: 'BOOKING_MISSING_ALLERGEN_DISCLOSURE',
} as const;

export type BookingErrorCode =
  (typeof BOOKING_ERROR)[keyof typeof BOOKING_ERROR];

// ===========================================================
// PAYMENT ERROR CODES
// ===========================================================

export const PAYMENT_ERROR = {
  // General
  PAYMENT_FAILED: 'PAYMENT_FAILED',
  PAYMENT_DECLINED: 'PAYMENT_DECLINED',
  PAYMENT_NOT_FOUND: 'PAYMENT_NOT_FOUND',

  // Stripe
  STRIPE_SESSION_INVALID: 'PAYMENT_STRIPE_SESSION_INVALID',
  STRIPE_SESSION_EXPIRED: 'PAYMENT_STRIPE_SESSION_EXPIRED',
  STRIPE_WEBHOOK_INVALID: 'PAYMENT_STRIPE_WEBHOOK_INVALID',
  STRIPE_SIGNATURE_INVALID: 'PAYMENT_STRIPE_SIGNATURE_INVALID',

  // Verification (Zelle/Venmo)
  VERIFICATION_PENDING: 'PAYMENT_VERIFICATION_PENDING',
  VERIFICATION_FAILED: 'PAYMENT_VERIFICATION_FAILED',
  REFERENCE_INVALID: 'PAYMENT_REFERENCE_INVALID',
  AMOUNT_MISMATCH: 'PAYMENT_AMOUNT_MISMATCH',

  // Refund
  REFUND_FAILED: 'PAYMENT_REFUND_FAILED',
  REFUND_NOT_ALLOWED: 'PAYMENT_REFUND_NOT_ALLOWED',
  REFUND_DEADLINE_PASSED: 'PAYMENT_REFUND_DEADLINE_PASSED',
} as const;

export type PaymentErrorCode =
  (typeof PAYMENT_ERROR)[keyof typeof PAYMENT_ERROR];

// ===========================================================
// AUTH ERROR CODES
// ===========================================================

export const AUTH_ERROR = {
  // Authentication
  INVALID_CREDENTIALS: 'AUTH_INVALID_CREDENTIALS',
  TOKEN_EXPIRED: 'AUTH_TOKEN_EXPIRED',
  TOKEN_INVALID: 'AUTH_TOKEN_INVALID',
  SESSION_EXPIRED: 'AUTH_SESSION_EXPIRED',

  // Authorization
  UNAUTHORIZED: 'AUTH_UNAUTHORIZED',
  FORBIDDEN: 'AUTH_FORBIDDEN',
  INSUFFICIENT_ROLE: 'AUTH_INSUFFICIENT_ROLE',
  INSUFFICIENT_PERMISSIONS: 'AUTH_INSUFFICIENT_PERMISSIONS',

  // Account
  ACCOUNT_DISABLED: 'AUTH_ACCOUNT_DISABLED',
  ACCOUNT_LOCKED: 'AUTH_ACCOUNT_LOCKED',
  EMAIL_NOT_VERIFIED: 'AUTH_EMAIL_NOT_VERIFIED',

  // Rate limiting
  TOO_MANY_ATTEMPTS: 'AUTH_TOO_MANY_ATTEMPTS',
} as const;

export type AuthErrorCode = (typeof AUTH_ERROR)[keyof typeof AUTH_ERROR];

// ===========================================================
// GENERAL API ERROR CODES
// ===========================================================

export const API_ERROR = {
  // Request errors
  VALIDATION_FAILED: 'API_VALIDATION_FAILED',
  INVALID_REQUEST: 'API_INVALID_REQUEST',
  MISSING_REQUIRED_FIELD: 'API_MISSING_REQUIRED_FIELD',

  // Server errors
  INTERNAL_ERROR: 'API_INTERNAL_ERROR',
  SERVICE_UNAVAILABLE: 'API_SERVICE_UNAVAILABLE',
  DATABASE_ERROR: 'API_DATABASE_ERROR',
  EXTERNAL_SERVICE_ERROR: 'API_EXTERNAL_SERVICE_ERROR',

  // Rate limiting
  RATE_LIMIT_EXCEEDED: 'API_RATE_LIMIT_EXCEEDED',
} as const;

export type ApiErrorCode = (typeof API_ERROR)[keyof typeof API_ERROR];

// ===========================================================
// COMBINED ERROR CODE TYPE
// ===========================================================

export type ErrorCode =
  | SlotHoldErrorCode
  | AgreementErrorCode
  | BookingErrorCode
  | PaymentErrorCode
  | AuthErrorCode
  | ApiErrorCode;

// ===========================================================
// ERROR RESPONSE STRUCTURE
// ===========================================================

export interface ApiErrorResponse {
  success: false;
  error: {
    code: ErrorCode;
    message: string;
    details?: Record<string, unknown>;
    field?: string; // For validation errors
    timestamp: string;
    requestId?: string;
  };
}

export const ApiErrorResponseSchema = z.object({
  success: z.literal(false),
  error: z.object({
    code: z.string(),
    message: z.string(),
    details: z.record(z.unknown()).optional(),
    field: z.string().optional(),
    timestamp: z.string().datetime(),
    requestId: z.string().optional(),
  }),
});

// ===========================================================
// ERROR HELPER FUNCTIONS
// ===========================================================

/**
 * Check if an error code belongs to a specific category.
 */
export function isSlotHoldError(code: string): code is SlotHoldErrorCode {
  return code.startsWith('SLOT_HOLD_');
}

export function isAgreementError(code: string): code is AgreementErrorCode {
  return code.startsWith('AGREEMENT_');
}

export function isBookingError(code: string): code is BookingErrorCode {
  return code.startsWith('BOOKING_');
}

export function isPaymentError(code: string): code is PaymentErrorCode {
  return code.startsWith('PAYMENT_');
}

export function isAuthError(code: string): code is AuthErrorCode {
  return code.startsWith('AUTH_');
}

export function isApiError(code: string): code is ApiErrorCode {
  return code.startsWith('API_');
}

// ===========================================================
// HTTP STATUS MAPPING
// ===========================================================

/**
 * Map error codes to appropriate HTTP status codes.
 */
export const ERROR_HTTP_STATUS: Record<string, number> = {
  // 400 Bad Request
  [API_ERROR.VALIDATION_FAILED]: 400,
  [API_ERROR.INVALID_REQUEST]: 400,
  [API_ERROR.MISSING_REQUIRED_FIELD]: 400,
  [SLOT_HOLD_ERROR.INVALID_SIGNATURE]: 400,
  [SLOT_HOLD_ERROR.INVALID_PAYMENT_METHOD]: 400,
  [SLOT_HOLD_ERROR.INVALID_PAYMENT_AMOUNT]: 400,

  // 401 Unauthorized
  [AUTH_ERROR.INVALID_CREDENTIALS]: 401,
  [AUTH_ERROR.TOKEN_EXPIRED]: 401,
  [AUTH_ERROR.TOKEN_INVALID]: 401,
  [AUTH_ERROR.SESSION_EXPIRED]: 401,
  [AUTH_ERROR.UNAUTHORIZED]: 401,

  // 403 Forbidden
  [AUTH_ERROR.FORBIDDEN]: 403,
  [AUTH_ERROR.INSUFFICIENT_ROLE]: 403,
  [AUTH_ERROR.INSUFFICIENT_PERMISSIONS]: 403,
  [AUTH_ERROR.ACCOUNT_DISABLED]: 403,
  [AUTH_ERROR.ACCOUNT_LOCKED]: 403,
  [AGREEMENT_ERROR.UNAUTHORIZED]: 403,

  // 404 Not Found
  [SLOT_HOLD_ERROR.HOLD_NOT_FOUND]: 404,
  [BOOKING_ERROR.NOT_FOUND]: 404,
  [BOOKING_ERROR.CUSTOMER_NOT_FOUND]: 404,
  [AGREEMENT_ERROR.TEMPLATE_NOT_FOUND]: 404,
  [AGREEMENT_ERROR.AGREEMENT_NOT_FOUND]: 404,
  [PAYMENT_ERROR.PAYMENT_NOT_FOUND]: 404,

  // 409 Conflict
  [SLOT_HOLD_ERROR.ALREADY_SIGNED]: 409,
  [SLOT_HOLD_ERROR.ALREADY_PAID]: 409,
  [SLOT_HOLD_ERROR.ALREADY_COMPLETED]: 409,
  [BOOKING_ERROR.SLOT_CONFLICT]: 409,
  [AGREEMENT_ERROR.ALREADY_SIGNED]: 409,

  // 410 Gone
  [SLOT_HOLD_ERROR.TOKEN_EXPIRED]: 410,
  [SLOT_HOLD_ERROR.ALREADY_EXPIRED]: 410,
  [SLOT_HOLD_ERROR.ALREADY_CANCELLED]: 410,
  [SLOT_HOLD_ERROR.SIGNING_DEADLINE_PASSED]: 410,
  [SLOT_HOLD_ERROR.PAYMENT_DEADLINE_PASSED]: 410,

  // 422 Unprocessable Entity
  [SLOT_HOLD_ERROR.MUST_SIGN_FIRST]: 422,
  [SLOT_HOLD_ERROR.SLOT_UNAVAILABLE]: 422,
  [BOOKING_ERROR.BELOW_MINIMUM]: 422,
  [BOOKING_ERROR.ABOVE_MAXIMUM]: 422,
  [BOOKING_ERROR.TOO_SOON]: 422,
  [BOOKING_ERROR.DEPOSIT_REQUIRED]: 422,
  [PAYMENT_ERROR.AMOUNT_MISMATCH]: 422,

  // 429 Too Many Requests
  [AUTH_ERROR.TOO_MANY_ATTEMPTS]: 429,
  [API_ERROR.RATE_LIMIT_EXCEEDED]: 429,

  // 500 Internal Server Error
  [API_ERROR.INTERNAL_ERROR]: 500,
  [API_ERROR.DATABASE_ERROR]: 500,
  [AGREEMENT_ERROR.PDF_GENERATION_FAILED]: 500,

  // 502 Bad Gateway
  [API_ERROR.EXTERNAL_SERVICE_ERROR]: 502,

  // 503 Service Unavailable
  [API_ERROR.SERVICE_UNAVAILABLE]: 503,
};

/**
 * Get HTTP status code for an error code.
 * Defaults to 500 if not mapped.
 */
export function getHttpStatusForError(code: ErrorCode): number {
  return ERROR_HTTP_STATUS[code] ?? 500;
}
