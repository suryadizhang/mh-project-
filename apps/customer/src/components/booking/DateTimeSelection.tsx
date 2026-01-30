'use client';

import { format } from 'date-fns';
import React from 'react';

import { LazyDatePicker } from '@/components/ui/LazyDatePicker';
import { usePricing } from '@/hooks/usePricing';

import type { BookingFormData, EventTimeValue, TimeSlot } from '../../data/booking/types';
import { GROUPED_TIME_OPTIONS } from '../../data/booking/types';

interface DateTimeSelectionProps {
  formData: BookingFormData;
  onChange: (field: keyof BookingFormData, value: string | number | Date | boolean) => void;
  errors: Record;
  timeSlots: TimeSlot[];
}

export function DateTimeSelection({
  formData,
  onChange,
  errors,
  timeSlots,
}: DateTimeSelectionProps) {
  const { adultPrice, childPrice, childFreeUnderAge, isLoading } = usePricing();
  const today = new Date();
  const oneYearFromNow = new Date(today.getFullYear() + 1, today.getMonth(), today.getDate());

  // Handle dropdown time selection
  const handleTimeChange = (e: React.ChangeEvent) => {
    const selectedTime = e.target.value as EventTimeValue | '';
    onChange('eventTime', selectedTime);
  };

  return (
    <div className="form-section">
      <h3 className="section-title">Event Date & Time</h3>
      <div className="form-grid">
        <div className="form-group date-group">
          <label htmlFor="eventDate" className="form-label">
            Event Date <span className="required">*</span>
          </label>
          <LazyDatePicker
            id="eventDate"
            selected={formData.eventDate}
            onChange={(date) => onChange('eventDate', date || new Date())}
            minDate={today}
            maxDate={oneYearFromNow}
            placeholderText="Select event date"
            className={`form-input ${errors.eventDate ? 'error' : ''}`}
            dateFormat="MMMM d, yyyy"
            showPopperArrow={false}
            required
          />
          {errors.eventDate && <span className="error-message">{errors.eventDate}</span>}
          <div className="date-info">
            {formData.eventDate && (
              <span className="selected-date">
                📅 {format(formData.eventDate, 'EEEE, MMMM d, yyyy')}
              </span>
            )}
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="eventTime" className="form-label">
            Event Start Time <span className="required">*</span>
          </label>
          <select
            id="eventTime"
            value={formData.eventTime}
            onChange={handleTimeChange}
            className={`form-input time-dropdown ${errors.eventTime ? 'error' : ''}`}
            required
          >
            <option value="">Select a time</option>
            {GROUPED_TIME_OPTIONS.map((group) => (
              <optgroup key={group.slot} label={group.label}>
                {group.times.map((timeOption) => {
                  // Check availability from slot data if provided
                  const slotInfo = timeSlots?.find((s) => s.time === group.slot);
                  const isAvailable = slotInfo ? slotInfo.isAvailable : true;

                  return (
                    <option key={timeOption.value} value={timeOption.value} disabled={!isAvailable}>
                      {timeOption.label}
                      {!isAvailable ? ' (Booked)' : ''}
                    </option>
                  );
                })}
              </optgroup>
            ))}
          </select>
          <p className="chef-arrival-note">👨‍🍳 Chef arrives 15-30 min early for setup</p>
          {errors.eventTime && <span className="error-message">{errors.eventTime}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="guestCount" className="form-label">
            Number of Guests <span className="required">*</span>
          </label>
          <div className="guest-count-container">
            <input
              type="number"
              id="guestCount"
              name="guestCount"
              value={formData.guestCount}
              onChange={(e) => onChange('guestCount', parseInt(e.target.value) || 0)}
              min="1"
              max="20"
              placeholder="Enter guest count"
              className={`form-input ${errors.guestCount ? 'error' : ''}`}
              required
            />
            <div className="guest-count-buttons">
              <button
                type="button"
                className="count-btn"
                onClick={() => onChange('guestCount', Math.max(1, formData.guestCount - 1))}
                disabled={formData.guestCount <= 1}
              >
                -
              </button>
              <button
                type="button"
                className="count-btn"
                onClick={() => onChange('guestCount', Math.min(20, formData.guestCount + 1))}
                disabled={formData.guestCount >= 20}
              >
                +
              </button>
            </div>
          </div>
          {errors.guestCount && <span className="error-message">{errors.guestCount}</span>}
          <div className="guest-info">
            <p className="pricing-note">
              💡 <strong>Pricing:</strong> Adults {isLoading ? '...' : `$${adultPrice}`} each •
              Children ({childFreeUnderAge}-12) {isLoading ? '...' : `$${childPrice}`} each
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
