/**
 * Booking Form Modules
 *
 * Reusable, modular components for the booking flow.
 * Each module is self-contained with its own TypeScript interfaces.
 *
 * Form Order (Smart Scheduling Optimized):
 * 1. PersonalInfoSection - Name, email, phone, SMS consent
 * 2. VenueAddressSection - Google Places, geocoding, travel fee preview
 * 3. EventDetailsSection - Guest counts, upgrades, live cost calculator
 * 4. DateTimeSection - Date picker, time slots (LAST - for travel-aware availability)
 * 5. TipCalculator - Gratuity selection before booking submission
 */

// Personal Info Section
export {
  PersonalInfoSection,
  type PersonalInfoFormData,
  type CommunicationPreference,
} from './PersonalInfoSection';

// Venue Address Section
export {
  VenueAddressSection,
  type VenueAddressFormData,
  type VenueCoordinates,
  type TravelFeeResult,
} from './VenueAddressSection';

// Event Details Section (Guest counts + tips + total estimate)
export {
  EventDetailsSection,
  type EventDetailsFormData,
  type CostBreakdown,
} from './EventDetailsSection';

// Date & Time Section
export {
  DateTimeSection,
  type DateTimeFormData,
  type TimeSlotValue,
  type TimeSlot,
} from './DateTimeSection';

// Tip Calculator
export { TipCalculator, type TipFormData, type TipPercentage } from './TipCalculator';

/**
 * Combined form data type for the complete booking form
 */
export interface BookingFormData extends Record<string, unknown> {
  // Personal Info
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  preferredCommunication: 'phone' | 'text' | 'email';
  smsConsent: boolean;

  // Venue Address
  venueStreet: string;
  venueCity: string;
  venueState: string;
  venueZipcode: string;
  venueType: 'house' | 'apartment' | 'office' | 'venue' | 'other';
  specialInstructions?: string;
  venueCoordinates?: {
    lat: number;
    lng: number;
  };

  // Event Details
  adultCount: number;
  childCount: number;
  upgrades: {
    salmon: number;
    scallops: number;
    filetMignon: number;
    lobsterTail: number;
    extraProtein: number;
    yakisoba: number;
    extraRice: number;
    vegetables: number;
    edamame: number;
    gyoza: number;
  };
  specialDietaryRequests?: string;

  // Date & Time
  eventDate: Date | null;
  timeSlot: '12PM' | '3PM' | '6PM' | '9PM' | null;

  // Tip
  tipPercentage: 0 | 15 | 20 | 25 | 30 | 'custom';
  customTipAmount?: number;

  // Additional
  agreedToTerms: boolean;
}

/**
 * Default values for booking form
 */
export const DEFAULT_BOOKING_FORM_VALUES: Partial<BookingFormData> = {
  firstName: '',
  lastName: '',
  email: '',
  phone: '',
  preferredCommunication: undefined, // No default - let user select
  smsConsent: false,
  venueStreet: '',
  venueCity: '',
  venueState: '',
  venueZipcode: '',
  venueType: 'house',
  specialInstructions: '',
  adultCount: 2,
  childCount: 0,
  upgrades: {
    salmon: 0,
    scallops: 0,
    filetMignon: 0,
    lobsterTail: 0,
    extraProtein: 0,
    yakisoba: 0,
    extraRice: 0,
    vegetables: 0,
    edamame: 0,
    gyoza: 0,
  },
  specialDietaryRequests: '',
  eventDate: null,
  timeSlot: null,
  tipPercentage: 0, // No default - let user select
  customTipAmount: 0,
  agreedToTerms: false,
};
