import './styles/BookingFormContainer.module.css';

import { addDays, format } from 'date-fns';
import React, { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';

import { apiFetch } from '@/lib/api';
import { logger } from '@/lib/logger';

import ContactInfoSection from './ContactInfoSection';
import CustomerAddressSection from './CustomerAddressSection';
import EventDetailsSection from './EventDetailsSection';
import SubmitSection from './SubmitSection';
import VenueAddressSection from './VenueAddressSection';

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
};

interface TimeSlot {
  time: '12PM' | '3PM' | '6PM' | '9PM';
  label: string;
  available: number;
  isAvailable: boolean;
}

interface BookingFormContainerProps {
  className?: string;
}

interface ApiResponse {
  bookedDates?: string[];
  timeSlots?: TimeSlot[];
}

interface BookingFormContainerProps {
  className?: string;
}

const BookingFormContainer: React.FC<BookingFormContainerProps> = ({ className = '' }) => {
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
  });

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
      const result = await apiFetch('/api/v1/bookings/booked-dates', {
        cacheStrategy: {
          strategy: 'cache-first',
          ttl: 5 * 60 * 1000, // 5 minutes
        },
      });
      if (result.success && result.data) {
        // Convert string dates to Date objects
        const bookedDates = (result.data as ApiResponse)?.bookedDates;
        const dates = Array.isArray(bookedDates)
          ? bookedDates.map((dateStr: string) => new Date(dateStr))
          : [];
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

  // Fetch available time slots for selected date
  const fetchAvailableTimeSlots = async (date: Date) => {
    setLoadingTimeSlots(true);
    try {
      const dateStr = format(date, 'yyyy-MM-dd');
      const response = await apiFetch(`/api/v1/bookings/available-times?date=${dateStr}`, {
        cacheStrategy: {
          strategy: 'cache-first',
          ttl: 3 * 60 * 1000, // 3 minutes
        },
      });

      if (response.success && response.data) {
        const timeSlots = (response.data as ApiResponse)?.timeSlots;
        setAvailableTimeSlots(Array.isArray(timeSlots) ? timeSlots : []);
      } else {
        // Fallback to default time slots if API fails
        setAvailableTimeSlots([
          { time: '12PM', label: '12:00 PM - 2:00 PM', available: 2, isAvailable: true },
          { time: '3PM', label: '3:00 PM - 5:00 PM', available: 2, isAvailable: true },
          { time: '6PM', label: '6:00 PM - 8:00 PM', available: 2, isAvailable: true },
          { time: '9PM', label: '9:00 PM - 11:00 PM', available: 1, isAvailable: true },
        ]);
      }
    } catch (error) {
      logger.warn('Error fetching time slots', { error });
      // Fallback to default time slots
      setAvailableTimeSlots([
        { time: '12PM', label: '12:00 PM - 2:00 PM', available: 2, isAvailable: true },
        { time: '3PM', label: '3:00 PM - 5:00 PM', available: 2, isAvailable: true },
        { time: '6PM', label: '6:00 PM - 8:00 PM', available: 2, isAvailable: true },
        { time: '9PM', label: '9:00 PM - 11:00 PM', available: 1, isAvailable: true },
      ]);
    } finally {
      setLoadingTimeSlots(false);
    }
  };

  // Load booked dates on component mount
  useEffect(() => {
    fetchBookedDates();
  }, []);

  // Fetch time slots when date changes
  useEffect(() => {
    if (selectedDate) {
      fetchAvailableTimeSlots(selectedDate);
    }
  }, [selectedDate]);

  // Auto-fill venue address when "Same as venue" is checked
  useEffect(() => {
    if (sameAsVenue && venueStreet && venueCity && venueState && venueZipcode) {
      setValue('addressStreet', venueStreet);
      setValue('addressCity', venueCity);
      setValue('addressState', venueState);
      setValue('addressZipcode', venueZipcode);
    }
  }, [sameAsVenue, venueStreet, venueCity, venueState, venueZipcode, setValue]);

  // Enhanced onSubmit with comprehensive validation
  const onSubmit = async (data: BookingFormData) => {
    logger.debug('Form submission started'); // DO NOT log data - contains PII

    // Validate required fields manually
    const requiredFields = [];
    if (!data.name?.trim()) requiredFields.push('Name');
    if (!data.email?.trim()) requiredFields.push('Email');
    if (!data.phone?.trim()) requiredFields.push('Phone');
    if (!data.eventDate) requiredFields.push('Event Date');
    if (!data.eventTime) requiredFields.push('Event Time');
    if (!data.guestCount || data.guestCount < 1) requiredFields.push('Guest Count');

    // Address validation
    if (!data.addressStreet?.trim()) requiredFields.push('Address Street');
    if (!data.addressCity?.trim()) requiredFields.push('Address City');
    if (!data.addressState?.trim()) requiredFields.push('Address State');
    if (!data.addressZipcode?.trim()) requiredFields.push('Address ZIP Code');

    // Venue validation (only if different from address)
    if (!data.sameAsVenue) {
      if (!data.venueStreet?.trim()) requiredFields.push('Venue Street');
      if (!data.venueCity?.trim()) requiredFields.push('Venue City');
      if (!data.venueState?.trim()) requiredFields.push('Venue State');
      if (!data.venueZipcode?.trim()) requiredFields.push('Venue ZIP Code');
    }

    if (requiredFields.length > 0) {
      setMissingFields(requiredFields);
      setShowValidationModal(true);
      return;
    }

    // Store form data and show agreement modal
    setFormData(data);
    setShowAgreementModal(true);
  };

  const handleAgreementConfirm = async () => {
    if (!formData) return;

    setIsSubmitting(true);
    setShowAgreementModal(false);

    try {
      logger.debug('Submitting booking request'); // DO NOT log formData - contains PII

      // Map form data to backend schema
      const fullAddress = formData.sameAsVenue
        ? `${formData.addressStreet}, ${formData.addressCity}, ${formData.addressState} ${formData.addressZipcode}`
        : `${formData.venueStreet}, ${formData.venueCity}, ${formData.venueState} ${formData.venueZipcode}`;

      // Convert 12-hour time to 24-hour format
      const timeMap: Record<string, string> = {
        '12PM': '12:00',
        '3PM': '15:00',
        '6PM': '18:00',
        '9PM': '21:00',
      };

      const submissionData = {
        customer_name: formData.name,
        customer_phone: formData.phone,
        customer_email: formData.email,
        date: format(formData.eventDate, 'yyyy-MM-dd'),
        time: timeMap[formData.eventTime] || '18:00',
        guests: formData.guestCount,
        location_address: fullAddress,
        special_requests: '', // Form doesn't have special requests field yet
      };

      const response = await apiFetch('/api/v1/public/bookings', {
        method: 'POST',
        body: JSON.stringify(submissionData),
      });

      if (response.success) {
        logger.info('Booking submitted successfully');
        // Redirect to success page
        window.location.href = '/booking-success';
      } else {
        const errorData = response.data || response;
        logger.error('Booking submission failed', undefined, { error: errorData });
        alert(
          'Sorry, there was an error submitting your booking. Please try again or contact us directly.',
        );
      }
    } catch (error) {
      logger.error('Error submitting booking', error as Error);
      alert(
        'Sorry, there was an error submitting your booking. Please try again or contact us directly.',
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAgreementCancel = () => {
    setShowAgreementModal(false);
    setFormData(null);
  };

  // Helper function to determine if a date should be disabled
  const isDateDisabled = (date: Date) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // Disable dates in the past
    if (date < today) return true;

    // Disable dates more than 3 months in advance
    const maxDate = addDays(today, 90);
    if (date > maxDate) return true;

    // Check if date is fully booked
    const isBooked = bookedDates.some((bookedDate) => {
      const bDate = new Date(bookedDate);
      bDate.setHours(0, 0, 0, 0);
      return bDate.getTime() === date.getTime();
    });

    return isBooked;
  };

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
    sameAsVenue,
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className={`booking-form ${className}`}>
      <ContactInfoSection {...formProps} />
      <EventDetailsSection {...formProps} />
      <VenueAddressSection {...formProps} />
      <CustomerAddressSection {...formProps} />
      <SubmitSection {...formProps} />
    </form>
  );
};

export default BookingFormContainer;
