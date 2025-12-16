'use client';

import { AlertCircle, CheckCircle, MapPin, User, Phone, Users, Baby, Navigation } from 'lucide-react';
import { useEffect, useRef, useState, useCallback } from 'react';

import { ProtectedPhone } from '@/components/ui/ProtectedPhone';
import { submitQuoteLead } from '@/lib/leadService';
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
            options?: AutocompleteOptions
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
  id, label, type = 'text', value, onChange, placeholder, required, error, hint, icon, min, max, autoComplete
}: FormInputProps) => (
  <div className="flex flex-col space-y-1.5">
    <label htmlFor={id} className="text-sm font-semibold text-gray-700 flex items-center gap-2">
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
      className={`w-full px-4 py-3 rounded-lg border-2 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-1 ${error
        ? 'border-red-300 focus:border-red-500 focus:ring-red-200 bg-red-50'
        : 'border-gray-200 focus:border-red-500 focus:ring-red-200 hover:border-gray-300'
        }`}
      required={required}
    />
    {error && (
      <p className="text-sm text-red-600 flex items-center gap-1 animate-in slide-in-from-top-1">
        <AlertCircle className="w-4 h-4" />
        {error}
      </p>
    )}
    {hint && !error && (
      <p className="text-xs text-gray-500">{hint}</p>
    )}
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
    <label className="text-sm font-medium text-gray-700">{label} <span className="text-red-600 font-semibold">({price})</span></label>
    <input
      type="number"
      min="0"
      value={value}
      onChange={(e) => onChange(Math.max(0, parseInt(e.target.value) || 0))}
      className="w-full px-4 py-3 rounded-lg border-2 border-gray-200 transition-all duration-200 focus:outline-none focus:border-red-500 focus:ring-2 focus:ring-red-200 focus:ring-offset-1 hover:border-gray-300"
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

  // Google Places Autocomplete refs
  const venueAddressInputRef = useRef<HTMLInputElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const autocompleteRef = useRef<any>(null);

  // Real-time validation
  const validateField = useCallback((field: keyof QuoteData, value: string | number): string | undefined => {
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
  }, []);

  // Mark field as touched and validate
  const handleBlur = useCallback((field: keyof QuoteData) => {
    setTouched(prev => ({ ...prev, [field]: true }));
    const error = validateField(field, quoteData[field]);
    setValidationErrors(prev => ({ ...prev, [field]: error }));
  }, [quoteData, validateField]);

  const handleInputChange = (field: keyof QuoteData, value: number | string) => {
    setQuoteData((prev) => ({ ...prev, [field]: value }));
    setQuoteResult(null);
    setCalculationError('');

    // Real-time validation for touched fields
    if (touched[field]) {
      const error = validateField(field, value);
      setValidationErrors(prev => ({ ...prev, [field]: error }));
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

      // Submit lead data to backend using centralized service
      submitQuoteLead({
        name: quoteData.name,
        phone: quoteData.phone,
        adults: quoteData.adults,
        children: quoteData.children,
        location: quoteData.location,
        zipCode: quoteData.zipCode,
        grandTotal: result.grandTotal,
      }).catch((err) => {
        logger.warn('Failed to submit lead data', err as Error);
        // Don't block the quote display if lead submission fails
      });
    } catch (error) {
      logger.error('Calculation error', error as Error);
      setCalculationError('Error calculating quote. Please try again.');
    } finally {
      setIsCalculating(false);
    }
  };

  return (
    <div className="bg-gradient-to-br from-orange-50 via-amber-50 to-red-50 py-8 px-4 rounded-2xl my-8">
      <div className="max-w-4xl mx-auto">
        {/* Calculator Form */}
        <div className="space-y-6">
          {/* Contact Information Section */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h3 className="text-xl font-bold text-red-600 mb-2 flex items-center gap-2">
              <User className="w-5 h-5" />
              Contact Information
            </h3>
            <p className="text-gray-500 text-sm mb-6">Required for instant quote and lead generation</p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <FormInput
                id="name"
                label="Your Name"
                value={quoteData.name}
                onChange={(v) => handleInputChange('name', v)}
                placeholder="Enter your name"
                required
                error={touched.name ? validationErrors.name : undefined}
                icon={<User className="w-4 h-4 text-gray-400" />}
              />

              <div className="flex flex-col space-y-1.5">
                <label htmlFor="phone" className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                  <Phone className="w-4 h-4 text-gray-400" />
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
                  className={`w-full px-4 py-3 rounded-lg border-2 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-1 ${touched.phone && validationErrors.phone
                    ? 'border-red-300 focus:border-red-500 focus:ring-red-200 bg-red-50'
                    : 'border-gray-200 focus:border-red-500 focus:ring-red-200 hover:border-gray-300'
                    }`}
                  required
                />
                {touched.phone && validationErrors.phone ? (
                  <p className="text-sm text-red-600 flex items-center gap-1">
                    <AlertCircle className="w-4 h-4" />
                    {validationErrors.phone}
                  </p>
                ) : (
                  <p className="text-xs text-gray-500">We&apos;ll text you the quote instantly</p>
                )}
              </div>
            </div>
          </div>

          {/* Event Details Section */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h3 className="text-xl font-bold text-red-600 mb-6 flex items-center gap-2">
              <Users className="w-5 h-5" />
              Event Details
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div className="flex flex-col space-y-1.5">
                <label htmlFor="adults" className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                  <Users className="w-4 h-4 text-gray-400" />
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
                  className="w-full px-4 py-3 rounded-lg border-2 border-gray-200 transition-all duration-200 focus:outline-none focus:border-red-500 focus:ring-2 focus:ring-red-200 focus:ring-offset-1 hover:border-gray-300"
                  required
                />
                <p className="text-xs text-green-600 font-medium">${adultPrice} each</p>
              </div>

              <div className="flex flex-col space-y-1.5">
                <label htmlFor="children" className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                  <Baby className="w-4 h-4 text-gray-400" />
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
                  className="w-full px-4 py-3 rounded-lg border-2 border-gray-200 transition-all duration-200 focus:outline-none focus:border-red-500 focus:ring-2 focus:ring-red-200 focus:ring-offset-1 hover:border-gray-300"
                />
                <p className="text-xs text-green-600 font-medium">${childPrice} each ({childFreeUnderAge} &amp; under free)</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <FormInput
                id="location"
                label="Event Location/City"
                value={quoteData.location}
                onChange={(v) => handleInputChange('location', v)}
                placeholder="e.g., San Francisco, San Jose..."
                icon={<MapPin className="w-4 h-4 text-gray-400" />}
              />

              <div className="flex flex-col space-y-1.5">
                <label htmlFor="zipCode" className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                  <Navigation className="w-4 h-4 text-gray-400" />
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
                  className="w-full px-4 py-3 rounded-lg border-2 border-gray-200 transition-all duration-200 focus:outline-none focus:border-red-500 focus:ring-2 focus:ring-red-200 focus:ring-offset-1 hover:border-gray-300"
                />
                <p className="text-xs text-gray-500">For service area confirmation</p>
              </div>
            </div>

            {/* Full Address Field - Full Width */}
            <div className="flex flex-col space-y-1.5">
              <label htmlFor="venueAddress" className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                <MapPin className="w-4 h-4 text-gray-400" />
                Full Venue Address
                <span className="text-red-500">*</span>
                <span className="ml-1 text-xs font-normal text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full">
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
                className="w-full px-4 py-3 rounded-lg border-2 border-gray-200 transition-all duration-200 focus:outline-none focus:border-red-500 focus:ring-2 focus:ring-red-200 focus:ring-offset-1 hover:border-gray-300"
                required
                autoComplete="off"
              />
              <p className="text-xs text-gray-500 flex items-center gap-1">
                📍 <strong>Smart Address Search:</strong> Start typing and select from suggestions for automatic travel fee calculation via Google Maps
              </p>
            </div>
          </div>

          {/* Premium Upgrades Section */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center gap-2 mb-2">
              <span className="bg-gradient-to-r from-amber-500 to-orange-500 text-white text-xs font-bold px-2.5 py-1 rounded-full">PREMIUM</span>
              <h3 className="text-xl font-bold text-gray-800">Premium Upgrades</h3>
            </div>
            <p className="text-gray-500 text-sm mb-6">Replace any protein with these premium options</p>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
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
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-2">Additional Enhancements</h3>
            <p className="text-gray-500 text-sm mb-6">Additional choice options to customize your hibachi experience</p>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
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
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-200 p-6">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-2xl">🚗</span>
              </div>
              <div>
                <h4 className="font-bold text-blue-900 text-lg mb-1">Smart Travel Fee Calculation</h4>
                <p className="text-blue-800">
                  <strong>Enter your venue address above</strong> and we&apos;ll calculate your exact
                  travel fee using Google Maps! The first 30 miles are FREE, then $2 per mile for
                  distances beyond that.
                </p>
                <p className="text-blue-700 mt-2 flex items-center gap-1">
                  <span className="text-lg">✨</span>
                  <strong>New!</strong> Get instant travel fee calculation when you enter your venue address
                </p>
              </div>
            </div>
          </div>

          {/* Calculate Button */}
          <button
            className={`w-full py-4 px-8 rounded-xl font-bold text-lg transition-all duration-300 transform ${isCalculating
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 hover:scale-[1.02] hover:shadow-xl active:scale-[0.98]'
              } text-white shadow-lg`}
            onClick={calculateQuote}
            disabled={isCalculating || quoteData.adults === 0}
          >
            {isCalculating ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Calculating...
              </span>
            ) : (
              'Calculate Quote'
            )}
          </button>

          {/* Error Display */}
          {calculationError && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
              <p className="text-red-700">{calculationError}</p>
            </div>
          )}
        </div>

        {/* Quote Results */}
        {quoteResult && (
          <div className="mt-8 bg-white rounded-2xl shadow-xl border-2 border-red-500 overflow-hidden">
            {/* Results Header */}
            <div className="bg-gradient-to-r from-red-600 to-red-700 px-6 py-4">
              <h3 className="text-2xl font-bold text-white text-center flex items-center justify-center gap-2">
                <CheckCircle className="w-6 h-6" />
                Your Estimated Quote
              </h3>
            </div>

            <div className="p-6 space-y-6">
              {/* Price Breakdown */}
              <div className="space-y-3">
                <div className="flex justify-between items-center py-3 border-b border-gray-100">
                  <span className="text-gray-600 font-medium">Base Price:</span>
                  <span className="text-xl font-bold text-gray-800">${quoteResult.baseTotal}</span>
                </div>

                {quoteResult.upgradeTotal > 0 && (
                  <div className="flex justify-between items-center py-3 border-b border-gray-100">
                    <span className="text-gray-600 font-medium">Upgrades:</span>
                    <span className="text-xl font-bold text-orange-600">${quoteResult.upgradeTotal}</span>
                  </div>
                )}

                {/* Travel Fee Display */}
                {quoteResult.travelDistance !== undefined && quoteResult.travelFee !== undefined ? (
                  <div className="flex justify-between items-center py-3 border-b border-gray-100">
                    <span className="text-gray-600 font-medium">
                      Travel Fee ({quoteResult.travelDistance.toFixed(1)} miles):
                    </span>
                    <span className="text-xl font-bold">
                      {quoteResult.travelFee === 0 ? (
                        <span className="text-green-600 flex items-center gap-1">
                          FREE <span className="text-lg">✨</span>
                        </span>
                      ) : (
                        <span className="text-blue-600">${quoteResult.travelFee.toFixed(2)}</span>
                      )}
                    </span>
                  </div>
                ) : (
                  <div className="flex justify-between items-center py-3 border-b border-gray-100">
                    <span className="text-gray-600 font-medium">Travel Fee:</span>
                    <span className="text-sm text-gray-500 italic">Enter address for calculation</span>
                  </div>
                )}

                {/* Total */}
                <div className="flex justify-between items-center py-4 px-4 bg-gradient-to-r from-red-600 to-red-700 rounded-xl -mx-2">
                  <span className="text-white font-bold text-lg">
                    {quoteResult.travelFee !== undefined ? 'Total:' : 'Estimated Subtotal:'}
                  </span>
                  <span className="text-3xl font-bold text-white">${quoteResult.grandTotal.toFixed(2)}</span>
                </div>
              </div>

              {/* Gratuity Section */}
              <div className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-xl p-6 border border-amber-200">
                <h4 className="text-lg font-bold text-amber-800 mb-3 flex items-center gap-2">
                  💝 Show Your Appreciation
                </h4>
                <p className="text-amber-700 text-sm mb-4">
                  <strong>Please note:</strong> This quote does not include gratuity for our talented
                  chefs who pour their hearts into making your event unforgettable.
                </p>

                <p className="text-amber-800 font-semibold mb-3">Recommended Gratuity:</p>
                <div className="grid grid-cols-3 gap-3">
                  <div className="bg-white rounded-lg p-3 text-center border border-amber-200">
                    <div className="text-xl font-bold text-amber-600">20%</div>
                    <div className="text-xs text-gray-600">Good Service</div>
                    <div className="text-sm font-semibold text-gray-800 mt-1">
                      ${(quoteResult.grandTotal * 0.2).toFixed(2)}
                    </div>
                  </div>
                  <div className="bg-gradient-to-br from-amber-100 to-orange-100 rounded-lg p-3 text-center border-2 border-amber-400 relative">
                    <div className="absolute -top-2 left-1/2 -translate-x-1/2 bg-amber-500 text-white text-xs px-2 py-0.5 rounded-full">
                      Recommended
                    </div>
                    <div className="text-xl font-bold text-amber-700">25%</div>
                    <div className="text-xs text-gray-700">Great Service ⭐</div>
                    <div className="text-sm font-semibold text-gray-800 mt-1">
                      ${(quoteResult.grandTotal * 0.25).toFixed(2)}
                    </div>
                  </div>
                  <div className="bg-white rounded-lg p-3 text-center border border-amber-200">
                    <div className="text-xl font-bold text-amber-600">30-35%</div>
                    <div className="text-xs text-gray-600">Exceptional</div>
                    <div className="text-sm font-semibold text-gray-800 mt-1">
                      ${(quoteResult.grandTotal * 0.3).toFixed(2)}+
                    </div>
                  </div>
                </div>
                <p className="text-xs text-amber-700 mt-3 italic">
                  💡 Gratuity is paid directly to your chef at the end of your event. Cash, Venmo, or Zelle are greatly appreciated!
                </p>
              </div>

              {/* Important Notes */}
              <div className="bg-gray-50 rounded-xl p-5">
                <h4 className="font-bold text-gray-800 mb-3">Important Information:</h4>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li className="flex items-start gap-2">
                    <span className="text-green-500 mt-0.5">✓</span>
                    <span><strong>Minimum:</strong> $550 party total automatically applied</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-500 mt-0.5">✓</span>
                    <span><strong>Pricing:</strong> This is an initial estimate - final pricing confirmed during booking consultation</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-500 mt-0.5">✓</span>
                    <span><strong>Travel Fee:</strong> First 30 miles FREE, then $2/mile</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-500 mt-0.5">✓</span>
                    <span><strong>Deposit:</strong> $100 refundable deposit required (refunded if canceled 7+ days before event)</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-500 mt-0.5">✓</span>
                    <span><strong>What&apos;s Included:</strong> Professional chef, all equipment, ingredients, setup, performance, and cleanup</span>
                  </li>
                </ul>
              </div>

              {/* CTA Buttons */}
              <div className="flex flex-col sm:flex-row gap-4">
                <a
                  href="/BookUs"
                  className="flex-1 inline-flex items-center justify-center gap-2 px-6 py-4 bg-gradient-to-r from-red-600 to-red-700 text-white font-bold rounded-xl shadow-lg hover:from-red-700 hover:to-red-800 hover:shadow-xl transition-all duration-300 transform hover:scale-[1.02]"
                >
                  🎉 Book Your Event Now
                </a>
                <ProtectedPhone className="flex-1 inline-flex items-center justify-center gap-2 px-6 py-4 border-2 border-red-600 text-red-600 font-bold rounded-xl hover:bg-red-50 transition-all duration-300" showIcon={true} />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
