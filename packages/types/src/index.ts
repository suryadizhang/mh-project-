import { z } from 'zod';

// Core domain types
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
  status: 'pending' | 'completed' | 'failed' | 'refunded';
  transactionId?: string;
  stripeSessionId?: string;
}

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

export interface PaginatedResponse<T = unknown> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// Common utility types
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export type RequireField<T, K extends keyof T> = T & Required<Pick<T, K>>;

export type OmitField<T, K extends keyof T> = Omit<T, K>;
