/**
 * Alternative Payer Component
 * 
 * Allows customers to specify if someone else (friend/family) will make the payment.
 * This helps with payment matching when the payer name/email doesn't match booking.
 * 
 * Usage in payment page:
 * ```tsx
 * const [alternativePayer, setAlternativePayer] = useState<AlternativePayerData | null>(null);
 * 
 * <AlternativePayerField 
 *   value={alternativePayer}
 *   onChange={setAlternativePayer}
 * />
 * ```
 */

'use client';

import { useState } from 'react';
import { Users, X, ChevronDown, ChevronUp } from 'lucide-react';

export interface AlternativePayerData {
  name: string;
  email?: string;
  phone?: string;
  venmoUsername?: string;
  zelleEmail?: string;
  zellePhone?: string;
  relationship?: string; // e.g., "friend", "family", "spouse", "parent"
}

interface AlternativePayerFieldProps {
  value: AlternativePayerData | null;
  onChange: (data: AlternativePayerData | null) => void;
  className?: string;
}

export default function AlternativePayerField({
  value,
  onChange,
  className = '',
}: AlternativePayerFieldProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [hasAlternativePayer, setHasAlternativePayer] = useState(!!value);

  const handleToggle = (enabled: boolean) => {
    setHasAlternativePayer(enabled);
    if (!enabled) {
      onChange(null);
      setIsExpanded(false);
    } else {
      setIsExpanded(true);
      onChange({
        name: '',
        email: '',
        phone: '',
        venmoUsername: '',
        relationship: '',
      });
    }
  };

  const handleFieldChange = (field: keyof AlternativePayerData, fieldValue: string) => {
    if (!value) return;
    onChange({
      ...value,
      [field]: fieldValue,
    });
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Toggle Section */}
      <div className="rounded-lg border-2 border-gray-200 bg-gray-50 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100">
              <Users className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Someone else paying for you?</h3>
              <p className="text-sm text-gray-600">
                Let us know if a friend or family member will send the payment
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => handleToggle(!hasAlternativePayer)}
            className={`
              relative inline-flex h-6 w-11 items-center rounded-full transition-colors
              ${hasAlternativePayer ? 'bg-blue-600' : 'bg-gray-300'}
            `}
          >
            <span
              className={`
                inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                ${hasAlternativePayer ? 'translate-x-6' : 'translate-x-1'}
              `}
            />
          </button>
        </div>

        {hasAlternativePayer && (
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="mt-3 flex w-full items-center justify-between text-sm font-medium text-blue-600 hover:text-blue-700"
          >
            <span>{isExpanded ? 'Hide Details' : 'Show Details'}</span>
            {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
        )}
      </div>

      {/* Expanded Form */}
      {hasAlternativePayer && isExpanded && value && (
        <div className="space-y-4 rounded-lg border-2 border-blue-200 bg-blue-50 p-6">
          <div className="mb-4 flex items-start gap-2">
            <div className="rounded-md bg-blue-100 p-2">
              <Users className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <h4 className="font-semibold text-gray-900">Alternative Payer Information</h4>
              <p className="text-sm text-gray-600">
                This helps us match the payment correctly. Provide as much info as possible.
              </p>
            </div>
          </div>

          {/* Name (Required) */}
          <div>
            <label htmlFor="alt-payer-name" className="mb-1 block text-sm font-medium text-gray-700">
              Full Name <span className="text-red-500">*</span>
            </label>
            <input
              id="alt-payer-name"
              type="text"
              value={value.name}
              onChange={(e) => handleFieldChange('name', e.target.value)}
              placeholder="John Doe"
              className="w-full rounded-lg border-2 border-gray-300 px-4 py-2 focus:border-blue-500 focus:outline-none"
              required
            />
          </div>

          {/* Relationship */}
          <div>
            <label htmlFor="alt-payer-relationship" className="mb-1 block text-sm font-medium text-gray-700">
              Relationship to You
            </label>
            <select
              id="alt-payer-relationship"
              value={value.relationship || ''}
              onChange={(e) => handleFieldChange('relationship', e.target.value)}
              className="w-full rounded-lg border-2 border-gray-300 px-4 py-2 focus:border-blue-500 focus:outline-none"
            >
              <option value="">Select...</option>
              <option value="friend">Friend</option>
              <option value="family">Family Member</option>
              <option value="spouse">Spouse/Partner</option>
              <option value="parent">Parent</option>
              <option value="sibling">Sibling</option>
              <option value="colleague">Colleague</option>
              <option value="other">Other</option>
            </select>
          </div>

          {/* Phone (Recommended for matching) */}
          <div>
            <label htmlFor="alt-payer-phone" className="mb-1 block text-sm font-medium text-gray-700">
              Phone Number <span className="text-blue-600">(Recommended)</span>
            </label>
            <input
              id="alt-payer-phone"
              type="tel"
              value={value.phone || ''}
              onChange={(e) => handleFieldChange('phone', e.target.value)}
              placeholder="+1 (234) 567-8900"
              className="w-full rounded-lg border-2 border-gray-300 px-4 py-2 focus:border-blue-500 focus:outline-none"
            />
            <p className="mt-1 text-xs text-gray-600">
              Helps us match Zelle/Venmo payments that include phone numbers
            </p>
          </div>

          {/* Email (Optional) */}
          <div>
            <label htmlFor="alt-payer-email" className="mb-1 block text-sm font-medium text-gray-700">
              Email Address <span className="text-gray-500">(Optional)</span>
            </label>
            <input
              id="alt-payer-email"
              type="email"
              value={value.email || ''}
              onChange={(e) => handleFieldChange('email', e.target.value)}
              placeholder="john@example.com"
              className="w-full rounded-lg border-2 border-gray-300 px-4 py-2 focus:border-blue-500 focus:outline-none"
            />
          </div>

          {/* Venmo Username (Optional) */}
          <div>
            <label htmlFor="alt-payer-venmo" className="mb-1 block text-sm font-medium text-gray-700">
              Venmo Username <span className="text-gray-500">(Optional)</span>
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">@</span>
              <input
                id="alt-payer-venmo"
                type="text"
                value={value.venmoUsername || ''}
                onChange={(e) => handleFieldChange('venmoUsername', e.target.value)}
                placeholder="johndoe"
                className="w-full rounded-lg border-2 border-gray-300 py-2 pl-8 pr-4 focus:border-blue-500 focus:outline-none"
              />
            </div>
            <p className="mt-1 text-xs text-gray-600">
              If paying via Venmo, provide their username for faster matching
            </p>
          </div>

          {/* Zelle Email/Phone */}
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label htmlFor="alt-payer-zelle-email" className="mb-1 block text-sm font-medium text-gray-700">
                Zelle Email <span className="text-gray-500">(Optional)</span>
              </label>
              <input
                id="alt-payer-zelle-email"
                type="email"
                value={value.zelleEmail || ''}
                onChange={(e) => handleFieldChange('zelleEmail', e.target.value)}
                placeholder="john@example.com"
                className="w-full rounded-lg border-2 border-gray-300 px-4 py-2 focus:border-blue-500 focus:outline-none"
              />
            </div>

            <div>
              <label htmlFor="alt-payer-zelle-phone" className="mb-1 block text-sm font-medium text-gray-700">
                Zelle Phone <span className="text-gray-500">(Optional)</span>
              </label>
              <input
                id="alt-payer-zelle-phone"
                type="tel"
                value={value.zellePhone || ''}
                onChange={(e) => handleFieldChange('zellePhone', e.target.value)}
                placeholder="+1 (234) 567-8900"
                className="w-full rounded-lg border-2 border-gray-300 px-4 py-2 focus:border-blue-500 focus:outline-none"
              />
            </div>
          </div>

          {/* Helper Text */}
          <div className="rounded-lg bg-blue-100 p-4">
            <p className="text-sm text-blue-900">
              <strong>Why we ask:</strong> This information helps us automatically match the payment to your
              booking, even if the payer's name doesn't match yours. The more details you provide, the faster
              we can confirm your payment.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Integration Instructions:
 * 
 * 1. Add state to payment page:
 * ```tsx
 * const [alternativePayer, setAlternativePayer] = useState<AlternativePayerData | null>(null);
 * ```
 * 
 * 2. Add component before payment method selection:
 * ```tsx
 * <AlternativePayerField 
 *   value={alternativePayer}
 *   onChange={setAlternativePayer}
 *   className="mb-6"
 * />
 * ```
 * 
 * 3. Include in API call when creating payment intent:
 * ```tsx
 * const response = await apiFetch('/api/v1/payments/create-intent', {
 *   method: 'POST',
 *   body: JSON.stringify({
 *     ...otherData,
 *     alternativePayer: alternativePayer,
 *   }),
 * });
 * ```
 * 
 * 4. Backend will store in catering_bookings table:
 * - alternative_payer_name
 * - alternative_payer_email
 * - alternative_payer_phone
 * - alternative_payer_venmo
 * 
 * 5. Payment matching service will check both:
 * - Customer info (name, phone, email)
 * - Alternative payer info (if provided)
 */
