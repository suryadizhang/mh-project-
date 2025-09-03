// src/lib/server/stripeCustomerService.ts
// This service now calls the backend API instead of using Stripe directly
import { apiFetch } from '../api'

export interface CustomerData {
  email: string
  name: string
  phone?: string
  address?: {
    line1?: string
    city?: string
    state?: string
    postal_code?: string
    country?: string
  }
}

export interface PaymentPreferences {
  preferredPaymentMethod: 'zelle' | 'venmo' | 'stripe'
  totalBookings?: number
  totalSpent?: number
  zelleUsageCount?: number
  totalSavingsFromZelle?: number
}

export interface StripeCustomer {
  id: string
  email: string
  name: string
  phone?: string
  metadata: Record<string, string>
}

export class StripeCustomerService {
  // Create customer via backend API
  static async createOrUpdateCustomer(customerData: CustomerData): Promise<StripeCustomer> {
    try {
      const response = await apiFetch('/api/v1/customers/create-or-update', {
        method: 'POST',
        body: JSON.stringify(customerData)
      })
      if (!response.success || !response.data) {
        throw new Error(response.error || 'Failed to create/update customer')
      }
      return response.data as StripeCustomer
    } catch (error) {
      console.error('Error creating/updating customer:', error)
      throw error
    }
  }

  // Update payment preferences via backend API
  static async updatePaymentPreferences(
    stripeCustomerId: string,
    preferences: PaymentPreferences
  ): Promise<StripeCustomer> {
    try {
      const response = await apiFetch(`/api/v1/customers/${stripeCustomerId}/preferences`, {
        method: 'PUT',
        body: JSON.stringify(preferences)
      })
      if (!response.success || !response.data) {
        throw new Error(response.error || 'Failed to update preferences')
      }
      return response.data as StripeCustomer
    } catch (error) {
      console.error('Error updating customer preferences:', error)
      throw error
    }
  }

  // Get customer with analytics via backend API
  static async getCustomerAnalytics(stripeCustomerId: string) {
    try {
      const response = await apiFetch(`/api/v1/customers/${stripeCustomerId}/analytics`)
      if (!response.success) {
        throw new Error(response.error || 'Failed to get analytics')
      }
      return response.data
    } catch (error) {
      console.error('Error getting customer analytics:', error)
      throw error
    }
  }

  // Track customer payment preferences via backend API
  static async trackPaymentPreference(customerId: string, paymentMethod: string): Promise<void> {
    try {
      const response = await apiFetch(`/api/v1/customers/${customerId}/track-payment`, {
        method: 'POST',
        body: JSON.stringify({ paymentMethod })
      })
      if (!response.success) {
        throw new Error(response.error || 'Failed to track payment preference')
      }
      console.log(`[PAYMENT PREFERENCE TRACKED] Customer: ${customerId}, Method: ${paymentMethod}`)
    } catch (error) {
      console.error('Error tracking payment preference:', error)
    }
  }

  // Find customer by email via backend API
  static async findCustomerByEmail(email: string): Promise<StripeCustomer | null> {
    try {
      const response = await apiFetch(
        `/api/v1/customers/find-by-email?email=${encodeURIComponent(email)}`
      )
      if (!response.success) {
        return null // Customer not found
      }
      return response.data as StripeCustomer
    } catch (error) {
      console.error('Error finding customer by email:', error)
      return null
    }
  }

  // Create customer portal session via backend API
  static async createPortalSession(stripeCustomerId: string, returnUrl?: string) {
    try {
      const response = await apiFetch(`/api/v1/customers/${stripeCustomerId}/portal`, {
        method: 'POST',
        body: JSON.stringify({ returnUrl })
      })
      if (!response.success || !response.data) {
        throw new Error(response.error || 'Failed to create portal session')
      }
      return response.data
    } catch (error) {
      console.error('Error creating portal session:', error)
      throw error
    }
  }
}
