'use client'

import { useState, useEffect, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import {
  CheckCircle,
  Download,
  Mail,
  Phone,
  Home,
  CreditCard,
  Calendar,
  DollarSign
} from 'lucide-react'
import Link from 'next/link'
import { apiFetch } from '@/lib/api'

interface PaymentSuccess {
  payment_intent: string
  amount: number
  currency: string
  status: string
  customer: {
    name?: string
    email?: string
  }
  metadata: {
    booking_id?: string
    customer_name?: string
    event_date?: string
    payment_type?: string
  }
  receipt_url?: string
  created: number
}

function CheckoutSuccessContent() {
  const searchParams = useSearchParams()
  const sessionId = searchParams?.get('session_id')
  const [paymentData, setPaymentData] = useState<PaymentSuccess | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchSessionData = async () => {
      if (!sessionId) {
        setError('No session ID provided')
        setIsLoading(false)
        return
      }

      try {
        // Call backend to retrieve checkout session details
        const response = await apiFetch('/api/v1/payments/checkout-session', {
          method: 'POST',
          body: JSON.stringify({ session_id: sessionId })
        })

        if (response.success) {
          setPaymentData(response.data)
        } else {
          setError(response.error || 'Failed to retrieve payment details')
        }
      } catch (err) {
        console.error('Error fetching session data:', err)
        setError('Failed to load payment information')
      } finally {
        setIsLoading(false)
      }
    }

    fetchSessionData()
  }, [sessionId])

  const downloadReceipt = async () => {
    if (!paymentData) return

    try {
      const receiptData = {
        paymentId: paymentData.payment_intent,
        amount: paymentData.amount / 100,
        currency: paymentData.currency.toUpperCase(),
        date: new Date(paymentData.created * 1000).toLocaleDateString(),
        customer: paymentData.customer.name || paymentData.metadata.customer_name || 'Customer',
        bookingId: paymentData.metadata.booking_id,
        paymentType: paymentData.metadata.payment_type,
        sessionId: sessionId
      }

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
${receiptData.paymentType ? `Payment Type: ${receiptData.paymentType === 'deposit' ? 'Deposit Payment' : 'Balance Payment'}` : ''}

Contact Information
-------------------
My Hibachi
Phone: (916) 740-8768
Email: info@myhibachi.com
Website: www.myhibachi.com

Thank you for choosing My Hibachi!
We look forward to serving you an unforgettable experience.
      `.trim()

      const blob = new Blob([receiptText], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `MyHibachi_Receipt_${receiptData.paymentId.slice(-8)}.txt`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Error downloading receipt:', err)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-green-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your payment confirmation...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-xl shadow-lg p-8 max-w-md w-full mx-4 text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CreditCard className="w-8 h-8 text-red-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Payment Error</h1>
          <p className="text-gray-600 mb-6">{error}</p>
          <Link
            href="/payment"
            className="inline-flex items-center px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            <Home className="w-5 h-5 mr-2" />
            Return to Payment Page
          </Link>
        </div>
      </div>
    )
  }

  if (!paymentData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-xl shadow-lg p-8 max-w-md w-full mx-4 text-center">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CreditCard className="w-8 h-8 text-gray-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Payment Not Found</h1>
          <p className="text-gray-600 mb-6">
            We couldn&apos;t find the payment details for this session.
          </p>
          <Link
            href="/payment"
            className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Home className="w-5 h-5 mr-2" />
            Return to Payment Page
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Success Header */}
        <div className="bg-white rounded-xl shadow-lg p-8 mb-6 text-center">
          <div className="w-24 h-24 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="w-16 h-16 text-green-600" />
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-3">Payment Successful!</h1>
          <p className="text-2xl text-green-600 font-bold mb-4">
            ${(paymentData.amount / 100).toFixed(2)} USD
          </p>
          <p className="text-gray-600 text-lg max-w-2xl mx-auto">
            Thank you for your payment! Your transaction has been processed successfully. A
            confirmation email has been sent to your registered email address.
          </p>
        </div>

        {/* Payment Summary */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
            <DollarSign className="w-6 h-6 mr-2 text-green-600" />
            Payment Summary
          </h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="flex justify-between items-center pb-2 border-b border-gray-100">
                <span className="text-gray-600">Payment Amount</span>
                <span className="font-semibold text-lg">
                  ${(paymentData.amount / 100).toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between items-center pb-2 border-b border-gray-100">
                <span className="text-gray-600">Currency</span>
                <span className="font-medium">{paymentData.currency.toUpperCase()}</span>
              </div>
              <div className="flex justify-between items-center pb-2 border-b border-gray-100">
                <span className="text-gray-600">Status</span>
                <span className="inline-flex items-center px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                  <CheckCircle className="w-4 h-4 mr-1" />
                  Completed
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Date & Time</span>
                <span className="font-medium">
                  {new Date(paymentData.created * 1000).toLocaleString()}
                </span>
              </div>
            </div>
            <div className="space-y-4">
              <div className="flex justify-between items-center pb-2 border-b border-gray-100">
                <span className="text-gray-600">Payment ID</span>
                <span className="font-mono text-sm">{paymentData.payment_intent.slice(-12)}</span>
              </div>
              <div className="flex justify-between items-center pb-2 border-b border-gray-100">
                <span className="text-gray-600">Session ID</span>
                <span className="font-mono text-sm">{sessionId?.slice(-12)}</span>
              </div>
              {paymentData.metadata.payment_type && (
                <div className="flex justify-between items-center pb-2 border-b border-gray-100">
                  <span className="text-gray-600">Payment Type</span>
                  <span className="font-medium capitalize">
                    {paymentData.metadata.payment_type === 'deposit'
                      ? 'Deposit Payment'
                      : 'Balance Payment'}
                  </span>
                </div>
              )}
              {paymentData.customer.name && (
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Customer</span>
                  <span className="font-medium">{paymentData.customer.name}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Booking Information */}
        {paymentData.metadata.booking_id && (
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-xl p-6 mb-6">
            <h3 className="text-xl font-semibold text-blue-900 mb-4 flex items-center">
              <Calendar className="w-6 h-6 mr-2" />
              Booking Confirmation
            </h3>
            <div className="grid md:grid-cols-2 gap-4 text-blue-800">
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
              <div className="mt-4 p-4 bg-blue-100 rounded-lg">
                <p className="text-blue-800 text-sm">
                  <strong>Next Steps:</strong> Your booking is now confirmed! We&apos;ll send you a
                  final invoice for the remaining balance closer to your event date. Keep this
                  confirmation for your records.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Next Steps</h3>
          <div className="grid md:grid-cols-3 gap-4">
            <button
              onClick={downloadReceipt}
              className="flex items-center justify-center px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              <Download className="w-5 h-5 mr-2" />
              Download Receipt
            </button>
            {paymentData.receipt_url && (
              <a
                href={paymentData.receipt_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Mail className="w-5 h-5 mr-2" />
                Email Receipt
              </a>
            )}
            <Link
              href="/"
              className="flex items-center justify-center px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
            >
              <Home className="w-5 h-5 mr-2" />
              Return Home
            </Link>
          </div>
        </div>

        {/* What's Next Section */}
        <div className="bg-gradient-to-r from-red-50 to-orange-50 border border-red-200 rounded-xl p-6 mb-6">
          <h3 className="text-xl font-semibold text-red-900 mb-4">What Happens Next?</h3>
          <div className="space-y-3 text-red-800">
            <div className="flex items-start">
              <div className="w-6 h-6 bg-red-200 rounded-full flex items-center justify-center mr-3 mt-0.5">
                <span className="text-red-800 text-sm font-bold">1</span>
              </div>
              <div>
                <p className="font-medium">Confirmation Email</p>
                <p className="text-sm text-red-700">
                  You&apos;ll receive a detailed confirmation email within 5 minutes.
                </p>
              </div>
            </div>
            <div className="flex items-start">
              <div className="w-6 h-6 bg-red-200 rounded-full flex items-center justify-center mr-3 mt-0.5">
                <span className="text-red-800 text-sm font-bold">2</span>
              </div>
              <div>
                <p className="font-medium">Chef Assignment</p>
                <p className="text-sm text-red-700">
                  We&apos;ll assign your personal hibachi chef and send you their details.
                </p>
              </div>
            </div>
            <div className="flex items-start">
              <div className="w-6 h-6 bg-red-200 rounded-full flex items-center justify-center mr-3 mt-0.5">
                <span className="text-red-800 text-sm font-bold">3</span>
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
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Need Help or Have Questions?</h3>
          <p className="text-gray-600 mb-4">
            Our team is here to help! Contact us if you have any questions about your booking or
            payment.
          </p>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="flex items-center p-4 bg-gray-50 rounded-lg">
              <Phone className="w-6 h-6 text-gray-500 mr-3" />
              <div>
                <div className="font-medium text-gray-900">Phone Support</div>
                <div className="text-gray-600">(916) 740-8768</div>
                <div className="text-sm text-gray-500">Available 9 AM - 9 PM PST</div>
              </div>
            </div>
            <div className="flex items-center p-4 bg-gray-50 rounded-lg">
              <Mail className="w-6 h-6 text-gray-500 mr-3" />
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
  )
}

function CheckoutSuccessLoading() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <div className="w-16 h-16 border-4 border-green-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-gray-600">Loading your payment confirmation...</p>
      </div>
    </div>
  )
}

export default function CheckoutSuccessPage() {
  return (
    <Suspense fallback={<CheckoutSuccessLoading />}>
      <CheckoutSuccessContent />
    </Suspense>
  )
}
