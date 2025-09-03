import React from 'react'
import { CustomerAddressSectionProps } from './types'
import './styles/CustomerAddressSection.module.css'

const CustomerAddressSection: React.FC<CustomerAddressSectionProps & { className?: string }> = ({
  register,
  errors,
  sameAsVenue,
  className = ''
}) => {
  return (
    <div className={`form-section ${className}`}>
      <h3 className="section-title">
        <i className="bi bi-house me-2"></i>
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
                  {...register('addressStreet', { required: 'Street address is required' })}
                  placeholder="123 Main Street, Apt 2B"
                />
                {errors.addressStreet && (
                  <div className="invalid-feedback">{errors.addressStreet.message}</div>
                )}
              </div>
            </div>
          </div>

          <div className="row">
            <div className="col-md-6">
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

            <div className="col-md-3">
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

            <div className="col-md-3">
              <div className="form-group">
                <label htmlFor="addressZipcode" className="form-label required">
                  ZIP Code
                </label>
                <input
                  type="text"
                  id="addressZipcode"
                  className={`form-control ${errors.addressZipcode ? 'is-invalid' : ''}`}
                  {...register('addressZipcode', { required: 'ZIP code is required' })}
                  placeholder="94102"
                />
                {errors.addressZipcode && (
                  <div className="invalid-feedback">{errors.addressZipcode.message}</div>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default CustomerAddressSection
