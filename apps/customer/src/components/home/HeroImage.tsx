import Image from 'next/image';

/**
 * Server-rendered hero image for instant LCP
 * This is a SERVER COMPONENT - renders immediately in HTML
 * No JavaScript required for the image to appear
 */
export function HeroImage() {
  return (
    <Image
      className="hero-media"
      src="/images/hero-poster.jpg"
      alt=""
      width={1920}
      height={533}
      priority
      quality={75}
      sizes="100vw"
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
