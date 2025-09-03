'use client'

import React from 'react'
import type { BookingFormData } from '../../data/booking/types'

interface ContactInfoProps {
  formData: BookingFormData
  onChange: (field: keyof BookingFormData, value: string | number | Date | boolean) => void
  errors: Record<string, string>
}

export function ContactInfo({ formData, onChange, errors }: ContactInfoProps) {
  return (
    <div className="form-section">
      <h3 className="section-title">Contact Information</h3>
      <div className="form-grid">
        <div className="form-group">
          <label htmlFor="name" className="form-label">
            Full Name <span className="required">*</span>
          </label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={e => onChange('name', e.target.value)}
            placeholder="Enter your full name"
            className={`form-input ${errors.name ? 'error' : ''}`}
            required
          />
          {errors.name && <span className="error-message">{errors.name}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="email" className="form-label">
            Email <span className="required">*</span>
          </label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={e => onChange('email', e.target.value)}
            placeholder="Enter your email address"
            className={`form-input ${errors.email ? 'error' : ''}`}
            required
          />
          {errors.email && <span className="error-message">{errors.email}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="phone" className="form-label">
            Phone Number <span className="required">*</span>
          </label>
          <input
            type="tel"
            id="phone"
            name="phone"
            value={formData.phone}
            onChange={e => onChange('phone', e.target.value)}
            placeholder="(555) 123-4567"
            className={`form-input ${errors.phone ? 'error' : ''}`}
            required
          />
          {errors.phone && <span className="error-message">{errors.phone}</span>}
        </div>
      </div>
    </div>
  )
}
