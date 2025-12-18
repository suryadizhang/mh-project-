'use client';

import { useEffect, useState } from 'react';

/**
 * Lazy-loaded hero video component
 * Shows poster immediately (for fast LCP), loads video after hydration
 */
export function HeroVideoLazy() {
  const [shouldLoadVideo, setShouldLoadVideo] = useState(false);

  useEffect(() => {
    // Delay video loading until after LCP (poster shows first)
    // Use requestIdleCallback if available, otherwise setTimeout
    if ('requestIdleCallback' in window) {
      window.requestIdleCallback(() => setShouldLoadVideo(true), { timeout: 2000 });
    } else {
      // Delay video loading to prioritize LCP
      const timer = setTimeout(() => setShouldLoadVideo(true), 1000);
      return () => clearTimeout(timer);
    }
  }, []);

  return (
    <div className="hero-media-container">
      <div className="hero-media-overlay"></div>
      {shouldLoadVideo ? (
        <video
          className="hero-media hero-video"
          width="1920"
          height="533"
          autoPlay
          muted
          loop
          playsInline
          preload="none"
          poster="/images/hero-poster.jpg"
          style={{ backgroundColor: '#000' }}
          aria-hidden="true"
        >
          <source src="/videos/hero_video.mp4" type="video/mp4" />
          <track kind="captions" src="/videos/hero_video.vtt" srcLang="en" label="English" />
        </video>
      ) : (
        // Show poster as static image until video loads
        /* eslint-disable-next-line jsx-a11y/alt-text */
        <img
          className="hero-media hero-video"
          src="/images/hero-poster.jpg"
          alt=""
          width="1920"
          height="533"
          style={{ backgroundColor: '#000', objectFit: 'cover' }}
          aria-hidden="true"
          fetchPriority="high"
        />
      )}
    </div>
  );
}
