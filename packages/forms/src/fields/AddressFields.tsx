'use client';

import React, { useCallback, useRef, useEffect } from 'react';
import { MapPin, Building2 } from 'lucide-react';
import type {
  FieldErrors,
  UseFormRegister,
  UseFormSetValue,
  Path,
  FieldValues,
} from 'react-hook-form';
import {
  US_STATES,
  WEST_COAST_STATES,
  type StateCode,
  type FormLayout,
} from '../types';

/**
 * Props for AddressFields component
 */
export interface AddressFieldsProps<
  TFieldValues extends FieldValues = FieldValues,
> {
  /** react-hook-form register function */
  register: UseFormRegister<TFieldValues>;
  /** react-hook-form errors object */
  errors: FieldErrors<TFieldValues>;
  /** react-hook-form setValue function for autocomplete */
  setValue?: UseFormSetValue<TFieldValues>;

  /** Prefix for field names (e.g., "venue" → "venueStreet") */
  fieldPrefix?: string;

  /** Enable Google Places Autocomplete */
  enableAutocomplete?: boolean;
  /** Google Places API key (required if enableAutocomplete is true) */
  googleMapsApiKey?: string;

  /** Callback when address is geocoded */
  onGeocode?: (coords: { lat: number; lng: number }) => void;
  /** Callback when autocomplete fills address */
  onAddressSelect?: (address: {
    street: string;
    city: string;
    state: string;
    zipcode: string;
    lat?: number;
    lng?: number;
  }) => void;

  /** Which states to show in dropdown */
  stateOptions?: 'all' | 'west_coast' | StateCode[];

  /** Which fields are required */
  required?: {
    street?: boolean;
    city?: boolean;
    state?: boolean;
    zipcode?: boolean;
  };

  /** Layout variant */
  layout?: FormLayout;

  /** Show labels above inputs */
  showLabels?: boolean;

  /** Show icons in inputs */
  showIcons?: boolean;

  /** Custom placeholders */
  placeholders?: {
    street?: string;
    city?: string;
    state?: string;
    zipcode?: string;
  };

  /** Additional CSS class */
  className?: string;

  /** Disable all fields */
  disabled?: boolean;
}

/**
 * Get available states based on option
 */
function getStateList(option: 'all' | 'west_coast' | StateCode[]): StateCode[] {
  if (option === 'all') {
    return Object.keys(US_STATES) as StateCode[];
  }
  if (option === 'west_coast') {
    return WEST_COAST_STATES;
  }
  return option;
}

/**
 * Reusable address fields (street, city, state, zipcode)
 *
 * @example
 * // Basic usage
 * <AddressFields register={register} errors={errors} />
 *
 * @example
 * // With Google Places autocomplete
 * <AddressFields
 *   register={register}
 *   errors={errors}
 *   setValue={setValue}
 *   enableAutocomplete={true}
 *   googleMapsApiKey={process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY}
 *   onAddressSelect={(addr) => console.log('Selected:', addr)}
 * />
 *
 * @example
 * // West coast only states
 * <AddressFields
 *   register={register}
 *   errors={errors}
 *   stateOptions="west_coast"
 * />
 */
export function AddressFields<TFieldValues extends FieldValues = FieldValues>({
  register,
  errors,
  setValue,
  fieldPrefix = '',
  enableAutocomplete = false,
  googleMapsApiKey,
  onGeocode,
  onAddressSelect,
  stateOptions = 'west_coast',
  required = { street: true, city: true, state: true, zipcode: true },
  layout = 'grid',
  showLabels = true,
  showIcons = false,
  placeholders = {},
  className = '',
  disabled = false,
}: AddressFieldsProps<TFieldValues>) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const autocompleteRef = useRef<any>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  // Build field names with optional prefix
  const streetField = (
    fieldPrefix ? `${fieldPrefix}Street` : 'street'
  ) as Path<TFieldValues>;
  const cityField = (
    fieldPrefix ? `${fieldPrefix}City` : 'city'
  ) as Path<TFieldValues>;
  const stateField = (
    fieldPrefix ? `${fieldPrefix}State` : 'state'
  ) as Path<TFieldValues>;
  const zipcodeField = (
    fieldPrefix ? `${fieldPrefix}Zipcode` : 'zipcode'
  ) as Path<TFieldValues>;

  // Get error for a field
  const getError = (field: string): string | undefined => {
    const parts = field.split('.');
    let error: unknown = errors;
    for (const part of parts) {
      if (error && typeof error === 'object' && part in error) {
        error = (error as Record<string, unknown>)[part];
      } else {
        return undefined;
      }
    }
    return (error as { message?: string })?.message;
  };

  const streetError = getError(streetField);
  const cityError = getError(cityField);
  const stateError = getError(stateField);
  const zipcodeError = getError(zipcodeField);

  const states = getStateList(stateOptions);

  // Initialize Google Places Autocomplete
  const initAutocomplete = useCallback(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const googleMaps = (window as any).google;
    if (!enableAutocomplete || !inputRef.current || !googleMaps?.maps?.places) {
      return;
    }

    autocompleteRef.current = new googleMaps.maps.places.Autocomplete(
      inputRef.current,
      {
        componentRestrictions: { country: 'us' },
        fields: ['address_components', 'geometry', 'formatted_address'],
        types: ['address'],
      }
    );

    autocompleteRef.current.addListener('place_changed', () => {
      const place = autocompleteRef.current?.getPlace();
      if (!place?.address_components) return;

      let street = '';
      let city = '';
      let state = '';
      let zipcode = '';

      for (const component of place.address_components) {
        const type = component.types[0];
        switch (type) {
          case 'street_number':
            street = component.long_name + ' ';
            break;
          case 'route':
            street += component.long_name;
            break;
          case 'locality':
            city = component.long_name;
            break;
          case 'administrative_area_level_1':
            state = component.short_name;
            break;
          case 'postal_code':
            zipcode = component.long_name;
            break;
        }
      }

      // Set form values
      if (setValue) {
        // Type assertion needed due to generic constraints
        setValue(streetField, street.trim() as never, { shouldValidate: true });
        setValue(cityField, city as never, { shouldValidate: true });
        setValue(stateField, state as never, { shouldValidate: true });
        setValue(zipcodeField, zipcode as never, { shouldValidate: true });
      }

      // Callback with parsed address
      const lat = place.geometry?.location?.lat();
      const lng = place.geometry?.location?.lng();

      if (onAddressSelect) {
        onAddressSelect({
          street: street.trim(),
          city,
          state,
          zipcode,
          lat,
          lng,
        });
      }

      if (onGeocode && lat && lng) {
        onGeocode({ lat, lng });
      }
    });
  }, [
    enableAutocomplete,
    setValue,
    streetField,
    cityField,
    stateField,
    zipcodeField,
    onAddressSelect,
    onGeocode,
  ]);

  // Set up autocomplete when Google Maps is loaded
  useEffect(() => {
    if (!enableAutocomplete) return;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const googleMaps = (window as any).google;

    // Check if Google Maps is already loaded
    if (googleMaps?.maps?.places) {
      initAutocomplete();
      return;
    }

    // Load Google Maps script if not present and API key provided
    if (
      googleMapsApiKey &&
      !document.querySelector('script[src*="maps.googleapis.com"]')
    ) {
      const script = document.createElement('script');
      script.src = `https://maps.googleapis.com/maps/api/js?key=${googleMapsApiKey}&libraries=places`;
      script.async = true;
      script.onload = initAutocomplete;
      document.head.appendChild(script);
    }
  }, [enableAutocomplete, googleMapsApiKey, initAutocomplete]);

  // Register for street field with separate ref
  const { ref: streetRef, ...streetRegister } = register(streetField, {
    required: required.street ? 'Street address is required' : false,
    minLength: { value: 5, message: 'Please enter a complete address' },
  });

  // Combine refs callback
  const setStreetRef = useCallback(
    (el: HTMLInputElement | null) => {
      inputRef.current = el;
      streetRef(el);
    },
    [streetRef]
  );

  // Layout classes
  const containerClass =
    layout === 'grid'
      ? 'grid grid-cols-1 gap-4 md:grid-cols-6'
      : layout === 'inline'
        ? 'flex flex-wrap gap-4'
        : 'space-y-4';

  return (
    <div className={`${containerClass} ${className}`}>
      {/* Street Address - Full width */}
      <div
        className={layout === 'grid' ? 'md:col-span-6' : 'flex-1 min-w-full'}
      >
        <div className="form-group">
          {showLabels && (
            <label htmlFor={streetField} className="form-label">
              {showIcons && <MapPin className="mr-1 inline-block h-4 w-4" />}
              Street Address
              {required.street && <span className="text-red-500 ml-1">*</span>}
            </label>
          )}
          <input
            type="text"
            id={streetField}
            {...streetRegister}
            ref={setStreetRef}
            className={`form-control ${streetError ? 'is-invalid' : ''}`}
            placeholder={placeholders.street || 'Enter street address'}
            disabled={disabled}
            autoComplete={enableAutocomplete ? 'off' : 'street-address'}
          />
          {streetError && <div className="invalid-feedback">{streetError}</div>}
        </div>
      </div>

      {/* City - 2/6 width */}
      <div
        className={layout === 'grid' ? 'md:col-span-2' : 'flex-1 min-w-[150px]'}
      >
        <div className="form-group">
          {showLabels && (
            <label htmlFor={cityField} className="form-label">
              {showIcons && <Building2 className="mr-1 inline-block h-4 w-4" />}
              City
              {required.city && <span className="text-red-500 ml-1">*</span>}
            </label>
          )}
          <input
            type="text"
            id={cityField}
            className={`form-control ${cityError ? 'is-invalid' : ''}`}
            placeholder={placeholders.city || 'City'}
            disabled={disabled}
            autoComplete="address-level2"
            {...register(cityField, {
              required: required.city ? 'City is required' : false,
              minLength: { value: 2, message: 'City name is too short' },
            })}
          />
          {cityError && <div className="invalid-feedback">{cityError}</div>}
        </div>
      </div>

      {/* State - 2/6 width */}
      <div
        className={layout === 'grid' ? 'md:col-span-2' : 'flex-1 min-w-[100px]'}
      >
        <div className="form-group">
          {showLabels && (
            <label htmlFor={stateField} className="form-label">
              State
              {required.state && <span className="text-red-500 ml-1">*</span>}
            </label>
          )}
          <select
            id={stateField}
            className={`form-control ${stateError ? 'is-invalid' : ''}`}
            disabled={disabled}
            autoComplete="address-level1"
            {...register(stateField, {
              required: required.state ? 'State is required' : false,
            })}
          >
            <option value="">{placeholders.state || 'Select State'}</option>
            {states.map(code => (
              <option key={code} value={code}>
                {US_STATES[code]}
              </option>
            ))}
          </select>
          {stateError && <div className="invalid-feedback">{stateError}</div>}
        </div>
      </div>

      {/* ZIP Code - 2/6 width */}
      <div
        className={layout === 'grid' ? 'md:col-span-2' : 'flex-1 min-w-[100px]'}
      >
        <div className="form-group">
          {showLabels && (
            <label htmlFor={zipcodeField} className="form-label">
              ZIP Code
              {required.zipcode && <span className="text-red-500 ml-1">*</span>}
            </label>
          )}
          <input
            type="text"
            id={zipcodeField}
            className={`form-control ${zipcodeError ? 'is-invalid' : ''}`}
            placeholder={placeholders.zipcode || 'ZIP'}
            disabled={disabled}
            autoComplete="postal-code"
            maxLength={10}
            {...register(zipcodeField, {
              required: required.zipcode ? 'ZIP code is required' : false,
              pattern: {
                value: /^\d{5}(-\d{4})?$/,
                message: 'Invalid ZIP code format',
              },
            })}
          />
          {zipcodeError && (
            <div className="invalid-feedback">{zipcodeError}</div>
          )}
        </div>
      </div>
    </div>
  );
}

export default AddressFields;
