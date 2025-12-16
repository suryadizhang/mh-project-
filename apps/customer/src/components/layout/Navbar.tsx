'use client';

import {
  BookOpen,
  Calculator,
  Calendar,
  HelpCircle,
  Home,
  MapPin,
  Menu,
  MessageCircle,
  UtensilsCrossed,
  X,
} from 'lucide-react';
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

  const navLinks = [
    { href: '/', label: 'Home', icon: Home },
    { href: '/menu', label: 'Menu', icon: UtensilsCrossed },
    { href: '/service-areas', label: 'Service Areas', icon: MapPin },
    { href: '/quote', label: 'Get Quote', icon: Calculator },
    { href: '/BookUs', label: 'Book Us', icon: Calendar },
    { href: '/faqs', label: 'FAQs', icon: HelpCircle },
    { href: '/contact', label: 'Contact', icon: MessageCircle },
    { href: '/blog', label: 'Blog', icon: BookOpen },
  ];

  return (
    <nav className={styles.navbar}>
      <div className={styles.container}>
        {/* Brand Logo */}
        <Link href="/" className={styles.brand}>
          <Image
            src="/My Hibachi logo.png"
            alt="MyHibachi Private Hibachi Chef Bay Area Sacramento San Jose Catering Logo"
            width={238}
            height={238}
            className={styles.logo}
          />
          <span className={styles.brandText}>My Hibachi Chef</span>
        </Link>

        {/* Mobile Menu Toggle */}
        <button
          className={styles.toggler}
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          aria-controls="navbarNav"
          aria-expanded={isOpen}
          aria-label="Toggle navigation"
        >
          {isOpen ? <X size={24} /> : <Menu size={24} />}
        </button>

        {/* Navigation Links */}
        <div className={cn(styles.navCollapse, isOpen && styles.show)} id="navbarNav">
          <ul className={styles.navList}>
            {navLinks.map((link) => {
              const Icon = link.icon;
              return (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className={cn(styles.navLink, pathname === link.href && styles.active)}
                    onClick={handleLinkClick}
                  >
                    <Icon size={18} className={styles.navIcon} />
                    <span className={styles.navText}>{link.label}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      </div>
    </nav>
  );
}
