import './styles/BookUsPageContainer.module.css';

import React from 'react';

import Assistant from '@/components/chat/Assistant';

import BookingFormContainer from './BookingFormContainer';
import BookUsHero from './BookUsHero';

interface BookUsPageContainerProps {
  className?: string;
}

const BookUsPageContainer: React.FC<BookUsPageContainerProps> = ({ className = '' }) => {
  return (
    <div className={`booking-page ${className}`}>
      <BookUsHero />
      <div className="container mx-auto px-4">
        <div className="flex justify-center">
          <div className="w-full lg:w-2/3">
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
