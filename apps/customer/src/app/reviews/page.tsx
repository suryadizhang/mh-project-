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
      `${API_URL}/api/customer-reviews/approved-reviews?page=${page}&per_page=${REVIEWS_PER_PAGE}`,
    );

    if (!response.ok) {
      throw new Error('Failed to fetch reviews');
    }

    return response.json();
  }

  static async likeReview(reviewId: number): Promise<void> {
    const response = await fetch(`${API_URL}/api/customer-reviews/reviews/${reviewId}/like`, {
      method: 'POST',
    });

    if (!response.ok) {
      throw new Error('Failed to like review');
    }
  }

  static async markHelpful(reviewId: number): Promise<void> {
    const response = await fetch(`${API_URL}/api/customer-reviews/reviews/${reviewId}/helpful`, {
      method: 'POST',
    });

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
  const stars = Array(5)
    .fill(0)
    .map((_, i) => (
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

const LazyImage = React.memo(
  ({ src, alt, className }: { src: string; alt: string; className?: string }) => {
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
        { rootMargin: '50px' }, // Preload 50px before visible
      );

      observer.observe(imgRef.current);

      return () => observer.disconnect();
    }, []);

    return (
      <div ref={imgRef as any} className={`relative ${className || ''}`}>
        {!isLoaded && <div className="absolute inset-0 animate-pulse bg-gray-200" />}
        {isVisible && (
          <img
            src={src}
            alt={alt}
            onLoad={() => setIsLoaded(true)}
            className={`${className || ''} transition-opacity duration-300 ${isLoaded ? 'opacity-100' : 'opacity-0'
              }`}
          />
        )}
      </div>
    );
  },
);

LazyImage.displayName = 'LazyImage';

// ============================================================================
// Media Gallery Component (Memoized)
// ============================================================================

const MediaGallery = React.memo(({ media, reviewId }: { media: MediaFile[]; reviewId: number }) => {
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null);

  // Optimize: Use Map for O(1) lookup instead of array iteration
  // Must be called before any conditional returns (React Hooks rule)
  const mediaMap = useMemo(() => {
    if (!media || media.length === 0) return new Map();
    const map = new Map<number, MediaFile>();
    media.forEach((m, i) => map.set(i, m));
    return map;
  }, [media]);

  if (!media || media.length === 0) return null;

  const gridCols =
    media.length === 1 ? 'grid-cols-1' : media.length === 2 ? 'grid-cols-2' : 'grid-cols-3';

  return (
    <>
      <div className={`grid ${gridCols} mt-4 gap-2`}>
        {media.slice(0, 6).map((item, index) => (
          <div
            key={item.public_id}
            className="relative aspect-square cursor-pointer transition hover:opacity-90"
            onClick={() => setLightboxIndex(index)}
          >
            {item.resource_type === 'image' ? (
              <LazyImage
                src={item.url}
                alt={`Review media ${index + 1}`}
                className="h-full w-full rounded-lg object-cover"
              />
            ) : (
              <video
                src={item.url}
                className="h-full w-full rounded-lg object-cover"
                muted
                loop
                playsInline
              />
            )}
            {index === 5 && media.length > 6 && (
              <div className="bg-opacity-50 absolute inset-0 flex items-center justify-center rounded-lg bg-black">
                <span className="text-2xl font-bold text-white">+{media.length - 6}</span>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Lightbox Modal */}
      {lightboxIndex !== null && (
        <div
          className="bg-opacity-90 fixed inset-0 z-50 flex items-center justify-center bg-black p-4"
          onClick={() => setLightboxIndex(null)}
        >
          <button
            onClick={(e) => {
              e.stopPropagation();
              setLightboxIndex(null);
            }}
            className="absolute top-4 right-4 text-4xl text-white hover:text-gray-300"
          >
            ×
          </button>

          {mediaMap.get(lightboxIndex)?.resource_type === 'image' ? (
            <img
              src={mediaMap.get(lightboxIndex)?.url}
              alt="Full size"
              className="max-h-full max-w-full object-contain"
              onClick={(e) => e.stopPropagation()}
            />
          ) : (
            <video
              src={mediaMap.get(lightboxIndex)?.url}
              controls
              autoPlay
              className="max-h-full max-w-full"
              onClick={(e) => e.stopPropagation()}
            />
          )}

          {/* Navigation */}
          <div className="absolute bottom-4 left-1/2 flex -translate-x-1/2 transform gap-4">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setLightboxIndex(Math.max(0, lightboxIndex - 1));
              }}
              disabled={lightboxIndex === 0}
              className="rounded bg-white px-4 py-2 disabled:opacity-50"
            >
              ← Prev
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setLightboxIndex(Math.min(media.length - 1, lightboxIndex + 1));
              }}
              disabled={lightboxIndex === media.length - 1}
              className="rounded bg-white px-4 py-2 disabled:opacity-50"
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

const ReviewCard = React.memo(
  ({
    review,
    onLike,
    onHelpful,
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
        month: 'short',
        day: 'numeric',
      });
    }, [review.created_at]);

    return (
      <article className="rounded-lg bg-white p-4 shadow-md transition hover:shadow-lg">
        {/* Header */}
        <div className="mb-3 flex items-start justify-between">
          <div className="flex-1">
            <div className="mb-1 flex items-center gap-2">
              {/* Avatar with initials/name */}
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-purple-500 text-sm font-bold text-white">
                {review.customer_name.substring(0, 2).toUpperCase()}
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-900">{review.customer_name}</p>
                <p className="text-xs text-gray-500">{formattedDate}</p>
              </div>
              <div className="ml-2">
                <StarRating rating={review.rating} />
              </div>
            </div>
          </div>
        </div>

        {/* Content */}
        <h3 className="mb-1 text-lg font-bold">{review.title}</h3>
        <p className="mb-3 text-sm whitespace-pre-line text-gray-700">{review.content}</p>

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
                className="flex items-center gap-1 text-blue-600 hover:underline"
              >
                📍 Google Review
              </a>
            )}
            {review.yelp_review_link && (
              <a
                href={review.yelp_review_link}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-red-600 hover:underline"
              >
                ⭐ Yelp Review
              </a>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="mt-4 flex gap-3 border-t pt-3">
          <button
            onClick={() => onLike(review.id)}
            className="flex items-center gap-1 text-sm text-gray-600 transition hover:text-blue-600"
          >
            <span>👍</span>
            <span className="font-semibold">{review.likes_count}</span>
          </button>

          <button
            onClick={() => onHelpful(review.id)}
            className="flex items-center gap-1 text-sm text-gray-600 transition hover:text-green-600"
          >
            <span>✨</span>
            <span className="font-semibold">{review.helpful_count}</span>
          </button>

          <button className="ml-auto flex items-center gap-1 text-sm text-gray-600 transition hover:text-purple-600">
            <span>🔗</span>
            <span>Share</span>
          </button>
        </div>
      </article>
    );
  },
);

ReviewCard.displayName = 'ReviewCard';

// ============================================================================
// Main Newsfeed Component
// ============================================================================

export default function CustomerReviewNewsfeed() {
  const queryClient = useQueryClient();

  // React Query: Infinite scroll with automatic caching
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage, isLoading, isError, error } =
    useInfiniteQuery<ReviewsResponse>({
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
  const handleLike = useCallback(
    (id: number) => {
      likeMutation.mutate(id);
    },
    [likeMutation],
  );

  const handleHelpful = useCallback(
    (id: number) => {
      helpfulMutation.mutate(id);
    },
    [helpfulMutation],
  );

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
      { threshold: 0.1 },
    );

    observer.observe(observerTarget.current);

    return () => observer.disconnect();
  }, [fetchNextPage, hasNextPage, isFetchingNextPage]);

  // Loading state
  if (isLoading) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-4">
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse rounded-lg bg-white p-4 shadow-md">
              <div className="mb-3 h-3 w-3/4 rounded bg-gray-200"></div>
              <div className="mb-2 h-3 w-full rounded bg-gray-200"></div>
              <div className="h-3 w-2/3 rounded bg-gray-200"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Error state
  if (isError) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-4">
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-center">
          <span className="mb-2 block text-2xl">😞</span>
          <h2 className="mb-1 text-lg font-bold text-red-900">Failed to Load Reviews</h2>
          <p className="text-sm text-red-700">{error?.message || 'Please try again later'}</p>
        </div>
      </div>
    );
  }

  // Empty state
  if (allReviews.length === 0) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-4">
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-8 text-center">
          <span className="mb-2 block text-4xl">📝</span>
          <h2 className="mb-1 text-xl font-bold text-gray-900">No Reviews Yet</h2>
          <p className="mb-4 text-sm text-gray-600">Be the first to share your experience!</p>
          <a
            href="/reviews/submit"
            className="inline-block rounded-lg bg-blue-600 px-5 py-2 text-sm text-white transition hover:bg-blue-700"
          >
            Write a Review
          </a>
        </div>
      </div>
    );
  }

  // Main content
  return (
    <div className="mx-auto max-w-4xl px-4 py-4">
      {/* Header */}
      <div className="mb-5">
        <h1 className="mb-1 text-2xl font-bold text-gray-900">Customer Reviews</h1>
        <p className="text-sm text-gray-600">
          What our customers say about their hibachi experience
        </p>
      </div>

      {/* Reviews Grid - O(n) iteration, no nested loops */}
      <div className="space-y-4">
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
          <div className="py-8 text-center">
            <div className="inline-block animate-spin text-4xl">⏳</div>
            <p className="mt-2 text-gray-600">Loading more reviews...</p>
          </div>
        )}

        {!hasNextPage && allReviews.length > 0 && (
          <div className="py-8 text-center text-gray-500">
            <span className="mb-2 block text-2xl">🎉</span>
            You&apos;ve reached the end!
          </div>
        )}
      </div>
    </div>
  );
}
