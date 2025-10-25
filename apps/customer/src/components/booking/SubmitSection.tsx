import './styles/SubmitSection.module.css'

import React from 'react'

interface SubmitSectionProps {
  isSubmitting: boolean
  className?: string
}

const SubmitSection: React.FC<SubmitSectionProps> = ({ isSubmitting, className = '' }) => {
  return (
    <div className={`form-section text-center ${className}`}>
      {/* Newsletter Auto-Subscribe Notice */}
      <div className="mb-4 p-3 bg-orange-50 border border-orange-200 rounded-lg">
        <p className="text-xs text-gray-700">
          📧 <strong>You&apos;ll automatically receive our newsletter</strong> with exclusive offers and hibachi tips.
          <br />
          <span className="text-gray-600">Don&apos;t want updates? Simply reply <strong>&quot;STOP&quot;</strong> anytime to unsubscribe.</span>
        </p>
      </div>

      <button
        type="submit"
        className="btn btn-primary btn-lg booking-submit-btn"
        disabled={isSubmitting}
      >
        {isSubmitting ? (
          <>
            <i className="bi bi-hourglass-split me-2"></i>
            Processing Booking...
          </>
        ) : (
          <>
            <i className="bi bi-calendar-check me-2"></i>
            Submit Booking Request
          </>
        )}
      </button>
      <p className="mt-3 text-muted">
        <small>
          <i className="bi bi-shield-check me-1"></i>
          Your information is secure and will only be used to process your booking.
        </small>
      </p>
    </div>
  )
}

export default SubmitSection
