import './styles/ContactInfoSection.module.css'

import React from 'react'

import { FormSectionProps } from './types'

const ContactInfoSection: React.FC<FormSectionProps & { className?: string }> = ({
  register,
  errors,
  className = ''
}) => {
  return (
    <div className={`form-section ${className}`}>
      <h3 className="section-title">
        <i className="bi bi-person-fill me-2"></i>
        Contact Information
      </h3>

      <div className="row">
        <div className="col-md-6">
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
            {errors.name && <div className="invalid-feedback">{errors.name.message}</div>}
          </div>
        </div>

        <div className="col-md-6">
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
                  message: 'Invalid email address'
                }
              })}
              placeholder="your.email@example.com"
            />
            {errors.email && <div className="invalid-feedback">{errors.email.message}</div>}
          </div>
        </div>
      </div>

      <div className="row">
        <div className="col-md-6">
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
            {errors.phone && <div className="invalid-feedback">{errors.phone.message}</div>}
          </div>
        </div>

        <div className="col-md-6">
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
                max: { value: 50, message: 'Maximum 50 guests allowed' }
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
  )
}

export default ContactInfoSection
