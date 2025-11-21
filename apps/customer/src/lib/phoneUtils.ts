/**
 * Phone number validation and formatting utilities
 * Normalizes phone numbers to 10-digit format for consistent storage
 */

/**
 * Normalize phone number to 10 digits (removes all non-numeric characters)
 * @param phone - Phone number in any format
 * @returns 10-digit phone number or empty string if invalid
 */
export function normalizePhoneNumber(phone: string): string {
  if (!phone) return '';

  // Remove all non-numeric characters
  const digits = phone.replace(/\D/g, '');

  // Remove country code if present (1 at start)
  const normalized = digits.startsWith('1') && digits.length === 11 ? digits.substring(1) : digits;

  // Return only if exactly 10 digits
  return normalized.length === 10 ? normalized : digits;
}

/**
 * Format phone number for display (e.g., 2103884155 -> (210) 388-4155)
 * @param phone - 10-digit phone number
 * @returns Formatted phone number
 */
export function formatPhoneNumber(phone: string): string {
  const normalized = normalizePhoneNumber(phone);

  if (normalized.length !== 10) return phone; // Return as-is if invalid

  const areaCode = normalized.substring(0, 3);
  const prefix = normalized.substring(3, 6);
  const lineNumber = normalized.substring(6, 10);

  return `(${areaCode}) ${prefix}-${lineNumber}`;
}

/**
 * Validate phone number format
 * @param phone - Phone number to validate
 * @returns true if valid 10-digit US phone number
 */
export function isValidPhoneNumber(phone: string): boolean {
  const normalized = normalizePhoneNumber(phone);
  return /^\d{10}$/.test(normalized);
}

/**
 * Get phone validation error message
 * @param phone - Phone number to validate
 * @returns Error message or null if valid
 */
export function getPhoneValidationError(phone: string): string | null {
  if (!phone) return 'Phone number is required';

  const normalized = normalizePhoneNumber(phone);

  if (normalized.length === 0) return 'Phone number must contain digits';
  if (normalized.length < 10) return 'Phone number must be 10 digits';
  if (normalized.length > 10) return 'Phone number must be exactly 10 digits';
  if (!/^\d{10}$/.test(normalized)) return 'Invalid phone number format';

  return null;
}
