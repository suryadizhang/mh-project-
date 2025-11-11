'use client';

import { ChevronLeft, ChevronRight, Quote, Star } from 'lucide-react';
import { useEffect, useState } from 'react';

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
  const { trackPageEngagement } = useAnalytics();

  // Auto-rotate testimonials
  useEffect(() => {
    if (!isAutoPlaying) return;

    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % testimonials.length);
    }, 5000); // Change every 5 seconds

    return () => clearInterval(interval);
  }, [isAutoPlaying]);

  const nextTestimonial = () => {
    setCurrentIndex((prev) => (prev + 1) % testimonials.length);
    setIsAutoPlaying(false);
  };

  const prevTestimonial = () => {
    setCurrentIndex((prev) => (prev - 1 + testimonials.length) % testimonials.length);
    setIsAutoPlaying(false);
  };

  const goToTestimonial = (index: number) => {
    setCurrentIndex(index);
    setIsAutoPlaying(false);
  };

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

        {/* Main Testimonial Display */}
        <div className="relative">
          <div className="relative overflow-hidden rounded-2xl bg-white p-8 shadow-xl md:p-12">
            {/* Background Quote Icon */}
            <Quote className="absolute top-6 right-6 h-16 w-16 text-red-100 opacity-50" />

            {/* Testimonial Content */}
            <div className="relative z-10">
              {/* Rating Stars */}
              <div className="mb-6 flex justify-center">
                {[...Array(currentTestimonial.rating)].map((_, i) => (
                  <Star key={i} className="mx-1 h-6 w-6 fill-yellow-400 text-yellow-400" />
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
                  <div className="flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-r from-red-500 to-orange-500 text-xl font-bold text-white">
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

          {/* Navigation Arrows */}
          <button
            onClick={prevTestimonial}
            className="absolute top-1/2 left-4 z-10 -translate-y-1/2 rounded-full bg-white p-3 shadow-lg transition-colors hover:bg-gray-50"
            aria-label="Previous testimonial"
          >
            <ChevronLeft className="h-6 w-6 text-gray-600" />
          </button>

          <button
            onClick={nextTestimonial}
            className="absolute top-1/2 right-4 z-10 -translate-y-1/2 rounded-full bg-white p-3 shadow-lg transition-colors hover:bg-gray-50"
            aria-label="Next testimonial"
          >
            <ChevronRight className="h-6 w-6 text-gray-600" />
          </button>
        </div>

        {/* Dot Indicators */}
        <div className="mt-8 flex justify-center gap-2">
          {testimonials.map((_, index) => (
            <button
              key={index}
              onClick={() => goToTestimonial(index)}
              className={`h-3 w-3 rounded-full transition-all duration-300 ${
                index === currentIndex ? 'scale-125 bg-red-500' : 'bg-gray-300 hover:bg-gray-400'
              }`}
              aria-label={`Go to testimonial ${index + 1}`}
            />
          ))}
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
