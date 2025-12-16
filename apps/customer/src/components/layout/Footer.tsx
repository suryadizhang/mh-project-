'use client';

import { ChevronRight, Facebook, FileText, Instagram, MessageCircle, Phone, Shield } from 'lucide-react';
import Image from 'next/image';
import Link from 'next/link';

import { ProtectedPhone } from '@/components/ui/ProtectedPhone';
import { SITE_CONFIG } from '@/lib/seo-config';

import styles from './Footer.module.css';

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={styles.content}>
        {/* Brand Section */}
        <div className={styles.brand}>
          <Image
            src="/My Hibachi logo.webp"
            alt="MyHibachi Private Chef Logo"
            width={80}
            height={80}
            className={styles.logo}
          />
          <h3>My Hibachi Chef</h3>
          <p className={styles.description}>
            Premium mobile hibachi catering for unforgettable events.
          </p>
          <div className={styles.social}>
            <a
              href={SITE_CONFIG.social.instagram}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.socialIcon}
              aria-label="Follow us on Instagram"
            >
              <Instagram size={20} />
            </a>
            <a
              href={SITE_CONFIG.social.facebook}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.socialIcon}
              aria-label="Follow us on Facebook"
            >
              <Facebook size={20} />
            </a>
          </div>
        </div>

        {/* Quick Links */}
        <div className={styles.menu}>
          <h3>Quick Links</h3>
          <ul className={styles.links}>
            <li>
              <Link href="/BookUs">
                <ChevronRight size={14} className={styles.linkIcon} /> Book Now
              </Link>
            </li>
            <li>
              <Link href="/menu">
                <ChevronRight size={14} className={styles.linkIcon} /> Menu
              </Link>
            </li>
            <li>
              <Link href="/quote">
                <ChevronRight size={14} className={styles.linkIcon} /> Get Quote
              </Link>
            </li>
            <li>
              <Link href="/faqs">
                <ChevronRight size={14} className={styles.linkIcon} /> FAQs
              </Link>
            </li>
          </ul>
        </div>

        {/* Legal & Contact */}
        <div className={styles.menu}>
          <h3>Support</h3>
          <ul className={styles.links}>
            <li>
              <Link href="/contact">
                <ChevronRight size={14} className={styles.linkIcon} /> Contact Us
              </Link>
            </li>
            <li>
              <Link href="/privacy">
                <Shield size={14} className={styles.linkIcon} /> Privacy Policy
              </Link>
            </li>
            <li>
              <Link href="/terms">
                <FileText size={14} className={styles.linkIcon} /> Terms
              </Link>
            </li>
          </ul>
        </div>

        {/* Contact - Simplified */}
        <div className={styles.contact}>
          <h3>Get in Touch</h3>
          <ul className={styles.contactInfo}>
            <li>
              <Phone size={16} className={styles.contactIcon} />
              <ProtectedPhone showIcon={false} />
            </li>
            <li>
              <Instagram size={16} className={styles.contactIcon} />
              <a
                href="https://ig.me/m/my_hibachi_chef"
                target="_blank"
                rel="noopener noreferrer"
              >
                DM @my_hibachi_chef
              </a>
            </li>
            <li>
              <MessageCircle size={16} className={styles.contactIcon} />
              <a
                href={SITE_CONFIG.social.facebookMessenger}
                target="_blank"
                rel="noopener noreferrer"
              >
                Chat on Messenger
              </a>
            </li>
          </ul>
        </div>
      </div>

      <div className={styles.copyright}>
        <p>&copy; {new Date().getFullYear()} My Hibachi Chef. All rights reserved.</p>
      </div>
    </footer>
  );
}
