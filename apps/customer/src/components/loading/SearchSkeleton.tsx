/**
 * Skeleton loader for Search component (with fuse.js)
 * Shows while enhanced search is being lazy-loaded
 */

export default function SearchSkeleton() {
  return (
    <div className="space-y-4" aria-label="Loading search..." role="status">
      <span className="sr-only">Loading search...</span>

      {/* Search input skeleton */}
      <div className="relative">
        <div className="h-12 animate-pulse rounded-lg bg-gray-200 dark:bg-gray-700" />
        {/* Search icon placeholder */}
        <div className="absolute top-1/2 right-4 h-5 w-5 -translate-y-1/2 animate-pulse rounded bg-gray-300 dark:bg-gray-600" />
      </div>

      {/* Search filters skeleton */}
      <div className="flex flex-wrap gap-2">
        {[...Array(4)].map((_, i) => (
          <div
            key={i}
            className="h-8 w-20 animate-pulse rounded-full bg-gray-200 dark:bg-gray-700"
          />
        ))}
      </div>

      {/* Search results skeleton */}
      <div className="space-y-3 pt-2">
        {[...Array(3)].map((_, i) => (
          <div
            key={i}
            className="space-y-2 rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800"
          >
            <div className="h-5 w-3/4 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
            <div className="h-4 w-full animate-pulse rounded bg-gray-100 dark:bg-gray-600" />
            <div className="h-4 w-2/3 animate-pulse rounded bg-gray-100 dark:bg-gray-600" />
          </div>
        ))}
      </div>
    </div>
  );
}
