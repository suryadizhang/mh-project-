/**
 * Skeleton loader for Booking Form components
 * Shows while booking form is being lazy-loaded
 */

export default function BookingFormSkeleton() {
  return (
    <div 
      className="space-y-6 p-6 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700"
      aria-label="Loading booking form..."
      role="status"
    >
      <span className="sr-only">Loading booking form...</span>
      
      {/* Form title skeleton */}
      <div className="space-y-2">
        <div className="h-8 w-48 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
        <div className="h-4 w-full max-w-md bg-gray-100 dark:bg-gray-600 rounded animate-pulse" />
      </div>
      
      {/* Form fields skeleton (4 fields) */}
      {[...Array(4)].map((_, i) => (
        <div key={i} className="space-y-2">
          <div className="h-4 w-32 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
          <div className="h-12 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
        </div>
      ))}
      
      {/* Date picker skeleton */}
      <div className="space-y-2">
        <div className="h-4 w-40 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
        <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
      </div>
      
      {/* Submit button skeleton */}
      <div className="pt-4">
        <div className="h-12 bg-primary/20 rounded animate-pulse" />
      </div>
    </div>
  );
}
