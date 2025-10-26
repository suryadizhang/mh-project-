/**
 * RingCentral SMS Integration
 *
 * This module provides utilities for integrating with RingCentral SMS service.
 * RingCentral provides SMS messaging and voice communication capabilities.
 *
 * Backend Integration:
 * - SMS sending via /api/ringcentral/sms/send
 * - SMS webhooks at /api/ringcentral/webhooks
 * - Conversation tracking in CRM
 */

// Extend window interface for RingCentral widget
declare global {
  interface Window {
    RingCentralWidget?: {
      call?: (phoneNumber: string) => void;
      sendMessage?: (message: string) => void;
      show?: () => void;
      hide?: () => void;
      open?: () => void;
      close?: () => void;
    };
  }
}

/**
 * RingCentral configuration
 */
const RINGCENTRAL_CONFIG = {
  // This should match your backend RingCentral phone number
  BUSINESS_PHONE: '+19167408768', // Your MyHibachi business number
  SMS_ENDPOINT: '/api/ringcentral/sms/send',
  // RingCentral Engage Widget URL (if using web widget)
  WIDGET_URL: 'https://ringcentral.github.io/engage-voice-embeddable/',
} as const;

export interface SMSMessage {
  to: string; // Phone number to send to (E.164 format: +1234567890)
  body: string; // Message content
  from?: string; // Optional: Override from number
}

export interface SMSResponse {
  success: boolean;
  message_id?: string;
  error?: string;
}

/**
 * Sends an SMS message via RingCentral backend API
 *
 * @param message - SMS message details
 * @returns Promise with SMS send result
 *
 * @example
 * ```ts
 * const result = await sendSMS({
 *   to: '+14155551234',
 *   body: 'Thank you for booking with MyHibachi!'
 * });
 *
 * if (result.success) {
 *   console.log('SMS sent:', result.message_id);
 * }
 * ```
 */
export async function sendSMS(message: SMSMessage): Promise<SMSResponse> {
  try {
    // Validate phone number format
    if (!message.to.match(/^\+1\d{10}$/)) {
      return {
        success: false,
        error: 'Invalid phone number format. Must be E.164 format: +1234567890',
      };
    }

    // Validate message body
    if (!message.body || message.body.trim().length === 0) {
      return {
        success: false,
        error: 'Message body cannot be empty',
      };
    }

    // SMS length limit (160 chars for single SMS, 1600 for concatenated)
    if (message.body.length > 1600) {
      return {
        success: false,
        error: 'Message exceeds maximum length of 1600 characters',
      };
    }

    const response = await fetch(RINGCENTRAL_CONFIG.SMS_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        to: message.to,
        body: message.body,
        from: message.from || RINGCENTRAL_CONFIG.BUSINESS_PHONE,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Failed to send SMS' }));
      return {
        success: false,
        error: errorData.error || `Server error: ${response.status}`,
      };
    }

    const data = await response.json();
    return {
      success: true,
      message_id: data.message_id,
    };
  } catch (error) {
    console.error('Error sending SMS:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to send SMS',
    };
  }
}

/**
 * Initiates a phone call using RingCentral Click-to-Call
 * Opens the phone dialer with the RingCentral business number pre-filled
 *
 * @param phoneNumber - Optional specific number to call (defaults to business number)
 */
export function initiateCall(phoneNumber?: string): void {
  if (typeof window !== 'undefined') {
    const number = phoneNumber || RINGCENTRAL_CONFIG.BUSINESS_PHONE;
    window.location.href = `tel:${number}`;
  }
}

/**
 * Formats a phone number to E.164 format for RingCentral
 *
 * @param phoneNumber - Phone number in various formats
 * @returns E.164 formatted number (+1234567890) or null if invalid
 *
 * @example
 * ```ts
 * formatPhoneNumber('(415) 555-1234')  // '+14155551234'
 * formatPhoneNumber('415-555-1234')    // '+14155551234'
 * formatPhoneNumber('4155551234')      // '+14155551234'
 * ```
 */
export function formatPhoneNumber(phoneNumber: string): string | null {
  // Remove all non-numeric characters
  const cleaned = phoneNumber.replace(/\D/g, '');

  // Check if it's a valid US phone number (10 digits)
  if (cleaned.length === 10) {
    return `+1${cleaned}`;
  }

  // Check if it already has country code
  if (cleaned.length === 11 && cleaned.startsWith('1')) {
    return `+${cleaned}`;
  }

  // Invalid format
  return null;
}

/**
 * Gets the RingCentral business phone number
 */
export function getBusinessPhone(): string {
  return RINGCENTRAL_CONFIG.BUSINESS_PHONE;
}

/**
 * Checks if RingCentral SMS is available
 * (Always returns true as it's backend-integrated)
 */
export function isRingCentralAvailable(): boolean {
  return typeof window !== 'undefined';
}

/**
 * Opens RingCentral live chat widget
 * This opens the RingCentral Engage widget for live chat with a real person
 */
export function openRingCentralChat(): void {
  if (typeof window !== 'undefined') {
    // If RingCentral widget is loaded
    if (window.RingCentralWidget?.show) {
      window.RingCentralWidget.show();
    } else if (window.RingCentralWidget?.open) {
      window.RingCentralWidget.open();
    } else {
      // Fallback: Initiate a call if widget not available
      initiateCall();
    }
  }
}

/**
 * Sends a message via RingCentral live chat widget
 *
 * @param message - The message to send
 */
export function sendRingCentralMessage(message: string): void {
  if (typeof window !== 'undefined' && window.RingCentralWidget?.sendMessage) {
    window.RingCentralWidget.sendMessage(message);
  }
}

/**
 * Checks if RingCentral live chat widget is loaded
 */
export function isRingCentralWidgetLoaded(): boolean {
  return typeof window !== 'undefined' && !!window.RingCentralWidget;
}
