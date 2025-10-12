'use client';

import { Check, Copy, ExternalLink, Mail, Phone, QrCode, Smartphone } from 'lucide-react';
import QRCodeGenerator from 'qrcode';
import { useState } from 'react';

import { apiFetch } from '@/lib/api';
import { logger } from '@/lib/logger';

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

interface AlternativePaymentOptionsProps {
  method: 'zelle' | 'venmo';
  amount: number;
  bookingData: BookingData | null;
  paymentType: 'deposit' | 'balance';
  tipAmount: number;
}

export default function AlternativePaymentOptions({
  method,
  amount,
  bookingData,
  paymentType,
  tipAmount,
}: AlternativePaymentOptionsProps) {
  const [copied, setCopied] = useState<string | null>(null);
  const [paymentSent, setPaymentSent] = useState(false);
  const [showQR, setShowQR] = useState(false);
  const [qrCode, setQrCode] = useState<string | null>(null);
  const [customerInfo, setCustomerInfo] = useState({
    name: bookingData?.customerName || '',
    email: bookingData?.customerEmail || '',
    phone: '',
  });

  const paymentDetails = {
    zelle: {
      email: 'myhibachichef@gmail.com',
      phone: '(916) 740-8768',
      name: 'My Hibachi LLC',
      color: 'purple',
      icon: 'Z',
    },
    venmo: {
      username: '@myhibachichef',
      phone: '(916) 740-8768',
      name: 'My Hibachi LLC',
      color: 'blue',
      icon: 'V',
    },
  };

  const details = paymentDetails[method];

  const copyToClipboard = async (text: string, type: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(type);
      setTimeout(() => setCopied(null), 2000);
    } catch (err) {
      logger.error('Failed to copy', err as Error);
    }
  };

  const generatePaymentMemo = () => {
    const parts = [];
    if (bookingData) {
      parts.push(`Booking: ${bookingData.id}`);
      parts.push(`Event: ${bookingData.eventDate}`);
    }
    parts.push(`Type: ${paymentType === 'deposit' ? 'Deposit' : 'Balance'}`);
    if (tipAmount > 0) {
      parts.push(`Tip: $${tipAmount.toFixed(2)}`);
    }
    return parts.join(' | ');
  };

  const generateVenmoDeepLink = () => {
    const memo = generatePaymentMemo();
    const venmoUrl = `venmo://paycharge?txn=pay&recipients=${encodeURIComponent(
      '@myhibachichef',
    )}&amount=${amount}&note=${encodeURIComponent(memo)}`;
    return venmoUrl;
  };

  const openVenmoApp = () => {
    const deepLink = generateVenmoDeepLink();
    // Try to open Venmo app, fallback to web if app not installed
    window.location.href = deepLink;

    // Fallback to web version after a short delay if app doesn't open
    setTimeout(() => {
      const webUrl = `https://venmo.com/?txn=pay&recipients=myhibachichef&amount=${amount}&note=${encodeURIComponent(
        generatePaymentMemo(),
      )}`;
      window.open(webUrl, '_blank');
    }, 2000);
  };

  const generateQRCode = async () => {
    try {
      let qrData = '';
      if (method === 'venmo') {
        qrData = generateVenmoDeepLink();
      } else if (method === 'zelle') {
        // For Zelle, we'll create a data string with payment info
        qrData = `Zelle Payment\nEmail: myhibachichef@gmail.com\nAmount: $${amount.toFixed(
          2,
        )}\nMemo: ${generatePaymentMemo()}`;
      }

      const qrCodeDataUrl = await QRCodeGenerator.toDataURL(qrData, {
        width: 200,
        margin: 2,
        color: {
          dark: method === 'venmo' ? '#3D95CE' : '#6B46C1',
          light: '#FFFFFF',
        },
      });
      setQrCode(qrCodeDataUrl);
      setShowQR(true);
    } catch (error) {
      logger.error('Error generating QR code', error as Error);
    }
  };

  const handleConfirmPayment = async () => {
    // In a real implementation, this would:
    // 1. Send notification to admin
    // 2. Update booking status
    // 3. Send confirmation email
    setPaymentSent(true);

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
          timestamp: new Date().toISOString(),
        }),
      });
    } catch (error) {
      logger.error('Error recording payment', error as Error);
    }
  };

  if (paymentSent) {
    return (
      <div className="rounded-xl bg-white p-8 text-center shadow-lg">
        <div
          className={`h-16 w-16 bg-${details.color}-100 mx-auto mb-4 flex items-center justify-center rounded-full`}
        >
          <div
            className={`h-8 w-8 bg-${details.color}-600 flex items-center justify-center rounded text-lg font-bold text-white`}
          >
            {details.icon}
          </div>
        </div>
        <h3 className="mb-2 text-2xl font-bold text-gray-900">Payment Instructions Sent!</h3>
        <p className="mb-6 text-gray-600">
          We&apos;ve recorded your intent to pay ${amount.toFixed(2)} via{' '}
          {method.charAt(0).toUpperCase() + method.slice(1)}.
        </p>
        <div className="mb-6 rounded-lg bg-green-50 p-4">
          <div className="text-sm text-green-800">
            <div className="mb-2 font-medium">Next Steps:</div>
            <ol className="list-inside list-decimal space-y-1 text-left">
              <li>Send payment using the details provided above</li>
              <li>Include the memo/note for payment identification</li>
              <li>We&apos;ll confirm receipt within 1-2 business hours</li>
              <li>You&apos;ll receive email confirmation once verified</li>
            </ol>
          </div>
        </div>
        <div className="flex items-center justify-center space-x-4 text-sm text-gray-600">
          <div className="flex items-center">
            <Phone className="mr-1 h-4 w-4" />
            <span>(916) 740-8768</span>
          </div>
          <div className="flex items-center">
            <Mail className="mr-1 h-4 w-4" />
            <span>info@myhibachi.com</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl bg-white p-6 shadow-lg">
      <div className="mb-6">
        <h3 className="mb-2 flex items-center text-lg font-semibold text-gray-900">
          <div
            className={`h-6 w-6 bg-${details.color}-600 mr-2 flex items-center justify-center rounded text-sm font-bold text-white`}
          >
            {details.icon}
          </div>
          {method.charAt(0).toUpperCase() + method.slice(1)} Payment
        </h3>
        <p className="text-sm text-gray-600">
          {method === 'zelle'
            ? 'No processing fees! Send payment directly using Zelle.'
            : 'Send payment using Venmo with 3% processing fee included in total above.'}
        </p>
      </div>

      {/* Payment Instructions */}
      <div className={`bg-${details.color}-50 mb-6 rounded-lg p-4`}>
        <h4 className={`font-medium text-${details.color}-900 mb-3`}>Payment Instructions</h4>
        <div className="space-y-3">
          {method === 'zelle' && (
            <>
              <div className="flex items-center justify-between rounded bg-white p-3">
                <div>
                  <div className="text-sm font-medium text-gray-900">Email</div>
                  <div className="font-mono text-purple-700">{paymentDetails.zelle.email}</div>
                </div>
                <button
                  onClick={() => copyToClipboard(paymentDetails.zelle.email, 'email')}
                  className="rounded p-2 text-purple-600 transition-colors hover:bg-purple-100"
                >
                  {copied === 'email' ? (
                    <Check className="h-4 w-4" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </button>
              </div>
              <div className="flex items-center justify-between rounded bg-white p-3">
                <div>
                  <div className="text-sm font-medium text-gray-900">Phone</div>
                  <div className="font-mono text-purple-700">{details.phone}</div>
                </div>
                <button
                  onClick={() => copyToClipboard(details.phone, 'phone')}
                  className="rounded p-2 text-purple-600 transition-colors hover:bg-purple-100"
                >
                  {copied === 'phone' ? (
                    <Check className="h-4 w-4" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </button>
              </div>
            </>
          )}

          {method === 'venmo' && (
            <div className="flex items-center justify-between rounded bg-white p-3">
              <div>
                <div className="text-sm font-medium text-gray-900">Username</div>
                <div className="font-mono text-blue-700">{paymentDetails.venmo.username}</div>
              </div>
              <button
                onClick={() => copyToClipboard(paymentDetails.venmo.username, 'username')}
                className="rounded p-2 text-blue-600 transition-colors hover:bg-blue-100"
              >
                {copied === 'username' ? (
                  <Check className="h-4 w-4" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </button>
            </div>
          )}

          <div className="flex items-center justify-between rounded bg-white p-3">
            <div>
              <div className="text-sm font-medium text-gray-900">Recipient Name</div>
              <div className={`text-${details.color}-700 font-medium`}>{details.name}</div>
            </div>
          </div>
        </div>

        {/* Quick Payment Buttons */}
        <div className="mb-6">
          <h4 className="mb-3 font-medium text-gray-900">Quick Payment Options</h4>
          <div className="space-y-3">
            {method === 'venmo' && (
              <>
                <button
                  onClick={openVenmoApp}
                  className="flex w-full items-center justify-center rounded-lg bg-blue-600 px-4 py-3 text-white transition-colors hover:bg-blue-700"
                >
                  <Smartphone className="mr-2 h-5 w-5" />
                  Open Venmo App (${amount.toFixed(2)} pre-filled)
                </button>
                <a
                  href={`https://venmo.com/?txn=pay&recipients=myhibachichef&amount=${amount}&note=${encodeURIComponent(
                    generatePaymentMemo(),
                  )}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex w-full items-center justify-center rounded-lg bg-blue-500 px-4 py-3 text-white transition-colors hover:bg-blue-600"
                >
                  <ExternalLink className="mr-2 h-5 w-5" />
                  Pay via Venmo Web
                </a>
                <button
                  onClick={generateQRCode}
                  className="flex w-full items-center justify-center rounded-lg bg-blue-400 px-4 py-3 text-white transition-colors hover:bg-blue-500"
                >
                  <QrCode className="mr-2 h-5 w-5" />
                  Show Venmo QR Code
                </button>
              </>
            )}

            {method === 'zelle' && (
              <>
                <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4">
                  <div className="flex items-start">
                    <QrCode className="mt-0.5 mr-2 h-5 w-5 text-yellow-600" />
                    <div className="text-sm text-yellow-800">
                      <div className="mb-1 font-medium">Zelle Quick Send</div>
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
                  className="flex w-full items-center justify-center rounded-lg bg-purple-600 px-4 py-3 text-white transition-colors hover:bg-purple-700"
                >
                  <QrCode className="mr-2 h-5 w-5" />
                  Generate Payment QR Code
                </button>
              </>
            )}
          </div>
        </div>

        {/* QR Code Display */}
        {showQR && qrCode && (
          <div className="mb-6 rounded-lg border bg-white p-6 text-center">
            <h4 className="mb-3 font-medium text-gray-900">
              {method === 'venmo' ? 'Venmo' : 'Zelle'} Payment QR Code
            </h4>
            <div className="inline-block rounded-lg bg-white p-4 shadow-sm">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={qrCode} alt={`${method} Payment QR Code`} className="mx-auto h-48 w-48" />
            </div>
            <p className="mt-3 text-sm text-gray-600">
              {method === 'venmo'
                ? 'Scan with your Venmo app to pay instantly'
                : 'Scan with your banking app or save payment details'}
            </p>
            <button
              onClick={() => setShowQR(false)}
              className="mt-3 px-4 py-2 text-gray-600 transition-colors hover:text-gray-800"
            >
              Hide QR Code
            </button>
          </div>
        )}
      </div>

      {/* Amount and Memo */}
      <div className="mb-6 rounded-lg bg-gray-50 p-4">
        <h4 className="mb-3 font-medium text-gray-900">Payment Details</h4>
        <div className="space-y-3">
          <div className="flex items-center justify-between rounded bg-white p-3">
            <div>
              <div className="text-sm font-medium text-gray-900">Amount to Send</div>
              <div className="text-xl font-bold text-green-600">${amount.toFixed(2)}</div>
            </div>
            <button
              onClick={() => copyToClipboard(amount.toFixed(2), 'amount')}
              className="rounded p-2 text-gray-600 transition-colors hover:bg-gray-100"
            >
              {copied === 'amount' ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            </button>
          </div>

          <div className="rounded bg-white p-3">
            <div className="mb-2 text-sm font-medium text-gray-900">Memo/Note (Required)</div>
            <div className="rounded border border-yellow-200 bg-yellow-50 p-2">
              <div className="font-mono text-sm break-all text-yellow-800">
                {generatePaymentMemo()}
              </div>
              <button
                onClick={() => copyToClipboard(generatePaymentMemo(), 'memo')}
                className="mt-2 flex items-center text-xs text-yellow-700 hover:text-yellow-900"
              >
                {copied === 'memo' ? (
                  <>
                    <Check className="mr-1 h-3 w-3" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="mr-1 h-3 w-3" />
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
        <div className="mb-6 rounded-lg bg-gray-50 p-4">
          <h4 className="mb-3 font-medium text-gray-900">Your Information</h4>
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
            <div className="md:col-span-2">
              <label className="mb-1 block text-sm font-medium text-gray-700">Phone Number *</label>
              <input
                type="tel"
                required
                value={customerInfo.phone}
                onChange={(e) => setCustomerInfo((prev) => ({ ...prev, phone: e.target.value }))}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-transparent focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="space-y-4">
        {method === 'venmo' && (
          <a
            href={`venmo://paycharge?txn=pay&recipients=@myhibachichef&amount=${amount}&note=${encodeURIComponent(
              generatePaymentMemo(),
            )}`}
            className={`w-full bg-${details.color}-600 rounded-lg px-6 py-3 font-medium text-white hover:bg-${details.color}-700 flex items-center justify-center transition-colors`}
          >
            <ExternalLink className="mr-2 h-5 w-5" />
            Open in Venmo App
          </a>
        )}

        <button
          onClick={handleConfirmPayment}
          disabled={!customerInfo.name || !customerInfo.email || !customerInfo.phone}
          className="w-full rounded-lg bg-green-600 px-6 py-3 font-medium text-white transition-colors hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          I&apos;ve Sent the Payment
        </button>
      </div>

      {/* Important Notes */}
      <div className="mt-6 rounded-lg border border-yellow-200 bg-yellow-50 p-4">
        <h5 className="mb-2 font-medium text-yellow-900">Important Notes:</h5>
        <ul className="space-y-1 text-sm text-yellow-800">
          <li>• Include the memo/note exactly as shown for faster processing</li>
          <li>• Payments are typically verified within 1-2 business hours</li>
          <li>• You&apos;ll receive email confirmation once payment is verified</li>
          <li>• For questions, call (916) 740-8768 or email info@myhibachi.com</li>
        </ul>
      </div>
    </div>
  );
}

