'use client'

import Link from 'next/link'
import '@/styles/home.css'
import { useScrollAnimation } from '@/hooks/useScrollAnimation'
import { FreeQuoteButton } from '@/components/quote/FreeQuoteButton'

export default function Home() {
  useScrollAnimation()
  return (
    <main>
      {/* Hero Video Section */}
      <section className="about-section">
        {/* Hero Media Container */}
        <div className="hero-media-container">
          <div className="hero-media-overlay"></div>
          <video
            className="hero-media hero-video"
            width="1920"
            height="800"
            autoPlay
            muted
            loop
            playsInline
            style={{ backgroundColor: '#000' }}
          >
            <source src="/videos/hero_video.mp4" type="video/mp4" />
            Your browser does not support the video tag.
          </video>
        </div>

        <div className="container">
          {/* Animated Headline Section */}
          <div className="headline-section animate-on-scroll">
            <h1 className="main-title text-center">
              Experience the Art of Japanese Hibachi
            </h1>
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
          <div className="row experience-sections animate-on-scroll mb-5">
            <div className="col-lg-6 mb-4">
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
                    At <span className="highlight-text">My Hibachi</span>, our talented chefs are true maestros of the teppanyaki grill,
                    blending years of experience with an unwavering passion for flavor and flair. Having honed their skills in renowned
                    Japanese kitchens, our chefs fuse traditional techniques with a modern twist, ensuring each dish is a unique encounter
                    that delights both the palate and the memory.
                  </p>
                  <p className="experience-text">
                    We believe that <span className="highlight-text">quality ingredients at reasonable prices</span> and exceptional
                    service bring people together. We are committed to turning every event into a celebration of fresh, delectable
                    Japanese cuisine with <span className="highlight-text">quality as our top priority</span>.
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

            <div className="col-lg-6 mb-4">
              <div className="experience-card right-card">
                <div className="experience-icon-wrapper experience-wrapper">
                  <span className="experience-icon pulsing-circus">🎪</span>
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
                    <span className="highlight-text">My Hibachi</span> brings the thrill of hibachi cooking and entertainment directly
                    to you as your mobile, private chef experience in the North California Bay Area and Sacramento. Whether you&apos;re
                    celebrating a wedding, proposal, birthday, family reunion, corporate event, anniversary, holiday party, engagement,
                    or bachelor/bachelorette party, My Hibachi transforms your gathering into a memorable occasion.
                  </p>
                  <p className="experience-text">
                    Our skilled chefs don&apos;t just cook—they perform, crafting a vibrant, interactive atmosphere that keeps your guests
                    entertained and engaged. With <span className="highlight-text">premium quality ingredients and reasonable pricing</span>,
                    we deliver exceptional value for your special events.
                  </p>
                  <div className="experience-stats">
                    <div className="stat-mini">
                      <span className="stat-emoji">📍</span>
                      <span className="stat-text">Bay Area & Sacramento</span>
                    </div>
                    <div className="stat-mini">
                      <span className="stat-emoji">🎉</span>
                      <span className="stat-text">All Events Welcome</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Features Grid */}
          <div className="features-section">
            <h2 className="features-heading">
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
                  <h4 className="feature-title">Premium Quality Ingredients</h4>
                  <p className="feature-description">
                    Fresh, high-quality meats, vegetables, and authentic Japanese seasonings sourced from trusted suppliers.
                  </p>
                  <div className="feature-tag">Quality First</div>
                </div>
              </div>
              <div className="feature-item feature-pricing">
                <div className="feature-icon-container">
                  <span className="feature-icon feature-icon-pricing">💰</span>
                </div>
                <div className="feature-content">
                  <h4 className="feature-title">Reasonable Pricing</h4>
                  <p className="feature-description">
                    Competitive rates that deliver exceptional value without compromising on quality or service excellence.
                  </p>
                  <div className="feature-tag">Great Value</div>
                </div>
              </div>
              <div className="feature-item feature-entertainment">
                <div className="feature-icon-container">
                  <span className="feature-icon feature-icon-entertainment">🎭</span>
                </div>
                <div className="feature-content">
                  <h4 className="feature-title">Interactive Entertainment</h4>
                  <p className="feature-description">
                    Skilled chefs who combine culinary expertise with entertaining performances for an unforgettable experience.
                  </p>
                  <div className="feature-tag">Fun & Engaging</div>
                </div>
              </div>
              <div className="feature-item feature-location">
                <div className="feature-icon-container">
                  <span className="feature-icon feature-icon-location">📍</span>
                </div>
                <div className="feature-content">
                  <h4 className="feature-title">Mobile Service</h4>
                  <p className="feature-description">
                    We bring the complete hibachi experience to your location across the Bay Area and Sacramento region.
                  </p>
                  <div className="feature-tag">Convenient</div>
                </div>
              </div>
              <div className="feature-item feature-excellence">
                <div className="feature-icon-container">
                  <span className="feature-icon feature-icon-excellence">🏆</span>
                </div>
                <div className="feature-content">
                  <h4 className="feature-title">Excellence Guarantee</h4>
                  <p className="feature-description">
                    Our commitment to quality is our priority, ensuring every event exceeds your expectations.
                  </p>
                  <div className="feature-tag">Guaranteed</div>
                </div>
              </div>
              <div className="feature-item feature-occasions">
                <div className="feature-icon-container">
                  <span className="feature-icon feature-icon-occasions">🎉</span>
                </div>
                <div className="feature-content">
                  <h4 className="feature-title">All Occasions</h4>
                  <p className="feature-description">
                    Perfect for weddings, birthdays, corporate events, and any celebration that deserves something special.
                  </p>
                  <div className="feature-tag">Versatile</div>
                </div>
              </div>
            </div>
          </div>

          {/* Service Areas */}
          <div className="service-areas animate-on-scroll">
            <h3 className="section-title text-center">🌟 Bringing Hibachi Experience to Your Neighborhood! 🌟</h3>
            <p className="service-intro text-center">
              We&apos;re excited to bring our premium hibachi experience directly to your location!
              Serving within <span className="highlight-text">150 miles from our location</span> with
              <span className="highlight-text">reasonable travel fees</span> for locations outside our primary service areas.
            </p>

            <div className="row mt-4">
              <div className="col-md-6">
                <div className="service-area-card">
                  <h4 className="area-title">🏙️ Primary Bay Area Locations</h4>
                  <p className="area-subtitle">No to minimum travel fees within these areas!</p>
                  <ul className="area-list">
                    <li>San Francisco - The heart of culinary excellence</li>
                    <li>San Jose - Silicon Valley&apos;s finest hibachi</li>
                    <li>Oakland - East Bay entertainment at its best</li>
                    <li>Bay Area - Our home base with premium service</li>
                    <li>Santa Clara - Tech meets traditional Japanese cuisine</li>
                    <li>Sunnyvale - Where innovation meets flavor</li>
                    <li>Mountain View - Bringing mountains of flavor</li>
                    <li>Palo Alto - Stanford-level culinary performance</li>
                  </ul>
                </div>
              </div>
              <div className="col-md-6">
                <div className="service-area-card">
                  <h4 className="area-title">🏞️ Sacramento & Extended Regions</h4>
                  <p className="area-subtitle">Minimal travel fees for these beautiful locations!</p>
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

            <div className="service-radius-info text-center mt-4">
              <div className="radius-card">
                <span className="radius-icon">📍</span>
                <h4 className="radius-title">We Come to You!</h4>
                <p className="radius-description">
                  Serving anywhere within <span className="highlight-text">150 miles from our location</span>
                </p>
                <p className="travel-fee-info">
                  <span className="travel-highlight">💰 Transparent Pricing:</span>
                  Minimal travel fees apply for locations outside our primary service areas.
                  <br />
                  <strong>Call us for a custom quote - we make it affordable for everyone!</strong>
                </p>
                <div className="service-promise">
                  <span className="promise-icon">🎯</span>
                  <span className="promise-text">
                    <strong>Our Promise:</strong> No hidden fees, just honest pricing and exceptional service!
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Call-to-Action Section */}
          <div className="cta-section animate-on-scroll text-center">
            <h2 className="cta-title">🎉 Ready to host an unforgettable hibachi experience? 🎉</h2>
            <p className="cta-description">
              Join hundreds of satisfied customers across the Bay Area and Sacramento! Discover why <span className="highlight-text">My Hibachi</span>
              is the premier choice for <span className="highlight-text">quality ingredients, reasonable prices, and exceptional entertainment</span>.
              We bring the restaurant experience to your backyard - anywhere within 150 miles!
            </p>
            <div className="cta-special-offer">
              <span className="offer-badge">✨ Special Offer ✨</span>
              <p className="offer-text">Book now and let us create memories that will last a lifetime!</p>
            </div>
            <div className="cta-buttons">
              <Link href="/menu" className="btn btn-primary btn-lg me-3">
                🔥 View Our Menu
              </Link>
              <Link href="/contact" className="btn btn-outline-primary btn-lg">
                💬 Get Your Free Quote
              </Link>
            </div>
            <p className="cta-footer">
              <small>📞 Questions? Call us for instant assistance! • 🚗 We travel to you! • 💯 Satisfaction guaranteed!</small>
            </p>
          </div>

          {/* About Us Section */}
          <div className="about-us-section animate-on-scroll">
            <h3 className="section-title text-center">Our Story</h3>
            <div className="row">
              <div className="col-lg-8 offset-lg-2">
                <p className="about-text">
                  My Hibachi Chef was founded with a simple mission: to bring the excitement and
                  flavors of hibachi cooking directly to our customers. What started as a small
                  catering service has grown into a premier hibachi experience provider serving
                  the entire region.
                </p>
                <p className="about-text">
                  Our team of professionally trained chefs combines culinary expertise with
                  entertainment to create memorable dining experiences for any occasion.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Services Section */}
      <section className="services-section">
        <div className="container">
          <h2 className="services-heading text-center">
            <span className="service-icon">🍽️</span> Premium Services for Every Occasion <span className="service-icon">🎪</span>
          </h2>

          <div className="row services-grid">
            <div className="col-md-4 mb-4">
              <div className="service-card">
                <div className="service-icon-wrapper">
                  <i className="bi bi-calendar-event service-icon-bi"></i>
                </div>
                <h3 className="service-title">Private Events</h3>
                <p className="service-description">
                  Transform your special occasions into extraordinary experiences with our premium
                  hibachi service. Perfect for birthdays, anniversaries, family gatherings and
                  celebrations of all sizes.
                </p>
                <div className="service-features">
                  <span className="service-feature"><i className="bi bi-check-circle"></i> Professional chef service</span>
                  <span className="service-feature"><i className="bi bi-check-circle"></i> Custom menu options</span>
                  <span className="service-feature"><i className="bi bi-check-circle"></i> Personalized entertainment</span>
                </div>
              </div>
            </div>

            <div className="col-md-4 mb-4">
              <div className="service-card">
                <div className="service-icon-wrapper">
                  <i className="bi bi-building service-icon-bi"></i>
                </div>
                <h3 className="service-title">Corporate Events</h3>
                <p className="service-description">
                  Impress your team or clients with a unique dining experience at your office or chosen venue.
                  Our professional service adds flair to any corporate gathering or team celebration.
                </p>
                <div className="service-features">
                  <span className="service-feature"><i className="bi bi-check-circle"></i> Professional presentation</span>
                  <span className="service-feature"><i className="bi bi-check-circle"></i> Flexible scheduling</span>
                  <span className="service-feature"><i className="bi bi-check-circle"></i> Volume discounts available</span>
                </div>
              </div>
            </div>

            <div className="col-md-4 mb-4">
              <div className="service-card">
                <div className="service-icon-wrapper">
                  <i className="bi bi-stars service-icon-bi"></i>
                </div>
                <h3 className="service-title">Premium Experience</h3>
                <p className="service-description">
                  We offer customizable menus tailored to your preferences and dietary needs.
                  From classic hibachi favorites to premium upgrades, we create a perfect menu for your event.
                </p>
                <div className="service-features">
                  <span className="service-feature"><i className="bi bi-check-circle"></i> Dietary accommodations</span>
                  <span className="service-feature"><i className="bi bi-check-circle"></i> Premium ingredient options</span>
                  <span className="service-feature"><i className="bi bi-check-circle"></i> Signature entertainment</span>
                </div>
              </div>
            </div>
          </div>

          <div className="services-cta text-center">
            <Link href="/contact" className="btn btn-primary btn-lg">
              <i className="bi bi-calendar-check me-2"></i> Book Your Premium Experience
            </Link>
            <div className="mt-3">
              <FreeQuoteButton variant="secondary" />
            </div>
          </div>
        </div>
      </section>

      {/* Floating Quote Button removed - users can get quotes from dedicated quote page */}
    </main>
  )
}
