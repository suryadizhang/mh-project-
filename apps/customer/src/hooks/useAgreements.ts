/**
 * useAgreements Hook - Agreements API Integration
 * ================================================
 *
 * Handles all interactions with the agreements API for legal protection:
 * - Slot holds (temporary reservation)
 * - Agreement signing (liability waiver + allergen disclosure)
 * - Agreement status checking
 *
 * SSoT Compliant: NO fallback values for business data.
 *
 * Related Backend: apps/backend/src/routers/v1/agreements.py
 * Related Component: BookingAgreementModal.tsx
 *
 * @see 20-SINGLE_SOURCE_OF_TRUTH.instructions.md
 * @see docs/04-DEPLOYMENT/LEGAL_PROTECTION_IMPLEMENTATION.md
 */

'use client';

import { useState, useCallback } from 'react';
import { apiFetch } from '@/lib/api';

// =============================================================================
// TYPES - Matching backend Pydantic models from agreements.py
// =============================================================================

/**
 * Request to sign an agreement.
 * Maps to SignAgreementRequest in backend.
 */
export interface SignAgreementRequest {
  /** Slot hold token from createSlotHold */
  hold_token: string;
  /** Agreement type being signed */
  agreement_type: 'liability_waiver' | 'allergen_disclosure';
  /** Base64 PNG of signature image from SignaturePad */
  signature_image_base64: string;
  /** Customer's typed name (for record) */
  typed_name?: string;
  /** Customer email for confirmation */
  customer_email: string;
  /** How agreement was signed */
  signing_method?: 'online' | 'sms_link' | 'phone' | 'in_person' | 'ai_chat';
  /** Common allergens selected */
  common_allergens?: string[];
  /** Free-text allergen description */
  other_allergens?: string;
  /** Customer confirms they asked all guests */
  allergen_confirmed?: boolean;
}

/**
 * Response from signing an agreement.
 * Maps to SignAgreementResponse in backend.
 */
export interface SignAgreementResponse {
  success: boolean;
  agreement_id: string;
  booking_id: string;
  signed_at: string;
  confirmation_pdf_url?: string;
  message: string;
}

/**
 * Request to create a slot hold (temporary reservation).
 */
export interface CreateSlotHoldRequest {
  station_id: string;
  event_date: string; // ISO date string
  slot_time: string; // "12PM", "3PM", "6PM", "9PM"
  guest_count: number;
  customer_email?: string;
  customer_phone?: string;
}

/**
 * Response from creating a slot hold.
 */
export interface SlotHoldResponse {
  success: boolean;
  hold_token: string;
  expires_at: string;
  slot_details: {
    station_id: string;
    event_date: string;
    slot_time: string;
    guest_count: number;
  };
  message: string;
}

/**
 * Agreement status response.
 */
export interface AgreementStatusResponse {
  booking_id: string;
  is_signed: boolean;
  signed_at?: string;
  agreement_type?: string;
  signer_name?: string;
}

/**
 * Agreement template response.
 */
export interface AgreementTemplateResponse {
  agreement_type: string;
  version: string;
  title: string;
  content: string;
  effective_date: string;
}

/**
 * Error response from API.
 */
export interface AgreementError {
  success: false;
  error: string;
  detail?: string;
}

// =============================================================================
// HOOK IMPLEMENTATION
// =============================================================================

interface UseAgreementsReturn {
  // State
  isLoading: boolean;
  error: string | null;
  holdToken: string | null;
  holdExpiresAt: Date | null;

  // Actions
  createSlotHold: (request: CreateSlotHoldRequest) => Promise<SlotHoldResponse | null>;
  signAgreement: (request: SignAgreementRequest) => Promise<SignAgreementResponse | null>;
  getAgreementStatus: (bookingId: string) => Promise<AgreementStatusResponse | null>;
  getAgreementTemplate: (
    type: 'liability_waiver' | 'allergen_disclosure',
  ) => Promise<AgreementTemplateResponse | null>;
  releaseHold: (holdToken: string) => Promise<boolean>;
  clearError: () => void;
  clearHold: () => void;
}

/**
 * Hook for managing legal agreements in the booking flow.
 *
 * @example
 * ```tsx
 * const { createSlotHold, signAgreement, isLoading, error } = useAgreements();
 *
 * // Step 1: Create a slot hold when user starts booking
 * const hold = await createSlotHold({
 *   station_id: 'CA-FREMONT-001',
 *   event_date: '2025-02-01',
 *   slot_time: '6PM',
 *   guest_count: 15
 * });
 *
 * // Step 2: Sign agreement with signature
 * const result = await signAgreement({
 *   hold_token: hold.hold_token,
 *   agreement_type: 'liability_waiver',
 *   signature_image_base64: signaturePadData,
 *   customer_email: 'customer@example.com',
 *   common_allergens: ['shellfish'],
 *   allergen_confirmed: true
 * });
 * ```
 */
export function useAgreements(): UseAgreementsReturn {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [holdToken, setHoldToken] = useState<string | null>(null);
  const [holdExpiresAt, setHoldExpiresAt] = useState<Date | null>(null);

  /**
   * Clear any error state.
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  /**
   * Clear hold state (e.g., when modal closes).
   */
  const clearHold = useCallback(() => {
    setHoldToken(null);
    setHoldExpiresAt(null);
  }, []);

  /**
   * Create a temporary slot hold (2-hour expiry).
   * Prevents double-booking while user fills out agreement.
   */
  const createSlotHold = useCallback(
    async (request: CreateSlotHoldRequest): Promise<SlotHoldResponse | null> => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await apiFetch<SlotHoldResponse>('/api/v1/agreements/holds', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(request),
        });

        if (response && response.success && response.data) {
          setHoldToken(response.data.hold_token);
          setHoldExpiresAt(new Date(response.data.expires_at));
          return response.data;
        }

        // Handle error response
        setError(response?.error || 'Failed to create slot hold');
        return null;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Network error creating slot hold';
        setError(errorMessage);
        console.error('[useAgreements] createSlotHold error:', err);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [],
  );

  /**
   * Sign a legal agreement with digital signature.
   * Creates immutable record in signed_agreements table.
   */
  const signAgreement = useCallback(
    async (request: SignAgreementRequest): Promise<SignAgreementResponse | null> => {
      setIsLoading(true);
      setError(null);

      // Validate signature is provided
      if (!request.signature_image_base64) {
        setError('Signature is required');
        setIsLoading(false);
        return null;
      }

      try {
        const response = await apiFetch<SignAgreementResponse>('/api/v1/agreements/sign', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(request),
        });

        if (response && response.success && response.data) {
          // Clear hold after successful signing (it's now converted to booking)
          clearHold();
          return response.data;
        }

        // Handle error response
        setError(response?.error || 'Failed to sign agreement');
        return null;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Network error signing agreement';
        setError(errorMessage);
        console.error('[useAgreements] signAgreement error:', err);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [clearHold],
  );

  /**
   * Check if an agreement has been signed for a booking.
   */
  const getAgreementStatus = useCallback(
    async (bookingId: string): Promise<AgreementStatusResponse | null> => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await apiFetch<AgreementStatusResponse>(
          `/api/v1/agreements/status/${bookingId}`,
        );

        if (response && response.success && response.data) {
          return response.data;
        }

        setError(response?.error || 'Failed to fetch agreement status');
        return null;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Network error checking agreement status';
        setError(errorMessage);
        console.error('[useAgreements] getAgreementStatus error:', err);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [],
  );

  /**
   * Get the current active agreement template for display.
   */
  const getAgreementTemplate = useCallback(
    async (
      type: 'liability_waiver' | 'allergen_disclosure',
    ): Promise<AgreementTemplateResponse | null> => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await apiFetch<AgreementTemplateResponse>(
          `/api/v1/agreements/templates/${type}`,
        );

        if (response && response.success && response.data) {
          return response.data;
        }

        setError(response?.error || 'Failed to fetch agreement template');
        return null;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Network error fetching agreement template';
        setError(errorMessage);
        console.error('[useAgreements] getAgreementTemplate error:', err);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [],
  );

  /**
   * Release a slot hold (e.g., when user cancels).
   */
  const releaseHold = useCallback(
    async (token: string): Promise<boolean> => {
      setIsLoading(true);
      setError(null);

      try {
        await apiFetch(`/api/v1/agreements/holds/${token}`, {
          method: 'DELETE',
        });

        clearHold();
        return true;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Network error releasing hold';
        setError(errorMessage);
        console.error('[useAgreements] releaseHold error:', err);
        return false;
      } finally {
        setIsLoading(false);
      }
    },
    [clearHold],
  );

  return {
    // State
    isLoading,
    error,
    holdToken,
    holdExpiresAt,

    // Actions
    createSlotHold,
    signAgreement,
    getAgreementStatus,
    getAgreementTemplate,
    releaseHold,
    clearError,
    clearHold,
  };
}

export default useAgreements;
