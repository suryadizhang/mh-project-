'use client';

import {
  Calendar,
  CheckCircle,
  CreditCard,
  DollarSign,
  Download,
  Home,
  Mail,
  Phone,
} from 'lucide-react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useState } from 'react';

import { apiFetch } from '@/lib/api';
import { logger } from '@/lib/logger';

interface PaymentSuccess {
  payment_intent: string;
  amount: number;
  currency: string;
  status: string;
  customer: {
    name?: string;
    email?: string;
  };
  metadata: {
    booking_id?: string;
    customer_name?: string;
    event_date?: string;
    payment_type?: string;
  };
  receipt_url?: string;
  created: number;
}

function CheckoutSuccessContent() {
  const searchParams = useSearchParams();
  const sessionId = searchParams?.get('session_id');
  const [paymentData, setPaymentData] = useState<PaymentSuccess | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSessionData = async () => {
      if (!sessionId) {
        setError('No session ID provided');
        setIsLoading(false);
        return;
      }

      try {
        // NOTE: This endpoint is NOT IMPLEMENTED in the backend yet.
        // Documented in PAYMENT_SCHEMA_ANALYSIS.md - Phase 2B future work.
        // Backend needs: POST /api/v1/payments/checkout-session
        // Should use: stripe.checkout.sessions.retrieve(session_id)
        // Schema ready: CheckoutSessionVerifyResponseSchema (when implemented)
        const response = await apiFetch('/api/v1/payments/checkout-session', {
          method: 'POST',
          body: JSON.stringify({ session_id: sessionId }),
          // TODO: Add schema validation when endpoint implemented:
          // schema: CheckoutSessionVerifyResponseSchema,
        });

        if (response.success && response.data) {
          setPaymentData(response.data as unknown as PaymentSuccess);
        } else {
          setError(response.error || 'Failed to retrieve payment details');
        }
      } catch (err) {
        logger.error('Error fetching session data', err as Error);
        setError('Failed to load payment information');
      } finally {
        setIsLoading(false);
      }
    };

    fetchSessionData();
  }, [sessionId]);

  const downloadReceipt = async () => {
    if (!paymentData) return;

    try {
      const receiptData = {
        paymentId: paymentData.payment_intent,
        amount: paymentData.amount / 100,
        currency: paymentData.currency.toUpperCase(),
        date: new Date(paymentData.created * 1000).toLocaleDateString(),
        customer: paymentData.customer.name || paymentData.metadata.customer_name || 'Customer',
        bookingId: paymentData.metadata.booking_id,
        paymentType: paymentData.metadata.payment_type,
        sessionId: sessionId,
      };

      const receiptText = `
MY HIBACHI - PAYMENT RECEIPT
=============================

Payment Details
---------------
Payment ID: ${receiptData.paymentId}
Session ID: ${receiptData.sessionId}
Amount: $${receiptData.amount.toFixed(2)} ${receiptData.currency}
Date: ${receiptData.date}
Status: Completed

Customer Information
-------------------
Name: ${receiptData.customer}
${receiptData.bookingId ? `Booking ID: ${receiptData.bookingId}` : ''}
${
  receiptData.paymentType
    ? `Payment Type: ${
        receiptData.paymentType === 'deposit' ? 'Deposit Payment' : 'Balance Payment'
      }`
    : ''
}

Contact Information
-------------------
My Hibachi
Phone: (916) 740-8768
Email: info@myhibachi.com
Website: www.myhibachi.com

Thank you for choosing My Hibachi!
We look forward to serving you an unforgettable experience.
      `.trim();

      const blob = new Blob([receiptText], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `MyHibachi_Receipt_${receiptData.paymentId.slice(-8)}.txt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      logger.error('Error downloading receipt', err as Error);
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="mx-auto mb-4 h-16 w-16 animate-spin rounded-full border-4 border-green-600 border-t-transparent"></div>
          <p className="text-gray-600">Loading your payment confirmation...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="mx-4 w-full max-w-md rounded-xl bg-white p-8 text-center shadow-lg">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
            <CreditCard className="h-8 w-8 text-red-600" />
          </div>
          <h1 className="mb-2 text-2xl font-bold text-gray-900">Payment Error</h1>
          <p className="mb-6 text-gray-600">{error}</p>
          <Link
            href="/payment"
            className="inline-flex items-center rounded-lg bg-red-600 px-6 py-3 text-white transition-colors hover:bg-red-700"
          >
            <Home className="mr-2 h-5 w-5" />
            Return to Payment Page
          </Link>
        </div>
      </div>
    );
  }

  if (!paymentData) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="mx-4 w-full max-w-md rounded-xl bg-white p-8 text-center shadow-lg">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gray-100">
            <CreditCard className="h-8 w-8 text-gray-600" />
          </div>
          <h1 className="mb-2 text-2xl font-bold text-gray-900">Payment Not Found</h1>
          <p className="mb-6 text-gray-600">
            We couldn&apos;t find the payment details for this session.
          </p>
          <Link
            href="/payment"
            className="inline-flex items-center rounded-lg bg-blue-600 px-6 py-3 text-white transition-colors hover:bg-blue-700"
          >
            <Home className="mr-2 h-5 w-5" />
            Return to Payment Page
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-8">
      <div className="mx-auto max-w-3xl">
        {/* Success Header */}
        <div className="mb-6 rounded-xl bg-white p-8 text-center shadow-lg">
          <div className="mx-auto mb-6 flex h-24 w-24 items-center justify-center rounded-full bg-green-100">
            <CheckCircle className="h-16 w-16 text-green-600" />
          </div>
          <h1 className="mb-3 text-4xl font-bold text-gray-900">Payment Successful!</h1>
          <p className="mb-4 text-2xl font-bold text-green-600">
            ${(paymentData.amount / 100).toFixed(2)} USD
          </p>
          <p className="mx-auto max-w-2xl text-lg text-gray-600">
            Thank you for your payment! Your transaction has been processed successfully. A
            confirmation email has been sent to your registered email address.
          </p>
        </div>

        {/* Payment Summary */}
        <div className="mb-6 rounded-xl bg-white p-6 shadow-lg">
          <h2 className="mb-6 flex items-center text-xl font-semibold text-gray-900">
            <DollarSign className="mr-2 h-6 w-6 text-green-600" />
            Payment Summary
          </h2>
          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-gray-100 pb-2">
                <span className="text-gray-600">Payment Amount</span>
                <span className="text-lg font-semibold">
                  ${(paymentData.amount / 100).toFixed(2)}
                </span>
              </div>
              <div className="flex items-center justify-between border-b border-gray-100 pb-2">
                <span className="text-gray-600">Currency</span>
                <span className="font-medium">{paymentData.currency.toUpperCase()}</span>
              </div>
              <div className="flex items-center justify-between border-b border-gray-100 pb-2">
                <span className="text-gray-600">Status</span>
                <span className="inline-flex items-center rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-800">
                  <CheckCircle className="mr-1 h-4 w-4" />
                  Completed
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Date & Time</span>
                <span className="font-medium">
                  {new Date(paymentData.created * 1000).toLocaleString()}
                </span>
              </div>
            </div>
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-gray-100 pb-2">
                <span className="text-gray-600">Payment ID</span>
                <span className="font-mono text-sm">{paymentData.payment_intent.slice(-12)}</span>
              </div>
              <div className="flex items-center justify-between border-b border-gray-100 pb-2">
                <span className="text-gray-600">Session ID</span>
                <span className="font-mono text-sm">{sessionId?.slice(-12)}</span>
              </div>
              {paymentData.metadata.payment_type && (
                <div className="flex items-center justify-between border-b border-gray-100 pb-2">
                  <span className="text-gray-600">Payment Type</span>
                  <span className="font-medium capitalize">
                    {paymentData.metadata.payment_type === 'deposit'
                      ? 'Deposit Payment'
                      : 'Balance Payment'}
                  </span>
                </div>
              )}
              {paymentData.customer.name && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Customer</span>
                  <span className="font-medium">{paymentData.customer.name}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Booking Information */}
        {paymentData.metadata.booking_id && (
          <div className="mb-6 rounded-xl border border-blue-200 bg-gradient-to-r from-blue-50 to-purple-50 p-6">
            <h3 className="mb-4 flex items-center text-xl font-semibold text-blue-900">
              <Calendar className="mr-2 h-6 w-6" />
              Booking Confirmation
            </h3>
            <div className="grid gap-4 text-blue-800 md:grid-cols-2">
              <div>
                <div className="text-blue-600">Booking ID</div>
                <div className="font-mono text-lg font-semibold">
                  {paymentData.metadata.booking_id}
                </div>
              </div>
              {paymentData.metadata.customer_name && (
                <div>
                  <div className="text-blue-600">Customer Name</div>
                  <div className="font-semibold">{paymentData.metadata.customer_name}</div>
                </div>
              )}
              {paymentData.metadata.event_date && (
                <div>
                  <div className="text-blue-600">Event Date</div>
                  <div className="font-semibold">{paymentData.metadata.event_date}</div>
                </div>
              )}
              <div>
                <div className="text-blue-600">Payment Status</div>
                <div className="font-semibold">
                  {paymentData.metadata.payment_type === 'deposit'
                    ? 'Deposit Secured'
                    : 'Balance Paid'}
                </div>
              </div>
            </div>
            {paymentData.metadata.payment_type === 'deposit' && (
              <div className="mt-4 rounded-lg bg-blue-100 p-4">
                <p className="text-sm text-blue-800">
                  <strong>Next Steps:</strong> Your booking is now confirmed! We&apos;ll send you a
                  final invoice for the remaining balance closer to your event date. Keep this
                  confirmation for your records.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="mb-6 rounded-xl bg-white p-6 shadow-lg">
          <h3 className="mb-4 text-lg font-semibold text-gray-900">Next Steps</h3>
          <div className="grid gap-4 md:grid-cols-3">
            <button
              onClick={downloadReceipt}
              className="flex items-center justify-center rounded-lg bg-green-600 px-6 py-3 text-white transition-colors hover:bg-green-700"
            >
              <Download className="mr-2 h-5 w-5" />
              Download Receipt
            </button>
            {paymentData.receipt_url && (
              <a
                href={paymentData.receipt_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center rounded-lg bg-blue-600 px-6 py-3 text-white transition-colors hover:bg-blue-700"
              >
                <Mail className="mr-2 h-5 w-5" />
                Email Receipt
              </a>
            )}
            <Link
              href="/"
              className="flex items-center justify-center rounded-lg bg-gray-600 px-6 py-3 text-white transition-colors hover:bg-gray-700"
            >
              <Home className="mr-2 h-5 w-5" />
              Return Home
            </Link>
          </div>
        </div>

        {/* What's Next Section */}
        <div className="mb-6 rounded-xl border border-red-200 bg-gradient-to-r from-red-50 to-orange-50 p-6">
          <h3 className="mb-4 text-xl font-semibold text-red-900">What Happens Next?</h3>
          <div className="space-y-3 text-red-800">
            <div className="flex items-start">
              <div className="mt-0.5 mr-3 flex h-6 w-6 items-center justify-center rounded-full bg-red-200">
                <span className="text-sm font-bold text-red-800">1</span>
              </div>
              <div>
                <p className="font-medium">Confirmation Email</p>
                <p className="text-sm text-red-700">
                  You&apos;ll receive a detailed confirmation email within 5 minutes.
                </p>
              </div>
            </div>
            <div className="flex items-start">
              <div className="mt-0.5 mr-3 flex h-6 w-6 items-center justify-center rounded-full bg-red-200">
                <span className="text-sm font-bold text-red-800">2</span>
              </div>
              <div>
                <p className="font-medium">Chef Assignment</p>
                <p className="text-sm text-red-700">
                  We&apos;ll assign your personal hibachi chef and send you their details.
                </p>
              </div>
            </div>
            <div className="flex items-start">
              <div className="mt-0.5 mr-3 flex h-6 w-6 items-center justify-center rounded-full bg-red-200">
                <span className="text-sm font-bold text-red-800">3</span>
              </div>
              <div>
                <p className="font-medium">Event Preparation</p>
                <p className="text-sm text-red-700">
                  {paymentData.metadata.payment_type === 'deposit'
                    ? "We'll contact you 48 hours before your event for final details and balance payment."
                    : "Your event is fully paid! We'll contact you 48 hours before for final preparations."}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Contact Information */}
        <div className="rounded-xl bg-white p-6 shadow-lg">
          <h3 className="mb-4 text-lg font-semibold text-gray-900">Need Help or Have Questions?</h3>
          <p className="mb-4 text-gray-600">
            Our team is here to help! Contact us if you have any questions about your booking or
            payment.
          </p>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="flex items-center rounded-lg bg-gray-50 p-4">
              <Phone className="mr-3 h-6 w-6 text-gray-500" />
              <div>
                <div className="font-medium text-gray-900">Phone Support</div>
                <div className="text-gray-600">(916) 740-8768</div>
                <div className="text-sm text-gray-500">Available 9 AM - 9 PM PST</div>
              </div>
            </div>
            <div className="flex items-center rounded-lg bg-gray-50 p-4">
              <Mail className="mr-3 h-6 w-6 text-gray-500" />
              <div>
                <div className="font-medium text-gray-900">Email Support</div>
                <div className="text-gray-600">info@myhibachi.com</div>
                <div className="text-sm text-gray-500">Response within 24 hours</div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Note */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>This payment was processed securely by Stripe with 256-bit SSL encryption.</p>
          <p className="mt-1">
            Transaction ID: {paymentData.payment_intent} • Session: {sessionId}
          </p>
          <p className="mt-2">
            Keep this confirmation for your records. Your receipt has been automatically emailed to
            you.
          </p>
        </div>
      </div>
    </div>
  );
}

function CheckoutSuccessLoading() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="mx-auto mb-4 h-16 w-16 animate-spin rounded-full border-4 border-green-600 border-t-transparent"></div>
        <p className="text-gray-600">Loading your payment confirmation...</p>
      </div>
    </div>
  );
}

export default function CheckoutSuccessPage() {
  return (
    <Suspense fallback={<CheckoutSuccessLoading />}>
      <CheckoutSuccessContent />
    </Suspense>
  );
}
