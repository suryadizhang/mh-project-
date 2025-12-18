/**
 * Server-rendered hero image for instant LCP
 * CRITICAL: Uses native <picture> with WebP, NOT next/image
 *
 * Why native picture/img instead of next/image?
 * - next/image requires JavaScript for srcset selection
 * - next/image has hydration overhead
 * - For LCP element, raw <picture> with preload is faster
 * - WebP is 43KB vs JPEG 91KB (52% smaller)
 */
export function HeroImage() {
  return (
    <picture>
      <source srcSet="/images/hero-poster.webp" type="image/webp" />
      <img
        className="hero-media"
        src="/images/hero-poster.jpg"
        alt=""
        width={1920}
        height={533}
        decoding="sync"
        fetchPriority="high"
        style={{
          backgroundColor: '#000',
          objectFit: 'cover',
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
        }}
        aria-hidden="true"
      />
    </picture>
  );
}
