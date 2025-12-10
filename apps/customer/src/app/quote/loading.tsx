/**
 * Quote Page Loading State
 *
 * Displays while the quote calculator is loading.
 */

import { Skeleton, SkeletonInput } from '@/components/ui/Skeleton';

export default function QuoteLoading() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Hero Section Skeleton */}
      <div className="bg-gradient-to-r from-red-600 to-red-700 px-4 py-16 text-white">
        <div className="mx-auto max-w-4xl text-center">
          <div className="mx-auto mb-4 h-10 w-72 animate-pulse rounded bg-white/20" />
          <div className="mx-auto h-6 w-96 animate-pulse rounded bg-white/20" />
        </div>
      </div>

      {/* Quote Calculator */}
      <div className="mx-auto -mt-8 max-w-2xl px-4 pb-16">
        <div className="rounded-xl bg-white p-8 shadow-lg">
          <div className="mb-6 text-center">
            <Skeleton className="mx-auto mb-2 h-8 w-48" />
            <Skeleton className="mx-auto h-4 w-64" />
          </div>

          <div className="space-y-6">
            {/* Guest Count */}
            <div>
              <Skeleton className="mb-2 h-4 w-32" />
              <div className="flex items-center gap-4">
                <Skeleton className="h-12 w-12 rounded-full" />
                <Skeleton className="h-12 flex-1 rounded-lg" />
                <Skeleton className="h-12 w-12 rounded-full" />
              </div>
            </div>

            {/* Date Selection */}
            <SkeletonInput />

            {/* Address */}
            <SkeletonInput />

            {/* Price Display */}
            <div className="rounded-lg bg-gray-50 p-6">
              <Skeleton className="mx-auto mb-4 h-6 w-32" />
              <Skeleton className="mx-auto h-12 w-40" />
              <Skeleton className="mx-auto mt-2 h-4 w-48" />
            </div>

            {/* CTA Button */}
            <Skeleton className="h-14 w-full rounded-lg" />
          </div>
        </div>
      </div>
    </div>
  );
}
