'use client';

import Image from 'next/image';
import { useEffect, useState } from 'react';

/**
 * Hero video component with progressive enhancement
 * - Server renders the poster image immediately (for instant LCP)
 * - Client hydrates and swaps to video after idle
 */
export function HeroVideoLazy() {
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
        // This renders on server AND client initially - instant LCP
        <Image
          className="hero-media hero-video"
          src="/images/hero-poster.jpg"
          alt=""
          width={1920}
          height={533}
          priority
          quality={75}
          sizes="100vw"
          style={{ backgroundColor: '#000', objectFit: 'cover' }}
          aria-hidden="true"
        />
      )}
    </div>
  );
}
