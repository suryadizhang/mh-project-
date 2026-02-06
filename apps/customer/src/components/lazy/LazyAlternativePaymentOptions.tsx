/**
 * Lazy-loaded wrapper for Alternative Payment Options (Zelle, Venmo)
 * Reduces initial bundle size by ~50KB (includes QR code library)
 * Only loaded when user selects non-Stripe payment method
 */

'use client';

import dynamic from 'next/dynamic';

import { QRCodeSkeleton } from '@/components/loading';

// Define the props type to maintain type safety
interface BookingData {
  id: string;
  customerName: string;
  customerEmail: string;
  eventDate: string;
  eventTime: string;
  guestCount: number;
  venueAddress: string;
  totalAmount: number;
  depositPaid: boolean;
  depositAmount: number;
  remainingBalance: number;
}

interface AlternativePaymentOptionsProps {
  method: 'zelle' | 'venmo';
  amount: number;
  bookingData: BookingData | null;
  paymentType: 'deposit' | 'balance';
  tipAmount: number;
}

// Lazy load the AlternativePaymentOptions component
// ssr: false because QR code generation requires browser APIs
const DynamicAlternativePaymentOptions = dynamic<AlternativePaymentOptionsProps>(
  () => import('@/components/payment/AlternativePaymentOptions'),
  {
    loading: () => (
      <div className="rounded-xl bg-white p-8 shadow-lg">
        <QRCodeSkeleton />
        <div className="mt-4 text-center">
          <div className="mx-auto mb-2 h-6 w-48 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
          <div className="mx-auto h-4 w-64 animate-pulse rounded bg-gray-100 dark:bg-gray-600" />
        </div>
      </div>
    ),
    ssr: false, // QR code generation requires canvas API
  },
);

export default function LazyAlternativePaymentOptions(props: AlternativePaymentOptionsProps) {
  return <DynamicAlternativePaymentOptions {...props} />;
}

// Re-export types for convenience
export type { AlternativePaymentOptionsProps, BookingData };
