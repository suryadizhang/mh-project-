'use client'

import React, { useEffect, useState } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { format, addDays } from 'date-fns'
import DatePicker from 'react-datepicker'
import 'react-datepicker/dist/react-datepicker.css'
import './datepicker.css'
import Assistant from '@/components/chat/Assistant'

// Type definitions for booking form

type BookingFormData = {
  name: string;
  email: string;
  phone: string;
  eventDate: Date;
  eventTime: '12PM' | '3PM' | '6PM' | '9PM';
  guestCount: number;
  addressStreet: string;
  addressCity: string;
  addressState: string;
  addressZipcode: string;
  sameAsVenue: boolean;
  venueStreet?: string;
  venueCity?: string;
  venueState?: string;
  venueZipcode?: string;
}

export default function BookingPage() {
  const [showValidationModal, setShowValidationModal] = useState(false)
  const [missingFields, setMissingFields] = useState<string[]>([])
  const [showAgreementModal, setShowAgreementModal] = useState(false)
  const [formData, setFormData] = useState<BookingFormData | null>(null)
  const [bookedDates, setBookedDates] = useState<Date[]>([])
  const [loadingDates, setLoadingDates] = useState(false)
  const [dateError, setDateError] = useState<string | null>(null)
  const [availableTimeSlots, setAvailableTimeSlots] = useState<Array<{
    time: string
    label: string
    available: number
    isAvailable: boolean
  }>>([])
  const [loadingTimeSlots, setLoadingTimeSlots] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    control,
    watch,
    setValue,
    formState: { errors },
  } = useForm<BookingFormData>({
    defaultValues: {
      sameAsVenue: false,
      guestCount: undefined,
    },
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
      const response = await fetch('/api/v1/bookings/booked-dates')
      if (response.ok) {
        const data = await response.json()
        // Convert string dates to Date objects
        const dates = data.bookedDates?.map((dateStr: string) => new Date(dateStr)) || []
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

  // Fetch booked dates on component mount
  useEffect(() => {
    fetchBookedDates()
  }, [])

  // Fetch availability for selected date
  const fetchAvailability = async (date: Date) => {
    setLoadingTimeSlots(true)
    setDateError(null)
    try {
      const dateStr = format(date, 'yyyy-MM-dd')
      const response = await fetch(`/api/v1/bookings/availability?date=${dateStr}`)

      if (response.ok) {
        const data = await response.json()
        const formattedSlots = data.timeSlots.map((slot: {
          time: string;
          available: number;
          maxCapacity: number;
          booked: number;
          isAvailable: boolean;
        }) => ({
          time: slot.time,
          label: slot.time === '12PM' ? '12:00 PM' :
                 slot.time === '3PM' ? '3:00 PM' :
                 slot.time === '6PM' ? '6:00 PM' : '9:00 PM',
          available: slot.available,
          isAvailable: slot.isAvailable
        }))
        setAvailableTimeSlots(formattedSlots)
      } else {
        console.warn('Could not fetch availability, using default slots')
        setAvailableTimeSlots([])
      }
    } catch (error) {
      console.warn('Error fetching availability:', error)
      setAvailableTimeSlots([])
    } finally {
      setLoadingTimeSlots(false)
    }
  }

  // Fetch availability when date changes
  useEffect(() => {
    if (selectedDate) {
      fetchAvailability(selectedDate)
    } else {
      setAvailableTimeSlots([])
    }
  }, [selectedDate])

  // Check if venue address is completely filled
  const isVenueAddressComplete = venueStreet && venueCity && venueState && venueZipcode

  // Auto-fill billing address when checkbox is checked and venue address is complete
  useEffect(() => {
    if (sameAsVenue && isVenueAddressComplete) {
      setValue('addressStreet', venueStreet)
      setValue('addressCity', venueCity)
      setValue('addressState', venueState)
      setValue('addressZipcode', venueZipcode)
    }
  }, [sameAsVenue, venueStreet, venueCity, venueState, venueZipcode, isVenueAddressComplete, setValue])

  // Automatically uncheck if venue address becomes incomplete
  useEffect(() => {
    if (sameAsVenue && !isVenueAddressComplete) {
      setValue('sameAsVenue', false)
    }
  }, [sameAsVenue, isVenueAddressComplete, setValue])

  // Enhanced onSubmit with comprehensive validation
  const onSubmit = async (data: BookingFormData) => {
    setIsSubmitting(true)

    try {
      // Check for missing fields
      const missing: string[] = []

      if (!data.name || data.name.length < 2) missing.push('Full Name')
      if (!data.email) missing.push('Email Address')
      if (!data.phone || data.phone.length < 10) missing.push('Phone Number')
      if (!data.eventDate) missing.push('Event Date')
      if (!data.eventTime) missing.push('Event Time')
      if (!data.guestCount || data.guestCount < 1) missing.push('Estimate Number of Guests')

      // Check venue address
      if (!data.venueStreet) missing.push('Venue Street Address')
      if (!data.venueCity) missing.push('Venue City')
      if (!data.venueState) missing.push('Venue State')
      if (!data.venueZipcode) missing.push('Venue ZIP Code')

      // Check billing address (only if not same as venue)
      if (!data.sameAsVenue) {
        if (!data.addressStreet) missing.push('Billing Street Address')
        if (!data.addressCity) missing.push('Billing City')
      if (!data.addressState) missing.push('Billing State')
      if (!data.addressZipcode) missing.push('Billing ZIP Code')
    }

    // If there are missing fields, show modal
    if (missing.length > 0) {
      setMissingFields(missing)
      setShowValidationModal(true)
      return
    }

    // Additional validation: Check if selected time slot is still available
    if (data.eventDate && data.eventTime) {
      try {
        const dateStr = format(data.eventDate, 'yyyy-MM-dd')
        const response = await fetch(`/api/v1/bookings/availability?date=${dateStr}`)

        if (response.ok) {
          const availabilityData = await response.json()
          const selectedSlot = availabilityData.timeSlots.find(
            (slot: { time: string; isAvailable: boolean }) => slot.time === data.eventTime
          )

          if (!selectedSlot || !selectedSlot.isAvailable) {
            setDateError(`The ${data.eventTime} time slot is no longer available. Please select a different time.`)
            return
          }
        }
      } catch (error) {
        console.warn('Could not verify slot availability:', error)
        // Continue with booking as a fallback
      }
    }

    // If all validation passes, show agreement modal
    setFormData(data)
    setShowAgreementModal(true)
    } catch (error) {
      console.error('Form submission error:', error)
      setDateError('An unexpected error occurred. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  // Handle agreement confirmation with actual booking submission
  const handleAgreementConfirm = async () => {
    if (!formData) return

    try {
      const bookingData = {
        date: format(formData.eventDate, 'yyyy-MM-dd'),
        time: formData.eventTime,
        customerInfo: {
          name: formData.name,
          email: formData.email,
          phone: formData.phone,
          guestCount: formData.guestCount,
          venueAddress: {
            street: formData.venueStreet,
            city: formData.venueCity,
            state: formData.venueState,
            zipcode: formData.venueZipcode
          },
          billingAddress: formData.sameAsVenue ? null : {
            street: formData.addressStreet,
            city: formData.addressCity,
            state: formData.addressState,
            zipcode: formData.addressZipcode
          }
        }
      }

      const response = await fetch('/api/v1/bookings/availability', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(bookingData)
      })

      const result = await response.json()

      if (response.ok && result.success) {
        setShowAgreementModal(false)
        setFormData(null)

        // Show success message with booking ID
        alert(`Booking Confirmed!\n\nConfirmation Code: ${result.bookingId}\n\nWe will contact you soon at ${formData.email} to finalize your hibachi experience details.\n\nThank you for choosing My Hibachi!`)

        // Reset form
        window.location.reload()
      } else {
        // Handle booking errors
        if (result.code === 'SLOT_FULL') {
          setShowAgreementModal(false)
          setDateError('This time slot just became fully booked. Please select a different time.')

          // Refresh availability data
          if (formData.eventDate) {
            fetchAvailability(formData.eventDate)
          }
        } else {
          alert(`❌ Booking Failed\n\n${result.error || 'Please try again or contact support.'}\n\nYour information has been preserved.`)
        }
      }
    } catch (error) {
      console.error('Booking submission error:', error)
      alert('❌ Network Error\n\nPlease check your connection and try again.\nYour information has been preserved.')
    }
  }

  const handleAgreementCancel = () => {
    setShowAgreementModal(false)
    setFormData(null)
  }

  // Validation Modal Component
  const ValidationModal = () => {
    if (!showValidationModal) return null

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6">
          <div className="text-center mb-4">
            <div className="text-4xl mb-2">⚠️</div>
            <h3 className="text-xl font-bold text-red-600">Please Complete Your Booking</h3>
            <p className="text-gray-600 mt-2">The following fields are required:</p>
          </div>

          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <ul className="space-y-1">
              {missingFields.map((field, index) => (
                <li key={index} className="flex items-center space-x-2 text-red-700">
                  <span className="text-red-500">•</span>
                  <span className="font-medium">{field}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="flex space-x-3">
            <button
              onClick={() => setShowValidationModal(false)}
              className="flex-1 bg-red-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-red-700 transition duration-200"
            >
              Got it, I&apos;ll complete the form
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Agreement Modal Component
  const AgreementModal = () => {
    if (!showAgreementModal) return null

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
          <div className="bg-red-600 text-white p-6 text-center">
            <div className="text-4xl mb-2">📋</div>
            <h3 className="text-2xl font-bold">My Hibachi Catering Agreement</h3>
            <p className="text-red-100 mt-2">Please review and confirm the terms below</p>
          </div>

          <div className="p-6 overflow-y-auto max-h-[60vh]">
            <div className="space-y-6 text-sm">
              <div>
                <h4 className="font-bold text-red-600 mb-2">1. SERVICES</h4>
                <p className="text-gray-700 mb-2">
                  My Hibachi will provide hibachi catering services at the Customer&apos;s location on [Event Date] from [Start Time] to approximately [End Time]. We will bring a private chef, all cooking equipment, and fresh food ingredients.
                </p>
                <p className="text-gray-600 italic">
                  Note: We do not provide table setup, chairs, plates, or utensils. Customers are responsible for arranging seating and place settings.
                </p>
              </div>

              <div>
                <h4 className="font-bold text-red-600 mb-2">2. CUSTOMER RESPONSIBILITIES</h4>
                <p className="text-gray-700 mb-2">Customer must provide:</p>
                <ul className="list-disc list-inside text-gray-700 space-y-1 ml-4">
                  <li>Tables, chairs, and dining utensils (plates, napkins, forks, etc.)</li>
                  <li>Safe, level space for outdoor cooking (patio, driveway, etc.)</li>
                  <li>Adequate lighting for evening events</li>
                  <li>Covering in case of rain (e.g., tent or covered patio)</li>
                  <li>Parking and venue access for setup</li>
                  <li>Confirmed guest count and food selections</li>
                </ul>
              </div>

              <div>
                <h4 className="font-bold text-red-600 mb-2">3. MENU, HEADCOUNT & FINAL DETAILS</h4>
                <ul className="list-disc list-inside text-gray-700 space-y-1">
                  <li>Food orders and headcount must be confirmed via text or email the week of the event.</li>
                  <li>Final protein choices must be submitted at least 2 days before the event. If not received, default proteins (chicken and steak) will be served.</li>
                  <li>Menu changes allowed up to 48 hours prior.</li>
                  <li>Guest additions allowed up to 24 hours prior.</li>
                  <li>Same-day changes are not allowed. The full confirmed order will be charged regardless of attendance.</li>
                </ul>
              </div>

              <div>
                <h4 className="font-bold text-red-600 mb-2">4. PAYMENT TERMS</h4>
                <ul className="list-disc list-inside text-gray-700 space-y-1">
                  <li>Deposit: $100 (refundable if canceled 7+ days before event, required to reserve your date)</li>
                  <li>Remaining balance: Due on or before the event date</li>
                  <li>Accepted payments: Venmo Business, Zelle Business, Cash, or Card</li>
                </ul>
              </div>

              <div>
                <h4 className="font-bold text-red-600 mb-2">5. CANCELLATION & WEATHER POLICY</h4>
                <ul className="list-disc list-inside text-gray-700 space-y-1">
                  <li>Full refund if canceled at least 7 days before the event</li>
                  <li>One-time reschedule allowed within 48 hours; otherwise, a $100 rescheduling fee applies</li>
                  <li>Customer must provide overhead covering in the event of rain. Unsafe/uncovered setups may lead to cancellation without refund.</li>
                </ul>
              </div>

              <div>
                <h4 className="font-bold text-red-600 mb-2">6. LIABILITY WAIVER</h4>
                <p className="text-gray-700 mb-2 font-medium">
                  PLEASE TAKE NOTICE: My Hibachi and its agents, employees, or representatives will NOT be liable to any Host or guests for property damage or personal injury resulting from the event.
                </p>
                <ul className="list-disc list-inside text-gray-700 space-y-1">
                  <li>Property damage includes injury to any real or personal property at the event site.</li>
                  <li>Host and guests waive any claim for loss, damage, or destruction of property before, during, or after the event.</li>
                </ul>
              </div>

              <div>
                <h4 className="font-bold text-red-600 mb-2">7. FORCE MAJEURE</h4>
                <p className="text-gray-700">
                  Neither party shall be held liable for failure to perform due to events beyond their reasonable control including but not limited to illness, accidents, fire, flood, government restrictions, or natural disasters.
                </p>
              </div>

              <div>
                <h4 className="font-bold text-red-600 mb-2">8. FOOD SAFETY & ALLERGIES</h4>
                <ul className="list-disc list-inside text-gray-700 space-y-1">
                  <li>Customer is responsible for notifying Caterer of any food allergies at least 48 hours in advance.</li>
                  <li>My Hibachi is not liable for allergic reactions due to undisclosed sensitivities or customer-supplied ingredients.</li>
                </ul>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 p-6 border-t">
            {/* Customer Details Confirmation */}
            {formData && (
              <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
                <h4 className="font-bold text-gray-900 mb-3 text-center">Customer Agreement Confirmation</h4>
                <div className="text-sm text-gray-700 space-y-2">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <p><strong>Customer Name:</strong> {formData.name}</p>
                      <p><strong>Email:</strong> {formData.email}</p>
                      <p><strong>Phone:</strong> {formData.phone}</p>
                    </div>
                    <div>
                      <p><strong>Event Date:</strong> {formData.eventDate ? format(new Date(formData.eventDate), 'MMMM dd, yyyy') : 'Not selected'}</p>
                      <p><strong>Event Time:</strong> {formData.eventTime || 'Not selected'}</p>
                      <p><strong>Estimate Number of Guests:</strong> {formData.guestCount || 'Not specified'}</p>
                    </div>
                  </div>
                  <div className="mt-4 pt-3 border-t border-gray-200">
                    <p><strong>Event Venue:</strong></p>
                    <p className="ml-4">{formData.venueStreet}</p>
                    <p className="ml-4">{formData.venueCity}, {formData.venueState} {formData.venueZipcode}</p>
                  </div>
                  {!formData.sameAsVenue && (
                    <div className="mt-2">
                      <p><strong>Billing Address:</strong></p>
                      <p className="ml-4">{formData.addressStreet}</p>
                      <p className="ml-4">{formData.addressCity}, {formData.addressState} {formData.addressZipcode}</p>
                    </div>
                  )}
                  <div className="mt-4 pt-3 border-t border-gray-200 text-center">
                    <p className="font-medium text-red-600">
                      <strong>{formData.name}</strong> agrees with this My Hibachi Catering Agreement
                    </p>
                  </div>
                </div>
              </div>
            )}

            <div className="text-center mb-4">
              <p className="text-lg font-bold text-gray-900">By clicking &quot;Confirm Booking&quot;, you acknowledge that you have read and agree to all terms above</p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={handleAgreementCancel}
                className="flex-1 bg-gray-500 text-white py-3 px-4 rounded-lg font-medium hover:bg-gray-600 transition duration-200"
              >
                Cancel & Review Form
              </button>
              <button
                onClick={handleAgreementConfirm}
                className="flex-1 bg-red-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-red-700 transition duration-200"
              >
                ✅ Confirm Booking & Accept Agreement
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <>
      <ValidationModal />
      <AgreementModal />

      {/* Hero Section with Company Background */}
      <section className="page-hero-background py-20 text-white text-center">
        <div className="max-w-4xl mx-auto px-4">
          <div className="text-6xl mb-6">🍽️</div>
          <h1 className="text-5xl font-bold mb-6">Book Your Hibachi Experience</h1>
          <p className="text-xl mb-8 text-gray-200">Premium Japanese hibachi dining at your location</p>
          <div className="text-lg mb-12">
            <span className="bg-red-600 text-white px-4 py-2 rounded-full">Professional Catering Service</span>
          </div>
        </div>
      </section>

      {/* Booking Form Section */}
      <div className="py-16 section-background">
        <div className="max-w-4xl mx-auto px-4">
          <div className="bg-white rounded-2xl shadow-xl overflow-hidden">

          {/* Form */}
          <form onSubmit={handleSubmit(onSubmit)} className="p-8 space-y-8">
            {/* Form Progress Indicator */}
            <div className="bg-gradient-to-r from-blue-50 to-red-50 rounded-xl p-6 mb-8 mt-4 border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 text-center">📋 Booking Progress</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 md:gap-4 text-center">
                <div className="space-y-2">
                  <div className={`w-12 h-12 mx-auto rounded-full flex items-center justify-center text-xl font-bold ${
                    (watch('eventDate') && watch('eventTime')) ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-500'
                  }`}>
                    📅
                  </div>
                  <div className="text-sm">
                    <div className="font-medium">Date & Time</div>
                    <div className={`text-xs ${
                      (watch('eventDate') && watch('eventTime')) ? 'text-green-600' : 'text-gray-500'
                    }`}>
                      {(watch('eventDate') && watch('eventTime')) ? 'Complete' : 'Pending'}
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className={`w-12 h-12 mx-auto rounded-full flex items-center justify-center text-xl font-bold ${
                    (watch('name') && watch('email') && watch('phone')) ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-500'
                  }`}>
                    👤
                  </div>
                  <div className="text-sm">
                    <div className="font-medium">Customer Info</div>
                    <div className={`text-xs ${
                      (watch('name') && watch('email') && watch('phone')) ? 'text-green-600' : 'text-gray-500'
                    }`}>
                      {(watch('name') && watch('email') && watch('phone')) ? 'Complete' : 'Pending'}
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className={`w-12 h-12 mx-auto rounded-full flex items-center justify-center text-xl font-bold ${
                    (watch('venueStreet') && watch('venueCity') && watch('venueState') && watch('venueZipcode')) ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-500'
                  }`}>
                    🎪
                  </div>
                  <div className="text-sm">
                    <div className="font-medium">Event Venue</div>
                    <div className={`text-xs ${
                      (watch('venueStreet') && watch('venueCity') && watch('venueState') && watch('venueZipcode')) ? 'text-green-600' : 'text-gray-500'
                    }`}>
                      {(watch('venueStreet') && watch('venueCity') && watch('venueState') && watch('venueZipcode')) ? 'Complete' : 'Pending'}
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className={`w-12 h-12 mx-auto rounded-full flex items-center justify-center text-xl font-bold ${
                    (watch('sameAsVenue') || (watch('addressStreet') && watch('addressCity') && watch('addressState') && watch('addressZipcode'))) ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-500'
                  }`}>
                    💳
                  </div>
                  <div className="text-sm">
                    <div className="font-medium">Billing Address</div>
                    <div className={`text-xs ${
                      (watch('sameAsVenue') || (watch('addressStreet') && watch('addressCity') && watch('addressState') && watch('addressZipcode'))) ? 'text-green-600' : 'text-gray-500'
                    }`}>
                      {(watch('sameAsVenue') || (watch('addressStreet') && watch('addressCity') && watch('addressState') && watch('addressZipcode'))) ? 'Complete' : 'Pending'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Overall Progress Bar */}
              <div className="mt-6">
                <div className="flex justify-between text-sm text-gray-600 mb-2">
                  <span>Form Completion</span>
                  <span>{Math.round((
                    (watch('eventDate') && watch('eventTime') ? 1 : 0) +
                    (watch('name') && watch('email') && watch('phone') ? 1 : 0) +
                    (watch('venueStreet') && watch('venueCity') && watch('venueState') && watch('venueZipcode') ? 1 : 0) +
                    (watch('sameAsVenue') || (watch('addressStreet') && watch('addressCity') && watch('addressState') && watch('addressZipcode')) ? 1 : 0)
                  ) / 4 * 100)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className="bg-gradient-to-r from-blue-500 to-red-500 h-3 rounded-full transition-all duration-300"
                    style={{
                      width: `${(
                        (watch('eventDate') && watch('eventTime') ? 1 : 0) +
                        (watch('name') && watch('email') && watch('phone') ? 1 : 0) +
                        (watch('venueStreet') && watch('venueCity') && watch('venueState') && watch('venueZipcode') ? 1 : 0) +
                        (watch('sameAsVenue') || (watch('addressStreet') && watch('addressCity') && watch('addressState') && watch('addressZipcode')) ? 1 : 0)
                      ) / 4 * 100}%`
                    }}
                  ></div>
                </div>
              </div>
            </div>
            {/* Customer Information */}
            <div className="border-b pb-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-semibold text-gray-900">
                  👤 Customer Information
                </h2>
                <div className="text-sm">
                  {watch('name') && watch('email') && watch('phone') ? (
                    <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full font-semibold">
                      ✅ Complete
                    </span>
                  ) : (
                    <span className="bg-amber-100 text-amber-800 px-3 py-1 rounded-full">
                      ⏳ Pending
                    </span>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Full Name *
                  </label>
                  <input
                    {...register('name')}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                    placeholder="John Smith"
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
                    placeholder="john@example.com"
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

            {/* Date & Time Selection */}
            <div className="border-b pb-6">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                📅 Date & Time Selection
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Event Date *
                  </label>
                  <Controller
                    name="eventDate"
                    control={control}
                    render={({ field }) => (
                      <div className="relative">
                        <DatePicker
                          selected={field.value}
                          onChange={(date: Date | null) => {
                            setDateError(null)
                            field.onChange(date)
                          }}
                          minDate={addDays(new Date(), 2)} // 48 hours minimum
                          maxDate={addDays(new Date(), 730)} // 2 years maximum
                          excludeDates={bookedDates}
                          dateFormat="MMMM d, yyyy"
                          placeholderText="Select your event date"
                          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all duration-200"
                          calendarClassName="shadow-xl border border-gray-200"
                          wrapperClassName="w-full"
                          showPopperArrow={false}
                          autoComplete="off"
                          showYearDropdown
                          showMonthDropdown
                          dropdownMode="select"
                          yearDropdownItemNumber={3}
                          scrollableYearDropdown={false}
                          dayClassName={(date) => {
                            // Highlight selected date
                            if (field.value && date.toDateString() === field.value.toDateString()) {
                              return 'bg-red-500 text-white font-bold rounded'
                            }

                            // Style for booked dates
                            const isBooked = bookedDates.some(bookedDate =>
                              bookedDate.toDateString() === date.toDateString()
                            )

                            if (isBooked) {
                              return 'bg-red-100 text-red-400 line-through cursor-not-allowed'
                            }

                            return ''
                          }}
                          onSelect={(date: Date | null) => {
                            // Additional validation when user selects a date
                            if (!date) return

                            const now = new Date()
                            const timeDiff = date.getTime() - now.getTime()
                            const hoursDiff = timeDiff / (1000 * 60 * 60)

                            if (hoursDiff < 48) {
                              setDateError('Please select a date at least 48 hours in advance')
                              return
                            }

                            // Check if the date is booked
                            const isBooked = bookedDates.some(bookedDate =>
                              bookedDate.toDateString() === date.toDateString()
                            )

                            if (isBooked) {
                              setDateError('This date is fully booked. Please select another date.')
                              return
                            }

                            setDateError(null)
                          }}
                          filterDate={(date: Date) => {
                            // Filter out dates that don't meet our criteria
                            const now = new Date()
                            const timeDiff = date.getTime() - now.getTime()
                            const hoursDiff = timeDiff / (1000 * 60 * 60)

                            // Must be at least 48 hours in future
                            if (hoursDiff < 48) return false

                            // Only allow current year and future years (prevents previous year navigation)
                            if (date.getFullYear() < now.getFullYear()) return false

                            // Check if the date is booked
                            const isBooked = bookedDates.some(bookedDate =>
                              bookedDate.toDateString() === date.toDateString()
                            )

                            return !isBooked
                          }}
                        />
                        {loadingDates && (
                          <div className="absolute right-3 top-3">
                            <div className="animate-spin h-4 w-4 border-2 border-red-500 border-t-transparent rounded-full"></div>
                          </div>
                        )}
                      </div>
                    )}
                  />
                  <div className="text-sm mt-1 space-y-1">
                    <p className="text-gray-500">Must be at least 48 hours in advance</p>
                    {dateError && (
                      <p className="text-red-500 font-medium">⚠️ {dateError}</p>
                    )}
                    {loadingDates && (
                      <p className="text-blue-500">🔄 Loading available dates...</p>
                    )}
                    {bookedDates.length > 0 && !loadingDates && (
                      <p className="text-amber-600">📅 {bookedDates.length} date(s) are already booked and unavailable</p>
                    )}
                    {!loadingDates && bookedDates.length === 0 && (
                      <p className="text-green-600">✅ All future dates are available for booking</p>
                    )}
                  </div>
                  {errors.eventDate && (
                    <p className="text-red-500 text-sm mt-1">{errors.eventDate.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Event Time *
                  </label>
                  <Controller
                    name="eventTime"
                    control={control}
                    render={({ field }) => (
                      <select
                        {...field}
                        className={`w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all duration-200 ${
                          loadingTimeSlots ? 'animate-pulse bg-gray-100' : ''
                        } ${
                          field.value ? 'bg-green-50 border-green-300' : ''
                        }`}
                        disabled={loadingTimeSlots}
                      >
                        <option value="">
                          {loadingTimeSlots ? "⏳ Loading time slots..." : "🕐 Select a time"}
                        </option>
                        {availableTimeSlots.map((slot) => (
                          <option
                            key={slot.time}
                            value={slot.time}
                            disabled={!slot.isAvailable}
                            style={{
                              color: !slot.isAvailable ? '#9ca3af' : '#059669',
                              fontWeight: slot.isAvailable ? 'bold' : 'normal'
                            }}
                          >
                            {slot.isAvailable
                              ? `✅ ${slot.label} (${slot.available} slot${slot.available !== 1 ? 's' : ''} available)`
                              : `❌ ${slot.label} – Fully Booked`
                            }
                          </option>
                        ))}
                        {availableTimeSlots.length === 0 && selectedDate && !loadingTimeSlots && (
                          <option disabled>⚠️ No time slots available for this date</option>
                        )}
                      </select>
                    )}
                  />
                  {errors.eventTime && (
                    <p className="text-red-500 text-sm mt-1">{errors.eventTime.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Estimate Number of Guests *
                  </label>
                  <Controller
                    name="guestCount"
                    control={control}
                    render={({ field }) => (
                      <input
                        type="number"
                        min="1"
                        value={field.value || ''}
                        onChange={(e) => field.onChange(e.target.value ? parseInt(e.target.value) : undefined)}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                        placeholder="Enter estimated guest count"
                      />
                    )}
                  />
                  {errors.guestCount && (
                    <p className="text-red-500 text-sm mt-1">{errors.guestCount.message}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Event Venue - Now above Billing Address */}
            <div className="border-b pb-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-semibold text-gray-900">
                  🎪 Event Venue
                </h2>
                <div className="text-sm">
                  {watch('venueStreet') && watch('venueCity') && watch('venueState') && watch('venueZipcode') ? (
                    <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full font-semibold">
                      ✅ Complete
                    </span>
                  ) : (
                    <span className="bg-amber-100 text-amber-800 px-3 py-1 rounded-full">
                      ⏳ Pending
                    </span>
                  )}
                </div>
              </div>

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
                    City *
                  </label>
                  <input
                    {...register('venueCity')}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                    placeholder="Event City"
                  />
                  {errors.venueCity && (
                    <p className="text-red-500 text-sm mt-1">{errors.venueCity.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    State *
                  </label>
                  <input
                    {...register('venueState')}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                    placeholder="ST"
                    maxLength={2}
                  />
                  {errors.venueState && (
                    <p className="text-red-500 text-sm mt-1">{errors.venueState.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    ZIP Code *
                  </label>
                  <input
                    {...register('venueZipcode')}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                    placeholder="12345"
                    maxLength={10}
                  />
                  {errors.venueZipcode && (
                    <p className="text-red-500 text-sm mt-1">{errors.venueZipcode.message}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Billing Address - Changed from Customer Address */}
            <div className="border-b pb-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-semibold text-gray-900">
                  💳 Billing Address
                </h2>
                <div className="text-sm">
                  {(watch('sameAsVenue') || (watch('addressStreet') && watch('addressCity') && watch('addressState') && watch('addressZipcode'))) ? (
                    <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full font-semibold">
                      ✅ Complete
                    </span>
                  ) : (
                    <span className="bg-amber-100 text-amber-800 px-3 py-1 rounded-full">
                      ⏳ Pending
                    </span>
                  )}
                </div>
              </div>

              {/* Checkbox - Disabled until venue address is complete */}
              <div className="mb-4">
                <label className={`flex items-center space-x-3 ${isVenueAddressComplete ? 'cursor-pointer' : 'cursor-not-allowed'}`}>
                  <Controller
                    name="sameAsVenue"
                    control={control}
                    render={({ field }) => (
                      <input
                        type="checkbox"
                        checked={field.value}
                        onChange={field.onChange}
                        disabled={!isVenueAddressComplete}
                        className={`w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500 focus:ring-2 ${
                          !isVenueAddressComplete ? 'opacity-50 cursor-not-allowed' : ''
                        }`}
                      />
                    )}
                  />
                  <span className={`text-sm font-medium ${isVenueAddressComplete ? 'text-gray-700' : 'text-gray-400'}`}>
                    Billing address is the same as Event Venue address
                  </span>
                </label>
                {!isVenueAddressComplete && (
                  <p className="text-amber-600 text-sm mt-2 ml-7">
                    ⚠️ Please complete the Event Venue address above to use this option
                  </p>
                )}
              </div>

              {/* Show minimized summary when checkbox is checked */}
              {sameAsVenue && isVenueAddressComplete ? (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="text-green-600 font-medium">✓ Billing address is the same as venue address:</span>
                  </div>
                  <div className="text-sm text-gray-700">
                    <p><strong>{venueStreet}</strong></p>
                    <p>{venueCity}, {venueState} {venueZipcode}</p>
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Street Address *
                    </label>
                    <input
                      {...register('addressStreet')}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                      placeholder="123 Main Street"
                      disabled={sameAsVenue}
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
                      placeholder="Your City"
                      disabled={sameAsVenue}
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
                      placeholder="ST"
                      maxLength={2}
                      disabled={sameAsVenue}
                    />
                    {errors.addressState && (
                      <p className="text-red-500 text-sm mt-1">{errors.addressState.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      ZIP Code *
                    </label>
                    <input
                      {...register('addressZipcode')}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                      placeholder="12345"
                      maxLength={10}
                      disabled={sameAsVenue}
                    />
                    {errors.addressZipcode && (
                      <p className="text-red-500 text-sm mt-1">{errors.addressZipcode.message}</p>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Submit Button */}
            <div className="text-center">
              {/* Form completion status */}
              {(
                (watch('eventDate') && watch('eventTime') ? 1 : 0) +
                (watch('name') && watch('email') && watch('phone') ? 1 : 0) +
                (watch('venueStreet') && watch('venueCity') && watch('venueState') && watch('venueZipcode') ? 1 : 0) +
                (watch('sameAsVenue') || (watch('addressStreet') && watch('addressCity') && watch('addressState') && watch('addressZipcode')) ? 1 : 0)
              ) < 4 && (
                <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                  <p className="text-amber-800 text-sm flex items-center justify-center">
                    <span className="mr-2">⚠️</span>
                    Please complete all required sections above to submit your booking
                  </p>
                </div>
              )}

              <button
                type="submit"
                disabled={
                  (
                    (watch('eventDate') && watch('eventTime') ? 1 : 0) +
                    (watch('name') && watch('email') && watch('phone') ? 1 : 0) +
                    (watch('venueStreet') && watch('venueCity') && watch('venueState') && watch('venueZipcode') ? 1 : 0) +
                    (watch('sameAsVenue') || (watch('addressStreet') && watch('addressCity') && watch('addressState') && watch('addressZipcode')) ? 1 : 0)
                  ) < 4 || isSubmitting
                }
                className={`px-8 py-4 rounded-lg text-lg font-semibold transition duration-200 shadow-lg transform ${
                  (
                    (watch('eventDate') && watch('eventTime') ? 1 : 0) +
                    (watch('name') && watch('email') && watch('phone') ? 1 : 0) +
                    (watch('venueStreet') && watch('venueCity') && watch('venueState') && watch('venueZipcode') ? 1 : 0) +
                    (watch('sameAsVenue') || (watch('addressStreet') && watch('addressCity') && watch('addressState') && watch('addressZipcode')) ? 1 : 0)
                  ) === 4 && !isSubmitting
                    ? 'bg-gradient-to-r from-red-600 to-red-700 text-white hover:from-red-700 hover:to-red-800 hover:shadow-xl hover:scale-105 cursor-pointer'
                    : 'bg-gray-500 text-gray-100 cursor-not-allowed'
                }`}
              >
                {isSubmitting ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Processing Booking...
                  </span>
                ) : (
                  (
                    (watch('eventDate') && watch('eventTime') ? 1 : 0) +
                    (watch('name') && watch('email') && watch('phone') ? 1 : 0) +
                    (watch('venueStreet') && watch('venueCity') && watch('venueState') && watch('venueZipcode') ? 1 : 0) +
                    (watch('sameAsVenue') || (watch('addressStreet') && watch('addressCity') && watch('addressState') && watch('addressZipcode')) ? 1 : 0)
                  ) === 4
                    ? '🔥 Book Your Hibachi Experience'
                    : '📝 Complete Form to Continue'
                )}
              </button>

              {/* Form completion summary */}
              <div className="mt-4 text-sm text-gray-600">
                <div className="flex flex-wrap justify-center items-center gap-2">
                  <span className={`px-2 py-1 rounded text-xs ${(watch('eventDate') && watch('eventTime')) ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-500'}`}>
                    📅 Date & Time
                  </span>
                  <span className={`px-2 py-1 rounded text-xs ${(watch('name') && watch('email') && watch('phone')) ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-500'}`}>
                    👤 Customer Info
                  </span>
                  <span className={`px-2 py-1 rounded text-xs ${(watch('venueStreet') && watch('venueCity') && watch('venueState') && watch('venueZipcode')) ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-500'}`}>
                    🎪 Venue
                  </span>
                  <span className={`px-2 py-1 rounded text-xs ${(watch('sameAsVenue') || (watch('addressStreet') && watch('addressCity') && watch('addressState') && watch('addressZipcode'))) ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-500'}`}>
                    💳 Billing
                  </span>
                </div>
              </div>
            </div>
          </form>
        </div>
      </div>
      </div>

      <Assistant page="/BookUs" />
    </>
  )
}
