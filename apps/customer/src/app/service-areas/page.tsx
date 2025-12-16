'use client';

// Service areas uses menu styling
import '@/styles/menu.css';
import '@/styles/menu/menu-features.css';
import '@/styles/menu/menu-pricing.css';
import '@/styles/menu/menu-base.css';
import '@/styles/menu/base.css';
import '@/styles/pages/menu.page.css';

import { Calculator, Calendar, MessageCircle } from 'lucide-react';
import Link from 'next/link';

export default function ServiceAreasPage() {
  return (
    <main data-page="menu">
      <div className="menu-container">
        <div className="container-fluid px-lg-5">
          {/* Hero Section - Ultra Compact */}
          <div className="hero-section hero-compact page-hero-background mb-3 text-center">
            <div className="hero-content">
              <div className="hero-icon">🗺️</div>

              <h1 className="fw-bold">
                <span className="gradient-text">Our Service Areas</span>
              </h1>

              <p className="hero-subtitle">
                We bring the hibachi experience directly to your location
              </p>
            </div>
          </div>

          {/* Service Areas Content */}
          <div className="card menu-card mb-3 overflow-hidden border-0 p-0">
            <div className="service-areas p-3">
              <p className="service-intro text-center text-sm">
                We bring authentic hibachi dining to homes and venues across the Bay Area,
                Sacramento, San Jose & surrounding regions. Not sure we cover you? Reach
                out—we&apos;ll do our best!
              </p>

              <div className="mt-2 mb-3 text-center">
                <Link href="/BookUs" className="btn btn-primary btn-sm me-2">
                  <Calendar className="me-1 inline h-4 w-4" />
                  Plan Your Date
                </Link>
                <Link href="/quote" className="btn btn-outline-primary btn-sm me-2">
                  <Calculator className="me-1 inline h-4 w-4" />
                  Get Quote
                </Link>
                <Link href="/contact" className="btn btn-outline-secondary btn-sm">
                  <MessageCircle className="me-1 inline h-4 w-4" />
                  Contact Us
                </Link>
              </div>

              <div className="mt-3 grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <div className="service-area-card">
                    <h4 className="area-title">🌉 Bay Area & Peninsula</h4>
                    <p className="area-subtitle">Our primary service area with premium coverage!</p>
                    <ul className="area-list">
                      <li>San Francisco - The heart of culinary excellence</li>
                      <li>San Jose - Silicon Valley&apos;s finest hibachi</li>
                      <li>Oakland - East Bay entertainment at its best</li>
                      <li>Santa Clara - Tech meets traditional Japanese cuisine</li>
                      <li>Sunnyvale - Where innovation meets flavor</li>
                      <li>Mountain View - Bringing mountains of flavor</li>
                      <li>Palo Alto - Stanford-level culinary performance</li>
                    </ul>
                  </div>
                </div>
                <div>
                  <div className="service-area-card">
                    <h4 className="area-title">🏞️ Sacramento & Extended Regions</h4>
                    <p className="area-subtitle">
                      Minimal travel fees for these beautiful locations!
                    </p>
                    <ul className="area-list">
                      <li>Sacramento - Capital city hibachi experiences</li>
                      <li>Elk Grove - Family-friendly neighborhood service</li>
                      <li>Roseville - Elegant dining in wine country vicinity</li>
                      <li>Folsom - Historic charm meets modern hibachi</li>
                      <li>Davis - University town celebrations</li>
                      <li>Stockton - Central Valley&apos;s premier hibachi</li>
                      <li>Modesto - Agricultural heart, culinary soul</li>
                      <li>Livermore - Wine country hibachi perfection</li>
                    </ul>
                  </div>
                </div>
              </div>

              <div className="service-radius-info mt-3 text-center">
                <div className="radius-card">
                  <span className="radius-icon"> 🚗 </span>
                  <h4 className="radius-title">We Come to You!</h4>
                  <p className="radius-description text-sm">
                    Serving the Bay Area, Sacramento, San Jose & surrounding regions.
                  </p>
                  <p className="travel-fee-info text-sm" style={{ color: 'white' }}>
                    <span className="travel-highlight">💰 Transparent Pricing:</span>
                    Flexible service area with transparent travel options!
                  </p>
                  <div className="service-promise">
                    <span className="promise-icon">🎯</span>
                    <span className="promise-text text-sm">
                      <strong>Our Promise:</strong> No hidden fees, just honest pricing!
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* CTA Section - Compact */}
          <div className="card menu-card mb-3 overflow-hidden border-0 p-0">
            <div className="cta-section p-3 text-center">
              <div className="cta-content-wrapper">
                <div className="cta-background-pattern"></div>
                <div className="cta-header mb-3">
                  <div className="cta-icon-group mb-2">
                    <span className="cta-icon emoji-visible floating-cta-icon">🍽️</span>
                    <span className="cta-icon emoji-visible floating-cta-icon">🎉</span>
                    <span className="cta-icon emoji-visible floating-cta-icon">👨‍🍳</span>
                  </div>
                  <h2 className="cta-main-title" style={{ fontSize: '1.5rem' }}>
                    Ready for an Unforgettable Experience?
                  </h2>
                  <p className="cta-main-subtitle text-sm">
                    Book your premium hibachi experience today
                  </p>
                </div>

                <div className="cta-button-wrapper mb-3">
                  <Link
                    href="/BookUs"
                    aria-label="Order your hibachi experience now"
                    className="cta-link"
                  >
                    <button
                      className="cta-main-button modern-cta-button"
                      style={{ padding: '0.75rem 1.5rem' }}
                    >
                      <span className="button-icon emoji-visible">🍽️</span>
                      <span className="button-text">Order Your Hibachi Experience</span>
                      <span className="button-icon emoji-visible">🍽️</span>
                      <div className="button-shimmer"></div>
                    </button>
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
