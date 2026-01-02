'use client';

import Link from 'next/link';
import React from 'react';

import { useProtectedPhone, ProtectedEmail } from '@/components/ui/ProtectedPhone';

/**
 * Props for SMSConsentCheckbox component
 *
 * Supports both react-hook-form and useState patterns:
 * - For react-hook-form: pass `checked` and `onChange` from Controller's field
 * - For useState: pass `checked` and `onChange` directly from state
 */
export interface SMSConsentCheckboxProps {
  /** Whether the checkbox is checked */
  checked: boolean;
  /** Callback when checkbox changes */
  onChange: (checked: boolean) => void;
  /** Additional CSS classes for the wrapper */
  className?: string;
  /**
   * Variant style:
   * - 'default': Blue background theme (for booking pages)
   * - 'minimal': Gray/subtle theme (for contact/quote pages)
   */
  variant?: 'default' | 'minimal';
  /** Whether to show the full disclosure section */
  showFullDisclosure?: boolean;
  /** ID for accessibility - connects label to checkbox */
  id?: string;
}

/**
 * SMSConsentCheckbox - Reusable TCR/Carrier Compliant SMS Consent Component
 *
 * This component follows RingCentral TCR compliance requirements:
 * - Clear opt-in language
 * - Message types disclosure
 * - Frequency and rates disclosure
 * - STOP/HELP instructions
 * - Links to SMS Terms and Privacy Policy
 * - "Not required for purchase" disclaimer
 *
 * Usage with react-hook-form:
 * ```tsx
 * <Controller
 *   name="smsConsent"
 *   control={control}
 *   render={({ field }) => (
 *     <SMSConsentCheckbox
 *       checked={field.value || false}
 *       onChange={field.onChange}
 *     />
 *   )}
 * />
 * ```
 *
 * Usage with useState:
 * ```tsx
 * const [smsConsent, setSmsConsent] = useState(false);
 * <SMSConsentCheckbox
 *   checked={smsConsent}
 *   onChange={setSmsConsent}
 * />
 * ```
 */
export const SMSConsentCheckbox: React.FC<SMSConsentCheckboxProps> = ({
  checked,
  onChange,
  className = '',
  variant = 'default',
  showFullDisclosure = true,
  id = 'sms-consent',
}) => {
  // Anti-scraper protected contact info
  const { formatted: protectedPhone, tel: protectedTel } = useProtectedPhone();

  // Style variants
  const wrapperStyles = {
    default: 'rounded-lg border border-blue-200 bg-blue-50 p-4',
    minimal: 'rounded-xl border-2 border-gray-200 bg-gray-50 p-4',
  };

  const badgeStyles = {
    default: 'rounded-full bg-blue-600 px-3 py-1 text-xs font-bold text-white',
    minimal: 'rounded bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700',
  };

  const headerStyles = {
    default: 'text-lg font-semibold text-blue-900',
    minimal: 'text-sm font-medium text-gray-700',
  };

  const checkboxStyles = {
    default: 'mt-1 h-5 w-5 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500',
    minimal: 'mt-1 h-4 w-4 rounded border-gray-300 text-red-600 focus:ring-red-500',
  };

  return (
    <div className={`${wrapperStyles[variant]} ${className}`}>
      {/* Header with OPTIONAL badge */}
      <div className="mb-3 flex items-center justify-between">
        <h3 className={headerStyles[variant]}>
          {variant === 'default' ? 'SMS Communication Consent' : 'SMS Consent'}
        </h3>
        <span className={badgeStyles[variant]}>OPTIONAL</span>
      </div>

      <p className="mb-3 text-xs text-gray-600">
        Checking this box is not required to complete your{' '}
        {variant === 'default' ? 'booking' : 'request'}.
      </p>

      {/* Consent Checkbox */}
      <div className={variant === 'default' ? 'mb-4 space-y-3' : ''}>
        <div
          className={variant === 'default' ? 'rounded-md border border-blue-300 bg-white p-3' : ''}
        >
          <label className="flex cursor-pointer items-start space-x-3">
            <input
              type="checkbox"
              id={id}
              checked={checked}
              onChange={(e) => onChange(e.target.checked)}
              className={checkboxStyles[variant]}
              aria-describedby={`${id}-description`}
            />
            <div className="text-sm" id={`${id}-description`}>
              <div
                className={
                  variant === 'default' ? 'font-medium text-gray-900' : 'font-medium text-gray-800'
                }
              >
                {variant === 'default'
                  ? 'Yes, I consent to receive SMS text messages from My Hibachi Chef'
                  : 'I consent to receive text messages from My Hibachi Chef'}
              </div>

              <div className="mt-2 text-gray-600">
                <p className="mb-2 text-xs">
                  By checking this box, I agree to receive the following SMS messages:
                </p>
                <ul className="ml-4 list-disc space-y-1 text-xs">
                  <li>Booking confirmations and order details</li>
                  <li>Event reminders (48hrs and 24hrs before your event)</li>
                  <li>Chef updates and arrival notifications</li>
                  <li>Customer support conversations</li>
                  <li>Order alerts and booking changes</li>
                  {variant === 'minimal' && (
                    <li>Promotional offers (reply STOP to opt out of marketing)</li>
                  )}
                </ul>
              </div>

              {/* TCR Required: Consent not required for purchase */}
              <p className="mt-3 text-xs font-semibold text-gray-500">
                Consent is not required to{' '}
                {variant === 'default' ? 'make a purchase' : 'receive a response to your inquiry'}.
              </p>

              {variant === 'minimal' && (
                <p className="mt-1 text-xs text-gray-500">
                  SMS consent is not shared with third parties.
                </p>
              )}
            </div>
          </label>
        </div>

        {/* Full Disclosure Section - for booking pages */}
        {showFullDisclosure && variant === 'default' && (
          <div className="space-y-1 text-xs text-gray-600">
            <p>
              <strong>Message Frequency:</strong> Varies based on your booking activity. Message and
              data rates may apply.
            </p>
            <p>
              <strong>Opt-out:</strong> Reply STOP to any message to unsubscribe. Reply START to
              re-subscribe. Reply HELP for support.
            </p>
            <p>
              <strong>Contact:</strong>{' '}
              <a
                href={protectedTel ? `tel:${protectedTel}` : '#'}
                className="text-blue-600 hover:underline"
              >
                {protectedPhone || 'Loading...'}
              </a>{' '}
              | <ProtectedEmail className="text-blue-600 hover:underline" />
            </p>
            <p>
              <strong>Policies:</strong>{' '}
              <Link href="/privacy" className="text-blue-600 hover:underline">
                Privacy Policy
              </Link>{' '}
              |{' '}
              <Link href="/terms#sms" className="text-blue-600 hover:underline">
                Terms & SMS Policy
              </Link>
            </p>
          </div>
        )}

        {/* Minimal disclosure for quote/contact pages */}
        {showFullDisclosure && variant === 'minimal' && (
          <p className="mt-2 text-xs text-gray-500">
            Message frequency varies. Message and data rates may apply. Reply STOP to opt-out. Reply
            HELP for assistance or call{' '}
            <a
              href={protectedTel ? `tel:${protectedTel}` : '#'}
              className="text-red-600 hover:underline"
            >
              {protectedPhone || '(916) 740-8786'}
            </a>
            . View our{' '}
            <Link href="/terms#sms" className="text-red-600 hover:underline">
              SMS Terms
            </Link>{' '}
            and{' '}
            <Link href="/privacy" className="text-red-600 hover:underline">
              Privacy Policy
            </Link>
            .
          </p>
        )}
      </div>
    </div>
  );
};

export default SMSConsentCheckbox;
