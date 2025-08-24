import React from 'react';
import './styles/SubmitSection.module.css';

interface SubmitSectionProps {
  isSubmitting: boolean;
  className?: string;
}

const SubmitSection: React.FC<SubmitSectionProps> = ({ 
  isSubmitting,
  className = '' 
}) => {
  return (
    <div className={`form-section text-center ${className}`}>
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
  );
};

export default SubmitSection;

