import { z } from 'zod';

// ===========================================================
// RE-EXPORTS FROM NEW MODULES
// ===========================================================

// Slot Hold types (Batch 1 - 2-step booking flow)
export * from './slot-hold';

// Agreement types (Batch 1 - Digital signing)
export * from './agreement';

// Error codes (Descriptive string codes)
export * from './errors';

// ===========================================================
// Core domain types
// ===========================================================

export interface User {
  id: string;
  email: string;
  name: string;
  role: 'customer' | 'admin' | 'chef';
  createdAt: Date;
  updatedAt: Date;
}

export interface Booking {
  id: string;
  userId: string;
  eventDate: Date;
  eventTime: string;
  guestCount: number;
  location: BookingLocation;
  menuItems: MenuItem[];
  totalAmount: number;
  status: BookingStatus;
  createdAt: Date;
  updatedAt: Date;
}

export interface MenuItem {
  id: string;
  name: string;
  description: string;
  price: number;
  category: 'appetizer' | 'protein' | 'vegetable' | 'rice' | 'dessert';
  allergens: string[];
  available: boolean;
}

export interface BookingLocation {
  address: string;
  city: string;
  state: string;
  zipCode: string;
  coordinates?: {
    lat: number;
    lng: number;
  };
}

export type BookingStatus =
  | 'pending'
  | 'confirmed'
  | 'in_progress'
  | 'completed'
  | 'cancelled'
  | 'refunded';

export type PaymentMethod = 'stripe' | 'zelle' | 'venmo';

export interface PaymentInfo {
  method: PaymentMethod;
  amount: number;
  currency: 'USD';
  status:
    | 'pending'
    | 'processing'
    | 'succeeded'
    | 'failed'
    | 'canceled'
    | 'refunded'
    | 'partially_refunded';
  transactionId?: string;
  stripeSessionId?: string;
}

/**
 * Payment Status enum values - matches backend PaymentStatus and Stripe standard
 * IMPORTANT: 'succeeded' is the Stripe-standard term (NOT 'completed')
 */
export type PaymentStatus =
  | 'pending'
  | 'processing'
  | 'succeeded'
  | 'failed'
  | 'canceled'
  | 'refunded'
  | 'partially_refunded';

/**
 * Stripe Payment Intent status values
 */
export type StripePaymentIntentStatus =
  | 'requires_payment_method'
  | 'requires_confirmation'
  | 'requires_action'
  | 'processing'
  | 'requires_capture'
  | 'canceled'
  | 'succeeded';

/**
 * Invoice status values - matches backend InvoiceStatus
 */
export type InvoiceStatus =
  | 'draft'
  | 'open'
  | 'paid'
  | 'uncollectible'
  | 'void';

/**
 * Refund status values - matches backend RefundStatus
 */
export type RefundStatus = 'pending' | 'succeeded' | 'failed' | 'canceled';

// Zod schemas for validation
export const UserSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  name: z.string().min(1).max(100),
  role: z.enum(['customer', 'admin', 'chef']),
  createdAt: z.date(),
  updatedAt: z.date(),
});

export const BookingLocationSchema = z.object({
  address: z.string().min(5).max(200),
  city: z.string().min(2).max(50),
  state: z.string().length(2),
  zipCode: z.string().regex(/^\d{5}(-\d{4})?$/),
  coordinates: z
    .object({
      lat: z.number().min(-90).max(90),
      lng: z.number().min(-180).max(180),
    })
    .optional(),
});

export const MenuItemSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(100),
  description: z.string().max(500),
  price: z.number().positive(),
  category: z.enum(['appetizer', 'protein', 'vegetable', 'rice', 'dessert']),
  allergens: z.array(z.string()),
  available: z.boolean(),
});

export const BookingSchema = z.object({
  id: z.string().uuid(),
  userId: z.string().uuid(),
  eventDate: z.date().min(new Date()),
  eventTime: z.string().regex(/^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/),
  guestCount: z.number().int().min(1).max(50),
  location: BookingLocationSchema,
  menuItems: z.array(MenuItemSchema).min(1),
  totalAmount: z.number().positive(),
  status: z.enum([
    'pending',
    'confirmed',
    'in_progress',
    'completed',
    'cancelled',
    'refunded',
  ]),
  createdAt: z.date(),
  updatedAt: z.date(),
});

export const PaymentInfoSchema = z.object({
  method: z.enum(['stripe', 'zelle', 'venmo']),
  amount: z.number().positive(),
  currency: z.literal('USD'),
  status: z.enum(['pending', 'completed', 'failed', 'refunded']),
  transactionId: z.string().optional(),
  stripeSessionId: z.string().optional(),
});

// API Response types
export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  timestamp: string;
  requestId: string;
}

// Legacy page-based pagination (deprecated, use CursorPaginatedResponse)
export interface PaginatedResponse<T = unknown> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// Modern cursor-based pagination (MEDIUM #34 Phase 2)
// Provides O(1) performance regardless of page depth
export interface CursorPaginatedResponse<T = unknown> {
  items: T[];
  next_cursor: string | null;
  prev_cursor: string | null;
  has_next: boolean;
  has_prev: boolean;
  count: number;
  total_count?: number; // Optional, expensive to compute
}

// Alias for backward compatibility
export type PaginatedData<T> = CursorPaginatedResponse<T>;

// Common utility types
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export type RequireField<T, K extends keyof T> = T & Required<Pick<T, K>>;

export type OmitField<T, K extends keyof T> = Omit<T, K>;
