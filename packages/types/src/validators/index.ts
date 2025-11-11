import { z } from 'zod';

/**
 * Validation Result Interface
 * Represents the outcome of a validation operation
 * 
 * @template T The expected type of the validated data
 */
export interface ValidationResult<T> {
  /**
   * Whether validation succeeded
   */
  success: boolean;
  
  /**
   * The validated data (only present if success is true)
   */
  data?: T;
  
  /**
   * Error message (only present if success is false)
   */
  error?: string;
  
  /**
   * Original Zod error for detailed debugging
   */
  zodError?: z.ZodError;
  
  /**
   * Validation context information
   */
  context?: ValidationContext;
}

/**
 * Validation Context
 * Additional context about where validation occurred
 */
export interface ValidationContext {
  /**
   * The endpoint that was called
   */
  endpoint?: string;
  
  /**
   * HTTP method used
   */
  method?: string;
  
  /**
   * Request ID for tracing
   */
  requestId?: string;
  
  /**
   * Component or file where validation was called
   */
  source?: string;
}

/**
 * Validates response data against a Zod schema
 * 
 * Throws an error if validation fails. Use this when you want
 * validation errors to propagate and be caught by error boundaries.
 * 
 * @template T The expected type of the validated data
 * @param schema Zod schema to validate against
 * @param data The data to validate
 * @param context Optional context for debugging
 * @returns The validated data with full type safety
 * @throws ValidationError if validation fails
 * 
 * @example
 * try {
 *   const data = await apiFetch('/api/v1/bookings/booked-dates');
 *   const validData = validateResponse(BookedDatesResponseSchema, data, {
 *     endpoint: '/api/v1/bookings/booked-dates',
 *     method: 'GET',
 *     source: 'useBooking.ts'
 *   });
 *   console.log('Valid dates:', validData.data.dates);
 * } catch (error) {
 *   console.error('Validation failed:', error.message);
 * }
 */
export function validateResponse<T extends z.ZodType>(
  schema: T,
  data: unknown,
  context?: ValidationContext
): z.infer<T> {
  try {
    const result = schema.parse(data);
    
    // Log successful validation in development
    if (process.env.NODE_ENV === 'development' && context) {
      console.log(`[Validation Success] ${context.method || 'REQUEST'} ${context.endpoint || 'unknown'}`, {
        requestId: context.requestId,
        source: context.source,
      });
    }
    
    return result;
  } catch (error) {
    if (error instanceof z.ZodError) {
      // Log validation error
      console.error('[Validation Error]', {
        context,
        errors: error.errors,
        data: process.env.NODE_ENV === 'development' ? data : '[redacted]',
      });
      
      // Create user-friendly error message
      const firstError = error.errors[0];
      const path = firstError.path.join('.');
      const message = `API response validation failed: ${firstError.message}${path ? ` at ${path}` : ''}`;
      
      throw new ValidationError(message, error, context);
    }
    throw error;
  }
}

/**
 * Safely validates response data without throwing
 * 
 * Returns a ValidationResult object with success/error information.
 * Use this when you want to handle validation errors gracefully without
 * try/catch blocks.
 * 
 * @template T The expected type of the validated data
 * @param schema Zod schema to validate against
 * @param data The data to validate
 * @param context Optional context for debugging
 * @returns ValidationResult object with success flag and data/error
 * 
 * @example
 * const data = await apiFetch('/api/v1/bookings/booked-dates');
 * const result = safeValidateResponse(BookedDatesResponseSchema, data, {
 *   endpoint: '/api/v1/bookings/booked-dates',
 *   method: 'GET'
 * });
 * 
 * if (result.success) {
 *   console.log('Valid dates:', result.data.data.dates);
 * } else {
 *   console.error('Validation failed:', result.error);
 *   // Gracefully degrade or show error to user
 * }
 */
export function safeValidateResponse<T extends z.ZodType>(
  schema: T,
  data: unknown,
  context?: ValidationContext
): ValidationResult<z.infer<T>> {
  const result = schema.safeParse(data);
  
  if (result.success) {
    // Log successful validation in development
    if (process.env.NODE_ENV === 'development' && context) {
      console.log(`[Safe Validation Success] ${context.method || 'REQUEST'} ${context.endpoint || 'unknown'}`);
    }
    
    return {
      success: true,
      data: result.data,
      context,
    };
  } else {
    // Log validation error
    console.warn('[Safe Validation Error]', {
      context,
      errors: result.error.errors,
      data: process.env.NODE_ENV === 'development' ? data : '[redacted]',
    });
    
    const firstError = result.error.errors[0];
    const path = firstError.path.join('.');
    const message = `API response validation failed: ${firstError.message}${path ? ` at ${path}` : ''}`;
    
    return {
      success: false,
      error: message,
      zodError: result.error,
      context,
    };
  }
}

/**
 * Validates an array of items against a schema
 * 
 * Useful for validating paginated responses or lists of items.
 * Validates each item individually and collects all errors.
 * 
 * @template T The expected type of each array item
 * @param itemSchema Zod schema for individual array items
 * @param data The array to validate
 * @param context Optional context for debugging
 * @returns Array of validated items
 * @throws ValidationError if validation fails
 * 
 * @example
 * const data = await apiFetch('/api/v1/bookings');
 * const validBookings = validateArray(BookingSchema, data.data.items, {
 *   endpoint: '/api/v1/bookings',
 *   method: 'GET',
 *   source: 'BookingList.tsx'
 * });
 */
export function validateArray<T extends z.ZodType>(
  itemSchema: T,
  data: unknown,
  context?: ValidationContext
): z.infer<T>[] {
  if (!Array.isArray(data)) {
    throw new ValidationError(
      'Expected an array but received: ' + typeof data,
      undefined,
      context
    );
  }
  
  const arraySchema = z.array(itemSchema);
  return validateResponse(arraySchema, data, context);
}

/**
 * Safely validates an array without throwing
 * 
 * @template T The expected type of each array item
 * @param itemSchema Zod schema for individual array items
 * @param data The array to validate
 * @param context Optional context for debugging
 * @returns ValidationResult with array of validated items
 * 
 * @example
 * const data = await apiFetch('/api/v1/bookings');
 * const result = safeValidateArray(BookingSchema, data.data.items);
 * 
 * if (result.success) {
 *   result.data.forEach(booking => console.log(booking.id));
 * } else {
 *   console.error('Array validation failed:', result.error);
 * }
 */
export function safeValidateArray<T extends z.ZodType>(
  itemSchema: T,
  data: unknown,
  context?: ValidationContext
): ValidationResult<z.infer<T>[]> {
  if (!Array.isArray(data)) {
    return {
      success: false,
      error: 'Expected an array but received: ' + typeof data,
      context,
    };
  }
  
  const arraySchema = z.array(itemSchema);
  return safeValidateResponse(arraySchema, data, context);
}

/**
 * Custom Validation Error Class
 * Extends Error with Zod error details and context
 */
export class ValidationError extends Error {
  public readonly zodError?: z.ZodError;
  public readonly context?: ValidationContext;
  
  constructor(message: string, zodError?: z.ZodError, context?: ValidationContext) {
    super(message);
    this.name = 'ValidationError';
    this.zodError = zodError;
    this.context = context;
    
    // Maintains proper stack trace for where error was thrown
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, ValidationError);
    }
  }
  
  /**
   * Get formatted error details for logging/debugging
   */
  public getDetails(): Record<string, unknown> {
    return {
      message: this.message,
      context: this.context,
      zodErrors: this.zodError?.errors.map(err => ({
        path: err.path.join('.'),
        message: err.message,
        code: err.code,
      })),
    };
  }
}

/**
 * Type guard to check if an error is a ValidationError
 */
export function isValidationError(error: unknown): error is ValidationError {
  return error instanceof ValidationError;
}

/**
 * Partial validation - validates only specified fields
 * 
 * Useful when you only care about certain fields in a response
 * and want to ignore validation errors in other fields.
 * 
 * @template T The schema type
 * @template K Keys to validate
 * @param schema Zod schema to validate against
 * @param data The data to validate
 * @param keys Keys to validate (validates all if not provided)
 * @param context Optional context for debugging
 * @returns Partial validated data
 * 
 * @example
 * // Only validate the 'data' and 'success' fields
 * const result = partialValidate(
 *   BookedDatesResponseSchema,
 *   apiResponse,
 *   ['data', 'success'],
 *   { endpoint: '/api/v1/bookings/booked-dates' }
 * );
 */
export function partialValidate<
  T extends z.ZodObject<any>,
  K extends keyof z.infer<T>
>(
  schema: T,
  data: unknown,
  keys?: K[],
  context?: ValidationContext
): Pick<z.infer<T>, K> | z.infer<T> {
  if (keys && keys.length > 0) {
    const partialSchema = schema.pick(
      keys.reduce((acc, key) => ({ ...acc, [key]: true }), {} as any)
    );
    return validateResponse(partialSchema, data, context);
  }
  
  return validateResponse(schema, data, context);
}

/**
 * Export all validation utilities
 */
export const ValidationUtilities = {
  validate: validateResponse,
  safeValidate: safeValidateResponse,
  validateArray,
  safeValidateArray,
  partialValidate,
  isValidationError,
} as const;
