'use client';

import { useState } from 'react';
import { Send, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { SITE_CONFIG } from '@/lib/seo-config';

interface FormData {
  name: string;
  email: string;
  phone: string;
  subject: string;
  message: string;
}

interface FormErrors {
  name?: string;
  email?: string;
  message?: string;
}

type FormStatus = 'idle' | 'submitting' | 'success' | 'error';

export default function ContactForm() {
  const [formData, setFormData] = useState<FormData>({
    name: '',
    email: '',
    phone: '',
    subject: 'General Inquiry',
    message: '',
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [status, setStatus] = useState<FormStatus>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (!formData.message.trim()) {
      newErrors.message = 'Message is required';
    } else if (formData.message.trim().length < 10) {
      newErrors.message = 'Message must be at least 10 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setStatus('submitting');
    setErrorMessage('');

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/v1/contact`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: formData.name,
          email: formData.email,
          phone: formData.phone || null,
          subject: formData.subject,
          message: formData.message,
          source: 'website_contact_form',
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to send message. Please try again.');
      }

      setStatus('success');
      setFormData({
        name: '',
        email: '',
        phone: '',
        subject: 'General Inquiry',
        message: '',
      });

      // Reset success message after 5 seconds
      setTimeout(() => {
        setStatus('idle');
      }, 5000);
    } catch (error) {
      setStatus('error');
      setErrorMessage(
        error instanceof Error ? error.message : 'An unexpected error occurred. Please try again.'
      );
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));

    // Clear error when user starts typing
    if (errors[name as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  };

  if (status === 'success') {
    return (
      <div className="rounded-2xl border border-green-200 bg-green-50 p-8 text-center">
        <CheckCircle className="mx-auto mb-4 h-16 w-16 text-green-500" />
        <h3 className="mb-2 text-xl font-bold text-green-800">Message Sent Successfully!</h3>
        <p className="text-green-700">
          Thank you for contacting us. We&apos;ll get back to you within 1-2 hours during business
          hours.
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {status === 'error' && (
        <div className="flex items-center gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
          <AlertCircle className="h-5 w-5 flex-shrink-0" />
          <p>{errorMessage}</p>
        </div>
      )}

      {/* Name Field */}
      <div>
        <label htmlFor="contact-name" className="mb-2 block text-sm font-medium text-gray-700">
          Your Name <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          id="contact-name"
          name="name"
          value={formData.name}
          onChange={handleChange}
          className={`w-full rounded-xl border-2 px-4 py-3 transition-colors focus:outline-none focus:ring-2 focus:ring-red-500/20 ${errors.name
              ? 'border-red-300 bg-red-50'
              : 'border-gray-200 bg-white focus:border-red-500'
            }`}
          placeholder="John Doe"
          aria-invalid={!!errors.name}
          aria-describedby={errors.name ? 'name-error' : undefined}
        />
        {errors.name && (
          <p id="name-error" className="mt-1 text-sm text-red-600">
            {errors.name}
          </p>
        )}
      </div>

      {/* Email Field */}
      <div>
        <label htmlFor="contact-email" className="mb-2 block text-sm font-medium text-gray-700">
          Email Address <span className="text-red-500">*</span>
        </label>
        <input
          type="email"
          id="contact-email"
          name="email"
          value={formData.email}
          onChange={handleChange}
          className={`w-full rounded-xl border-2 px-4 py-3 transition-colors focus:outline-none focus:ring-2 focus:ring-red-500/20 ${errors.email
              ? 'border-red-300 bg-red-50'
              : 'border-gray-200 bg-white focus:border-red-500'
            }`}
          placeholder="john@example.com"
          aria-invalid={!!errors.email}
          aria-describedby={errors.email ? 'email-error' : undefined}
        />
        {errors.email && (
          <p id="email-error" className="mt-1 text-sm text-red-600">
            {errors.email}
          </p>
        )}
      </div>

      {/* Phone Field (Optional) */}
      <div>
        <label htmlFor="contact-phone" className="mb-2 block text-sm font-medium text-gray-700">
          Phone Number <span className="text-gray-400">(optional)</span>
        </label>
        <input
          type="tel"
          id="contact-phone"
          name="phone"
          value={formData.phone}
          onChange={handleChange}
          className="w-full rounded-xl border-2 border-gray-200 bg-white px-4 py-3 transition-colors focus:border-red-500 focus:outline-none focus:ring-2 focus:ring-red-500/20"
          placeholder="(555) 123-4567"
        />
      </div>

      {/* Subject Field */}
      <div>
        <label htmlFor="contact-subject" className="mb-2 block text-sm font-medium text-gray-700">
          Subject
        </label>
        <select
          id="contact-subject"
          name="subject"
          value={formData.subject}
          onChange={handleChange}
          className="w-full rounded-xl border-2 border-gray-200 bg-white px-4 py-3 transition-colors focus:border-red-500 focus:outline-none focus:ring-2 focus:ring-red-500/20"
        >
          <option value="General Inquiry">General Inquiry</option>
          <option value="Booking Question">Booking Question</option>
          <option value="Pricing Information">Pricing Information</option>
          <option value="Event Planning">Event Planning</option>
          <option value="Feedback">Feedback</option>
          <option value="Other">Other</option>
        </select>
      </div>

      {/* Message Field */}
      <div>
        <label htmlFor="contact-message" className="mb-2 block text-sm font-medium text-gray-700">
          Your Message <span className="text-red-500">*</span>
        </label>
        <textarea
          id="contact-message"
          name="message"
          value={formData.message}
          onChange={handleChange}
          rows={5}
          className={`w-full resize-none rounded-xl border-2 px-4 py-3 transition-colors focus:outline-none focus:ring-2 focus:ring-red-500/20 ${errors.message
              ? 'border-red-300 bg-red-50'
              : 'border-gray-200 bg-white focus:border-red-500'
            }`}
          placeholder="Tell us about your event, questions, or how we can help..."
          aria-invalid={!!errors.message}
          aria-describedby={errors.message ? 'message-error' : undefined}
        />
        {errors.message && (
          <p id="message-error" className="mt-1 text-sm text-red-600">
            {errors.message}
          </p>
        )}
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={status === 'submitting'}
        className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-red-600 to-red-700 px-8 py-4 text-lg font-bold text-white shadow-lg transition-all hover:-translate-y-0.5 hover:from-red-700 hover:to-red-800 hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:translate-y-0"
      >
        {status === 'submitting' ? (
          <>
            <Loader2 className="h-5 w-5 animate-spin" />
            Sending...
          </>
        ) : (
          <>
            <Send className="h-5 w-5" />
            Send Message
          </>
        )}
      </button>

      <p className="text-center text-sm text-gray-500">
        We typically respond within 1-2 hours. For urgent inquiries, call{' '}
        <a href={`tel:${SITE_CONFIG.contact.phoneTel}`} className="font-medium text-red-600 hover:underline">
          {SITE_CONFIG.contact.phone}
        </a>
      </p>
    </form>
  );
}
