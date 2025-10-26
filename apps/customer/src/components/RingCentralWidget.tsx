'use client'

import { useEffect } from 'react'

/**
 * RingCentral Embeddable Widget Component
 *
 * This component initializes and configures the RingCentral widget
 * for live chat, SMS, and phone call capabilities.
 */
export default function RingCentralWidget() {
  useEffect(() => {
    // Wait for RingCentral widget to load
    const checkWidget = setInterval(() => {
      if (typeof window !== 'undefined' && window.RingCentralWidget) {
        clearInterval(checkWidget)
        
        // Widget is loaded, you can configure it here if needed
        console.log('✅ RingCentral Widget loaded successfully')
        
        // Optional: Configure widget behavior
        // Example: Auto-hide on load, only show when user clicks
        if (window.RingCentralWidget.hide) {
          window.RingCentralWidget.hide()
        }
        
        // GTM tracking when widget loads
        if (typeof window !== 'undefined' && (window as unknown as { dataLayer?: unknown[] }).dataLayer) {
          ;(window as unknown as { dataLayer: unknown[] }).dataLayer.push({
            event: 'ringcentral_widget_loaded'
          })
        }
      }
    }, 500)

    // Cleanup
    return () => {
      clearInterval(checkWidget)
    }
  }, [])

  // This component doesn't render anything visible
  return null
}
