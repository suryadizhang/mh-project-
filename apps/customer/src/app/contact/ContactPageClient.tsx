'use client';

import { useState } from 'react';
import { logger } from '@/lib/logger';
import { useProtectedPhone } from '@/components/ui/ProtectedPhone';
import { SITE_CONFIG } from '@/lib/seo-config';
import ContactForm from '@/components/contact/ContactForm';
import {
  MessageCircle,
  Instagram,
  Heart,
  Trophy,
  Sparkles,
  MapPin,
  Mail,
  MessageSquare,
  Clock,
  Star,
  CalendarCheck,
  Phone,
  Facebook,
  Send,
  ChevronDown,
} from 'lucide-react';

// Type definitions
declare global {
  interface Window {
    FB?: {
      init: (config: { xfbml: boolean; version: string }) => void;
      CustomerChat: {
        show: () => void;
        hide: () => void;
      };
    };
    dataLayer?: unknown[];
    opera?: string;
  }
}

// Inline Chat Button Components
function InlineMessengerButton() {
  const handleMessengerClick = () => {
    try {
      // GTM tracking
      if (typeof window !== 'undefined' && window.dataLayer) {
        window.dataLayer.push({ event: 'chat_open', channel: 'messenger' });
      }

      // Try to show Facebook Customer Chat if available
      if (typeof window !== 'undefined' && window.FB?.CustomerChat?.show) {
        window.FB.CustomerChat.show();
        logger.debug('Facebook Customer Chat opened');
      } else {
        // Fallback: Open Messenger directly using centralized config
        logger.debug('Opening Messenger directly', { url: SITE_CONFIG.social.facebookMessenger });
        window.open(SITE_CONFIG.social.facebookMessenger, '_blank', 'noopener,noreferrer');
      }
    } catch (error) {
      logger.warn('Error opening Messenger', { error });
      // Final fallback
      window.open(SITE_CONFIG.social.facebookMessenger, '_blank', 'noopener,noreferrer');
    }
  };

  return (
    <button
      onClick={handleMessengerClick}
      className="social-link facebook-link messenger-chat-button"
      style={{ cursor: 'pointer', border: 'none', background: 'none', padding: 0, width: '100%' }}
    >
      <MessageCircle className="social-icon h-6 w-6" />
      <div>
        <strong>💬 Chat on Messenger</strong>
        <small>Instant messaging with our team</small>
      </div>
    </button>
  );
}

function InlineInstagramButton() {
  const handleInstagramClick = () => {
    try {
      // GTM tracking
      if (typeof window !== 'undefined' && window.dataLayer) {
        window.dataLayer.push({ event: 'chat_open', channel: 'instagram' });
      }

      // Mobile app detection and opening
      const userAgent = navigator.userAgent || navigator.vendor || window.opera || '';
      const isMobile = /android|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(
        userAgent.toLowerCase(),
      );

      if (isMobile) {
        // Try to open Instagram app first with the ig.me URL (works best on mobile)
        logger.debug('Opening Instagram DM (mobile)', { url: SITE_CONFIG.social.instagramDm });

        // Try Instagram app deep link first
        const iframe = document.createElement('iframe');
        iframe.style.display = 'none';
        iframe.src = `instagram://user?username=${SITE_CONFIG.social.instagramHandle}`;
        document.body.appendChild(iframe);

        setTimeout(() => {
          document.body.removeChild(iframe);
          // Fallback to ig.me which works on both app and web
          window.open(SITE_CONFIG.social.instagramDm, '_blank', 'noopener,noreferrer');
        }, 1000);
      } else {
        // Desktop - use ig.me URL which redirects properly
        logger.debug('Opening Instagram DM (desktop)', { url: SITE_CONFIG.social.instagramDm });
        window.open(SITE_CONFIG.social.instagramDm, '_blank', 'noopener,noreferrer');
      }
    } catch (error) {
      logger.warn('Error opening Instagram', { error });
      // Ultimate fallback to profile page
      window.open(SITE_CONFIG.social.instagram, '_blank', 'noopener,noreferrer');
    }
  };

  return (
    <button
      onClick={handleInstagramClick}
      className="social-link instagram-link instagram-chat-button"
      style={{ cursor: 'pointer', border: 'none', background: 'none', padding: 0, width: '100%' }}
    >
      <Instagram className="social-icon h-6 w-6" />
      <div>
        <strong>📸 DM on Instagram</strong>
        <small>Message @{SITE_CONFIG.social.instagramHandle} directly</small>
      </div>
    </button>
  );
}

export default function ContactPageClient() {
  // Use protected phone hook for anti-scraping
  const { tel } = useProtectedPhone();
  const [isFormExpanded, setIsFormExpanded] = useState(false);

  return (
    <div className="contact-page">
      {/* Hero Section */}
      <div className="contact-hero page-hero-background">
        <div className="hero-content">
          <div className="animated-hero-icons">
            <span className="hero-icon-floating">🎉</span>
            <span className="hero-icon-floating">🔥</span>
            <span className="hero-icon-floating">👨‍🍳</span>
            <span className="hero-icon-floating">🍽️</span>
          </div>
          <h1 className="hero-title">
            <Heart className="heart-icon pulse-animation mr-2 inline-block h-8 w-8 fill-current text-red-500" />
            <span className="gradient-text">Book Your Hibachi Experience</span>
          </h1>
          <p className="hero-subtitle">
            <span className="highlight-text">Elevate Your Celebration</span> with a spectacular
            culinary journey! Our master hibachi chefs bring{' '}
            <span className="highlight-text">restaurant-quality dining</span> and
            <span className="highlight-text">unforgettable entertainment</span> directly to your
            venue!
          </p>
          <div className="hero-features">
            <div className="feature-badge">
              <Trophy className="feature-icon h-5 w-5" />
              <span>Premium Experience</span>
            </div>
            <div className="feature-badge">
              <Sparkles className="feature-icon h-5 w-5" />
              <span>Master Chefs</span>
            </div>
            <div className="feature-badge">
              <MapPin className="feature-icon h-5 w-5" />
              <span>We Come To You</span>
            </div>
          </div>
        </div>
      </div>

      <div className="contact-container container mx-auto px-4">
        {/* Main Contact Section */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2" id="contact-details">
          {/* Contact Information Card */}
          <div className="mb-4">
            <div className="card contact-card h-100">
              <div className="card-body">
                <h3 className="card-title">
                  <Mail className="title-icon mr-2 inline-block h-6 w-6" />
                  Professional Booking Services
                </h3>

                <div className="contact-info-list">
                  <div className="contact-item">
                    <Mail className="contact-icon h-5 w-5" />
                    <div className="contact-details">
                      <h5>Professional Booking</h5>
                      <a href={`mailto:${SITE_CONFIG.contact.email}`} className="contact-link">
                        {SITE_CONFIG.contact.email}
                      </a>
                      <p className="contact-note">
                        Premium service bookings, custom quotes, and expert consultation
                      </p>
                    </div>
                  </div>

                  <div className="contact-item">
                    <MessageSquare className="contact-icon h-5 w-5" />
                    <div className="contact-details">
                      <h5>Instant Response</h5>
                      <a href={`sms:${SITE_CONFIG.contact.phoneTel}`} className="contact-link">
                        {SITE_CONFIG.contact.phone}
                      </a>
                      <p className="contact-note">
                        Text for immediate assistance, scheduled calls available
                      </p>
                    </div>
                  </div>

                  <div className="contact-item">
                    <Clock className="contact-icon h-5 w-5" />
                    <div className="contact-details">
                      <h5>Rapid Response Guarantee</h5>
                      <p className="contact-link">Within 1-2 hours</p>
                      <p className="contact-note">
                        Professional team standing by! Email or social media DM for fastest response
                      </p>
                    </div>
                  </div>

                  <div className="contact-item">
                    <MapPin className="contact-icon h-5 w-5" />
                    <div className="contact-details">
                      <h5>Service Coverage</h5>
                      <p className="contact-link">
                        We come to you across the Bay Area, Sacramento, San Jose, and nearby
                        communities—just ask!
                      </p>
                      <p className="contact-note">
                        Premium mobile hibachi service delivered to your location!
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Reviews & Social Media Card */}
          <div className="mb-4">
            <div className="card contact-card h-100">
              <div className="card-body">
                <h3 className="card-title">
                  <Star className="title-icon mr-2 inline-block h-6 w-6 fill-current text-yellow-500" />
                  Client Reviews & Community
                </h3>

                {/* Review Platforms */}
                <div className="review-section">
                  <h5 className="section-subtitle">
                    ⭐ Share Your Experience & Help Others Discover Excellence!
                  </h5>
                  <p className="review-incentive">
                    Your testimonials inspire confidence in future clients and help us maintain our
                    commitment to exceptional service. We value every review! 🙏
                  </p>
                  <div className="review-buttons">
                    <a
                      href={SITE_CONFIG.social.yelp}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="review-button yelp-button"
                    >
                      <span className="review-icon text-xl font-bold text-red-500">Y!</span>
                      <div className="review-content">
                        <strong>Share Your Hibachi Experience</strong>
                        <small>Help others discover our service!</small>
                      </div>
                      <div className="review-badge">⭐ 5.0 Stars</div>
                    </a>

                    <a
                      href={SITE_CONFIG.social.google}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="review-button google-button"
                    >
                      <span className="review-icon text-xl font-bold text-blue-500">G</span>
                      <div className="review-content">
                        <strong>Google Business Review</strong>
                        <small>Boost our visibility to new clients!</small>
                      </div>
                      <div className="review-badge">⭐ 5.0 Stars</div>
                    </a>
                  </div>

                  <div className="review-stats">
                    <div className="stat-item">
                      <span className="stat-number">⭐⭐⭐⭐⭐</span>
                      <span className="stat-label">Five Star Service</span>
                    </div>
                  </div>
                </div>

                {/* Social Media */}
                <div className="social-section">
                  <h5 className="section-subtitle">🔗 Connect With Our Community</h5>
                  <div className="social-links">
                    <a
                      href={SITE_CONFIG.social.instagram}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="social-link instagram-link"
                    >
                      <Instagram className="social-icon h-6 w-6" />
                      <div>
                        <strong>@{SITE_CONFIG.social.instagramHandle}</strong>
                        <small>Exclusive content & culinary inspiration</small>
                      </div>
                    </a>

                    <a
                      href={SITE_CONFIG.social.facebook}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="social-link facebook-link"
                    >
                      <Facebook className="social-icon h-6 w-6" />
                      <div>
                        <strong>My Hibachi</strong>
                        <small>Event galleries & client testimonials</small>
                      </div>
                    </a>
                  </div>

                  {/* Chat Options Integration */}
                  <div className="chat-options-section mt-4">
                    <h6 className="chat-subtitle">💬 Instant Messaging</h6>
                    <div className="chat-buttons">
                      <InlineMessengerButton />
                      <InlineInstagramButton />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Email Contact Form Section - Collapsible */}
        <div className="collapsible-form-section" id="business-inquiries">
          <div className="mx-auto max-w-2xl">
            <button
              onClick={() => setIsFormExpanded(!isFormExpanded)}
              className={`collapsible-form-header w-full ${isFormExpanded ? 'expanded' : ''}`}
              aria-expanded={isFormExpanded}
              aria-controls="contact-form-content"
            >
              <div className="collapsible-form-title">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-r from-red-100 to-orange-100">
                  <Send className="h-6 w-6 text-red-600" />
                </div>
                <div className="text-left">
                  <h3>Send Us a Message</h3>
                  <p className="mt-0.5 text-sm text-gray-500">
                    Click to {isFormExpanded ? 'close' : 'open'} the contact form
                  </p>
                </div>
              </div>
              <div className={`collapsible-form-toggle ${isFormExpanded ? 'expanded' : ''}`}>
                <ChevronDown className="h-5 w-5" />
              </div>
            </button>
            <div
              id="contact-form-content"
              className={`collapsible-form-content ${isFormExpanded ? 'expanded' : ''}`}
            >
              <div className="collapsible-form-inner">
                <p className="mb-4 text-center text-gray-600">
                  Have a question or need a custom quote? Fill out the form below and we&apos;ll get
                  back to you quickly.
                </p>
                <ContactForm />
              </div>
            </div>
          </div>
        </div>

        {/* Booking Call-to-Action Section */}
        <div className="booking-cta-section compact-cta">
          <div className="card booking-cta-card">
            <div className="card-body text-center">
              <div className="cta-icon-container">
                <CalendarCheck className="cta-icon h-8 w-8" />
              </div>
              <h2 className="cta-title">Ready to Experience Hibachi Excellence?</h2>
              <p className="cta-text">
                Turn your next gathering into an unforgettable culinary event with our professional
                hibachi chefs.
              </p>
              <div className="cta-buttons flex flex-wrap justify-center gap-3">
                <a
                  href="#contact-details"
                  className="cta-btn-primary inline-flex transform items-center gap-2 rounded-full px-6 py-3 text-base font-bold shadow-lg transition-all duration-300 hover:-translate-y-1"
                >
                  <MessageSquare className="h-5 w-5" />
                  Get a Custom Quote
                </a>
                <a
                  href={tel ? `tel:${tel}` : '#'}
                  className="cta-btn-secondary inline-flex transform items-center gap-2 rounded-full px-6 py-3 text-base font-bold transition-all duration-300 hover:-translate-y-1"
                >
                  <Phone className="h-5 w-5" />
                  Call Us Now
                </a>
              </div>
            </div>
          </div>
        </div>

        {/* Reviews Link - Points to dedicated reviews page */}
        <div className="reviews-link-section py-4 text-center">
          <a
            href="/reviews"
            className="inline-flex items-center gap-2 font-semibold text-red-600 transition-colors hover:text-red-700"
          >
            <Star className="h-5 w-5 fill-current text-yellow-500" />
            <span>See What Our Clients Say</span>
            <span className="text-gray-400">→</span>
          </a>
        </div>
      </div>

      {/* Service Areas Link - Points to dedicated page */}
      <section className="service-areas-link-section bg-gray-50 py-4 text-center">
        <div className="container mx-auto px-4">
          <div className="flex flex-wrap items-center justify-center gap-4">
            <div className="flex items-center gap-2">
              <MapPin className="h-5 w-5 text-red-600" />
              <span className="text-gray-700">
                Serving Bay Area, Sacramento & Northern California
              </span>
            </div>
            <a
              href="/service-areas"
              className="inline-flex items-center gap-1 font-semibold text-red-600 transition-colors hover:text-red-700"
            >
              View All Service Areas →
            </a>
          </div>
        </div>
      </section>
    </div>
  );
}
