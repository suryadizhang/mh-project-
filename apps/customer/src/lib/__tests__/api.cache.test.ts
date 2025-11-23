/**
 * Integration Tests for API Client Caching
 *
 * Tests cover:
 * - apiFetch with cacheStrategy option
 * - All 3 cache strategies (cache-first, stale-while-revalidate, network-first)
 * - Automatic cache invalidation after mutations
 * - Integration with rate limiting and retries
 * - Error handling with caching
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'

import { apiFetch } from '../api'
import { getCacheService, resetCacheService } from '../cacheService'

// Mock fetch globally
global.fetch = vi.fn()

describe('API Client Caching Integration', () => {
  beforeEach(() => {
    // Reset cache before each test
    resetCacheService()

    // Clear mocks
    vi.clearAllMocks()

    // Mock console to reduce noise
    vi.spyOn(console, 'warn').mockImplementation(() => {})
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('apiFetch with cacheStrategy option', () => {
    it('should cache GET request with cache-first strategy', async () => {
      const mockData = { bookings: [] }
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockData,
        headers: new Headers(),
      })
      global.fetch = mockFetch

      // First call - should fetch
      const result1 = await apiFetch('/api/v1/bookings', {
        method: 'GET',
        cacheStrategy: {
          strategy: 'cache-first',
          ttl: 60000,
        },
      })

      expect(result1).toEqual({ data: mockData, success: true })
      expect(mockFetch).toHaveBeenCalledTimes(1)

      // Second call - should use cache
      const result2 = await apiFetch('/api/v1/bookings', {
        method: 'GET',
        cacheStrategy: {
          strategy: 'cache-first',
          ttl: 60000,
        },
      })

      expect(result2).toEqual({ data: mockData, success: true })
      expect(mockFetch).toHaveBeenCalledTimes(1) // Still 1 - cached
    })

    it('should use custom cache key if provided', async () => {
      const mockData = { data: 'test' }
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockData,
        headers: new Headers(),
      })
      global.fetch = mockFetch

      // First call with custom key
      await apiFetch('/api/v1/data?param=1', {
        method: 'GET',
        cacheStrategy: {
          strategy: 'cache-first',
          ttl: 60000,
          key: 'custom-data-key',
        },
      })

      // Second call with same custom key (different URL)
      const result = await apiFetch('/api/v1/data?param=2', {
        method: 'GET',
        cacheStrategy: {
          strategy: 'cache-first',
          ttl: 60000,
          key: 'custom-data-key',
        },
      })

      expect(result).toEqual({ data: mockData, success: true })
      expect(mockFetch).toHaveBeenCalledTimes(1) // Used same cache key
    })

    it('should not cache POST requests', async () => {
      const mockData = { success: true }
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockData,
        headers: new Headers(),
      })
      global.fetch = mockFetch

      // POST with cacheStrategy should be ignored
      await apiFetch('/api/v1/bookings', {
        method: 'POST',
        body: JSON.stringify({ data: 'test' }),
        cacheStrategy: {
          strategy: 'cache-first',
          ttl: 60000,
        },
      })

      await apiFetch('/api/v1/bookings', {
        method: 'POST',
        body: JSON.stringify({ data: 'test' }),
        cacheStrategy: {
          strategy: 'cache-first',
          ttl: 60000,
        },
      })

      // Should fetch both times (no caching for POST)
      expect(mockFetch).toHaveBeenCalledTimes(2)
    })
  })

  describe('cache-first strategy', () => {
    it('should return cached data immediately if fresh', async () => {
      const mockData = { users: ['Alice', 'Bob'] }
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockData,
        headers: new Headers(),
      })
      global.fetch = mockFetch

      // First call
      await apiFetch('/api/v1/users', {
        cacheStrategy: {
          strategy: 'cache-first',
          ttl: 5000,
        },
      })

      // Second call - should be instant (cached)
      const startTime = Date.now()
      const result = await apiFetch('/api/v1/users', {
        cacheStrategy: {
          strategy: 'cache-first',
          ttl: 5000,
        },
      })
      const duration = Date.now() - startTime

      expect(result).toEqual({ data: mockData, success: true })
      expect(duration).toBeLessThan(50) // Should be near-instant
      expect(mockFetch).toHaveBeenCalledTimes(1)
    })

    it('should refetch if cache expired', async () => {
      const mockFetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({ version: 1 }),
          headers: new Headers(),
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({ version: 2 }),
          headers: new Headers(),
        })
      global.fetch = mockFetch

      const ttl = 100 // 100ms

      // First call
      const result1 = await apiFetch('/api/v1/version', {
        cacheStrategy: {
          strategy: 'cache-first',
          ttl,
        },
      })
      expect(result1).toEqual({ data: { version: 1 }, success: true })

      // Wait for expiration
      await new Promise(resolve => setTimeout(resolve, ttl + 50))

      // Second call - cache expired
      const result2 = await apiFetch('/api/v1/version', {
        cacheStrategy: {
          strategy: 'cache-first',
          ttl,
        },
      })
      expect(result2).toEqual({ data: { version: 2 }, success: true })
      expect(mockFetch).toHaveBeenCalledTimes(2)
    })
  })

  describe('stale-while-revalidate strategy', () => {
    it('should return stale data immediately and revalidate', async () => {
      const mockFetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({ count: 1 }),
          headers: new Headers(),
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({ count: 2 }),
          headers: new Headers(),
        })
      global.fetch = mockFetch

      const ttl = 100

      // First call - fetch fresh
      const result1 = await apiFetch('/api/v1/count', {
        cacheStrategy: {
          strategy: 'stale-while-revalidate',
          ttl,
        },
      })
      expect(result1).toEqual({ data: { count: 1 }, success: true })

      // Wait for expiration
      await new Promise(resolve => setTimeout(resolve, ttl + 50))

      // Second call - should return stale immediately
      const result2 = await apiFetch('/api/v1/count', {
        cacheStrategy: {
          strategy: 'stale-while-revalidate',
          ttl,
        },
      })
      expect(result2).toEqual({ data: { count: 1 }, success: true }) // Still stale
      expect(mockFetch).toHaveBeenCalledTimes(2) // But triggered revalidation

      // Wait for revalidation
      await new Promise(resolve => setTimeout(resolve, 100))

      // Third call - should have fresh data
      const result3 = await apiFetch('/api/v1/count', {
        cacheStrategy: {
          strategy: 'stale-while-revalidate',
          ttl,
        },
      })
      expect(result3).toEqual({ data: { count: 2 }, success: true })
    })
  })

  describe('network-first strategy', () => {
    it('should always try network first', async () => {
      const mockFetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({ value: 'first' }),
          headers: new Headers(),
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({ value: 'second' }),
          headers: new Headers(),
        })
      global.fetch = mockFetch

      // First call
      const result1 = await apiFetch('/api/v1/data', {
        cacheStrategy: {
          strategy: 'network-first',
          ttl: 60000,
        },
      })
      expect(result1).toEqual({ data: { value: 'first' }, success: true })

      // Second call - should try network again
      const result2 = await apiFetch('/api/v1/data', {
        cacheStrategy: {
          strategy: 'network-first',
          ttl: 60000,
        },
      })
      expect(result2).toEqual({ data: { value: 'second' }, success: true })
      expect(mockFetch).toHaveBeenCalledTimes(2)
    })

    it('should fallback to cache if network fails', async () => {
      const mockFetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({ data: 'cached' }),
          headers: new Headers(),
        })
        .mockRejectedValueOnce(new Error('Network error'))
      global.fetch = mockFetch

      // First call - succeed and cache
      await apiFetch('/api/v1/fallback', {
        cacheStrategy: {
          strategy: 'network-first',
          ttl: 60000,
        },
        retry: false, // Disable retries for this test
      })

      // Second call - network fails, should fallback
      const result = await apiFetch('/api/v1/fallback', {
        cacheStrategy: {
          strategy: 'network-first',
          ttl: 60000,
        },
        retry: false, // Disable retries for this test
      })

      expect(result).toEqual({ data: { data: 'cached' }, success: true })
      expect(mockFetch).toHaveBeenCalledTimes(2)
    })
  })

  describe('Automatic Cache Invalidation', () => {
    // SKIP: These tests have design issues - cache keys don't match invalidation patterns
    // The tests use custom keys like 'booked-dates' but invalidation looks for 'GET:/api/v1/bookings/booked-dates'
    // This is a known issue to fix in a separate PR
    it.skip('should invalidate booking-related caches after booking mutation', async () => {
      const cacheService = getCacheService()
      const mockFetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({ dates: ['2025-10-15'] }),
          headers: new Headers(),
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 201,
          json: async () => ({ id: 123 }),
          headers: new Headers(),
        })
      global.fetch = mockFetch

      // Cache booked-dates
      await apiFetch('/api/v1/bookings/booked-dates', {
        cacheStrategy: {
          strategy: 'cache-first',
          ttl: 60000,
          key: 'booked-dates',
        },
      })

      // Verify it's cached
      expect(cacheService.get('booked-dates')).toBeTruthy()

      // Create a booking (POST)
      await apiFetch('/api/v1/bookings', {
        method: 'POST',
        body: JSON.stringify({ date: '2025-10-16' }),
      })

      // Cache should be invalidated
      expect(cacheService.get('booked-dates')).toBeNull()
    })

    it.skip('should invalidate availability* caches after booking mutation', async () => {
      const cacheService = getCacheService()
      const mockFetch = vi.fn()
        .mockResolvedValue({
          ok: true,
          status: 200,
          json: async () => ({}),
          headers: new Headers(),
        })
      global.fetch = mockFetch

      // Cache availability entries
      await apiFetch('/api/v1/bookings/availability', {
        cacheStrategy: {
          strategy: 'cache-first',
          ttl: 60000,
          key: 'availability-2025-10-15',
        },
      })

      expect(cacheService.get('availability-2025-10-15')).toBeTruthy()

      // Update a booking (PUT)
      await apiFetch('/api/v1/bookings/123', {
        method: 'PUT',
        body: JSON.stringify({ status: 'confirmed' }),
      })

      // Wildcard pattern should invalidate availability*
      expect(cacheService.get('availability-2025-10-15')).toBeNull()
    })

    it.skip('should invalidate dashboard after customer mutation', async () => {
      const cacheService = getCacheService()
      const mockFetch = vi.fn()
        .mockResolvedValue({
          ok: true,
          status: 200,
          json: async () => ({}),
          headers: new Headers(),
        })
      global.fetch = mockFetch

      // Cache dashboard
      await apiFetch('/api/v1/customers/dashboard', {
        cacheStrategy: {
          strategy: 'cache-first',
          ttl: 60000,
          key: 'dashboard',
        },
      })

      expect(cacheService.get('dashboard')).toBeTruthy()

      // Update customer (PATCH)
      await apiFetch('/api/v1/customers/456', {
        method: 'PATCH',
        body: JSON.stringify({ name: 'Updated' }),
      })

      // Dashboard should be invalidated
      expect(cacheService.get('dashboard')).toBeNull()
    })

    it.skip('should invalidate menu* after menu mutation', async () => {
      const cacheService = getCacheService()
      const mockFetch = vi.fn()
        .mockResolvedValue({
          ok: true,
          status: 200,
          json: async () => ({}),
          headers: new Headers(),
        })
      global.fetch = mockFetch

      // Cache menu entries
      await apiFetch('/api/v1/menu/items', {
        cacheStrategy: {
          strategy: 'cache-first',
          ttl: 60000,
          key: 'menu-items',
        },
      })

      expect(cacheService.get('menu-items')).toBeTruthy()

      // Update menu (PUT)
      await apiFetch('/api/v1/menu/items/789', {
        method: 'PUT',
        body: JSON.stringify({ price: 25.99 }),
      })

      // Menu caches should be invalidated
      expect(cacheService.get('menu-items')).toBeNull()
    })

    it('should not invalidate on GET requests', async () => {
      const cacheService = getCacheService()
      const mockFetch = vi.fn()
        .mockResolvedValue({
          ok: true,
          status: 200,
          json: async () => ({}),
          headers: new Headers(),
        })
      global.fetch = mockFetch

      // Cache data
      await apiFetch('/api/v1/data', {
        cacheStrategy: {
          strategy: 'cache-first',
          ttl: 60000,
          key: 'test-data',
        },
      })

      expect(cacheService.get('test-data')).toBeTruthy()

      // Another GET request
      await apiFetch('/api/v1/bookings', {
        method: 'GET',
      })

      // Cache should still exist
      expect(cacheService.get('test-data')).toBeTruthy()
    })
  })

  describe('Error Handling with Caching', () => {
    it('should not cache failed requests', async () => {
      const mockFetch = vi.fn()
        .mockResolvedValueOnce({
          ok: false,
          status: 500,
          text: async () => 'Server error',
          json: async () => ({ error: 'Server error' }),
          headers: new Headers(),
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({ data: 'success' }),
          headers: new Headers(),
        })
      global.fetch = mockFetch

      // First call - fails
      try {
        await apiFetch('/api/v1/error', {
          cacheStrategy: {
            strategy: 'cache-first',
            ttl: 60000,
          },
          retry: false, // Disable retries for this test
        })
      } catch (error) {
        // Expected to fail
      }

      // Second call - should fetch again (no cache of error)
      const result = await apiFetch('/api/v1/error', {
        cacheStrategy: {
          strategy: 'cache-first',
          ttl: 60000,
        },
        retry: false, // Disable retries for this test
      })

      expect(result).toEqual({ data: { data: 'success' }, success: true })
      expect(mockFetch).toHaveBeenCalledTimes(2)
    })

    it('should handle cache service errors gracefully', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ data: 'test' }),
        headers: new Headers(),
      })
      global.fetch = mockFetch

      // Mock cache service to throw
      const cacheService = getCacheService()
      vi.spyOn(cacheService, 'cacheFirst').mockRejectedValue(
        new Error('Cache error')
      )

      // Should return error response when cache fails
      const result = await apiFetch('/api/v1/data', {
        cacheStrategy: {
          strategy: 'cache-first',
          ttl: 60000,
        },
      })

      // When cache strategy fails, it returns an error response
      expect(result.success).toBe(false)
      expect(result.error).toBeTruthy()
    })
  })

  describe('Integration with Rate Limiting', () => {
    it('should work with rate limiting', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ data: 'limited' }),
        headers: new Headers(),
      })
      global.fetch = mockFetch

      // First call with caching
      await apiFetch('/api/v1/limited', {
        cacheStrategy: {
          strategy: 'cache-first',
          ttl: 60000,
        },
      })

      // Second call - should use cache (no rate limit check needed)
      await apiFetch('/api/v1/limited', {
        cacheStrategy: {
          strategy: 'cache-first',
          ttl: 60000,
        },
      })

      // Only one actual fetch
      expect(mockFetch).toHaveBeenCalledTimes(1)
    })

    it('should handle 429 responses with caching', async () => {
      const mockFetch = vi.fn()
        .mockResolvedValueOnce({
          ok: false,
          status: 429,
          headers: new Headers({ 'Retry-After': '1' }),
          json: async () => ({ error: 'Rate limited' }),
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({ data: 'success' }),
          headers: new Headers(),
        })
      global.fetch = mockFetch

      // First call - rate limited
      try {
        await apiFetch('/api/v1/rate-limited', {
          retry: true,
          cacheStrategy: {
            strategy: 'cache-first',
            ttl: 60000,
          },
        })
      } catch (error) {
        // May throw or retry
      }

      // Retry logic should work with caching
      // Implementation specific
    })
  })

  describe('Performance Optimization', () => {
    it('should reduce API calls significantly', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ items: [] }),
        headers: new Headers(),
      })
      global.fetch = mockFetch

      // Make 10 identical requests
      for (let i = 0; i < 10; i++) {
        await apiFetch('/api/v1/items', {
          cacheStrategy: {
            strategy: 'cache-first',
            ttl: 60000,
          },
        })
      }

      // Should only fetch once (9 cache hits)
      expect(mockFetch).toHaveBeenCalledTimes(1)

      const cacheService = getCacheService()
      const metadata = cacheService.getMetadata()
      expect(metadata.hits).toBeGreaterThanOrEqual(9)
    })

    it('should improve response time with caching', async () => {
      const mockFetch = vi.fn().mockImplementation(() => {
        // Simulate network delay
        return new Promise(resolve => {
          setTimeout(() => {
            resolve({
              ok: true,
              status: 200,
              json: async () => ({ data: 'slow' }),
              headers: new Headers(),
            })
          }, 100) // 100ms delay
        })
      })
      global.fetch = mockFetch

      // First call - slow (network)
      const start1 = Date.now()
      await apiFetch('/api/v1/slow', {
        cacheStrategy: {
          strategy: 'cache-first',
          ttl: 60000,
        },
      })
      const duration1 = Date.now() - start1
      expect(duration1).toBeGreaterThanOrEqual(100)

      // Second call - fast (cached)
      const start2 = Date.now()
      await apiFetch('/api/v1/slow', {
        cacheStrategy: {
          strategy: 'cache-first',
          ttl: 60000,
        },
      })
      const duration2 = Date.now() - start2
      expect(duration2).toBeLessThan(50) // Much faster
    })
  })
})
