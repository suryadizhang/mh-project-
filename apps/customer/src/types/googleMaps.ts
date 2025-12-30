/**
 * Google Maps Types
 *
 * Shared type declarations for Google Maps API
 * Used by address autocomplete and geocoding features
 */

export interface GoogleAddressComponent {
  long_name: string;
  short_name: string;
  types: string[];
}

export interface GooglePlace {
  formatted_address?: string;
  address_components?: GoogleAddressComponent[];
  geometry?: {
    location?: {
      lat: () => number;
      lng: () => number;
    };
  };
}

export interface GoogleMapsAutocomplete {
  addListener: (event: string, callback: () => void) => void;
  getPlace: () => GooglePlace;
}

export interface AutocompleteOptions {
  componentRestrictions?: { country: string };
  types?: string[];
  fields?: string[];
}

// Extend the Window interface for Google Maps
declare global {
  interface Window {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    google?: any;
    initAutocomplete?: () => void;
  }
}

// Ensure this file is treated as a module
export { };
