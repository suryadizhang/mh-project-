/**
 * BookUs Step Components
 *
 * Re-exports from the shared booking step components location.
 * This file maintains backward compatibility for existing imports.
 *
 * For new code, prefer importing from:
 * @/components/booking/steps
 */

// Re-export from shared location for backward compatibility
export {
  ContactInfoStep,
  VenueAddressStep,
  PartySizeStep,
  DateTimeStep,
} from '@/components/booking/steps';

export type {
  BookingFormData,
  TimeSlot,
  AlternativeSuggestion,
  VenueCoordinates,
  BookingStep,
  StepVariant,
  BaseStepProps,
} from '@/components/booking/steps';
