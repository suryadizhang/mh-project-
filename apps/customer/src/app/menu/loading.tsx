/**
 * Menu Page Loading State
 *
 * Displays while the menu is loading.
 */

import { Skeleton, SkeletonMenuItem, SkeletonPageHeader } from '@/components/ui/Skeleton';

export default function MenuLoading() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section Skeleton */}
      <div className="bg-gradient-to-r from-red-600 to-red-700 px-4 py-20 text-white">
        <div className="mx-auto max-w-4xl text-center">
          <div className="mx-auto mb-4 h-12 w-48 animate-pulse rounded bg-white/20" />
          <div className="mx-auto h-6 w-80 animate-pulse rounded bg-white/20" />
        </div>
      </div>

      {/* Menu Content */}
      <div className="mx-auto max-w-6xl px-4 py-12">
        {/* Category Tabs Skeleton */}
        <div className="mb-8 flex gap-4 overflow-x-auto">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-28 flex-shrink-0 rounded-full" />
          ))}
        </div>

        {/* Menu Items Grid */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonMenuItem key={i} />
          ))}
        </div>
      </div>
    </div>
  );
}
