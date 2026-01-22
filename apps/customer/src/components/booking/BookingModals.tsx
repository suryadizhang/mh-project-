import { AlertTriangle, ArrowRight, Check, FileText, X } from 'lucide-react';
import React from 'react';

import { usePricing } from '@/hooks/usePricing';
import { BookingModalProps } from './types';

const BookingModals: React.FC<BookingModalProps> = ({
  showValidationModal,
  setShowValidationModal,
  showAgreementModal,
  // setShowAgreementModal, // Commented out as it's not used in this component
  missingFields,
  isSubmitting,
  onAgreementConfirm,
  onAgreementCancel,
  // className = '' // Commented out as it's not used in this component
}) => {
  // Get deposit amount and refund policy from SSoT pricing system
  const {
    depositAmount,
    depositRefundableDays,
    standardDurationMinutes,
    freeRescheduleHours,
    rescheduleFee,
  } = usePricing();

  const handleCloseValidation = () => {
    setShowValidationModal(false);
  };

  const handleConfirmAgreement = () => {
    onAgreementConfirm();
  };

  const handleCancelAgreement = () => {
    onAgreementCancel();
  };

  return (
    <>
      {/* Validation Modal */}
      {showValidationModal && (
        <div className="animate-in fade-in fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm duration-200">
          <div className="animate-in zoom-in-95 mx-4 w-full max-w-md duration-200">
            <div className="overflow-hidden rounded-2xl bg-white shadow-2xl">
              {/* Header */}
              <div className="bg-gradient-to-r from-amber-500 to-orange-500 px-6 py-4">
                <h5 className="flex items-center gap-2 text-xl font-bold text-white">
                  <AlertTriangle className="h-6 w-6" />
                  Missing Information
                </h5>
              </div>

              {/* Body */}
              <div className="p-6">
                <p className="mb-4 text-gray-600">Please fill in the following required fields:</p>
                <ul className="space-y-2">
                  {missingFields.map((field, index) => (
                    <li
                      key={index}
                      className="flex items-center gap-2 rounded-lg bg-gray-50 px-4 py-2 text-gray-700"
                    >
                      <ArrowRight className="h-4 w-4 flex-shrink-0 text-red-500" />
                      <span>{field}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Footer */}
              <div className="border-t border-gray-100 bg-gray-50 px-6 py-4">
                <button
                  type="button"
                  className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-red-600 to-red-700 px-6 py-3 font-semibold text-white shadow-md transition-all duration-200 hover:from-red-700 hover:to-red-800 hover:shadow-lg"
                  onClick={handleCloseValidation}
                >
                  <Check className="h-5 w-5" />
                  Got It
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Agreement Modal */}
      {showAgreementModal && (
        <div className="animate-in fade-in fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm duration-200">
          <div className="animate-in zoom-in-95 mx-4 max-h-[90vh] w-full max-w-2xl duration-200">
            <div className="flex max-h-[90vh] flex-col overflow-hidden rounded-2xl bg-white shadow-2xl">
              {/* Header */}
              <div className="flex-shrink-0 bg-gradient-to-r from-red-600 to-red-700 px-6 py-4">
                <h5 className="flex items-center gap-2 text-xl font-bold text-white">
                  <FileText className="h-6 w-6" />
                  Booking Agreement & Terms
                </h5>
              </div>

              {/* Body - Scrollable */}
              <div className="flex-grow overflow-y-auto p-6">
                <div className="space-y-6">
                  <div>
                    <h6 className="mb-2 flex items-center gap-2 font-bold text-gray-800">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-red-100 text-sm text-red-600">
                        1
                      </span>
                      Service Agreement
                    </h6>
                    <ul className="ml-8 space-y-1 text-sm text-gray-600">
                      <li className="flex items-start gap-2">
                        <span className="mt-1 text-green-500">✓</span>
                        Professional hibachi chef service with entertainment and cooking
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="mt-1 text-green-500">✓</span>
                        Fresh, high-quality ingredients prepared on-site
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="mt-1 text-green-500">✓</span>
                        All necessary cooking equipment and utensils provided
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="mt-1 text-green-500">✓</span>
                        {Math.floor((standardDurationMinutes ?? 90) / 60)}-hour service duration
                        (additional time available upon request)
                      </li>
                    </ul>
                  </div>

                  <div>
                    <h6 className="mb-2 flex items-center gap-2 font-bold text-gray-800">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-green-100 text-sm text-green-600">
                        2
                      </span>
                      Pricing & Payment
                    </h6>
                    <ul className="ml-8 space-y-1 text-sm text-gray-600">
                      <li className="flex items-start gap-2">
                        <span className="mt-1 text-green-500">✓</span>
                        Final pricing will be confirmed based on guest count and menu selection
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="mt-1 text-green-500">✓</span>${depositAmount ?? 100}{' '}
                        refundable deposit required to secure booking
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="mt-1 text-green-500">✓</span>
                        Deposit is refundable if canceled {depositRefundableDays ?? 4}+ days before
                        event, non-refundable within {depositRefundableDays ?? 4} days
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="mt-1 text-green-500">✓</span>
                        Remaining balance due on event day
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="mt-1 text-green-500">✓</span>
                        Travel fees may apply for locations outside our standard service area
                      </li>
                    </ul>
                  </div>

                  <div>
                    <h6 className="mb-2 flex items-center gap-2 font-bold text-gray-800">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-amber-100 text-sm text-amber-600">
                        3
                      </span>
                      Cancellation Policy
                    </h6>
                    <ul className="ml-8 space-y-1 text-sm text-gray-600">
                      <li className="flex items-start gap-2">
                        <span className="mt-1 text-green-500">✓</span>
                        Full refund if cancelled {depositRefundableDays ?? 4}+ days before event
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="mt-1 text-amber-500">⚠</span>
                        No refund if cancelled within {depositRefundableDays ?? 4} days of event
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="mt-1 text-green-500">✓</span>
                        One free reschedule within {freeRescheduleHours ?? 24} hours of booking;
                        additional reschedules cost ${rescheduleFee ?? 200}
                      </li>
                    </ul>
                  </div>

                  <div>
                    <h6 className="mb-2 flex items-center gap-2 font-bold text-gray-800">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-100 text-sm text-blue-600">
                        4
                      </span>
                      Client Responsibilities
                    </h6>
                    <ul className="ml-8 space-y-1 text-sm text-gray-600">
                      <li className="flex items-start gap-2">
                        <span className="mt-1 text-blue-500">•</span>
                        Provide adequate outdoor space with access to power outlet
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="mt-1 text-blue-500">•</span>
                        Ensure safe and clean cooking environment
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="mt-1 text-blue-500">•</span>
                        Inform us of any food allergies or dietary restrictions
                      </li>
                    </ul>
                  </div>

                  <div className="rounded-xl border border-red-200 bg-red-50 p-4">
                    <p className="text-sm font-semibold text-red-800">
                      By confirming this booking, you agree to these terms and conditions.
                    </p>
                  </div>
                </div>
              </div>

              {/* Footer */}
              <div className="flex flex-shrink-0 flex-col gap-3 border-t border-gray-100 bg-gray-50 px-6 py-4 sm:flex-row">
                <button
                  type="button"
                  className="flex flex-1 items-center justify-center gap-2 rounded-xl border-2 border-gray-300 px-6 py-3 font-semibold text-gray-700 transition-all duration-200 hover:bg-gray-100"
                  onClick={handleCancelAgreement}
                >
                  <X className="h-5 w-5" />
                  Cancel
                </button>
                <button
                  type="button"
                  className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-green-600 to-green-700 px-6 py-3 font-semibold text-white shadow-md transition-all duration-200 hover:from-green-700 hover:to-green-800 hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-50"
                  onClick={handleConfirmAgreement}
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <>
                      <svg className="h-5 w-5 animate-spin" viewBox="0 0 24 24">
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                          fill="none"
                        />
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        />
                      </svg>
                      Submitting...
                    </>
                  ) : (
                    <>
                      <Check className="h-5 w-5" />I Agree - Submit Booking
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default BookingModals;
