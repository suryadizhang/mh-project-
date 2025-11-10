'use client';

import { AlertCircle, Check, Loader2,Mail, MessageSquare, Phone, X } from 'lucide-react';
import { useState } from 'react';

interface EscalationFormProps {
  conversationId: string;
  userName?: string | null;
  userPhone?: string | null;
  userEmail?: string | null;
  onClose: () => void;
  onSuccess?: () => void;
}

type EscalationMethod = 'phone' | 'email' | 'preferred_method';
type EscalationPriority = 'low' | 'medium' | 'high' | 'urgent';

interface EscalationRequest {
  conversation_id: string;
  customer_name: string;
  customer_phone: string;
  customer_email?: string;
  reason: string;
  preferred_method: EscalationMethod;
  priority: EscalationPriority;
  customer_consent: boolean;
  metadata: Record<string, unknown>;
}

export default function EscalationForm({
  conversationId,
  userName,
  userPhone,
  userEmail,
  onClose,
  onSuccess,
}: EscalationFormProps) {
  // Form state
  const [name, setName] = useState(userName || '');
  const [phone, setPhone] = useState(userPhone || '');
  const [email, setEmail] = useState(userEmail || '');
  const [reason, setReason] = useState('');
  const [preferredMethod, setPreferredMethod] = useState<EscalationMethod>('phone');
  const [consent, setConsent] = useState(false);

  // UI state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [step, setStep] = useState<'form' | 'confirmation'>('form');

  // Validation
  const [phoneError, setPhoneError] = useState<string | null>(null);
  const [emailError, setEmailError] = useState<string | null>(null);

  // Phone validation
  const validatePhone = (value: string): boolean => {
    const cleaned = value.replace(/\D/g, '');
    if (cleaned.length !== 10 && cleaned.length !== 11) {
      setPhoneError('Please enter a valid 10-digit phone number');
      return false;
    }
    setPhoneError(null);
    return true;
  };

  // Email validation
  const validateEmail = (value: string): boolean => {
    if (value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
      setEmailError('Please enter a valid email address');
      return false;
    }
    setEmailError(null);
    return true;
  };

  // Format phone number as user types
  const formatPhone = (value: string): string => {
    const cleaned = value.replace(/\D/g, '');
    if (cleaned.length <= 3) return cleaned;
    if (cleaned.length <= 6) return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3)}`;
    return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6, 10)}`;
  };

  const handlePhoneChange = (value: string) => {
    const formatted = formatPhone(value);
    setPhone(formatted);
    if (formatted.replace(/\D/g, '').length === 10) {
      validatePhone(formatted);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!name.trim()) {
      setError('Please enter your name');
      return;
    }

    if (!validatePhone(phone)) {
      return;
    }

    if (email && !validateEmail(email)) {
      return;
    }

    if (!reason.trim() || reason.trim().length < 10) {
      setError('Please provide a detailed reason (at least 10 characters)');
      return;
    }

    if (!consent) {
      setError('Please consent to being contacted');
      return;
    }

    setIsSubmitting(true);

    try {
      const escalationData: EscalationRequest = {
        conversation_id: conversationId,
        customer_name: name.trim(),
        customer_phone: `+1${phone.replace(/\D/g, '')}`, // Add US country code
        customer_email: email.trim() || undefined,
        reason: reason.trim(),
        preferred_method: preferredMethod,
        priority: 'medium' as EscalationPriority, // Default to medium, admin can adjust later
        customer_consent: consent,
        metadata: {
          source: 'chat_widget',
          timestamp: new Date().toISOString(),
          user_agent: typeof window !== 'undefined' ? window.navigator.userAgent : '',
        },
      };

      const response = await fetch('/api/v1/escalations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(escalationData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to submit escalation request');
      }

      await response.json(); // Consume response

      // Save user info for future use
      if (typeof window !== 'undefined') {
        localStorage.setItem('mh_user_name', name);
        localStorage.setItem('mh_user_phone', phone);
        if (email) localStorage.setItem('mh_user_email', email);
      }

      setSuccess(true);
      setStep('confirmation');

      // Auto-close after 3 seconds
      setTimeout(() => {
        onSuccess?.();
        onClose();
      }, 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Success confirmation screen
  if (step === 'confirmation' && success) {
    return (
      <div className="absolute inset-0 z-50 flex items-center justify-center rounded-2xl bg-black/50 p-4">
        <div className="relative w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
          <div className="text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
              <Check size={32} className="text-green-600" />
            </div>
            <h3 className="mb-2 text-xl font-semibold text-gray-900">Request Submitted!</h3>
            <p className="mb-4 text-sm text-gray-600">
              Our team will contact you{' '}
              {preferredMethod === 'phone'
                ? 'by phone'
                : preferredMethod === 'email'
                  ? 'by email'
                  : 'via your preferred method'}{' '}
              within the next few minutes.
            </p>
            <div className="rounded-lg bg-blue-50 p-4">
              <p className="text-sm font-medium text-blue-900">
                {preferredMethod === 'phone' && `We'll call you at ${phone}`}
                {preferredMethod === 'email' && `We'll email you at ${email}`}
                {preferredMethod === 'preferred_method' &&
                  "We'll reach out using your preferred contact method"}
              </p>
            </div>
            <p className="mt-4 text-xs text-gray-500">Closing automatically...</p>
          </div>
        </div>
      </div>
    );
  }

  // Main escalation form
  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center rounded-2xl bg-black/50 p-4">
      <div className="relative max-h-[90vh] w-full max-w-md overflow-y-auto rounded-xl bg-white shadow-xl">
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between border-b bg-white p-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Talk to a Human 👋</h3>
            <p className="text-xs text-gray-500">We&apos;ll connect you with our team</p>
          </div>
          <button
            onClick={onClose}
            className="flex items-center justify-center rounded-full p-1.5 transition-colors hover:bg-gray-100"
            aria-label="Close"
          >
            <X size={20} className="text-gray-500" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-5 p-6">
          {/* Error Alert */}
          {error && (
            <div className="flex items-start space-x-2 rounded-lg bg-red-50 p-3 text-sm text-red-800">
              <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Name */}
          <div>
            <label htmlFor="name" className="mb-1 block text-sm font-medium text-gray-700">
              Your Name <span className="text-red-500">*</span>
            </label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="John Doe"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
              required
            />
          </div>

          {/* Phone */}
          <div>
            <label htmlFor="phone" className="mb-1 block text-sm font-medium text-gray-700">
              Phone Number <span className="text-red-500">*</span>
            </label>
            <input
              id="phone"
              type="tel"
              value={phone}
              onChange={(e) => handlePhoneChange(e.target.value)}
              onBlur={() => validatePhone(phone)}
              placeholder="(916) 740-8768"
              className={`w-full rounded-lg border px-3 py-2 text-sm focus:ring-1 focus:outline-none ${
                phoneError
                  ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
                  : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'
              }`}
              required
            />
            {phoneError && <p className="mt-1 text-xs text-red-600">{phoneError}</p>}
          </div>

          {/* Email (Optional) */}
          <div>
            <label htmlFor="email" className="mb-1 block text-sm font-medium text-gray-700">
              Email <span className="text-xs text-gray-400">(Optional)</span>
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onBlur={() => validateEmail(email)}
              placeholder="john@example.com"
              className={`w-full rounded-lg border px-3 py-2 text-sm focus:ring-1 focus:outline-none ${
                emailError
                  ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
                  : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'
              }`}
            />
            {emailError && <p className="mt-1 text-xs text-red-600">{emailError}</p>}
          </div>

          {/* Preferred Contact Method */}
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              How should we contact you? <span className="text-red-500">*</span>
            </label>
            <div className="space-y-2">
              <label className="flex cursor-pointer items-center space-x-3 rounded-lg border border-gray-200 p-3 transition-colors hover:bg-gray-50">
                <input
                  type="radio"
                  name="method"
                  value="phone"
                  checked={preferredMethod === 'phone'}
                  onChange={(e) => setPreferredMethod(e.target.value as EscalationMethod)}
                  className="h-4 w-4 text-blue-600"
                />
                <Phone size={18} className="text-gray-500" />
                <span className="text-sm font-medium text-gray-700">Phone Call</span>
              </label>

              {email && (
                <label className="flex cursor-pointer items-center space-x-3 rounded-lg border border-gray-200 p-3 transition-colors hover:bg-gray-50">
                  <input
                    type="radio"
                    name="method"
                    value="email"
                    checked={preferredMethod === 'email'}
                    onChange={(e) => setPreferredMethod(e.target.value as EscalationMethod)}
                    className="h-4 w-4 text-blue-600"
                  />
                  <Mail size={18} className="text-gray-500" />
                  <span className="text-sm font-medium text-gray-700">Email</span>
                </label>
              )}

              <label className="flex cursor-pointer items-center space-x-3 rounded-lg border border-gray-200 p-3 transition-colors hover:bg-gray-50">
                <input
                  type="radio"
                  name="method"
                  value="preferred_method"
                  checked={preferredMethod === 'preferred_method'}
                  onChange={(e) => setPreferredMethod(e.target.value as EscalationMethod)}
                  className="h-4 w-4 text-blue-600"
                />
                <MessageSquare size={18} className="text-gray-500" />
                <span className="text-sm font-medium text-gray-700">Agent&apos;s Choice</span>
              </label>
            </div>
          </div>

          {/* Reason */}
          <div>
            <label htmlFor="reason" className="mb-1 block text-sm font-medium text-gray-700">
              How can we help? <span className="text-red-500">*</span>
            </label>
            <textarea
              id="reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Please describe your question or concern in detail..."
              rows={4}
              className="w-full resize-none rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
              required
              minLength={10}
            />
            <p className="mt-1 text-xs text-gray-500">{reason.length}/10 characters minimum</p>
          </div>

          {/* Priority (Hidden for better UX, defaults to medium) */}
          {/* We'll let backend/admin adjust priority later if needed */}

          {/* Consent Checkbox */}
          <div className="rounded-lg bg-gray-50 p-4">
            <label className="flex cursor-pointer items-start space-x-3">
              <input
                type="checkbox"
                checked={consent}
                onChange={(e) => setConsent(e.target.checked)}
                className="mt-0.5 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                required
              />
              <span className="text-xs text-gray-600">
                I consent to MyHibachi contacting me at the phone number and/or email provided
                above. I understand that our team will reach out to assist with my request.{' '}
                <span className="text-red-500">*</span>
              </span>
            </label>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isSubmitting || !consent}
            className="flex w-full items-center justify-center space-x-2 rounded-lg bg-gradient-to-r from-orange-500 to-red-500 px-4 py-3 text-sm font-medium text-white transition-all hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isSubmitting ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                <span>Submitting...</span>
              </>
            ) : (
              <>
                <MessageSquare size={18} />
                <span>Connect Me with a Human</span>
              </>
            )}
          </button>

          {/* Help Text */}
          <p className="text-center text-xs text-gray-500">
            Our team typically responds within 2-3 minutes during business hours
          </p>
        </form>
      </div>
    </div>
  );
}
