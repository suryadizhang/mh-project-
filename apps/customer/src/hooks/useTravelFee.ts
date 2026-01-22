/**
 * Travel Fee Calculator Hook
 *
 * Calculates travel fees based on distance from station using SSoT pricing.
 * Fetches travel configuration from API and provides fee calculation utilities.
 *
 * @example
 * ```tsx
 * const { calculateFee, freeMiles, perMileRate, isLoading } = useTravelFee();
 *
 * // Calculate fee for 45 miles
 * const fee = calculateFee(45); // Returns 30 (45-30) * $2 = $30
 * ```
 */

import { useCallback, useMemo } from 'react';

import { usePricing } from './usePricing';

export interface TravelFeeResult {
  /** Fee amount in dollars (0 if within free radius) */
  fee: number;
  /** Fee amount in cents */
  feeCents: number;
  /** Miles that are free */
  freeMiles: number;
  /** Billable miles (distance - freeMiles, min 0) */
  billableMiles: number;
  /** Whether the destination is within free radius */
  isFree: boolean;
  /** Formatted fee string (e.g., "$30.00") */
  formattedFee: string;
  /** Human-readable breakdown */
  breakdown: string;
}

export interface UseTravelFeeReturn {
  /** Free travel radius in miles */
  freeMiles: number;
  /** Cost per mile after free radius (in dollars) */
  perMileRate: number;
  /** Cost per mile in cents */
  perMileCents: number;
  /** Loading state */
  isLoading: boolean;
  /** Error state */
  error: Error | null;

  /**
   * Calculate travel fee for a given distance
   * @param distanceMiles - Distance from station to venue in miles
   * @returns Detailed travel fee result
   */
  calculateFee: (distanceMiles: number) => TravelFeeResult;

  /**
   * Get just the fee amount in dollars
   * @param distanceMiles - Distance from station to venue in miles
   * @returns Fee in dollars (0 if within free radius)
   */
  getFeeAmount: (distanceMiles: number) => number;

  /**
   * Check if a distance is within the free radius
   * @param distanceMiles - Distance to check
   * @returns True if within free radius
   */
  isWithinFreeRadius: (distanceMiles: number) => boolean;

  /**
   * Format a fee amount for display
   * @param amount - Fee amount in dollars
   * @returns Formatted string (e.g., "$30.00")
   */
  formatFee: (amount: number) => string;

  /**
   * Get travel fee policy text
   * @returns Human-readable policy string
   */
  getPolicyText: () => string;
}

/**
 * Hook for calculating travel fees based on SSoT configuration
 */
export function useTravelFee(): UseTravelFeeReturn {
  const { freeMiles, perMileRate, isLoading, error } = usePricing();

  // Use defaults when values are undefined
  const freeTravelMiles = freeMiles ?? 30;
  const costPerMileAfter = perMileRate ?? 2;

  // Memoize the per mile rate in cents
  const perMileCents = useMemo(() => {
    return Math.round(costPerMileAfter * 100);
  }, [costPerMileAfter]);

  // Format currency helper
  const formatFee = useCallback((amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    }).format(amount);
  }, []);

  // Check if within free radius
  const isWithinFreeRadius = useCallback(
    (distanceMiles: number): boolean => {
      return distanceMiles <= freeTravelMiles;
    },
    [freeTravelMiles],
  );

  // Calculate detailed travel fee
  const calculateFee = useCallback(
    (distanceMiles: number): TravelFeeResult => {
      // Validate input
      const distance = Math.max(0, distanceMiles);

      // Calculate billable miles (beyond free radius)
      const billableMiles = Math.max(0, distance - freeTravelMiles);

      // Calculate fee
      const feeCents = billableMiles * perMileCents;
      const fee = feeCents / 100;

      // Determine if free
      const isFree = billableMiles === 0;

      // Format fee
      const formattedFee = formatFee(fee);

      // Create breakdown text
      let breakdown: string;
      if (isFree) {
        breakdown = `Within ${freeTravelMiles} mile free radius - No travel fee`;
      } else {
        breakdown = `${distance} miles - ${freeTravelMiles} free miles = ${billableMiles} billable miles × ${formatFee(
          costPerMileAfter,
        )}/mile = ${formattedFee}`;
      }

      return {
        fee,
        feeCents,
        freeMiles: freeTravelMiles,
        billableMiles,
        isFree,
        formattedFee,
        breakdown,
      };
    },
    [freeTravelMiles, perMileCents, costPerMileAfter, formatFee],
  );

  // Simple fee amount getter
  const getFeeAmount = useCallback(
    (distanceMiles: number): number => {
      return calculateFee(distanceMiles).fee;
    },
    [calculateFee],
  );

  // Get policy text
  const getPolicyText = useCallback((): string => {
    return `First ${freeTravelMiles} miles are free. After that, ${formatFee(
      costPerMileAfter,
    )} per mile.`;
  }, [freeTravelMiles, costPerMileAfter, formatFee]);

  return {
    freeMiles: freeTravelMiles,
    perMileRate: costPerMileAfter,
    perMileCents,
    isLoading,
    error: error ? new Error(error) : null,
    calculateFee,
    getFeeAmount,
    isWithinFreeRadius,
    formatFee,
    getPolicyText,
  };
}

/**
 * Calculate travel fee without React hook (for server-side or utilities)
 *
 * @param distanceMiles - Distance from station to venue
 * @param freeMiles - Free travel radius (default: 30)
 * @param perMileRate - Rate per mile after free radius in dollars (default: 2)
 * @returns Fee in dollars
 */
export function calculateTravelFeeStatic(
  distanceMiles: number,
  freeMiles: number = 30,
  perMileRate: number = 2,
): number {
  const billableMiles = Math.max(0, distanceMiles - freeMiles);
  return billableMiles * perMileRate;
}

/**
 * Calculate travel fee in cents (for precision)
 *
 * @param distanceMiles - Distance from station to venue
 * @param freeMiles - Free travel radius (default: 30)
 * @param perMileCents - Rate per mile in cents (default: 200)
 * @returns Fee in cents
 */
export function calculateTravelFeeCents(
  distanceMiles: number,
  freeMiles: number = 30,
  perMileCents: number = 200,
): number {
  const billableMiles = Math.max(0, distanceMiles - freeMiles);
  return billableMiles * perMileCents;
}
