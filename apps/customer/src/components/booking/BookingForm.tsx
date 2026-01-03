'use client';

import React, { useState } from 'react';

import { apiFetch } from '@/lib/api';
import { logger } from '@/lib/logger';
import { FormErrorBoundary } from '@/components/ErrorBoundary';

interface BookingFormProps {
  className?: string;
}

interface BookingData {
  name: string;
  email: string;
  phone: string;
  eventDate: string;
  guestCount: number;
  location: string;
  specialRequests?: string;
}

function BookingFormComponent({ className = '' }: BookingFormProps) {
  const [formData, setFormData] = useState<BookingData>({
    name: '',
    email: '',
    phone: '',
    eventDate: '',
    guestCount: 1,
    location: '',
    specialRequests: '',
  });

  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      await apiFetch('/api/v1/bookings', {
        method: 'POST',
        body: JSON.stringify(formData),
      });

      logger.info('Booking created');
    } catch (error) {
      logger.error('Error creating booking', error as Error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className={`mx-auto max-w-2xl rounded-lg bg-white p-6 shadow-md ${className}`}>
      <h2 className="mb-6 text-2xl font-bold text-gray-800">Book Your Hibachi Experience</h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <label htmlFor="name" className="mb-2 block text-sm font-medium text-gray-700">
              Name *
            </label>
            <input
              type="text"
              id="name"
              required
              value={formData.name}
              onChange={(e) => setFormData((prev) => ({ ...prev, name: e.target.value }))}
              className="w-full rounded-md border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label htmlFor="email" className="mb-2 block text-sm font-medium text-gray-700">
              Email *
            </label>
            <input
              type="email"
              id="email"
              required
              value={formData.email}
              onChange={(e) => setFormData((prev) => ({ ...prev, email: e.target.value }))}
              className="w-full rounded-md border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>
        </div>

        <div>
          <label htmlFor="phone" className="mb-2 block text-sm font-medium text-gray-700">
            Phone *
          </label>
          <input
            type="tel"
            id="phone"
            required
            value={formData.phone}
            onChange={(e) => setFormData((prev) => ({ ...prev, phone: e.target.value }))}
            className="w-full rounded-md border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
          />
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <label htmlFor="eventDate" className="mb-2 block text-sm font-medium text-gray-700">
              Event Date *
            </label>
            <input
              type="date"
              id="eventDate"
              required
              value={formData.eventDate}
              onChange={(e) => setFormData((prev) => ({ ...prev, eventDate: e.target.value }))}
              className="w-full rounded-md border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label htmlFor="guestCount" className="mb-2 block text-sm font-medium text-gray-700">
              Guest Count *
            </label>
            <input
              type="number"
              id="guestCount"
              required
              min="1"
              max="50"
              value={formData.guestCount}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, guestCount: parseInt(e.target.value) }))
              }
              className="w-full rounded-md border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>
        </div>

        <div>
          <label htmlFor="location" className="mb-2 block text-sm font-medium text-gray-700">
            Event Location *
          </label>
          <input
            type="text"
            id="location"
            required
            placeholder="Enter your event address"
            value={formData.location}
            onChange={(e) => setFormData((prev) => ({ ...prev, location: e.target.value }))}
            className="w-full rounded-md border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
          />
        </div>

        <div>
          <label htmlFor="specialRequests" className="mb-2 block text-sm font-medium text-gray-700">
            Special Requests
          </label>
          <textarea
            id="specialRequests"
            rows={4}
            placeholder="Any dietary restrictions, special occasions, or additional requests..."
            value={formData.specialRequests}
            onChange={(e) => setFormData((prev) => ({ ...prev, specialRequests: e.target.value }))}
            className="w-full rounded-md border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
          />
        </div>

        {/* Health Notice */}
        <div className="rounded-lg border border-amber-300 bg-amber-50 p-4">
          <p className="text-sm text-amber-800">
            <span className="font-semibold">⚠️ Health Notice:</span> To protect all guests, please
            ensure that no one who has experienced vomiting, diarrhea, or fever within the past 48
            hours attends your event. Norovirus and other stomach bugs spread easily at gatherings.
            Questions about food safety? Contact us at{' '}
            <a href="mailto:cs@myhibachichef.com" className="font-medium underline">
              cs@myhibachichef.com
            </a>
          </p>
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full rounded-md bg-blue-600 px-4 py-3 text-white transition-colors hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isSubmitting ? 'Submitting...' : 'Book My Hibachi Experience'}
        </button>
      </form>
    </div>
  );
}

// Wrap component with error boundary
export default function BookingForm(props: BookingFormProps) {
  return (
    <FormErrorBoundary formName="BookingForm">
      <BookingFormComponent {...props} />
    </FormErrorBoundary>
  );
}
