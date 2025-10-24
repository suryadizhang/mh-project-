# Client-Side Caching System - Research & Analysis

**Issue**: HIGH PRIORITY #14 - Client-Side Caching  
**Date**: October 12, 2025  
**Status**: Research Phase  

---

## 🎯 Executive Summary

### Current State
- ❌ No client-side caching implemented
- ❌ Every page load fetches fresh data from API
- ❌ Repeated requests for static/semi-static data
- ❌ No offline capabilities
- ✅ SessionStorage only used for rate limiting

### Problem Statement
1. **Performance**: Unnecessary API calls on every page load
2. **User Experience**: Slow page loads, waiting for same data repeatedly
3. **Server Load**: Redundant requests burden backend
4. **Network Costs**: Wasted bandwidth fetching unchanged data
5. **Mobile Experience**: Poor performance on slow connections

### Goals
1. Reduce API calls by 40-60% through intelligent caching
2. Improve page load times by 50-70%
3. Better offline experience (stale data > no data)
4. Reduce server load and bandwidth usage
5. Maintain data freshness and consistency

---

## 📊 API Endpoint Analysis

### Cacheable Endpoints (High Value)

#### **1. Booking Availability** (High Cache Value)
| Endpoint | Current Behavior | Cache Strategy | TTL |
|----------|------------------|----------------|-----|
| `GET /api/v1/bookings/booked-dates` | Fetch on every calendar view | **Cache-First** | 5 minutes |
| `GET /api/v1/bookings/availability?date=X` | Fetch on date select | **Cache-First** | 3 minutes |
| `GET /api/v1/bookings/available-times?date=X` | Fetch on date select | **Cache-First** | 3 minutes |

**Reasoning:**
- Booking availability changes infrequently (only when bookings created)
- High read frequency (every user checks availability)
- Perfect for aggressive caching with short TTL
- Invalidate on successful booking creation

**Cache Invalidation:**
- On successful booking creation (POST /api/v1/bookings/submit)
- Manual refresh button
- 5-minute TTL expiration

#### **2. Customer Dashboard** (Medium Cache Value)
| Endpoint | Current Behavior | Cache Strategy | TTL |
|----------|------------------|----------------|-----|
| `GET /api/v1/customers/dashboard` | Fetch on dashboard load | **Stale-While-Revalidate** | 2 minutes |

**Reasoning:**
- Dashboard data changes occasionally (new bookings, savings updates)
- User expects relatively fresh data
- Can show stale data while fetching fresh in background

**Cache Invalidation:**
- On new booking creation
- On payment completion
- 2-minute TTL expiration

#### **3. Menu Items** (High Cache Value)
| Endpoint | Current Behavior | Cache Strategy | TTL |
|----------|------------------|----------------|-----|
| `GET /api/v1/menu` | Fetch on menu page load | **Cache-First** | 1 hour |

**Reasoning:**
- Menu items rarely change (admin-managed)
- Same for all users
- Very high read frequency
- Perfect for aggressive caching

**Cache Invalidation:**
- Manual admin refresh
- 1-hour TTL expiration
- Version header from backend

#### **4. Static Content** (Very High Cache Value)
| Endpoint | Current Behavior | Cache Strategy | TTL |
|----------|------------------|----------------|-----|
| `GET /api/v1/content/about` | Fetch on page load | **Cache-First** | 24 hours |
| `GET /api/v1/content/faq` | Fetch on page load | **Cache-First** | 24 hours |
| `GET /api/v1/content/terms` | Fetch on page load | **Cache-First** | 24 hours |

**Reasoning:**
- Content changes very rarely
- Same for all users
- Can cache aggressively

**Cache Invalidation:**
- Manual admin content update
- 24-hour TTL expiration

### Non-Cacheable Endpoints (Never Cache)

| Endpoint | Reason |
|----------|--------|
| `POST /api/v1/bookings/submit` | Mutations (write operations) |
| `POST /api/v1/payments/create-intent` | Sensitive, unique per transaction |
| `POST /api/v1/payments/checkout-session` | Payment verification (when implemented) |
| `POST /api/v1/auth/*` | Authentication (security-sensitive) |
| `GET /api/v1/admin/*` | Admin data (always fresh) |

---

## 🏗️ Architecture Design

### Cache Storage Strategy

#### **Option 1: localStorage (Recommended)**
**Pros:**
- Simple API (synchronous)
- Persistent across sessions
- ~5-10MB storage
- Great for semi-static data

**Cons:**
- Synchronous (can block main thread)
- Limited to 5-10MB
- Only stores strings (JSON serialization needed)

**Use For:**
- Menu items
- Static content
- User preferences
- Booking availability (short TTL)

#### **Option 2: IndexedDB**
**Pros:**
- Asynchronous (non-blocking)
- Much larger storage (~50MB+)
- Structured data support
- Better performance for large datasets

**Cons:**
- More complex API
- Overkill for current needs
- Requires wrapper library

**Use For:**
- Future: Large datasets (booking history, analytics)
- Future: Offline-first features

#### **Option 3: Memory Cache (in-memory object)**
**Pros:**
- Fastest (no I/O)
- Simple implementation
- No storage limits

**Cons:**
- Lost on page refresh
- Lost on navigation (SPA mitigates this)
- Not persistent

**Use For:**
- Session-specific data
- Very short-lived cache (< 1 minute)
- Dedupe in-flight requests

### **Recommended Hybrid Approach**

```typescript
// Three-tier caching strategy
1. Memory Cache (L1) - Fastest, session-only
   - In-flight request deduplication
   - Sub-second TTL for rapid requests

2. localStorage (L2) - Fast, persistent
   - Main cache tier (most endpoints)
   - TTLs from 1 minute to 24 hours
   - Automatic TTL expiration

3. API (L3) - Slowest, source of truth
   - Fallback when cache miss/stale
   - Always revalidate after TTL
```

---

## 🔧 Cache Service Design

### Core Features

#### **1. Cache Entry Structure**
```typescript
interface CacheEntry<T> {
  data: T;                    // Cached response data
  timestamp: number;          // When cached (Date.now())
  ttl: number;                // Time-to-live in milliseconds
  etag?: string;              // Optional ETag for validation
  version?: string;           // Optional version header
  endpoint: string;           // API endpoint (cache key)
  method: string;             // HTTP method
}

interface CacheMetadata {
  hits: number;               // Cache hits counter
  misses: number;             // Cache misses counter
  size: number;               // Total cache size in bytes
  entries: number;            // Number of cached entries
  lastCleanup: number;        // Last cleanup timestamp
}
```

#### **2. Cache Strategies**

**Strategy 1: Cache-First (Aggressive)**
```typescript
// Use cached data if available and not expired
// Perfect for: Menu items, static content, availability
async function cacheFirst<T>(endpoint: string, ttl: number): Promise<T> {
  const cached = getFromCache<T>(endpoint);
  
  if (cached && !isExpired(cached, ttl)) {
    return cached.data; // Cache hit!
  }
  
  // Cache miss or expired - fetch fresh
  const fresh = await fetchFromAPI<T>(endpoint);
  saveToCache(endpoint, fresh, ttl);
  return fresh;
}
```

**Strategy 2: Stale-While-Revalidate (Smart)**
```typescript
// Return stale data immediately, fetch fresh in background
// Perfect for: Dashboard, user-specific data
async function staleWhileRevalidate<T>(endpoint: string, ttl: number): Promise<T> {
  const cached = getFromCache<T>(endpoint);
  
  if (cached) {
    if (!isExpired(cached, ttl)) {
      return cached.data; // Fresh cache hit
    }
    
    // Expired but return stale, revalidate in background
    fetchFromAPI<T>(endpoint).then(fresh => {
      saveToCache(endpoint, fresh, ttl);
    });
    
    return cached.data; // Stale data (better than loading spinner)
  }
  
  // Cache miss - fetch fresh
  const fresh = await fetchFromAPI<T>(endpoint);
  saveToCache(endpoint, fresh, ttl);
  return fresh;
}
```

**Strategy 3: Network-First (Conservative)**
```typescript
// Try network first, fallback to cache on failure
// Perfect for: Critical data, admin panel
async function networkFirst<T>(endpoint: string, ttl: number): Promise<T> {
  try {
    const fresh = await fetchFromAPI<T>(endpoint);
    saveToCache(endpoint, fresh, ttl);
    return fresh;
  } catch (error) {
    // Network failed - try cache as fallback
    const cached = getFromCache<T>(endpoint);
    if (cached) {
      logger.warn('Network failed, using cached data', { endpoint, age: Date.now() - cached.timestamp });
      return cached.data;
    }
    throw error; // No cache available
  }
}
```

#### **3. Cache Invalidation**

```typescript
interface InvalidationRule {
  trigger: string;           // Mutation endpoint (e.g., POST /bookings)
  invalidates: string[];     // Endpoints to invalidate
}

const invalidationRules: InvalidationRule[] = [
  {
    trigger: 'POST /api/v1/bookings/submit',
    invalidates: [
      'GET /api/v1/bookings/booked-dates',
      'GET /api/v1/bookings/availability*',  // Wildcard
      'GET /api/v1/customers/dashboard',
    ]
  },
  {
    trigger: 'POST /api/v1/payments/create-intent',
    invalidates: [
      'GET /api/v1/customers/dashboard',
    ]
  },
  // ... more rules
];

function invalidateCache(mutationEndpoint: string): void {
  const rule = invalidationRules.find(r => r.trigger === mutationEndpoint);
  if (rule) {
    rule.invalidates.forEach(pattern => {
      if (pattern.endsWith('*')) {
        // Wildcard - remove all matching
        clearCacheByPrefix(pattern.slice(0, -1));
      } else {
        // Exact match
        removeFromCache(pattern);
      }
    });
  }
}
```

#### **4. Cache Warming (Optional Enhancement)**

```typescript
// Pre-fetch critical data on app load
async function warmCache(): Promise<void> {
  const criticalEndpoints = [
    { endpoint: '/api/v1/menu', ttl: 3600000 },           // 1 hour
    { endpoint: '/api/v1/content/about', ttl: 86400000 }, // 24 hours
  ];
  
  await Promise.all(
    criticalEndpoints.map(({ endpoint, ttl }) =>
      cacheFirst(endpoint, ttl).catch(err => {
        logger.warn('Cache warming failed', { endpoint, error: err });
      })
    )
  );
}
```

---

## 📦 Implementation Plan

### Phase 1: Core Cache Service (4 hours)

**File:** `apps/customer/src/lib/cacheService.ts`

**Features:**
1. CacheService class (singleton)
2. localStorage integration
3. Basic get/set with TTL
4. Automatic expiration
5. Cache size limits (5MB)
6. LRU eviction (when full)

**API:**
```typescript
class CacheService {
  // Core operations
  get<T>(key: string): CacheEntry<T> | null
  set<T>(key: string, data: T, ttl: number): void
  remove(key: string): void
  clear(): void
  
  // Strategies
  cacheFirst<T>(endpoint: string, ttl: number, fetcher: () => Promise<T>): Promise<T>
  staleWhileRevalidate<T>(endpoint: string, ttl: number, fetcher: () => Promise<T>): Promise<T>
  networkFirst<T>(endpoint: string, ttl: number, fetcher: () => Promise<T>): Promise<T>
  
  // Invalidation
  invalidate(pattern: string): void
  invalidateAll(): void
  
  // Metadata
  getMetadata(): CacheMetadata
  getSize(): number
}
```

### Phase 2: API Client Integration (2 hours)

**File:** `apps/customer/src/lib/api.ts`

**Changes:**
1. Add optional cache parameter to apiFetch
2. Integrate cache strategies
3. Automatic cache invalidation on mutations
4. Cache headers support (ETag, Cache-Control)

**Enhanced apiFetch:**
```typescript
interface ApiRequestOptions {
  method?: string;
  body?: string;
  headers?: Record<string, string>;
  schema?: z.ZodType;
  cache?: {
    strategy: 'cache-first' | 'stale-while-revalidate' | 'network-first';
    ttl: number;
    key?: string; // Optional custom cache key
  };
}

async function apiFetch<T>(
  path: string,
  options?: ApiRequestOptions
): Promise<ApiResponse<T>> {
  // If cache enabled, use cache service
  if (options?.cache) {
    const cacheService = CacheService.getInstance();
    const strategy = options.cache.strategy;
    const ttl = options.cache.ttl;
    const key = options.cache.key || `${options.method || 'GET'}:${path}`;
    
    switch (strategy) {
      case 'cache-first':
        return cacheService.cacheFirst(key, ttl, () => fetchFromNetwork<T>(path, options));
      case 'stale-while-revalidate':
        return cacheService.staleWhileRevalidate(key, ttl, () => fetchFromNetwork<T>(path, options));
      case 'network-first':
        return cacheService.networkFirst(key, ttl, () => fetchFromNetwork<T>(path, options));
    }
  }
  
  // No cache - fetch normally
  return fetchFromNetwork<T>(path, options);
}
```

### Phase 3: Component Updates (4 hours)

**Update Components to Use Caching:**

1. **BookUs/page.tsx** - Booking availability
   ```typescript
   const result = await apiFetch<BookedDatesResponse>(
     '/api/v1/bookings/booked-dates',
     {
       schema: BookedDatesResponseSchema,
       cache: {
         strategy: 'cache-first',
         ttl: 5 * 60 * 1000, // 5 minutes
       }
     }
   );
   ```

2. **CustomerSavingsDisplay.tsx** - Dashboard
   ```typescript
   const response = await apiFetch('/api/v1/customers/dashboard', {
     cache: {
       strategy: 'stale-while-revalidate',
       ttl: 2 * 60 * 1000, // 2 minutes
     }
   });
   ```

3. **Menu components** - Menu items
   ```typescript
   const menu = await apiFetch('/api/v1/menu', {
     cache: {
       strategy: 'cache-first',
       ttl: 60 * 60 * 1000, // 1 hour
     }
   });
   ```

### Phase 4: Cache Invalidation Rules (2 hours)

**File:** `apps/customer/src/lib/cacheInvalidationRules.ts`

**Implementation:**
1. Define invalidation rules
2. Hook into mutation endpoints
3. Automatic cache clearing on success

### Phase 5: Developer Tools & Monitoring (2 hours)

**Features:**
1. Cache inspector (dev tools panel)
2. Cache hit/miss metrics
3. Manual cache clear button
4. Cache size monitoring

**File:** `apps/customer/src/components/dev/CacheDevTools.tsx`

### Phase 6: Testing & Documentation (4 hours)

**Testing:**
1. Cache hit/miss scenarios
2. TTL expiration behavior
3. Invalidation rules
4. Cache size limits
5. LRU eviction
6. Error handling (localStorage full)

**Documentation:**
1. Cache strategy guide
2. Usage examples
3. Performance benchmarks
4. Troubleshooting guide

---

## 📊 Expected Impact

### Performance Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **API Calls** | 100% | 40-50% | 50-60% reduction |
| **Page Load Time** | 800ms | 300ms | 62% faster |
| **Data Transfer** | 500KB/session | 200KB/session | 60% reduction |
| **Server Load** | 100% | 40% | 60% reduction |
| **Mobile Experience** | Poor | Good | Significant |

### User Experience Improvements

- ✅ Instant page loads (cached data)
- ✅ Stale data > loading spinners
- ✅ Better offline experience
- ✅ Reduced waiting time
- ✅ Smoother navigation

### Technical Benefits

- ✅ Reduced server costs (fewer requests)
- ✅ Better mobile performance (less network)
- ✅ Improved scalability
- ✅ Better user retention (faster = better UX)

---

## ⚠️ Risks & Mitigations

### Risk 1: Stale Data
**Problem:** Users see outdated information  
**Mitigation:**
- Short TTLs (1-5 minutes)
- Manual refresh button
- Automatic invalidation on mutations
- Version headers from backend

### Risk 2: Storage Limits
**Problem:** localStorage full (5-10MB limit)  
**Mitigation:**
- LRU eviction policy
- Size monitoring
- Graceful degradation (no cache = fetch normally)
- Clear old entries automatically

### Risk 3: Cache Corruption
**Problem:** Invalid data in cache  
**Mitigation:**
- Zod validation on cache reads
- Try-catch around cache operations
- Auto-clear on errors
- Version stamping

### Risk 4: Complexity
**Problem:** Cache invalidation is hard  
**Mitigation:**
- Simple invalidation rules
- Conservative TTLs (short)
- Manual clear available
- Comprehensive testing

---

## 🎯 Success Criteria

### Must-Have
- ✅ Core CacheService implemented
- ✅ API client integration complete
- ✅ At least 5 endpoints cached
- ✅ Cache invalidation working
- ✅ TTL expiration working
- ✅ No breaking changes

### Nice-to-Have
- ✅ Cache dev tools
- ✅ Hit/miss metrics
- ✅ Cache warming
- ✅ ETag support
- ✅ Compression

---

## 📋 Checklist

### Research & Planning
- [x] Analyze cacheable endpoints
- [x] Define cache strategies
- [x] Design cache service architecture
- [x] Plan invalidation rules
- [x] Estimate impact

### Implementation
- [ ] Create CacheService class
- [ ] Implement cache strategies
- [ ] Integrate with API client
- [ ] Update components
- [ ] Add invalidation rules
- [ ] Create dev tools

### Testing
- [ ] Unit tests for CacheService
- [ ] Integration tests for cached endpoints
- [ ] TTL expiration tests
- [ ] Invalidation tests
- [ ] Error handling tests
- [ ] Performance benchmarks

### Documentation
- [ ] Cache strategy guide
- [ ] Usage examples
- [ ] API documentation
- [ ] Troubleshooting guide
- [ ] Performance report

---

## 🚀 Next Steps

1. ✅ **Research Complete** (this document)
2. ⏳ Create CacheService (Phase 1 - 4 hours)
3. ⏳ Integrate with API client (Phase 2 - 2 hours)
4. ⏳ Update components (Phase 3 - 4 hours)
5. ⏳ Implement invalidation (Phase 4 - 2 hours)
6. ⏳ Add dev tools (Phase 5 - 2 hours)
7. ⏳ Testing & docs (Phase 6 - 4 hours)

**Total Estimated Time:** 18 hours (2-3 days)

---

**Status**: ✅ Research Complete - Ready for Implementation  
**Next**: Phase 1 - Core CacheService Implementation  
**Date**: October 12, 2025
