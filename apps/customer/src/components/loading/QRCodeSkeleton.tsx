/**
 * Skeleton loader for QR Code component
 * Shows while qrcode library is being lazy-loaded
 */

export default function QRCodeSkeleton() {
  return (
    <div
      className="flex items-center justify-center p-4"
      aria-label="Generating QR code..."
      role="status"
    >
      <span className="sr-only">Generating QR code...</span>

      {/* QR Code skeleton */}
      <div className="h-64 w-64 animate-pulse rounded-lg border-4 border-gray-300 bg-gray-200 dark:border-gray-600 dark:bg-gray-700" />
    </div>
  );
}
