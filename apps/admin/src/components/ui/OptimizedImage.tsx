'use client';

import Image from 'next/image';
import { useState } from 'react';
import { ImageIcon } from 'lucide-react';

interface OptimizedImageProps {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  className?: string;
  priority?: boolean;
  fill?: boolean;
  sizes?: string;
  quality?: number;
  placeholder?: 'blur' | 'empty';
  blurDataURL?: string;
}

export default function OptimizedImage({
  src,
  alt,
  width,
  height,
  className = '',
  priority = false,
  fill = false,
  sizes,
  quality = 85,
  placeholder = 'empty',
  blurDataURL,
}: OptimizedImageProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  // Generate blur placeholder if not provided
  const generateBlurDataURL = (w: number = 10, h: number = 10) => {
    return `data:image/svg+xml;base64,${Buffer.from(
      `<svg width="${w}" height="${h}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#f0f0f0"/>
      </svg>`
    ).toString('base64')}`;
  };

  const handleLoad = () => {
    setIsLoading(false);
  };

  const handleError = () => {
    setIsLoading(false);
    setHasError(true);
  };

  // Fallback image for errors
  if (hasError) {
    return (
      <div className={`image-error-fallback ${className}`}>
        <ImageIcon className="h-8 w-8 text-gray-400" />
        <span className="sr-only">{alt}</span>
      </div>
    );
  }

  const imageProps = {
    src,
    alt,
    className: `optimized-image ${isLoading ? 'loading' : 'loaded'
      } ${className}`,
    onLoad: handleLoad,
    onError: handleError,
    quality,
    priority,
    ...(placeholder === 'blur' && { placeholder: 'blur' as const }),
    ...(placeholder === 'blur' && {
      blurDataURL: blurDataURL || generateBlurDataURL(width, height),
    }),
    ...(sizes && { sizes }),
  };

  if (fill) {
    return <Image {...imageProps} alt={alt} fill />;
  }

  if (width && height) {
    return <Image {...imageProps} alt={alt} width={width} height={height} />;
  }

  // Default responsive image
  return (
    <Image
      {...imageProps}
      alt={alt}
      width={800}
      height={600}
      style={{ width: '100%', height: 'auto' }}
    />
  );
}

// Hero image component with optimization
export function HeroImage({
  src,
  alt,
  className = '',
}: {
  src: string;
  alt: string;
  className?: string;
}) {
  return (
    <OptimizedImage
      src={src}
      alt={alt}
      width={1920}
      height={1080}
      priority
      quality={90}
      className={`hero-image ${className}`}
      placeholder="blur"
      sizes="100vw"
    />
  );
}

// Card image component
export function CardImage({
  src,
  alt,
  className = '',
}: {
  src: string;
  alt: string;
  className?: string;
}) {
  return (
    <OptimizedImage
      src={src}
      alt={alt}
      width={400}
      height={300}
      quality={80}
      className={`card-image ${className}`}
      placeholder="blur"
      sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
    />
  );
}

// Avatar/profile image component
export function AvatarImage({
  src,
  alt,
  size = 100,
  className = '',
}: {
  src: string;
  alt: string;
  size?: number;
  className?: string;
}) {
  return (
    <OptimizedImage
      src={src}
      alt={alt}
      width={size}
      height={size}
      quality={90}
      className={`avatar-image ${className}`}
      placeholder="blur"
    />
  );
}

// Gallery image component
export function GalleryImage({
  src,
  alt,
  className = '',
}: {
  src: string;
  alt: string;
  className?: string;
}) {
  return (
    <OptimizedImage
      src={src}
      alt={alt}
      width={600}
      height={400}
      quality={85}
      className={`gallery-image ${className}`}
      placeholder="blur"
      sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
    />
  );
}
