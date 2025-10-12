import { z } from 'zod';
import { BookingSchema } from '../index';

/**
 * Common response wrapper fields
 * All API responses include these standard fields for tracking and debugging
 */
const BaseResponseSchema = z.object({
  success: z.boolean().describe('Indicates if the request was successful'),
  timestamp: z.string().datetime().describe('ISO 8601 timestamp of the response'),
  requestId: z.string().uuid().describe('Unique identifier for request tracing'),
});

/**
 * Schema for GET /api/v1/customers/dashboard
 * Returns comprehensive dashboard data for authenticated customer
 * 
 * Used by:
 * - apps/customer/src/components/CustomerSavingsDisplay.tsx
 * - Future dashboard pages
 * 
 * @example
 * {
 *   success: true,
 *   data: {
 *     customer: {
 *       id: "123e4567-e89b-12d3-a456-426614174000",
 *       email: "customer@example.com",
 *       name: "John Doe",
 *       phone: "+1-555-123-4567",
 *       memberSince: "2024-01-15T00:00:00.000Z"
 *     },
 *     stats: {
 *       totalBookings: 15,
 *       upcomingBookings: 2,
 *       completedBookings: 13,
 *       cancelledBookings: 0,
 *       totalSpent: 7500.00,
 *       averageBookingAmount: 500.00,
 *       favoriteMenuItem: "Hibachi Chicken"
 *     },
 *     savings: {
 *       totalSaved: 1500.00,
 *       savingsPercentage: 16.67,
 *       comparedToMarket: "restaurant-average"
 *     },
 *     upcomingBookings: [...],
 *     recentBookings: [...]
 *   },
 *   timestamp: "2025-10-12T10:30:00.000Z",
 *   requestId: "123e4567-e89b-12d3-a456-426614174000"
 * }
 */
export const CustomerDashboardResponseSchema = BaseResponseSchema.extend({
  data: z.object({
    customer: z.object({
      id: z.string().uuid().describe('Customer unique identifier'),
      email: z.string().email().describe('Customer email address'),
      name: z.string().min(1).max(100).describe('Customer full name'),
      phone: z
        .string()
        .regex(/^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$/)
        .optional()
        .describe('Optional: Customer phone number'),
      memberSince: z
        .string()
        .datetime()
        .describe('ISO 8601 timestamp when customer joined'),
      loyaltyTier: z
        .enum(['bronze', 'silver', 'gold', 'platinum'])
        .optional()
        .describe('Optional: Customer loyalty tier'),
      profileImageUrl: z
        .string()
        .url()
        .optional()
        .describe('Optional: URL to customer profile image'),
    }).describe('Customer profile information'),
    stats: z.object({
      totalBookings: z
        .number()
        .int()
        .nonnegative()
        .describe('Total number of bookings (all statuses)'),
      upcomingBookings: z
        .number()
        .int()
        .nonnegative()
        .describe('Number of upcoming bookings (confirmed/pending)'),
      completedBookings: z
        .number()
        .int()
        .nonnegative()
        .describe('Number of completed bookings'),
      cancelledBookings: z
        .number()
        .int()
        .nonnegative()
        .describe('Number of cancelled bookings'),
      totalSpent: z
        .number()
        .nonnegative()
        .describe('Total amount spent (in dollars)'),
      averageBookingAmount: z
        .number()
        .nonnegative()
        .describe('Average amount per booking (in dollars)'),
      favoriteMenuItem: z
        .string()
        .optional()
        .describe('Optional: Most frequently ordered menu item'),
      totalGuests: z
        .number()
        .int()
        .nonnegative()
        .optional()
        .describe('Optional: Total number of guests served'),
    }).describe('Customer statistics'),
    savings: z.object({
      totalSaved: z
        .number()
        .nonnegative()
        .describe('Total amount saved compared to market average (in dollars)'),
      savingsPercentage: z
        .number()
        .nonnegative()
        .max(100)
        .describe('Percentage saved compared to market average'),
      comparedToMarket: z
        .enum(['restaurant-average', 'catering-average', 'both'])
        .describe('What market average is used for comparison'),
      breakdown: z
        .object({
          serviceFees: z.number().nonnegative().optional(),
          deliveryFees: z.number().nonnegative().optional(),
          markups: z.number().nonnegative().optional(),
        })
        .optional()
        .describe('Optional: Detailed breakdown of savings by category'),
    }).describe('Savings information'),
    upcomingBookings: z
      .array(
        BookingSchema.pick({
          id: true,
          eventDate: true,
          eventTime: true,
          guestCount: true,
          status: true,
          totalAmount: true,
        }).extend({
          confirmationCode: z.string().min(1).max(50),
          daysUntil: z.number().int().nonnegative(),
        })
      )
      .max(5)
      .describe('Array of upcoming bookings (max 5)'),
    recentBookings: z
      .array(
        BookingSchema.pick({
          id: true,
          eventDate: true,
          guestCount: true,
          status: true,
          totalAmount: true,
        }).extend({
          confirmationCode: z.string().min(1).max(50),
        })
      )
      .max(5)
      .describe('Array of recent bookings (max 5)'),
    notifications: z
      .array(
        z.object({
          id: z.string().uuid(),
          type: z.enum(['info', 'warning', 'success', 'error']),
          message: z.string(),
          createdAt: z.string().datetime(),
          read: z.boolean(),
        })
      )
      .optional()
      .describe('Optional: Array of unread notifications'),
  }).describe('Customer dashboard data'),
  error: z.string().optional().describe('Error message if success is false'),
});

export type CustomerDashboardResponse = z.infer<typeof CustomerDashboardResponseSchema>;

/**
 * Schema for GET /api/v1/customers/profile
 * Returns customer profile information
 * 
 * Future usage for profile management
 * 
 * @example
 * {
 *   success: true,
 *   data: {
 *     id: "123e4567-e89b-12d3-a456-426614174000",
 *     email: "customer@example.com",
 *     name: "John Doe",
 *     phone: "+1-555-123-4567",
 *     preferences: {
 *       dietaryRestrictions: ["vegetarian"],
 *       communicationPreferences: { email: true, sms: false }
 *     }
 *   },
 *   timestamp: "2025-10-12T10:30:00.000Z",
 *   requestId: "123e4567-e89b-12d3-a456-426614174000"
 * }
 */
export const CustomerProfileResponseSchema = BaseResponseSchema.extend({
  data: z.object({
    id: z.string().uuid().describe('Customer unique identifier'),
    email: z.string().email().describe('Customer email address'),
    name: z.string().min(1).max(100).describe('Customer full name'),
    phone: z
      .string()
      .regex(/^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$/)
      .optional()
      .describe('Optional: Customer phone number'),
    memberSince: z
      .string()
      .datetime()
      .describe('ISO 8601 timestamp when customer joined'),
    preferences: z
      .object({
        dietaryRestrictions: z
          .array(z.string())
          .optional()
          .describe('Optional: Array of dietary restrictions'),
        allergens: z
          .array(z.string())
          .optional()
          .describe('Optional: Array of allergens to avoid'),
        communicationPreferences: z
          .object({
            email: z.boolean().default(true),
            sms: z.boolean().default(false),
            push: z.boolean().default(false),
          })
          .optional()
          .describe('Optional: Communication preferences'),
        preferredPaymentMethod: z
          .enum(['stripe', 'zelle', 'venmo'])
          .optional()
          .describe('Optional: Preferred payment method'),
      })
      .optional()
      .describe('Optional: Customer preferences'),
    addresses: z
      .array(
        z.object({
          id: z.string().uuid(),
          address: z.string().min(5).max(200),
          city: z.string().min(2).max(50),
          state: z.string().length(2),
          zipCode: z.string().regex(/^\d{5}(-\d{4})?$/),
          isDefault: z.boolean(),
          label: z.string().optional(),
        })
      )
      .optional()
      .describe('Optional: Saved addresses'),
  }).describe('Customer profile data'),
  error: z.string().optional().describe('Error message if success is false'),
});

export type CustomerProfileResponse = z.infer<typeof CustomerProfileResponseSchema>;

/**
 * Export all schemas for easy import
 */
export const CustomerResponseSchemas = {
  Dashboard: CustomerDashboardResponseSchema,
  Profile: CustomerProfileResponseSchema,
} as const;
