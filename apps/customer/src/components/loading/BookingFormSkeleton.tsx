/**
 * Skeleton loader for Booking Form components
 * Shows while booking form is being lazy-loaded
 */

export default function BookingFormSkeleton() {
  return (
    <div
      className="space-y-6 rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800"
      aria-label="Loading booking form..."
      role="status"
    >
      <span className="sr-only">Loading booking form...</span>

      {/* Form title skeleton */}
      <div className="space-y-2">
        <div className="h-8 w-48 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
        <div className="h-4 w-full max-w-md animate-pulse rounded bg-gray-100 dark:bg-gray-600" />
      </div>

      {/* Form fields skeleton (4 fields) */}
      {[...Array(4)].map((_, i) => (
        <div key={i} className="space-y-2">
          <div className="h-4 w-32 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
          <div className="h-12 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
        </div>
      ))}

      {/* Date picker skeleton */}
      <div className="space-y-2">
        <div className="h-4 w-40 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
        <div className="h-64 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
      </div>

      {/* Submit button skeleton */}
      <div className="pt-4">
        <div className="bg-primary/20 h-12 animate-pulse rounded" />
      </div>
    </div>
  );
}
