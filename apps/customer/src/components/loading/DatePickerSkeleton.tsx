/**
 * Generic skeleton loader for DatePicker component
 * Shows while react-datepicker is being lazy-loaded
 */

export default function DatePickerSkeleton() {
  return (
    <div 
      className="space-y-2"
      aria-label="Loading date picker..."
      role="status"
    >
      <span className="sr-only">Loading date picker...</span>
      
      {/* Input field skeleton */}
      <div className="h-12 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse" />
      
      {/* Calendar skeleton */}
      <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
        {/* Month/Year header skeleton */}
        <div className="flex items-center justify-between mb-4">
          <div className="h-6 w-6 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
          <div className="h-6 w-32 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
          <div className="h-6 w-6 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
        </div>
        
        {/* Weekday headers skeleton */}
        <div className="grid grid-cols-7 gap-2 mb-2">
          {[...Array(7)].map((_, i) => (
            <div 
              key={i} 
              className="h-8 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" 
            />
          ))}
        </div>
        
        {/* Calendar days skeleton */}
        <div className="grid grid-cols-7 gap-2">
          {[...Array(35)].map((_, i) => (
            <div 
              key={i} 
              className="h-10 bg-gray-100 dark:bg-gray-600 rounded animate-pulse" 
            />
          ))}
        </div>
      </div>
    </div>
  );
}
