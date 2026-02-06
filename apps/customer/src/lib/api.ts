/**
 * Unified API client for My Hibachi frontend
 * All backend communication should go through this module
 *
 * Features:
 * - Configurable timeouts per endpoint type
 * - Automatic retry logic for failed requests
 * - Client-side rate limiting (token bucket)
 * - 429 response handling with Retry-After
 * - Request/response logging
 * - Error handling with user-friendly messages
 * - Abort controller for timeout management
 * - **NEW**: Automatic response validation with Zod schemas
 */

import type { z } from 'zod';
import { safeValidateResponse } from '@myhibachi/types/validators';

import { logger, logApiRequest } from '@/lib/logger';
import { getRateLimiter } from '@/lib/rateLimiter';
import { getCacheService, type CacheStrategy } from '@/lib/cacheService';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Type definitions
export interface ApiResponse<T = Record<string, unknown>> {
  data?: T;
  error?: string;
  message?: string;
  success: boolean;
}

export interface ApiRequestOptions extends RequestInit {
  timeout?: number;
  retry?: boolean;
  maxRetries?: number;
  retryDelay?: number;
  schema?: z.ZodType; // Zod schema for automatic response validation
  cacheStrategy?: {
    strategy: CacheStrategy; // Cache strategy to use
    ttl: number; // Time-to-live in milliseconds
    key?: string; // Custom cache key (defaults to method:path)
  };
}

export interface StripePaymentData {
  amount: number;
  customer_email: string;
  customer_name: string;
  [key: string]: unknown;
}

/**
 * Timeout configuration for different endpoint types
 * Longer timeouts for complex operations, shorter for quick lookups
 */
export const TIMEOUT_CONFIG = {
  // Complex operations
  BOOKING_CREATE: 45000, // 45s - Complex validation and database operations
  PAYMENT_PROCESS: 60000, // 60s - Stripe processing time + webhooks
  FILE_UPLOAD: 120000, // 120s - Large image uploads
  REPORT_GENERATE: 90000, // 90s - Report generation with data aggregation

  // Standard operations
  BOOKING_UPDATE: 30000, // 30s - Update operations
  BOOKING_DELETE: 20000, // 20s - Delete operations
  CUSTOMER_UPDATE: 30000, // 30s - Customer profile updates

  // Quick lookups
  BOOKING_LIST: 15000, // 15s - List operations with pagination
  BOOKING_GET: 10000, // 10s - Single record retrieval
  AVAILABILITY_CHECK: 10000, // 10s - Availability queries (cached)
  DASHBOARD_DATA: 15000, // 15s - Dashboard data (may have multiple queries)

  // Real-time operations
  CHAT_MESSAGE: 30000, // 30s - AI chat responses
  WEBSOCKET: 5000, // 5s - WebSocket connections

  // Default fallback
  DEFAULT: 30000, // 30s - Default for unspecified endpoints
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
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Main API fetch function - all backend calls should use this
 *
 * Features:
 * - Client-side rate limiting (checked before request)
 * - Automatic timeout based on endpoint type
 * - Retry logic for transient failures (network errors, 5xx, 429 errors)
 * - 429 response handling with Retry-After header
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
  options: ApiRequestOptions = {},
): Promise<ApiResponse<T>> {
  const {
    timeout,
    retry = true,
    maxRetries = 3,
    retryDelay = 1000,
    schema,
    cacheStrategy: cacheConfig,
    ...fetchOptions
  } = options;

  // Determine timeout: explicit > endpoint-specific > default
  const method = (fetchOptions.method || 'GET').toUpperCase();
  const timeoutMs = timeout ?? getTimeoutForEndpoint(path, method);

  const url = `${API_BASE_URL}${path}`;
  const startTime = performance.now();

  // Get rate limiter instance
  const rateLimiter = getRateLimiter();

  // Generate cache key
  const cacheKey = cacheConfig?.key || `${method}:${path}`;

  // Generate request ID for distributed tracing
  const requestId = crypto.randomUUID();

  // Check if caching is enabled and method is cacheable (GET requests only)
  const isCacheable = cacheConfig && method === 'GET';

  // If caching enabled, try to fetch from cache using the appropriate strategy
  if (isCacheable) {
    const cacheService = getCacheService();
    const { strategy, ttl } = cacheConfig;

    logger.debug(`Using cache strategy: ${strategy}`, {
      path,
      cacheKey,
      ttl,
    });

    try {
      // Define the fetcher function for cache strategies
      const fetcher = async (): Promise<T> => {
        // Execute the full API fetch logic (rate limiting, retries, validation)
        const response = await executeFetch<T>(
          url,
          path,
          method,
          timeoutMs,
          fetchOptions,
          retry,
          maxRetries,
          retryDelay,
          schema,
          rateLimiter,
          startTime,
          requestId, // Pass request ID
        );

        if (!response.success || !response.data) {
          throw new Error(response.error || 'API request failed');
        }

        return response.data;
      };

      // Use the appropriate cache strategy
      let data: T;

      switch (strategy) {
        case 'cache-first':
          data = await cacheService.cacheFirst<T>(cacheKey, ttl, fetcher);
          break;

        case 'stale-while-revalidate':
          data = await cacheService.staleWhileRevalidate<T>(cacheKey, ttl, fetcher);
          break;

        case 'network-first':
          data = await cacheService.networkFirst<T>(cacheKey, ttl, fetcher);
          break;

        default:
          // Fallback to network fetch if strategy unknown
          logger.warn(`Unknown cache strategy: ${strategy}, falling back to network fetch`);
          return await executeFetch<T>(
            url,
            path,
            method,
            timeoutMs,
            fetchOptions,
            retry,
            maxRetries,
            retryDelay,
            schema,
            rateLimiter,
            startTime,
            requestId, // Pass request ID
          );
      }

      return {
        data,
        success: true,
      };
    } catch (error) {
      // Cache strategy failed, return error
      logger.error('Cache strategy execution failed', error instanceof Error ? error : undefined, {
        path,
        strategy,
        cacheKey,
      });

      return {
        error: error instanceof Error ? error.message : 'Cache operation failed',
        success: false,
      };
    }
  }

  // No caching - execute normal fetch
  // For mutations (POST, PUT, PATCH, DELETE), also invalidate related cache
  if (!isCacheable && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    logger.debug(`Mutation detected: ${method} ${path}, will invalidate cache after success`);
  }

  const response = await executeFetch<T>(
    url,
    path,
    method,
    timeoutMs,
    fetchOptions,
    retry,
    maxRetries,
    retryDelay,
    schema,
    rateLimiter,
    startTime,
    requestId, // Pass request ID
  );

  // If mutation was successful, invalidate related cache entries
  if (response.success && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    invalidateCacheForMutation(method, path);
  }

  return response;
}

/**
 * Execute the actual fetch request with all retry/timeout/validation logic
 * Extracted into separate function to be reusable by cache strategies
 */
async function executeFetch<T>(
  url: string,
  path: string,
  method: string,
  timeoutMs: number,
  fetchOptions: RequestInit,
  retry: boolean,
  maxRetries: number,
  retryDelay: number,
  schema: z.ZodType | undefined,
  rateLimiter: ReturnType<typeof getRateLimiter>,
  startTime: number,
  requestId: string, // Add request ID parameter
): Promise<ApiResponse<T>> {
  // Check client-side rate limit BEFORE making request
  if (!rateLimiter.checkLimit(path)) {
    const waitTime = rateLimiter.getWaitTime(path);
    const info = rateLimiter.getInfo(path);

    logger.warn('Client-side rate limit exceeded', {
      path,
      category: info.category,
      waitTime,
      remaining: info.remaining,
    });

    // Emit rate limit event for UI
    if (typeof window !== 'undefined') {
      window.dispatchEvent(
        new CustomEvent('rate-limit-exceeded', {
          detail: {
            endpoint: path,
            waitTime,
            category: info.category,
            remaining: info.remaining,
          },
        }),
      );
    }

    return {
      error: `Rate limit exceeded. Please wait ${waitTime} second${waitTime !== 1 ? 's' : ''} before trying again.`,
      success: false,
    };
  }

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
        timeout: timeoutMs,
        requestId, // Log request ID for tracing
      });

      const response = await fetch(url, {
        ...fetchOptions,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          'X-Request-ID': requestId, // Add request ID for distributed tracing
          ...fetchOptions.headers,
        },
      });

      clearTimeout(timeoutId);

      const duration = performance.now() - startTime;

      // Log successful request
      logApiRequest(method, path, response.status, duration);

      if (!response.ok) {
        // Server returned error status
        const errorText = await response.text().catch(() => 'Unknown error');

        // Handle 429 Rate Limit Exceeded with Retry-After
        if (response.status === 429) {
          const retryAfter = response.headers.get('Retry-After');
          let waitSeconds = parseInt(retryAfter || '60', 10);

          // Retry-After can be seconds or HTTP date
          if (isNaN(waitSeconds)) {
            // Try parsing as HTTP date
            const retryDate = new Date(retryAfter || '');
            if (!isNaN(retryDate.getTime())) {
              waitSeconds = Math.ceil((retryDate.getTime() - Date.now()) / 1000);
            } else {
              waitSeconds = 60; // Default to 60 seconds
            }
          }

          logger.warn('Server rate limit exceeded (429)', {
            path,
            waitSeconds,
            retryAfter,
            attempt,
            maxRetries,
          });

          // Store rate limit info in sessionStorage for UI
          if (typeof window !== 'undefined') {
            const rateLimitInfo = {
              endpoint: path,
              until: Date.now() + waitSeconds * 1000,
              waitSeconds,
            };
            sessionStorage.setItem(`rate-limit-429-${path}`, JSON.stringify(rateLimitInfo));

            // Emit event for UI components
            window.dispatchEvent(
              new CustomEvent('server-rate-limit-exceeded', {
                detail: rateLimitInfo,
              }),
            );
          }

          // Retry with exponential backoff if enabled
          if (retry && attempt < maxRetries) {
            const backoffDelay = Math.min(waitSeconds * 1000, retryDelay * Math.pow(2, attempt));
            logger.info(`Retrying after ${backoffDelay}ms due to 429...`, {
              attempt,
              maxRetries,
              path,
              waitSeconds,
              backoffDelay,
            });

            lastError = new Error(`Rate limit exceeded: ${errorText}`);
            await sleep(backoffDelay);
            continue;
          }

          return {
            error: `Too many requests. Please wait ${waitSeconds} second${waitSeconds !== 1 ? 's' : ''} before trying again.`,
            success: false,
          };
        }

        // Retry on 5xx errors (server errors) if retry is enabled
        if (retry && response.status >= 500 && attempt < maxRetries) {
          logger.warn(`API Request failed with ${response.status}, retrying...`, {
            attempt,
            maxRetries,
            path,
            status: response.status,
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
          success: false,
        };
      }

      // Parse response
      const data = await response.json();

      // Record successful request in rate limiter
      rateLimiter.recordRequest(path);

      // Validate response if schema provided
      if (schema) {
        const validationResult = safeValidateResponse(schema, data, {
          endpoint: path,
          method,
        });

        if (!validationResult.success) {
          // Validation failed - log detailed error
          logger.error(
            'API Response validation failed',
            new Error(validationResult.error || 'Unknown validation error'),
            {
              path,
              method,
              zodError: validationResult.zodError?.errors,
              receivedData: data,
            },
          );

          // Emit validation error event for UI
          if (typeof window !== 'undefined') {
            window.dispatchEvent(
              new CustomEvent('api-validation-error', {
                detail: {
                  endpoint: path,
                  method,
                  error: validationResult.error,
                  zodError: validationResult.zodError,
                  data,
                },
              }),
            );
          }

          return {
            error:
              'Invalid response from server. Please try again or contact support if the problem persists.',
            success: false,
          };
        }

        // Validation successful - return validated data
        logger.debug('API Response validated successfully', {
          path,
          method,
        });

        return {
          data: validationResult.data as T,
          success: true,
        };
      }

      // No schema provided - return raw data (backward compatible)
      return {
        data,
        success: true,
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
            timeout: timeoutMs,
          });

          lastError = timeoutError;
          await sleep(retryDelay * attempt);
          continue;
        }

        return {
          error: `Request timed out after ${timeoutMs / 1000} seconds. Please check your connection and try again.`,
          success: false,
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
            path,
          });

          lastError = networkError;
          await sleep(retryDelay * attempt);
          continue;
        }

        return {
          error: 'Network error. Please check your internet connection and try again.',
          success: false,
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
          error: lastError.message,
        });

        await sleep(retryDelay * attempt);
        continue;
      }

      return {
        error: lastError.message || 'An unexpected error occurred. Please try again.',
        success: false,
      };
    }
  }

  // All retries exhausted
  logger.error(`API Request failed after ${maxRetries} attempts`, lastError || undefined, {
    path,
    method,
  });

  return {
    error: lastError?.message || 'Request failed after multiple attempts. Please try again later.',
    success: false,
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
      return "You don't have permission to perform this action.";
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
 * Invalidate cache entries based on mutation type and endpoint
 * This ensures cache stays fresh after data modifications
 *
 * Invalidation Rules:
 * - Booking mutations: Clear booked-dates, availability, dashboard
 * - Customer mutations: Clear dashboard, profile
 * - Payment mutations: Clear dashboard
 * - Menu mutations: Clear menu cache
 */
function invalidateCacheForMutation(method: string, path: string): void {
  const cacheService = getCacheService();

  logger.debug(`Invalidating cache after ${method} ${path}`);

  try {
    // Booking mutations
    if (path.includes('/bookings')) {
      // Clear booking-related caches (both public and authenticated endpoints)
      cacheService.invalidate('GET:/api/v1/bookings/booked-dates');
      cacheService.invalidate('GET:/api/v1/public/bookings/booked-dates');
      cacheService.invalidate('GET:/api/v1/bookings/availability*'); // Wildcard for query params
      cacheService.invalidate('GET:/api/v1/public/bookings/available-times*');
      cacheService.invalidate('GET:/api/v1/customers/dashboard');

      // If specific booking modified, clear that too
      if (method !== 'POST') {
        cacheService.invalidate(`GET:${path}`);
      }

      logger.debug('Invalidated booking-related caches', { method, path });
    }

    // Customer mutations
    if (path.includes('/customers')) {
      cacheService.invalidate('GET:/api/v1/customers/dashboard');
      cacheService.invalidate('GET:/api/v1/customers/profile*');

      logger.debug('Invalidated customer-related caches', { method, path });
    }

    // Payment mutations
    if (path.includes('/payment')) {
      cacheService.invalidate('GET:/api/v1/customers/dashboard');

      logger.debug('Invalidated payment-related caches', { method, path });
    }

    // Menu mutations (admin only, but be safe)
    if (path.includes('/menu')) {
      cacheService.invalidate('GET:/api/v1/menu*');

      logger.debug('Invalidated menu caches', { method, path });
    }

    // Content mutations
    if (path.includes('/content')) {
      cacheService.invalidate('GET:/api/v1/content*');

      logger.debug('Invalidated content caches', { method, path });
    }
  } catch (error) {
    // Don't fail the request if cache invalidation fails
    logger.error('Cache invalidation failed', error instanceof Error ? error : undefined, {
      method,
      path,
    });
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
    options?: ApiRequestOptions,
  ) =>
    apiFetch<T>(path, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    }),

  put: <T = Record<string, unknown>>(
    path: string,
    data?: Record<string, unknown>,
    options?: ApiRequestOptions,
  ) =>
    apiFetch<T>(path, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    }),

  patch: <T = Record<string, unknown>>(
    path: string,
    data?: Record<string, unknown>,
    options?: ApiRequestOptions,
  ) =>
    apiFetch<T>(path, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    }),

  delete: <T = Record<string, unknown>>(path: string, options?: ApiRequestOptions) =>
    apiFetch<T>(path, { ...options, method: 'DELETE' }),
};

/**
 * Stripe-specific API calls (to be migrated to backend)
 */
export const stripeApi = {
  createPaymentIntent: async (data: StripePaymentData) =>
    api.post('/api/v1/payments/create-intent', data),

  getCustomerDashboard: async (customerId: string) =>
    api.get(`/api/v1/customers/dashboard?customer_id=${customerId}`),

  createPortalSession: async (customerId: string) =>
    api.post('/api/v1/customers/portal', { customer_id: customerId }),
};

/**
 * Environment validation
 */
if (typeof window !== 'undefined') {
  // Client-side validation
  if (!process.env.NEXT_PUBLIC_API_URL) {
    console.warn('NEXT_PUBLIC_API_URL not set, using default:', API_BASE_URL);
  }
}

export { API_BASE_URL };
