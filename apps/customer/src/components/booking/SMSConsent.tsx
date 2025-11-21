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
 * SMS Consent checkbox for TCPA compliance
 * Required at point of SMS collection for legal compliance
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
          <strong>📱 SMS Notifications (Required):</strong>
          <p className="mt-1 mb-1">
            I agree to receive text messages from My Hibachi Chef including:
          </p>
          <ul className="small mb-2">
            <li>Booking confirmations with deposit payment instructions</li>
            <li>Event reminders (48 hours and 24 hours before)</li>
            <li>Chef arrival notifications</li>
            <li>Important booking updates</li>
          </ul>
          <p className="small mb-0">
            Message frequency varies. Message and data rates may apply. Reply STOP to opt-out
            anytime. See our{' '}
            <Link href="/terms#sms" target="_blank" className="text-primary">
              SMS Terms
            </Link>
            .
          </p>
        </label>
        {error && <div className="invalid-feedback d-block">{error}</div>}
      </div>
      <div className="alert alert-info small mt-2 mb-0">
        <strong>Why required?</strong> We need your permission to send you booking confirmation and
        the $100 deposit payment instructions via SMS within 2 hours.
      </div>
    </div>
  );
};

export default SMSConsent;
