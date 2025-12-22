'use client';

import { X } from 'lucide-react';
import React, { useState } from 'react';

import { apiFetch } from '@/lib/api';
import { logger } from '@/lib/logger';

interface ExitIntentPopupProps {
  isVisible: boolean;
  onClose: () => void;
}

interface FormData {
  email: string;
  phone: string;
  name: string;
  emailConsent: boolean;
  smsConsent: boolean;
}

/**
 * Exit-Intent Popup for Lead Capture
 *
 * Triggers when user's mouse leaves the viewport (intent to exit).
 * Offers value proposition and newsletter signup with TCPA compliance.
 *
 * Features:
 * - Delayed display (waits for exit intent)
 * - Session-based (shows once per session)
 * - TCPA/CAN-SPAM compliant consent checkboxes
 * - Email or phone capture (at least one required)
 * - Mobile-responsive
 */
export default function ExitIntentPopup({ isVisible, onClose }: ExitIntentPopupProps) {
  const [formData, setFormData] = useState<FormData>({
    email: '',
    phone: '',
    name: '',
    emailConsent: false,
    smsConsent: false,
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;

    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  // Format phone number as user types
  const formatPhoneForDisplay = (value: string): string => {
    const digits = value.replace(/\D/g, '');

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

    // Validate: At least email or phone required
    if (!formData.email && !formData.phone) {
      setError('Please provide your email or phone number');
      setIsSubmitting(false);
      return;
    }

    // Validate: At least one consent required
    if (!formData.emailConsent && !formData.smsConsent) {
      setError('Please select at least one communication preference');
      setIsSubmitting(false);
      return;
    }

    // Validate phone format if provided
    if (formData.phone && formData.phone.replace(/\D/g, '').length < 10) {
      setError('Please enter a valid phone number');
      setIsSubmitting(false);
      return;
    }

    // Validate email format if provided
    if (formData.email && !formData.email.includes('@')) {
      setError('Please enter a valid email address');
      setIsSubmitting(false);
      return;
    }

    try {
      // Call public lead capture endpoint
      const response = await apiFetch('/api/v1/public/leads', {
        method: 'POST',
        body: JSON.stringify({
          name: formData.name || 'Newsletter Subscriber',
          phone: formData.phone || undefined,
          email: formData.email || undefined,
          source: 'exit_intent',
          sms_consent: formData.smsConsent,
          email_consent: formData.emailConsent,
          consent_text: formData.smsConsent
            ? 'I consent to receive SMS messages from my Hibachi LLC including: booking confirmations, event reminders, chef notifications, booking updates, customer support responses, and promotional offers. Message frequency varies. Message and data rates may apply. Reply STOP to opt out, HELP for assistance. View SMS Terms at https://myhibachichef.com/terms#sms and Privacy Policy at https://myhibachichef.com/privacy.'
            : undefined,
        }),
      });

      if (response.success) {
        logger.info('Exit intent lead captured successfully');
        setSubmitted(true);

        // Auto-close after 2 seconds
        setTimeout(() => {
          onClose();
        }, 2000);
      } else {
        throw new Error(response.message || 'Failed to subscribe');
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to subscribe. Please try again.';
      setError(errorMessage);
      logger.error('Exit intent subscription failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isVisible) return null;

  return (
    <div
      className="bg-opacity-50 fixed inset-0 z-50 flex items-center justify-center bg-black p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative max-h-[90vh] w-full max-w-md overflow-y-auto rounded-2xl bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 transition-colors hover:text-gray-600"
          aria-label="Close"
        >
          <X className="h-6 w-6" />
        </button>

        {/* Success State */}
        {submitted ? (
          <div className="p-8 text-center">
            <div className="mb-4">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
                <svg
                  className="h-8 w-8 text-green-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
            </div>
            <h3 className="mb-2 text-2xl font-bold text-gray-900">You&apos;re All Set! 🎉</h3>
            <p className="text-gray-600">
              Thanks for subscribing! Get ready for exclusive hibachi deals and tips.
            </p>
          </div>
        ) : (
          <>
            {/* Header */}
            <div className="rounded-t-2xl bg-gradient-to-r from-red-600 to-orange-500 p-6 text-white">
              <h2 className="mb-2 text-2xl font-bold">Wait! Don&apos;t Miss Out! 🍤</h2>
              <p className="text-sm opacity-90">
                Join our VIP list for exclusive hibachi deals, cooking tips, and event specials!
              </p>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4 p-6">
              {error && (
                <div className="rounded-lg border border-red-200 bg-red-50 p-3">
                  <p className="text-sm text-red-600">{error}</p>
                </div>
              )}

              {/* Benefits */}
              <div className="space-y-2 rounded-lg border border-orange-200 bg-orange-50 p-4">
                <p className="text-sm font-semibold text-gray-900">What You&apos;ll Get:</p>
                <ul className="space-y-1 text-sm text-gray-700">
                  <li className="flex items-start">
                    <span className="mr-2 text-orange-600">✓</span>
                    <span>10% off your first booking</span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-2 text-orange-600">✓</span>
                    <span>Early access to holiday specials</span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-2 text-orange-600">✓</span>
                    <span>Exclusive hibachi recipes & tips</span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-2 text-orange-600">✓</span>
                    <span>Priority booking during peak seasons</span>
                  </li>
                </ul>
              </div>

              {/* Name (Optional) */}
              <div>
                <label
                  htmlFor="popup-name"
                  className="mb-1 block text-sm font-medium text-gray-700"
                >
                  Name (Optional)
                </label>
                <input
                  type="text"
                  id="popup-name"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-transparent focus:ring-2 focus:ring-red-500"
                  placeholder="John Doe"
                />
              </div>

              {/* Email */}
              <div>
                <label
                  htmlFor="popup-email"
                  className="mb-1 block text-sm font-medium text-gray-700"
                >
                  Email Address
                </label>
                <input
                  type="email"
                  id="popup-email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-transparent focus:ring-2 focus:ring-red-500"
                  placeholder="you@example.com"
                />
              </div>

              {/* Phone */}
              <div>
                <label
                  htmlFor="popup-phone"
                  className="mb-1 block text-sm font-medium text-gray-700"
                >
                  Phone Number
                </label>
                <input
                  type="tel"
                  id="popup-phone"
                  name="phone"
                  value={formData.phone}
                  onChange={handlePhoneChange}
                  maxLength={14}
                  className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-transparent focus:ring-2 focus:ring-red-500"
                  placeholder="(555) 123-4567"
                />
              </div>

              {/* Consent Checkboxes */}
              <div className="space-y-3">
                <p className="text-sm font-medium text-gray-700">Communication Preferences:</p>

                {/* Email Consent */}
                <div className="flex items-start">
                  <input
                    type="checkbox"
                    id="popup-emailConsent"
                    name="emailConsent"
                    checked={formData.emailConsent}
                    onChange={handleChange}
                    className="mt-1 h-4 w-4 rounded border-gray-300 text-red-600 focus:ring-red-500"
                  />
                  <label htmlFor="popup-emailConsent" className="ml-3 text-sm text-gray-700">
                    Send me emails with hibachi tips and special offers
                  </label>
                </div>

                {/* SMS Consent */}
                <div className="flex items-start">
                  <input
                    type="checkbox"
                    id="popup-smsConsent"
                    name="smsConsent"
                    checked={formData.smsConsent}
                    onChange={handleChange}
                    className="mt-1 h-4 w-4 rounded border-gray-300 text-red-600 focus:ring-red-500"
                  />
                  <label htmlFor="popup-smsConsent" className="ml-3 text-sm text-gray-700">
                    I consent to receive SMS messages (booking confirmations, reminders, promotions)
                    <span className="mt-1 block text-xs text-gray-500">
                      Message frequency varies. Rates may apply. Reply STOP to opt out, HELP for
                      help.
                      <a
                        href="/terms#sms"
                        target="_blank"
                        className="ml-1 text-blue-600 hover:underline"
                      >
                        SMS Terms
                      </a>
                    </span>
                  </label>
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isSubmitting}
                className={`w-full rounded-lg px-6 py-3 font-semibold text-white transition-all duration-200 ${
                  isSubmitting
                    ? 'cursor-not-allowed bg-gray-400'
                    : 'bg-gradient-to-r from-red-600 to-orange-500 hover:from-red-700 hover:to-orange-600'
                } `}
              >
                {isSubmitting ? 'Subscribing...' : 'Get My VIP Access'}
              </button>

              {/* Privacy Notice */}
              <p className="text-center text-xs text-gray-500">
                We respect your privacy. Unsubscribe anytime.{' '}
                <a href="/privacy" target="_blank" className="text-blue-600 hover:underline">
                  Privacy Policy
                </a>
              </p>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
