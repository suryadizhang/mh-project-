import './styles/BookUsHero.module.css'

import React from 'react'

interface BookUsHeroProps {
  className?: string
}

const BookUsHero: React.FC<BookUsHeroProps> = ({ className = '' }) => {
  return (
    <section className={`booking-hero ${className}`}>
      <div className="container">
        <div className="hero-content text-center">
          <h1 className="hero-title">
            <i className="bi bi-calendar-check-fill me-3"></i>
            Book Your Hibachi Experience
          </h1>
          <p className="hero-subtitle">
            Reserve your premium private hibachi chef service for an unforgettable culinary
            experience
          </p>
          <div className="hero-features">
            <div className="feature-item">
              <i className="bi bi-shield-check feature-icon"></i>
              <span>100% Satisfaction Guaranteed</span>
            </div>
            <div className="feature-item">
              <i className="bi bi-clock feature-icon"></i>
              <span>Flexible Scheduling</span>
            </div>
            <div className="feature-item">
              <i className="bi bi-geo-alt feature-icon"></i>
              <span>We Come To You</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

export default BookUsHero
