'use client'

import { useState, useEffect } from 'react'
import { loadStripe } from '@stripe/stripe-js'
import { Elements } from '@stripe/react-stripe-js'
import { CreditCard, DollarSign, Shield, Users, Calendar, MapPin, Loader2 } from 'lucide-react'
import PaymentForm from '@/components/payment/PaymentForm'
import AlternativePaymentOptions from '@/components/payment/AlternativePaymentOptions'
import BookingLookup from '@/components/payment/BookingLookup'

// Initialize Stripe
const stripePublishableKey = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY
const stripePromise = stripePublishableKey ? loadStripe(stripePublishableKey) : null

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
  services: Array<{
    name: string
    price: number
    quantity: number
  }>
}

export default function PaymentPage() {
  const [selectedBooking, setSelectedBooking] = useState<BookingData | null>(null)
  const [paymentType, setPaymentType] = useState<'deposit' | 'balance'>('deposit')
  const [customAmount, setCustomAmount] = useState('')
  const [tipAmount, setTipAmount] = useState('')
  const [paymentMethod, setPaymentMethod] = useState<'stripe' | 'zelle' | 'venmo'>('stripe')
  const [isLoading, setIsLoading] = useState(false)
  const [clientSecret, setClientSecret] = useState<string | null>(null)
  const [stripeElementsKey, setStripeElementsKey] = useState(0) // Force re-render

  // Calculate totals
  const baseAmount = selectedBooking 
    ? paymentType === 'deposit' 
      ? 100 
      : selectedBooking.remainingBalance
    : parseFloat(customAmount) || 0

  const tipValue = parseFloat(tipAmount) || 0
  const subtotal = baseAmount + tipValue
  
  // Add processing fees based on payment method
  const processingFee = paymentMethod === 'stripe' 
    ? subtotal * 0.08 
    : paymentMethod === 'venmo' 
    ? subtotal * 0.03 
    : 0
  const totalAmount = subtotal + processingFee

  // Create payment intent when amount changes and using Stripe
  useEffect(() => {
    const createPaymentIntent = async () => {
      try {
        setIsLoading(true)
        const response = await fetch('/api/v1/payments/create-intent', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
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
              zipCode: ''
            },
            metadata: {
              bookingId: selectedBooking?.id || 'manual-payment',
              customerName: selectedBooking?.customerName || 'Guest User',
              eventDate: selectedBooking?.eventDate || 'N/A',
              paymentType
            }
          }),
        })

        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.error || 'Failed to create payment intent')
        }

        const { clientSecret: newClientSecret } = await response.json()
        setClientSecret(newClientSecret)
        setStripeElementsKey(prev => prev + 1) // Force Elements re-render
      } catch (error) {
        console.error('Error creating payment intent:', error)
        setClientSecret(null)
      } finally {
        setIsLoading(false)
      }
    }

    if (paymentMethod === 'stripe' && totalAmount > 0) {
      createPaymentIntent()
    } else {
      setClientSecret(null)
    }
  }, [totalAmount, paymentMethod, selectedBooking, paymentType, tipValue])

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
  }

  const options = clientSecret ? {
    clientSecret,
    appearance,
    loader: 'auto' as const,
  } : {
    appearance,
    loader: 'auto' as const,
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
          <div className="text-center">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <DollarSign className="w-8 h-8 text-red-600" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              My Hibachi Payment Portal
            </h1>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Secure payment processing for your hibachi booking. Pay your deposit to lock in your date 
              or settle your remaining balance with optional tips.
            </p>
          </div>

          {/* Security Badge */}
          <div className="flex items-center justify-center mt-6 p-4 bg-green-50 rounded-lg border border-green-200">
            <Shield className="w-5 h-5 text-green-600 mr-2" />
            <span className="text-green-800 font-medium">
              Secured by Stripe with 2-Factor Authentication
            </span>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Left Column - Booking Lookup */}
          <div className="lg:col-span-1">
            <BookingLookup 
              onBookingFound={setSelectedBooking}
              isLoading={isLoading}
              setIsLoading={setIsLoading}
            />

            {/* Manual Amount Entry */}
            {!selectedBooking && (
              <div className="bg-white rounded-xl shadow-lg p-6 mt-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Or Enter Custom Amount
                </h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Amount to Pay
                    </label>
                    <div className="relative">
                      <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">
                        $
                      </span>
                      <input
                        type="number"
                        value={customAmount}
                        onChange={(e) => setCustomAmount(e.target.value)}
                        placeholder="0.00"
                        className="w-full pl-8 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
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
              <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <Users className="w-5 h-5 mr-2 text-red-600" />
                  Booking Details
                </h3>
                <div className="grid md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="flex items-center text-gray-600 mb-2">
                      <Calendar className="w-4 h-4 mr-2" />
                      <span>{selectedBooking.eventDate} at {selectedBooking.eventTime}</span>
                    </div>
                    <div className="flex items-center text-gray-600 mb-2">
                      <Users className="w-4 h-4 mr-2" />
                      <span>{selectedBooking.guestCount} guests</span>
                    </div>
                    <div className="flex items-center text-gray-600">
                      <MapPin className="w-4 h-4 mr-2" />
                      <span>{selectedBooking.venueAddress}</span>
                    </div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-xs text-gray-500 uppercase tracking-wide mb-2">Payment Status</div>
                    <div className="text-sm">
                      <div className="flex justify-between">
                        <span>Total Event Cost:</span>
                        <span className="font-medium">${selectedBooking.totalAmount.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Deposit Paid:</span>
                        <span className={selectedBooking.depositPaid ? 'text-green-600' : 'text-red-600'}>
                          {selectedBooking.depositPaid ? `$${selectedBooking.depositAmount.toFixed(2)}` : 'Not Paid'}
                        </span>
                      </div>
                      <div className="flex justify-between border-t pt-2 mt-2">
                        <span className="font-medium">Remaining Balance:</span>
                        <span className="font-medium">${selectedBooking.remainingBalance.toFixed(2)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Payment Type Selection */}
            {selectedBooking && (
              <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Select Payment Type
                </h3>
                <div className="grid md:grid-cols-2 gap-4">
                  <button
                    onClick={() => setPaymentType('deposit')}
                    disabled={selectedBooking.depositPaid}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      paymentType === 'deposit' 
                        ? 'border-red-500 bg-red-50' 
                        : 'border-gray-200 hover:border-gray-300'
                    } ${selectedBooking.depositPaid ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    <div className="text-left">
                      <div className="font-medium">Deposit Payment</div>
                      <div className="text-sm text-gray-600">$100.00 to secure your booking</div>
                      {selectedBooking.depositPaid && (
                        <div className="text-xs text-green-600 mt-1">✓ Already Paid</div>
                      )}
                    </div>
                  </button>
                  <button
                    onClick={() => setPaymentType('balance')}
                    className={`p-4 rounded-lg border-2 transition-all ${
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
            <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Choose Payment Method
              </h3>
              <div className="grid md:grid-cols-3 gap-4">
                <button
                  onClick={() => setPaymentMethod('stripe')}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    paymentMethod === 'stripe' 
                      ? 'border-blue-500 bg-blue-50' 
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <CreditCard className="w-6 h-6 mx-auto mb-2 text-blue-600" />
                  <div className="text-sm font-medium">Credit Card</div>
                  <div className="text-xs text-gray-600">+8% processing fee</div>
                </button>
                <button
                  onClick={() => setPaymentMethod('zelle')}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    paymentMethod === 'zelle' 
                      ? 'border-purple-500 bg-purple-50' 
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="w-6 h-6 mx-auto mb-2 bg-purple-600 rounded text-white text-xs flex items-center justify-center font-bold">
                    Z
                  </div>
                  <div className="text-sm font-medium">Zelle</div>
                  <div className="text-xs text-gray-600">No fees</div>
                </button>
                <button
                  onClick={() => setPaymentMethod('venmo')}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    paymentMethod === 'venmo' 
                      ? 'border-blue-400 bg-blue-50' 
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="w-6 h-6 mx-auto mb-2 bg-blue-400 rounded text-white text-xs flex items-center justify-center font-bold">
                    V
                  </div>
                  <div className="text-sm font-medium">Venmo</div>
                  <div className="text-xs text-gray-600">+3% processing fee</div>
                </button>
              </div>
            </div>

            {/* Tips/Gratuity */}
            <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Add Tip/Gratuity (Optional)
              </h3>
              <div className="grid grid-cols-4 gap-3 mb-4">
                {[20, 25, 30, 35].map((percent) => {
                  const tipValue = (baseAmount * percent / 100).toFixed(2)
                  return (
                    <button
                      key={percent}
                      onClick={() => setTipAmount(tipValue)}
                      className="p-3 border border-gray-300 rounded-lg hover:border-red-500 hover:bg-red-50 transition-all text-center"
                    >
                      <div className="font-medium">{percent}%</div>
                      <div className="text-sm text-gray-600">${tipValue}</div>
                    </button>
                  )
                })}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Custom Tip Amount
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">
                    $
                  </span>
                  <input
                    type="number"
                    value={tipAmount}
                    onChange={(e) => setTipAmount(e.target.value)}
                    placeholder="0.00"
                    className="w-full pl-8 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  />
                </div>
              </div>
            </div>

            {/* Payment Summary */}
            <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Payment Summary
              </h3>
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
                <div className="border-t pt-2 mt-2">
                  <div className="flex justify-between font-bold text-lg">
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
                    <PaymentForm 
                      amount={totalAmount}
                      bookingData={selectedBooking}
                      paymentType={paymentType}
                      tipAmount={tipValue}
                      clientSecret={clientSecret}
                    />
                  </Elements>
                ) : (
                  <div className="bg-white rounded-xl shadow-lg p-8 text-center">
                    <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
                    </div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">Preparing Payment...</h3>
                    <p className="text-gray-600">
                      Setting up secure payment processing. This will only take a moment.
                    </p>
                  </div>
                )
              ) : (
                <div className="bg-white rounded-xl shadow-lg p-8 text-center">
                  <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <CreditCard className="w-8 h-8 text-red-600" />
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">Payment Processing Unavailable</h3>
                  <p className="text-gray-600 mb-4">
                    Credit card processing is currently not configured. Please use Zelle or Venmo instead.
                  </p>
                  <button
                    onClick={() => setPaymentMethod('zelle')}
                    className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors mr-2"
                  >
                    Use Zelle
                  </button>
                  <button
                    onClick={() => setPaymentMethod('venmo')}
                    className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Use Venmo
                  </button>
                </div>
              )
            ) : (
              <AlternativePaymentOptions 
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
  )
}
