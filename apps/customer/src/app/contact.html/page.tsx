"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

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
          .split("; ")
          .find((row) => row.startsWith("qr_session="))
          ?.split("=")[1];

        // Track via backend API
        await fetch("/api/qr/scan/BC001", {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        });
      } catch (error) {
        console.error("Failed to track QR scan:", error);
      }
    };

    // Track the scan
    trackQRScan();

    // Redirect to new contact page after brief delay
    const timer = setTimeout(() => {
      router.push("/contact");
    }, 500);

    return () => clearTimeout(timer);
  }, [router]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50 flex items-center justify-center">
      <div className="text-center">
        {/* Loading Animation */}
        <div className="mb-6">
          <div className="inline-block w-16 h-16 border-4 border-red-600 border-t-transparent rounded-full animate-spin"></div>
        </div>

        <h1 className="text-2xl font-bold text-gray-800 mb-2">
          Welcome to My Hibachi Chef!
        </h1>
        <p className="text-gray-600">
          Redirecting you to our contact page...
        </p>
      </div>
    </div>
  );
}
