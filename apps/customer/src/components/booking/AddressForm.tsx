'use client';

import React from 'react';

import type { BookingFormData } from '../../data/booking/types';

interface AddressFormProps {
  formData: BookingFormData;
  onChange: (field: keyof BookingFormData, value: string | number | Date | boolean) => void;
  errors: Record<string, string>;
}

export function AddressForm({ formData, onChange, errors }: AddressFormProps) {
  return (
    <div className="form-section">
      <h3 className="section-title">Event Location</h3>

      <div className="location-section">
        <h4 className="subsection-title">Service Address</h4>
        <p className="section-description">
          Where should our chef come to prepare your hibachi experience?
        </p>

        <div className="form-grid">
          <div className="form-group full-width">
            <label htmlFor="addressStreet" className="form-label">
              Street Address <span className="required">*</span>
            </label>
            <input
              type="text"
              id="addressStreet"
              name="addressStreet"
              value={formData.addressStreet}
              onChange={(e) => onChange('addressStreet', e.target.value)}
              placeholder="Enter street address"
              className={`form-input ${errors.addressStreet ? 'error' : ''}`}
              required
            />
            {errors.addressStreet && <span className="error-message">{errors.addressStreet}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="addressCity" className="form-label">
              City <span className="required">*</span>
            </label>
            <input
              type="text"
              id="addressCity"
              name="addressCity"
              value={formData.addressCity}
              onChange={(e) => onChange('addressCity', e.target.value)}
              placeholder="Enter city"
              className={`form-input ${errors.addressCity ? 'error' : ''}`}
              required
            />
            {errors.addressCity && <span className="error-message">{errors.addressCity}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="addressState" className="form-label">
              State <span className="required">*</span>
            </label>
            <input
              type="text"
              id="addressState"
              name="addressState"
              value={formData.addressState}
              onChange={(e) => onChange('addressState', e.target.value)}
              placeholder="Enter state"
              className={`form-input ${errors.addressState ? 'error' : ''}`}
              required
            />
            {errors.addressState && <span className="error-message">{errors.addressState}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="addressZipcode" className="form-label">
              ZIP Code <span className="required">*</span>
            </label>
            <input
              type="text"
              id="addressZipcode"
              name="addressZipcode"
              value={formData.addressZipcode}
              onChange={(e) => onChange('addressZipcode', e.target.value)}
              placeholder="Enter ZIP code"
              className={`form-input ${errors.addressZipcode ? 'error' : ''}`}
              required
            />
            {errors.addressZipcode && (
              <span className="error-message">{errors.addressZipcode}</span>
            )}
          </div>
        </div>
      </div>

      <div className="location-section">
        <div className="venue-checkbox">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={formData.sameAsVenue}
              onChange={(e) => onChange('sameAsVenue', e.target.checked)}
              className="checkbox-input"
            />
            <span className="checkbox-text">Event venue is the same as service address</span>
          </label>
        </div>

        {!formData.sameAsVenue && (
          <div className="venue-section">
            <h4 className="subsection-title">Event Venue (if different)</h4>
            <p className="section-description">
              If your event is at a different location (park, venue, etc.)
            </p>

            <div className="form-grid">
              <div className="form-group full-width">
                <label htmlFor="venueStreet" className="form-label">
                  Venue Street Address
                </label>
                <input
                  type="text"
                  id="venueStreet"
                  name="venueStreet"
                  value={formData.venueStreet || ''}
                  onChange={(e) => onChange('venueStreet', e.target.value)}
                  placeholder="Enter venue street address"
                  className={`form-input ${errors.venueStreet ? 'error' : ''}`}
                />
                {errors.venueStreet && <span className="error-message">{errors.venueStreet}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="venueCity" className="form-label">
                  Venue City
                </label>
                <input
                  type="text"
                  id="venueCity"
                  name="venueCity"
                  value={formData.venueCity || ''}
                  onChange={(e) => onChange('venueCity', e.target.value)}
                  placeholder="Enter venue city"
                  className={`form-input ${errors.venueCity ? 'error' : ''}`}
                />
                {errors.venueCity && <span className="error-message">{errors.venueCity}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="venueState" className="form-label">
                  Venue State
                </label>
                <input
                  type="text"
                  id="venueState"
                  name="venueState"
                  value={formData.venueState || ''}
                  onChange={(e) => onChange('venueState', e.target.value)}
                  placeholder="Enter venue state"
                  className={`form-input ${errors.venueState ? 'error' : ''}`}
                />
                {errors.venueState && <span className="error-message">{errors.venueState}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="venueZipcode" className="form-label">
                  Venue ZIP Code
                </label>
                <input
                  type="text"
                  id="venueZipcode"
                  name="venueZipcode"
                  value={formData.venueZipcode || ''}
                  onChange={(e) => onChange('venueZipcode', e.target.value)}
                  placeholder="Enter venue ZIP code"
                  className={`form-input ${errors.venueZipcode ? 'error' : ''}`}
                />
                {errors.venueZipcode && (
                  <span className="error-message">{errors.venueZipcode}</span>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
