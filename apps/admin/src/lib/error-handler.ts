/**
 * Centralized Error Handling Utility
 * Provides consistent error handling patterns across the application
 */

import type { ApiResponse } from './api';

export interface ErrorDetails {
  title: string;
  message: string;
  status?: number;
  code?: string;
}

/**
 * Parse API error response into user-friendly error details
 */
export function parseApiError(error: unknown): ErrorDetails {
  // Handle API response errors
  if (error && typeof error === 'object' && 'error' in error) {
    const apiError = error as ApiResponse;
    return {
      title: 'API Error',
      message: apiError.error || 'An unexpected error occurred',
    };
  }

  // Handle Error objects
  if (error instanceof Error) {
    // Network errors
    if (error.message.includes('Failed to fetch')) {
      return {
        title: 'Network Error',
        message: 'Unable to connect to the server. Please check your internet connection.',
      };
    }

    // Timeout errors
    if (error.message.includes('timeout') || error.message.includes('aborted')) {
      return {
        title: 'Request Timeout',
        message: 'The request took too long. Please try again.',
      };
    }

    // HTTP errors
    const httpMatch = error.message.match(/HTTP (\d+)/);
    if (httpMatch) {
      const status = parseInt(httpMatch[1]);
      return {
        title: `Error ${status}`,
        message: getHttpErrorMessage(status),
        status,
      };
    }

    // Generic error
    return {
      title: 'Error',
      message: error.message,
    };
  }

  // Unknown error type
  return {
    title: 'Unknown Error',
    message: 'Something went wrong. Please try again.',
  };
}

/**
 * Get user-friendly message for HTTP status codes
 */
function getHttpErrorMessage(status: number): string {
  switch (status) {
    case 400:
      return 'Invalid request. Please check your input and try again.';
    case 401:
      return 'You are not authorized. Please log in again.';
    case 403:
      return 'You do not have permission to perform this action.';
    case 404:
      return 'The requested resource was not found.';
    case 409:
      return 'This action conflicts with existing data.';
    case 422:
      return 'The data provided is invalid or incomplete.';
    case 429:
      return 'Too many requests. Please wait a moment and try again.';
    case 500:
      return 'Server error. Please try again later.';
    case 502:
      return 'Bad gateway. The server is temporarily unavailable.';
    case 503:
      return 'Service unavailable. Please try again later.';
    case 504:
      return 'Gateway timeout. The server took too long to respond.';
    default:
      return `Request failed with status ${status}`;
  }
}

/**
 * Retry configuration for different error types
 */
export interface RetryConfig {
  maxAttempts: number;
  delayMs: number;
  backoffMultiplier: number;
  retryableStatuses: number[];
}

export const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxAttempts: 3,
  delayMs: 1000,
  backoffMultiplier: 2,
  retryableStatuses: [408, 429, 500, 502, 503, 504],
};

/**
 * Determine if an error is retryable
 */
export function isRetryableError(error: unknown): boolean {
  const details = parseApiError(error);

  // Network errors are retryable
  if (details.title === 'Network Error' || details.title === 'Request Timeout') {
    return true;
  }

  // Certain HTTP status codes are retryable
  if (details.status && DEFAULT_RETRY_CONFIG.retryableStatuses.includes(details.status)) {
    return true;
  }

  return false;
}

/**
 * Sleep helper for retry delays
 */
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Retry a function with exponential backoff
 */
export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  config: Partial<RetryConfig> = {}
): Promise<T> {
  const { maxAttempts, delayMs, backoffMultiplier } = {
    ...DEFAULT_RETRY_CONFIG,
    ...config,
  };

  let lastError: unknown;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      // Don't retry if error is not retryable
      if (!isRetryableError(error)) {
        throw error;
      }

      // Don't retry on last attempt
      if (attempt === maxAttempts) {
        throw error;
      }

      // Calculate delay with exponential backoff
      const delay = delayMs * Math.pow(backoffMultiplier, attempt - 1);
      console.log(`Retry attempt ${attempt}/${maxAttempts} after ${delay}ms...`);
      await sleep(delay);
    }
  }

  throw lastError;
}

/**
 * Validation error helpers
 */
export interface ValidationError {
  field: string;
  message: string;
}

export function parseValidationErrors(error: unknown): ValidationError[] {
  if (!error || typeof error !== 'object') {
    return [];
  }

  // FastAPI/Pydantic validation error format
  if ('detail' in error && Array.isArray((error as any).detail)) {
    return (error as any).detail.map((err: any) => ({
      field: err.loc?.join('.') || 'unknown',
      message: err.msg || 'Validation error',
    }));
  }

  return [];
}

/**
 * Format validation errors for display
 */
export function formatValidationErrors(errors: ValidationError[]): string {
  if (errors.length === 0) {
    return 'Validation failed';
  }

  if (errors.length === 1) {
    return `${errors[0].field}: ${errors[0].message}`;
  }

  return errors.map(err => `${err.field}: ${err.message}`).join('; ');
}
