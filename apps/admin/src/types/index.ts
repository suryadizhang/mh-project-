/**
 * Type definitions for the MyHibachi Admin Dashboard
 */

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  total_count?: number;
}

export interface Customer {
  customer_id: string;
  email: string;
  name: string;
  phone?: string;
  created_at: string;
  updated_at: string;
  total_bookings?: number;
  total_spent_cents?: number;
  last_booking_date?: string;
  status?: 'active' | 'inactive' | 'vip';
}

export interface Booking {
  booking_id: string;
  customer: {
    customer_id: string;
    email: string;
    name: string;
    phone?: string;
  };
  date: string; // ISO date string
  slot: string;
  total_guests: number;
  status: 'pending' | 'confirmed' | 'cancelled' | 'completed';
  payment_status: 'unpaid' | 'partial' | 'paid' | 'refunded';
  total_due_cents: number;
  balance_due_cents: number;
  special_requests?: string;
  source: string;
  created_at: string;
  updated_at: string;
}

export interface Payment {
  payment_id: string;
  booking_id: string;
  amount_cents: number;
  payment_method: string;
  payment_reference?: string;
  status: 'pending' | 'completed' | 'failed' | 'refunded';
  created_at: string;
  notes?: string;
}

export interface Invoice {
  invoice_id: string;
  booking_id: string;
  invoice_number: string;
  amount_cents: number;
  status: 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled';
  due_date: string;
  created_at: string;
  updated_at: string;
}

export interface DashboardStats {
  total_bookings: number;
  active_bookings: number;
  total_revenue_cents: number;
  pending_payments_cents: number;
  customers_count: number;
  bookings_this_month: number;
  revenue_this_month_cents: number;
  growth_rate: number;
}

export interface PaginationParams {
  page?: number;
  limit?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface BookingFilters extends PaginationParams {
  status?: string;
  payment_status?: string;
  date_from?: string;
  date_to?: string;
  customer_search?: string;
}

export interface CustomerFilters extends PaginationParams {
  status?: string;
  search?: string;
}