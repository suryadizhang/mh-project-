'use client';

import { ArrowLeft, CheckCircle2, Loader2, Copy, Check } from 'lucide-react';
import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import QRCode from 'qrcode';

interface PaymentData {
  baseAmount: number;
  tipAmount: number;
  subtotal: number;
  selectedMethod?: string;
}

/**
 * Venmo Payment Page
 *
 * Features:
 * - QR code for Venmo app
 * - Manual payment info (username)
 * - Payment confirmation button
 * - 3% processing fee
 */
export default function VenmoPaymentPage() {
  const router = useRouter();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [paymentData, setPaymentData] = useState<PaymentData | null>(null);
  const [totalWithFee, setTotalWithFee] = useState(0);
  const [processingFee, setProcessingFee] = useState(0);
  const [qrCodeGenerated, setQrCodeGenerated] = useState(false);
  const [isConfirmed, setIsConfirmed] = useState(false);
  const [copiedField, setCopiedField] = useState<string>('');

  // Venmo payment info
  const venmoUsername = '@myhibachi-chef'; // Replace with actual Venmo username

  useEffect(() => {
    // Load payment data from sessionStorage
    const storedData = sessionStorage.getItem('paymentData');
    if (!storedData) {
      router.push('/payment');
      return;
    }

    const data: PaymentData = JSON.parse(storedData);
    setPaymentData(data);

    // Calculate fee (3%)
    const fee = data.subtotal * 0.03;
    const total = data.subtotal + fee;
    setProcessingFee(fee);
    setTotalWithFee(total);

    // Generate QR code
    generateQRCode(total);
  }, [router]);

  // Generate Venmo QR code
  const generateQRCode = async (amount: number) => {
    if (!canvasRef.current) return;

    try {
      // Venmo deep link format
      // venmo://paycharge?txn=pay&recipients=USERNAME&amount=AMOUNT&note=NOTE
      const venmoDeepLink = `venmo://paycharge?txn=pay&recipients=${encodeURIComponent(venmoUsername)}&amount=${amount.toFixed(2)}&note=${encodeURIComponent('My Hibachi Payment')}`;

      await QRCode.toCanvas(canvasRef.current, venmoDeepLink, {
        width: 256,
        margin: 2,
        color: {
          dark: '#3D95CE', // Venmo blue
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
      router.push('/payment/success?method=venmo');
    }, 1500);
  };

  const handleBack = () => {
    router.push('/payment/select-method');
  };

  if (!paymentData) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100">
        <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-gray-100 px-4 py-8">
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
            <div className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-blue-400 to-blue-500 text-3xl font-bold text-white shadow-lg">
              V
            </div>
            <h1 className="mb-2 text-3xl font-bold text-gray-900">Pay with Venmo</h1>
            <p className="text-gray-600">3% Processing Fee</p>
          </div>

          {/* Amount Summary */}
          <div className="mb-8 rounded-xl bg-gradient-to-r from-blue-50 to-blue-100 p-6">
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
              <div className="flex justify-between border-t border-blue-200 pt-2">
                <span className="text-orange-600">Processing Fee (3%):</span>
                <span className="font-bold text-orange-600">+${processingFee.toFixed(2)}</span>
              </div>
              <div className="flex justify-between border-t border-blue-300 pt-2">
                <span className="text-lg font-bold text-gray-900">Total Amount:</span>
                <span className="text-2xl font-bold text-blue-600">
                  ${totalWithFee.toFixed(2)}
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
              <div className="rounded-2xl border-4 border-blue-200 bg-white p-4 shadow-lg">
                <canvas ref={canvasRef} className="mx-auto" />
                {!qrCodeGenerated && (
                  <div className="flex h-64 w-64 items-center justify-center">
                    <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
                  </div>
                )}
              </div>
            </div>
            <p className="mt-4 text-center text-sm text-gray-500">
              Open your Venmo app and scan this QR code
            </p>
          </div>

          {/* Manual Payment Info */}
          <div className="mb-8">
            <h2 className="mb-4 text-center text-lg font-semibold text-gray-900">
              Or Send Payment Manually
            </h2>
            <div className="space-y-3">
              {/* Username */}
              <div className="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 p-4">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">👤</span>
                  <div>
                    <p className="text-xs text-gray-500">Venmo Username</p>
                    <p className="font-mono font-medium text-blue-600">{venmoUsername}</p>
                  </div>
                </div>
                <button
                  onClick={() => copyToClipboard(venmoUsername, 'username')}
                  className="rounded-lg p-2 text-blue-600 transition-colors hover:bg-blue-100"
                  title="Copy username"
                >
                  {copiedField === 'username' ? (
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
                    <p className="text-xs text-gray-500">Amount to Send (with fee)</p>
                    <p className="text-xl font-bold text-blue-600">
                      ${totalWithFee.toFixed(2)}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => copyToClipboard(totalWithFee.toFixed(2), 'amount')}
                  className="rounded-lg p-2 text-blue-600 transition-colors hover:bg-blue-100"
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

          {/* Fee Notice */}
          <div className="mb-8 rounded-lg border border-orange-200 bg-orange-50 p-4">
            <div className="flex items-start gap-3">
              <span className="text-2xl">💳</span>
              <div>
                <h3 className="mb-1 font-semibold text-gray-900">Processing Fee Applied</h3>
                <p className="text-sm text-gray-700">
                  A 3% processing fee (${processingFee.toFixed(2)}) has been added to cover payment
                  processing costs. The total amount is ${totalWithFee.toFixed(2)}.
                </p>
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
            className="group flex w-full items-center justify-center gap-3 rounded-xl bg-gradient-to-r from-blue-500 to-blue-600 px-8 py-5 text-lg font-semibold text-white shadow-lg transition-all hover:from-blue-600 hover:to-blue-700 hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-50"
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
            Click the button above after you&apos;ve completed the Venmo payment
          </p>
        </div>

        {/* Security Badge */}
        <div className="mt-6 text-center">
          <p className="flex items-center justify-center gap-2 text-sm text-gray-600">
            <svg className="h-5 w-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            Secure Payment via Venmo
          </p>
        </div>
      </div>
    </div>
  );
}
