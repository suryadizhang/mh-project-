/**
 * Generic skeleton loader for DatePicker component
 * Shows while react-datepicker is being lazy-loaded
 */

export default function DatePickerSkeleton() {
  return (
    <div className="space-y-2" aria-label="Loading date picker..." role="status">
      <span className="sr-only">Loading date picker...</span>

      {/* Input field skeleton */}
      <div className="h-12 animate-pulse rounded-lg bg-gray-200 dark:bg-gray-700" />

      {/* Calendar skeleton */}
      <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-lg dark:border-gray-700 dark:bg-gray-800">
        {/* Month/Year header skeleton */}
        <div className="mb-4 flex items-center justify-between">
          <div className="h-6 w-6 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
          <div className="h-6 w-32 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
          <div className="h-6 w-6 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
        </div>

        {/* Weekday headers skeleton */}
        <div className="mb-2 grid grid-cols-7 gap-2">
          {[...Array(7)].map((_, i) => (
            <div key={i} className="h-8 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
          ))}
        </div>

        {/* Calendar days skeleton */}
        <div className="grid grid-cols-7 gap-2">
          {[...Array(35)].map((_, i) => (
            <div key={i} className="h-10 animate-pulse rounded bg-gray-100 dark:bg-gray-600" />
          ))}
        </div>
      </div>
    </div>
  );
}
