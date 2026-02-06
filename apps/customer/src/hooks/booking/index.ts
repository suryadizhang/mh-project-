/**
 * Booking Hooks
 *
 * Shared hooks for booking functionality used by both
 * BookUs page and Quote calculator.
 */

export { useBooking } from './useBooking';
export { useAddressAutocomplete } from './useAddressAutocomplete';
export { useGeocode } from './useGeocode';

// Types
export type {
  AddressData,
  UseAddressAutocompleteOptions,
  UseAddressAutocompleteReturn,
} from './useAddressAutocomplete';
export type { GeocodeResult, GeocodeError, UseGeocodeReturn } from './useGeocode';
