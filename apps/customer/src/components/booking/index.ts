// Booking component exports
export { AddressForm } from './AddressForm';
export { BookingHero } from './BookingHero';
export { BookingSummary } from './BookingSummary';
export { ContactInfo } from './ContactInfo';
export { DateTimeSelection } from './DateTimeSelection';
export { SMSConsent } from './SMSConsent';

// Shared step components with variant support
export { ContactInfoStep, VenueAddressStep, PartySizeStep, DateTimeStep } from './steps';

// Step component types
export type {
  BookingFormData,
  TimeSlot,
  AlternativeSuggestion,
  VenueCoordinates,
  BookingStep,
  StepVariant,
  BaseStepProps,
} from './steps';
