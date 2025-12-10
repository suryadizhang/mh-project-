/**
 * Payment Page Loading State
 *
 * Displays while payment options are loading.
 */

import { Skeleton } from '@/components/ui/Skeleton';

export default function PaymentLoading() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <div className="bg-white px-4 py-6 shadow-sm">
        <div className="mx-auto max-w-2xl">
          <Skeleton className="mx-auto h-8 w-48" />
        </div>
      </div>

      {/* Payment Content */}
      <div className="mx-auto max-w-2xl px-4 py-8">
        {/* Order Summary */}
        <div className="mb-6 rounded-lg bg-white p-6 shadow-sm">
          <Skeleton className="mb-4 h-6 w-36" />
          <div className="space-y-3">
            <div className="flex justify-between">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-4 w-16" />
            </div>
            <div className="flex justify-between">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-4 w-20" />
            </div>
            <div className="border-t pt-3">
              <div className="flex justify-between">
                <Skeleton className="h-5 w-20" />
                <Skeleton className="h-5 w-24" />
              </div>
            </div>
          </div>
        </div>

        {/* Payment Methods */}
        <div className="rounded-lg bg-white p-6 shadow-sm">
          <Skeleton className="mb-6 h-6 w-40" />
          <div className="space-y-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="flex items-center gap-4 rounded-lg border p-4">
                <Skeleton className="h-10 w-10 rounded" />
                <div className="flex-1">
                  <Skeleton className="mb-1 h-5 w-32" />
                  <Skeleton className="h-3 w-48" />
                </div>
                <Skeleton className="h-6 w-6 rounded-full" />
              </div>
            ))}
          </div>
        </div>

        {/* Continue Button */}
        <Skeleton className="mt-6 h-14 w-full rounded-lg" />
      </div>
    </div>
  );
}
