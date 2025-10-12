# 🚀 MyHibachi Cache Strategy Guide

**Purpose:** Guidelines for implementing caching in the MyHibachi backend  
**Cache System:** Redis with TTL-based expiration + pattern-based invalidation  
**Location:** `apps/backend/src/core/cache.py`

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [When to Use Caching](#when-to-use-caching)
3. [Cache Decorators](#cache-decorators)
4. [TTL Guidelines](#ttl-guidelines)
5. [Cache Invalidation Patterns](#cache-invalidation-patterns)
6. [Best Practices](#best-practices)
7. [Examples](#examples)
8. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### **Step 1: Import the Cache Service**

```python
from src.core.cache import cached, invalidate_cache, get_cache_service
```

### **Step 2: Add Caching to Read Operations**

```python
@cached(ttl=300, key_prefix="user:profile")
async def get_user_profile(self, user_id: int) -> UserProfile:
    # Expensive database query
    return await self.db.query(UserProfile).filter_by(id=user_id).first()
```

### **Step 3: Add Invalidation to Write Operations**

```python
@invalidate_cache("user:*")  # Invalidates all user-related caches
async def update_user_profile(self, user_id: int, data: dict) -> UserProfile:
    # Update user in database
    user = await self.db.query(UserProfile).filter_by(id=user_id).first()
    for key, value in data.items():
        setattr(user, key, value)
    await self.db.commit()
    return user
```

---

## 🎯 When to Use Caching

### **✅ DO Cache:**

1. **Expensive Aggregations**
   - Dashboard statistics
   - Reports with multiple JOINs
   - COUNT, SUM, AVG operations
   
   ```python
   @cached(ttl=300, key_prefix="dashboard:stats")
   async def get_dashboard_stats(self):
       # Complex aggregation query
   ```

2. **Frequently Accessed Data**
   - User profiles (accessed on every request)
   - Configuration settings
   - Static reference data
   
   ```python
   @cached(ttl=3600, key_prefix="config:settings")
   async def get_app_settings(self):
       # Settings rarely change
   ```

3. **External API Calls**
   - Third-party API responses
   - Geocoding results
   - Exchange rates
   
   ```python
   @cached(ttl=1800, key_prefix="geo:location")
   async def geocode_address(self, address: str):
       # External API call
   ```

4. **Computed/Derived Data**
   - Availability calculations
   - Search results
   - Filtered lists
   
   ```python
   @cached(ttl=60, key_prefix="search:results")
   async def search_restaurants(self, query: str):
       # Complex search logic
   ```

### **❌ DON'T Cache:**

1. **Real-time Data**
   - Live order status
   - Current user location
   - Active session data

2. **User-specific Sensitive Data**
   - Payment information
   - Personal messages
   - Authentication tokens

3. **Rapidly Changing Data**
   - Live inventory counts
   - Real-time analytics
   - Streaming data

4. **Simple Single-row Lookups**
   ```python
   # DON'T cache this - it's already fast
   async def get_user_by_id(self, user_id: int):
       return await self.db.query(User).get(user_id)
   ```

---

## 🎨 Cache Decorators

### **1. @cached - Caching Decorator**

**Purpose:** Cache function results with TTL expiration

**Signature:**
```python
@cached(
    ttl: int,              # Time-to-live in seconds
    key_prefix: str,       # Cache key prefix (e.g., "booking:stats")
    cache_service: Optional[CacheService] = None  # Auto-injected
)
```

**How It Works:**
1. Function is called with arguments
2. Cache key is generated: `{namespace}:{key_prefix}:{function_name}:{args_hash}`
3. Check if key exists in Redis
4. If exists → return cached value (cache HIT)
5. If not exists → execute function, cache result, return value (cache MISS)

**Example:**
```python
@cached(ttl=300, key_prefix="booking:stats")
async def get_dashboard_stats(self, station_id: Optional[int] = None):
    # This function result is cached for 5 minutes
    # Key: myhibachi:booking:stats:get_dashboard_stats:a1b2c3d4
    return await self._calculate_stats(station_id)
```

### **2. @invalidate_cache - Invalidation Decorator**

**Purpose:** Clear cache keys after successful operation

**Signature:**
```python
@invalidate_cache(
    pattern: str,          # Redis pattern to match (e.g., "booking:*")
    cache_service: Optional[CacheService] = None  # Auto-injected
)
```

**How It Works:**
1. Function executes normally
2. If function succeeds → delete all matching cache keys
3. If function fails → cache is NOT invalidated (correct behavior)

**Example:**
```python
@invalidate_cache("booking:*")  # Wildcard pattern
async def create_booking(self, booking_data: BookingCreate):
    # Create booking in database
    booking = await self._insert_booking(booking_data)
    
    # After success, ALL keys matching "booking:*" are deleted:
    # - booking:stats:get_dashboard_stats:*
    # - booking:availability:get_available_slots:*
    
    return booking
```

---

## ⏱️ TTL Guidelines

**Choose TTL based on data characteristics:**

| Data Type | Recommended TTL | Rationale |
|-----------|----------------|-----------|
| **Critical/Real-time** | 30-60 seconds | Availability slots, live inventory |
| **Frequently Updated** | 5 minutes (300s) | Dashboard stats, aggregations |
| **Moderately Static** | 30 minutes (1800s) | User profiles, configurations |
| **Rarely Changing** | 1 hour (3600s) | Static reference data, settings |
| **External API Calls** | Depends on API | Follow API rate limits |

**Examples:**

```python
# Real-time availability (changes on every booking)
@cached(ttl=60, key_prefix="booking:availability")
async def get_available_slots(self, date: str):
    # 1 minute TTL - ensures fresh data

# Dashboard statistics (expensive calculation, acceptable staleness)
@cached(ttl=300, key_prefix="booking:stats")
async def get_dashboard_stats(self):
    # 5 minute TTL - balances performance and freshness

# Configuration settings (rarely change)
@cached(ttl=3600, key_prefix="config:settings")
async def get_app_settings(self):
    # 1 hour TTL - configuration changes are infrequent
```

---

## 🔄 Cache Invalidation Patterns

### **Pattern 1: Wildcard Invalidation (Recommended)**

**Use when:** Write operation affects multiple related caches

```python
# Cache booking statistics
@cached(ttl=300, key_prefix="booking:stats")
async def get_booking_stats(self): pass

# Cache availability
@cached(ttl=60, key_prefix="booking:availability")
async def get_available_slots(self): pass

# Invalidate ALL booking caches on create
@invalidate_cache("booking:*")  # Matches both stats and availability
async def create_booking(self, data: BookingCreate):
    # This invalidates:
    # - booking:stats:*
    # - booking:availability:*
    return await self._insert_booking(data)
```

**Benefits:**
- ✅ Simple - one pattern invalidates everything
- ✅ Safe - no risk of stale data
- ✅ Maintainable - add new caches without updating invalidation

**Trade-offs:**
- ⚠️ May invalidate more than necessary
- ⚠️ Cache hit rate may be lower

### **Pattern 2: Granular Invalidation (Advanced)**

**Use when:** High traffic or scaling concerns

```python
# Only invalidate specific cache
@invalidate_cache("booking:stats:*")  # Only stats, NOT availability
async def confirm_booking(self, booking_id: int):
    # Confirming a booking changes stats but not availability
    return await self._confirm_booking(booking_id)
```

**Benefits:**
- ✅ Higher cache hit rate
- ✅ Better performance at scale
- ✅ Less cache churn

**Trade-offs:**
- ⚠️ More complex - need to track which caches are affected
- ⚠️ Risk of missing invalidation (stale data)

**Recommendation:** Start with wildcard, move to granular if needed

### **Pattern 3: Multiple Invalidations**

**Use when:** Operation affects different cache namespaces

```python
from functools import wraps

def invalidate_multiple(*patterns):
    """Invalidate multiple cache patterns"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            cache = get_cache_service()
            for pattern in patterns:
                await cache.delete_pattern(pattern)
            return result
        return wrapper
    return decorator

# Usage:
@invalidate_multiple("booking:*", "user:stats:*")
async def create_booking_for_user(self, user_id: int, data: BookingCreate):
    # Invalidates both booking and user caches
    pass
```

---

## ✅ Best Practices

### **1. Namespace Your Cache Keys**

```python
# ✅ GOOD - Namespaced
@cached(ttl=300, key_prefix="booking:stats")
@cached(ttl=300, key_prefix="user:profile")

# ❌ BAD - No namespace (risk of collisions)
@cached(ttl=300, key_prefix="stats")
@cached(ttl=300, key_prefix="profile")
```

### **2. Invalidate on ALL Write Operations**

```python
@invalidate_cache("booking:*")
async def create_booking(self, data): pass

@invalidate_cache("booking:*")
async def update_booking(self, id: int, data): pass

@invalidate_cache("booking:*")
async def delete_booking(self, id: int): pass

# ❌ FORGOT confirm_booking! This causes stale stats.
```

### **3. Use Consistent Key Prefixes**

```python
# ✅ GOOD - Consistent naming
@cached(key_prefix="booking:stats")
@cached(key_prefix="booking:availability")
@cached(key_prefix="booking:details")

# ❌ BAD - Inconsistent naming
@cached(key_prefix="bookingStats")  # CamelCase
@cached(key_prefix="availability")   # No namespace
@cached(key_prefix="booking-details") # Hyphen instead of colon
```

### **4. Choose Appropriate TTL**

```python
# ✅ GOOD - TTL matches data freshness requirements
@cached(ttl=60, key_prefix="booking:availability")  # Changes frequently
@cached(ttl=300, key_prefix="booking:stats")        # Can be slightly stale

# ❌ BAD - TTL too long for critical data
@cached(ttl=3600, key_prefix="booking:availability")  # Users see stale availability!
```

### **5. Always Include Error Handling**

The cache service already handles errors gracefully:

```python
# cache.py already does this:
async def get(self, key: str):
    try:
        value = await self.redis.get(key)
        return json.loads(value) if value else None
    except Exception as e:
        logger.error(f"Cache get error: {e}")
        return None  # Fallback to database
```

No additional error handling needed in your code! If Redis fails, functions execute normally.

---

## 📚 Examples

### **Example 1: Booking Service (Current Implementation)**

```python
from src.core.cache import cached, invalidate_cache

class BookingService:
    # Cache expensive aggregation
    @cached(ttl=300, key_prefix="booking:stats")
    async def get_dashboard_stats(self, station_id: Optional[int] = None):
        """Get booking statistics (cached for 5 minutes)"""
        total_bookings = await self.repository.count_all()
        total_revenue = await self.repository.sum_revenue()
        confirmed_bookings = await self.repository.count_by_status("CONFIRMED")
        # ... more calculations
        return {
            "total_bookings": total_bookings,
            "total_revenue": total_revenue,
            "confirmed_bookings": confirmed_bookings,
        }
    
    # Cache frequently-accessed data with short TTL
    @cached(ttl=60, key_prefix="booking:availability")
    async def get_available_slots(self, date: str, party_size: int):
        """Get available booking slots (cached for 1 minute)"""
        all_slots = self._generate_time_slots(date)
        booked_slots = await self.repository.get_booked_slots(date)
        return [slot for slot in all_slots if slot not in booked_slots]
    
    # Invalidate all booking caches on write
    @invalidate_cache("booking:*")
    async def create_booking(self, data: BookingCreate):
        """Create new booking (invalidates all booking caches)"""
        booking = await self.repository.create(data)
        return booking
    
    @invalidate_cache("booking:*")
    async def confirm_booking(self, booking_id: int):
        """Confirm booking (invalidates stats)"""
        return await self.repository.update_status(booking_id, "CONFIRMED")
    
    @invalidate_cache("booking:*")
    async def cancel_booking(self, booking_id: int):
        """Cancel booking (invalidates stats and availability)"""
        return await self.repository.update_status(booking_id, "CANCELLED")
```

### **Example 2: User Service (Hypothetical)**

```python
class UserService:
    # Cache user profile (accessed on every request)
    @cached(ttl=1800, key_prefix="user:profile")
    async def get_user_profile(self, user_id: int):
        """Get user profile (cached for 30 minutes)"""
        return await self.repository.get_by_id(user_id)
    
    # Cache user statistics
    @cached(ttl=300, key_prefix="user:stats")
    async def get_user_stats(self, user_id: int):
        """Get user statistics (cached for 5 minutes)"""
        booking_count = await self.repository.count_bookings(user_id)
        total_spent = await self.repository.sum_payments(user_id)
        return {"booking_count": booking_count, "total_spent": total_spent}
    
    # Invalidate only profile cache (stats unchanged)
    @invalidate_cache("user:profile:*")
    async def update_user_profile(self, user_id: int, data: UserUpdate):
        """Update user profile"""
        return await self.repository.update(user_id, data)
    
    # Invalidate ALL user caches (profile + stats affected)
    @invalidate_cache("user:*")
    async def delete_user(self, user_id: int):
        """Delete user (invalidates all user caches)"""
        return await self.repository.delete(user_id)
```

### **Example 3: Configuration Service**

```python
class ConfigService:
    # Cache rarely-changing settings with long TTL
    @cached(ttl=3600, key_prefix="config:settings")
    async def get_app_settings(self):
        """Get application settings (cached for 1 hour)"""
        return await self.repository.get_all_settings()
    
    @cached(ttl=3600, key_prefix="config:features")
    async def get_feature_flags(self):
        """Get feature flags (cached for 1 hour)"""
        return await self.repository.get_feature_flags()
    
    # Invalidate ALL config caches
    @invalidate_cache("config:*")
    async def update_setting(self, key: str, value: Any):
        """Update setting (invalidates all config caches)"""
        return await self.repository.update_setting(key, value)
```

---

## 🐛 Troubleshooting

### **Problem: Cache not being used**

**Symptoms:**
- All requests hitting database
- Cache hit rate = 0%

**Causes:**
1. Redis service not running
2. Cache service not initialized
3. Function not decorated with `@cached`

**Solutions:**
```bash
# Check Redis status
redis-cli ping  # Should return "PONG"

# Check cache service initialization
# Look for this log on startup:
# "Cache service connected to Redis"
```

### **Problem: Stale data in cache**

**Symptoms:**
- Users see old data after updates
- Changes not reflected immediately

**Causes:**
1. Missing `@invalidate_cache` on write operation
2. Wrong invalidation pattern
3. TTL too long

**Solutions:**
```python
# ✅ Add invalidation to ALL write operations
@invalidate_cache("booking:*")
async def update_booking(self, id: int, data): pass

# ✅ Use wildcard pattern to catch all related caches
@invalidate_cache("booking:*")  # Not "booking:stats:*" (too specific)

# ✅ Reduce TTL if freshness is critical
@cached(ttl=30, key_prefix="booking:availability")  # Was 60
```

### **Problem: Cache invalidation not working**

**Symptoms:**
- `@invalidate_cache` decorated but cache not cleared
- Pattern doesn't match keys

**Causes:**
1. Pattern doesn't match key structure
2. Decorator on wrong function
3. Redis SCAN pattern syntax error

**Solutions:**
```python
# ❌ WRONG - Pattern doesn't match
@cached(key_prefix="booking_stats")  # Uses underscore
@invalidate_cache("booking:*")        # Uses colon (no match!)

# ✅ CORRECT - Consistent delimiters
@cached(key_prefix="booking:stats")
@invalidate_cache("booking:*")

# Test pattern matching in Redis CLI:
# redis-cli
# > KEYS myhibachi:booking:*
# Should see all matching keys
```

### **Problem: High memory usage**

**Symptoms:**
- Redis memory growing unbounded
- Out of memory errors

**Causes:**
1. TTL not set (keys never expire)
2. TTL too long
3. Caching too much data

**Solutions:**
```python
# ✅ Always set TTL
@cached(ttl=300, key_prefix="booking:stats")  # REQUIRED

# ✅ Reduce TTL if data is large
@cached(ttl=60, key_prefix="search:results")  # Was 300

# ✅ Don't cache large result sets
# Cache the query result count, not the full data
@cached(ttl=300, key_prefix="search:count")
async def count_search_results(self, query: str):
    return await self.repository.count(query)  # Just the count
```

---

## 📊 Monitoring Cache Performance

### **Cache Metrics (Already Implemented)**

```python
# src/core/metrics.py tracks:
cache_hits = Counter("cache_hits_total", "Cache hit count", ["key_prefix"])
cache_misses = Counter("cache_misses_total", "Cache miss count", ["key_prefix"])
```

### **Key Metrics to Monitor**

1. **Hit Rate:** `hits / (hits + misses)`
   - **Target:** > 70%
   - **Action if low:** Increase TTL or check invalidation frequency

2. **Miss Rate:** `misses / (hits + misses)`
   - **Target:** < 30%
   - **Action if high:** Check if cache is being populated

3. **Invalidation Frequency**
   - **Target:** Depends on write load
   - **Action if high:** Consider granular invalidation

### **Redis CLI Commands**

```bash
# Check cache size
redis-cli DBSIZE

# See all cache keys
redis-cli KEYS "myhibachi:*"

# Check key TTL
redis-cli TTL "myhibachi:booking:stats:get_dashboard_stats:abc123"

# Manually clear cache (for testing)
redis-cli FLUSHDB
```

---

## 🎓 Additional Resources

**Internal:**
- `apps/backend/src/core/cache.py` - Cache service implementation
- `CACHE_INVALIDATION_AUDIT.md` - Audit report

**External:**
- [Redis Best Practices](https://redis.io/docs/manual/patterns/)
- [Caching Strategies](https://aws.amazon.com/caching/best-practices/)

---

**Questions?** Contact the backend team or refer to the cache service source code.

**Last Updated:** October 11, 2025
