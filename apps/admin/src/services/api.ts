/**
 * Admin API Service
 * Handles all backend communication for the admin dashboard
 */

import { api } from '@/lib/api';
import type {
  ApiResponse,
  Booking,
  BookingFilters,
  Customer,
  CustomerFilters,
  DashboardStats,
  Invoice,
  Payment,
} from '@/types';

// Base API endpoints
const ENDPOINTS = {
  // CRM endpoints
  bookings: '/api/crm/bookings',
  customers: '/api/crm/customers',
  dashboard: '/api/crm/dashboard/stats',
  availability: '/api/crm/availability',
  
  // Auth endpoints  
  auth: '/api/auth',
  
  // Health endpoints
  health: '/api/health',
  
  // Stripe endpoints
  payments: '/api/stripe/payments',
  invoices: '/api/stripe/invoices',
} as const;

/**
 * Authentication service
 */
export const authService = {
  /**
   * Login with admin credentials
   */
  async login(email: string, password: string) {
    return api.post<{ access_token: string; token_type: string }>(
      `${ENDPOINTS.auth}/login`,
      { 
        username: email, // FastAPI uses 'username' field
        password,
        grant_type: 'password'
      }
    );
  },

  /**
   * Get current user info
   */
  async getCurrentUser() {
    return api.get<any>(`${ENDPOINTS.auth}/me`);
  },

  /**
   * Refresh token
   */
  async refreshToken() {
    return api.post<{ access_token: string; token_type: string }>(
      `${ENDPOINTS.auth}/refresh`
    );
  },
};

/**
 * Booking service
 */
export const bookingService = {
  /**
   * Get all bookings with optional filters and pagination
   */
  async getBookings(filters: BookingFilters = {}) {
    const params = new URLSearchParams();
    
    if (filters.page) params.append('page', filters.page.toString());
    if (filters.limit) params.append('limit', filters.limit.toString());
    if (filters.sort_by) params.append('sort_by', filters.sort_by);
    if (filters.sort_order) params.append('sort_order', filters.sort_order);
    if (filters.status) params.append('status', filters.status);
    if (filters.payment_status) params.append('payment_status', filters.payment_status);
    if (filters.date_from) params.append('date_from', filters.date_from);
    if (filters.date_to) params.append('date_to', filters.date_to);
    if (filters.customer_search) params.append('customer_search', filters.customer_search);

    const query = params.toString();
    const url = query ? `${ENDPOINTS.bookings}?${query}` : ENDPOINTS.bookings;
    
    return api.get<ApiResponse<Booking[]>>(url);
  },

  /**
   * Get a specific booking by ID
   */
  async getBooking(bookingId: string) {
    return api.get<ApiResponse<Booking>>(`${ENDPOINTS.bookings}/${bookingId}`);
  },

  /**
   * Create a new booking
   */
  async createBooking(booking: Partial<Booking>) {
    return api.post<ApiResponse<Booking>>(ENDPOINTS.bookings, booking);
  },

  /**
   * Update a booking
   */
  async updateBooking(bookingId: string, updates: Partial<Booking>) {
    return api.put<ApiResponse<Booking>>(`${ENDPOINTS.bookings}/${bookingId}`, updates);
  },

  /**
   * Cancel a booking
   */
  async cancelBooking(bookingId: string, reason: string, refundAmount: number = 0) {
    return api.delete<ApiResponse<void>>(`${ENDPOINTS.bookings}/${bookingId}`, {
      body: JSON.stringify({
        cancellation_reason: reason,
        refund_amount_cents: refundAmount,
      }),
    });
  },

  /**
   * Record a payment for a booking
   */
  async recordPayment(bookingId: string, payment: Partial<Payment>) {
    return api.post<ApiResponse<Payment>>(
      `${ENDPOINTS.bookings}/${bookingId}/payments`,
      payment
    );
  },
};

/**
 * Customer service
 */
export const customerService = {
  /**
   * Get all customers with optional filters and pagination
   */
  async getCustomers(filters: CustomerFilters = {}) {
    const params = new URLSearchParams();
    
    if (filters.page) params.append('page', filters.page.toString());
    if (filters.limit) params.append('limit', filters.limit.toString());
    if (filters.sort_by) params.append('sort_by', filters.sort_by);
    if (filters.sort_order) params.append('sort_order', filters.sort_order);
    if (filters.status) params.append('status', filters.status);
    if (filters.search) params.append('search', filters.search);

    const query = params.toString();
    const url = query ? `${ENDPOINTS.customers}?${query}` : ENDPOINTS.customers;
    
    return api.get<ApiResponse<Customer[]>>(url);
  },

  /**
   * Get customer by ID
   */
  async getCustomer(customerId: string) {
    return api.get<ApiResponse<Customer>>(`${ENDPOINTS.customers}/${customerId}`);
  },

  /**
   * Get customer bookings
   */
  async getCustomerBookings(customerId: string) {
    return api.get<ApiResponse<Booking[]>>(`${ENDPOINTS.customers}/${customerId}/bookings`);
  },
};

/**
 * Dashboard service
 */
export const dashboardService = {
  /**
   * Get dashboard statistics
   */
  async getStats() {
    return api.get<ApiResponse<DashboardStats>>(ENDPOINTS.dashboard);
  },

  /**
   * Get availability data
   */
  async getAvailability(date?: string) {
    const url = date ? `${ENDPOINTS.availability}?date=${date}` : ENDPOINTS.availability;
    return api.get<ApiResponse<any>>(url);
  },
};

/**
 * Payment service
 */
export const paymentService = {
  /**
   * Get all payments
   */
  async getPayments(filters: any = {}) {
    const params = new URLSearchParams(filters);
    const query = params.toString();
    const url = query ? `${ENDPOINTS.payments}?${query}` : ENDPOINTS.payments;
    
    return api.get<ApiResponse<Payment[]>>(url);
  },

  /**
   * Get payment analytics
   */
  async getPaymentAnalytics(period?: string) {
    const url = period 
      ? `${ENDPOINTS.payments}/analytics?period=${period}` 
      : `${ENDPOINTS.payments}/analytics`;
    return api.get<ApiResponse<any>>(url);
  },
};

/**
 * Invoice service
 */
export const invoiceService = {
  /**
   * Get all invoices
   */
  async getInvoices(filters: any = {}) {
    const params = new URLSearchParams(filters);
    const query = params.toString();
    const url = query ? `${ENDPOINTS.invoices}?${query}` : ENDPOINTS.invoices;
    
    return api.get<ApiResponse<Invoice[]>>(url);
  },

  /**
   * Get invoice by ID
   */
  async getInvoice(invoiceId: string) {
    return api.get<ApiResponse<Invoice>>(`${ENDPOINTS.invoices}/${invoiceId}`);
  },

  /**
   * Create invoice
   */
  async createInvoice(invoice: Partial<Invoice>) {
    return api.post<ApiResponse<Invoice>>(ENDPOINTS.invoices, invoice);
  },
};

/**
 * Health service
 */
export const healthService = {
  /**
   * Check API health
   */
  async checkHealth() {
    return api.get<any>(ENDPOINTS.health);
  },

  /**
   * Check database health
   */
  async checkDatabaseHealth() {
    return api.get<any>(`${ENDPOINTS.health}/db`);
  },
};

/**
 * Token management utilities
 */
export const tokenManager = {
  getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('admin_token');
  },

  setToken(token: string): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem('admin_token', token);
  },

  removeToken(): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem('admin_token');
  },

  getAuthHeaders(): Record<string, string> {
    const token = this.getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  },
};

/**
 * Add token to all requests
 */
export const apiWithAuth = {
  get: <T = any>(path: string, options: any = {}) =>
    api.get<T>(path, {
      ...options,
      headers: {
        ...tokenManager.getAuthHeaders(),
        ...options.headers,
      },
    }),

  post: <T = any>(path: string, data?: any, options: any = {}) =>
    api.post<T>(path, data, {
      ...options,
      headers: {
        ...tokenManager.getAuthHeaders(),
        ...options.headers,
      },
    }),

  put: <T = any>(path: string, data?: any, options: any = {}) =>
    api.put<T>(path, data, {
      ...options,
      headers: {
        ...tokenManager.getAuthHeaders(),
        ...options.headers,
      },
    }),

  patch: <T = any>(path: string, data?: any, options: any = {}) =>
    api.patch<T>(path, data, {
      ...options,
      headers: {
        ...tokenManager.getAuthHeaders(),
        ...options.headers,
      },
    }),

  delete: <T = any>(path: string, options: any = {}) =>
    api.delete<T>(path, {
      ...options,
      headers: {
        ...tokenManager.getAuthHeaders(),
        ...options.headers,
      },
    }),
};