import { z } from 'zod';

/**
 * ============================================================================
 * Common Response Schemas for My Hibachi Chef API
 * ============================================================================
 * 
 * IMPORTANT: This file defines GENERIC response structures, but most current
 * endpoints use DIRECT DATA formats without wrappers.
 * 
 * CURRENT BACKEND PATTERNS:
 * 
 * 1. DIRECT DATA (Most Common):
 *    - Booking endpoints: Return arrays/objects directly
 *      Example: [{ id: "123", date: "2025-01-01", ... }]
 *    
 *    - Payment endpoints: Return minimal objects directly
 *      Example: { clientSecret: "...", paymentIntentId: "pi_...", ... }
 *    
 *    - Customer endpoints: Return nested objects directly
 *      Example: { customer: {...}, analytics: {...}, ... }
 * 
 * 2. SIMPLE SUCCESS/ERROR (Rare):
 *    - Some endpoints may return { success: true } or { success: false, error: "..." }
 *    - BUT: No timestamp or requestId fields in current implementation
 * 
 * 3. STANDARDIZED WRAPPER (Future):
 *    - These schemas support future migration to:
 *      { success: true, data: {...}, timestamp: "...", requestId: "..." }
 *    - Currently NOT used by endpoints
 * 
 * USAGE GUIDELINES:
 * 
 * ✅ DO: Define response schemas directly for new endpoints
 *    const MyResponseSchema = z.object({ field1: z.string(), field2: z.number() });
 * 
 * ✅ DO: Use BaseResponseSchema only if endpoint actually returns success/timestamp/requestId
 * 
 * ❌ DON'T: Assume all responses have success/timestamp/requestId wrappers
 * 
 * ❌ DON'T: Use ApiResponseSchema unless implementing new standardized endpoints
 * 
 * See booking-responses.ts, payment-responses.ts, customer-responses.ts for
 * examples of correctly matching actual backend responses.
 * ============================================================================
 */

/**
 * Base Response Schema
 * Standard wrapper for all API responses
 * Includes success flag, timestamp, and request ID for tracing
 * 
 * NOTE: Many existing endpoints return direct data without this wrapper.
 * This schema is kept for consistency but timestamp and requestId are OPTIONAL
 * to support both patterns:
 * 1. Wrapped: { success: true, data: {...}, timestamp: "...", requestId: "..." }
 * 2. Simple: { success: true, data: {...} } or just direct data
 * 
 * @example Wrapped response (full)
 * {
 *   success: true,
 *   timestamp: "2025-10-12T10:30:00.000Z",
 *   requestId: "123e4567-e89b-12d3-a456-426614174000"
 * }
 * 
 * @example Simple response (common in current backend)
 * {
 *   success: true
 * }
 */
export const BaseResponseSchema = z.object({
  success: z
    .boolean()
    .describe('Indicates if the request was successful'),
  timestamp: z
    .string()
    .datetime()
    .optional()
    .describe('ISO 8601 timestamp of the response (OPTIONAL - not all endpoints use this)'),
  requestId: z
    .string()
    .uuid()
    .optional()
    .describe('Unique identifier for request tracing (OPTIONAL - not all endpoints use this)'),
});

export type BaseResponse = z.infer<typeof BaseResponseSchema>;

/**
 * Generic API Response Schema
 * Wraps any data type with standard response fields
 * Used as a base for all endpoint-specific response schemas
 * 
 * NOTE: Most current endpoints return DIRECT DATA without the wrapper.
 * For example:
 * - Booking endpoints: Return direct arrays/objects
 * - Payment endpoints: Return { clientSecret, paymentIntentId, ... } directly
 * - Customer endpoints: Return { customer, analytics, ... } directly
 * 
 * This schema is kept for:
 * 1. Future endpoints that may use standardized format
 * 2. Backward compatibility if we add wrappers later
 * 3. Error responses that may need structured format
 * 
 * CURRENT PATTERN: Define response schemas directly without this wrapper.
 * See booking-responses.ts, payment-responses.ts, customer-responses.ts for examples.
 * 
 * @example Full wrapped response (NOT commonly used)
 * const UserResponseSchema = ApiResponseSchema(z.object({ name: z.string() }));
 * // { success: true, data: { name: "John" }, timestamp: "...", requestId: "..." }
 * 
 * @example Direct response (COMMON in current backend)
 * const UserResponseSchema = z.object({ name: z.string() });
 * // { name: "John" }
 */
export function ApiResponseSchema<T extends z.ZodType>(dataSchema: T) {
  return BaseResponseSchema.extend({
    data: dataSchema.optional().describe('Response data (optional if error)'),
    error: z
      .string()
      .optional()
      .describe('Error message if success is false'),
    message: z
      .string()
      .optional()
      .describe('Optional user-friendly message'),
  });
}

/**
 * Error Response Schema
 * Standard error response structure
 * Returned when success is false
 * 
 * @example
 * {
 *   success: false,
 *   error: "Validation failed",
 *   message: "The provided email address is invalid",
 *   timestamp: "2025-10-12T10:30:00.000Z",
 *   requestId: "123e4567-e89b-12d3-a456-426614174000",
 *   details: {
 *     field: "email",
 *     code: "INVALID_EMAIL"
 *   }
 * }
 */
export const ErrorResponseSchema = BaseResponseSchema.extend({
  success: z.literal(false).describe('Always false for error responses'),
  error: z.string().describe('Error message describing what went wrong'),
  message: z
    .string()
    .optional()
    .describe('Optional user-friendly error message'),
  details: z
    .record(z.any())
    .optional()
    .describe('Optional detailed error information'),
  code: z
    .string()
    .optional()
    .describe('Optional error code for programmatic handling'),
  statusCode: z
    .number()
    .int()
    .min(400)
    .max(599)
    .optional()
    .describe('Optional HTTP status code'),
});

export type ErrorResponse = z.infer<typeof ErrorResponseSchema>;

/**
 * Paginated Response Schema
 * Standard structure for paginated list endpoints
 * 
 * @example
 * const PaginatedUsersSchema = PaginatedResponseSchema(UserSchema);
 * 
 * {
 *   success: true,
 *   data: {
 *     items: [{ id: "1", name: "User 1" }, { id: "2", name: "User 2" }],
 *     total: 100,
 *     page: 1,
 *     pageSize: 10,
 *     totalPages: 10,
 *     hasNext: true,
 *     hasPrevious: false
 *   },
 *   timestamp: "2025-10-12T10:30:00.000Z",
 *   requestId: "123e4567-e89b-12d3-a456-426614174000"
 * }
 */
export function PaginatedResponseSchema<T extends z.ZodType>(itemSchema: T) {
  return BaseResponseSchema.extend({
    data: z.object({
      items: z
        .array(itemSchema)
        .describe('Array of items for the current page'),
      total: z
        .number()
        .int()
        .nonnegative()
        .describe('Total number of items across all pages'),
      page: z
        .number()
        .int()
        .positive()
        .describe('Current page number (1-indexed)'),
      pageSize: z
        .number()
        .int()
        .positive()
        .max(100)
        .describe('Number of items per page'),
      totalPages: z
        .number()
        .int()
        .nonnegative()
        .describe('Total number of pages available'),
      hasNext: z
        .boolean()
        .optional()
        .describe('Optional: Whether there is a next page'),
      hasPrevious: z
        .boolean()
        .optional()
        .describe('Optional: Whether there is a previous page'),
    }).describe('Paginated data'),
    error: z.string().optional().describe('Error message if success is false'),
  });
}

/**
 * Success Response Schema
 * Simple success response with optional message
 * Used for endpoints that don't return specific data
 * 
 * @example
 * {
 *   success: true,
 *   message: "Operation completed successfully",
 *   timestamp: "2025-10-12T10:30:00.000Z",
 *   requestId: "123e4567-e89b-12d3-a456-426614174000"
 * }
 */
export const SuccessResponseSchema = BaseResponseSchema.extend({
  success: z.literal(true).describe('Always true for success responses'),
  message: z
    .string()
    .optional()
    .describe('Optional success message for the user'),
});

export type SuccessResponse = z.infer<typeof SuccessResponseSchema>;

/**
 * Empty Response Schema
 * For endpoints that return no data (e.g., DELETE operations)
 * 
 * @example
 * {
 *   success: true,
 *   timestamp: "2025-10-12T10:30:00.000Z",
 *   requestId: "123e4567-e89b-12d3-a456-426614174000"
 * }
 */
export const EmptyResponseSchema = BaseResponseSchema;

export type EmptyResponse = z.infer<typeof EmptyResponseSchema>;

/**
 * Metadata Schema
 * Common metadata structure for responses that include additional context
 * 
 * @example
 * {
 *   version: "1.0",
 *   environment: "production",
 *   region: "us-west-2",
 *   executionTime: 45
 * }
 */
export const MetadataSchema = z.object({
  version: z
    .string()
    .optional()
    .describe('Optional: API version'),
  environment: z
    .enum(['development', 'staging', 'production'])
    .optional()
    .describe('Optional: Environment where request was processed'),
  region: z
    .string()
    .optional()
    .describe('Optional: AWS region or server location'),
  executionTime: z
    .number()
    .int()
    .nonnegative()
    .optional()
    .describe('Optional: Execution time in milliseconds'),
});

export type Metadata = z.infer<typeof MetadataSchema>;

/**
 * Response with Metadata Schema
 * Extends base response with metadata field
 * 
 * @example
 * const ResponseWithMeta = ResponseWithMetadataSchema(z.object({ name: z.string() }));
 */
export function ResponseWithMetadataSchema<T extends z.ZodType>(dataSchema: T) {
  return BaseResponseSchema.extend({
    data: dataSchema.optional().describe('Response data'),
    error: z.string().optional().describe('Error message if success is false'),
    message: z.string().optional().describe('Optional message'),
    metadata: MetadataSchema.optional().describe('Optional metadata'),
  });
}

/**
 * Validation Error Schema
 * Structured validation error for form submissions
 * 
 * @example
 * {
 *   success: false,
 *   error: "Validation failed",
 *   timestamp: "2025-10-12T10:30:00.000Z",
 *   requestId: "123e4567-e89b-12d3-a456-426614174000",
 *   validationErrors: {
 *     email: ["Email is required", "Email must be valid"],
 *     password: ["Password must be at least 8 characters"]
 *   }
 * }
 */
export const ValidationErrorResponseSchema = ErrorResponseSchema.extend({
  validationErrors: z
    .record(z.array(z.string()))
    .describe('Map of field names to array of error messages'),
});

export type ValidationErrorResponse = z.infer<typeof ValidationErrorResponseSchema>;

/**
 * Export all common schemas
 */
export const CommonResponseSchemas = {
  Base: BaseResponseSchema,
  ApiResponse: ApiResponseSchema,
  Error: ErrorResponseSchema,
  Paginated: PaginatedResponseSchema,
  Success: SuccessResponseSchema,
  Empty: EmptyResponseSchema,
  Metadata: MetadataSchema,
  ResponseWithMetadata: ResponseWithMetadataSchema,
  ValidationError: ValidationErrorResponseSchema,
} as const;
