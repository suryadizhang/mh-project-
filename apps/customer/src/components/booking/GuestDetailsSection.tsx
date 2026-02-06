import './styles/GuestDetailsSection.module.css';

import React from 'react';
import { Control, Controller, FieldErrors } from 'react-hook-form';

import { BookingFormData } from '../../data/booking/types';

interface GuestDetailsSectionProps {
  control: Control<BookingFormData>;
  errors: FieldErrors<BookingFormData>;
  className?: string;
}

const GuestDetailsSection: React.FC<GuestDetailsSectionProps> = ({
  control,
  errors,
  className = '',
}) => {
  return (
    <div className={`guest-details-section ${className}`}>
      <h3 className="mb-4 text-xl font-semibold">Guest Information</h3>

      <div className="space-y-4">
        <div>
          <label className="mb-2 block text-sm font-medium text-gray-700">Full Name *</label>
          <Controller
            name="name"
            control={control}
            render={({ field }) => (
              <input
                {...field}
                type="text"
                className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:border-red-500 focus:ring-2 focus:ring-red-500"
                placeholder="Enter your full name"
              />
            )}
          />
          {errors.name && <p className="mt-1 text-sm text-red-500">{errors.name.message}</p>}
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-gray-700">Email Address *</label>
          <Controller
            name="email"
            control={control}
            render={({ field }) => (
              <input
                {...field}
                type="email"
                className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:border-red-500 focus:ring-2 focus:ring-red-500"
                placeholder="Enter your email"
              />
            )}
          />
          {errors.email && <p className="mt-1 text-sm text-red-500">{errors.email.message}</p>}
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-gray-700">Phone Number *</label>
          <Controller
            name="phone"
            control={control}
            render={({ field }) => (
              <input
                {...field}
                type="tel"
                className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:border-red-500 focus:ring-2 focus:ring-red-500"
                placeholder="Enter your phone number"
              />
            )}
          />
          {errors.phone && <p className="mt-1 text-sm text-red-500">{errors.phone.message}</p>}
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-gray-700">
            Preferred Communication Method *
          </label>
          <Controller
            name="preferredCommunication"
            control={control}
            render={({ field }) => (
              <select
                {...field}
                className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:border-red-500 focus:ring-2 focus:ring-red-500"
              >
                <option value="">Select how we should contact you</option>
                <option value="phone">📞 Phone Call</option>
                <option value="text">💬 Text Message</option>
                <option value="email">📧 Email</option>
              </select>
            )}
          />
          {errors.preferredCommunication && (
            <p className="mt-1 text-sm text-red-500">{errors.preferredCommunication.message}</p>
          )}
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-gray-700">Number of Guests</label>
          <Controller
            name="guestCount"
            control={control}
            render={({ field }) => (
              <input
                {...field}
                type="number"
                min="1"
                max="50"
                className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:border-red-500 focus:ring-2 focus:ring-red-500"
                placeholder="How many guests?"
              />
            )}
          />
          {errors.guestCount && (
            <p className="mt-1 text-sm text-red-500">{errors.guestCount.message}</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default GuestDetailsSection;
