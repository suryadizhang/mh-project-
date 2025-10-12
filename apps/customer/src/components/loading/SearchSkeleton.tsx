/**
 * Skeleton loader for Search component (with fuse.js)
 * Shows while enhanced search is being lazy-loaded
 */

export default function SearchSkeleton() {
  return (
    <div 
      className="space-y-4"
      aria-label="Loading search..."
      role="status"
    >
      <span className="sr-only">Loading search...</span>
      
      {/* Search input skeleton */}
      <div className="relative">
        <div className="h-12 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse" />
        {/* Search icon placeholder */}
        <div className="absolute right-4 top-1/2 -translate-y-1/2 h-5 w-5 bg-gray-300 dark:bg-gray-600 rounded animate-pulse" />
      </div>
      
      {/* Search filters skeleton */}
      <div className="flex gap-2 flex-wrap">
        {[...Array(4)].map((_, i) => (
          <div 
            key={i} 
            className="h-8 w-20 bg-gray-200 dark:bg-gray-700 rounded-full animate-pulse" 
          />
        ))}
      </div>
      
      {/* Search results skeleton */}
      <div className="space-y-3 pt-2">
        {[...Array(3)].map((_, i) => (
          <div 
            key={i} 
            className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 space-y-2"
          >
            <div className="h-5 w-3/4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
            <div className="h-4 w-full bg-gray-100 dark:bg-gray-600 rounded animate-pulse" />
            <div className="h-4 w-2/3 bg-gray-100 dark:bg-gray-600 rounded animate-pulse" />
          </div>
        ))}
      </div>
    </div>
  );
}
