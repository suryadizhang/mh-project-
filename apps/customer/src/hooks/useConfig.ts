/**
 * useConfig Hook
 * ===============
 *
 * Fetches complete business configuration from the API.
 * This is the primary hook for accessing all SSoT configuration values.
 *
 * Usage:
 *   const { config, isLoading, error, refetch } = useConfig();
 *
 *   if (isLoading) return <Loading />;
 *   if (error) return <Error message={error.message} />;
 *
 *   // Access config values - NO FALLBACKS per instruction 01-CORE_PRINCIPLES Rule #14
 *   const adultPrice = config?.pricing?.adult_price_cents ? config.pricing.adult_price_cents / 100 : undefined;
 *
 * CRITICAL: Per SSoT architecture (20-SINGLE_SOURCE_OF_TRUTH.instructions.md)
 * - API is the single source of truth
 * - Frontend NEVER provides fallback values for business data
 * - If API fails, show graceful error - do NOT guess values
 *
 * @see 20-SINGLE_SOURCE_OF_TRUTH.instructions.md
 * @see services/business_config_service.py
 */

'use client';

import { useState, useEffect, useCallback } from 'react';

// ============================================================================
// TYPES
// ============================================================================

export interface PricingConfig {
  adult_price_cents: number;
  child_price_cents: number;
  child_free_under_age: number;
  party_minimum_cents: number;
}

export interface TravelConfig {
  free_miles: number;
  per_mile_cents: number;
}

export interface DepositConfig {
  deposit_amount_cents: number;
  deposit_refundable_days: number;
}

export interface BookingConfig {
  min_advance_hours: number;
}

export interface GuestLimitsConfig {
  minimum: number;
  maximum: number;
  minimum_for_hibachi: number;
}

export interface BusinessConfig {
  pricing: PricingConfig;
  travel: TravelConfig;
  deposit: DepositConfig;
  booking: BookingConfig;
  guest_limits?: GuestLimitsConfig;
  source: string;
}

export interface UseConfigReturn {
  /** Complete business configuration from API */
  config: BusinessConfig | null;
  /** Loading state */
  isLoading: boolean;
  /** Error if fetch failed */
  error: Error | null;
  /** Has data been loaded successfully */
  hasData: boolean;
  /** Refetch configuration from API */
  refetch: () => Promise<void>;

  // Convenience values (dollars, not cents) - undefined if not loaded
  adultPrice?: number;
  childPrice?: number;
  childFreeUnderAge?: number;
  partyMinimum?: number;
  depositAmount?: number;
  freeMiles?: number;
  perMileRate?: number;
  minAdvanceHours?: number;
}

// ============================================================================
// HOOK IMPLEMENTATION
// ============================================================================

export function useConfig(): UseConfigReturn {
  const [config, setConfig] = useState<BusinessConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchConfig = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/v1/config/all`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch config: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();

      // API may return in different structures, normalize
      const normalizedConfig: BusinessConfig = {
        pricing: data.pricing || {
          adult_price_cents: data.adult_price_cents,
          child_price_cents: data.child_price_cents,
          child_free_under_age: data.child_free_under_age,
          party_minimum_cents: data.party_minimum_cents,
        },
        travel: data.travel || {
          free_miles: data.travel_free_miles,
          per_mile_cents: data.travel_per_mile_cents,
        },
        deposit: data.deposit || {
          deposit_amount_cents: data.deposit_amount_cents,
          deposit_refundable_days: data.deposit_refundable_days,
        },
        booking: data.booking || {
          min_advance_hours: data.min_advance_hours,
        },
        guest_limits: data.guest_limits,
        source: data.source || 'api',
      };

      setConfig(normalizedConfig);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to fetch configuration');
      setError(error);
      console.error('useConfig error:', error);
      // Per SSoT: NO fallback values - let component handle the error state
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Fetch on mount
  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  // Extract convenience values - convert cents to dollars
  // NO FALLBACK VALUES per instruction 01-CORE_PRINCIPLES Rule #14
  const adultPrice = config?.pricing?.adult_price_cents
    ? config.pricing.adult_price_cents / 100
    : undefined;
  const childPrice = config?.pricing?.child_price_cents
    ? config.pricing.child_price_cents / 100
    : undefined;
  const childFreeUnderAge = config?.pricing?.child_free_under_age;
  const partyMinimum = config?.pricing?.party_minimum_cents
    ? config.pricing.party_minimum_cents / 100
    : undefined;
  const depositAmount = config?.deposit?.deposit_amount_cents
    ? config.deposit.deposit_amount_cents / 100
    : undefined;
  const freeMiles = config?.travel?.free_miles;
  const perMileRate = config?.travel?.per_mile_cents
    ? config.travel.per_mile_cents / 100
    : undefined;
  const minAdvanceHours = config?.booking?.min_advance_hours;

  return {
    config,
    isLoading,
    error,
    hasData: config !== null && !error,
    refetch: fetchConfig,

    // Convenience values
    adultPrice,
    childPrice,
    childFreeUnderAge,
    partyMinimum,
    depositAmount,
    freeMiles,
    perMileRate,
    minAdvanceHours,
  };
}

export default useConfig;
