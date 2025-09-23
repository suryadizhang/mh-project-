'use client'

import { CheckCircle, CreditCard, Download, Home, Mail, Phone } from 'lucide-react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { Suspense, useEffect, useState } from 'react'

interface PaymentDetails {
  id: string
  status: string
  amount: number
  currency: string
  metadata: {
    bookingId?: string
    customerName?: string
    eventDate?: string
    paymentType?: string
  }
  created: number
}

function PaymentSuccessContent() {
  const searchParams = useSearchParams()
  const paymentIntentId = searchParams?.get('payment_intent')
  const [paymentDetails, setPaymentDetails] = useState<PaymentDetails | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchPaymentDetails = async () => {
      if (!paymentIntentId) {
        setError('No payment information found')
        setIsLoading(false)
        return
      }

      try {
        const response = await fetch(
          `/api/v1/payments/create-intent?payment_intent_id=${paymentIntentId}`
        )
        const data = await response.json()

        if (response.ok) {
          setPaymentDetails(data)
        } else {
          setError(data.error || 'Failed to retrieve payment details')
        }
      } catch (err) {
        console.error('Error fetching payment details:', err)
        setError('Failed to load payment information')
      } finally {
        setIsLoading(false)
      }
    }

    fetchPaymentDetails()
  }, [paymentIntentId])

  const downloadReceipt = async () => {
    if (!paymentDetails) return

    try {
      // In production, you would generate and download a proper receipt
      const receiptData = {
        paymentId: paymentDetails.id,
        amount: paymentDetails.amount / 100,
        currency: paymentDetails.currency.toUpperCase(),
        date: new Date(paymentDetails.created * 1000).toLocaleDateString(),
        customer: paymentDetails.metadata.customerName,
        bookingId: paymentDetails.metadata.bookingId,
        paymentType: paymentDetails.metadata.paymentType
      }

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
Contact: (916) 740-8768 | info@myhibachi.com
      `.trim()

      const blob = new Blob([receiptText], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `MyHibachi_Receipt_${receiptData.paymentId}.txt`
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
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading payment details...</p>
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

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Success Header */}
        <div className="bg-white rounded-xl shadow-lg p-8 mb-6 text-center">
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="w-12 h-12 text-green-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Payment Successful!</h1>
          <p className="text-xl text-green-600 font-semibold mb-4">
            ${paymentDetails ? (paymentDetails.amount / 100).toFixed(2) : '0.00'} USD
          </p>
          <p className="text-gray-600">
            Your payment has been processed successfully. A confirmation email will be sent to your
            registered email address.
          </p>
        </div>

        {/* Payment Details */}
        {paymentDetails && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Payment Details</h2>
            <div className="grid md:grid-cols-2 gap-4 text-sm">
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
                  <div className="inline-flex items-center px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-medium">
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
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 mb-6">
            <h3 className="text-lg font-semibold text-blue-900 mb-3">Booking Information</h3>
            <div className="text-sm text-blue-800 space-y-2">
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
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">What&apos;s Next?</h3>
          <div className="grid md:grid-cols-2 gap-4">
            <button
              onClick={downloadReceipt}
              className="flex items-center justify-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Download className="w-5 h-5 mr-2" />
              Download Receipt
            </button>
            <Link
              href="/"
              className="flex items-center justify-center px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
            >
              <Home className="w-5 h-5 mr-2" />
              Return Home
            </Link>
          </div>
        </div>

        {/* Contact Information */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Need Help?</h3>
          <p className="text-gray-600 mb-4">
            If you have any questions about your payment or booking, please don&apos;t hesitate to
            contact us:
          </p>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-center space-y-2 sm:space-y-0 sm:space-x-6 text-sm">
            <div className="flex items-center">
              <Phone className="w-4 h-4 mr-2 text-gray-500" />
              <span>(916) 740-8768</span>
            </div>
            <div className="flex items-center">
              <Mail className="w-4 h-4 mr-2 text-gray-500" />
              <span>info@myhibachi.com</span>
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
  )
}

function PaymentSuccessLoading() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-gray-600">Loading payment details...</p>
      </div>
    </div>
  )
}

export default function PaymentSuccessPage() {
  return (
    <Suspense fallback={<PaymentSuccessLoading />}>
      <PaymentSuccessContent />
    </Suspense>
  )
}
