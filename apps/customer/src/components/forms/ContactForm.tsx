import React, { useState } from 'react'

import { apiFetch } from '@/lib/api'
import { logger } from '@/lib/logger'

interface ContactFormData {
  name: string
  email: string
  phone: string
  message: string
  emailConsent: boolean
}

interface ContactFormProps {
  className?: string
  onSuccess?: () => void
}

export function ContactForm({ className = '', onSuccess }: ContactFormProps) {
  const [formData, setFormData] = useState<ContactFormData>({
    name: '',
    email: '',
    phone: '',
    message: '',
    emailConsent: true,
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value, type } = e.target
    const checked = (e.target as HTMLInputElement).checked

    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)

    try {
      const response = await apiFetch('/api/v1/public/leads', {
        method: 'POST',
        body: JSON.stringify({
          name: formData.name,
          email: formData.email || undefined,
          phone: formData.phone || undefined,
          message: formData.message || undefined,
          email_consent: formData.emailConsent,
          sms_consent: false,
          source: 'contact',
        }),
      })

      if (response && typeof response === 'object' && 'success' in response) {
        setSubmitted(true)
        logger.info('Contact form submitted successfully')

        // Call onSuccess callback if provided
        if (onSuccess) {
          onSuccess()
        }

        // Reset form after 3 seconds
        setTimeout(() => {
          setSubmitted(false)
          setFormData({
            name: '',
            email: '',
            phone: '',
            message: '',
            emailConsent: true,
          })
        }, 3000)
      }
    } catch (err) {
      logger.error('Failed to submit contact form')
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to submit form. Please try again.'
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  if (submitted) {
    return (
      <div className={`p-8 text-center ${className}`}>
        <div className="inline-flex h-16 w-16 items-center justify-center rounded-full bg-green-100 mb-4">
          <svg
            className="h-10 w-10 text-green-600"
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
        <h3 className="text-2xl font-bold text-gray-900 mb-2">
          Thank You!
        </h3>
        <p className="text-gray-600">
          We&apos;ve received your message and will get back to you shortly.
        </p>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className={`space-y-6 ${className}`}>
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Get in Touch</h2>
        <p className="text-gray-600">
          Have a question? Send us a message and we&apos;ll respond as soon as possible.
        </p>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                Error submitting form
              </h3>
              <div className="mt-2 text-sm text-red-700">{error}</div>
            </div>
          </div>
        </div>
      )}

      {/* Name */}
      <div>
        <label
          htmlFor="name"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Name <span className="text-red-500">*</span>
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
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500 focus:border-transparent"
          placeholder="Your name"
        />
      </div>

      {/* Email */}
      <div>
        <label
          htmlFor="email"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Email <span className="text-red-500">*</span>
        </label>
        <input
          type="email"
          id="email"
          name="email"
          value={formData.email}
          onChange={handleChange}
          required
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500 focus:border-transparent"
          placeholder="you@example.com"
        />
      </div>

      {/* Phone (Optional) */}
      <div>
        <label
          htmlFor="phone"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Phone <span className="text-gray-400 text-xs">(Optional)</span>
        </label>
        <input
          type="tel"
          id="phone"
          name="phone"
          value={formData.phone}
          onChange={handleChange}
          pattern="[0-9]{10,15}"
          minLength={10}
          maxLength={15}
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500 focus:border-transparent"
          placeholder="5551234567"
        />
        <p className="mt-1 text-xs text-gray-500">10-15 digits, no spaces or dashes</p>
      </div>

      {/* Message */}
      <div>
        <label
          htmlFor="message"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Message <span className="text-red-500">*</span>
        </label>
        <textarea
          id="message"
          name="message"
          value={formData.message}
          onChange={handleChange}
          required
          minLength={10}
          maxLength={2000}
          rows={5}
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500 focus:border-transparent resize-y"
          placeholder="How can we help you?"
        />
        <p className="mt-1 text-xs text-gray-500">
          {formData.message.length}/2000 characters
        </p>
      </div>

      {/* Email Consent */}
      <div className="flex items-start">
        <input
          type="checkbox"
          id="emailConsent"
          name="emailConsent"
          checked={formData.emailConsent}
          onChange={handleChange}
          className="mt-1 h-4 w-4 text-red-600 border-gray-300 rounded focus:ring-red-500"
        />
        <label htmlFor="emailConsent" className="ml-2 text-sm text-gray-700">
          I agree to receive email communications from MyHibachi
        </label>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isSubmitting}
        className={`
          w-full py-3 px-6 rounded-md text-white font-semibold text-lg
          transition-colors duration-200
          ${
            isSubmitting
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-red-600 hover:bg-red-700'
          }
        `}
      >
        {isSubmitting ? 'Sending...' : 'Send Message'}
      </button>

      <p className="text-xs text-gray-500 text-center">
        By submitting this form, you agree to our privacy policy.
      </p>
    </form>
  )
}
