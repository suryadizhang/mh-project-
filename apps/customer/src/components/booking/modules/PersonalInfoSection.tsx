'use client';

import { AlertCircle, Mail, Phone, User, MessageSquare } from 'lucide-react';
import React from 'react';
import {
  Control,
  Controller,
  FieldErrors,
  UseFormRegister,
  UseFormSetValue,
  UseFormWatch,
} from 'react-hook-form';

import { SMSConsentCheckbox } from '@/components/ui/SMSConsentCheckbox';

/**
 * Communication preference type
 */
export type CommunicationPreference = 'phone' | 'text' | 'email';

/**
 * Personal Info form data structure
 * This can be extended by the parent form
 */
export interface PersonalInfoFormData {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  preferredCommunication: CommunicationPreference;
  smsConsent: boolean;
}

// Use 'any' to allow parent forms with additional fields to pass their control/register
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export interface PersonalInfoSectionProps {
  register: UseFormRegister<any>;
  control: Control<any>;
  errors: FieldErrors<PersonalInfoFormData>;
  watch: UseFormWatch<any>;
  setValue: UseFormSetValue<any>;
  className?: string;
  showCompletionBadge?: boolean;
}

/**
 * PersonalInfoSection - Reusable personal information form section
 *
 * Features:
 * - Name, email, phone inputs with validation
 * - Preferred communication method selector
 * - SMS consent with TCR/carrier compliance
 * - Completion status badge
 */
export const PersonalInfoSection: React.FC<PersonalInfoSectionProps> = ({
  register,
  control,
  errors,
  watch,
  setValue,
  className = '',
  showCompletionBadge = true,
}) => {
  // Check if section is complete
  const isComplete = Boolean(
    watch('firstName') &&
      watch('lastName') &&
      watch('email') &&
      watch('phone') &&
      watch('preferredCommunication'),
  );

  return (
    <div className={`rounded-xl border border-gray-200 bg-white p-6 shadow-sm ${className}`}>
      {/* Section Header */}
      <div className="mb-4 flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-900">
          <User className="h-5 w-5 text-red-500" />
          Personal Information
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

      {/* Form Fields */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {/* First Name */}
        <div className="flex flex-col space-y-1.5">
          <label
            htmlFor="firstName"
            className="flex items-center gap-2 text-sm font-semibold text-gray-700"
          >
            <User className="h-4 w-4 text-gray-400" />
            First Name
            <span className="text-red-500">*</span>
          </label>
          <input
            id="firstName"
            type="text"
            {...register('firstName', {
              required: 'Please enter your first name',
              minLength: { value: 2, message: 'First name must be at least 2 characters' },
            })}
            placeholder="John"
            className={`w-full rounded-lg border-2 px-4 py-3 transition-all duration-200 focus:ring-2 focus:ring-offset-1 focus:outline-none ${
              errors.firstName
                ? 'border-red-300 bg-red-50 focus:border-red-500 focus:ring-red-200'
                : 'border-gray-200 hover:border-gray-300 focus:border-red-500 focus:ring-red-200'
            }`}
          />
          {errors.firstName && (
            <p className="flex items-center gap-1 text-sm text-red-600">
              <AlertCircle className="h-4 w-4" />
              {errors.firstName.message}
            </p>
          )}
        </div>

        {/* Last Name */}
        <div className="flex flex-col space-y-1.5">
          <label
            htmlFor="lastName"
            className="flex items-center gap-2 text-sm font-semibold text-gray-700"
          >
            <User className="h-4 w-4 text-gray-400" />
            Last Name
            <span className="text-red-500">*</span>
          </label>
          <input
            id="lastName"
            type="text"
            {...register('lastName', {
              required: 'Please enter your last name',
              minLength: { value: 2, message: 'Last name must be at least 2 characters' },
            })}
            placeholder="Smith"
            className={`w-full rounded-lg border-2 px-4 py-3 transition-all duration-200 focus:ring-2 focus:ring-offset-1 focus:outline-none ${
              errors.lastName
                ? 'border-red-300 bg-red-50 focus:border-red-500 focus:ring-red-200'
                : 'border-gray-200 hover:border-gray-300 focus:border-red-500 focus:ring-red-200'
            }`}
          />
          {errors.lastName && (
            <p className="flex items-center gap-1 text-sm text-red-600">
              <AlertCircle className="h-4 w-4" />
              {errors.lastName.message}
            </p>
          )}
        </div>

        {/* Email */}
        <div className="flex flex-col space-y-1.5">
          <label
            htmlFor="email"
            className="flex items-center gap-2 text-sm font-semibold text-gray-700"
          >
            <Mail className="h-4 w-4 text-gray-400" />
            Email Address
            <span className="text-red-500">*</span>
          </label>
          <input
            id="email"
            type="email"
            {...register('email', {
              required: 'Please enter your email',
              pattern: {
                value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                message: 'Please enter a valid email address',
              },
            })}
            placeholder="john@example.com"
            className={`w-full rounded-lg border-2 px-4 py-3 transition-all duration-200 focus:ring-2 focus:ring-offset-1 focus:outline-none ${
              errors.email
                ? 'border-red-300 bg-red-50 focus:border-red-500 focus:ring-red-200'
                : 'border-gray-200 hover:border-gray-300 focus:border-red-500 focus:ring-red-200'
            }`}
          />
          {errors.email && (
            <p className="flex items-center gap-1 text-sm text-red-600">
              <AlertCircle className="h-4 w-4" />
              {errors.email.message}
            </p>
          )}
        </div>

        {/* Phone */}
        <div className="flex flex-col space-y-1.5">
          <label
            htmlFor="phone"
            className="flex items-center gap-2 text-sm font-semibold text-gray-700"
          >
            <Phone className="h-4 w-4 text-gray-400" />
            Phone Number
            <span className="text-red-500">*</span>
          </label>
          <input
            id="phone"
            type="tel"
            {...register('phone', {
              required: 'Please enter your phone number',
              validate: (value) => {
                const digitsOnly = value.replace(/\D/g, '');
                if (digitsOnly.length < 10) return 'Phone number must have at least 10 digits';
                return true;
              },
            })}
            placeholder="(555) 123-4567"
            className={`w-full rounded-lg border-2 px-4 py-3 transition-all duration-200 focus:ring-2 focus:ring-offset-1 focus:outline-none ${
              errors.phone
                ? 'border-red-300 bg-red-50 focus:border-red-500 focus:ring-red-200'
                : 'border-gray-200 hover:border-gray-300 focus:border-red-500 focus:ring-red-200'
            }`}
          />
          {errors.phone ? (
            <p className="flex items-center gap-1 text-sm text-red-600">
              <AlertCircle className="h-4 w-4" />
              {errors.phone.message}
            </p>
          ) : (
            <p className="text-xs text-gray-500">
              We&apos;ll use this to contact you about your booking
            </p>
          )}
        </div>

        {/* Preferred Communication */}
        <div className="flex flex-col space-y-1.5">
          <label
            htmlFor="preferredCommunication"
            className="flex items-center gap-2 text-sm font-semibold text-gray-700"
          >
            <MessageSquare className="h-4 w-4 text-gray-400" />
            Preferred Communication
            <span className="text-red-500">*</span>
          </label>
          <Controller
            name="preferredCommunication"
            control={control}
            rules={{ required: 'Please select how you prefer to be contacted' }}
            render={({ field }) => (
              <select
                {...field}
                id="preferredCommunication"
                onChange={(e) => {
                  field.onChange(e);
                  // Auto-check SMS consent when "text" is selected
                  if (e.target.value === 'text') {
                    setValue('smsConsent', true);
                  }
                }}
                className={`w-full rounded-lg border-2 px-4 py-3 transition-all duration-200 focus:ring-2 focus:ring-offset-1 focus:outline-none ${
                  errors.preferredCommunication
                    ? 'border-red-300 bg-red-50 focus:border-red-500 focus:ring-red-200'
                    : 'border-gray-200 hover:border-gray-300 focus:border-red-500 focus:ring-red-200'
                }`}
              >
                <option value="">Select how we should contact you</option>
                <option value="phone">📞 Phone Call</option>
                <option value="text">💬 Text Message</option>
                <option value="email">📧 Email</option>
              </select>
            )}
          />
          {errors.preferredCommunication && (
            <p className="flex items-center gap-1 text-sm text-red-600">
              <AlertCircle className="h-4 w-4" />
              {errors.preferredCommunication.message}
            </p>
          )}
        </div>
      </div>

      {/* SMS Consent Section - TCR/Carrier Compliant */}
      <Controller
        name="smsConsent"
        control={control}
        render={({ field }) => (
          <SMSConsentCheckbox
            checked={field.value || false}
            onChange={field.onChange}
            variant="default"
            showFullDisclosure={true}
            id="booking-sms-consent"
          />
        )}
      />
    </div>
  );
};

export default PersonalInfoSection;
