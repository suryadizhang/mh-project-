'use client';

import { useEffect, useState } from 'react';

/**
 * Client component that swaps in video AFTER hydration
 * The poster image is rendered by the parent server component for instant LCP
 * This component only handles the video enhancement - not the initial image
 */
export function HeroVideoOverlay() {
  const [shouldLoadVideo, setShouldLoadVideo] = useState(false);

  useEffect(() => {
    // Delay video loading until after LCP and idle time
    if ('requestIdleCallback' in window) {
      window.requestIdleCallback(() => setShouldLoadVideo(true), { timeout: 3000 });
    } else {
      const timer = setTimeout(() => setShouldLoadVideo(true), 2000);
      return () => clearTimeout(timer);
    }
  }, []);

  if (!shouldLoadVideo) {
    return null; // Server-rendered image shows underneath
  }

  return (
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
      style={{
        backgroundColor: '#000',
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        objectFit: 'cover',
        zIndex: 1,
      }}
      aria-hidden="true"
    >
      <source src="/videos/hero_video.mp4" type="video/mp4" />
      <track kind="captions" src="/videos/hero_video.vtt" srcLang="en" label="English" />
    </video>
  );
}

// Legacy export for backwards compatibility during migration
export { HeroVideoOverlay as HeroVideoLazy };
