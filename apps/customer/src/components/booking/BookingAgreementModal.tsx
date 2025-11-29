'use client';

import React from 'react';

interface BookingAgreementModalProps {
  isOpen: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  isSubmitting: boolean;
  allergenAcknowledged: boolean;
  setAllergenAcknowledged: (value: boolean) => void;
  riskAccepted: boolean;
  setRiskAccepted: (value: boolean) => void;
  willCommunicate: boolean;
  setWillCommunicate: (value: boolean) => void;
}

export default function BookingAgreementModal({
  isOpen,
  onConfirm,
  onCancel,
  isSubmitting,
  allergenAcknowledged,
  setAllergenAcknowledged,
  riskAccepted,
  setRiskAccepted,
  willCommunicate,
  setWillCommunicate,
}: BookingAgreementModalProps) {
  if (!isOpen) return null;

  return (
    <div className="modal fade show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
      <div className="modal-dialog modal-dialog-centered modal-lg">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">
              <i className="bi bi-file-text text-primary me-2"></i>
              Booking Agreement & Terms
            </h5>
          </div>
          <div className="modal-body" style={{ maxHeight: '70vh', overflowY: 'auto' }}>
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
                  Deposit is refundable if canceled 4+ days before event, non-refundable within 4
                  days
                </li>
                <li>Remaining balance due on event day</li>
                <li>Travel fees may apply for locations outside our standard service area</li>
              </ul>

              <h6 className="mt-3">Cancellation & Changes Policy:</h6>
              <ul>
                <li>
                  <strong>Deposit Refund:</strong> $100 deposit is refundable if canceled 4+ days
                  before event, non-refundable within 4 days
                </li>
                <li>
                  <strong>Free Reschedule:</strong> One free reschedule allowed if requested 24+
                  hours before event; additional reschedules cost $100
                </li>
                <li>
                  <strong>Menu Changes:</strong> No menu changes allowed within 12 hours of event (we
                  prepare fresh ingredients specifically for your party)
                </li>
                <li>
                  <strong>Food Safety:</strong> No refund for ordered food as we cannot keep food that
                  has been out of refrigeration for more than 4 hours
                </li>
              </ul>

              {/* ⚠️ ALLERGEN DISCLOSURE SECTION - CRITICAL FOR LEGAL PROTECTION */}
              <div
                className="alert alert-warning mt-4 mb-3"
                style={{ border: '2px solid #ff9800', backgroundColor: '#fff3e0' }}
              >
                <h6 className="text-danger mb-3">
                  <i className="bi bi-exclamation-triangle-fill me-2"></i>
                  ALLERGEN DISCLOSURE & ACKNOWLEDGMENT
                </h6>

                <p>
                  <strong>IMPORTANT - Please Read Carefully:</strong>
                </p>

                <p className="mb-2">
                  <strong>Our kitchen uses and tracks these allergens:</strong>
                </p>
                <ul className="mb-3">
                  <li>
                    <strong>Major Allergens (FDA):</strong> Shellfish (shrimp, lobster, scallops),
                    Fish (salmon), Gluten (gyoza, noodles, teriyaki sauce), Soy (sauces, tofu), Eggs
                    (fried rice)
                  </li>
                  <li>
                    <strong>Additional Allergens:</strong> Celery (salad dressing), Corn (corn starch
                    in teriyaki sauce), Sulfites (in sake)
                  </li>
                </ul>

                <div
                  className="border-top pt-3 mt-3"
                  style={{ borderColor: '#ff9800 !important' }}
                >
                  <p className="mb-2">
                    <strong className="text-danger">⚠️ CROSS-CONTAMINATION RISK:</strong>
                  </p>
                  <p className="mb-3">
                    We use <strong>shared cooking surfaces, utensils, and oils</strong>. While we take
                    precautions to accommodate dietary restrictions, we{' '}
                    <strong className="text-danger">CANNOT GUARANTEE</strong> a 100% allergen-free
                    environment for customers with severe allergies.
                  </p>
                </div>

                {/* Required Allergen Checkboxes */}
                <div className="form-check mb-2">
                  <input
                    type="checkbox"
                    className="form-check-input"
                    id="allergen-read"
                    checked={allergenAcknowledged}
                    onChange={(e) => setAllergenAcknowledged(e.target.checked)}
                    required
                  />
                  <label className="form-check-label" htmlFor="allergen-read">
                    <strong>I acknowledge</strong> that I have read the allergen information and
                    cross-contamination warning above. *
                  </label>
                </div>

                <div className="form-check mb-2">
                  <input
                    type="checkbox"
                    className="form-check-input"
                    id="allergen-risk"
                    checked={riskAccepted}
                    onChange={(e) => setRiskAccepted(e.target.checked)}
                    required
                  />
                  <label className="form-check-label" htmlFor="allergen-risk">
                    I understand that My Hibachi cannot guarantee a 100% allergen-free environment and{' '}
                    <strong>I accept this risk</strong>. *
                  </label>
                </div>

                <div className="form-check mb-3">
                  <input
                    type="checkbox"
                    className="form-check-input"
                    id="allergen-communicate"
                    checked={willCommunicate}
                    onChange={(e) => setWillCommunicate(e.target.checked)}
                    required
                  />
                  <label className="form-check-label" htmlFor="allergen-communicate">
                    <strong>I will communicate ALL food allergies</strong> and dietary restrictions to
                    My Hibachi staff before my event. *
                  </label>
                </div>

                <p className="small mb-0">
                  <a href="/allergens" target="_blank" className="text-primary">
                    <i className="bi bi-info-circle me-1"></i>
                    View Full Allergen List & Safety Guide →
                  </a>
                </p>
              </div>

              <h6 className="mt-3">Liability Waiver:</h6>
              <p className="mb-2">
                By confirming this booking, I release My Hibachi LLC from liability for allergic
                reactions resulting from:
              </p>
              <ul className="mb-3">
                <li>Failure to communicate allergies in advance</li>
                <li>Cross-contamination despite reasonable precautions taken by staff</li>
                <li>Consumption of menu items known to contain allergens</li>
              </ul>

              <h6 className="mt-3">Client Responsibilities:</h6>
              <ul>
                <li>Provide adequate outdoor space with access to power outlet</li>
                <li>Ensure safe and clean cooking environment</li>
                <li>Communicate all food allergies and dietary restrictions in advance</li>
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
              onClick={onCancel}
            >
              <i className="bi bi-x-lg me-2"></i>
              Cancel
            </button>
            <button
              type="button"
              className="btn btn-primary"
              onClick={onConfirm}
              disabled={isSubmitting || !allergenAcknowledged || !riskAccepted || !willCommunicate}
              title={
                !allergenAcknowledged || !riskAccepted || !willCommunicate
                  ? 'Please check all allergen acknowledgment boxes to continue'
                  : ''
              }
            >
              <i className="bi bi-check-lg me-2"></i>
              {isSubmitting ? 'Submitting...' : 'I Agree - Submit Booking'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
