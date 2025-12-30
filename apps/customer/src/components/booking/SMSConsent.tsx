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
 *
 * CRITICAL: RingCentral/TCR Compliance Requirements:
 * 1. Checkbox must be UNCHECKED by default (no forced opt-in)
 * 2. Checkbox must be clearly marked as OPTIONAL
 * 3. Must state "Consent is not required to make a purchase"
 * 4. Must list ALL types of messages customer will receive
 * 5. Must include opt-out instructions (STOP)
 * 6. Must include help instructions (HELP)
 * 7. Must include frequency disclosure
 * 8. Must include data rates disclaimer
 * 9. Must link to Privacy Policy and SMS Terms
 * 10. NO EMOJIS per carrier compliance
 * 11. SMS consent must not be shared with third parties
 */
export const SMSConsent: React.FC<SMSConsentProps> = ({
  checked,
  onChange,
  error,
  className = '',
}) => {
  return (
    <div className={`bg-light rounded border p-3 ${className}`}>
      {/* OPTIONAL Badge - Required for TCR compliance */}
      <div className="d-flex align-items-center mb-2">
        <span className="badge bg-info text-white me-2">OPTIONAL</span>
        <span className="small text-muted">Checking this box is not required to complete your booking</span>
      </div>

      <div className="form-check">
        <input
          type="checkbox"
          id="smsConsent"
          className={`form-check-input ${error ? 'is-invalid' : ''}`}
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          aria-describedby="smsConsentDescription"
        />
        <label htmlFor="smsConsent" className="form-check-label">
          <strong>I consent to receive text messages from My Hibachi Chef</strong>
          <p className="small mt-2 mb-2">
            By checking this box and providing my phone number, I voluntarily agree to receive the following
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
              exclusive deals (you may opt out of marketing messages separately by replying STOP)
            </li>
          </ul>
          <p className="small mb-2" style={{ lineHeight: '1.5' }}>
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
            . SMS consent is not shared with third parties or affiliates.
          </p>
          {/* TCR Required: Consent not required for purchase */}
          <p className="small mb-0 fw-bold text-muted">
            Consent is not required to make a purchase. You can still complete your booking without checking this box.
          </p>
        </label>
        {error && <div className="invalid-feedback d-block">{error}</div>}
      </div>
      <div id="smsConsentDescription" className="alert alert-secondary small mt-2 mb-0 py-2">
        <strong>What happens if I don&apos;t check this box?</strong> You will still receive essential
        transactional SMS messages related to your booking (confirmations, reminders, chef arrival updates).
        However, you will not receive promotional offers or marketing messages. You can opt into marketing
        messages later by texting START to our number.
      </div>
    </div>
  );
};

export default SMSConsent;
