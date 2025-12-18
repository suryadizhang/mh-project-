/**
 * Image Optimization Utilities
 *
 * Enterprise-grade image optimization for Core Web Vitals improvement.
 * Addresses the 289 KiB potential savings identified in Lighthouse.
 */

import { IMAGE_CONFIG } from './performanceConfig';

/**
 * Image priority levels for loading strategy
 */
export type ImagePriority = 'critical' | 'high' | 'normal' | 'low';

/**
 * Generate optimized image props for Next.js Image component
 */
export interface OptimizedImageConfig {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  priority?: ImagePriority;
  quality?: number;
  fill?: boolean;
  sizes?: string;
  className?: string;
}

/**
 * Generate responsive sizes attribute based on layout
 */
export function generateSizes(
  layout: 'full' | 'half' | 'third' | 'quarter' | 'custom',
  customSizes?: string,
): string {
  if (layout === 'custom' && customSizes) {
    return customSizes;
  }

  switch (layout) {
    case 'full':
      return '100vw';
    case 'half':
      return '(max-width: 768px) 100vw, 50vw';
    case 'third':
      return '(max-width: 768px) 100vw, (max-width: 1024px) 50vw, 33vw';
    case 'quarter':
      return '(max-width: 768px) 50vw, (max-width: 1024px) 33vw, 25vw';
    default:
      return '100vw';
  }
}

/**
 * Get loading strategy based on priority
 */
export function getLoadingStrategy(priority: ImagePriority): {
  loading: 'eager' | 'lazy';
  priority: boolean;
  fetchPriority: 'high' | 'low' | 'auto';
} {
  switch (priority) {
    case 'critical':
      return { loading: 'eager', priority: true, fetchPriority: 'high' };
    case 'high':
      return { loading: 'eager', priority: false, fetchPriority: 'high' };
    case 'normal':
      return { loading: 'lazy', priority: false, fetchPriority: 'auto' };
    case 'low':
      return { loading: 'lazy', priority: false, fetchPriority: 'low' };
    default:
      return { loading: 'lazy', priority: false, fetchPriority: 'auto' };
  }
}

/**
 * Get quality setting based on image type
 */
export function getQualitySetting(type: 'hero' | 'content' | 'thumbnail'): number {
  return IMAGE_CONFIG.quality[type];
}

/**
 * Generate blur placeholder data URL
 * For use with placeholder="blur" in Next.js Image
 */
export function generateBlurPlaceholder(width: number = 10, height: number = 10): string {
  // Simple gray blur placeholder
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}">
    <filter id="b" color-interpolation-filters="sRGB">
      <feGaussianBlur stdDeviation="20"/>
    </filter>
    <rect width="100%" height="100%" fill="#e5e7eb" filter="url(#b)"/>
  </svg>`;

  const base64 = typeof window !== 'undefined' ? btoa(svg) : Buffer.from(svg).toString('base64');

  return `data:image/svg+xml;base64,${base64}`;
}

/**
 * Calculate aspect ratio for responsive images
 */
export function calculateAspectRatio(width: number, height: number): string {
  const gcd = (a: number, b: number): number => (b === 0 ? a : gcd(b, a % b));
  const divisor = gcd(width, height);
  return `${width / divisor}/${height / divisor}`;
}

/**
 * Preload critical images
 * Call this in _document.tsx or layout.tsx for LCP images
 */
export function getCriticalImagePreloadLinks(images: string[]): Array<{
  rel: string;
  href: string;
  as: string;
  type: string;
  fetchPriority: string;
}> {
  return images.map((src) => ({
    rel: 'preload',
    href: src,
    as: 'image',
    type: src.endsWith('.webp') ? 'image/webp' : 'image/jpeg',
    fetchPriority: 'high',
  }));
}

/**
 * Video optimization configuration for hero videos
 */
export const VIDEO_CONFIG = {
  // Poster image for video (shown before video loads)
  posterQuality: 75,

  // Video loading strategy
  preload: 'metadata' as const, // Only load metadata initially

  // Lazy load video when approaching viewport
  lazyLoadThreshold: '200px',

  // Reduce video quality on slow connections
  adaptiveQuality: true,
} as const;

/**
 * Check if user prefers reduced motion
 */
export function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined') return false;
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/**
 * Check connection quality for adaptive loading
 */
export function getConnectionQuality(): 'fast' | 'slow' | 'unknown' {
  if (typeof navigator === 'undefined') return 'unknown';

  const connection = (navigator as any).connection;
  if (!connection) return 'unknown';

  const { effectiveType, saveData } = connection;

  if (saveData) return 'slow';
  if (effectiveType === '4g') return 'fast';
  if (effectiveType === '3g' || effectiveType === '2g' || effectiveType === 'slow-2g') {
    return 'slow';
  }

  return 'unknown';
}
