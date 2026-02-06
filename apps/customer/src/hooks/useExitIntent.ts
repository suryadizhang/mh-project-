'use client';

import { useEffect, useState } from 'react';

/**
 * Exit Intent Hook
 *
 * Detects when user's mouse leaves the viewport (exit intent)
 * and triggers a callback, typically to show a popup.
 *
 * Features:
 * - Session-based (shows once per session using sessionStorage)
 * - Configurable threshold (default 20px from top)
 * - Mobile-friendly (detects touch events for mobile)
 * - Prevents multiple triggers
 *
 * @param threshold - Distance from top of viewport to trigger (default: 20px)
 * @param delay - Optional delay in ms before enabling detection (default: 3000ms)
 * @returns {showPopup, setShowPopup} - State and setter for popup visibility
 */
export function useExitIntent(threshold: number = 20, delay: number = 3000) {
  const [showPopup, setShowPopup] = useState(false);
  const [hasShown, setHasShown] = useState(false);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    // Check if already shown in this session
    if (typeof window !== 'undefined' && sessionStorage.getItem('exitIntentShown')) {
      setHasShown(true);
      return;
    }

    // Delay before enabling detection (give user time to browse)
    const delayTimer = setTimeout(() => {
      setIsReady(true);
    }, delay);

    return () => clearTimeout(delayTimer);
  }, [delay]);

  useEffect(() => {
    if (!isReady || hasShown) return;

    const handleMouseLeave = (e: MouseEvent) => {
      // Detect mouse leaving viewport from top
      // This is the most reliable exit intent signal
      if (e.clientY <= threshold && e.relatedTarget === null) {
        setShowPopup(true);
        setHasShown(true);
        if (typeof window !== 'undefined') {
          sessionStorage.setItem('exitIntentShown', 'true');
        }
      }
    };

    // For mobile: Detect when user scrolls to top aggressively
    // Commented out by default - uncomment if you want mobile scroll detection
    /*
    let lastScrollY = 0
    const handleScroll = () => {
      const currentScrollY = window.scrollY

      // If user scrolls up quickly to the top, consider it exit intent
      if (currentScrollY === 0 && lastScrollY > 100) {
        setShowPopup(true)
        setHasShown(true)
        sessionStorage.setItem('exitIntentShown', 'true')
      }

      lastScrollY = currentScrollY
    }
    */

    // Desktop: Mouse leave detection
    document.addEventListener('mouseleave', handleMouseLeave);

    // Mobile: Scroll detection (optional, commented out by default)
    // window.addEventListener('scroll', handleScroll)

    return () => {
      document.removeEventListener('mouseleave', handleMouseLeave);
      // window.removeEventListener('scroll', handleScroll)
    };
  }, [isReady, hasShown, threshold]);

  // Manual trigger (can be used programmatically)
  const triggerPopup = () => {
    if (!hasShown) {
      setShowPopup(true);
      setHasShown(true);
      if (typeof window !== 'undefined') {
        sessionStorage.setItem('exitIntentShown', 'true');
      }
    }
  };

  return { showPopup, setShowPopup, triggerPopup };
}
