'use client'

import { useState, FormEvent } from 'react'
import { useStripe, useElements, PaymentElement } from '@stripe/react-stripe-js'
import { Loader2, CreditCard, Shield, Lock, CheckCircle } from 'lucide-react'

interface BookingData {
  id: string
  customerName: string
  customerEmail: string
  eventDate: string
  eventTime: string
  guestCount: number
  venueAddress: string
  totalAmount: number
  depositPaid: boolean
  depositAmount: number
  remainingBalance: number
}

interface PaymentFormProps {
  amount: number
  bookingData: BookingData | null
  paymentType: 'deposit' | 'balance'
  tipAmount: number
  clientSecret: string
}

export default function PaymentForm({
  amount,
  bookingData,
  paymentType,
  tipAmount,
  clientSecret
}: PaymentFormProps) {
  const stripe = useStripe()
  const elements = useElements()

  const [isLoading, setIsLoading] = useState(false)
  const [paymentError, setPaymentError] = useState<string | null>(null)
  const [paymentSuccess, setPaymentSuccess] = useState(false)
  const [customerInfo, setCustomerInfo] = useState({
    name: bookingData?.customerName || '',
    email: bookingData?.customerEmail || '',
    phone: '',
    address: '',
    city: '',
    state: '',
    zipCode: ''
  })

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()

    if (!stripe || !elements || !clientSecret) {
      return
    }

    setIsLoading(true)
    setPaymentError(null)

    try {
      // Confirm payment with Stripe using the existing clientSecret
      const { error: submitError } = await elements.submit()
      if (submitError) {
        throw new Error(submitError.message)
      }

      const { error } = await stripe.confirmPayment({
        elements,
        clientSecret,
        confirmParams: {
          return_url: `${window.location.origin}/payment/success`,
          payment_method_data: {
            billing_details: {
              name: customerInfo.name,
              email: customerInfo.email,
              phone: customerInfo.phone,
              address: {
                line1: customerInfo.address,
                city: customerInfo.city,
                state: customerInfo.state,
                postal_code: customerInfo.zipCode,
                country: 'US'
              }
            }
          }
        }
      })

      if (error) {
        if (error.type === 'card_error' || error.type === 'validation_error') {
          setPaymentError(error.message || 'Payment failed')
        } else {
          setPaymentError('An unexpected error occurred.')
        }
      } else {
        setPaymentSuccess(true)
      }
    } catch (error) {
      console.error('Payment error:', error)
      setPaymentError(error instanceof Error ? error.message : 'Payment failed. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  if (paymentSuccess) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-8 text-center">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <CheckCircle className="w-8 h-8 text-green-600" />
        </div>
        <h3 className="text-2xl font-bold text-gray-900 mb-2">Payment Successful!</h3>
        <p className="text-gray-600 mb-6">
          Your payment of ${amount.toFixed(2)} has been processed successfully.
        </p>
        <div className="bg-green-50 rounded-lg p-4 mb-6">
          <div className="text-sm text-green-800">
            <div className="font-medium mb-1">Payment Details:</div>
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
    )
  }

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center">
          <CreditCard className="w-5 h-5 mr-2 text-blue-600" />
          Credit Card Payment
        </h3>
        <div className="flex items-center text-sm text-gray-600">
          <Shield className="w-4 h-4 mr-1 text-green-600" />
          <span>Secured by Stripe with 256-bit SSL encryption</span>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Customer Information */}
        {!bookingData && (
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-3">Customer Information</h4>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Full Name *</label>
                <input
                  type="text"
                  required
                  value={customerInfo.name}
                  onChange={e => setCustomerInfo(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email Address *
                </label>
                <input
                  type="email"
                  required
                  value={customerInfo.email}
                  onChange={e => setCustomerInfo(prev => ({ ...prev, email: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Phone Number *
                </label>
                <input
                  type="tel"
                  required
                  value={customerInfo.phone}
                  onChange={e => setCustomerInfo(prev => ({ ...prev, phone: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
                <input
                  type="text"
                  value={customerInfo.address}
                  onChange={e => setCustomerInfo(prev => ({ ...prev, address: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">City</label>
                <input
                  type="text"
                  value={customerInfo.city}
                  onChange={e => setCustomerInfo(prev => ({ ...prev, city: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
                <input
                  type="text"
                  value={customerInfo.state}
                  onChange={e => setCustomerInfo(prev => ({ ...prev, state: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">ZIP Code</label>
                <input
                  type="text"
                  value={customerInfo.zipCode}
                  onChange={e => setCustomerInfo(prev => ({ ...prev, zipCode: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>
        )}

        {/* Stripe Payment Element */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-3 flex items-center">
            <Lock className="w-4 h-4 mr-2 text-blue-600" />
            Payment Details
          </h4>
          <PaymentElement
            options={{
              layout: 'tabs',
              paymentMethodOrder: ['card', 'apple_pay', 'google_pay']
            }}
          />
        </div>

        {/* Error Display */}
        {paymentError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-600 text-sm">{paymentError}</p>
          </div>
        )}

        {/* Payment Summary */}
        <div className="bg-blue-50 rounded-lg p-4">
          <h4 className="font-medium text-blue-900 mb-2">Final Payment Summary</h4>
          <div className="text-sm text-blue-800 space-y-1">
            <div className="flex justify-between">
              <span>Payment Type:</span>
              <span className="font-medium">
                {paymentType === 'deposit' ? 'Deposit Payment' : 'Balance Payment'}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Total Amount:</span>
              <span className="font-bold text-lg">${amount.toFixed(2)}</span>
            </div>
            <div className="text-xs text-blue-600 mt-2">
              * Includes 8% processing fee for card payments
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={!stripe || isLoading || amount <= 0}
          className="w-full bg-blue-600 text-white py-4 px-6 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-5 h-5 mr-2 animate-spin" />
              Processing Payment...
            </>
          ) : (
            <>
              <Lock className="w-5 h-5 mr-2" />
              Pay ${amount.toFixed(2)} Securely
            </>
          )}
        </button>

        {/* Security Notice */}
        <div className="text-center text-xs text-gray-500">
          <div className="flex items-center justify-center mb-1">
            <Shield className="w-3 h-3 mr-1" />
            <span>Your payment is secured by Stripe</span>
          </div>
          <div>256-bit SSL encryption • PCI DSS compliant • 2-Factor Authentication</div>
        </div>
      </form>
    </div>
  )
}
