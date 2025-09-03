import Image from 'next/image'
import { useState, useRef, useEffect } from 'react'

interface LazyBlogImageProps {
  src: string
  alt: string
  width: number
  height: number
  className?: string
  priority?: boolean
  onLoad?: () => void
  onError?: () => void
  fallbackSrc?: string
  quality?: number
  sizes?: string
}

export default function LazyBlogImage({
  src,
  alt,
  width,
  height,
  className = '',
  priority = false,
  onLoad,
  onError,
  fallbackSrc,
  quality = 85,
  sizes = '(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw'
}: LazyBlogImageProps) {
  const [isLoading, setIsLoading] = useState(true)
  const [hasError, setHasError] = useState(false)
  const [isInView, setIsInView] = useState(false)
  const imgRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true)
          observer.unobserve(entry.target)
        }
      },
      {
        threshold: 0.1,
        rootMargin: '50px'
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
  }, [])

  const handleLoad = () => {
    setIsLoading(false)
    onLoad?.()
  }

  const handleError = () => {
    setHasError(true)
    setIsLoading(false)
    onError?.()
  }

  const shouldLoad = priority || isInView

  return (
    <div ref={imgRef} className={`relative overflow-hidden ${className}`} style={{ width, height }}>
      {/* Loading Skeleton */}
      {isLoading && shouldLoad && (
        <div className="absolute inset-0 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 animate-pulse">
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/60 to-transparent animate-shimmer"></div>
        </div>
      )}

      {/* Placeholder when not in view */}
      {!shouldLoad && (
        <div className="absolute inset-0 bg-gradient-to-br from-orange-100 to-red-100 flex items-center justify-center">
          <div className="text-gray-400 text-center">
            <div className="w-8 h-8 mx-auto mb-2 opacity-50">🍱</div>
            <div className="text-xs font-medium">Loading...</div>
          </div>
        </div>
      )}

      {/* Actual Image */}
      {shouldLoad && (
        <Image
          src={hasError && fallbackSrc ? fallbackSrc : src}
          alt={alt}
          width={width}
          height={height}
          className={`
            w-full h-full object-cover transition-all duration-700 ease-out
            ${isLoading ? 'opacity-0 scale-105' : 'opacity-100 scale-100'}
            ${hasError ? 'filter grayscale' : ''}
          `}
          onLoad={handleLoad}
          onError={handleError}
          priority={priority}
          loading={priority ? 'eager' : 'lazy'}
          quality={quality}
          sizes={sizes}
        />
      )}

      {/* Error State */}
      {hasError && !fallbackSrc && (
        <div className="absolute inset-0 bg-gradient-to-br from-red-50 to-orange-50 flex items-center justify-center">
          <div className="text-gray-500 text-center">
            <div className="w-8 h-8 mx-auto mb-2 opacity-50">⚠️</div>
            <div className="text-xs font-medium">Image unavailable</div>
          </div>
        </div>
      )}

      {/* Progressive Enhancement Overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/20 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
    </div>
  )
}
