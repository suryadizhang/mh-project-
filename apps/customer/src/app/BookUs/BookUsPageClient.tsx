'use client';

import './datepicker.css';
import '@/styles/booking/booking.css';

import { addDays, format } from 'date-fns';
import {
  AlertTriangle,
  ArrowRight,
  CalendarCheck,
  CalendarDays,
  Check,
  CheckCircle,
  Clock,
  Home,
  Hourglass,
  Info,
  MapPin,
  RefreshCw,
  ShieldCheck,
  User,
} from 'lucide-react';
import React, { useCallback, useEffect, useState } from 'react';
import { Controller, useForm } from 'react-hook-form';

import BookingAgreementModal from '@/components/booking/BookingAgreementModal';
import { LazyDatePicker } from '@/components/ui/LazyDatePicker';
import { useAutoSave, useAutoSaveIndicator } from '@/hooks/useAutoSave';
import { apiFetch } from '@/lib/api';
import { logger } from '@/lib/logger';

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

export default function BookUsPageClient() {
  const [showValidationModal, setShowValidationModal] = useState(false);
  const [missingFields, setMissingFields] = useState<string[]>([]);
  const [showAgreementModal, setShowAgreementModal] = useState(false);
  const [formData, setFormData] = useState<BookingFormData | null>(null);
  const [bookedDates, setBookedDates] = useState<Date[]>([]);
  const [loadingDates, setLoadingDates] = useState(false);
  const [dateError, setDateError] = useState<string | null>(null);
  const [availableTimeSlots, setAvailableTimeSlots] = useState<
    Array<{ time: string; label: string; available: number; isAvailable: boolean }>
  >([]);
  const [loadingTimeSlots, setLoadingTimeSlots] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Allergen acknowledgment checkboxes
  const [allergenAcknowledged, setAllergenAcknowledged] = useState(false);
  const [riskAccepted, setRiskAccepted] = useState(false);
  const [willCommunicate, setWillCommunicate] = useState(false);

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

  // Watch all form values for auto-save
  const formValues = watch();

  // Auto-save callback to restore form data
  const handleRestore = useCallback(
    (savedData: Partial<BookingFormData>) => {
      Object.entries(savedData).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          // Handle Date conversion for eventDate
          if (key === 'eventDate' && typeof value === 'string') {
            setValue(key as keyof BookingFormData, new Date(value) as unknown as never);
          } else {
            setValue(key as keyof BookingFormData, value as never);
          }
        }
      });
    },
    [setValue],
  );

  // Auto-save form data to localStorage
  const { hasSavedData, lastSaved, clearSavedData, isSaving } = useAutoSave<BookingFormData>({
    key: 'booking-form',
    data: formValues as BookingFormData,
    onRestore: handleRestore,
    debounceMs: 1000,
    expirationMs: 24 * 60 * 60 * 1000, // 24 hours
    excludeFields: [], // No sensitive fields to exclude in booking form
  });

  // Auto-save status indicator
  const autoSaveStatus = useAutoSaveIndicator(isSaving, lastSaved);

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
        const bookedDates = (result.data as Record<string, unknown>)?.bookedDates;
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
        const timeSlots = (response.data as Record<string, unknown>)?.timeSlots;
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
    logger.debug('Form submission started');

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
      // DO NOT log formData - contains PII (name, email, phone, address)
      logger.debug('Submitting booking request');

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
        // Clear auto-saved form data on successful submission
        clearSavedData();
        // Redirect to success page
        window.location.href = '/booking-success';
      } else {
        logger.error('Booking submission failed', undefined, { error: response.error });
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

  return (
    <div className="booking-page">
      {/* Hero Section */}
      <section className="booking-hero">
        <div className="container">
          <div className="hero-content text-center">
            <h1 className="hero-title inline-flex items-center gap-3">
              <CalendarCheck className="h-10 w-10" />
              Book Your Hibachi Experience
            </h1>
            <p className="hero-subtitle">
              Reserve your premium private hibachi chef service for an unforgettable culinary
              experience
            </p>
            <div className="hero-features">
              <div className="feature-item">
                <ShieldCheck className="mr-2 h-5 w-5" />
                <span>100% Satisfaction Guaranteed</span>
              </div>
              <div className="feature-item">
                <Clock className="mr-2 h-5 w-5" />
                <span>Flexible Scheduling</span>
              </div>
              <div className="feature-item">
                <MapPin className="mr-2 h-5 w-5" />
                <span>We Come To You</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="container mx-auto px-4">
        <div className="flex justify-center">
          <div className="w-full lg:w-2/3">
            {/* Deposit Warning Banner */}
            <div className="alert alert-warning border-warning mb-4 shadow-sm" role="alert">
              <div className="flex items-start">
                <AlertTriangle className="mt-1 mr-3 h-6 w-6 flex-shrink-0 text-yellow-500" />
                <div className="flex-1">
                  <h5 className="mb-2 font-bold">
                    💳 Deposit Required to Secure Your Booking
                  </h5>
                  <p className="mb-2">
                    A <strong>$100 refundable deposit</strong> is required to confirm and secure
                    your booking date.
                  </p>
                  <p className="mb-0 text-sm">
                    <Clock className="mr-1 inline-block h-4 w-4" />
                    <strong>Important:</strong> Bookings submitted without deposit payment are
                    subject to
                    <strong className="text-danger">
                      {' '}
                      automatic release without notice within 2 hours
                    </strong>
                    . Please complete your deposit payment promptly after booking to guarantee your
                    reserved date and time.
                  </p>
                </div>
              </div>
            </div>

            <div className="booking-form-container">
              {/* Auto-save status indicator */}
              {autoSaveStatus !== 'idle' && (
                <div className="auto-save-indicator mb-3 flex items-center justify-end">
                  {autoSaveStatus === 'saving' && (
                    <span className="text-sm text-gray-500">
                      <RefreshCw className="mr-1 inline-block h-4 w-4 animate-spin" />
                      Saving...
                    </span>
                  )}
                  {autoSaveStatus === 'saved' && (
                    <span className="text-sm text-green-600">
                      <CheckCircle className="mr-1 inline-block h-4 w-4" />
                      Draft saved
                    </span>
                  )}
                </div>
              )}

              {/* Show restore notice if there's saved data */}
              {hasSavedData && lastSaved && (
                <div className="relative bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6 flex items-start gap-3" role="alert">
                  <Info className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-blue-800">
                      <strong>Draft restored!</strong> Your previous booking form was saved on{' '}
                      {lastSaved.toLocaleDateString()} at {lastSaved.toLocaleTimeString()}.
                    </p>
                    <button
                      type="button"
                      className="text-blue-600 hover:text-blue-800 text-sm font-medium underline mt-1"
                      onClick={clearSavedData}
                    >
                      Clear draft
                    </button>
                  </div>
                  <button
                    type="button"
                    className="text-blue-400 hover:text-blue-600 transition-colors"
                    aria-label="Close"
                    onClick={() => {
                      /* Just hides the alert */
                    }}
                  >
                    <span className="text-xl leading-none">&times;</span>
                  </button>
                </div>
              )}

              <form onSubmit={handleSubmit(onSubmit)} className="booking-form">
                {/* Contact Information */}
                <div className="form-section">
                  <h3 className="section-title inline-flex items-center">
                    <User className="mr-2 h-5 w-5" />
                    Contact Information
                  </h3>

                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div>
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

                    <div>
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
                              message: 'Invalid email address',
                            },
                          })}
                          placeholder="your.email@example.com"
                        />
                        {errors.email && (
                          <div className="invalid-feedback">{errors.email.message}</div>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div>
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

                    <div>
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
                            max: { value: 50, message: 'Maximum 50 guests allowed' },
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
                  <h3 className="section-title inline-flex items-center">
                    <CalendarDays className="mr-2 h-5 w-5" />
                    Event Details
                  </h3>

                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div>
                      <div className="form-group">
                        <label htmlFor="eventDate" className="form-label required">
                          Event Date
                        </label>
                        <Controller
                          name="eventDate"
                          control={control}
                          rules={{ required: 'Event date is required' }}
                          render={({ field }) => (
                            <LazyDatePicker
                              selected={field.value}
                              onChange={(date: Date | null) => field.onChange(date)}
                              filterDate={(date: Date) => !isDateDisabled(date)}
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
                          <div className="invalid-feedback block">{errors.eventDate.message}</div>
                        )}
                      </div>
                    </div>

                    <div>
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
                            {availableTimeSlots.map((slot) => (
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
                  <h3 className="section-title inline-flex items-center">
                    <MapPin className="mr-2 h-5 w-5" />
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
                            required: 'Venue street address is required',
                          })}
                          placeholder="123 Main Street, Apt 2B"
                        />
                        {errors.venueStreet && (
                          <div className="invalid-feedback">{errors.venueStreet.message}</div>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 gap-4 md:grid-cols-6">
                    <div className="md:col-span-3">
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

                    <div className="md:col-span-1">
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

                    <div className="md:col-span-2">
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
                  <h3 className="section-title inline-flex items-center">
                    <Home className="mr-2 h-5 w-5" />
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
                                required: 'Street address is required',
                              })}
                              placeholder="123 Main Street, Apt 2B"
                            />
                            {errors.addressStreet && (
                              <div className="invalid-feedback">{errors.addressStreet.message}</div>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 gap-4 md:grid-cols-6">
                        <div className="md:col-span-3">
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

                        <div className="md:col-span-1">
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

                        <div className="md:col-span-2">
                          <div className="form-group">
                            <label htmlFor="addressZipcode" className="form-label required">
                              ZIP Code
                            </label>
                            <input
                              type="text"
                              id="addressZipcode"
                              className={`form-control ${errors.addressZipcode ? 'is-invalid' : ''
                                }`}
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

                {/* Newsletter Auto-Subscribe Notice */}
                <div className="form-section">
                  <div
                    className="mb-4 p-3"
                    style={{
                      backgroundColor: '#fff7ed',
                      border: '1px solid #fed7aa',
                      borderRadius: '0.5rem',
                    }}
                  >
                    <p className="text-xs" style={{ color: '#374151', margin: 0 }}>
                      📧 <strong>You&apos;ll automatically receive our newsletter</strong> with
                      exclusive offers and hibachi tips.
                      <br />
                      <span style={{ color: '#6b7280' }}>
                        Don&apos;t want updates? Simply reply <strong>&quot;STOP&quot;</strong>{' '}
                        anytime to unsubscribe.
                      </span>
                    </p>
                  </div>
                </div>

                {/* Submit Button */}
                <div className="text-center py-6">
                  <button
                    type="submit"
                    className="w-full md:w-auto inline-flex items-center justify-center gap-2 px-10 py-4 bg-gradient-to-r from-red-600 to-red-700 text-white text-lg font-bold rounded-xl shadow-lg hover:from-red-700 hover:to-red-800 hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? (
                      <>
                        <Hourglass className="h-5 w-5 animate-pulse" />
                        Processing Booking...
                      </>
                    ) : (
                      <>
                        <CalendarCheck className="h-5 w-5" />
                        Submit Booking Request
                      </>
                    )}
                  </button>
                  <p className="mt-4 text-gray-500 text-sm">
                    <ShieldCheck className="inline-block mr-1 h-4 w-4" />
                    Your information is secure and will only be used to process your booking.
                  </p>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>

      {/* Validation Modal */}
      {showValidationModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-md mx-4 animate-in zoom-in-95 duration-200">
            <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
              <div className="bg-gradient-to-r from-amber-500 to-orange-500 px-6 py-4">
                <h5 className="text-xl font-bold text-white flex items-center gap-2">
                  <AlertTriangle className="w-6 h-6" />
                  Missing Information
                </h5>
              </div>
              <div className="p-6">
                <p className="text-gray-600 mb-4">Please fill in the following required fields:</p>
                <ul className="space-y-2">
                  {missingFields.map((field, index) => (
                    <li key={index} className="flex items-center gap-2 text-gray-700 bg-gray-50 px-4 py-2 rounded-lg">
                      <ArrowRight className="w-4 h-4 text-red-500 flex-shrink-0" />
                      {field}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="px-6 py-4 bg-gray-50 border-t border-gray-100">
                <button
                  type="button"
                  className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-red-600 to-red-700 text-white font-semibold rounded-xl hover:from-red-700 hover:to-red-800 transition-all duration-200 shadow-md hover:shadow-lg"
                  onClick={() => setShowValidationModal(false)}
                >
                  <Check className="w-5 h-5" />
                  Got It
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Agreement Modal */}
      <BookingAgreementModal
        isOpen={showAgreementModal}
        onConfirm={handleAgreementConfirm}
        onCancel={handleAgreementCancel}
        isSubmitting={isSubmitting}
        allergenAcknowledged={allergenAcknowledged}
        setAllergenAcknowledged={setAllergenAcknowledged}
        riskAccepted={riskAccepted}
        setRiskAccepted={setRiskAccepted}
        willCommunicate={willCommunicate}
        setWillCommunicate={setWillCommunicate}
      />
    </div>
  );
}
