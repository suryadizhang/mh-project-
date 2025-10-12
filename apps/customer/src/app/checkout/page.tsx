'use client';

import { loadStripe } from '@stripe/stripe-js';
import {
  ArrowLeft,
  Calendar,
  CheckCircle,
  CreditCard,
  DollarSign,
  Loader2,
  Users,
  XCircle,
} from 'lucide-react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useState } from 'react';

import { apiFetch } from '@/lib/api';
import { logger } from '@/lib/logger';

// Initialize Stripe
const stripePublishableKey = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY;
const stripePromise = stripePublishableKey ? loadStripe(stripePublishableKey) : null;

interface CheckoutSession {
  id: string;
  status: string;
  payment_status: string;
  amount_total: number;
  currency: string;
  customer_details?: {
    name?: string;
    email?: string;
  };
  metadata?: {
    booking_id?: string;
    customer_name?: string;
    event_date?: string;
    payment_type?: string;
  };
  payment_intent?: string;
}

function CheckoutContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const sessionId = searchParams?.get('session_id');

  const [session, setSession] = useState<CheckoutSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const retrieveSession = async () => {
      if (!sessionId) {
        setError('No session ID provided');
        setLoading(false);
        return;
      }

      try {
        // In a real implementation, you'd call your backend to retrieve the session
        // For now, we'll simulate this with the Stripe session
        const stripe = await stripePromise;
        if (!stripe) {
          throw new Error('Stripe not initialized');
        }

        // This would be replaced with your backend call
        const response = await apiFetch('/api/v1/payments/checkout-session', {
          method: 'POST',
          body: JSON.stringify({ session_id: sessionId }),
        });

        if (response.success && response.data) {
          const sessionData = response.data as unknown as CheckoutSession;
          setSession(sessionData);

          // If payment was successful, redirect to success page
          if (sessionData.payment_status === 'paid') {
            router.push(`/payment/success?payment_intent=${sessionData.payment_intent}`);
            return;
          }
        } else {
          setError(response.error || 'Failed to retrieve session');
        }
      } catch (err) {
        logger.error('Error retrieving session', err as Error);
        setError('Failed to retrieve checkout session');
      } finally {
        setLoading(false);
      }
    };

    retrieveSession();
  }, [sessionId, router]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <Loader2 className="mx-auto mb-4 h-16 w-16 animate-spin text-blue-600" />
          <h2 className="mb-2 text-xl font-semibold text-gray-900">Processing Payment...</h2>
          <p className="text-gray-600">Please wait while we verify your payment details.</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="mx-4 w-full max-w-md rounded-xl bg-white p-8 text-center shadow-lg">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
            <XCircle className="h-8 w-8 text-red-600" />
          </div>
          <h1 className="mb-2 text-2xl font-bold text-gray-900">Checkout Error</h1>
          <p className="mb-6 text-gray-600">{error}</p>
          <div className="space-y-3">
            <Link
              href="/payment"
              className="block w-full rounded-lg bg-red-600 px-6 py-3 text-white transition-colors hover:bg-red-700"
            >
              Try Again
            </Link>
            <Link
              href="/"
              className="block w-full rounded-lg border border-gray-300 px-6 py-3 text-gray-700 transition-colors hover:bg-gray-50"
            >
              Return Home
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="mx-4 w-full max-w-md rounded-xl bg-white p-8 text-center shadow-lg">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gray-100">
            <CreditCard className="h-8 w-8 text-gray-600" />
          </div>
          <h1 className="mb-2 text-2xl font-bold text-gray-900">Session Not Found</h1>
          <p className="mb-6 text-gray-600">
            The checkout session could not be found or has expired.
          </p>
          <Link
            href="/payment"
            className="inline-flex items-center rounded-lg bg-blue-600 px-6 py-3 text-white transition-colors hover:bg-blue-700"
          >
            <ArrowLeft className="mr-2 h-5 w-5" />
            Back to Payment
          </Link>
        </div>
      </div>
    );
  }

  // Handle different payment statuses
  const getStatusDisplay = () => {
    switch (session.payment_status) {
      case 'paid':
        return {
          icon: <CheckCircle className="h-12 w-12 text-green-600" />,
          title: 'Payment Successful!',
          subtitle: 'Your payment has been processed successfully.',
          bgColor: 'bg-green-100',
          textColor: 'text-green-600',
        };
      case 'unpaid':
        return {
          icon: <XCircle className="h-12 w-12 text-red-600" />,
          title: 'Payment Failed',
          subtitle: 'Your payment could not be processed.',
          bgColor: 'bg-red-100',
          textColor: 'text-red-600',
        };
      case 'no_payment_required':
        return {
          icon: <CheckCircle className="h-12 w-12 text-blue-600" />,
          title: 'No Payment Required',
          subtitle: 'This session does not require payment.',
          bgColor: 'bg-blue-100',
          textColor: 'text-blue-600',
        };
      default:
        return {
          icon: <Loader2 className="h-12 w-12 animate-spin text-yellow-600" />,
          title: 'Processing...',
          subtitle: 'Your payment is being processed.',
          bgColor: 'bg-yellow-100',
          textColor: 'text-yellow-600',
        };
    }
  };

  const statusDisplay = getStatusDisplay();

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-8">
      <div className="mx-auto max-w-2xl">
        {/* Status Header */}
        <div className="mb-6 rounded-xl bg-white p-8 text-center shadow-lg">
          <div
            className={`h-20 w-20 ${statusDisplay.bgColor} mx-auto mb-6 flex items-center justify-center rounded-full`}
          >
            {statusDisplay.icon}
          </div>
          <h1 className="mb-2 text-3xl font-bold text-gray-900">{statusDisplay.title}</h1>
          <p className="mb-4 text-xl text-gray-600">{statusDisplay.subtitle}</p>
          {session.amount_total && (
            <p className={`text-xl font-semibold ${statusDisplay.textColor}`}>
              ${(session.amount_total / 100).toFixed(2)} {session.currency?.toUpperCase()}
            </p>
          )}
        </div>

        {/* Session Details */}
        <div className="mb-6 rounded-xl bg-white p-6 shadow-lg">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">Transaction Details</h2>
          <div className="grid gap-4 text-sm md:grid-cols-2">
            <div className="space-y-3">
              <div>
                <div className="text-gray-500">Session ID</div>
                <div className="font-mono text-gray-900">{session.id}</div>
              </div>
              <div>
                <div className="text-gray-500">Status</div>
                <div className="text-gray-900 capitalize">{session.status}</div>
              </div>
              <div>
                <div className="text-gray-500">Payment Status</div>
                <div
                  className={`inline-flex items-center rounded px-2 py-1 text-xs font-medium ${
                    session.payment_status === 'paid'
                      ? 'bg-green-100 text-green-800'
                      : session.payment_status === 'unpaid'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-yellow-100 text-yellow-800'
                  }`}
                >
                  {session.payment_status}
                </div>
              </div>
            </div>
            <div className="space-y-3">
              {session.customer_details?.name && (
                <div>
                  <div className="text-gray-500">Customer</div>
                  <div className="text-gray-900">{session.customer_details.name}</div>
                </div>
              )}
              {session.customer_details?.email && (
                <div>
                  <div className="text-gray-500">Email</div>
                  <div className="text-gray-900">{session.customer_details.email}</div>
                </div>
              )}
              {session.payment_intent && (
                <div>
                  <div className="text-gray-500">Payment Intent</div>
                  <div className="font-mono text-xs text-gray-900">{session.payment_intent}</div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Booking Information */}
        {session.metadata?.booking_id && (
          <div className="mb-6 rounded-xl border border-blue-200 bg-blue-50 p-6">
            <h3 className="mb-3 flex items-center text-lg font-semibold text-blue-900">
              <Calendar className="mr-2 h-5 w-5" />
              Booking Information
            </h3>
            <div className="space-y-2 text-sm text-blue-800">
              <div className="flex items-center">
                <DollarSign className="mr-2 h-4 w-4" />
                <span>Booking ID: </span>
                <span className="ml-1 font-mono">{session.metadata.booking_id}</span>
              </div>
              {session.metadata.customer_name && (
                <div className="flex items-center">
                  <Users className="mr-2 h-4 w-4" />
                  <span>Customer: </span>
                  <span className="ml-1">{session.metadata.customer_name}</span>
                </div>
              )}
              {session.metadata.event_date && (
                <div className="flex items-center">
                  <Calendar className="mr-2 h-4 w-4" />
                  <span>Event Date: </span>
                  <span className="ml-1">{session.metadata.event_date}</span>
                </div>
              )}
              {session.metadata.payment_type && (
                <div className="flex items-center">
                  <CreditCard className="mr-2 h-4 w-4" />
                  <span>Payment Type: </span>
                  <span className="ml-1 capitalize">
                    {session.metadata.payment_type === 'deposit'
                      ? 'Deposit Payment'
                      : 'Balance Payment'}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="mb-6 rounded-xl bg-white p-6 shadow-lg">
          <h3 className="mb-4 text-lg font-semibold text-gray-900">What&apos;s Next?</h3>
          <div className="grid gap-4 md:grid-cols-2">
            {session.payment_status === 'paid' ? (
              <>
                <Link
                  href={`/payment/success?payment_intent=${session.payment_intent}`}
                  className="flex items-center justify-center rounded-lg bg-green-600 px-6 py-3 text-white transition-colors hover:bg-green-700"
                >
                  <CheckCircle className="mr-2 h-5 w-5" />
                  View Receipt
                </Link>
                <Link
                  href="/"
                  className="flex items-center justify-center rounded-lg bg-gray-600 px-6 py-3 text-white transition-colors hover:bg-gray-700"
                >
                  Return Home
                </Link>
              </>
            ) : (
              <>
                <Link
                  href="/payment"
                  className="flex items-center justify-center rounded-lg bg-blue-600 px-6 py-3 text-white transition-colors hover:bg-blue-700"
                >
                  <ArrowLeft className="mr-2 h-5 w-5" />
                  Try Again
                </Link>
                <Link
                  href="/"
                  className="flex items-center justify-center rounded-lg bg-gray-600 px-6 py-3 text-white transition-colors hover:bg-gray-700"
                >
                  Return Home
                </Link>
              </>
            )}
          </div>
        </div>

        {/* Additional Information */}
        <div className="text-center text-sm text-gray-500">
          <p>
            {session.payment_status === 'paid'
              ? 'Your payment was processed securely by Stripe.'
              : 'If you continue to experience issues, please contact our support team.'}
          </p>
          <p className="mt-1">Session ID: {session.id}</p>
        </div>
      </div>
    </div>
  );
}

function CheckoutLoading() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="text-center">
        <Loader2 className="mx-auto mb-4 h-16 w-16 animate-spin text-blue-600" />
        <h2 className="mb-2 text-xl font-semibold text-gray-900">Processing...</h2>
        <p className="text-gray-600">Please wait while we verify your payment.</p>
      </div>
    </div>
  );
}

export default function CheckoutPage() {
  return (
    <Suspense fallback={<CheckoutLoading />}>
      <CheckoutContent />
    </Suspense>
  );
}
