'use client';

import React from 'react';
import { User, ArrowRight, RefreshCw } from 'lucide-react';
import { BookingFormData, BaseStepProps, StepVariant } from './types';

interface ContactInfoStepProps extends BaseStepProps<BookingFormData> {
  isSubmittingLead?: boolean;
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
      input:
        'w-full px-4 py-3 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all',
      inputError:
        'w-full px-4 py-3 bg-white border border-red-300 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all',
      label: 'block text-sm font-semibold text-gray-700 mb-2',
      errorText: 'text-sm text-red-600 mt-1',
      button:
        'inline-flex items-center gap-2 rounded-xl px-8 py-3 font-semibold text-white transition-all duration-300 bg-gradient-to-r from-red-600 to-red-700 hover:-translate-y-1 hover:from-red-700 hover:to-red-800 hover:shadow-lg',
      buttonDisabled:
        'inline-flex items-center gap-2 rounded-xl px-8 py-3 font-semibold text-white bg-gray-400 cursor-not-allowed',
      grid: 'grid grid-cols-1 gap-6 md:grid-cols-2',
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
    button:
      'inline-flex items-center gap-2 rounded-xl px-8 py-3 font-semibold text-white transition-all duration-300 bg-gradient-to-r from-red-600 to-red-700 hover:-translate-y-1 hover:from-red-700 hover:to-red-800 hover:shadow-lg',
    buttonDisabled:
      'inline-flex items-center gap-2 rounded-xl px-8 py-3 font-semibold text-white bg-gray-400 cursor-not-allowed',
    grid: 'grid grid-cols-1 gap-4 md:grid-cols-2',
  };
};

/**
 * Step 1: Contact Information
 * Collects customer name, email, and phone number
 * Supports both 'booking' (Bootstrap) and 'quote' (Tailwind gradient) styling
 */
export function ContactInfoStep({
  register,
  errors,
  onContinue,
  isValid,
  isSubmittingLead = false,
  variant = 'booking',
}: ContactInfoStepProps) {
  const styles = getStyles(variant);

  return (
    <div className={styles.container}>
      <div className={styles.section}>
        <h3 className={styles.title}>
          <User className="mr-2 h-5 w-5" />
          Contact Information
        </h3>
        <p className={styles.description}>
          <strong>Let&apos;s start with your details!</strong> This helps us personalize your
          hibachi experience.
        </p>

        <div className={styles.grid}>
          <div>
            <div className={variant === 'booking' ? 'form-group' : ''}>
              <label htmlFor="name" className={styles.label}>
                Full Name
              </label>
              <input
                type="text"
                id="name"
                className={errors.name ? styles.inputError : styles.input}
                {...register('name', { required: 'Name is required' })}
                placeholder="Enter your full name"
              />
              {errors.name && <div className={styles.errorText}>{errors.name.message}</div>}
            </div>
          </div>

          <div>
            <div className={variant === 'booking' ? 'form-group' : ''}>
              <label htmlFor="email" className={styles.label}>
                Email Address
              </label>
              <input
                type="email"
                id="email"
                className={errors.email ? styles.inputError : styles.input}
                {...register('email', {
                  required: 'Email is required',
                  pattern: {
                    value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                    message: 'Invalid email address',
                  },
                })}
                placeholder="your.email@example.com"
              />
              {errors.email && <div className={styles.errorText}>{errors.email.message}</div>}
            </div>
          </div>
        </div>

        <div className={variant === 'booking' ? 'form-group' : 'mt-6'}>
          <label htmlFor="phone" className={styles.label}>
            Phone Number
          </label>
          <input
            type="tel"
            id="phone"
            className={errors.phone ? styles.inputError : styles.input}
            {...register('phone', { required: 'Phone number is required' })}
            placeholder="(555) 123-4567"
          />
          {errors.phone && <div className={styles.errorText}>{errors.phone.message}</div>}
        </div>
      </div>

      {/* Step 1 Navigation */}
      <div className="mt-6 flex justify-end">
        <button
          type="button"
          disabled={!isValid || isSubmittingLead}
          onClick={onContinue}
          className={isValid && !isSubmittingLead ? styles.button : styles.buttonDisabled}
        >
          {isSubmittingLead ? (
            <>
              <RefreshCw className="h-5 w-5 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              Continue to Venue
              <ArrowRight className="h-5 w-5" />
            </>
          )}
        </button>
      </div>
    </div>
  );
}
