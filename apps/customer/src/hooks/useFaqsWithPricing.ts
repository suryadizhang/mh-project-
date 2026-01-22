/**
 * useFaqsWithPricing Hook
 *
 * Provides FAQ data with dynamic pricing interpolated from the database.
 * Uses the pricing templates system to replace {{PLACEHOLDER}} values
 * with actual pricing from the /api/v1/pricing/current endpoint.
 */

import { useMemo } from 'react';

import { faqs as rawFaqs, type FaqItem } from '@/data/faqsData';
import { usePricing } from '@/hooks/usePricing';
import { DEFAULT_PRICING, interpolatePricing, type PricingValues } from '@/lib/pricingTemplates';

interface UseFaqsWithPricingResult {
  faqs: FaqItem[];
  isLoading: boolean;
  error: string | null;
  pricing: PricingValues;
}

/**
 * Hook to get FAQs with dynamic pricing values interpolated
 *
 * @example
 * ```tsx
 * function FAQPage() {
 *   const { faqs, isLoading } = useFaqsWithPricing()
 *
 *   if (isLoading) return <Loading />
 *
 *   return (
 *     <div>
 *       {faqs.map(faq => (
 *         <div key={faq.id}>
 *           <h3>{faq.question}</h3>
 *           <p>{faq.answer}</p> // Prices are already interpolated
 *         </div>
 *       ))}
 *     </div>
 *   )
 * }
 * ```
 */
export function useFaqsWithPricing(): UseFaqsWithPricingResult {
  const {
    adultPrice,
    childPrice,
    childFreeUnderAge,
    partyMinimum,
    freeMiles,
    perMileRate,
    depositAmount,
    depositRefundableDays,
    // Timing values from SSoT
    guestCountFinalizeHours,
    menuChangeCutoffHours,
    freeRescheduleHours,
    isLoading,
    error,
    pricing,
  } = usePricing();

  // Build pricing values object, using defaults for missing values
  // Note: FAQs require actual values for template interpolation, so we use defaults as fallback
  const pricingValues: PricingValues = useMemo(
    () => ({
      adultPrice: adultPrice ?? DEFAULT_PRICING.adultPrice,
      childPrice: childPrice ?? DEFAULT_PRICING.childPrice,
      childFreeUnderAge: childFreeUnderAge ?? DEFAULT_PRICING.childFreeUnderAge,
      partyMinimum: partyMinimum ?? DEFAULT_PRICING.partyMinimum,
      // Map usePricing property names to PricingValues interface names
      freeTravelMiles: freeMiles ?? DEFAULT_PRICING.freeTravelMiles,
      costPerMileAfter: perMileRate ?? DEFAULT_PRICING.costPerMileAfter,
      // Deposit & Policy values from SSoT (usePricing hook)
      depositAmount: depositAmount ?? DEFAULT_PRICING.depositAmount,
      depositRefundableDays: depositRefundableDays ?? DEFAULT_PRICING.depositRefundableDays,
      // Timing values from SSoT (usePricing hook)
      guestCountFinalizeHours: guestCountFinalizeHours ?? DEFAULT_PRICING.guestCountFinalizeHours,
      menuChangeCutoffHours: menuChangeCutoffHours ?? DEFAULT_PRICING.menuChangeCutoffHours,
      freeRescheduleHours: freeRescheduleHours ?? DEFAULT_PRICING.freeRescheduleHours,
    }),
    [
      adultPrice,
      childPrice,
      childFreeUnderAge,
      partyMinimum,
      freeMiles,
      perMileRate,
      depositAmount,
      depositRefundableDays,
      guestCountFinalizeHours,
      menuChangeCutoffHours,
      freeRescheduleHours,
      pricing,
    ],
  );

  // Interpolate pricing into all FAQ answers and tags
  const interpolatedFaqs = useMemo(() => {
    return rawFaqs.map((faq) => ({
      ...faq,
      answer: interpolatePricing(faq.answer, pricingValues),
      tags: faq.tags.map((tag) => interpolatePricing(tag, pricingValues)),
    }));
  }, [pricingValues]);

  return {
    faqs: interpolatedFaqs,
    isLoading,
    error,
    pricing: pricingValues,
  };
}

/**
 * Interpolate pricing into a single FAQ item
 * Useful when you have a single FAQ from another source
 */
export function interpolateFaqPricing(
  faq: FaqItem,
  pricingValues: PricingValues = DEFAULT_PRICING,
): FaqItem {
  return {
    ...faq,
    answer: interpolatePricing(faq.answer, pricingValues),
    tags: faq.tags.map((tag) => interpolatePricing(tag, pricingValues)),
  };
}
