'use client';

import React from 'react';
import { Users, CheckCircle, ArrowRight } from 'lucide-react';
import { BookingFormData, BaseStepProps, StepVariant } from './types';

interface PartySizeStepProps extends BaseStepProps<BookingFormData> {
  onBack: () => void;
  // Previous steps summary data
  contactName: string;
  contactEmail: string;
  venueStreet?: string;
  venueCity?: string;
  venueState?: string;
  venueZipcode?: string;
  guestCount: number | undefined;
  // Navigation callbacks
  onEditContact: () => void;
  onEditVenue: () => void;
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
      label: 'block text-sm font-semibold text-gray-700 mb-2',
      errorText: 'text-sm text-red-600 mt-1',
      helpText: 'text-sm text-gray-500 mt-2',
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
    label: 'form-label required',
    errorText: 'invalid-feedback',
    helpText: 'text-muted',
    summaryBox: 'mb-4 rounded-lg border border-green-200 bg-green-50 p-3',
    summaryText: 'flex items-center gap-2 text-green-800',
    editButton: 'ml-auto text-sm text-green-600 hover:underline',
    backButton: 'inline-flex items-center gap-2 rounded-xl border border-gray-300 bg-white px-6 py-3 font-semibold text-gray-700 transition-all duration-200 hover:bg-gray-50',
    continueButton: 'inline-flex items-center gap-2 rounded-xl px-8 py-3 font-semibold text-white transition-all duration-300 bg-gradient-to-r from-red-600 to-red-700 hover:-translate-y-1 hover:from-red-700 hover:to-red-800 hover:shadow-lg',
    buttonDisabled: 'inline-flex items-center gap-2 rounded-xl px-8 py-3 font-semibold text-white bg-gray-400 cursor-not-allowed',
  };
};

/**
 * Step 3: Party Size
 * Collects number of guests for the hibachi event
 * Supports both 'booking' (Bootstrap) and 'quote' (Tailwind gradient) styling
 */
export function PartySizeStep({
  register,
  errors,
  onContinue,
  onBack,
  isValid,
  contactName,
  contactEmail,
  venueStreet,
  venueCity,
  venueState,
  venueZipcode,
  guestCount,
  onEditContact,
  onEditVenue,
  variant = 'booking',
}: PartySizeStepProps) {
  const styles = getStyles(variant);

  return (
    <div className={styles.container}>
      {/* Show previous steps summary */}
      <div className="mb-4 space-y-2">
        <div className={styles.summaryBox}>
          <div className={styles.summaryText}>
            <CheckCircle className="h-5 w-5" />
            <span className="font-medium">Contact:</span>
            <span>{contactName} • {contactEmail}</span>
            <button
              type="button"
              className={styles.editButton}
              onClick={onEditContact}
            >
              Edit
            </button>
          </div>
        </div>
        <div className={styles.summaryBox}>
          <div className={styles.summaryText}>
            <CheckCircle className="h-5 w-5" />
            <span className="font-medium">Venue:</span>
            <span>{venueStreet}, {venueCity}, {venueState} {venueZipcode}</span>
            <button
              type="button"
              className={styles.editButton}
              onClick={onEditVenue}
            >
              Edit
            </button>
          </div>
        </div>
      </div>

      <div className={styles.section}>
        <h3 className={styles.title}>
          <Users className="mr-2 h-5 w-5" />
          Party Size
        </h3>
        <p className={styles.description}>
          How many guests will be at your hibachi event?
        </p>

        <div className={variant === 'booking' ? 'form-group' : ''}>
          <label htmlFor="guestCount" className={styles.label}>
            Number of Guests
          </label>
          <input
            type="number"
            id="guestCount"
            min="1"
            max="50"
            className={errors.guestCount ? styles.inputError : styles.input}
            {...register('guestCount', {
              required: 'Guest count is required',
              min: { value: 1, message: 'At least 1 guest required' },
              max: { value: 50, message: 'Maximum 50 guests allowed' },
            })}
            placeholder="e.g., 10"
          />
          {errors.guestCount && (
            <div className={styles.errorText}>{errors.guestCount.message}</div>
          )}
          <small className={styles.helpText}>
            This helps us assign the right chef and calculate your quote.
          </small>
        </div>
      </div>

      {/* Step 3 Navigation */}
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
          Continue to Date & Time
          <ArrowRight className="h-5 w-5" />
        </button>
      </div>
    </div>
  );
}
