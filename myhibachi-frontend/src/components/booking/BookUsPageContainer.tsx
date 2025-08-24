import React from 'react';
import BookUsHero from './BookUsHero';
import BookingFormContainer from './BookingFormContainer';
import Assistant from '@/components/chat/Assistant';
import './styles/BookUsPageContainer.module.css';

interface BookUsPageContainerProps {
  className?: string;
}

const BookUsPageContainer: React.FC<BookUsPageContainerProps> = ({ className = '' }) => {
  return (
    <div className={`booking-page ${className}`}>
      <BookUsHero />
      <div className="container">
        <div className="row justify-content-center">
          <div className="col-lg-8">
            <div className="booking-form-container">
              <BookingFormContainer />
            </div>
          </div>
        </div>
      </div>
      {/* Modals will be handled by the BookingFormContainer */}
      <Assistant />
    </div>
  );
};

export default BookUsPageContainer;

