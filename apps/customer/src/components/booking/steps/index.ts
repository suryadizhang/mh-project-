/**
 * Booking Step Components
 *
 * Shared step components for booking wizards.
 * Supports two styling variants:
 * - 'booking': Bootstrap-style (BookUs page)
 * - 'quote': Tailwind gradient style (Quote calculator)
 *
 * @example
 * // BookUs page (default booking variant)
 * <ContactInfoStep register={register} errors={errors} onContinue={next} isValid={true} />
 *
 * // Quote calculator (quote variant)
 * <ContactInfoStep register={register} errors={errors} onContinue={next} isValid={true} variant="quote" />
 */

export { ContactInfoStep } from './ContactInfoStep';
export { VenueAddressStep } from './VenueAddressStep';
export { PartySizeStep } from './PartySizeStep';
export { DateTimeStep } from './DateTimeStep';

// Types
export type {
  BookingFormData,
  TimeSlot,
  AlternativeSuggestion,
  VenueCoordinates,
  BookingStep,
  StepVariant,
  BaseStepProps,
} from './types';
