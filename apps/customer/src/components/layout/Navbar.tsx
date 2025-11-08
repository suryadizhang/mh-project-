'use client';

import Image from 'next/image';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';

import { cn } from '@/lib/utils';

import styles from './Navbar.module.css';

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const pathname = usePathname();

  const handleLinkClick = () => {
    setIsOpen(false); // Close mobile menu when link is clicked
  };

  return (
    <nav className={cn('navbar navbar-expand-lg', styles.navbar)}>
      <div className={cn('container', styles.container)}>
        <Link href="/" className={cn('navbar-brand', styles.brand)}>
          <Image
            src="/My Hibachi logo.png"
            alt="MyHibachi Private Hibachi Chef Bay Area Sacramento San Jose Catering Logo"
            width={238}
            height={238}
            className={styles.logo}
          />
          <span className={styles.brandText}>My Hibachi Chef</span>
        </Link>

        <button
          className={cn('navbar-toggler d-lg-none', styles.toggler)}
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          aria-controls="navbarNav"
          aria-expanded={isOpen}
        >
          <span className={cn('navbar-toggler-icon', styles.togglerIcon)}></span>
        </button>

        <div className={cn('navbar-collapse', styles.navCollapse, isOpen && 'show')} id="navbarNav">
          <ul className={cn('navbar-nav ms-auto', styles.navList)}>
            {/* Changed to ms-auto for Bootstrap 5 */}
            <li className="nav-item">
              <Link
                href="/"
                className={cn('nav-link', styles.navLink, pathname === '/' && 'active')}
                onClick={handleLinkClick}
              >
                <i className={cn('bi bi-house-fill', styles.navIcon)}></i>
                <span className={styles.navText}>Home</span>
              </Link>
            </li>
            <li className="nav-item">
              <Link
                href="/menu"
                className={cn('nav-link', styles.navLink, pathname === '/menu' && 'active')}
                onClick={handleLinkClick}
              >
                <i className={cn('bi bi-card-list', styles.navIcon)}></i>
                <span className={styles.navText}>Menu</span>
              </Link>
            </li>
            <li className="nav-item">
              <Link
                href="/quote"
                className={cn('nav-link', styles.navLink, pathname === '/quote' && 'active')}
                onClick={handleLinkClick}
              >
                <i className={cn('bi bi-calculator', styles.navIcon)}></i>
                <span className={styles.navText}>Get Quote</span>
              </Link>
            </li>
            <li className="nav-item">
              <Link
                href="/BookUs"
                className={cn('nav-link', styles.navLink, pathname === '/BookUs' && 'active')}
                onClick={handleLinkClick}
              >
                <i className={cn('bi bi-calendar-check', styles.navIcon)}></i>
                <span className={styles.navText}>Book Us</span>
              </Link>
            </li>
            <li className="nav-item">
              <Link
                href="/faqs"
                className={cn('nav-link', styles.navLink, pathname === '/faqs' && 'active')}
                onClick={handleLinkClick}
              >
                <i className={cn('bi bi-question-circle', styles.navIcon)}></i>
                <span className={styles.navText}>FAQs</span>
              </Link>
            </li>
            <li className="nav-item">
              <Link
                href="/contact"
                className={cn('nav-link', styles.navLink, pathname === '/contact' && 'active')}
                onClick={handleLinkClick}
              >
                <i className={cn('bi bi-chat-dots-fill', styles.navIcon)}></i>
                <span className={styles.navText}>Contact</span>
              </Link>
            </li>
            <li className="nav-item">
              <Link
                href="/blog"
                className={cn('nav-link', styles.navLink, pathname === '/blog' && 'active')}
                onClick={handleLinkClick}
              >
                <i className={cn('bi bi-journal-text', styles.navIcon)}></i>
                <span className={styles.navText}>Blog</span>
              </Link>
            </li>
          </ul>
        </div>
      </div>
    </nav>
  );
}
