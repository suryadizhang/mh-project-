/**
 * Unified API client for My Hibachi frontend
 * All backend communication should go through this module
 *
 * Features:
 * - Configurable timeouts per endpoint type
 * - Automatic retry logic for failed requests
 * - Request/response logging
 * - Error handling with user-friendly messages
 * - Abort controller for timeout management
 */

import { logger, logApiRequest } from '@/lib/logger';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Type definitions
export interface ApiResponse<T = Record<string, unknown>> {
  data?: T
  error?: string
  message?: string
  success: boolean
}

export interface ApiRequestOptions extends RequestInit {
  timeout?: number
  retry?: boolean
  maxRetries?: number
  retryDelay?: number
}

export interface StripePaymentData {
  amount: number
  customer_email: string
  customer_name: string
  [key: string]: unknown
}

/**
 * Timeout configuration for different endpoint types
 * Longer timeouts for complex operations, shorter for quick lookups
 */
export const TIMEOUT_CONFIG = {
  // Complex operations
  BOOKING_CREATE: 45000,      // 45s - Complex validation and database operations
  PAYMENT_PROCESS: 60000,     // 60s - Stripe processing time + webhooks
  FILE_UPLOAD: 120000,        // 120s - Large image uploads
  REPORT_GENERATE: 90000,     // 90s - Report generation with data aggregation

  // Standard operations
  BOOKING_UPDATE: 30000,      // 30s - Update operations
  BOOKING_DELETE: 20000,      // 20s - Delete operations
  CUSTOMER_UPDATE: 30000,     // 30s - Customer profile updates

  // Quick lookups
  BOOKING_LIST: 15000,        // 15s - List operations with pagination
  BOOKING_GET: 10000,         // 10s - Single record retrieval
  AVAILABILITY_CHECK: 10000,  // 10s - Availability queries (cached)
  DASHBOARD_DATA: 15000,      // 15s - Dashboard data (may have multiple queries)

  // Real-time operations
  CHAT_MESSAGE: 30000,        // 30s - AI chat responses
  WEBSOCKET: 5000,            // 5s - WebSocket connections

  // Default fallback
  DEFAULT: 30000              // 30s - Default for unspecified endpoints
} as const;

/**
 * Determine appropriate timeout based on endpoint path and method
 */
function getTimeoutForEndpoint(path: string, method: string = 'GET'): number {
  // Booking operations
  if (path.includes('/bookings')) {
    if (method === 'POST' && path.includes('/submit')) return TIMEOUT_CONFIG.BOOKING_CREATE;
    if (method === 'POST') return TIMEOUT_CONFIG.BOOKING_CREATE;
    if (method === 'PUT' || method === 'PATCH') return TIMEOUT_CONFIG.BOOKING_UPDATE;
    if (method === 'DELETE') return TIMEOUT_CONFIG.BOOKING_DELETE;
    if (path.includes('/availability')) return TIMEOUT_CONFIG.AVAILABILITY_CHECK;
    if (path.includes('/booked-dates')) return TIMEOUT_CONFIG.AVAILABILITY_CHECK;
    return TIMEOUT_CONFIG.BOOKING_GET;
  }

  // Payment operations
  if (path.includes('/payment')) {
    if (method === 'POST') return TIMEOUT_CONFIG.PAYMENT_PROCESS;
    return TIMEOUT_CONFIG.DEFAULT;
  }

  // File uploads
  if (path.includes('/upload') || path.includes('/image')) {
    return TIMEOUT_CONFIG.FILE_UPLOAD;
  }

  // Chat operations
  if (path.includes('/chat') || path.includes('/ai')) {
    return TIMEOUT_CONFIG.CHAT_MESSAGE;
  }

  // Customer operations
  if (path.includes('/customer')) {
    if (method === 'PUT' || method === 'PATCH' || method === 'POST') {
      return TIMEOUT_CONFIG.CUSTOMER_UPDATE;
    }
    if (path.includes('/dashboard')) return TIMEOUT_CONFIG.DASHBOARD_DATA;
    return TIMEOUT_CONFIG.DEFAULT;
  }

  // Reports
  if (path.includes('/report')) {
    return TIMEOUT_CONFIG.REPORT_GENERATE;
  }

  return TIMEOUT_CONFIG.DEFAULT;
}

/**
 * Sleep utility for retry delays
 */
function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Main API fetch function - all backend calls should use this
 *
 * Features:
 * - Automatic timeout based on endpoint type
 * - Retry logic for transient failures (network errors, 5xx errors)
 * - Request/response logging
 * - User-friendly error messages
 * - Abort controller for proper cancellation
 *
 * @param path - API endpoint path (e.g., '/api/v1/bookings')
 * @param options - Request options including timeout, retry config
 * @returns Promise with typed API response
 */
export async function apiFetch<T = Record<string, unknown>>(
  path: string,
  options: ApiRequestOptions = {}
): Promise<ApiResponse<T>> {
  const {
    timeout,
    retry = true,
    maxRetries = 3,
    retryDelay = 1000,
    ...fetchOptions
  } = options;

  // Determine timeout: explicit > endpoint-specific > default
  const method = (fetchOptions.method || 'GET').toUpperCase();
  const timeoutMs = timeout ?? getTimeoutForEndpoint(path, method);

  const url = `${API_BASE_URL}${path}`;
  const startTime = performance.now();

  let lastError: Error | null = null;
  let attempt = 0;

  while (attempt < maxRetries) {
    attempt++;

    // Setup abort controller for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      logger.debug(`API Request [${method}] ${path}`, {
        attempt,
        maxRetries,
        timeout: timeoutMs
      });

      const response = await fetch(url, {
        ...fetchOptions,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...fetchOptions.headers
        }
      });

      clearTimeout(timeoutId);

      const duration = performance.now() - startTime;

      // Log successful request
      logApiRequest(method, path, response.status, duration);

      if (!response.ok) {
        // Server returned error status
        const errorText = await response.text().catch(() => 'Unknown error');

        // Retry on 5xx errors (server errors) if retry is enabled
        if (retry && response.status >= 500 && attempt < maxRetries) {
          logger.warn(`API Request failed with ${response.status}, retrying...`, {
            attempt,
            maxRetries,
            path,
            status: response.status
          });

          lastError = new Error(`HTTP ${response.status}: ${errorText}`);
          await sleep(retryDelay * attempt); // Exponential backoff
          continue;
        }

        // Don't retry 4xx errors (client errors)
        const error = `HTTP ${response.status}: ${errorText}`;
        logApiRequest(method, path, response.status, duration, new Error(error));

        return {
          error: getUserFriendlyError(response.status, errorText),
          success: false
        };
      }

      // Parse response
      const data = await response.json();

      return {
        data,
        success: true
      };

    } catch (error) {
      clearTimeout(timeoutId);

      const duration = performance.now() - startTime;

      // Handle abort (timeout)
      if (error instanceof Error && error.name === 'AbortError') {
        const timeoutError = new Error(`Request timeout after ${timeoutMs}ms`);

        // Log timeout error
        logApiRequest(method, path, undefined, duration, timeoutError);

        // Retry on timeout if enabled
        if (retry && attempt < maxRetries) {
          logger.warn(`Request timeout, retrying...`, {
            attempt,
            maxRetries,
            path,
            timeout: timeoutMs
          });

          lastError = timeoutError;
          await sleep(retryDelay * attempt);
          continue;
        }

        return {
          error: `Request timed out after ${timeoutMs / 1000} seconds. Please check your connection and try again.`,
          success: false
        };
      }

      // Handle network errors
      if (error instanceof TypeError && error.message.includes('fetch')) {
        const networkError = new Error('Network request failed');
        logApiRequest(method, path, undefined, duration, networkError);

        // Retry network errors if enabled
        if (retry && attempt < maxRetries) {
          logger.warn('Network error, retrying...', {
            attempt,
            maxRetries,
            path
          });

          lastError = networkError;
          await sleep(retryDelay * attempt);
          continue;
        }

        return {
          error: 'Network error. Please check your internet connection and try again.',
          success: false
        };
      }

      // Handle other errors
      lastError = error instanceof Error ? error : new Error('Unknown error');
      logApiRequest(method, path, undefined, duration, lastError);

      // Retry generic errors if enabled
      if (retry && attempt < maxRetries) {
        logger.warn('Request failed, retrying...', {
          attempt,
          maxRetries,
          path,
          error: lastError.message
        });

        await sleep(retryDelay * attempt);
        continue;
      }

      return {
        error: lastError.message || 'An unexpected error occurred. Please try again.',
        success: false
      };
    }
  }

  // All retries exhausted
  logger.error(`API Request failed after ${maxRetries} attempts`, lastError || undefined, {
    path,
    method
  });

  return {
    error: lastError?.message || 'Request failed after multiple attempts. Please try again later.',
    success: false
  };
}

/**
 * Convert HTTP status codes and errors into user-friendly messages
 */
function getUserFriendlyError(status: number, errorText: string): string {
  switch (status) {
    case 400:
      return 'Invalid request. Please check your input and try again.';
    case 401:
      return 'Please log in to continue.';
    case 403:
      return 'You don\'t have permission to perform this action.';
    case 404:
      return 'The requested resource was not found.';
    case 409:
      return 'This action conflicts with existing data. Please refresh and try again.';
    case 422:
      return 'The data you provided is invalid. Please check and try again.';
    case 429:
      return 'Too many requests. Please wait a moment and try again.';
    case 500:
      return 'Server error. Our team has been notified. Please try again later.';
    case 502:
    case 503:
      return 'Service temporarily unavailable. Please try again in a few moments.';
    case 504:
      return 'Request timed out. Please try again.';
    default:
      return errorText || `An error occurred (${status}). Please try again.`;
  }
}

/**
 * Convenience methods for common HTTP verbs
 */
export const api = {
  get: <T = Record<string, unknown>>(path: string, options?: ApiRequestOptions) =>
    apiFetch<T>(path, { ...options, method: 'GET' }),

  post: <T = Record<string, unknown>>(
    path: string,
    data?: Record<string, unknown>,
    options?: ApiRequestOptions
  ) =>
    apiFetch<T>(path, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined
    }),

  put: <T = Record<string, unknown>>(
    path: string,
    data?: Record<string, unknown>,
    options?: ApiRequestOptions
  ) =>
    apiFetch<T>(path, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined
    }),

  patch: <T = Record<string, unknown>>(
    path: string,
    data?: Record<string, unknown>,
    options?: ApiRequestOptions
  ) =>
    apiFetch<T>(path, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined
    }),

  delete: <T = Record<string, unknown>>(path: string, options?: ApiRequestOptions) =>
    apiFetch<T>(path, { ...options, method: 'DELETE' })
}

/**
 * Stripe-specific API calls (to be migrated to backend)
 */
export const stripeApi = {
  createPaymentIntent: async (data: StripePaymentData) =>
    api.post('/api/v1/payments/create-intent', data),

  getCustomerDashboard: async (customerId: string) =>
    api.get(`/api/v1/customers/dashboard?customer_id=${customerId}`),

  createPortalSession: async (customerId: string) =>
    api.post('/api/v1/customers/portal', { customer_id: customerId })
}

/**
 * Environment validation
 */
if (typeof window !== 'undefined') {
  // Client-side validation
  if (!process.env.NEXT_PUBLIC_API_URL) {
    console.warn('NEXT_PUBLIC_API_URL not set, using default:', API_BASE_URL)
  }
}

export { API_BASE_URL }
