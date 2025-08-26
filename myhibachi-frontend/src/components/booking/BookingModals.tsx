import React from 'react';
import { BookingModalProps } from './types';
import './styles/BookingModals.module.css';

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
        <div className="modal fade show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  <i className="bi bi-exclamation-triangle text-warning me-2"></i>
                  Missing Information
                </h5>
              </div>
              <div className="modal-body">
                <p>Please fill in the following required fields:</p>
                <ul className="list-unstyled">
                  {missingFields.map((field, index) => (
                    <li key={index} className="mb-1">
                      <i className="bi bi-arrow-right text-primary me-2"></i>
                      {field}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={handleCloseValidation}
                >
                  <i className="bi bi-check-lg me-2"></i>
                  Got It
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Agreement Modal */}
      {showAgreementModal && (
        <div className="modal fade show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered modal-lg">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  <i className="bi bi-file-text text-primary me-2"></i>
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
                    <li>50% deposit required to secure booking</li>
                    <li>Remaining balance due on event day</li>
                    <li>Travel fees may apply for locations outside our standard service area</li>
                  </ul>

                  <h6 className="mt-3">Cancellation Policy:</h6>
                  <ul>
                    <li>Full refund if cancelled 7+ days before event</li>
                    <li>50% refund if cancelled 3-6 days before event</li>
                    <li>No refund if cancelled within 48 hours of event</li>
                  </ul>

                  <h6 className="mt-3">Client Responsibilities:</h6>
                  <ul>
                    <li>Provide adequate outdoor space with access to power outlet</li>
                    <li>Ensure safe and clean cooking environment</li>
                    <li>Inform us of any food allergies or dietary restrictions</li>
                  </ul>

                  <p className="mt-3">
                    <strong>By confirming this booking, you agree to these terms and conditions.</strong>
                  </p>
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-outline-secondary me-2"
                  onClick={handleCancelAgreement}
                >
                  <i className="bi bi-x-lg me-2"></i>
                  Cancel
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={handleConfirmAgreement}
                  disabled={isSubmitting}
                >
                  <i className="bi bi-check-lg me-2"></i>
                  I Agree - Submit Booking
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
