/**
 * usePricing Hook
 * React hook for accessing dynamic pricing from database
 *
 * Features:
 * - Automatic data fetching on mount
 * - Loading states
 * - Error handling with fallback values
 * - Automatic caching via pricingApi
 * - Helper functions for common pricing calculations
 */

import { useEffect, useState } from 'react';

import {
  type CurrentPricingResponse,
  getAddonPrices,
  getBasePricing,
  getCurrentPricing,
  hasPricingData
} from '@/lib/pricingApi';

interface UsePricingResult {
  // Raw pricing data
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
  addonPrices: Record<string, number> | undefined;

  // Helper functions
  hasData: boolean;
  refetch: () => Promise<void>;
}

/**
 * Hook to fetch and manage current pricing data
 *
 * @example
 * ```tsx
 * function QuoteCalculator() {
 *   const { pricing, isLoading, adultPrice, childPrice, addonPrices } = usePricing();
 *
 *   if (isLoading) return <div>Loading pricing...</div>;
 *
 *   return (
 *     <div>
 *       <p>Adult: ${adultPrice}</p>
 *       <p>Child: ${childPrice}</p>
 *       <p>Salmon upgrade: ${addonPrices.salmon}</p>
 *     </div>
 *   );
 * }
 * ```
 */
export function usePricing(): UsePricingResult {
  const [pricing, setPricing] = useState<CurrentPricingResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPricing = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await getCurrentPricing();

      if (data) {
        setPricing(data);
        setError(null);
      } else {
        // Pricing fetch failed, set error but keep fallback values
        setError('Using default pricing (backend unavailable)');
        setPricing(null);
      }
    } catch (err) {
      console.error('Error fetching pricing:', err);
      setError('Using default pricing (backend unavailable)');
      setPricing(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPricing();
  }, []);

  // Extract convenience values - undefined when pricing not loaded
  // NO FALLBACK VALUES: Per instruction 01-CORE_PRINCIPLES Rule #14,
  // API is single source of truth. Frontend NEVER calculates or provides defaults.
  const basePricing = pricing ? getBasePricing(pricing) : undefined;
  const addonPrices = pricing ? getAddonPrices(pricing) : undefined;
  const hasData = hasPricingData(pricing);

  // Get party minimum from pricing response - NO FALLBACK (API is source of truth)
  const partyMinimum = (pricing as unknown as { policies?: { minimum_order?: number } })?.policies?.minimum_order;
  const depositAmount = (pricing as unknown as { policies?: { deposit_amount?: number } })?.policies?.deposit_amount;

  return {
    pricing,
    isLoading,
    error,
    adultPrice: basePricing?.adultPrice,
    childPrice: basePricing?.childPrice,
    childFreeUnderAge: basePricing?.childFreeUnderAge,
    partyMinimum,
    depositAmount,
    addonPrices,
    hasData,
    refetch: fetchPricing
  };
}
