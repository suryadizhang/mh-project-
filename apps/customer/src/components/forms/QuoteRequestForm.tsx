'use client'

import React, { useState } from 'react'

import { apiFetch } from '@/lib/api'
import { logger } from '@/lib/logger'

interface QuoteFormData {
  name: string
  email: string
  phone: string
  eventDate: string
  guestCount: number
  budget: string
  location: string
  message: string
}

interface QuoteRequestFormProps {
  className?: string
  onSuccess?: () => void
}

const budgetOptions = [
  'Under $500',
  '$500 - $1,000',
  '$1,000 - $2,000',
  '$2,000 - $5,000',
  'Over $5,000',
  'Not sure / Need help'
]

export function QuoteRequestForm({ className = '', onSuccess }: QuoteRequestFormProps) {
  const [formData, setFormData] = useState<QuoteFormData>({
    name: '',
    email: '',
    phone: '',
    eventDate: '',
    guestCount: 1,
    budget: '',
    location: '',
    message: ''
  })

  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target
    
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value
    }))
  }

  // Format phone number as user types
  const formatPhoneForDisplay = (value: string): string => {
    // Remove all non-digit characters
    const digits = value.replace(/\D/g, '')
    
    // Format as (XXX) XXX-XXXX
    if (digits.length <= 3) {
      return digits
    } else if (digits.length <= 6) {
      return `(${digits.slice(0, 3)}) ${digits.slice(3)}`
    } else {
      return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6, 10)}`
    }
  }

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatPhoneForDisplay(e.target.value)
    setFormData(prev => ({ ...prev, phone: formatted }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setError(null)

    // Validate required fields
    if (!formData.name || formData.name.trim().length < 2) {
      setError('Please enter your full name')
      setIsSubmitting(false)
      return
    }

    if (!formData.phone || formData.phone.replace(/\D/g, '').length < 10) {
      setError('Please enter a valid phone number with at least 10 digits')
      setIsSubmitting(false)
      return
    }

    try {
      // Call public lead capture endpoint (no auth required)
      const response = await apiFetch('/api/v1/public/leads', {
        method: 'POST',
        body: JSON.stringify({
          name: formData.name,
          phone: formData.phone,  // Now required
          email: formData.email || undefined,
          event_date: formData.eventDate || undefined,
          guest_count: formData.guestCount || undefined,
          budget: formData.budget || undefined,
          location: formData.location || undefined,
          message: formData.message || undefined,
          source: 'quote'
        })
      })

      if (response.success) {
        logger.info('Quote request submitted successfully')
        
        setSubmitted(true)
        
        if (onSuccess) {
          onSuccess()
        }

        // Reset form after 3 seconds
        setTimeout(() => {
          setFormData({
            name: '',
            email: '',
            phone: '',
            eventDate: '',
            guestCount: 1,
            budget: '',
            location: '',
            message: ''
          })
          setSubmitted(false)
        }, 3000)
      } else {
        throw new Error(response.message || 'Failed to submit quote request')
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to submit quote request'
      setError(errorMessage)
      logger.error('Quote request submission failed')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (submitted) {
    return (
      <div className={`bg-green-50 border border-green-200 rounded-lg p-8 text-center ${className}`}>
        <div className="text-green-600 mb-4">
          <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h3 className="text-2xl font-bold text-gray-900 mb-2">Thank You!</h3>
        <p className="text-gray-600">
          We&apos;ve received your quote request and will contact you shortly with a personalized quote.
        </p>
        <p className="text-sm text-gray-500 mt-4">
          Expected response time: Within 24 hours
        </p>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className={`space-y-6 ${className}`}>
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Get Your Free Quote</h2>
        
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-600">{error}</p>
          </div>
        )}

        {/* Contact Information */}
        <div className="space-y-4 mb-6">
          <h3 className="text-lg font-semibold text-gray-700">Contact Information</h3>
          
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
              Full Name *
            </label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              minLength={2}
              maxLength={100}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
              placeholder="John Doe"
            />
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Email Address
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
              placeholder="john@example.com"
            />
            <p className="text-sm text-gray-500 mt-1">Optional, but recommended for confirmations</p>
          </div>

          <div>
            <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-1">
              Phone Number *
            </label>
            <input
              type="tel"
              id="phone"
              name="phone"
              value={formData.phone}
              onChange={handlePhoneChange}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
              placeholder="(555) 123-4567"
              maxLength={14}
            />
            <p className="text-sm text-gray-500 mt-1">Required - We&apos;ll call to confirm your quote</p>
          </div>
        </div>

        {/* Event Details */}
        <div className="space-y-4 mb-6">
          <h3 className="text-lg font-semibold text-gray-700">Event Details</h3>
          
          <div>
            <label htmlFor="eventDate" className="block text-sm font-medium text-gray-700 mb-1">
              Preferred Event Date
            </label>
            <input
              type="date"
              id="eventDate"
              name="eventDate"
              value={formData.eventDate}
              onChange={handleChange}
              min={new Date().toISOString().split('T')[0]}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
            />
          </div>

          <div>
            <label htmlFor="guestCount" className="block text-sm font-medium text-gray-700 mb-1">
              Number of Guests *
            </label>
            <input
              type="number"
              id="guestCount"
              name="guestCount"
              value={formData.guestCount}
              onChange={handleChange}
              required
              min={1}
              max={500}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
            />
          </div>

          <div>
            <label htmlFor="budget" className="block text-sm font-medium text-gray-700 mb-1">
              Budget Range
            </label>
            <select
              id="budget"
              name="budget"
              value={formData.budget}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
            >
              <option value="">Select budget range...</option>
              {budgetOptions.map(option => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-1">
              Event Location / Zip Code
            </label>
            <input
              type="text"
              id="location"
              name="location"
              value={formData.location}
              onChange={handleChange}
              maxLength={200}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
              placeholder="City or Zip Code"
            />
          </div>

          <div>
            <label htmlFor="message" className="block text-sm font-medium text-gray-700 mb-1">
              Additional Details or Questions
            </label>
            <textarea
              id="message"
              name="message"
              value={formData.message}
              onChange={handleChange}
              rows={4}
              maxLength={2000}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent resize-none"
              placeholder="Tell us about your event, dietary restrictions, special requests, etc."
            />
          </div>
        </div>

        {/* Newsletter Auto-Subscribe Notice */}
        <div className="mb-6 p-3 bg-orange-50 border border-orange-200 rounded-lg">
          <p className="text-xs text-gray-700">
            📧 <strong>You&apos;ll automatically receive our newsletter</strong> with exclusive offers and hibachi tips.
            <br />
            <span className="text-gray-600">Don&apos;t want updates? Simply reply <strong>&quot;STOP&quot;</strong> anytime to unsubscribe.</span>
          </p>
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className={`
            w-full py-3 px-6 rounded-lg font-semibold text-white
            transition-all duration-200
            ${isSubmitting
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-red-600 hover:bg-red-700 active:bg-red-800'
            }
          `}
        >
          {isSubmitting ? 'Submitting...' : 'Get Your Free Quote'}
        </button>

        <p className="text-xs text-gray-500 text-center mt-4">
          * Required fields. We typically respond within 24 hours.
        </p>
      </div>
    </form>
  )
}
