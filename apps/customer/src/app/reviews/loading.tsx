/**
 * Reviews Page Loading State
 *
 * Displays while reviews are loading.
 */

import { Skeleton, SkeletonReviewCard } from '@/components/ui/Skeleton';

export default function ReviewsLoading() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section Skeleton */}
      <div className="bg-gradient-to-r from-red-600 to-red-700 px-4 py-16 text-white">
        <div className="mx-auto max-w-4xl text-center">
          <div className="mx-auto mb-4 h-10 w-56 animate-pulse rounded bg-white/20" />
          <div className="mx-auto mb-6 h-6 w-80 animate-pulse rounded bg-white/20" />
          {/* Stats */}
          <div className="flex justify-center gap-8">
            <div className="text-center">
              <div className="mx-auto mb-1 h-10 w-16 animate-pulse rounded bg-white/20" />
              <div className="mx-auto h-4 w-20 animate-pulse rounded bg-white/20" />
            </div>
            <div className="text-center">
              <div className="mx-auto mb-1 h-10 w-24 animate-pulse rounded bg-white/20" />
              <div className="mx-auto h-4 w-16 animate-pulse rounded bg-white/20" />
            </div>
          </div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="border-b bg-white px-4 py-4">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <div className="flex gap-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-8 w-20 rounded-full" />
            ))}
          </div>
          <Skeleton className="h-8 w-32 rounded" />
        </div>
      </div>

      {/* Reviews Grid */}
      <div className="mx-auto max-w-6xl px-4 py-12">
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 9 }).map((_, i) => (
            <SkeletonReviewCard key={i} />
          ))}
        </div>
      </div>
    </div>
  );
}
