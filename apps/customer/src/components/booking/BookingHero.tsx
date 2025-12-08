'use client';

import React from 'react';

import { usePricing } from '@/hooks/usePricing';

export function BookingHero() {
  const { adultPrice, childPrice, isLoading } = usePricing();

  return (
    <div className="booking-hero page-hero-background mb-5 text-center">
      <div className="container">
        <div className="hero-content">
          <h1 className="hero-title mb-4">🎊 Book Your Hibachi Experience 🎊</h1>
          <p className="hero-subtitle mb-4">
            Schedule your unforgettable hibachi dinner with professional chef service, live
            entertainment, and premium ingredients delivered to your location.
          </p>

          <div className="hero-features">
            <div className="feature-item">
              <span className="feature-icon">🚚</span>
              <span className="feature-text">We Come to You</span>
            </div>
            <div className="feature-divider">•</div>
            <div className="feature-item">
              <span className="feature-icon">👨‍🍳</span>
              <span className="feature-text">Professional Chef</span>
            </div>
            <div className="feature-divider">•</div>
            <div className="feature-item">
              <span className="feature-icon">🎭</span>
              <span className="feature-text">Live Entertainment</span>
            </div>
          </div>

          <div className="pricing-highlight">
            <div className="pricing-card">
              <span className="pricing-label">Starting at</span>
              <span className="pricing-amount">{isLoading ? '...' : `$${adultPrice}`}</span>
              <span className="pricing-unit">per adult</span>
            </div>
            <div className="pricing-card">
              <span className="pricing-label">Children</span>
              <span className="pricing-amount">{isLoading ? '...' : `$${childPrice}`}</span>
              <span className="pricing-unit">ages 6-12</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
