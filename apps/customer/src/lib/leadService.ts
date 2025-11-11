/**
 * Lead Generation Service
 * Centralized service for submitting leads from various sources
 *
 * This service provides a unified interface for lead submission across:
 * - Quote Calculator (WEB_QUOTE)
 * - Chat Assistant (CHAT)
 * - Failed Bookings (BOOKING_FAILED)
 */

import { logger } from '@/lib/logger'

// TypeScript Types
export type LeadSource =
  | 'WEB_QUOTE'
  | 'CHAT'
  | 'BOOKING_FAILED'
  | 'INSTAGRAM'
  | 'FACEBOOK'
  | 'GOOGLE'
  | 'SMS'
  | 'PHONE'
  | 'REFERRAL'
  | 'EVENT'

export type ContactChannel =
  | 'EMAIL'
  | 'SMS'
  | 'INSTAGRAM'
  | 'FACEBOOK'
  | 'GOOGLE'
  | 'YELP'
  | 'WEB'

export interface LeadContact {
  channel: ContactChannel
  handle_or_address: string
  verified?: boolean
}

export interface LeadContext {
  party_size_adults?: number
  party_size_kids?: number
  estimated_budget_dollars?: number
  event_date_pref?: string  // ISO date string
  event_date_range_start?: string  // ISO date string
  event_date_range_end?: string  // ISO date string
  zip_code?: string
  service_type?: string
  preferred_date?: string  // For failed bookings
  preferred_time?: string  // For failed bookings
  notes?: string
}

export interface LeadSubmission {
  source: LeadSource
  contacts: LeadContact[]
  context?: LeadContext
  utm_source?: string
  utm_medium?: string
  utm_campaign?: string
}

export interface LeadResponse {
  id: string
  source: LeadSource
  status: string
  quality: string | null
  score: number
  created_at: string
  utm_source?: string
  utm_medium?: string
  utm_campaign?: string
}

export interface LeadError {
  error: string
  details?: unknown
}

/**
 * Submit a lead to the backend
 *
 * @param lead - Lead submission data
 * @returns Promise with lead response or error
 */
export async function submitLead(
  lead: LeadSubmission
): Promise<{ success: true; data: LeadResponse } | { success: false; error: string }> {
  try {
    // Validate lead data
    if (!lead.source) {
      throw new Error('Lead source is required')
    }

    if (!lead.contacts || lead.contacts.length === 0) {
      throw new Error('At least one contact is required')
    }

    // Validate contacts
    for (const contact of lead.contacts) {
      if (!contact.channel || !contact.handle_or_address) {
        throw new Error('Each contact must have channel and handle_or_address')
      }
    }

    logger.debug('Submitting lead', {
      source: lead.source,
      contactCount: lead.contacts.length,
      campaign: lead.utm_campaign
    })

    // Submit to API
    const response = await fetch('/api/leads', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(lead)
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
      logger.error('Lead submission failed', undefined, {
        status: response.status,
        error: errorData
      })

      return {
        success: false,
        error: errorData.error || `Failed to submit lead (${response.status})`
      }
    }

    const data = await response.json()

    logger.info('Lead submitted successfully', {
      leadId: data.id,
      source: lead.source,
      campaign: lead.utm_campaign
    })

    return {
      success: true,
      data
    }
  } catch (error) {
    logger.error('Lead submission error', error as Error)

    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to submit lead'
    }
  }
}

/**
 * Submit a lead from the Quote Calculator
 *
 * @param quoteData - Quote calculator data
 * @returns Promise with lead response or error
 */
export async function submitQuoteLead(quoteData: {
  name: string
  phone: string
  adults: number
  children: number
  location?: string
  zipCode?: string
  grandTotal: number
}): Promise<{ success: true; data: LeadResponse } | { success: false; error: string }> {
  const lead: LeadSubmission = {
    source: 'WEB_QUOTE',
    contacts: [
      {
        channel: 'SMS',
        handle_or_address: quoteData.phone,
        verified: false
      }
    ],
    context: {
      party_size_adults: quoteData.adults,
      party_size_kids: quoteData.children,
      estimated_budget_dollars: quoteData.grandTotal,
      zip_code: quoteData.zipCode,
      service_type: 'hibachi_catering',
      notes: `Quote requested via calculator. Location: ${quoteData.location || 'Not specified'}. Name: ${quoteData.name}`
    },
    utm_source: 'website',
    utm_medium: 'quote_calculator',
    utm_campaign: 'quote_page'
  }

  return await submitLead(lead)
}

/**
 * Submit a lead from the Chat Assistant
 *
 * @param chatData - Chat assistant data
 * @returns Promise with lead response or error
 */
export async function submitChatLead(chatData: {
  name: string
  phone: string
}): Promise<{ success: true; data: LeadResponse } | { success: false; error: string }> {
  const lead: LeadSubmission = {
    source: 'CHAT',
    contacts: [
      {
        channel: 'SMS',
        handle_or_address: chatData.phone,
        verified: false
      }
    ],
    context: {
      service_type: 'hibachi_catering',
      notes: `Chat lead captured. Name: ${chatData.name}`
    },
    utm_source: 'website',
    utm_medium: 'chat_widget',
    utm_campaign: 'chat_page'
  }

  return await submitLead(lead)
}

/**
 * Submit a lead from a failed booking
 *
 * @param bookingData - Failed booking data
 * @param failureReason - Reason for booking failure
 * @param errorDetails - Optional error details
 * @returns Promise with lead response or error
 */
export async function submitFailedBookingLead(bookingData: {
  name: string
  email: string
  phone: string
  eventDate: Date
  eventTime: '12PM' | '3PM' | '6PM' | '9PM'
  guestCount: number
  addressZipcode?: string
  venueZipcode?: string
  fullAddress: string
}, failureReason: string, errorDetails?: unknown): Promise<{ success: true; data: LeadResponse } | { success: false; error: string }> {
  const lead: LeadSubmission = {
    source: 'BOOKING_FAILED',
    contacts: [
      {
        channel: 'SMS',
        handle_or_address: bookingData.phone,
        verified: false
      },
      {
        channel: 'EMAIL',
        handle_or_address: bookingData.email,
        verified: false
      }
    ],
    context: {
      party_size_adults: bookingData.guestCount,
      party_size_kids: 0,
      estimated_budget_dollars: bookingData.guestCount * 65, // $65 per person estimate
      zip_code: bookingData.addressZipcode || bookingData.venueZipcode,
      service_type: 'hibachi_catering',
      preferred_date: bookingData.eventDate.toISOString().split('T')[0],
      preferred_time: bookingData.eventTime,
      notes: `Failed booking attempt. Name: ${bookingData.name}. Reason: ${failureReason}. Date: ${bookingData.eventDate.toISOString().split('T')[0]} at ${bookingData.eventTime}. Location: ${bookingData.fullAddress}. ${errorDetails ? `Error: ${JSON.stringify(errorDetails)}` : ''}`
    },
    utm_source: 'website',
    utm_medium: 'booking_form',
    utm_campaign: 'failed_booking_recovery'
  }

  return await submitLead(lead)
}

/**
 * Validate phone number format
 *
 * @param phone - Phone number to validate
 * @returns True if valid, false otherwise
 */
export function validatePhoneNumber(phone: string): boolean {
  // Remove all non-digit characters
  const digitsOnly = phone.replace(/\D/g, '')

  // Must have at least 10 digits
  return digitsOnly.length >= 10
}

/**
 * Validate ZIP code format
 *
 * @param zipCode - ZIP code to validate
 * @returns True if valid, false otherwise
 */
export function validateZipCode(zipCode: string): boolean {
  // US ZIP code format: 12345 or 12345-6789
  return /^\d{5}(-\d{4})?$/.test(zipCode)
}

/**
 * Validate email format
 *
 * @param email - Email to validate
 * @returns True if valid, false otherwise
 */
export function validateEmail(email: string): boolean {
  // Basic email validation
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}
