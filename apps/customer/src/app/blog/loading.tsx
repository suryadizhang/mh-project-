/**
 * Blog Page Loading State
 *
 * Displays while blog posts are loading.
 */

import { Skeleton, SkeletonText } from '@/components/ui/Skeleton';

function BlogPostSkeleton() {
  return (
    <div className="overflow-hidden rounded-lg border bg-white shadow-sm">
      <Skeleton className="h-48 w-full" />
      <div className="p-4">
        <Skeleton className="mb-2 h-3 w-24" />
        <Skeleton className="mb-3 h-6 w-full" />
        <SkeletonText lines={2} />
        <div className="mt-4 flex items-center justify-between">
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-8 w-24 rounded" />
        </div>
      </div>
    </div>
  );
}

export default function BlogLoading() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section Skeleton */}
      <div className="bg-gradient-to-r from-red-600 to-red-700 px-4 py-16 text-white">
        <div className="mx-auto max-w-4xl text-center">
          <div className="mx-auto mb-4 h-10 w-40 animate-pulse rounded bg-white/20" />
          <div className="mx-auto h-6 w-96 animate-pulse rounded bg-white/20" />
        </div>
      </div>

      {/* Category Filter */}
      <div className="border-b bg-white px-4 py-4">
        <div className="mx-auto flex max-w-6xl gap-4 overflow-x-auto">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-8 w-24 flex-shrink-0 rounded-full" />
          ))}
        </div>
      </div>

      {/* Blog Grid */}
      <div className="mx-auto max-w-6xl px-4 py-12">
        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <BlogPostSkeleton key={i} />
          ))}
        </div>
      </div>
    </div>
  );
}
