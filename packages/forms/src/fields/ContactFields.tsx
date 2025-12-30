'use client';

import React from 'react';
import { User, Mail, Phone } from 'lucide-react';
import type { FieldErrors, UseFormRegister, Path, FieldValues } from 'react-hook-form';
import { formatPhoneNumber } from '../hooks/usePhoneFormat';
import type { FormLayout } from '../types';

/**
 * Props for ContactFields component
 */
export interface ContactFieldsProps<TFieldValues extends FieldValues = FieldValues> {
  /** react-hook-form register function */
  register: UseFormRegister<TFieldValues>;
  /** react-hook-form errors object */
  errors: FieldErrors<TFieldValues>;

  /** Prefix for field names (e.g., "billing" → "billingName") */
  fieldPrefix?: string;

  /** Which fields are required */
  required?: {
    name?: boolean;
    email?: boolean;
    phone?: boolean;
  };

  /** Layout variant */
  layout?: FormLayout;

  /** Show labels above inputs */
  showLabels?: boolean;

  /** Show icons in inputs */
  showIcons?: boolean;

  /** Custom placeholders */
  placeholders?: {
    name?: string;
    email?: string;
    phone?: string;
  };

  /** Callback when phone changes (for formatting) */
  onPhoneChange?: (formatted: string, raw: string) => void;

  /** Callback when email field loses focus */
  onEmailBlur?: (email: string) => void;

  /** Additional CSS class */
  className?: string;

  /** Disable all fields */
  disabled?: boolean;
}

/**
 * Reusable contact information fields (name, email, phone)
 *
 * @example
 * // Basic usage
 * <ContactFields register={register} errors={errors} />
 *
 * @example
 * // With prefix for billing
 * <ContactFields
 *   register={register}
 *   errors={errors}
 *   fieldPrefix="billing"
 * />
 *
 * @example
 * // With icons and custom placeholders
 * <ContactFields
 *   register={register}
 *   errors={errors}
 *   showIcons={true}
 *   placeholders={{
 *     name: "Your full name",
 *     email: "your@email.com",
 *     phone: "(555) 123-4567"
 *   }}
 * />
 */
export function ContactFields<TFieldValues extends FieldValues = FieldValues>({
  register,
  errors,
  fieldPrefix = '',
  required = { name: true, email: true, phone: true },
  layout = 'grid',
  showLabels = true,
  showIcons = false,
  placeholders = {},
  onPhoneChange,
  onEmailBlur,
  className = '',
  disabled = false,
}: ContactFieldsProps<TFieldValues>) {
  // Build field names with optional prefix
  const nameField = (fieldPrefix ? `${fieldPrefix}Name` : 'name') as Path<TFieldValues>;
  const emailField = (fieldPrefix ? `${fieldPrefix}Email` : 'email') as Path<TFieldValues>;
  const phoneField = (fieldPrefix ? `${fieldPrefix}Phone` : 'phone') as Path<TFieldValues>;

  // Get error for a field (handle nested errors)
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

  const nameError = getError(nameField);
  const emailError = getError(emailField);
  const phoneError = getError(phoneField);

  // Layout classes
  const containerClass = layout === 'grid'
    ? 'grid grid-cols-1 gap-4 md:grid-cols-2'
    : layout === 'inline'
      ? 'flex flex-wrap gap-4'
      : 'space-y-4';

  const handlePhoneInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatPhoneNumber(e.target.value);
    e.target.value = formatted;
    if (onPhoneChange) {
      onPhoneChange(formatted, formatted.replace(/\D/g, ''));
    }
  };

  return (
    <div className={`${containerClass} ${className}`}>
      {/* Name Field */}
      <div className={layout === 'grid' ? '' : 'flex-1 min-w-[200px]'}>
        <div className="form-group">
          {showLabels && (
            <label htmlFor={nameField} className="form-label">
              {showIcons && <User className="mr-1 inline-block h-4 w-4" />}
              Full Name
              {required.name && <span className="text-red-500 ml-1">*</span>}
            </label>
          )}
          <input
            type="text"
            id={nameField}
            className={`form-control ${nameError ? 'is-invalid' : ''}`}
            placeholder={placeholders.name || 'Enter your full name'}
            disabled={disabled}
            {...register(nameField, {
              required: required.name ? 'Name is required' : false,
              minLength: { value: 2, message: 'Name must be at least 2 characters' },
            })}
          />
          {nameError && (
            <div className="invalid-feedback">{nameError}</div>
          )}
        </div>
      </div>

      {/* Email Field */}
      <div className={layout === 'grid' ? '' : 'flex-1 min-w-[200px]'}>
        <div className="form-group">
          {showLabels && (
            <label htmlFor={emailField} className="form-label">
              {showIcons && <Mail className="mr-1 inline-block h-4 w-4" />}
              Email Address
              {required.email && <span className="text-red-500 ml-1">*</span>}
            </label>
          )}
          <input
            type="email"
            id={emailField}
            className={`form-control ${emailError ? 'is-invalid' : ''}`}
            placeholder={placeholders.email || 'your.email@example.com'}
            disabled={disabled}
            {...register(emailField, {
              required: required.email ? 'Email is required' : false,
              pattern: {
                value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                message: 'Invalid email address',
              },
            })}
            onBlur={(e) => onEmailBlur?.(e.target.value)}
          />
          {emailError && (
            <div className="invalid-feedback">{emailError}</div>
          )}
        </div>
      </div>

      {/* Phone Field - Full width in grid layout */}
      <div className={layout === 'grid' ? 'md:col-span-2' : 'flex-1 min-w-[200px]'}>
        <div className="form-group">
          {showLabels && (
            <label htmlFor={phoneField} className="form-label">
              {showIcons && <Phone className="mr-1 inline-block h-4 w-4" />}
              Phone Number
              {required.phone && <span className="text-red-500 ml-1">*</span>}
            </label>
          )}
          <input
            type="tel"
            id={phoneField}
            className={`form-control ${phoneError ? 'is-invalid' : ''}`}
            placeholder={placeholders.phone || '(555) 123-4567'}
            disabled={disabled}
            {...register(phoneField, {
              required: required.phone ? 'Phone number is required' : false,
              minLength: { value: 14, message: 'Please enter a complete phone number' },
            })}
            onInput={handlePhoneInput}
          />
          {phoneError && (
            <div className="invalid-feedback">{phoneError}</div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ContactFields;
