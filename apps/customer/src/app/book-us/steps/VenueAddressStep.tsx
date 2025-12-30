/**
 * VenueAddressStep - Re-export from shared location
 *
 * This file re-exports the VenueAddressStep component from the shared
 * booking steps to maintain backward compatibility with existing imports.
 *
 * The shared component supports a 'variant' prop for styling:
 * - 'booking' (default): Bootstrap-style for BookUs page
 * - 'quote': Tailwind-style for QuoteCalculator
 */
export { VenueAddressStep } from '@/components/booking/steps';
