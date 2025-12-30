'use client';

import { useCallback, useState } from 'react';

import { apiFetch } from '@/lib/api';
import { logger } from '@/lib/logger';

export interface GeocodeResult {
  lat: number;
  lng: number;
  formattedAddress?: string;
}

export interface GeocodeError {
  code: 'API_ERROR' | 'NETWORK_ERROR' | 'INVALID_ADDRESS' | 'NOT_FOUND';
  message: string;
}

export interface UseGeocodeReturn {
  /** Geocode an address string */
  geocode: (address: string) => Promise<GeocodeResult | null>;
  /** Current geocoding result */
  result: GeocodeResult | null;
  /** Whether geocoding is in progress */
  isLoading: boolean;
  /** Error if geocoding failed */
  error: GeocodeError | null;
  /** Reset the geocode state */
  reset: () => void;
}

/**
 * Hook for geocoding addresses via the backend API
 *
 * Uses the backend scheduling geocode endpoint which caches results
 * and uses Google Geocoding API.
 *
 * @example
 * ```tsx
 * const { geocode, result, isLoading, error } = useGeocode();
 *
 * const handleAddressComplete = async () => {
 *   const fullAddress = `${street}, ${city}, ${state} ${zipCode}`;
 *   const coords = await geocode(fullAddress);
 *   if (coords) {
 *     setVenueCoordinates(coords);
 *   }
 * };
 * ```
 */
export function useGeocode(): UseGeocodeReturn {
  const [result, setResult] = useState<GeocodeResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<GeocodeError | null>(null);

  const geocode = useCallback(async (address: string): Promise<GeocodeResult | null> => {
    if (!address || address.trim().length < 5) {
      setError({
        code: 'INVALID_ADDRESS',
        message: 'Address is too short',
      });
      return null;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Call the backend scheduling geocode endpoint
      const response = await apiFetch<{
        lat?: number;
        lng?: number;
        formatted_address?: string;
        error?: string;
      }>('/api/v1/scheduling/geocode', {
        method: 'POST',
        body: JSON.stringify({ address: address.trim() }),
      });

      if (!response.success || !response.data) {
        throw new Error(response.error || 'Geocoding failed');
      }

      const data = response.data;

      if (data.error) {
        setError({
          code: 'NOT_FOUND',
          message: data.error,
        });
        setResult(null);
        return null;
      }

      if (typeof data.lat !== 'number' || typeof data.lng !== 'number') {
        setError({
          code: 'NOT_FOUND',
          message: 'Could not find coordinates for this address',
        });
        setResult(null);
        return null;
      }

      const geocodeResult: GeocodeResult = {
        lat: data.lat,
        lng: data.lng,
        formattedAddress: data.formatted_address,
      };

      setResult(geocodeResult);
      return geocodeResult;
    } catch (err) {
      logger.error('Geocoding error', err instanceof Error ? err : new Error(String(err)));

      const errorMessage = err instanceof Error ? err.message : 'Failed to geocode address';

      // Determine error type
      let code: GeocodeError['code'] = 'API_ERROR';
      if (errorMessage.includes('network') || errorMessage.includes('fetch')) {
        code = 'NETWORK_ERROR';
      } else if (errorMessage.includes('not found') || errorMessage.includes('no results')) {
        code = 'NOT_FOUND';
      }

      setError({
        code,
        message: errorMessage,
      });
      setResult(null);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
    setIsLoading(false);
  }, []);

  return {
    geocode,
    result,
    isLoading,
    error,
    reset,
  };
}
