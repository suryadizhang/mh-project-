/**
 * Enhanced API Client with Error Handling
 * Wrapper around the base API client with automatic error parsing and retry logic
 */

import { api, type ApiRequestOptions, type ApiResponse } from './api';
import { parseApiError, retryWithBackoff, type RetryConfig } from './error-handler';

export interface EnhancedApiOptions extends ApiRequestOptions {
  retry?: boolean | Partial<RetryConfig>;
  throwOnError?: boolean;
}

/**
 * Enhanced API client with error handling and retry logic
 */
export const enhancedApi = {
  /**
   * GET request with error handling
   */
  async get<T = Record<string, unknown>>(
    path: string,
    options: EnhancedApiOptions = {}
  ): Promise<ApiResponse<T>> {
    const { retry = false, throwOnError = false, ...apiOptions } = options;

    const makeRequest = () => api.get<T>(path, apiOptions);

    try {
      if (retry) {
        const retryConfig = typeof retry === 'object' ? retry : undefined;
        return await retryWithBackoff(makeRequest, retryConfig);
      }

      return await makeRequest();
    } catch (error) {
      const errorDetails = parseApiError(error);
      console.error(`API GET ${path} failed:`, errorDetails);

      if (throwOnError) {
        throw new Error(errorDetails.message);
      }

      return {
        success: false,
        error: errorDetails.message,
      };
    }
  },

  /**
   * POST request with error handling
   */
  async post<T = Record<string, unknown>>(
    path: string,
    data?: Record<string, unknown>,
    options: EnhancedApiOptions = {}
  ): Promise<ApiResponse<T>> {
    const { retry = false, throwOnError = false, ...apiOptions } = options;

    const makeRequest = () => api.post<T>(path, data, apiOptions);

    try {
      if (retry) {
        const retryConfig = typeof retry === 'object' ? retry : undefined;
        return await retryWithBackoff(makeRequest, retryConfig);
      }

      return await makeRequest();
    } catch (error) {
      const errorDetails = parseApiError(error);
      console.error(`API POST ${path} failed:`, errorDetails);

      if (throwOnError) {
        throw new Error(errorDetails.message);
      }

      return {
        success: false,
        error: errorDetails.message,
      };
    }
  },

  /**
   * PUT request with error handling
   */
  async put<T = Record<string, unknown>>(
    path: string,
    data?: Record<string, unknown>,
    options: EnhancedApiOptions = {}
  ): Promise<ApiResponse<T>> {
    const { retry = false, throwOnError = false, ...apiOptions } = options;

    const makeRequest = () => api.put<T>(path, data, apiOptions);

    try {
      if (retry) {
        const retryConfig = typeof retry === 'object' ? retry : undefined;
        return await retryWithBackoff(makeRequest, retryConfig);
      }

      return await makeRequest();
    } catch (error) {
      const errorDetails = parseApiError(error);
      console.error(`API PUT ${path} failed:`, errorDetails);

      if (throwOnError) {
        throw new Error(errorDetails.message);
      }

      return {
        success: false,
        error: errorDetails.message,
      };
    }
  },

  /**
   * PATCH request with error handling
   */
  async patch<T = Record<string, unknown>>(
    path: string,
    data?: Record<string, unknown>,
    options: EnhancedApiOptions = {}
  ): Promise<ApiResponse<T>> {
    const { retry = false, throwOnError = false, ...apiOptions } = options;

    const makeRequest = () => api.patch<T>(path, data, apiOptions);

    try {
      if (retry) {
        const retryConfig = typeof retry === 'object' ? retry : undefined;
        return await retryWithBackoff(makeRequest, retryConfig);
      }

      return await makeRequest();
    } catch (error) {
      const errorDetails = parseApiError(error);
      console.error(`API PATCH ${path} failed:`, errorDetails);

      if (throwOnError) {
        throw new Error(errorDetails.message);
      }

      return {
        success: false,
        error: errorDetails.message,
      };
    }
  },

  /**
   * DELETE request with error handling
   */
  async delete<T = Record<string, unknown>>(
    path: string,
    options: EnhancedApiOptions = {}
  ): Promise<ApiResponse<T>> {
    const { retry = false, throwOnError = false, ...apiOptions } = options;

    const makeRequest = () => api.delete<T>(path, apiOptions);

    try {
      if (retry) {
        const retryConfig = typeof retry === 'object' ? retry : undefined;
        return await retryWithBackoff(makeRequest, retryConfig);
      }

      return await makeRequest();
    } catch (error) {
      const errorDetails = parseApiError(error);
      console.error(`API DELETE ${path} failed:`, errorDetails);

      if (throwOnError) {
        throw new Error(errorDetails.message);
      }

      return {
        success: false,
        error: errorDetails.message,
      };
    }
  },
};

/**
 * Convenience hook for API calls with toast notifications
 * Usage:
 * 
 * const { execute, loading } = useApiCall(async () => {
 *   return api.post('/endpoint', data);
 * });
 * 
 * await execute({
 *   successMessage: 'Operation completed',
 *   errorMessage: 'Operation failed',
 * });
 */
export function createApiCallHook() {
  // This would be better as a React hook, but keeping it simple for now
  return {
    execute: async <T>(
      fn: () => Promise<ApiResponse<T>>,
      options?: {
        successMessage?: string;
        errorMessage?: string;
        onSuccess?: (data: T) => void;
        onError?: (error: string) => void;
      }
    ) => {
      try {
        const response = await fn();

        if (response.success && response.data) {
          options?.onSuccess?.(response.data);
          return { success: true, data: response.data };
        } else {
          options?.onError?.(response.error || 'Request failed');
          return { success: false, error: response.error };
        }
      } catch (error) {
        const errorDetails = parseApiError(error);
        options?.onError?.(errorDetails.message);
        return { success: false, error: errorDetails.message };
      }
    },
  };
}
