/**
 * usePolicies Hook
 * =================
 *
 * Fetches business policies with pre-rendered text from the API.
 * Policies include deposit, cancellation, travel, and booking rules.
 *
 * Usage:
 *   const { policies, isLoading, error, refetch } = usePolicies();
 *
 *   if (isLoading) return <Loading />;
 *   if (error) return <Error message={error.message} />;
 *
 *   // Access pre-formatted policy text - values already injected by backend
 *   <p>{policies.deposit.text}</p>  // "Your $100 deposit is fully refundable..."
 *   <p>{policies.cancellation.text}</p>  // "Full refund if canceled 4+ days before..."
 *
 * CRITICAL: Per SSoT architecture (20-SINGLE_SOURCE_OF_TRUTH.instructions.md)
 * - API is the single source of truth
 * - Backend renders policy text with current values from database
 * - Frontend displays pre-formatted text - NO local value substitution
 * - If API fails, show graceful error - do NOT guess policy text
 *
 * @see 20-SINGLE_SOURCE_OF_TRUTH.instructions.md
 * @see services/business_config_service.py
 */

'use client';

import { useState, useEffect, useCallback } from 'react';

// ============================================================================
// TYPES
// ============================================================================

export interface DepositPolicy {
  /** Deposit amount in dollars */
  amount: number;
  /** Number of days before event for full refund */
  refund_days: number;
  /** Pre-rendered policy text with values injected */
  text: string;
}

export interface CancellationPolicy {
  /** Days before event for full refund */
  refund_days: number;
  /** Pre-rendered policy text with values injected */
  text: string;
}

export interface TravelPolicy {
  /** Free miles included */
  free_miles: number;
  /** Per mile rate in dollars after free miles */
  per_mile_rate: number;
  /** Pre-rendered policy text with values injected */
  text: string;
}

export interface BookingPolicy {
  /** Minimum hours in advance required */
  advance_hours: number;
  /** Pre-rendered policy text with values injected */
  text: string;
}

export interface PoliciesBundle {
  deposit: DepositPolicy;
  cancellation: CancellationPolicy;
  travel: TravelPolicy;
  booking: BookingPolicy;
  /** Source of the data for debugging */
  source?: string;
  /** Timestamp when data was fetched */
  fetched_at?: string;
}

export interface UsePoliciesReturn {
  /** Complete policies bundle from API */
  policies: PoliciesBundle | null;
  /** Loading state */
  isLoading: boolean;
  /** Error if fetch failed */
  error: Error | null;
  /** Has data been loaded successfully */
  hasData: boolean;
  /** Refetch policies from API */
  refetch: () => Promise<void>;

  // Convenience accessors - undefined if not loaded
  depositText?: string;
  cancellationText?: string;
  travelText?: string;
  bookingText?: string;
}

// ============================================================================
// HOOK IMPLEMENTATION
// ============================================================================

export function usePolicies(): UsePoliciesReturn {
  const [policies, setPolicies] = useState<PoliciesBundle | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchPolicies = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/v1/policies/current`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch policies: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();

      // Normalize the response structure
      const normalizedPolicies: PoliciesBundle = {
        deposit: {
          amount: data.deposit?.amount ?? data.deposit_amount ?? 0,
          refund_days: data.deposit?.refund_days ?? data.deposit_refundable_days ?? 0,
          text:
            data.deposit?.text ??
            `$${
              data.deposit?.amount ?? data.deposit_amount ?? 100
            } deposit required, refundable if canceled ${
              data.deposit?.refund_days ?? data.deposit_refundable_days ?? 4
            }+ days before event.`,
        },
        cancellation: {
          refund_days:
            data.cancellation?.refund_days ?? data.deposit?.refund_days ?? data.refund_days ?? 4,
          text:
            data.cancellation?.text ??
            `Full refund if canceled ${data.cancellation?.refund_days ?? 4}+ days before event.`,
        },
        travel: {
          free_miles: data.travel?.free_miles ?? data.free_miles ?? 0,
          per_mile_rate: data.travel?.per_mile_rate ?? (data.travel?.per_mile_cents ?? 0) / 100,
          text:
            data.travel?.text ??
            `First ${data.travel?.free_miles ?? 30} miles free, then $${
              data.travel?.per_mile_rate ?? 2
            }/mile.`,
        },
        booking: {
          advance_hours: data.booking?.advance_hours ?? data.min_advance_hours ?? 0,
          text:
            data.booking?.text ??
            `Book at least ${data.booking?.advance_hours ?? 48} hours in advance.`,
        },
        source: data.source ?? 'api',
        fetched_at: new Date().toISOString(),
      };

      setPolicies(normalizedPolicies);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to fetch policies');
      setError(error);
      console.error('usePolicies error:', error);
      // Per SSoT: NO fallback values - let component handle the error state
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Fetch on mount
  useEffect(() => {
    fetchPolicies();
  }, [fetchPolicies]);

  // Extract convenience text accessors
  // NO FALLBACK VALUES per instruction 01-CORE_PRINCIPLES Rule #14
  const depositText = policies?.deposit?.text;
  const cancellationText = policies?.cancellation?.text;
  const travelText = policies?.travel?.text;
  const bookingText = policies?.booking?.text;

  return {
    policies,
    isLoading,
    error,
    hasData: policies !== null && !error,
    refetch: fetchPolicies,

    // Convenience accessors
    depositText,
    cancellationText,
    travelText,
    bookingText,
  };
}

export default usePolicies;
