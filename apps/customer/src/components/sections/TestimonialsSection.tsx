'use client';

import { ChevronLeft, ChevronRight, Quote, Star } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';

import { useAnalytics } from '@/components/analytics/GoogleAnalytics';

interface Testimonial {
  id: number;
  name: string;
  location: string;
  event: string;
  rating: number;
  text: string;
  date: string;
  avatar?: string;
}

const testimonials: Testimonial[] = [
  {
    id: 1,
    name: 'Sarah Johnson',
    location: 'Palo Alto, CA',
    event: 'Corporate Event',
    rating: 5,
    text: "My Hibachi Chef made our company retreat absolutely unforgettable! The interactive cooking experience had everyone engaged and the food was incredible. Chef's entertainment skills were top-notch. Highly recommend for any corporate event!",
    date: 'August 2025',
  },
  {
    id: 2,
    name: 'Mike Chen',
    location: 'Mountain View, CA',
    event: 'Birthday Party',
    rating: 5,
    text: 'Best birthday party ever! The chef was amazing with the kids and adults alike. The hibachi grill setup in our backyard was seamless and the cleanup was fantastic. Worth every penny for the memories we made!',
    date: 'July 2025',
  },
  {
    id: 3,
    name: 'Jennifer Lopez',
    location: 'San Jose, CA',
    event: 'Wedding Reception',
    rating: 5,
    text: 'Our wedding guests are still talking about the hibachi experience! It was unique, delicious, and so entertaining. The chef accommodated all our dietary restrictions perfectly. Made our special day even more memorable.',
    date: 'June 2025',
  },
  {
    id: 4,
    name: 'David Park',
    location: 'Fremont, CA',
    event: 'Family Reunion',
    rating: 5,
    text: 'Having hibachi at our family reunion was the perfect choice. Three generations all enjoyed the show and the food brought everyone together. The chef was professional and the experience was seamless from start to finish.',
    date: 'August 2025',
  },
  {
    id: 5,
    name: 'Lisa Rodriguez',
    location: 'Sacramento, CA',
    event: 'Graduation Party',
    rating: 5,
    text: "What an amazing way to celebrate our daughter's graduation! The hibachi chef turned our backyard into a restaurant-quality dining experience. All our guests were impressed and the graduate loved being the center of attention!",
    date: 'May 2025',
  },
  {
    id: 6,
    name: 'Tom Anderson',
    location: 'Oakland, CA',
    event: 'Anniversary Celebration',
    rating: 5,
    text: 'For our 25th anniversary, we wanted something special. The hibachi experience was intimate yet exciting, and the quality of food exceeded our expectations. The chef made us feel like VIPs in our own home!',
    date: 'July 2025',
  },
];

export default function TestimonialsSection() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(true);
  const [slideDirection, setSlideDirection] = useState<'left' | 'right'>('right');
  const { trackPageEngagement } = useAnalytics();

  // Touch handling state
  const touchStartX = useRef<number | null>(null);
  const touchEndX = useRef<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Minimum swipe distance (in px) to trigger navigation
  const minSwipeDistance = 50;

  // Auto-rotate testimonials
  useEffect(() => {
    if (!isAutoPlaying) return;

    const interval = setInterval(() => {
      setSlideDirection('right');
      setCurrentIndex((prev) => (prev + 1) % testimonials.length);
    }, 5000); // Change every 5 seconds

    return () => clearInterval(interval);
  }, [isAutoPlaying]);

  const nextTestimonial = useCallback(() => {
    setSlideDirection('right');
    setCurrentIndex((prev) => (prev + 1) % testimonials.length);
    setIsAutoPlaying(false);
  }, []);

  const prevTestimonial = useCallback(() => {
    setSlideDirection('left');
    setCurrentIndex((prev) => (prev - 1 + testimonials.length) % testimonials.length);
    setIsAutoPlaying(false);
  }, []);

  const goToTestimonial = (index: number) => {
    setSlideDirection(index > currentIndex ? 'right' : 'left');
    setCurrentIndex(index);
    setIsAutoPlaying(false);
  };

  // Touch handlers for swipe navigation
  const onTouchStart = (e: React.TouchEvent) => {
    touchEndX.current = null;
    touchStartX.current = e.targetTouches[0].clientX;
  };

  const onTouchMove = (e: React.TouchEvent) => {
    touchEndX.current = e.targetTouches[0].clientX;
  };

  const onTouchEnd = () => {
    if (!touchStartX.current || !touchEndX.current) return;

    const distance = touchStartX.current - touchEndX.current;
    const isLeftSwipe = distance > minSwipeDistance;
    const isRightSwipe = distance < -minSwipeDistance;

    if (isLeftSwipe) {
      nextTestimonial();
    } else if (isRightSwipe) {
      prevTestimonial();
    }

    // Reset values
    touchStartX.current = null;
    touchEndX.current = null;
  };

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft') {
        prevTestimonial();
      } else if (e.key === 'ArrowRight') {
        nextTestimonial();
      }
    };

    const container = containerRef.current;
    if (container) {
      container.addEventListener('keydown', handleKeyDown as unknown as EventListener);
    }

    return () => {
      if (container) {
        container.removeEventListener('keydown', handleKeyDown as unknown as EventListener);
      }
    };
  }, [nextTestimonial, prevTestimonial]);

  const currentTestimonial = testimonials[currentIndex];

  return (
    <section className="testimonials-section bg-gradient-to-br from-gray-50 to-gray-100 py-20">
      <div className="container mx-auto max-w-6xl px-4">
        {/* Section Header */}
        <div className="mb-16 text-center">
          <h2 className="mb-4 text-4xl font-bold text-gray-800 md:text-5xl">
            What Our Customers Say
          </h2>
          <p className="mx-auto max-w-3xl text-xl text-gray-600">
            Don&apos;t just take our word for it. Here&apos;s what families and businesses across
            the Bay Area and Sacramento are saying about their hibachi experiences.
          </p>
          <div className="mt-6 flex justify-center">
            <div className="flex items-center gap-2">
              {[...Array(5)].map((_, i) => (
                <Star key={i} className="h-6 w-6 fill-yellow-400 text-yellow-400" />
              ))}
              <span className="ml-2 text-lg font-semibold text-gray-700">
                5.0 from 200+ reviews
              </span>
            </div>
          </div>
        </div>

        {/* Main Testimonial Display with Touch Support */}
        <div
          ref={containerRef}
          className="relative"
          onTouchStart={onTouchStart}
          onTouchMove={onTouchMove}
          onTouchEnd={onTouchEnd}
          tabIndex={0}
          role="region"
          aria-label="Customer testimonials carousel"
          aria-roledescription="carousel"
        >
          {/* Swipe hint for mobile */}
          <div className="md:hidden text-center text-sm text-gray-500 mb-4">
            <span className="inline-flex items-center gap-1">
              <ChevronLeft className="w-4 h-4" />
              Swipe to navigate
              <ChevronRight className="w-4 h-4" />
            </span>
          </div>

          <div className="relative overflow-hidden rounded-2xl bg-white p-8 shadow-xl md:p-12">
            {/* Background Quote Icon */}
            <Quote className="absolute top-6 right-6 h-16 w-16 text-red-100 opacity-50" />

            {/* Testimonial Content with Animation */}
            <div
              className={`relative z-10 transition-all duration-500 ease-out ${slideDirection === 'right'
                  ? 'animate-in slide-in-from-right-4 fade-in'
                  : 'animate-in slide-in-from-left-4 fade-in'
                }`}
              key={currentIndex}
            >
              {/* Rating Stars */}
              <div className="mb-6 flex justify-center">
                {[...Array(currentTestimonial.rating)].map((_, i) => (
                  <Star key={i} className="mx-1 h-6 w-6 fill-yellow-400 text-yellow-400 transition-transform hover:scale-110" />
                ))}
              </div>

              {/* Testimonial Text */}
              <blockquote className="mb-8 text-center text-xl leading-relaxed font-medium text-gray-700 md:text-2xl">
                &ldquo;{currentTestimonial.text}&rdquo;
              </blockquote>

              {/* Customer Info */}
              <div className="text-center">
                <div className="flex flex-col items-center gap-2">
                  {/* Avatar placeholder */}
                  <div className="flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-r from-red-500 to-orange-500 text-xl font-bold text-white shadow-lg">
                    {currentTestimonial.name
                      .split(' ')
                      .map((n) => n[0])
                      .join('')}
                  </div>

                  <div>
                    <h4 className="text-xl font-bold text-gray-800">{currentTestimonial.name}</h4>
                    <p className="text-gray-600">
                      {currentTestimonial.event} • {currentTestimonial.location}
                    </p>
                    <p className="mt-1 text-sm text-gray-500">{currentTestimonial.date}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Enhanced Navigation Arrows - Hidden on mobile, visible on desktop */}
          <button
            onClick={prevTestimonial}
            className="absolute top-1/2 left-0 md:left-4 z-10 -translate-y-1/2 rounded-full bg-white p-3 md:p-4 shadow-lg transition-all duration-300 hover:bg-gray-50 hover:scale-110 hover:shadow-xl hidden md:flex items-center justify-center group"
            aria-label="Previous testimonial"
          >
            <ChevronLeft className="h-6 w-6 text-gray-600 group-hover:text-red-600 transition-colors" />
          </button>

          <button
            onClick={nextTestimonial}
            className="absolute top-1/2 right-0 md:right-4 z-10 -translate-y-1/2 rounded-full bg-white p-3 md:p-4 shadow-lg transition-all duration-300 hover:bg-gray-50 hover:scale-110 hover:shadow-xl hidden md:flex items-center justify-center group"
            aria-label="Next testimonial"
          >
            <ChevronRight className="h-6 w-6 text-gray-600 group-hover:text-red-600 transition-colors" />
          </button>
        </div>

        {/* Enhanced Dot Indicators with Progress */}
        <div className="mt-8 flex flex-col items-center gap-4">
          {/* Dot navigation */}
          <div className="flex justify-center gap-3">
            {testimonials.map((testimonial, index) => (
              <button
                key={index}
                onClick={() => goToTestimonial(index)}
                className={`relative h-3 rounded-full transition-all duration-500 ${index === currentIndex
                    ? 'w-8 bg-gradient-to-r from-red-500 to-orange-500'
                    : 'w-3 bg-gray-300 hover:bg-gray-400'
                  }`}
                aria-label={`Go to testimonial from ${testimonial.name}`}
                aria-current={index === currentIndex ? 'true' : 'false'}
              />
            ))}
          </div>

          {/* Counter */}
          <p className="text-sm text-gray-500">
            {currentIndex + 1} of {testimonials.length} reviews
          </p>

          {/* Auto-play toggle */}
          <button
            onClick={() => setIsAutoPlaying(!isAutoPlaying)}
            className={`text-sm px-4 py-1.5 rounded-full transition-all duration-300 ${isAutoPlaying
                ? 'bg-green-100 text-green-700 hover:bg-green-200'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
          >
            {isAutoPlaying ? '⏸ Auto-playing' : '▶ Resume auto-play'}
          </button>
        </div>

        {/* Trust Indicators */}
        <div className="mt-16 grid grid-cols-1 gap-8 text-center md:grid-cols-3">
          <div className="p-6">
            <div className="mb-2 text-4xl font-bold text-red-600">200+</div>
            <div className="text-gray-600">Happy Customers</div>
          </div>
          <div className="p-6">
            <div className="mb-2 text-4xl font-bold text-red-600">500+</div>
            <div className="text-gray-600">Events Catered</div>
          </div>
          <div className="p-6">
            <div className="mb-2 text-4xl font-bold text-red-600">5★</div>
            <div className="text-gray-600">Average Rating</div>
          </div>
        </div>

        {/* CTA */}
        <div className="mt-12 text-center">
          <h3 className="mb-4 text-2xl font-bold text-gray-800">
            Ready to Create Your Own Amazing Experience?
          </h3>
          <div className="flex flex-col justify-center gap-4 sm:flex-row">
            <a
              href="/BookUs"
              className="inline-flex transform items-center justify-center rounded-lg bg-gradient-to-r from-red-600 to-red-700 px-8 py-3 font-semibold text-white shadow-lg transition-all hover:scale-105 hover:from-red-700 hover:to-red-800"
              onClick={() => trackPageEngagement('click', 'testimonials_book_now_cta')}
            >
              Book Your Event Now
            </a>
            <a
              href="/quote"
              className="inline-flex items-center justify-center rounded-lg border-2 border-red-600 px-8 py-3 font-semibold text-red-600 transition-all hover:bg-red-50"
              onClick={() => trackPageEngagement('click', 'testimonials_get_quote_cta')}
            >
              Get Your Quote
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
