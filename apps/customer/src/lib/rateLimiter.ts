/**
 * Client-Side Rate Limiter with Token Bucket Algorithm
 * ====================================================
 *
 * Prevents excessive API calls before they reach the server.
 * Works alongside server-side rate limiting for better UX.
 *
 * Features:
 * - Token bucket algorithm for smooth rate limiting
 * - Per-endpoint rate limit configuration
 * - SessionStorage persistence (survives page refreshes)
 * - Automatic token refill over time
 * - Countdown timers for cooldown periods
 * - TypeScript type safety
 *
 * Usage:
 * ```typescript
 * const limiter = RateLimiter.getInstance();
 *
 * // Check before making request
 * if (!limiter.checkLimit('/api/v1/bookings')) {
 *   const waitTime = limiter.getWaitTime('/api/v1/bookings');
 *   console.log(`Please wait ${waitTime}s before retrying`);
 *   return;
 * }
 *
 * // Record successful request
 * limiter.recordRequest('/api/v1/bookings');
 * ```
 */

import { logger } from '@/lib/logger';

/**
 * Rate limit configuration for different endpoint categories
 */
export interface RateLimitConfig {
  /** Maximum number of requests allowed */
  maxRequests: number;
  /** Time window in milliseconds */
  windowMs: number;
  /** Refill rate (tokens per second) */
  refillRate: number;
  /** Burst capacity (max tokens at once) */
  burstCapacity: number;
}

/**
 * Token bucket state for an endpoint
 */
interface TokenBucket {
  /** Current number of tokens available */
  tokens: number;
  /** Last time tokens were refilled */
  lastRefill: number;
  /** Total requests made in current window */
  requestCount: number;
  /** Start of current time window */
  windowStart: number;
}

/**
 * Rate limit configuration per endpoint category
 *
 * Categories:
 * - booking: Complex operations (create, update booking)
 * - search: Search and filter operations
 * - api: General API calls
 * - payment: Payment processing
 * - upload: File uploads
 * - chat: AI chat messages
 */
const RATE_LIMIT_CONFIGS: Record<string, RateLimitConfig> = {
  // Booking operations - strict limits for critical endpoints
  booking_create: {
    maxRequests: 5, // 5 requests per minute
    windowMs: 60 * 1000, // 1 minute
    refillRate: 0.0833, // ~5 tokens per minute
    burstCapacity: 5, // Can make 5 requests at once
  },

  booking_update: {
    maxRequests: 10, // 10 requests per minute
    windowMs: 60 * 1000,
    refillRate: 0.1667, // ~10 tokens per minute
    burstCapacity: 10,
  },

  booking_list: {
    maxRequests: 30, // 30 requests per minute
    windowMs: 60 * 1000,
    refillRate: 0.5, // 30 tokens per minute
    burstCapacity: 30,
  },

  // Search operations - moderate limits
  search: {
    maxRequests: 20, // 20 searches per minute
    windowMs: 60 * 1000,
    refillRate: 0.3333, // ~20 tokens per minute
    burstCapacity: 10, // Prevent search spam
  },

  // Payment operations - very strict
  payment: {
    maxRequests: 3, // 3 payments per 5 minutes
    windowMs: 5 * 60 * 1000, // 5 minutes
    refillRate: 0.01, // ~3 tokens per 5 minutes
    burstCapacity: 3,
  },

  // File uploads - strict limits
  upload: {
    maxRequests: 5, // 5 uploads per 5 minutes
    windowMs: 5 * 60 * 1000,
    refillRate: 0.0167, // ~5 tokens per 5 minutes
    burstCapacity: 5,
  },

  // Chat operations - moderate limits
  chat: {
    maxRequests: 15, // 15 messages per minute
    windowMs: 60 * 1000,
    refillRate: 0.25, // 15 tokens per minute
    burstCapacity: 15,
  },

  // General API calls - lenient limits
  api: {
    maxRequests: 60, // 60 requests per minute
    windowMs: 60 * 1000,
    refillRate: 1.0, // 60 tokens per minute
    burstCapacity: 60,
  },
};

/**
 * Determines rate limit category for an endpoint
 */
function getCategoryForEndpoint(endpoint: string): string {
  // Normalize endpoint
  const path = endpoint.toLowerCase();

  // Booking operations
  if (path.includes('/bookings') && path.includes('submit')) return 'booking_create';
  if (path.includes('/bookings') && (path.includes('update') || path.includes('modify'))) {
    return 'booking_update';
  }
  if (path.includes('/bookings')) return 'booking_list';

  // Search operations
  if (path.includes('search') || path.includes('filter') || path.includes('query')) {
    return 'search';
  }

  // Payment operations
  if (path.includes('/payment') || path.includes('/stripe') || path.includes('/checkout')) {
    return 'payment';
  }

  // File uploads
  if (path.includes('/upload') || path.includes('/image')) {
    return 'upload';
  }

  // Chat operations
  if (path.includes('/chat') || path.includes('/ai/')) {
    return 'chat';
  }

  // Default to general API
  return 'api';
}

/**
 * Client-side rate limiter using token bucket algorithm
 * Singleton pattern to maintain state across the app
 */
export class RateLimiter {
  private static instance: RateLimiter;
  private buckets: Map<string, TokenBucket>;
  private readonly storageKey = 'rate_limiter_state';

  private constructor() {
    this.buckets = new Map();
    this.loadState();

    // Auto-save state every 5 seconds
    if (typeof window !== 'undefined') {
      setInterval(() => this.saveState(), 5000);
    }
  }

  /**
   * Get singleton instance
   */
  public static getInstance(): RateLimiter {
    if (!RateLimiter.instance) {
      RateLimiter.instance = new RateLimiter();
    }
    return RateLimiter.instance;
  }

  /**
   * Load state from sessionStorage
   */
  private loadState(): void {
    if (typeof window === 'undefined') return;

    try {
      const stored = sessionStorage.getItem(this.storageKey);
      if (stored) {
        const data = JSON.parse(stored);
        this.buckets = new Map(Object.entries(data));
        logger.debug('Rate limiter state loaded from storage', { bucketCount: this.buckets.size });
      }
    } catch (error) {
      logger.warn('Failed to load rate limiter state', { error });
    }
  }

  /**
   * Save state to sessionStorage
   */
  private saveState(): void {
    if (typeof window === 'undefined') return;

    try {
      const data = Object.fromEntries(this.buckets);
      sessionStorage.setItem(this.storageKey, JSON.stringify(data));
    } catch (error) {
      logger.warn('Failed to save rate limiter state', { error });
    }
  }

  /**
   * Get or create token bucket for endpoint
   */
  private getBucket(endpoint: string): TokenBucket {
    const category = getCategoryForEndpoint(endpoint);

    if (!this.buckets.has(endpoint)) {
      const config = RATE_LIMIT_CONFIGS[category];
      this.buckets.set(endpoint, {
        tokens: config.burstCapacity,
        lastRefill: Date.now(),
        requestCount: 0,
        windowStart: Date.now(),
      });
    }

    return this.buckets.get(endpoint)!;
  }

  /**
   * Refill tokens based on elapsed time
   */
  private refillTokens(endpoint: string): void {
    const category = getCategoryForEndpoint(endpoint);
    const config = RATE_LIMIT_CONFIGS[category];
    const bucket = this.getBucket(endpoint);

    const now = Date.now();
    const elapsed = (now - bucket.lastRefill) / 1000; // seconds

    // Calculate tokens to add based on refill rate
    const tokensToAdd = elapsed * config.refillRate;

    if (tokensToAdd >= 1) {
      // Add tokens up to burst capacity
      bucket.tokens = Math.min(config.burstCapacity, bucket.tokens + Math.floor(tokensToAdd));
      bucket.lastRefill = now;

      logger.debug('Tokens refilled', {
        endpoint,
        category,
        tokensAdded: Math.floor(tokensToAdd),
        currentTokens: bucket.tokens,
      });
    }

    // Reset window if expired
    if (now - bucket.windowStart > config.windowMs) {
      bucket.requestCount = 0;
      bucket.windowStart = now;
    }
  }

  /**
   * Check if request is allowed
   *
   * @param endpoint - API endpoint path
   * @returns true if request is allowed, false if rate limited
   */
  public checkLimit(endpoint: string): boolean {
    const category = getCategoryForEndpoint(endpoint);
    const config = RATE_LIMIT_CONFIGS[category];

    // Refill tokens first
    this.refillTokens(endpoint);

    const bucket = this.getBucket(endpoint);

    // Check sliding window limit
    if (bucket.requestCount >= config.maxRequests) {
      const timeInWindow = Date.now() - bucket.windowStart;
      if (timeInWindow < config.windowMs) {
        logger.warn('Rate limit exceeded (sliding window)', {
          endpoint,
          category,
          requestCount: bucket.requestCount,
          maxRequests: config.maxRequests,
          windowMs: config.windowMs,
        });
        return false;
      }
    }

    // Check token bucket
    if (bucket.tokens < 1) {
      logger.warn('Rate limit exceeded (token bucket)', {
        endpoint,
        category,
        tokens: bucket.tokens,
        burstCapacity: config.burstCapacity,
      });
      return false;
    }

    return true;
  }

  /**
   * Record a request (consume a token)
   *
   * @param endpoint - API endpoint path
   */
  public recordRequest(endpoint: string): void {
    const bucket = this.getBucket(endpoint);
    const category = getCategoryForEndpoint(endpoint);

    // Consume token
    bucket.tokens = Math.max(0, bucket.tokens - 1);
    bucket.requestCount++;

    logger.debug('Request recorded', {
      endpoint,
      category,
      remainingTokens: bucket.tokens,
      requestCount: bucket.requestCount,
    });

    // Save state after recording
    this.saveState();
  }

  /**
   * Get remaining requests for endpoint
   *
   * @param endpoint - API endpoint path
   * @returns number of requests remaining
   */
  public getRemainingRequests(endpoint: string): number {
    const category = getCategoryForEndpoint(endpoint);
    const config = RATE_LIMIT_CONFIGS[category];

    this.refillTokens(endpoint);
    const bucket = this.getBucket(endpoint);

    // Return minimum of token bucket and sliding window limit
    const slidingWindowRemaining = Math.max(0, config.maxRequests - bucket.requestCount);
    return Math.min(Math.floor(bucket.tokens), slidingWindowRemaining);
  }

  /**
   * Get wait time in seconds before next request allowed
   *
   * @param endpoint - API endpoint path
   * @returns seconds to wait (0 if request allowed now)
   */
  public getWaitTime(endpoint: string): number {
    if (this.checkLimit(endpoint)) {
      return 0;
    }

    const category = getCategoryForEndpoint(endpoint);
    const config = RATE_LIMIT_CONFIGS[category];
    const bucket = this.getBucket(endpoint);

    // Calculate wait time based on token refill rate
    const tokensNeeded = 1 - bucket.tokens;
    const waitTime = Math.ceil(tokensNeeded / config.refillRate);

    return Math.max(1, waitTime);
  }

  /**
   * Reset rate limit for specific endpoint
   *
   * @param endpoint - API endpoint path
   */
  public reset(endpoint: string): void {
    const category = getCategoryForEndpoint(endpoint);
    const config = RATE_LIMIT_CONFIGS[category];

    this.buckets.set(endpoint, {
      tokens: config.burstCapacity,
      lastRefill: Date.now(),
      requestCount: 0,
      windowStart: Date.now(),
    });

    this.saveState();

    logger.info('Rate limit reset', { endpoint, category });
  }

  /**
   * Reset all rate limits
   */
  public resetAll(): void {
    this.buckets.clear();
    this.saveState();
    logger.info('All rate limits reset');
  }

  /**
   * Get rate limit info for endpoint (useful for UI display)
   *
   * @param endpoint - API endpoint path
   * @returns rate limit information
   */
  public getInfo(endpoint: string): {
    category: string;
    config: RateLimitConfig;
    remaining: number;
    waitTime: number;
    isLimited: boolean;
  } {
    const category = getCategoryForEndpoint(endpoint);
    const config = RATE_LIMIT_CONFIGS[category];

    return {
      category,
      config,
      remaining: this.getRemainingRequests(endpoint),
      waitTime: this.getWaitTime(endpoint),
      isLimited: !this.checkLimit(endpoint),
    };
  }
}

/**
 * Convenience function to get rate limiter instance
 */
export function getRateLimiter(): RateLimiter {
  return RateLimiter.getInstance();
}

/**
 * React hook for using rate limiter in components
 *
 * @param endpoint - API endpoint to rate limit
 * @returns rate limiter instance and endpoint-specific helpers
 */
export function useRateLimiter(endpoint: string) {
  const limiter = getRateLimiter();

  return {
    checkLimit: () => limiter.checkLimit(endpoint),
    recordRequest: () => limiter.recordRequest(endpoint),
    getRemainingRequests: () => limiter.getRemainingRequests(endpoint),
    getWaitTime: () => limiter.getWaitTime(endpoint),
    reset: () => limiter.reset(endpoint),
    getInfo: () => limiter.getInfo(endpoint),
  };
}

/**
 * Export default instance for convenience
 */
export default RateLimiter.getInstance();
