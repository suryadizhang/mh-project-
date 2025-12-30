/**
 * Pricing API Client
 * Connects customer frontend to backend pricing endpoints
 *
 * Features:
 * - Fetch current menu items and addon pricing from database
 * - Calculate party quotes with travel fees
 * - Get pricing summary
 * - Automatic caching for menu data (5 minutes TTL)
 * - Type-safe responses
 */

import { api } from '@/lib/api';

/**
 * Menu Item from database
 */
export interface MenuItem {
  id: number;
  name: string;
  description: string;
  category: string;
  base_price: number;
  is_premium: boolean;
  is_available: boolean;
  dietary_info: string | null;
  image_url: string | null;
  display_order: number;
}

/**
 * Addon Item from database
 */
export interface AddonItem {
  id: number;
  name: string;
  description: string;
  category: string;
  price: number;
  is_active: boolean;
  image_url: string | null;
  display_order: number;
}

/**
 * Current pricing response from /api/v1/pricing/current
 */
export interface CurrentPricingResponse {
  base_pricing: {
    adult_price: number;
    child_price: number;
    child_free_under_age: number;
  };
  menu_items: {
    base_experiences: MenuItem[];
    free_proteins: MenuItem[];
    included_sides: MenuItem[];
  };
  addon_items: {
    protein_upgrades: AddonItem[];
    enhancements: AddonItem[];
    equipment: AddonItem[];
    entertainment: AddonItem[];
    beverages: AddonItem[];
  };
  travel_policy: {
    free_travel_radius_miles: number;
    cost_per_mile_after: number;
    base_location_zipcode: string;
  };
  gratuity_guidance: {
    suggested_percentage: number;
    note: string;
  };
}

/**
 * Quote calculation request payload
 */
export interface QuoteCalculationRequest {
  adults: number;
  children?: number;
  children_under_5?: number;
  upgrades?: {
    salmon?: number;
    scallops?: number;
    filet_mignon?: number;
    lobster_tail?: number;
    extra_protein?: number;
  };
  addons?: {
    yakisoba_noodles?: number;
    extra_fried_rice?: number;
    extra_vegetables?: number;
    edamame?: number;
    gyoza?: number;
  };
  customer_address?: string;
  customer_zipcode?: string;
}

/**
 * Quote calculation response from /api/v1/pricing/calculate
 */
export interface QuoteCalculationResponse {
  base_quote: {
    adult_count: number;
    adult_price: number;
    adult_total: number;
    child_count: number;
    child_price: number;
    child_total: number;
    child_free_count: number;
    base_subtotal: number;
  };
  upgrades: {
    items: Array<{
      name: string;
      quantity: number;
      unit_price: number;
      subtotal: number;
    }>;
    total: number;
  };
  addons: {
    items: Array<{
      name: string;
      quantity: number;
      unit_price: number;
      subtotal: number;
    }>;
    total: number;
  };
  travel_fee: {
    customer_address: string | null;
    customer_zipcode: string | null;
    distance_miles: number | null;
    travel_fee: number;
    is_free_delivery: boolean;
    calculation_note: string;
  };
  minimum_enforcement: {
    meets_minimum: boolean;
    minimum_required: number;
    current_total: number;
    shortfall: number | null;
    suggestion: string | null;
  };
  totals: {
    subtotal: number;
    travel_fee: number;
    grand_total: number;
  };
  breakdown_text: string;
}

/**
 * Pricing summary response from /api/v1/pricing/summary
 */
export interface PricingSummaryResponse {
  current_pricing: CurrentPricingResponse;
  sample_quotes: Array<{
    scenario: string;
    adults: number;
    children: number;
    estimated_total: number;
  }>;
  policies: {
    minimum_guests: number;
    minimum_order: number;
    travel_policy: string;
    gratuity_guidance: string;
  };
}

/**
 * Fetch current pricing from database
 * Cached for 5 minutes to reduce database load
 *
 * @returns Current menu items, addons, and pricing policies
 */
export async function getCurrentPricing(): Promise<CurrentPricingResponse | null> {
  const response = await api.get<CurrentPricingResponse>('/api/v1/pricing/current', {
    cacheStrategy: {
      strategy: 'stale-while-revalidate',
      ttl: 5 * 60 * 1000, // 5 minutes
      key: 'pricing:current',
    },
  });

  if (!response.success || !response.data) {
    console.error('Failed to fetch current pricing:', response.error);
    return null;
  }

  return response.data;
}

/**
 * Calculate party quote with travel fees
 * Not cached - each quote is unique
 *
 * @param request - Quote calculation parameters
 * @returns Detailed quote breakdown with travel fees
 */
export async function calculateQuote(
  request: QuoteCalculationRequest,
): Promise<QuoteCalculationResponse | null> {
  const response = await api.post<QuoteCalculationResponse>(
    '/api/v1/pricing/calculate',
    request as unknown as Record<string, unknown>,
  );

  if (!response.success || !response.data) {
    console.error('Failed to calculate quote:', response.error);
    return null;
  }

  return response.data;
}

/**
 * Get comprehensive pricing summary
 * Cached for 5 minutes
 *
 * @returns Pricing summary with sample quotes and policies
 */
export async function getPricingSummary(): Promise<PricingSummaryResponse | null> {
  const response = await api.get<PricingSummaryResponse>('/api/v1/pricing/summary', {
    cacheStrategy: {
      strategy: 'stale-while-revalidate',
      ttl: 5 * 60 * 1000, // 5 minutes
      key: 'pricing:summary',
    },
  });

  if (!response.success || !response.data) {
    console.error('Failed to fetch pricing summary:', response.error);
    return null;
  }

  return response.data;
}

/**
 * Extract base pricing from current pricing response
 * Useful for quick access to adult/child prices
 *
 * @param pricing - Current pricing response
 * @returns Base pricing object or undefined if no data (NO FALLBACKS - API is source of truth)
 */
export function getBasePricing(pricing: CurrentPricingResponse | null): {
  adultPrice: number;
  childPrice: number;
  childFreeUnderAge: number;
} | undefined {
  // NO FALLBACK VALUES: Per instruction 01-CORE_PRINCIPLES Rule #14,
  // API is single source of truth. Frontend NEVER provides default business values.
  if (!pricing?.base_pricing) {
    return undefined;
  }
  return {
    adultPrice: pricing.base_pricing.adult_price,
    childPrice: pricing.base_pricing.child_price,
    childFreeUnderAge: pricing.base_pricing.child_free_under_age,
  };
}

/**
 * Extract addon prices by name for easy lookup
 * Useful for quote calculators and booking forms
 *
 * @param pricing - Current pricing response
 * @returns Map of addon names to prices, or undefined if no data (NO FALLBACKS - API is source of truth)
 */
export function getAddonPrices(pricing: CurrentPricingResponse | null): Record<string, number> | undefined {
  // NO FALLBACK VALUES: Per instruction 01-CORE_PRINCIPLES Rule #14,
  // API is single source of truth. Frontend NEVER provides default business values.
  if (!pricing?.addon_items) {
    return undefined;
  }

  const prices: Record<string, number> = {};

  // Extract protein upgrades (with safe null check)
  if (pricing.addon_items?.protein_upgrades) {
    pricing.addon_items.protein_upgrades.forEach((addon) => {
      const key = addon.name.toLowerCase().replace(/\s+/g, '_');
      prices[key] = addon.price;
    });
  }

  // Extract enhancements (with safe null check)
  if (pricing.addon_items?.enhancements) {
    pricing.addon_items.enhancements.forEach((addon) => {
      const key = addon.name.toLowerCase().replace(/\s+/g, '_');
      prices[key] = addon.price;
    });
  }

  return prices;
}

/**
 * Check if pricing data is available
 * Useful for loading states and error handling
 *
 * @param pricing - Current pricing response
 * @returns True if pricing data is valid
 */
export function hasPricingData(pricing: CurrentPricingResponse | null): boolean {
  return !!(pricing && pricing.base_pricing && pricing.menu_items && pricing.addon_items);
}
