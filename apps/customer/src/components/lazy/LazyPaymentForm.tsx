/**
 * Lazy-loaded wrapper for Stripe Payment Form
 * Reduces initial bundle size by ~70KB
 * Stripe SDK and payment form only loaded when user reaches payment page
 */

'use client';

import dynamic from 'next/dynamic';

import { PaymentFormSkeleton } from '@/components/loading';

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

interface PaymentFormProps {
  amount: number;
  bookingData: BookingData | null;
  paymentType: 'deposit' | 'balance';
  tipAmount: number;
  clientSecret: string;
}

// Lazy load the PaymentForm component
// ssr: false because Stripe SDK requires browser APIs
const DynamicPaymentForm = dynamic<PaymentFormProps>(
  () => import('@/components/payment/PaymentForm'),
  {
    loading: () => <PaymentFormSkeleton />,
    ssr: false, // Stripe Elements requires window object
  },
);

export default function LazyPaymentForm(props: PaymentFormProps) {
  return <DynamicPaymentForm {...props} />;
}

// Re-export types for convenience
export type { PaymentFormProps, BookingData };
