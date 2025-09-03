'use client'

import Image from 'next/image'
import { useEffect, useRef, useState } from 'react'

interface ResponsiveImageProps {
  src: string
  alt: string
  priority?: boolean
  className?: string
  fill?: boolean
  sizes?: string
  quality?: number
  placeholder?: 'blur' | 'empty'
  onLoad?: () => void
  onError?: () => void
}

export default function ResponsiveImage({
  src,
  alt,
  priority = false,
  className = '',
  fill = false,
  sizes = '(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw',
  quality = 85,
  placeholder = 'empty',
  onLoad,
  onError
}: ResponsiveImageProps) {
  const [isLoaded, setIsLoaded] = useState(false)
  const [hasError, setHasError] = useState(false)
  const [isInView, setIsInView] = useState(priority)
  const imgRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (priority) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true)
          observer.disconnect()
        }
      },
      {
        threshold: 0.1,
        rootMargin: '50px 0px'
      }
    )

    const currentRef = imgRef.current
    if (currentRef) {
      observer.observe(currentRef)
    }

    return () => {
      if (currentRef) {
        observer.unobserve(currentRef)
      }
    }
  }, [priority])

  const handleLoad = () => {
    setIsLoaded(true)
    onLoad?.()
  }

  const handleError = () => {
    setHasError(true)
    onError?.()
  }

  // Determine optimal sizes based on layout
  const responsiveSizes =
    sizes ||
    `
    (max-width: 320px) 320px,
    (max-width: 640px) 640px,
    (max-width: 768px) 768px,
    (max-width: 1024px) 1024px,
    (max-width: 1280px) 1280px,
    1536px
  `

  return (
    <div
      ref={imgRef}
      className={`responsive-image-container ${className}`}
      style={{
        position: fill ? 'absolute' : 'relative',
        width: fill ? '100%' : 'auto',
        height: fill ? '100%' : 'auto'
      }}
    >
      {/* Loading skeleton */}
      {!isLoaded && !hasError && (
        <div className="responsive-image-skeleton">
          <div className="shimmer-effect" />
        </div>
      )}

      {/* Error state */}
      {hasError && (
        <div className="responsive-image-error">
          <div className="error-icon">⚠️</div>
          <span>Image failed to load</span>
        </div>
      )}

      {/* Actual image */}
      {isInView && !hasError && (
        <Image
          src={src}
          alt={alt}
          fill={fill}
          width={fill ? undefined : 800}
          height={fill ? undefined : 600}
          sizes={responsiveSizes}
          quality={quality}
          priority={priority}
          placeholder={placeholder}
          className={`responsive-image ${isLoaded ? 'loaded' : 'loading'}`}
          onLoad={handleLoad}
          onError={handleError}
          style={{
            objectFit: 'cover',
            transition: 'opacity 0.3s ease-in-out'
          }}
        />
      )}

      <style jsx>{`
        .responsive-image-container {
          overflow: hidden;
          border-radius: 12px;
          background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
        }

        .responsive-image-skeleton {
          width: 100%;
          height: 100%;
          min-height: 200px;
          position: relative;
          background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
          overflow: hidden;
        }

        .shimmer-effect {
          position: absolute;
          top: 0;
          left: -100%;
          width: 100%;
          height: 100%;
          background: linear-gradient(
            90deg,
            transparent 0%,
            rgba(255, 255, 255, 0.4) 50%,
            transparent 100%
          );
          animation: shimmer 1.5s infinite ease-in-out;
        }

        @keyframes shimmer {
          0% {
            left: -100%;
          }
          100% {
            left: 100%;
          }
        }

        .responsive-image-error {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          width: 100%;
          height: 200px;
          background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
          color: #dc2626;
          border-radius: 12px;
          gap: 8px;
        }

        .error-icon {
          font-size: 2rem;
        }

        .responsive-image {
          opacity: 0;
          transition: opacity 0.3s ease-in-out;
        }

        .responsive-image.loaded {
          opacity: 1;
        }

        @media (prefers-reduced-motion: reduce) {
          .shimmer-effect {
            animation: none;
          }
          .responsive-image {
            transition: none;
          }
        }

        /* Responsive breakpoints */
        @media (max-width: 640px) {
          .responsive-image-container {
            border-radius: 8px;
          }
          .responsive-image-skeleton {
            min-height: 160px;
          }
        }

        @media (max-width: 480px) {
          .responsive-image-container {
            border-radius: 6px;
          }
          .responsive-image-skeleton {
            min-height: 140px;
          }
        }
      `}</style>
    </div>
  )
}
