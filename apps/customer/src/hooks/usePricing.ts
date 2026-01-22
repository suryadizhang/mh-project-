/**
 * usePricing Hook
 * React hook for accessing dynamic pricing from /api/v1/config/all (SSoT endpoint)
 *
 * Features:
 * - Fetches from /api/v1/config/all which includes ALL pricing data
 * - Loading states
 * - Error handling (NO FALLBACKS per SSoT rules)
 * - Includes partyMinimum and depositAmount
 *
 * @see 20-SINGLE_SOURCE_OF_TRUTH.instructions.md
 */

import { useEffect, useState, useCallback } from 'react';

import {
  type CurrentPricingResponse,
  getAddonPrices,
  getBasePricing,
  getCurrentPricing,
  hasPricingData,
} from '@/lib/pricingApi';

interface UsePricingResult {
  // Raw pricing data from /api/v1/pricing/current (for menu items)
  pricing: CurrentPricingResponse | null;

  // Loading and error states
  isLoading: boolean;
  error: string | null;

  // Convenience values - undefined when loading/unavailable (NO FALLBACKS - API is source of truth)
  adultPrice: number | undefined;
  childPrice: number | undefined;
  childFreeUnderAge: number | undefined;
  partyMinimum: number | undefined;
  depositAmount: number | undefined;
  depositRefundableDays: number | undefined;
  freeMiles: number | undefined;
  perMileRate: number | undefined;
  addonPrices: Record<string, number> | undefined;

  // Booking rules
  minAdvanceHours: number | undefined;

  // Timing (deadlines/cutoffs in hours) - SSoT from dynamic_variables
  menuChangeCutoffHours: number | undefined;
  guestCountFinalizeHours: number | undefined;
  freeRescheduleHours: number | undefined;

  // Service (duration and logistics)
  standardDurationMinutes: number | undefined;
  extendedDurationMinutes: number | undefined;
  chefArrivalMinutesBefore: number | undefined;

  // Policy (fees and limits)
  rescheduleFee: number | undefined; // in dollars (converted from cents)
  freeRescheduleCount: number | undefined;

  // Contact (business info)
  businessPhone: string | undefined;
  businessEmail: string | undefined;

  // Helper functions
  hasData: boolean;
  refetch: () => Promise<void>;
}

// Business config from /api/v1/config/all
interface BusinessConfig {
  pricing: {
    adult_price_cents: number;
    child_price_cents: number;
    child_free_under_age: number;
    party_minimum_cents: number;
  };
  travel: {
    free_miles: number;
    per_mile_cents: number;
  };
  deposit: {
    deposit_amount_cents: number;
    deposit_refundable_days: number;
  };
  booking: {
    min_advance_hours: number;
  };
  timing?: {
    menu_change_cutoff_hours: number;
    guest_count_finalize_hours: number;
    free_reschedule_hours: number;
  };
  service?: {
    standard_duration_minutes: number;
    extended_duration_minutes: number;
    chef_arrival_minutes_before: number;
  };
  policy?: {
    reschedule_fee_cents: number;
    free_reschedule_count: number;
  };
  contact?: {
    business_phone: string;
    business_email: string;
  };
  source: string;
}

/**
 * Hook to fetch and manage current pricing data
 * Uses /api/v1/config/all for complete SSoT data including partyMinimum and depositAmount
 *
 * @example
 * ```tsx
 * function QuoteCalculator() {
 *   const { pricing, isLoading, adultPrice, childPrice, partyMinimum, depositAmount } = usePricing();
 *
 *   if (isLoading) return <div>Loading pricing...</div>;
 *
 *   return (
 *     <div>
 *       <p>Adult: ${adultPrice}</p>
 *       <p>Child: ${childPrice}</p>
 *       <p>Minimum: ${partyMinimum}</p>
 *       <p>Deposit: ${depositAmount}</p>
 *     </div>
 *   );
 * }
 * ```
 */
export function usePricing(): UsePricingResult {
  const [pricing, setPricing] = useState<CurrentPricingResponse | null>(null);
  const [businessConfig, setBusinessConfig] = useState<BusinessConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPricing = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch from local proxy route to avoid CORS issues
      // The proxy route forwards to backend /api/v1/config/all
      // NOTE: Must include trailing slash to avoid 308 redirect from Next.js
      console.log('[usePricing] Starting fetch from /api/v1/config/');
      const configResponse = await fetch('/api/v1/config/', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      console.log('[usePricing] Response status:', configResponse.status, configResponse.ok);

      if (configResponse.ok) {
        const configData = await configResponse.json();
        console.log('[usePricing] Received config data:', {
          hasPricing: !!configData?.pricing,
          adultPriceCents: configData?.pricing?.adult_price_cents,
          partyMinimumCents: configData?.pricing?.party_minimum_cents,
          depositCents: configData?.deposit?.deposit_amount_cents,
        });
        setBusinessConfig(configData);
      } else {
        console.error('[usePricing] Failed to fetch config:', configResponse.status);
        setError('Failed to fetch pricing configuration');
      }

      // Also fetch menu items from /api/v1/pricing/current (for addon prices)
      const pricingData = await getCurrentPricing();
      if (pricingData) {
        setPricing(pricingData);
      }
    } catch (err) {
      console.error('Error fetching pricing:', err);
      setError('Failed to fetch pricing (backend unavailable)');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPricing();
  }, [fetchPricing]);

  // Extract convenience values from businessConfig (SSoT)
  // NO FALLBACK VALUES: Per instruction 01-CORE_PRINCIPLES Rule #14
  const adultPrice = businessConfig?.pricing?.adult_price_cents
    ? businessConfig.pricing.adult_price_cents / 100
    : undefined;
  const childPrice = businessConfig?.pricing?.child_price_cents
    ? businessConfig.pricing.child_price_cents / 100
    : undefined;
  const childFreeUnderAge = businessConfig?.pricing?.child_free_under_age;
  const partyMinimum = businessConfig?.pricing?.party_minimum_cents
    ? businessConfig.pricing.party_minimum_cents / 100
    : undefined;
  const depositAmount = businessConfig?.deposit?.deposit_amount_cents
    ? businessConfig.deposit.deposit_amount_cents / 100
    : undefined;
  const depositRefundableDays = businessConfig?.deposit?.deposit_refundable_days;
  const freeMiles = businessConfig?.travel?.free_miles;
  const perMileRate = businessConfig?.travel?.per_mile_cents
    ? businessConfig.travel.per_mile_cents / 100
    : undefined;

  // Booking rules
  const minAdvanceHours = businessConfig?.booking?.min_advance_hours;

  // Timing (deadlines/cutoffs) from SSoT
  const menuChangeCutoffHours = businessConfig?.timing?.menu_change_cutoff_hours;
  const guestCountFinalizeHours = businessConfig?.timing?.guest_count_finalize_hours;
  const freeRescheduleHours = businessConfig?.timing?.free_reschedule_hours;

  // Service (duration and logistics)
  const standardDurationMinutes = businessConfig?.service?.standard_duration_minutes;
  const extendedDurationMinutes = businessConfig?.service?.extended_duration_minutes;
  const chefArrivalMinutesBefore = businessConfig?.service?.chef_arrival_minutes_before;

  // Policy (fees and limits) - convert cents to dollars
  const rescheduleFee = businessConfig?.policy?.reschedule_fee_cents
    ? businessConfig.policy.reschedule_fee_cents / 100
    : undefined;
  const freeRescheduleCount = businessConfig?.policy?.free_reschedule_count;

  // Contact (business info)
  const businessPhone = businessConfig?.contact?.business_phone;
  const businessEmail = businessConfig?.contact?.business_email;

  // Debug logging for pricing extraction
  console.log('[usePricing] Extracted values:', {
    businessConfig: businessConfig !== null,
    adultPrice,
    childPrice,
    partyMinimum,
    depositAmount,
    depositRefundableDays,
    freeMiles,
    perMileRate,
    minAdvanceHours,
    menuChangeCutoffHours,
    standardDurationMinutes,
    rescheduleFee,
    businessPhone,
    isLoading,
  });

  // Addon prices from /api/v1/pricing/current
  const addonPrices = pricing ? getAddonPrices(pricing) : undefined;
  const hasData = businessConfig !== null || hasPricingData(pricing);

  return {
    pricing,
    isLoading,
    error,
    adultPrice,
    childPrice,
    childFreeUnderAge,
    partyMinimum,
    depositAmount,
    depositRefundableDays,
    freeMiles,
    perMileRate,
    addonPrices,
    minAdvanceHours,
    menuChangeCutoffHours,
    guestCountFinalizeHours,
    freeRescheduleHours,
    standardDurationMinutes,
    extendedDurationMinutes,
    chefArrivalMinutesBefore,
    rescheduleFee,
    freeRescheduleCount,
    businessPhone,
    businessEmail,
    hasData,
    refetch: fetchPricing,
  };
}
