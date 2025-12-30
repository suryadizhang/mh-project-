import { useCallback } from 'react';

/**
 * Format a phone number as (XXX) XXX-XXXX
 */
export function formatPhoneNumber(value: string): string {
  // Remove all non-digits
  const cleaned = value.replace(/\D/g, '');

  // Limit to 10 digits
  const limited = cleaned.slice(0, 10);

  // Format based on length
  if (limited.length <= 3) {
    return limited;
  } else if (limited.length <= 6) {
    return `(${limited.slice(0, 3)}) ${limited.slice(3)}`;
  } else {
    return `(${limited.slice(0, 3)}) ${limited.slice(3, 6)}-${limited.slice(6)}`;
  }
}

/**
 * Strip formatting from phone number (get raw digits)
 */
export function stripPhoneFormatting(value: string): string {
  return value.replace(/\D/g, '');
}

/**
 * Validate phone number has 10 digits
 */
export function isValidPhone(value: string): boolean {
  const digits = stripPhoneFormatting(value);
  return digits.length === 10;
}

/**
 * Hook for phone number formatting
 *
 * @example
 * const { format, strip, isValid } = usePhoneFormat();
 *
 * <input
 *   onChange={(e) => {
 *     const formatted = format(e.target.value);
 *     setValue('phone', formatted);
 *   }}
 * />
 */
export function usePhoneFormat() {
  const format = useCallback(formatPhoneNumber, []);
  const strip = useCallback(stripPhoneFormatting, []);
  const isValid = useCallback(isValidPhone, []);

  return { format, strip, isValid };
}

export default usePhoneFormat;
