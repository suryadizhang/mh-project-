'use client';

import { useEffect, useState } from 'react';

interface ProtectedPhoneProps {
  className?: string;
  showIcon?: boolean;
}

// Base64 encoded phone number (encode: btoa('916-740-8768'))
const ENCODED_PHONE = 'OTE2LTc0MC04NzY4';
const ENCODED_TEL = 'KzE5MTY3NDA4NzY4'; // btoa('+19167408768')

/**
 * ProtectedPhone - Anti-scraper phone number component
 *
 * How it works:
 * - Server-side scrapers see: "Call Us" (no phone number)
 * - Google sees: tel:+19167408768 after JS executes (for mobile click-to-call)
 * - Users see: (916) 740-8768 after JS loads (~100ms)
 * - Accessibility: aria-label provides screen reader support
 */
export function ProtectedPhone({
  className,
  showIcon = true,
}: ProtectedPhoneProps) {
  const [phone, setPhone] = useState<string | null>(null);
  const [tel, setTel] = useState<string | null>(null);

  useEffect(() => {
    // Decode only on client-side - scrapers see nothing
    try {
      setPhone(atob(ENCODED_PHONE));
      setTel(atob(ENCODED_TEL));
    } catch {
      // Fallback for SSR or decode errors
      setPhone(null);
    }
  }, []);

  if (!phone || !tel) {
    // SSR/Loading: Show nothing to scrapers
    return (
      <span className={className} aria-label="Phone number loading">
        {showIcon && '📞 '}Call Us
      </span>
    );
  }

  return (
    <a
      href={`tel:${tel}`}
      className={className}
      aria-label={`Call us at ${phone}`}
    >
      {showIcon && '📞 '}({phone.slice(0, 3)}) {phone.slice(4, 7)}-
      {phone.slice(8)}
    </a>
  );
}

/**
 * Hook for places that need just the formatted number (no link)
 */
export function useProtectedPhone() {
  const [phone, setPhone] = useState<string | null>(null);
  const [tel, setTel] = useState<string | null>(null);

  useEffect(() => {
    try {
      setPhone(atob(ENCODED_PHONE));
      setTel(atob(ENCODED_TEL));
    } catch {
      setPhone(null);
    }
  }, []);

  return {
    phone, // "916-740-8768"
    tel, // "+19167408768"
    formatted: phone
      ? `(${phone.slice(0, 3)}) ${phone.slice(4, 7)}-${phone.slice(8)}`
      : null,
    isLoaded: !!phone,
  };
}

/**
 * ProtectedEmail - Links to contact form instead of exposing email
 */
interface ProtectedEmailProps {
  className?: string;
  showIcon?: boolean;
  text?: string;
}

export function ProtectedEmail({
  className,
  showIcon = true,
  text = 'Email Us',
}: ProtectedEmailProps) {
  return (
    <a
      href="/contact#email-us"
      className={className}
      aria-label="Send us an email via contact form"
    >
      {showIcon && '✉️ '}{text}
    </a>
  );
}

// Base64 encoded emails for payment
// btoa('myhibachichef@gmail.com') = 'bXloaWJhY2hpY2hlZkBnbWFpbC5jb20='
const ENCODED_PAYMENT_EMAIL = 'bXloaWJhY2hpY2hlZkBnbWFpbC5jb20=';

/**
 * ProtectedPaymentEmail - Shows decoded email for Zelle/Venmo payments
 * 
 * Unlike ProtectedEmail (which links to contact form), this component
 * shows the actual email address because users need it for payments.
 * Still protected from scrapers via JS decode.
 */
interface ProtectedPaymentEmailProps {
  className?: string;
  showAsLink?: boolean;
  copyable?: boolean;
}

export function ProtectedPaymentEmail({
  className,
  showAsLink = false,
  copyable = true,
}: ProtectedPaymentEmailProps) {
  const [email, setEmail] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    try {
      setEmail(atob(ENCODED_PAYMENT_EMAIL));
    } catch {
      setEmail(null);
    }
  }, []);

  const handleCopy = async () => {
    if (email) {
      await navigator.clipboard.writeText(email);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!email) {
    return <span className={className}>Loading...</span>;
  }

  if (showAsLink) {
    return (
      <a href={`mailto:${email}`} className={className}>
        {email}
      </a>
    );
  }

  return (
    <span className={className}>
      {email}
      {copyable && (
        <button
          onClick={handleCopy}
          className="ml-2 text-xs text-gray-500 hover:text-gray-700"
          title="Copy to clipboard"
        >
          {copied ? '✓ Copied!' : '📋 Copy'}
        </button>
      )}
    </span>
  );
}

/**
 * Hook for payment email - use in places needing programmatic access
 */
export function useProtectedPaymentEmail() {
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    try {
      setEmail(atob(ENCODED_PAYMENT_EMAIL));
    } catch {
      setEmail(null);
    }
  }, []);

  return {
    email, // "myhibachichef@gmail.com"
    isLoaded: !!email,
  };
}
