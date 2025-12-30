// Shared form types

import type { FieldErrors, UseFormRegister, UseFormWatch, UseFormSetValue } from 'react-hook-form';

/**
 * Common form field props for react-hook-form integration
 */
export interface FormFieldProps<TFieldValues extends Record<string, unknown> = Record<string, unknown>> {
  register: UseFormRegister<TFieldValues>;
  errors: FieldErrors<TFieldValues>;
  watch?: UseFormWatch<TFieldValues>;
  setValue?: UseFormSetValue<TFieldValues>;
}

/**
 * Contact information structure
 */
export interface ContactInfo {
  name: string;
  email: string;
  phone: string;
}

/**
 * Address structure
 */
export interface Address {
  street: string;
  city: string;
  state: string;
  zipcode: string;
}

/**
 * Venue address with additional fields
 */
export interface VenueAddress extends Address {
  lat?: number;
  lng?: number;
  normalized?: string;
}

/**
 * Time slot structure from smart scheduling
 */
export interface TimeSlot {
  slot_time: string;
  is_available: boolean;
  available_chefs?: number;
  estimated_duration?: number;
}

/**
 * Alternative suggestion from smart scheduling
 */
export interface AlternativeSuggestion {
  date: string;
  slot_time: string;
  reason: string;
  available_chefs?: number;
}

/**
 * State code type
 */
export type StateCode =
  | 'AL' | 'AK' | 'AZ' | 'AR' | 'CA' | 'CO' | 'CT' | 'DE' | 'FL' | 'GA'
  | 'HI' | 'ID' | 'IL' | 'IN' | 'IA' | 'KS' | 'KY' | 'LA' | 'ME' | 'MD'
  | 'MA' | 'MI' | 'MN' | 'MS' | 'MO' | 'MT' | 'NE' | 'NV' | 'NH' | 'NJ'
  | 'NM' | 'NY' | 'NC' | 'ND' | 'OH' | 'OK' | 'OR' | 'PA' | 'RI' | 'SC'
  | 'SD' | 'TN' | 'TX' | 'UT' | 'VT' | 'VA' | 'WA' | 'WV' | 'WI' | 'WY';

/**
 * US States lookup
 */
export const US_STATES: Record<StateCode, string> = {
  AL: 'Alabama', AK: 'Alaska', AZ: 'Arizona', AR: 'Arkansas', CA: 'California',
  CO: 'Colorado', CT: 'Connecticut', DE: 'Delaware', FL: 'Florida', GA: 'Georgia',
  HI: 'Hawaii', ID: 'Idaho', IL: 'Illinois', IN: 'Indiana', IA: 'Iowa',
  KS: 'Kansas', KY: 'Kentucky', LA: 'Louisiana', ME: 'Maine', MD: 'Maryland',
  MA: 'Massachusetts', MI: 'Michigan', MN: 'Minnesota', MS: 'Mississippi', MO: 'Missouri',
  MT: 'Montana', NE: 'Nebraska', NV: 'Nevada', NH: 'New Hampshire', NJ: 'New Jersey',
  NM: 'New Mexico', NY: 'New York', NC: 'North Carolina', ND: 'North Dakota', OH: 'Ohio',
  OK: 'Oklahoma', OR: 'Oregon', PA: 'Pennsylvania', RI: 'Rhode Island', SC: 'South Carolina',
  SD: 'South Dakota', TN: 'Tennessee', TX: 'Texas', UT: 'Utah', VT: 'Vermont',
  VA: 'Virginia', WA: 'Washington', WV: 'West Virginia', WI: 'Wisconsin', WY: 'Wyoming',
};

/**
 * West Coast states (primary service area)
 */
export const WEST_COAST_STATES: StateCode[] = ['CA', 'NV', 'OR', 'WA'];

/**
 * Layout options for form fields
 */
export type FormLayout = 'stacked' | 'inline' | 'grid';

/**
 * Step in a multi-step wizard
 */
export interface WizardStep {
  label: string;
  icon?: React.ReactNode;
  description?: string;
}
