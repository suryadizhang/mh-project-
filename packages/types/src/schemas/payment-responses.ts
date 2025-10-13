import { z } from 'zod';

/**
 * Stripe Payment Response Schemas
 * 
 * ✅ CORRECTED TO MATCH ACTUAL BACKEND RESPONSES
 * Backend: apps/backend/src/api/app/routers/stripe.py
 * 
 * All schemas validated against actual Stripe integration:
 * - PaymentIntent: 3-field minimal response (clientSecret, paymentIntentId, stripeCustomerId)
 * - CheckoutSession CREATE: 2-field response (url, session_id)
 * - CheckoutSession VERIFY: ⚠️ NOT IMPLEMENTED (endpoint missing, documented for future)
 * 
 * Backend follows "minimal response" pattern for security - only returns essential fields.
 * Does not expose full Stripe API objects to frontend.
 */

/**
 * Schema for POST /api/v1/payments/create-intent
 * Creates a Stripe PaymentIntent for processing payment
 * 
 * ✅ ACTUAL RESPONSE FORMAT (apps/backend/src/api/app/routers/stripe.py line 743-747)
 * Backend returns minimal response with only 3 essential fields:
 * {
 *   "clientSecret": payment_intent.client_secret,
 *   "paymentIntentId": payment_intent.id,
 *   "stripeCustomerId": stripe_customer.id
 * }
 * 
 * Used by:
 * - apps/customer/src/app/(pages)/payment/page.tsx (line 93: extracts only clientSecret)
 * 
 * @example
 * {
 *   clientSecret: "pi_3ABC123_secret_xyz",
 *   paymentIntentId: "pi_3ABC123",
 *   stripeCustomerId: "cus_ABC123"
 * }
 * 
 * Note: Backend follows minimal response pattern for security.
 * Full PaymentIntent details not exposed to frontend.
 */
export const PaymentIntentResponseSchema = z.object({
  clientSecret: z
    .string()
    .min(1)
    .describe('Stripe client secret for confirming payment on client side'),
  paymentIntentId: z
    .string()
    .startsWith('pi_')
    .describe('Stripe PaymentIntent ID (starts with "pi_")'),
  stripeCustomerId: z
    .string()
    .startsWith('cus_')
    .describe('Stripe Customer ID (starts with "cus_")'),
});

export type PaymentIntentResponse = z.infer<typeof PaymentIntentResponseSchema>;

/**
 * Schema for POST /create-checkout-session
 * Creates a Stripe Checkout Session for hosted payment page
 * 
 * ✅ ACTUAL RESPONSE FORMAT (apps/backend/src/api/app/routers/stripe.py line 103)
 * Backend returns: CheckoutSessionResponse(url=session.url, session_id=session.id)
 * {
 *   "url": "https://checkout.stripe.com/c/pay/cs_test_abc123xyz",
 *   "session_id": "cs_test_abc123xyz"
 * }
 * 
 * Used by:
 * - apps/customer/src/app/(pages)/checkout/page.tsx
 * 
 * @example
 * {
 *   url: "https://checkout.stripe.com/c/pay/cs_test_abc123xyz",
 *   session_id: "cs_test_abc123xyz"
 * }
 * 
 * Note: This schema is CORRECT - matches backend exactly.
 */
export const CheckoutSessionResponseSchema = z.object({
  url: z
    .string()
    .url()
    .describe('Full URL to redirect user to Stripe Checkout page'),
  session_id: z
    .string()
    .startsWith('cs_')
    .describe('Stripe Checkout Session ID (starts with "cs_")'),
});

export type CheckoutSessionResponse = z.infer<typeof CheckoutSessionResponseSchema>;

/**
 * ⚠️ ENDPOINT NOT IMPLEMENTED - FRONTEND PLACEHOLDER CODE
 * 
 * Schema for POST /api/v1/payments/checkout-session (VERIFY endpoint)
 * Intended to verify a Stripe Checkout Session and retrieve payment details
 * 
 * ❌ CRITICAL: This endpoint does NOT exist in the backend!
 * - Frontend calls: apps/customer/src/app/(pages)/checkout/page.tsx line 70
 * - Frontend calls: apps/customer/src/app/(pages)/checkout/success/page.tsx line 56
 * - Backend: No matching endpoint in stripe.py
 * 
 * Frontend uses type assertion `as unknown as CheckoutSession` to bypass validation.
 * This is placeholder code for an incomplete feature.
 * 
 * @future To implement this endpoint:
 * 1. Add backend route: @router.post("/v1/payments/checkout-session")
 * 2. Call stripe.checkout.Session.retrieve(session_id)
 * 3. Return session details with payment_status, amount_total, customer_details
 * 4. Update schema to match actual Stripe Session object returned
 * 
 * @example Expected response when implemented:
 * {
 *   id: "cs_test_abc123xyz",
 *   status: "complete",
 *   payment_status: "paid",
 *   amount_total: 50000,
 *   currency: "usd",
 *   customer_details: {
 *     email: "customer@example.com",
 *     name: "John Doe"
 *   },
 *   metadata: {
 *     booking_id: "123e4567-e89b-12d3-a456-426614174000"
 *   },
 *   payment_intent: "pi_3ABC123"
 * }
 */
export const CheckoutSessionVerifyResponseSchema = z.object({
  id: z
    .string()
    .startsWith('cs_')
    .describe('Stripe Checkout Session ID'),
  status: z
    .enum(['open', 'complete', 'expired'])
    .describe('Session status'),
  payment_status: z
    .enum(['paid', 'unpaid', 'no_payment_required'])
    .describe('Payment status of the session'),
  amount_total: z
    .number()
    .int()
    .nonnegative()
    .describe('Total amount in cents'),
  currency: z
    .string()
    .length(3)
    .toLowerCase()
    .describe('Currency code'),
  customer_details: z
    .object({
      email: z.string().email().optional(),
      name: z.string().optional(),
      phone: z.string().optional(),
    })
    .optional()
    .describe('Customer details from Stripe session'),
  metadata: z
    .record(z.string())
    .optional()
    .describe('Session metadata'),
  payment_intent: z
    .string()
    .startsWith('pi_')
    .optional()
    .describe('Associated PaymentIntent ID if using payment mode'),
}).describe('⚠️ NOT IMPLEMENTED: Checkout session verification - endpoint missing');

export type CheckoutSessionVerifyResponse = z.infer<typeof CheckoutSessionVerifyResponseSchema>;

/**
 * Export all schemas for easy import
 */
export const PaymentResponseSchemas = {
  PaymentIntent: PaymentIntentResponseSchema,
  CheckoutSession: CheckoutSessionResponseSchema,
  CheckoutSessionVerify: CheckoutSessionVerifyResponseSchema,
} as const;
