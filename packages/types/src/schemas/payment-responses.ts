import { z } from 'zod';
import { PaymentInfoSchema } from '../index';

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
 * Schema for POST /api/v1/payments/create-intent
 * Creates a Stripe PaymentIntent for processing payment
 * 
 * Used by:
 * - apps/customer/src/app/(pages)/payment/page.tsx
 * 
 * @example
 * {
 *   success: true,
 *   data: {
 *     clientSecret: "pi_3ABC123_secret_xyz",
 *     paymentIntentId: "pi_3ABC123",
 *     amount: 50000,
 *     currency: "usd",
 *     status: "requires_payment_method",
 *     bookingId: "123e4567-e89b-12d3-a456-426614174000"
 *   },
 *   timestamp: "2025-10-12T10:30:00.000Z",
 *   requestId: "123e4567-e89b-12d3-a456-426614174000"
 * }
 */
export const PaymentIntentResponseSchema = BaseResponseSchema.extend({
  data: z.object({
    clientSecret: z
      .string()
      .min(1)
      .describe('Stripe client secret for confirming payment on client side'),
    paymentIntentId: z
      .string()
      .startsWith('pi_')
      .describe('Stripe PaymentIntent ID (starts with "pi_")'),
    amount: z
      .number()
      .int()
      .positive()
      .describe('Amount in cents (e.g., 50000 = $500.00)'),
    currency: z
      .string()
      .length(3)
      .toLowerCase()
      .default('usd')
      .describe('Three-letter ISO currency code (lowercase)'),
    status: z
      .enum([
        'requires_payment_method',
        'requires_confirmation',
        'requires_action',
        'processing',
        'requires_capture',
        'canceled',
        'succeeded',
      ])
      .describe('Current status of the PaymentIntent'),
    bookingId: z
      .string()
      .uuid()
      .describe('Associated booking ID for this payment'),
    description: z
      .string()
      .optional()
      .describe('Optional payment description'),
    metadata: z
      .record(z.string())
      .optional()
      .describe('Optional metadata attached to the payment'),
  }).describe('Payment intent data'),
  error: z.string().optional().describe('Error message if success is false'),
  message: z.string().optional().describe('User-friendly message'),
});

export type PaymentIntentResponse = z.infer<typeof PaymentIntentResponseSchema>;

/**
 * Schema for POST /api/v1/payments/checkout-session
 * Creates a Stripe Checkout Session for hosted payment page
 * 
 * Used by:
 * - apps/customer/src/app/(pages)/checkout/page.tsx
 * 
 * @example
 * {
 *   success: true,
 *   data: {
 *     sessionId: "cs_test_abc123xyz",
 *     url: "https://checkout.stripe.com/c/pay/cs_test_abc123xyz",
 *     bookingId: "123e4567-e89b-12d3-a456-426614174000",
 *     expiresAt: "2025-10-12T11:30:00.000Z",
 *     amount: 50000,
 *     currency: "usd"
 *   },
 *   timestamp: "2025-10-12T10:30:00.000Z",
 *   requestId: "123e4567-e89b-12d3-a456-426614174000"
 * }
 */
export const CheckoutSessionResponseSchema = BaseResponseSchema.extend({
  data: z.object({
    sessionId: z
      .string()
      .startsWith('cs_')
      .describe('Stripe Checkout Session ID (starts with "cs_")'),
    url: z
      .string()
      .url()
      .describe('Full URL to redirect user to Stripe Checkout page'),
    bookingId: z
      .string()
      .uuid()
      .describe('Associated booking ID for this checkout session'),
    expiresAt: z
      .string()
      .datetime()
      .describe('ISO 8601 timestamp when the session expires'),
    amount: z
      .number()
      .int()
      .positive()
      .describe('Total amount in cents'),
    currency: z
      .string()
      .length(3)
      .toLowerCase()
      .default('usd')
      .describe('Three-letter ISO currency code'),
    status: z
      .enum(['open', 'complete', 'expired'])
      .optional()
      .describe('Current status of the checkout session'),
    paymentStatus: z
      .enum(['paid', 'unpaid', 'no_payment_required'])
      .optional()
      .describe('Payment status of the session'),
  }).describe('Checkout session data'),
  error: z.string().optional().describe('Error message if success is false'),
  message: z.string().optional().describe('User-friendly message'),
});

export type CheckoutSessionResponse = z.infer<typeof CheckoutSessionResponseSchema>;

/**
 * Schema for GET /api/v1/payments/checkout-session/verify
 * Verifies a Stripe Checkout Session and retrieves payment details
 * 
 * Used by:
 * - apps/customer/src/app/(pages)/checkout/success/page.tsx
 * 
 * @example
 * {
 *   success: true,
 *   data: {
 *     sessionId: "cs_test_abc123xyz",
 *     paymentStatus: "paid",
 *     bookingId: "123e4567-e89b-12d3-a456-426614174000",
 *     confirmationCode: "MHBC-2025-001234",
 *     amount: 50000,
 *     currency: "usd",
 *     paymentIntentId: "pi_3ABC123",
 *     customerEmail: "customer@example.com",
 *     paidAt: "2025-10-12T10:35:00.000Z"
 *   },
 *   timestamp: "2025-10-12T10:36:00.000Z",
 *   requestId: "123e4567-e89b-12d3-a456-426614174000"
 * }
 */
export const CheckoutSessionVerifyResponseSchema = BaseResponseSchema.extend({
  data: z.object({
    sessionId: z
      .string()
      .startsWith('cs_')
      .describe('Stripe Checkout Session ID'),
    paymentStatus: z
      .enum(['paid', 'unpaid', 'no_payment_required'])
      .describe('Payment status of the session'),
    bookingId: z
      .string()
      .uuid()
      .describe('Associated booking ID'),
    confirmationCode: z
      .string()
      .min(1)
      .max(50)
      .describe('Booking confirmation code'),
    amount: z
      .number()
      .int()
      .positive()
      .describe('Amount paid in cents'),
    currency: z
      .string()
      .length(3)
      .toLowerCase()
      .describe('Currency code'),
    paymentIntentId: z
      .string()
      .startsWith('pi_')
      .optional()
      .describe('Optional: Associated PaymentIntent ID'),
    customerEmail: z
      .string()
      .email()
      .describe('Customer email from Stripe session'),
    customerName: z
      .string()
      .optional()
      .describe('Optional: Customer name from Stripe session'),
    paidAt: z
      .string()
      .datetime()
      .optional()
      .describe('Optional: Timestamp when payment was completed'),
    receiptUrl: z
      .string()
      .url()
      .optional()
      .describe('Optional: URL to Stripe receipt'),
    metadata: z
      .record(z.string())
      .optional()
      .describe('Optional: Session metadata'),
  }).describe('Checkout session verification data'),
  error: z.string().optional().describe('Error message if success is false'),
  message: z.string().optional().describe('User-friendly message'),
});

export type CheckoutSessionVerifyResponse = z.infer<typeof CheckoutSessionVerifyResponseSchema>;

/**
 * Schema for GET /api/v1/payments/alternative-payment
 * Retrieves alternative payment options (Zelle, Venmo) and their details
 * 
 * Used by:
 * - apps/customer/src/components/AlternativePaymentOptions.tsx
 * 
 * @example
 * {
 *   success: true,
 *   data: {
 *     options: [
 *       {
 *         method: "zelle",
 *         displayName: "Zelle",
 *         available: true,
 *         details: {
 *           email: "payments@myhibachi.com",
 *           phone: "+1-555-123-4567"
 *         },
 *         instructions: "Send payment to the email or phone number shown. Include your booking confirmation code in the notes.",
 *         processingTime: "Instant"
 *       },
 *       {
 *         method: "venmo",
 *         displayName: "Venmo",
 *         available: true,
 *         details: {
 *           username: "@MyHibachi",
 *           qrCodeUrl: "https://api.myhibachi.com/qr/venmo"
 *         },
 *         instructions: "Send payment to @MyHibachi. Include your booking confirmation code in the notes.",
 *         processingTime: "1-2 business days"
 *       }
 *     ],
 *     bookingId: "123e4567-e89b-12d3-a456-426614174000",
 *     amount: 500.00,
 *     currency: "USD"
 *   },
 *   timestamp: "2025-10-12T10:30:00.000Z",
 *   requestId: "123e4567-e89b-12d3-a456-426614174000"
 * }
 */
export const AlternativePaymentResponseSchema = BaseResponseSchema.extend({
  data: z.object({
    options: z
      .array(
        z.object({
          method: z
            .enum(['zelle', 'venmo'])
            .describe('Payment method identifier'),
          displayName: z
            .string()
            .describe('Human-readable payment method name'),
          available: z
            .boolean()
            .describe('Whether this payment method is currently available'),
          details: z
            .record(z.string())
            .describe('Payment method specific details (email, phone, username, etc.)'),
          instructions: z
            .string()
            .describe('Step-by-step instructions for the customer'),
          processingTime: z
            .string()
            .describe('Estimated time for payment to be processed'),
          qrCodeUrl: z
            .string()
            .url()
            .optional()
            .describe('Optional: URL to QR code for mobile payment'),
          minimumAmount: z
            .number()
            .positive()
            .optional()
            .describe('Optional: Minimum amount in dollars for this method'),
          maximumAmount: z
            .number()
            .positive()
            .optional()
            .describe('Optional: Maximum amount in dollars for this method'),
        })
      )
      .describe('Array of available alternative payment options'),
    bookingId: z
      .string()
      .uuid()
      .describe('Associated booking ID'),
    amount: z
      .number()
      .positive()
      .describe('Total amount to be paid (in dollars, not cents)'),
    currency: z
      .literal('USD')
      .describe('Currency for the payment'),
    confirmationRequired: z
      .boolean()
      .optional()
      .default(true)
      .describe('Whether payment confirmation is required after payment'),
  }).describe('Alternative payment options data'),
  error: z.string().optional().describe('Error message if success is false'),
  message: z.string().optional().describe('User-friendly message'),
});

export type AlternativePaymentResponse = z.infer<typeof AlternativePaymentResponseSchema>;

/**
 * Schema for POST /api/v1/payments/confirm
 * Confirms that an alternative payment has been made
 * 
 * Future usage for manual payment confirmation
 * 
 * @example
 * {
 *   success: true,
 *   data: {
 *     paymentId: "pay_abc123",
 *     bookingId: "123e4567-e89b-12d3-a456-426614174000",
 *     status: "pending_verification",
 *     confirmedAt: "2025-10-12T10:30:00.000Z",
 *     message: "Payment confirmation received. We'll verify and update your booking within 1-2 business days."
 *   },
 *   timestamp: "2025-10-12T10:30:00.000Z",
 *   requestId: "123e4567-e89b-12d3-a456-426614174000"
 * }
 */
export const PaymentConfirmationResponseSchema = BaseResponseSchema.extend({
  data: z.object({
    paymentId: z
      .string()
      .min(1)
      .describe('Internal payment record ID'),
    bookingId: z
      .string()
      .uuid()
      .describe('Associated booking ID'),
    status: z
      .enum([
        'pending_verification',
        'verified',
        'rejected',
        'processing',
      ])
      .describe('Current status of the payment confirmation'),
    confirmedAt: z
      .string()
      .datetime()
      .describe('Timestamp when confirmation was received'),
    verificationMethod: z
      .string()
      .optional()
      .describe('Optional: How the payment will be verified'),
    estimatedVerificationTime: z
      .string()
      .optional()
      .describe('Optional: Estimated time until verification completes'),
    message: z
      .string()
      .optional()
      .describe('Optional: Message for the customer about next steps'),
  }).describe('Payment confirmation data'),
  error: z.string().optional().describe('Error message if success is false'),
  message: z.string().optional().describe('User-friendly message'),
});

export type PaymentConfirmationResponse = z.infer<typeof PaymentConfirmationResponseSchema>;

/**
 * Export all schemas for easy import
 */
export const PaymentResponseSchemas = {
  PaymentIntent: PaymentIntentResponseSchema,
  CheckoutSession: CheckoutSessionResponseSchema,
  CheckoutSessionVerify: CheckoutSessionVerifyResponseSchema,
  AlternativePayment: AlternativePaymentResponseSchema,
  PaymentConfirmation: PaymentConfirmationResponseSchema,
} as const;
