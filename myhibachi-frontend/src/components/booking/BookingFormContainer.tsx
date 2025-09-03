import './styles/BookingFormContainer.module.css'

import { addDays, format } from 'date-fns'
import React, { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'

import { apiFetch } from '@/lib/api'

import ContactInfoSection from './ContactInfoSection'
import CustomerAddressSection from './CustomerAddressSection'
import EventDetailsSection from './EventDetailsSection'
import SubmitSection from './SubmitSection'
import VenueAddressSection from './VenueAddressSection'

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

interface BookingFormContainerProps {
  className?: string
}

const BookingFormContainer: React.FC<BookingFormContainerProps> = ({ className = '' }) => {
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
        const errorData = response.data || response
        console.error('Booking submission failed:', errorData)
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

  // Pass state and handlers to child components
  const formProps = {
    register,
    control,
    errors,
    watch,
    setValue,
    loadingDates,
    dateError,
    availableTimeSlots,
    loadingTimeSlots,
    isDateDisabled,
    isSubmitting,
    showValidationModal,
    setShowValidationModal,
    missingFields,
    showAgreementModal,
    setShowAgreementModal,
    handleAgreementConfirm,
    handleAgreementCancel,
    sameAsVenue
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className={`booking-form ${className}`}>
      <ContactInfoSection {...formProps} />
      <EventDetailsSection {...formProps} />
      <VenueAddressSection {...formProps} />
      <CustomerAddressSection {...formProps} />
      <SubmitSection {...formProps} />
    </form>
  )
}

export default BookingFormContainer
