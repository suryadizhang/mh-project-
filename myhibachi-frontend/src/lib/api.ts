/**
 * Unified API client for My Hibachi frontend
 * All backend communication should go through this module
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Type definitions
export interface ApiResponse<T = Record<string, unknown>> {
  data?: T
  error?: string
  message?: string
  success: boolean
}

export interface ApiRequestOptions extends RequestInit {
  timeout?: number
}

export interface StripePaymentData {
  amount: number
  customer_email: string
  customer_name: string
  [key: string]: unknown
}

/**
 * Main API fetch function - all backend calls should use this
 */
export async function apiFetch<T = Record<string, unknown>>(
  path: string,
  options: ApiRequestOptions = {}
): Promise<ApiResponse<T>> {
  const { timeout = 10000, ...fetchOptions } = options

  const url = `${API_BASE_URL}${path}`

  // Setup abort controller for timeout
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeout)

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...fetchOptions.headers
      }
    })

    clearTimeout(timeoutId)

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const data = await response.json()
    return {
      data,
      success: true
    }
  } catch (error) {
    clearTimeout(timeoutId)

    if (error instanceof Error) {
      return {
        error: error.message,
        success: false
      }
    }

    return {
      error: 'Unknown error occurred',
      success: false
    }
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
