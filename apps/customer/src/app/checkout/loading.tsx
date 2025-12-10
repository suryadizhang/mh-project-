/**
 * Checkout Page Loading State
 *
 * Displays while checkout is loading.
 */

import { Skeleton, SkeletonInput } from '@/components/ui/Skeleton';

export default function CheckoutLoading() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white px-4 py-4 shadow-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <Skeleton className="h-8 w-32" />
          <div className="flex items-center gap-2">
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-4 w-4 rounded-full" />
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-4 w-4 rounded-full" />
            <Skeleton className="h-4 w-20" />
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-6xl px-4 py-8">
        <div className="grid gap-8 lg:grid-cols-3">
          {/* Form Section */}
          <div className="lg:col-span-2">
            <div className="rounded-lg bg-white p-6 shadow-sm">
              <Skeleton className="mb-6 h-7 w-48" />

              <div className="space-y-6">
                {/* Contact Info */}
                <div>
                  <Skeleton className="mb-4 h-5 w-40" />
                  <div className="grid gap-4 md:grid-cols-2">
                    <SkeletonInput />
                    <SkeletonInput />
                    <SkeletonInput />
                    <SkeletonInput />
                  </div>
                </div>

                {/* Event Details */}
                <div>
                  <Skeleton className="mb-4 h-5 w-32" />
                  <div className="grid gap-4 md:grid-cols-2">
                    <SkeletonInput />
                    <SkeletonInput />
                  </div>
                </div>

                {/* Address */}
                <div>
                  <Skeleton className="mb-4 h-5 w-36" />
                  <div className="space-y-4">
                    <SkeletonInput />
                    <div className="grid gap-4 md:grid-cols-3">
                      <SkeletonInput />
                      <SkeletonInput />
                      <SkeletonInput />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Order Summary */}
          <div>
            <div className="sticky top-4 rounded-lg bg-white p-6 shadow-sm">
              <Skeleton className="mb-6 h-6 w-36" />

              <div className="space-y-4">
                <div className="flex justify-between">
                  <Skeleton className="h-4 w-28" />
                  <Skeleton className="h-4 w-16" />
                </div>
                <div className="flex justify-between">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-4 w-16" />
                </div>
                <div className="flex justify-between">
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-4 w-16" />
                </div>

                <div className="border-t pt-4">
                  <div className="flex justify-between">
                    <Skeleton className="h-5 w-16" />
                    <Skeleton className="h-5 w-24" />
                  </div>
                </div>

                <Skeleton className="mt-4 h-12 w-full rounded-lg" />

                <div className="flex items-center justify-center gap-2 pt-2">
                  <Skeleton className="h-4 w-4" />
                  <Skeleton className="h-3 w-32" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
