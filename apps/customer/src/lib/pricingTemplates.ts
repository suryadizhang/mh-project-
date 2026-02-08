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
  // Deposit & Policy values (SSoT extension)
  depositAmount: number;
  depositRefundableDays: number;
  // Timing values (SSoT extension - hours before event)
  guestCountFinalizeHours?: number;
  menuChangeCutoffHours?: number;
  freeRescheduleHours?: number;
  // Menu upgrade prices (SSoT extension)
  salmonUpgrade?: number;
  scallopsUpgrade?: number;
  filetUpgrade?: number;
  lobsterUpgrade?: number;
  extraProtein?: number;
  // Menu addon prices (SSoT extension)
  yakisobaNoodles?: number;
  extraFriedRice?: number;
  extraVegetables?: number;
  edamame?: number;
  gyoza?: number;
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
  // Deposit & Policy defaults (must match database dynamic_variables)
  depositAmount: 100,
  depositRefundableDays: 4,
  // Timing defaults (must match database dynamic_variables)
  guestCountFinalizeHours: 24,
  menuChangeCutoffHours: 12,
  freeRescheduleHours: 24,
  // Menu upgrade defaults (must match database dynamic_variables)
  salmonUpgrade: 5,
  scallopsUpgrade: 5,
  filetUpgrade: 5,
  lobsterUpgrade: 15,
  extraProtein: 10,
  // Menu addon defaults (must match database dynamic_variables)
  yakisobaNoodles: 5,
  extraFriedRice: 5,
  extraVegetables: 5,
  edamame: 5,
  gyoza: 10,
};

/**
 * Template placeholders used in content strings
 * All business-critical values should use these placeholders
 * and be interpolated at runtime from the SSoT (database)
 */
export const PRICING_PLACEHOLDERS = {
  ADULT_PRICE: '{{ADULT_PRICE}}',
  CHILD_PRICE: '{{CHILD_PRICE}}',
  CHILD_FREE_AGE: '{{CHILD_FREE_AGE}}',
  PARTY_MINIMUM: '{{PARTY_MINIMUM}}',
  FREE_TRAVEL_MILES: '{{FREE_TRAVEL_MILES}}',
  COST_PER_MILE: '{{COST_PER_MILE}}',
  // Deposit & Policy placeholders (SSoT extension)
  DEPOSIT_AMOUNT: '{{DEPOSIT_AMOUNT}}',
  DEPOSIT_REFUNDABLE_DAYS: '{{DEPOSIT_REFUNDABLE_DAYS}}',
  // Timing placeholders (SSoT extension - hours before event)
  GUEST_COUNT_FINALIZE_HOURS: '{{GUEST_COUNT_FINALIZE_HOURS}}',
  MENU_CHANGE_CUTOFF_HOURS: '{{MENU_CHANGE_CUTOFF_HOURS}}',
  FREE_RESCHEDULE_HOURS: '{{FREE_RESCHEDULE_HOURS}}',
  // Menu upgrade placeholders (SSoT extension)
  SALMON_UPGRADE: '{{SALMON_UPGRADE}}',
  SCALLOPS_UPGRADE: '{{SCALLOPS_UPGRADE}}',
  FILET_UPGRADE: '{{FILET_UPGRADE}}',
  LOBSTER_UPGRADE: '{{LOBSTER_UPGRADE}}',
  EXTRA_PROTEIN: '{{EXTRA_PROTEIN}}',
  // Menu addon placeholders (SSoT extension)
  YAKISOBA_NOODLES: '{{YAKISOBA_NOODLES}}',
  EXTRA_FRIED_RICE: '{{EXTRA_FRIED_RICE}}',
  EXTRA_VEGETABLES: '{{EXTRA_VEGETABLES}}',
  EDAMAME: '{{EDAMAME}}',
  GYOZA: '{{GYOZA}}',
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
 *
 * const policyTemplate = "Refundable if canceled {{DEPOSIT_REFUNDABLE_DAYS}}+ days before"
 * const policyResult = interpolatePricing(policyTemplate, { depositRefundableDays: 4, ... })
 * // Returns: "Refundable if canceled 4+ days before"
 * ```
 */
export function interpolatePricing(
  template: string,
  pricing: PricingValues = DEFAULT_PRICING,
): string {
  return (
    template
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
      .replace(
        new RegExp(PRICING_PLACEHOLDERS.COST_PER_MILE, 'g'),
        String(pricing.costPerMileAfter),
      )
      // Deposit & Policy interpolations (SSoT extension)
      .replace(new RegExp(PRICING_PLACEHOLDERS.DEPOSIT_AMOUNT, 'g'), String(pricing.depositAmount))
      .replace(
        new RegExp(PRICING_PLACEHOLDERS.DEPOSIT_REFUNDABLE_DAYS, 'g'),
        String(pricing.depositRefundableDays),
      )
      // Timing interpolations (SSoT extension)
      .replace(
        new RegExp(PRICING_PLACEHOLDERS.GUEST_COUNT_FINALIZE_HOURS, 'g'),
        String(pricing.guestCountFinalizeHours ?? DEFAULT_PRICING.guestCountFinalizeHours),
      )
      .replace(
        new RegExp(PRICING_PLACEHOLDERS.MENU_CHANGE_CUTOFF_HOURS, 'g'),
        String(pricing.menuChangeCutoffHours ?? DEFAULT_PRICING.menuChangeCutoffHours),
      )
      .replace(
        new RegExp(PRICING_PLACEHOLDERS.FREE_RESCHEDULE_HOURS, 'g'),
        String(pricing.freeRescheduleHours ?? DEFAULT_PRICING.freeRescheduleHours),
      )
      // Menu upgrade interpolations (SSoT extension)
      .replace(
        new RegExp(PRICING_PLACEHOLDERS.SALMON_UPGRADE, 'g'),
        String(pricing.salmonUpgrade ?? DEFAULT_PRICING.salmonUpgrade),
      )
      .replace(
        new RegExp(PRICING_PLACEHOLDERS.SCALLOPS_UPGRADE, 'g'),
        String(pricing.scallopsUpgrade ?? DEFAULT_PRICING.scallopsUpgrade),
      )
      .replace(
        new RegExp(PRICING_PLACEHOLDERS.FILET_UPGRADE, 'g'),
        String(pricing.filetUpgrade ?? DEFAULT_PRICING.filetUpgrade),
      )
      .replace(
        new RegExp(PRICING_PLACEHOLDERS.LOBSTER_UPGRADE, 'g'),
        String(pricing.lobsterUpgrade ?? DEFAULT_PRICING.lobsterUpgrade),
      )
      .replace(
        new RegExp(PRICING_PLACEHOLDERS.EXTRA_PROTEIN, 'g'),
        String(pricing.extraProtein ?? DEFAULT_PRICING.extraProtein),
      )
      // Menu addon interpolations (SSoT extension)
      .replace(
        new RegExp(PRICING_PLACEHOLDERS.YAKISOBA_NOODLES, 'g'),
        String(pricing.yakisobaNoodles ?? DEFAULT_PRICING.yakisobaNoodles),
      )
      .replace(
        new RegExp(PRICING_PLACEHOLDERS.EXTRA_FRIED_RICE, 'g'),
        String(pricing.extraFriedRice ?? DEFAULT_PRICING.extraFriedRice),
      )
      .replace(
        new RegExp(PRICING_PLACEHOLDERS.EXTRA_VEGETABLES, 'g'),
        String(pricing.extraVegetables ?? DEFAULT_PRICING.extraVegetables),
      )
      .replace(
        new RegExp(PRICING_PLACEHOLDERS.EDAMAME, 'g'),
        String(pricing.edamame ?? DEFAULT_PRICING.edamame),
      )
      .replace(
        new RegExp(PRICING_PLACEHOLDERS.GYOZA, 'g'),
        String(pricing.gyoza ?? DEFAULT_PRICING.gyoza),
      )
  );
}

/**
 * Check if a string contains any pricing placeholders
 */
export function hasPricingPlaceholders(text: string): boolean {
  return Object.values(PRICING_PLACEHOLDERS).some((placeholder) => text.includes(placeholder));
}

/**
 * Convert pricing response from API to PricingValues format
 *
 * Handles responses from:
 * - /api/v1/config/all (full config)
 * - /api/v1/pricing/current (pricing only)
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
      deposit_amount?: number;
      deposit_refundable_days?: number;
    };
    deposit?: {
      amount?: number;
      refundable_days?: number;
    };
    timing?: {
      guest_count_finalize_hours?: number;
      menu_change_cutoff_hours?: number;
      free_reschedule_hours?: number;
    };
    menu?: {
      upgrades?: {
        salmon_cents?: number;
        scallops_cents?: number;
        filet_mignon_cents?: number;
        lobster_tail_cents?: number;
        extra_protein_cents?: number;
      };
      addons?: {
        yakisoba_noodles_cents?: number;
        extra_fried_rice_cents?: number;
        extra_vegetables_cents?: number;
        edamame_cents?: number;
        gyoza_cents?: number;
      };
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
    // Deposit values - check multiple possible locations in response
    depositAmount:
      response?.deposit?.amount ??
      response?.policies?.deposit_amount ??
      DEFAULT_PRICING.depositAmount,
    depositRefundableDays:
      response?.deposit?.refundable_days ??
      response?.policies?.deposit_refundable_days ??
      DEFAULT_PRICING.depositRefundableDays,
    // Timing values (SSoT extension)
    guestCountFinalizeHours:
      response?.timing?.guest_count_finalize_hours ?? DEFAULT_PRICING.guestCountFinalizeHours,
    menuChangeCutoffHours:
      response?.timing?.menu_change_cutoff_hours ?? DEFAULT_PRICING.menuChangeCutoffHours,
    freeRescheduleHours:
      response?.timing?.free_reschedule_hours ?? DEFAULT_PRICING.freeRescheduleHours,
    // Menu upgrade values (SSoT extension - convert cents to dollars)
    salmonUpgrade: response?.menu?.upgrades?.salmon_cents
      ? response.menu.upgrades.salmon_cents / 100
      : DEFAULT_PRICING.salmonUpgrade,
    scallopsUpgrade: response?.menu?.upgrades?.scallops_cents
      ? response.menu.upgrades.scallops_cents / 100
      : DEFAULT_PRICING.scallopsUpgrade,
    filetUpgrade: response?.menu?.upgrades?.filet_mignon_cents
      ? response.menu.upgrades.filet_mignon_cents / 100
      : DEFAULT_PRICING.filetUpgrade,
    lobsterUpgrade: response?.menu?.upgrades?.lobster_tail_cents
      ? response.menu.upgrades.lobster_tail_cents / 100
      : DEFAULT_PRICING.lobsterUpgrade,
    extraProtein: response?.menu?.upgrades?.extra_protein_cents
      ? response.menu.upgrades.extra_protein_cents / 100
      : DEFAULT_PRICING.extraProtein,
    // Menu addon values (SSoT extension - convert cents to dollars)
    yakisobaNoodles: response?.menu?.addons?.yakisoba_noodles_cents
      ? response.menu.addons.yakisoba_noodles_cents / 100
      : DEFAULT_PRICING.yakisobaNoodles,
    extraFriedRice: response?.menu?.addons?.extra_fried_rice_cents
      ? response.menu.addons.extra_fried_rice_cents / 100
      : DEFAULT_PRICING.extraFriedRice,
    extraVegetables: response?.menu?.addons?.extra_vegetables_cents
      ? response.menu.addons.extra_vegetables_cents / 100
      : DEFAULT_PRICING.extraVegetables,
    edamame: response?.menu?.addons?.edamame_cents
      ? response.menu.addons.edamame_cents / 100
      : DEFAULT_PRICING.edamame,
    gyoza: response?.menu?.addons?.gyoza_cents
      ? response.menu.addons.gyoza_cents / 100
      : DEFAULT_PRICING.gyoza,
  };
}
