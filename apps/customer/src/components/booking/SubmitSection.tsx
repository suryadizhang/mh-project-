import './styles/SubmitSection.module.css';

import { CalendarCheck, Hourglass, Shield } from 'lucide-react';
import React from 'react';

interface SubmitSectionProps {
  isSubmitting: boolean;
  className?: string;
}

const SubmitSection: React.FC<SubmitSectionProps> = ({ isSubmitting, className = '' }) => {
  return (
    <div className={`form-section text-center ${className}`}>
      {/* Newsletter Auto-Subscribe Notice */}
      <div className="mb-4 rounded-lg border border-orange-200 bg-orange-50 p-3">
        <p className="text-xs text-gray-700">
          📧 <strong>You&apos;ll automatically receive our newsletter</strong> with exclusive offers
          and hibachi tips.
          <br />
          <span className="text-gray-600">
            Don&apos;t want updates? Simply reply <strong>&quot;STOP&quot;</strong> anytime to
            unsubscribe.
          </span>
        </p>
      </div>

      <button
        type="submit"
        className="btn btn-primary btn-lg booking-submit-btn"
        disabled={isSubmitting}
      >
        {isSubmitting ? (
          <>
            <Hourglass className="mr-2 inline-block" size={20} />
            Processing Booking...
          </>
        ) : (
          <>
            <CalendarCheck className="mr-2 inline-block" size={20} />
            Submit Booking Request
          </>
        )}
      </button>
      <p className="text-muted mt-3">
        <small>
          <Shield className="mr-1 inline-block" size={16} />
          Your information is secure and will only be used to process your booking.
        </small>
      </p>
    </div>
  );
};

export default SubmitSection;
