'use client';

import React from 'react';
import { MapPin, CheckCircle, RefreshCw, AlertTriangle, ArrowRight } from 'lucide-react';
import { BookingFormData, BaseStepProps, StepVariant, VenueCoordinates } from './types';

interface VenueAddressStepProps extends BaseStepProps<BookingFormData> {
  onBack: () => void;
  // Contact info for summary display
  contactName: string;
  contactEmail: string;
  // Geocoding state
  isGeocodingVenue?: boolean;
  venueCoordinates?: VenueCoordinates | null;
  geocodingError?: string | null;
}

/**
 * Style configuration for different variants
 */
const getStyles = (variant: StepVariant = 'booking') => {
  if (variant === 'quote') {
    return {
      container: 'animate-in fade-in slide-in-from-right-4 duration-300',
      section: 'mb-6',
      title: 'text-xl font-bold text-gray-900 inline-flex items-center mb-4',
      description: 'text-gray-600 mb-6',
      input: 'w-full px-4 py-3 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all',
      inputError: 'w-full px-4 py-3 bg-white border border-red-300 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all',
      select: 'w-full px-4 py-3 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all',
      selectError: 'w-full px-4 py-3 bg-white border border-red-300 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all',
      label: 'block text-sm font-semibold text-gray-700 mb-2',
      errorText: 'text-sm text-red-600 mt-1',
      summaryBox: 'mb-4 rounded-xl border border-green-200 bg-green-50 p-4',
      summaryText: 'flex items-center gap-2 text-green-800',
      editButton: 'ml-auto text-sm text-green-600 hover:underline',
      backButton: 'inline-flex items-center gap-2 rounded-xl border border-gray-300 bg-white px-6 py-3 font-semibold text-gray-700 transition-all duration-200 hover:bg-gray-50',
      continueButton: 'inline-flex items-center gap-2 rounded-xl px-8 py-3 font-semibold text-white transition-all duration-300 bg-gradient-to-r from-red-600 to-red-700 hover:-translate-y-1 hover:from-red-700 hover:to-red-800 hover:shadow-lg',
      buttonDisabled: 'inline-flex items-center gap-2 rounded-xl px-8 py-3 font-semibold text-white bg-gray-400 cursor-not-allowed',
    };
  }

  // Default 'booking' variant (Bootstrap-style)
  return {
    container: 'animate-in fade-in slide-in-from-right-4 duration-300',
    section: 'form-section',
    title: 'section-title inline-flex items-center',
    description: 'section-description',
    input: 'form-control',
    inputError: 'form-control is-invalid',
    select: 'form-control',
    selectError: 'form-control is-invalid',
    label: 'form-label required',
    errorText: 'invalid-feedback',
    summaryBox: 'mb-4 rounded-lg border border-green-200 bg-green-50 p-3',
    summaryText: 'flex items-center gap-2 text-green-800',
    editButton: 'ml-auto text-sm text-green-600 hover:underline',
    backButton: 'inline-flex items-center gap-2 rounded-xl border border-gray-300 bg-white px-6 py-3 font-semibold text-gray-700 transition-all duration-200 hover:bg-gray-50',
    continueButton: 'inline-flex items-center gap-2 rounded-xl px-8 py-3 font-semibold text-white transition-all duration-300 bg-gradient-to-r from-red-600 to-red-700 hover:-translate-y-1 hover:from-red-700 hover:to-red-800 hover:shadow-lg',
    buttonDisabled: 'inline-flex items-center gap-2 rounded-xl px-8 py-3 font-semibold text-white bg-gray-400 cursor-not-allowed',
  };
};

/**
 * Step 2: Venue Address
 * Collects event venue address with geocoding verification
 * Supports both 'booking' (Bootstrap) and 'quote' (Tailwind gradient) styling
 */
export function VenueAddressStep({
  register,
  errors,
  onContinue,
  onBack,
  isValid,
  contactName,
  contactEmail,
  isGeocodingVenue = false,
  venueCoordinates = null,
  geocodingError = null,
  variant = 'booking',
}: VenueAddressStepProps) {
  const styles = getStyles(variant);

  return (
    <div className={styles.container}>
      {/* Show contact summary */}
      <div className={styles.summaryBox}>
        <div className={styles.summaryText}>
          <CheckCircle className="h-5 w-5" />
          <span className="font-medium">Contact:</span>
          <span>{contactName} • {contactEmail}</span>
          <button
            type="button"
            className={styles.editButton}
            onClick={onBack}
          >
            Edit
          </button>
        </div>
      </div>

      <div className={styles.section}>
        <h3 className={styles.title}>
          <MapPin className="mr-2 h-5 w-5" />
          Event Venue Address
          {isGeocodingVenue && (
            <span className="ml-2 animate-pulse text-sm text-gray-500">
              <RefreshCw className="mr-1 inline h-4 w-4 animate-spin" />
              Verifying...
            </span>
          )}
          {venueCoordinates && !isGeocodingVenue && (
            <span className="ml-2 text-sm text-green-600">
              <CheckCircle className="mr-1 inline h-4 w-4" />
              Verified
            </span>
          )}
        </h3>
        <p className={styles.description}>
          Tell us where your hibachi event will be held.
          {venueCoordinates && (
            <span className="ml-2 text-green-600">
              ✓ We&apos;ll check chef availability in your area.
            </span>
          )}
        </p>
        {geocodingError && (
          <div className="mt-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            <AlertTriangle className="mr-1 inline h-4 w-4" />
            {geocodingError}
          </div>
        )}

        <div className={variant === 'booking' ? 'row' : ''}>
          <div className={variant === 'booking' ? 'col-12' : ''}>
            <div className={variant === 'booking' ? 'form-group' : 'mb-6'}>
              <label htmlFor="venueStreet" className={styles.label}>
                Street Address
              </label>
              <input
                type="text"
                id="venueStreet"
                className={errors.venueStreet ? styles.inputError : styles.input}
                {...register('venueStreet', {
                  required: 'Venue street address is required',
                })}
                placeholder="123 Main Street, Apt 2B"
              />
              {errors.venueStreet && (
                <div className={styles.errorText}>{errors.venueStreet.message}</div>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-6">
          <div className="md:col-span-3">
            <div className={variant === 'booking' ? 'form-group' : ''}>
              <label htmlFor="venueCity" className={styles.label}>
                City
              </label>
              <input
                type="text"
                id="venueCity"
                className={errors.venueCity ? styles.inputError : styles.input}
                {...register('venueCity', { required: 'Venue city is required' })}
                placeholder="San Francisco"
              />
              {errors.venueCity && (
                <div className={styles.errorText}>{errors.venueCity.message}</div>
              )}
            </div>
          </div>

          <div className="md:col-span-1">
            <div className={variant === 'booking' ? 'form-group' : ''}>
              <label htmlFor="venueState" className={styles.label}>
                State
              </label>
              <select
                id="venueState"
                className={errors.venueState ? styles.selectError : styles.select}
                {...register('venueState', { required: 'Venue state is required' })}
              >
                <option value="">Select</option>
                <option value="CA">CA</option>
                <option value="NV">NV</option>
                <option value="OR">OR</option>
                <option value="WA">WA</option>
              </select>
              {errors.venueState && (
                <div className={styles.errorText}>{errors.venueState.message}</div>
              )}
            </div>
          </div>

          <div className="md:col-span-2">
            <div className={variant === 'booking' ? 'form-group' : ''}>
              <label htmlFor="venueZipcode" className={styles.label}>
                ZIP Code
              </label>
              <input
                type="text"
                id="venueZipcode"
                className={errors.venueZipcode ? styles.inputError : styles.input}
                {...register('venueZipcode', {
                  required: 'Venue ZIP code is required',
                })}
                placeholder="94102"
              />
              {errors.venueZipcode && (
                <div className={styles.errorText}>{errors.venueZipcode.message}</div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Step 2 Navigation */}
      <div className="mt-6 flex justify-between">
        <button
          type="button"
          onClick={onBack}
          className={styles.backButton}
        >
          Back
        </button>
        <button
          type="button"
          disabled={!isValid}
          onClick={onContinue}
          className={isValid ? styles.continueButton : styles.buttonDisabled}
        >
          Continue to Party Size
          <ArrowRight className="h-5 w-5" />
        </button>
      </div>
    </div>
  );
}
