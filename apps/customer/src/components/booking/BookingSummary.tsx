'use client';

import { format } from 'date-fns';
import React from 'react';

import { usePricing } from '@/hooks/usePricing';

import type { BookingFormData } from '../../data/booking/types';

interface BookingSummaryProps {
  formData: BookingFormData;
  isSubmitting: boolean;
  onSubmit: () => void;
}

export function BookingSummary({ formData, isSubmitting, onSubmit }: BookingSummaryProps) {
  // Fetch dynamic pricing from database
  const { adultPrice, childPrice, isLoading: isPricingLoading } = usePricing();

  // Estimated total - only calculate when pricing is available
  const estimatedTotal = adultPrice !== undefined ? formData.guestCount * adultPrice : 0;

  return (
    <div className="booking-summary">
      <div className="summary-card">
        <h3 className="summary-title">Booking Summary</h3>

        <div className="summary-section">
          <h4 className="summary-subtitle">Event Details</h4>
          <div className="summary-item">
            <span className="summary-label">Date:</span>
            <span className="summary-value">
              {formData.eventDate
                ? format(formData.eventDate, 'EEEE, MMMM d, yyyy')
                : 'Not selected'}
            </span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Time:</span>
            <span className="summary-value">{formData.eventTime || 'Not selected'}</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Guests:</span>
            <span className="summary-value">{formData.guestCount} people</span>
          </div>
        </div>

        <div className="summary-section">
          <h4 className="summary-subtitle">Contact</h4>
          <div className="summary-item">
            <span className="summary-label">Name:</span>
            <span className="summary-value">{formData.name || 'Not provided'}</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Email:</span>
            <span className="summary-value">{formData.email || 'Not provided'}</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Phone:</span>
            <span className="summary-value">{formData.phone || 'Not provided'}</span>
          </div>
        </div>

        <div className="summary-section">
          <h4 className="summary-subtitle">Location</h4>
          <div className="summary-item">
            <span className="summary-label">Service Address:</span>
            <span className="summary-value">
              {formData.addressStreet ? (
                <>
                  {formData.addressStreet}
                  <br />
                  {formData.addressCity}, {formData.addressState} {formData.addressZipcode}
                </>
              ) : (
                'Not provided'
              )}
            </span>
          </div>
          {!formData.sameAsVenue && formData.venueStreet && (
            <div className="summary-item">
              <span className="summary-label">Venue:</span>
              <span className="summary-value">
                {formData.venueStreet}
                <br />
                {formData.venueCity}, {formData.venueState} {formData.venueZipcode}
              </span>
            </div>
          )}
        </div>

        <div className="summary-section pricing-section">
          <h4 className="summary-subtitle">Estimated Pricing</h4>
          {isPricingLoading ? (
            <div className="pricing-loading">
              <small>Loading current pricing...</small>
            </div>
          ) : (
            <>
              <div className="pricing-breakdown">
                <div className="pricing-item">
                  <span className="pricing-label">
                    {formData.guestCount} Adults @ ${adultPrice} each:
                  </span>
                  <span className="pricing-value">${estimatedTotal}</span>
                </div>
                <div className="pricing-note">
                  <small>
                    * Final pricing may vary based on specific menu selections and add-ons. Children
                    (6-12) are ${childPrice} each. Final quote will be provided after booking.
                  </small>
                </div>
              </div>
              <div className="total-price">
                <span className="total-label">Estimated Total:</span>
                <span className="total-value">${estimatedTotal}</span>
              </div>
            </>
          )}
        </div>

        <div className="terms-section">
          <div className="terms-note">
            <small>
              📋 <strong>Next Steps:</strong> After submitting, we&apos;ll contact you within 24
              hours to confirm details, finalize menu selection, and process payment.
            </small>
          </div>
        </div>

        <button
          type="button"
          className={`submit-btn ${isSubmitting ? 'submitting' : ''}`}
          onClick={onSubmit}
          disabled={isSubmitting}
        >
          {isSubmitting ? (
            <>
              <span className="submit-spinner">⏳</span>
              Submitting Booking...
            </>
          ) : (
            <>
              <span className="submit-icon">🎉</span>
              Submit Booking Request
            </>
          )}
        </button>
      </div>
    </div>
  );
}
