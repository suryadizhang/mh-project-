'use client';

import React from 'react';
import { PaymentElement, useElements, useStripe } from '@stripe/react-stripe-js';
import { CheckCircle, CreditCard, Loader2, Lock, Shield } from 'lucide-react';
import { FormEvent, useState } from 'react';

import { logger } from '@/lib/logger';
import { FormErrorBoundary } from '@/components/ErrorBoundary';

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

function PaymentFormComponent({
  amount,
  bookingData,
  paymentType,
  tipAmount,
  clientSecret,
}: PaymentFormProps) {
  const stripe = useStripe();
  const elements = useElements();

  const [isLoading, setIsLoading] = useState(false);
  const [paymentError, setPaymentError] = useState<string | null>(null);
  const [paymentSuccess, setPaymentSuccess] = useState(false);
  // Note: Billing address is now collected by Stripe PaymentElement (billingDetails: 'auto')
  // We only need to track name/email for confirmation display
  const [customerInfo, setCustomerInfo] = useState({
    name: bookingData?.customerName || '',
    email: bookingData?.customerEmail || '',
  });

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();

    if (!stripe || !elements || !clientSecret) {
      return;
    }

    setIsLoading(true);
    setPaymentError(null);

    try {
      // Confirm payment with Stripe using the existing clientSecret
      const { error: submitError } = await elements.submit();
      if (submitError) {
        throw new Error(submitError.message);
      }

      // Billing details are collected automatically by PaymentElement (billingDetails: 'auto')
      // Stripe handles address validation, autocomplete, and fraud detection
      const { error } = await stripe.confirmPayment({
        elements,
        clientSecret,
        confirmParams: {
          return_url: `${window.location.origin}/payment/success`,
          // Only pass receipt email - billing address comes from PaymentElement
          receipt_email: customerInfo.email || undefined,
        },
      });

      if (error) {
        if (error.type === 'card_error' || error.type === 'validation_error') {
          setPaymentError(error.message || 'Payment failed');
        } else {
          setPaymentError('An unexpected error occurred.');
        }
      } else {
        setPaymentSuccess(true);
      }
    } catch (error) {
      logger.error('Payment error', error as Error);
      setPaymentError(error instanceof Error ? error.message : 'Payment failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (paymentSuccess) {
    return (
      <div className="rounded-xl bg-white p-8 text-center shadow-lg">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
          <CheckCircle className="h-8 w-8 text-green-600" />
        </div>
        <h3 className="mb-2 text-2xl font-bold text-gray-900">Payment Successful!</h3>
        <p className="mb-6 text-gray-600">
          Your payment of ${amount.toFixed(2)} has been processed successfully.
        </p>
        <div className="mb-6 rounded-lg bg-green-50 p-4">
          <div className="text-sm text-green-800">
            <div className="mb-1 font-medium">Payment Details:</div>
            <div>Amount: ${amount.toFixed(2)}</div>
            <div>Type: {paymentType === 'deposit' ? 'Deposit Payment' : 'Balance Payment'}</div>
            {tipAmount > 0 && <div>Tip: ${tipAmount.toFixed(2)}</div>}
            {bookingData && <div>Booking: {bookingData.id}</div>}
          </div>
        </div>
        <p className="text-sm text-gray-500">
          A confirmation email will be sent to {customerInfo.email}
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl bg-white p-6 shadow-lg">
      <div className="mb-6">
        <h3 className="mb-2 flex items-center text-lg font-semibold text-gray-900">
          <CreditCard className="mr-2 h-5 w-5 text-blue-600" />
          Credit Card Payment
        </h3>
        <div className="flex items-center text-sm text-gray-600">
          <Shield className="mr-1 h-4 w-4 text-green-600" />
          <span>Secured by Stripe with 256-bit SSL encryption</span>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Customer Contact - Only shown when no booking data (standalone payment) */}
        {!bookingData && (
          <div className="rounded-lg bg-gray-50 p-4">
            <h4 className="mb-3 font-medium text-gray-900">Contact Information</h4>
            <p className="mb-3 text-sm text-gray-600">
              For your payment receipt. Billing address will be collected below.
            </p>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">Full Name *</label>
                <input
                  type="text"
                  required
                  value={customerInfo.name}
                  onChange={(e) => setCustomerInfo((prev) => ({ ...prev, name: e.target.value }))}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-transparent focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Email Address *
                </label>
                <input
                  type="email"
                  required
                  value={customerInfo.email}
                  onChange={(e) => setCustomerInfo((prev) => ({ ...prev, email: e.target.value }))}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-transparent focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>
        )}

        {/* Stripe Payment Element - Collects card + billing address automatically */}
        <div className="rounded-lg bg-gray-50 p-4">
          <h4 className="mb-3 flex items-center font-medium text-gray-900">
            <Lock className="mr-2 h-4 w-4 text-blue-600" />
            Payment Details
          </h4>
          <PaymentElement
            options={{
              layout: 'tabs',
              paymentMethodOrder: ['card', 'apple_pay', 'google_pay'],
              // Let Stripe collect billing address - better validation, fraud detection
              fields: {
                billingDetails: {
                  address: 'auto', // Stripe collects billing address
                },
              },
            }}
          />
        </div>

        {/* Error Display */}
        {paymentError && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4">
            <p className="text-sm text-red-600">{paymentError}</p>
          </div>
        )}

        {/* Payment Summary */}
        <div className="rounded-lg bg-blue-50 p-4">
          <h4 className="mb-2 font-medium text-blue-900">Final Payment Summary</h4>
          <div className="space-y-1 text-sm text-blue-800">
            <div className="flex justify-between">
              <span>Payment Type:</span>
              <span className="font-medium">
                {paymentType === 'deposit' ? 'Deposit Payment' : 'Balance Payment'}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Total Amount:</span>
              <span className="text-lg font-bold">${amount.toFixed(2)}</span>
            </div>
            <div className="mt-2 text-xs text-blue-600">
              * Includes 8% processing fee for card payments
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={!stripe || isLoading || amount <= 0}
          className="flex w-full items-center justify-center rounded-lg bg-blue-600 px-6 py-4 font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Processing Payment...
            </>
          ) : (
            <>
              <Lock className="mr-2 h-5 w-5" />
              Pay ${amount.toFixed(2)} Securely
            </>
          )}
        </button>

        {/* Security Notice */}
        <div className="text-center text-xs text-gray-500">
          <div className="mb-1 flex items-center justify-center">
            <Shield className="mr-1 h-3 w-3" />
            <span>Your payment is secured by Stripe</span>
          </div>
          <div>256-bit SSL encryption • PCI DSS compliant • 2-Factor Authentication</div>
        </div>
      </form>
    </div>
  );
}

// Wrap component with error boundary
export default function PaymentForm(props: PaymentFormProps) {
  return (
    <FormErrorBoundary formName="PaymentForm">
      <PaymentFormComponent {...props} />
    </FormErrorBoundary>
  );
}
