import { Metadata } from 'next';
import './privacy.css';
import Link from 'next/link';

import { ProtectedPhone, ProtectedEmail } from '@/components/ui/ProtectedPhone';

export const metadata: Metadata = {
  title: 'Privacy Policy - My Hibachi Chef',
  description:
    'Privacy Policy and SMS Terms for My Hibachi Chef catering services. Learn how we collect, use, and protect your personal information.',
  robots: 'index, follow',
  openGraph: {
    title: 'Privacy Policy - My Hibachi Chef',
    description: 'Privacy Policy and SMS Terms for My Hibachi Chef catering services',
    type: 'website',
  },
};

export default function PrivacyPage() {
  return (
    <div className="privacy-policy">
      <div className="container">
        <div className="privacy-content">
          <header className="privacy-header">
            <h1>Privacy Policy</h1>
            <p className="last-updated">Last updated: October 8, 2025</p>
          </header>
          <section className="privacy-section privacy-overview">
            <h2>Privacy Overview</h2>
            <p>
              my Hibachi LLC (&quot;we,&quot; &quot;us,&quot; or &quot;our&quot;) is committed to
              protecting your privacy and ensuring the security of your personal information. This
              Privacy Policy explains how we collect, use, and safeguard your information when you
              use our hibachi catering services.
            </p>
            <div className="privacy-summary">
              <h3>Quick Summary:</h3>
              <ul>
                <li>We collect information necessary to provide hibachi catering services</li>
                <li>We use your information to deliver excellent culinary experiences</li>
                <li>We do not sell your personal information to third parties</li>
                <li>You have control over your communication preferences</li>
                <li>We implement industry-standard security measures</li>
              </ul>
            </div>
          </section>
          <section className="privacy-section sms-privacy-section">
            <h2>SMS Communication & Privacy</h2>
            <div className="sms-consent-notice">
              <h3>SMS Terms & Consent</h3>
              <p className="consent-statement">
                <strong>
                  By providing your phone number and opting into SMS communications, you consent to
                  receive text messages from my Hibachi LLC regarding your bookings and our
                  services.
                </strong>
              </p>
            </div>
            <h3>SMS Data Collection:</h3>
            <ul>
              <li>
                <strong>Phone Number:</strong> Required for booking confirmations and event
                coordination
              </li>
              <li>
                <strong>Booking Information:</strong> Event details, dates, and guest preferences
              </li>
              <li>
                <strong>Communication Preferences:</strong> Your SMS communication settings and
                opt-in status
              </li>
              <li>
                <strong>Response Data:</strong> Your replies to our messages for service improvement
              </li>
            </ul>
            <h3>SMS Usage:</h3>
            <ul>
              <li>Booking confirmations and event details</li>
              <li>Event reminders (48 hours and 24 hours before service)</li>
              <li>Chef arrival notifications and real-time updates</li>
              <li>Customer support responses and service coordination</li>
              <li>Optional promotional offers (only with explicit consent)</li>
            </ul>
            <div className="sms-privacy-controls">
              <h3>Your SMS Privacy Rights:</h3>
              <ul>
                <li>
                  <strong>Opt-Out:</strong> Text <code>STOP</code> to unsubscribe at any time
                </li>
                <li>
                  <strong>Data Retention:</strong> SMS data is kept only as long as necessary for
                  service delivery
                </li>
                <li>
                  <strong>Third-Party Sharing:</strong> We do not share your SMS consent with third
                  parties
                </li>
                <li>
                  <strong>Frequency Control:</strong> Message frequency varies based on your
                  bookings
                </li>
              </ul>
              <div className="ringcentral-compliance">
                <p className="compliance-statement">
                  <strong>Mobile Opt-In Compliance:</strong> Mobile opt-in, SMS consent, and phone
                  numbers will not be shared with third parties and affiliates for marketing
                  purposes.
                </p>
              </div>
            </div>
          </section>
          <section className="privacy-section">
            <h2>1. Information We Collect</h2>
            <h3>1.1 Personal Information</h3>
            <p>We collect personal information that you provide directly to us, including:</p>
            <ul>
              <li>
                <strong>Contact Information:</strong> Name, email address, phone number, mailing
                address
              </li>
              <li>
                <strong>Event Details:</strong> Event date, location, guest count, menu preferences
              </li>
              <li>
                <strong>Payment Information:</strong> Credit card details, billing address
                (processed securely through Stripe)
              </li>
              <li>
                <strong>Dietary Information:</strong> Food allergies, dietary restrictions, and
                special requests
              </li>
              <li>
                <strong>Communication Records:</strong> Email correspondence, SMS messages, phone
                call notes
              </li>
            </ul>
            <h3>1.2 Automatically Collected Information</h3>
            <ul>
              <li>
                <strong>Website Usage:</strong> IP address, browser type, pages visited, time spent
                on site
              </li>
              <li>
                <strong>Device Information:</strong> Device type, operating system, unique device
                identifiers
              </li>
              <li>
                <strong>Location Data:</strong> General location for service delivery (when
                explicitly provided)
              </li>
              <li>
                <strong>Cookies:</strong> Small data files to improve website functionality and user
                experience
              </li>
            </ul>
            <h3>1.3 Third-Party Information</h3>
            <p>We may receive information about you from:</p>
            <ul>
              <li>Event hosts who book our services on your behalf</li>
              <li>Payment processors (Stripe) for transaction verification</li>
              <li>Social media platforms (if you engage with our content)</li>
              <li>Business partners and referral sources</li>
            </ul>
          </section>
          <section className="privacy-section">
            <h2>2. How We Use Your Information</h2>
            <h3>2.1 Primary Service Delivery</h3>
            <ul>
              <li>Process and fulfill your hibachi catering bookings</li>
              <li>Coordinate event logistics and chef scheduling</li>
              <li>Provide customer support and address inquiries</li>
              <li>Process payments and manage billing</li>
              <li>Accommodate dietary restrictions and special requests</li>
            </ul>
            <h3>2.2 Communication</h3>
            <ul>
              <li>Send booking confirmations and event reminders</li>
              <li>Provide real-time updates about your event</li>
              <li>Respond to customer service requests</li>
              <li>Share important service announcements</li>
              <li>Send promotional offers (with your consent)</li>
            </ul>
            <h3>2.3 Business Operations</h3>
            <ul>
              <li>Improve our services and develop new offerings</li>
              <li>Analyze customer preferences and booking patterns</li>
              <li>Maintain accurate business records</li>
              <li>Comply with legal and regulatory requirements</li>
              <li>Protect against fraud and ensure payment security</li>
            </ul>
          </section>
          <section className="privacy-section">
            <h2>3. Information Sharing</h2>
            <h3>3.1 We Do Not Sell Your Information</h3>
            <p className="no-sale-statement">
              <strong>
                We do not sell, rent, or trade your personal information to third parties for their
                marketing purposes.
              </strong>
            </p>
            <h3>3.2 Service Providers</h3>
            <p>
              We may share your information with trusted service providers who help us operate our
              business:
            </p>
            <ul>
              <li>
                <strong>Payment Processing:</strong> Stripe (for secure credit card processing)
              </li>
              <li>
                <strong>Communication Services:</strong> SMS and email service providers
              </li>
              <li>
                <strong>Cloud Storage:</strong> Secure data hosting and backup services
              </li>
              <li>
                <strong>Analytics:</strong> Website performance and user experience tools
              </li>
              <li>
                <strong>Legal Services:</strong> Attorneys and accountants (when necessary)
              </li>
            </ul>
            <h3>3.3 Legal Requirements</h3>
            <p>We may disclose your information when required by law or to:</p>
            <ul>
              <li>Comply with court orders, subpoenas, or government requests</li>
              <li>Protect our rights, property, or safety</li>
              <li>Investigate potential fraud or security breaches</li>
              <li>Enforce our Terms & Conditions</li>
            </ul>
            <h3>3.4 Business Transfers</h3>
            <p>
              In the event of a merger, acquisition, or sale of assets, your information may be
              transferred to the new entity, with continued protection under this Privacy Policy.
            </p>
          </section>
          <section className="privacy-section">
            <h2>4. Data Security</h2>
            <h3>4.1 Security Measures</h3>
            <p>We implement industry-standard security measures to protect your information:</p>
            <ul>
              <li>
                <strong>Encryption:</strong> All sensitive data is encrypted in transit and at rest
              </li>
              <li>
                <strong>Secure Payment Processing:</strong> PCI DSS compliant payment handling
                through Stripe
              </li>
              <li>
                <strong>Access Controls:</strong> Limited employee access on a need-to-know basis
              </li>
              <li>
                <strong>Regular Security Audits:</strong> Ongoing monitoring and vulnerability
                assessments
              </li>
              <li>
                <strong>Secure Communication:</strong> Protected SMS and email transmission
              </li>
            </ul>
            <h3>4.2 Data Breach Response</h3>
            <p>In the unlikely event of a data security incident, we will:</p>
            <ul>
              <li>Immediately investigate and contain the breach</li>
              <li>Notify affected customers within 72 hours</li>
              <li>Report to relevant authorities as required by law</li>
              <li>Take corrective actions to prevent future incidents</li>
              <li>Provide credit monitoring services if sensitive data is compromised</li>
            </ul>
          </section>
          <section className="privacy-section">
            <h2>5. Your Privacy Rights</h2>
            <h3>5.1 Access and Correction</h3>
            <ul>
              <li>
                <strong>View Your Data:</strong> Request a copy of all personal information we have
                about you
              </li>
              <li>
                <strong>Update Information:</strong> Correct or update your contact and event
                details
              </li>
              <li>
                <strong>Data Portability:</strong> Receive your data in a commonly used format
              </li>
            </ul>
            <h3>5.2 Communication Preferences</h3>
            <ul>
              <li>
                <strong>Email Opt-Out:</strong> Unsubscribe from promotional emails at any time by
                clicking the {'"Unsubscribe"'} link in any marketing email, or use our{' '}
                <Link href="/contact">contact form</Link>
              </li>
              <li>
                <strong>SMS Opt-Out:</strong> Text <code>STOP</code> to discontinue SMS messages
              </li>
              <li>
                <strong>One-Click Unsubscribe:</strong> All marketing emails include a direct
                unsubscribe link for instant removal from our mailing list (CAN-SPAM compliant)
              </li>
              <li>
                <strong>Marketing Controls:</strong> Choose which types of promotional content you
                receive
              </li>
              <li>
                <strong>Frequency Management:</strong> Adjust how often you hear from us
              </li>
            </ul>
            <h3>5.3 Data Deletion</h3>
            <ul>
              <li>
                <strong>Account Deletion:</strong> Request complete removal of your personal
                information
              </li>
              <li>
                <strong>Selective Deletion:</strong> Remove specific data points or communication
                records
              </li>
              <li>
                <strong>Retention Limits:</strong> We automatically delete old data according to our
                retention policy
              </li>
            </ul>
            <h3>5.4 California Privacy Rights (CCPA)</h3>
            <p>
              California residents have additional rights under the California Consumer Privacy Act:
            </p>
            <ul>
              <li>Right to know what personal information is collected and how it&apos;s used</li>
              <li>Right to delete personal information (with certain exceptions)</li>
              <li>
                Right to opt-out of the sale of personal information (we don&apos;t sell data)
              </li>
              <li>Right to non-discrimination for exercising privacy rights</li>
            </ul>
          </section>
          <section className="privacy-section">
            <h2>6. Data Retention</h2>
            <h3>6.1 Retention Periods</h3>
            <ul>
              <li>
                <strong>Active Customers:</strong> Information retained while you&apos;re an active
                customer
              </li>
              <li>
                <strong>Booking Records:</strong> 7 years for tax and business record purposes
              </li>
              <li>
                <strong>Payment Information:</strong> Minimal retention as required by payment
                processors
              </li>
              <li>
                <strong>Communication Records:</strong> 3 years for customer service quality
              </li>
              <li>
                <strong>Marketing Data:</strong> Until you opt-out or request deletion
              </li>
            </ul>
            <h3>6.2 Automatic Deletion</h3>
            <p>
              We automatically delete or anonymize personal information when it&apos;s no longer
              needed for business purposes, legal compliance, or legitimate interests.
            </p>
          </section>
          <section className="privacy-section">
            <h2>7. Cookies and Tracking</h2>
            <h3>7.1 Types of Cookies</h3>
            <ul>
              <li>
                <strong>Essential Cookies:</strong> Required for website functionality and security
              </li>
              <li>
                <strong>Analytics Cookies:</strong> Help us understand how visitors use our website
              </li>
              <li>
                <strong>Preference Cookies:</strong> Remember your settings and preferences
              </li>
              <li>
                <strong>Marketing Cookies:</strong> Used to show relevant advertisements (with
                consent)
              </li>
            </ul>
            <h3>7.2 Cookie Management</h3>
            <p>
              You can control cookies through your browser settings. Note that disabling essential
              cookies may affect website functionality.
            </p>
          </section>
          <section className="privacy-section">
            <h2>8. Third-Party Links</h2>
            <p>
              Our website may contain links to third-party websites or services. We are not
              responsible for the privacy practices of these external sites. We encourage you to
              read their privacy policies before providing any personal information.
            </p>
          </section>
          <section className="privacy-section">
            <h2>9. Children&apos;s Privacy</h2>
            <p>
              Our services are not directed to children under 13. We do not knowingly collect
              personal information from children under 13. If we learn that we have collected such
              information, we will delete it immediately.
            </p>
          </section>
          <section className="privacy-section">
            <h2>10. International Data Transfers</h2>
            <p>
              Your information may be processed and stored in the United States. By using our
              services, you consent to the transfer of your information to the U.S., where privacy
              laws may differ from your jurisdiction.
            </p>
          </section>
          <section className="privacy-section">
            <h2>11. Privacy Policy Updates</h2>
            <p>
              We may update this Privacy Policy from time to time. We will notify you of material
              changes through:
            </p>
            <ul>
              <li>Email notification to registered customers</li>
              <li>SMS notification (if you&apos;ve opted in)</li>
              <li>Website banner on our homepage</li>
              <li>Updated &quot;Last Modified&quot; date at the top of this page</li>
            </ul>
            <p>
              Your continued use of our services after changes become effective indicates acceptance
              of the updated Privacy Policy.
            </p>
          </section>
          <section className="privacy-section contact-section">
            <h2>12. Contact Us About Privacy</h2>
            <div className="privacy-contact">
              <h3>Privacy Officer</h3>
              <p>
                <strong>my Hibachi LLC</strong>
              </p>
              <h4>For Privacy-Related Inquiries:</h4>
              <p>
                <strong>Email:</strong>{' '}
                <ProtectedEmail showIcon={false} text="Privacy Contact Form" />
              </p>
              <p>
                <strong>Phone:</strong> <ProtectedPhone showIcon={false} />
              </p>
              <p>
                <strong>Response Time:</strong> We respond to privacy requests within 30 days
              </p>
              <h4>Service Areas (Data Processing Locations):</h4>
              <ul>
                <li>Sacramento Metro Area</li>
                <li>San Francisco Bay Area</li>
                <li>Central Valley Region</li>
              </ul>
              <h4>Business Hours:</h4>
              <p>Monday - Sunday: 12:00 PM - 9:00 PM PST</p>
              <div className="gdpr-notice">
                <h4>EU/UK Residents:</h4>
                <p>
                  If you are located in the European Union or United Kingdom, you may have
                  additional rights under GDPR. Contact us at the above information for assistance
                  with GDPR-related requests.
                </p>
              </div>
            </div>
          </section>
          <section className="privacy-section">
            <div className="policy-links">
              <p>
                <strong>Related Information:</strong>
              </p>
              <ul>
                <li>
                  <Link href="/terms">Terms & Conditions</Link>
                </li>
                <li>
                  <Link href="/contact">Contact Us</Link>
                </li>
                <li>
                  <Link href="/quote">Request a Quote</Link>
                </li>
                <li>
                  <Link href="/book-us/">Book Our Services</Link>
                </li>
              </ul>
            </div>
          </section>
          <section className="privacy-section">
            <div className="privacy-commitment">
              <p>
                <strong>
                  Our Commitment: We are dedicated to protecting your privacy and will continue to
                  implement best practices as technology and regulations evolve. Your trust is
                  essential to our business.
                </strong>
              </p>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
