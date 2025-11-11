import { z } from 'zod';

/**
 * Formatted Error Interface
 * User-friendly representation of a validation error
 */
export interface FormattedError {
  /**
   * User-friendly error message
   */
  message: string;
  
  /**
   * Field path where error occurred (e.g., "data.dates[0]")
   */
  field?: string;
  
  /**
   * Error code for programmatic handling
   */
  code: string;
  
  /**
   * Array of detailed field errors
   */
  fieldErrors?: FieldError[];
  
  /**
   * Suggestions for fixing the error
   */
  suggestions?: string[];
}

/**
 * Field Error Interface
 * Detailed error information for a specific field
 */
export interface FieldError {
  /**
   * Field path (e.g., "email", "data.dates", "items[2].price")
   */
  path: string;
  
  /**
   * User-friendly error message
   */
  message: string;
  
  /**
   * Zod error code
   */
  code: string;
  
  /**
   * Expected value or type
   */
  expected?: string;
  
  /**
   * Received value or type
   */
  received?: string;
}

/**
 * Formats a Zod error into a user-friendly error message
 * 
 * Converts technical Zod validation errors into messages that can be
 * displayed to end users or used for debugging.
 * 
 * @param error Zod validation error
 * @param options Formatting options
 * @returns Formatted error object
 * 
 * @example
 * try {
 *   const result = BookedDatesResponseSchema.parse(invalidData);
 * } catch (error) {
 *   if (error instanceof z.ZodError) {
 *     const formatted = formatZodError(error);
 *     console.error(formatted.message);
 *     formatted.fieldErrors?.forEach(fe => {
 *       console.error(`- ${fe.path}: ${fe.message}`);
 *     });
 *   }
 * }
 */
export function formatZodError(
  error: z.ZodError,
  options: FormatOptions = {}
): FormattedError {
  const {
    includeFieldErrors = true,
    includeSuggestions = true,
    maxFieldErrors = 5,
  } = options;
  
  const issues = error.errors;
  const firstIssue = issues[0];
  
  // Build user-friendly message
  const message = buildMainMessage(issues);
  
  // Build field errors array
  const fieldErrors = includeFieldErrors
    ? issues.slice(0, maxFieldErrors).map(issue => buildFieldError(issue))
    : undefined;
  
  // Build suggestions
  const suggestions = includeSuggestions
    ? buildSuggestions(issues)
    : undefined;
  
  return {
    message,
    field: firstIssue.path.length > 0 ? formatPath(firstIssue.path) : undefined,
    code: firstIssue.code,
    fieldErrors,
    suggestions,
  };
}

/**
 * Format Options Interface
 */
export interface FormatOptions {
  /**
   * Whether to include detailed field errors
   * @default true
   */
  includeFieldErrors?: boolean;
  
  /**
   * Whether to include suggestions for fixing errors
   * @default true
   */
  includeSuggestions?: boolean;
  
  /**
   * Maximum number of field errors to include
   * @default 5
   */
  maxFieldErrors?: number;
  
  /**
   * Custom error message templates
   */
  customMessages?: Record<string, string>;
}

/**
 * Builds the main error message
 */
function buildMainMessage(issues: z.ZodIssue[]): string {
  if (issues.length === 0) {
    return 'Validation failed';
  }
  
  if (issues.length === 1) {
    const issue = issues[0];
    const path = formatPath(issue.path);
    if (path) {
      return `Validation failed at "${path}": ${issue.message}`;
    }
    return `Validation failed: ${issue.message}`;
  }
  
  return `Validation failed with ${issues.length} errors`;
}

/**
 * Builds a field error object from a Zod issue
 */
function buildFieldError(issue: z.ZodIssue): FieldError {
  const path = formatPath(issue.path);
  
  const fieldError: FieldError = {
    path: path || '(root)',
    message: humanizeMessage(issue.message),
    code: issue.code,
  };
  
  // Add expected/received for certain error types
  if (issue.code === 'invalid_type') {
    fieldError.expected = issue.expected;
    fieldError.received = issue.received;
  } else if (issue.code === 'invalid_string' && 'validation' in issue) {
    fieldError.expected = String(issue.validation);
  } else if (issue.code === 'too_small') {
    fieldError.expected = `minimum ${issue.minimum}`;
  } else if (issue.code === 'too_big') {
    fieldError.expected = `maximum ${issue.maximum}`;
  }
  
  return fieldError;
}

/**
 * Builds suggestions for fixing validation errors
 */
function buildSuggestions(issues: z.ZodIssue[]): string[] {
  const suggestions: string[] = [];
  const seenCodes = new Set<string>();
  
  for (const issue of issues) {
    if (seenCodes.has(issue.code)) continue;
    seenCodes.add(issue.code);
    
    const suggestion = getSuggestionForCode(issue);
    if (suggestion) {
      suggestions.push(suggestion);
    }
  }
  
  return suggestions;
}

/**
 * Gets a helpful suggestion based on error code
 */
function getSuggestionForCode(issue: z.ZodIssue): string | null {
  switch (issue.code) {
    case 'invalid_type':
      if (issue.received === 'undefined') {
        return 'This field is required. Make sure it is included in the response.';
      }
      if (issue.received === 'null') {
        return 'This field cannot be null. Check if the API is returning the correct value.';
      }
      return `Expected ${issue.expected} but received ${issue.received}. Check the API response format.`;
      
    case 'invalid_string':
      if ('validation' in issue) {
        if (issue.validation === 'email') {
          return 'Please provide a valid email address format.';
        }
        if (issue.validation === 'url') {
          return 'Please provide a valid URL (e.g., https://example.com).';
        }
        if (issue.validation === 'uuid') {
          return 'This field must be a valid UUID.';
        }
        if (issue.validation === 'datetime') {
          return 'Please provide a valid ISO 8601 datetime format.';
        }
      }
      return 'The string format is invalid. Check the expected pattern.';
      
    case 'too_small':
      if (issue.type === 'string') {
        return `This field must be at least ${issue.minimum} characters long.`;
      }
      if (issue.type === 'number') {
        return `This value must be at least ${issue.minimum}.`;
      }
      if (issue.type === 'array') {
        return `This array must contain at least ${issue.minimum} items.`;
      }
      return 'The value is too small. Check the minimum requirements.';
      
    case 'too_big':
      if (issue.type === 'string') {
        return `This field must be at most ${issue.maximum} characters long.`;
      }
      if (issue.type === 'number') {
        return `This value must be at most ${issue.maximum}.`;
      }
      if (issue.type === 'array') {
        return `This array must contain at most ${issue.maximum} items.`;
      }
      return 'The value is too large. Check the maximum requirements.';
      
    case 'invalid_enum_value':
      if ('options' in issue) {
        const options = (issue as any).options.join(', ');
        return `Valid options are: ${options}`;
      }
      return 'The value is not a valid option. Check the allowed values.';
      
    case 'unrecognized_keys':
      if ('keys' in issue) {
        const keys = (issue as any).keys.join(', ');
        return `Unexpected fields found: ${keys}. These fields are not allowed.`;
      }
      return 'Unexpected fields found in the response.';
      
    case 'invalid_date':
      return 'Please provide a valid date format.';
      
    case 'custom':
      return issue.message;
      
    default:
      return null;
  }
}

/**
 * Formats a Zod path array into a readable string
 * 
 * @example
 * formatPath(['data', 'items', 0, 'name']) // "data.items[0].name"
 */
function formatPath(path: (string | number)[]): string {
  if (path.length === 0) return '';
  
  return path.reduce<string>((acc, part, index) => {
    if (typeof part === 'number') {
      return `${acc}[${part}]`;
    }
    if (index === 0) {
      return part;
    }
    return `${acc}.${part}`;
  }, '');
}

/**
 * Humanizes a Zod error message
 * Makes technical messages more user-friendly
 */
function humanizeMessage(message: string): string {
  // Remove "Expected" prefix if present
  message = message.replace(/^Expected /, '');
  
  // Capitalize first letter
  message = message.charAt(0).toUpperCase() + message.slice(1);
  
  // Add period if not present
  if (!message.endsWith('.')) {
    message += '.';
  }
  
  return message;
}

/**
 * Creates a formatted error message for display to users
 * 
 * Generates a concise, user-friendly message suitable for toast
 * notifications or inline error displays.
 * 
 * @param error Zod validation error
 * @returns User-friendly error message
 * 
 * @example
 * try {
 *   validateResponse(BookedDatesResponseSchema, data);
 * } catch (error) {
 *   if (error instanceof z.ZodError) {
 *     const message = formatErrorForDisplay(error);
 *     toast.error(message); // "Unable to process response: Invalid date format"
 *   }
 * }
 */
export function formatErrorForDisplay(error: z.ZodError): string {
  const formatted = formatZodError(error, {
    includeFieldErrors: false,
    includeSuggestions: false,
  });
  
  // Create concise message
  if (formatted.field) {
    return `Unable to process response: ${formatted.message}`;
  }
  
  return `Unable to process response: ${formatted.message}`;
}

/**
 * Creates a detailed error report for logging/debugging
 * 
 * Generates a comprehensive error report with all details,
 * suitable for console logging or error tracking services.
 * 
 * @param error Zod validation error
 * @param additionalContext Additional context to include
 * @returns Detailed error report object
 * 
 * @example
 * try {
 *   validateResponse(BookedDatesResponseSchema, data);
 * } catch (error) {
 *   if (error instanceof z.ZodError) {
 *     const report = formatErrorForLogging(error, {
 *       endpoint: '/api/v1/bookings/booked-dates',
 *       requestId: 'abc-123'
 *     });
 *     console.error('[Validation Error]', report);
 *   }
 * }
 */
export function formatErrorForLogging(
  error: z.ZodError,
  additionalContext?: Record<string, unknown>
): Record<string, unknown> {
  const formatted = formatZodError(error);
  
  return {
    type: 'ValidationError',
    message: formatted.message,
    field: formatted.field,
    code: formatted.code,
    fieldErrors: formatted.fieldErrors,
    suggestions: formatted.suggestions,
    errorCount: error.errors.length,
    timestamp: new Date().toISOString(),
    ...additionalContext,
  };
}

/**
 * Export all formatting utilities
 */
export const ErrorFormatters = {
  formatZodError,
  formatErrorForDisplay,
  formatErrorForLogging,
  formatPath,
} as const;
