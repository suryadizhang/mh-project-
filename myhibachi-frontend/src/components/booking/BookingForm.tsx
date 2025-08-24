import React, { useState, useEffect } from 'react';
import EventDetailsSection from './EventDetailsSection';
import GuestDetailsSection from './GuestDetailsSection';
import LocationSection from './LocationSection';
import { BookingSummary } from './BookingSummary';
import type { BookingFormData } from '../../data/booking/types';
import './styles/BookingForm.module.css';

interface BookingFormProps {
  className?: string;
}

const BookingForm: React.FC<BookingFormProps> = ({ className = '' }) => {
  const [formData, setFormData] = useState<BookingFormData>({
    name: '',
    email: '',
    phone: '',
    eventDate: new Date(),
    eventTime: '6PM',
    guestCount: 10,
    addressStreet: '',
    addressCity: '',
    addressState: 'CA',
    addressZipcode: '',
    sameAsVenue: true,
    venueStreet: '',
    venueCity: '',
    venueState: 'CA',
    venueZipcode: '',
    ...DEFAULT_FORM_VALUES
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [availableSlots, setAvailableSlots] = useState<string[]>([]);

  const updateFormData = (updates: Partial<BookingFormData>) => {
    setFormData(prev => ({ ...prev, ...updates }));
    
    // Clear errors for updated fields
    const updatedFields = Object.keys(updates);
    setErrors(prev => {
      const newErrors = { ...prev };
      updatedFields.forEach(field => delete newErrors[field]);
      return newErrors;
    });
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.eventDate) newErrors.eventDate = 'Event date is required';
    if (!formData.eventTime) newErrors.eventTime = 'Event time is required';
    if (formData.guestCount < 10) newErrors.guestCount = 'Minimum 10 guests required';
    if (!formData.name.trim()) newErrors.name = 'Name is required';
    if (!formData.email.trim()) newErrors.email = 'Email is required';
    if (!formData.phone.trim()) newErrors.phone = 'Phone number is required';

    if (!formData.sameAsVenue) {
      if (!formData.addressStreet.trim()) newErrors.addressStreet = 'Address is required';
      if (!formData.addressCity.trim()) newErrors.addressCity = 'City is required';
      if (!formData.addressState.trim()) newErrors.addressState = 'State is required';
      if (!formData.addressZipcode.trim()) newErrors.addressZipcode = 'ZIP code is required';
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (formData.email && !emailRegex.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    // Phone validation
    const phoneRegex = /^\+?[\d\s\-\(\)]{10,}$/;
    if (formData.phone && !phoneRegex.test(formData.phone)) {
      newErrors.phone = 'Please enter a valid phone number';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch('/api/v1/bookings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      // Handle success - this will be managed by BookingModals component
      window.dispatchEvent(new CustomEvent('bookingSuccess', { detail: result }));
      
    } catch (error) {
      console.error('Booking submission error:', error);
      window.dispatchEvent(new CustomEvent('bookingError', { 
        detail: { message: 'Failed to submit booking. Please try again.' }
      }));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSubmit();
  };

  // Fetch available time slots when date changes
  useEffect(() => {
    if (formData.eventDate) {
      const fetchAvailableSlots = async () => {
        try {
          const dateStr = formData.eventDate?.toISOString().split('T')[0];
          const response = await fetch(`/api/v1/availability?date=${dateStr}`);
          
          if (response.ok) {
            const data = await response.json();
            setAvailableSlots(data.availableSlots || []);
          }
        } catch (error) {
          console.error('Error fetching availability:', error);
          setAvailableSlots([]);
        }
      };

      fetchAvailableSlots();
    } else {
      setAvailableSlots([]);
    }
  }, [formData.eventDate]);

  return (
    <div className={`booking-content ${className}`}>
      <form onSubmit={handleFormSubmit} className="booking-form">
        <EventDetailsSection
          eventDate={formData.eventDate}
          eventTime={formData.eventTime}
          availableSlots={availableSlots}
          errors={errors}
          onUpdate={updateFormData}
        />

        <GuestDetailsSection
          guestCount={formData.guestCount}
          name={formData.name}
          email={formData.email}
          phone={formData.phone}
          errors={errors}
          onUpdate={updateFormData}
        />

        <LocationSection
          sameAsVenue={formData.sameAsVenue}
          addressStreet={formData.addressStreet}
          addressCity={formData.addressCity}
          addressState={formData.addressState}
          addressZipcode={formData.addressZipcode}
          venueStreet={formData.venueStreet}
          venueCity={formData.venueCity}
          venueState={formData.venueState}
          venueZipcode={formData.venueZipcode}
          errors={errors}
          onUpdate={updateFormData}
        />
      </form>

      <div className="booking-sidebar">
        <BookingSummary
          formData={formData}
          isSubmitting={isSubmitting}
          onSubmit={handleSubmit}
        />
      </div>
    </div>
  );
};

export default BookingForm;

export default BookingForm;

