'use client';

import { useState, useEffect, useRef } from 'react';

import { logger } from '@/lib/logger';
import { submitQuoteLead } from '@/lib/leadService';

// Google Maps Autocomplete types
declare global {
  interface Window {
    google: any;
    initAutocomplete?: () => void;
  }
}

interface QuoteData {
  adults: number;
  children: number;
  location: string;
  zipCode: string;
  venueAddress: string; // NEW: Full venue address for accurate travel fee
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

interface QuoteResult {
  baseTotal: number;
  upgradeTotal: number;
  grandTotal: number;
  travelFee?: number; // NEW: Travel fee from backend calculation
  travelDistance?: number; // NEW: Distance in miles
  finalTotal?: number; // NEW: Grand total + travel fee
}

export function QuoteCalculator() {
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
  const [isCalculatingTravelFee, setIsCalculatingTravelFee] = useState(false);

  // Google Places Autocomplete refs
  const venueAddressInputRef = useRef<HTMLInputElement>(null);
  const autocompleteRef = useRef<any>(null);

  const handleInputChange = (field: keyof QuoteData, value: number | string) => {
    setQuoteData((prev) => ({ ...prev, [field]: value }));
    setQuoteResult(null); // Clear results when input changes
    setCalculationError('');
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

            place.address_components.forEach((component: any) => {
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
    <div className="quote-calculator">
      <div className="calculator-form">
        <div className="form-section">
          <h3>Contact Information</h3>
          <p className="section-subtitle">Required for instant quote and lead generation</p>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="name">Your Name *</label>
              <input
                id="name"
                type="text"
                value={quoteData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                placeholder="Enter your name"
                className="form-input"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="phone">Phone Number *</label>
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
                placeholder="(916) 740-8768"
                className="form-input"
                required
              />
              <span className="field-note">We&apos;ll text you the quote instantly</span>
            </div>
          </div>
        </div>

        <div className="form-section">
          <h3>Event Details</h3>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="adults">Adults (13+) *</label>
              <input
                id="adults"
                type="number"
                min="1"
                max="50"
                value={quoteData.adults}
                onChange={(e) =>
                  handleInputChange('adults', Math.max(1, parseInt(e.target.value) || 1))
                }
                className="form-input"
                required
              />
              <span className="field-note">$55 each</span>
            </div>

            <div className="form-group">
              <label htmlFor="children">Children (6-12)</label>
              <input
                id="children"
                type="number"
                min="0"
                max="20"
                value={quoteData.children}
                onChange={(e) =>
                  handleInputChange('children', Math.max(0, parseInt(e.target.value) || 0))
                }
                className="form-input"
              />
              <span className="field-note">$30 each (5 & under free)</span>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="location">Event Location/City</label>
              <input
                id="location"
                type="text"
                value={quoteData.location}
                onChange={(e) => handleInputChange('location', e.target.value)}
                placeholder="e.g., San Francisco, San Jose..."
                className="form-input"
              />
            </div>

            <div className="form-group">
              <label htmlFor="zipCode">Zip Code</label>
              <input
                id="zipCode"
                type="text"
                value={quoteData.zipCode}
                onChange={(e) =>
                  handleInputChange('zipCode', e.target.value.replace(/\D/g, '').slice(0, 5))
                }
                placeholder="94xxx"
                className="form-input"
                maxLength={5}
              />
              <span className="field-note">For service area confirmation</span>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group" style={{ gridColumn: '1 / -1' }}>
              <label htmlFor="venueAddress">
                Full Venue Address *
                <span className="ml-2 text-xs text-blue-600">
                  (Required for accurate travel fee calculation)
                </span>
              </label>
              <input
                ref={venueAddressInputRef}
                id="venueAddress"
                type="text"
                value={quoteData.venueAddress}
                onChange={(e) => handleInputChange('venueAddress', e.target.value)}
                placeholder="Start typing your address... (e.g., 123 Main Street)"
                className="form-input"
                required
                autoComplete="off"
              />
              <span className="field-note">
                📍 <strong>Smart Address Search:</strong> Start typing and select from suggestions
                for automatic travel fee calculation via Google Maps
              </span>
            </div>
          </div>
        </div>

        <div className="form-section">
          <h3>Premium Upgrades (Optional)</h3>
          <p className="section-subtitle">Replace any protein with these premium options</p>

          <div className="form-row">
            <div className="form-group">
              <label>Salmon (+$5 each)</label>
              <input
                type="number"
                min="0"
                value={quoteData.salmon}
                onChange={(e) => handleInputChange('salmon', parseInt(e.target.value) || 0)}
                className="form-input"
              />
            </div>

            <div className="form-group">
              <label>Scallops (+$5 each)</label>
              <input
                type="number"
                min="0"
                value={quoteData.scallops}
                onChange={(e) => handleInputChange('scallops', parseInt(e.target.value) || 0)}
                className="form-input"
              />
            </div>

            <div className="form-group">
              <label>Filet Mignon (+$5 each)</label>
              <input
                type="number"
                min="0"
                value={quoteData.filetMignon}
                onChange={(e) => handleInputChange('filetMignon', parseInt(e.target.value) || 0)}
                className="form-input"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Lobster Tail (+$15 each)</label>
              <input
                type="number"
                min="0"
                value={quoteData.lobsterTail}
                onChange={(e) => handleInputChange('lobsterTail', parseInt(e.target.value) || 0)}
                className="form-input"
              />
            </div>

            <div className="form-group">
              <label>3rd Protein (+$10 each)</label>
              <input
                type="number"
                min="0"
                value={quoteData.thirdProteins}
                onChange={(e) => handleInputChange('thirdProteins', parseInt(e.target.value) || 0)}
                className="form-input"
              />
            </div>

            <div className="form-group">{/* Empty div to maintain grid layout */}</div>
          </div>
        </div>

        <div className="form-section">
          <h3>Additional Enhancements (Optional)</h3>
          <p className="section-subtitle">
            Additional choice options to customize your hibachi experience
          </p>

          <div className="form-row">
            <div className="form-group">
              <label>Yakisoba Noodles (+$5 each)</label>
              <input
                type="number"
                min="0"
                value={quoteData.yakisobaNoodles}
                onChange={(e) =>
                  handleInputChange('yakisobaNoodles', parseInt(e.target.value) || 0)
                }
                className="form-input"
              />
              <span className="field-note">Japanese style lo mein noodles</span>
            </div>

            <div className="form-group">
              <label>Extra Fried Rice (+$5 each)</label>
              <input
                type="number"
                min="0"
                value={quoteData.extraFriedRice}
                onChange={(e) => handleInputChange('extraFriedRice', parseInt(e.target.value) || 0)}
                className="form-input"
              />
              <span className="field-note">Additional portion of hibachi fried rice</span>
            </div>

            <div className="form-group">
              <label>Extra Vegetables (+$5 each)</label>
              <input
                type="number"
                min="0"
                value={quoteData.extraVegetables}
                onChange={(e) =>
                  handleInputChange('extraVegetables', parseInt(e.target.value) || 0)
                }
                className="form-input"
              />
              <span className="field-note">Additional portion of mixed seasonal vegetables</span>
            </div>

            <div className="form-group">
              <label>Edamame (+$5 each)</label>
              <input
                type="number"
                min="0"
                value={quoteData.edamame}
                onChange={(e) => handleInputChange('edamame', parseInt(e.target.value) || 0)}
                className="form-input"
              />
              <span className="field-note">Fresh steamed soybeans with sea salt</span>
            </div>

            <div className="form-group">
              <label>Gyoza (+$10 each)</label>
              <input
                type="number"
                min="0"
                value={quoteData.gyoza}
                onChange={(e) => handleInputChange('gyoza', parseInt(e.target.value) || 0)}
                className="form-input"
              />
              <span className="field-note">Pan-fried Japanese dumplings</span>
            </div>
          </div>
        </div>

        {/* Travel Fee Notice */}
        <div className="travel-notice">
          <div className="notice-content">
            <h4>🚗 Smart Travel Fee Calculation</h4>
            <p>
              <strong>Enter your venue address above</strong> and we&apos;ll calculate your exact
              travel fee using Google Maps! The first 30 miles are FREE, then $2 per mile for
              distances beyond that.
            </p>
            <p className="feature-highlight">
              ✨ <strong>New!</strong> Get instant travel fee calculation when you enter your venue
              address
            </p>
          </div>
        </div>

        <button
          className={`calculate-btn ${isCalculating ? 'calculating' : ''}`}
          onClick={calculateQuote}
          disabled={isCalculating || quoteData.adults === 0}
        >
          {isCalculating ? 'Calculating...' : 'Calculate Quote'}
        </button>

        {calculationError && (
          <div className="calculation-error">
            <p>{calculationError}</p>
          </div>
        )}
      </div>

      {quoteResult && (
        <div className="quote-results">
          <h3>Your Estimated Quote</h3>

          <div className="results-section">
            <div className="result-item">
              <span className="result-label">Base Price:</span>
              <span className="result-value">${quoteResult.baseTotal}</span>
            </div>

            {quoteResult.upgradeTotal > 0 && (
              <div className="result-item">
                <span className="result-label">Upgrades:</span>
                <span className="result-value">${quoteResult.upgradeTotal}</span>
              </div>
            )}

            {/* Travel Fee Display */}
            {quoteResult.travelDistance !== undefined && quoteResult.travelFee !== undefined ? (
              <div className="result-item travel-calculated">
                <span className="result-label">
                  Travel Fee ({quoteResult.travelDistance.toFixed(1)} miles):
                </span>
                <span className="result-value">
                  {quoteResult.travelFee === 0 ? (
                    <span className="free-badge">FREE ✨</span>
                  ) : (
                    `$${quoteResult.travelFee.toFixed(2)}`
                  )}
                </span>
              </div>
            ) : (
              <div className="result-item travel-note">
                <span className="result-label">Travel Fee:</span>
                <span className="result-value">Enter address for calculation</span>
              </div>
            )}

            <div className="result-item total">
              <span className="result-label">
                {quoteResult.travelFee !== undefined ? 'Total:' : 'Estimated Subtotal:'}
              </span>
              <span className="result-value">${quoteResult.grandTotal.toFixed(2)}</span>
            </div>
          </div>

          {/* Gratuity/Tip Recommendation */}
          <div className="gratuity-notice">
            <div className="gratuity-content">
              <h4>💝 Show Your Appreciation</h4>
              <p className="gratuity-message">
                <strong>Please note:</strong> This quote does not include gratuity for our talented
                chefs who pour their hearts into making your event unforgettable. Our chefs work
                tirelessly to deliver an exceptional hibachi experience, bringing the excitement,
                skill, and entertainment that makes your celebration truly special.
              </p>
              <div className="gratuity-recommendation">
                <p className="gratuity-subtitle">
                  <strong>Recommended Gratuity:</strong>
                </p>
                <div className="gratuity-tiers">
                  <div className="gratuity-tier">
                    <span className="tier-percentage">20%</span>
                    <span className="tier-label">Good Service</span>
                    <span className="tier-amount">
                      ${(quoteResult.grandTotal * 0.2).toFixed(2)}
                    </span>
                  </div>
                  <div className="gratuity-tier highlighted">
                    <span className="tier-percentage">25%</span>
                    <span className="tier-label">Great Service ⭐</span>
                    <span className="tier-amount">
                      ${(quoteResult.grandTotal * 0.25).toFixed(2)}
                    </span>
                  </div>
                  <div className="gratuity-tier">
                    <span className="tier-percentage">30-35%</span>
                    <span className="tier-label">Exceptional Service</span>
                    <span className="tier-amount">
                      ${(quoteResult.grandTotal * 0.3).toFixed(2)} - $
                      {(quoteResult.grandTotal * 0.35).toFixed(2)}
                    </span>
                  </div>
                </div>
                <p className="gratuity-note">
                  💡{' '}
                  <em>
                    Gratuity is based on your satisfaction and is paid directly to your chef at the
                    end of your event. Cash, Venmo, or Zelle are greatly appreciated!
                  </em>
                </p>
              </div>
            </div>
          </div>

          <div className="quote-notes">
            <h4>Important Information:</h4>
            <ul>
              <li>
                ✓ <strong>Minimum:</strong> $550 party total automatically applied
              </li>
              <li>
                ✓ <strong>Pricing:</strong> This is an initial estimate - final pricing confirmed
                during booking consultation
              </li>
              <li>
                ✓ <strong>Travel Fee:</strong> First 30 miles FREE, then $2/mile (calculated based
                on your venue address)
              </li>
              <li>
                ✓ <strong>Deposit:</strong> $100 refundable deposit required to secure your date
                (refunded if canceled 7+ days before event)
              </li>
              <li>
                ✓ <strong>What&apos;s Included:</strong> Professional chef, all equipment,
                ingredients, setup, performance, and cleanup
              </li>
            </ul>
          </div>

          <div className="quote-actions">
            <a href="/BookUs" className="book-now-btn">
              🎉 Book Your Event Now
            </a>
            <a href="tel:9167408768" className="call-btn">
              📞 Call Us: (916) 740-8768
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
