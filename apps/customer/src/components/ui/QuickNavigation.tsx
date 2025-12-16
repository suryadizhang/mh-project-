'use client';

import React, { useEffect, useState } from 'react';
import { toast } from '@/components/ui/toaster';

interface QuickNavigationProps {
  showProgress?: boolean;
  showTableOfContents?: boolean;
  className?: string;
}

const QuickNavigation: React.FC<QuickNavigationProps> = ({
  showProgress = true,
  showTableOfContents = false,
  className = '',
}) => {
  const [scrollProgress, setScrollProgress] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const [headings, setHeadings] = useState<Array<{ id: string; text: string; level: number }>>([]);

  // Track scroll progress and visibility
  useEffect(() => {
    const handleScroll = () => {
      const scrollTop = window.pageYOffset;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      const progress = (scrollTop / docHeight) * 100;

      setScrollProgress(Math.min(progress, 100));
      setIsVisible(scrollTop > 300);
    };

    // Extract headings for table of contents
    if (showTableOfContents) {
      const extractHeadings = () => {
        const headingElements = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
        const headingsArray = Array.from(headingElements).map((heading, index) => {
          // Create ID if it doesn't exist
          if (!heading.id) {
            heading.id = `heading-${index}`;
          }

          return {
            id: heading.id,
            text: heading.textContent || '',
            level: parseInt(heading.tagName.charAt(1)),
          };
        });

        setHeadings(headingsArray);
      };

      // Extract headings after a short delay to ensure content is loaded
      const timeoutId = setTimeout(extractHeadings, 1000);
      return () => clearTimeout(timeoutId);
    }

    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll(); // Initial call

    return () => window.removeEventListener('scroll', handleScroll);
  }, [showTableOfContents]);

  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth',
    });
  };

  const scrollToBottom = () => {
    window.scrollTo({
      top: document.documentElement.scrollHeight,
      behavior: 'smooth',
    });
  };

  const scrollToHeading = (headingId: string) => {
    const element = document.getElementById(headingId);
    if (element) {
      element.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      });
    }
  };

  if (!isVisible) return null;

  return (
    <div className={`fixed left-4 bottom-36 z-30 sm:left-6 ${className}`}>
      <div className="flex flex-col items-start space-y-3">
        {/* Table of Contents (if enabled) */}
        {showTableOfContents && headings.length > 0 && (
          <div className="max-h-80 max-w-xs overflow-y-auto rounded-lg border border-gray-200 bg-white p-4 shadow-lg">
            <h4 className="mb-3 flex items-center text-sm font-semibold text-gray-900">
              <span className="mr-2">📋</span>
              Table of Contents
            </h4>
            <nav className="space-y-1">
              {headings.map((heading) => (
                <button
                  key={heading.id}
                  onClick={() => scrollToHeading(heading.id)}
                  className={`block w-full rounded px-2 py-1 text-left text-xs transition-colors hover:bg-gray-100 ${heading.level === 1 ? 'font-semibold text-gray-900' : ''} ${heading.level === 2 ? 'ml-2 font-medium text-gray-800' : ''} ${heading.level === 3 ? 'ml-4 text-gray-700' : ''} ${heading.level >= 4 ? 'ml-6 text-gray-600' : ''} `}
                  style={{
                    paddingLeft: `${(heading.level - 1) * 8 + 8}px`,
                  }}
                >
                  {heading.text}
                </button>
              ))}
            </nav>
          </div>
        )}

        {/* Navigation Buttons */}
        <div className="flex flex-col space-y-2">
          {/* Scroll to Top */}
          <button
            onClick={scrollToTop}
            className="group rounded-full border border-gray-200 bg-white p-3 shadow-lg transition-all duration-200 hover:scale-110 hover:border-orange-300 hover:bg-orange-50 hover:shadow-xl"
            title="Scroll to top"
            aria-label="Scroll to top"
          >
            <svg
              className="h-5 w-5 text-gray-600 transition-colors group-hover:text-orange-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 10l7-7m0 0l7 7m-7-7v18"
              />
            </svg>
          </button>

          {/* Reading Progress (if enabled) */}
          {showProgress && (
            <div className="relative">
              <div className="rounded-full border border-gray-200 bg-white p-3 shadow-lg">
                <div className="relative h-8 w-8">
                  {/* Background Circle */}
                  <svg className="h-8 w-8 -rotate-90 transform" viewBox="0 0 32 32">
                    <circle
                      cx="16"
                      cy="16"
                      r="14"
                      stroke="currentColor"
                      strokeWidth="2"
                      fill="none"
                      className="text-gray-200"
                    />
                    {/* Progress Circle */}
                    <circle
                      cx="16"
                      cy="16"
                      r="14"
                      stroke="currentColor"
                      strokeWidth="2"
                      fill="none"
                      strokeDasharray={87.96}
                      strokeDashoffset={87.96 - (87.96 * scrollProgress) / 100}
                      className="text-orange-500 transition-all duration-150 ease-out"
                      strokeLinecap="round"
                    />
                  </svg>

                  {/* Progress Percentage */}
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-xs font-semibold text-gray-700">
                      {Math.round(scrollProgress)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Progress Tooltip */}
              <div className="pointer-events-none absolute top-1/2 right-full mr-3 -translate-y-1/2 transform rounded bg-gray-900 px-2 py-1 text-xs whitespace-nowrap text-white opacity-0 transition-opacity group-hover:opacity-100">
                {Math.round(scrollProgress)}% complete
                <div className="absolute top-1/2 left-full -translate-y-1/2 transform border-4 border-transparent border-l-gray-900"></div>
              </div>
            </div>
          )}

          {/* Scroll to Bottom */}
          <button
            onClick={scrollToBottom}
            className="group rounded-full border border-gray-200 bg-white p-3 shadow-lg transition-all duration-200 hover:scale-110 hover:border-orange-300 hover:bg-orange-50 hover:shadow-xl"
            title="Scroll to bottom"
            aria-label="Scroll to bottom"
          >
            <svg
              className="h-5 w-5 text-gray-600 transition-colors group-hover:text-orange-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 14l-7 7m0 0l-7-7m7 7V4"
              />
            </svg>
          </button>
        </div>

        {/* Additional Actions */}
        <div className="flex space-x-2">
          {/* Print Page */}
          <button
            onClick={() => window.print()}
            className="group rounded-full border border-gray-200 bg-white p-2 shadow-lg transition-all duration-200 hover:scale-110 hover:border-blue-300 hover:bg-blue-50 hover:shadow-xl"
            title="Print page"
            aria-label="Print page"
          >
            <svg
              className="h-4 w-4 text-gray-600 transition-colors group-hover:text-blue-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"
              />
            </svg>
          </button>

          {/* Share Page */}
          <button
            onClick={() => {
              if (navigator.share) {
                navigator.share({
                  title: document.title,
                  url: window.location.href,
                });
              } else {
                // Fallback: copy to clipboard
                navigator.clipboard.writeText(window.location.href);
                toast.success('Link copied to clipboard!');
              }
            }}
            className="group rounded-full border border-gray-200 bg-white p-2 shadow-lg transition-all duration-200 hover:scale-110 hover:border-green-300 hover:bg-green-50 hover:shadow-xl"
            title="Share page"
            aria-label="Share page"
          >
            <svg
              className="h-4 w-4 text-gray-600 transition-colors group-hover:text-green-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

export default QuickNavigation;
