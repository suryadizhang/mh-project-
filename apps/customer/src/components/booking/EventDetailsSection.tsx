import 'react-datepicker/dist/react-datepicker.css';
import '../../../app/BookUs/datepicker.css';
import './styles/EventDetailsSection.module.css';

import { addDays } from 'date-fns';
import { CalendarDays } from 'lucide-react';
import React from 'react';
import DatePicker from 'react-datepicker';
import { Controller } from 'react-hook-form';

import { EventDetailsSectionProps } from './types';

const EventDetailsSection: React.FC<EventDetailsSectionProps & { className?: string }> = ({
  register,
  control,
  errors,
  loadingDates,
  dateError,
  availableTimeSlots,
  loadingTimeSlots,
  isDateDisabled,
  className = '',
}) => {
  return (
    <div className={`form-section ${className}`}>
      <h3 className="section-title">
        <CalendarDays className="mr-2 inline-block" size={20} />
        Event Details
      </h3>

      <div className="row">
        <div className="col-md-6">
          <div className="form-group">
            <label htmlFor="eventDate" className="form-label required">
              Event Date
            </label>
            <Controller
              name="eventDate"
              control={control}
              rules={{ required: 'Event date is required' }}
              render={({ field }) => (
                <DatePicker
                  selected={field.value}
                  onChange={(date) => field.onChange(date)}
                  filterDate={(date) => !isDateDisabled(date)}
                  minDate={new Date()}
                  maxDate={addDays(new Date(), 90)}
                  className={`form-control ${errors.eventDate ? 'is-invalid' : ''}`}
                  placeholderText="Select event date"
                  dateFormat="MMMM d, yyyy"
                  id="eventDate"
                />
              )}
            />
            {loadingDates && <small className="text-muted">Loading available dates...</small>}
            {dateError && <small className="text-danger">{dateError}</small>}
            {errors.eventDate && (
              <div className="invalid-feedback d-block">{errors.eventDate.message}</div>
            )}
          </div>
        </div>

        <div className="col-md-6">
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
                  <option key={slot.time} value={slot.time} disabled={!slot.isAvailable}>
                    {slot.label}{' '}
                    {slot.isAvailable ? `(${slot.available} available)` : '(Fully Booked)'}
                  </option>
                ))}
              </select>
            )}
            {errors.eventTime && <div className="invalid-feedback">{errors.eventTime.message}</div>}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EventDetailsSection;
