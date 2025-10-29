'use client';

import { useMemo } from 'react';
import type { BlogPost } from '@my-hibachi/blog-types';

import { useCachedFetch } from './useCachedFetch';

type BlogAPIType =
  | 'featured'
  | 'seasonal'
  | 'recent'
  | 'all'
  | 'search'
  | 'categories'
  | 'tags'
  | 'serviceAreas'
  | 'eventTypes';

interface UseBlogAPIOptions {
  type: BlogAPIType;
  query?: string;
  limit?: number;
  enabled?: boolean;
  ttl?: number;
}

interface BlogAPIResponse {
  posts?: BlogPost[];
  categories?: string[];
  tags?: string[];
  serviceAreas?: string[];
  eventTypes?: string[];
}

/**
 * Specialized hook for blog API calls with caching
 */
export function useBlogAPI(options: UseBlogAPIOptions) {
  const { type, query, limit, enabled = true, ttl = 5 * 60 * 1000 } = options;

  // Generate cache key
  const cacheKey = useMemo(() => {
    if (!enabled) return null;

    const params = new URLSearchParams({ type });
    if (query) params.append('query', query);
    if (limit) params.append('limit', String(limit));

    return `/api/blog?${params.toString()}`;
  }, [type, query, limit, enabled]);

  // Fetcher function
  const fetcher = useMemo(
    () => async () => {
      if (!cacheKey) throw new Error('Cache key is null');

      const response = await fetch(cacheKey);
      if (!response.ok) {
        throw new Error(`Blog API error: ${response.status}`);
      }

      return response.json() as Promise<BlogAPIResponse>;
    },
    [cacheKey]
  );

  // Use cached fetch hook
  const result = useCachedFetch<BlogAPIResponse>(cacheKey, fetcher, {
    ttl,
    enabled,
    staleWhileRevalidate: true, // Show cached data while revalidating
  });

  return result;
}

/**
 * Hook for fetching featured posts
 */
export function useFeaturedPosts(limit?: number) {
  return useBlogAPI({ type: 'featured', limit });
}

/**
 * Hook for fetching seasonal posts
 */
export function useSeasonalPosts(limit?: number) {
  return useBlogAPI({ type: 'seasonal', limit });
}

/**
 * Hook for fetching recent posts
 */
export function useRecentPosts(limit?: number) {
  return useBlogAPI({ type: 'recent', limit });
}

/**
 * Hook for fetching all posts
 */
export function useAllPosts() {
  return useBlogAPI({ type: 'all' });
}

/**
 * Hook for searching posts
 */
export function useSearchPosts(query: string, enabled = true) {
  return useBlogAPI({ type: 'search', query, enabled });
}

/**
 * Hook for fetching categories
 */
export function useCategories() {
  return useBlogAPI({ type: 'categories', ttl: 10 * 60 * 1000 }); // 10 minutes
}

/**
 * Hook for fetching tags
 */
export function useTags() {
  return useBlogAPI({ type: 'tags', ttl: 10 * 60 * 1000 }); // 10 minutes
}

/**
 * Hook for fetching service areas
 */
export function useServiceAreas() {
  return useBlogAPI({ type: 'serviceAreas', ttl: 10 * 60 * 1000 }); // 10 minutes
}

/**
 * Hook for fetching event types
 */
export function useEventTypes() {
  return useBlogAPI({ type: 'eventTypes', ttl: 10 * 60 * 1000 }); // 10 minutes
}
