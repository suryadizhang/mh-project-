import { UseFormRegister, Control, FieldErrors } from 'react-hook-form'

// Type definitions for booking form
export type BookingFormData = {
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

export type TimeSlot = {
  time: string
  label: string
  available: number
  isAvailable: boolean
}

export type FormSectionProps = {
  register: UseFormRegister<BookingFormData>
  errors: FieldErrors<BookingFormData>
}

export type BookingModalProps = {
  showValidationModal: boolean
  setShowValidationModal: (show: boolean) => void
  showAgreementModal: boolean
  setShowAgreementModal: (show: boolean) => void
  missingFields: string[]
  isSubmitting: boolean
  onAgreementConfirm: () => void
  onAgreementCancel: () => void
}

export type EventDetailsSectionProps = {
  register: UseFormRegister<BookingFormData>
  control: Control<BookingFormData>
  errors: FieldErrors<BookingFormData>
  loadingDates: boolean
  dateError: string | null
  availableTimeSlots: TimeSlot[]
  loadingTimeSlots: boolean
  isDateDisabled: (date: Date) => boolean
}

export type CustomerAddressSectionProps = {
  register: UseFormRegister<BookingFormData>
  errors: FieldErrors<BookingFormData>
  sameAsVenue: boolean
}

export type VenueAddressSectionProps = {
  register: UseFormRegister<BookingFormData>
  errors: FieldErrors<BookingFormData>
}

export type SubmitSectionProps = {
  isSubmitting: boolean
}
