'use client'

import { useEffect } from 'react'
import contactData from '@/data/contact.json'

declare global {
  interface Window {
    FB?: {
      init: (config: { xfbml: boolean; version: string }) => void
      CustomerChat: {
        show: () => void
        hide: () => void
      }
    }
  }
}

export default function MetaMessenger() {
  useEffect(() => {
    // Only run in browser environment
    if (typeof window === 'undefined') return

    // Check if Facebook App ID is properly configured
    const appId = contactData.facebookAppId
    if (!appId || appId === '1234567890123456') {
      console.warn(
        'Facebook Messenger: App ID not configured. Please set up a real Facebook App ID to enable Messenger chat.'
      )
      return
    }

    // Load Facebook SDK
    const loadFacebookSDK = () => {
      // Prevent multiple SDK loads
      if (window.FB) return

      // Create Facebook SDK script with App ID
      const script = document.createElement('script')
      script.async = true
      script.defer = true
      script.crossOrigin = 'anonymous'
      script.src = `https://connect.facebook.net/en_US/sdk.js#xfbml=1&version=v18.0&appId=${appId}`

      script.onload = () => {
        if (window.FB) {
          window.FB.init({
            xfbml: true,
            version: 'v18.0'
          })
          console.log('Facebook SDK loaded successfully with App ID:', appId)
        }
      }

      script.onerror = () => {
        console.error('Failed to load Facebook SDK')
      }

      document.head.appendChild(script)
    }

    loadFacebookSDK()

    return () => {
      // Cleanup function - remove SDK script if component unmounts
      const script = document.querySelector('script[src*="facebook.net"]')
      if (script) {
        script.remove()
      }
    }
  }, [])

  // Check if Facebook App ID is configured
  const appId = contactData.facebookAppId
  const pageId = contactData.facebookPageId

  if (!appId || appId === '1234567890123456') {
    // Return null if not configured - no Facebook Messenger widget will show
    return null
  }

  return (
    <>
      {/* Facebook Customer Chat Plugin */}
      <div id="fb-root"></div>
      <div
        className="fb-customerchat"
        data-attribution="page_inbox"
        data-page-id={pageId}
        data-theme-color="#db2b28"
        data-logged-in-greeting={contactData.greetings.loggedIn}
        data-logged-out-greeting={contactData.greetings.loggedOut}
      ></div>
    </>
  )
}
