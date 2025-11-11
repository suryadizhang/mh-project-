'use client';

import { ArrowLeft, Loader2, AlertCircle } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

import { PaymentMethodCard } from '@/components/payment/PaymentMethodCard';

interface PaymentData {
  baseAmount: number;
  tipAmount: number;
  subtotal: number;
}

interface PaymentMethod {
  method: string;
  name: string;
  icon: string;
  color: string;
  total_amount: number;
  processing_fee: number;
  savings_vs_stripe: number;
  is_free: boolean;
  is_instant: boolean;
  confirmation_time: string;
}

interface CompareResponse {
  base_amount: number;
  tip_amount: number;
  subtotal: number;
  methods: PaymentMethod[];
  recommendation: string;
}

/**
 * Payment Method Selection Page - Step 2 of Payment Flow
 *
 * Displays 4 payment method cards:
 * - Zelle (FREE, 1-2 hours)
 * - Plaid RTP (FREE, Instant) ⭐ BEST
 * - Venmo (3% fee, 1-2 hours)
 * - Stripe (3% fee, Instant)
 *
 * Fetches real-time fee calculations from API
 */
export default function SelectMethodPage() {
  const router = useRouter();
  const [paymentData, setPaymentData] = useState<PaymentData | null>(null);
  const [methods, setMethods] = useState<PaymentMethod[]>([]);
  const [recommendation, setRecommendation] = useState('');
  const [selectedMethod, setSelectedMethod] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // Load payment data from sessionStorage
  useEffect(() => {
    const storedData = sessionStorage.getItem('paymentData');
    if (!storedData) {
      // Redirect back to payment input if no data
      router.push('/payment');
      return;
    }

    const data: PaymentData = JSON.parse(storedData);
    setPaymentData(data);

    // Fetch payment method comparison from API
    fetchPaymentMethods(data);
  }, [router]);

  // Fetch payment methods from API
  const fetchPaymentMethods = async (data: PaymentData) => {
    try {
      setIsLoading(true);
      setError('');

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/payments/compare`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          base_amount: data.baseAmount,
          tip_amount: data.tipAmount,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch payment methods');
      }

      const result: CompareResponse = await response.json();
      setMethods(result.methods);
      setRecommendation(result.recommendation);

      // Auto-select best method (Plaid RTP)
      const bestMethod = result.methods.find(m => m.is_free && m.is_instant);
      if (bestMethod) {
        setSelectedMethod(bestMethod.method);
      }
    } catch (err) {
      console.error('Error fetching payment methods:', err);
      setError('Unable to load payment methods. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle method selection and navigation
  const handleMethodSelect = (methodId: string) => {
    setSelectedMethod(methodId);
  };

  const handleContinue = () => {
    if (!selectedMethod) return;

    // Store selected method in sessionStorage
    const currentData = sessionStorage.getItem('paymentData');
    if (currentData) {
      const data = JSON.parse(currentData);
      data.selectedMethod = selectedMethod;
      sessionStorage.setItem('paymentData', JSON.stringify(data));
    }

    // Navigate to method-specific page
    router.push(`/payment/${selectedMethod}`);
  };

  const handleBack = () => {
    router.push('/payment');
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100">
        <div className="text-center">
          <Loader2 className="mx-auto mb-4 h-12 w-12 animate-spin text-red-600" />
          <p className="text-lg font-medium text-gray-700">Loading payment methods...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 px-4">
        <div className="max-w-md rounded-2xl bg-white p-8 text-center shadow-xl">
          <AlertCircle className="mx-auto mb-4 h-12 w-12 text-red-600" />
          <h2 className="mb-2 text-2xl font-bold text-gray-900">Error Loading Methods</h2>
          <p className="mb-6 text-gray-600">{error}</p>
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
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 px-4 py-8">
      <div className="mx-auto max-w-7xl">
        {/* Back Button */}
        <button
          onClick={handleBack}
          className="mb-6 flex items-center gap-2 text-gray-600 transition-colors hover:text-gray-900"
        >
          <ArrowLeft className="h-5 w-5" />
          <span className="font-medium">Back to Payment Input</span>
        </button>

        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="mb-3 text-4xl font-bold text-gray-900">Choose Your Payment Method</h1>
          <p className="text-lg text-gray-600">Select the best option for your payment</p>
        </div>

        {/* Payment Summary Card */}
        {paymentData && (
          <div className="mx-auto mb-8 max-w-2xl rounded-2xl bg-white p-6 shadow-lg">
            <h3 className="mb-4 text-lg font-semibold text-gray-900">Payment Details</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Base Amount:</span>
                <span className="font-medium text-gray-900">${paymentData.baseAmount.toFixed(2)}</span>
              </div>
              {paymentData.tipAmount > 0 && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Tip:</span>
                  <span className="font-medium text-gray-900">${paymentData.tipAmount.toFixed(2)}</span>
                </div>
              )}
              <div className="flex justify-between border-t pt-2">
                <span className="font-semibold text-gray-900">Subtotal:</span>
                <span className="text-xl font-bold text-gray-900">${paymentData.subtotal.toFixed(2)}</span>
              </div>
            </div>
          </div>
        )}

        {/* Payment Method Cards Grid */}
        <div className="mx-auto mb-8 grid max-w-6xl gap-6 md:grid-cols-2 lg:grid-cols-4">
          {methods.map((method) => (
            <PaymentMethodCard
              key={method.method}
              method={{
                id: method.method,
                name: method.name,
                icon: method.icon,
                color: method.color,
                totalAmount: method.total_amount,
                processingFee: method.processing_fee,
                isFree: method.is_free,
                isInstant: method.is_instant,
                confirmationTime: method.confirmation_time,
                savingsVsStripe: method.savings_vs_stripe,
              }}
              selected={selectedMethod === method.method}
              onSelect={() => handleMethodSelect(method.method)}
            />
          ))}
        </div>

        {/* Recommendation Banner */}
        {recommendation && (
          <div className="mx-auto mb-8 max-w-3xl rounded-2xl bg-gradient-to-r from-green-50 to-emerald-50 p-6 shadow-md">
            <div className="flex items-start gap-4">
              <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-green-500 text-xl">
                💡
              </div>
              <div>
                <h3 className="mb-1 text-lg font-bold text-gray-900">Recommendation</h3>
                <p className="text-gray-700">{recommendation}</p>
              </div>
            </div>
          </div>
        )}

        {/* Continue Button */}
        <div className="mx-auto max-w-2xl">
          <button
            onClick={handleContinue}
            disabled={!selectedMethod}
            className="w-full rounded-xl bg-gradient-to-r from-red-600 to-red-700 px-8 py-5 text-lg font-semibold text-white shadow-lg transition-all hover:from-red-700 hover:to-red-800 hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:from-red-600 disabled:hover:to-red-700"
          >
            {selectedMethod
              ? `Continue with ${methods.find(m => m.method === selectedMethod)?.name || 'Selected Method'}`
              : 'Select a Payment Method'
            }
          </button>
        </div>

        {/* Info Box */}
        <div className="mx-auto mt-6 max-w-2xl rounded-lg border border-blue-200 bg-blue-50 p-4">
          <p className="text-sm text-blue-800">
            <strong>💳 All payment methods are secure.</strong> Processing fees are added on top of your subtotal.
            FREE methods save you money!
          </p>
        </div>
      </div>
    </div>
  );
}
