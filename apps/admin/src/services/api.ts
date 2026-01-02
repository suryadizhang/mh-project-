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

// Station-aware types
export interface StationContext {
  station_id: number;
  station_name: string;
  role: string;
  permissions: string[];
  is_super_admin: boolean;
}

export interface StationLoginRequest {
  email: string;
  password: string;
  station_id?: number;
}

export interface StationLoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  station_context: StationContext;
}

export interface Station {
  id: number | string; // UUID as string from backend
  code: string; // Station code e.g. "CA-FREMONT-001"
  name: string;
  display_name: string;
  description?: string;

  // Address fields
  address?: string;
  city?: string;
  state?: string;
  postal_code?: string;
  country?: string;
  location?: string; // Legacy - use address fields instead

  // Geocoding (from Google Maps API)
  lat?: number; // Latitude (DECIMAL 10,8)
  lng?: number; // Longitude (DECIMAL 11,8)
  geocode_status?: 'pending' | 'success' | 'failed';
  geocoded_at?: string;

  // Service area configuration
  service_area_radius?: number; // Miles - default 150
  escalation_radius_miles?: number; // When to require human approval - default 150

  // Contact info
  phone?: string;
  email?: string;
  timezone?: string; // IANA timezone e.g. "America/Los_Angeles"

  // Business settings
  status?: 'active' | 'inactive' | 'suspended' | 'maintenance';
  settings: Record<string, any>;
  business_hours?: Record<string, { open: string; close: string }>;
  max_concurrent_bookings?: number;
  booking_lead_time_hours?: number;
  branding_config?: Record<string, any>;

  // Metadata
  is_active: boolean;
  created_at: string;
  updated_at: string;

  // Statistics (optional)
  user_count?: number;
  booking_count?: number;
  active_booking_count?: number;
  total_booking_count?: number;
  last_activity?: string;
  manager_name?: string; // Primary manager/owner name
}

export interface StationUser {
  id: number;
  user_id: number;
  station_id: number;
  role: string;
  permissions: string[];
  assigned_at: string;
  assigned_by: number;
  is_active: boolean;
  user_email?: string;
  user_name?: string;
  last_login?: string;
}

export interface GeocodeStationResponse {
  success: boolean;
  station_id: string;
  lat?: number;
  lng?: number;
  geocode_status: 'pending' | 'success' | 'failed';
  geocoded_at?: string;
  full_address?: string;
  message: string;
}

export interface AuditLog {
  id: number;
  station_id: number;
  user_id: number;
  action: string;
  resource_type: string;
  resource_id?: string;
  details: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
  timestamp: string;
  user_email?: string;
  user_role?: string;
}

// Base API endpoints
const ENDPOINTS = {
  // CRM endpoints
  bookings: '/api/crm/bookings',
  customers: '/api/crm/customers',
  dashboard: '/api/crm/dashboard/stats',
  availability: '/api/crm/availability',

  // Auth endpoints
  auth: '/api/auth',
  stationAuth: '/api/station/station-login',

  // Station admin endpoints
  stations: '/api/admin/stations',

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
   * Login with admin credentials (legacy)
   */
  async login(email: string, password: string) {
    return api.post<{ access_token: string; token_type: string }>(
      `${ENDPOINTS.auth}/login`,
      {
        username: email, // FastAPI uses 'username' field
        password,
        grant_type: 'password',
      }
    );
  },

  /**
   * Station-aware login
   */
  async stationLogin(email: string, password: string, stationId?: number) {
    return api.post<StationLoginResponse>(ENDPOINTS.stationAuth, {
      email,
      password,
      station_id: stationId,
    });
  },

  /**
   * Get available stations for user
   */
  async getUserStations(email: string) {
    return api.get<Station[]>(
      `/api/station/user-stations?email=${encodeURIComponent(email)}`
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
   * Get all bookings with cursor-based pagination (MEDIUM #34 Phase 2)
   *
   * @param filters - Filter options
   * @param filters.cursor - Pagination cursor from previous response
   * @param filters.limit - Number of items per page (default: 50, max: 100)
   * @param filters.page - Legacy page number (deprecated, use cursor instead)
   *
   * Performance: O(1) regardless of page depth (150x faster for deep pages)
   */
  async getBookings(filters: BookingFilters = {}) {
    const params = new URLSearchParams();

    // Modern cursor-based pagination (preferred)
    if (filters.cursor) {
      params.append('cursor', filters.cursor);
    }

    // Legacy page-based pagination (fallback for backward compatibility)
    if (filters.page && !filters.cursor) {
      params.append('page', filters.page.toString());
    }

    if (filters.limit) params.append('limit', filters.limit.toString());
    if (filters.sort_by) params.append('sort_by', filters.sort_by);
    if (filters.sort_order) params.append('sort_order', filters.sort_order);
    if (filters.status) params.append('status', filters.status);
    if (filters.payment_status)
      params.append('payment_status', filters.payment_status);
    if (filters.date_from) params.append('date_from', filters.date_from);
    if (filters.date_to) params.append('date_to', filters.date_to);
    if (filters.customer_search)
      params.append('customer_search', filters.customer_search);

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
    return api.put<ApiResponse<Booking>>(
      `${ENDPOINTS.bookings}/${bookingId}`,
      updates
    );
  },

  /**
   * Cancel a booking (legacy - direct cancellation)
   */
  async cancelBooking(
    bookingId: string,
    reason: string,
    refundAmount: number = 0
  ) {
    return api.delete<ApiResponse<void>>(`${ENDPOINTS.bookings}/${bookingId}`, {
      body: JSON.stringify({
        cancellation_reason: reason,
        refund_amount_cents: refundAmount,
      }),
    });
  },

  /**
   * Request cancellation (2-step workflow - Step 1)
   * Creates CANCELLATION_REQUESTED status, slot remains held
   */
  async requestCancellation(bookingId: string, reason: string) {
    return api.post<ApiResponse<Booking>>(
      `${ENDPOINTS.bookings}/${bookingId}/request-cancellation`,
      { reason }
    );
  },

  /**
   * Approve cancellation request (2-step workflow - Step 2a)
   * Changes status to CANCELLED, releases slot
   */
  async approveCancellation(bookingId: string, adminNotes?: string) {
    return api.post<ApiResponse<Booking>>(
      `${ENDPOINTS.bookings}/${bookingId}/approve-cancellation`,
      { admin_notes: adminNotes }
    );
  },

  /**
   * Reject cancellation request (2-step workflow - Step 2b)
   * Restores original status, slot remains held
   */
  async rejectCancellation(bookingId: string, adminNotes?: string) {
    return api.post<ApiResponse<Booking>>(
      `${ENDPOINTS.bookings}/${bookingId}/reject-cancellation`,
      { admin_notes: adminNotes }
    );
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
    return api.get<ApiResponse<Customer>>(
      `${ENDPOINTS.customers}/${customerId}`
    );
  },

  /**
   * Get customer bookings
   */
  async getCustomerBookings(customerId: string) {
    return api.get<ApiResponse<Booking[]>>(
      `${ENDPOINTS.customers}/${customerId}/bookings`
    );
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
    const url = date
      ? `${ENDPOINTS.availability}?date=${date}`
      : ENDPOINTS.availability;
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
 * Station management service
 */
export const stationService = {
  /**
   * Get all stations
   */
  async getStations(includeStats: boolean = false) {
    const params = new URLSearchParams();
    if (includeStats) params.append('include_stats', 'true');

    const query = params.toString();
    const url = query ? `${ENDPOINTS.stations}?${query}` : ENDPOINTS.stations;

    return api.get<Station[]>(url);
  },

  /**
   * Get station by ID
   */
  async getStation(stationId: number, includeStats: boolean = false) {
    const params = new URLSearchParams();
    if (includeStats) params.append('include_stats', 'true');

    const query = params.toString();
    const url = query
      ? `${ENDPOINTS.stations}/${stationId}?${query}`
      : `${ENDPOINTS.stations}/${stationId}`;

    return api.get<Station>(url);
  },

  /**
   * Create new station (super admin only)
   */
  async createStation(station: Partial<Station>) {
    return api.post<Station>(ENDPOINTS.stations, station);
  },

  /**
   * Update station
   */
  async updateStation(stationId: number | string, updates: Partial<Station>) {
    return api.put<Station>(`${ENDPOINTS.stations}/${stationId}`, updates);
  },

  /**
   * Geocode station address using Google Maps API
   */
  async geocodeStation(stationId: number | string) {
    return api.post<GeocodeStationResponse>(
      `${ENDPOINTS.stations}/${stationId}/geocode`,
      {}
    );
  },

  /**
   * Get station users
   */
  async getStationUsers(
    stationId: number | string,
    includeUserDetails: boolean = false
  ) {
    const params = new URLSearchParams();
    if (includeUserDetails) params.append('include_user_details', 'true');

    const query = params.toString();
    const url = query
      ? `${ENDPOINTS.stations}/${stationId}/users?${query}`
      : `${ENDPOINTS.stations}/${stationId}/users`;

    return api.get<StationUser[]>(url);
  },

  /**
   * Assign user to station
   */
  async assignUserToStation(
    stationId: number | string,
    assignment: {
      user_id: number;
      role: string;
      permissions?: string[];
    }
  ) {
    return api.post<StationUser>(
      `${ENDPOINTS.stations}/${stationId}/users`,
      assignment
    );
  },

  /**
   * Update user station assignment
   */
  async updateUserStationAssignment(
    stationId: number | string,
    userId: number | string,
    updates: {
      role?: string;
      permissions?: string[];
      is_active?: boolean;
    }
  ) {
    return api.put<StationUser>(
      `${ENDPOINTS.stations}/${stationId}/users/${userId}`,
      updates
    );
  },

  /**
   * Remove user from station
   */
  async removeUserFromStation(
    stationId: number | string,
    userId: number | string
  ) {
    return api.delete<void>(
      `${ENDPOINTS.stations}/${stationId}/users/${userId}`
    );
  },

  /**
   * Get station audit logs
   */
  async getStationAuditLogs(
    stationId: number | string,
    filters: {
      action?: string;
      resource_type?: string;
      user_id?: number;
      days?: number;
      skip?: number;
      limit?: number;
    } = {}
  ) {
    const params = new URLSearchParams();

    if (filters.action) params.append('action', filters.action);
    if (filters.resource_type)
      params.append('resource_type', filters.resource_type);
    if (filters.user_id) params.append('user_id', filters.user_id.toString());
    if (filters.days) params.append('days', filters.days.toString());
    if (filters.skip) params.append('skip', filters.skip.toString());
    if (filters.limit) params.append('limit', filters.limit.toString());

    const query = params.toString();
    const url = query
      ? `${ENDPOINTS.stations}/${stationId}/audit?${query}`
      : `${ENDPOINTS.stations}/${stationId}/audit`;

    return api.get<AuditLog[]>(url);
  },
};

/**
 * Token management utilities with station context
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

  getStationContext(): StationContext | null {
    if (typeof window === 'undefined') return null;
    const stored = localStorage.getItem('station_context');
    if (!stored) return null;

    try {
      return JSON.parse(stored);
    } catch {
      return null;
    }
  },

  setStationContext(context: StationContext): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem('station_context', JSON.stringify(context));
  },

  removeStationContext(): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem('station_context');
  },

  getAuthHeaders(): Record<string, string> {
    const token = this.getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  },

  hasPermission(permission: string): boolean {
    const context = this.getStationContext();
    if (!context) return false;

    // Super admin has all permissions
    if (context.is_super_admin) return true;

    return context.permissions.includes(permission);
  },

  hasRole(role: string): boolean {
    const context = this.getStationContext();
    if (!context) return false;

    return context.role === role;
  },

  isSuperAdmin(): boolean {
    const context = this.getStationContext();
    return context?.is_super_admin || false;
  },
};

/**
 * Enhanced API with automatic authentication and station context
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

/**
 * Leads Management Service (CRM)
 */
export const leadService = {
  async getLeads(filters: any = {}) {
    const params = new URLSearchParams();
    Object.keys(filters).forEach(key => {
      if (filters[key] !== undefined && filters[key] !== '') {
        params.append(key, filters[key]);
      }
    });
    return api.get<{ data: any[]; total_count: number }>(
      `/api/leads?${params.toString()}`
    );
  },

  async getLead(leadId: string) {
    return api.get(`/api/leads/${leadId}`);
  },

  async createLead(data: any) {
    return api.post('/api/leads', data);
  },

  async updateLead(leadId: string, data: any) {
    return api.put(`/api/leads/${leadId}`, data);
  },

  async trackLeadEvent(leadId: string, event: any) {
    return api.post(`/api/leads/${leadId}/events`, event);
  },

  async getAIAnalysis(leadId: string) {
    return api.post(`/api/leads/${leadId}/ai-analysis`, {});
  },

  async getNurtureSequence(leadId: string) {
    return api.get(`/api/leads/${leadId}/nurture-sequence`);
  },
};

/**
 * Social Media Management Service
 */
export const socialService = {
  async getSocialThreads(filters: any = {}) {
    const params = new URLSearchParams();
    Object.keys(filters).forEach(key => {
      if (filters[key] !== undefined && filters[key] !== '') {
        params.append(key, filters[key]);
      }
    });
    return api.get<{ data: any[]; total_count: number }>(
      `/api/leads/social-threads?${params.toString()}`
    );
  },

  async getSocialThread(threadId: string) {
    return api.get(`/api/leads/social-threads/${threadId}`);
  },

  async createSocialThread(data: any) {
    return api.post('/api/leads/social-threads', data);
  },

  async respondToThread(threadId: string, message: string) {
    return api.post(`/api/v1/inbox/threads/${threadId}/messages`, {
      content: message,
      direction: 'outbound',
      message_type: 'text',
    });
  },

  async convertThreadToLead(threadId: string, leadData?: Partial<any>) {
    return api.post(`/api/leads/social-threads`, {
      thread_id: threadId,
      ...leadData,
    });
  },
};

/**
 * Reviews Management Service
 */
export const reviewService = {
  async getReviews(filters: any = {}) {
    const params = new URLSearchParams();
    Object.keys(filters).forEach(key => {
      if (filters[key] !== undefined && filters[key] !== '') {
        params.append(key, filters[key]);
      }
    });
    return api.get<{ data: any[]; total_count: number }>(
      `/api/reviews?${params.toString()}`
    );
  },

  async getReview(reviewId: string) {
    return api.get(`/api/reviews/${reviewId}`);
  },

  async getEscalatedReviews() {
    return api.get<{ data: any[] }>('/api/reviews/admin/escalated');
  },

  async resolveReview(reviewId: string, resolution: any) {
    return api.post(`/api/reviews/${reviewId}/resolve`, resolution);
  },

  async issueAICoupon(reviewId: string) {
    return api.post(`/api/reviews/ai/issue-coupon`, { review_id: reviewId });
  },

  async getReviewAnalytics() {
    return api.get('/api/reviews/admin/analytics');
  },

  async getCustomerReviews(customerId: string) {
    return api.get(`/api/reviews/customers/${customerId}/reviews`);
  },

  async trackExternalReview(data: any) {
    return api.post('/api/reviews/track-external', data);
  },
};

/**
 * Coupon Management Service
 */
export const couponService = {
  async validateCoupon(code: string) {
    return api.post('/api/reviews/coupons/validate', { code });
  },

  async applyCoupon(bookingId: string, code: string) {
    return api.post('/api/reviews/coupons/apply', {
      booking_id: bookingId,
      code,
    });
  },

  async getCustomerCoupons(customerId: string) {
    return api.get(`/api/reviews/customers/${customerId}/coupons`);
  },
};

/**
 * Analytics Service
 */
export const analyticsService = {
  async getOverview(filters: any = {}) {
    const params = new URLSearchParams();
    Object.keys(filters).forEach(key => {
      if (filters[key]) params.append(key, filters[key]);
    });
    return api.get(`/api/admin/analytics/overview?${params.toString()}`);
  },

  async getLeadAnalytics(filters: any = {}) {
    const params = new URLSearchParams();
    Object.keys(filters).forEach(key => {
      if (filters[key]) params.append(key, filters[key]);
    });
    return api.get(`/api/admin/analytics/leads?${params.toString()}`);
  },

  async getNewsletterAnalytics() {
    return api.get('/api/admin/analytics/newsletter');
  },

  async getConversionFunnel() {
    return api.get('/api/admin/analytics/funnel');
  },

  async getLeadScoring() {
    return api.get('/api/admin/analytics/lead-scoring');
  },

  async getEngagementTrends(filters: any = {}) {
    const params = new URLSearchParams();
    Object.keys(filters).forEach(key => {
      if (filters[key]) params.append(key, filters[key]);
    });
    return api.get(
      `/api/admin/analytics/engagement-trends?${params.toString()}`
    );
  },

  async getPaymentAnalytics(filters: any = {}) {
    const params = new URLSearchParams();
    Object.keys(filters).forEach(key => {
      if (filters[key]) params.append(key, filters[key]);
    });
    return api.get(`/api/stripe/analytics/payments?${params.toString()}`);
  },
};

/**
 * QR Code Management Service
 */
export const qrService = {
  async listQRCodes(filters: any = {}) {
    const params = new URLSearchParams();
    Object.keys(filters).forEach(key => {
      if (filters[key]) params.append(key, filters[key]);
    });
    return api.get<{ data: any[] }>(`/api/qr/list?${params.toString()}`);
  },

  async createQRCode(data: any) {
    return api.post('/api/qr/create', data);
  },

  async getQRAnalytics(code: string) {
    return api.get(`/api/qr/analytics/${code}`);
  },

  async trackScan(code: string, data: any) {
    return api.get(`/api/qr/scan/${code}`); // Public endpoint
  },

  async trackConversion(data: any) {
    return api.post('/api/qr/conversion', data);
  },
};

/**
 * SMS Messaging Service
 */
export const smsService = {
  async sendSMS(data: { to: string; message: string }) {
    return api.post('/api/ringcentral/send-sms', data);
  },

  async syncMessages() {
    return api.post('/api/ringcentral/sync-messages', {});
  },

  async getMessages(filters: any = {}) {
    const params = new URLSearchParams();
    if (filters.channel) params.append('channel', filters.channel);
    if (filters.status) params.append('status', filters.status);
    if (filters.phone_number)
      params.append('phone_number', filters.phone_number);

    const query = params.toString();
    const url = query
      ? `/api/v1/inbox/messages?${query}`
      : '/api/v1/inbox/messages';
    return api.get(url);
  },
};

// ==============================================================================
// SSoT Config Service (Dynamic Variables Management)
// ==============================================================================

export interface ConfigVariable {
  id?: string;
  key: string;
  value: unknown;
  value_type: 'string' | 'integer' | 'number' | 'boolean' | 'json';
  category: 'pricing' | 'deposit' | 'travel' | 'booking' | 'feature' | 'ai';
  description?: string;
  is_active?: boolean;
  effective_from?: string;
  effective_to?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ConfigVariableUpdate {
  value: unknown;
  description?: string;
  is_active?: boolean;
  effective_from?: string;
  effective_to?: string;
  [key: string]: unknown; // Index signature for Record<string, unknown> compatibility
}

export interface ConfigVariableCreate {
  key: string;
  value: unknown;
  value_type: 'string' | 'integer' | 'number' | 'boolean' | 'json';
  category: string;
  description?: string;
  is_active?: boolean;
  [key: string]: unknown; // Index signature for Record<string, unknown> compatibility
}

export interface ConfigAuditEntry {
  id: string;
  category: string;
  key: string;
  old_value: unknown;
  new_value: unknown;
  changed_by: string;
  changed_at: string;
  reason?: string;
}

// ============================================
// TWO-PERSON APPROVAL SYSTEM TYPES
// ============================================

/**
 * Status of an approval request
 */
export type ApprovalStatus =
  | 'pending'
  | 'approved'
  | 'rejected'
  | 'cancelled'
  | 'expired';

/**
 * Priority levels that determine approval requirements
 */
export type VariablePriority = 'critical' | 'high' | 'medium' | 'low';

/**
 * Approval request for a variable change
 */
export interface ApprovalRequest {
  id: string;
  category: string;
  key: string;
  current_value: unknown;
  proposed_value: unknown;
  requester_id: string;
  requester_name: string;
  status: ApprovalStatus;
  reason?: string;
  scheduled_for?: string;
  created_at: string;
  expires_at?: string;
  reviewed_by?: string;
  reviewer_name?: string;
  reviewed_at?: string;
  rejection_reason?: string;
}

/**
 * Request payload for creating an approval request
 */
export interface ApprovalRequestCreate {
  category: string;
  key: string;
  proposed_value: unknown;
  reason?: string;
  scheduled_for?: string;
  [key: string]: unknown; // Index signature for Record<string, unknown> compatibility
}

/**
 * Response for approval status check
 */
export interface ApprovalStatusCheck {
  has_pending_approval: boolean;
  approval?: ApprovalRequest;
}

/**
 * SSoT Configuration Service
 *
 * Manages dynamic business variables stored in PostgreSQL.
 * All pricing, fees, and policies should be managed through this service.
 *
 * API Endpoints:
 * - GET /api/v1/admin/config - List all variables
 * - GET /api/v1/admin/config/{category} - List by category
 * - POST /api/v1/admin/config - Create new variable
 * - PUT /api/v1/admin/config/{category}/{key} - Update variable
 * - DELETE /api/v1/admin/config/{category}/{key} - Delete variable
 * - POST /api/v1/admin/config/cache/invalidate - Force cache invalidation
 * - GET /api/v1/admin/config/audit - Get audit log
 */
export const configService = {
  /**
   * Get all configuration variables
   */
  async getVariables(): Promise<ApiResponse<{ data: ConfigVariable[] }>> {
    return api.get<{ data: ConfigVariable[] }>('/api/v1/admin/config');
  },

  /**
   * Get variables by category (pricing, deposit, travel, booking, etc.)
   */
  async getVariablesByCategory(
    category: string
  ): Promise<ApiResponse<{ data: ConfigVariable[] }>> {
    return api.get<{ data: ConfigVariable[] }>(
      `/api/v1/admin/config/${category}`
    );
  },

  /**
   * Get a single variable by category and key
   */
  async getVariable(
    category: string,
    key: string
  ): Promise<ApiResponse<ConfigVariable>> {
    return api.get<ConfigVariable>(`/api/v1/admin/config/${category}/${key}`);
  },

  /**
   * Create a new configuration variable
   */
  async createVariable(
    data: ConfigVariableCreate
  ): Promise<ApiResponse<ConfigVariable>> {
    return api.post<ConfigVariable>('/api/v1/admin/config', data);
  },

  /**
   * Update an existing configuration variable
   * Automatically invalidates cache on success
   */
  async updateVariable(
    category: string,
    key: string,
    data: ConfigVariableUpdate
  ): Promise<ApiResponse<ConfigVariable>> {
    return api.put<ConfigVariable>(
      `/api/v1/admin/config/${category}/${key}`,
      data
    );
  },

  /**
   * Delete a configuration variable
   */
  async deleteVariable(
    category: string,
    key: string
  ): Promise<ApiResponse<{ success: boolean }>> {
    return api.delete<{ success: boolean }>(
      `/api/v1/admin/config/${category}/${key}`
    );
  },

  /**
   * Force invalidate all cached configuration
   * Use after bulk updates or when debugging cache issues
   */
  async invalidateCache(): Promise<
    ApiResponse<{ success: boolean; message: string }>
  > {
    return api.post<{ success: boolean; message: string }>(
      '/api/v1/admin/config/cache/invalidate',
      {}
    );
  },

  /**
   * Get audit log for configuration changes
   */
  async getAuditLog(filters?: {
    category?: string;
    key?: string;
    from_date?: string;
    to_date?: string;
    limit?: number;
  }): Promise<ApiResponse<{ data: ConfigAuditEntry[] }>> {
    const params = new URLSearchParams();
    if (filters?.category) params.append('category', filters.category);
    if (filters?.key) params.append('key', filters.key);
    if (filters?.from_date) params.append('from_date', filters.from_date);
    if (filters?.to_date) params.append('to_date', filters.to_date);
    if (filters?.limit) params.append('limit', filters.limit.toString());

    const query = params.toString();
    const url = query
      ? `/api/v1/admin/config/audit?${query}`
      : '/api/v1/admin/config/audit';
    return api.get<{ data: ConfigAuditEntry[] }>(url);
  },

  /**
   * Bulk update multiple variables at once
   * Useful for initial setup or migrations
   */
  async bulkUpdate(
    updates: Array<{ category: string; key: string; value: unknown }>
  ): Promise<ApiResponse<{ updated: number; failed: number }>> {
    return api.post<{ updated: number; failed: number }>(
      '/api/v1/admin/config/bulk',
      { updates }
    );
  },

  // ============================================
  // TWO-PERSON APPROVAL SYSTEM METHODS
  // ============================================

  /**
   * Get all pending approval requests
   * Super admins see all, others see only their own
   */
  async getPendingApprovals(filters?: {
    category?: string;
    status?: ApprovalStatus;
    requester_id?: string;
  }): Promise<ApiResponse<{ data: ApprovalRequest[]; total: number }>> {
    const params = new URLSearchParams();
    if (filters?.category) params.append('category', filters.category);
    if (filters?.status) params.append('status', filters.status);
    if (filters?.requester_id)
      params.append('requester_id', filters.requester_id);

    const query = params.toString();
    const url = query
      ? `/api/v1/admin/config/approvals/pending?${query}`
      : '/api/v1/admin/config/approvals/pending';
    return api.get<{ data: ApprovalRequest[]; total: number }>(url);
  },

  /**
   * Get a single approval request by ID
   */
  async getApproval(approvalId: string): Promise<ApiResponse<ApprovalRequest>> {
    return api.get<ApprovalRequest>(
      `/api/v1/admin/config/approvals/${approvalId}`
    );
  },

  /**
   * Request approval for a variable change
   * Required for critical and high priority variables
   */
  async requestApproval(
    data: ApprovalRequestCreate
  ): Promise<ApiResponse<ApprovalRequest>> {
    return api.post<ApprovalRequest>(
      '/api/v1/admin/config/approvals/request',
      data
    );
  },

  /**
   * Approve a pending approval request
   * Automatically applies the change on approval
   */
  async approveRequest(
    approvalId: string,
    reason?: string
  ): Promise<ApiResponse<ApprovalRequest>> {
    return api.post<ApprovalRequest>(
      `/api/v1/admin/config/approvals/${approvalId}/approve`,
      {
        reason,
      }
    );
  },

  /**
   * Reject a pending approval request
   */
  async rejectRequest(
    approvalId: string,
    rejection_reason: string
  ): Promise<ApiResponse<ApprovalRequest>> {
    return api.post<ApprovalRequest>(
      `/api/v1/admin/config/approvals/${approvalId}/reject`,
      {
        rejection_reason,
      }
    );
  },

  /**
   * Cancel an approval request (only by requester)
   */
  async cancelRequest(
    approvalId: string
  ): Promise<ApiResponse<{ success: boolean }>> {
    return api.delete<{ success: boolean }>(
      `/api/v1/admin/config/approvals/${approvalId}`
    );
  },

  /**
   * Check if a variable has a pending approval
   */
  async checkApprovalStatus(
    category: string,
    key: string
  ): Promise<ApiResponse<ApprovalStatusCheck>> {
    return api.get<ApprovalStatusCheck>(
      `/api/v1/admin/config/approvals/check/${category}/${key}`
    );
  },
};
