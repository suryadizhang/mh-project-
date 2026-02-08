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

    // Fetch from config/all to get all pricing including menu upgrades/addons
    const response = await fetch(`${apiUrl}/api/v1/config/all`, {
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
      adultPrice: data.pricing?.adult_price_cents
        ? data.pricing.adult_price_cents / 100
        : DEFAULT_PRICING.adultPrice,
      childPrice: data.pricing?.child_price_cents
        ? data.pricing.child_price_cents / 100
        : DEFAULT_PRICING.childPrice,
      childFreeUnderAge:
        data.pricing?.child_free_under_age ?? DEFAULT_PRICING.childFreeUnderAge,
      partyMinimum: data.pricing?.party_minimum_cents
        ? data.pricing.party_minimum_cents / 100
        : DEFAULT_PRICING.partyMinimum,
      freeTravelMiles:
        data.travel?.free_miles ?? DEFAULT_PRICING.freeTravelMiles,
      costPerMileAfter: data.travel?.per_mile_cents
        ? data.travel.per_mile_cents / 100
        : DEFAULT_PRICING.costPerMileAfter,
      // Deposit & Policy values
      depositAmount: data.deposit?.amount_cents
        ? data.deposit.amount_cents / 100
        : DEFAULT_PRICING.depositAmount,
      depositRefundableDays: data.deposit?.refundable_days ?? DEFAULT_PRICING.depositRefundableDays,
      // Menu upgrade values (SSoT extension)
      salmonUpgrade: data.menu?.upgrades?.salmon_cents
        ? data.menu.upgrades.salmon_cents / 100
        : DEFAULT_PRICING.salmonUpgrade,
      scallopsUpgrade: data.menu?.upgrades?.scallops_cents
        ? data.menu.upgrades.scallops_cents / 100
        : DEFAULT_PRICING.scallopsUpgrade,
      filetUpgrade: data.menu?.upgrades?.filet_mignon_cents
        ? data.menu.upgrades.filet_mignon_cents / 100
        : DEFAULT_PRICING.filetUpgrade,
      lobsterUpgrade: data.menu?.upgrades?.lobster_tail_cents
        ? data.menu.upgrades.lobster_tail_cents / 100
        : DEFAULT_PRICING.lobsterUpgrade,
      extraProtein: data.menu?.upgrades?.extra_protein_cents
        ? data.menu.upgrades.extra_protein_cents / 100
        : DEFAULT_PRICING.extraProtein,
      // Menu addon values (SSoT extension)
      yakisobaNoodles: data.menu?.addons?.yakisoba_noodles_cents
        ? data.menu.addons.yakisoba_noodles_cents / 100
        : DEFAULT_PRICING.yakisobaNoodles,
      extraFriedRice: data.menu?.addons?.extra_fried_rice_cents
        ? data.menu.addons.extra_fried_rice_cents / 100
        : DEFAULT_PRICING.extraFriedRice,
      extraVegetables: data.menu?.addons?.extra_vegetables_cents
        ? data.menu.addons.extra_vegetables_cents / 100
        : DEFAULT_PRICING.extraVegetables,
      edamame: data.menu?.addons?.edamame_cents
        ? data.menu.addons.edamame_cents / 100
        : DEFAULT_PRICING.edamame,
      gyoza: data.menu?.addons?.gyoza_cents
        ? data.menu.addons.gyoza_cents / 100
        : DEFAULT_PRICING.gyoza,
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
