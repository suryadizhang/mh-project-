'use client'

import React from 'react'
import { BookingHero } from '../../components/booking/BookingHero'
import { ContactInfo } from '../../components/booking/ContactInfo'
import { DateTimeSelection } from '../../components/booking/DateTimeSelection'
import { AddressForm } from '../../components/booking/AddressForm'
import { BookingSummary } from '../../components/booking/BookingSummary'
import { useBooking } from '../../hooks/booking/useBooking'
import { DEFAULT_FORM_VALUES } from '../../data/booking/types'
import '../../styles/booking/booking.css'

export default function BookUsPage() {
  const {
    handleSubmit,
    errors,
    watch,
    setValue,
    availableTimeSlots,
    isSubmitting,
    onSubmit
  } = useBooking()

  // Get current form values
  const watchedValues = watch()
  const formData = { ...DEFAULT_FORM_VALUES, ...watchedValues }

  // Helper function to update form data
  const updateFormData = (field: keyof typeof formData, value: string | number | Date | boolean) => {
    setValue(field, value)
  }

  // Convert errors to simple string format
  const errorMessages: Record<string, string> = {}
  Object.entries(errors).forEach(([key, error]) => {
    if (error?.message) {
      errorMessages[key] = error.message
    }
  })

  return (
    <div className="booking-page">
      <BookingHero />

      <div className="container">
        <div className="booking-content">
          <div className="booking-form">
            <form onSubmit={handleSubmit(onSubmit)}>
              <ContactInfo
                formData={formData}
                onChange={updateFormData}
                errors={errorMessages}
              />

              <DateTimeSelection
                formData={formData}
                onChange={updateFormData}
                errors={errorMessages}
                timeSlots={availableTimeSlots}
              />

              <AddressForm
                formData={formData}
                onChange={updateFormData}
                errors={errorMessages}
              />
            </form>
          </div>

          <div className="booking-sidebar">
            <BookingSummary
              formData={formData}
              isSubmitting={isSubmitting}
              onSubmit={() => handleSubmit(onSubmit)()}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
