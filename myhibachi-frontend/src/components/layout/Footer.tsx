import Image from 'next/image'
import Link from 'next/link'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-content">
        <div className="footer-brand">
          <Image
            src="/My Hibachi logo.png"
            alt="MyHibachi Private Hibachi Chef Bay Area Sacramento San Jose Mobile Catering Service Logo"
            width={100}
            height={100}
            className="footer-logo"
          />
          <h3>My Hibachi Chef</h3>
          <p className="footer-description">
            Bringing the authentic hibachi experience to your location with premium quality and
            reasonable prices.
          </p>
          <div className="footer-social">
            <a
              href="https://www.instagram.com/my_hibachi_chef/"
              target="_blank"
              rel="noopener noreferrer"
              className="footer-social-icon"
            >
              <i className="bi bi-instagram"></i>
            </a>
            <a
              href="https://www.facebook.com/people/My-hibachi/61577483702847/"
              target="_blank"
              rel="noopener noreferrer"
              className="footer-social-icon"
            >
              <i className="bi bi-facebook"></i>
            </a>
            <a
              href="https://www.yelp.com/biz/my-hibachi-fremont"
              target="_blank"
              rel="noopener noreferrer"
              className="footer-social-icon"
            >
              <i className="bi bi-yelp"></i>
            </a>
          </div>
        </div>

        <div className="footer-menu">
          <h3>Quick Links</h3>
          <ul className="footer-links">
            <li>
              <Link href="/">
                <i className="bi bi-chevron-right footer-link-icon"></i> Home
              </Link>
            </li>
            <li>
              <Link href="/menu">
                <i className="bi bi-chevron-right footer-link-icon"></i> Menu
              </Link>
            </li>
            <li>
              <Link href="/BookUs">
                <i className="bi bi-chevron-right footer-link-icon"></i> Book Us
              </Link>
            </li>
            <li>
              <Link href="/quote">
                <i className="bi bi-chevron-right footer-link-icon"></i> Get Quote
              </Link>
            </li>
          </ul>
        </div>

        <div className="footer-contact">
          <h3>Contact Us</h3>
          <ul className="footer-contact-info">
            <li>
              <i className="bi bi-geo-alt footer-contact-icon"></i>
              <span>Serving the Bay Area & Sacramento Region</span>
            </li>
            <li>
              <i className="bi bi-envelope footer-contact-icon"></i>
              <span>cs@myhibachichef.com</span>
            </li>
            <li>
              <i className="bi bi-telephone footer-contact-icon"></i>
              <span>(916) 740-8768</span>
            </li>
            <li>
              <i className="bi bi-messenger footer-contact-icon"></i>
              <a href="https://m.me/61577483702847" target="_blank" rel="noopener noreferrer">
                Facebook Messenger
              </a>
            </li>
            <li>
              <i className="bi bi-instagram footer-contact-icon"></i>
              <a href="https://ig.me/m/my_hibachi_chef" target="_blank" rel="noopener noreferrer">
                Instagram DM
              </a>
            </li>
          </ul>
        </div>
      </div>

      <div className="footer-copyright">
        <p>&copy; 2025 My Hibachi Chef. All rights reserved.</p>
      </div>
    </footer>
  )
}
