/**
 * Server-rendered hero image for instant LCP
 * CRITICAL: Uses native <img> tag, NOT next/image
 *
 * Why native img instead of next/image?
 * - next/image requires JavaScript for srcset selection
 * - next/image has hydration overhead
 * - For LCP element, raw <img> with preload is faster
 * - The image is already optimized via FFmpeg (1.2MB, 720p)
 */
export function HeroImage() {
  return (
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
  );
}
