'use client'

import 'react-datepicker/dist/react-datepicker.css'
import './datepicker.css'
import '@/styles/booking/booking.css'

import { addDays, format } from 'date-fns'
import React, { useEffect, useState } from 'react'
import DatePicker from 'react-datepicker'
import { Controller, useForm } from 'react-hook-form'

import Assistant from '@/components/chat/Assistant'
import { apiFetch } from '@/lib/api'

// Type definitions for booking form
type BookingFormData = {
  name: string
  email: string
  phone: string
  eventDate: Date
  eventTime: '12PM' | '3PM' | '6PM' | '9PM'
  guestCount: number
  addressStreet: string
  addressCity: string
  addressState: string
  addressZipcode: string
  sameAsVenue: boolean
  venueStreet?: string
  venueCity?: string
  venueState?: string
  venueZipcode?: string
}

export default function BookUsPageClient() {
  const [showValidationModal, setShowValidationModal] = useState(false)
  const [missingFields, setMissingFields] = useState<string[]>([])
  const [showAgreementModal, setShowAgreementModal] = useState(false)
  const [formData, setFormData] = useState<BookingFormData | null>(null)
  const [bookedDates, setBookedDates] = useState<Date[]>([])
  const [loadingDates, setLoadingDates] = useState(false)
  const [dateError, setDateError] = useState<string | null>(null)
  const [availableTimeSlots, setAvailableTimeSlots] = useState<
    Array<{
      time: string
      label: string
      available: number
      isAvailable: boolean
    }>
  >([])
  const [loadingTimeSlots, setLoadingTimeSlots] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    control,
    watch,
    setValue,
    formState: { errors }
  } = useForm<BookingFormData>({
    defaultValues: {
      sameAsVenue: false,
      guestCount: undefined
    }
  })

  // Watch form values
  const sameAsVenue = watch('sameAsVenue')
  const venueStreet = watch('venueStreet')
  const venueCity = watch('venueCity')
  const venueState = watch('venueState')
  const venueZipcode = watch('venueZipcode')
  const selectedDate = watch('eventDate')

  // Fetch booked dates from API
  const fetchBookedDates = async () => {
    setLoadingDates(true)
    setDateError(null)
    try {
      const result = await apiFetch('/api/v1/bookings/booked-dates')
      if (result.success) {
        // Convert string dates to Date objects
        const dates = result.data.bookedDates?.map((dateStr: string) => new Date(dateStr)) || []
        setBookedDates(dates)
      } else {
        console.warn('Could not fetch booked dates, continuing without blocking dates')
        setBookedDates([])
      }
    } catch (error) {
      console.warn('Error fetching booked dates:', error)
      setBookedDates([])
    } finally {
      setLoadingDates(false)
    }
  }

  // Fetch available time slots for selected date
  const fetchAvailableTimeSlots = async (date: Date) => {
    setLoadingTimeSlots(true)
    try {
      const dateStr = format(date, 'yyyy-MM-dd')
      const response = await apiFetch(`/api/v1/bookings/available-times?date=${dateStr}`)

      if (response.success) {
        setAvailableTimeSlots(response.data.timeSlots || [])
      } else {
        // Fallback to default time slots if API fails
        setAvailableTimeSlots([
          { time: '12PM', label: '12:00 PM - 2:00 PM', available: 2, isAvailable: true },
          { time: '3PM', label: '3:00 PM - 5:00 PM', available: 2, isAvailable: true },
          { time: '6PM', label: '6:00 PM - 8:00 PM', available: 2, isAvailable: true },
          { time: '9PM', label: '9:00 PM - 11:00 PM', available: 1, isAvailable: true }
        ])
      }
    } catch (error) {
      console.warn('Error fetching time slots:', error)
      // Fallback to default time slots
      setAvailableTimeSlots([
        { time: '12PM', label: '12:00 PM - 2:00 PM', available: 2, isAvailable: true },
        { time: '3PM', label: '3:00 PM - 5:00 PM', available: 2, isAvailable: true },
        { time: '6PM', label: '6:00 PM - 8:00 PM', available: 2, isAvailable: true },
        { time: '9PM', label: '9:00 PM - 11:00 PM', available: 1, isAvailable: true }
      ])
    } finally {
      setLoadingTimeSlots(false)
    }
  }

  // Load booked dates on component mount
  useEffect(() => {
    fetchBookedDates()
  }, [])

  // Fetch time slots when date changes
  useEffect(() => {
    if (selectedDate) {
      fetchAvailableTimeSlots(selectedDate)
    }
  }, [selectedDate])

  // Auto-fill venue address when "Same as venue" is checked
  useEffect(() => {
    if (sameAsVenue && venueStreet && venueCity && venueState && venueZipcode) {
      setValue('addressStreet', venueStreet)
      setValue('addressCity', venueCity)
      setValue('addressState', venueState)
      setValue('addressZipcode', venueZipcode)
    }
  }, [sameAsVenue, venueStreet, venueCity, venueState, venueZipcode, setValue])

  // Enhanced onSubmit with comprehensive validation
  const onSubmit = async (data: BookingFormData) => {
    console.log('Form submission started with data:', data)

    // Validate required fields manually
    const requiredFields = []
    if (!data.name?.trim()) requiredFields.push('Name')
    if (!data.email?.trim()) requiredFields.push('Email')
    if (!data.phone?.trim()) requiredFields.push('Phone')
    if (!data.eventDate) requiredFields.push('Event Date')
    if (!data.eventTime) requiredFields.push('Event Time')
    if (!data.guestCount || data.guestCount < 1) requiredFields.push('Guest Count')

    // Address validation
    if (!data.addressStreet?.trim()) requiredFields.push('Address Street')
    if (!data.addressCity?.trim()) requiredFields.push('Address City')
    if (!data.addressState?.trim()) requiredFields.push('Address State')
    if (!data.addressZipcode?.trim()) requiredFields.push('Address ZIP Code')

    // Venue validation (only if different from address)
    if (!data.sameAsVenue) {
      if (!data.venueStreet?.trim()) requiredFields.push('Venue Street')
      if (!data.venueCity?.trim()) requiredFields.push('Venue City')
      if (!data.venueState?.trim()) requiredFields.push('Venue State')
      if (!data.venueZipcode?.trim()) requiredFields.push('Venue ZIP Code')
    }

    if (requiredFields.length > 0) {
      setMissingFields(requiredFields)
      setShowValidationModal(true)
      return
    }

    // Store form data and show agreement modal
    setFormData(data)
    setShowAgreementModal(true)
  }

  const handleAgreementConfirm = async () => {
    if (!formData) return

    setIsSubmitting(true)
    setShowAgreementModal(false)

    try {
      console.log('Submitting booking request:', formData)

      const submissionData = {
        ...formData,
        eventDate: format(formData.eventDate, 'yyyy-MM-dd'),
        submittedAt: new Date().toISOString(),
        status: 'pending'
      }

      const response = await apiFetch('/api/v1/bookings/submit', {
        method: 'POST',
        body: JSON.stringify(submissionData)
      })

      if (response.success) {
        console.log('Booking submitted successfully')
        // Redirect to success page
        window.location.href = '/booking-success'
      } else {
        console.error('Booking submission failed:', response.error)
        alert(
          'Sorry, there was an error submitting your booking. Please try again or contact us directly.'
        )
      }
    } catch (error) {
      console.error('Error submitting booking:', error)
      alert(
        'Sorry, there was an error submitting your booking. Please try again or contact us directly.'
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleAgreementCancel = () => {
    setShowAgreementModal(false)
    setFormData(null)
  }

  // Helper function to determine if a date should be disabled
  const isDateDisabled = (date: Date) => {
    const today = new Date()
    today.setHours(0, 0, 0, 0)

    // Disable dates in the past
    if (date < today) return true

    // Disable dates more than 3 months in advance
    const maxDate = addDays(today, 90)
    if (date > maxDate) return true

    // Check if date is fully booked
    const isBooked = bookedDates.some(bookedDate => {
      const bDate = new Date(bookedDate)
      bDate.setHours(0, 0, 0, 0)
      return bDate.getTime() === date.getTime()
    })

    return isBooked
  }

  return (
    <div className="booking-page">
      {/* Hero Section */}
      <section className="booking-hero">
        <div className="container">
          <div className="hero-content text-center">
            <h1 className="hero-title">
              <i className="bi bi-calendar-check-fill me-3"></i>
              Book Your Hibachi Experience
            </h1>
            <p className="hero-subtitle">
              Reserve your premium private hibachi chef service for an unforgettable culinary
              experience
            </p>
            <div className="hero-features">
              <div className="feature-item">
                <i className="bi bi-shield-check feature-icon"></i>
                <span>100% Satisfaction Guaranteed</span>
              </div>
              <div className="feature-item">
                <i className="bi bi-clock feature-icon"></i>
                <span>Flexible Scheduling</span>
              </div>
              <div className="feature-item">
                <i className="bi bi-geo-alt feature-icon"></i>
                <span>We Come To You</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="container">
        <div className="row justify-content-center">
          <div className="col-lg-8">
            <div className="booking-form-container">
              <form onSubmit={handleSubmit(onSubmit)} className="booking-form">
                {/* Contact Information */}
                <div className="form-section">
                  <h3 className="section-title">
                    <i className="bi bi-person-fill me-2"></i>
                    Contact Information
                  </h3>

                  <div className="row">
                    <div className="col-md-6">
                      <div className="form-group">
                        <label htmlFor="name" className="form-label required">
                          Full Name
                        </label>
                        <input
                          type="text"
                          id="name"
                          className={`form-control ${errors.name ? 'is-invalid' : ''}`}
                          {...register('name', { required: 'Name is required' })}
                          placeholder="Enter your full name"
                        />
                        {errors.name && (
                          <div className="invalid-feedback">{errors.name.message}</div>
                        )}
                      </div>
                    </div>

                    <div className="col-md-6">
                      <div className="form-group">
                        <label htmlFor="email" className="form-label required">
                          Email Address
                        </label>
                        <input
                          type="email"
                          id="email"
                          className={`form-control ${errors.email ? 'is-invalid' : ''}`}
                          {...register('email', {
                            required: 'Email is required',
                            pattern: {
                              value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                              message: 'Invalid email address'
                            }
                          })}
                          placeholder="your.email@example.com"
                        />
                        {errors.email && (
                          <div className="invalid-feedback">{errors.email.message}</div>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="row">
                    <div className="col-md-6">
                      <div className="form-group">
                        <label htmlFor="phone" className="form-label required">
                          Phone Number
                        </label>
                        <input
                          type="tel"
                          id="phone"
                          className={`form-control ${errors.phone ? 'is-invalid' : ''}`}
                          {...register('phone', { required: 'Phone number is required' })}
                          placeholder="(555) 123-4567"
                        />
                        {errors.phone && (
                          <div className="invalid-feedback">{errors.phone.message}</div>
                        )}
                      </div>
                    </div>

                    <div className="col-md-6">
                      <div className="form-group">
                        <label htmlFor="guestCount" className="form-label required">
                          Number of Guests
                        </label>
                        <input
                          type="number"
                          id="guestCount"
                          min="1"
                          max="50"
                          className={`form-control ${errors.guestCount ? 'is-invalid' : ''}`}
                          {...register('guestCount', {
                            required: 'Guest count is required',
                            min: { value: 1, message: 'At least 1 guest required' },
                            max: { value: 50, message: 'Maximum 50 guests allowed' }
                          })}
                          placeholder="e.g., 8"
                        />
                        {errors.guestCount && (
                          <div className="invalid-feedback">{errors.guestCount.message}</div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Event Details */}
                <div className="form-section">
                  <h3 className="section-title">
                    <i className="bi bi-calendar-event me-2"></i>
                    Event Details
                  </h3>

                  <div className="row">
                    <div className="col-md-6">
                      <div className="form-group">
                        <label htmlFor="eventDate" className="form-label required">
                          Event Date
                        </label>
                        <Controller
                          name="eventDate"
                          control={control}
                          rules={{ required: 'Event date is required' }}
                          render={({ field }) => (
                            <DatePicker
                              selected={field.value}
                              onChange={date => field.onChange(date)}
                              filterDate={date => !isDateDisabled(date)}
                              minDate={new Date()}
                              maxDate={addDays(new Date(), 90)}
                              className={`form-control ${errors.eventDate ? 'is-invalid' : ''}`}
                              placeholderText="Select event date"
                              dateFormat="MMMM d, yyyy"
                              id="eventDate"
                            />
                          )}
                        />
                        {loadingDates && (
                          <small className="text-muted">Loading available dates...</small>
                        )}
                        {dateError && <small className="text-danger">{dateError}</small>}
                        {errors.eventDate && (
                          <div className="invalid-feedback d-block">{errors.eventDate.message}</div>
                        )}
                      </div>
                    </div>

                    <div className="col-md-6">
                      <div className="form-group">
                        <label htmlFor="eventTime" className="form-label required">
                          Preferred Time
                        </label>
                        {loadingTimeSlots ? (
                          <div className="form-control">Loading available times...</div>
                        ) : (
                          <select
                            id="eventTime"
                            className={`form-control ${errors.eventTime ? 'is-invalid' : ''}`}
                            {...register('eventTime', { required: 'Event time is required' })}
                          >
                            <option value="">Select a time</option>
                            {availableTimeSlots.map(slot => (
                              <option
                                key={slot.time}
                                value={slot.time}
                                disabled={!slot.isAvailable}
                              >
                                {slot.label}{' '}
                                {slot.isAvailable
                                  ? `(${slot.available} available)`
                                  : '(Fully Booked)'}
                              </option>
                            ))}
                          </select>
                        )}
                        {errors.eventTime && (
                          <div className="invalid-feedback">{errors.eventTime.message}</div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Venue Address */}
                <div className="form-section">
                  <h3 className="section-title">
                    <i className="bi bi-geo-alt me-2"></i>
                    Event Venue Address
                  </h3>
                  <p className="section-description">
                    Please provide the address where the hibachi event will take place.
                  </p>

                  <div className="row">
                    <div className="col-12">
                      <div className="form-group">
                        <label htmlFor="venueStreet" className="form-label required">
                          Street Address
                        </label>
                        <input
                          type="text"
                          id="venueStreet"
                          className={`form-control ${errors.venueStreet ? 'is-invalid' : ''}`}
                          {...register('venueStreet', {
                            required: 'Venue street address is required'
                          })}
                          placeholder="123 Main Street, Apt 2B"
                        />
                        {errors.venueStreet && (
                          <div className="invalid-feedback">{errors.venueStreet.message}</div>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="row">
                    <div className="col-md-6">
                      <div className="form-group">
                        <label htmlFor="venueCity" className="form-label required">
                          City
                        </label>
                        <input
                          type="text"
                          id="venueCity"
                          className={`form-control ${errors.venueCity ? 'is-invalid' : ''}`}
                          {...register('venueCity', { required: 'Venue city is required' })}
                          placeholder="San Francisco"
                        />
                        {errors.venueCity && (
                          <div className="invalid-feedback">{errors.venueCity.message}</div>
                        )}
                      </div>
                    </div>

                    <div className="col-md-3">
                      <div className="form-group">
                        <label htmlFor="venueState" className="form-label required">
                          State
                        </label>
                        <select
                          id="venueState"
                          className={`form-control ${errors.venueState ? 'is-invalid' : ''}`}
                          {...register('venueState', { required: 'Venue state is required' })}
                        >
                          <option value="">Select State</option>
                          <option value="CA">California</option>
                          <option value="NV">Nevada</option>
                          <option value="OR">Oregon</option>
                          <option value="WA">Washington</option>
                        </select>
                        {errors.venueState && (
                          <div className="invalid-feedback">{errors.venueState.message}</div>
                        )}
                      </div>
                    </div>

                    <div className="col-md-3">
                      <div className="form-group">
                        <label htmlFor="venueZipcode" className="form-label required">
                          ZIP Code
                        </label>
                        <input
                          type="text"
                          id="venueZipcode"
                          className={`form-control ${errors.venueZipcode ? 'is-invalid' : ''}`}
                          {...register('venueZipcode', { required: 'Venue ZIP code is required' })}
                          placeholder="94102"
                        />
                        {errors.venueZipcode && (
                          <div className="invalid-feedback">{errors.venueZipcode.message}</div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Customer Address */}
                <div className="form-section">
                  <h3 className="section-title">
                    <i className="bi bi-house me-2"></i>
                    Your Contact Address
                  </h3>
                  <p className="section-description">
                    This address will be used for billing and communication purposes.
                  </p>

                  <div className="form-check mb-3">
                    <input
                      type="checkbox"
                      id="sameAsVenue"
                      className="form-check-input"
                      {...register('sameAsVenue')}
                    />
                    <label htmlFor="sameAsVenue" className="form-check-label">
                      Same as venue address
                    </label>
                  </div>

                  {!sameAsVenue && (
                    <>
                      <div className="row">
                        <div className="col-12">
                          <div className="form-group">
                            <label htmlFor="addressStreet" className="form-label required">
                              Street Address
                            </label>
                            <input
                              type="text"
                              id="addressStreet"
                              className={`form-control ${errors.addressStreet ? 'is-invalid' : ''}`}
                              {...register('addressStreet', {
                                required: 'Street address is required'
                              })}
                              placeholder="123 Main Street, Apt 2B"
                            />
                            {errors.addressStreet && (
                              <div className="invalid-feedback">{errors.addressStreet.message}</div>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="row">
                        <div className="col-md-6">
                          <div className="form-group">
                            <label htmlFor="addressCity" className="form-label required">
                              City
                            </label>
                            <input
                              type="text"
                              id="addressCity"
                              className={`form-control ${errors.addressCity ? 'is-invalid' : ''}`}
                              {...register('addressCity', { required: 'City is required' })}
                              placeholder="San Francisco"
                            />
                            {errors.addressCity && (
                              <div className="invalid-feedback">{errors.addressCity.message}</div>
                            )}
                          </div>
                        </div>

                        <div className="col-md-3">
                          <div className="form-group">
                            <label htmlFor="addressState" className="form-label required">
                              State
                            </label>
                            <select
                              id="addressState"
                              className={`form-control ${errors.addressState ? 'is-invalid' : ''}`}
                              {...register('addressState', { required: 'State is required' })}
                            >
                              <option value="">Select State</option>
                              <option value="CA">California</option>
                              <option value="NV">Nevada</option>
                              <option value="OR">Oregon</option>
                              <option value="WA">Washington</option>
                            </select>
                            {errors.addressState && (
                              <div className="invalid-feedback">{errors.addressState.message}</div>
                            )}
                          </div>
                        </div>

                        <div className="col-md-3">
                          <div className="form-group">
                            <label htmlFor="addressZipcode" className="form-label required">
                              ZIP Code
                            </label>
                            <input
                              type="text"
                              id="addressZipcode"
                              className={`form-control ${errors.addressZipcode ? 'is-invalid' : ''}`}
                              {...register('addressZipcode', { required: 'ZIP code is required' })}
                              placeholder="94102"
                            />
                            {errors.addressZipcode && (
                              <div className="invalid-feedback">
                                {errors.addressZipcode.message}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </>
                  )}
                </div>

                {/* Submit Button */}
                <div className="form-section text-center">
                  <button
                    type="submit"
                    className="btn btn-primary btn-lg booking-submit-btn"
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? (
                      <>
                        <i className="bi bi-hourglass-split me-2"></i>
                        Processing Booking...
                      </>
                    ) : (
                      <>
                        <i className="bi bi-calendar-check me-2"></i>
                        Submit Booking Request
                      </>
                    )}
                  </button>
                  <p className="mt-3 text-muted">
                    <small>
                      <i className="bi bi-shield-check me-1"></i>
                      Your information is secure and will only be used to process your booking.
                    </small>
                  </p>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>

      {/* Validation Modal */}
      {showValidationModal && (
        <div className="modal fade show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  <i className="bi bi-exclamation-triangle text-warning me-2"></i>
                  Missing Information
                </h5>
              </div>
              <div className="modal-body">
                <p>Please fill in the following required fields:</p>
                <ul className="list-unstyled">
                  {missingFields.map((field, index) => (
                    <li key={index} className="mb-1">
                      <i className="bi bi-arrow-right text-primary me-2"></i>
                      {field}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => setShowValidationModal(false)}
                >
                  <i className="bi bi-check-lg me-2"></i>
                  Got It
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Agreement Modal */}
      {showAgreementModal && (
        <div className="modal fade show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered modal-lg">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  <i className="bi bi-file-text text-primary me-2"></i>
                  Booking Agreement & Terms
                </h5>
              </div>
              <div className="modal-body">
                <div className="agreement-content">
                  <h6>Service Agreement:</h6>
                  <ul>
                    <li>Professional hibachi chef service with entertainment and cooking</li>
                    <li>Fresh, high-quality ingredients prepared on-site</li>
                    <li>All necessary cooking equipment and utensils provided</li>
                    <li>2-hour service duration (additional time available upon request)</li>
                  </ul>

                  <h6 className="mt-3">Pricing & Payment:</h6>
                  <ul>
                    <li>Final pricing will be confirmed based on guest count and menu selection</li>
                    <li>50% deposit required to secure booking</li>
                    <li>Remaining balance due on event day</li>
                    <li>Travel fees may apply for locations outside our standard service area</li>
                  </ul>

                  <h6 className="mt-3">Cancellation Policy:</h6>
                  <ul>
                    <li>Full refund if cancelled 7+ days before event</li>
                    <li>50% refund if cancelled 3-6 days before event</li>
                    <li>No refund if cancelled within 48 hours of event</li>
                  </ul>

                  <h6 className="mt-3">Client Responsibilities:</h6>
                  <ul>
                    <li>Provide adequate outdoor space with access to power outlet</li>
                    <li>Ensure safe and clean cooking environment</li>
                    <li>Inform us of any food allergies or dietary restrictions</li>
                  </ul>

                  <p className="mt-3">
                    <strong>
                      By confirming this booking, you agree to these terms and conditions.
                    </strong>
                  </p>
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-outline-secondary me-2"
                  onClick={handleAgreementCancel}
                >
                  <i className="bi bi-x-lg me-2"></i>
                  Cancel
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={handleAgreementConfirm}
                  disabled={isSubmitting}
                >
                  <i className="bi bi-check-lg me-2"></i>I Agree - Submit Booking
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <Assistant page="/BookUs" />
    </div>
  )
}
