'use client';'use client';



import { DollarSign, ArrowRight } from 'lucide-react';import { Elements } from '@stripe/react-stripe-js';

import { useState } from 'react';import { loadStripe } from '@stripe/stripe-js';

import { useRouter } from 'next/navigation';import { Calendar, CreditCard, DollarSign, Loader2, MapPin, Shield, Users } from 'lucide-react';

import { useEffect, useState } from 'react';

/**import type { z } from 'zod';

 * Payment Input Page - Step 1 of Payment Flowimport { PaymentIntentResponseSchema } from '@myhibachi/types/schemas';

 * 

 * User enters:import CustomerSavingsDisplay from '@/components/CustomerSavingsDisplay';

 * - Base amount (order balance)import BookingLookup from '@/components/payment/BookingLookup';

 * - Tip amount (optional)import { LazyAlternativePaymentOptions, LazyPaymentForm } from '@/components/lazy';

 * import { apiFetch } from '@/lib/api';

 * Then navigates to method selection pageimport { logger } from '@/lib/logger';

 */

export default function PaymentInputPage() {// Infer type from schema for type-safe responses

  const router = useRouter();type PaymentIntentResponse = z.infer<typeof PaymentIntentResponseSchema>;

  const [baseAmount, setBaseAmount] = useState('');

  const [tipAmount, setTipAmount] = useState('');// Initialize Stripe

  const [errors, setErrors] = useState({ base: '', tip: '' });const stripePublishableKey = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY;

const stripePromise = stripePublishableKey ? loadStripe(stripePublishableKey) : null;

  // Calculate subtotal

  const baseValue = parseFloat(baseAmount) || 0;interface BookingData {

  const tipValue = parseFloat(tipAmount) || 0;  id: string;

  const subtotal = baseValue + tipValue;  customerName: string;

  customerEmail: string;

  // Validate inputs  eventDate: string;

  const validateInputs = () => {  eventTime: string;

    const newErrors = { base: '', tip: '' };  guestCount: number;

    let isValid = true;  venueAddress: string;

  totalAmount: number;

    if (!baseAmount || baseValue <= 0) {  depositPaid: boolean;

      newErrors.base = 'Please enter a valid base amount';  depositAmount: number;

      isValid = false;  remainingBalance: number;

    }  services: Array<{ name: string; price: number }>;

}

    if (tipAmount && tipValue < 0) {

      newErrors.tip = 'Tip amount cannot be negative';export default function PaymentPage() {

      isValid = false;  const [selectedBooking, setSelectedBooking] = useState<BookingData | null>(null);

    }  const [paymentType, setPaymentType] = useState<'deposit' | 'balance'>('deposit');

  const [customAmount, setCustomAmount] = useState('');

    setErrors(newErrors);  const [tipAmount, setTipAmount] = useState('');

    return isValid;  const [paymentMethod, setPaymentMethod] = useState<'stripe' | 'zelle' | 'venmo'>('stripe');

  };  const [isLoading, setIsLoading] = useState(false);

  const [clientSecret, setClientSecret] = useState<string | null>(null);

  // Handle continue to payment methods  const [stripeElementsKey, setStripeElementsKey] = useState(0); // Force re-render

  const handleContinue = () => {

    if (validateInputs()) {  // Calculate totals

      // Store payment data in sessionStorage  const baseAmount = selectedBooking

      sessionStorage.setItem('paymentData', JSON.stringify({    ? paymentType === 'deposit'

        baseAmount: baseValue,      ? 100

        tipAmount: tipValue,      : selectedBooking.remainingBalance

        subtotal: subtotal,    : parseFloat(customAmount) || 0;

      }));

  const tipValue = parseFloat(tipAmount) || 0;

      // Navigate to method selection  const subtotal = baseAmount + tipValue;

      router.push('/payment/select-method');

    }  // Add processing fees based on payment method

  };  const processingFee =

    paymentMethod === 'stripe' ? subtotal * 0.08 : paymentMethod === 'venmo' ? subtotal * 0.03 : 0;

  // Quick tip buttons  const totalAmount = subtotal + processingFee;

  const quickTipPercentages = [15, 18, 20, 25];

  // Create payment intent when amount changes and using Stripe

  return (  useEffect(() => {

    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 px-4 py-12">    const createPaymentIntent = async () => {

      <div className="mx-auto max-w-2xl">      try {

        {/* Header */}        setIsLoading(true);

        <div className="mb-8 text-center">        const response = await apiFetch<PaymentIntentResponse>('/api/v1/payments/create-intent', {

          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-red-500 to-red-600 shadow-lg">          method: 'POST',

            <DollarSign className="h-8 w-8 text-white" />          body: JSON.stringify({

          </div>            amount: Math.round(totalAmount * 100), // Convert to cents

          <h1 className="mb-2 text-4xl font-bold text-gray-900">Payment Information</h1>            currency: 'usd',

          <p className="text-lg text-gray-600">            bookingId: selectedBooking?.id || null,

            Enter your payment amount and optional tip            paymentType,

          </p>            tipAmount: Math.round(tipValue * 100),

        </div>            customerInfo: {

              name: selectedBooking?.customerName || 'Guest User',

        {/* Payment Input Card */}              email: selectedBooking?.customerEmail || 'guest@example.com',

        <div className="rounded-2xl bg-white p-8 shadow-xl">              phone: '',

          <div className="space-y-6">              address: '',

            {/* Base Amount */}              city: '',

            <div>              state: '',

              <label htmlFor="baseAmount" className="mb-2 block text-sm font-semibold text-gray-700">              zipCode: '',

                Base Amount <span className="text-red-500">*</span>            },

              </label>            metadata: {

              <div className="relative">              bookingId: selectedBooking?.id || 'manual-payment',

                <span className="absolute top-1/2 left-4 -translate-y-1/2 transform text-xl font-medium text-gray-500">              customerName: selectedBooking?.customerName || 'Guest User',

                  $              eventDate: selectedBooking?.eventDate || 'N/A',

                </span>              paymentType,

                <input            },

                  id="baseAmount"          }),

                  type="number"          schema: PaymentIntentResponseSchema,

                  value={baseAmount}        });

                  onChange={(e) => {

                    setBaseAmount(e.target.value);        if (!response.success || !response.data) {

                    setErrors({ ...errors, base: '' });          throw new Error(response.error || 'Failed to create payment intent');

                  }}        }

                  placeholder="0.00"

                  step="0.01"        // Type-safe access to clientSecret

                  min="0"        const newClientSecret = response.data.clientSecret;

                  className={`w-full rounded-xl border-2 py-4 pr-4 pl-12 text-xl font-medium transition-colors        setClientSecret(newClientSecret);

                    ${errors.base         setStripeElementsKey((prev) => prev + 1); // Force Elements re-render

                      ? 'border-red-300 focus:border-red-500'       } catch (error) {

                      : 'border-gray-300 focus:border-red-500'        logger.error('Error creating payment intent', error as Error, {

                    }          amount: totalAmount,

                    focus:outline-none focus:ring-4 focus:ring-red-500/10`}          method: paymentMethod,

                />        });

              </div>        setClientSecret(null);

              {errors.base && (      } finally {

                <p className="mt-2 text-sm text-red-600">{errors.base}</p>        setIsLoading(false);

              )}      }

              <p className="mt-2 text-sm text-gray-500">    };

                Enter the order balance or amount you wish to pay

              </p>    if (paymentMethod === 'stripe' && totalAmount > 0) {

            </div>      createPaymentIntent();

    } else {

            {/* Quick Tip Buttons */}      setClientSecret(null);

            {baseValue > 0 && (    }

              <div>  }, [totalAmount, paymentMethod, selectedBooking, paymentType, tipValue]);

                <label className="mb-3 block text-sm font-semibold text-gray-700">

                  Quick Tip Amounts  const appearance = {

                </label>    theme: 'stripe' as const,

                <div className="grid grid-cols-4 gap-3">    variables: {

                  {quickTipPercentages.map((percentage) => {      colorPrimary: '#dc2626',

                    const tipValue = ((baseValue * percentage) / 100);      colorBackground: '#ffffff',

                    return (      colorText: '#1f2937',

                      <button      colorDanger: '#ef4444',

                        key={percentage}      fontFamily: 'Inter, system-ui, sans-serif',

                        onClick={() => setTipAmount(tipValue.toFixed(2))}      spacingUnit: '4px',

                        className="rounded-lg border-2 border-gray-300 p-3 text-center transition-all hover:border-red-500 hover:bg-red-50 focus:border-red-500 focus:bg-red-50 focus:outline-none"      borderRadius: '8px',

                      >    },

                        <div className="text-sm font-bold text-gray-900">{percentage}%</div>  };

                        <div className="text-xs text-gray-600">${tipValue.toFixed(2)}</div>

                      </button>  const options = clientSecret

                    );    ? {

                  })}        clientSecret,

                </div>        appearance,

              </div>        loader: 'auto' as const,

            )}      }

    : {

            {/* Tip Amount */}        appearance,

            <div>        loader: 'auto' as const,

              <label htmlFor="tipAmount" className="mb-2 block text-sm font-semibold text-gray-700">      };

                Tip Amount <span className="text-gray-400">(Optional)</span>

              </label>  return (

              <div className="relative">    <div className="min-h-screen bg-gray-50 px-4 py-8">

                <span className="absolute top-1/2 left-4 -translate-y-1/2 transform text-xl font-medium text-gray-500">      <div className="mx-auto max-w-4xl">

                  $        {/* Header */}

                </span>        <div className="mb-8 rounded-xl bg-white p-8 shadow-lg">

                <input          <div className="text-center">

                  id="tipAmount"            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-100">

                  type="number"              <DollarSign className="h-8 w-8 text-red-600" />

                  value={tipAmount}            </div>

                  onChange={(e) => {            <h1 className="mb-2 text-3xl font-bold text-gray-900">My Hibachi Payment Portal</h1>

                    setTipAmount(e.target.value);            <p className="mx-auto max-w-2xl text-gray-600">

                    setErrors({ ...errors, tip: '' });              Secure payment processing for your hibachi booking. Pay your deposit to lock in your

                  }}              date or settle your remaining balance with optional tips.

                  placeholder="0.00"            </p>

                  step="0.01"          </div>

                  min="0"

                  className={`w-full rounded-xl border-2 py-4 pr-4 pl-12 text-xl font-medium transition-colors          {/* Security Badge */}

                    ${errors.tip           <div className="mt-6 flex items-center justify-center rounded-lg border border-green-200 bg-green-50 p-4">

                      ? 'border-red-300 focus:border-red-500'             <Shield className="mr-2 h-5 w-5 text-green-600" />

                      : 'border-gray-300 focus:border-red-500'            <span className="font-medium text-green-800">

                    }              Secured by Stripe with 2-Factor Authentication

                    focus:outline-none focus:ring-4 focus:ring-red-500/10`}            </span>

                />          </div>

              </div>        </div>

              {errors.tip && (

                <p className="mt-2 text-sm text-red-600">{errors.tip}</p>        <div className="grid gap-8 lg:grid-cols-3">

              )}          {/* Left Column - Booking Lookup */}

              <p className="mt-2 text-sm text-gray-500">          <div className="lg:col-span-1">

                Show your appreciation for great service            <BookingLookup

              </p>              onBookingFound={setSelectedBooking}

            </div>              isLoading={isLoading}

              setIsLoading={setIsLoading}

            {/* Subtotal Display */}            />

            {subtotal > 0 && (

              <div className="rounded-xl bg-gradient-to-r from-gray-50 to-gray-100 p-6">            {/* Customer Savings Display */}

                <div className="flex items-center justify-between">            {selectedBooking?.customerEmail && (

                  <div>              <div className="mt-6">

                    <p className="text-sm font-medium text-gray-600">Subtotal Before Fees</p>                <CustomerSavingsDisplay customerEmail={selectedBooking.customerEmail} />

                    <p className="mt-1 text-3xl font-bold text-gray-900">              </div>

                      ${subtotal.toFixed(2)}            )}

                    </p>

                  </div>            {/* Manual Amount Entry */}

                  <div className="text-right">            {!selectedBooking && (

                    <p className="text-xs text-gray-500">Base: ${baseValue.toFixed(2)}</p>              <div className="mt-6 rounded-xl bg-white p-6 shadow-lg">

                    {tipValue > 0 && (                <h3 className="mb-4 text-lg font-semibold text-gray-900">Or Enter Custom Amount</h3>

                      <p className="text-xs text-gray-500">Tip: ${tipValue.toFixed(2)}</p>                <div className="space-y-4">

                    )}                  <div>

                  </div>                    <label className="mb-1 block text-sm font-medium text-gray-700">

                </div>                      Amount to Pay

              </div>                    </label>

            )}                    <div className="relative">

                      <span className="absolute top-1/2 left-3 -translate-y-1/2 transform text-gray-500">

            {/* Continue Button */}                        $

            <button                      </span>

              onClick={handleContinue}                      <input

              disabled={!baseAmount || baseValue <= 0}                        type="number"

              className="group flex w-full items-center justify-center gap-3 rounded-xl bg-gradient-to-r from-red-600 to-red-700 px-8 py-5 text-lg font-semibold text-white shadow-lg transition-all hover:from-red-700 hover:to-red-800 hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:from-red-600 disabled:hover:to-red-700"                        value={customAmount}

            >                        onChange={(e) => setCustomAmount(e.target.value)}

              <span>Continue to Payment Methods</span>                        placeholder="0.00"

              <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />                        className="w-full rounded-lg border border-gray-300 py-3 pr-4 pl-8 focus:border-transparent focus:ring-2 focus:ring-red-500"

            </button>                      />

                    </div>

            {/* Info Message */}                  </div>

            <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">                </div>

              <p className="text-sm text-blue-800">              </div>

                <strong>Next Step:</strong> You'll see 4 payment options with their total costs including any processing fees.            )}

              </p>          </div>

            </div>

          </div>          {/* Right Column - Payment Details */}

        </div>          <div className="lg:col-span-2">

            {/* Booking Summary */}

        {/* Security Badge */}            {selectedBooking && (

        <div className="mt-6 text-center">              <div className="mb-6 rounded-xl bg-white p-6 shadow-lg">

          <p className="flex items-center justify-center gap-2 text-sm text-gray-500">                <h3 className="mb-4 flex items-center text-lg font-semibold text-gray-900">

            <svg className="h-5 w-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">                  <Users className="mr-2 h-5 w-5 text-red-600" />

              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />                  Booking Details

            </svg>                </h3>

            Secured Payment Processing                <div className="grid gap-4 text-sm md:grid-cols-2">

          </p>                  <div>

        </div>                    <div className="mb-2 flex items-center text-gray-600">

      </div>                      <Calendar className="mr-2 h-4 w-4" />

    </div>                      <span>

  );                        {selectedBooking.eventDate} at {selectedBooking.eventTime}

}                      </span>

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
                      <div className="text-sm text-gray-600">$100.00 to secure your booking</div>
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
