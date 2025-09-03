'use client'

import { Check, Copy, ExternalLink, Mail, Phone, QrCode, Smartphone } from 'lucide-react'
import QRCodeGenerator from 'qrcode'
import { useState } from 'react'

import { apiFetch } from '@/lib/api'

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

interface AlternativePaymentOptionsProps {
  method: 'zelle' | 'venmo'
  amount: number
  bookingData: BookingData | null
  paymentType: 'deposit' | 'balance'
  tipAmount: number
}

export default function AlternativePaymentOptions({
  method,
  amount,
  bookingData,
  paymentType,
  tipAmount
}: AlternativePaymentOptionsProps) {
  const [copied, setCopied] = useState<string | null>(null)
  const [paymentSent, setPaymentSent] = useState(false)
  const [showQR, setShowQR] = useState(false)
  const [qrCode, setQrCode] = useState<string | null>(null)
  const [customerInfo, setCustomerInfo] = useState({
    name: bookingData?.customerName || '',
    email: bookingData?.customerEmail || '',
    phone: ''
  })

  const paymentDetails = {
    zelle: {
      email: 'myhibachichef@gmail.com',
      phone: '(916) 740-8768',
      name: 'My Hibachi LLC',
      color: 'purple',
      icon: 'Z'
    },
    venmo: {
      username: '@myhibachichef',
      phone: '(916) 740-8768',
      name: 'My Hibachi LLC',
      color: 'blue',
      icon: 'V'
    }
  }

  const details = paymentDetails[method]

  const copyToClipboard = async (text: string, type: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(type)
      setTimeout(() => setCopied(null), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const generatePaymentMemo = () => {
    const parts = []
    if (bookingData) {
      parts.push(`Booking: ${bookingData.id}`)
      parts.push(`Event: ${bookingData.eventDate}`)
    }
    parts.push(`Type: ${paymentType === 'deposit' ? 'Deposit' : 'Balance'}`)
    if (tipAmount > 0) {
      parts.push(`Tip: $${tipAmount.toFixed(2)}`)
    }
    return parts.join(' | ')
  }

  const generateVenmoDeepLink = () => {
    const memo = generatePaymentMemo()
    const venmoUrl = `venmo://paycharge?txn=pay&recipients=${encodeURIComponent('@myhibachichef')}&amount=${amount}&note=${encodeURIComponent(memo)}`
    return venmoUrl
  }

  const openVenmoApp = () => {
    const deepLink = generateVenmoDeepLink()
    // Try to open Venmo app, fallback to web if app not installed
    window.location.href = deepLink

    // Fallback to web version after a short delay if app doesn't open
    setTimeout(() => {
      const webUrl = `https://venmo.com/?txn=pay&recipients=myhibachichef&amount=${amount}&note=${encodeURIComponent(generatePaymentMemo())}`
      window.open(webUrl, '_blank')
    }, 2000)
  }

  const generateQRCode = async () => {
    try {
      let qrData = ''
      if (method === 'venmo') {
        qrData = generateVenmoDeepLink()
      } else if (method === 'zelle') {
        // For Zelle, we'll create a data string with payment info
        qrData = `Zelle Payment\nEmail: myhibachichef@gmail.com\nAmount: $${amount.toFixed(2)}\nMemo: ${generatePaymentMemo()}`
      }

      const qrCodeDataUrl = await QRCodeGenerator.toDataURL(qrData, {
        width: 200,
        margin: 2,
        color: {
          dark: method === 'venmo' ? '#3D95CE' : '#6B46C1',
          light: '#FFFFFF'
        }
      })
      setQrCode(qrCodeDataUrl)
      setShowQR(true)
    } catch (error) {
      console.error('Error generating QR code:', error)
    }
  }

  const handleConfirmPayment = async () => {
    // In a real implementation, this would:
    // 1. Send notification to admin
    // 2. Update booking status
    // 3. Send confirmation email
    setPaymentSent(true)

    // Simulate API call
    try {
      await apiFetch('/api/v1/payments/alternative-payment', {
        method: 'POST',
        body: JSON.stringify({
          method,
          amount,
          bookingId: bookingData?.id || null,
          paymentType,
          tipAmount,
          customerInfo,
          memo: generatePaymentMemo(),
          timestamp: new Date().toISOString()
        })
      })
    } catch (error) {
      console.error('Error recording payment:', error)
    }
  }

  if (paymentSent) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-8 text-center">
        <div
          className={`w-16 h-16 bg-${details.color}-100 rounded-full flex items-center justify-center mx-auto mb-4`}
        >
          <div
            className={`w-8 h-8 bg-${details.color}-600 rounded text-white text-lg flex items-center justify-center font-bold`}
          >
            {details.icon}
          </div>
        </div>
        <h3 className="text-2xl font-bold text-gray-900 mb-2">Payment Instructions Sent!</h3>
        <p className="text-gray-600 mb-6">
          We&apos;ve recorded your intent to pay ${amount.toFixed(2)} via{' '}
          {method.charAt(0).toUpperCase() + method.slice(1)}.
        </p>
        <div className="bg-green-50 rounded-lg p-4 mb-6">
          <div className="text-sm text-green-800">
            <div className="font-medium mb-2">Next Steps:</div>
            <ol className="list-decimal list-inside space-y-1 text-left">
              <li>Send payment using the details provided above</li>
              <li>Include the memo/note for payment identification</li>
              <li>We&apos;ll confirm receipt within 1-2 business hours</li>
              <li>You&apos;ll receive email confirmation once verified</li>
            </ol>
          </div>
        </div>
        <div className="flex items-center justify-center space-x-4 text-sm text-gray-600">
          <div className="flex items-center">
            <Phone className="w-4 h-4 mr-1" />
            <span>(916) 740-8768</span>
          </div>
          <div className="flex items-center">
            <Mail className="w-4 h-4 mr-1" />
            <span>info@myhibachi.com</span>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center">
          <div
            className={`w-6 h-6 bg-${details.color}-600 rounded text-white text-sm flex items-center justify-center font-bold mr-2`}
          >
            {details.icon}
          </div>
          {method.charAt(0).toUpperCase() + method.slice(1)} Payment
        </h3>
        <p className="text-gray-600 text-sm">
          {method === 'zelle'
            ? 'No processing fees! Send payment directly using Zelle.'
            : 'Send payment using Venmo with 3% processing fee included in total above.'}
        </p>
      </div>

      {/* Payment Instructions */}
      <div className={`bg-${details.color}-50 rounded-lg p-4 mb-6`}>
        <h4 className={`font-medium text-${details.color}-900 mb-3`}>Payment Instructions</h4>
        <div className="space-y-3">
          {method === 'zelle' && (
            <>
              <div className="flex items-center justify-between bg-white rounded p-3">
                <div>
                  <div className="text-sm font-medium text-gray-900">Email</div>
                  <div className="text-purple-700 font-mono">{paymentDetails.zelle.email}</div>
                </div>
                <button
                  onClick={() => copyToClipboard(paymentDetails.zelle.email, 'email')}
                  className="p-2 text-purple-600 hover:bg-purple-100 rounded transition-colors"
                >
                  {copied === 'email' ? (
                    <Check className="w-4 h-4" />
                  ) : (
                    <Copy className="w-4 h-4" />
                  )}
                </button>
              </div>
              <div className="flex items-center justify-between bg-white rounded p-3">
                <div>
                  <div className="text-sm font-medium text-gray-900">Phone</div>
                  <div className="text-purple-700 font-mono">{details.phone}</div>
                </div>
                <button
                  onClick={() => copyToClipboard(details.phone, 'phone')}
                  className="p-2 text-purple-600 hover:bg-purple-100 rounded transition-colors"
                >
                  {copied === 'phone' ? (
                    <Check className="w-4 h-4" />
                  ) : (
                    <Copy className="w-4 h-4" />
                  )}
                </button>
              </div>
            </>
          )}

          {method === 'venmo' && (
            <div className="flex items-center justify-between bg-white rounded p-3">
              <div>
                <div className="text-sm font-medium text-gray-900">Username</div>
                <div className="text-blue-700 font-mono">{paymentDetails.venmo.username}</div>
              </div>
              <button
                onClick={() => copyToClipboard(paymentDetails.venmo.username, 'username')}
                className="p-2 text-blue-600 hover:bg-blue-100 rounded transition-colors"
              >
                {copied === 'username' ? (
                  <Check className="w-4 h-4" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </button>
            </div>
          )}

          <div className="flex items-center justify-between bg-white rounded p-3">
            <div>
              <div className="text-sm font-medium text-gray-900">Recipient Name</div>
              <div className={`text-${details.color}-700 font-medium`}>{details.name}</div>
            </div>
          </div>
        </div>

        {/* Quick Payment Buttons */}
        <div className="mb-6">
          <h4 className="font-medium text-gray-900 mb-3">Quick Payment Options</h4>
          <div className="space-y-3">
            {method === 'venmo' && (
              <>
                <button
                  onClick={openVenmoApp}
                  className="w-full flex items-center justify-center px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <Smartphone className="w-5 h-5 mr-2" />
                  Open Venmo App (${amount.toFixed(2)} pre-filled)
                </button>
                <a
                  href={`https://venmo.com/?txn=pay&recipients=myhibachichef&amount=${amount}&note=${encodeURIComponent(generatePaymentMemo())}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full flex items-center justify-center px-4 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                >
                  <ExternalLink className="w-5 h-5 mr-2" />
                  Pay via Venmo Web
                </a>
                <button
                  onClick={generateQRCode}
                  className="w-full flex items-center justify-center px-4 py-3 bg-blue-400 text-white rounded-lg hover:bg-blue-500 transition-colors"
                >
                  <QrCode className="w-5 h-5 mr-2" />
                  Show Venmo QR Code
                </button>
              </>
            )}

            {method === 'zelle' && (
              <>
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <div className="flex items-start">
                    <QrCode className="w-5 h-5 text-yellow-600 mr-2 mt-0.5" />
                    <div className="text-sm text-yellow-800">
                      <div className="font-medium mb-1">Zelle Quick Send</div>
                      <div>Open your banking app and use these details for Zelle payment:</div>
                      <div className="mt-2 space-y-1">
                        <div>
                          Email:{' '}
                          <span className="font-mono font-medium">myhibachichef@gmail.com</span>
                        </div>
                        <div>
                          Amount:{' '}
                          <span className="font-mono font-medium">${amount.toFixed(2)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <button
                  onClick={generateQRCode}
                  className="w-full flex items-center justify-center px-4 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                >
                  <QrCode className="w-5 h-5 mr-2" />
                  Generate Payment QR Code
                </button>
              </>
            )}
          </div>
        </div>

        {/* QR Code Display */}
        {showQR && qrCode && (
          <div className="mb-6 bg-white rounded-lg p-6 text-center border">
            <h4 className="font-medium text-gray-900 mb-3">
              {method === 'venmo' ? 'Venmo' : 'Zelle'} Payment QR Code
            </h4>
            <div className="inline-block p-4 bg-white rounded-lg shadow-sm">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={qrCode} alt={`${method} Payment QR Code`} className="w-48 h-48 mx-auto" />
            </div>
            <p className="text-sm text-gray-600 mt-3">
              {method === 'venmo'
                ? 'Scan with your Venmo app to pay instantly'
                : 'Scan with your banking app or save payment details'}
            </p>
            <button
              onClick={() => setShowQR(false)}
              className="mt-3 px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
            >
              Hide QR Code
            </button>
          </div>
        )}
      </div>

      {/* Amount and Memo */}
      <div className="bg-gray-50 rounded-lg p-4 mb-6">
        <h4 className="font-medium text-gray-900 mb-3">Payment Details</h4>
        <div className="space-y-3">
          <div className="flex items-center justify-between bg-white rounded p-3">
            <div>
              <div className="text-sm font-medium text-gray-900">Amount to Send</div>
              <div className="text-green-600 font-bold text-xl">${amount.toFixed(2)}</div>
            </div>
            <button
              onClick={() => copyToClipboard(amount.toFixed(2), 'amount')}
              className="p-2 text-gray-600 hover:bg-gray-100 rounded transition-colors"
            >
              {copied === 'amount' ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
            </button>
          </div>

          <div className="bg-white rounded p-3">
            <div className="text-sm font-medium text-gray-900 mb-2">Memo/Note (Required)</div>
            <div className="bg-yellow-50 border border-yellow-200 rounded p-2">
              <div className="text-yellow-800 text-sm font-mono break-all">
                {generatePaymentMemo()}
              </div>
              <button
                onClick={() => copyToClipboard(generatePaymentMemo(), 'memo')}
                className="mt-2 text-yellow-700 hover:text-yellow-900 text-xs flex items-center"
              >
                {copied === 'memo' ? (
                  <>
                    <Check className="w-3 h-3 mr-1" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="w-3 h-3 mr-1" />
                    Copy Memo
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Customer Information for Manual Payments */}
      {!bookingData && (
        <div className="bg-gray-50 rounded-lg p-4 mb-6">
          <h4 className="font-medium text-gray-900 mb-3">Your Information</h4>
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
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number *</label>
              <input
                type="tel"
                required
                value={customerInfo.phone}
                onChange={e => setCustomerInfo(prev => ({ ...prev, phone: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="space-y-4">
        {method === 'venmo' && (
          <a
            href={`venmo://paycharge?txn=pay&recipients=@myhibachichef&amount=${amount}&note=${encodeURIComponent(generatePaymentMemo())}`}
            className={`w-full bg-${details.color}-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-${details.color}-700 transition-colors flex items-center justify-center`}
          >
            <ExternalLink className="w-5 h-5 mr-2" />
            Open in Venmo App
          </a>
        )}

        <button
          onClick={handleConfirmPayment}
          disabled={!customerInfo.name || !customerInfo.email || !customerInfo.phone}
          className="w-full bg-green-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          I&apos;ve Sent the Payment
        </button>
      </div>

      {/* Important Notes */}
      <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <h5 className="font-medium text-yellow-900 mb-2">Important Notes:</h5>
        <ul className="text-sm text-yellow-800 space-y-1">
          <li>• Include the memo/note exactly as shown for faster processing</li>
          <li>• Payments are typically verified within 1-2 business hours</li>
          <li>• You&apos;ll receive email confirmation once payment is verified</li>
          <li>• For questions, call (916) 740-8768 or email info@myhibachi.com</li>
        </ul>
      </div>
    </div>
  )
}
