'use client';

import './datepicker.css';

import {
  AvailabilityResponseSchema,
  BookedDatesResponseSchema,
  BookingSubmitResponseSchema,
} from '@myhibachi/types/schemas';
import { addDays, format } from 'date-fns';
import Link from 'next/link';
import React, { useEffect, useRef, useState } from 'react';
import { Controller, useForm } from 'react-hook-form';
import type { z } from 'zod';

import { LazyDatePicker } from '@/components/ui/LazyDatePicker';
import { useProtectedPhone, ProtectedEmail } from '@/components/ui/ProtectedPhone';
import { apiFetch } from '@/lib/api';
import { logger } from '@/lib/logger';
import type { TimeSlot as TimeSlotType } from '@/types/data';

// Google Maps types - extend Window interface
interface GoogleMapsAutocomplete {
  addListener: (event: string, callback: () => void) => void;
  getPlace: () => {
    formatted_address?: string;
    address_components?: Array<{
      long_name: string;
      short_name: string;
      types: string[];
    }>;
  };
}

interface AutocompleteOptions {
  componentRestrictions?: { country: string };
  types?: string[];
  fields?: string[];
}

declare global {
  interface Window {
    google?: {
      maps: {
        places: {
          Autocomplete: new (
            input: HTMLInputElement,
            options?: AutocompleteOptions,
          ) => GoogleMapsAutocomplete;
        };
        event: {
          clearInstanceListeners: (instance: object) => void;
        };
      };
    };
  }
}

// Infer types from schemas for type-safe responses
type BookedDatesResponse = z.infer<typeof BookedDatesResponseSchema>;
type AvailabilityResponse = z.infer<typeof AvailabilityResponseSchema>;
type BookingSubmitResponse = z.infer<typeof BookingSubmitResponseSchema>;

// Type definitions for booking form
type TimeSlot = {
  time: string;
  label: string;
  available: number;
  isAvailable: boolean;
};
type BookingFormData = {
  name: string;
  email: string;
  phone: string;
  preferredCommunication: 'phone' | 'text' | 'email' | '';
  smsConsent?: boolean;
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
};
export default function BookingPage() {
  // Anti-scraper protected contact info
  const { formatted: protectedPhone, tel: protectedTel } = useProtectedPhone();

  const [showValidationModal, setShowValidationModal] = useState(false);
  const [missingFields, setMissingFields] = useState<string[]>([]);
  const [showAgreementModal, setShowAgreementModal] = useState(false);
  const [formData, setFormData] = useState<BookingFormData | null>(null);
  const [bookedDates, setBookedDates] = useState<Date[]>([]);
  const [loadingDates, setLoadingDates] = useState(false);
  const [dateError, setDateError] = useState<string | null>(null);
  const [availableTimeSlots, setAvailableTimeSlots] = useState<TimeSlot[]>([]);
  const [loadingTimeSlots, setLoadingTimeSlots] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Google Places Autocomplete refs - use mutable ref for callback ref pattern
  const venueAddressInputRef = useRef<HTMLInputElement | null>(null);
  const autocompleteRef = useRef<GoogleMapsAutocomplete | null>(null);

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
      preferredCommunication: '',
      smsConsent: false,
    },
  });

  // Extract venueStreet register to merge with autocomplete ref
  const { ref: venueStreetFormRef, ...venueStreetRegister } = register('venueStreet');

  // Watch form values
  const sameAsVenue = watch('sameAsVenue');
  const venueStreet = watch('venueStreet');
  const venueCity = watch('venueCity');
  const venueState = watch('venueState');
  const venueZipcode = watch('venueZipcode');
  const selectedDate = watch('eventDate');
  // Fetch booked dates from API
  const fetchBookedDates = async () => {
    setLoadingDates(true);
    setDateError(null);
    try {
      const result = await apiFetch<BookedDatesResponse>('/api/v1/bookings/booked-dates', {
        schema: BookedDatesResponseSchema,
        cacheStrategy: {
          strategy: 'cache-first',
          ttl: 5 * 60 * 1000, // 5 minutes
        },
      });

      if (result.success && result.data) {
        // Type-safe access to bookedDates
        const dates = result.data.data.bookedDates.map((dateStr: string) => new Date(dateStr));
        setBookedDates(dates);
      } else {
        logger.warn('Could not fetch booked dates, continuing without blocking dates');
        setBookedDates([]);
      }
    } catch (error) {
      logger.warn('Error fetching booked dates', { error });
      setBookedDates([]);
    } finally {
      setLoadingDates(false);
    }
  };
  // Fetch booked dates on component mount
  useEffect(() => {
    fetchBookedDates();
  }, []);

  // Pre-fill form from quote calculator sessionStorage data
  useEffect(() => {
    try {
      const storedData = sessionStorage.getItem('quoteBookingData');
      if (storedData) {
        const quoteData = JSON.parse(storedData);

        // Pre-fill form fields
        if (quoteData.name) setValue('name', quoteData.name);
        if (quoteData.phone) setValue('phone', quoteData.phone);
        if (quoteData.guestCount) setValue('guestCount', quoteData.guestCount);
        if (quoteData.venueAddress) setValue('venueStreet', quoteData.venueAddress);
        if (quoteData.venueCity) setValue('venueCity', quoteData.venueCity);
        if (quoteData.venueZipcode) setValue('venueZipcode', quoteData.venueZipcode);

        // Pre-fill date and time if available
        if (quoteData.eventDate) {
          const eventDate = new Date(quoteData.eventDate);
          setValue('eventDate', eventDate);
        }
        if (quoteData.eventTime) {
          setValue('eventTime', quoteData.eventTime as '12PM' | '3PM' | '6PM' | '9PM');
        }

        // Clear the sessionStorage after reading (one-time use)
        sessionStorage.removeItem('quoteBookingData');

        // Log for tracking
        console.log('📋 Pre-filled booking form from quote calculator');
      }
    } catch (error) {
      console.warn('Could not read quote data from sessionStorage', error);
    }
  }, [setValue]);

  // Initialize Google Places Autocomplete for venue address
  useEffect(() => {
    const initializeAutocomplete = () => {
      if (!venueAddressInputRef.current || !window.google) return;

      try {
        // Initialize autocomplete with US-only restriction
        autocompleteRef.current = new window.google.maps.places.Autocomplete(
          venueAddressInputRef.current,
          {
            types: ['address'],
            componentRestrictions: { country: 'us' },
            fields: ['formatted_address', 'address_components', 'geometry'],
          },
        );

        // Listen for place selection
        autocompleteRef.current.addListener('place_changed', () => {
          const place = autocompleteRef.current?.getPlace();
          if (!place || !place.formatted_address) return;

          // Set the full formatted address
          setValue('venueStreet', place.formatted_address);

          // Extract city, state, and ZIP from address components
          if (place.address_components) {
            let city = '';
            let state = '';
            let zipCode = '';

            place.address_components.forEach(
              (component: { types: string[]; long_name: string; short_name: string }) => {
                const types = component.types;
                if (types.includes('locality')) {
                  city = component.long_name;
                } else if (types.includes('administrative_area_level_1')) {
                  state = component.short_name;
                } else if (types.includes('postal_code')) {
                  zipCode = component.long_name;
                }
              },
            );

            // Auto-fill city, state, and ZIP
            if (city) setValue('venueCity', city);
            if (state) setValue('venueState', state);
            if (zipCode) setValue('venueZipcode', zipCode);
          }
        });
      } catch (error) {
        logger.error('Error initializing Google Places Autocomplete', error as Error);
      }
    };

    // Load Google Maps script if not already loaded
    if (!window.google) {
      const script = document.createElement('script');
      script.src = `https://maps.googleapis.com/maps/api/js?key=${process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY}&libraries=places`;
      script.async = true;
      script.defer = true;
      script.onload = initializeAutocomplete;
      script.onerror = () => {
        logger.error('Failed to load Google Maps script', new Error('Script load failed'));
      };
      document.head.appendChild(script);
    } else {
      initializeAutocomplete();
    }
  }, [setValue]);

  // Fetch availability for selected date
  const fetchAvailability = async (date: Date) => {
    setLoadingTimeSlots(true);
    setDateError(null);
    try {
      const dateStr = format(date, 'yyyy-MM-dd');
      const response = await apiFetch<AvailabilityResponse>(
        `/api/v1/bookings/availability?date=${dateStr}`,
        {
          schema: AvailabilityResponseSchema,
          cacheStrategy: {
            strategy: 'cache-first',
            ttl: 3 * 60 * 1000, // 3 minutes
          },
        },
      );

      if (response.success && response.data) {
        // Type-safe access to timeSlots
        const formattedSlots = response.data.data.timeSlots.map((slot: TimeSlotType) => ({
          time: slot.time,
          label:
            slot.time === '12PM'
              ? '12:00 PM'
              : slot.time === '3PM'
                ? '3:00 PM'
                : slot.time === '6PM'
                  ? '6:00 PM'
                  : '9:00 PM',
          available: slot.available,
          isAvailable: slot.isAvailable,
        }));
        setAvailableTimeSlots(formattedSlots);
      } else {
        logger.warn('Could not fetch availability, using default slots');
        setAvailableTimeSlots([]);
      }
    } catch (error) {
      logger.warn('Error fetching availability', { error });
      setAvailableTimeSlots([]);
    } finally {
      setLoadingTimeSlots(false);
    }
  };
  // Fetch availability when date changes
  useEffect(() => {
    if (selectedDate) {
      fetchAvailability(selectedDate);
    } else {
      setAvailableTimeSlots([]);
    }
  }, [selectedDate]);
  // Check if venue address is completely filled
  const isVenueAddressComplete = venueStreet && venueCity && venueState && venueZipcode;
  // Auto-fill billing address when checkbox is checked and venue address is complete
  useEffect(() => {
    if (sameAsVenue && isVenueAddressComplete) {
      setValue('addressStreet', venueStreet);
      setValue('addressCity', venueCity);
      setValue('addressState', venueState);
      setValue('addressZipcode', venueZipcode);
    }
  }, [
    sameAsVenue,
    venueStreet,
    venueCity,
    venueState,
    venueZipcode,
    isVenueAddressComplete,
    setValue,
  ]);
  // Automatically uncheck if venue address becomes incomplete
  useEffect(() => {
    if (sameAsVenue && !isVenueAddressComplete) {
      setValue('sameAsVenue', false);
    }
  }, [sameAsVenue, isVenueAddressComplete, setValue]);
  // Enhanced onSubmit with comprehensive validation
  const onSubmit = async (data: BookingFormData) => {
    setIsSubmitting(true);
    try {
      // Check for missing fields
      const missing: string[] = [];
      if (!data.name || data.name.length < 2) missing.push('Full Name');
      if (!data.email) missing.push('Email Address');
      if (!data.phone || data.phone.length < 10) missing.push('Phone Number');
      if (!data.preferredCommunication) missing.push('Preferred Communication Method');
      if (!data.eventDate) missing.push('Event Date');
      if (!data.eventTime) missing.push('Event Time');
      if (!data.guestCount || data.guestCount < 1) missing.push('Estimate Number of Guests');
      // Check venue address
      if (!data.venueStreet) missing.push('Venue Street Address');
      if (!data.venueCity) missing.push('Venue City');
      if (!data.venueState) missing.push('Venue State');
      if (!data.venueZipcode) missing.push('Venue ZIP Code');
      // Check billing address (only if not same as venue)
      if (!data.sameAsVenue) {
        if (!data.addressStreet) missing.push('Billing Street Address');
        if (!data.addressCity) missing.push('Billing City');
        if (!data.addressState) missing.push('Billing State');
        if (!data.addressZipcode) missing.push('Billing ZIP Code');
      }
      // If there are missing fields, show modal
      if (missing.length > 0) {
        setMissingFields(missing);
        setShowValidationModal(true);
        return;
      }
      // Additional validation: Check if selected time slot is still available
      if (data.eventDate && data.eventTime) {
        try {
          const dateStr = format(data.eventDate, 'yyyy-MM-dd');
          const response = await fetch(`/api/v1/bookings/availability?date=${dateStr}`);
          if (response.ok) {
            const availabilityData = await response.json();
            const selectedSlot = availabilityData.timeSlots.find(
              (slot: { time: string; isAvailable: boolean }) => slot.time === data.eventTime,
            );
            if (!selectedSlot || !selectedSlot.isAvailable) {
              setDateError(
                `The ${data.eventTime} time slot is no longer available. Please select a different time.`,
              );
              return;
            }
          }
        } catch (error) {
          logger.warn('Could not verify slot availability', { error });
          // Continue with booking as a fallback
        }
      }
      // If all validation passes, show agreement modal
      setFormData(data);
      setShowAgreementModal(true);
    } catch (error) {
      logger.error('Form submission error', error as Error);
      setDateError('An unexpected error occurred. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };
  // Handle agreement confirmation with actual booking submission
  const handleAgreementConfirm = async () => {
    if (!formData) return;
    try {
      const bookingData = {
        date: format(formData.eventDate, 'yyyy-MM-dd'),
        time: formData.eventTime,
        customerInfo: {
          name: formData.name,
          email: formData.email,
          phone: formData.phone,
          preferredCommunication: formData.preferredCommunication,
          smsConsent: formData.smsConsent || false,
          guestCount: formData.guestCount,
          venueAddress: {
            street: formData.venueStreet,
            city: formData.venueCity,
            state: formData.venueState,
            zipcode: formData.venueZipcode,
          },
          billingAddress: formData.sameAsVenue
            ? null
            : {
                street: formData.addressStreet,
                city: formData.addressCity,
                state: formData.addressState,
                zipcode: formData.addressZipcode,
              },
        },
      };
      const response = await apiFetch<BookingSubmitResponse>('/api/v1/bookings/availability', {
        method: 'POST',
        body: JSON.stringify(bookingData),
        schema: BookingSubmitResponseSchema,
      });

      if (response.success && response.data?.data) {
        setShowAgreementModal(false);
        setFormData(null);
        // Type-safe access to bookingId
        const bookingId = response.data.data.bookingId;
        alert(
          `Booking Confirmed!\n\nConfirmation Code: ${bookingId}\n\nWe will contact you soon at ${formData.email} to finalize your hibachi experience details.\n\nThank you for choosing My Hibachi!`,
        );
        // Reset form
        window.location.reload();
      } else {
        // Handle booking errors
        const errorData = response.data as Record<string, unknown> | undefined;
        if (errorData?.code === 'SLOT_FULL') {
          setShowAgreementModal(false);
          setDateError('This time slot just became fully booked. Please select a different time.');
          // Refresh availability data
          if (formData.eventDate) {
            fetchAvailability(formData.eventDate);
          }
        } else {
          alert(
            `❌ Booking Failed\n\n${
              response.error || 'Please try again or contact support.'
            }\n\nYour information has been preserved.`,
          );
        }
      }
    } catch (error) {
      logger.error('Booking submission error', error as Error);
      alert(
        '❌ Network Error\n\nPlease check your connection and try again.\nYour information has been preserved.',
      );
    }
  };
  const handleAgreementCancel = () => {
    setShowAgreementModal(false);
    setFormData(null);
  };
  // Validation Modal Component
  const ValidationModal = () => {
    if (!showValidationModal) return null;
    return (
      <div
        className="bg-opacity-50 fixed inset-0 flex items-center justify-center bg-black p-4"
        style={{ zIndex: 1040 }}
      >
        <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-2xl">
          <div className="mb-4 text-center">
            <div className="mb-2 text-4xl">⚠️</div>
            <h3 className="text-xl font-bold text-red-600">Please Complete Your Booking</h3>
            <p className="mt-2 text-gray-600">The following fields are required:</p>
          </div>
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4">
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
              className="flex-1 rounded-lg bg-red-600 px-4 py-3 font-medium text-white transition duration-200 hover:bg-red-700"
            >
              Got it, I&apos;ll complete the form
            </button>
          </div>
        </div>
      </div>
    );
  };
  // Agreement Modal Component
  const AgreementModal = () => {
    if (!showAgreementModal) return null;
    return (
      <div
        className="bg-opacity-50 fixed inset-0 flex items-center justify-center bg-black p-4"
        style={{ zIndex: 1040 }}
      >
        <div className="max-h-[90vh] w-full max-w-4xl overflow-hidden rounded-xl bg-white shadow-2xl">
          <div className="bg-red-600 p-6 text-center text-white">
            <div className="mb-2 text-4xl">📋</div>
            <h3 className="text-2xl font-bold">My Hibachi Catering Agreement</h3>
            <p className="mt-2 text-red-100">Please review and confirm the terms below</p>
          </div>
          <div className="max-h-[50vh] overflow-y-auto p-6">
            <div className="space-y-6 text-sm">
              <div>
                <h4 className="mb-2 font-bold text-red-600">1. SERVICES</h4>
                <p className="mb-2 text-gray-700">
                  My Hibachi will provide hibachi catering services at the Customer&apos;s location
                  on [Event Date] from [Start Time] to approximately [End Time]. We will bring a
                  private chef, all cooking equipment, and fresh food ingredients.
                </p>
                <p className="text-gray-600 italic">
                  Note: We do not provide table setup, chairs, plates, or utensils. Customers are
                  responsible for arranging seating and place settings.
                </p>
              </div>
              <div>
                <h4 className="mb-2 font-bold text-red-600">2. CUSTOMER RESPONSIBILITIES</h4>
                <p className="mb-2 text-gray-700">Customer must provide:</p>
                <ul className="ml-4 list-inside list-disc space-y-1 text-gray-700">
                  <li>Tables, chairs, and dining utensils (plates, napkins, forks, etc.)</li>
                  <li>Safe, level space for outdoor cooking (patio, driveway, etc.)</li>
                  <li>Adequate lighting for evening events</li>
                  <li>Covering in case of rain (e.g., tent or covered patio)</li>
                  <li>Parking and venue access for setup</li>
                  <li>Confirmed guest count and food selections</li>
                </ul>
              </div>
              <div>
                <h4 className="mb-2 font-bold text-red-600">3. MENU, HEADCOUNT & FINAL DETAILS</h4>
                <ul className="list-inside list-disc space-y-1 text-gray-700">
                  <li>
                    Food orders and headcount must be confirmed via text or email the week of the
                    event.
                  </li>
                  <li>
                    Final protein choices must be submitted at least 2 days before the event. If not
                    received, default proteins (chicken and steak) will be served.
                  </li>
                  <li>Menu changes allowed up to 48 hours prior.</li>
                  <li>Guest additions allowed up to 24 hours prior.</li>
                  <li>
                    Same-day changes are not allowed. The full confirmed order will be charged
                    regardless of attendance.
                  </li>
                </ul>
              </div>
              <div>
                <h4 className="mb-2 font-bold text-red-600">4. PAYMENT TERMS</h4>
                <ul className="list-inside list-disc space-y-1 text-gray-700">
                  <li>
                    Deposit: $100 (refundable if canceled 7+ days before event, required to reserve
                    your date)
                  </li>
                  <li>Remaining balance: Due on or before the event date</li>
                  <li>Accepted payments: Venmo Business, Zelle Business, Cash, or Card</li>
                </ul>
              </div>
              <div>
                <h4 className="mb-2 font-bold text-red-600">5. CANCELLATION & WEATHER POLICY</h4>
                <ul className="list-inside list-disc space-y-1 text-gray-700">
                  <li>Full refund if canceled at least 7 days before the event</li>
                  <li>
                    One-time reschedule allowed within 48 hours; otherwise, a $100 rescheduling fee
                    applies
                  </li>
                  <li>
                    Customer must provide overhead covering in the event of rain. Unsafe/uncovered
                    setups may lead to cancellation without refund.
                  </li>
                </ul>
              </div>
              <div>
                <h4 className="mb-2 font-bold text-red-600">6. LIABILITY WAIVER</h4>
                <p className="mb-2 font-medium text-gray-700">
                  PLEASE TAKE NOTICE: My Hibachi and its agents, employees, or representatives will
                  NOT be liable to any Host or guests for property damage or personal injury
                  resulting from the event.
                </p>
                <ul className="list-inside list-disc space-y-1 text-gray-700">
                  <li>
                    Property damage includes injury to any real or personal property at the event
                    site.
                  </li>
                  <li>
                    Host and guests waive any claim for loss, damage, or destruction of property
                    before, during, or after the event.
                  </li>
                </ul>
              </div>
              <div>
                <h4 className="mb-2 font-bold text-red-600">7. FORCE MAJEURE</h4>
                <p className="text-gray-700">
                  Neither party shall be held liable for failure to perform due to events beyond
                  their reasonable control including but not limited to illness, accidents, fire,
                  flood, government restrictions, or natural disasters.
                </p>
              </div>
              <div>
                <h4 className="mb-2 font-bold text-red-600">8. FOOD SAFETY & ALLERGIES</h4>
                <ul className="list-inside list-disc space-y-1 text-gray-700">
                  <li>
                    Customer is responsible for notifying Caterer of any food allergies at least 48
                    hours in advance.
                  </li>
                  <li>
                    My Hibachi is not liable for allergic reactions due to undisclosed sensitivities
                    or customer-supplied ingredients.
                  </li>
                </ul>
              </div>
              {/* Customer Details Confirmation */}
              {formData && (
                <div className="mt-6 rounded-lg border border-gray-200 bg-white p-4">
                  <h4 className="mb-3 text-center font-bold text-gray-900">
                    Customer Agreement Confirmation
                  </h4>
                  <div className="space-y-2 text-sm text-gray-700">
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                      <div>
                        <p>
                          <strong>Customer Name:</strong> {formData.name}
                        </p>
                        <p>
                          <strong>Email:</strong> {formData.email}
                        </p>
                        <p>
                          <strong>Phone:</strong> {formData.phone}
                        </p>
                        <p>
                          <strong>Preferred Contact:</strong>{' '}
                          {formData.preferredCommunication === 'phone'
                            ? '📞 Phone Call'
                            : formData.preferredCommunication === 'text'
                              ? '💬 Text Message'
                              : formData.preferredCommunication === 'email'
                                ? '📧 Email'
                                : 'Not specified'}
                        </p>
                      </div>
                      <div>
                        <p>
                          <strong>Event Date:</strong>{' '}
                          {formData.eventDate
                            ? format(new Date(formData.eventDate), 'MMMM dd, yyyy')
                            : 'Not selected'}
                        </p>
                        <p>
                          <strong>Event Time:</strong> {formData.eventTime || 'Not selected'}
                        </p>
                        <p>
                          <strong>Estimate Number of Guests:</strong>{' '}
                          {formData.guestCount || 'Not specified'}
                        </p>
                      </div>
                    </div>
                    <div className="mt-4 border-t border-gray-200 pt-3">
                      <p>
                        <strong>Event Venue:</strong>
                      </p>
                      <p className="ml-4">{formData.venueStreet}</p>
                      <p className="ml-4">
                        {formData.venueCity}, {formData.venueState} {formData.venueZipcode}
                      </p>
                    </div>
                    {!formData.sameAsVenue && (
                      <div className="mt-2">
                        <p>
                          <strong>Billing Address:</strong>
                        </p>
                        <p className="ml-4">{formData.addressStreet}</p>
                        <p className="ml-4">
                          {formData.addressCity}, {formData.addressState} {formData.addressZipcode}
                        </p>
                      </div>
                    )}
                    <div className="mt-4 border-t border-gray-200 pt-3 text-center">
                      <p className="font-medium text-red-600">
                        <strong>{formData.name}</strong> agrees with this My Hibachi Catering
                        Agreement
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
          {/* Fixed Footer with Buttons */}
          <div className="border-t border-gray-200 bg-gray-50 p-6">
            <div className="mb-4 text-center">
              <p className="text-lg font-bold text-gray-900">
                By clicking &quot;Confirm Booking&quot;, you acknowledge that you have read and
                agree to all terms above
              </p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={handleAgreementCancel}
                className="flex-1 rounded-lg bg-gray-500 px-4 py-3 font-medium text-white transition duration-200 hover:bg-gray-600"
              >
                Cancel & Review Form
              </button>
              <button
                onClick={handleAgreementConfirm}
                className="flex-1 rounded-lg bg-red-600 px-4 py-3 font-medium text-white transition duration-200 hover:bg-red-700"
              >
                ✅ Confirm Booking & Accept Agreement
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };
  return (
    <>
      <ValidationModal />
      <AgreementModal />
      {/* Hero Section with Company Background */}
      <section className="page-hero-background py-10 text-center text-white">
        <div className="mx-auto max-w-4xl px-4">
          <div className="mb-3 text-4xl">🍽️</div>
          <h1 className="mb-3 text-3xl font-bold">Book Your Hibachi Experience</h1>
          <p className="mb-4 text-base text-gray-200">
            Premium Japanese hibachi dining at your location
          </p>
          <div className="mb-6 text-sm">
            <span className="rounded-full bg-red-600 px-3 py-1.5 text-white">
              Professional Catering Service
            </span>
          </div>
        </div>
      </section>
      {/* Booking Form Section */}
      <div className="section-background py-8">
        <div className="mx-auto max-w-4xl px-4">
          <div className="overflow-hidden rounded-xl bg-white shadow-xl">
            {/* Form */}
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 p-5">
              {/* Form Progress Indicator - Compact */}
              <div className="mt-2 mb-4 rounded-lg border border-gray-200 bg-gradient-to-r from-blue-50 to-red-50 p-4">
                <h3 className="mb-3 text-center text-base font-semibold text-gray-900">
                  📋 Booking Progress
                </h3>
                <div className="grid grid-cols-4 gap-2 text-center">
                  <div className="space-y-1">
                    <div
                      className={`mx-auto flex h-9 w-9 items-center justify-center rounded-full text-base font-bold ${
                        watch('eventDate') && watch('eventTime')
                          ? 'bg-green-500 text-white'
                          : 'bg-gray-200 text-gray-500'
                      }`}
                    >
                      📅
                    </div>
                    <div className="text-xs">
                      <div className="font-medium">Date/Time</div>
                    </div>
                  </div>
                  <div className="space-y-1">
                    <div
                      className={`mx-auto flex h-9 w-9 items-center justify-center rounded-full text-base font-bold ${
                        watch('name') &&
                        watch('email') &&
                        watch('phone') &&
                        watch('preferredCommunication')
                          ? 'bg-green-500 text-white'
                          : 'bg-gray-200 text-gray-500'
                      }`}
                    >
                      👤
                    </div>
                    <div className="text-xs">
                      <div className="font-medium">Info</div>
                    </div>
                  </div>
                  <div className="space-y-1">
                    <div
                      className={`mx-auto flex h-9 w-9 items-center justify-center rounded-full text-base font-bold ${
                        watch('venueStreet') &&
                        watch('venueCity') &&
                        watch('venueState') &&
                        watch('venueZipcode')
                          ? 'bg-green-500 text-white'
                          : 'bg-gray-200 text-gray-500'
                      }`}
                    >
                      🎪
                    </div>
                    <div className="text-xs">
                      <div className="font-medium">Venue</div>
                    </div>
                  </div>
                  <div className="space-y-1">
                    <div
                      className={`mx-auto flex h-9 w-9 items-center justify-center rounded-full text-base font-bold ${
                        watch('sameAsVenue') ||
                        (watch('addressStreet') &&
                          watch('addressCity') &&
                          watch('addressState') &&
                          watch('addressZipcode'))
                          ? 'bg-green-500 text-white'
                          : 'bg-gray-200 text-gray-500'
                      }`}
                    >
                      💳
                    </div>
                    <div className="text-xs">
                      <div className="font-medium">Billing</div>
                    </div>
                  </div>
                </div>
                {/* Overall Progress Bar */}
                <div className="mt-4">
                  <div className="mb-1 flex justify-between text-xs text-gray-600">
                    <span>Completion</span>
                    <span>
                      {Math.round(
                        (((watch('eventDate') && watch('eventTime') ? 1 : 0) +
                          (watch('name') &&
                          watch('email') &&
                          watch('phone') &&
                          watch('preferredCommunication')
                            ? 1
                            : 0) +
                          (watch('venueStreet') &&
                          watch('venueCity') &&
                          watch('venueState') &&
                          watch('venueZipcode')
                            ? 1
                            : 0) +
                          (watch('sameAsVenue') ||
                          (watch('addressStreet') &&
                            watch('addressCity') &&
                            watch('addressState') &&
                            watch('addressZipcode'))
                            ? 1
                            : 0)) /
                          4) *
                          100,
                      )}
                      %
                    </span>
                  </div>
                  <div className="h-3 w-full rounded-full bg-gray-200">
                    <div
                      className="h-3 rounded-full bg-gradient-to-r from-blue-500 to-red-500 transition-all duration-300"
                      style={{
                        width: `${
                          (((watch('eventDate') && watch('eventTime') ? 1 : 0) +
                            (watch('name') &&
                            watch('email') &&
                            watch('phone') &&
                            watch('preferredCommunication')
                              ? 1
                              : 0) +
                            (watch('venueStreet') &&
                            watch('venueCity') &&
                            watch('venueState') &&
                            watch('venueZipcode')
                              ? 1
                              : 0) +
                            (watch('sameAsVenue') ||
                            (watch('addressStreet') &&
                              watch('addressCity') &&
                              watch('addressState') &&
                              watch('addressZipcode'))
                              ? 1
                              : 0)) /
                            4) *
                          100
                        }%`,
                      }}
                    ></div>
                  </div>
                </div>
              </div>
              {/* Customer Information */}
              <div className="border-b pb-4">
                <div className="mb-3 flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-gray-900">👤 Customer Information</h2>
                  <div className="text-xs">
                    {watch('name') &&
                    watch('email') &&
                    watch('phone') &&
                    watch('preferredCommunication') ? (
                      <span className="rounded-full bg-green-100 px-2 py-0.5 font-semibold text-green-800">
                        ✅ Complete
                      </span>
                    ) : (
                      <span className="rounded-full bg-amber-100 px-2 py-0.5 text-amber-800">
                        ⏳ Pending
                      </span>
                    )}
                  </div>
                </div>
                <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700">
                      Full Name *
                    </label>
                    <input
                      {...register('name')}
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-red-500 focus:ring-2 focus:ring-red-500"
                      placeholder="John Smith"
                    />
                    {errors.name && (
                      <p className="mt-1 text-xs text-red-500">{errors.name.message}</p>
                    )}
                  </div>
                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700">
                      Email Address *
                    </label>
                    <input
                      {...register('email')}
                      type="email"
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-red-500 focus:ring-2 focus:ring-red-500"
                      placeholder="john@example.com"
                    />
                    {errors.email && (
                      <p className="mt-1 text-sm text-red-500">{errors.email.message}</p>
                    )}
                  </div>
                  <div>
                    <label className="mb-2 block text-sm font-medium text-gray-700">
                      Phone Number *
                    </label>
                    <input
                      {...register('phone')}
                      type="tel"
                      className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:border-red-500 focus:ring-2 focus:ring-red-500"
                      placeholder="(555) 123-4567"
                    />
                    {errors.phone && (
                      <p className="mt-1 text-sm text-red-500">{errors.phone.message}</p>
                    )}
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
                      <p className="mt-1 text-sm text-red-500">
                        {errors.preferredCommunication.message}
                      </p>
                    )}
                  </div>
                </div>
                {/* SMS Consent Section */}
                <div className="mt-6 rounded-lg border border-blue-200 bg-blue-50 p-4">
                  <h3 className="mb-3 text-lg font-semibold text-blue-900">
                    📱 SMS Communication Consent
                  </h3>
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
                              className="mt-0.5 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500"
                            />
                          )}
                        />
                        <div className="text-sm">
                          <div className="font-medium text-gray-900">
                            Yes, I consent to receive SMS text messages from My Hibachi Chef
                          </div>
                          <div className="mt-1 text-gray-600">
                            <p className="mb-2">
                              <strong>By checking this box, I agree to receive SMS messages</strong>{' '}
                              including:
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
                        </div>
                      </label>
                    </div>
                    <div className="space-y-1 text-xs text-gray-600">
                      <p>
                        <strong>Important:</strong> Message frequency varies. Message and data rates
                        may apply. Consent is not required for purchase.
                      </p>
                      <p>
                        <strong>Opt-out:</strong> Reply STOP to opt-out anytime. Reply START to
                        re-subscribe. Reply HELP for support.
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
                        <Link href="/terms" className="text-blue-600 hover:underline">
                          Terms & Conditions
                        </Link>
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              {/* Date & Time Selection */}
              <div className="border-b pb-4">
                <h2 className="mb-3 text-lg font-semibold text-gray-900">
                  📅 Date & Time Selection
                </h2>
                <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                  <div>
                    <label className="mb-2 block text-sm font-medium text-gray-700">
                      Event Date *
                    </label>
                    <Controller
                      name="eventDate"
                      control={control}
                      render={({ field }) => (
                        <div className="relative">
                          <LazyDatePicker
                            selected={field.value}
                            onChange={(date: Date | null) => {
                              setDateError(null);
                              field.onChange(date);
                            }}
                            minDate={addDays(new Date(), 2)} // 48 hours minimum
                            maxDate={addDays(new Date(), 730)} // 2 years maximum
                            excludeDates={bookedDates}
                            dateFormat="MMMM d, yyyy"
                            placeholderText="Select your event date"
                            className="w-full rounded-lg border border-gray-300 px-4 py-3 transition-all duration-200 focus:border-red-500 focus:ring-2 focus:ring-red-500"
                            calendarClassName="shadow-xl border border-gray-200"
                            wrapperClassName="w-full"
                            showPopperArrow={false}
                            autoComplete="off"
                            showYearDropdown
                            showMonthDropdown
                            dropdownMode="select"
                            yearDropdownItemNumber={3}
                            scrollableYearDropdown={false}
                            dayClassName={(date: Date) => {
                              // Highlight selected date
                              if (
                                field.value &&
                                date.toDateString() === field.value.toDateString()
                              ) {
                                return 'bg-red-500 text-white font-bold rounded';
                              }
                              // Style for booked dates
                              const isBooked = bookedDates.some(
                                (bookedDate) => bookedDate.toDateString() === date.toDateString(),
                              );
                              if (isBooked) {
                                return 'bg-red-100 text-red-400 line-through cursor-not-allowed';
                              }
                              return '';
                            }}
                            onSelect={(date: Date | null) => {
                              // Additional validation when user selects a date
                              if (!date) return;
                              const now = new Date();
                              const timeDiff = date.getTime() - now.getTime();
                              const hoursDiff = timeDiff / (1000 * 60 * 60);
                              if (hoursDiff < 48) {
                                setDateError('Please select a date at least 48 hours in advance');
                                return;
                              }
                              // Check if the date is booked
                              const isBooked = bookedDates.some(
                                (bookedDate) => bookedDate.toDateString() === date.toDateString(),
                              );
                              if (isBooked) {
                                setDateError(
                                  'This date is fully booked. Please select another date.',
                                );
                                return;
                              }
                              setDateError(null);
                            }}
                            filterDate={(date: Date) => {
                              // Filter out dates that don't meet our criteria
                              const now = new Date();
                              const timeDiff = date.getTime() - now.getTime();
                              const hoursDiff = timeDiff / (1000 * 60 * 60);
                              // Must be at least 48 hours in future
                              if (hoursDiff < 48) return false;
                              // Only allow current year and future years (prevents previous year navigation)
                              if (date.getFullYear() < now.getFullYear()) return false;
                              // Check if the date is booked
                              const isBooked = bookedDates.some(
                                (bookedDate) => bookedDate.toDateString() === date.toDateString(),
                              );
                              return !isBooked;
                            }}
                          />
                          {loadingDates && (
                            <div className="absolute top-3 right-3">
                              <div className="h-4 w-4 animate-spin rounded-full border-2 border-red-500 border-t-transparent"></div>
                            </div>
                          )}
                        </div>
                      )}
                    />
                    <div className="mt-1 space-y-1 text-sm">
                      <p className="text-gray-500">Must be at least 48 hours in advance</p>
                      {dateError && <p className="font-medium text-red-500">⚠️ {dateError}</p>}
                      {loadingDates && (
                        <p className="text-blue-500">🔄 Loading available dates...</p>
                      )}
                      {bookedDates.length > 0 && !loadingDates && (
                        <p className="text-amber-600">
                          📅 {bookedDates.length} date(s) are already booked and unavailable
                        </p>
                      )}
                      {!loadingDates && bookedDates.length === 0 && (
                        <p className="text-green-600">
                          ✅ All future dates are available for booking
                        </p>
                      )}
                    </div>
                    {errors.eventDate && (
                      <p className="mt-1 text-sm text-red-500">{errors.eventDate.message}</p>
                    )}
                  </div>
                  <div>
                    <label className="mb-2 block text-sm font-medium text-gray-700">
                      Event Time *
                    </label>
                    <Controller
                      name="eventTime"
                      control={control}
                      render={({ field }) => (
                        <select
                          {...field}
                          className={`w-full rounded-lg border border-gray-300 px-4 py-3 transition-all duration-200 focus:border-red-500 focus:ring-2 focus:ring-red-500 ${
                            loadingTimeSlots ? 'animate-pulse bg-gray-100' : ''
                          } ${field.value ? 'border-green-300 bg-green-50' : ''}`}
                          disabled={loadingTimeSlots}
                        >
                          <option value="">
                            {loadingTimeSlots ? '⏳ Loading time slots...' : '🕐 Select a time'}
                          </option>
                          {availableTimeSlots.map((slot) => (
                            <option
                              key={slot.time}
                              value={slot.time}
                              disabled={!slot.isAvailable}
                              style={{
                                color: !slot.isAvailable ? '#9ca3af' : '#059669',
                                fontWeight: slot.isAvailable ? 'bold' : 'normal',
                              }}
                            >
                              {slot.isAvailable
                                ? `✅ ${slot.label} (${slot.available} slot${
                                    slot.available !== 1 ? 's' : ''
                                  } available)`
                                : `❌ ${slot.label} – Fully Booked`}
                            </option>
                          ))}
                          {availableTimeSlots.length === 0 && selectedDate && !loadingTimeSlots && (
                            <option disabled>⚠️ No time slots available for this date</option>
                          )}
                        </select>
                      )}
                    />
                    {errors.eventTime && (
                      <p className="mt-1 text-sm text-red-500">{errors.eventTime.message}</p>
                    )}
                  </div>
                  <div>
                    <label className="mb-2 block text-sm font-medium text-gray-700">
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
                          onChange={(e) =>
                            field.onChange(e.target.value ? parseInt(e.target.value) : undefined)
                          }
                          className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:border-red-500 focus:ring-2 focus:ring-red-500"
                          placeholder="Enter estimated guest count"
                        />
                      )}
                    />
                    {errors.guestCount && (
                      <p className="mt-1 text-sm text-red-500">{errors.guestCount.message}</p>
                    )}
                  </div>
                </div>
              </div>
              {/* Event Venue - Now above Billing Address */}
              <div className="border-b pb-4">
                <div className="mb-3 flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-gray-900">🎪 Event Venue</h2>
                  <div className="text-xs">
                    {watch('venueStreet') &&
                    watch('venueCity') &&
                    watch('venueState') &&
                    watch('venueZipcode') ? (
                      <span className="rounded-full bg-green-100 px-2 py-0.5 font-semibold text-green-800">
                        ✅ Complete
                      </span>
                    ) : (
                      <span className="rounded-full bg-amber-100 px-2 py-0.5 text-amber-800">
                        ⏳ Pending
                      </span>
                    )}
                  </div>
                </div>
                <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                  <div className="md:col-span-2">
                    <label className="mb-2 block text-sm font-medium text-gray-700">
                      Venue Street Address *
                    </label>
                    <input
                      {...venueStreetRegister}
                      ref={(element) => {
                        // Set React Hook Form ref for form validation
                        venueStreetFormRef(element);
                        // Set our custom ref for Google Places Autocomplete
                        venueAddressInputRef.current = element;
                      }}
                      className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:border-red-500 focus:ring-2 focus:ring-red-500"
                      placeholder="Start typing your venue address..."
                      autoComplete="off"
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      📍 Smart Address Search: Start typing and select from Google suggestions
                    </p>
                    {errors.venueStreet && (
                      <p className="mt-1 text-sm text-red-500">{errors.venueStreet.message}</p>
                    )}
                  </div>
                  <div>
                    <label className="mb-2 block text-sm font-medium text-gray-700">City *</label>
                    <input
                      {...register('venueCity')}
                      className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:border-red-500 focus:ring-2 focus:ring-red-500"
                      placeholder="Event City"
                    />
                    {errors.venueCity && (
                      <p className="mt-1 text-sm text-red-500">{errors.venueCity.message}</p>
                    )}
                  </div>
                  <div>
                    <label className="mb-2 block text-sm font-medium text-gray-700">State *</label>
                    <input
                      {...register('venueState')}
                      className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:border-red-500 focus:ring-2 focus:ring-red-500"
                      placeholder="ST"
                      maxLength={2}
                    />
                    {errors.venueState && (
                      <p className="mt-1 text-sm text-red-500">{errors.venueState.message}</p>
                    )}
                  </div>
                  <div>
                    <label className="mb-2 block text-sm font-medium text-gray-700">
                      ZIP Code *
                    </label>
                    <input
                      {...register('venueZipcode')}
                      className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:border-red-500 focus:ring-2 focus:ring-red-500"
                      placeholder="12345"
                      maxLength={10}
                    />
                    {errors.venueZipcode && (
                      <p className="mt-1 text-sm text-red-500">{errors.venueZipcode.message}</p>
                    )}
                  </div>
                </div>
              </div>
              {/* Billing Address - Changed from Customer Address */}
              <div className="border-b pb-4">
                <div className="mb-3 flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-gray-900">💳 Billing Address</h2>
                  <div className="text-xs">
                    {watch('sameAsVenue') ||
                    (watch('addressStreet') &&
                      watch('addressCity') &&
                      watch('addressState') &&
                      watch('addressZipcode')) ? (
                      <span className="rounded-full bg-green-100 px-2 py-0.5 font-semibold text-green-800">
                        ✅ Complete
                      </span>
                    ) : (
                      <span className="rounded-full bg-amber-100 px-2 py-0.5 text-amber-800">
                        ⏳ Pending
                      </span>
                    )}
                  </div>
                </div>
                {/* Checkbox - Disabled until venue address is complete */}
                <div className="mb-3">
                  <label
                    className={`flex items-center space-x-3 ${
                      isVenueAddressComplete ? 'cursor-pointer' : 'cursor-not-allowed'
                    }`}
                  >
                    <Controller
                      name="sameAsVenue"
                      control={control}
                      render={({ field }) => (
                        <input
                          type="checkbox"
                          checked={field.value}
                          onChange={field.onChange}
                          disabled={!isVenueAddressComplete}
                          className={`h-4 w-4 rounded border-gray-300 text-red-600 focus:ring-2 focus:ring-red-500 ${
                            !isVenueAddressComplete ? 'cursor-not-allowed opacity-50' : ''
                          }`}
                        />
                      )}
                    />
                    <span
                      className={`text-sm font-medium ${
                        isVenueAddressComplete ? 'text-gray-700' : 'text-gray-400'
                      }`}
                    >
                      Billing address is the same as Event Venue address
                    </span>
                  </label>
                  {!isVenueAddressComplete && (
                    <p className="mt-2 ml-7 text-sm text-amber-600">
                      ⚠️ Please complete the Event Venue address above to use this option
                    </p>
                  )}
                </div>
                {/* Show minimized summary when checkbox is checked */}
                {sameAsVenue && isVenueAddressComplete ? (
                  <div className="rounded-lg border border-green-200 bg-green-50 p-4">
                    <div className="mb-2 flex items-center space-x-2">
                      <span className="font-medium text-green-600">
                        ✓ Billing address is the same as venue address:
                      </span>
                    </div>
                    <div className="text-sm text-gray-700">
                      <p>
                        <strong>{venueStreet}</strong>
                      </p>
                      <p>
                        {venueCity}, {venueState} {venueZipcode}
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div className="md:col-span-2">
                      <label className="mb-2 block text-sm font-medium text-gray-700">
                        Street Address *
                      </label>
                      <input
                        {...register('addressStreet')}
                        className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:border-red-500 focus:ring-2 focus:ring-red-500"
                        placeholder="123 Main Street"
                        disabled={sameAsVenue}
                      />
                      {errors.addressStreet && (
                        <p className="mt-1 text-sm text-red-500">{errors.addressStreet.message}</p>
                      )}
                    </div>
                    <div>
                      <label className="mb-2 block text-sm font-medium text-gray-700">City *</label>
                      <input
                        {...register('addressCity')}
                        className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:border-red-500 focus:ring-2 focus:ring-red-500"
                        placeholder="Your City"
                        disabled={sameAsVenue}
                      />
                      {errors.addressCity && (
                        <p className="mt-1 text-sm text-red-500">{errors.addressCity.message}</p>
                      )}
                    </div>
                    <div>
                      <label className="mb-2 block text-sm font-medium text-gray-700">
                        State *
                      </label>
                      <input
                        {...register('addressState')}
                        className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:border-red-500 focus:ring-2 focus:ring-red-500"
                        placeholder="ST"
                        maxLength={2}
                        disabled={sameAsVenue}
                      />
                      {errors.addressState && (
                        <p className="mt-1 text-sm text-red-500">{errors.addressState.message}</p>
                      )}
                    </div>
                    <div>
                      <label className="mb-2 block text-sm font-medium text-gray-700">
                        ZIP Code *
                      </label>
                      <input
                        {...register('addressZipcode')}
                        className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:border-red-500 focus:ring-2 focus:ring-red-500"
                        placeholder="12345"
                        maxLength={10}
                        disabled={sameAsVenue}
                      />
                      {errors.addressZipcode && (
                        <p className="mt-1 text-sm text-red-500">{errors.addressZipcode.message}</p>
                      )}
                    </div>
                  </div>
                )}
              </div>
              {/* Submit Button */}
              <div className="text-center">
                {/* Form completion status */}
                {(watch('eventDate') && watch('eventTime') ? 1 : 0) +
                  (watch('name') &&
                  watch('email') &&
                  watch('phone') &&
                  watch('preferredCommunication')
                    ? 1
                    : 0) +
                  (watch('venueStreet') &&
                  watch('venueCity') &&
                  watch('venueState') &&
                  watch('venueZipcode')
                    ? 1
                    : 0) +
                  (watch('sameAsVenue') ||
                  (watch('addressStreet') &&
                    watch('addressCity') &&
                    watch('addressState') &&
                    watch('addressZipcode'))
                    ? 1
                    : 0) <
                  4 && (
                  <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 p-4">
                    <div className="text-sm text-amber-800">
                      <div className="mb-3 flex items-center justify-center">
                        <span className="mr-2">⚠️</span>
                        <span className="font-semibold">
                          Please complete the following sections to submit your booking (
                          {(watch('eventDate') && watch('eventTime') ? 1 : 0) +
                            (watch('name') &&
                            watch('email') &&
                            watch('phone') &&
                            watch('preferredCommunication')
                              ? 1
                              : 0) +
                            (watch('venueStreet') &&
                            watch('venueCity') &&
                            watch('venueState') &&
                            watch('venueZipcode')
                              ? 1
                              : 0) +
                            (watch('sameAsVenue') ||
                            (watch('addressStreet') &&
                              watch('addressCity') &&
                              watch('addressState') &&
                              watch('addressZipcode'))
                              ? 1
                              : 0)}
                          /4 sections complete):
                        </span>
                      </div>
                      <div className="space-y-2">
                        {/* Date & Time Section */}
                        {!(watch('eventDate') && watch('eventTime')) && (
                          <div className="flex items-center justify-center space-x-2 rounded bg-amber-100 px-3 py-2 text-amber-700">
                            <span>📅</span>
                            <span className="font-medium">Date & Time Selection</span>
                            <span className="text-xs">
                              (
                              {!watch('eventDate') && !watch('eventTime')
                                ? 'Select date and time'
                                : !watch('eventDate')
                                  ? 'Select event date'
                                  : 'Select event time'}
                              )
                            </span>
                          </div>
                        )}
                        {/* Customer Information Section */}
                        {!(
                          watch('name') &&
                          watch('email') &&
                          watch('phone') &&
                          watch('preferredCommunication')
                        ) && (
                          <div className="flex items-center justify-center space-x-2 rounded bg-amber-100 px-3 py-2 text-amber-700">
                            <span>👤</span>
                            <span className="font-medium">Customer Information</span>
                            <span className="text-xs">
                              (
                              {[
                                !watch('name') && 'name',
                                !watch('email') && 'email',
                                !watch('phone') && 'phone',
                                !watch('preferredCommunication') && 'communication method',
                              ]
                                .filter(Boolean)
                                .join(', ')}
                              )
                            </span>
                          </div>
                        )}
                        {/* Event Venue Section */}
                        {!(
                          watch('venueStreet') &&
                          watch('venueCity') &&
                          watch('venueState') &&
                          watch('venueZipcode')
                        ) && (
                          <div className="flex items-center justify-center space-x-2 rounded bg-amber-100 px-3 py-2 text-amber-700">
                            <span>🎪</span>
                            <span className="font-medium">Event Venue Address</span>
                            <span className="text-xs">
                              (
                              {[
                                !watch('venueStreet') && 'street',
                                !watch('venueCity') && 'city',
                                !watch('venueState') && 'state',
                                !watch('venueZipcode') && 'zip code',
                              ]
                                .filter(Boolean)
                                .join(', ')}
                              )
                            </span>
                          </div>
                        )}
                        {/* Billing Address Section */}
                        {!(
                          watch('sameAsVenue') ||
                          (watch('addressStreet') &&
                            watch('addressCity') &&
                            watch('addressState') &&
                            watch('addressZipcode'))
                        ) && (
                          <div className="flex items-center justify-center space-x-2 rounded bg-amber-100 px-3 py-2 text-amber-700">
                            <span>💳</span>
                            <span className="font-medium">Billing Address</span>
                            <span className="text-xs">
                              (Complete billing address or check &quot;same as venue&quot;)
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
                <button
                  type="submit"
                  disabled={
                    (watch('eventDate') && watch('eventTime') ? 1 : 0) +
                      (watch('name') &&
                      watch('email') &&
                      watch('phone') &&
                      watch('preferredCommunication')
                        ? 1
                        : 0) +
                      (watch('venueStreet') &&
                      watch('venueCity') &&
                      watch('venueState') &&
                      watch('venueZipcode')
                        ? 1
                        : 0) +
                      (watch('sameAsVenue') ||
                      (watch('addressStreet') &&
                        watch('addressCity') &&
                        watch('addressState') &&
                        watch('addressZipcode'))
                        ? 1
                        : 0) <
                      4 || isSubmitting
                  }
                  className={`position-relative inline-flex items-center gap-3 overflow-hidden border-none text-base font-bold transition-all duration-300 ${
                    (watch('eventDate') && watch('eventTime') ? 1 : 0) +
                      (watch('name') &&
                      watch('email') &&
                      watch('phone') &&
                      watch('preferredCommunication')
                        ? 1
                        : 0) +
                      (watch('venueStreet') &&
                      watch('venueCity') &&
                      watch('venueState') &&
                      watch('venueZipcode')
                        ? 1
                        : 0) +
                      (watch('sameAsVenue') ||
                      (watch('addressStreet') &&
                        watch('addressCity') &&
                        watch('addressState') &&
                        watch('addressZipcode'))
                        ? 1
                        : 0) ===
                      4 && !isSubmitting
                      ? 'cursor-pointer bg-gradient-to-r from-red-500 to-red-400 text-white hover:scale-105 hover:shadow-2xl'
                      : 'cursor-not-allowed bg-gradient-to-r from-gray-400 to-gray-500 text-white'
                  }`}
                  style={{
                    borderRadius: '50px',
                    paddingLeft: '2rem',
                    paddingRight: '2rem',
                    paddingTop: '0.6rem',
                    paddingBottom: '0.6rem',
                    minWidth: '240px',
                    textShadow: '0 2px 4px rgba(0, 0, 0, 0.5)',
                    boxShadow:
                      (watch('eventDate') && watch('eventTime') ? 1 : 0) +
                        (watch('name') &&
                        watch('email') &&
                        watch('phone') &&
                        watch('preferredCommunication')
                          ? 1
                          : 0) +
                        (watch('venueStreet') &&
                        watch('venueCity') &&
                        watch('venueState') &&
                        watch('venueZipcode')
                          ? 1
                          : 0) +
                        (watch('sameAsVenue') ||
                        (watch('addressStreet') &&
                          watch('addressCity') &&
                          watch('addressState') &&
                          watch('addressZipcode'))
                          ? 1
                          : 0) ===
                        4 && !isSubmitting
                        ? '0 8px 25px rgba(239, 68, 68, 0.4)'
                        : '0 4px 15px rgba(156, 163, 175, 0.3)',
                  }}
                >
                  {isSubmitting ? (
                    <span className="flex items-center justify-center">
                      <svg
                        className="mr-3 -ml-1 h-5 w-5 animate-spin text-white"
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                      >
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                        ></circle>
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        ></path>
                      </svg>
                      Processing Booking...
                    </span>
                  ) : (watch('eventDate') && watch('eventTime') ? 1 : 0) +
                      (watch('name') &&
                      watch('email') &&
                      watch('phone') &&
                      watch('preferredCommunication')
                        ? 1
                        : 0) +
                      (watch('venueStreet') &&
                      watch('venueCity') &&
                      watch('venueState') &&
                      watch('venueZipcode')
                        ? 1
                        : 0) +
                      (watch('sameAsVenue') ||
                      (watch('addressStreet') &&
                        watch('addressCity') &&
                        watch('addressState') &&
                        watch('addressZipcode'))
                        ? 1
                        : 0) ===
                    4 ? (
                    '🔥 Book Your Hibachi Experience'
                  ) : (
                    '📝 Complete Form to Continue'
                  )}
                </button>
                {/* Form completion summary */}
                <div className="mt-4 text-sm text-gray-600">
                  <div className="flex flex-wrap items-center justify-center gap-2">
                    <span
                      className={`rounded px-2 py-1 text-xs ${
                        watch('eventDate') && watch('eventTime')
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-500'
                      }`}
                    >
                      📅 Date & Time
                    </span>
                    <span
                      className={`rounded px-2 py-1 text-xs ${
                        watch('name') &&
                        watch('email') &&
                        watch('phone') &&
                        watch('preferredCommunication')
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-500'
                      }`}
                    >
                      👤 Customer Info
                    </span>
                    <span
                      className={`rounded px-2 py-1 text-xs ${
                        watch('venueStreet') &&
                        watch('venueCity') &&
                        watch('venueState') &&
                        watch('venueZipcode')
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-500'
                      }`}
                    >
                      🎪 Venue
                    </span>
                    <span
                      className={`rounded px-2 py-1 text-xs ${
                        watch('sameAsVenue') ||
                        (watch('addressStreet') &&
                          watch('addressCity') &&
                          watch('addressState') &&
                          watch('addressZipcode'))
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-500'
                      }`}
                    >
                      💳 Billing
                    </span>
                  </div>
                </div>
              </div>
            </form>
          </div>
        </div>
      </div>
    </>
  );
}
