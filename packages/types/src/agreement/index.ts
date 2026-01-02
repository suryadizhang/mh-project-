/**
 * Agreement Types
 * ===============
 *
 * Types for digital agreements and liability waivers.
 *
 * Features:
 * - Digital signature capture (SignaturePad canvas)
 * - Immutable signed agreements (never modified after signing)
 * - Multi-channel tracking (online, sms_link, phone, in_person, ai_chat)
 * - PDF generation and storage
 * - 7-year retention for legal compliance
 *
 * @module @myhibachi/types/agreement
 */

import { z } from 'zod';

// ===========================================================
// CONSTANTS
// ===========================================================

/**
 * Agreement types supported.
 */
export const AGREEMENT_TYPE = {
  LIABILITY_WAIVER: 'liability_waiver',
  ALLERGEN_DISCLOSURE: 'allergen_disclosure',
  TERMS_OF_SERVICE: 'terms_of_service',
} as const;

export type AgreementType =
  (typeof AGREEMENT_TYPE)[keyof typeof AGREEMENT_TYPE];

/**
 * How the agreement was signed.
 */
export const SIGNING_METHOD = {
  ONLINE: 'online', // Customer signed through website during booking
  SMS_LINK: 'sms_link', // Customer clicked link sent via SMS
  PHONE: 'phone', // Staff collected verbal agreement over phone
  IN_PERSON: 'in_person', // Chef collected signature at venue
  AI_CHAT: 'ai_chat', // Customer agreed through AI assistant
} as const;

export type SigningMethod =
  (typeof SIGNING_METHOD)[keyof typeof SIGNING_METHOD];

// ===========================================================
// INTERFACES
// ===========================================================

/**
 * Agreement template stored in database.
 */
export interface AgreementTemplate {
  id: string;
  agreementType: AgreementType;
  version: string; // e.g., "2025.1"
  title: string;
  contentMarkdown: string; // Template with {{variable}} placeholders
  effectiveDate: string; // ISO date
  isActive: boolean;
  variableRefs: string[]; // List of variables used in template
  createdAt: string;
  updatedAt: string;
  createdBy: string | null;
}

/**
 * Signed agreement record (immutable after creation).
 */
export interface SignedAgreement {
  id: string;
  bookingId: string | null;
  customerId: string;
  agreementType: AgreementType;
  agreementVersion: string;
  agreementText: string; // Full text at time of signing

  // Signature data
  signatureImage: string | null; // Base64 PNG of canvas signature
  signatureTypedName: string | null; // If typed instead of drawn
  signedAt: string;

  // Verification data
  signerIpAddress: string | null;
  signerUserAgent: string | null;
  signerDeviceFingerprint: string | null;

  // Confirmation
  confirmationEmailSentAt: string | null;
  confirmationPdfUrl: string | null;

  // Multi-channel tracking
  signingMethod: SigningMethod;

  // Immutable - only created_at, no updated_at
  createdAt: string;
}

/**
 * Agreement response for API.
 */
export interface AgreementResponse {
  success: boolean;
  data: {
    id: string;
    agreementType: AgreementType;
    agreementVersion: string;
    title: string;
    contentHtml: string; // Rendered with current values
    effectiveDate: string;
    variablesUsed: Record<string, string>; // For audit trail
  };
  message?: string;
}

/**
 * Request to sign an agreement.
 */
export interface SignAgreementPayload {
  slotHoldToken?: string; // For slot hold flow
  bookingId?: string; // For existing booking
  agreementType: AgreementType;
  agreementVersion: string;

  // Signature
  signatureData?: string; // Base64 encoded PNG from SignaturePad
  typedName?: string; // Alternative to drawn signature

  // Verification
  consentChecked: boolean;
  allergenConfirmed?: boolean; // For allergen disclosure

  // Multi-channel
  signingMethod: SigningMethod;
}

/**
 * Allergen disclosure data collected at booking.
 */
export interface AllergenDisclosure {
  commonAllergens: string[]; // ['shellfish', 'soy', 'eggs']
  otherAllergens: string; // Free text
  confirmed: boolean; // "I have asked all guests about allergies"
  confirmedAt: string;
  confirmedMethod: SigningMethod;
}

/**
 * Common allergen reference data.
 */
export interface CommonAllergen {
  id: number;
  name: string; // 'shellfish'
  displayName: string; // 'Shellfish (shrimp, crab, lobster)'
  icon: string; // '🦐'
  displayOrder: number;
  isActive: boolean;
}

/**
 * Agreement signing link for SMS/email.
 */
export interface SigningLink {
  token: string;
  url: string;
  expiresAt: string;
  slotHoldId: string;
  agreementType: AgreementType;
  customerName: string;
  customerEmail: string;
  customerPhone: string;
  sentAt: string | null;
  signedAt: string | null;
}

// ===========================================================
// ZOD SCHEMAS
// ===========================================================

export const AgreementTypeSchema = z.enum([
  'liability_waiver',
  'allergen_disclosure',
  'terms_of_service',
]);

export const SigningMethodSchema = z.enum([
  'online',
  'sms_link',
  'phone',
  'in_person',
  'ai_chat',
]);

export const AgreementTemplateSchema = z.object({
  id: z.string().uuid(),
  agreementType: AgreementTypeSchema,
  version: z.string().regex(/^\d{4}\.\d+$/), // e.g., "2025.1"
  title: z.string().min(1).max(200),
  contentMarkdown: z.string().min(1),
  effectiveDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  isActive: z.boolean(),
  variableRefs: z.array(z.string()),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
  createdBy: z.string().uuid().nullable(),
});

export const SignedAgreementSchema = z.object({
  id: z.string().uuid(),
  bookingId: z.string().uuid().nullable(),
  customerId: z.string().uuid(),
  agreementType: AgreementTypeSchema,
  agreementVersion: z.string(),
  agreementText: z.string(),
  signatureImage: z.string().nullable(),
  signatureTypedName: z.string().nullable(),
  signedAt: z.string().datetime(),
  signerIpAddress: z.string().nullable(),
  signerUserAgent: z.string().nullable(),
  signerDeviceFingerprint: z.string().nullable(),
  confirmationEmailSentAt: z.string().datetime().nullable(),
  confirmationPdfUrl: z.string().url().nullable(),
  signingMethod: SigningMethodSchema,
  createdAt: z.string().datetime(),
});

export const SignAgreementPayloadSchema = z
  .object({
    slotHoldToken: z.string().optional(),
    bookingId: z.string().uuid().optional(),
    agreementType: AgreementTypeSchema,
    agreementVersion: z.string().regex(/^\d{4}\.\d+$/),
    signatureData: z.string().optional(),
    typedName: z.string().max(200).optional(),
    consentChecked: z.literal(true, {
      errorMap: () => ({ message: 'You must agree to the terms' }),
    }),
    allergenConfirmed: z.boolean().optional(),
    signingMethod: SigningMethodSchema,
  })
  .refine(data => data.signatureData || data.typedName, {
    message: 'Either signature or typed name is required',
  });

export const AllergenDisclosureSchema = z.object({
  commonAllergens: z.array(z.string()),
  otherAllergens: z.string().max(500),
  confirmed: z.literal(true, {
    errorMap: () => ({
      message: 'You must confirm you have asked all guests about allergies',
    }),
  }),
  confirmedAt: z.string().datetime(),
  confirmedMethod: SigningMethodSchema,
});

export const CommonAllergenSchema = z.object({
  id: z.number().int().positive(),
  name: z.string(),
  displayName: z.string(),
  icon: z.string(),
  displayOrder: z.number().int(),
  isActive: z.boolean(),
});

// ===========================================================
// TYPE EXPORTS FROM SCHEMAS
// ===========================================================

export type AgreementTemplateData = z.infer<typeof AgreementTemplateSchema>;
export type SignedAgreementData = z.infer<typeof SignedAgreementSchema>;
export type SignAgreementPayloadData = z.infer<
  typeof SignAgreementPayloadSchema
>;
export type AllergenDisclosureData = z.infer<typeof AllergenDisclosureSchema>;
export type CommonAllergenData = z.infer<typeof CommonAllergenSchema>;
