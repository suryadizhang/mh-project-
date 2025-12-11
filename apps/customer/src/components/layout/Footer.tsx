'use client';

import {
  ChevronRight,
  Facebook,
  FileText,
  Instagram,
  Mail,
  MapPin,
  MessageCircle,
  Phone,
  Shield,
} from 'lucide-react';
import Image from 'next/image';
import Link from 'next/link';

import { ProtectedPhone } from '@/components/ui/ProtectedPhone';

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
              <Instagram size={24} />
            </a>
            <a
              href="https://www.facebook.com/people/My-hibachi/61577483702847/"
              target="_blank"
              rel="noopener noreferrer"
              className={styles.socialIcon}
            >
              <Facebook size={24} />
            </a>
          </div>
        </div>

        <div className={styles.menu}>
          <h3>Quick Links</h3>
          <ul className={styles.links}>
            <li>
              <Link href="/">
                <ChevronRight size={16} className={styles.linkIcon} /> Home
              </Link>
            </li>
            <li>
              <Link href="/menu">
                <ChevronRight size={16} className={styles.linkIcon} /> Menu
              </Link>
            </li>
            <li>
              <Link href="/BookUs">
                <ChevronRight size={16} className={styles.linkIcon} /> Book Us
              </Link>
            </li>
            <li>
              <Link href="/quote">
                <ChevronRight size={16} className={styles.linkIcon} /> Get Quote
              </Link>
            </li>
            <li>
              <Link href="/contact">
                <ChevronRight size={16} className={styles.linkIcon} /> Contact
              </Link>
            </li>
          </ul>
        </div>

        <div className={styles.menu}>
          <h3>Legal</h3>
          <ul className={styles.links}>
            <li>
              <Link href="/privacy">
                <Shield size={16} className={styles.linkIcon} /> Privacy Policy
              </Link>
            </li>
            <li>
              <Link href="/terms">
                <FileText size={16} className={styles.linkIcon} /> Terms & Conditions
              </Link>
            </li>
          </ul>
        </div>

        <div className={styles.contact}>
          <h3>Contact Us</h3>
          <ul className={styles.contactInfo}>
            <li>
              <MapPin size={18} className={styles.contactIcon} />
              <span>Serving the Bay Area & Sacramento Region</span>
            </li>
            <li>
              <Phone size={18} className={styles.contactIcon} />
              <ProtectedPhone showIcon={false} />
            </li>
            <li>
              <Mail size={18} className={styles.contactIcon} />
              <Link href="/contact#business-inquiries">Business Inquiries Form</Link>
            </li>
            <li>
              <MessageCircle size={18} className={styles.contactIcon} />
              <a href="https://m.me/61577483702847" target="_blank" rel="noopener noreferrer">
                Facebook Messenger
              </a>
            </li>
            <li>
              <Instagram size={18} className={styles.contactIcon} />
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
