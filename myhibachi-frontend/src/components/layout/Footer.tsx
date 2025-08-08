import Link from 'next/link'
import Image from 'next/image'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-content">
        <div className="footer-brand">
          <Image 
            src="/My Hibachi logo.png" 
            alt="My Hibachi Chef Logo" 
            width={80} 
            height={80}
            className="footer-logo"
          />
          <h3>My Hibachi Chef</h3>
          <p className="footer-description">
            Bringing the authentic hibachi experience to your location with premium quality and reasonable prices.
          </p>
          <div className="footer-social">
            <a href="https://www.instagram.com/my_hibachi_chef/" target="_blank" rel="noopener noreferrer" className="footer-social-icon">
              <i className="bi bi-instagram"></i>
            </a>
            <a href="https://www.facebook.com/myhibachi" target="_blank" rel="noopener noreferrer" className="footer-social-icon">
              <i className="bi bi-facebook"></i>
            </a>
            <a href="https://www.yelp.com/biz/my-hibachi-fremont" target="_blank" rel="noopener noreferrer" className="footer-social-icon">
              <i className="bi bi-yelp"></i>
            </a>
          </div>
        </div>
        
        <div className="footer-menu">
          <h3>Quick Links</h3>
          <ul className="footer-links">
            <li><Link href="/"><i className="bi bi-chevron-right footer-link-icon"></i> Home</Link></li>
            <li><Link href="/menu"><i className="bi bi-chevron-right footer-link-icon"></i> Menu</Link></li>
            <li><Link href="/contact"><i className="bi bi-chevron-right footer-link-icon"></i> Contact</Link></li>
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
          </ul>
        </div>
      </div>
      
      <div className="footer-copyright">
        <p>&copy; 2025 My Hibachi Chef. All rights reserved.</p>
      </div>
    </footer>
  )
}
