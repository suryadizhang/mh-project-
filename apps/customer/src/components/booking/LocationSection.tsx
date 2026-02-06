import './styles/LocationSection.module.css';

import React from 'react';
import { Control, Controller, FieldErrors, UseFormWatch } from 'react-hook-form';

import { BookingFormData, US_STATES } from '../../data/booking/types';

interface LocationSectionProps {
  control: Control<BookingFormData>;
  errors: FieldErrors<BookingFormData>;
  watch: UseFormWatch<BookingFormData>;
  className?: string;
}

const LocationSection: React.FC<LocationSectionProps> = ({
  control,
  errors,
  watch,
  className = '',
}) => {
  const sameAsVenue = watch('sameAsVenue');

  return (
    <div className={`location-section ${className}`}>
      <h3 className="mb-4 text-xl font-semibold">Event Location</h3>

      <div className="space-y-4">
        <div>
          <label htmlFor="venueStreet" className="mb-2 block text-sm font-medium text-gray-700">
            Street Address *
          </label>
          <Controller
            name="venueStreet"
            control={control}
            render={({ field }) => (
              <input
                {...field}
                id="venueStreet"
                type="text"
                autoComplete="off"
                className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:border-red-500 focus:ring-2 focus:ring-red-500"
                placeholder="Enter venue street address"
              />
            )}
          />
          {errors.venueStreet && (
            <p className="mt-1 text-sm text-red-500">{errors.venueStreet.message}</p>
          )}
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <div>
            <label htmlFor="venueCity" className="mb-2 block text-sm font-medium text-gray-700">
              City *
            </label>
            <Controller
              name="venueCity"
              control={control}
              render={({ field }) => (
                <input
                  {...field}
                  id="venueCity"
                  type="text"
                  autoComplete="off"
                  className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:border-red-500 focus:ring-2 focus:ring-red-500"
                  placeholder="City"
                />
              )}
            />
            {errors.venueCity && (
              <p className="mt-1 text-sm text-red-500">{errors.venueCity.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="venueState" className="mb-2 block text-sm font-medium text-gray-700">
              State *
            </label>
            <Controller
              name="venueState"
              control={control}
              render={({ field }) => (
                <select
                  {...field}
                  id="venueState"
                  autoComplete="off"
                  className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:border-red-500 focus:ring-2 focus:ring-red-500"
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
              <p className="mt-1 text-sm text-red-500">{errors.venueState.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="venueZipcode" className="mb-2 block text-sm font-medium text-gray-700">
              Zip Code *
            </label>
            <Controller
              name="venueZipcode"
              control={control}
              render={({ field }) => (
                <input
                  {...field}
                  id="venueZipcode"
                  type="text"
                  autoComplete="off"
                  className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:border-red-500 focus:ring-2 focus:ring-red-500"
                  placeholder="Zip Code"
                />
              )}
            />
            {errors.venueZipcode && (
              <p className="mt-1 text-sm text-red-500">{errors.venueZipcode.message}</p>
            )}
          </div>
        </div>

        <div className="mt-6 border-t pt-4">
          <div className="mb-4 flex items-center">
            <Controller
              name="sameAsVenue"
              control={control}
              render={({ field: { value, onChange } }) => (
                <input
                  id="sameAsVenue"
                  type="checkbox"
                  checked={value}
                  onChange={onChange}
                  className="h-4 w-4 rounded border-gray-300 text-red-600 focus:ring-red-500"
                />
              )}
            />
            <label htmlFor="sameAsVenue" className="ml-2 block text-sm text-gray-900">
              Billing address is the same as venue address
            </label>
          </div>

          {!sameAsVenue && (
            <div className="space-y-4">
              <h4 className="text-lg font-medium text-gray-900">Billing Address</h4>

              <div>
                <label
                  htmlFor="addressStreet"
                  className="mb-2 block text-sm font-medium text-gray-700"
                >
                  Street Address *
                </label>
                <Controller
                  name="addressStreet"
                  control={control}
                  render={({ field }) => (
                    <input
                      {...field}
                      id="addressStreet"
                      type="text"
                      autoComplete="billing street-address"
                      className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:border-red-500 focus:ring-2 focus:ring-red-500"
                      placeholder="Enter billing street address"
                    />
                  )}
                />
                {errors.addressStreet && (
                  <p className="mt-1 text-sm text-red-500">{errors.addressStreet.message}</p>
                )}
              </div>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                <div>
                  <label
                    htmlFor="addressCity"
                    className="mb-2 block text-sm font-medium text-gray-700"
                  >
                    City *
                  </label>
                  <Controller
                    name="addressCity"
                    control={control}
                    render={({ field }) => (
                      <input
                        {...field}
                        id="addressCity"
                        type="text"
                        autoComplete="billing address-level2"
                        className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:border-red-500 focus:ring-2 focus:ring-red-500"
                        placeholder="City"
                      />
                    )}
                  />
                  {errors.addressCity && (
                    <p className="mt-1 text-sm text-red-500">{errors.addressCity.message}</p>
                  )}
                </div>

                <div>
                  <label
                    htmlFor="addressState"
                    className="mb-2 block text-sm font-medium text-gray-700"
                  >
                    State *
                  </label>
                  <Controller
                    name="addressState"
                    control={control}
                    render={({ field }) => (
                      <select
                        {...field}
                        id="addressState"
                        autoComplete="billing address-level1"
                        className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:border-red-500 focus:ring-2 focus:ring-red-500"
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
                  {errors.addressState && (
                    <p className="mt-1 text-sm text-red-500">{errors.addressState.message}</p>
                  )}
                </div>

                <div>
                  <label
                    htmlFor="addressZipcode"
                    className="mb-2 block text-sm font-medium text-gray-700"
                  >
                    Zip Code *
                  </label>
                  <Controller
                    name="addressZipcode"
                    control={control}
                    render={({ field }) => (
                      <input
                        {...field}
                        id="addressZipcode"
                        type="text"
                        autoComplete="billing postal-code"
                        className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:border-red-500 focus:ring-2 focus:ring-red-500"
                        placeholder="Zip Code"
                      />
                    )}
                  />
                  {errors.addressZipcode && (
                    <p className="mt-1 text-sm text-red-500">{errors.addressZipcode.message}</p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LocationSection;
