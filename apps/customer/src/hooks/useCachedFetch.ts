'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

import { getCacheService } from '@/lib/cacheService';
import { requestDeduplicator } from '@/lib/cache/RequestDeduplicator';

interface UseCachedFetchOptions<T> {
  ttl?: number;
  enabled?: boolean;
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
  refetchInterval?: number;
  staleWhileRevalidate?: boolean;
}

interface UseCachedFetchResult<T> {
  data: T | null;
  isLoading: boolean;
  error: Error | null;
  isStale: boolean;
  refetch: () => Promise<void>;
  invalidate: () => void;
}

/**
 * Custom hook for fetching data with caching support
 *
 * @param key - Unique cache key
 * @param fetcher - Function that fetches the data
 * @param options - Configuration options
 */
export function useCachedFetch<T>(
  key: string | null,
  fetcher: () => Promise<T>,
  options: UseCachedFetchOptions<T> = {},
): UseCachedFetchResult<T> {
  const {
    ttl = 5 * 60 * 1000, // Default 5 minutes
    enabled = true,
    onSuccess,
    onError,
    refetchInterval,
    staleWhileRevalidate = false,
  } = options;

  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);
  const [isStale, setIsStale] = useState<boolean>(false);

  const isMountedRef = useRef(true);
  const refetchIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const dataRef = useRef<T | null>(null);

  // Keep dataRef in sync with data state
  useEffect(() => {
    dataRef.current = data;
  }, [data]);

  /**
   * Fetch data with caching logic
   */
  const fetchData = useCallback(
    async (bypassCache = false) => {
      if (!key || !enabled) return;

      // Get cache service instance (singleton, stable reference)
      const cache = getCacheService();

      try {
        // Check cache first (unless bypassing)
        if (!bypassCache) {
          const cachedEntry = cache.get<T>(key);
          if (cachedEntry) {
            setData(cachedEntry.data);
            setError(null);
            setIsStale(false);

            // If stale-while-revalidate, fetch in background
            if (staleWhileRevalidate) {
              setIsStale(true);
              // Use setTimeout to avoid recursive call during render
              setTimeout(() => fetchData(true), 0);
            }
            return;
          }
        }

        // Set loading state (only if not doing background revalidation)
        // Check if we already have data to avoid showing loading on revalidation
        if (!bypassCache && !dataRef.current) {
          setIsLoading(true);
        }

        // Fetch fresh data with deduplication to prevent duplicate simultaneous requests
        const freshData = await requestDeduplicator.dedupe(key, fetcher);

        // Only update state if component is still mounted
        if (!isMountedRef.current) return;

        // Cache the data
        cache.set(key, freshData, ttl);

        setData(freshData);
        setError(null);
        setIsStale(false);
        setIsLoading(false);

        onSuccess?.(freshData);
      } catch (err) {
        if (!isMountedRef.current) return;

        const error = err instanceof Error ? err : new Error('Unknown error');
        setError(error);
        setIsLoading(false);
        setIsStale(false);

        onError?.(error);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    // CRITICAL: Intentionally excluding 'data' from deps to prevent infinite loop
    // We use dataRef.current to check for existing data instead
    // cache is from singleton getInstance, so it's stable and doesn't need to be in deps
    [key, enabled, ttl, fetcher, onSuccess, onError, staleWhileRevalidate],
  );

  /**
   * Invalidate cache and refetch
   */
  const invalidate = useCallback(() => {
    const cache = getCacheService();
    if (key) {
      cache.remove(key);
    }
    setIsStale(true);
  }, [key]);

  /**
   * Manual refetch
   */
  const refetch = useCallback(async () => {
    await fetchData(true);
  }, [fetchData]);

  /**
   * Initial fetch on mount or when key/enabled changes
   */
  useEffect(() => {
    isMountedRef.current = true;
    fetchData();

    return () => {
      isMountedRef.current = false;
    };
  }, [fetchData]);

  /**
   * Set up refetch interval if specified
   */
  useEffect(() => {
    if (refetchInterval && enabled) {
      refetchIntervalRef.current = setInterval(() => {
        fetchData(true);
      }, refetchInterval);

      return () => {
        if (refetchIntervalRef.current) {
          clearInterval(refetchIntervalRef.current);
        }
      };
    }
  }, [refetchInterval, enabled, fetchData]);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      if (refetchIntervalRef.current) {
        clearInterval(refetchIntervalRef.current);
      }
    };
  }, []);

  return {
    data,
    isLoading,
    error,
    isStale,
    refetch,
    invalidate,
  };
}
