/**
 * React Query Client Configuration - Performance Optimized
 * 
 * Optimizations:
 * - Stale-while-revalidate caching strategy
 * - Smart refetch policies
 * - Error retry with exponential backoff
 * - Garbage collection for unused data
 * - Prefetching support
 */

import { QueryClient } from '@tanstack/react-query';

/**
 * Create optimized QueryClient instance
 * 
 * Configuration Philosophy:
 * - Minimize network requests (aggressive caching)
 * - Keep UI responsive (background refetch)
 * - Handle errors gracefully (retry logic)
 * - Clean up unused data (garbage collection)
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Cache Strategy
      staleTime: 5 * 60 * 1000, // Data is fresh for 5 minutes
      gcTime: 10 * 60 * 1000, // Keep unused data for 10 minutes (v5: cacheTime renamed to gcTime)

      // Refetch Policies (Minimize unnecessary requests)
      refetchOnWindowFocus: false, // Don't refetch on tab focus (can be annoying)
      refetchOnReconnect: true, // DO refetch when internet reconnects
      refetchOnMount: false, // Use cached data when component mounts

      // Error Handling
      retry: 3, // Retry failed requests 3 times
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000), // Exponential backoff

      // Performance
      structuralSharing: true, // Reuse objects to prevent unnecessary re-renders
    },

    mutations: {
      // Retry failed mutations once
      retry: 1,
      retryDelay: 1000,
    },
  },
});

/**
 * Prefetch data for better perceived performance
 * Call this before navigating to a page
 */
export const prefetchReviews = async (page: number = 1) => {
  await queryClient.prefetchQuery({
    queryKey: ['reviews', page],
    queryFn: async () => {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/api/customer-reviews/approved-reviews?page=${page}&per_page=20`
      );
      
      if (!response.ok) {
        throw new Error('Failed to fetch reviews');
      }
      
      return response.json();
    },
    staleTime: 5 * 60 * 1000,
  });
};

/**
 * Prefetch pending reviews for admin
 */
export const prefetchPendingReviews = async () => {
  await queryClient.prefetchQuery({
    queryKey: ['admin', 'pending-reviews'],
    queryFn: async () => {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/api/admin/review-moderation/pending-reviews`
      );
      
      if (!response.ok) {
        throw new Error('Failed to fetch pending reviews');
      }
      
      return response.json();
    },
    staleTime: 2 * 60 * 1000, // Admin data is fresher (2 minutes)
  });
};

/**
 * Invalidate and refetch all reviews
 * Useful for manual refresh button
 */
export const refreshReviews = async () => {
  await queryClient.invalidateQueries({ queryKey: ['reviews'] });
  await queryClient.refetchQueries({ queryKey: ['reviews'], type: 'active' });
};

/**
 * Invalidate and refetch admin pending reviews
 */
export const refreshPendingReviews = async () => {
  await queryClient.invalidateQueries({ queryKey: ['admin', 'pending-reviews'] });
  await queryClient.refetchQueries({ queryKey: ['admin', 'pending-reviews'], type: 'active' });
};

/**
 * Clear all cached data
 * Use sparingly (e.g., on logout)
 */
export const clearCache = () => {
  queryClient.clear();
};

/**
 * Get cache statistics for debugging
 */
export const getCacheStats = () => {
  const cache = queryClient.getQueryCache();
  const queries = cache.getAll();

  return {
    totalQueries: queries.length,
    freshQueries: queries.filter(q => q.state.dataUpdatedAt > Date.now() - 5 * 60 * 1000).length,
    staleQueries: queries.filter(q => q.state.dataUpdatedAt <= Date.now() - 5 * 60 * 1000).length,
    fetchingQueries: queries.filter(q => q.state.fetchStatus === 'fetching').length,
  };
};

export default queryClient;
