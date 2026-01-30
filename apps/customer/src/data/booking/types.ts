// Booking form types and interfaces

/**
 * Valid event time values (±60 min from slot centers in 30-min increments)
 *
 * 4 Slots with 5 times each = 20 total valid times:
 * - Lunch (12 PM center): 11:00 AM - 1:00 PM
 * - Afternoon (3 PM center): 2:00 PM - 4:00 PM
 * - Evening (6 PM center): 5:00 PM - 7:00 PM
 * - Prime (9 PM center): 8:00 PM - 10:00 PM
 */
export type EventTimeValue =
  // Lunch Service (centered on 12:00 PM)
  | '11:00 AM'
  | '11:30 AM'
  | '12:00 PM'
  | '12:30 PM'
  | '1:00 PM'
  // Afternoon Service (centered on 3:00 PM)
  | '2:00 PM'
  | '2:30 PM'
  | '3:00 PM'
  | '3:30 PM'
  | '4:00 PM'
  // Evening Service (centered on 6:00 PM)
  | '5:00 PM'
  | '5:30 PM'
  | '6:00 PM'
  | '6:30 PM'
  | '7:00 PM'
  // Prime Service (centered on 9:00 PM)
  | '8:00 PM'
  | '8:30 PM'
  | '9:00 PM'
  | '9:30 PM'
  | '10:00 PM';

export type BookingFormData = {
  name: string;
  email: string;
  phone: string;
  preferredCommunication: 'phone' | 'text' | 'email' | '';
  eventDate: Date;
  eventTime: EventTimeValue | '';
  guestCount: number;
  addressStreet: string;
  addressCity: string;
  addressState: string;
  addressZipcode: string;
  sameAsVenue: boolean;
  venueStreet?: string;
  venueCity?: string;
  venueState?: string;
  venueZipcode?: string;
};

export type TimeSlot = {
  time: string;
  label: string;
  available: number;
  isAvailable: boolean;
};

export type BookingState = {
  showValidationModal: boolean;
  missingFields: string[];
  showAgreementModal: boolean;
  formData: BookingFormData | null;
  bookedDates: Date[];
  loadingDates: boolean;
  dateError: string | null;
  availableTimeSlots: TimeSlot[];
  loadingTimeSlots: boolean;
  isSubmitting: boolean;
};

/**
 * Grouped time options for the event time dropdown.
 * Each slot has 5 time options (±60 min from center in 30-min increments).
 * Standard times (slot centers) are marked for user clarity.
 */
export type TimeOption = {
  value: EventTimeValue;
  label: string;
  isStandard?: boolean; // True for slot center times (12 PM, 3 PM, 6 PM, 9 PM)
};

export type TimeSlotGroup = {
  slot: string;
  label: string;
  centerTime: EventTimeValue;
  times: TimeOption[];
};

export const GROUPED_TIME_OPTIONS: TimeSlotGroup[] = [
  {
    slot: 'lunch',
    label: '🍽️ Lunch Service',
    centerTime: '12:00 PM',
    times: [
      { value: '11:00 AM', label: '11:00 AM' },
      { value: '11:30 AM', label: '11:30 AM' },
      { value: '12:00 PM', label: '12:00 PM (Standard)', isStandard: true },
      { value: '12:30 PM', label: '12:30 PM' },
      { value: '1:00 PM', label: '1:00 PM' },
    ],
  },
  {
    slot: 'afternoon',
    label: '☀️ Afternoon Service',
    centerTime: '3:00 PM',
    times: [
      { value: '2:00 PM', label: '2:00 PM' },
      { value: '2:30 PM', label: '2:30 PM' },
      { value: '3:00 PM', label: '3:00 PM (Standard)', isStandard: true },
      { value: '3:30 PM', label: '3:30 PM' },
      { value: '4:00 PM', label: '4:00 PM' },
    ],
  },
  {
    slot: 'evening',
    label: '🌅 Evening Service',
    centerTime: '6:00 PM',
    times: [
      { value: '5:00 PM', label: '5:00 PM' },
      { value: '5:30 PM', label: '5:30 PM' },
      { value: '6:00 PM', label: '6:00 PM (Standard)', isStandard: true },
      { value: '6:30 PM', label: '6:30 PM' },
      { value: '7:00 PM', label: '7:00 PM' },
    ],
  },
  {
    slot: 'prime',
    label: '🌙 Prime Evening Service',
    centerTime: '9:00 PM',
    times: [
      { value: '8:00 PM', label: '8:00 PM' },
      { value: '8:30 PM', label: '8:30 PM' },
      { value: '9:00 PM', label: '9:00 PM (Standard)', isStandard: true },
      { value: '9:30 PM', label: '9:30 PM' },
      { value: '10:00 PM', label: '10:00 PM' },
    ],
  },
];

/**
 * Get the slot group for a given time value
 */
export function getSlotForTime(time: EventTimeValue): TimeSlotGroup | undefined {
  return GROUPED_TIME_OPTIONS.find((group) => group.times.some((t) => t.value === time));
}

// Legacy time slot constants (for backward compatibility)
export const TIME_SLOTS = [
  { value: '12PM', label: '12:00 PM - Lunch Service' },
  { value: '3PM', label: '3:00 PM - Afternoon Service' },
  { value: '6PM', label: '6:00 PM - Dinner Service' },
  { value: '9PM', label: '9:00 PM - Late Evening Service' },
] as const;

// State options
export const US_STATES = [
  'AL',
  'AK',
  'AZ',
  'AR',
  'CA',
  'CO',
  'CT',
  'DE',
  'FL',
  'GA',
  'HI',
  'ID',
  'IL',
  'IN',
  'IA',
  'KS',
  'KY',
  'LA',
  'ME',
  'MD',
  'MA',
  'MI',
  'MN',
  'MS',
  'MO',
  'MT',
  'NE',
  'NV',
  'NH',
  'NJ',
  'NM',
  'NY',
  'NC',
  'ND',
  'OH',
  'OK',
  'OR',
  'PA',
  'RI',
  'SC',
  'SD',
  'TN',
  'TX',
  'UT',
  'VT',
  'VA',
  'WA',
  'WV',
  'WI',
  'WY',
];

// Default form values
export const DEFAULT_FORM_VALUES: Partial = {
  preferredCommunication: '',
  addressState: 'CA',
  venueState: 'CA',
  sameAsVenue: true,
  guestCount: 6,
};

// Form validation rules
export const VALIDATION_RULES = {
  name: { required: 'Name is required' },
  email: {
    required: 'Email is required',
    pattern: {
      value: /^\S+@\S+$/i,
      message: 'Please enter a valid email address',
    },
  },
  phone: { required: 'Phone number is required' },
  preferredCommunication: { required: 'Please select a communication method' },
  eventDate: { required: 'Event date is required' },
  eventTime: { required: 'Event time is required' },
  guestCount: {
    required: 'Guest count is required',
    min: { value: 1, message: 'At least 1 guest is required' },
    max: { value: 50, message: 'Maximum 50 guests allowed' },
  },
  addressStreet: { required: 'Street address is required' },
  addressCity: { required: 'City is required' },
  addressState: { required: 'State is required' },
  addressZipcode: { required: 'Zip code is required' },
};
