'use client'

import { useState } from 'react'

interface QuoteData {
  adults: number
  children: number
  location: string
  zipCode: string
  salmon: number
  scallops: number
  filetMignon: number
  lobsterTail: number
  thirdProteins: number
  yakisobaNoodles: number
  extraFriedRice: number
  extraVegetables: number
  edamame: number
  gyoza: number
}

interface QuoteResult {
  baseTotal: number
  upgradeTotal: number
  grandTotal: number
}

export function QuoteCalculator() {
  const [quoteData, setQuoteData] = useState<QuoteData>({
    adults: 10,
    children: 0,
    location: '',
    zipCode: '',
    salmon: 0,
    scallops: 0,
    filetMignon: 0,
    lobsterTail: 0,
    thirdProteins: 0,
    yakisobaNoodles: 0,
    extraFriedRice: 0,
    extraVegetables: 0,
    edamame: 0,
    gyoza: 0
  })

  const [quoteResult, setQuoteResult] = useState<QuoteResult | null>(null)
  const [isCalculating, setIsCalculating] = useState(false)
  const [calculationError, setCalculationError] = useState('')

  const handleInputChange = (field: keyof QuoteData, value: number | string) => {
    setQuoteData(prev => ({ ...prev, [field]: value }))
    setQuoteResult(null) // Clear results when input changes
    setCalculationError('')
  }

  const calculateQuote = () => {
    setIsCalculating(true)
    setCalculationError('')

    try {
      // Basic validation
      if (quoteData.adults === 0) {
        setCalculationError('Please specify at least 1 adult guest.')
        setIsCalculating(false)
        return
      }

      // Calculate base pricing
      const adultPrice = 55 // $55 per adult
      const childPrice = 30 // $30 per child
      const baseTotal = (quoteData.adults * adultPrice) + (quoteData.children * childPrice)

      // Calculate upgrades
      let upgradeTotal = 0
      upgradeTotal += quoteData.salmon * 5        // Salmon +$5 each
      upgradeTotal += quoteData.scallops * 5      // Scallops +$5 each
      upgradeTotal += quoteData.filetMignon * 5   // Filet Mignon +$5 each
      upgradeTotal += quoteData.lobsterTail * 15  // Lobster Tail +$15 each
      upgradeTotal += quoteData.thirdProteins * 10 // 3rd Protein +$10 each
      upgradeTotal += quoteData.yakisobaNoodles * 5 // Yakisoba Noodles +$5 each
      upgradeTotal += quoteData.extraFriedRice * 5  // Extra Fried Rice +$5 each
      upgradeTotal += quoteData.extraVegetables * 5 // Extra Vegetables +$5 each
      upgradeTotal += quoteData.edamame * 5       // Edamame +$5 each
      upgradeTotal += quoteData.gyoza * 10        // Gyoza +$10 each

      // Apply $550 minimum
      const subtotal = baseTotal + upgradeTotal
      const finalSubtotal = Math.max(subtotal, 550)

      const result: QuoteResult = {
        baseTotal: baseTotal,
        upgradeTotal: upgradeTotal,
        grandTotal: finalSubtotal
      }

      setQuoteResult(result)
    } catch (error) {
      console.error('Calculation error:', error)
      setCalculationError('Error calculating quote. Please try again.')
    } finally {
      setIsCalculating(false)
    }
  }

  return (
    <div className="quote-calculator">
      <div className="calculator-form">
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
                onChange={(e) => handleInputChange('adults', Math.max(1, parseInt(e.target.value) || 1))}
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
                onChange={(e) => handleInputChange('children', Math.max(0, parseInt(e.target.value) || 0))}
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
                onChange={(e) => handleInputChange('zipCode', e.target.value.replace(/\D/g, '').slice(0, 5))}
                placeholder="94xxx"
                className="form-input"
                maxLength={5}
              />
              <span className="field-note">For service area confirmation</span>
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

            <div className="form-group">
              {/* Empty div to maintain grid layout */}
            </div>
          </div>
        </div>

        <div className="form-section">
          <h3>Additional Enhancements (Optional)</h3>
          <p className="section-subtitle">Additional choice options to customize your hibachi experience</p>

          <div className="form-row">
            <div className="form-group">
              <label>Yakisoba Noodles (+$5 each)</label>
              <input
                type="number"
                min="0"
                value={quoteData.yakisobaNoodles}
                onChange={(e) => handleInputChange('yakisobaNoodles', parseInt(e.target.value) || 0)}
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
                onChange={(e) => handleInputChange('extraVegetables', parseInt(e.target.value) || 0)}
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
            <h4>🚗 Travel Fees</h4>
            <p>
              Travel fees may apply depending on your location. The first 30 miles are free, then $2 per mile for distances beyond that.
            </p>
            <p className="contact-note">
              <strong>Contact our customer service</strong> at <a href="tel:9167408768">(916) 740-8768</a> or
              <a href="mailto:cs@myhibachichef.com"> cs@myhibachichef.com</a> for exact travel fee calculation for your area.
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

            <div className="result-item travel-note">
              <span className="result-label">Travel Fee:</span>
              <span className="result-value">Contact us for calculation</span>
            </div>

            <div className="result-item total">
              <span className="result-label">Estimated Subtotal:</span>
              <span className="result-value">${quoteResult.grandTotal}</span>
            </div>
          </div>

          <div className="quote-notes">
            <h4>Important Notes:</h4>
            <ul>
              <li>• $550 minimum party total automatically applied</li>
              <li>• This is an initial estimate only - final pricing confirmed upon booking</li>
              <li>• Travel fees calculated separately based on your exact location</li>
              <li>• Gratuity (20-35% suggested) paid directly to chef</li>
              <li>• $100 refundable deposit required to secure booking (refundable if canceled 7+ days before event)</li>
            </ul>
          </div>

          <div className="quote-actions">
            <a
              href="/BookUs"
              className="book-now-btn"
            >
              Book Your Event Now
            </a>
            <a
              href="/contact"
              className="call-btn"
            >
              Contact Us
            </a>
          </div>
        </div>
      )}
    </div>
  )
}
