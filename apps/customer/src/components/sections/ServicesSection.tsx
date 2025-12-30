'use client';

import { Building, CalendarCheck, CalendarDays, CheckCircle, Sparkles } from 'lucide-react';
import Link from 'next/link';

/**
 * ServicesSection - Premium Services for Every Occasion
 *
 * This component is lazy-loaded to reduce initial JavaScript bundle.
 * It contains lucide-react icons which add ~50KB to the bundle.
 *
 * By lazy-loading this section (which appears below the fold),
 * we improve LCP and reduce unused JavaScript on initial load.
 */
export default function ServicesSection() {
  return (
    <section className="services-section">
      <div className="container">
        <h2 className="services-heading text-center">
          <span className="service-icon">🍽️</span> Premium Services for Every Occasion{' '}
          <span className="service-icon">🎪</span>
        </h2>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          <div className="mb-4">
            <div className="service-card">
              <div className="service-icon-wrapper">
                <CalendarDays className="h-10 w-10 text-white" />
              </div>
              <h3 className="service-title">Private Events</h3>
              <p className="service-description">
                Transform your special occasions into extraordinary experiences with our premium
                hibachi service. Perfect for birthdays, anniversaries, family gatherings and
                celebrations of all sizes.
              </p>
              <div className="service-features">
                <span className="service-feature">
                  <CheckCircle className="mr-1 inline-block h-4 w-4 text-red-600" /> Professional
                  chef service
                </span>
                <span className="service-feature">
                  <CheckCircle className="mr-1 inline-block h-4 w-4 text-red-600" /> Custom menu
                  options
                </span>
                <span className="service-feature">
                  <CheckCircle className="mr-1 inline-block h-4 w-4 text-red-600" /> Personalized
                  entertainment
                </span>
              </div>
            </div>
          </div>

          <div className="mb-4">
            <div className="service-card">
              <div className="service-icon-wrapper">
                <Building className="h-10 w-10 text-white" />
              </div>
              <h3 className="service-title">Corporate Events</h3>
              <p className="service-description">
                Impress your team or clients with a unique dining experience at your office or
                chosen venue. Our professional service adds flair to any corporate gathering or team
                celebration.
              </p>
              <div className="service-features">
                <span className="service-feature">
                  <CheckCircle className="mr-1 inline-block h-4 w-4 text-red-600" /> Professional
                  presentation
                </span>
                <span className="service-feature">
                  <CheckCircle className="mr-1 inline-block h-4 w-4 text-red-600" /> Flexible
                  scheduling
                </span>
                <span className="service-feature">
                  <CheckCircle className="mr-1 inline-block h-4 w-4 text-red-600" /> Volume
                  discounts available
                </span>
              </div>
            </div>
          </div>

          <div className="mb-4">
            <div className="service-card">
              <div className="service-icon-wrapper">
                <Sparkles className="h-10 w-10 text-white" />
              </div>
              <h3 className="service-title">Premium Experience</h3>
              <p className="service-description">
                We offer customizable menus tailored to your preferences and dietary needs. From
                classic hibachi favorites to premium upgrades, we create a perfect menu for your
                event.
              </p>
              <div className="service-features">
                <span className="service-feature">
                  <CheckCircle className="mr-1 inline-block h-4 w-4 text-red-600" /> Dietary
                  accommodations
                </span>
                <span className="service-feature">
                  <CheckCircle className="mr-1 inline-block h-4 w-4 text-red-600" /> Premium
                  ingredient options
                </span>
                <span className="service-feature">
                  <CheckCircle className="mr-1 inline-block h-4 w-4 text-red-600" /> Signature
                  entertainment
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="services-cta mt-8 text-center">
          <Link href="/book-us/" className="btn-cta-primary btn-cta-shimmer">
            <CalendarCheck className="h-5 w-5" />
            <span>Book Your Premium Experience</span>
          </Link>
        </div>
      </div>
    </section>
  );
}
