'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

// Import shared Google Maps types (declares Window.google globally)
import '@/types/googleMaps';
import type { GoogleMapsAutocomplete, GooglePlace } from '@/types/googleMaps';

export interface AddressData {
  street: string;
  city: string;
  state: string;
  zipCode: string;
  formattedAddress: string;
  coordinates?: {
    lat: number;
    lng: number;
  };
}

export interface UseAddressAutocompleteOptions {
  /** Country restriction for autocomplete (default: 'us') */
  country?: string;
  /** Callback when address is selected */
  onAddressSelect?: (address: AddressData) => void;
  /** Callback on error */
  onError?: (error: Error) => void;
}

export interface UseAddressAutocompleteReturn {
  /** Ref to attach to the input element */
  inputRef: React.RefObject<HTMLInputElement | null>;
  /** Current address data */
  addressData: AddressData | null;
  /** Whether Google Maps API is loaded */
  isLoaded: boolean;
  /** Error if any */
  error: string | null;
  /** Reset the autocomplete state */
  reset: () => void;
}

/**
 * Hook for Google Places Address Autocomplete
 *
 * @example
 * ```tsx
 * const { inputRef, addressData, isLoaded } = useAddressAutocomplete({
 *   onAddressSelect: (address) => {
 *     setValue('venueStreet', address.street);
 *     setValue('venueCity', address.city);
 *     setValue('venueState', address.state);
 *     setValue('venueZipcode', address.zipCode);
 *   }
 * });
 *
 * return (
 *   <input
 *     ref={inputRef}
 *     type="text"
 *     placeholder="Start typing an address..."
 *     disabled={!isLoaded}
 *   />
 * );
 * ```
 */
export function useAddressAutocomplete(
  options: UseAddressAutocompleteOptions = {}
): UseAddressAutocompleteReturn {
  const { country = 'us', onAddressSelect, onError } = options;

  const inputRef = useRef<HTMLInputElement>(null);
  const autocompleteRef = useRef<GoogleMapsAutocomplete | null>(null);

  const [addressData, setAddressData] = useState<AddressData | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize autocomplete
  const initializeAutocomplete = useCallback(() => {
    if (!inputRef.current || !window.google?.maps?.places) return;

    try {
      autocompleteRef.current = new window.google.maps.places.Autocomplete(
        inputRef.current,
        {
          types: ['address'],
          componentRestrictions: { country },
          fields: ['formatted_address', 'address_components', 'geometry'],
        }
      );

      if (!autocompleteRef.current) return;

      autocompleteRef.current.addListener('place_changed', () => {
        const place = autocompleteRef.current?.getPlace();
        if (!place?.formatted_address) return;

        let street = '';
        let city = '';
        let state = '';
        let zipCode = '';

        // Extract address components
        place.address_components?.forEach((component) => {
          const types = component.types;

          if (types.includes('street_number')) {
            street = component.long_name + ' ';
          }
          if (types.includes('route')) {
            street += component.long_name;
          }
          if (types.includes('locality')) {
            city = component.long_name;
          }
          if (types.includes('administrative_area_level_1')) {
            state = component.short_name;
          }
          if (types.includes('postal_code')) {
            zipCode = component.short_name;
          }
        });

        const newAddressData: AddressData = {
          street: street.trim(),
          city,
          state,
          zipCode,
          formattedAddress: place.formatted_address || '',
          coordinates: place.geometry?.location
            ? {
              lat: place.geometry.location.lat(),
              lng: place.geometry.location.lng(),
            }
            : undefined,
        };

        setAddressData(newAddressData);
        onAddressSelect?.(newAddressData);
      });

      setIsLoaded(true);
      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to initialize autocomplete';
      setError(errorMessage);
      onError?.(err instanceof Error ? err : new Error(errorMessage));
    }
  }, [country, onAddressSelect, onError]);

  // Load Google Maps script and initialize
  useEffect(() => {
    const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;

    if (!apiKey) {
      setError('Google Maps API key not configured');
      return;
    }

    // If already loaded, just initialize
    if (window.google?.maps?.places) {
      initializeAutocomplete();
      return;
    }

    // Load the script
    const existingScript = document.querySelector(
      'script[src*="maps.googleapis.com/maps/api/js"]'
    );

    if (existingScript) {
      // Script is loading, wait for it
      existingScript.addEventListener('load', initializeAutocomplete);
      return;
    }

    // Create and load the script
    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places`;
    script.async = true;
    script.defer = true;
    script.onload = initializeAutocomplete;
    script.onerror = () => {
      setError('Failed to load Google Maps');
      onError?.(new Error('Failed to load Google Maps'));
    };
    document.head.appendChild(script);

    return () => {
      // Cleanup autocomplete listeners
      if (autocompleteRef.current) {
        window.google?.maps?.event?.clearInstanceListeners(autocompleteRef.current);
      }
    };
  }, [initializeAutocomplete, onError]);

  const reset = useCallback(() => {
    setAddressData(null);
    setError(null);
  }, []);

  return {
    inputRef,
    addressData,
    isLoaded,
    error,
    reset,
  };
}
