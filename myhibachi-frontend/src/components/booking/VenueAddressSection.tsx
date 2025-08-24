import React from 'react';
import { VenueAddressSectionProps } from './types';
import './styles/VenueAddressSection.module.css';

const VenueAddressSection: React.FC<VenueAddressSectionProps & { className?: string }> = ({ 
  register, 
  errors, 
  className = '' 
}) => {
  return (
    <div className={`form-section ${className}`}>
      <h3 className="section-title">
        <i className="bi bi-geo-alt me-2"></i>
        Event Venue Address
      </h3>
      <p className="section-description">
        Please provide the address where the hibachi event will take place.
      </p>

      <div className="row">
        <div className="col-12">
          <div className="form-group">
            <label htmlFor="venueStreet" className="form-label required">Street Address</label>
            <input
              type="text"
              id="venueStreet"
              className={`form-control ${errors.venueStreet ? 'is-invalid' : ''}`}
              {...register('venueStreet', { required: 'Venue street address is required' })}
              placeholder="123 Main Street, Apt 2B"
            />
            {errors.venueStreet && (
              <div className="invalid-feedback">{errors.venueStreet.message}</div>
            )}
          </div>
        </div>
      </div>

      <div className="row">
        <div className="col-md-6">
          <div className="form-group">
            <label htmlFor="venueCity" className="form-label required">City</label>
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

        <div className="col-md-3">
          <div className="form-group">
            <label htmlFor="venueState" className="form-label required">State</label>
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

        <div className="col-md-3">
          <div className="form-group">
            <label htmlFor="venueZipcode" className="form-label required">ZIP Code</label>
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
  );
};

export default VenueAddressSection;

