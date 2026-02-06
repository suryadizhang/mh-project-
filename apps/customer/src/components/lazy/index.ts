/**
 * Lazy-loaded components for code splitting
 * Centralized exports for easy imports throughout the app
 */

export { default as LazyPaymentForm } from './LazyPaymentForm';
export { default as LazyAlternativePaymentOptions } from './LazyAlternativePaymentOptions';
export { default as LazyDatePicker } from './LazyDatePicker';

// Re-export types
export type { PaymentFormProps, BookingData as PaymentBookingData } from './LazyPaymentForm';
export type {
  AlternativePaymentOptionsProps,
  BookingData as AlternativePaymentBookingData,
} from './LazyAlternativePaymentOptions';
