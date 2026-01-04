'use client';

import { PaymentIntentResponseSchema } from '@myhibachi/types/schemas';
import { Elements } from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';
import { Calendar, CreditCard, DollarSign, Loader2, MapPin, Shield, Users } from 'lucide-react';
import { useEffect, useState } from 'react';
import type { z } from 'zod';

import CustomerSavingsDisplay from '@/components/CustomerSavingsDisplay';
import { LazyAlternativePaymentOptions, LazyPaymentForm } from '@/components/lazy';
import BookingLookup from '@/components/payment/BookingLookup';
import { apiFetch } from '@/lib/api';
import { logger } from '@/lib/logger';

// Infer type from schema for type-safe responses
type PaymentIntentResponse = z.infer<typeof PaymentIntentResponseSchema>;

// Initialize Stripe
const stripePublishableKey = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY;
const stripePromise = stripePublishableKey ? loadStripe(stripePublishableKey) : null;

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
  services: Array<{ name: string; price: number }>;
}

export default function PaymentPage() {
  const [selectedBooking, setSelectedBooking] = useState<BookingData | null>(null);
  const [paymentType, setPaymentType] = useState<'deposit' | 'balance'>('deposit');
  const [customAmount, setCustomAmount] = useState('');
  const [tipAmount, setTipAmount] = useState('');
  const [paymentMethod, setPaymentMethod] = useState<'stripe' | 'zelle' | 'venmo'>('stripe');
  const [isLoading, setIsLoading] = useState(false);
  const [clientSecret, setClientSecret] = useState<string | null>(null);
  const [stripeElementsKey, setStripeElementsKey] = useState(0); // Force re-render

  // Calculate totals
  const baseAmount = selectedBooking
    ? paymentType === 'deposit'
      ? selectedBooking.depositAmount
      : selectedBooking.remainingBalance
    : parseFloat(customAmount) || 0;

  const tipValue = parseFloat(tipAmount) || 0;
  const subtotal = baseAmount + tipValue;

  // Add processing fees based on payment method
  const processingFee =
    paymentMethod === 'stripe' ? subtotal * 0.08 : paymentMethod === 'venmo' ? subtotal * 0.03 : 0;
  const totalAmount = subtotal + processingFee;

  // Create payment intent when amount changes and using Stripe
  useEffect(() => {
    const createPaymentIntent = async () => {
      try {
        setIsLoading(true);
        const response = await apiFetch<PaymentIntentResponse>('/api/v1/payments/create-intent', {
          method: 'POST',
          body: JSON.stringify({
            amount: Math.round(totalAmount * 100), // Convert to cents
            currency: 'usd',
            bookingId: selectedBooking?.id || null,
            paymentType,
            tipAmount: Math.round(tipValue * 100),
            customerInfo: {
              name: selectedBooking?.customerName || 'Guest User',
              email: selectedBooking?.customerEmail || 'guest@example.com',
              phone: '',
              address: '',
              city: '',
              state: '',
              zipCode: '',
            },
            metadata: {
              bookingId: selectedBooking?.id || 'manual-payment',
              customerName: selectedBooking?.customerName || 'Guest User',
              eventDate: selectedBooking?.eventDate || 'N/A',
              paymentType,
            },
          }),
          schema: PaymentIntentResponseSchema,
        });

        if (!response.success || !response.data) {
          throw new Error(response.error || 'Failed to create payment intent');
        }

        // Type-safe access to clientSecret
        const newClientSecret = response.data.clientSecret;
        setClientSecret(newClientSecret);
        setStripeElementsKey((prev) => prev + 1); // Force Elements re-render
      } catch (error) {
        logger.error('Error creating payment intent', error as Error, {
          amount: totalAmount,
          method: paymentMethod,
        });
        setClientSecret(null);
      } finally {
        setIsLoading(false);
      }
    };

    if (paymentMethod === 'stripe' && totalAmount > 0) {
      createPaymentIntent();
    } else {
      setClientSecret(null);
    }
  }, [totalAmount, paymentMethod, selectedBooking, paymentType, tipValue]);

  const appearance = {
    theme: 'stripe' as const,
    variables: {
      colorPrimary: '#dc2626',
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
        loader: 'auto' as const,
      }
    : {
        appearance,
        loader: 'auto' as const,
      };

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-8">
      <div className="mx-auto max-w-4xl">
        {/* Header */}
        <div className="mb-8 rounded-xl bg-white p-8 shadow-lg">
          <div className="text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
              <DollarSign className="h-8 w-8 text-red-600" />
            </div>
            <h1 className="mb-2 text-3xl font-bold text-gray-900">My Hibachi Payment Portal</h1>
            <p className="mx-auto max-w-2xl text-gray-600">
              Secure payment processing for your hibachi booking. Pay your deposit to lock in your
              date or settle your remaining balance with optional tips.
            </p>
          </div>

          {/* Security Badge */}
          <div className="mt-6 flex items-center justify-center rounded-lg border border-green-200 bg-green-50 p-4">
            <Shield className="mr-2 h-5 w-5 text-green-600" />
            <span className="font-medium text-green-800">
              Secured by Stripe with 2-Factor Authentication
            </span>
          </div>
        </div>

        <div className="grid gap-8 lg:grid-cols-3">
          {/* Left Column - Booking Lookup */}
          <div className="lg:col-span-1">
            <BookingLookup
              onBookingFound={setSelectedBooking}
              isLoading={isLoading}
              setIsLoading={setIsLoading}
            />

            {/* Customer Savings Display */}
            {selectedBooking?.customerEmail && (
              <div className="mt-6">
                <CustomerSavingsDisplay customerEmail={selectedBooking.customerEmail} />
              </div>
            )}

            {/* Manual Amount Entry */}
            {!selectedBooking && (
              <div className="mt-6 rounded-xl bg-white p-6 shadow-lg">
                <h3 className="mb-4 text-lg font-semibold text-gray-900">Or Enter Custom Amount</h3>
                <div className="space-y-4">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700">
                      Amount to Pay
                    </label>
                    <div className="relative">
                      <span className="absolute top-1/2 left-3 -translate-y-1/2 transform text-gray-500">
                        $
                      </span>
                      <input
                        type="number"
                        value={customAmount}
                        onChange={(e) => setCustomAmount(e.target.value)}
                        placeholder="0.00"
                        className="w-full rounded-lg border border-gray-300 py-3 pr-4 pl-8 focus:border-transparent focus:ring-2 focus:ring-red-500"
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Right Column - Payment Details */}
          <div className="lg:col-span-2">
            {/* Booking Summary */}
            {selectedBooking && (
              <div className="mb-6 rounded-xl bg-white p-6 shadow-lg">
                <h3 className="mb-4 flex items-center text-lg font-semibold text-gray-900">
                  <Users className="mr-2 h-5 w-5 text-red-600" />
                  Booking Details
                </h3>
                <div className="grid gap-4 text-sm md:grid-cols-2">
                  <div>
                    <div className="mb-2 flex items-center text-gray-600">
                      <Calendar className="mr-2 h-4 w-4" />
                      <span>
                        {selectedBooking.eventDate} at {selectedBooking.eventTime}
                      </span>
                    </div>
                    <div className="mb-2 flex items-center text-gray-600">
                      <Users className="mr-2 h-4 w-4" />
                      <span>{selectedBooking.guestCount} guests</span>
                    </div>
                    <div className="flex items-center text-gray-600">
                      <MapPin className="mr-2 h-4 w-4" />
                      <span>{selectedBooking.venueAddress}</span>
                    </div>
                  </div>
                  <div className="rounded-lg bg-gray-50 p-4">
                    <div className="mb-2 text-xs tracking-wide text-gray-500 uppercase">
                      Payment Status
                    </div>
                    <div className="text-sm">
                      <div className="flex justify-between">
                        <span>Total Event Cost:</span>
                        <span className="font-medium">
                          ${selectedBooking.totalAmount.toFixed(2)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Deposit Paid:</span>
                        <span
                          className={
                            selectedBooking.depositPaid ? 'text-green-600' : 'text-red-600'
                          }
                        >
                          {selectedBooking.depositPaid
                            ? `$${selectedBooking.depositAmount.toFixed(2)}`
                            : 'Not Paid'}
                        </span>
                      </div>
                      <div className="mt-2 flex justify-between border-t pt-2">
                        <span className="font-medium">Remaining Balance:</span>
                        <span className="font-medium">
                          ${selectedBooking.remainingBalance.toFixed(2)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Payment Type Selection */}
            {selectedBooking && (
              <div className="mb-6 rounded-xl bg-white p-6 shadow-lg">
                <h3 className="mb-4 text-lg font-semibold text-gray-900">Select Payment Type</h3>
                <div className="grid gap-4 md:grid-cols-2">
                  <button
                    onClick={() => setPaymentType('deposit')}
                    disabled={selectedBooking.depositPaid}
                    className={`rounded-lg border-2 p-4 transition-all ${
                      paymentType === 'deposit'
                        ? 'border-red-500 bg-red-50'
                        : 'border-gray-200 hover:border-gray-300'
                    } ${selectedBooking.depositPaid ? 'cursor-not-allowed opacity-50' : ''}`}
                  >
                    <div className="text-left">
                      <div className="font-medium">Deposit Payment</div>
                      <div className="text-sm text-gray-600">
                        ${selectedBooking.depositAmount.toFixed(2)} to secure your booking
                      </div>
                      {selectedBooking.depositPaid && (
                        <div className="mt-1 text-xs text-green-600">✓ Already Paid</div>
                      )}
                    </div>
                  </button>
                  <button
                    onClick={() => setPaymentType('balance')}
                    className={`rounded-lg border-2 p-4 transition-all ${
                      paymentType === 'balance'
                        ? 'border-red-500 bg-red-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="text-left">
                      <div className="font-medium">Remaining Balance</div>
                      <div className="text-sm text-gray-600">
                        ${selectedBooking.remainingBalance.toFixed(2)} + optional tips
                      </div>
                    </div>
                  </button>
                </div>
              </div>
            )}

            {/* Payment Method Selection */}
            <div className="mb-6 rounded-xl bg-white p-6 shadow-lg">
              <h3 className="mb-4 text-lg font-semibold text-gray-900">Choose Payment Method</h3>
              <div className="grid gap-4 md:grid-cols-3">
                <button
                  onClick={() => setPaymentMethod('stripe')}
                  className={`rounded-lg border-2 p-4 transition-all ${
                    paymentMethod === 'stripe'
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <CreditCard className="mx-auto mb-2 h-6 w-6 text-blue-600" />
                  <div className="text-sm font-medium">Credit Card</div>
                  <div className="text-xs text-gray-600">+8% processing fee</div>
                </button>
                <button
                  onClick={() => setPaymentMethod('zelle')}
                  className={`rounded-lg border-2 p-4 transition-all ${
                    paymentMethod === 'zelle'
                      ? 'border-purple-500 bg-purple-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="mx-auto mb-2 flex h-6 w-6 items-center justify-center rounded bg-purple-600 text-xs font-bold text-white">
                    Z
                  </div>
                  <div className="text-sm font-medium">Zelle</div>
                  <div className="text-xs text-gray-600">No fees</div>
                </button>
                <button
                  onClick={() => setPaymentMethod('venmo')}
                  className={`rounded-lg border-2 p-4 transition-all ${
                    paymentMethod === 'venmo'
                      ? 'border-blue-400 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="mx-auto mb-2 flex h-6 w-6 items-center justify-center rounded bg-blue-400 text-xs font-bold text-white">
                    V
                  </div>
                  <div className="text-sm font-medium">Venmo</div>
                  <div className="text-xs text-gray-600">+3% processing fee</div>
                </button>
              </div>
            </div>

            {/* Tips/Gratuity */}
            <div className="mb-6 rounded-xl bg-white p-6 shadow-lg">
              <h3 className="mb-4 text-lg font-semibold text-gray-900">
                Add Tip/Gratuity (Optional)
              </h3>
              <div className="mb-4 grid grid-cols-4 gap-3">
                {[20, 25, 30, 35].map((percent) => {
                  const tipValue = ((baseAmount * percent) / 100).toFixed(2);
                  return (
                    <button
                      key={percent}
                      onClick={() => setTipAmount(tipValue)}
                      className="rounded-lg border border-gray-300 p-3 text-center transition-all hover:border-red-500 hover:bg-red-50"
                    >
                      <div className="font-medium">{percent}%</div>
                      <div className="text-sm text-gray-600">${tipValue}</div>
                    </button>
                  );
                })}
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Custom Tip Amount
                </label>
                <div className="relative">
                  <span className="absolute top-1/2 left-3 -translate-y-1/2 transform text-gray-500">
                    $
                  </span>
                  <input
                    type="number"
                    value={tipAmount}
                    onChange={(e) => setTipAmount(e.target.value)}
                    placeholder="0.00"
                    className="w-full rounded-lg border border-gray-300 py-3 pr-4 pl-8 focus:border-transparent focus:ring-2 focus:ring-red-500"
                  />
                </div>
              </div>
            </div>

            {/* Payment Summary */}
            <div className="mb-6 rounded-xl bg-white p-6 shadow-lg">
              <h3 className="mb-4 text-lg font-semibold text-gray-900">Payment Summary</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Base Amount:</span>
                  <span>${baseAmount.toFixed(2)}</span>
                </div>
                {tipValue > 0 && (
                  <div className="flex justify-between">
                    <span>Tip/Gratuity:</span>
                    <span>${tipValue.toFixed(2)}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span>Subtotal:</span>
                  <span>${subtotal.toFixed(2)}</span>
                </div>
                {paymentMethod === 'stripe' && processingFee > 0 && (
                  <div className="flex justify-between text-orange-600">
                    <span>Processing Fee (8%):</span>
                    <span>${processingFee.toFixed(2)}</span>
                  </div>
                )}
                {paymentMethod === 'venmo' && processingFee > 0 && (
                  <div className="flex justify-between text-blue-600">
                    <span>Processing Fee (3%):</span>
                    <span>${processingFee.toFixed(2)}</span>
                  </div>
                )}
                <div className="mt-2 border-t pt-2">
                  <div className="flex justify-between text-lg font-bold">
                    <span>Total Amount:</span>
                    <span className="text-red-600">${totalAmount.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Payment Form */}
            {paymentMethod === 'stripe' ? (
              stripePromise ? (
                clientSecret ? (
                  <Elements key={stripeElementsKey} stripe={stripePromise} options={options}>
                    <LazyPaymentForm
                      amount={totalAmount}
                      bookingData={selectedBooking}
                      paymentType={paymentType}
                      tipAmount={tipValue}
                      clientSecret={clientSecret}
                    />
                  </Elements>
                ) : (
                  <div className="rounded-xl bg-white p-8 text-center shadow-lg">
                    <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-blue-100">
                      <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
                    </div>
                    <h3 className="mb-2 text-xl font-bold text-gray-900">Preparing Payment...</h3>
                    <p className="text-gray-600">
                      Setting up secure payment processing. This will only take a moment.
                    </p>
                  </div>
                )
              ) : (
                <div className="rounded-xl bg-white p-8 text-center shadow-lg">
                  <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
                    <CreditCard className="h-8 w-8 text-red-600" />
                  </div>
                  <h3 className="mb-2 text-xl font-bold text-gray-900">
                    Payment Processing Unavailable
                  </h3>
                  <p className="mb-4 text-gray-600">
                    Credit card processing is currently not configured. Please use Zelle or Venmo
                    instead.
                  </p>
                  <button
                    onClick={() => setPaymentMethod('zelle')}
                    className="mr-2 rounded-lg bg-purple-600 px-6 py-3 text-white transition-colors hover:bg-purple-700"
                  >
                    Use Zelle
                  </button>
                  <button
                    onClick={() => setPaymentMethod('venmo')}
                    className="rounded-lg bg-blue-600 px-6 py-3 text-white transition-colors hover:bg-blue-700"
                  >
                    Use Venmo
                  </button>
                </div>
              )
            ) : (
              <LazyAlternativePaymentOptions
                method={paymentMethod}
                amount={totalAmount}
                bookingData={selectedBooking}
                paymentType={paymentType}
                tipAmount={tipValue}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
