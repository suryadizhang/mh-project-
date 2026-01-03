'use client';

import './datepicker.css';

import { BookingSubmitResponseSchema } from '@myhibachi/types/schemas';
import { format } from 'date-fns';
import {
  CheckCircle2,
  Clock,
  MapPin,
  User,
  Users,
  DollarSign,
  Flame,
  ChevronDown,
} from 'lucide-react';
import Link from 'next/link';
import React, { useEffect, useState, useMemo, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import type { z } from 'zod';

import {
  PersonalInfoSection,
  VenueAddressSection,
  EventDetailsSection,
  DateTimeSection,
  TipCalculator,
  type BookingFormData,
  type CostBreakdown,
  type TravelFeeResult,
  DEFAULT_BOOKING_FORM_VALUES,
} from '@/components/booking/modules';
import BookingAgreementModal from '@/components/booking/BookingAgreementModal';
import { useProtectedPhone } from '@/components/ui/ProtectedPhone';
import { apiFetch } from '@/lib/api';
import { logger } from '@/lib/logger';
import { usePricing } from '@/hooks/usePricing';

// Infer types from schemas for type-safe responses
type BookingSubmitResponse = z.infer<typeof BookingSubmitResponseSchema>;

/**
 * BookingPage - Refactored with modular components
 *
 * Form Order (Smart Scheduling Optimized):
 * 1. Personal Info - Name, email, phone, SMS consent
 * 2. Venue Address - Google Places, geocoding, travel fee preview
 * 3. Event Details - Guest counts, upgrades, live cost calculator
 * 4. Date & Time - Date picker, time slots (LAST - for travel-aware availability)
 * 5. Tip Calculator - Gratuity selection before booking submission
 * 6. Submit - Review and confirm booking
 *
 * NOTE: Billing is handled by Stripe at payment time, not collected here.
 */
export default function BookingPage() {
  // Anti-scraper protected contact info
  const { formatted: protectedPhone, tel: protectedTel } = useProtectedPhone();

  // Get dynamic pricing - NO FALLBACKS: API is single source of truth
  const {
    adultPrice,
    childPrice,
    partyMinimum,
    depositAmount,
    freeMiles,
    perMileRate,
    isLoading: pricingLoading,
    error: pricingError,
  } = usePricing();

  // Form state
  const [showAgreementModal, setShowAgreementModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [bookingConfirmation, setBookingConfirmation] = useState<string | null>(null);

  // Agreement acknowledgment states (for BookingAgreementModal)
  const [allergenAcknowledged, setAllergenAcknowledged] = useState(false);
  const [riskAccepted, setRiskAccepted] = useState(false);
  const [willCommunicate, setWillCommunicate] = useState(false);

  // Note: useAgreements hook available for slot-hold flow in future phases
  // For MVP, signature is included directly in booking payload

  // Cost tracking state
  const [costBreakdown, setCostBreakdown] = useState<CostBreakdown | null>(null);
  const [travelFeeResult, setTravelFeeResult] = useState<TravelFeeResult | null>(null);
  const [tipAmount, setTipAmount] = useState(0);

  // React Hook Form setup
  const {
    register,
    handleSubmit,
    control,
    watch,
    setValue,
    formState: { errors },
    trigger,
  } = useForm<BookingFormData>({
    defaultValues: DEFAULT_BOOKING_FORM_VALUES as BookingFormData,
  });

  // Watch all form values for progress tracking
  const watchAll = watch();

  // Pre-fill form from quote calculator sessionStorage data
  useEffect(() => {
    try {
      const storedData = sessionStorage.getItem('quoteBookingData');
      if (storedData) {
        const quoteData = JSON.parse(storedData);

        // Pre-fill form fields from quote calculator
        if (quoteData.name) {
          const nameParts = quoteData.name.split(' ');
          setValue('firstName', nameParts[0] || '');
          setValue('lastName', nameParts.slice(1).join(' ') || '');
        }
        if (quoteData.phone) setValue('phone', quoteData.phone);
        if (quoteData.email) setValue('email', quoteData.email);
        if (quoteData.guestCount) setValue('adultCount', quoteData.guestCount);
        if (quoteData.venueAddress) setValue('venueStreet', quoteData.venueAddress);
        if (quoteData.venueCity) setValue('venueCity', quoteData.venueCity);
        if (quoteData.venueZipcode) setValue('venueZipcode', quoteData.venueZipcode);

        // Pre-fill date and time if available
        if (quoteData.eventDate) {
          const eventDate = new Date(quoteData.eventDate);
          setValue('eventDate', eventDate);
        }
        if (quoteData.eventTime) {
          setValue('timeSlot', quoteData.eventTime);
        }

        // Clear the sessionStorage after reading (one-time use)
        sessionStorage.removeItem('quoteBookingData');
        logger.info('Pre-filled booking form from quote calculator');
      }
    } catch (error) {
      logger.warn('Could not read quote data from sessionStorage', { error });
    }
  }, [setValue]);

  // Calculate section completion
  const sectionCompletion = useMemo(() => {
    const personalComplete = Boolean(
      watchAll.firstName &&
        watchAll.lastName &&
        watchAll.email &&
        watchAll.phone &&
        watchAll.preferredCommunication,
    );

    const venueComplete = Boolean(
      watchAll.venueStreet && watchAll.venueCity && watchAll.venueState && watchAll.venueZipcode,
    );

    const eventComplete = Boolean((watchAll.adultCount ?? 0) >= 1);

    const dateTimeComplete = Boolean(watchAll.eventDate && watchAll.timeSlot);

    return {
      personal: personalComplete,
      venue: venueComplete,
      event: eventComplete,
      dateTime: dateTimeComplete,
      completedCount: [personalComplete, venueComplete, eventComplete, dateTimeComplete].filter(
        Boolean,
      ).length,
      totalSections: 4,
    };
  }, [
    watchAll.firstName,
    watchAll.lastName,
    watchAll.email,
    watchAll.phone,
    watchAll.preferredCommunication,
    watchAll.venueStreet,
    watchAll.venueCity,
    watchAll.venueState,
    watchAll.venueZipcode,
    watchAll.adultCount,
    watchAll.eventDate,
    watchAll.timeSlot,
  ]);

  // Calculate total cost
  const totalCost = useMemo(() => {
    const foodCost = costBreakdown?.subtotal || 0;
    const travelFee = travelFeeResult?.travelFee || 0;
    const subtotal = foodCost + travelFee;
    return {
      foodCost,
      travelFee,
      subtotal,
      tip: tipAmount,
      total: subtotal + tipAmount,
      deposit: depositAmount ?? 0, // No fallback - API is source of truth
    };
  }, [costBreakdown, travelFeeResult, tipAmount, depositAmount]);

  // Handle cost breakdown changes from EventDetailsSection
  const handleCostBreakdownChange = useCallback((breakdown: CostBreakdown) => {
    setCostBreakdown(breakdown);
  }, []);

  // Handle travel fee changes from VenueAddressSection
  const handleTravelFeeChange = useCallback((result: TravelFeeResult) => {
    setTravelFeeResult(result);
  }, []);

  // Handle tip changes from TipCalculator
  const handleTipChange = useCallback((amount: number) => {
    setTipAmount(amount);
  }, []);

  // NOTE: Calendar URL generation moved to email_service.py for email confirmation
  // This keeps the booking page simpler and calendar links in a more convenient location (email/SMS)

  // Form submission handler
  const onSubmit = async (data: BookingFormData) => {
    setSubmitError(null);

    // Show agreement modal first
    setShowAgreementModal(true);
  };

  // Handle agreement confirmation with actual booking submission
  const handleAgreementConfirm = async (signatureBase64: string) => {
    const data = watch();
    setIsSubmitting(true);
    setSubmitError(null);

    try {
      // Convert timeSlot to HH:MM format
      const timeMap: Record<string, string> = {
        '12PM': '12:00',
        '3PM': '15:00',
        '6PM': '18:00',
        '9PM': '21:00',
      };

      // Build full venue address string
      const fullAddress = [data.venueStreet, data.venueCity, data.venueState, data.venueZipcode]
        .filter(Boolean)
        .join(', ');

      // Calculate total guests
      const totalGuests = (data.adultCount || 0) + (data.childCount || 0);

      // Format data according to PublicBookingCreate schema
      const bookingData = {
        date: data.eventDate ? format(data.eventDate, 'yyyy-MM-dd') : '',
        time: data.timeSlot ? timeMap[data.timeSlot] || '18:00' : '18:00',
        guests: totalGuests,
        location_address: fullAddress,
        customer_name: `${data.firstName} ${data.lastName}`.trim(),
        customer_email: data.email,
        customer_phone: data.phone,
        special_requests: data.specialDietaryRequests || '',
        // Extended booking data
        adult_count: data.adultCount,
        child_count: data.childCount,
        venue_type: data.venueType,
        preferred_communication: data.preferredCommunication,
        sms_consent: data.smsConsent,
        venue_coordinates: data.venueCoordinates,
        upgrades: data.upgrades,
        tip_percentage: data.tipPercentage,
        tip_amount: tipAmount,
        total_amount: totalCost.total,
        deposit_amount: totalCost.deposit,
        travel_fee: totalCost.travelFee,
        // Include signature data for agreement
        signature_image_base64: signatureBase64,
        allergen_acknowledged: allergenAcknowledged,
        risk_accepted: riskAccepted,
        will_communicate: willCommunicate,
      };

      const response = await apiFetch<BookingSubmitResponse>('/api/v1/public/bookings', {
        method: 'POST',
        body: JSON.stringify(bookingData),
      });

      const responseData = response.data as
        | { id?: string; status?: string; message?: string }
        | undefined;

      if (response.success && responseData?.id) {
        // Signature and acknowledgments are included in bookingData above
        // The backend will store them with the booking (no separate agreement API call needed for MVP)
        setShowAgreementModal(false);
        setBookingConfirmation(responseData.id);
        setSubmitSuccess(true);
        logger.info('Booking created successfully with signature', { bookingId: responseData.id });
      } else {
        setSubmitError(response.error || 'Booking failed. Please try again.');
        logger.error('Booking submission failed', new Error(response.error || 'Unknown error'));
      }
    } catch (error) {
      setSubmitError('Network error. Please check your connection and try again.');
      logger.error('Booking submission error', error as Error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAgreementCancel = () => {
    setShowAgreementModal(false);
  };

  // Success state
  if (submitSuccess && bookingConfirmation) {
    return (
      <>
        {/* Hero Section */}
        <section className="page-hero-background py-10 text-center text-white">
          <div className="mx-auto max-w-4xl px-4">
            <div className="mb-3 text-4xl">🎉</div>
            <h1 className="mb-3 text-3xl font-bold">Booking Confirmed!</h1>
            <p className="mb-4 text-base text-gray-200">
              Your hibachi experience is being prepared
            </p>
          </div>
        </section>

        <div className="section-background py-8">
          <div className="mx-auto max-w-2xl px-4">
            <div className="overflow-hidden rounded-xl bg-white p-8 text-center shadow-xl">
              <CheckCircle2 className="mx-auto mb-4 h-16 w-16 text-green-500" />
              <h2 className="mb-2 text-2xl font-bold text-gray-900">Thank You!</h2>
              <p className="mb-6 text-gray-600">Your booking has been submitted successfully.</p>

              <div className="mb-6 rounded-lg border border-green-200 bg-green-50 p-4">
                <p className="mb-1 text-sm text-gray-600">Confirmation Code</p>
                <p className="font-mono text-2xl font-bold text-green-700">{bookingConfirmation}</p>
              </div>

              <div className="mb-8 space-y-4 rounded-lg bg-gray-50 p-4 text-left">
                <h3 className="font-semibold text-gray-900">What's Next?</h3>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li className="flex items-center gap-2">
                    <span className="text-green-500">✓</span>
                    You'll receive a confirmation email shortly
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-green-500">✓</span>A team member will contact you to
                    finalize details
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-green-500">✓</span>
                    Your chef will arrive 30 minutes before your event
                  </li>
                </ul>
              </div>

              <div className="flex flex-col justify-center gap-3 sm:flex-row">
                {/* Calendar link moved to email/SMS confirmation for user convenience */}
                <Link
                  href="/"
                  className="inline-flex items-center justify-center rounded-lg bg-red-600 px-6 py-3 font-semibold text-white transition-colors hover:bg-red-700"
                >
                  Return Home
                </Link>
                <a
                  href={`tel:${protectedTel}`}
                  className="inline-flex items-center justify-center rounded-lg border-2 border-gray-300 px-6 py-3 font-semibold text-gray-700 transition-colors hover:bg-gray-50"
                >
                  Call Us: {protectedPhone}
                </a>
              </div>

              {/* Calendar note */}
              <p className="mt-4 text-center text-sm text-gray-500">
                📅 A calendar invite link will be included in your confirmation email
              </p>
            </div>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      {/* Agreement Modal with Digital Signature */}
      <BookingAgreementModal
        isOpen={showAgreementModal}
        onConfirm={handleAgreementConfirm}
        onCancel={handleAgreementCancel}
        isSubmitting={isSubmitting}
        allergenAcknowledged={allergenAcknowledged}
        setAllergenAcknowledged={setAllergenAcknowledged}
        riskAccepted={riskAccepted}
        setRiskAccepted={setRiskAccepted}
        willCommunicate={willCommunicate}
        setWillCommunicate={setWillCommunicate}
      />

      {/* Hero Section */}
      <section className="page-hero-background py-10 text-center text-white">
        <div className="mx-auto max-w-4xl px-4">
          <div className="mb-3 text-4xl">🍽️</div>
          <h1 className="mb-3 text-3xl font-bold">Book Your Hibachi Experience</h1>
          <p className="mb-4 text-base text-gray-200">
            Premium Japanese hibachi dining at your location
          </p>
          <div className="mb-6 text-sm">
            <span className="rounded-full bg-red-600 px-3 py-1.5 text-white">
              Professional Catering Service
            </span>
          </div>
        </div>
      </section>

      {/* Booking Form Section */}
      <div className="section-background py-8">
        <div className="mx-auto max-w-4xl px-4">
          <div className="overflow-hidden rounded-xl bg-white shadow-xl">
            {/* Progress Indicator */}
            <ProgressIndicator completion={sectionCompletion} />

            {/* Form */}
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 p-5">
              {/* Section 1: Personal Information */}
              <PersonalInfoSection
                control={control}
                watch={watch}
                errors={errors}
                register={register}
                setValue={setValue}
              />

              {/* Section 2: Venue Address */}
              <VenueAddressSection
                control={control}
                register={register}
                watch={watch}
                errors={errors}
                setValue={setValue}
                onTravelFeeChange={handleTravelFeeChange}
                freeMiles={freeMiles}
                perMileRate={perMileRate}
              />

              {/* Section 3: Event Details + Cost Calculator */}
              <EventDetailsSection
                control={control}
                watch={watch}
                errors={errors}
                setValue={setValue}
                adultPrice={adultPrice ?? 0}
                childPrice={childPrice ?? 0}
                travelFee={travelFeeResult?.travelFee || 0}
                partyMinimum={partyMinimum ?? 0}
                depositAmount={depositAmount ?? 0}
                onCostBreakdownChange={handleCostBreakdownChange}
                isLoading={pricingLoading}
              />

              {/* Section 4: Date & Time (LAST - for smart scheduling) */}
              <DateTimeSection
                control={control}
                watch={watch}
                errors={errors}
                venueCoordinates={watchAll.venueCoordinates}
              />

              {/* Section 5: Order Summary & Gratuity (Collapsible) */}
              <PricingSummarySection
                totalCost={totalCost}
                control={control}
                watch={watch}
                onTipChange={handleTipChange}
              />

              {/* Submit Error with Actionable Guidance */}
              {submitError && (
                <div className="rounded-lg border border-red-200 bg-red-50 p-4">
                  <div className="flex items-start gap-3">
                    <span className="flex-shrink-0 text-xl text-red-500">⚠️</span>
                    <div className="flex-1">
                      <p className="font-medium text-red-700">{submitError}</p>
                      {/* Actionable help based on error type */}
                      {submitError.toLowerCase().includes('time slot') && (
                        <p className="mt-2 text-sm text-red-600">
                          💡 Tip: Try selecting a different time slot above, or choose another date.
                        </p>
                      )}
                      {submitError.toLowerCase().includes('48 hours') && (
                        <p className="mt-2 text-sm text-red-600">
                          💡 Tip: Please select a date at least 2 days from now. We need time to
                          prepare your experience!
                        </p>
                      )}
                      {submitError.toLowerCase().includes('network') && (
                        <p className="mt-2 text-sm text-red-600">
                          💡 Tip: Check your internet connection and try again. If the problem
                          persists, call us.
                        </p>
                      )}
                      {(submitError.toLowerCase().includes('database') ||
                        submitError.toLowerCase().includes('server')) && (
                        <p className="mt-2 text-sm text-red-600">
                          💡 Tip: Our system is temporarily busy. Please wait a moment and try
                          again.
                        </p>
                      )}
                      <p className="mt-3 text-sm text-gray-600">
                        Need help? Call us at{' '}
                        <a
                          href={`tel:${protectedTel}`}
                          className="font-semibold text-red-600 hover:underline"
                        >
                          {protectedPhone}
                        </a>
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Submit Button */}
              <div className="pt-4 text-center">
                <button
                  type="submit"
                  disabled={sectionCompletion.completedCount < 4 || isSubmitting}
                  className={`inline-flex items-center gap-3 rounded-full px-8 py-4 text-lg font-bold transition-all duration-300 ${
                    sectionCompletion.completedCount === 4 && !isSubmitting
                      ? 'cursor-pointer bg-gradient-to-r from-red-600 to-red-500 text-white hover:scale-105 hover:shadow-2xl'
                      : 'cursor-not-allowed bg-gray-300 text-gray-500'
                  }`}
                  style={{
                    boxShadow:
                      sectionCompletion.completedCount === 4 && !isSubmitting
                        ? '0 8px 25px rgba(239, 68, 68, 0.4)'
                        : 'none',
                  }}
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
                      Processing...
                    </>
                  ) : sectionCompletion.completedCount === 4 ? (
                    <>
                      <Flame className="h-6 w-6" />
                      Book Your Hibachi Experience
                    </>
                  ) : (
                    <>📝 Complete Form to Continue ({sectionCompletion.completedCount}/4)</>
                  )}
                </button>

                {/* Section Status Summary */}
                <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
                  <StatusBadge
                    label="Personal Info"
                    icon={<User className="h-3 w-3" />}
                    complete={sectionCompletion.personal}
                  />
                  <StatusBadge
                    label="Venue"
                    icon={<MapPin className="h-3 w-3" />}
                    complete={sectionCompletion.venue}
                  />
                  <StatusBadge
                    label="Event Details"
                    icon={<Users className="h-3 w-3" />}
                    complete={sectionCompletion.event}
                  />
                  <StatusBadge
                    label="Date & Time"
                    icon={<Clock className="h-3 w-3" />}
                    complete={sectionCompletion.dateTime}
                  />
                </div>
              </div>
            </form>
          </div>
        </div>
      </div>
    </>
  );
}

/**
 * Progress Indicator Component
 */
function ProgressIndicator({
  completion,
}: {
  completion: {
    personal: boolean;
    venue: boolean;
    event: boolean;
    dateTime: boolean;
    completedCount: number;
    totalSections: number;
  };
}) {
  const progressPercent = (completion.completedCount / completion.totalSections) * 100;

  return (
    <div className="border-b border-gray-200 bg-gradient-to-r from-blue-50 to-red-50 p-4">
      <h3 className="mb-3 text-center text-base font-semibold text-gray-900">
        📋 Booking Progress
      </h3>
      <div className="mb-4 grid grid-cols-4 gap-2 text-center">
        <ProgressStep emoji="👤" label="Info" complete={completion.personal} />
        <ProgressStep emoji="🎪" label="Venue" complete={completion.venue} />
        <ProgressStep emoji="👥" label="Event" complete={completion.event} />
        <ProgressStep emoji="📅" label="Time" complete={completion.dateTime} />
      </div>
      <div className="mt-2">
        <div className="mb-1 flex justify-between text-xs text-gray-600">
          <span>Completion</span>
          <span>{Math.round(progressPercent)}%</span>
        </div>
        <div className="h-2 w-full rounded-full bg-gray-200">
          <div
            className="h-2 rounded-full bg-gradient-to-r from-blue-500 to-red-500 transition-all duration-300"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>
    </div>
  );
}

function ProgressStep({
  emoji,
  label,
  complete,
}: {
  emoji: string;
  label: string;
  complete: boolean;
}) {
  return (
    <div className="space-y-1">
      <div
        className={`mx-auto flex h-9 w-9 items-center justify-center rounded-full text-base font-bold ${
          complete ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-500'
        }`}
      >
        {emoji}
      </div>
      <div className="text-xs font-medium">{label}</div>
    </div>
  );
}

/**
 * Status Badge Component
 */
function StatusBadge({
  label,
  icon,
  complete,
}: {
  label: string;
  icon: React.ReactNode;
  complete: boolean;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded px-2 py-1 text-xs ${
        complete ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-500'
      }`}
    >
      {icon}
      {label}
    </span>
  );
}

/**
 * Pricing Summary Section - Collapsible dropdown with Order Summary + Gratuity
 */
function PricingSummarySection({
  totalCost,
  control,
  watch,
  onTipChange,
}: {
  totalCost: {
    foodCost: number;
    travelFee: number;
    subtotal: number;
    tip: number;
    total: number;
    deposit: number;
  };
  control: ReturnType<typeof useForm<BookingFormData>>['control'];
  watch: ReturnType<typeof useForm<BookingFormData>>['watch'];
  onTipChange: (tip: number) => void;
}) {
  const [isExpanded, setIsExpanded] = useState(false); // Collapsed by default - user expands if needed

  return (
    <div className="overflow-hidden rounded-xl border-2 border-green-200 bg-gradient-to-r from-green-50 to-emerald-50">
      {/* Collapsible Header Button */}
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex w-full items-center justify-between p-4 transition-colors hover:bg-green-100/50"
        aria-expanded={isExpanded}
        aria-controls="pricing-summary-content"
      >
        <div className="flex items-center gap-2">
          <DollarSign className="h-5 w-5 text-green-600" />
          <span className="text-lg font-bold text-gray-900">Pricing & Gratuity</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-lg font-bold text-green-700">${totalCost.total.toFixed(2)}</span>
          <ChevronDown
            className={`h-5 w-5 text-gray-500 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
          />
        </div>
      </button>

      {/* Collapsible Content */}
      <div
        id="pricing-summary-content"
        className={`transition-all duration-200 ease-in-out ${isExpanded ? 'max-h-[800px] opacity-100' : 'max-h-0 overflow-hidden opacity-0'}`}
      >
        <div className="space-y-4 px-4 pb-4">
          {/* Order Summary */}
          <OrderSummary totalCost={totalCost} />

          {/* Gratuity Section */}
          <TipCalculator
            control={control}
            watch={watch}
            subtotal={totalCost.subtotal}
            onTipChange={onTipChange}
          />
        </div>
      </div>
    </div>
  );
}

/**
 * Order Summary Component (inner content, no outer wrapper)
 */
function OrderSummary({
  totalCost,
}: {
  totalCost: {
    foodCost: number;
    travelFee: number;
    subtotal: number;
    tip: number;
    total: number;
    deposit: number;
  };
}) {
  return (
    <div className="space-y-2 text-sm">
      <h4 className="mb-2 font-semibold text-gray-800">Order Summary</h4>
      <div className="flex justify-between">
        <span className="text-gray-600">Food & Beverages</span>
        <span className="font-medium">${totalCost.foodCost.toFixed(2)}</span>
      </div>
      {totalCost.travelFee > 0 && (
        <div className="flex justify-between">
          <span className="text-gray-600">Travel Fee</span>
          <span className="font-medium">${totalCost.travelFee.toFixed(2)}</span>
        </div>
      )}
      <div className="flex justify-between">
        <span className="text-gray-600">Subtotal</span>
        <span className="font-medium">${totalCost.subtotal.toFixed(2)}</span>
      </div>
      {totalCost.tip > 0 && (
        <div className="flex justify-between text-green-700">
          <span>Gratuity</span>
          <span className="font-medium">+${totalCost.tip.toFixed(2)}</span>
        </div>
      )}
      <div className="mt-2 border-t border-green-300 pt-2">
        <div className="flex justify-between text-lg font-bold">
          <span className="text-gray-900">Total</span>
          <span className="text-green-700">${totalCost.total.toFixed(2)}</span>
        </div>
      </div>
      <div className="mt-2 flex justify-between rounded bg-amber-50 p-2 text-amber-700">
        <span className="font-medium">Due Today (Deposit)</span>
        <span className="font-bold">${totalCost.deposit.toFixed(2)}</span>
      </div>
    </div>
  );
}
