import './styles/BookingModals.module.css';

import { AlertTriangle, ArrowRight, Check, FileText, X } from 'lucide-react';
import React from 'react';

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
        <div className="modal fade show block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  <AlertTriangle className="text-warning mr-2 inline-block" size={20} />
                  Missing Information
                </h5>
              </div>
              <div className="modal-body">
                <p>Please fill in the following required fields:</p>
                <ul className="list-unstyled">
                  {missingFields.map((field, index) => (
                    <li key={index} className="mb-1">
                      <ArrowRight className="text-primary mr-2 inline-block" size={16} />
                      {field}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-primary" onClick={handleCloseValidation}>
                  <Check className="mr-2 inline-block" size={18} />
                  Got It
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Agreement Modal */}
      {showAgreementModal && (
        <div className="modal fade show block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered modal-lg">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  <FileText className="text-primary mr-2 inline-block" size={20} />
                  Booking Agreement & Terms
                </h5>
              </div>
              <div className="modal-body">
                <div className="agreement-content">
                  <h6>Service Agreement:</h6>
                  <ul>
                    <li>Professional hibachi chef service with entertainment and cooking</li>
                    <li>Fresh, high-quality ingredients prepared on-site</li>
                    <li>All necessary cooking equipment and utensils provided</li>
                    <li>2-hour service duration (additional time available upon request)</li>
                  </ul>

                  <h6 className="mt-3">Pricing & Payment:</h6>
                  <ul>
                    <li>Final pricing will be confirmed based on guest count and menu selection</li>
                    <li>$100 refundable deposit required to secure booking</li>
                    <li>
                      Deposit is refundable if canceled 7+ days before event, non-refundable within
                      7 days
                    </li>
                    <li>Remaining balance due on event day</li>
                    <li>Travel fees may apply for locations outside our standard service area</li>
                  </ul>

                  <h6 className="mt-3">Cancellation Policy:</h6>
                  <ul>
                    <li>Full refund if cancelled 7+ days before event</li>
                    <li>No refund if cancelled within 7 days of event</li>
                    <li>
                      One free reschedule within 48 hours of booking; additional reschedules cost
                      $100
                    </li>
                  </ul>

                  <h6 className="mt-3">Client Responsibilities:</h6>
                  <ul>
                    <li>Provide adequate outdoor space with access to power outlet</li>
                    <li>Ensure safe and clean cooking environment</li>
                    <li>Inform us of any food allergies or dietary restrictions</li>
                  </ul>

                  <p className="mt-3">
                    <strong>
                      By confirming this booking, you agree to these terms and conditions.
                    </strong>
                  </p>
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-outline-secondary me-2"
                  onClick={handleCancelAgreement}
                >
                  <X className="mr-2 inline-block" size={18} />
                  Cancel
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={handleConfirmAgreement}
                  disabled={isSubmitting}
                >
                  <Check className="mr-2 inline-block" size={18} />I Agree - Submit Booking
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
