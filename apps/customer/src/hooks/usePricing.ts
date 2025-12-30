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
  freeMiles: number | undefined;
  perMileRate: number | undefined;
  addonPrices: Record<string, number> | undefined;

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
      // Fetch from /api/v1/config/all - the SSoT endpoint with ALL business data
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const configResponse = await fetch(`${apiUrl}/api/v1/config/all`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      if (configResponse.ok) {
        const configData = await configResponse.json();
        setBusinessConfig(configData);
      } else {
        console.error('Failed to fetch config:', configResponse.status);
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
  const freeMiles = businessConfig?.travel?.free_miles;
  const perMileRate = businessConfig?.travel?.per_mile_cents
    ? businessConfig.travel.per_mile_cents / 100
    : undefined;

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
    freeMiles,
    perMileRate,
    addonPrices,
    hasData,
    refetch: fetchPricing,
  };
}
