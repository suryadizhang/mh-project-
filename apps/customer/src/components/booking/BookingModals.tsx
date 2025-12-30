import { AlertTriangle, ArrowRight, Check, FileText, X } from 'lucide-react';
import React from 'react';

import { usePricing } from '@/hooks/usePricing';
import { BookingModalProps } from './types';

const BookingModals: React.FC<BookingModalProps & { className?: string }> = ({
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
  // Get deposit amount from SSoT pricing system
  const { depositAmount } = usePricing();

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
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-md mx-4 animate-in zoom-in-95 duration-200">
            <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
              {/* Header */}
              <div className="bg-gradient-to-r from-amber-500 to-orange-500 px-6 py-4">
                <h5 className="text-xl font-bold text-white flex items-center gap-2">
                  <AlertTriangle className="w-6 h-6" />
                  Missing Information
                </h5>
              </div>

              {/* Body */}
              <div className="p-6">
                <p className="text-gray-600 mb-4">Please fill in the following required fields:</p>
                <ul className="space-y-2">
                  {missingFields.map((field, index) => (
                    <li key={index} className="flex items-center gap-2 text-gray-700 bg-gray-50 px-4 py-2 rounded-lg">
                      <ArrowRight className="w-4 h-4 text-red-500 flex-shrink-0" />
                      <span>{field}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Footer */}
              <div className="px-6 py-4 bg-gray-50 border-t border-gray-100">
                <button
                  type="button"
                  className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-red-600 to-red-700 text-white font-semibold rounded-xl hover:from-red-700 hover:to-red-800 transition-all duration-200 shadow-md hover:shadow-lg"
                  onClick={handleCloseValidation}
                >
                  <Check className="w-5 h-5" />
                  Got It
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Agreement Modal */}
      {showAgreementModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-2xl mx-4 max-h-[90vh] animate-in zoom-in-95 duration-200">
            <div className="bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
              {/* Header */}
              <div className="bg-gradient-to-r from-red-600 to-red-700 px-6 py-4 flex-shrink-0">
                <h5 className="text-xl font-bold text-white flex items-center gap-2">
                  <FileText className="w-6 h-6" />
                  Booking Agreement & Terms
                </h5>
              </div>

              {/* Body - Scrollable */}
              <div className="p-6 overflow-y-auto flex-grow">
                <div className="space-y-6">
                  <div>
                    <h6 className="font-bold text-gray-800 mb-2 flex items-center gap-2">
                      <span className="w-6 h-6 bg-red-100 text-red-600 rounded-full flex items-center justify-center text-sm">1</span>
                      Service Agreement
                    </h6>
                    <ul className="space-y-1 text-gray-600 text-sm ml-8">
                      <li className="flex items-start gap-2">
                        <span className="text-green-500 mt-1">✓</span>
                        Professional hibachi chef service with entertainment and cooking
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-500 mt-1">✓</span>
                        Fresh, high-quality ingredients prepared on-site
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-500 mt-1">✓</span>
                        All necessary cooking equipment and utensils provided
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-500 mt-1">✓</span>
                        2-hour service duration (additional time available upon request)
                      </li>
                    </ul>
                  </div>

                  <div>
                    <h6 className="font-bold text-gray-800 mb-2 flex items-center gap-2">
                      <span className="w-6 h-6 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-sm">2</span>
                      Pricing & Payment
                    </h6>
                    <ul className="space-y-1 text-gray-600 text-sm ml-8">
                      <li className="flex items-start gap-2">
                        <span className="text-green-500 mt-1">✓</span>
                        Final pricing will be confirmed based on guest count and menu selection
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-500 mt-1">✓</span>
                        ${depositAmount ?? 100} refundable deposit required to secure booking
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-500 mt-1">✓</span>
                        Deposit is refundable if canceled 7+ days before event, non-refundable within 7 days
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-500 mt-1">✓</span>
                        Remaining balance due on event day
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-500 mt-1">✓</span>
                        Travel fees may apply for locations outside our standard service area
                      </li>
                    </ul>
                  </div>

                  <div>
                    <h6 className="font-bold text-gray-800 mb-2 flex items-center gap-2">
                      <span className="w-6 h-6 bg-amber-100 text-amber-600 rounded-full flex items-center justify-center text-sm">3</span>
                      Cancellation Policy
                    </h6>
                    <ul className="space-y-1 text-gray-600 text-sm ml-8">
                      <li className="flex items-start gap-2">
                        <span className="text-green-500 mt-1">✓</span>
                        Full refund if cancelled 7+ days before event
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-amber-500 mt-1">⚠</span>
                        No refund if cancelled within 7 days of event
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-500 mt-1">✓</span>
                        One free reschedule within 48 hours of booking; additional reschedules cost ${depositAmount ?? 100}
                      </li>
                    </ul>
                  </div>

                  <div>
                    <h6 className="font-bold text-gray-800 mb-2 flex items-center gap-2">
                      <span className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm">4</span>
                      Client Responsibilities
                    </h6>
                    <ul className="space-y-1 text-gray-600 text-sm ml-8">
                      <li className="flex items-start gap-2">
                        <span className="text-blue-500 mt-1">•</span>
                        Provide adequate outdoor space with access to power outlet
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-blue-500 mt-1">•</span>
                        Ensure safe and clean cooking environment
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-blue-500 mt-1">•</span>
                        Inform us of any food allergies or dietary restrictions
                      </li>
                    </ul>
                  </div>

                  <div className="bg-red-50 border border-red-200 rounded-xl p-4">
                    <p className="text-red-800 font-semibold text-sm">
                      By confirming this booking, you agree to these terms and conditions.
                    </p>
                  </div>
                </div>
              </div>

              {/* Footer */}
              <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex-shrink-0 flex flex-col sm:flex-row gap-3">
                <button
                  type="button"
                  className="flex-1 flex items-center justify-center gap-2 px-6 py-3 border-2 border-gray-300 text-gray-700 font-semibold rounded-xl hover:bg-gray-100 transition-all duration-200"
                  onClick={handleCancelAgreement}
                >
                  <X className="w-5 h-5" />
                  Cancel
                </button>
                <button
                  type="button"
                  className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-green-600 to-green-700 text-white font-semibold rounded-xl hover:from-green-700 hover:to-green-800 transition-all duration-200 shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                  onClick={handleConfirmAgreement}
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <>
                      <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Submitting...
                    </>
                  ) : (
                    <>
                      <Check className="w-5 h-5" />
                      I Agree - Submit Booking
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
