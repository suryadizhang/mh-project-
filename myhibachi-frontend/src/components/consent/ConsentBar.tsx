'use client'

import { useEffect, useState } from 'react'

export default function ConsentBar() {
  const [showConsent, setShowConsent] = useState(false)

  useEffect(() => {
    const consent = localStorage.getItem('mh_consent')
    if (!consent) {
      setShowConsent(true)
    }
  }, [])

  const handleAllow = () => {
    localStorage.setItem('mh_consent', 'true')
    setShowConsent(false)

    // Trigger messenger initialization if it's waiting
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('consentGranted'))
    }
  }

  const handleDecline = () => {
    localStorage.setItem('mh_consent', 'false')
    setShowConsent(false)
  }

  if (!showConsent) return null

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 bg-white border-t-2 border-gray-200 shadow-lg p-4">
      <div className="max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="text-sm text-gray-700">
          <span className="font-medium">We use cookies to enable chat features.</span>
          <span className="ml-2 text-gray-600">This helps us provide better customer support.</span>
        </div>

        <div className="flex gap-3">
          <button
            onClick={handleAllow}
            className="px-4 py-2 bg-gradient-to-r from-[#ffb800] to-[#db2b28] text-white rounded-lg font-medium hover:shadow-md transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-orange-500"
            aria-label="Allow cookies and enable chat"
          >
            Allow
          </button>
          <button
            onClick={handleDecline}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
            aria-label="Decline cookies"
          >
            Decline
          </button>
        </div>
      </div>
    </div>
  )
}
