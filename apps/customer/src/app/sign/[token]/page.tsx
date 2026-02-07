'use client';

/**
 * Signing Page for Agreement
 * ==========================
 *
 * This page handles:
 * 1. SMS/Email link signing (phone/text bookings)
 * 2. Token validation and hold status check
 * 3. Agreement display and digital signature capture
 * 4. Redirect to payment after signing
 *
 * URL: /sign/[token]
 * Example: /sign/abc123xyz789...
 *
 * Flow:
 * - Customer receives SMS/email with signing link
 * - Clicks link → lands here
 * - Validates token → shows agreement
 * - Signs → redirected to deposit payment
 */

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import SignaturePad from '@/components/agreements/SignaturePad';
import { apiFetch } from '@/lib/api';
import { usePricing } from '@/hooks/usePricing';

// Error codes (descriptive strings per user decision)
const SIGNING_ERROR_CODES = {
  SLOT_HOLD_EXPIRED: 'SLOT_HOLD_EXPIRED',
  SLOT_HOLD_NOT_FOUND: 'SLOT_HOLD_NOT_FOUND',
  SLOT_HOLD_COMPLETED: 'SLOT_HOLD_COMPLETED',
  SLOT_HOLD_CANCELLED: 'SLOT_HOLD_CANCELLED',
  AGREEMENT_ALREADY_SIGNED: 'AGREEMENT_ALREADY_SIGNED',
  SLOT_ALREADY_BOOKED: 'SLOT_ALREADY_BOOKED',
  INVALID_TOKEN: 'INVALID_TOKEN',
  SIGNATURE_REQUIRED: 'SIGNATURE_REQUIRED',
  SYSTEM_ERROR: 'SYSTEM_ERROR',
} as const;

type SigningErrorCode = keyof typeof SIGNING_ERROR_CODES;

interface HoldInfo {
  id: string;
  station_id: string;
  station_name: string;
  slot_datetime: string;
  customer_email: string;
  expires_at: string;
  status: 'pending' | 'converted' | 'expired' | 'cancelled';
  agreement_signed: boolean;
  deposit_paid: boolean;
  booking_id?: string | null;
}

interface AgreementContent {
  title: string;
  content_html: string;
  version: string;
  effective_date: string;
}

type PageState = 'loading' | 'valid' | 'expired' | 'already_signed' | 'error';

export default function SigningPage() {
  const params = useParams();
  const router = useRouter();
  const token = params.token as string;
  const { depositAmount } = usePricing();

  const [pageState, setPageState] = useState<PageState>('loading');
  const [errorCode, setErrorCode] = useState<SigningErrorCode | null>(null);
  const [holdInfo, setHoldInfo] = useState<HoldInfo | null>(null);
  const [agreement, setAgreement] = useState<AgreementContent | null>(null);
  const [signature, setSignature] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState<string>('');

  // Validate token and load hold info
  const validateToken = useCallback(async () => {
    try {
      const response = await apiFetch<{
        hold: HoldInfo;
        agreement: AgreementContent;
        error_code?: SigningErrorCode;
      }>(`/api/v1/agreements/holds/${token}`);

      if (!response.success || !response.data) {
        const errorCode = (response.data?.error_code || 'SYSTEM_ERROR') as SigningErrorCode;
        setErrorCode(errorCode);
        setPageState('error');
        return;
      }

      const { hold, agreement } = response.data;
      setHoldInfo(hold);
      setAgreement(agreement);

      // Check if already signed
      if (hold.agreement_signed) {
        setPageState('already_signed');
        return;
      }

      // Check if expired
      if (new Date(hold.expires_at) < new Date()) {
        setErrorCode('SLOT_HOLD_EXPIRED');
        setPageState('expired');
        return;
      }

      setPageState('valid');
    } catch (error) {
      console.error('Failed to validate signing token:', error);
      setErrorCode('SYSTEM_ERROR');
      setPageState('error');
    }
  }, [token]);

  useEffect(() => {
    if (token) {
      validateToken();
    }
  }, [token, validateToken]);

  // Countdown timer for hold expiration
  useEffect(() => {
    if (!holdInfo?.expires_at || pageState !== 'valid') return;

    const updateTimer = () => {
      const now = new Date();
      const expires = new Date(holdInfo.expires_at);
      const diff = expires.getTime() - now.getTime();

      if (diff <= 0) {
        setPageState('expired');
        setErrorCode('SLOT_HOLD_EXPIRED');
        return;
      }

      const hours = Math.floor(diff / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((diff % (1000 * 60)) / 1000);

      setTimeRemaining(hours > 0 ? `${hours}h ${minutes}m ${seconds}s` : `${minutes}m ${seconds}s`);
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);

    return () => clearInterval(interval);
  }, [holdInfo?.expires_at, pageState]);

  // Handle signature submission
  const handleSign = async () => {
    if (!signature) {
      setErrorCode('SIGNATURE_REQUIRED');
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await apiFetch<{
        redirect_url: string;
        error_code?: SigningErrorCode;
      }>('/api/v1/agreements/sign', {
        method: 'POST',
        body: JSON.stringify({
          hold_token: token,
          signature_image: signature,
          signing_method: 'sms_link',
        }),
      });

      if (!response.success || !response.data) {
        const errorCode = (response.data?.error_code || 'SYSTEM_ERROR') as SigningErrorCode;
        setErrorCode(errorCode);
        setIsSubmitting(false);
        return;
      }

      // Redirect to payment page
      router.push(response.data.redirect_url || `/checkout?hold=${token}`);
    } catch (error) {
      console.error('Failed to sign agreement:', error);
      setErrorCode('SYSTEM_ERROR');
      setIsSubmitting(false);
    }
  };

  // Format date for display
  const formatEventDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  };

  // Loading state
  if (pageState === 'loading') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-amber-50 to-orange-50">
        <div className="text-center">
          <div className="mx-auto mb-4 h-16 w-16 animate-spin rounded-full border-4 border-amber-500 border-t-transparent" />
          <h2 className="text-xl font-semibold text-gray-700">Validating your signing link...</h2>
        </div>
      </div>
    );
  }

  // Error states
  if (pageState === 'error' || pageState === 'expired') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-red-50 to-orange-50 p-4">
        <div className="w-full max-w-md rounded-2xl bg-white p-8 text-center shadow-xl">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
            <svg
              className="h-8 w-8 text-red-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </div>

          <h1 className="mb-2 text-2xl font-bold text-gray-800">
            {errorCode === 'SLOT_HOLD_EXPIRED'
              ? 'Signing Link Expired'
              : errorCode === 'SLOT_HOLD_COMPLETED'
                ? 'Already Completed!'
                : errorCode === 'SLOT_HOLD_CANCELLED'
                  ? 'Booking Cancelled'
                  : errorCode === 'SLOT_HOLD_NOT_FOUND'
                    ? 'Link Not Found'
                    : 'Unable to Load'}
          </h1>

          <p className="mb-6 text-gray-600">
            {errorCode === 'SLOT_HOLD_EXPIRED'
              ? 'This signing link has expired. The time slot may no longer be available. Please start a new booking.'
              : errorCode === 'SLOT_HOLD_COMPLETED'
                ? 'Great news! This booking has already been completed. Check your email for confirmation details.'
                : errorCode === 'SLOT_HOLD_CANCELLED'
                  ? 'This booking was cancelled. If you still want to book, please start a new reservation.'
                  : errorCode === 'SLOT_HOLD_NOT_FOUND'
                    ? 'This signing link is invalid or has already been used.'
                    : 'Something went wrong. Please try again or contact support.'}
          </p>

          <div className="space-y-3">
            <Link
              href="/book-us"
              className="block w-full rounded-lg bg-amber-500 px-4 py-3 font-medium text-white transition-colors hover:bg-amber-600"
            >
              Start New Booking
            </Link>

            <Link
              href="/contact"
              className="block w-full rounded-lg border border-gray-300 px-4 py-3 font-medium text-gray-700 transition-colors hover:bg-gray-50"
            >
              Contact Support
            </Link>
          </div>

          {errorCode && <p className="mt-4 text-xs text-gray-400">Error Code: {errorCode}</p>}
        </div>
      </div>
    );
  }

  // Already signed state - redirect to payment
  if (pageState === 'already_signed') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-green-50 to-emerald-50 p-4">
        <div className="w-full max-w-md rounded-2xl bg-white p-8 text-center shadow-xl">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
            <svg
              className="h-8 w-8 text-green-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>

          <h1 className="mb-2 text-2xl font-bold text-gray-800">Agreement Already Signed!</h1>

          <p className="mb-6 text-gray-600">
            {holdInfo?.deposit_paid
              ? 'Your booking is confirmed! Check your email for details.'
              : `Please complete your $${depositAmount ?? 100} deposit to confirm your booking.`}
          </p>

          <div className="space-y-3">
            {!holdInfo?.deposit_paid && (
              <Link
                href={`/checkout?hold=${token}`}
                className="block w-full rounded-lg bg-amber-500 px-4 py-3 font-medium text-white transition-colors hover:bg-amber-600"
              >
                Pay ${depositAmount ?? 100} Deposit
              </Link>
            )}

            <Link
              href="/"
              className="block w-full rounded-lg border border-gray-300 px-4 py-3 font-medium text-gray-700 transition-colors hover:bg-gray-50"
            >
              Return Home
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Valid state - show agreement and signature pad
  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 to-orange-50 px-4 py-8">
      <div className="mx-auto max-w-3xl">
        {/* Header */}
        <div className="rounded-t-2xl border-b bg-white p-6 shadow-lg">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-800">My Hibachi Service Agreement</h1>
              <p className="text-gray-600">Please review and sign to confirm your booking</p>
            </div>

            {/* Countdown Timer */}
            <div className="rounded-lg bg-amber-100 px-4 py-2 text-center">
              <p className="text-xs tracking-wide text-amber-700 uppercase">Time Remaining</p>
              <p className="text-lg font-bold text-amber-800">{timeRemaining}</p>
            </div>
          </div>
        </div>

        {/* Event Details */}
        {holdInfo && (
          <div className="border-x border-amber-100 bg-amber-50 p-4">
            <h2 className="mb-2 font-semibold text-amber-900">🎉 Your Event Details</h2>
            <div className="grid gap-2 text-sm text-amber-800 sm:grid-cols-2">
              <p>
                <strong>Date:</strong> {formatEventDate(holdInfo.slot_datetime)}
              </p>
              <p>
                <strong>Location:</strong> {holdInfo.station_name}
              </p>
              <p>
                <strong>Email:</strong> {holdInfo.customer_email}
              </p>
            </div>
          </div>
        )}

        {/* Agreement Content */}
        {agreement && (
          <div className="max-h-96 overflow-y-auto border-x bg-white p-6">
            <h2 className="mb-4 text-lg font-semibold text-gray-800">{agreement.title}</h2>
            <div
              className="prose prose-sm max-w-none text-gray-600"
              dangerouslySetInnerHTML={{ __html: agreement.content_html }}
            />
            <p className="mt-4 text-xs text-gray-400">
              Version: {agreement.version} | Effective: {agreement.effective_date}
            </p>
          </div>
        )}

        {/* Signature Section */}
        <div className="rounded-b-2xl border-t bg-white p-6 shadow-lg">
          <h2 className="mb-4 font-semibold text-gray-800">✍️ Your Signature</h2>

          <SignaturePad onSignatureChange={setSignature} disabled={isSubmitting} />

          <p className="mt-4 text-sm text-gray-500">
            By signing above, you agree to the terms and conditions of this service agreement. After
            signing, you will be redirected to pay the ${depositAmount ?? 100} refundable deposit.
          </p>

          {/* Error message */}
          {errorCode === 'SIGNATURE_REQUIRED' && (
            <p className="mt-2 text-sm text-red-500">Please provide your signature to continue.</p>
          )}

          {/* Submit Button */}
          <button
            onClick={handleSign}
            disabled={isSubmitting || !signature}
            className={`mt-6 w-full rounded-xl px-6 py-4 text-lg font-semibold transition-all ${
              isSubmitting || !signature
                ? 'cursor-not-allowed bg-gray-300 text-gray-500'
                : 'bg-amber-500 text-white shadow-lg hover:bg-amber-600 hover:shadow-xl'
            }`}
          >
            {isSubmitting ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="h-5 w-5 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  />
                </svg>
                Processing...
              </span>
            ) : (
              'Sign & Continue to Payment →'
            )}
          </button>
        </div>

        {/* Footer */}
        <p className="mt-6 text-center text-xs text-gray-500">
          Questions? Contact us at{' '}
          <a href="tel:9167408768" className="text-amber-600 hover:underline">
            (916) 740-8768
          </a>{' '}
          or{' '}
          <a href="mailto:cs@myhibachichef.com" className="text-amber-600 hover:underline">
            cs@myhibachichef.com
          </a>
        </p>
      </div>
    </div>
  );
}
