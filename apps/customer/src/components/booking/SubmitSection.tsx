import { CalendarCheck, Hourglass, Shield } from 'lucide-react';
import React from 'react';

interface SubmitSectionProps {
  isSubmitting: boolean;
  className?: string;
}

const SubmitSection: React.FC<SubmitSectionProps> = ({ isSubmitting, className = '' }) => {
  return (
    <div className={`py-6 text-center ${className}`}>
      {/* Newsletter Auto-Subscribe Notice */}
      <div className="mb-6 rounded-xl border border-orange-200 bg-orange-50 p-4">
        <p className="text-sm text-gray-700">
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
        className="inline-flex w-full transform items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-red-600 to-red-700 px-10 py-4 text-lg font-bold text-white shadow-lg transition-all duration-300 hover:-translate-y-1 hover:from-red-700 hover:to-red-800 hover:shadow-xl disabled:transform-none disabled:cursor-not-allowed disabled:opacity-50 md:w-auto"
        disabled={isSubmitting}
      >
        {isSubmitting ? (
          <>
            <Hourglass className="h-5 w-5 animate-pulse" />
            Processing Booking...
          </>
        ) : (
          <>
            <CalendarCheck className="h-5 w-5" />
            Submit Booking Request
          </>
        )}
      </button>
      <p className="mt-4 text-sm text-gray-500">
        <Shield className="mr-1 inline-block h-4 w-4" />
        Your information is secure and will only be used to process your booking.
      </p>
    </div>
  );
};

export default SubmitSection;
