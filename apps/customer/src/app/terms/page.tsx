import type { Metadata } from 'next'
import './terms.css'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Terms & Conditions - My Hibachi Chef',
  description: 'Terms & Conditions and SMS Terms of Service for My Hibachi Chef catering services. Read our complete terms of service and SMS communication policies.',
  robots: 'index, follow',
  openGraph: {
    title: 'Terms & Conditions - My Hibachi Chef',
    description: 'Terms & Conditions and SMS Terms of Service for My Hibachi Chef catering services',
    type: 'website'
  }
}

export default function TermsPage() {
  return (
    <div className="terms-conditions">
      <div className="container">
        <div className="terms-content">
          <header className="terms-header">
            <h1>Terms & Conditions</h1>
            <p className="last-updated">Last updated: October 8, 2025</p>
          </header>
          <section className="terms-section sms-priority-section">
            <h2>SMS Terms of Service</h2>
            <div className="sms-consent-box">
              <h3>SMS Communication Agreement</h3>
              <p className="sms-agreement">
                <strong>By opting into SMS from a web form or other medium, you are agreeing to receive SMS messages from my Hibachi LLC.</strong>
              </p>
            </div>
            <h3>Types of Messages:</h3>
            <ul className="sms-message-types">
              <li><strong>Booking confirmations</strong> - Order details and confirmation numbers</li>
              <li><strong>Event reminders</strong> - 48 hours and 24 hours before your event</li>
              <li><strong>Chef updates and arrival notifications</strong> - Real-time status updates</li>
              <li><strong>Customer support conversations</strong> - Responses to your inquiries</li>
              <li><strong>Order alerts</strong> - Important booking changes or updates</li>
              <li><strong>Account notifications</strong> - Service-related announcements</li>
              <li><strong>Promotional offers (optional)</strong> - Special deals and new services</li>
            </ul>
            <div className="sms-important-info">
              <h3>Important SMS Information:</h3>
              <ul>
                <li><strong>Message frequency varies</strong> based on your bookings and preferences</li>
                <li><strong>Message and data rates may apply</strong> according to your mobile carrier plan</li>
                <li><strong>Consent not required for purchase</strong> - SMS is optional for service delivery</li>
                <li><strong className="highlight-text">SMS consent is not shared with third parties</strong></li>
              </ul>
            </div>
            <div className="sms-controls">
              <h3>SMS Controls:</h3>
              <ul>
                <li><strong>Opt-Out:</strong> Reply <code>STOP</code> to opt-out at any time</li>
                <li><strong>Opt-In:</strong> Reply <code>START</code> to re-subscribe</li>
                <li><strong>Help:</strong> Reply <code>HELP</code> or contact us:</li>
              </ul>
              <div className="contact-methods">
                <p><strong>Call:</strong> <a href="tel:+19167408768">(916) 740-8768</a></p>
                <p><strong>Email:</strong> <a href="mailto:cs@myhibachichef.com">cs@myhibachichef.com</a></p>
                <p><strong>Visit:</strong> <a href="https://myhibachichef.com">https://myhibachichef.com</a></p>
              </div>
              <div className="policy-resources">
                <h4>Resources:</h4>
                <ul>
                  <li><strong>Privacy Policy:</strong> <Link href="/privacy">https://myhibachichef.com/privacy</Link></li>
                  <li><strong>Terms of Service:</strong> <Link href="/terms">https://myhibachichef.com/terms</Link></li>
                </ul>
              </div>
            </div>
          </section>
          <section className="terms-section">
            <h2>1. Acceptance of Terms</h2>
            <p>
              By accessing and using the services provided by my Hibachi LLC (&quot;Company,&quot; &quot;we,&quot; &quot;us,&quot; or &quot;our&quot;), you (&quot;Customer,&quot; &quot;you,&quot; or &quot;your&quot;) agree to be bound by these Terms & Conditions. These terms apply to all users of our website, mobile applications, and catering services.
            </p>
            <p>
              If you do not agree with any part of these terms, you may not use our services.
            </p>
          </section>
          <section className="terms-section">
            <h2>2. Service Description</h2>
            <p>
              My Hibachi Chef provides premium private hibachi catering services, including:
            </p>
            <ul>
              <li>Private hibachi chef experiences at your location</li>
              <li>Teppanyaki cooking and entertainment</li>
              <li>Event catering for parties, corporate events, and special occasions</li>
              <li>Mobile hibachi grill setup and service</li>
              <li>Custom menu planning and dietary accommodation</li>
            </ul>
            <p>
              Services are available in the Bay Area and Sacramento regions, subject to availability and travel requirements.
            </p>
          </section>
          <section className="terms-section">
            <h2>3. Booking and Payment Terms</h2>
            <h3>3.1 Booking Process</h3>
            <ul>
              <li>All bookings must be confirmed with a signed contract and deposit payment</li>
              <li>Bookings are subject to chef availability and location accessibility</li>
              <li>Final guest count must be provided 48 hours before the event</li>
              <li>Menu selections and dietary restrictions must be communicated in advance</li>
            </ul>
            <h3>3.2 Payment Schedule</h3>
            <ul>
              <li><strong>Deposit:</strong> $100 refundable deposit required to secure booking</li>
              <li><strong>Deposit Refund:</strong> Deposit is refundable if canceled 7+ days before event, non-refundable within 7 days</li>
              <li><strong>Final Payment:</strong> Remaining balance due on event day</li>
              <li><strong>Payment Methods:</strong> Credit cards (Visa, MasterCard, American Express), Venmo Business, Zelle Business, Cash</li>
              <li><strong>Processing:</strong> All credit card payments processed securely through Stripe</li>
            </ul>
            <h3>3.3 Pricing</h3>
            <ul>
              <li>Prices are based on guest count, menu selection, and travel distance</li>
              <li>Additional fees may apply for premium ingredients or extended service time</li>
              <li>Travel fees apply for locations beyond our standard service area</li>
              <li>Prices are subject to change with 30 days notice</li>
            </ul>
          </section>
          <section className="terms-section">
            <h2>4. Cancellation Policy</h2>
            <div className="cancellation-tiers">
              <h3>4.1 Cancellation Timeline</h3>
              <div className="policy-tier">
                <h4>7+ Days Before Event</h4>
                <p>Full refund including $100 deposit</p>
              </div>
              <div className="policy-tier">
                <h4>Less than 7 Days Before Event</h4>
                <p>$100 deposit is non-refundable. No refund for remaining balance.</p>
              </div>
            </div>
            <h3>4.2 Emergency Cancellations</h3>
            <p>
              Cancellations due to severe weather, natural disasters, or other circumstances beyond our control will be handled on a case-by-case basis. We will work with you to reschedule or provide appropriate compensation.
            </p>
          </section>
          <section className="terms-section">
            <h2>5. Rescheduling Policy</h2>
            <ul>
              <li><strong>First Reschedule:</strong> One free reschedule allowed within 48 hours of booking</li>
              <li><strong>Additional Reschedules:</strong> $100 fee applies to any reschedules after the first one</li>
              <li><strong>Notice Required:</strong> Minimum 7 days advance notice recommended</li>
              <li><strong>Availability:</strong> New date subject to chef availability</li>
              <li><strong>Peak Seasons:</strong> Limited rescheduling options during holidays</li>
              <li><strong>Weather:</strong> No fee for weather-related rescheduling if proper notice is given</li>
            </ul>
          </section>
          <section className="terms-section">
            <h2>6. Client Responsibilities</h2>
            <h3>6.1 Venue Requirements</h3>
            <ul>
              <li>Provide adequate space for hibachi grill setup (minimum 10x10 feet)</li>
              <li>Ensure access to standard electrical outlets (110V)</li>
              <li>Provide access to running water for cleanup</li>
              <li>Ensure safe vehicle access for equipment delivery</li>
              <li>Notify neighbors of potential smoke from grilling</li>
            </ul>
            <h3>6.2 Information Requirements</h3>
            <ul>
              <li>Provide accurate guest count 48 hours before event</li>
              <li>Communicate all dietary restrictions and allergies in advance</li>
              <li>Provide clear directions and parking information</li>
              <li>Ensure contact person is available on event day</li>
            </ul>
            <h3>6.3 Safety and Compliance</h3>
            <ul>
              <li>Ensure compliance with local fire safety regulations</li>
              <li>Provide safe working environment for our staff</li>
              <li>Maintain appropriate insurance coverage for your event</li>
              <li>Follow all COVID-19 safety protocols as applicable</li>
            </ul>
          </section>
          <section className="terms-section">
            <h2>7. Liability and Insurance</h2>
            <h3>7.1 Our Insurance Coverage</h3>
            <ul>
              <li>General liability insurance covering our operations</li>
              <li>Food handler&apos;s permits and health certifications</li>
              <li>Equipment insurance for our grills and tools</li>
            </ul>
            <h3>7.2 Limitation of Liability</h3>
            <p>
              Our liability is limited to the total amount paid for services. We are not responsible for:
            </p>
            <ul>
              <li>Damage to client property beyond our direct control</li>
              <li>Injuries resulting from client or guest negligence</li>
              <li>Food allergies not properly communicated in advance</li>
              <li>Weather-related disruptions to outdoor events</li>
              <li>Venue-related issues beyond our control</li>
            </ul>
            <h3>7.3 Indemnification</h3>
            <p>
              Client agrees to indemnify and hold harmless my Hibachi LLC from any claims arising from the event, except those directly caused by our negligence.
            </p>
          </section>
          <section className="terms-section">
            <h2>8. Intellectual Property</h2>
            <ul>
              <li>All recipes, cooking techniques, and proprietary methods remain our intellectual property</li>
              <li>Photos and videos of our services may be used for marketing purposes</li>
              <li>Client may request not to be featured in marketing materials</li>
              <li>Our logo, brand name, and marketing materials are protected trademarks</li>
            </ul>
          </section>
          <section className="terms-section">
            <h2>9. Privacy and Data Protection</h2>
            <p>
              Your privacy is important to us. Please review our <Link href="/privacy">Privacy Policy</Link> for detailed information about how we collect, use, and protect your personal information, including:
            </p>
            <ul>
              <li>Contact information and event details</li>
              <li>Payment and billing information</li>
              <li>Communication preferences and consent</li>
              <li>SMS and email communication policies</li>
              <li>Data sharing and security measures</li>
            </ul>
          </section>
          <section className="terms-section">
            <h2>10. Dispute Resolution</h2>
            <h3>10.1 Informal Resolution</h3>
            <p>
              We encourage direct communication to resolve any disputes. Please contact us immediately if you have concerns about our services.
            </p>
            <h3>10.2 Formal Process</h3>
            <ul>
              <li><strong>Mediation:</strong> Disputes will first be addressed through mediation</li>
              <li><strong>Arbitration:</strong> Unresolved disputes may be subject to binding arbitration</li>
              <li><strong>Jurisdiction:</strong> California state law governs these terms</li>
              <li><strong>Venue:</strong> Legal proceedings must be filed in Alameda County, California</li>
            </ul>
          </section>
          <section className="terms-section">
            <h2>11. Force Majeure</h2>
            <p>
              We are not liable for any failure to perform services due to circumstances beyond our reasonable control, including but not limited to:
            </p>
            <ul>
              <li>Natural disasters, severe weather, or &quot;Acts of God&quot;</li>
              <li>Government regulations or public health emergencies</li>
              <li>Labor strikes or transportation disruptions</li>
              <li>Equipment failure not caused by negligence</li>
              <li>Venue cancellations or access restrictions</li>
            </ul>
          </section>
          <section className="terms-section">
            <h2>12. Changes to Terms</h2>
            <p>
              We reserve the right to modify these Terms & Conditions at any time. Changes will be effective immediately upon posting on our website. We will notify customers of material changes through:
            </p>
            <ul>
              <li>Email notification to registered users</li>
              <li>SMS notification (if you&apos;ve opted in)</li>
              <li>Website banner notification</li>
              <li><strong>Updated &quot;Last Modified&quot; date on this page</strong></li>
            </ul>
            <p>
              Continued use of our services after changes indicates acceptance of the updated terms.
            </p>
          </section>
          <section className="terms-section contact-section">
            <h2>13. Contact Information</h2>
            <div className="contact-info">
              <h3>my Hibachi LLC</h3>
              <p><strong>Private Chef Catering Services</strong></p>
              <h4>Service Areas:</h4>
              <ul>
                <li>Sacramento Metro Area</li>
                <li>San Francisco Bay Area</li>
                <li>Central Valley Region</li>
              </ul>
              <p><strong>Phone:</strong> <a href="tel:+19167408768">(916) 740-8768</a></p>
              <p><strong>Email:</strong> <a href="mailto:cs@myhibachichef.com">cs@myhibachichef.com</a></p>
              <p><strong>Website:</strong> <a href="https://myhibachichef.com">https://myhibachichef.com</a></p>
              <h4>Business Hours:</h4>
              <p>Monday - Sunday: 12:00 PM - 9:00 PM PST</p>
              <p>Emergency Contact: Same phone number available 24/7</p>
              <p style={{ marginTop: '15px', fontSize: '14px', color: '#666', fontStyle: 'italic' }}>
                <em>We are a mobile catering service. Events are held at your location or venue of choice.</em>
              </p>
            </div>
          </section>
          <section className="terms-section">
            <div className="policy-links">
              <p><strong>Related Policies:</strong></p>
              <ul>
                <li><Link href="/privacy">Privacy Policy</Link></li>
                <li><Link href="/contact">Contact Us</Link></li>
                <li><Link href="/quote">Get a Quote</Link></li>
                <li><Link href="/BookUs">Book Our Services</Link></li>
              </ul>
            </div>
          </section>
          <section className="terms-section">
            <div className="acknowledgment">
              <p><strong>By using our services, you acknowledge that you have read, understood, and agree to be bound by these Terms & Conditions and our Privacy Policy.</strong></p>
            </div>
          </section>
        </div>
      </div>

    </div>
  )
}
