'use client';

import React, { useState } from 'react';

import { apiFetch } from '@/lib/api';
import { logger } from '@/lib/logger';

interface QuoteFormData {
  name: string;
  email: string;
  phone: string;
  eventDate: string;
  guestCount: number;
  budget: string;
  location: string;
  message: string;
  smsConsent: boolean;
  emailConsent: boolean;
}

interface QuoteRequestFormProps {
  className?: string;
  onSuccess?: () => void;
}

const budgetOptions = [
  'Under $500',
  '$500 - $1,000',
  '$1,000 - $2,000',
  '$2,000 - $5,000',
  'Over $5,000',
  'Not sure / Need help',
];

export function QuoteRequestForm({ className = '', onSuccess }: QuoteRequestFormProps) {
  const [formData, setFormData] = useState<QuoteFormData>({
    name: '',
    email: '',
    phone: '',
    eventDate: '',
    guestCount: 1,
    budget: '',
    location: '',
    message: '',
    smsConsent: false,
    emailConsent: false,
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>,
  ) => {
    const { name, value, type } = e.target;

    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
    }));
  };

  // Format phone number as user types
  const formatPhoneForDisplay = (value: string): string => {
    // Remove all non-digit characters
    const digits = value.replace(/\D/g, '');

    // Format as (XXX) XXX-XXXX
    if (digits.length <= 3) {
      return digits;
    } else if (digits.length <= 6) {
      return `(${digits.slice(0, 3)}) ${digits.slice(3)}`;
    } else {
      return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6, 10)}`;
    }
  };

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatPhoneForDisplay(e.target.value);
    setFormData((prev) => ({ ...prev, phone: formatted }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    // Validate required fields
    if (!formData.name || formData.name.trim().length < 2) {
      setError('Please enter your full name');
      setIsSubmitting(false);
      return;
    }

    if (!formData.phone || formData.phone.replace(/\D/g, '').length < 10) {
      setError('Please enter a valid phone number with at least 10 digits');
      setIsSubmitting(false);
      return;
    }

    try {
      // Call public lead capture endpoint (no auth required)
      const response = await apiFetch('/api/v1/public/leads', {
        method: 'POST',
        body: JSON.stringify({
          name: formData.name,
          phone: formData.phone, // Now required
          email: formData.email || undefined,
          event_date: formData.eventDate || undefined,
          guest_count: formData.guestCount || undefined,
          budget: formData.budget || undefined,
          location: formData.location || undefined,
          message: formData.message || undefined,
          source: 'quote',
          sms_consent: formData.smsConsent,
          email_consent: formData.emailConsent,
          consent_text: formData.smsConsent
            ? 'By providing your phone number and checking this box, you consent to receive SMS messages from my Hibachi LLC. Message frequency varies based on your bookings. Message and data rates may apply. Reply STOP to opt out, HELP for assistance.'
            : undefined,
        }),
      });

      if (response.success) {
        logger.info('Quote request submitted successfully');

        setSubmitted(true);

        if (onSuccess) {
          onSuccess();
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
            message: '',
            smsConsent: false,
            emailConsent: false,
          });
          setSubmitted(false);
        }, 3000);
      } else {
        throw new Error(response.message || 'Failed to submit quote request');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to submit quote request';
      setError(errorMessage);
      logger.error('Quote request submission failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div
        className={`rounded-lg border border-green-200 bg-green-50 p-8 text-center ${className}`}
      >
        <div className="mb-4 text-green-600">
          <svg className="mx-auto h-16 w-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h3 className="mb-2 text-2xl font-bold text-gray-900">Thank You!</h3>
        <p className="text-gray-600">
          We&apos;ve received your quote request and will contact you shortly with a personalized
          quote.
        </p>
        <p className="mt-4 text-sm text-gray-500">Expected response time: Within 24 hours</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className={`space-y-6 ${className}`}>
      <div className="rounded-lg bg-white p-6 shadow-md">
        <h2 className="mb-6 text-2xl font-bold text-gray-900">Get Your Free Quote</h2>

        {error && (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4">
            <p className="text-red-600">{error}</p>
          </div>
        )}

        {/* Contact Information */}
        <div className="mb-6 space-y-4">
          <h3 className="text-lg font-semibold text-gray-700">Contact Information</h3>

          <div>
            <label htmlFor="name" className="mb-1 block text-sm font-medium text-gray-700">
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
              className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-transparent focus:ring-2 focus:ring-red-500"
              placeholder="John Doe"
            />
          </div>

          <div>
            <label htmlFor="email" className="mb-1 block text-sm font-medium text-gray-700">
              Email Address
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-transparent focus:ring-2 focus:ring-red-500"
              placeholder="john@example.com"
            />
            <p className="mt-1 text-sm text-gray-500">
              Optional, but recommended for confirmations
            </p>
          </div>

          <div>
            <label htmlFor="phone" className="mb-1 block text-sm font-medium text-gray-700">
              Phone Number *
            </label>
            <input
              type="tel"
              id="phone"
              name="phone"
              value={formData.phone}
              onChange={handlePhoneChange}
              required
              className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-transparent focus:ring-2 focus:ring-red-500"
              placeholder="(555) 123-4567"
              maxLength={14}
            />
            <p className="mt-1 text-sm text-gray-500">
              Required - We&apos;ll call to confirm your quote
            </p>
          </div>
        </div>

        {/* Event Details */}
        <div className="mb-6 space-y-4">
          <h3 className="text-lg font-semibold text-gray-700">Event Details</h3>

          <div>
            <label htmlFor="eventDate" className="mb-1 block text-sm font-medium text-gray-700">
              Preferred Event Date
            </label>
            <input
              type="date"
              id="eventDate"
              name="eventDate"
              value={formData.eventDate}
              onChange={handleChange}
              min={new Date().toISOString().split('T')[0]}
              className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-transparent focus:ring-2 focus:ring-red-500"
            />
          </div>

          <div>
            <label htmlFor="guestCount" className="mb-1 block text-sm font-medium text-gray-700">
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
              className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-transparent focus:ring-2 focus:ring-red-500"
            />
          </div>

          <div>
            <label htmlFor="budget" className="mb-1 block text-sm font-medium text-gray-700">
              Budget Range
            </label>
            <select
              id="budget"
              name="budget"
              value={formData.budget}
              onChange={handleChange}
              className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-transparent focus:ring-2 focus:ring-red-500"
            >
              <option value="">Select budget range...</option>
              {budgetOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="location" className="mb-1 block text-sm font-medium text-gray-700">
              Event Location / Zip Code
            </label>
            <input
              type="text"
              id="location"
              name="location"
              value={formData.location}
              onChange={handleChange}
              maxLength={200}
              className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-transparent focus:ring-2 focus:ring-red-500"
              placeholder="City or Zip Code"
            />
          </div>

          <div>
            <label htmlFor="message" className="mb-1 block text-sm font-medium text-gray-700">
              Additional Details or Questions
            </label>
            <textarea
              id="message"
              name="message"
              value={formData.message}
              onChange={handleChange}
              rows={4}
              maxLength={2000}
              className="w-full resize-none rounded-lg border border-gray-300 px-4 py-2 focus:border-transparent focus:ring-2 focus:ring-red-500"
              placeholder="Tell us about your event, dietary restrictions, special requests, etc."
            />
          </div>
        </div>

        {/* TCPA Consent Checkboxes */}
        <div className="mb-6 space-y-4">
          <h3 className="text-lg font-semibold text-gray-700">Communication Preferences</h3>

          {/* SMS Consent */}
          <div className="flex items-start">
            <input
              type="checkbox"
              id="smsConsent"
              name="smsConsent"
              checked={formData.smsConsent}
              onChange={handleChange}
              className="mt-1 h-4 w-4 rounded border-gray-300 text-red-600 focus:ring-red-500"
            />
            <label htmlFor="smsConsent" className="ml-3 text-sm text-gray-700">
              <strong>I consent to receive text messages from My Hibachi Chef</strong>
              <span className="mt-1 block text-xs text-gray-600">
                I agree to receive the following types of SMS messages: booking confirmations, event
                reminders, chef notifications, booking updates, customer support responses, and
                promotional offers. Message frequency varies. Message and data rates may apply.
                Reply <strong>STOP</strong> to opt out, <strong>HELP</strong> for assistance. View
                our{' '}
                <a href="/terms#sms" target="_blank" className="text-blue-600 hover:underline">
                  SMS Terms
                </a>{' '}
                and{' '}
                <a href="/privacy" target="_blank" className="text-blue-600 hover:underline">
                  Privacy Policy
                </a>
                .
              </span>
            </label>
          </div>

          {/* Email Consent */}
          <div className="flex items-start">
            <input
              type="checkbox"
              id="emailConsent"
              name="emailConsent"
              checked={formData.emailConsent}
              onChange={handleChange}
              className="mt-1 h-4 w-4 rounded border-gray-300 text-red-600 focus:ring-red-500"
            />
            <label htmlFor="emailConsent" className="ml-3 text-sm text-gray-700">
              <strong>Yes, send me email updates</strong> about hibachi tips, recipes, and special
              promotions.
              <span className="mt-1 block text-xs text-gray-600">
                You can unsubscribe anytime by clicking the unsubscribe link in any email.
              </span>
            </label>
          </div>

          {/* Privacy Notice */}
          <div className="rounded-lg border border-blue-200 bg-blue-50 p-3">
            <p className="text-xs text-gray-700">
              🔒 Your privacy matters. We never sell your information.{' '}
              <a
                href="/privacy"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 underline hover:text-blue-800"
              >
                Privacy Policy
              </a>
              {' | '}
              <a
                href="/terms"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 underline hover:text-blue-800"
              >
                Terms & Conditions
              </a>
            </p>
          </div>
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className={`w-full rounded-lg px-6 py-3 font-semibold text-white transition-all duration-200 ${
            isSubmitting
              ? 'cursor-not-allowed bg-gray-400'
              : 'bg-red-600 hover:bg-red-700 active:bg-red-800'
          } `}
        >
          {isSubmitting ? 'Submitting...' : 'Get Your Free Quote'}
        </button>

        <p className="mt-4 text-center text-xs text-gray-500">
          * Required fields. We typically respond within 24 hours.
        </p>
      </div>
    </form>
  );
}
