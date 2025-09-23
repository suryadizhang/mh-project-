// Booking form types and interfaces

export type BookingFormData = {
  name: string;
  email: string;
  phone: string;
  preferredCommunication: 'phone' | 'text' | 'email' | '';
  eventDate: Date;
  eventTime: '12PM' | '3PM' | '6PM' | '9PM';
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

// Time slot constants
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
export const DEFAULT_FORM_VALUES: Partial<BookingFormData> = {
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
