'use client'

import React, { useState, useEffect } from 'react'
import { useForm, Controller, SubmitHandler, Resolver } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { format, addDays } from 'date-fns'
// import { FreeQuoteButton } from '@/components/quote/FreeQuoteButton' // Removed floating button

// Validation schema
const bookingSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Invalid email address'),
  phone: z.string().min(10, 'Phone must be at least 10 digits'),
  eventDate: z.date().refine((date) => {
    const minDate = addDays(new Date(), 2)
    return date >= minDate
  }, 'Event date must be at least 2 days in advance'),
  eventTime: z.enum(['12PM', '3PM', '6PM', '9PM']),
  addressStreet: z.string().min(1, 'Street address is required'),
  addressCity: z.string().min(1, 'City is required'),
  addressState: z.string().min(2, 'State is required'),
  addressZipcode: z.string().min(5, 'Zipcode must be at least 5 digits'),
  sameAsCustomer: z.boolean().default(false),
  venueStreet: z.string().optional(),
  venueCity: z.string().optional(),
  venueState: z.string().optional(),
  venueZipcode: z.string().optional(),
}).refine((data) => {
  if (!data.sameAsCustomer) {
    return data.venueStreet && data.venueCity && data.venueState && data.venueZipcode
  }
  return true
}, {
  message: 'Venue address is required when different from customer address',
  path: ['venueStreet']
})

type BookingFormData = z.infer<typeof bookingSchema>

const timeSlots = [
  { value: '12PM', label: '12:00 PM' },
  { value: '3PM', label: '3:00 PM' },
  { value: '6PM', label: '6:00 PM' },
  { value: '9PM', label: '9:00 PM' },
]

export default function BookingPage() {
  const [isCheckingAvailability, setIsCheckingAvailability] = useState(false)
  const [availabilityStatus, setAvailabilityStatus] = useState<{ [key: string]: boolean }>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitMessage, setSubmitMessage] = useState('')

  const {
    register,
    handleSubmit,
    watch,
    control,
    setValue,
    formState: { errors }
  } = useForm<BookingFormData>({
    resolver: zodResolver(bookingSchema) as Resolver<BookingFormData>,
    defaultValues: {
      sameAsCustomer: false
    }
  })

  const watchedFields = watch()
  const minDate = addDays(new Date(), 2) // 2 days minimum

  // Check availability when date or time changes
  useEffect(() => {
    const checkAvailability = async () => {
      if (watchedFields.eventDate && watchedFields.eventTime) {
        setIsCheckingAvailability(true)
        const dateStr = format(watchedFields.eventDate, 'yyyy-MM-dd')
        const key = `${dateStr}_${watchedFields.eventTime}`

        try {
          const response = await fetch(`http://localhost:8000/api/v1/bookings/check?date=${dateStr}&time=${watchedFields.eventTime}`)
          const data = await response.json()
          setAvailabilityStatus(prev => ({
            ...prev,
            [key]: data.available
          }))
        } catch (error) {
          console.error('Error checking availability:', error)
          setAvailabilityStatus(prev => ({
            ...prev,
            [key]: false
          }))
        } finally {
          setIsCheckingAvailability(false)
        }
      }
    }

    checkAvailability()
  }, [watchedFields.eventDate, watchedFields.eventTime])

  // Auto-fill venue address when "same as customer" is checked
  useEffect(() => {
    if (watchedFields.sameAsCustomer) {
      setValue('venueStreet', watchedFields.addressStreet)
      setValue('venueCity', watchedFields.addressCity)
      setValue('venueState', watchedFields.addressState)
      setValue('venueZipcode', watchedFields.addressZipcode)
    }
  }, [watchedFields.sameAsCustomer, watchedFields.addressStreet, watchedFields.addressCity, watchedFields.addressState, watchedFields.addressZipcode, setValue])

  const onSubmit: SubmitHandler<BookingFormData> = async (data) => {
    setIsSubmitting(true)
    setSubmitMessage('')

    try {
      const submitData = {
        name: data.name,
        email: data.email,
        phone: data.phone,
        event_date: format(data.eventDate, 'yyyy-MM-dd'),
        event_time: data.eventTime,
        address_street: data.addressStreet,
        address_city: data.addressCity,
        address_state: data.addressState,
        address_zipcode: data.addressZipcode,
        venue_street: data.sameAsCustomer ? data.addressStreet : data.venueStreet,
        venue_city: data.sameAsCustomer ? data.addressCity : data.venueCity,
        venue_state: data.sameAsCustomer ? data.addressState : data.venueState,
        venue_zipcode: data.sameAsCustomer ? data.addressZipcode : data.venueZipcode,
      }

      const response = await fetch('http://localhost:8000/api/v1/bookings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(submitData),
      })

      if (response.ok) {
        setSubmitMessage('Booking submitted successfully! We will contact you within 1-2 hours to confirm your hibachi experience.')
      } else {
        const error = await response.json()
        setSubmitMessage(`Error: ${error.detail || 'Failed to submit booking'}`)
      }
    } catch (error) {
      console.error('Submission error:', error)
      setSubmitMessage('Error: Failed to submit booking. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const getCurrentAvailability = () => {
    if (!watchedFields.eventDate || !watchedFields.eventTime) return null
    const dateStr = format(watchedFields.eventDate, 'yyyy-MM-dd')
    const key = `${dateStr}_${watchedFields.eventTime}`
    return availabilityStatus[key]
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-red-50 py-12">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            🍽️ Book Us
          </h1>
          <p className="text-xl text-gray-600">
            Reserve your premium hibachi chef service - available 7 days a week!
          </p>
          <div className="flex justify-center gap-4 mt-4 text-sm text-gray-500">
            <span>✅ Professional Chef</span>
            <span>✅ Fresh Ingredients</span>
            <span>✅ Entertainment Included</span>
          </div>
        </div>

        {/* Form */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
            {/* Customer Information */}
            <div className="border-b pb-6">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                📞 Customer Information
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Full Name *
                  </label>
                  <input
                    {...register('name')}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                    placeholder="Enter your full name"
                  />
                  {errors.name && (
                    <p className="text-red-500 text-sm mt-1">{errors.name.message}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email Address *
                  </label>
                  <input
                    {...register('email')}
                    type="email"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                    placeholder="your.email@example.com"
                  />
                  {errors.email && (
                    <p className="text-red-500 text-sm mt-1">{errors.email.message}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Phone Number *
                  </label>
                  <input
                    {...register('phone')}
                    type="tel"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                    placeholder="(555) 123-4567"
                  />
                  {errors.phone && (
                    <p className="text-red-500 text-sm mt-1">{errors.phone.message}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Booking Date & Time */}
            <div className="border-b pb-6">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                📅 Booking Date & Time
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Event Date * (minimum 2 days advance)
                  </label>
                  <Controller
                    name="eventDate"
                    control={control}
                    render={({ field }) => (
                      <input
                        {...field}
                        type="date"
                        min={format(minDate, 'yyyy-MM-dd')}
                        value={field.value ? format(field.value, 'yyyy-MM-dd') : ''}
                        onChange={(e) => field.onChange(new Date(e.target.value))}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                      />
                    )}
                  />
                  {errors.eventDate && (
                    <p className="text-red-500 text-sm mt-1">{errors.eventDate.message}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Time Slot * (90 minutes each)
                  </label>
                  <select
                    {...register('eventTime')}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                  >
                    <option value="">Select a time slot</option>
                    {timeSlots.map((slot) => (
                      <option key={slot.value} value={slot.value}>
                        {slot.label}
                      </option>
                    ))}
                  </select>
                  {errors.eventTime && (
                    <p className="text-red-500 text-sm mt-1">{errors.eventTime.message}</p>
                  )}
                </div>
              </div>

              {/* Availability Status */}
              {watchedFields.eventDate && watchedFields.eventTime && (
                <div className="mt-4 p-4 rounded-lg border">
                  {isCheckingAvailability ? (
                    <div className="flex items-center text-blue-600">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                      Checking availability...
                    </div>
                  ) : getCurrentAvailability() === true ? (
                    <div className="flex items-center text-green-600">
                      <span className="mr-2">✅</span>
                      This time slot is available!
                    </div>
                  ) : getCurrentAvailability() === false ? (
                    <div className="flex items-center text-red-600">
                      <span className="mr-2">❌</span>
                      This time slot is not available. Please select a different time.
                    </div>
                  ) : null}
                </div>
              )}
            </div>

            {/* Customer Address */}
            <div className="border-b pb-6">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                🏠 Customer Address
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Street Address *
                  </label>
                  <input
                    {...register('addressStreet')}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                    placeholder="123 Main Street"
                  />
                  {errors.addressStreet && (
                    <p className="text-red-500 text-sm mt-1">{errors.addressStreet.message}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    City *
                  </label>
                  <input
                    {...register('addressCity')}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                    placeholder="San Francisco"
                  />
                  {errors.addressCity && (
                    <p className="text-red-500 text-sm mt-1">{errors.addressCity.message}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    State *
                  </label>
                  <input
                    {...register('addressState')}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                    placeholder="CA"
                  />
                  {errors.addressState && (
                    <p className="text-red-500 text-sm mt-1">{errors.addressState.message}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Zipcode *
                  </label>
                  <input
                    {...register('addressZipcode')}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                    placeholder="94105"
                  />
                  {errors.addressZipcode && (
                    <p className="text-red-500 text-sm mt-1">{errors.addressZipcode.message}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Venue Address */}
            <div className="border-b pb-6">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                🎪 Event Venue Address
              </h2>

              <div className="mb-4">
                <label className="flex items-center cursor-pointer">
                  <input
                    {...register('sameAsCustomer')}
                    type="checkbox"
                    className="rounded border-gray-300 text-red-600 focus:ring-red-500 mr-3"
                  />
                  <span className="text-sm font-medium text-gray-700">
                    Event venue is the same as customer address
                  </span>
                </label>
              </div>

              {!watchedFields.sameAsCustomer && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Venue Street Address *
                    </label>
                    <input
                      {...register('venueStreet')}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                      placeholder="456 Event Venue Street"
                    />
                    {errors.venueStreet && (
                      <p className="text-red-500 text-sm mt-1">{errors.venueStreet.message}</p>
                    )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Venue City *
                    </label>
                    <input
                      {...register('venueCity')}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                      placeholder="San Jose"
                    />
                    {errors.venueCity && (
                      <p className="text-red-500 text-sm mt-1">{errors.venueCity.message}</p>
                    )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Venue State *
                    </label>
                    <input
                      {...register('venueState')}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                      placeholder="CA"
                    />
                    {errors.venueState && (
                      <p className="text-red-500 text-sm mt-1">{errors.venueState.message}</p>
                    )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Venue Zipcode *
                    </label>
                    <input
                      {...register('venueZipcode')}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                      placeholder="95113"
                    />
                    {errors.venueZipcode && (
                      <p className="text-red-500 text-sm mt-1">{errors.venueZipcode.message}</p>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Submit Button */}
            <div className="text-center">
              <button
                type="submit"
                disabled={isSubmitting || getCurrentAvailability() === false}
                className="bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-700 hover:to-orange-700 disabled:from-gray-400 disabled:to-gray-500 text-white font-bold py-4 px-8 rounded-full text-lg transition-all duration-300 transform hover:scale-105 disabled:scale-100 disabled:cursor-not-allowed"
              >
                {isSubmitting ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    Submitting Booking...
                  </div>
                ) : (
                  <>🎉 Book My Hibachi Experience</>
                )}
              </button>
            </div>

            {/* Submit Message */}
            {submitMessage && (
              <div className={`mt-4 p-4 rounded-lg text-center ${
                submitMessage.includes('successfully')
                  ? 'bg-green-100 text-green-800 border border-green-200'
                  : 'bg-red-100 text-red-800 border border-red-200'
              }`}>
                {submitMessage}
              </div>
            )}
          </form>
        </div>

        {/* Additional Information */}
        <div className="mt-8 bg-blue-50 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">
            📋 Important Booking Information
          </h3>
          <ul className="text-blue-800 space-y-2">
            <li>• <strong>Advance Notice:</strong> All bookings require minimum 2 days advance notice</li>
            <li>• <strong>Duration:</strong> Each session is 90 minutes of premium hibachi entertainment</li>
            <li>• <strong>Confirmation:</strong> We will contact you within 1-2 hours to confirm details</li>
            <li>• <strong>Service Area:</strong> We serve within 150 miles of our location</li>
            <li>• <strong>Deposit Required:</strong> A deposit is required to lock the booking slot and secure your reservation</li>
          </ul>
        </div>
      </div>

      {/* Floating Quote Button removed - users can get quotes from dedicated quote page */}
    </div>
  )
}
