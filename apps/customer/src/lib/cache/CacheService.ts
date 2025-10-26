/**
 * CacheService - LRU Cache with TTL for client-side data caching
 *
 * Features:
 * - LRU (Least Recently Used) eviction policy
 * - TTL (Time To Live) expiration
 * - Memory management with configurable max entries
 * - Type-safe generic implementation
 */

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  expiresAt: number;
  hits: number;
}

interface CacheConfig {
  maxEntries?: number;
  defaultTTL?: number; // milliseconds
  enableLogging?: boolean;
}

interface CacheStats {
  size: number;
  maxSize: number;
  hits: number;
  misses: number;
  evictions: number;
  hitRate: number;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export class CacheService<T = any> {
  private cache: Map<string, CacheEntry<T>>;
  private accessOrder: string[]; // For LRU tracking
  private maxEntries: number;
  private defaultTTL: number;
  private enableLogging: boolean;
  
  // Statistics
  private stats = {
    hits: 0,
    misses: 0,
    evictions: 0,
  };

  constructor(config: CacheConfig = {}) {
    this.cache = new Map();
    this.accessOrder = [];
    this.maxEntries = config.maxEntries ?? 100;
    this.defaultTTL = config.defaultTTL ?? 5 * 60 * 1000; // 5 minutes default
    this.enableLogging = config.enableLogging ?? false;
  }

  /**
   * Get data from cache
   */
  get(key: string): T | null {
    const entry = this.cache.get(key);

    if (!entry) {
      this.stats.misses++;
      this.log('MISS', key);
      return null;
    }

    // Check if expired
    if (Date.now() > entry.expiresAt) {
      this.delete(key);
      this.stats.misses++;
      this.log('MISS (expired)', key);
      return null;
    }

    // Update LRU order
    this.updateAccessOrder(key);
    entry.hits++;
    this.stats.hits++;
    this.log('HIT', key, `(hits: ${entry.hits})`);

    return entry.data;
  }

  /**
   * Set data in cache
   */
  set(key: string, data: T, ttl?: number): void {
    const expiresAt = Date.now() + (ttl ?? this.defaultTTL);

    // Check if we need to evict
    if (!this.cache.has(key) && this.cache.size >= this.maxEntries) {
      this.evictLRU();
    }

    const entry: CacheEntry<T> = {
      data,
      timestamp: Date.now(),
      expiresAt,
      hits: 0,
    };

    this.cache.set(key, entry);
    this.updateAccessOrder(key);
    this.log('SET', key, `(ttl: ${(ttl ?? this.defaultTTL) / 1000}s)`);
  }

  /**
   * Check if key exists and is valid
   */
  has(key: string): boolean {
    const entry = this.cache.get(key);
    if (!entry) return false;

    // Check expiration
    if (Date.now() > entry.expiresAt) {
      this.delete(key);
      return false;
    }

    return true;
  }

  /**
   * Delete entry from cache
   */
  delete(key: string): boolean {
    const existed = this.cache.delete(key);
    if (existed) {
      this.removeFromAccessOrder(key);
      this.log('DELETE', key);
    }
    return existed;
  }

  /**
   * Clear all entries
   */
  clear(): void {
    this.cache.clear();
    this.accessOrder = [];
    this.log('CLEAR', 'all entries');
  }

  /**
   * Remove expired entries
   */
  prune(): number {
    const now = Date.now();
    let pruned = 0;

    for (const [key, entry] of this.cache.entries()) {
      if (now > entry.expiresAt) {
        this.cache.delete(key);
        this.removeFromAccessOrder(key);
        pruned++;
      }
    }

    if (pruned > 0) {
      this.log('PRUNE', `${pruned} expired entries`);
    }

    return pruned;
  }

  /**
   * Get cache statistics
   */
  getStats(): CacheStats {
    const totalRequests = this.stats.hits + this.stats.misses;
    return {
      size: this.cache.size,
      maxSize: this.maxEntries,
      hits: this.stats.hits,
      misses: this.stats.misses,
      evictions: this.stats.evictions,
      hitRate: totalRequests > 0 ? this.stats.hits / totalRequests : 0,
    };
  }

  /**
   * Reset statistics
   */
  resetStats(): void {
    this.stats = {
      hits: 0,
      misses: 0,
      evictions: 0,
    };
    this.log('STATS RESET');
  }

  /**
   * Get all cached keys
   */
  keys(): string[] {
    return Array.from(this.cache.keys());
  }

  /**
   * Get cache size
   */
  size(): number {
    return this.cache.size;
  }

  /**
   * Update LRU access order
   */
  private updateAccessOrder(key: string): void {
    // Remove from current position
    this.removeFromAccessOrder(key);
    // Add to end (most recently used)
    this.accessOrder.push(key);
  }

  /**
   * Remove from access order
   */
  private removeFromAccessOrder(key: string): void {
    const index = this.accessOrder.indexOf(key);
    if (index > -1) {
      this.accessOrder.splice(index, 1);
    }
  }

  /**
   * Evict least recently used entry
   */
  private evictLRU(): void {
    if (this.accessOrder.length === 0) return;

    // First item is least recently used
    const lruKey = this.accessOrder[0];
    this.cache.delete(lruKey);
    this.removeFromAccessOrder(lruKey);
    this.stats.evictions++;
    this.log('EVICT (LRU)', lruKey);
  }

  /**
   * Logging helper
   */
  private log(action: string, key: string = '', extra: string = ''): void {
    if (this.enableLogging) {
      const timestamp = new Date().toISOString().split('T')[1].slice(0, -1);
      console.log(`[CacheService ${timestamp}] ${action} ${key} ${extra}`.trim());
    }
  }
}

// Export singleton instances for common use cases
export const blogCache = new CacheService({
  maxEntries: 50,
  defaultTTL: 5 * 60 * 1000, // 5 minutes
  enableLogging: process.env.NODE_ENV === 'development',
});

export const apiCache = new CacheService({
  maxEntries: 100,
  defaultTTL: 3 * 60 * 1000, // 3 minutes
  enableLogging: process.env.NODE_ENV === 'development',
});
