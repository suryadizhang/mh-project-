'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

// Force dynamic rendering to prevent static export conflicts
export const dynamic = 'force-dynamic';

export default function ContactHtmlRedirect() {
  const router = useRouter();

  useEffect(() => {
    // Track that this came from the old QR code
    const trackQRScan = async () => {
      try {
        // Get session cookie (backend will create if needed)
        const _sessionId = document.cookie
          .split('; ')
          .find((row) => row.startsWith('qr_session='))
          ?.split('=')[1];

        // Track via backend API
        await fetch('/api/qr/scan/BC001', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });
      } catch (error) {
        console.error('Failed to track QR scan:', error);
      }
    };

    // Track the scan
    trackQRScan();

    // Redirect to booking page after brief delay
    const timer = setTimeout(() => {
      router.push('/book-us/');
    }, 500);

    return () => clearTimeout(timer);
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-red-50 to-orange-50">
      <div className="text-center">
        {/* Loading Animation */}
        <div className="mb-6">
          <div className="inline-block h-16 w-16 animate-spin rounded-full border-4 border-red-600 border-t-transparent"></div>
        </div>

        <h1 className="mb-2 text-2xl font-bold text-gray-800">Welcome to My Hibachi Chef!</h1>
        <p className="text-gray-600">Redirecting you to our booking page...</p>
      </div>
    </div>
  );
}
