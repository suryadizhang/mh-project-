/**
 * Unified API client for My Hibachi frontend
 * All backend communication should go through this module
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003';

// Type definitions
export interface ApiResponse<T = Record<string, unknown>> {
  data?: T;
  error?: string;
  message?: string;
  success: boolean;
}

export interface ApiRequestOptions extends RequestInit {
  timeout?: number;
}

export interface StripePaymentData {
  amount: number;
  customer_email: string;
  customer_name: string;
  [key: string]: unknown;
}

/**
 * Main API fetch function - all backend calls should use this
 */
export async function apiFetch<T = Record<string, unknown>>(
  path: string,
  options: ApiRequestOptions = {}
): Promise<ApiResponse<T>> {
  const { timeout = 10000, ...fetchOptions } = options;

  const url = `${API_BASE_URL}${path}`;

  // Generate request ID for distributed tracing
  const requestId = crypto.randomUUID();

  // Setup abort controller for timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    console.log('Fetching:', url);

    const response = await fetch(url, {
      ...fetchOptions,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        'X-Request-ID': requestId, // Add request ID for distributed tracing
        ...fetchOptions.headers,
      },
    });

    console.log('Response received:', response.status, response.statusText);
    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`API Error [${response.status}]:`, errorText);
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    console.log('Data parsed:', data);
    return {
      data,
      success: true,
    };
  } catch (error) {
    clearTimeout(timeoutId);

    // Extract all error details
    let errorMessage = 'Unknown error occurred';

    console.log('=== API FETCH ERROR DEBUG ===');
    console.log('URL:', url);
    console.log('Method:', fetchOptions.method || 'GET');
    console.log('Error type:', typeof error);
    console.log('Error instanceof Error:', error instanceof Error);
    console.log('Error constructor:', error?.constructor?.name);
    console.log(
      'Error keys:',
      error && typeof error === 'object' ? Object.keys(error) : 'N/A'
    );
    console.log('Error toString:', String(error));

    if (error instanceof Error) {
      errorMessage = error.message;
      console.log('Error name:', error.name);
      console.log('Error message:', error.message);
      console.log('Error stack:', error.stack);
    } else {
      console.log('Error value:', error);
      try {
        console.log('Error JSON:', JSON.stringify(error));
      } catch (e) {
        console.log('Cannot stringify error');
      }
    }
    console.log('=== END DEBUG ===');

    return {
      error: errorMessage,
      success: false,
    };
  }
}

/**
 * Convenience methods for common HTTP verbs
 */
export const api = {
  get: <T = Record<string, unknown>>(
    path: string,
    options?: ApiRequestOptions
  ) => apiFetch<T>(path, { ...options, method: 'GET' }),

  post: <T = Record<string, unknown>>(
    path: string,
    data?: Record<string, unknown>,
    options?: ApiRequestOptions
  ) =>
    apiFetch<T>(path, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    }),

  put: <T = Record<string, unknown>>(
    path: string,
    data?: Record<string, unknown>,
    options?: ApiRequestOptions
  ) =>
    apiFetch<T>(path, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    }),

  patch: <T = Record<string, unknown>>(
    path: string,
    data?: Record<string, unknown>,
    options?: ApiRequestOptions
  ) =>
    apiFetch<T>(path, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    }),

  delete: <T = Record<string, unknown>>(
    path: string,
    options?: ApiRequestOptions
  ) => apiFetch<T>(path, { ...options, method: 'DELETE' }),
};

/**
 * Chef types and API
 */
export interface Chef {
  id: string;
  name: string;
  phone?: string;
  email?: string;
  is_active: boolean;
  is_lead_chef: boolean;
  hire_date?: string;
  avatar_url?: string;
  color?: string;
}

export interface StationChefListResponse {
  success: boolean;
  chefs: Chef[];
  total: number;
  message?: string;
}

/**
 * Chef-related API calls
 */
export const chefService = {
  /**
   * Get all chefs for the current user's station
   * Endpoint: GET /api/v1/chef-portal/station/chefs
   */
  getStationChefs: async () =>
    api.get<StationChefListResponse>('/api/v1/chef-portal/station/chefs'),
};

/**
 * Booking types and API
 */
export interface Booking {
  id: string;
  booking_id?: number;
  date: string;
  time?: string;
  slot?: string;
  status: string;
  customer_name?: string;
  customer_email?: string;
  customer_phone?: string;
  party_adults?: number;
  party_kids?: number;
  guests?: number;
  total_due_cents?: number;
  chef_id?: string | null;
  chef_name?: string | null;
  station_id?: string;
  address_encrypted?: string;
  location_address?: string;
  special_requests?: string;
  created_at?: string;
}

export interface BookingListResponse {
  items: Booking[];
  total: number;
  page: number;
  limit: number;
  success?: boolean;
}

export interface BookingUpdateData {
  date?: string;
  time?: string;
  guests?: number;
  location_address?: string;
  special_requests?: string;
  status?: string;
  chef_id?: string | null;
}

export interface BookingUpdateResponse {
  id: string;
  message: string;
  date?: string;
  time?: string;
  guests?: number;
  status?: string;
  chef_id?: string | null;
  changes?: string[];
}

/**
 * Booking-related API calls
 */
export const bookingService = {
  /**
   * Get bookings with optional filters
   * Endpoint: GET /api/v1/crm/bookings
   */
  getBookings: async (params?: {
    dateFrom?: string;
    dateTo?: string;
    status?: string;
    page?: number;
    limit?: number;
  }) => {
    const searchParams = new URLSearchParams();
    if (params?.dateFrom) searchParams.append('date_from', params.dateFrom);
    if (params?.dateTo) searchParams.append('date_to', params.dateTo);
    if (params?.status) searchParams.append('status', params.status);
    if (params?.page) searchParams.append('page', String(params.page));
    if (params?.limit) searchParams.append('limit', String(params.limit));

    const queryString = searchParams.toString();
    return api.get<BookingListResponse>(
      `/api/v1/crm/bookings${queryString ? `?${queryString}` : ''}`
    );
  },

  /**
   * Update a booking (including chef assignment)
   * Endpoint: PUT /api/v1/bookings/{booking_id}
   */
  updateBooking: async (bookingId: string, data: BookingUpdateData) =>
    api.put<BookingUpdateResponse>(
      `/api/v1/bookings/${bookingId}`,
      data as Record<string, unknown>
    ),

  /**
   * Assign a chef to a booking
   */
  assignChef: async (bookingId: string, chefId: string) =>
    api.put<BookingUpdateResponse>(`/api/v1/bookings/${bookingId}`, {
      chef_id: chefId,
    }),

  /**
   * Unassign chef from a booking
   */
  unassignChef: async (bookingId: string) =>
    api.put<BookingUpdateResponse>(`/api/v1/bookings/${bookingId}`, {
      chef_id: null,
    }),
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
