'use client';

import React, { useState } from 'react';
import { FileText, AlertTriangle, Info, X, Check, Pen } from 'lucide-react';
import { usePricing } from '@/hooks/usePricing';
import SignaturePad from './SignaturePad';

interface BookingAgreementModalProps {
  isOpen: boolean;
  onConfirm: (signatureBase64: string) => void;
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
  // Get dynamic values from SSoT pricing system
  const {
    depositAmount,
    depositRefundableDays,
    standardDurationMinutes,
    rescheduleFee,
    freeRescheduleHours,
    guestCountFinalizeHours,
    menuChangeCutoffHours,
  } = usePricing();

  // Signature state for digital signing
  const [signatureBase64, setSignatureBase64] = useState<string | null>(null);
  const [isSignatureValid, setIsSignatureValid] = useState(false);

  if (!isOpen) return null;

  const allAcknowledged =
    allergenAcknowledged && riskAccepted && willCommunicate && isSignatureValid;

  return (
    <div className="animate-in fade-in fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm duration-200">
      <div className="animate-in zoom-in-95 mx-4 max-h-[90vh] w-full max-w-3xl duration-200">
        <div className="flex max-h-[90vh] flex-col overflow-hidden rounded-2xl bg-white shadow-2xl">
          {/* Header */}
          <div className="flex-shrink-0 bg-gradient-to-r from-red-600 to-red-700 px-6 py-4">
            <h5 className="flex items-center gap-2 text-xl font-bold text-white">
              <FileText className="h-6 w-6" />
              Booking Agreement & Terms
            </h5>
          </div>

          {/* Body - Scrollable */}
          <div className="flex-grow space-y-6 overflow-y-auto p-6">
            {/* Service Agreement */}
            <div>
              <h6 className="mb-2 flex items-center gap-2 font-bold text-gray-800">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-red-100 text-sm font-bold text-red-600">
                  1
                </span>
                Service Agreement
              </h6>
              <ul className="ml-8 space-y-1 text-sm text-gray-600">
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-green-500">✓</span>
                  Professional hibachi chef service with entertainment and cooking
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-green-500">✓</span>
                  Fresh, high-quality ingredients prepared on-site
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-green-500">✓</span>
                  All necessary cooking equipment and utensils provided
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-green-500">✓</span>
                  Approximately {standardDurationMinutes ?? 90}-minute service duration (additional
                  time available upon request)
                </li>
              </ul>
            </div>

            {/* Pricing & Payment */}
            <div>
              <h6 className="mb-2 flex items-center gap-2 font-bold text-gray-800">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-green-100 text-sm font-bold text-green-600">
                  2
                </span>
                Pricing & Payment
              </h6>
              <ul className="ml-8 space-y-1 text-sm text-gray-600">
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-green-500">✓</span>
                  Final pricing confirmed based on guest count and menu selection
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-green-500">✓</span>${depositAmount ?? 100} deposit
                  required to secure booking
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-green-500">✓</span>
                  <strong>{depositRefundableDays ?? 4}+ day full refund guarantee</strong> - cancel{' '}
                  {depositRefundableDays ?? 4}+ days before event for full deposit refund
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-green-500">✓</span>
                  Remaining balance due on event day (cash, Venmo, Zelle, or credit card)
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-green-500">✓</span>
                  Travel fees may apply for locations outside our standard service area
                </li>
              </ul>
            </div>

            {/* Cancellation & Changes Policy */}
            <div>
              <h6 className="mb-2 flex items-center gap-2 font-bold text-gray-800">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-amber-100 text-sm font-bold text-amber-600">
                  3
                </span>
                Cancellation & Changes Policy
              </h6>
              <ul className="ml-8 space-y-2 text-sm text-gray-600">
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 font-bold text-green-500">•</span>
                  <span>
                    <strong>{depositRefundableDays ?? 4}+ Day Full Refund:</strong> Cancel{' '}
                    {depositRefundableDays ?? 4}+ days before event for full deposit refund, no
                    questions asked
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 font-bold text-green-500">•</span>
                  <span>
                    <strong>Free Rescheduling:</strong> Reschedule free of charge with{' '}
                    {freeRescheduleHours ?? 24}+ hours notice; ${rescheduleFee ?? 200} rescheduling
                    fee applies with less than {freeRescheduleHours ?? 24} hours notice
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 font-bold text-amber-500">•</span>
                  <span>
                    <strong>Guest Count Changes:</strong> Final guest count required{' '}
                    {guestCountFinalizeHours ?? 24}+ hours before event (we prepare fresh
                    ingredients specifically for your party size)
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 font-bold text-amber-500">•</span>
                  <span>
                    <strong>Menu Changes:</strong> No menu changes allowed within{' '}
                    {menuChangeCutoffHours ?? 12} hours of event
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 font-bold text-red-500">•</span>
                  <span>
                    <strong>Food Safety:</strong> No refund for ordered food as we cannot keep food
                    that has been out of refrigeration for more than 4 hours (per FDA guidelines)
                  </span>
                </li>
              </ul>
            </div>

            {/* Allergen Warning Section */}
            <div className="rounded-xl border-2 border-amber-400 bg-amber-50 p-5">
              <h6 className="mb-3 flex items-center gap-2 font-bold text-red-600">
                <AlertTriangle className="h-5 w-5" />
                ALLERGEN DISCLOSURE & ACKNOWLEDGMENT
              </h6>

              <p className="mb-2 font-semibold text-gray-800">IMPORTANT - Please Read Carefully:</p>

              <p className="mb-2 font-medium text-gray-700">
                Our kitchen uses and tracks these allergens:
              </p>
              <ul className="mb-4 space-y-2 text-sm text-gray-600">
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 font-bold text-amber-600">⚠</span>
                  <span>
                    <strong>Major Allergens (FDA):</strong> Shellfish (shrimp, lobster, scallops),
                    Fish (salmon), Gluten (gyoza, noodles, teriyaki sauce), Soy (sauces, tofu), Eggs
                    (fried rice)
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 font-bold text-amber-600">⚠</span>
                  <span>
                    <strong>Additional Allergens:</strong> Celery (salad dressing), Corn (corn
                    starch in teriyaki sauce), Sulfites (in sake)
                  </span>
                </li>
              </ul>

              <div className="mt-4 border-t border-amber-300 pt-4">
                <p className="mb-2 font-semibold text-red-600">⚠️ CROSS-CONTAMINATION RISK:</p>
                <p className="mb-4 text-gray-700">
                  We use <strong>shared cooking surfaces, utensils, and oils</strong>. While we take
                  precautions to accommodate dietary restrictions, we{' '}
                  <strong className="text-red-600">CANNOT GUARANTEE</strong> a 100% allergen-free
                  environment for customers with severe allergies.
                </p>
              </div>

              {/* Required Allergen Checkboxes */}
              <div className="mt-4 space-y-3">
                <label className="group flex cursor-pointer items-start gap-3">
                  <input
                    type="checkbox"
                    className="mt-1 h-5 w-5 rounded border-2 border-amber-400 text-red-600 focus:ring-red-500 focus:ring-offset-0"
                    checked={allergenAcknowledged}
                    onChange={(e) => setAllergenAcknowledged(e.target.checked)}
                    required
                  />
                  <span className="text-sm text-gray-700 group-hover:text-gray-900">
                    <strong>I acknowledge</strong> that I have read the allergen information and
                    cross-contamination warning above. <span className="text-red-500">*</span>
                  </span>
                </label>

                <label className="group flex cursor-pointer items-start gap-3">
                  <input
                    type="checkbox"
                    className="mt-1 h-5 w-5 rounded border-2 border-amber-400 text-red-600 focus:ring-red-500 focus:ring-offset-0"
                    checked={riskAccepted}
                    onChange={(e) => setRiskAccepted(e.target.checked)}
                    required
                  />
                  <span className="text-sm text-gray-700 group-hover:text-gray-900">
                    I understand that My Hibachi cannot guarantee a 100% allergen-free environment
                    and <strong>I accept this risk</strong>. <span className="text-red-500">*</span>
                  </span>
                </label>

                <label className="group flex cursor-pointer items-start gap-3">
                  <input
                    type="checkbox"
                    className="mt-1 h-5 w-5 rounded border-2 border-amber-400 text-red-600 focus:ring-red-500 focus:ring-offset-0"
                    checked={willCommunicate}
                    onChange={(e) => setWillCommunicate(e.target.checked)}
                    required
                  />
                  <span className="text-sm text-gray-700 group-hover:text-gray-900">
                    <strong>I will communicate ALL food allergies</strong> and dietary restrictions
                    to My Hibachi staff before my event. <span className="text-red-500">*</span>
                  </span>
                </label>
              </div>

              <a
                href="/allergens"
                target="_blank"
                className="mt-4 inline-flex items-center gap-1 text-sm text-red-600 hover:text-red-700 hover:underline"
              >
                <Info className="h-4 w-4" />
                View Full Allergen List & Safety Guide →
              </a>
            </div>

            {/* Liability Waiver */}
            <div>
              <h6 className="mb-2 flex items-center gap-2 font-bold text-gray-800">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-red-100 text-sm font-bold text-red-600">
                  4
                </span>
                Liability Waiver & Release
              </h6>
              <p className="mb-2 ml-8 text-sm text-gray-600">
                By signing below, I (the &quot;Client&quot;) agree to release My Hibachi LLC, its
                owners, employees, and contractors from all liability for:
              </p>
              <ul className="ml-8 space-y-1 text-sm text-gray-600">
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-gray-400">•</span>
                  <strong>Allergic Reactions:</strong> Reactions resulting from failure to
                  communicate allergies in advance, cross-contamination despite reasonable
                  precautions, or consumption of items known to contain allergens
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-gray-400">•</span>
                  <strong>Property Damage:</strong> Any damage to property, furniture, surfaces,
                  flooring, or structures at the Client&apos;s premises arising from cooking
                  activities, heat, smoke, oil splatter, or equipment setup
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-gray-400">•</span>
                  <strong>Personal Injury:</strong> Any injury to guests resulting from proximity to
                  cooking equipment, hot surfaces, or entertainment elements, provided reasonable
                  safety measures were maintained
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-gray-400">•</span>
                  <strong>Third-Party Claims:</strong> Any claims by guests, venue owners, or third
                  parties arising from the event
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-gray-400">•</span>
                  <strong>Pre-Event Health:</strong> Illness claims where guests attended despite
                  experiencing vomiting, diarrhea, or fever within 48 hours prior
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-gray-400">•</span>
                  <strong>Post-Service Food Handling:</strong> Illness from leftovers not
                  refrigerated within 2 hours of service completion
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-gray-400">•</span>
                  <strong>Third-Party Food:</strong> Illness from food, beverages, or ice not
                  prepared by My Hibachi chef
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-gray-400">•</span>
                  <strong>Foodborne Illness Claims:</strong> Claims not reported within 72 hours,
                  lacking medical documentation, or affecting fewer than 3 guests
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-gray-400">•</span>
                  <strong>Norovirus Acknowledgment:</strong> Norovirus spreads person-to-person
                  through direct contact, not through properly cooked food—if multiple guests
                  develop symptoms 12-48 hours post-event, transmission likely occurred at the
                  gathering
                </li>
              </ul>
              <p className="mt-3 ml-8 text-xs text-gray-500 italic">
                This waiver shall be binding upon Client, their heirs, executors, and assigns. This
                agreement shall be governed by the laws of the state where the event takes place.
              </p>

              {/* Digital Signature Section */}
              <div className="mt-6 ml-8">
                <div className="rounded-xl border-2 border-gray-200 bg-gray-50 p-4">
                  <h6 className="mb-3 flex items-center gap-2 font-semibold text-gray-800">
                    <Pen className="h-5 w-5 text-red-600" />
                    Digital Signature <span className="text-red-500">*</span>
                  </h6>
                  <p className="mb-4 text-sm text-gray-600">
                    Please sign below to confirm your agreement to these terms and conditions. Your
                    signature will be captured and stored as part of your booking record.
                  </p>
                  <SignaturePad
                    onSignatureCapture={setSignatureBase64}
                    onValidityChange={setIsSignatureValid}
                    width={400}
                    height={150}
                  />
                  {!isSignatureValid && (
                    <p className="mt-2 flex items-center gap-1 text-sm text-amber-600">
                      <AlertTriangle className="h-4 w-4" />
                      Please sign above to continue
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Client Responsibilities */}
            <div>
              <h6 className="mb-2 flex items-center gap-2 font-bold text-gray-800">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-100 text-sm font-bold text-blue-600">
                  5
                </span>
                Client Responsibilities
              </h6>
              <ul className="ml-8 space-y-1 text-sm text-gray-600">
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-blue-500">•</span>
                  <strong>Weather Protection:</strong> Provide covering for outdoor events (tent,
                  covered patio, garage, or indoor space with proper ventilation). Chef cannot cook
                  in rain without protection.
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-blue-500">•</span>
                  <strong>Setup Space:</strong> Provide adequate outdoor space (minimum 8×6 feet
                  clearance) on level ground with proper ventilation
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-blue-500">•</span>
                  <strong>Tables & Seating:</strong> Provide tables, chairs, plates, utensils, and
                  napkins for guests (2 × 8-foot or 3 × 6-foot tables recommended)
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-blue-500">•</span>
                  <strong>Safe Environment:</strong> Ensure cooking area is clear of flammable
                  materials within 10 feet of grill, with proper ventilation
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-blue-500">•</span>
                  <strong>Guest Allergies:</strong> Communicate ALL guest allergies 48+ hours in
                  advance and confirm verbally with chef upon arrival
                </li>
              </ul>
            </div>

            {/* Final Agreement Notice */}
            <div className="rounded-xl border border-red-200 bg-red-50 p-4">
              <p className="text-center text-sm font-semibold text-red-800">
                By confirming this booking, you agree to these terms and conditions.
              </p>
            </div>
          </div>

          {/* Footer */}
          <div className="flex flex-shrink-0 flex-col gap-3 border-t border-gray-100 bg-gray-50 px-6 py-4 sm:flex-row">
            <button
              type="button"
              className="flex flex-1 items-center justify-center gap-2 rounded-xl border-2 border-gray-300 px-6 py-3 font-semibold text-gray-700 transition-all duration-200 hover:bg-gray-100"
              onClick={onCancel}
            >
              <X className="h-5 w-5" />
              Cancel
            </button>
            <button
              type="button"
              className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-green-600 to-green-700 px-6 py-3 font-semibold text-white shadow-md transition-all duration-200 hover:from-green-700 hover:to-green-800 hover:shadow-lg disabled:cursor-not-allowed disabled:from-gray-400 disabled:to-gray-500 disabled:opacity-50"
              onClick={() => signatureBase64 && onConfirm(signatureBase64)}
              disabled={isSubmitting || !allAcknowledged}
              title={
                !allAcknowledged
                  ? 'Please check all acknowledgment boxes and sign above to continue'
                  : ''
              }
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
  );
}
