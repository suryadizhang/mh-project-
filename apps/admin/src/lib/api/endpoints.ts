/**
 * Centralized API Endpoints - Single Source of Truth
 * =================================================
 *
 * NEVER hardcode API paths in components/services.
 * All backend API calls MUST use these constants.
 *
 * Pattern:
 *   apiFetch(API_ENDPOINTS.ADMIN.AUDIT_LOGS)
 *   NOT: apiFetch('/api/admin/audit-logs')
 *
 * See: .github/instructions/24-API_ROUTING_STANDARDS.instructions.md
 */

// Base prefixes - ALL backend routes start with /api
const V1 = '/api/v1';
const ADMIN = '/api/admin';

/**
 * API Endpoints organized by domain
 */
export const API_ENDPOINTS = {
  // ============================================
  // V1 PUBLIC/AUTHENTICATED ENDPOINTS
  // ============================================
  V1: {
    // Bookings
    BOOKINGS: `${V1}/bookings`,
    BOOKINGS_LIST: `${V1}/bookings`,
    BOOKINGS_CALENDAR: `${V1}/bookings/calendar`,
    BOOKINGS_AVAILABILITY: `${V1}/bookings/availability`,
    BOOKINGS_BOOKED_DATES: `${V1}/bookings/booked-dates`,
    BOOKING_DETAIL: (id: string) => `${V1}/bookings/${id}`,
    BOOKING_CANCEL: (id: string) => `${V1}/bookings/${id}/cancel`,
    BOOKING_RESCHEDULE: (id: string) => `${V1}/bookings/${id}/reschedule`,

    // Customers
    CUSTOMERS: `${V1}/customers`,
    CUSTOMERS_DASHBOARD: `${V1}/customers/dashboard`,
    CUSTOMER_DETAIL: (id: string) => `${V1}/customers/${id}`,
    CUSTOMER_BOOKINGS: (id: string) => `${V1}/customers/${id}/bookings`,

    // Chefs (Admin view - all chefs)
    CHEFS: `${V1}/chef-portal/station/chefs`,
    CHEF_DETAIL: (id: string) => `${V1}/chef-portal/station/chefs/${id}`,
    CHEF_AVAILABILITY: (id: string) =>
      `${V1}/chef-portal/station/chefs/${id}/availability`,
    // Note: CHEF_SCHEDULE is for admin to view a chef's schedule (not yet implemented)
    CHEF_SCHEDULE: (id: string) =>
      `${V1}/chef-portal/station/chefs/${id}/schedule`,

    // Chef Portal (Chef self-service endpoints)
    CHEF_PORTAL: {
      ME: `${V1}/chef-portal/me`,
      MY_AVAILABILITY: `${V1}/chef-portal/me/availability`,
      MY_AVAILABILITY_BULK: `${V1}/chef-portal/me/availability/bulk`,
      MY_AVAILABILITY_SLOT: (slotId: string) =>
        `${V1}/chef-portal/me/availability/${slotId}`,
      MY_TIMEOFF: `${V1}/chef-portal/me/timeoff`,
      MY_TIMEOFF_REQUEST: (requestId: string) =>
        `${V1}/chef-portal/me/timeoff/${requestId}`,
      MY_SCHEDULE: `${V1}/chef-portal/me/schedule`,
      MY_EVENTS: `${V1}/chef-portal/me/events`,
      MY_EARNINGS: `${V1}/chef-portal/me/earnings`,
    },

    // Stations
    STATIONS: `${V1}/stations`,
    STATION_DETAIL: (id: string) => `${V1}/stations/${id}`,

    // Leads
    LEADS: `${V1}/leads`,
    LEADS_EXPORT: `${V1}/leads/export`,
    LEAD_DETAIL: (id: string) => `${V1}/leads/${id}`,
    LEAD_NOTES: (id: string) => `${V1}/leads/${id}/notes`,
    LEAD_CONVERT: (id: string) => `${V1}/leads/${id}/convert`,

    // Payments
    PAYMENTS: `${V1}/payments`,
    PAYMENTS_CHECKOUT_SESSION: `${V1}/payments/checkout-session`,
    PAYMENTS_ALTERNATIVE: `${V1}/payments/alternative-payment`,

    // Stripe
    STRIPE_INVOICES: `${V1}/stripe/invoices`,
    STRIPE_REFUNDS: `${V1}/stripe/refunds`,
    STRIPE_CHECKOUT: `${V1}/stripe/checkout`,

    // Escalations
    ESCALATIONS: `${V1}/escalations`,
    ESCALATION_DETAIL: (id: string) => `${V1}/escalations/${id}`,
    ESCALATION_RESOLVE: (id: string) => `${V1}/escalations/${id}/resolve`,

    // Inbox
    INBOX_THREADS: `${V1}/inbox/threads`,
    INBOX_THREAD_DETAIL: (id: string) => `${V1}/inbox/threads/${id}`,
    INBOX_THREAD_MESSAGES: (id: string) => `${V1}/inbox/threads/${id}/messages`,

    // Reviews
    REVIEWS: `${V1}/reviews`,
    REVIEW_DETAIL: (id: string) => `${V1}/reviews/${id}`,
    REVIEW_REPLY: (id: string) => `${V1}/reviews/${id}/reply`,

    // Newsletter
    NEWSLETTER_SUBSCRIBERS: `${V1}/newsletter/subscribers`,
    NEWSLETTER_CAMPAIGNS: `${V1}/newsletter/campaigns`,
    NEWSLETTER_SEND: `${V1}/newsletter/send`,

    // Travel Fees
    TRAVEL_FEES: `${V1}/travel-fees`,
    TRAVEL_FEE_CALCULATE: `${V1}/travel-fees/calculate`,

    // Auth
    AUTH_LOGIN: `${V1}/auth/login`,
    AUTH_LOGOUT: `${V1}/auth/logout`,
    AUTH_REFRESH: `${V1}/auth/refresh`,
    AUTH_ME: `${V1}/auth/me`,

    // Config
    CONFIG_ALL: `${V1}/config/all`,
    CONFIG_PRICING: `${V1}/pricing/current`,

    // Public endpoints (no auth required)
    PUBLIC: {
      BOOKINGS_BOOKED_DATES: `${V1}/public/bookings/booked-dates`,
      QUOTE_EMAIL: `${V1}/public/quote/email`,
      LEADS: `${V1}/public/leads`,
      CONFIG: `${V1}/public/config`,
    },
  },

  // ============================================
  // ADMIN ENDPOINTS (Requires admin+ role)
  // ============================================
  ADMIN: {
    // Audit Logs
    AUDIT_LOGS: `${ADMIN}/audit-logs`,
    AUDIT_LOGS_STATS: `${ADMIN}/audit-logs/stats`,
    AUDIT_LOGS_ACTIONS: `${ADMIN}/audit-logs/actions`,
    AUDIT_LOG_DETAIL: (id: string) => `${ADMIN}/audit-logs/${id}`,
    AUDIT_LOG_RESTORE: (id: string) => `${ADMIN}/audit-logs/${id}/restore`,

    // Error Logs
    ERROR_LOGS: `${ADMIN}/error-logs`,
    ERROR_LOGS_STATS: `${ADMIN}/error-logs/stats`,
    ERROR_LOG_DETAIL: (id: string) => `${ADMIN}/error-logs/${id}`,

    // AI Readiness & Learning Queue
    AI_READINESS: `${ADMIN}/ai-readiness/`,
    LEARNING_QUEUE: `${ADMIN}/learning-queue/`,
    LEARNING_QUEUE_APPROVE: (id: string) =>
      `${ADMIN}/learning-queue/${id}/approve/`,

    // Analytics (trailing slash required to avoid 307 redirect)
    ANALYTICS_OVERVIEW: `${ADMIN}/analytics/overview/`,
    ANALYTICS_BOOKINGS: `${ADMIN}/analytics/bookings/`,
    ANALYTICS_REVENUE: `${ADMIN}/analytics/revenue/`,
    ANALYTICS_CUSTOMERS: `${ADMIN}/analytics/customers/`,

    // Dynamic Variables (SSoT)
    DYNAMIC_VARIABLES: `${ADMIN}/config/variables/`,
    DYNAMIC_VARIABLE_UPDATE: (category: string, key: string) =>
      `${ADMIN}/config/${category}/${key}/`,

    // Users & Roles
    USERS: `${ADMIN}/users/`,
    USER_DETAIL: (id: string) => `${ADMIN}/users/${id}/`,
    USER_ROLES: (id: string) => `${ADMIN}/users/${id}/roles/`,
    ADMIN_INVITATIONS: `${ADMIN}/invitations/`,

    // VPS Security Monitoring
    VPS_SECURITY_STATUS: `${ADMIN}/vps-security/status`,
    VPS_SECURITY_JAILS: `${ADMIN}/vps-security/jails`,
    VPS_SECURITY_BANNED_IPS: `${ADMIN}/vps-security/banned-ips`,
    VPS_SECURITY_FIREWALL_RULES: `${ADMIN}/vps-security/firewall-rules`,
    VPS_SECURITY_ATTACK_LOG: `${ADMIN}/vps-security/attack-log`,
    VPS_SECURITY_STATS: `${ADMIN}/vps-security/stats`,
    VPS_SECURITY_REPORT: `${ADMIN}/vps-security/report`,
    VPS_SECURITY_UNBAN: `${ADMIN}/vps-security/unban`,
    VPS_SECURITY_KNOWN_ATTACKERS: `${ADMIN}/vps-security/known-attackers`,
  },
} as const;

/**
 * Type helper for extracting endpoint types
 */
export type ApiEndpointV1 =
  (typeof API_ENDPOINTS.V1)[keyof typeof API_ENDPOINTS.V1];
export type ApiEndpointAdmin =
  (typeof API_ENDPOINTS.ADMIN)[keyof typeof API_ENDPOINTS.ADMIN];
