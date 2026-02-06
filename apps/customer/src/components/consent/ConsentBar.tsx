'use client';

import { useEffect, useState } from 'react';

export default function ConsentBar() {
  const [showConsent, setShowConsent] = useState(false);

  useEffect(() => {
    const consent = localStorage.getItem('mh_consent');
    if (!consent) {
      setShowConsent(true);
    }
  }, []);

  const handleAllow = () => {
    localStorage.setItem('mh_consent', 'true');
    setShowConsent(false);

    // Trigger messenger initialization if it's waiting
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('consentGranted'));
    }
  };

  const handleDecline = () => {
    localStorage.setItem('mh_consent', 'false');
    setShowConsent(false);
  };

  if (!showConsent) return null;

  return (
    <div className="fixed right-0 bottom-0 left-0 z-40 border-t-2 border-gray-200 bg-white p-4 shadow-lg">
      <div className="mx-auto flex max-w-4xl flex-col items-center justify-between gap-4 sm:flex-row">
        <div className="text-sm text-gray-700">
          <span className="font-medium">We use cookies to enable chat features.</span>
          <span className="ml-2 text-gray-600">This helps us provide better customer support.</span>
        </div>

        <div className="flex gap-3">
          <button
            onClick={handleAllow}
            className="rounded-lg bg-gradient-to-r from-[#ffb800] to-[#db2b28] px-4 py-2 font-medium text-white transition-all duration-200 hover:shadow-md focus:ring-2 focus:ring-orange-500 focus:outline-none"
            aria-label="Allow cookies and enable chat"
          >
            Allow
          </button>
          <button
            onClick={handleDecline}
            className="rounded-lg bg-gray-100 px-4 py-2 font-medium text-gray-700 transition-all duration-200 hover:bg-gray-200 focus:ring-2 focus:ring-gray-500 focus:outline-none"
            aria-label="Decline cookies"
          >
            Decline
          </button>
        </div>
      </div>
    </div>
  );
}
