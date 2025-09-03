'use client'

import { useState, useEffect } from 'react'
import { ChevronLeft, ChevronRight, Star, Quote } from 'lucide-react'
import { useAnalytics } from '@/components/analytics/GoogleAnalytics'

interface Testimonial {
  id: number
  name: string
  location: string
  event: string
  rating: number
  text: string
  date: string
  avatar?: string
}

const testimonials: Testimonial[] = [
  {
    id: 1,
    name: 'Sarah Johnson',
    location: 'Palo Alto, CA',
    event: 'Corporate Event',
    rating: 5,
    text: "My Hibachi Chef made our company retreat absolutely unforgettable! The interactive cooking experience had everyone engaged and the food was incredible. Chef's entertainment skills were top-notch. Highly recommend for any corporate event!",
    date: 'August 2025'
  },
  {
    id: 2,
    name: 'Mike Chen',
    location: 'Mountain View, CA',
    event: 'Birthday Party',
    rating: 5,
    text: 'Best birthday party ever! The chef was amazing with the kids and adults alike. The hibachi grill setup in our backyard was seamless and the cleanup was fantastic. Worth every penny for the memories we made!',
    date: 'July 2025'
  },
  {
    id: 3,
    name: 'Jennifer Lopez',
    location: 'San Jose, CA',
    event: 'Wedding Reception',
    rating: 5,
    text: 'Our wedding guests are still talking about the hibachi experience! It was unique, delicious, and so entertaining. The chef accommodated all our dietary restrictions perfectly. Made our special day even more memorable.',
    date: 'June 2025'
  },
  {
    id: 4,
    name: 'David Park',
    location: 'Fremont, CA',
    event: 'Family Reunion',
    rating: 5,
    text: 'Having hibachi at our family reunion was the perfect choice. Three generations all enjoyed the show and the food brought everyone together. The chef was professional and the experience was seamless from start to finish.',
    date: 'August 2025'
  },
  {
    id: 5,
    name: 'Lisa Rodriguez',
    location: 'Sacramento, CA',
    event: 'Graduation Party',
    rating: 5,
    text: "What an amazing way to celebrate our daughter's graduation! The hibachi chef turned our backyard into a restaurant-quality dining experience. All our guests were impressed and the graduate loved being the center of attention!",
    date: 'May 2025'
  },
  {
    id: 6,
    name: 'Tom Anderson',
    location: 'Oakland, CA',
    event: 'Anniversary Celebration',
    rating: 5,
    text: 'For our 25th anniversary, we wanted something special. The hibachi experience was intimate yet exciting, and the quality of food exceeded our expectations. The chef made us feel like VIPs in our own home!',
    date: 'July 2025'
  }
]

export default function TestimonialsSection() {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isAutoPlaying, setIsAutoPlaying] = useState(true)
  const { trackPageEngagement } = useAnalytics()

  // Auto-rotate testimonials
  useEffect(() => {
    if (!isAutoPlaying) return

    const interval = setInterval(() => {
      setCurrentIndex(prev => (prev + 1) % testimonials.length)
    }, 5000) // Change every 5 seconds

    return () => clearInterval(interval)
  }, [isAutoPlaying])

  const nextTestimonial = () => {
    setCurrentIndex(prev => (prev + 1) % testimonials.length)
    setIsAutoPlaying(false)
  }

  const prevTestimonial = () => {
    setCurrentIndex(prev => (prev - 1 + testimonials.length) % testimonials.length)
    setIsAutoPlaying(false)
  }

  const goToTestimonial = (index: number) => {
    setCurrentIndex(index)
    setIsAutoPlaying(false)
  }

  const currentTestimonial = testimonials[currentIndex]

  return (
    <section className="testimonials-section py-20 bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="container mx-auto px-4 max-w-6xl">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-800 mb-4">
            What Our Customers Say
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Don&apos;t just take our word for it. Here&apos;s what families and businesses across
            the Bay Area and Sacramento are saying about their hibachi experiences.
          </p>
          <div className="flex justify-center mt-6">
            <div className="flex items-center gap-2">
              {[...Array(5)].map((_, i) => (
                <Star key={i} className="w-6 h-6 fill-yellow-400 text-yellow-400" />
              ))}
              <span className="ml-2 text-lg font-semibold text-gray-700">
                5.0 from 200+ reviews
              </span>
            </div>
          </div>
        </div>

        {/* Main Testimonial Display */}
        <div className="relative">
          <div className="bg-white rounded-2xl shadow-xl p-8 md:p-12 relative overflow-hidden">
            {/* Background Quote Icon */}
            <Quote className="absolute top-6 right-6 w-16 h-16 text-red-100 opacity-50" />

            {/* Testimonial Content */}
            <div className="relative z-10">
              {/* Rating Stars */}
              <div className="flex justify-center mb-6">
                {[...Array(currentTestimonial.rating)].map((_, i) => (
                  <Star key={i} className="w-6 h-6 fill-yellow-400 text-yellow-400 mx-1" />
                ))}
              </div>

              {/* Testimonial Text */}
              <blockquote className="text-xl md:text-2xl text-gray-700 text-center mb-8 leading-relaxed font-medium">
                &ldquo;{currentTestimonial.text}&rdquo;
              </blockquote>

              {/* Customer Info */}
              <div className="text-center">
                <div className="flex flex-col items-center gap-2">
                  {/* Avatar placeholder */}
                  <div className="w-16 h-16 bg-gradient-to-r from-red-500 to-orange-500 rounded-full flex items-center justify-center text-white text-xl font-bold">
                    {currentTestimonial.name
                      .split(' ')
                      .map(n => n[0])
                      .join('')}
                  </div>

                  <div>
                    <h4 className="text-xl font-bold text-gray-800">{currentTestimonial.name}</h4>
                    <p className="text-gray-600">
                      {currentTestimonial.event} • {currentTestimonial.location}
                    </p>
                    <p className="text-sm text-gray-500 mt-1">{currentTestimonial.date}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Navigation Arrows */}
          <button
            onClick={prevTestimonial}
            className="absolute left-4 top-1/2 -translate-y-1/2 bg-white shadow-lg rounded-full p-3 hover:bg-gray-50 transition-colors z-10"
            aria-label="Previous testimonial"
          >
            <ChevronLeft className="w-6 h-6 text-gray-600" />
          </button>

          <button
            onClick={nextTestimonial}
            className="absolute right-4 top-1/2 -translate-y-1/2 bg-white shadow-lg rounded-full p-3 hover:bg-gray-50 transition-colors z-10"
            aria-label="Next testimonial"
          >
            <ChevronRight className="w-6 h-6 text-gray-600" />
          </button>
        </div>

        {/* Dot Indicators */}
        <div className="flex justify-center mt-8 gap-2">
          {testimonials.map((_, index) => (
            <button
              key={index}
              onClick={() => goToTestimonial(index)}
              className={`w-3 h-3 rounded-full transition-all duration-300 ${
                index === currentIndex ? 'bg-red-500 scale-125' : 'bg-gray-300 hover:bg-gray-400'
              }`}
              aria-label={`Go to testimonial ${index + 1}`}
            />
          ))}
        </div>

        {/* Trust Indicators */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
          <div className="p-6">
            <div className="text-4xl font-bold text-red-600 mb-2">200+</div>
            <div className="text-gray-600">Happy Customers</div>
          </div>
          <div className="p-6">
            <div className="text-4xl font-bold text-red-600 mb-2">500+</div>
            <div className="text-gray-600">Events Catered</div>
          </div>
          <div className="p-6">
            <div className="text-4xl font-bold text-red-600 mb-2">5★</div>
            <div className="text-gray-600">Average Rating</div>
          </div>
        </div>

        {/* CTA */}
        <div className="text-center mt-12">
          <h3 className="text-2xl font-bold text-gray-800 mb-4">
            Ready to Create Your Own Amazing Experience?
          </h3>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="/BookUs"
              className="inline-flex items-center justify-center px-8 py-3 bg-gradient-to-r from-red-600 to-red-700 text-white font-semibold rounded-lg hover:from-red-700 hover:to-red-800 transition-all transform hover:scale-105 shadow-lg"
              onClick={() => trackPageEngagement('click', 'testimonials_book_now_cta')}
            >
              Book Your Event Now
            </a>
            <a
              href="/quote"
              className="inline-flex items-center justify-center px-8 py-3 border-2 border-red-600 text-red-600 font-semibold rounded-lg hover:bg-red-50 transition-all"
              onClick={() => trackPageEngagement('click', 'testimonials_get_quote_cta')}
            >
              Get Your Quote
            </a>
          </div>
        </div>
      </div>
    </section>
  )
}
