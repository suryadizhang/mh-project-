'use client';

import { addDays, format } from 'date-fns';
import {
  AlertCircle,
  CheckCircle,
  MapPin,
  User,
  Phone,
  Users,
  Baby,
  Navigation,
  Calendar,
  Clock,
  ArrowRight,
  Loader2,
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useEffect, useRef, useState, useCallback } from 'react';

import { LazyDatePicker } from '@/components/ui/LazyDatePicker';
import { ProtectedPhone } from '@/components/ui/ProtectedPhone';
import { apiFetch } from '@/lib/api';
import { submitQuoteLead, submitLeadEvent } from '@/lib/leadService';
import { logger } from '@/lib/logger';
import { usePricing } from '@/hooks/usePricing';
import type { GoogleAddressComponent } from '@/types/data';

// Google Maps Autocomplete types
interface GoogleMapsAutocomplete {
  addListener: (event: string, callback: () => void) => void;
  getPlace: () => {
    formatted_address?: string;
    address_components?: Array<{
      long_name: string;
      short_name: string;
      types: string[];
    }>;
  };
}

interface AutocompleteOptions {
  componentRestrictions?: { country: string };
  types?: string[];
  fields?: string[];
}

declare global {
  interface Window {
    google?: {
      maps: {
        places: {
          Autocomplete: new (
            input: HTMLInputElement,
            options?: AutocompleteOptions,
          ) => GoogleMapsAutocomplete;
        };
        event: {
          clearInstanceListeners: (instance: object) => void;
        };
      };
    };
    initAutocomplete?: () => void;
  }
}

interface QuoteData {
  adults: number;
  children: number;
  location: string;
  zipCode: string;
  venueAddress: string;
  name: string;
  phone: string;
  salmon: number;
  scallops: number;
  filetMignon: number;
  lobsterTail: number;
  thirdProteins: number;
  yakisobaNoodles: number;
  extraFriedRice: number;
  extraVegetables: number;
  edamame: number;
  gyoza: number;
}

// Validation errors type
interface ValidationErrors {
  name?: string;
  phone?: string;
  adults?: string;
  venueAddress?: string;
}

interface QuoteResult {
  baseTotal: number;
  upgradeTotal: number;
  grandTotal: number;
  travelFee?: number;
  travelDistance?: number;
  finalTotal?: number;
}

// Time slot from availability API
interface TimeSlot {
  time: string;
  label: string;
  available: number;
  isAvailable: boolean;
}

// Funnel step for progressive reveal
type FunnelStep = 'quote' | 'availability' | 'booking';

// Input component with validation
interface FormInputProps {
  id: string;
  label: string;
  type?: string;
  value: string | number;
  onChange: (value: string | number) => void;
  placeholder?: string;
  required?: boolean;
  error?: string;
  hint?: string;
  icon?: React.ReactNode;
  min?: number;
  max?: number;
  ref?: React.RefObject<HTMLInputElement>;
  autoComplete?: string;
}

const FormInput = ({
  id,
  label,
  type = 'text',
  value,
  onChange,
  placeholder,
  required,
  error,
  hint,
  icon,
  min,
  max,
  autoComplete,
}: FormInputProps) => (
  <div className="flex flex-col space-y-1.5">
    <label htmlFor={id} className="flex items-center gap-2 text-sm font-semibold text-gray-700">
      {icon}
      {label}
      {required && <span className="text-red-500">*</span>}
    </label>
    <input
      id={id}
      type={type}
      value={value}
      onChange={(e) => onChange(type === 'number' ? parseInt(e.target.value) || 0 : e.target.value)}
      placeholder={placeholder}
      min={min}
      max={max}
      autoComplete={autoComplete}
      className={`w-full rounded-lg border-2 px-4 py-3 transition-all duration-200 focus:ring-2 focus:ring-offset-1 focus:outline-none ${
        error
          ? 'border-red-300 bg-red-50 focus:border-red-500 focus:ring-red-200'
          : 'border-gray-200 hover:border-gray-300 focus:border-red-500 focus:ring-red-200'
      }`}
      required={required}
    />
    {error && (
      <p className="animate-in slide-in-from-top-1 flex items-center gap-1 text-sm text-red-600">
        <AlertCircle className="h-4 w-4" />
        {error}
      </p>
    )}
    {hint && !error && <p className="text-xs text-gray-500">{hint}</p>}
  </div>
);

// Number input for upgrades
interface UpgradeInputProps {
  label: string;
  price: string;
  value: number;
  onChange: (value: number) => void;
  hint?: string;
}

const UpgradeInput = ({ label, price, value, onChange, hint }: UpgradeInputProps) => (
  <div className="flex flex-col space-y-1.5">
    <label className="text-sm font-medium text-gray-700">
      {label} <span className="font-semibold text-red-600">({price})</span>
    </label>
    <input
      type="number"
      min="0"
      value={value}
      onChange={(e) => onChange(Math.max(0, parseInt(e.target.value) || 0))}
      className="w-full rounded-lg border-2 border-gray-200 px-4 py-3 transition-all duration-200 hover:border-gray-300 focus:border-red-500 focus:ring-2 focus:ring-red-200 focus:ring-offset-1 focus:outline-none"
    />
    {hint && <p className="text-xs text-gray-500">{hint}</p>}
  </div>
);

export function QuoteCalculator() {
  // Fetch dynamic pricing from database
  const { adultPrice, childPrice, childFreeUnderAge } = usePricing();

  const [quoteData, setQuoteData] = useState<QuoteData>({
    adults: 10,
    children: 0,
    location: '',
    zipCode: '',
    venueAddress: '', // NEW: Full venue address
    name: '',
    phone: '',
    salmon: 0,
    scallops: 0,
    filetMignon: 0,
    lobsterTail: 0,
    thirdProteins: 0,
    yakisobaNoodles: 0,
    extraFriedRice: 0,
    extraVegetables: 0,
    edamame: 0,
    gyoza: 0,
  });

  const [quoteResult, setQuoteResult] = useState<QuoteResult | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);
  const [calculationError, setCalculationError] = useState('');
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  // Progressive reveal state
  const [funnelStep, setFunnelStep] = useState<FunnelStep>('quote');
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [selectedTime, setSelectedTime] = useState<string | null>(null);
  const [timeSlots, setTimeSlots] = useState<TimeSlot[]>([]);
  const [loadingTimeSlots, setLoadingTimeSlots] = useState(false);
  const [leadId, setLeadId] = useState<string | null>(null);

  // Router for navigation
  const router = useRouter();

  // Google Places Autocomplete refs
  const venueAddressInputRef = useRef<HTMLInputElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const autocompleteRef = useRef<any>(null);

  // Real-time validation
  const validateField = useCallback(
    (field: keyof QuoteData, value: string | number): string | undefined => {
      switch (field) {
        case 'name':
          if (!String(value).trim()) return 'Please enter your name';
          if (String(value).trim().length < 2) return 'Name must be at least 2 characters';
          return undefined;
        case 'phone':
          const digitsOnly = String(value).replace(/\D/g, '');
          if (!digitsOnly) return 'Please enter your phone number';
          if (digitsOnly.length < 10) return 'Phone number must have at least 10 digits';
          return undefined;
        case 'adults':
          if (Number(value) < 1) return 'At least 1 adult is required';
          if (Number(value) > 50) return 'Maximum 50 adults per event';
          return undefined;
        case 'venueAddress':
          // Optional but recommended
          return undefined;
        default:
          return undefined;
      }
    },
    [],
  );

  // Mark field as touched and validate
  const handleBlur = useCallback(
    (field: keyof QuoteData) => {
      setTouched((prev) => ({ ...prev, [field]: true }));
      const error = validateField(field, quoteData[field]);
      setValidationErrors((prev) => ({ ...prev, [field]: error }));
    },
    [quoteData, validateField],
  );

  const handleInputChange = (field: keyof QuoteData, value: number | string) => {
    setQuoteData((prev) => ({ ...prev, [field]: value }));
    setQuoteResult(null);
    setCalculationError('');

    // Real-time validation for touched fields
    if (touched[field]) {
      const error = validateField(field, value);
      setValidationErrors((prev) => ({ ...prev, [field]: error }));
    }
  };

  // Initialize Google Places Autocomplete
  useEffect(() => {
    // Load Google Maps script if not already loaded
    if (!window.google) {
      const script = document.createElement('script');
      script.src = `https://maps.googleapis.com/maps/api/js?key=${process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY}&libraries=places`;
      script.async = true;
      script.defer = true;
      script.onload = initializeAutocomplete;
      document.head.appendChild(script);
    } else {
      initializeAutocomplete();
    }

    function initializeAutocomplete() {
      if (!venueAddressInputRef.current || !window.google) return;

      // Initialize autocomplete
      autocompleteRef.current = new window.google.maps.places.Autocomplete(
        venueAddressInputRef.current,
        {
          types: ['address'],
          componentRestrictions: { country: 'us' }, // Restrict to US addresses
          fields: ['formatted_address', 'address_components', 'geometry'],
        },
      );

      // Listen for place selection
      autocompleteRef.current.addListener('place_changed', () => {
        const place = autocompleteRef.current.getPlace();

        if (place.formatted_address) {
          // Update venue address with formatted address from Google
          setQuoteData((prev) => ({
            ...prev,
            venueAddress: place.formatted_address,
          }));

          // Extract city and ZIP from address components
          if (place.address_components) {
            let city = '';
            let zipCode = '';

            place.address_components.forEach((component: GoogleAddressComponent) => {
              if (component.types.includes('locality')) {
                city = component.long_name;
              }
              if (component.types.includes('postal_code')) {
                zipCode = component.short_name;
              }
            });

            // Auto-fill location and zipCode fields
            setQuoteData((prev) => ({
              ...prev,
              location: city || prev.location,
              zipCode: zipCode || prev.zipCode,
            }));
          }
        }
      });
    }

    return () => {
      // Cleanup
      if (autocompleteRef.current) {
        window.google?.maps.event.clearInstanceListeners(autocompleteRef.current);
      }
    };
  }, []);

  // Fetch availability when date is selected
  const fetchAvailability = useCallback(async (date: Date) => {
    setLoadingTimeSlots(true);
    setSelectedTime(null);
    try {
      const dateStr = format(date, 'yyyy-MM-dd');
      // Response shape: { success, data: { timeSlots: [...] } }
      // But API may also return nested data: { success, data: { data: { timeSlots: [...] } } }
      const response = await apiFetch<{
        timeSlots?: TimeSlot[];
        data?: { timeSlots?: TimeSlot[] };
      }>(`/api/v1/bookings/availability?date=${dateStr}`, {
        cacheStrategy: {
          strategy: 'cache-first',
          ttl: 3 * 60 * 1000, // 3 minutes
        },
      });

      if (response.success && response.data) {
        // Handle both possible response shapes
        const slots =
          response.data.timeSlots ||
          (response.data as { data?: { timeSlots?: TimeSlot[] } }).data?.timeSlots ||
          [];
        setTimeSlots(slots);
      } else {
        setTimeSlots([]);
        logger.warn('Could not fetch availability');
      }
    } catch (error) {
      logger.error('Error fetching availability', error as Error);
      setTimeSlots([]);
    } finally {
      setLoadingTimeSlots(false);
    }
  }, []);

  // Fetch availability when date changes
  useEffect(() => {
    if (selectedDate && funnelStep === 'availability') {
      fetchAvailability(selectedDate);

      // Track funnel event when user checks availability
      if (leadId) {
        submitLeadEvent(leadId, 'funnel_checked_availability', {
          selectedDate: format(selectedDate, 'yyyy-MM-dd'),
        });
      }
    }
  }, [selectedDate, funnelStep, fetchAvailability, leadId]);

  // Handle proceeding to booking
  const handleProceedToBooking = () => {
    if (!selectedDate || !selectedTime || !quoteResult) return;

    // Store data in sessionStorage for BookUs page to read
    const bookingData = {
      name: quoteData.name,
      phone: quoteData.phone,
      guestCount: quoteData.adults + quoteData.children,
      adults: quoteData.adults,
      children: quoteData.children,
      venueAddress: quoteData.venueAddress,
      venueCity: quoteData.location,
      venueZipcode: quoteData.zipCode,
      eventDate: format(selectedDate, 'yyyy-MM-dd'),
      eventTime: selectedTime,
      quoteTotal: quoteResult.grandTotal,
      leadId: leadId,
      // Upgrades
      salmon: quoteData.salmon,
      scallops: quoteData.scallops,
      filetMignon: quoteData.filetMignon,
      lobsterTail: quoteData.lobsterTail,
      thirdProteins: quoteData.thirdProteins,
      yakisobaNoodles: quoteData.yakisobaNoodles,
      extraFriedRice: quoteData.extraFriedRice,
      extraVegetables: quoteData.extraVegetables,
      edamame: quoteData.edamame,
      gyoza: quoteData.gyoza,
    };

    // Track funnel event
    if (leadId) {
      submitLeadEvent(leadId, 'funnel_started_booking', {
        eventDate: format(selectedDate, 'yyyy-MM-dd'),
        eventTime: selectedTime,
        quoteTotal: quoteResult.grandTotal,
      });
    }

    sessionStorage.setItem('quoteBookingData', JSON.stringify(bookingData));
    router.push('/BookUs');
  };

  const calculateQuote = async () => {
    setIsCalculating(true);
    setCalculationError('');

    try {
      // Basic validation
      if (quoteData.adults === 0) {
        setCalculationError('Please specify at least 1 adult guest.');
        setIsCalculating(false);
        return;
      }

      if (!quoteData.name.trim()) {
        setCalculationError('Please enter your name.');
        setIsCalculating(false);
        return;
      }

      if (!quoteData.phone.trim()) {
        setCalculationError('Please enter your phone number.');
        setIsCalculating(false);
        return;
      }

      // Validate phone number (basic check for at least 10 digits)
      const digitsOnly = quoteData.phone.replace(/\D/g, '');
      if (digitsOnly.length < 10) {
        setCalculationError('Please enter a valid phone number with at least 10 digits.');
        setIsCalculating(false);
        return;
      }

      // Call backend API to calculate quote with travel fee
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE}/api/v1/public/quote/calculate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          adults: quoteData.adults,
          children: quoteData.children,
          salmon: quoteData.salmon,
          scallops: quoteData.scallops,
          filet_mignon: quoteData.filetMignon,
          lobster_tail: quoteData.lobsterTail,
          third_proteins: quoteData.thirdProteins,
          yakisoba_noodles: quoteData.yakisobaNoodles,
          extra_fried_rice: quoteData.extraFriedRice,
          extra_vegetables: quoteData.extraVegetables,
          edamame: quoteData.edamame,
          gyoza: quoteData.gyoza,
          venue_address: quoteData.venueAddress,
          zip_code: quoteData.zipCode,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to calculate quote');
      }

      const data = await response.json();

      // Set quote result with travel fee information
      const result: QuoteResult = {
        baseTotal: data.base_total,
        upgradeTotal: data.upgrade_total,
        grandTotal: data.grand_total,
        travelFee: data.travel_info?.travel_fee || 0,
        travelDistance: data.travel_info?.distance_miles || undefined,
        finalTotal: data.grand_total, // Already includes travel fee
      };

      setQuoteResult(result);

      // Submit lead data to backend using centralized service and capture leadId
      submitQuoteLead({
        name: quoteData.name,
        phone: quoteData.phone,
        adults: quoteData.adults,
        children: quoteData.children,
        location: quoteData.location,
        zipCode: quoteData.zipCode,
        grandTotal: result.grandTotal,
      })
        .then((leadResult) => {
          if (leadResult.success && leadResult.data?.id) {
            setLeadId(leadResult.data.id);
          }
        })
        .catch((err) => {
          logger.warn('Failed to submit lead data', err as Error);
          // Don't block the quote display if lead submission fails
        });

      // Progress to availability step
      setFunnelStep('availability');
    } catch (error) {
      logger.error('Calculation error', error as Error);
      setCalculationError('Error calculating quote. Please try again.');
    } finally {
      setIsCalculating(false);
    }
  };

  return (
    <div className="my-8 rounded-2xl bg-gradient-to-br from-orange-50 via-amber-50 to-red-50 px-4 py-8">
      <div className="mx-auto max-w-4xl">
        {/* Calculator Form */}
        <div className="space-y-6">
          {/* Contact Information Section */}
          <div className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
            <h3 className="mb-2 flex items-center gap-2 text-xl font-bold text-red-600">
              <User className="h-5 w-5" />
              Contact Information
            </h3>
            <p className="mb-6 text-sm text-gray-500">
              Required for instant quote and lead generation
            </p>

            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              <FormInput
                id="name"
                label="Your Name"
                value={quoteData.name}
                onChange={(v) => handleInputChange('name', v)}
                placeholder="Enter your name"
                required
                error={touched.name ? validationErrors.name : undefined}
                icon={<User className="h-4 w-4 text-gray-400" />}
              />

              <div className="flex flex-col space-y-1.5">
                <label
                  htmlFor="phone"
                  className="flex items-center gap-2 text-sm font-semibold text-gray-700"
                >
                  <Phone className="h-4 w-4 text-gray-400" />
                  Phone Number
                  <span className="text-red-500">*</span>
                </label>
                <input
                  id="phone"
                  type="tel"
                  value={quoteData.phone}
                  onChange={(e) =>
                    handleInputChange(
                      'phone',
                      e.target.value.replace(/[^\d\s\-\(\)\+]/g, '').slice(0, 20),
                    )
                  }
                  onBlur={() => handleBlur('phone')}
                  placeholder="(916) 740-8768"
                  className={`w-full rounded-lg border-2 px-4 py-3 transition-all duration-200 focus:ring-2 focus:ring-offset-1 focus:outline-none ${
                    touched.phone && validationErrors.phone
                      ? 'border-red-300 bg-red-50 focus:border-red-500 focus:ring-red-200'
                      : 'border-gray-200 hover:border-gray-300 focus:border-red-500 focus:ring-red-200'
                  }`}
                  required
                />
                {touched.phone && validationErrors.phone ? (
                  <p className="flex items-center gap-1 text-sm text-red-600">
                    <AlertCircle className="h-4 w-4" />
                    {validationErrors.phone}
                  </p>
                ) : (
                  <p className="text-xs text-gray-500">We&apos;ll text you the quote instantly</p>
                )}
              </div>
            </div>
          </div>

          {/* Event Details Section */}
          <div className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
            <h3 className="mb-6 flex items-center gap-2 text-xl font-bold text-red-600">
              <Users className="h-5 w-5" />
              Event Details
            </h3>

            <div className="mb-6 grid grid-cols-1 gap-6 md:grid-cols-2">
              <div className="flex flex-col space-y-1.5">
                <label
                  htmlFor="adults"
                  className="flex items-center gap-2 text-sm font-semibold text-gray-700"
                >
                  <Users className="h-4 w-4 text-gray-400" />
                  Adults (13+)
                  <span className="text-red-500">*</span>
                </label>
                <input
                  id="adults"
                  type="number"
                  min="1"
                  max="50"
                  value={quoteData.adults}
                  onChange={(e) =>
                    handleInputChange('adults', Math.max(1, parseInt(e.target.value) || 1))
                  }
                  onBlur={() => handleBlur('adults')}
                  className="w-full rounded-lg border-2 border-gray-200 px-4 py-3 transition-all duration-200 hover:border-gray-300 focus:border-red-500 focus:ring-2 focus:ring-red-200 focus:ring-offset-1 focus:outline-none"
                  required
                />
                <p className="text-xs font-medium text-green-600">${adultPrice} each</p>
              </div>

              <div className="flex flex-col space-y-1.5">
                <label
                  htmlFor="children"
                  className="flex items-center gap-2 text-sm font-semibold text-gray-700"
                >
                  <Baby className="h-4 w-4 text-gray-400" />
                  Children (6-12)
                </label>
                <input
                  id="children"
                  type="number"
                  min="0"
                  max="20"
                  value={quoteData.children}
                  onChange={(e) =>
                    handleInputChange('children', Math.max(0, parseInt(e.target.value) || 0))
                  }
                  className="w-full rounded-lg border-2 border-gray-200 px-4 py-3 transition-all duration-200 hover:border-gray-300 focus:border-red-500 focus:ring-2 focus:ring-red-200 focus:ring-offset-1 focus:outline-none"
                />
                <p className="text-xs font-medium text-green-600">
                  ${childPrice} each ({childFreeUnderAge} &amp; under free)
                </p>
              </div>
            </div>

            <div className="mb-6 grid grid-cols-1 gap-6 md:grid-cols-2">
              <FormInput
                id="location"
                label="Event Location/City"
                value={quoteData.location}
                onChange={(v) => handleInputChange('location', v)}
                placeholder="e.g., San Francisco, San Jose..."
                icon={<MapPin className="h-4 w-4 text-gray-400" />}
              />

              <div className="flex flex-col space-y-1.5">
                <label
                  htmlFor="zipCode"
                  className="flex items-center gap-2 text-sm font-semibold text-gray-700"
                >
                  <Navigation className="h-4 w-4 text-gray-400" />
                  Zip Code
                </label>
                <input
                  id="zipCode"
                  type="text"
                  value={quoteData.zipCode}
                  onChange={(e) =>
                    handleInputChange('zipCode', e.target.value.replace(/\D/g, '').slice(0, 5))
                  }
                  placeholder="94xxx"
                  maxLength={5}
                  className="w-full rounded-lg border-2 border-gray-200 px-4 py-3 transition-all duration-200 hover:border-gray-300 focus:border-red-500 focus:ring-2 focus:ring-red-200 focus:ring-offset-1 focus:outline-none"
                />
                <p className="text-xs text-gray-500">For service area confirmation</p>
              </div>
            </div>

            {/* Full Address Field - Full Width */}
            <div className="flex flex-col space-y-1.5">
              <label
                htmlFor="venueAddress"
                className="flex items-center gap-2 text-sm font-semibold text-gray-700"
              >
                <MapPin className="h-4 w-4 text-gray-400" />
                Full Venue Address
                <span className="text-red-500">*</span>
                <span className="ml-1 rounded-full bg-blue-50 px-2 py-0.5 text-xs font-normal text-blue-600">
                  Required for travel fee
                </span>
              </label>
              <input
                ref={venueAddressInputRef}
                id="venueAddress"
                type="text"
                value={quoteData.venueAddress}
                onChange={(e) => handleInputChange('venueAddress', e.target.value)}
                placeholder="Start typing your address... (e.g., 123 Main Street)"
                className="w-full rounded-lg border-2 border-gray-200 px-4 py-3 transition-all duration-200 hover:border-gray-300 focus:border-red-500 focus:ring-2 focus:ring-red-200 focus:ring-offset-1 focus:outline-none"
                required
                autoComplete="off"
              />
              <p className="flex items-center gap-1 text-xs text-gray-500">
                📍 <strong>Smart Address Search:</strong> Start typing and select from suggestions
                for automatic travel fee calculation via Google Maps
              </p>
            </div>
          </div>

          {/* Premium Upgrades Section */}
          <div className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
            <div className="mb-2 flex items-center gap-2">
              <span className="rounded-full bg-gradient-to-r from-amber-500 to-orange-500 px-2.5 py-1 text-xs font-bold text-white">
                PREMIUM
              </span>
              <h3 className="text-xl font-bold text-gray-800">Premium Upgrades</h3>
            </div>
            <p className="mb-6 text-sm text-gray-500">
              Replace any protein with these premium options
            </p>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <UpgradeInput
                label="Salmon"
                price="+$5 each"
                value={quoteData.salmon}
                onChange={(v) => handleInputChange('salmon', v)}
              />
              <UpgradeInput
                label="Scallops"
                price="+$5 each"
                value={quoteData.scallops}
                onChange={(v) => handleInputChange('scallops', v)}
              />
              <UpgradeInput
                label="Filet Mignon"
                price="+$5 each"
                value={quoteData.filetMignon}
                onChange={(v) => handleInputChange('filetMignon', v)}
              />
              <UpgradeInput
                label="Lobster Tail"
                price="+$15 each"
                value={quoteData.lobsterTail}
                onChange={(v) => handleInputChange('lobsterTail', v)}
              />
              <UpgradeInput
                label="3rd Protein"
                price="+$10 each"
                value={quoteData.thirdProteins}
                onChange={(v) => handleInputChange('thirdProteins', v)}
              />
            </div>
          </div>

          {/* Additional Enhancements Section */}
          <div className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
            <h3 className="mb-2 text-xl font-bold text-gray-800">Additional Enhancements</h3>
            <p className="mb-6 text-sm text-gray-500">
              Additional choice options to customize your hibachi experience
            </p>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <UpgradeInput
                label="Yakisoba Noodles"
                price="+$5 each"
                value={quoteData.yakisobaNoodles}
                onChange={(v) => handleInputChange('yakisobaNoodles', v)}
                hint="Japanese style lo mein noodles"
              />
              <UpgradeInput
                label="Extra Fried Rice"
                price="+$5 each"
                value={quoteData.extraFriedRice}
                onChange={(v) => handleInputChange('extraFriedRice', v)}
                hint="Additional portion of hibachi fried rice"
              />
              <UpgradeInput
                label="Extra Vegetables"
                price="+$5 each"
                value={quoteData.extraVegetables}
                onChange={(v) => handleInputChange('extraVegetables', v)}
                hint="Additional portion of mixed seasonal vegetables"
              />
              <UpgradeInput
                label="Edamame"
                price="+$5 each"
                value={quoteData.edamame}
                onChange={(v) => handleInputChange('edamame', v)}
                hint="Fresh steamed soybeans with sea salt"
              />
              <UpgradeInput
                label="Gyoza"
                price="+$10 each"
                value={quoteData.gyoza}
                onChange={(v) => handleInputChange('gyoza', v)}
                hint="Pan-fried Japanese dumplings"
              />
            </div>
          </div>

          {/* Travel Fee Notice */}
          <div className="rounded-xl border border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50 p-6">
            <div className="flex items-start gap-4">
              <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-blue-100">
                <span className="text-2xl">🚗</span>
              </div>
              <div>
                <h4 className="mb-1 text-lg font-bold text-blue-900">
                  Smart Travel Fee Calculation
                </h4>
                <p className="text-blue-800">
                  <strong>Enter your venue address above</strong> and we&apos;ll calculate your
                  exact travel fee using Google Maps! The first 30 miles are FREE, then $2 per mile
                  for distances beyond that.
                </p>
                <p className="mt-2 flex items-center gap-1 text-blue-700">
                  <span className="text-lg">✨</span>
                  <strong>New!</strong> Get instant travel fee calculation when you enter your venue
                  address
                </p>
              </div>
            </div>
          </div>

          {/* Calculate Button */}
          <button
            className={`w-full transform rounded-xl px-8 py-4 text-lg font-bold transition-all duration-300 ${
              isCalculating
                ? 'cursor-not-allowed bg-gray-400'
                : 'bg-gradient-to-r from-red-600 to-red-700 hover:scale-[1.02] hover:from-red-700 hover:to-red-800 hover:shadow-xl active:scale-[0.98]'
            } text-white shadow-lg`}
            onClick={calculateQuote}
            disabled={isCalculating || quoteData.adults === 0}
          >
            {isCalculating ? (
              <span className="flex items-center justify-center gap-2">
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
                Calculating...
              </span>
            ) : (
              'Calculate Quote'
            )}
          </button>

          {/* Error Display */}
          {calculationError && (
            <div className="flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 p-4">
              <AlertCircle className="h-5 w-5 flex-shrink-0 text-red-500" />
              <p className="text-red-700">{calculationError}</p>
            </div>
          )}
        </div>

        {/* Quote Results */}
        {quoteResult && (
          <div className="mt-8 overflow-hidden rounded-2xl border-2 border-red-500 bg-white shadow-xl">
            {/* Results Header */}
            <div className="bg-gradient-to-r from-red-600 to-red-700 px-6 py-4">
              <h3 className="flex items-center justify-center gap-2 text-center text-2xl font-bold text-white">
                <CheckCircle className="h-6 w-6" />
                Your Estimated Quote
              </h3>
            </div>

            <div className="space-y-6 p-6">
              {/* Price Breakdown */}
              <div className="space-y-3">
                <div className="flex items-center justify-between border-b border-gray-100 py-3">
                  <span className="font-medium text-gray-600">Base Price:</span>
                  <span className="text-xl font-bold text-gray-800">${quoteResult.baseTotal}</span>
                </div>

                {quoteResult.upgradeTotal > 0 && (
                  <div className="flex items-center justify-between border-b border-gray-100 py-3">
                    <span className="font-medium text-gray-600">Upgrades:</span>
                    <span className="text-xl font-bold text-orange-600">
                      ${quoteResult.upgradeTotal}
                    </span>
                  </div>
                )}

                {/* Travel Fee Display */}
                {quoteResult.travelDistance !== undefined && quoteResult.travelFee !== undefined ? (
                  <div className="flex items-center justify-between border-b border-gray-100 py-3">
                    <span className="font-medium text-gray-600">
                      Travel Fee ({quoteResult.travelDistance.toFixed(1)} miles):
                    </span>
                    <span className="text-xl font-bold">
                      {quoteResult.travelFee === 0 ? (
                        <span className="flex items-center gap-1 text-green-600">
                          FREE <span className="text-lg">✨</span>
                        </span>
                      ) : (
                        <span className="text-blue-600">${quoteResult.travelFee.toFixed(2)}</span>
                      )}
                    </span>
                  </div>
                ) : (
                  <div className="flex items-center justify-between border-b border-gray-100 py-3">
                    <span className="font-medium text-gray-600">Travel Fee:</span>
                    <span className="text-sm text-gray-500 italic">
                      Enter address for calculation
                    </span>
                  </div>
                )}

                {/* Total */}
                <div className="-mx-2 flex items-center justify-between rounded-xl bg-gradient-to-r from-red-600 to-red-700 px-4 py-4">
                  <span className="text-lg font-bold text-white">
                    {quoteResult.travelFee !== undefined ? 'Total:' : 'Estimated Subtotal:'}
                  </span>
                  <span className="text-3xl font-bold text-white">
                    ${quoteResult.grandTotal.toFixed(2)}
                  </span>
                </div>
              </div>

              {/* Gratuity Section */}
              <div className="rounded-xl border border-amber-200 bg-gradient-to-br from-amber-50 to-orange-50 p-6">
                <h4 className="mb-3 flex items-center gap-2 text-lg font-bold text-amber-800">
                  💝 Show Your Appreciation
                </h4>
                <p className="mb-4 text-sm text-amber-700">
                  <strong>Please note:</strong> This quote does not include gratuity for our
                  talented chefs who pour their hearts into making your event unforgettable.
                </p>

                <p className="mb-3 font-semibold text-amber-800">Recommended Gratuity:</p>
                <div className="grid grid-cols-3 gap-3">
                  <div className="rounded-lg border border-amber-200 bg-white p-3 text-center">
                    <div className="text-xl font-bold text-amber-600">20%</div>
                    <div className="text-xs text-gray-600">Good Service</div>
                    <div className="mt-1 text-sm font-semibold text-gray-800">
                      ${(quoteResult.grandTotal * 0.2).toFixed(2)}
                    </div>
                  </div>
                  <div className="relative rounded-lg border-2 border-amber-400 bg-gradient-to-br from-amber-100 to-orange-100 p-3 text-center">
                    <div className="absolute -top-2 left-1/2 -translate-x-1/2 rounded-full bg-amber-500 px-2 py-0.5 text-xs text-white">
                      Recommended
                    </div>
                    <div className="text-xl font-bold text-amber-700">25%</div>
                    <div className="text-xs text-gray-700">Great Service ⭐</div>
                    <div className="mt-1 text-sm font-semibold text-gray-800">
                      ${(quoteResult.grandTotal * 0.25).toFixed(2)}
                    </div>
                  </div>
                  <div className="rounded-lg border border-amber-200 bg-white p-3 text-center">
                    <div className="text-xl font-bold text-amber-600">30-35%</div>
                    <div className="text-xs text-gray-600">Exceptional</div>
                    <div className="mt-1 text-sm font-semibold text-gray-800">
                      ${(quoteResult.grandTotal * 0.3).toFixed(2)}+
                    </div>
                  </div>
                </div>
                <p className="mt-3 text-xs text-amber-700 italic">
                  💡 Gratuity is paid directly to your chef at the end of your event. Cash, Venmo,
                  or Zelle are greatly appreciated!
                </p>
              </div>

              {/* Important Notes */}
              <div className="rounded-xl bg-gray-50 p-5">
                <h4 className="mb-3 font-bold text-gray-800">Important Information:</h4>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li className="flex items-start gap-2">
                    <span className="mt-0.5 text-green-500">✓</span>
                    <span>
                      <strong>Minimum:</strong> $550 party total automatically applied
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-0.5 text-green-500">✓</span>
                    <span>
                      <strong>Pricing:</strong> This is an initial estimate - final pricing
                      confirmed during booking consultation
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-0.5 text-green-500">✓</span>
                    <span>
                      <strong>Travel Fee:</strong> First 30 miles FREE, then $2/mile
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-0.5 text-green-500">✓</span>
                    <span>
                      <strong>Deposit:</strong> $100 refundable deposit required (refunded if
                      canceled 7+ days before event)
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-0.5 text-green-500">✓</span>
                    <span>
                      <strong>What&apos;s Included:</strong> Professional chef, all equipment,
                      ingredients, setup, performance, and cleanup
                    </span>
                  </li>
                </ul>
              </div>

              {/* CTA Buttons - Changed to Availability Check */}
              {funnelStep === 'availability' ? (
                <div className="space-y-6">
                  {/* Availability Check Section */}
                  <div className="rounded-xl border border-blue-200 bg-gradient-to-br from-blue-50 to-indigo-50 p-6">
                    <h4 className="mb-4 flex items-center gap-2 text-lg font-bold text-blue-900">
                      <Calendar className="h-5 w-5" />
                      Check Availability
                    </h4>
                    <p className="mb-4 text-sm text-blue-700">
                      Select your preferred date and time to check if we can serve your event.
                    </p>

                    {/* Date Picker */}
                    <div className="mb-4">
                      <label className="mb-2 block text-sm font-semibold text-gray-700">
                        Event Date
                      </label>
                      <LazyDatePicker
                        selected={selectedDate}
                        onChange={(date: Date | null) => setSelectedDate(date)}
                        minDate={addDays(new Date(), 2)}
                        maxDate={addDays(new Date(), 90)}
                        placeholderText="Select your event date"
                        className="w-full rounded-lg border-2 border-gray-200 px-4 py-3 transition-all duration-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 focus:outline-none"
                        dateFormat="MMMM d, yyyy"
                      />
                    </div>

                    {/* Time Slots */}
                    {selectedDate && (
                      <div className="mt-4">
                        <label className="mb-2 block flex items-center gap-2 text-sm font-semibold text-gray-700">
                          <Clock className="h-4 w-4" />
                          Available Time Slots for {format(selectedDate, 'MMMM d, yyyy')}
                        </label>

                        {loadingTimeSlots ? (
                          <div className="flex items-center justify-center py-6">
                            <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
                            <span className="ml-2 text-gray-600">Checking availability...</span>
                          </div>
                        ) : timeSlots.length > 0 ? (
                          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                            {timeSlots.map((slot) => (
                              <button
                                key={slot.time}
                                type="button"
                                onClick={() => slot.isAvailable && setSelectedTime(slot.time)}
                                disabled={!slot.isAvailable}
                                className={`rounded-lg px-4 py-3 text-center transition-all duration-200 ${
                                  selectedTime === slot.time
                                    ? 'scale-105 bg-blue-600 text-white shadow-lg'
                                    : slot.isAvailable
                                      ? 'border-2 border-gray-200 bg-white hover:border-blue-400 hover:bg-blue-50'
                                      : 'cursor-not-allowed bg-gray-100 text-gray-400 line-through'
                                }`}
                              >
                                <div className="font-bold">{slot.label || slot.time}</div>
                                <div className="mt-1 text-xs">
                                  {slot.isAvailable ? (
                                    <span className="text-green-600">Available</span>
                                  ) : (
                                    <span className="text-red-500">Booked</span>
                                  )}
                                </div>
                              </button>
                            ))}
                          </div>
                        ) : (
                          <div className="py-6 text-center text-gray-500">
                            <p>No time slots available for this date.</p>
                            <p className="mt-1 text-sm">Please try a different date.</p>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Proceed to Booking Button */}
                    {selectedDate && selectedTime && (
                      <button
                        onClick={handleProceedToBooking}
                        className="mt-6 flex w-full transform items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-green-600 to-green-700 px-6 py-4 font-bold text-white shadow-lg transition-all duration-300 hover:scale-[1.02] hover:from-green-700 hover:to-green-800 hover:shadow-xl"
                      >
                        <span>Proceed to Booking</span>
                        <ArrowRight className="h-5 w-5" />
                      </button>
                    )}
                  </div>

                  {/* Alternative: Call Us */}
                  <div className="flex flex-col gap-4 sm:flex-row">
                    <ProtectedPhone
                      className="inline-flex flex-1 items-center justify-center gap-2 rounded-xl border-2 border-red-600 px-6 py-4 font-bold text-red-600 transition-all duration-300 hover:bg-red-50"
                      showIcon={true}
                    />
                  </div>
                </div>
              ) : (
                <div className="flex flex-col gap-4 sm:flex-row">
                  <a
                    href="/BookUs"
                    className="inline-flex flex-1 transform items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-red-600 to-red-700 px-6 py-4 font-bold text-white shadow-lg transition-all duration-300 hover:scale-[1.02] hover:from-red-700 hover:to-red-800 hover:shadow-xl"
                  >
                    🎉 Book Your Event Now
                  </a>
                  <ProtectedPhone
                    className="inline-flex flex-1 items-center justify-center gap-2 rounded-xl border-2 border-red-600 px-6 py-4 font-bold text-red-600 transition-all duration-300 hover:bg-red-50"
                    showIcon={true}
                  />
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
