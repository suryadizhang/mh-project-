'use client'

import React, { useState } from 'react'

import { apiFetch } from '@/lib/api'
import { logger } from '@/lib/logger'

interface BookingFormProps {
  className?: string
}

interface BookingData {
  name: string
  email: string
  phone: string
  eventDate: string
  guestCount: number
  location: string
  specialRequests?: string
}

export default function BookingForm({ className = '' }: BookingFormProps) {
  const [formData, setFormData] = useState<BookingData>({
    name: '',
    email: '',
    phone: '',
    eventDate: '',
    guestCount: 1,
    location: '',
    specialRequests: ''
  })

  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      const result = await apiFetch('/api/v1/bookings', {
        method: 'POST',
        body: JSON.stringify(formData)
      })

      logger.info('Booking created')
    } catch (error) {
      logger.error('Error creating booking', error as Error)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className={`max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-md ${className}`}>
      <h2 className="text-2xl font-bold mb-6 text-gray-800">Book Your Hibachi Experience</h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
              Name *
            </label>
            <input
              type="text"
              id="name"
              required
              value={formData.name}
              onChange={e => setFormData(prev => ({ ...prev, name: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
              Email *
            </label>
            <input
              type="email"
              id="email"
              required
              value={formData.email}
              onChange={e => setFormData(prev => ({ ...prev, email: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div>
          <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-2">
            Phone *
          </label>
          <input
            type="tel"
            id="phone"
            required
            value={formData.phone}
            onChange={e => setFormData(prev => ({ ...prev, phone: e.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="eventDate" className="block text-sm font-medium text-gray-700 mb-2">
              Event Date *
            </label>
            <input
              type="date"
              id="eventDate"
              required
              value={formData.eventDate}
              onChange={e => setFormData(prev => ({ ...prev, eventDate: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="guestCount" className="block text-sm font-medium text-gray-700 mb-2">
              Guest Count *
            </label>
            <input
              type="number"
              id="guestCount"
              required
              min="1"
              max="50"
              value={formData.guestCount}
              onChange={e =>
                setFormData(prev => ({ ...prev, guestCount: parseInt(e.target.value) }))
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div>
          <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-2">
            Event Location *
          </label>
          <input
            type="text"
            id="location"
            required
            placeholder="Enter your event address"
            value={formData.location}
            onChange={e => setFormData(prev => ({ ...prev, location: e.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label htmlFor="specialRequests" className="block text-sm font-medium text-gray-700 mb-2">
            Special Requests
          </label>
          <textarea
            id="specialRequests"
            rows={4}
            placeholder="Any dietary restrictions, special occasions, or additional requests..."
            value={formData.specialRequests}
            onChange={e => setFormData(prev => ({ ...prev, specialRequests: e.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isSubmitting ? 'Submitting...' : 'Book My Hibachi Experience'}
        </button>
      </form>
    </div>
  )
}
