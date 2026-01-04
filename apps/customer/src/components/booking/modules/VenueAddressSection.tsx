'use client';

import { AlertCircle, MapPin, Navigation, DollarSign } from 'lucide-react';
import React, { useEffect, useRef, useState, useCallback } from 'react';
import {
  Control,
  Controller,
  FieldErrors,
  UseFormRegister,
  UseFormSetValue,
  UseFormWatch,
} from 'react-hook-form';

/**
 * Type for Google Maps Address Component
 */
interface GoogleAddressComponent {
  long_name: string;
  short_name: string;
  types: string[];
}

/**
 * Type for venue coordinates
 */
export interface VenueCoordinates {
  lat: number;
  lng: number;
}

/**
 * Venue Address form data structure
 */
export interface VenueAddressFormData {
  venueStreet: string;
  venueCity: string;
  venueState: string;
  venueZipcode: string;
  venueCoordinates?: VenueCoordinates;
}

/**
 * Travel fee calculation result
 */
export interface TravelFeeResult {
  distanceMiles: number;
  freeMiles: number;
  billableMiles: number;
  perMileRate: number;
  travelFee: number;
  isWithinServiceArea: boolean;
}

export interface VenueAddressSectionProps {
  // Use 'any' to allow parent forms with additional fields
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  control: Control<any>;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  errors: FieldErrors<any>;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  register: UseFormRegister<any>;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  watch: UseFormWatch<any>;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  setValue: UseFormSetValue<any>;
  className?: string;
  showCompletionBadge?: boolean;
  showTravelFeePreview?: boolean;
  /** Station coordinates for distance calculation */
  stationCoordinates?: VenueCoordinates;
  /** Free miles before charging (default 30) */
  freeMiles?: number;
  /** Rate per mile after free miles (default $2) */
  perMileRate?: number;
  /** Maximum service distance in miles (default 100) */
  maxServiceDistance?: number;
  /** Callback when venue is geocoded */
  onVenueGeocoded?: (coordinates: VenueCoordinates, address: string) => void;
  /** Callback when travel fee is calculated */
  onTravelFeeCalculated?: (result: TravelFeeResult) => void;
  /** Alias callback for page compatibility */
  onTravelFeeChange?: (result: TravelFeeResult) => void;
}

// Extend Window interface for Google Maps
declare global {
  interface Window {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    google?: any;
  }
}

/**
 * VenueAddressSection - Enhanced venue address form with Google Places Autocomplete
 *
 * Features:
 * - Google Places Autocomplete for address search
 * - Auto-fill city, state, zip from selection
 * - Real-time travel fee calculation preview
 * - Service area validation
 * - Geocoding for smart scheduling
 */
export const VenueAddressSection: React.FC<VenueAddressSectionProps> = ({
  control,
  errors,
  register,
  watch,
  setValue,
  className = '',
  showCompletionBadge = true,
  showTravelFeePreview = true,
  stationCoordinates,
  freeMiles = 30,
  perMileRate = 2,
  maxServiceDistance = 100,
  onVenueGeocoded,
  onTravelFeeCalculated,
  onTravelFeeChange,
}) => {
  // Refs for Google Places Autocomplete
  const venueAddressInputRef = useRef<HTMLInputElement | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const autocompleteRef = useRef<any>(null);

  // State
  const [travelFeeResult, setTravelFeeResult] = useState<TravelFeeResult | null>(null);
  const [isCalculatingDistance, setIsCalculatingDistance] = useState(false);
  const [googleMapsLoaded, setGoogleMapsLoaded] = useState(false);

  // Check if section is complete
  const venueStreet = watch('venueStreet');
  const venueCity = watch('venueCity');
  const venueState = watch('venueState');
  const venueZipcode = watch('venueZipcode');

  const isComplete = Boolean(venueStreet && venueCity && venueState && venueZipcode);

  // Watch venue coordinates from form
  const venueCoordinates = watch('venueCoordinates');

  // Recalculate travel fee when stationCoordinates arrives AFTER venue was already selected
  // This fixes the timing issue where user picks address before station coords load
  useEffect(() => {
    // Only calculate if we have both coordinates AND haven't calculated yet
    if (
      stationCoordinates &&
      venueCoordinates?.lat &&
      venueCoordinates?.lng &&
      showTravelFeePreview &&
      !travelFeeResult
    ) {
      setIsCalculatingDistance(true);
      try {
        const R = 3959; // Earth's radius in miles
        const lat1 = stationCoordinates.lat;
        const lon1 = stationCoordinates.lng;
        const lat2 = venueCoordinates.lat;
        const lon2 = venueCoordinates.lng;

        const dLat = ((lat2 - lat1) * Math.PI) / 180;
        const dLon = ((lon2 - lon1) * Math.PI) / 180;
        const a =
          Math.sin(dLat / 2) * Math.sin(dLat / 2) +
          Math.cos((lat1 * Math.PI) / 180) *
            Math.cos((lat2 * Math.PI) / 180) *
            Math.sin(dLon / 2) *
            Math.sin(dLon / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        const distance = R * c;

        const billableMiles = Math.max(0, distance - freeMiles);
        const travelFee = billableMiles * perMileRate;
        const isWithinServiceArea = distance <= maxServiceDistance;

        const result: TravelFeeResult = {
          distanceMiles: distance,
          freeMiles,
          billableMiles,
          perMileRate,
          travelFee,
          isWithinServiceArea,
        };

        setTravelFeeResult(result);
        onTravelFeeCalculated?.(result);
        onTravelFeeChange?.(result);
      } finally {
        setIsCalculatingDistance(false);
      }
    }
  }, [
    stationCoordinates,
    venueCoordinates,
    showTravelFeePreview,
    travelFeeResult,
    freeMiles,
    perMileRate,
    maxServiceDistance,
    onTravelFeeCalculated,
    onTravelFeeChange,
  ]);

  // Use callback alias if provided
  const handleTravelFeeResult = useCallback(
    (result: TravelFeeResult) => {
      setTravelFeeResult(result);
      onTravelFeeCalculated?.(result);
      onTravelFeeChange?.(result);
    },
    [onTravelFeeCalculated, onTravelFeeChange],
  );

  /**
   * Calculate distance between two coordinates using Haversine formula
   */
  const calculateDistanceMiles = useCallback(
    (lat1: number, lon1: number, lat2: number, lon2: number): number => {
      const R = 3959; // Earth's radius in miles
      const dLat = ((lat2 - lat1) * Math.PI) / 180;
      const dLon = ((lon2 - lon1) * Math.PI) / 180;
      const a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos((lat1 * Math.PI) / 180) *
          Math.cos((lat2 * Math.PI) / 180) *
          Math.sin(dLon / 2) *
          Math.sin(dLon / 2);
      const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
      return R * c;
    },
    [],
  );

  /**
   * Calculate travel fee based on distance
   */
  const calculateTravelFee = useCallback(
    (distanceMiles: number): TravelFeeResult => {
      const billableMiles = Math.max(0, distanceMiles - freeMiles);
      const travelFee = billableMiles * perMileRate;
      const isWithinServiceArea = distanceMiles <= maxServiceDistance;

      return {
        distanceMiles: Math.round(distanceMiles * 10) / 10,
        freeMiles,
        billableMiles: Math.round(billableMiles * 10) / 10,
        perMileRate,
        travelFee: Math.round(travelFee * 100) / 100,
        isWithinServiceArea,
      };
    },
    [freeMiles, perMileRate, maxServiceDistance],
  );

  /**
   * Handle place selection from Google Places Autocomplete
   */
  const handlePlaceSelect = useCallback(() => {
    if (!autocompleteRef.current) return;

    const place = autocompleteRef.current.getPlace();

    if (!place.formatted_address || !place.address_components) {
      console.warn('No address details returned from Google Places');
      return;
    }

    // Update venue address with formatted address
    setValue('venueStreet', place.formatted_address, { shouldValidate: true });

    // Extract address components
    let city = '';
    let state = '';
    let zipCode = '';
    let streetNumber = '';
    let streetName = '';

    place.address_components.forEach((component: GoogleAddressComponent) => {
      const types = component.types;

      if (types.includes('street_number')) {
        streetNumber = component.short_name;
      }
      if (types.includes('route')) {
        streetName = component.long_name;
      }
      // Check multiple types for city - Google returns different types depending on the address
      // Priority: locality > sublocality > sublocality_level_1 > neighborhood
      if (!city && types.includes('locality')) {
        city = component.long_name;
      }
      if (!city && types.includes('sublocality')) {
        city = component.long_name;
      }
      if (!city && types.includes('sublocality_level_1')) {
        city = component.long_name;
      }
      if (!city && types.includes('neighborhood')) {
        city = component.long_name;
      }
      if (types.includes('administrative_area_level_1')) {
        state = component.short_name; // Use abbreviation (e.g., "CA" not "California")
      }
      if (types.includes('postal_code')) {
        zipCode = component.short_name;
      }
    });

    // Update form values
    if (city) setValue('venueCity', city, { shouldValidate: true });
    if (state) setValue('venueState', state, { shouldValidate: true });
    if (zipCode) setValue('venueZipcode', zipCode, { shouldValidate: true });

    // Get coordinates
    if (place.geometry?.location) {
      const lat = place.geometry.location.lat();
      const lng = place.geometry.location.lng();
      const coordinates: VenueCoordinates = { lat, lng };

      setValue('venueCoordinates', coordinates);

      // Notify parent
      if (onVenueGeocoded) {
        onVenueGeocoded(coordinates, place.formatted_address);
      }

      // Calculate travel fee if station coordinates available

      if (stationCoordinates && showTravelFeePreview) {
        setIsCalculatingDistance(true);
        try {
          const distance = calculateDistanceMiles(
            stationCoordinates.lat,
            stationCoordinates.lng,
            lat,
            lng,
          );
          const result = calculateTravelFee(distance);

          handleTravelFeeResult(result);
        } finally {
          setIsCalculatingDistance(false);
        }
      } else {
        console.warn('[VenueAddressSection] Cannot calculate travel fee:', {
          hasStationCoordinates: !!stationCoordinates,
          showTravelFeePreview,
        });
      }
    }
  }, [
    setValue,
    stationCoordinates,
    showTravelFeePreview,
    calculateDistanceMiles,
    calculateTravelFee,
    onVenueGeocoded,
    handleTravelFeeResult,
  ]);

  /**
   * Initialize Google Places Autocomplete
   */
  useEffect(() => {
    const initializeAutocomplete = () => {
      if (!venueAddressInputRef.current || !window.google?.maps?.places) {
        return;
      }

      // Prevent double initialization
      if (autocompleteRef.current) {
        return;
      }

      autocompleteRef.current = new window.google.maps.places.Autocomplete(
        venueAddressInputRef.current,
        {
          types: ['address'],
          componentRestrictions: { country: 'us' },
          fields: ['formatted_address', 'address_components', 'geometry'],
        },
      );

      autocompleteRef.current.addListener('place_changed', handlePlaceSelect);
      setGoogleMapsLoaded(true);
    };

    // Check if Google Maps is already loaded
    if (window.google?.maps?.places) {
      initializeAutocomplete();
      return;
    }

    // Load Google Maps script
    const existingScript = document.querySelector('script[src*="maps.googleapis.com/maps/api/js"]');

    if (existingScript) {
      // Script exists, wait for it to load
      existingScript.addEventListener('load', initializeAutocomplete);
      return;
    }

    // Load new script
    const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;
    if (!apiKey) {
      console.warn('Google Maps API key not found');
      return;
    }

    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places`;
    script.async = true;
    script.defer = true;
    script.onload = initializeAutocomplete;
    document.head.appendChild(script);

    return () => {
      // Cleanup
      if (autocompleteRef.current && window.google?.maps?.event) {
        window.google.maps.event.clearInstanceListeners(autocompleteRef.current);
      }
    };
  }, [handlePlaceSelect]);

  // US States for dropdown
  const US_STATES = [
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

  return (
    <div className={`rounded-xl border border-gray-200 bg-white p-6 shadow-sm ${className}`}>
      {/* Section Header */}
      <div className="mb-4 flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-900">
          <MapPin className="h-5 w-5 text-red-500" />
          Event Venue
        </h2>
        {showCompletionBadge && (
          <div className="text-xs">
            {isComplete ? (
              <span className="rounded-full bg-green-100 px-2 py-0.5 font-semibold text-green-800">
                ✅ Complete
              </span>
            ) : (
              <span className="rounded-full bg-amber-100 px-2 py-0.5 text-amber-800">
                ⏳ Pending
              </span>
            )}
          </div>
        )}
      </div>

      <p className="mb-4 text-sm text-gray-600">
        Where will your hibachi party be? We need this to calculate travel and check chef
        availability.
      </p>

      {/* Google Places Autocomplete Search */}
      <div className="mb-4">
        <label htmlFor="venueStreet" className="mb-1.5 block text-sm font-semibold text-gray-700">
          <span className="flex items-center gap-2">
            <Navigation className="h-4 w-4 text-gray-400" />
            Search Address
            <span className="text-red-500">*</span>
          </span>
        </label>
        <div className="relative">
          <Controller
            name="venueStreet"
            control={control}
            rules={{ required: 'Please enter your venue address' }}
            render={({ field }) => (
              <input
                {...field}
                ref={(e) => {
                  field.ref(e);
                  venueAddressInputRef.current = e;
                }}
                id="venueStreet"
                type="text"
                placeholder={
                  googleMapsLoaded ? 'Start typing your address...' : 'Loading address search...'
                }
                className={`w-full rounded-lg border-2 px-4 py-3 pr-10 transition-all duration-200 focus:ring-2 focus:ring-offset-1 focus:outline-none ${
                  errors.venueStreet
                    ? 'border-red-300 bg-red-50 focus:border-red-500 focus:ring-red-200'
                    : 'border-gray-200 hover:border-gray-300 focus:border-red-500 focus:ring-red-200'
                }`}
                autoComplete="off"
              />
            )}
          />
          <MapPin className="absolute top-1/2 right-3 h-5 w-5 -translate-y-1/2 text-gray-400" />
        </div>
        {errors.venueStreet && (
          <p className="mt-1 flex items-center gap-1 text-sm text-red-600">
            <AlertCircle className="h-4 w-4" />
            {(errors.venueStreet as { message?: string })?.message || 'Invalid address'}
          </p>
        )}
      </div>

      {/* City, State, ZIP fields */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {/* City - using Controller for controlled input so setValue updates display */}
        <div className="flex flex-col space-y-1.5">
          <label htmlFor="venueCity" className="text-sm font-semibold text-gray-700">
            City <span className="text-red-500">*</span>
          </label>
          <Controller
            name="venueCity"
            control={control}
            rules={{ required: 'City is required' }}
            render={({ field }) => (
              <input
                {...field}
                id="venueCity"
                type="text"
                placeholder="City"
                autoComplete="address-level2"
                className={`w-full rounded-lg border-2 px-4 py-3 transition-all duration-200 focus:ring-2 focus:ring-offset-1 focus:outline-none ${
                  errors.venueCity
                    ? 'border-red-300 bg-red-50 focus:border-red-500 focus:ring-red-200'
                    : 'border-gray-200 hover:border-gray-300 focus:border-red-500 focus:ring-red-200'
                }`}
              />
            )}
          />
          {errors.venueCity && (
            <p className="flex items-center gap-1 text-sm text-red-600">
              <AlertCircle className="h-4 w-4" />
              {(errors.venueCity as { message?: string })?.message || 'City is required'}
            </p>
          )}
        </div>

        {/* State */}
        <div className="flex flex-col space-y-1.5">
          <label htmlFor="venueState" className="text-sm font-semibold text-gray-700">
            State <span className="text-red-500">*</span>
          </label>
          <Controller
            name="venueState"
            control={control}
            rules={{ required: 'State is required' }}
            render={({ field }) => (
              <select
                {...field}
                id="venueState"
                className={`w-full rounded-lg border-2 px-4 py-3 transition-all duration-200 focus:ring-2 focus:ring-offset-1 focus:outline-none ${
                  errors.venueState
                    ? 'border-red-300 bg-red-50 focus:border-red-500 focus:ring-red-200'
                    : 'border-gray-200 hover:border-gray-300 focus:border-red-500 focus:ring-red-200'
                }`}
              >
                <option value="">Select State</option>
                {US_STATES.map((state) => (
                  <option key={state} value={state}>
                    {state}
                  </option>
                ))}
              </select>
            )}
          />
          {errors.venueState && (
            <p className="flex items-center gap-1 text-sm text-red-600">
              <AlertCircle className="h-4 w-4" />
              {(errors.venueState as { message?: string })?.message || 'State is required'}
            </p>
          )}
        </div>

        {/* ZIP Code - using Controller for controlled input so setValue updates display */}
        <div className="flex flex-col space-y-1.5">
          <label htmlFor="venueZipcode" className="text-sm font-semibold text-gray-700">
            ZIP Code <span className="text-red-500">*</span>
          </label>
          <Controller
            name="venueZipcode"
            control={control}
            rules={{
              required: 'ZIP code is required',
              pattern: {
                value: /^\d{5}(-\d{4})?$/,
                message: 'Please enter a valid ZIP code',
              },
            }}
            render={({ field }) => (
              <input
                {...field}
                id="venueZipcode"
                type="text"
                placeholder="12345"
                maxLength={10}
                autoComplete="postal-code"
                className={`w-full rounded-lg border-2 px-4 py-3 transition-all duration-200 focus:ring-2 focus:ring-offset-1 focus:outline-none ${
                  errors.venueZipcode
                    ? 'border-red-300 bg-red-50 focus:border-red-500 focus:ring-red-200'
                    : 'border-gray-200 hover:border-gray-300 focus:border-red-500 focus:ring-red-200'
                }`}
              />
            )}
          />
          {errors.venueZipcode && (
            <p className="flex items-center gap-1 text-sm text-red-600">
              <AlertCircle className="h-4 w-4" />
              {(errors.venueZipcode as { message?: string })?.message || 'ZIP code is required'}
            </p>
          )}
        </div>
      </div>

      {/* Travel Fee Preview */}
      {showTravelFeePreview && travelFeeResult && (
        <div className="mt-4 rounded-lg border border-gray-200 bg-gray-50 p-4">
          <div className="flex items-center gap-2 font-semibold text-gray-700">
            <DollarSign className="h-5 w-5 text-green-600" />
            Travel Fee Estimate
          </div>

          {travelFeeResult.isWithinServiceArea ? (
            <div className="mt-2 space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Distance:</span>
                <span className="font-medium">{travelFeeResult.distanceMiles} miles</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Free miles included:</span>
                <span className="font-medium text-green-600">
                  {travelFeeResult.freeMiles} miles
                </span>
              </div>
              {travelFeeResult.billableMiles > 0 ? (
                <>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Billable miles:</span>
                    <span className="font-medium">
                      {travelFeeResult.billableMiles} miles × ${travelFeeResult.perMileRate}
                    </span>
                  </div>
                  <div className="mt-2 flex justify-between border-t pt-2">
                    <span className="font-semibold text-gray-900">Travel Fee:</span>
                    <span className="font-bold text-red-600">
                      ${travelFeeResult.travelFee.toFixed(2)}
                    </span>
                  </div>
                </>
              ) : (
                <div className="mt-2 rounded-md bg-green-100 p-2 text-center text-sm font-semibold text-green-800">
                  ✨ Great news! Your location is within our FREE travel zone!
                </div>
              )}
            </div>
          ) : (
            <div className="mt-2 rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
              <strong>⚠️ Location Notice:</strong> Your venue is {travelFeeResult.distanceMiles}{' '}
              miles from our station. Our maximum service area is {maxServiceDistance} miles. Please
              contact us to discuss special arrangements.
            </div>
          )}
        </div>
      )}

      {/* Distance Calculation Loading */}
      {isCalculatingDistance && (
        <div className="mt-4 flex items-center gap-2 text-sm text-gray-500">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-gray-300 border-t-red-500" />
          Calculating travel distance...
        </div>
      )}
    </div>
  );
};

export default VenueAddressSection;
