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
  id: number;
  name: string;
  description?: string;
  location?: string;
  phone?: string;
  email?: string;
  manager_name?: string;
  settings: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  user_count?: number;
  booking_count?: number;
  last_activity?: string;
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
        grant_type: 'password'
      }
    );
  },

  /**
   * Station-aware login
   */
  async stationLogin(email: string, password: string, stationId?: number) {
    return api.post<StationLoginResponse>(
      ENDPOINTS.stationAuth,
      { 
        email,
        password,
        station_id: stationId
      }
    );
  },

  /**
   * Get available stations for user
   */
  async getUserStations(email: string) {
    return api.get<Station[]>(`/api/station/user-stations?email=${encodeURIComponent(email)}`);
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
    const url = query ? `${ENDPOINTS.stations}/${stationId}?${query}` : `${ENDPOINTS.stations}/${stationId}`;
    
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
  async updateStation(stationId: number, updates: Partial<Station>) {
    return api.put<Station>(`${ENDPOINTS.stations}/${stationId}`, updates);
  },

  /**
   * Get station users
   */
  async getStationUsers(stationId: number, includeUserDetails: boolean = false) {
    const params = new URLSearchParams();
    if (includeUserDetails) params.append('include_user_details', 'true');
    
    const query = params.toString();
    const url = query ? `${ENDPOINTS.stations}/${stationId}/users?${query}` : `${ENDPOINTS.stations}/${stationId}/users`;
    
    return api.get<StationUser[]>(url);
  },

  /**
   * Assign user to station
   */
  async assignUserToStation(stationId: number, assignment: {
    user_id: number;
    role: string;
    permissions?: string[];
  }) {
    return api.post<StationUser>(`${ENDPOINTS.stations}/${stationId}/users`, assignment);
  },

  /**
   * Update user station assignment
   */
  async updateUserStationAssignment(stationId: number, userId: number, updates: {
    role?: string;
    permissions?: string[];
    is_active?: boolean;
  }) {
    return api.put<StationUser>(`${ENDPOINTS.stations}/${stationId}/users/${userId}`, updates);
  },

  /**
   * Remove user from station
   */
  async removeUserFromStation(stationId: number, userId: number) {
    return api.delete<void>(`${ENDPOINTS.stations}/${stationId}/users/${userId}`);
  },

  /**
   * Get station audit logs
   */
  async getStationAuditLogs(stationId: number, filters: {
    action?: string;
    resource_type?: string;
    user_id?: number;
    days?: number;
    skip?: number;
    limit?: number;
  } = {}) {
    const params = new URLSearchParams();
    
    if (filters.action) params.append('action', filters.action);
    if (filters.resource_type) params.append('resource_type', filters.resource_type);
    if (filters.user_id) params.append('user_id', filters.user_id.toString());
    if (filters.days) params.append('days', filters.days.toString());
    if (filters.skip) params.append('skip', filters.skip.toString());
    if (filters.limit) params.append('limit', filters.limit.toString());

    const query = params.toString();
    const url = query ? `${ENDPOINTS.stations}/${stationId}/audit?${query}` : `${ENDPOINTS.stations}/${stationId}/audit`;
    
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
    return authenticatedApi.get<{ data: any[]; total_count: number }>(
      `/api/leads?${params.toString()}`
    );
  },

  async getLead(leadId: string) {
    return authenticatedApi.get(`/api/leads/${leadId}`);
  },

  async createLead(data: any) {
    return authenticatedApi.post('/api/leads', data);
  },

  async updateLead(leadId: string, data: any) {
    return authenticatedApi.put(`/api/leads/${leadId}`, data);
  },

  async trackLeadEvent(leadId: string, event: any) {
    return authenticatedApi.post(`/api/leads/${leadId}/events`, event);
  },

  async getAIAnalysis(leadId: string) {
    return authenticatedApi.post(`/api/leads/${leadId}/ai-analysis`, {});
  },

  async getNurtureSequence(leadId: string) {
    return authenticatedApi.get(`/api/leads/${leadId}/nurture-sequence`);
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
    return authenticatedApi.get<{ data: any[]; total_count: number }>(
      `/api/leads/social-threads?${params.toString()}`
    );
  },

  async getSocialThread(threadId: string) {
    return authenticatedApi.get(`/api/leads/social-threads/${threadId}`);
  },

  async createSocialThread(data: any) {
    return authenticatedApi.post('/api/leads/social-threads', data);
  },

  async respondToThread(threadId: string, message: string) {
    return authenticatedApi.post(`/api/leads/social-threads/${threadId}/respond`, {
      message,
    });
  },

  async convertThreadToLead(threadId: string) {
    return authenticatedApi.post(`/api/leads/social-threads/${threadId}/convert`, {});
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
    return authenticatedApi.get<{ data: any[]; total_count: number }>(
      `/api/reviews?${params.toString()}`
    );
  },

  async getReview(reviewId: string) {
    return authenticatedApi.get(`/api/reviews/${reviewId}`);
  },

  async getEscalatedReviews() {
    return authenticatedApi.get<{ data: any[] }>('/api/reviews/admin/escalated');
  },

  async resolveReview(reviewId: string, resolution: any) {
    return authenticatedApi.post(`/api/reviews/${reviewId}/resolve`, resolution);
  },

  async issueAICoupon(reviewId: string) {
    return authenticatedApi.post(`/api/reviews/ai/issue-coupon`, { review_id: reviewId });
  },

  async getReviewAnalytics() {
    return authenticatedApi.get('/api/reviews/admin/analytics');
  },

  async getCustomerReviews(customerId: string) {
    return authenticatedApi.get(`/api/reviews/customers/${customerId}/reviews`);
  },

  async trackExternalReview(data: any) {
    return authenticatedApi.post('/api/reviews/track-external', data);
  },
};

/**
 * Coupon Management Service
 */
export const couponService = {
  async validateCoupon(code: string) {
    return authenticatedApi.post('/api/reviews/coupons/validate', { code });
  },

  async applyCoupon(bookingId: string, code: string) {
    return authenticatedApi.post('/api/reviews/coupons/apply', {
      booking_id: bookingId,
      code,
    });
  },

  async getCustomerCoupons(customerId: string) {
    return authenticatedApi.get(`/api/reviews/customers/${customerId}/coupons`);
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
    return authenticatedApi.get(`/api/admin/analytics/overview?${params.toString()}`);
  },

  async getLeadAnalytics(filters: any = {}) {
    const params = new URLSearchParams();
    Object.keys(filters).forEach(key => {
      if (filters[key]) params.append(key, filters[key]);
    });
    return authenticatedApi.get(`/api/admin/analytics/leads?${params.toString()}`);
  },

  async getNewsletterAnalytics() {
    return authenticatedApi.get('/api/admin/analytics/newsletter');
  },

  async getConversionFunnel() {
    return authenticatedApi.get('/api/admin/analytics/funnel');
  },

  async getLeadScoring() {
    return authenticatedApi.get('/api/admin/analytics/lead-scoring');
  },

  async getEngagementTrends(filters: any = {}) {
    const params = new URLSearchParams();
    Object.keys(filters).forEach(key => {
      if (filters[key]) params.append(key, filters[key]);
    });
    return authenticatedApi.get(`/api/admin/analytics/engagement-trends?${params.toString()}`);
  },

  async getPaymentAnalytics(filters: any = {}) {
    const params = new URLSearchParams();
    Object.keys(filters).forEach(key => {
      if (filters[key]) params.append(key, filters[key]);
    });
    return authenticatedApi.get(`/api/stripe/analytics/payments?${params.toString()}`);
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
    return authenticatedApi.get<{ data: any[] }>(`/api/qr/list?${params.toString()}`);
  },

  async createQRCode(data: any) {
    return authenticatedApi.post('/api/qr/create', data);
  },

  async getQRAnalytics(code: string) {
    return authenticatedApi.get(`/api/qr/analytics/${code}`);
  },

  async trackScan(code: string, data: any) {
    return api.get(`/api/qr/scan/${code}`); // Public endpoint
  },

  async trackConversion(data: any) {
    return authenticatedApi.post('/api/qr/conversion', data);
  },
};

/**
 * SMS Messaging Service
 */
export const smsService = {
  async sendSMS(data: { to: string; message: string }) {
    return authenticatedApi.post('/api/ringcentral/send-sms', data);
  },

  async syncMessages() {
    return authenticatedApi.post('/api/ringcentral/sync-messages', {});
  },

  async getMessages(filters: any = {}) {
    // Note: This endpoint may need to be created in backend
    return authenticatedApi.get('/api/ringcentral/messages');
  },
};