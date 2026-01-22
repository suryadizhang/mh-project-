/**
 * Server-side FAQ Data Provider
 *
 * Fetches pricing from the API and interpolates it into FAQ data
 * for use in Server Components or getStaticProps/getServerSideProps
 */

import { faqs as rawFaqs, type FaqItem } from '@/data/faqsData';

import { DEFAULT_PRICING, interpolatePricing, type PricingValues } from './pricingTemplates';

/**
 * Fetch current pricing from API (server-side)
 * In development without backend, returns defaults immediately
 */
async function fetchPricingServer(): Promise<PricingValues> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;

  // Skip API call entirely in development when pointing to localhost
  // (backend likely not running during frontend development)
  if (!apiUrl || (process.env.NODE_ENV === 'development' && apiUrl.includes('localhost'))) {
    return DEFAULT_PRICING;
  }

  try {
    // Use AbortController for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000); // 2 second timeout

    const response = await fetch(`${apiUrl}/api/v1/pricing/current`, {
      next: { revalidate: 300 }, // Cache for 5 minutes
      signal: controller.signal,
      cache: 'force-cache', // Prefer cached response
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      return DEFAULT_PRICING;
    }

    const data = await response.json();

    return {
      adultPrice: data.base_pricing?.adult_price ?? DEFAULT_PRICING.adultPrice,
      childPrice: data.base_pricing?.child_price ?? DEFAULT_PRICING.childPrice,
      childFreeUnderAge:
        data.base_pricing?.child_free_under_age ?? DEFAULT_PRICING.childFreeUnderAge,
      partyMinimum: DEFAULT_PRICING.partyMinimum, // Not in current API
      freeTravelMiles:
        data.travel_policy?.free_travel_radius_miles ?? DEFAULT_PRICING.freeTravelMiles,
      costPerMileAfter: data.travel_policy?.cost_per_mile_after ?? DEFAULT_PRICING.costPerMileAfter,
      // Deposit & Policy values - using defaults until API extended
      // TODO: Update when /api/v1/pricing/current includes deposit_amount and deposit_refundable_days
      depositAmount: DEFAULT_PRICING.depositAmount,
      depositRefundableDays: DEFAULT_PRICING.depositRefundableDays,
    };
  } catch {
    // Silently fall back to defaults - this is expected when backend is not running
    return DEFAULT_PRICING;
  }
}

/**
 * Get FAQs with pricing interpolated (server-side)
 *
 * @example Server Component
 * ```tsx
 * // app/faqs/page.tsx
 * import { getFaqsWithPricing } from '@/lib/faqDataProvider'
 *
 * export default async function FAQsPage() {
 *   const { faqs, pricing } = await getFaqsWithPricing()
 *
 *   return <FAQList faqs={faqs} />
 * }
 * ```
 */
export async function getFaqsWithPricing(): Promise<{ faqs: FaqItem[]; pricing: PricingValues }> {
  const pricing = await fetchPricingServer();

  const faqs = rawFaqs.map((faq) => ({
    ...faq,
    answer: interpolatePricing(faq.answer, pricing),
    tags: faq.tags.map((tag) => interpolatePricing(tag, pricing)),
  }));

  return { faqs, pricing };
}

/**
 * Get a single FAQ by ID with pricing interpolated
 */
export async function getFaqById(id: string): Promise<FaqItem | null> {
  const pricing = await fetchPricingServer();
  const faq = rawFaqs.find((f) => f.id === id);

  if (!faq) return null;

  return {
    ...faq,
    answer: interpolatePricing(faq.answer, pricing),
    tags: faq.tags.map((tag) => interpolatePricing(tag, pricing)),
  };
}

/**
 * Get FAQs filtered by category with pricing interpolated
 */
export async function getFaqsByCategory(category: string): Promise<FaqItem[]> {
  const pricing = await fetchPricingServer();

  return rawFaqs
    .filter((faq) => faq.category === category)
    .map((faq) => ({
      ...faq,
      answer: interpolatePricing(faq.answer, pricing),
      tags: faq.tags.map((tag) => interpolatePricing(tag, pricing)),
    }));
}

/**
 * Get pricing values for use in other components
 */
export async function getCurrentPricingValues(): Promise<PricingValues> {
  return fetchPricingServer();
}
