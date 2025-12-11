/**
 * Pricing Templates
 * Utility functions to inject dynamic pricing into static content
 *
 * This ensures FAQ, policies, and other content always reflects
 * the current pricing from the database (single source of truth)
 */

export interface PricingValues {
  adultPrice: number;
  childPrice: number;
  childFreeUnderAge: number;
  partyMinimum: number;
  freeTravelMiles: number;
  costPerMileAfter: number;
}

/**
 * Default pricing values (fallback when API unavailable)
 * These should match the database defaults
 */
export const DEFAULT_PRICING: PricingValues = {
  adultPrice: 55,
  childPrice: 30,
  childFreeUnderAge: 5,
  partyMinimum: 550,
  freeTravelMiles: 30,
  costPerMileAfter: 2,
};

/**
 * Template placeholders used in content strings
 */
export const PRICING_PLACEHOLDERS = {
  ADULT_PRICE: '{{ADULT_PRICE}}',
  CHILD_PRICE: '{{CHILD_PRICE}}',
  CHILD_FREE_AGE: '{{CHILD_FREE_AGE}}',
  PARTY_MINIMUM: '{{PARTY_MINIMUM}}',
  FREE_TRAVEL_MILES: '{{FREE_TRAVEL_MILES}}',
  COST_PER_MILE: '{{COST_PER_MILE}}',
} as const;

/**
 * Replace pricing placeholders in a string with actual values
 *
 * @param template - String containing pricing placeholders
 * @param pricing - Pricing values to inject
 * @returns String with placeholders replaced by actual values
 *
 * @example
 * ```ts
 * const template = "Adults cost ${{ADULT_PRICE}} each"
 * const result = interpolatePricing(template, { adultPrice: 55, ... })
 * // Returns: "Adults cost $55 each"
 * ```
 */
export function interpolatePricing(
  template: string,
  pricing: PricingValues = DEFAULT_PRICING,
): string {
  return template
    .replace(new RegExp(PRICING_PLACEHOLDERS.ADULT_PRICE, 'g'), String(pricing.adultPrice))
    .replace(new RegExp(PRICING_PLACEHOLDERS.CHILD_PRICE, 'g'), String(pricing.childPrice))
    .replace(
      new RegExp(PRICING_PLACEHOLDERS.CHILD_FREE_AGE, 'g'),
      String(pricing.childFreeUnderAge),
    )
    .replace(new RegExp(PRICING_PLACEHOLDERS.PARTY_MINIMUM, 'g'), String(pricing.partyMinimum))
    .replace(
      new RegExp(PRICING_PLACEHOLDERS.FREE_TRAVEL_MILES, 'g'),
      String(pricing.freeTravelMiles),
    )
    .replace(new RegExp(PRICING_PLACEHOLDERS.COST_PER_MILE, 'g'), String(pricing.costPerMileAfter));
}

/**
 * Check if a string contains any pricing placeholders
 */
export function hasPricingPlaceholders(text: string): boolean {
  return Object.values(PRICING_PLACEHOLDERS).some((placeholder) => text.includes(placeholder));
}

/**
 * Convert pricing response from API to PricingValues format
 */
export function apiResponseToPricingValues(
  response: {
    base_pricing?: {
      adult_price?: number;
      child_price?: number;
      child_free_under_age?: number;
    };
    travel_policy?: {
      free_travel_radius_miles?: number;
      cost_per_mile_after?: number;
    };
    policies?: {
      minimum_order?: number;
    };
  } | null,
): PricingValues {
  return {
    adultPrice: response?.base_pricing?.adult_price ?? DEFAULT_PRICING.adultPrice,
    childPrice: response?.base_pricing?.child_price ?? DEFAULT_PRICING.childPrice,
    childFreeUnderAge:
      response?.base_pricing?.child_free_under_age ?? DEFAULT_PRICING.childFreeUnderAge,
    partyMinimum: response?.policies?.minimum_order ?? DEFAULT_PRICING.partyMinimum,
    freeTravelMiles:
      response?.travel_policy?.free_travel_radius_miles ?? DEFAULT_PRICING.freeTravelMiles,
    costPerMileAfter:
      response?.travel_policy?.cost_per_mile_after ?? DEFAULT_PRICING.costPerMileAfter,
  };
}
