import Image from 'next/image';
import Link from 'next/link';

import styles from './Footer.module.css';

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={styles.content}>
        <div className={styles.brand}>
          <Image
            src="/My Hibachi logo.png"
            alt="MyHibachi Private Hibachi Chef Bay Area Sacramento San Jose Mobile Catering Service Logo"
            width={100}
            height={100}
            className={styles.logo}
          />
          <h3>My Hibachi Chef</h3>
          <p className={styles.description}>
            Bringing the authentic hibachi experience to your location with premium quality and
            reasonable prices.
          </p>
          <div className={styles.social}>
            <a
              href="https://www.instagram.com/my_hibachi_chef/"
              target="_blank"
              rel="noopener noreferrer"
              className={styles.socialIcon}
            >
              <i className="bi bi-instagram"></i>
            </a>
            <a
              href="https://www.facebook.com/people/My-hibachi/61577483702847/"
              target="_blank"
              rel="noopener noreferrer"
              className={styles.socialIcon}
            >
              <i className="bi bi-facebook"></i>
            </a>
            <a
              href="https://www.yelp.com/biz/my-hibachi-fremont"
              target="_blank"
              rel="noopener noreferrer"
              className={styles.socialIcon}
            >
              <i className="bi bi-yelp"></i>
            </a>
          </div>
        </div>

        <div className={styles.menu}>
          <h3>Quick Links</h3>
          <ul className={styles.links}>
            <li>
              <Link href="/">
                <i className={`bi bi-chevron-right ${styles.linkIcon}`}></i> Home
              </Link>
            </li>
            <li>
              <Link href="/menu">
                <i className={`bi bi-chevron-right ${styles.linkIcon}`}></i> Menu
              </Link>
            </li>
            <li>
              <Link href="/BookUs">
                <i className={`bi bi-chevron-right ${styles.linkIcon}`}></i> Book Us
              </Link>
            </li>
            <li>
              <Link href="/quote">
                <i className={`bi bi-chevron-right ${styles.linkIcon}`}></i> Get Quote
              </Link>
            </li>
            <li>
              <Link href="/contact">
                <i className={`bi bi-chevron-right ${styles.linkIcon}`}></i> Contact
              </Link>
            </li>
          </ul>
        </div>

        <div className={styles.menu}>
          <h3>Legal</h3>
          <ul className={styles.links}>
            <li>
              <Link href="/privacy">
                <i className={`bi bi-shield-check ${styles.linkIcon}`}></i> Privacy Policy
              </Link>
            </li>
            <li>
              <Link href="/terms">
                <i className={`bi bi-file-text ${styles.linkIcon}`}></i> Terms & Conditions
              </Link>
            </li>
          </ul>
        </div>

        <div className={styles.contact}>
          <h3>Contact Us</h3>
          <ul className={styles.contactInfo}>
            <li>
              <i className={`bi bi-geo-alt ${styles.contactIcon}`}></i>
              <span>Serving the Bay Area & Sacramento Region</span>
            </li>
            <li>
              <i className={`bi bi-telephone ${styles.contactIcon}`}></i>
              <a href="tel:+19167408768">(916) 740-8768</a>
            </li>
            <li>
              <i className={`bi bi-envelope ${styles.contactIcon}`}></i>
              <Link href="/contact#business-inquiries">Business Inquiries Form</Link>
            </li>
            <li>
              <i className={`bi bi-messenger ${styles.contactIcon}`}></i>
              <a href="https://m.me/61577483702847" target="_blank" rel="noopener noreferrer">
                Facebook Messenger
              </a>
            </li>
            <li>
              <i className={`bi bi-instagram ${styles.contactIcon}`}></i>
              <a href="https://ig.me/m/my_hibachi_chef" target="_blank" rel="noopener noreferrer">
                Instagram DM
              </a>
            </li>
          </ul>
        </div>
      </div>

      <div className={styles.copyright}>
        <p>&copy; 2025 My Hibachi Chef. All rights reserved.</p>
      </div>
    </footer>
  );
}
