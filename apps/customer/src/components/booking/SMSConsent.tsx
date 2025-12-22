'use client';

import Link from 'next/link';
import React from 'react';

interface SMSConsentProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  error?: string;
  className?: string;
}

/**
 * SMS Consent checkbox for TCPA and carrier compliance
 * Required at point of SMS collection for legal compliance
 *
 * RingCentral Requirements (TCR Registration):
 * - Must list ALL types of messages customer will receive
 * - Must include opt-out instructions (STOP)
 * - Must include help instructions (HELP)
 * - Must include frequency disclosure
 * - Must include data rates disclaimer
 * - Must link to Privacy Policy and SMS Terms
 * - NO EMOJIS per carrier compliance (Rejection Code 6103)
 */
export const SMSConsent: React.FC<SMSConsentProps> = ({
  checked,
  onChange,
  error,
  className = '',
}) => {
  return (
    <div className={`bg-light rounded border p-3 ${className}`}>
      <div className="form-check">
        <input
          type="checkbox"
          id="smsConsent"
          className={`form-check-input ${error ? 'is-invalid' : ''}`}
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          required
        />
        <label htmlFor="smsConsent" className="form-check-label">
          <strong>I consent to receive text messages from My Hibachi Chef</strong>
          <p className="small mt-2 mb-2">
            By checking this box and providing my phone number, I agree to receive the following
            types of SMS text messages from my Hibachi LLC (doing business as My Hibachi Chef):
          </p>
          <ul className="small mb-2" style={{ paddingLeft: '1.2rem' }}>
            <li>
              <strong>Booking Confirmations</strong> - Confirmation of your reservation with deposit
              payment instructions
            </li>
            <li>
              <strong>Event Reminders</strong> - Reminders 48 hours and 24 hours before your
              scheduled hibachi event
            </li>
            <li>
              <strong>Chef Notifications</strong> - Updates about your assigned chef and arrival
              status
            </li>
            <li>
              <strong>Booking Updates</strong> - Important changes or updates to your reservation
            </li>
            <li>
              <strong>Customer Support</strong> - Responses to your questions or service inquiries
            </li>
            <li>
              <strong>Promotional Offers</strong> - Special discounts, seasonal offers, and
              exclusive deals (optional - you may opt out of marketing messages separately)
            </li>
          </ul>
          <p className="small mb-0" style={{ lineHeight: '1.5' }}>
            <strong>Message frequency varies</strong> based on your booking activity.{' '}
            <strong>Message and data rates may apply.</strong> Reply <strong>STOP</strong> to
            opt-out at any time. Reply <strong>HELP</strong> for assistance or call (916) 740-8786.{' '}
            View our{' '}
            <Link
              href="/terms#sms"
              target="_blank"
              className="text-primary text-decoration-underline"
            >
              SMS Terms of Service
            </Link>{' '}
            and{' '}
            <Link
              href="/privacy"
              target="_blank"
              className="text-primary text-decoration-underline"
            >
              Privacy Policy
            </Link>
            . SMS consent is not shared with third parties.
          </p>
        </label>
        {error && <div className="invalid-feedback d-block">{error}</div>}
      </div>
      <div className="alert alert-secondary small mt-2 mb-0 py-2">
        <strong>Why is this required?</strong> We need your permission to send you a booking
        confirmation and the $100 deposit payment link via text message within 2 hours of your
        booking request. Without SMS consent, you will only receive email notifications.
      </div>
    </div>
  );
};

export default SMSConsent;
