'use client';

import { ArrowLeft, Loader2, CreditCard, Lock } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Elements, PaymentElement, useStripe, useElements } from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';

interface PaymentData {
  baseAmount: number;
  tipAmount: number;
  subtotal: number;
  selectedMethod?: string;
}

// Initialize Stripe
const stripePublishableKey = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY;
const stripePromise = stripePublishableKey ? loadStripe(stripePublishableKey) : null;

/**
 * Stripe Payment Form Component (wrapped in Elements)
 */
function StripePaymentForm({ totalAmount, onBack }: { totalAmount: number; onBack: () => void }) {
  const stripe = useStripe();
  const elements = useElements();
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!stripe || !elements) {
      return;
    }

    setIsProcessing(true);
    setError('');

    try {
      const { error: submitError } = await elements.submit();
      if (submitError) {
        throw new Error(submitError.message || 'Payment failed');
      }

      const { error: confirmError } = await stripe.confirmPayment({
        elements,
        confirmParams: {
          return_url: `${window.location.origin}/payment/success?method=stripe`,
        },
      });

      if (confirmError) {
        throw new Error(confirmError.message || 'Payment failed');
      }

      // If we reach here, payment was successful
      // (usually redirects before this)
    } catch (err) {
      console.error('Error processing payment:', err);
      const errorMessage = err instanceof Error ? err.message : 'Payment failed. Please try again.';
      setError(errorMessage);
      setIsProcessing(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Payment Element */}
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <PaymentElement />
      </div>

      {/* Error Display */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Buttons */}
      <div className="flex gap-4">
        <button
          type="button"
          onClick={onBack}
          disabled={isProcessing}
          className="flex-1 rounded-xl border-2 border-gray-300 px-6 py-4 font-semibold text-gray-700 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Back
        </button>
        <button
          type="submit"
          disabled={!stripe || isProcessing}
          className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-orange-600 to-red-600 px-6 py-4 font-semibold text-white shadow-lg transition-all hover:from-orange-700 hover:to-red-700 hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isProcessing ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" />
              <span>Processing...</span>
            </>
          ) : (
            <>
              <Lock className="h-5 w-5" />
              <span>Pay ${totalAmount.toFixed(2)}</span>
            </>
          )}
        </button>
      </div>

      {/* Security Info */}
      <div className="rounded-lg border border-green-200 bg-green-50 p-3">
        <p className="text-center text-xs text-green-800">
          <Lock className="mr-1 inline h-4 w-4" />
          Your payment is secured with 256-bit SSL encryption
        </p>
      </div>
    </form>
  );
}

/**
 * Stripe Payment Page
 *
 * Features:
 * - Stripe Elements for card payment
 * - 3% processing fee
 * - Instant payment processing
 */
export default function StripePaymentPage() {
  const router = useRouter();
  const [paymentData, setPaymentData] = useState<PaymentData | null>(null);
  const [totalWithFee, setTotalWithFee] = useState(0);
  const [processingFee, setProcessingFee] = useState(0);
  const [clientSecret, setClientSecret] = useState<string | null>(null);
  const [isLoadingIntent, setIsLoadingIntent] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    // Load payment data from sessionStorage
    const storedData = sessionStorage.getItem('paymentData');
    if (!storedData) {
      router.push('/payment');
      return;
    }

    const data: PaymentData = JSON.parse(storedData);
    setPaymentData(data);

    // Calculate fee (3%)
    const fee = data.subtotal * 0.03;
    const total = data.subtotal + fee;
    setProcessingFee(fee);
    setTotalWithFee(total);

    // Create payment intent
    createPaymentIntent(total);
  }, [router]);

  // Create Stripe payment intent
  const createPaymentIntent = async (amount: number) => {
    try {
      setIsLoadingIntent(true);
      setError('');

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/payments/create-intent`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          amount: Math.round(amount * 100), // Convert to cents
          currency: 'usd',
          payment_method_types: ['card'],
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create payment intent');
      }

      const data = await response.json();
      setClientSecret(data.clientSecret || data.client_secret);
    } catch (err) {
      console.error('Error creating payment intent:', err);
      setError('Unable to initialize payment. Please try again or use another payment method.');
    } finally {
      setIsLoadingIntent(false);
    }
  };

  const handleBack = () => {
    router.push('/payment/select-method');
  };

  // Stripe Elements appearance
  const appearance = {
    theme: 'stripe' as const,
    variables: {
      colorPrimary: '#DC2626',
      colorBackground: '#ffffff',
      colorText: '#1f2937',
      colorDanger: '#ef4444',
      fontFamily: 'Inter, system-ui, sans-serif',
      spacingUnit: '4px',
      borderRadius: '8px',
    },
  };

  const options = clientSecret
    ? {
        clientSecret,
        appearance,
      }
    : undefined;

  // Loading state
  if (!paymentData || isLoadingIntent) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-orange-50 to-gray-100">
        <div className="text-center">
          <Loader2 className="mx-auto mb-4 h-12 w-12 animate-spin text-orange-600" />
          <p className="text-lg font-medium text-gray-700">Initializing secure payment...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !clientSecret) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-orange-50 to-gray-100 px-4">
        <div className="max-w-md rounded-2xl bg-white p-8 text-center shadow-2xl">
          <div className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-red-100">
            <CreditCard className="h-10 w-10 text-red-600" />
          </div>
          <h2 className="mb-2 text-2xl font-bold text-gray-900">Payment Unavailable</h2>
          <p className="mb-6 text-gray-600">
            {error || 'Unable to initialize payment. Please try another payment method.'}
          </p>
          <button
            onClick={handleBack}
            className="rounded-lg bg-red-600 px-6 py-3 font-semibold text-white hover:bg-red-700"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-gray-100 px-4 py-8">
      <div className="mx-auto max-w-2xl">
        {/* Back Button */}
        <button
          onClick={handleBack}
          className="mb-6 flex items-center gap-2 text-gray-600 transition-colors hover:text-gray-900"
        >
          <ArrowLeft className="h-5 w-5" />
          <span className="font-medium">Back to Payment Methods</span>
        </button>

        {/* Main Payment Card */}
        <div className="rounded-2xl bg-white p-8 shadow-2xl">
          {/* Header */}
          <div className="mb-6 text-center">
            <div className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-orange-600 to-red-600 text-3xl font-bold text-white shadow-lg">
              💳
            </div>
            <h1 className="mb-2 text-3xl font-bold text-gray-900">Pay with Credit Card</h1>
            <p className="text-gray-600">Secure payment via Stripe</p>
          </div>

          {/* Amount Summary */}
          <div className="mb-8 rounded-xl bg-gradient-to-r from-orange-50 to-red-50 p-6">
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Base Amount:</span>
                <span className="font-medium">${paymentData.baseAmount.toFixed(2)}</span>
              </div>
              {paymentData.tipAmount > 0 && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Tip:</span>
                  <span className="font-medium">${paymentData.tipAmount.toFixed(2)}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-gray-600">Subtotal:</span>
                <span className="font-medium">${paymentData.subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between border-t border-orange-200 pt-2">
                <span className="text-orange-600">Processing Fee (3%):</span>
                <span className="font-bold text-orange-600">+${processingFee.toFixed(2)}</span>
              </div>
              <div className="flex justify-between border-t border-orange-300 pt-2">
                <span className="text-lg font-bold text-gray-900">Total Amount:</span>
                <span className="text-2xl font-bold text-orange-600">
                  ${totalWithFee.toFixed(2)}
                </span>
              </div>
            </div>
          </div>

          {/* Fee Notice */}
          <div className="mb-8 rounded-lg border border-orange-200 bg-orange-50 p-4">
            <div className="flex items-start gap-3">
              <span className="text-2xl">💳</span>
              <div>
                <h3 className="mb-1 font-semibold text-gray-900">Processing Fee Applied</h3>
                <p className="text-sm text-gray-700">
                  A 3% processing fee (${processingFee.toFixed(2)}) has been added to cover credit
                  card processing costs. Consider using Bank Transfer (FREE!) to save money.
                </p>
              </div>
            </div>
          </div>

          {/* Stripe Payment Form */}
          {stripePromise && clientSecret && options && (
            <Elements stripe={stripePromise} options={options}>
              <StripePaymentForm totalAmount={totalWithFee} onBack={handleBack} />
            </Elements>
          )}

          {(!stripePromise || !clientSecret) && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-center">
              <p className="text-sm text-red-700">
                Stripe is not configured. Please contact support or use another payment method.
              </p>
            </div>
          )}
        </div>

        {/* Security Badge */}
        <div className="mt-6 text-center">
          <p className="flex items-center justify-center gap-2 text-sm text-gray-600">
            <svg className="h-5 w-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            PCI DSS Compliant - Secured by Stripe
          </p>
        </div>
      </div>
    </div>
  );
}
