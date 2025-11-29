/**
 * Error Message System
 *
 * Converts API errors and generic errors into user-friendly messages
 * with actionable guidance.
 */

export type ErrorType =
  | 'network'
  | 'authentication'
  | 'authorization'
  | 'validation'
  | 'not_found'
  | 'conflict'
  | 'rate_limit'
  | 'server_error'
  | 'unknown';

export interface UserFriendlyError {
  type: ErrorType;
  title: string;
  message: string;
  action?: string;
  details?: string;
}

/**
 * API Error Code to User-Friendly Message Mapping
 */
const ERROR_MESSAGES: Record<string, UserFriendlyError> = {
  // Authentication Errors
  INVALID_CREDENTIALS: {
    type: 'authentication',
    title: 'Invalid Login',
    message: 'The email or password you entered is incorrect.',
    action: 'Please check your credentials and try again.',
  },
  TOKEN_EXPIRED: {
    type: 'authentication',
    title: 'Session Expired',
    message: 'Your session has expired for security reasons.',
    action: 'Please log in again to continue.',
  },
  UNAUTHORIZED: {
    type: 'authentication',
    title: 'Authentication Required',
    message: 'You need to be logged in to perform this action.',
    action: 'Please log in and try again.',
  },

  // Authorization Errors
  FORBIDDEN: {
    type: 'authorization',
    title: 'Access Denied',
    message: 'You do not have permission to perform this action.',
    action: 'Contact your administrator if you believe this is an error.',
  },
  INSUFFICIENT_PERMISSIONS: {
    type: 'authorization',
    title: 'Insufficient Permissions',
    message: 'Your account does not have the required permissions.',
    action: 'Contact your administrator to request access.',
  },

  // Validation Errors
  VALIDATION_ERROR: {
    type: 'validation',
    title: 'Invalid Information',
    message: 'Please check the form and correct any errors.',
    action: 'Review the highlighted fields and try again.',
  },
  INVALID_EMAIL: {
    type: 'validation',
    title: 'Invalid Email',
    message: 'The email address format is not valid.',
    action: 'Please enter a valid email address.',
  },
  INVALID_PHONE: {
    type: 'validation',
    title: 'Invalid Phone Number',
    message: 'The phone number format is not valid.',
    action: 'Please enter a valid phone number (e.g., +1234567890).',
  },
  INVALID_DATE: {
    type: 'validation',
    title: 'Invalid Date',
    message: 'The date you selected is not valid.',
    action: 'Please select a valid date.',
  },

  // Not Found Errors
  NOT_FOUND: {
    type: 'not_found',
    title: 'Not Found',
    message: 'The item you are looking for could not be found.',
    action: 'It may have been deleted or moved.',
  },
  BOOKING_NOT_FOUND: {
    type: 'not_found',
    title: 'Booking Not Found',
    message: 'This booking no longer exists in the system.',
    action: 'It may have been canceled or deleted.',
  },
  CUSTOMER_NOT_FOUND: {
    type: 'not_found',
    title: 'Customer Not Found',
    message: 'This customer could not be found.',
    action: 'The customer may have been removed from the system.',
  },

  // Conflict Errors
  DUPLICATE_EMAIL: {
    type: 'conflict',
    title: 'Email Already Exists',
    message: 'An account with this email address already exists.',
    action: 'Try logging in or use a different email address.',
  },
  DUPLICATE_BOOKING: {
    type: 'conflict',
    title: 'Booking Conflict',
    message: 'This time slot is already booked.',
    action: 'Please select a different date or time.',
  },
  RESOURCE_LOCKED: {
    type: 'conflict',
    title: 'Resource In Use',
    message: 'This resource is currently being edited by another user.',
    action: 'Please try again in a few moments.',
  },

  // Rate Limit Errors
  RATE_LIMIT_EXCEEDED: {
    type: 'rate_limit',
    title: 'Too Many Requests',
    message: 'You have made too many requests in a short time.',
    action: 'Please wait a moment and try again.',
  },

  // Payment Errors
  PAYMENT_FAILED: {
    type: 'validation',
    title: 'Payment Failed',
    message: 'Your payment could not be processed.',
    action: 'Please check your payment information and try again.',
  },
  CARD_DECLINED: {
    type: 'validation',
    title: 'Card Declined',
    message: 'Your card was declined by your bank.',
    action: 'Please try a different payment method or contact your bank.',
  },
  INSUFFICIENT_FUNDS: {
    type: 'validation',
    title: 'Insufficient Funds',
    message: 'Your account does not have sufficient funds.',
    action: 'Please try a different payment method.',
  },

  // Server Errors
  INTERNAL_SERVER_ERROR: {
    type: 'server_error',
    title: 'Server Error',
    message: 'Something went wrong on our end.',
    action: 'Please try again. If the problem persists, contact support.',
  },
  SERVICE_UNAVAILABLE: {
    type: 'server_error',
    title: 'Service Temporarily Unavailable',
    message: 'Our service is temporarily down for maintenance.',
    action: 'Please try again in a few minutes.',
  },
  DATABASE_ERROR: {
    type: 'server_error',
    title: 'Database Error',
    message: 'We encountered a problem accessing your data.',
    action: 'Please try again. If the problem persists, contact support.',
  },

  // Network Errors
  NETWORK_ERROR: {
    type: 'network',
    title: 'Connection Error',
    message: 'Unable to connect to the server.',
    action: 'Please check your internet connection and try again.',
  },
  TIMEOUT: {
    type: 'network',
    title: 'Request Timeout',
    message: 'The request took too long to complete.',
    action: 'Please try again. Your connection may be slow.',
  },
};

/**
 * HTTP Status Code to Error Type Mapping
 */
const STATUS_CODE_ERRORS: Record<number, UserFriendlyError> = {
  400: {
    type: 'validation',
    title: 'Invalid Request',
    message: 'The information you provided is not valid.',
    action: 'Please check your input and try again.',
  },
  401: ERROR_MESSAGES.UNAUTHORIZED,
  403: ERROR_MESSAGES.FORBIDDEN,
  404: ERROR_MESSAGES.NOT_FOUND,
  409: {
    type: 'conflict',
    title: 'Conflict',
    message: 'This operation conflicts with existing data.',
    action: 'Please refresh the page and try again.',
  },
  422: ERROR_MESSAGES.VALIDATION_ERROR,
  429: ERROR_MESSAGES.RATE_LIMIT_EXCEEDED,
  500: ERROR_MESSAGES.INTERNAL_SERVER_ERROR,
  502: {
    type: 'server_error',
    title: 'Bad Gateway',
    message: 'The server is temporarily unavailable.',
    action: 'Please try again in a moment.',
  },
  503: ERROR_MESSAGES.SERVICE_UNAVAILABLE,
  504: ERROR_MESSAGES.TIMEOUT,
};

/**
 * Convert any error to a user-friendly error object
 */
export function parseError(error: unknown): UserFriendlyError {
  // Network errors
  if (error instanceof TypeError && error.message.includes('fetch')) {
    return ERROR_MESSAGES.NETWORK_ERROR;
  }

  // API errors with response
  if (isApiError(error)) {
    const { status, data } = error;

    // Try to get error code from response
    if (data?.code && ERROR_MESSAGES[data.code]) {
      const detailStr = typeof data.detail === 'string' ? data.detail : data.message;
      return {
        ...ERROR_MESSAGES[data.code],
        details: detailStr,
      };
    }

    // Try to get error from detail field
    if (data?.detail && typeof data.detail === 'string') {
      const code = extractErrorCode(data.detail);
      if (code && ERROR_MESSAGES[code]) {
        return {
          ...ERROR_MESSAGES[code],
          details: data.detail,
        };
      }
    }

    // Fallback to status code
    if (STATUS_CODE_ERRORS[status]) {
      const detailStr = typeof data?.detail === 'string' ? data.detail : data?.message;
      return {
        ...STATUS_CODE_ERRORS[status],
        details: detailStr,
      };
    }
  }

  // Validation errors with field-specific messages
  if (isValidationError(error)) {
    return formatValidationError(error);
  }

  // Generic JavaScript errors
  if (error instanceof Error) {
    return {
      type: 'unknown',
      title: 'Unexpected Error',
      message: 'An unexpected error occurred.',
      action: 'Please try again or contact support if the problem persists.',
      details: error.message,
    };
  }

  // Unknown error
  return {
    type: 'unknown',
    title: 'Unknown Error',
    message: 'Something unexpected happened.',
    action: 'Please try again or contact support.',
  };
}

/**
 * Type guard for API errors
 */
interface ApiError {
  status: number;
  data?: {
    code?: string;
    message?: string;
    detail?: string | Record<string, unknown>;
    errors?: Record<string, string[]>;
  };
}

function isApiError(error: unknown): error is ApiError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'status' in error &&
    typeof (error as ApiError).status === 'number'
  );
}

/**
 * Type guard for validation errors
 */
interface ValidationError {
  status: 422;
  data: {
    detail: Array<{
      loc: string[];
      msg: string;
      type: string;
    }>;
  };
}

function isValidationError(error: unknown): error is ValidationError {
  return (
    isApiError(error) &&
    error.status === 422 &&
    Array.isArray(error.data?.detail)
  );
}

/**
 * Format validation errors into user-friendly message
 */
function formatValidationError(error: ValidationError): UserFriendlyError {
  const fields = error.data.detail
    .map((err) => {
      const fieldName = err.loc[err.loc.length - 1];
      return `${fieldName}: ${err.msg}`;
    })
    .join(', ');

  return {
    type: 'validation',
    title: 'Validation Error',
    message: 'Please check the following fields:',
    action: fields,
    details: JSON.stringify(error.data.detail),
  };
}

/**
 * Extract error code from error message
 */
function extractErrorCode(message: string): string | null {
  const match = message.match(/\[([A-Z_]+)\]/);
  return match ? match[1] : null;
}

/**
 * Get user-friendly error message string
 */
export function getErrorMessage(error: unknown): string {
  const parsed = parseError(error);
  let message = `${parsed.title}: ${parsed.message}`;
  if (parsed.action) {
    message += ` ${parsed.action}`;
  }
  return message;
}

/**
 * Get short error message (for toasts)
 */
export function getShortErrorMessage(error: unknown): string {
  const parsed = parseError(error);
  return parsed.message;
}

/**
 * Check if error requires re-authentication
 */
export function requiresReauth(error: unknown): boolean {
  const parsed = parseError(error);
  return parsed.type === 'authentication';
}

/**
 * Check if error is temporary (worth retrying)
 */
export function isTemporaryError(error: unknown): boolean {
  const parsed = parseError(error);
  return ['network', 'rate_limit', 'server_error'].includes(parsed.type);
}
