/**
 * Skeleton loader for ChatWidget component
 * Shows while the chat widget is being lazy-loaded
 */

export default function ChatWidgetSkeleton() {
  return (
    <div className="fixed right-4 bottom-4 z-50">
      <div
        className="h-14 w-14 animate-pulse rounded-full bg-gray-200 shadow-lg dark:bg-gray-700"
        aria-label="Loading chat widget..."
        role="status"
      >
        <span className="sr-only">Loading chat widget...</span>
      </div>
    </div>
  );
}
