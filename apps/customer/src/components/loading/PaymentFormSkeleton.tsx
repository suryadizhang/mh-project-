/**
 * Skeleton loader for Payment Form component
 * Shows while Stripe payment form is being lazy-loaded
 */

export default function PaymentFormSkeleton() {
  return (
    <div 
      className="space-y-4 p-6 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700"
      aria-label="Loading payment form..."
      role="status"
    >
      <span className="sr-only">Loading payment form...</span>
      
      {/* Card number field skeleton */}
      <div className="space-y-2">
        <div className="h-4 w-24 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
        <div className="h-12 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
      </div>
      
      {/* Expiry and CVC fields skeleton */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <div className="h-4 w-20 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
          <div className="h-12 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
        </div>
        <div className="space-y-2">
          <div className="h-4 w-16 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
          <div className="h-12 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
        </div>
      </div>
      
      {/* Postal code field skeleton */}
      <div className="space-y-2">
        <div className="h-4 w-28 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
        <div className="h-12 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
      </div>
      
      {/* Submit button skeleton */}
      <div className="pt-2">
        <div className="h-12 bg-primary/20 rounded animate-pulse" />
      </div>
      
      {/* Stripe branding skeleton */}
      <div className="flex items-center justify-center gap-2 pt-2">
        <div className="h-4 w-32 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
      </div>
    </div>
  );
}
