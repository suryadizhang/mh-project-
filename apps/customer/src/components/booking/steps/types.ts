/**
 * Booking Step Component Types
 *
 * Shared types for step components used in both BookUs and Quote pages
 */

import { UseFormRegister, FieldErrors, UseFormSetValue, UseFormWatch } from 'react-hook-form';

/**
 * Complete booking form data structure
 */
export type BookingFormData = {
  // Contact info (Step 1)
  name: string;
  email: string;
  phone: string;

  // Event details (Step 4)
  eventDate: Date;
  eventTime: '12PM' | '3PM' | '6PM' | '9PM';

  // Party size (Step 3)
  guestCount: number;

  // Billing address (Step 4) - Now handled by Stripe PaymentElement
  addressStreet: string;
  addressCity: string;
  addressState: string;
  addressZipcode: string;

  // Venue address (Step 2)
  sameAsVenue: boolean;
  venueStreet?: string;
  venueCity?: string;
  venueState?: string;
  venueZipcode?: string;
};

/**
 * Time slot configuration
 */
export interface TimeSlot {
  time: string;
  label: string;
  available: number;
  isAvailable: boolean;
}

/**
 * Alternative suggestion from smart scheduling
 */
export interface AlternativeSuggestion {
  slot_date: string;
  slot_time: string;
  score: number;
}

/**
 * Venue coordinates from geocoding
 */
export interface VenueCoordinates {
  lat: number;
  lng: number;
}

/**
 * Step configuration for the wizard
 */
export interface BookingStep {
  step: number;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

/**
 * Style variant for step components
 * - 'booking': Bootstrap-style form (BookUs page)
 * - 'quote': Tailwind gradient style (Quote calculator)
 */
export type StepVariant = 'booking' | 'quote';

/**
 * Common props shared by all step components
 */
export interface BaseStepProps<T extends Record<string, unknown> = BookingFormData> {
  register: UseFormRegister<T>;
  errors: FieldErrors<T>;
  onContinue: () => void;
  isValid: boolean;
  /** Style variant - 'booking' or 'quote' */
  variant?: StepVariant;
}
