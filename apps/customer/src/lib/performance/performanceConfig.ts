/**
 * Performance Configuration
 *
 * Centralized configuration for performance optimizations.
 * Based on Core Web Vitals targets:
 * - LCP: < 2.5s (currently 9.5s - CRITICAL)
 * - FID/TBT: < 200ms (currently 3,170ms - CRITICAL)
 * - CLS: < 0.1 (currently 0 - GOOD)
 */

/**
 * Core Web Vitals Thresholds
 * @see https://web.dev/vitals/
 */
export const CORE_WEB_VITALS = {
  LCP: {
    good: 2500, // < 2.5s
    needsWork: 4000, // < 4s
    poor: 4001, // > 4s
  },
  FID: {
    good: 100, // < 100ms
    needsWork: 300, // < 300ms
    poor: 301, // > 300ms
  },
  CLS: {
    good: 0.1, // < 0.1
    needsWork: 0.25, // < 0.25
    poor: 0.26, // > 0.25
  },
  TBT: {
    good: 200, // < 200ms
    needsWork: 600, // < 600ms
    poor: 601, // > 600ms
  },
} as const;

/**
 * Image optimization configuration
 */
export const IMAGE_CONFIG = {
  // Device sizes for responsive images
  deviceSizes: [320, 420, 640, 768, 1024, 1200, 1536] as const,

  // Image sizes for srcset
  imageSizes: [16, 32, 48, 64, 96, 128, 256, 384] as const,

  // Supported formats in order of preference
  formats: ['image/avif', 'image/webp'] as const,

  // Minimum cache TTL (1 week)
  minimumCacheTTL: 60 * 60 * 24 * 7,

  // Quality settings by use case
  quality: {
    hero: 85, // High quality for hero images
    content: 75, // Standard quality for content
    thumbnail: 60, // Lower quality for thumbnails
  },

  // Lazy loading intersection observer options
  lazyLoadConfig: {
    rootMargin: '200px 0px',
    threshold: 0.01,
  },
} as const;

/**
 * Lazy loading priority levels
 */
export const LAZY_LOAD_PRIORITY = {
  // Load immediately with page - LCP elements
  CRITICAL: 'critical',
  // Load after initial paint - above fold
  HIGH: 'high',
  // Load when approaching viewport
  NORMAL: 'normal',
  // Load only when in viewport
  LOW: 'low',
} as const;

/**
 * Cache headers configuration
 */
export const CACHE_CONFIG = {
  // Static assets (images, fonts, etc.)
  static: {
    maxAge: 31536000, // 1 year
    staleWhileRevalidate: 86400, // 1 day
    immutable: true,
  },
  // Dynamic content
  dynamic: {
    maxAge: 0,
    staleWhileRevalidate: 60,
    immutable: false,
  },
  // API responses
  api: {
    maxAge: 0,
    staleWhileRevalidate: 30,
    immutable: false,
  },
} as const;

/**
 * Font optimization configuration
 */
export const FONT_CONFIG = {
  display: 'swap' as const,
  preload: [
    // Critical fonts loaded first
    { family: 'Poppins', weights: ['400', '600', '700'] },
    { family: 'Inter', weights: ['400', '500'] },
  ],
} as const;

/**
 * Resource hints configuration
 */
export const RESOURCE_HINTS = {
  // Domains to preconnect
  preconnect: [
    'https://fonts.googleapis.com',
    'https://fonts.gstatic.com',
    'https://www.googletagmanager.com',
  ],
  // Domains to dns-prefetch
  dnsPrefetch: ['https://api.stripe.com', 'https://www.google-analytics.com'],
} as const;

/**
 * Bundle splitting configuration
 * Components that should be dynamically imported
 */
export const DYNAMIC_IMPORT_CONFIG = {
  // Heavy components (>50KB) - always lazy load
  heavy: [
    'ChatWidget',
    'PaymentForm',
    'DatePicker',
    'QuoteCalculator',
    'ValuePropositionSection',
    'BookingForm',
    'CustomerReviewForm',
  ],
  // Medium components (20-50KB) - lazy load below fold
  medium: ['TestimonialsSection', 'Footer', 'AlternativePaymentOptions'],
  // Light components (<20KB) - can be included in bundle
  light: ['Button', 'Navbar', 'BackToTopButton'],
} as const;

export type LazyLoadPriority = (typeof LAZY_LOAD_PRIORITY)[keyof typeof LAZY_LOAD_PRIORITY];
