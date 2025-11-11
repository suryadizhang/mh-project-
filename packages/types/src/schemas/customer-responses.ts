import { z } from 'zod';

/**
 * Customer Response Schemas
 * 
 * ✅ CORRECTED TO MATCH ACTUAL BACKEND RESPONSES
 * Backend: apps/backend/src/api/app/routers/stripe.py
 * 
 * All schemas validated against actual customer dashboard integration.
 */

/**
 * Schema for GET /api/v1/customers/dashboard
 * Returns comprehensive dashboard data for authenticated customer
 * 
 * ✅ ACTUAL RESPONSE FORMAT (apps/backend/src/api/app/routers/stripe.py line 566-604)
 * Backend returns:
 * {
 *   customer: { id, email, name, phone },
 *   analytics: { totalSpent, totalBookings, zelleAdoptionRate, totalSavingsFromZelle, ... },
 *   savingsInsights: { 
 *     totalSavingsFromZelle, 
 *     potentialSavingsIfAllZelle, 
 *     zelleAdoptionRate,
 *     recommendedAction,
 *     nextBookingPotentialSavings: { smallEvent, mediumEvent, largeEvent }
 *   },
 *   loyaltyStatus: { tier, benefits, nextTierProgress, ... }
 * }
 * 
 * Used by:
 * - apps/customer/src/components/CustomerSavingsDisplay.tsx (line 85)
 * 
 * @example
 * {
 *   customer: {
 *     id: "cus_ABC123",
 *     email: "customer@example.com",
 *     name: "John Doe",
 *     phone: "+1-555-123-4567"
 *   },
 *   analytics: {
 *     totalSpent: 7500.00,
 *     totalBookings: 15,
 *     zelleAdoptionRate: 60,
 *     totalSavingsFromZelle: 360.00
 *   },
 *   savingsInsights: {
 *     totalSavingsFromZelle: 360.00,
 *     potentialSavingsIfAllZelle: 600.00,
 *     zelleAdoptionRate: 60,
 *     recommendedAction: "Great job using Zelle! You're saving money on booking.",
 *     nextBookingPotentialSavings: {
 *       smallEvent: { amount: 500, savings: 40 },
 *       mediumEvent: { amount: 1000, savings: 80 },
 *       largeEvent: { amount: 2000, savings: 160 }
 *     }
 *   },
 *   loyaltyStatus: {
 *     tier: "silver",
 *     benefits: ["Priority support", "5% discount"],
 *     nextTierProgress: 45
 *   }
 * }
 */
export const CustomerDashboardResponseSchema = z.object({
  customer: z.object({
    id: z
      .string()
      .startsWith('cus_')
      .describe('Stripe customer ID (starts with "cus_")'),
    email: z.string().email().describe('Customer email address'),
    name: z.string().nullable().describe('Customer full name'),
    phone: z.string().nullable().describe('Customer phone number'),
  }).describe('Customer profile information'),
  analytics: z.object({
    totalSpent: z
      .number()
      .nonnegative()
      .describe('Total amount spent (in dollars)'),
    totalBookings: z
      .number()
      .int()
      .nonnegative()
      .describe('Total number of bookings'),
    zelleAdoptionRate: z
      .number()
      .min(0)
      .max(100)
      .describe('Percentage of payments made via Zelle (0-100)'),
    totalSavingsFromZelle: z
      .number()
      .nonnegative()
      .describe('Total savings from using Zelle instead of Stripe (in dollars)'),
  }).describe('Customer analytics'),
  savingsInsights: z.object({
    totalSavingsFromZelle: z
      .number()
      .nonnegative()
      .describe('Total savings from Zelle (8% fee savings)'),
    potentialSavingsIfAllZelle: z
      .number()
      .nonnegative()
      .describe('Potential savings if all payments were Zelle (8% of total spent)'),
    zelleAdoptionRate: z
      .number()
      .min(0)
      .max(100)
      .describe('Percentage of Zelle usage'),
    recommendedAction: z
      .string()
      .describe('Personalized recommendation based on Zelle adoption'),
    nextBookingPotentialSavings: z.object({
      smallEvent: z.object({
        amount: z.number().describe('Small event amount ($500)'),
        savings: z.number().describe('Potential savings (8% of amount)'),
      }),
      mediumEvent: z.object({
        amount: z.number().describe('Medium event amount ($1000)'),
        savings: z.number().describe('Potential savings (8% of amount)'),
      }),
      largeEvent: z.object({
        amount: z.number().describe('Large event amount ($2000)'),
        savings: z.number().describe('Potential savings (8% of amount)'),
      }),
    }).describe('Potential savings for different event sizes'),
  }).describe('Savings insights and recommendations'),
  loyaltyStatus: z
    .object({
      tier: z
        .enum(['bronze', 'silver', 'gold', 'platinum'])
        .describe('Customer loyalty tier'),
      benefits: z
        .array(z.string())
        .describe('Benefits associated with current tier'),
      nextTierProgress: z
        .number()
        .min(0)
        .max(100)
        .describe('Progress towards next tier (0-100%)'),
      nextTier: z
        .string()
        .optional()
        .describe('Name of next tier'),
      requiredForNextTier: z
        .string()
        .optional()
        .describe('Requirements to reach next tier'),
    })
    .describe('Customer loyalty status'),
});

export type CustomerDashboardResponse = z.infer<typeof CustomerDashboardResponseSchema>;

/**
 * Export all schemas for easy import
 */
export const CustomerResponseSchemas = {
  Dashboard: CustomerDashboardResponseSchema,
} as const;
