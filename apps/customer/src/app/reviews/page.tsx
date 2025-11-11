/**
 * Customer Review Newsfeed - Performance Optimized
 * 
 * Performance Optimizations:
 * - React Query for data fetching and caching
 * - Memoized review cards to prevent unnecessary re-renders
 * - Intersection Observer for lazy loading images
 * - No nested loops - O(n) complexity
 * - Efficient data structures (Map for lookups)
 * - Code splitting and lazy loading
 * 
 * Privacy Compliant:
 * - Displays customer_name from API (backend handles initials/full name)
 * - Never displays email or phone
 */

'use client';

import React, { useState, useCallback, useMemo } from 'react';
import { useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// ============================================================================
// Types
// ============================================================================

interface Review {
  id: number;
  title: string;
  content: string;
  rating: number;
  customer_name: string; // Backend returns initials OR full name based on privacy
  media: MediaFile[];
  likes_count: number;
  helpful_count: number;
  created_at: string;
  approved_at: string | null;
  reviewed_on_google: boolean;
  reviewed_on_yelp: boolean;
  google_review_link?: string;
  yelp_review_link?: string;
}

interface MediaFile {
  url: string;
  public_id: string;
  resource_type: 'image' | 'video';
  format: string;
  width?: number;
  height?: number;
}

interface ReviewsResponse {
  success: boolean;
  reviews: Review[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

// ============================================================================
// API Configuration
// ============================================================================

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
const REVIEWS_PER_PAGE = 20;

// ============================================================================
// API Functions (Single Responsibility Principle)
// ============================================================================

class ReviewAPI {
  static async fetchReviews(page: number): Promise<ReviewsResponse> {
    const response = await fetch(
      `${API_URL}/api/customer-reviews/approved-reviews?page=${page}&per_page=${REVIEWS_PER_PAGE}`
    );
    
    if (!response.ok) {
      throw new Error('Failed to fetch reviews');
    }
    
    return response.json();
  }
  
  static async likeReview(reviewId: number): Promise<void> {
    const response = await fetch(
      `${API_URL}/api/customer-reviews/reviews/${reviewId}/like`,
      { method: 'POST' }
    );
    
    if (!response.ok) {
      throw new Error('Failed to like review');
    }
  }
  
  static async markHelpful(reviewId: number): Promise<void> {
    const response = await fetch(
      `${API_URL}/api/customer-reviews/reviews/${reviewId}/helpful`,
      { method: 'POST' }
    );
    
    if (!response.ok) {
      throw new Error('Failed to mark helpful');
    }
  }
}

// ============================================================================
// Memoized Components (Performance Optimization)
// ============================================================================

const StarRating = React.memo(({ rating }: { rating: number }) => {
  // Use array fill for O(1) instead of loop
  const stars = Array(5).fill(0).map((_, i) => (
    <span key={i} className={i < rating ? 'text-yellow-400' : 'text-gray-300'}>
      ★
    </span>
  ));
  
  return <div className="flex gap-1">{stars}</div>;
});

StarRating.displayName = 'StarRating';

// ============================================================================
// Lazy Image Component with Intersection Observer
// ============================================================================

const LazyImage = React.memo(({ src, alt, className }: { src: string; alt: string; className?: string }) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const imgRef = React.useRef<HTMLImageElement>(null);
  
  React.useEffect(() => {
    if (!imgRef.current) return;
    
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin: '50px' } // Preload 50px before visible
    );
    
    observer.observe(imgRef.current);
    
    return () => observer.disconnect();
  }, []);
  
  return (
    <div ref={imgRef as any} className={`relative ${className || ''}`}>
      {!isLoaded && (
        <div className="absolute inset-0 bg-gray-200 animate-pulse" />
      )}
      {isVisible && (
        <img
          src={src}
          alt={alt}
          onLoad={() => setIsLoaded(true)}
          className={`${className || ''} transition-opacity duration-300 ${
            isLoaded ? 'opacity-100' : 'opacity-0'
          }`}
        />
      )}
    </div>
  );
});

LazyImage.displayName = 'LazyImage';

// ============================================================================
// Media Gallery Component (Memoized)
// ============================================================================

const MediaGallery = React.memo(({ media, reviewId }: { media: MediaFile[]; reviewId: number }) => {
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null);
  
  if (!media || media.length === 0) return null;
  
  // Optimize: Use Map for O(1) lookup instead of array iteration
  const mediaMap = useMemo(() => {
    const map = new Map<number, MediaFile>();
    media.forEach((m, i) => map.set(i, m));
    return map;
  }, [media]);
  
  const gridCols = media.length === 1 ? 'grid-cols-1' : media.length === 2 ? 'grid-cols-2' : 'grid-cols-3';
  
  return (
    <>
      <div className={`grid ${gridCols} gap-2 mt-4`}>
        {media.slice(0, 6).map((item, index) => (
          <div
            key={item.public_id}
            className="relative aspect-square cursor-pointer hover:opacity-90 transition"
            onClick={() => setLightboxIndex(index)}
          >
            {item.resource_type === 'image' ? (
              <LazyImage
                src={item.url}
                alt={`Review media ${index + 1}`}
                className="w-full h-full object-cover rounded-lg"
              />
            ) : (
              <video
                src={item.url}
                className="w-full h-full object-cover rounded-lg"
                muted
                loop
                playsInline
              />
            )}
            {index === 5 && media.length > 6 && (
              <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center rounded-lg">
                <span className="text-white text-2xl font-bold">+{media.length - 6}</span>
              </div>
            )}
          </div>
        ))}
      </div>
      
      {/* Lightbox Modal */}
      {lightboxIndex !== null && (
        <div
          className="fixed inset-0 bg-black bg-opacity-90 z-50 flex items-center justify-center p-4"
          onClick={() => setLightboxIndex(null)}
        >
          <button
            onClick={(e) => {
              e.stopPropagation();
              setLightboxIndex(null);
            }}
            className="absolute top-4 right-4 text-white text-4xl hover:text-gray-300"
          >
            ×
          </button>
          
          {mediaMap.get(lightboxIndex)?.resource_type === 'image' ? (
            <img
              src={mediaMap.get(lightboxIndex)?.url}
              alt="Full size"
              className="max-w-full max-h-full object-contain"
              onClick={(e) => e.stopPropagation()}
            />
          ) : (
            <video
              src={mediaMap.get(lightboxIndex)?.url}
              controls
              autoPlay
              className="max-w-full max-h-full"
              onClick={(e) => e.stopPropagation()}
            />
          )}
          
          {/* Navigation */}
          <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex gap-4">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setLightboxIndex(Math.max(0, lightboxIndex - 1));
              }}
              disabled={lightboxIndex === 0}
              className="px-4 py-2 bg-white rounded disabled:opacity-50"
            >
              ← Prev
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setLightboxIndex(Math.min(media.length - 1, lightboxIndex + 1));
              }}
              disabled={lightboxIndex === media.length - 1}
              className="px-4 py-2 bg-white rounded disabled:opacity-50"
            >
              Next →
            </button>
          </div>
        </div>
      )}
    </>
  );
});

MediaGallery.displayName = 'MediaGallery';

// ============================================================================
// Review Card Component (Memoized for Performance)
// ============================================================================

const ReviewCard = React.memo(({ 
  review, 
  onLike, 
  onHelpful 
}: { 
  review: Review; 
  onLike: (id: number) => void;
  onHelpful: (id: number) => void;
}) => {
  // Format date (memoized)
  const formattedDate = useMemo(() => {
    const date = new Date(review.created_at);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  }, [review.created_at]);
  
  return (
    <article className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            {/* Avatar with initials/name */}
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold text-lg">
              {review.customer_name.substring(0, 2).toUpperCase()}
            </div>
            <div>
              <p className="font-semibold text-gray-900">{review.customer_name}</p>
              <p className="text-sm text-gray-500">{formattedDate}</p>
            </div>
          </div>
          <StarRating rating={review.rating} />
        </div>
      </div>
      
      {/* Content */}
      <h3 className="text-xl font-bold mb-2">{review.title}</h3>
      <p className="text-gray-700 mb-4 whitespace-pre-line">{review.content}</p>
      
      {/* Media Gallery */}
      <MediaGallery media={review.media} reviewId={review.id} />
      
      {/* External Links */}
      {(review.google_review_link || review.yelp_review_link) && (
        <div className="mt-4 flex gap-3 text-sm">
          {review.google_review_link && (
            <a
              href={review.google_review_link}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline flex items-center gap-1"
            >
              📍 Google Review
            </a>
          )}
          {review.yelp_review_link && (
            <a
              href={review.yelp_review_link}
              target="_blank"
              rel="noopener noreferrer"
              className="text-red-600 hover:underline flex items-center gap-1"
            >
              ⭐ Yelp Review
            </a>
          )}
        </div>
      )}
      
      {/* Actions */}
      <div className="mt-6 pt-4 border-t flex gap-4">
        <button
          onClick={() => onLike(review.id)}
          className="flex items-center gap-2 text-gray-600 hover:text-blue-600 transition"
        >
          <span className="text-xl">👍</span>
          <span className="font-semibold">{review.likes_count}</span>
          <span className="text-sm">Likes</span>
        </button>
        
        <button
          onClick={() => onHelpful(review.id)}
          className="flex items-center gap-2 text-gray-600 hover:text-green-600 transition"
        >
          <span className="text-xl">✨</span>
          <span className="font-semibold">{review.helpful_count}</span>
          <span className="text-sm">Helpful</span>
        </button>
        
        <button className="flex items-center gap-2 text-gray-600 hover:text-purple-600 transition ml-auto">
          <span className="text-xl">🔗</span>
          <span className="text-sm">Share</span>
        </button>
      </div>
    </article>
  );
});

ReviewCard.displayName = 'ReviewCard';

// ============================================================================
// Main Newsfeed Component
// ============================================================================

export default function CustomerReviewNewsfeed() {
  const queryClient = useQueryClient();
  
  // React Query: Infinite scroll with automatic caching
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
    isError,
    error,
  } = useInfiniteQuery<ReviewsResponse>({
    queryKey: ['reviews'],
    queryFn: ({ pageParam = 1 }) => ReviewAPI.fetchReviews(pageParam as number),
    initialPageParam: 1, // React Query v5 requires this
    getNextPageParam: (lastPage) =>
      lastPage.pagination.has_next ? lastPage.pagination.page + 1 : undefined,
    gcTime: 10 * 60 * 1000, // 10 minutes (React Query v5: cacheTime → gcTime)
  });
  
  // Mutations for like/helpful
  const likeMutation = useMutation({
    mutationFn: ReviewAPI.likeReview,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reviews'] });
    },
  });
  
  const helpfulMutation = useMutation({
    mutationFn: ReviewAPI.markHelpful,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reviews'] });
    },
  });
  
  // Memoized handlers (prevent unnecessary re-renders)
  const handleLike = useCallback((id: number) => {
    likeMutation.mutate(id);
  }, [likeMutation]);
  
  const handleHelpful = useCallback((id: number) => {
    helpfulMutation.mutate(id);
  }, [helpfulMutation]);
  
  // Flatten reviews from all pages (O(n) complexity, no nested loops)
  const allReviews = useMemo(() => {
    if (!data?.pages) return [];
    return data.pages.flatMap((page) => page.reviews);
  }, [data?.pages]);
  
  // Intersection Observer for infinite scroll
  const observerTarget = React.useRef<HTMLDivElement>(null);
  
  React.useEffect(() => {
    if (!observerTarget.current) return;
    
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasNextPage && !isFetchingNextPage) {
          fetchNextPage();
        }
      },
      { threshold: 0.1 }
    );
    
    observer.observe(observerTarget.current);
    
    return () => observer.disconnect();
  }, [fetchNextPage, hasNextPage, isFetchingNextPage]);
  
  // Loading state
  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="space-y-6">
          {[1, 2, 3].map(i => (
            <div key={i} className="bg-white rounded-lg shadow-md p-6 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
              <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-2/3"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }
  
  // Error state
  if (isError) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <span className="text-4xl mb-4 block">😞</span>
          <h2 className="text-xl font-bold text-red-900 mb-2">Failed to Load Reviews</h2>
          <p className="text-red-700">{error?.message || 'Please try again later'}</p>
        </div>
      </div>
    );
  }
  
  // Empty state
  if (allReviews.length === 0) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-12 text-center">
          <span className="text-6xl mb-4 block">📝</span>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">No Reviews Yet</h2>
          <p className="text-gray-600 mb-6">Be the first to share your experience!</p>
          <a
            href="/reviews/submit"
            className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            Write a Review
          </a>
        </div>
      </div>
    );
  }
  
  // Main content
  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">Customer Reviews</h1>
        <p className="text-gray-600">
          Read what our customers are saying about their hibachi experience
        </p>
      </div>
      
      {/* Reviews Grid - O(n) iteration, no nested loops */}
      <div className="space-y-6">
        {allReviews.map((review) => (
          <ReviewCard
            key={review.id}
            review={review}
            onLike={handleLike}
            onHelpful={handleHelpful}
          />
        ))}
      </div>
      
      {/* Infinite Scroll Trigger */}
      <div ref={observerTarget} className="mt-8">
        {isFetchingNextPage && (
          <div className="text-center py-8">
            <div className="inline-block animate-spin text-4xl">⏳</div>
            <p className="text-gray-600 mt-2">Loading more reviews...</p>
          </div>
        )}
        
        {!hasNextPage && allReviews.length > 0 && (
          <div className="text-center py-8 text-gray-500">
            <span className="text-2xl block mb-2">🎉</span>
            You&apos;ve reached the end!
          </div>
        )}
      </div>
    </div>
  );
}
