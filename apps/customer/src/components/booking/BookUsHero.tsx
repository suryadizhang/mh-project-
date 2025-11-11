import './styles/BookUsHero.module.css';

import { CalendarCheck, Clock, MapPin, Shield } from 'lucide-react';
import React from 'react';

interface BookUsHeroProps {
  className?: string;
}

const BookUsHero: React.FC<BookUsHeroProps> = ({ className = '' }) => {
  return (
    <section className={`booking-hero ${className}`}>
      <div className="container">
        <div className="hero-content text-center">
          <h1 className="hero-title">
            <CalendarCheck className="mr-3 inline-block" size={36} />
            Book Your Hibachi Experience
          </h1>
          <p className="hero-subtitle">
            Reserve your premium private hibachi chef service for an unforgettable culinary
            experience
          </p>
          <div className="hero-features">
            <div className="feature-item">
              <Shield className="feature-icon" size={24} />
              <span>100% Satisfaction Guaranteed</span>
            </div>
            <div className="feature-item">
              <Clock className="feature-icon" size={24} />
              <span>Flexible Scheduling</span>
            </div>
            <div className="feature-item">
              <MapPin className="feature-icon" size={24} />
              <span>We Come To You</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default BookUsHero;
