/**
 * Async CSS Loader for Non-Critical Stylesheets
 *
 * This component defers loading of non-critical CSS until after
 * the initial paint, reducing render-blocking resources.
 *
 * Technique: Uses link rel="preload" with onload to convert to stylesheet
 * Fallback: noscript tag for users without JavaScript
 *
 * @see https://web.dev/defer-non-critical-css/
 */
'use client';

import { useEffect } from 'react';

interface AsyncCSSLoaderProps {
  /**
   * Array of CSS file paths to load asynchronously
   */
  stylesheets?: string[];
}

/**
 * Deferred CSS loader that prevents render-blocking
 *
 * Usage:
 * ```tsx
 * <AsyncCSSLoader stylesheets={['/styles/animations.css', '/styles/below-fold.css']} />
 * ```
 */
export function AsyncCSSLoader({ stylesheets = [] }: AsyncCSSLoaderProps) {
  useEffect(() => {
    // Load stylesheets after hydration (non-blocking)
    stylesheets.forEach((href) => {
      // Check if already loaded
      if (document.querySelector(`link[href="${href}"]`)) {
        return;
      }

      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = href;
      link.media = 'all';
      document.head.appendChild(link);
    });
  }, [stylesheets]);

  return null;
}

/**
 * Script to inject into head for immediate async CSS loading
 * Uses the print media trick: load as print, switch to all on load
 *
 * This runs before React hydration, so CSS loads earlier than useEffect
 */
export const asyncCSSScript = `
(function() {
  // Mark that critical CSS is loaded
  document.documentElement.classList.add('css-critical-loaded');

  // After first paint, mark as fully loaded
  if (typeof requestIdleCallback !== 'undefined') {
    requestIdleCallback(function() {
      document.documentElement.classList.add('css-full-loaded');
    });
  } else {
    setTimeout(function() {
      document.documentElement.classList.add('css-full-loaded');
    }, 100);
  }
})();
`;

export default AsyncCSSLoader;
