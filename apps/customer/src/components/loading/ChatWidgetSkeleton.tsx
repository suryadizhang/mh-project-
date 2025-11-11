/**
 * Skeleton loader for ChatWidget component
 * Shows while the chat widget is being lazy-loaded
 */

export default function ChatWidgetSkeleton() {
  return (
    <div className="fixed bottom-4 right-4 z-50">
      <div 
        className="h-14 w-14 bg-gray-200 dark:bg-gray-700 rounded-full animate-pulse shadow-lg"
        aria-label="Loading chat widget..."
        role="status"
      >
        <span className="sr-only">Loading chat widget...</span>
      </div>
    </div>
  );
}
