/**
 * FAQs Page Loading State
 *
 * Displays while FAQs are loading.
 */

import { Skeleton } from '@/components/ui/Skeleton';

function FAQItemSkeleton() {
  return (
    <div className="rounded-lg border bg-white p-4">
      <div className="flex items-center justify-between">
        <Skeleton className="h-5 w-3/4" />
        <Skeleton className="h-5 w-5 rounded" />
      </div>
    </div>
  );
}

export default function FAQsLoading() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section Skeleton */}
      <div className="bg-gradient-to-r from-red-600 to-red-700 px-4 py-16 text-white">
        <div className="mx-auto max-w-4xl text-center">
          <div className="mx-auto mb-4 h-10 w-64 animate-pulse rounded bg-white/20" />
          <div className="mx-auto h-6 w-80 animate-pulse rounded bg-white/20" />
        </div>
      </div>

      {/* Search Bar */}
      <div className="mx-auto -mt-6 max-w-2xl px-4">
        <Skeleton className="h-14 w-full rounded-lg shadow-lg" />
      </div>

      {/* FAQ Categories */}
      <div className="mx-auto max-w-4xl px-4 py-12">
        {/* Category Tabs */}
        <div className="mb-8 flex gap-4 overflow-x-auto">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-32 flex-shrink-0 rounded-full" />
          ))}
        </div>

        {/* FAQ Items */}
        <div className="space-y-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <FAQItemSkeleton key={i} />
          ))}
        </div>
      </div>
    </div>
  );
}
