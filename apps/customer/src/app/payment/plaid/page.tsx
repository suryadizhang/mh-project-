'use client';

import { ArrowLeft, CheckCircle2, Loader2, AlertCircle, Zap } from 'lucide-react';
import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { usePlaidLink, type PlaidLinkOnSuccessMetadata } from 'react-plaid-link';

interface PaymentData {
  baseAmount: number;
  tipAmount: number;
  subtotal: number;
  selectedMethod?: string;
}

/**
 * Plaid RTP Payment Page
 *
 * Features:
 * - Plaid Link for bank account connection
 * - Real-time payment (RTP) processing
 * - FREE + Instant (best option!)
 * - No processing fees
 */
export default function PlaidPaymentPage() {
  const router = useRouter();
  const [paymentData, setPaymentData] = useState<PaymentData | null>(null);
  const [linkToken, setLinkToken] = useState<string | null>(null);
  const [isLoadingToken, setIsLoadingToken] = useState(true);
  const [error, setError] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  useEffect(() => {
    // Load payment data from sessionStorage
    const storedData = sessionStorage.getItem('paymentData');
    if (!storedData) {
      router.push('/payment');
      return;
    }

    const data: PaymentData = JSON.parse(storedData);
    setPaymentData(data);

    // Create Plaid link token
    createLinkToken();
  }, [router]);

  // Create Plaid link token from backend
  const createLinkToken = async () => {
    try {
      setIsLoadingToken(true);
      setError('');

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/plaid/create-link-token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: 'customer-' + Date.now(), // In production, use actual user ID
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create Plaid link token');
      }

      const data = await response.json();
      setLinkToken(data.link_token);
    } catch (err) {
      console.error('Error creating link token:', err);
      setError('Unable to initialize bank connection. Please try again or use another payment method.');
    } finally {
      setIsLoadingToken(false);
    }
  };

  // Handle successful Plaid Link
  const onSuccess = useCallback(async (public_token: string, metadata: PlaidLinkOnSuccessMetadata) => {
    try {
      setIsProcessing(true);
      setError('');

      if (!paymentData) return;

      // Get account_id from metadata
      const account_id = metadata.accounts?.[0]?.id || '';

      // Exchange public token for access token and initiate payment
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/plaid/initiate-payment`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          public_token,
          account_id,
          amount: paymentData.subtotal,
          description: `Payment of $${paymentData.subtotal.toFixed(2)}`,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Payment failed');
      }

      const result = await response.json();

      // Payment successful!
      setIsSuccess(true);

      // Redirect to success page
      setTimeout(() => {
        router.push('/payment/success?method=plaid&transfer_id=' + result.transfer_id);
      }, 2000);
    } catch (err) {
      console.error('Error processing payment:', err);
      const errorMessage = err instanceof Error ? err.message : 'Payment failed. Please try again.';
      setError(errorMessage);
      setIsProcessing(false);
    }
  }, [paymentData, router]);

  // Handle Plaid Link exit
  const onExit = useCallback((err: unknown) => {
    if (err != null) {
      console.error('Plaid Link error:', err);
      setError('Bank connection cancelled or failed. Please try again.');
    }
  }, []);

  // Initialize Plaid Link
  const config = {
    token: linkToken || '',
    onSuccess,
    onExit,
  };

  const { open, ready } = usePlaidLink(config);

  const handleBack = () => {
    router.push('/payment/select-method');
  };

  const handleOpenPlaidLink = () => {
    if (ready) {
      open();
    }
  };

  // Loading state
  if (!paymentData || isLoadingToken) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-green-50 to-gray-100">
        <div className="text-center">
          <Loader2 className="mx-auto mb-4 h-12 w-12 animate-spin text-green-600" />
          <p className="text-lg font-medium text-gray-700">Initializing secure bank connection...</p>
        </div>
      </div>
    );
  }

  // Success state
  if (isSuccess) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-green-50 to-gray-100 px-4">
        <div className="max-w-md rounded-2xl bg-white p-8 text-center shadow-2xl">
          <div className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-green-100">
            <CheckCircle2 className="h-12 w-12 text-green-600" />
          </div>
          <h2 className="mb-2 text-3xl font-bold text-gray-900">Payment Successful!</h2>
          <p className="mb-6 text-gray-600">
            Your payment of ${paymentData.subtotal.toFixed(2)} has been processed instantly.
          </p>
          <Loader2 className="mx-auto h-6 w-6 animate-spin text-green-600" />
          <p className="mt-2 text-sm text-gray-500">Redirecting...</p>
        </div>
      </div>
    );
  }

  // Processing state
  if (isProcessing) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-green-50 to-gray-100 px-4">
        <div className="max-w-md rounded-2xl bg-white p-8 text-center shadow-2xl">
          <Loader2 className="mx-auto mb-4 h-12 w-12 animate-spin text-green-600" />
          <h2 className="mb-2 text-2xl font-bold text-gray-900">Processing Payment...</h2>
          <p className="text-gray-600">
            Please wait while we process your instant bank transfer.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-gray-100 px-4 py-8">
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
            <div className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-green-600 to-green-700 text-3xl font-bold text-white shadow-lg">
              🏦
            </div>
            <h1 className="mb-2 text-3xl font-bold text-gray-900">Bank Transfer (Plaid RTP)</h1>
            <div className="flex items-center justify-center gap-2">
              <span className="rounded-full bg-green-100 px-3 py-1 text-sm font-bold text-green-800">
                FREE ✨
              </span>
              <span className="rounded-full bg-blue-100 px-3 py-1 text-sm font-bold text-blue-800">
                <Zap className="mr-1 inline h-4 w-4" />
                INSTANT
              </span>
              <span className="rounded-full bg-yellow-100 px-3 py-1 text-sm font-bold text-yellow-800">
                ⭐ BEST
              </span>
            </div>
          </div>

          {/* Amount Summary */}
          <div className="mb-8 rounded-xl bg-gradient-to-r from-green-50 to-emerald-100 p-6">
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
              <div className="flex justify-between border-t border-green-200 pt-2">
                <span className="text-green-600">Processing Fee:</span>
                <span className="font-bold text-green-600">FREE ✨</span>
              </div>
              <div className="flex justify-between border-t border-green-300 pt-2">
                <span className="text-lg font-bold text-gray-900">Total Amount:</span>
                <span className="text-2xl font-bold text-green-600">
                  ${paymentData.subtotal.toFixed(2)}
                </span>
              </div>
            </div>
          </div>

          {/* Benefits Section */}
          <div className="mb-8 space-y-3">
            <h2 className="text-lg font-semibold text-gray-900">Why Choose Bank Transfer?</h2>
            <div className="space-y-2">
              <div className="flex items-start gap-3 rounded-lg bg-green-50 p-3">
                <CheckCircle2 className="mt-0.5 h-5 w-5 flex-shrink-0 text-green-600" />
                <div>
                  <p className="font-medium text-gray-900">No Processing Fees</p>
                  <p className="text-sm text-gray-600">
                    Save ${((paymentData.subtotal * 0.03).toFixed(2))} compared to credit cards
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3 rounded-lg bg-blue-50 p-3">
                <Zap className="mt-0.5 h-5 w-5 flex-shrink-0 text-blue-600" />
                <div>
                  <p className="font-medium text-gray-900">Instant Processing</p>
                  <p className="text-sm text-gray-600">
                    Payment processed immediately - no waiting!
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3 rounded-lg bg-purple-50 p-3">
                <svg className="mt-0.5 h-5 w-5 flex-shrink-0 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                <div>
                  <p className="font-medium text-gray-900">Bank-Level Security</p>
                  <p className="text-sm text-gray-600">
                    Secured by Plaid with 256-bit encryption
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-red-600" />
                <div>
                  <h3 className="font-semibold text-red-900">Payment Error</h3>
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Connect Bank Button */}
          <button
            onClick={handleOpenPlaidLink}
            disabled={!ready || isProcessing}
            className="group flex w-full items-center justify-center gap-3 rounded-xl bg-gradient-to-r from-green-600 to-green-700 px-8 py-5 text-lg font-semibold text-white shadow-lg transition-all hover:from-green-700 hover:to-green-800 hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-50"
          >
            <svg className="h-6 w-6 transition-transform group-hover:scale-110" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
            </svg>
            <span>Connect Your Bank Account</span>
          </button>

          {/* Help Text */}
          <p className="mt-4 text-center text-xs text-gray-500">
            You&apos;ll be redirected to securely connect your bank account
          </p>

          {/* How It Works */}
          <div className="mt-8 rounded-lg border border-gray-200 bg-gray-50 p-4">
            <h3 className="mb-3 font-semibold text-gray-900">How It Works</h3>
            <ol className="space-y-2 text-sm text-gray-700">
              <li className="flex items-start gap-2">
                <span className="font-bold text-green-600">1.</span>
                <span>Click the button above to connect your bank account securely</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="font-bold text-green-600">2.</span>
                <span>Select your bank and log in with your credentials</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="font-bold text-green-600">3.</span>
                <span>Authorize the payment - it processes instantly!</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="font-bold text-green-600">4.</span>
                <span>Receive instant confirmation</span>
              </li>
            </ol>
          </div>
        </div>

        {/* Security Badge */}
        <div className="mt-6 text-center">
          <p className="flex items-center justify-center gap-2 text-sm text-gray-600">
            <svg className="h-5 w-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            Secured by Plaid - Trusted by millions
          </p>
        </div>
      </div>
    </div>
  );
}
