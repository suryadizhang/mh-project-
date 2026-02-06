/**
 * Skeleton loader for Payment Form component
 * Shows while Stripe payment form is being lazy-loaded
 */

export default function PaymentFormSkeleton() {
  return (
    <div
      className="space-y-4 rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800"
      aria-label="Loading payment form..."
      role="status"
    >
      <span className="sr-only">Loading payment form...</span>

      {/* Card number field skeleton */}
      <div className="space-y-2">
        <div className="h-4 w-24 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
        <div className="h-12 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
      </div>

      {/* Expiry and CVC fields skeleton */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <div className="h-4 w-20 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
          <div className="h-12 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
        </div>
        <div className="space-y-2">
          <div className="h-4 w-16 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
          <div className="h-12 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
        </div>
      </div>

      {/* Postal code field skeleton */}
      <div className="space-y-2">
        <div className="h-4 w-28 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
        <div className="h-12 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
      </div>

      {/* Submit button skeleton */}
      <div className="pt-2">
        <div className="bg-primary/20 h-12 animate-pulse rounded" />
      </div>

      {/* Stripe branding skeleton */}
      <div className="flex items-center justify-center gap-2 pt-2">
        <div className="h-4 w-32 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
      </div>
    </div>
  );
}
