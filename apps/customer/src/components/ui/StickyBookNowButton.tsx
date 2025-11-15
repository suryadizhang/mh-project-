'use client';

import { Calendar, X } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function StickyBookNowButton() {
  const pathname = usePathname();
  const [isVisible, setIsVisible] = useState(false);
  const [isDismissed, setIsDismissed] = useState(false);
  const [lastScrollY, setLastScrollY] = useState(0);

  // Check if user dismissed button in this session
  useEffect(() => {
    const dismissed = sessionStorage.getItem('stickyCtaDismissed');
    if (dismissed === 'true') {
      setIsDismissed(true);
    }
  }, []);

  // Smart scroll detection: hide when scrolling down, show when scrolling up
  useEffect(() => {
    let ticking = false;

    const handleScroll = () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          const currentScrollY = window.scrollY;
          
          // Detect scroll direction
          const scrollingUp = currentScrollY < lastScrollY;
          setLastScrollY(currentScrollY);

          // Show button only when:
          // 1. Scrolled past 500px (increased from 300px)
          // 2. User is scrolling up (less intrusive)
          // 3. Not dismissed by user
          if (!isDismissed) {
            setIsVisible(currentScrollY > 500 && scrollingUp);
          }

          ticking = false;
        });
        ticking = true;
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [lastScrollY, isDismissed]);

  // Don't show on booking/quote pages or contact page
  if (pathname === '/BookUs' || pathname === '/quote' || pathname === '/contact') {
    return null;
  }

  // Handle dismiss
  const handleDismiss = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDismissed(true);
    setIsVisible(false);
    sessionStorage.setItem('stickyCtaDismissed', 'true');
  };

  if (isDismissed) {
    return null;
  }

  return (
    <div
      className={`
        fixed bottom-6 right-6 z-50
        transform transition-all duration-300 ease-in-out
        ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-20 opacity-0 pointer-events-none'}
      `}
    >
      {/* Dismiss button */}
      <button
        onClick={handleDismiss}
        className="
          absolute -top-2 -right-2 z-10
          w-6 h-6 rounded-full
          bg-gray-800 text-white
          flex items-center justify-center
          hover:bg-gray-900 transition-colors
          shadow-lg
        "
        aria-label="Dismiss booking button"
      >
        <X className="w-4 h-4" />
      </button>

      {/* Main CTA button */}
      <Link
        href="/BookUs"
        className="
          flex items-center gap-3
          px-6 py-4
          bg-gradient-to-r from-red-600 to-red-700
          text-white font-bold text-lg
          rounded-full shadow-2xl
          transform transition-all duration-300 ease-in-out
          hover:from-red-700 hover:to-red-800 hover:scale-105 hover:shadow-3xl
          active:scale-95
          group
        "
        style={{
          minHeight: '56px',
          minWidth: '56px',
        }}
      >
        <Calendar className="w-6 h-6 group-hover:rotate-12 transition-transform" />
        <span className="hidden sm:inline">Book Your Event Now</span>
        <span className="sm:hidden">Book Now</span>
      </Link>
    </div>
  );
}
