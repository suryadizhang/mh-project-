# HIGH #14: Client-Side Caching Implementation Plan

**Priority**: HIGH  
**Estimated Time**: 18 hours  
**Impact**: Performance improvement, reduced server load  
**Status**: 📋 READY TO START

---

## 🎯 Objectives

1. Implement intelligent client-side caching for API responses
2. Reduce redundant API calls
3. Improve page load times and user experience
4. Lower server load and bandwidth usage
5. Support cache invalidation and refresh strategies

---

## 📊 Current State Analysis

### API Endpoints (Cacheable)
```typescript
// From /api/blog route
✓ GET /api/blog?type=featured      // Changes: Rarely (new featured posts)
✓ GET /api/blog?type=seasonal      // Changes: Seasonally (~3 months)
✓ GET /api/blog?type=recent        // Changes: Frequently (new posts)
✓ GET /api/blog?type=all           // Changes: Frequently (new posts)
✓ GET /api/blog?type=search&q=...  // Changes: Never (deterministic)
✓ GET /api/blog?type=categories    // Changes: Rarely (new categories)
✓ GET /api/blog?type=tags          // Changes: Occasionally (new tags)
✓ GET /api/blog?type=serviceAreas  // Changes: Rarely (new locations)
✓ GET /api/blog?type=eventTypes    // Changes: Rarely (new event types)
```

### Current Fetch Patterns
```typescript
// Client components make direct fetch calls
// No caching - every mount = new request

// Example: FeaturedPostsCarousel.tsx
useEffect(() => {
  const fetchPosts = async () => {
    const featured = await fetch('/api/blog?type=featured').then(res => res.json());
    // ... use data
  };
  fetchPosts();
}, []);

// Problem: Re-fetches same data on every component mount
```

### Cache-able Data Analysis
```
High Priority (TTL: 5-10 minutes):
- Featured posts (changes rarely)
- Categories (nearly static)
- Tags (semi-static)
- Service areas (static)
- Event types (static)

Medium Priority (TTL: 1-2 minutes):
- Recent posts (changes frequently)
- All posts (changes frequently)

Low Priority (TTL: Indefinite):
- Search results (deterministic based on query)
```

---

## 🏗️ Architecture Design

### Cache Service Class

```typescript
// lib/cache/CacheService.ts

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
  key: string;
}

interface CacheConfig {
  storage: 'memory' | 'sessionStorage' | 'localStorage';
  defaultTTL: number; // milliseconds
  maxSize: number; // max entries
  debug: boolean;
}

class CacheService {
  private cache: Map<string, CacheEntry<any>>;
  private config: CacheConfig;

  constructor(config?: Partial<CacheConfig>) {
    this.cache = new Map();
    this.config = {
      storage: 'memory',
      defaultTTL: 5 * 60 * 1000, // 5 minutes
      maxSize: 100,
      debug: process.env.NODE_ENV === 'development',
      ...config
    };
  }

  /**
   * Get data from cache or fetch if not cached/expired
   */
  async get<T>(
    key: string,
    fetcher: () => Promise<T>,
    ttl?: number
  ): Promise<T> {
    const cached = this.cache.get(key);
    
    // Check if cached and not expired
    if (cached && Date.now() - cached.timestamp < cached.ttl) {
      this.log(`Cache HIT: ${key}`);
      return cached.data as T;
    }

    // Cache miss or expired - fetch new data
    this.log(`Cache MISS: ${key}`);
    const data = await fetcher();
    
    this.set(key, data, ttl);
    return data;
  }

  /**
   * Set data in cache
   */
  set<T>(key: string, data: T, ttl?: number): void {
    // Enforce max size (LRU eviction)
    if (this.cache.size >= this.config.maxSize) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
      this.log(`Evicted oldest entry: ${firstKey}`);
    }

    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl: ttl || this.config.defaultTTL,
      key
    });

    this.log(`Cached: ${key} (TTL: ${ttl || this.config.defaultTTL}ms)`);
  }

  /**
   * Clear specific cache entry
   */
  invalidate(key: string): void {
    this.cache.delete(key);
    this.log(`Invalidated: ${key}`);
  }

  /**
   * Clear all cache entries
   */
  clear(): void {
    this.cache.clear();
    this.log('Cache cleared');
  }

  /**
   * Get cache statistics
   */
  getStats() {
    return {
      size: this.cache.size,
      maxSize: this.config.maxSize,
      entries: Array.from(this.cache.keys()),
      usage: `${((this.cache.size / this.config.maxSize) * 100).toFixed(1)}%`
    };
  }

  private log(message: string): void {
    if (this.config.debug) {
      console.log(`[CacheService] ${message}`);
    }
  }
}

// Singleton instance
export const cacheService = new CacheService({
  storage: 'memory',
  defaultTTL: 5 * 60 * 1000, // 5 minutes
  maxSize: 100,
  debug: true
});

export default cacheService;
```

### Cache-Aware Fetch Hook

```typescript
// lib/hooks/useCachedFetch.ts

import { useEffect, useState } from 'react';
import cacheService from '@/lib/cache/CacheService';

interface UseCachedFetchOptions {
  ttl?: number;
  revalidateOnMount?: boolean;
  refetchInterval?: number;
}

export function useCachedFetch<T>(
  key: string,
  fetcher: () => Promise<T>,
  options?: UseCachedFetchOptions
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let mounted = true;
    let intervalId: NodeJS.Timeout | null = null;

    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await cacheService.get(key, fetcher, options?.ttl);
        if (mounted) {
          setData(result);
          setError(null);
        }
      } catch (err) {
        if (mounted) {
          setError(err as Error);
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    fetchData();

    // Optional: Set up refetch interval
    if (options?.refetchInterval) {
      intervalId = setInterval(fetchData, options.refetchInterval);
    }

    return () => {
      mounted = false;
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [key, options?.ttl, options?.refetchInterval]);

  const refetch = async () => {
    cacheService.invalidate(key);
    const result = await cacheService.get(key, fetcher, options?.ttl);
    setData(result);
  };

  return { data, loading, error, refetch };
}
```

### Cache TTL Configuration

```typescript
// lib/cache/cacheConfig.ts

export const CACHE_TTL = {
  // Static data (rarely changes)
  CATEGORIES: 10 * 60 * 1000,      // 10 minutes
  TAGS: 10 * 60 * 1000,            // 10 minutes
  SERVICE_AREAS: 15 * 60 * 1000,   // 15 minutes
  EVENT_TYPES: 15 * 60 * 1000,     // 15 minutes

  // Semi-static data
  FEATURED_POSTS: 5 * 60 * 1000,   // 5 minutes
  SEASONAL_POSTS: 5 * 60 * 1000,   // 5 minutes

  // Dynamic data (changes frequently)
  RECENT_POSTS: 2 * 60 * 1000,     // 2 minutes
  ALL_POSTS: 2 * 60 * 1000,        // 2 minutes

  // Search results (deterministic)
  SEARCH: 10 * 60 * 1000,          // 10 minutes
} as const;

export function getCacheKey(type: string, params?: Record<string, any>): string {
  if (!params || Object.keys(params).length === 0) {
    return `/api/blog?type=${type}`;
  }
  
  const queryString = Object.entries(params)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([key, value]) => `${key}=${value}`)
    .join('&');
  
  return `/api/blog?type=${type}&${queryString}`;
}
```

---

## 🔨 Implementation Steps

### Phase 1: Core Cache Service (3 hours)

**Tasks**:
1. Create `lib/cache/CacheService.ts`
2. Implement Map-based in-memory cache
3. Add TTL expiration logic
4. Add LRU eviction (max size enforcement)
5. Add debug logging
6. Create unit tests

**Files to Create**:
- `lib/cache/CacheService.ts`
- `lib/cache/cacheConfig.ts`
- `lib/cache/__tests__/CacheService.test.ts`

**Acceptance Criteria**:
- [x] Can store and retrieve data
- [x] TTL expiration works
- [x] LRU eviction works when max size reached
- [x] Can invalidate specific entries
- [x] Can clear entire cache
- [x] Stats method returns accurate info

### Phase 2: React Hook Integration (2 hours)

**Tasks**:
1. Create `useCachedFetch` hook
2. Support loading/error states
3. Support manual refetch
4. Support refetch intervals (optional)
5. Add TypeScript types

**Files to Create**:
- `lib/hooks/useCachedFetch.ts`
- `lib/hooks/__tests__/useCachedFetch.test.tsx`

**Acceptance Criteria**:
- [x] Hook returns data, loading, error states
- [x] Integrates with CacheService
- [x] Supports manual invalidation/refetch
- [x] Cleans up on unmount
- [x] TypeScript types are correct

### Phase 3: Blog Components Integration (8 hours)

**Components to Update**:

1. **FeaturedPostsCarousel.tsx**
```typescript
// BEFORE
useEffect(() => {
  const fetchPosts = async () => {
    const featured = await fetch('/api/blog?type=featured').then(res => res.json());
    setFeaturedPosts(featured);
  };
  fetchPosts();
}, []);

// AFTER
const { data: featured, loading } = useCachedFetch(
  getCacheKey('featured', { limit: maxPosts }),
  () => fetch('/api/blog?type=featured').then(res => res.json()),
  { ttl: CACHE_TTL.FEATURED_POSTS }
);
```

2. **blog/page.tsx** (4 fetch calls)
```typescript
// BEFORE
useEffect(() => {
  const loadData = async () => {
    const [featured, seasonal, recent] = await Promise.all([
      fetch('/api/blog?type=featured').then(res => res.json()),
      fetch('/api/blog?type=seasonal').then(res => res.json()),
      fetch('/api/blog?type=recent&limit=84').then(res => res.json())
    ]);
    // ... set state
  };
  loadData();
}, []);

// AFTER
const { data: featured } = useCachedFetch(
  getCacheKey('featured'),
  () => fetch('/api/blog?type=featured').then(res => res.json()),
  { ttl: CACHE_TTL.FEATURED_POSTS }
);

const { data: seasonal } = useCachedFetch(
  getCacheKey('seasonal'),
  () => fetch('/api/blog?type=seasonal').then(res => res.json()),
  { ttl: CACHE_TTL.SEASONAL_POSTS }
);

const { data: recent } = useCachedFetch(
  getCacheKey('recent', { limit: 84 }),
  () => fetch('/api/blog?type=recent&limit=84').then(res => res.json()),
  { ttl: CACHE_TTL.RECENT_POSTS }
);
```

3. **EnhancedSearch.tsx**
4. **TrendingPosts.tsx**
5. **AdvancedTagCloud.tsx**
6. **BlogSearch.tsx**

**Acceptance Criteria**:
- [x] All components use useCachedFetch
- [x] Appropriate TTL for each data type
- [x] No duplicate fetches on re-renders
- [x] Loading states work correctly
- [x] No breaking changes to UI

### Phase 4: Testing & Validation (3 hours)

**Manual Tests**:
- [x] Navigate to /blog - check Network tab (should see cache hits)
- [x] Refresh page - verify cached data used
- [x] Wait for TTL expiration - verify re-fetch
- [x] Navigate away and back - verify cache persistence
- [x] Open console - verify cache stats

**Performance Tests**:
```bash
# Before caching
# - Navigate to /blog: 10 API calls
# - Navigate to /blog/[slug]: 3-5 API calls
# - Total: 13-15 requests

# After caching
# - Navigate to /blog (first time): 10 API calls
# - Navigate to /blog (cached): 0 API calls
# - Navigate to /blog/[slug]: 0-1 API calls
# - Total (cached): 0-1 requests
```

**Unit Tests**:
- Cache service stores and retrieves
- TTL expiration works
- LRU eviction works
- useCachedFetch hook works
- Cache invalidation works

**Acceptance Criteria**:
- [x] All manual tests pass
- [x] Performance improvement measured (>80% reduction in requests)
- [x] All unit tests pass
- [x] No console errors
- [x] No memory leaks

### Phase 5: Documentation (2 hours)

**Documents to Create**:
1. `CACHING_GUIDE.md` - How caching works
2. `CACHE_STRATEGY.md` - When to cache, TTL values
3. Update `README.md` - Add caching section
4. JSDoc comments in code

**Acceptance Criteria**:
- [x] Documentation is clear and comprehensive
- [x] Examples provided for common use cases
- [x] Troubleshooting guide included

---

## 📊 Expected Benefits

### Performance Improvements
```
Metric                    Before    After     Improvement
===========================================================
API Calls (blog page)     10        1-2       80-90% ↓
API Calls (navigating)    5-10      0-1       90-95% ↓
Network bandwidth         High      Low       70-80% ↓
Server load               High      Low       70-80% ↓
Page load time (cached)   1-2s      <500ms    50-75% ↓
```

### User Experience
- ✅ Faster page loads (cached data loads instantly)
- ✅ Smoother navigation (no loading spinners for cached data)
- ✅ Better offline experience (cached data available)
- ✅ Reduced data usage (especially on mobile)

### Developer Experience
- ✅ Easy to use hook API
- ✅ Configurable TTL per endpoint
- ✅ Debug mode for development
- ✅ Cache stats for monitoring

---

## 🧪 Testing Strategy

### Unit Tests
```typescript
// CacheService.test.ts
describe('CacheService', () => {
  it('should store and retrieve data', () => {});
  it('should expire data after TTL', () => {});
  it('should evict oldest entry when max size reached', () => {});
  it('should invalidate specific entry', () => {});
  it('should clear all entries', () => {});
  it('should return accurate stats', () => {});
});

// useCachedFetch.test.tsx
describe('useCachedFetch', () => {
  it('should fetch data on mount', () => {});
  it('should use cached data on re-mount', () => {});
  it('should handle loading state', () => {});
  it('should handle error state', () => {});
  it('should support manual refetch', () => {});
});
```

### Integration Tests
```typescript
// blog/page.test.tsx
describe('Blog Page with Caching', () => {
  it('should make API calls on first load', () => {});
  it('should use cache on second load', () => {});
  it('should refetch after TTL expiration', () => {});
});
```

---

## 📝 Implementation Checklist

### Phase 1: Core (3 hours)
- [ ] Create CacheService class
- [ ] Implement get/set/invalidate/clear methods
- [ ] Add TTL expiration logic
- [ ] Add LRU eviction
- [ ] Add debug logging
- [ ] Create cache config
- [ ] Write unit tests
- [ ] Verify tests pass

### Phase 2: Hook (2 hours)
- [ ] Create useCachedFetch hook
- [ ] Add loading/error states
- [ ] Add refetch functionality
- [ ] Add TypeScript types
- [ ] Write unit tests
- [ ] Verify tests pass

### Phase 3: Integration (8 hours)
- [ ] Update FeaturedPostsCarousel
- [ ] Update blog/page.tsx
- [ ] Update EnhancedSearch
- [ ] Update TrendingPosts
- [ ] Update AdvancedTagCloud
- [ ] Update BlogSearch
- [ ] Test each component
- [ ] Verify no breaking changes

### Phase 4: Testing (3 hours)
- [ ] Manual testing (all scenarios)
- [ ] Performance benchmarks (before/after)
- [ ] Memory leak testing
- [ ] Cache stats validation
- [ ] Fix any issues found

### Phase 5: Documentation (2 hours)
- [ ] Create CACHING_GUIDE.md
- [ ] Create CACHE_STRATEGY.md
- [ ] Update README.md
- [ ] Add JSDoc comments
- [ ] Review and polish

---

## 🚀 Success Criteria

**HIGH #14 is COMPLETE when**:

1. ✅ CacheService class implemented and tested
2. ✅ useCachedFetch hook created and tested
3. ✅ All blog components using cache
4. ✅ 80%+ reduction in API calls (measured)
5. ✅ No console errors
6. ✅ No memory leaks
7. ✅ All tests pass
8. ✅ Documentation complete
9. ✅ Code reviewed
10. ✅ Committed to Git

---

## 📋 Next Steps After Completion

1. Monitor cache hit/miss ratio in production
2. Adjust TTL values based on real usage
3. Consider adding cache warming (prefetch common data)
4. Consider adding cache persistence (localStorage)
5. Consider adding cache compression (large datasets)

---

**Estimated Time**: 18 hours  
**Priority**: HIGH  
**Status**: 📋 READY TO START  
**Dependencies**: PHASE 2B must be complete ✅
