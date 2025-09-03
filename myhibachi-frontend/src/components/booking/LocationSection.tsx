import React from 'react'
import { Controller, Control, FieldErrors, UseFormWatch } from 'react-hook-form'
import { BookingFormData } from '../../data/booking/types'
import { US_STATES } from '../../data/booking/types'
import './styles/LocationSection.module.css'

interface LocationSectionProps {
  control: Control<BookingFormData>
  errors: FieldErrors<BookingFormData>
  watch: UseFormWatch<BookingFormData>
  className?: string
}

const LocationSection: React.FC<LocationSectionProps> = ({
  control,
  errors,
  watch,
  className = ''
}) => {
  const sameAsVenue = watch('sameAsVenue')

  return (
    <div className={`location-section ${className}`}>
      <h3 className="text-xl font-semibold mb-4">Event Location</h3>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Street Address *</label>
          <Controller
            name="venueStreet"
            control={control}
            render={({ field }) => (
              <input
                {...field}
                type="text"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                placeholder="Enter venue street address"
              />
            )}
          />
          {errors.venueStreet && (
            <p className="text-red-500 text-sm mt-1">{errors.venueStreet.message}</p>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">City *</label>
            <Controller
              name="venueCity"
              control={control}
              render={({ field }) => (
                <input
                  {...field}
                  type="text"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                  placeholder="City"
                />
              )}
            />
            {errors.venueCity && (
              <p className="text-red-500 text-sm mt-1">{errors.venueCity.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">State *</label>
            <Controller
              name="venueState"
              control={control}
              render={({ field }) => (
                <select
                  {...field}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                >
                  <option value="">Select State</option>
                  {US_STATES.map(state => (
                    <option key={state} value={state}>
                      {state}
                    </option>
                  ))}
                </select>
              )}
            />
            {errors.venueState && (
              <p className="text-red-500 text-sm mt-1">{errors.venueState.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Zip Code *</label>
            <Controller
              name="venueZipcode"
              control={control}
              render={({ field }) => (
                <input
                  {...field}
                  type="text"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                  placeholder="Zip Code"
                />
              )}
            />
            {errors.venueZipcode && (
              <p className="text-red-500 text-sm mt-1">{errors.venueZipcode.message}</p>
            )}
          </div>
        </div>

        <div className="border-t pt-4 mt-6">
          <div className="flex items-center mb-4">
            <Controller
              name="sameAsVenue"
              control={control}
              render={({ field: { value, onChange } }) => (
                <input
                  id="sameAsVenue"
                  type="checkbox"
                  checked={value}
                  onChange={onChange}
                  className="h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300 rounded"
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
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Street Address *
                </label>
                <Controller
                  name="addressStreet"
                  control={control}
                  render={({ field }) => (
                    <input
                      {...field}
                      type="text"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                      placeholder="Enter billing street address"
                    />
                  )}
                />
                {errors.addressStreet && (
                  <p className="text-red-500 text-sm mt-1">{errors.addressStreet.message}</p>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">City *</label>
                  <Controller
                    name="addressCity"
                    control={control}
                    render={({ field }) => (
                      <input
                        {...field}
                        type="text"
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                        placeholder="City"
                      />
                    )}
                  />
                  {errors.addressCity && (
                    <p className="text-red-500 text-sm mt-1">{errors.addressCity.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">State *</label>
                  <Controller
                    name="addressState"
                    control={control}
                    render={({ field }) => (
                      <select
                        {...field}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                      >
                        <option value="">Select State</option>
                        {US_STATES.map(state => (
                          <option key={state} value={state}>
                            {state}
                          </option>
                        ))}
                      </select>
                    )}
                  />
                  {errors.addressState && (
                    <p className="text-red-500 text-sm mt-1">{errors.addressState.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Zip Code *</label>
                  <Controller
                    name="addressZipcode"
                    control={control}
                    render={({ field }) => (
                      <input
                        {...field}
                        type="text"
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                        placeholder="Zip Code"
                      />
                    )}
                  />
                  {errors.addressZipcode && (
                    <p className="text-red-500 text-sm mt-1">{errors.addressZipcode.message}</p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default LocationSection
