'use client';

import { format } from 'date-fns';
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';

import { BookingFormData, DEFAULT_FORM_VALUES, TimeSlot } from '@/data/booking/types';
import { apiFetch } from '@/lib/api';

interface BookedDatesResponse {
  bookedDates?: string[];
}

interface AvailabilityResponse {
  timeSlots: Array;
}

export function useBooking() {
  // Form state
  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
    watch,
    setValue,
    getValues,
  } = useForm<BookingFormData>({
    defaultValues: DEFAULT_FORM_VALUES,
  });

  // Local state
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

  // Watch form values
  const sameAsVenue = watch('sameAsVenue');
  const venueStreet = watch('venueStreet');
  const venueCity = watch('venueCity');
  const venueState = watch('venueState');
  const venueZipcode = watch('venueZipcode');
  const selectedDate = watch('eventDate');

  // Fetch booked dates
  const fetchBookedDates = async () => {
    setLoadingDates(true);
    setDateError(null);
    try {
      const result = await apiFetch('/api/v1/bookings/booked-dates');
      if (result.success && result.data) {
        console.log('Booked dates response:', result.data);
        const responseData = result.data as BookedDatesResponse;
        const dates = responseData.bookedDates?.map((dateStr: string) => new Date(dateStr)) || [];
        setBookedDates(dates);
      } else {
        throw new Error('Failed to fetch booked dates');
      }
    } catch (error) {
      console.error('Error fetching booked dates:', error);
      setDateError('Unable to load booked dates. Please try again.');
    } finally {
      setLoadingDates(false);
    }
  };

  // Fetch availability for selected date
  const fetchAvailability = async (date: Date) => {
    setLoadingTimeSlots(true);
    try {
      const dateStr = format(date, 'yyyy-MM-dd');
      const response = await apiFetch(`/api/v1/bookings/availability?date=${dateStr}`);

      if (response.success && response.data) {
        const responseData = response.data as unknown as AvailabilityResponse;
        const formattedSlots = responseData.timeSlots.map(
          (slot: { time: string; available: number; label: string }) => ({
            time: slot.time,
            label: slot.label,
            available: slot.available,
            isAvailable: slot.available > 0,
          }),
        );
        setAvailableTimeSlots(formattedSlots);
      } else {
        console.error('Failed to fetch availability');
        setAvailableTimeSlots([]);
      }
    } catch (error) {
      console.error('Error fetching availability:', error);
      setAvailableTimeSlots([]);
    } finally {
      setLoadingTimeSlots(false);
    }
  };

  // Load booked dates on mount
  useEffect(() => {
    fetchBookedDates();
  }, []);

  // Fetch availability when date changes
  useEffect(() => {
    if (selectedDate && selectedDate instanceof Date && !isNaN(selectedDate.getTime())) {
      fetchAvailability(selectedDate);
    }
  }, [selectedDate]);

  // Handle same as venue toggle
  useEffect(() => {
    if (sameAsVenue) {
      const formValues = getValues();
      setValue('venueStreet', formValues.addressStreet);
      setValue('venueCity', formValues.addressCity);
      setValue('venueState', formValues.addressState);
      setValue('venueZipcode', formValues.addressZipcode);
    }
  }, [sameAsVenue, setValue, getValues]);

  // Check if venue address is complete
  const isVenueAddressComplete = venueStreet && venueCity && venueState && venueZipcode;

  // Form submission
  const onSubmit = async (data: BookingFormData) => {
    setIsSubmitting(true);
    try {
      // Validation logic
      const missing: string[] = [];

      // Check required fields
      if (!data.name?.trim()) missing.push('Name');
      if (!data.email?.trim()) missing.push('Email');
      if (!data.phone?.trim()) missing.push('Phone');
      if (!data.eventDate) missing.push('Event Date');
      if (!data.eventTime) missing.push('Event Time');
      if (!data.guestCount) missing.push('Guest Count');
      if (!data.addressStreet?.trim()) missing.push('Address Street');
      if (!data.addressCity?.trim()) missing.push('Address City');
      if (!data.addressState?.trim()) missing.push('Address State');
      if (!data.addressZipcode?.trim()) missing.push('Address Zip Code');

      // Check venue address if different from billing
      if (!data.sameAsVenue) {
        if (!data.venueStreet?.trim()) missing.push('Venue Street');
        if (!data.venueCity?.trim()) missing.push('Venue City');
        if (!data.venueState?.trim()) missing.push('Venue State');
        if (!data.venueZipcode?.trim()) missing.push('Venue Zip Code');
      }

      if (missing.length > 0) {
        setMissingFields(missing);
        setShowValidationModal(true);
        setIsSubmitting(false);
        return;
      }

      // Set form data and show agreement modal
      setFormData(data);
      setShowAgreementModal(true);
    } catch (error) {
      console.error('Error in form submission:', error);
      setIsSubmitting(false);
    }
  };

  return {
    // Form methods
    register,
    handleSubmit,
    control,
    errors,
    watch,
    setValue,
    getValues,

    // State
    showValidationModal,
    setShowValidationModal,
    missingFields,
    showAgreementModal,
    setShowAgreementModal,
    formData,
    setFormData,
    bookedDates,
    loadingDates,
    dateError,
    availableTimeSlots,
    loadingTimeSlots,
    isSubmitting,
    setIsSubmitting,

    // Computed values
    sameAsVenue,
    venueStreet,
    venueCity,
    venueState,
    venueZipcode,
    selectedDate,
    isVenueAddressComplete,

    // Methods
    onSubmit,
    fetchBookedDates,
    fetchAvailability,
  };
}
