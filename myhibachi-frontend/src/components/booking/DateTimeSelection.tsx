'use client'

import React from 'react'
import DatePicker from 'react-datepicker'
import 'react-datepicker/dist/react-datepicker.css'
import { format } from 'date-fns'
import type { BookingFormData, TimeSlot } from '../../data/booking/types'

interface DateTimeSelectionProps {
  formData: BookingFormData
  onChange: (field: keyof BookingFormData, value: string | number | Date | boolean) => void
  errors: Record<string, string>
  timeSlots: TimeSlot[]
}

export function DateTimeSelection({
  formData,
  onChange,
  errors,
  timeSlots
}: DateTimeSelectionProps) {
  const today = new Date()
  const oneYearFromNow = new Date(today.getFullYear() + 1, today.getMonth(), today.getDate())

  return (
    <div className="form-section">
      <h3 className="section-title">Event Date & Time</h3>
      <div className="form-grid">
        <div className="form-group date-group">
          <label htmlFor="eventDate" className="form-label">
            Event Date <span className="required">*</span>
          </label>
          <DatePicker
            id="eventDate"
            selected={formData.eventDate}
            onChange={date => onChange('eventDate', date || new Date())}
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
          <label className="form-label">
            Event Time <span className="required">*</span>
          </label>
          <div className="time-slots">
            {timeSlots.map(slot => (
              <button
                key={slot.time}
                type="button"
                className={`time-slot ${formData.eventTime === slot.time ? 'selected' : ''} ${
                  !slot.isAvailable ? 'unavailable' : ''
                }`}
                onClick={() =>
                  slot.isAvailable &&
                  onChange('eventTime', slot.time as '12PM' | '3PM' | '6PM' | '9PM')
                }
                disabled={!slot.isAvailable}
              >
                <span className="time-label">{slot.label}</span>
                <span className="availability">
                  {slot.isAvailable ? `${slot.available} spots` : 'Booked'}
                </span>
              </button>
            ))}
          </div>
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
              onChange={e => onChange('guestCount', parseInt(e.target.value) || 0)}
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
              💡 <strong>Pricing:</strong> Adults $55 each • Children (6-12) $30 each
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
