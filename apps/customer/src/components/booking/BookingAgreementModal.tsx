'use client';

import React from 'react';
import { FileText, AlertTriangle, Info, X, Check } from 'lucide-react';

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

  const allAcknowledged = allergenAcknowledged && riskAccepted && willCommunicate;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-3xl mx-4 max-h-[90vh] animate-in zoom-in-95 duration-200">
        <div className="bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
          {/* Header */}
          <div className="bg-gradient-to-r from-red-600 to-red-700 px-6 py-4 flex-shrink-0">
            <h5 className="text-xl font-bold text-white flex items-center gap-2">
              <FileText className="w-6 h-6" />
              Booking Agreement & Terms
            </h5>
          </div>

          {/* Body - Scrollable */}
          <div className="p-6 overflow-y-auto flex-grow space-y-6">
            {/* Service Agreement */}
            <div>
              <h6 className="font-bold text-gray-800 mb-2 flex items-center gap-2">
                <span className="w-6 h-6 bg-red-100 text-red-600 rounded-full flex items-center justify-center text-sm font-bold">1</span>
                Service Agreement
              </h6>
              <ul className="space-y-1 text-gray-600 text-sm ml-8">
                <li className="flex items-start gap-2">
                  <span className="text-green-500 mt-0.5">✓</span>
                  Professional hibachi chef service with entertainment and cooking
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 mt-0.5">✓</span>
                  Fresh, high-quality ingredients prepared on-site
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 mt-0.5">✓</span>
                  All necessary cooking equipment and utensils provided
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 mt-0.5">✓</span>
                  2-hour service duration (additional time available upon request)
                </li>
              </ul>
            </div>

            {/* Pricing & Payment */}
            <div>
              <h6 className="font-bold text-gray-800 mb-2 flex items-center gap-2">
                <span className="w-6 h-6 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-sm font-bold">2</span>
                Pricing & Payment
              </h6>
              <ul className="space-y-1 text-gray-600 text-sm ml-8">
                <li className="flex items-start gap-2">
                  <span className="text-green-500 mt-0.5">✓</span>
                  Final pricing will be confirmed based on guest count and menu selection
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 mt-0.5">✓</span>
                  $100 refundable deposit required to secure booking
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 mt-0.5">✓</span>
                  Deposit is refundable if canceled 4+ days before event, non-refundable within 4 days
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 mt-0.5">✓</span>
                  Remaining balance due on event day
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 mt-0.5">✓</span>
                  Travel fees may apply for locations outside our standard service area
                </li>
              </ul>
            </div>

            {/* Cancellation & Changes Policy */}
            <div>
              <h6 className="font-bold text-gray-800 mb-2 flex items-center gap-2">
                <span className="w-6 h-6 bg-amber-100 text-amber-600 rounded-full flex items-center justify-center text-sm font-bold">3</span>
                Cancellation & Changes Policy
              </h6>
              <ul className="space-y-2 text-gray-600 text-sm ml-8">
                <li className="flex items-start gap-2">
                  <span className="text-green-500 mt-0.5 font-bold">•</span>
                  <span><strong>Deposit Refund:</strong> $100 deposit is refundable if canceled 4+ days before event, non-refundable within 4 days</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 mt-0.5 font-bold">•</span>
                  <span><strong>Free Reschedule:</strong> One free reschedule allowed if requested 24+ hours before event; additional reschedules cost $100</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-amber-500 mt-0.5 font-bold">•</span>
                  <span><strong>Menu Changes:</strong> No menu changes allowed within 12 hours of event (we prepare fresh ingredients specifically for your party)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-red-500 mt-0.5 font-bold">•</span>
                  <span><strong>Food Safety:</strong> No refund for ordered food as we cannot keep food that has been out of refrigeration for more than 4 hours</span>
                </li>
              </ul>
            </div>

            {/* Allergen Warning Section */}
            <div className="bg-amber-50 border-2 border-amber-400 rounded-xl p-5">
              <h6 className="font-bold text-red-600 mb-3 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5" />
                ALLERGEN DISCLOSURE & ACKNOWLEDGMENT
              </h6>

              <p className="font-semibold text-gray-800 mb-2">IMPORTANT - Please Read Carefully:</p>

              <p className="text-gray-700 font-medium mb-2">Our kitchen uses and tracks these allergens:</p>
              <ul className="space-y-2 text-gray-600 text-sm mb-4">
                <li className="flex items-start gap-2">
                  <span className="text-amber-600 mt-0.5 font-bold">⚠</span>
                  <span><strong>Major Allergens (FDA):</strong> Shellfish (shrimp, lobster, scallops), Fish (salmon), Gluten (gyoza, noodles, teriyaki sauce), Soy (sauces, tofu), Eggs (fried rice)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-amber-600 mt-0.5 font-bold">⚠</span>
                  <span><strong>Additional Allergens:</strong> Celery (salad dressing), Corn (corn starch in teriyaki sauce), Sulfites (in sake)</span>
                </li>
              </ul>

              <div className="border-t border-amber-300 pt-4 mt-4">
                <p className="font-semibold text-red-600 mb-2">⚠️ CROSS-CONTAMINATION RISK:</p>
                <p className="text-gray-700 mb-4">
                  We use <strong>shared cooking surfaces, utensils, and oils</strong>. While we take
                  precautions to accommodate dietary restrictions, we{' '}
                  <strong className="text-red-600">CANNOT GUARANTEE</strong> a 100% allergen-free
                  environment for customers with severe allergies.
                </p>
              </div>

              {/* Required Allergen Checkboxes */}
              <div className="space-y-3 mt-4">
                <label className="flex items-start gap-3 cursor-pointer group">
                  <input
                    type="checkbox"
                    className="mt-1 w-5 h-5 rounded border-2 border-amber-400 text-red-600 focus:ring-red-500 focus:ring-offset-0"
                    checked={allergenAcknowledged}
                    onChange={(e) => setAllergenAcknowledged(e.target.checked)}
                    required
                  />
                  <span className="text-gray-700 text-sm group-hover:text-gray-900">
                    <strong>I acknowledge</strong> that I have read the allergen information and
                    cross-contamination warning above. <span className="text-red-500">*</span>
                  </span>
                </label>

                <label className="flex items-start gap-3 cursor-pointer group">
                  <input
                    type="checkbox"
                    className="mt-1 w-5 h-5 rounded border-2 border-amber-400 text-red-600 focus:ring-red-500 focus:ring-offset-0"
                    checked={riskAccepted}
                    onChange={(e) => setRiskAccepted(e.target.checked)}
                    required
                  />
                  <span className="text-gray-700 text-sm group-hover:text-gray-900">
                    I understand that My Hibachi cannot guarantee a 100% allergen-free environment and{' '}
                    <strong>I accept this risk</strong>. <span className="text-red-500">*</span>
                  </span>
                </label>

                <label className="flex items-start gap-3 cursor-pointer group">
                  <input
                    type="checkbox"
                    className="mt-1 w-5 h-5 rounded border-2 border-amber-400 text-red-600 focus:ring-red-500 focus:ring-offset-0"
                    checked={willCommunicate}
                    onChange={(e) => setWillCommunicate(e.target.checked)}
                    required
                  />
                  <span className="text-gray-700 text-sm group-hover:text-gray-900">
                    <strong>I will communicate ALL food allergies</strong> and dietary restrictions to
                    My Hibachi staff before my event. <span className="text-red-500">*</span>
                  </span>
                </label>
              </div>

              <a
                href="/allergens"
                target="_blank"
                className="inline-flex items-center gap-1 mt-4 text-sm text-red-600 hover:text-red-700 hover:underline"
              >
                <Info className="w-4 h-4" />
                View Full Allergen List & Safety Guide →
              </a>
            </div>

            {/* Liability Waiver */}
            <div>
              <h6 className="font-bold text-gray-800 mb-2 flex items-center gap-2">
                <span className="w-6 h-6 bg-red-100 text-red-600 rounded-full flex items-center justify-center text-sm font-bold">4</span>
                Liability Waiver
              </h6>
              <p className="text-gray-600 text-sm ml-8 mb-2">
                By confirming this booking, I release My Hibachi LLC from liability for allergic
                reactions resulting from:
              </p>
              <ul className="space-y-1 text-gray-600 text-sm ml-8">
                <li className="flex items-start gap-2">
                  <span className="text-gray-400 mt-0.5">•</span>
                  Failure to communicate allergies in advance
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-gray-400 mt-0.5">•</span>
                  Cross-contamination despite reasonable precautions taken by staff
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-gray-400 mt-0.5">•</span>
                  Consumption of menu items known to contain allergens
                </li>
              </ul>
            </div>

            {/* Client Responsibilities */}
            <div>
              <h6 className="font-bold text-gray-800 mb-2 flex items-center gap-2">
                <span className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-bold">5</span>
                Client Responsibilities
              </h6>
              <ul className="space-y-1 text-gray-600 text-sm ml-8">
                <li className="flex items-start gap-2">
                  <span className="text-blue-500 mt-0.5">•</span>
                  Provide adequate outdoor space with access to power outlet
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-500 mt-0.5">•</span>
                  Ensure safe and clean cooking environment
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-500 mt-0.5">•</span>
                  Communicate all food allergies and dietary restrictions in advance
                </li>
              </ul>
            </div>

            {/* Final Agreement Notice */}
            <div className="bg-red-50 border border-red-200 rounded-xl p-4">
              <p className="text-red-800 font-semibold text-sm text-center">
                By confirming this booking, you agree to these terms and conditions.
              </p>
            </div>
          </div>

          {/* Footer */}
          <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex-shrink-0 flex flex-col sm:flex-row gap-3">
            <button
              type="button"
              className="flex-1 flex items-center justify-center gap-2 px-6 py-3 border-2 border-gray-300 text-gray-700 font-semibold rounded-xl hover:bg-gray-100 transition-all duration-200"
              onClick={onCancel}
            >
              <X className="w-5 h-5" />
              Cancel
            </button>
            <button
              type="button"
              className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-green-600 to-green-700 text-white font-semibold rounded-xl hover:from-green-700 hover:to-green-800 transition-all duration-200 shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed disabled:from-gray-400 disabled:to-gray-500"
              onClick={onConfirm}
              disabled={isSubmitting || !allAcknowledged}
              title={!allAcknowledged ? 'Please check all allergen acknowledgment boxes to continue' : ''}
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
  );
}
