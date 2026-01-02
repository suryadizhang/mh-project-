/**
 * Slot Hold Types
 * ================
 *
 * Types for the two-phase slot hold system:
 * 1. Phase 1: Hold created → 2 hours to sign agreement
 * 2. Phase 2: Agreement signed → 4 hours to pay deposit
 *
 * Warning notifications sent 1 hour before each deadline.
 *
 * @module @myhibachi/types/slot-hold
 */

import { z } from 'zod';

// ===========================================================
// CONSTANTS (Match Python Enums)
// ===========================================================

/**
 * Slot hold status values.
 *
 * PENDING_SIGNATURE → PENDING_DEPOSIT → COMPLETED | EXPIRED | CANCELLED
 */
export const SLOT_HOLD_STATUS = {
  PENDING_SIGNATURE: 'pending_signature',
  PENDING_DEPOSIT: 'pending_deposit',
  COMPLETED: 'completed',
  EXPIRED: 'expired',
  CANCELLED: 'cancelled',
} as const;

export type SlotHoldStatus =
  (typeof SLOT_HOLD_STATUS)[keyof typeof SLOT_HOLD_STATUS];

/**
 * Deposit payment methods.
 */
export const DEPOSIT_PAYMENT_METHOD = {
  STRIPE: 'stripe',
  ZELLE: 'zelle',
  VENMO: 'venmo',
  CASH: 'cash',
} as const;

export type DepositPaymentMethod =
  (typeof DEPOSIT_PAYMENT_METHOD)[keyof typeof DEPOSIT_PAYMENT_METHOD];

/**
 * Cancellation reason codes (descriptive strings per user decision).
 */
export const CANCELLATION_REASON = {
  SIGNING_TIMEOUT: 'SIGNING_TIMEOUT',
  PAYMENT_TIMEOUT: 'PAYMENT_TIMEOUT',
  CUSTOMER_CANCELLED: 'CUSTOMER_CANCELLED',
  ADMIN_CANCELLED: 'ADMIN_CANCELLED',
  SLOT_UNAVAILABLE: 'SLOT_UNAVAILABLE',
  DUPLICATE_HOLD: 'DUPLICATE_HOLD',
} as const;

export type CancellationReason =
  (typeof CANCELLATION_REASON)[keyof typeof CANCELLATION_REASON];

/**
 * Agreement status derived from slot hold.
 */
export const AGREEMENT_STATUS = {
  PENDING: 'pending',
  SIGNED: 'signed',
  EXPIRED: 'expired',
} as const;

export type AgreementStatus =
  (typeof AGREEMENT_STATUS)[keyof typeof AGREEMENT_STATUS];

/**
 * Deposit status derived from slot hold.
 */
export const DEPOSIT_STATUS = {
  NOT_DUE: 'not_due', // Agreement not signed yet
  PENDING: 'pending', // Awaiting payment
  PAID: 'paid',
  EXPIRED: 'expired',
} as const;

export type DepositStatus =
  (typeof DEPOSIT_STATUS)[keyof typeof DEPOSIT_STATUS];

// ===========================================================
// INTERFACES
// ===========================================================

/**
 * Slot hold record from database.
 */
export interface SlotHold {
  id: string;
  bookingId: string | null;
  stationId: string;
  slotDate: string; // ISO date string YYYY-MM-DD
  slotTime: string; // HH:MM format
  customerEmail: string;
  customerPhone: string;
  customerName: string;
  guestCount: number;
  status: SlotHoldStatus;

  // Token for public access
  token: string;
  tokenExpiresAt: string; // ISO datetime

  // Phase 1: Agreement signing (2 hour deadline)
  agreementSignedAt: string | null;
  signedAgreementId: string | null;
  signingDeadlineAt: string;
  signingWarningSentAt: string | null;

  // Phase 2: Deposit payment (4 hour deadline after signing)
  depositPaidAt: string | null;
  depositPaymentMethod: DepositPaymentMethod | null;
  depositPaymentReference: string | null;
  paymentDeadlineAt: string | null;
  paymentWarningSentAt: string | null;

  // Cancellation
  cancellationReason: CancellationReason | null;

  // Audit fields
  createdAt: string;
  updatedAt: string;
  expiresAt: string;
}

/**
 * API response for GET /api/v1/holds/{token}
 */
export interface SlotHoldResponse {
  success: boolean;
  data: {
    id: string;
    stationId: string;
    slotDate: string;
    slotTime: string;
    customerName: string;
    customerEmail: string;
    guestCount: number;
    status: SlotHoldStatus;

    // Computed status fields for UI
    agreementStatus: AgreementStatus;
    depositStatus: DepositStatus;

    // Deadline information
    signingDeadlineAt: string;
    paymentDeadlineAt: string | null;
    secondsUntilSigningDeadline: number;
    secondsUntilPaymentDeadline: number | null;

    // Flags
    isSigningWarningPeriod: boolean; // Within 1 hour of signing deadline
    isPaymentWarningPeriod: boolean; // Within 1 hour of payment deadline
    canSign: boolean; // Agreement can be signed
    canPay: boolean; // Deposit can be paid
  };
  message?: string;
}

/**
 * Request to sign agreement for a slot hold.
 */
export interface SignAgreementRequest {
  token: string;
  signatureData: string; // Base64 encoded signature image
  signerName: string;
  signerEmail: string;
  signerIpAddress?: string; // Captured server-side
  consentChecked: boolean;
}

/**
 * Response after signing agreement.
 */
export interface SignAgreementResponse {
  success: boolean;
  data: {
    holdId: string;
    signedAgreementId: string;
    signedAt: string;
    paymentDeadlineAt: string;
    depositAmountCents: number;
    paymentMethods: DepositPaymentMethod[];
  };
  message?: string;
}

/**
 * Request to record deposit payment.
 */
export interface RecordDepositRequest {
  token: string;
  paymentMethod: DepositPaymentMethod;
  paymentReference: string; // Stripe session ID, Zelle confirmation, etc.
  amountCents: number;
}

/**
 * Response after recording deposit.
 */
export interface RecordDepositResponse {
  success: boolean;
  data: {
    holdId: string;
    bookingId: string; // Slot hold converted to booking
    depositPaidAt: string;
    paymentMethod: DepositPaymentMethod;
    confirmationNumber: string;
  };
  message?: string;
}

// ===========================================================
// ZOD SCHEMAS
// ===========================================================

export const SlotHoldStatusSchema = z.enum([
  'pending_signature',
  'pending_deposit',
  'completed',
  'expired',
  'cancelled',
]);

export const DepositPaymentMethodSchema = z.enum([
  'stripe',
  'zelle',
  'venmo',
  'cash',
]);

export const CancellationReasonSchema = z.enum([
  'SIGNING_TIMEOUT',
  'PAYMENT_TIMEOUT',
  'CUSTOMER_CANCELLED',
  'ADMIN_CANCELLED',
  'SLOT_UNAVAILABLE',
  'DUPLICATE_HOLD',
]);

export const AgreementStatusSchema = z.enum(['pending', 'signed', 'expired']);

export const DepositStatusSchema = z.enum([
  'not_due',
  'pending',
  'paid',
  'expired',
]);

export const SlotHoldResponseSchema = z.object({
  success: z.boolean(),
  data: z.object({
    id: z.string().uuid(),
    stationId: z.string().uuid(),
    slotDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
    slotTime: z.string().regex(/^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/),
    customerName: z.string(),
    customerEmail: z.string().email(),
    guestCount: z.number().int().min(1),
    status: SlotHoldStatusSchema,
    agreementStatus: AgreementStatusSchema,
    depositStatus: DepositStatusSchema,
    signingDeadlineAt: z.string().datetime(),
    paymentDeadlineAt: z.string().datetime().nullable(),
    secondsUntilSigningDeadline: z.number(),
    secondsUntilPaymentDeadline: z.number().nullable(),
    isSigningWarningPeriod: z.boolean(),
    isPaymentWarningPeriod: z.boolean(),
    canSign: z.boolean(),
    canPay: z.boolean(),
  }),
  message: z.string().optional(),
});

export const SignAgreementRequestSchema = z.object({
  token: z.string().min(1),
  signatureData: z.string().min(1), // Base64 encoded
  signerName: z.string().min(1).max(200),
  signerEmail: z.string().email(),
  consentChecked: z.literal(true, {
    errorMap: () => ({ message: 'You must agree to the terms' }),
  }),
});

export const SignAgreementResponseSchema = z.object({
  success: z.boolean(),
  data: z.object({
    holdId: z.string().uuid(),
    signedAgreementId: z.string().uuid(),
    signedAt: z.string().datetime(),
    paymentDeadlineAt: z.string().datetime(),
    depositAmountCents: z.number().int().positive(),
    paymentMethods: z.array(DepositPaymentMethodSchema),
  }),
  message: z.string().optional(),
});

export const RecordDepositRequestSchema = z.object({
  token: z.string().min(1),
  paymentMethod: DepositPaymentMethodSchema,
  paymentReference: z.string().min(1),
  amountCents: z.number().int().positive(),
});

export const RecordDepositResponseSchema = z.object({
  success: z.boolean(),
  data: z.object({
    holdId: z.string().uuid(),
    bookingId: z.string().uuid(),
    depositPaidAt: z.string().datetime(),
    paymentMethod: DepositPaymentMethodSchema,
    confirmationNumber: z.string(),
  }),
  message: z.string().optional(),
});

// ===========================================================
// TYPE EXPORTS FROM SCHEMAS
// ===========================================================

export type SlotHoldResponseData = z.infer<typeof SlotHoldResponseSchema>;
export type SignAgreementRequestData = z.infer<
  typeof SignAgreementRequestSchema
>;
export type SignAgreementResponseData = z.infer<
  typeof SignAgreementResponseSchema
>;
export type RecordDepositRequestData = z.infer<
  typeof RecordDepositRequestSchema
>;
export type RecordDepositResponseData = z.infer<
  typeof RecordDepositResponseSchema
>;
