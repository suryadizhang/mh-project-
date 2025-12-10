'use client';

import { CheckCircle, CreditCard, Download, Home, Mail, Phone } from 'lucide-react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useState } from 'react';

import { useProtectedPhone, useProtectedPaymentEmail } from '@/components/ui/ProtectedPhone';
import { logger } from '@/lib/logger';

interface PaymentDetails {
  id: string;
  status: string;
  amount: number;
  currency: string;
  metadata: {
    bookingId?: string;
    customerName?: string;
    eventDate?: string;
    paymentType?: string;
  };
  created: number;
}

function PaymentSuccessContent() {
  // Anti-scraper protected contact info
  const { formatted: protectedPhone } = useProtectedPhone();
  const { email: protectedEmail } = useProtectedPaymentEmail();

  const searchParams = useSearchParams();
  const paymentIntentId = searchParams?.get('payment_intent');
  const [paymentDetails, setPaymentDetails] = useState<PaymentDetails | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPaymentDetails = async () => {
      if (!paymentIntentId) {
        setError('No payment information found');
        setIsLoading(false);
        return;
      }

      try {
        const response = await fetch(
          `/api/v1/payments/create-intent?payment_intent_id=${paymentIntentId}`,
        );
        const data = await response.json();

        if (response.ok) {
          setPaymentDetails(data);
        } else {
          setError(data.error || 'Failed to retrieve payment details');
        }
      } catch (err) {
        logger.error('Error fetching payment details', err as Error);
        setError('Failed to load payment information');
      } finally {
        setIsLoading(false);
      }
    };

    fetchPaymentDetails();
  }, [paymentIntentId]);

  const downloadReceipt = async () => {
    if (!paymentDetails) return;

    try {
      // In production, you would generate and download a proper receipt
      const receiptData = {
        paymentId: paymentDetails.id,
        amount: paymentDetails.amount / 100,
        currency: paymentDetails.currency.toUpperCase(),
        date: new Date(paymentDetails.created * 1000).toLocaleDateString(),
        customer: paymentDetails.metadata.customerName,
        bookingId: paymentDetails.metadata.bookingId,
        paymentType: paymentDetails.metadata.paymentType,
      };

      const receiptText = `
MY HIBACHI PAYMENT RECEIPT
--------------------------
Payment ID: ${receiptData.paymentId}
Amount: $${receiptData.amount.toFixed(2)} ${receiptData.currency}
Date: ${receiptData.date}
Customer: ${receiptData.customer}
Booking ID: ${receiptData.bookingId || 'N/A'}
Payment Type: ${receiptData.paymentType || 'Manual'}

Thank you for your payment!
Contact: ${protectedPhone || 'myhibachichef.com/contact'} | ${protectedEmail || 'myhibachichef.com/contact'}
      `.trim();

      const blob = new Blob([receiptText], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `MyHibachi_Receipt_${receiptData.paymentId}.txt`;
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
          <div className="mx-auto mb-4 h-16 w-16 animate-spin rounded-full border-4 border-blue-600 border-t-transparent"></div>
          <p className="text-gray-600">Loading payment details...</p>
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

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-8">
      <div className="mx-auto max-w-2xl">
        {/* Success Header */}
        <div className="mb-6 rounded-xl bg-white p-8 text-center shadow-lg">
          <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-green-100">
            <CheckCircle className="h-12 w-12 text-green-600" />
          </div>
          <h1 className="mb-2 text-3xl font-bold text-gray-900">Payment Successful!</h1>
          <p className="mb-4 text-xl font-semibold text-green-600">
            ${paymentDetails ? (paymentDetails.amount / 100).toFixed(2) : '0.00'} USD
          </p>
          <p className="text-gray-600">
            Your payment has been processed successfully. A confirmation email will be sent to your
            registered email address.
          </p>
        </div>

        {/* Payment Details */}
        {paymentDetails && (
          <div className="mb-6 rounded-xl bg-white p-6 shadow-lg">
            <h2 className="mb-4 text-lg font-semibold text-gray-900">Payment Details</h2>
            <div className="grid gap-4 text-sm md:grid-cols-2">
              <div className="space-y-3">
                <div>
                  <div className="text-gray-500">Payment ID</div>
                  <div className="font-mono text-gray-900">{paymentDetails.id}</div>
                </div>
                <div>
                  <div className="text-gray-500">Amount</div>
                  <div className="font-semibold text-gray-900">
                    ${(paymentDetails.amount / 100).toFixed(2)}{' '}
                    {paymentDetails.currency.toUpperCase()}
                  </div>
                </div>
                <div>
                  <div className="text-gray-500">Status</div>
                  <div className="inline-flex items-center rounded bg-green-100 px-2 py-1 text-xs font-medium text-green-800">
                    {paymentDetails.status === 'succeeded' ? 'Completed' : paymentDetails.status}
                  </div>
                </div>
              </div>
              <div className="space-y-3">
                <div>
                  <div className="text-gray-500">Date & Time</div>
                  <div className="text-gray-900">
                    {new Date(paymentDetails.created * 1000).toLocaleString()}
                  </div>
                </div>
                {paymentDetails.metadata.bookingId && (
                  <div>
                    <div className="text-gray-500">Booking ID</div>
                    <div className="font-mono text-gray-900">
                      {paymentDetails.metadata.bookingId}
                    </div>
                  </div>
                )}
                {paymentDetails.metadata.paymentType && (
                  <div>
                    <div className="text-gray-500">Payment Type</div>
                    <div className="text-gray-900 capitalize">
                      {paymentDetails.metadata.paymentType === 'deposit'
                        ? 'Deposit Payment'
                        : 'Balance Payment'}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Booking Information */}
        {paymentDetails?.metadata.bookingId && (
          <div className="mb-6 rounded-xl border border-blue-200 bg-blue-50 p-6">
            <h3 className="mb-3 text-lg font-semibold text-blue-900">Booking Information</h3>
            <div className="space-y-2 text-sm text-blue-800">
              <div className="flex justify-between">
                <span>Booking ID:</span>
                <span className="font-mono">{paymentDetails.metadata.bookingId}</span>
              </div>
              {paymentDetails.metadata.customerName && (
                <div className="flex justify-between">
                  <span>Customer:</span>
                  <span>{paymentDetails.metadata.customerName}</span>
                </div>
              )}
              {paymentDetails.metadata.eventDate && (
                <div className="flex justify-between">
                  <span>Event Date:</span>
                  <span>{paymentDetails.metadata.eventDate}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="mb-6 rounded-xl bg-white p-6 shadow-lg">
          <h3 className="mb-4 text-lg font-semibold text-gray-900">What&apos;s Next?</h3>
          <div className="grid gap-4 md:grid-cols-2">
            <button
              onClick={downloadReceipt}
              className="flex items-center justify-center rounded-lg bg-blue-600 px-6 py-3 text-white transition-colors hover:bg-blue-700"
            >
              <Download className="mr-2 h-5 w-5" />
              Download Receipt
            </button>
            <Link
              href="/"
              className="flex items-center justify-center rounded-lg bg-gray-600 px-6 py-3 text-white transition-colors hover:bg-gray-700"
            >
              <Home className="mr-2 h-5 w-5" />
              Return Home
            </Link>
          </div>
        </div>

        {/* Contact Information */}
        <div className="rounded-xl bg-white p-6 shadow-lg">
          <h3 className="mb-4 text-lg font-semibold text-gray-900">Need Help?</h3>
          <p className="mb-4 text-gray-600">
            If you have any questions about your payment or booking, please don&apos;t hesitate to
            contact us:
          </p>
          <div className="flex flex-col space-y-2 text-sm sm:flex-row sm:items-center sm:justify-center sm:space-y-0 sm:space-x-6">
            <div className="flex items-center">
              <Phone className="mr-2 h-4 w-4 text-gray-500" />
              <span>{protectedPhone || 'Loading...'}</span>
            </div>
            <div className="flex items-center">
              <Mail className="mr-2 h-4 w-4 text-gray-500" />
              <span>{protectedEmail || 'Loading...'}</span>
            </div>
          </div>
        </div>

        {/* Additional Information */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>This payment was processed securely by Stripe.</p>
          <p className="mt-1">
            Keep this confirmation for your records. A receipt has been emailed to you.
          </p>
        </div>
      </div>
    </div>
  );
}

function PaymentSuccessLoading() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="mx-auto mb-4 h-16 w-16 animate-spin rounded-full border-4 border-blue-600 border-t-transparent"></div>
        <p className="text-gray-600">Loading payment details...</p>
      </div>
    </div>
  );
}

export default function PaymentSuccessPage() {
  return (
    <Suspense fallback={<PaymentSuccessLoading />}>
      <PaymentSuccessContent />
    </Suspense>
  );
}
