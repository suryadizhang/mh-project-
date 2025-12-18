// Server Component - NO 'use client' for faster initial render
import '@/styles/home.css';
import '@/styles/pages/home.page.css';

import { Building, CalendarCheck, CalendarDays, CheckCircle, Sparkles } from 'lucide-react';
import Link from 'next/link';

import { HeroImage } from '@/components/home/HeroImage';
import { HeroVideoOverlay } from '@/components/home/HeroVideoLazy';
import { ScrollAnimationProvider } from '@/components/home/ScrollAnimationProvider';
import { LazyValuePropositionSection } from '@/lib/performance/lazyComponents';

export default function Home() {
  return (
    <ScrollAnimationProvider>
      <main data-page="home">
        {/* Hero Video Section */}
        <section className="about-section" aria-label="Hero section with video background">
          {/* Hero Media Container */}
          <div className="hero-media-container">
            <div className="hero-media-overlay"></div>
            {/* Server-rendered image for instant LCP - no JS required */}
            <HeroImage />
            {/* Client component overlays video after hydration */}
            <HeroVideoOverlay />
          </div>

          <div className="mx-auto max-w-7xl px-4">
            {/* Animated Headline Section */}
            <div className="headline-section animate-on-scroll">
              <h1 className="main-title text-center">Experience the Art of Japanese Hibachi</h1>
              <p className="subtitle text-center">
                Where Culinary Mastery Meets Unforgettable Entertainment
              </p>
              <div className="text-center">
                <span className="quality-badge">
                  🌟 Premium Quality Ingredients • Reasonable Prices • Excellence is Our Priority 🌟
                </span>
              </div>
            </div>

            {/* Experience Sections */}
            <section
              aria-labelledby="experience-heading"
              className="experience-sections animate-on-scroll mb-8 grid grid-cols-1 gap-6 lg:grid-cols-2"
            >
              <h2 id="experience-heading" className="sr-only">
                Our Hibachi Experience
              </h2>
              <div className="mb-4">
                <div className="experience-card left-card chef-card">
                  <div className="experience-icon-wrapper chef-wrapper">
                    <span className="experience-icon rotating-chef">👨‍🍳</span>
                  </div>
                  <div className="experience-content">
                    <h3 className="experience-title">
                      <span className="title-emoji">⭐</span>
                      Meet Our Expert Chefs
                      <span className="title-emoji">⭐</span>
                    </h3>
                    <div className="experience-highlights">
                      <div className="highlight-badge">🏆 Master Teppanyaki Artists</div>
                      <div className="highlight-badge">🌟 Traditional + Modern Fusion</div>
                    </div>
                    <p className="experience-text">
                      At <span className="highlight-text">My Hibachi</span>, our talented chefs are
                      true maestros of the teppanyaki grill, blending years of experience with an
                      unwavering passion for flavor and flair. Having honed their skills in renowned
                      Japanese kitchens, our chefs fuse traditional techniques with a modern twist,
                      ensuring each dish is a unique encounter that delights both the palate and the
                      memory.
                    </p>
                    <p className="experience-text">
                      We believe that{' '}
                      <span className="highlight-text">
                        quality ingredients at reasonable prices
                      </span>{' '}
                      and exceptional service bring people together. We are committed to turning
                      every event into a celebration of fresh, delectable Japanese cuisine with{' '}
                      <span className="highlight-text">quality as our top priority</span>.
                    </p>
                    <div className="experience-stats">
                      <div className="stat-mini">
                        <span className="stat-emoji">👨‍🍳</span>
                        <span className="stat-text">Expert Chefs</span>
                      </div>
                      <div className="stat-mini">
                        <span className="stat-emoji">🍱</span>
                        <span className="stat-text">Authentic Cuisine</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mb-4">
                <div className="experience-card right-card">
                  <div className="experience-icon-wrapper experience-wrapper">
                    <span className="experience-icon pulsing-flame">🔥</span>
                  </div>
                  <div className="experience-content">
                    <h3 className="experience-title">
                      <span className="title-emoji">🎊</span>
                      The Ultimate Mobile Hibachi Experience
                      <span className="title-emoji">🎊</span>
                    </h3>
                    <div className="experience-highlights">
                      <div className="highlight-badge">🚚 Mobile Chef Service</div>
                      <div className="highlight-badge">🎭 Interactive Entertainment</div>
                    </div>
                    <p className="experience-text">
                      <span className="highlight-text">My Hibachi</span> brings the thrill of
                      hibachi cooking and entertainment directly to you as your mobile, private chef
                      experience in the North California Bay Area and Sacramento. Whether
                      you&apos;re celebrating a wedding, proposal, birthday, family reunion,
                      corporate event, anniversary, holiday party, engagement, or
                      bachelor/bachelorette party, My Hibachi transforms your gathering into a
                      memorable occasion.
                    </p>
                    <p className="experience-text">
                      Our skilled chefs don&apos;t just cook—they perform, crafting a vibrant,
                      interactive atmosphere that keeps your guests entertained and engaged. With{' '}
                      <span className="highlight-text">
                        premium quality ingredients and reasonable pricing
                      </span>
                      , we deliver exceptional value for your special events.
                    </p>
                    <div className="experience-stats">
                      <div className="stat-mini">
                        <span className="stat-emoji">🌉</span>
                        <span className="stat-text">Bay Area & Sacramento</span>
                      </div>
                      <div className="stat-mini">
                        <span className="stat-emoji">*</span>
                        <span className="stat-text">All Events Welcome</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Features Grid - Compact */}
            <section
              className="features-section compact-features"
              aria-labelledby="features-heading"
            >
              <h2 id="features-heading" className="features-heading">
                <span className="heading-emoji">✨</span>
                What Makes Us Special
                <span className="heading-emoji">✨</span>
              </h2>
              <div className="features-grid animate-on-scroll">
                <div className="feature-item feature-premium">
                  <div className="feature-icon-container">
                    <span className="feature-icon feature-icon-premium">🥩</span>
                  </div>
                  <div className="feature-content">
                    <h3 className="feature-title">Premium Ingredients</h3>
                    <p className="feature-description">
                      Fresh, high-quality meats and authentic Japanese seasonings.
                    </p>
                  </div>
                </div>
                <div className="feature-item feature-pricing">
                  <div className="feature-icon-container">
                    <span className="feature-icon feature-icon-pricing">💰</span>
                  </div>
                  <div className="feature-content">
                    <h3 className="feature-title">Great Value</h3>
                    <p className="feature-description">
                      Competitive rates with exceptional quality and service.
                    </p>
                  </div>
                </div>
                <div className="feature-item feature-entertainment">
                  <div className="feature-icon-container">
                    <span className="feature-icon feature-icon-entertainment">🎭</span>
                  </div>
                  <div className="feature-content">
                    <h3 className="feature-title">Live Entertainment</h3>
                    <p className="feature-description">
                      Skilled chefs with entertaining performances.
                    </p>
                  </div>
                </div>
                <div className="feature-item feature-location">
                  <div className="feature-icon-container">
                    <span className="feature-icon feature-icon-location">📍</span>
                  </div>
                  <div className="feature-content">
                    <h3 className="feature-title">We Come To You</h3>
                    <p className="feature-description">
                      Mobile service across Bay Area & Sacramento.
                    </p>
                  </div>
                </div>
              </div>
            </section>

            {/* Service Areas - Compact Link */}
            <div className="service-areas-compact animate-on-scroll">
              <div className="service-areas-banner">
                <div className="banner-content-wrapper">
                  <span className="banner-icon">📍</span>
                  <div className="banner-text-content">
                    <p className="banner-title" role="heading" aria-level={3}>
                      Serving Bay Area, Sacramento & Northern California
                    </p>
                    <p className="banner-subtitle">No travel fee for most Bay Area locations!</p>
                  </div>
                  <Link href="/service-areas" className="banner-link">
                    View All Areas →
                  </Link>
                </div>
              </div>
              <div className="mt-3 flex flex-wrap justify-center gap-3">
                <Link href="/BookUs" className="btn-cta-primary btn-cta-shimmer">
                  <span>📅</span>
                  <span>Check Your Date</span>
                </Link>
                <Link href="/quote" className="btn-cta-secondary">
                  <span>💬</span>
                  <span>Get a Quote</span>
                </Link>
              </div>
            </div>

            {/* Call-to-Action Section */}
            <div className="cta-section animate-on-scroll text-center">
              <h2 className="cta-title">Ready to host an unforgettable hibachi experience?</h2>
              <p className="cta-description">
                Join hundreds of satisfied customers across the Bay Area and Sacramento! Discover
                why <span className="highlight-text">My Hibachi</span>
                is the premier choice for{' '}
                <span className="highlight-text">
                  quality ingredients, reasonable prices, and exceptional entertainment
                </span>
                . We come to you—chef, grill, and a full hibachi show. Just pick a date, we&apos;ll
                handle the rest!
              </p>
              <div className="cta-special-offer">
                <span className="offer-badge">✨ Special Offer ✨</span>
                <p className="offer-text">
                  Book now and let us create memories that will last a lifetime!
                </p>
              </div>
              <div className="cta-buttons flex flex-wrap justify-center gap-4">
                <Link href="/menu" className="btn-cta-primary btn-cta-shimmer btn-cta-pulse">
                  <span>🔥</span>
                  <span>View Our Menu</span>
                </Link>
                <Link href="/quote" className="btn-cta-secondary">
                  <span>💬</span>
                  <span>Get Your Free Quote</span>
                </Link>
              </div>
              <p className="cta-footer">
                <small>
                  📞 Questions? Call us for instant assistance! • 🚗 We travel to you! • 💯
                  Satisfaction guaranteed!
                </small>
              </p>
            </div>

            {/* About Us Section */}
            <div className="about-us-section animate-on-scroll">
              <h3 className="section-title text-center">Our Story</h3>
              <div className="mx-auto max-w-4xl">
                <p className="about-text">
                  My Hibachi Chef was founded with a simple mission: to bring the excitement and
                  flavors of hibachi cooking directly to our customers. What started as a small
                  catering service has grown into a premier hibachi experience provider serving the
                  entire region.
                </p>
                <p className="about-text">
                  Our team of professionally trained chefs combines culinary expertise with
                  entertainment to create memorable dining experiences for any occasion.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Services Section */}
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
                      <CheckCircle className="mr-1 inline-block h-4 w-4 text-red-600" />{' '}
                      Professional chef service
                    </span>
                    <span className="service-feature">
                      <CheckCircle className="mr-1 inline-block h-4 w-4 text-red-600" /> Custom menu
                      options
                    </span>
                    <span className="service-feature">
                      <CheckCircle className="mr-1 inline-block h-4 w-4 text-red-600" />{' '}
                      Personalized entertainment
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
                    chosen venue. Our professional service adds flair to any corporate gathering or
                    team celebration.
                  </p>
                  <div className="service-features">
                    <span className="service-feature">
                      <CheckCircle className="mr-1 inline-block h-4 w-4 text-red-600" />{' '}
                      Professional presentation
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
              <Link href="/BookUs" className="btn-cta-primary btn-cta-shimmer">
                <CalendarCheck className="h-5 w-5" />
                <span>Book Your Premium Experience</span>
              </Link>
            </div>
          </div>
        </section>

        {/* Value Proposition + Urgency Section - Lazy loaded for performance */}
        <LazyValuePropositionSection />
      </main>
    </ScrollAnimationProvider>
  );
}
