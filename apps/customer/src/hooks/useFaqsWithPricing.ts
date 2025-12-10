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
  const { adultPrice, childPrice, childFreeUnderAge, isLoading, error, pricing } = usePricing();

  // Build pricing values object, using defaults for missing values
  const pricingValues: PricingValues = useMemo(
    () => ({
      adultPrice,
      childPrice,
      childFreeUnderAge,
      // These values come from travel_policy in pricing response
      partyMinimum: pricing?.travel_policy
        ? 550 // Default party minimum - not in current API response
        : DEFAULT_PRICING.partyMinimum,
      freeTravelMiles:
        pricing?.travel_policy?.free_travel_radius_miles ?? DEFAULT_PRICING.freeTravelMiles,
      costPerMileAfter:
        pricing?.travel_policy?.cost_per_mile_after ?? DEFAULT_PRICING.costPerMileAfter,
    }),
    [adultPrice, childPrice, childFreeUnderAge, pricing],
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
