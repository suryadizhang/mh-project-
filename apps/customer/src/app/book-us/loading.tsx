/**
 * BookUs Page Loading State
 *
 * Displays while the booking form is loading.
 * Uses Next.js App Router loading.tsx convention.
 */

import { SkeletonBookingForm } from '@/components/ui/Skeleton';

export default function BookUsLoading() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Hero Section Skeleton */}
      <div className="bg-gradient-to-r from-red-600 to-red-700 px-4 py-16 text-white">
        <div className="mx-auto max-w-4xl text-center">
          <div className="mx-auto mb-4 h-10 w-64 animate-pulse rounded bg-white/20" />
          <div className="mx-auto h-6 w-96 animate-pulse rounded bg-white/20" />
        </div>
      </div>

      {/* Form Section */}
      <div className="mx-auto -mt-8 max-w-4xl px-4 pb-16">
        <SkeletonBookingForm />
      </div>
    </div>
  );
}
