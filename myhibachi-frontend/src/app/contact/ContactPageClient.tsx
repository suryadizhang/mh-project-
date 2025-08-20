'use client'

// Type definitions
declare global {
  interface Window {
    FB?: {
      init: (config: { xfbml: boolean; version: string }) => void
      CustomerChat: {
        show: () => void
        hide: () => void
      }
    }
    dataLayer?: unknown[]
    opera?: string
  }
}

// Inline Chat Button Components
function InlineMessengerButton() {
  const handleMessengerClick = () => {
    try {
      if (typeof window !== 'undefined' && window.FB?.CustomerChat?.show) {
        window.FB.CustomerChat.show()

        // GTM tracking
        if (window.dataLayer) {
          window.dataLayer.push({ event: 'chat_open', channel: 'messenger' })
        }
      } else {
        console.warn('Facebook Messenger not available')
      }
    } catch (error) {
      console.warn('Error opening Messenger:', error)
    }
  }

  return (
    <button
      onClick={handleMessengerClick}
      className="social-link facebook-link messenger-chat-button"
      style={{ cursor: 'pointer', border: 'none', background: 'none', padding: 0, width: '100%' }}
    >
      <i className="bi bi-messenger social-icon"></i>
      <div>
        <strong>💬 Chat on Messenger</strong>
        <small>Instant messaging with our team</small>
      </div>
    </button>
  )
}

function InlineInstagramButton() {
  const handleInstagramClick = () => {
    try {
      // GTM tracking
      if (typeof window !== 'undefined' && window.dataLayer) {
        window.dataLayer.push({ event: 'chat_open', channel: 'instagram' })
      }

      // Mobile app detection and opening
      const userAgent = navigator.userAgent || navigator.vendor || window.opera || ''
      const isMobile = /android|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent.toLowerCase())

      if (isMobile) {
        // Try to open Instagram app first
        const instagramUrl = 'instagram://user?username=my_hibachi_chef'
        const fallbackUrl = 'https://www.instagram.com/direct/t/my_hibachi_chef/'

        const iframe = document.createElement('iframe')
        iframe.style.display = 'none'
        iframe.src = instagramUrl
        document.body.appendChild(iframe)

        setTimeout(() => {
          document.body.removeChild(iframe)
          window.open(fallbackUrl, '_blank')
        }, 1000)
      } else {
        // Desktop - direct to Instagram DM
        window.open('https://www.instagram.com/direct/t/my_hibachi_chef/', '_blank')
      }
    } catch (error) {
      console.warn('Error opening Instagram:', error)
      // Fallback to profile page
      window.open('https://www.instagram.com/my_hibachi_chef/', '_blank')
    }
  }

  return (
    <button
      onClick={handleInstagramClick}
      className="social-link instagram-link instagram-chat-button"
      style={{ cursor: 'pointer', border: 'none', background: 'none', padding: 0, width: '100%' }}
    >
      <i className="bi bi-instagram social-icon"></i>
      <div>
        <strong>📸 DM on Instagram</strong>
        <small>Message @my_hibachi_chef directly</small>
      </div>
    </button>
  )
}

export default function ContactPageClient() {
  return (
    <div className="contact-page">
      {/* Hero Section */}
      <div className="contact-hero page-hero-background">
        <div className="hero-content">
          <div className="animated-hero-icons">
            <span className="hero-icon-floating">🎉</span>
            <span className="hero-icon-floating">🔥</span>
            <span className="hero-icon-floating">👨‍🍳</span>
            <span className="hero-icon-floating">🍽️</span>
          </div>
          <h1 className="hero-title">
            <i className="bi bi-heart-fill heart-icon pulse-animation"></i>
            <span className="gradient-text">Book Your Hibachi Experience</span>
          </h1>
          <p className="hero-subtitle">
            <span className="highlight-text">Elevate Your Celebration</span> with a spectacular culinary journey!
            Our master hibachi chefs bring <span className="highlight-text">restaurant-quality dining</span> and
            <span className="highlight-text">unforgettable entertainment</span> directly to your venue!
          </p>
          <div className="hero-features">
            <div className="feature-badge">
              <i className="bi bi-trophy-fill feature-icon"></i>
              <span>Premium Experience</span>
            </div>
            <div className="feature-badge">
              <i className="bi bi-stars feature-icon"></i>
              <span>Master Chefs</span>
            </div>
            <div className="feature-badge">
              <i className="bi bi-geo-alt-fill feature-icon"></i>
              <span>We Come To You</span>
            </div>
          </div>
        </div>
      </div>

      <div className="container contact-container">
        {/* Main Contact Section */}
        <div className="row contact-main-section" id="contact-details">
          {/* Contact Information Card */}
          <div className="col-lg-6 mb-4">
            <div className="card contact-card h-100">
              <div className="card-body">
                <h3 className="card-title">
                  <i className="bi bi-envelope-fill title-icon"></i>
                  Professional Booking Services
                </h3>

                <div className="contact-info-list">
                  <div className="contact-item">
                    <i className="bi bi-envelope-fill contact-icon"></i>
                    <div className="contact-details">
                      <h5>Professional Booking</h5>
                      <a href="mailto:cs@myhibachichef.com" className="contact-link">
                        cs@myhibachichef.com
                      </a>
                      <p className="contact-note">Premium service bookings, custom quotes, and expert consultation</p>
                    </div>
                  </div>

                  <div className="contact-item">
                    <i className="bi bi-chat-dots-fill contact-icon"></i>
                    <div className="contact-details">
                      <h5>Instant Response</h5>
                      <a href="sms:+19167408768" className="contact-link">
                        +1 (916) 740-8768
                      </a>
                      <p className="contact-note">Text for immediate assistance, scheduled calls available</p>
                    </div>
                  </div>

                  <div className="contact-item">
                    <i className="bi bi-clock-fill contact-icon"></i>
                    <div className="contact-details">
                      <h5>Rapid Response Guarantee</h5>
                      <p className="contact-link">Within 1-2 hours</p>
                      <p className="contact-note">Professional team standing by! Email or social media DM for fastest response</p>
                    </div>
                  </div>

                  <div className="contact-item">
                    <i className="bi bi-geo-alt-fill contact-icon"></i>
                    <div className="contact-details">
                      <h5>Service Coverage</h5>
                      <p className="contact-link">We come to you across the Bay Area, Sacramento, San Jose, and nearby communities—just ask!</p>
                      <p className="contact-note">Premium mobile hibachi service delivered to your location!</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Reviews & Social Media Card */}
          <div className="col-lg-6 mb-4">
            <div className="card contact-card h-100">
              <div className="card-body">
                <h3 className="card-title">
                  <i className="bi bi-star-fill title-icon"></i>
                  Client Reviews & Community
                </h3>

                {/* Review Platforms */}
                <div className="review-section">
                  <h5 className="section-subtitle">⭐ Share Your Experience & Help Others Discover Excellence!</h5>
                  <p className="review-incentive">
                    Your testimonials inspire confidence in future clients and help us maintain our commitment to exceptional service.
                    We value every review! 🙏
                  </p>
                  <div className="review-buttons">
                    <a
                      href="https://www.yelp.com/biz/my-hibachi-fremont"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="review-button yelp-button"
                    >
                      <i className="bi bi-yelp review-icon"></i>
                      <div className="review-content">
                        <strong>Share Your Hibachi Experience</strong>
                        <small>Help others discover our service!</small>
                      </div>
                      <div className="review-badge">⭐ 5.0 Stars</div>
                    </a>

                    <a
                      href="https://www.google.com/maps/place/My+hibachi/@37.8543835,-122.0808034,8z/data=!3m1!4b1!4m6!3m5!1s0x808fc75b1c21cf49:0x152b61e9f0a0f93d!8m2!3d37.8543835!4d-122.0808034!16s%2Fg%2F11xkvw5_hv?entry=ttu&g_ep=EgoyMDI1MDcxNi4wIKXMDSoASAFQAw%3D%3D"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="review-button google-button"
                    >
                      <i className="bi bi-google review-icon"></i>
                      <div className="review-content">
                        <strong>Google Business Review</strong>
                        <small>Boost our visibility to new clients!</small>
                      </div>
                      <div className="review-badge">⭐ 5.0 Stars</div>
                    </a>
                  </div>

                  <div className="review-stats">
                    <div className="stat-item">
                      <span className="stat-number">⭐⭐⭐⭐⭐</span>
                      <span className="stat-label">Five Star Service</span>
                    </div>
                  </div>
                </div>

                {/* Social Media */}
                <div className="social-section">
                  <h5 className="section-subtitle">🔗 Connect With Our Community</h5>
                  <div className="social-links">
                    <a
                      href="https://www.instagram.com/my_hibachi_chef/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="social-link instagram-link"
                    >
                      <i className="bi bi-instagram social-icon"></i>
                      <div>
                        <strong>@my_hibachi_chef</strong>
                        <small>Exclusive content & culinary inspiration</small>
                      </div>
                    </a>

                    <a
                      href="https://www.facebook.com/people/My-hibachi/61577483702847/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="social-link facebook-link"
                    >
                      <i className="bi bi-facebook social-icon"></i>
                      <div>
                        <strong>My Hibachi</strong>
                        <small>Event galleries & client testimonials</small>
                      </div>
                    </a>
                  </div>

                  {/* Chat Options Integration */}
                  <div className="chat-options-section mt-4">
                    <h6 className="chat-subtitle">💬 Instant Messaging</h6>
                    <div className="chat-buttons">
                      <InlineMessengerButton />
                      <InlineInstagramButton />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Booking Call-to-Action Section */}
        <div className="booking-cta-section">
          <div className="card booking-cta-card">
            <div className="card-body text-center">
              <div className="cta-icon-container">
                <i className="bi bi-calendar-check-fill cta-icon"></i>
              </div>
              <h2 className="cta-title">Ready to Experience Hibachi Excellence?</h2>
              <p className="cta-text">
                Turn your next gathering into an unforgettable culinary event with our professional hibachi chefs.
                From intimate dinners to large celebrations, we create personalized experiences that delight all your guests.
              </p>
              <div className="cta-buttons">
                <a href="#contact-details" className="btn btn-primary btn-lg me-3">
                  <i className="bi bi-chat-dots-fill me-2"></i>
                  Get a Custom Quote
                </a>
                <a href="tel:+19167408768" className="btn btn-outline-primary btn-lg">
                  <i className="bi bi-telephone-fill me-2"></i>
                  Call Us Now
                </a>
              </div>
            </div>
          </div>
        </div>

        {/* Testimonials Section */}
        <div className="testimonials-section">
          <h3 className="text-center mb-5">
            <i className="bi bi-quote me-2"></i>
            What Our Clients Say
          </h3>
          <div className="row">
            <div className="col-md-4 mb-4">
              <div className="testimonial-card">
                <div className="testimonial-header">
                  <div className="testimonial-rating">⭐⭐⭐⭐⭐</div>
                  <div className="testimonial-source">Google Review</div>
                </div>
                <div className="testimonial-content">
                  <p>&ldquo;Absolutely amazing experience! The chef was entertaining, professional and the food was delicious. Perfect for our anniversary celebration!&rdquo;</p>
                </div>
                <div className="testimonial-author">- Sarah J., San Francisco</div>
              </div>
            </div>
            <div className="col-md-4 mb-4">
              <div className="testimonial-card">
                <div className="testimonial-header">
                  <div className="testimonial-rating">⭐⭐⭐⭐⭐</div>
                  <div className="testimonial-source">Yelp Review</div>
                </div>
                <div className="testimonial-content">
                  <p>&ldquo;We booked My Hibachi for our company party and it was a huge hit! Great entertainment, delicious food, and excellent service from start to finish.&rdquo;</p>
                </div>
                <div className="testimonial-author">- Michael T., San Jose</div>
              </div>
            </div>
            <div className="col-md-4 mb-4">
              <div className="testimonial-card">
                <div className="testimonial-header">
                  <div className="testimonial-rating">⭐⭐⭐⭐⭐</div>
                  <div className="testimonial-source">Facebook Review</div>
                </div>
                <div className="testimonial-content">
                  <p>&ldquo;The convenience of having a hibachi chef come to our home for my daughter&apos;s birthday was incredible. The food was outstanding and the experience unforgettable!&rdquo;</p>
                </div>
                <div className="testimonial-author">- Jennifer P., Sacramento</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Service Areas */}
      <section className="py-5 service-areas-section">
        <div className="container">
          <h2 className="text-center mb-5">Our Service Areas</h2>

          {/* Primary Bay Area Locations */}
          <h4 className="text-center mb-4">🏙️ Primary Bay Area Locations</h4>
          <p className="text-center mb-4">No additional travel fees within these areas!</p>
          <div className="row mb-4">
            <div className="col-md-3 mb-3">
              <div className="d-flex align-items-center">
                <i className="bi bi-geo-alt-fill text-primary me-2"></i>
                <span>San Francisco</span>
              </div>
            </div>
            <div className="col-md-3 mb-3">
              <div className="d-flex align-items-center">
                <i className="bi bi-geo-alt-fill text-primary me-2"></i>
                <span>San Jose</span>
              </div>
            </div>
            <div className="col-md-3 mb-3">
              <div className="d-flex align-items-center">
                <i className="bi bi-geo-alt-fill text-primary me-2"></i>
                <span>Oakland</span>
              </div>
            </div>
            <div className="col-md-3 mb-3">
              <div className="d-flex align-items-center">
                <i className="bi bi-geo-alt-fill text-primary me-2"></i>
                <span>Northern California</span>
              </div>
            </div>
            <div className="col-md-3 mb-3">
              <div className="d-flex align-items-center">
                <i className="bi bi-geo-alt-fill text-primary me-2"></i>
                <span>Santa Clara</span>
              </div>
            </div>
            <div className="col-md-3 mb-3">
              <div className="d-flex align-items-center">
                <i className="bi bi-geo-alt-fill text-primary me-2"></i>
                <span>Sunnyvale</span>
              </div>
            </div>
            <div className="col-md-3 mb-3">
              <div className="d-flex align-items-center">
                <i className="bi bi-geo-alt-fill text-primary me-2"></i>
                <span>Mountain View</span>
              </div>
            </div>
            <div className="col-md-3 mb-3">
              <div className="d-flex align-items-center">
                <i className="bi bi-geo-alt-fill text-primary me-2"></i>
                <span>Palo Alto</span>
              </div>
            </div>
          </div>

          {/* Sacramento & Extended Regions */}
          <h4 className="text-center mb-4">🏞️ Sacramento & Extended Regions</h4>
          <p className="text-center mb-4">Minimal travel fees for these beautiful locations!</p>
          <div className="row">
            <div className="col-md-3 mb-3">
              <div className="d-flex align-items-center">
                <i className="bi bi-geo-alt-fill text-primary me-2"></i>
                <span>Sacramento</span>
              </div>
            </div>
            <div className="col-md-3 mb-3">
              <div className="d-flex align-items-center">
                <i className="bi bi-geo-alt-fill text-primary me-2"></i>
                <span>Elk Grove</span>
              </div>
            </div>
            <div className="col-md-3 mb-3">
              <div className="d-flex align-items-center">
                <i className="bi bi-geo-alt-fill text-primary me-2"></i>
                <span>Roseville</span>
              </div>
            </div>
            <div className="col-md-3 mb-3">
              <div className="d-flex align-items-center">
                <i className="bi bi-geo-alt-fill text-primary me-2"></i>
                <span>Folsom</span>
              </div>
            </div>
            <div className="col-md-3 mb-3">
              <div className="d-flex align-items-center">
                <i className="bi bi-geo-alt-fill text-primary me-2"></i>
                <span>Davis</span>
              </div>
            </div>
            <div className="col-md-3 mb-3">
              <div className="d-flex align-items-center">
                <i className="bi bi-geo-alt-fill text-primary me-2"></i>
                <span>Stockton</span>
              </div>
            </div>
            <div className="col-md-3 mb-3">
              <div className="d-flex align-items-center">
                <i className="bi bi-geo-alt-fill text-primary me-2"></i>
                <span>Modesto</span>
              </div>
            </div>
            <div className="col-md-3 mb-3">
              <div className="d-flex align-items-center">
                <i className="bi bi-geo-alt-fill text-primary me-2"></i>
                <span>Livermore</span>
              </div>
            </div>
          </div>

          <div className="text-center mt-4">
            <div className="alert alert-info d-inline-block">
              <i className="bi bi-info-circle-fill me-2"></i>
              We bring hibachi to your home or venue across Northern California—<strong>contact us to see if we can reach you</strong> with our flexible service area and transparent travel options.
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
