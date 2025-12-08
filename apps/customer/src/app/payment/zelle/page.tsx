'use client';

import { ArrowLeft, CheckCircle2, Loader2, Copy, Check } from 'lucide-react';
import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import QRCode from 'qrcode';
import { useProtectedPhone, useProtectedPaymentEmail } from '@/components/ui/ProtectedPhone';

interface PaymentData {
  baseAmount: number;
  tipAmount: number;
  subtotal: number;
  selectedMethod?: string;
}

/**
 * Zelle Payment Page
 *
 * Features:
 * - QR code for Zelle app
 * - Manual payment info (email, phone)
 * - Payment confirmation button
 * - FREE payment method (no processing fees)
 */
export default function ZellePaymentPage() {
  const router = useRouter();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [paymentData, setPaymentData] = useState<PaymentData | null>(null);
  const [qrCodeGenerated, setQrCodeGenerated] = useState(false);
  const [isConfirmed, setIsConfirmed] = useState(false);
  const [copiedField, setCopiedField] = useState<string>('');

  // Use protected hooks for anti-scraping
  const { formatted: zellePhone, tel: zelleTel } = useProtectedPhone();
  const { email: zelleEmail } = useProtectedPaymentEmail();

  useEffect(() => {
    // Load payment data from sessionStorage
    const storedData = sessionStorage.getItem('paymentData');
    if (!storedData) {
      router.push('/payment');
      return;
    }

    const data: PaymentData = JSON.parse(storedData);
    setPaymentData(data);
  }, [router]);

  // Generate QR code when email is loaded and paymentData is available
  useEffect(() => {
    if (zelleEmail && paymentData) {
      generateQRCode(paymentData.subtotal, zelleEmail);
    }
  }, [zelleEmail, paymentData]);

  // Generate Zelle QR code
  const generateQRCode = async (amount: number, email: string) => {
    if (!canvasRef.current || !email) return;

    try {
      // Zelle QR code format (simplified - actual format may vary)
      // This creates a QR code with the email and amount
      const zelleData = `mailto:${email}?subject=Payment&body=Amount: $${amount.toFixed(2)}`;

      await QRCode.toCanvas(canvasRef.current, zelleData, {
        width: 256,
        margin: 2,
        color: {
          dark: '#6B21A8', // Purple for Zelle
          light: '#FFFFFF',
        },
      });

      setQrCodeGenerated(true);
    } catch (error) {
      console.error('Error generating QR code:', error);
    }
  };

  // Copy to clipboard
  const copyToClipboard = async (text: string, field: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedField(field);
      setTimeout(() => setCopiedField(''), 2000);
    } catch (error) {
      console.error('Error copying to clipboard:', error);
    }
  };

  // Handle payment confirmation
  const handleConfirmPayment = async () => {
    setIsConfirmed(true);

    // In a real app, you would:
    // 1. Store the payment confirmation in the database
    // 2. Send email notification to admin
    // 3. Update booking status

    // For now, just redirect to success page after a delay
    setTimeout(() => {
      router.push('/payment/success?method=zelle');
    }, 1500);
  };

  const handleBack = () => {
    router.push('/payment/select-method');
  };

  if (!paymentData) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100">
        <Loader2 className="h-12 w-12 animate-spin text-purple-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-gray-100 px-4 py-8">
      <div className="mx-auto max-w-2xl">
        {/* Back Button */}
        <button
          onClick={handleBack}
          className="mb-6 flex items-center gap-2 text-gray-600 transition-colors hover:text-gray-900"
        >
          <ArrowLeft className="h-5 w-5" />
          <span className="font-medium">Back to Payment Methods</span>
        </button>

        {/* Main Payment Card */}
        <div className="rounded-2xl bg-white p-8 shadow-2xl">
          {/* Header */}
          <div className="mb-6 text-center">
            <div className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-purple-600 to-purple-700 text-3xl font-bold text-white shadow-lg">
              Z
            </div>
            <h1 className="mb-2 text-3xl font-bold text-gray-900">Pay with Zelle</h1>
            <p className="text-gray-600">FREE Payment - No Processing Fees</p>
          </div>

          {/* Amount Summary */}
          <div className="mb-8 rounded-xl bg-gradient-to-r from-purple-50 to-purple-100 p-6">
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Base Amount:</span>
                <span className="font-medium">${paymentData.baseAmount.toFixed(2)}</span>
              </div>
              {paymentData.tipAmount > 0 && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Tip:</span>
                  <span className="font-medium">${paymentData.tipAmount.toFixed(2)}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-gray-600">Subtotal:</span>
                <span className="font-medium">${paymentData.subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between border-t border-purple-200 pt-2">
                <span className="text-green-600">Processing Fee:</span>
                <span className="font-bold text-green-600">FREE ✨</span>
              </div>
              <div className="flex justify-between border-t border-purple-300 pt-2">
                <span className="text-lg font-bold text-gray-900">Total Amount:</span>
                <span className="text-2xl font-bold text-purple-600">
                  ${paymentData.subtotal.toFixed(2)}
                </span>
              </div>
            </div>
          </div>

          {/* QR Code Section */}
          <div className="mb-8">
            <h2 className="mb-4 text-center text-lg font-semibold text-gray-900">
              Scan QR Code to Pay
            </h2>
            <div className="flex justify-center">
              <div className="rounded-2xl border-4 border-purple-200 bg-white p-4 shadow-lg">
                <canvas ref={canvasRef} className="mx-auto" />
                {!qrCodeGenerated && (
                  <div className="flex h-64 w-64 items-center justify-center">
                    <Loader2 className="h-8 w-8 animate-spin text-purple-600" />
                  </div>
                )}
              </div>
            </div>
            <p className="mt-4 text-center text-sm text-gray-500">
              Open your Zelle app and scan this QR code
            </p>
          </div>

          {/* Manual Payment Info */}
          <div className="mb-8">
            <h2 className="mb-4 text-center text-lg font-semibold text-gray-900">
              Or Send Payment Manually
            </h2>
            <div className="space-y-3">
              {/* Email */}
              <div className="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 p-4">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">📧</span>
                  <div>
                    <p className="text-xs text-gray-500">Email</p>
                    <p className="font-mono font-medium text-gray-900">{zelleEmail || 'Loading...'}</p>
                  </div>
                </div>
                <button
                  onClick={() => zelleEmail && copyToClipboard(zelleEmail, 'email')}
                  className="rounded-lg p-2 text-purple-600 transition-colors hover:bg-purple-100"
                  title="Copy email"
                  disabled={!zelleEmail}
                >
                  {copiedField === 'email' ? (
                    <Check className="h-5 w-5 text-green-600" />
                  ) : (
                    <Copy className="h-5 w-5" />
                  )}
                </button>
              </div>

              {/* Phone */}
              <div className="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 p-4">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">📱</span>
                  <div>
                    <p className="text-xs text-gray-500">Phone</p>
                    <p className="font-mono font-medium text-gray-900">{zellePhone || 'Loading...'}</p>
                  </div>
                </div>
                <button
                  onClick={() => zellePhone && copyToClipboard(zellePhone, 'phone')}
                  className="rounded-lg p-2 text-purple-600 transition-colors hover:bg-purple-100"
                  title="Copy phone"
                  disabled={!zellePhone}
                >
                  {copiedField === 'phone' ? (
                    <Check className="h-5 w-5 text-green-600" />
                  ) : (
                    <Copy className="h-5 w-5" />
                  )}
                </button>
              </div>

              {/* Amount */}
              <div className="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 p-4">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">💰</span>
                  <div>
                    <p className="text-xs text-gray-500">Amount to Send</p>
                    <p className="text-xl font-bold text-purple-600">
                      ${paymentData.subtotal.toFixed(2)}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => copyToClipboard(paymentData.subtotal.toFixed(2), 'amount')}
                  className="rounded-lg p-2 text-purple-600 transition-colors hover:bg-purple-100"
                  title="Copy amount"
                >
                  {copiedField === 'amount' ? (
                    <Check className="h-5 w-5 text-green-600" />
                  ) : (
                    <Copy className="h-5 w-5" />
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Confirmation Time Info */}
          <div className="mb-8 rounded-lg border border-yellow-200 bg-yellow-50 p-4">
            <div className="flex items-start gap-3">
              <span className="text-2xl">⏱️</span>
              <div>
                <h3 className="mb-1 font-semibold text-gray-900">Confirmation Time</h3>
                <p className="text-sm text-gray-700">
                  After you send the payment, we&apos;ll confirm it within 1-2 hours and send you an
                  email confirmation.
                </p>
              </div>
            </div>
          </div>

          {/* Confirm Button */}
          <button
            onClick={handleConfirmPayment}
            disabled={isConfirmed}
            className="group flex w-full items-center justify-center gap-3 rounded-xl bg-gradient-to-r from-purple-600 to-purple-700 px-8 py-5 text-lg font-semibold text-white shadow-lg transition-all hover:from-purple-700 hover:to-purple-800 hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isConfirmed ? (
              <>
                <CheckCircle2 className="h-6 w-6" />
                <span>Payment Confirmed</span>
              </>
            ) : (
              <>
                <CheckCircle2 className="h-6 w-6 transition-transform group-hover:scale-110" />
                <span>I&apos;ve Sent the Payment</span>
              </>
            )}
          </button>

          {/* Help Text */}
          <p className="mt-4 text-center text-xs text-gray-500">
            Click the button above after you&apos;ve completed the Zelle payment
          </p>
        </div>

        {/* Security Badge */}
        <div className="mt-6 text-center">
          <p className="flex items-center justify-center gap-2 text-sm text-gray-600">
            <svg className="h-5 w-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            Secure Payment via Zelle
          </p>
        </div>
      </div>
    </div>
  );
}
