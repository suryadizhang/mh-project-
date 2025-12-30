'use client';

import { AlertCircle, Mail, Phone, User, MessageSquare } from 'lucide-react';
import Link from 'next/link';
import React from 'react';
import { Control, Controller, FieldErrors, UseFormRegister, UseFormWatch } from 'react-hook-form';

import { useProtectedPhone, ProtectedEmail } from '@/components/ui/ProtectedPhone';

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
  className = '',
  showCompletionBadge = true,
}) => {
  // Anti-scraper protected contact info
  const { formatted: protectedPhone, tel: protectedTel } = useProtectedPhone();

  // Check if section is complete
  const isComplete = Boolean(
    watch('firstName') &&
    watch('lastName') &&
    watch('email') &&
    watch('phone') &&
    watch('preferredCommunication')
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
          <label htmlFor="firstName" className="flex items-center gap-2 text-sm font-semibold text-gray-700">
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
            className={`w-full rounded-lg border-2 px-4 py-3 transition-all duration-200 focus:ring-2 focus:ring-offset-1 focus:outline-none ${errors.firstName
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
          <label htmlFor="lastName" className="flex items-center gap-2 text-sm font-semibold text-gray-700">
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
            className={`w-full rounded-lg border-2 px-4 py-3 transition-all duration-200 focus:ring-2 focus:ring-offset-1 focus:outline-none ${errors.lastName
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
          <label htmlFor="email" className="flex items-center gap-2 text-sm font-semibold text-gray-700">
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
            className={`w-full rounded-lg border-2 px-4 py-3 transition-all duration-200 focus:ring-2 focus:ring-offset-1 focus:outline-none ${errors.email
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
          <label htmlFor="phone" className="flex items-center gap-2 text-sm font-semibold text-gray-700">
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
            className={`w-full rounded-lg border-2 px-4 py-3 transition-all duration-200 focus:ring-2 focus:ring-offset-1 focus:outline-none ${errors.phone
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
            <p className="text-xs text-gray-500">We&apos;ll use this to contact you about your booking</p>
          )}
        </div>

        {/* Preferred Communication */}
        <div className="flex flex-col space-y-1.5">
          <label htmlFor="preferredCommunication" className="flex items-center gap-2 text-sm font-semibold text-gray-700">
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
                className={`w-full rounded-lg border-2 px-4 py-3 transition-all duration-200 focus:ring-2 focus:ring-offset-1 focus:outline-none ${errors.preferredCommunication
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
      <div className="mt-6 rounded-lg border border-blue-200 bg-blue-50 p-4">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-blue-900">
            SMS Communication Consent
          </h3>
          <span className="rounded-full bg-blue-600 px-3 py-1 text-xs font-bold text-white">
            OPTIONAL
          </span>
        </div>
        <p className="mb-3 text-xs text-gray-600">
          Checking this box is not required to complete your booking.
        </p>

        <div className="mb-4 space-y-3">
          <div className="rounded-md border border-blue-300 bg-white p-3">
            <label className="flex cursor-pointer items-start space-x-3">
              <Controller
                name="smsConsent"
                control={control}
                render={({ field }) => (
                  <input
                    type="checkbox"
                    checked={field.value || false}
                    onChange={field.onChange}
                    className="mt-1 h-5 w-5 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500"
                    aria-describedby="sms-consent-description"
                  />
                )}
              />
              <div className="text-sm" id="sms-consent-description">
                <div className="font-medium text-gray-900">
                  Yes, I consent to receive SMS text messages from My Hibachi Chef
                </div>
                <div className="mt-2 text-gray-600">
                  <p className="mb-2 text-xs">
                    By checking this box, I agree to receive the following SMS messages:
                  </p>
                  <ul className="ml-4 list-disc space-y-1 text-xs">
                    <li>Booking confirmations and order details</li>
                    <li>Event reminders (48hrs and 24hrs before your event)</li>
                    <li>Chef updates and arrival notifications</li>
                    <li>Customer support conversations</li>
                    <li>Order alerts and booking changes</li>
                    <li>Account notifications (service-related only)</li>
                  </ul>
                </div>
                {/* TCR Required: Consent not required for purchase */}
                <p className="mt-3 text-xs font-semibold text-gray-500">
                  Consent is not required to make a purchase. You can still complete your
                  booking without checking this box.
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  SMS consent is not shared with third parties or affiliates.
                </p>
              </div>
            </label>
          </div>

          {/* Disclosure section */}
          <div className="space-y-1 text-xs text-gray-600">
            <p>
              <strong>Message Frequency:</strong> Varies based on your booking activity.
              Message and data rates may apply.
            </p>
            <p>
              <strong>Opt-out:</strong> Reply STOP to any message to unsubscribe. Reply
              START to re-subscribe. Reply HELP for support.
            </p>
            <p>
              <strong>Contact:</strong>{' '}
              <a
                href={protectedTel ? `tel:${protectedTel}` : '#'}
                className="text-blue-600 hover:underline"
              >
                {protectedPhone || 'Loading...'}
              </a>{' '}
              | <ProtectedEmail className="text-blue-600 hover:underline" />
            </p>
            <p>
              <strong>Policies:</strong>{' '}
              <Link href="/privacy" className="text-blue-600 hover:underline">
                Privacy Policy
              </Link>{' '}
              |{' '}
              <Link href="/terms#sms" className="text-blue-600 hover:underline">
                Terms & SMS Policy
              </Link>
            </p>
          </div>

          {/* What happens if not checked */}
          <div className="rounded-md bg-gray-100 p-3 text-xs text-gray-600">
            <strong>What happens if I don&apos;t check this box?</strong>
            <p className="mt-1">
              You can still complete your booking! You will still receive essential
              transactional SMS messages (booking confirmations, event reminders, chef
              arrival updates). However, you will not receive promotional offers or
              marketing messages. You can opt in later by texting START.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PersonalInfoSection;
