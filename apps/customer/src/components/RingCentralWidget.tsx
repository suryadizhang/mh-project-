'use client'

import { useEffect } from 'react'

/**
 * RingCentral Configuration Component
 *
 * This component configures RingCentral for voice calls and SMS only.
 * Live chat happens within the existing AI Assistant window, not a separate widget.
 */
export default function RingCentralWidget() {
  useEffect(() => {
    // Configure RingCentral settings
    const configureRingCentral = () => {
      if (typeof window !== 'undefined' && window.RingCentralWidget) {
        console.log('✅ RingCentral loaded successfully')

        // IMPORTANT: Hide the RingCentral widget completely
        // We're using RingCentral API only, NOT their UI widget
        // Our AI Assistant window handles the live chat UI
        if (window.RingCentralWidget.hide) {
          window.RingCentralWidget.hide()
        }

        // Disable features we don't need
        const config = {
          // Enable only voice calls and SMS
          enableVoice: true,
          enableSMS: true,
          
          // Disable features we don't use
          enableVideo: false,
          enableScreenShare: false,
          enableConference: false,
          enableMeeting: false,
          
          // Hide the widget UI (we use our own chat window)
          hideWidget: true,
          startMinimized: true,
        }

        // Apply configuration if method exists
        if (window.RingCentralWidget.configure) {
          window.RingCentralWidget.configure(config)
        }

        // GTM tracking
        if (typeof window !== 'undefined' && (window as unknown as { dataLayer?: unknown[] }).dataLayer) {
          ;(window as unknown as { dataLayer: unknown[] }).dataLayer.push({
            event: 'ringcentral_configured',
            config: 'voice_sms_only'
          })
        }
      }
    }

    // Wait for RingCentral to load
    const checkWidget = setInterval(() => {
      if (typeof window !== 'undefined' && window.RingCentralWidget) {
        clearInterval(checkWidget)
        configureRingCentral()
      }
    }, 500)

    // Timeout after 10 seconds
    const timeout = setTimeout(() => {
      clearInterval(checkWidget)
      console.warn('⚠️ RingCentral widget did not load within 10 seconds')
    }, 10000)

    // Cleanup
    return () => {
      clearInterval(checkWidget)
      clearTimeout(timeout)
    }
  }, [])

  // This component doesn't render anything visible
  return null
}

/**
 * Lead Capture Integration
 * Call this before opening RingCentral to pre-fill user info
 */
export function setRingCentralUserInfo(userInfo: {
  name?: string
  phone?: string
  email?: string
  context?: string
}) {
  if (typeof window !== 'undefined' && window.RingCentralWidget) {
    // Store user info for RingCentral session
    if (window.RingCentralWidget.setUserInfo) {
      window.RingCentralWidget.setUserInfo({
        name: userInfo.name || '',
        phoneNumber: userInfo.phone || '',
        email: userInfo.email || '',
        notes: userInfo.context || 'Customer from MyHibachi website'
      })
    }

    console.log('✅ User info set for RingCentral:', userInfo.name)
  }
}

/**
 * Custom Trigger - Initiate RingCentral call
 */
export function initiateRingCentralCall(phoneNumber?: string) {
  const businessPhone = '+19167408768'
  const number = phoneNumber || businessPhone

  if (typeof window !== 'undefined' && window.RingCentralWidget?.call) {
    window.RingCentralWidget.call(number)
    
    // GTM tracking
    if ((window as unknown as { dataLayer?: unknown[] }).dataLayer) {
      ;(window as unknown as { dataLayer: unknown[] }).dataLayer.push({
        event: 'ringcentral_call_initiated',
        phone: number
      })
    }
  } else {
    // Fallback to tel: link
    window.location.href = `tel:${number}`
  }
}

/**
 * Custom Trigger - Send SMS via RingCentral
 */
export async function sendRingCentralSMS(to: string, message: string): Promise<boolean> {
  try {
    const response = await fetch('/api/ringcentral/sms/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ to, body: message, from: '+19167408768' })
    })

    if (response.ok) {
      // GTM tracking
      if (typeof window !== 'undefined' && (window as unknown as { dataLayer?: unknown[] }).dataLayer) {
        ;(window as unknown as { dataLayer: unknown[] }).dataLayer.push({
          event: 'ringcentral_sms_sent',
          to_masked: to.substring(0, 6) + '****'
        })
      }
      return true
    }
    return false
  } catch (error) {
    console.error('Failed to send SMS:', error)
    return false
  }
}

