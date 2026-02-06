/**
 * Client-Side Cache Service
 *
 * Implements a 3-tier caching strategy:
 * - L1: Memory cache (fastest, session-only)
 * - L2: localStorage (persistent, 5-10MB)
 * - L3: API (slowest, source of truth)
 *
 * Features:
 * - TTL-based expiration
 * - LRU eviction policy
 * - Multiple cache strategies
 * - Automatic invalidation
 * - Size limits
 *
 * @module cacheService
 */

import { logger } from './logger';

// =============================================================================
// Types
// =============================================================================

export interface CacheEntry<T = unknown> {
  data: T;
  timestamp: number;
  ttl: number;
  endpoint: string;
  method: string;
  etag?: string;
  version?: string;
}

export interface CacheMetadata {
  hits: number;
  misses: number;
  size: number;
  entries: number;
  lastCleanup: number;
}

export type CacheStrategy = 'cache-first' | 'stale-while-revalidate' | 'network-first';

export interface CacheConfig {
  maxSize?: number; // Max cache size in bytes (default: 5MB)
  cleanupInterval?: number; // Cleanup interval in ms (default: 5 minutes)
  enableMemoryCache?: boolean; // Enable L1 memory cache (default: true)
  enablePersistent?: boolean; // Enable L2 localStorage (default: true)
}

// =============================================================================
// Cache Service Class
// =============================================================================

export class CacheService {
  private static instance: CacheService | null = null;

  // L1 Cache (Memory) - Fastest, session-only
  private memoryCache: Map<string, CacheEntry> = new Map();

  // Configuration
  private readonly config: Required<CacheConfig>;

  // Metadata
  private metadata: CacheMetadata = {
    hits: 0,
    misses: 0,
    size: 0,
    entries: 0,
    lastCleanup: Date.now(),
  };

  // Storage key prefix
  private readonly STORAGE_PREFIX = 'cache:';
  private readonly METADATA_KEY = 'cache-metadata';

  // =============================================================================
  // Singleton
  // =============================================================================

  private constructor(config?: CacheConfig) {
    this.config = {
      maxSize: config?.maxSize ?? 5 * 1024 * 1024, // 5MB default
      cleanupInterval: config?.cleanupInterval ?? 5 * 60 * 1000, // 5 minutes
      enableMemoryCache: config?.enableMemoryCache ?? true,
      enablePersistent: config?.enablePersistent ?? true,
    };

    // Load metadata from localStorage
    this.loadMetadata();

    // Start periodic cleanup
    this.startCleanupInterval();

    logger.info('CacheService initialized', {
      maxSize: this.config.maxSize,
      cleanupInterval: this.config.cleanupInterval,
      enableMemoryCache: this.config.enableMemoryCache,
      enablePersistent: this.config.enablePersistent,
    });
  }

  public static getInstance(config?: CacheConfig): CacheService {
    if (!CacheService.instance) {
      CacheService.instance = new CacheService(config);
    }
    return CacheService.instance;
  }

  public static resetInstance(): void {
    if (CacheService.instance) {
      CacheService.instance.clear();
    }
    CacheService.instance = null;
  }

  // =============================================================================
  // Core Operations
  // =============================================================================

  /**
   * Get cached data by key
   */
  public get<T>(key: string): CacheEntry<T> | null {
    try {
      // Try L1 (memory) first
      if (this.config.enableMemoryCache) {
        const memCached = this.memoryCache.get(key);
        if (memCached) {
          this.metadata.hits++;
          return memCached as CacheEntry<T>;
        }
      }

      // Try L2 (localStorage)
      if (this.config.enablePersistent) {
        const stored = localStorage.getItem(this.STORAGE_PREFIX + key);
        if (stored) {
          const entry = JSON.parse(stored) as CacheEntry<T>;

          // Update L1 cache
          if (this.config.enableMemoryCache) {
            this.memoryCache.set(key, entry);
          }

          this.metadata.hits++;
          return entry;
        }
      }

      // Cache miss
      this.metadata.misses++;
      return null;
    } catch (error) {
      logger.error('Cache get error', error as Error, { key });
      this.metadata.misses++;
      return null;
    }
  }

  /**
   * Set cached data with TTL
   */
  public set<T>(
    key: string,
    data: T,
    ttl: number,
    options?: { etag?: string; version?: string },
  ): void {
    try {
      const entry: CacheEntry<T> = {
        data,
        timestamp: Date.now(),
        ttl,
        endpoint: key.split(':')[1] || key,
        method: key.split(':')[0] || 'GET',
        etag: options?.etag,
        version: options?.version,
      };

      const entrySize = this.calculateSize(entry);

      // Check if we need to evict entries (LRU)
      if (this.metadata.size + entrySize > this.config.maxSize) {
        this.evictLRU(entrySize);
      }

      // Update L1 (memory)
      if (this.config.enableMemoryCache) {
        this.memoryCache.set(key, entry);
      }

      // Update L2 (localStorage)
      if (this.config.enablePersistent) {
        try {
          localStorage.setItem(this.STORAGE_PREFIX + key, JSON.stringify(entry));
        } catch (storageError) {
          // localStorage full - evict and retry
          logger.warn('localStorage full, evicting entries', { key });
          this.evictLRU(entrySize * 2); // Evict extra space
          localStorage.setItem(this.STORAGE_PREFIX + key, JSON.stringify(entry));
        }
      }

      // Update metadata
      this.metadata.size += entrySize;
      this.metadata.entries++;
      this.saveMetadata();

      logger.debug('Cache set', { key, ttl, size: entrySize });
    } catch (error) {
      logger.error('Cache set error', error as Error, { key });
    }
  }

  /**
   * Remove cached entry
   */
  public remove(key: string): void {
    try {
      // Remove from L1
      if (this.config.enableMemoryCache) {
        this.memoryCache.delete(key);
      }

      // Remove from L2
      if (this.config.enablePersistent) {
        const stored = localStorage.getItem(this.STORAGE_PREFIX + key);
        if (stored) {
          const entry = JSON.parse(stored) as CacheEntry;
          const entrySize = this.calculateSize(entry);

          localStorage.removeItem(this.STORAGE_PREFIX + key);

          // Update metadata
          this.metadata.size -= entrySize;
          this.metadata.entries--;
        }
      }

      this.saveMetadata();
      logger.debug('Cache remove', { key });
    } catch (error) {
      logger.error('Cache remove error', error as Error, { key });
    }
  }

  /**
   * Clear all cached entries
   */
  public clear(): void {
    try {
      // Clear L1
      if (this.config.enableMemoryCache) {
        this.memoryCache.clear();
      }

      // Clear L2
      if (this.config.enablePersistent) {
        const keys = this.getAllKeys();
        keys.forEach((key) => localStorage.removeItem(key));
      }

      // Reset metadata
      this.metadata.entries = 0;
      this.metadata.size = 0;
      this.saveMetadata();

      logger.info('Cache cleared');
    } catch (error) {
      logger.error('Cache clear error', error as Error);
    }
  }

  // =============================================================================
  // Cache Strategies
  // =============================================================================

  /**
   * Cache-First Strategy
   * Use cached data if available and not expired, otherwise fetch fresh
   */
  public async cacheFirst<T>(key: string, ttl: number, fetcher: () => Promise<T>): Promise<T> {
    const cached = this.get<T>(key);

    // Check if cached and not expired
    if (cached && !this.isExpired(cached)) {
      logger.debug('Cache hit (cache-first)', { key, age: Date.now() - cached.timestamp });
      return cached.data;
    }

    // Cache miss or expired - fetch fresh
    logger.debug('Cache miss (cache-first)', {
      key,
      expired: cached ? this.isExpired(cached) : false,
    });
    const fresh = await fetcher();
    this.set(key, fresh, ttl);
    return fresh;
  }

  /**
   * Stale-While-Revalidate Strategy
   * Return stale data immediately, fetch fresh in background
   */
  public async staleWhileRevalidate<T>(
    key: string,
    ttl: number,
    fetcher: () => Promise<T>,
  ): Promise<T> {
    const cached = this.get<T>(key);

    if (cached) {
      if (!this.isExpired(cached)) {
        // Fresh cache hit
        logger.debug('Cache hit (stale-while-revalidate, fresh)', { key });
        return cached.data;
      }

      // Expired but return stale, revalidate in background
      logger.debug('Cache hit (stale-while-revalidate, stale)', {
        key,
        age: Date.now() - cached.timestamp,
      });

      // Background revalidation (don't await)
      fetcher()
        .then((fresh) => this.set(key, fresh, ttl))
        .catch((error) => logger.error('Background revalidation failed', error as Error, { key }));

      return cached.data;
    }

    // Cache miss - fetch fresh
    logger.debug('Cache miss (stale-while-revalidate)', { key });
    const fresh = await fetcher();
    this.set(key, fresh, ttl);
    return fresh;
  }

  /**
   * Network-First Strategy
   * Try network first, fallback to cache on failure
   */
  public async networkFirst<T>(key: string, ttl: number, fetcher: () => Promise<T>): Promise<T> {
    try {
      // Try network first
      const fresh = await fetcher();
      this.set(key, fresh, ttl);
      logger.debug('Network success (network-first)', { key });
      return fresh;
    } catch (error) {
      // Network failed - try cache as fallback
      const cached = this.get<T>(key);
      if (cached) {
        logger.warn('Network failed, using cached data', {
          key,
          age: Date.now() - cached.timestamp,
          expired: this.isExpired(cached),
        });
        return cached.data;
      }

      // No cache available - rethrow error
      logger.error('Network failed and no cache available', error as Error, { key });
      throw error;
    }
  }

  // =============================================================================
  // Cache Invalidation
  // =============================================================================

  /**
   * Invalidate cache by pattern (supports wildcards)
   */
  public invalidate(pattern: string): void {
    try {
      if (pattern.endsWith('*')) {
        // Wildcard - remove all matching
        const prefix = pattern.slice(0, -1);
        this.invalidateByPrefix(prefix);
      } else {
        // Exact match
        this.remove(pattern);
      }

      logger.info('Cache invalidated', { pattern });
    } catch (error) {
      logger.error('Cache invalidation error', error as Error, { pattern });
    }
  }

  /**
   * Invalidate all cache entries
   */
  public invalidateAll(): void {
    this.clear();
    logger.info('All cache invalidated');
  }

  /**
   * Invalidate by prefix (for wildcard patterns)
   */
  private invalidateByPrefix(prefix: string): void {
    const keys = this.getAllKeys();
    const fullPrefix = this.STORAGE_PREFIX + prefix;

    keys
      .filter((key) => key.startsWith(fullPrefix))
      .forEach((key) => {
        const shortKey = key.replace(this.STORAGE_PREFIX, '');
        this.remove(shortKey);
      });
  }

  // =============================================================================
  // Metadata & Utilities
  // =============================================================================

  /**
   * Get cache metadata (hits, misses, size, etc.)
   */
  public getMetadata(): CacheMetadata {
    return { ...this.metadata };
  }

  /**
   * Get cache size in bytes
   */
  public getSize(): number {
    return this.metadata.size;
  }

  /**
   * Get cache hit rate
   */
  public getHitRate(): number {
    const total = this.metadata.hits + this.metadata.misses;
    return total === 0 ? 0 : this.metadata.hits / total;
  }

  /**
   * Check if cache entry is expired
   */
  private isExpired(entry: CacheEntry): boolean {
    return Date.now() - entry.timestamp > entry.ttl;
  }

  /**
   * Calculate entry size (approximate)
   */
  private calculateSize(entry: CacheEntry): number {
    try {
      return JSON.stringify(entry).length * 2; // UTF-16 uses 2 bytes per char
    } catch {
      return 1024; // Default 1KB if calculation fails
    }
  }

  /**
   * Get all localStorage keys for this cache
   */
  private getAllKeys(): string[] {
    const keys: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key?.startsWith(this.STORAGE_PREFIX)) {
        keys.push(key);
      }
    }
    return keys;
  }

  /**
   * LRU Eviction - Remove oldest entries until enough space
   */
  private evictLRU(spaceNeeded: number): void {
    const keys = this.getAllKeys();
    const entries: Array<{ key: string; timestamp: number; size: number }> = [];

    // Collect all entries with timestamps
    keys.forEach((key) => {
      try {
        const stored = localStorage.getItem(key);
        if (stored) {
          const entry = JSON.parse(stored) as CacheEntry;
          entries.push({
            key: key.replace(this.STORAGE_PREFIX, ''),
            timestamp: entry.timestamp,
            size: this.calculateSize(entry),
          });
        }
      } catch {
        // Skip invalid entries
      }
    });

    // Sort by timestamp (oldest first)
    entries.sort((a, b) => a.timestamp - b.timestamp);

    // Remove oldest until we have enough space
    let freedSpace = 0;
    for (const entry of entries) {
      if (freedSpace >= spaceNeeded) break;

      this.remove(entry.key);
      freedSpace += entry.size;

      logger.debug('Evicted cache entry (LRU)', {
        key: entry.key,
        age: Date.now() - entry.timestamp,
        size: entry.size,
      });
    }

    logger.info('LRU eviction complete', {
      freedSpace,
      entriesRemoved: entries.length,
    });
  }

  /**
   * Cleanup expired entries
   */
  private cleanup(): void {
    const keys = this.getAllKeys();
    let removed = 0;

    keys.forEach((key) => {
      try {
        const stored = localStorage.getItem(key);
        if (stored) {
          const entry = JSON.parse(stored) as CacheEntry;
          if (this.isExpired(entry)) {
            this.remove(key.replace(this.STORAGE_PREFIX, ''));
            removed++;
          }
        }
      } catch {
        // Remove invalid entries
        localStorage.removeItem(key);
        removed++;
      }
    });

    this.metadata.lastCleanup = Date.now();
    this.saveMetadata();

    if (removed > 0) {
      logger.info('Cache cleanup complete', { removed, remaining: this.metadata.entries });
    }
  }

  /**
   * Start periodic cleanup interval
   */
  private startCleanupInterval(): void {
    setInterval(() => {
      this.cleanup();
    }, this.config.cleanupInterval);
  }

  /**
   * Load metadata from localStorage
   */
  private loadMetadata(): void {
    try {
      const stored = localStorage.getItem(this.METADATA_KEY);
      if (stored) {
        this.metadata = JSON.parse(stored);
      }
    } catch (error) {
      logger.warn('Failed to load cache metadata', { error });
    }
  }

  /**
   * Save metadata to localStorage
   */
  private saveMetadata(): void {
    try {
      localStorage.setItem(this.METADATA_KEY, JSON.stringify(this.metadata));
    } catch (error) {
      logger.warn('Failed to save cache metadata', { error });
    }
  }
}

// =============================================================================
// Exports
// =============================================================================

// Export singleton instance getter
export const getCacheService = (config?: CacheConfig): CacheService => {
  return CacheService.getInstance(config);
};

// Export for testing
export const resetCacheService = (): void => {
  CacheService.resetInstance();
};
