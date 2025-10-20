'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

import { CacheService } from '@/lib/cache/CacheService';

interface UseCachedFetchOptions<T> {
  cache?: CacheService<T>;
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
  options: UseCachedFetchOptions<T> = {}
): UseCachedFetchResult<T> {
  const {
    cache,
    ttl,
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

  /**
   * Fetch data with caching logic
   */
  const fetchData = useCallback(
    async (bypassCache = false) => {
      if (!key || !enabled) return;

      try {
        // Check cache first (unless bypassing)
        if (!bypassCache && cache) {
          const cachedData = cache.get(key);
          if (cachedData) {
            setData(cachedData);
            setError(null);
            setIsStale(false);

            // If stale-while-revalidate, fetch in background
            if (staleWhileRevalidate) {
              setIsStale(true);
              fetchData(true); // Revalidate in background
            }
            return;
          }
        }

        // Set loading state (only if not doing background revalidation)
        if (!staleWhileRevalidate || !data) {
          setIsLoading(true);
        }

        // Fetch fresh data
        const freshData = await fetcher();

        // Only update state if component is still mounted
        if (!isMountedRef.current) return;

        // Cache the data
        if (cache) {
          cache.set(key, freshData, ttl);
        }

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
    [key, enabled, cache, ttl, fetcher, onSuccess, onError, staleWhileRevalidate, data]
  );

  /**
   * Invalidate cache and refetch
   */
  const invalidate = useCallback(() => {
    if (key && cache) {
      cache.delete(key);
    }
    setIsStale(true);
  }, [key, cache]);

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
