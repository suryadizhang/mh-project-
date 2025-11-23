'use client';

import { useEffect, useState } from 'react';
import { AlertTriangle, Clock, X } from 'lucide-react';

interface RateLimitInfo {
  endpoint: string;
  waitTime?: number;
  waitSeconds?: number;
  category?: string;
  remaining?: number;
  until?: number;
}

/**
 * RateLimitBanner Component
 *
 * Displays a warning banner when rate limits are exceeded.
 * Shows countdown timer and allows manual dismissal.
 * Listens for custom events from the API client.
 *
 * Events:
 * - rate-limit-exceeded: Client-side rate limit (before request)
 * - server-rate-limit-exceeded: Server-side 429 response
 *
 * Features:
 * - Animated progress bar showing remaining time
 * - Color-coded countdown (red <10s, yellow 10-30s, green >30s)
 * - Auto-dismiss when cooldown expires
 * - Manual dismiss option
 * - Responsive design
 */
export default function RateLimitBanner() {
  const [isVisible, setIsVisible] = useState(false);
  const [rateLimitInfo, setRateLimitInfo] = useState<RateLimitInfo | null>(null);
  const [remainingSeconds, setRemainingSeconds] = useState(0);
  const [progress, setProgress] = useState(100);

  useEffect(() => {
    // Handler for client-side rate limit exceeded
    const handleClientRateLimit = (event: Event) => {
      const customEvent = event as CustomEvent<RateLimitInfo>;
      const info = customEvent.detail;

      setRateLimitInfo(info);
      setRemainingSeconds(info.waitTime || info.waitSeconds || 0);
      setIsVisible(true);
    };

    // Handler for server-side rate limit exceeded (429)
    const handleServerRateLimit = (event: Event) => {
      const customEvent = event as CustomEvent<RateLimitInfo>;
      const info = customEvent.detail;

      setRateLimitInfo(info);

      // Calculate remaining seconds from 'until' timestamp
      if (info.until) {
        const remaining = Math.ceil((info.until - Date.now()) / 1000);
        setRemainingSeconds(Math.max(0, remaining));
      } else {
        setRemainingSeconds(info.waitSeconds || 60);
      }

      setIsVisible(true);
    };

    // Add event listeners
    window.addEventListener('rate-limit-exceeded', handleClientRateLimit);
    window.addEventListener('server-rate-limit-exceeded', handleServerRateLimit);

    // Cleanup
    return () => {
      window.removeEventListener('rate-limit-exceeded', handleClientRateLimit);
      window.removeEventListener('server-rate-limit-exceeded', handleServerRateLimit);
    };
  }, []);

  // Countdown timer effect
  useEffect(() => {
    if (!isVisible || remainingSeconds <= 0) {
      return;
    }

    const interval = setInterval(() => {
      setRemainingSeconds((prev) => {
        const newValue = prev - 1;

        if (newValue <= 0) {
          setIsVisible(false);
          return 0;
        }

        // Update progress bar
        const totalSeconds = rateLimitInfo?.waitTime || rateLimitInfo?.waitSeconds || 60;
        setProgress((newValue / totalSeconds) * 100);

        return newValue;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isVisible, remainingSeconds, rateLimitInfo]);

  // Manual dismiss
  const handleDismiss = () => {
    setIsVisible(false);
    setRemainingSeconds(0);
  };

  if (!isVisible || !rateLimitInfo) {
    return null;
  }

  // Format countdown display
  const formatTime = (seconds: number): string => {
    if (seconds < 60) {
      return `${seconds}s`;
    }

    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  // Color coding based on remaining time
  const getColorClass = (): string => {
    if (remainingSeconds < 10) {
      return 'bg-red-50 border-red-200 text-red-800';
    }
    if (remainingSeconds < 30) {
      return 'bg-yellow-50 border-yellow-200 text-yellow-800';
    }
    return 'bg-blue-50 border-blue-200 text-blue-800';
  };

  const getProgressColorClass = (): string => {
    if (remainingSeconds < 10) {
      return 'bg-red-500';
    }
    if (remainingSeconds < 30) {
      return 'bg-yellow-500';
    }
    return 'bg-blue-500';
  };

  const getIconColorClass = (): string => {
    if (remainingSeconds < 10) {
      return 'text-red-500';
    }
    if (remainingSeconds < 30) {
      return 'text-yellow-500';
    }
    return 'text-blue-500';
  };

  // Get user-friendly endpoint name
  const getEndpointDisplay = (): string => {
    const endpoint = rateLimitInfo.endpoint || '';
    const category = rateLimitInfo.category || '';

    if (category === 'booking_create') return 'Booking Creation';
    if (category === 'booking_update') return 'Booking Updates';
    if (category === 'payment') return 'Payment Processing';
    if (category === 'search') return 'Search';
    if (category === 'chat') return 'Chat';

    // Fallback to endpoint path
    if (endpoint.includes('booking')) return 'Bookings';
    if (endpoint.includes('payment')) return 'Payments';
    if (endpoint.includes('search')) return 'Search';
    if (endpoint.includes('chat')) return 'Chat';

    return 'API Requests';
  };

  return (
    <div
      className={`
        fixed top-4 left-1/2 -translate-x-1/2 z-50 w-full max-w-2xl
        mx-auto px-4 transition-all duration-300 ease-in-out
        ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-4'}
      `}
      role="alert"
      aria-live="assertive"
    >
      <div
        className={`
          relative rounded-lg border-2 shadow-lg p-4
          ${getColorClass()}
        `}
      >
        {/* Close button */}
        <button
          onClick={handleDismiss}
          className="absolute top-2 right-2 p-1 rounded-full hover:bg-black/10 transition-colors"
          aria-label="Dismiss rate limit warning"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-start gap-3 pr-8">
          {/* Icon */}
          <div className="flex-shrink-0 mt-0.5">
            <AlertTriangle className={`w-6 h-6 ${getIconColorClass()}`} />
          </div>

          {/* Content */}
          <div className="flex-1">
            <h3 className="font-semibold text-lg mb-1">
              Rate Limit Reached
            </h3>

            <p className="text-sm mb-3">
              {"You've reached the limit for"} <strong>{getEndpointDisplay()}</strong>.
              Please wait before trying again.
            </p>

            {/* Countdown */}
            <div className="flex items-center gap-2 mb-3">
              <Clock className={`w-4 h-4 ${getIconColorClass()}`} />
              <span className="font-mono font-bold text-lg">
                {formatTime(remainingSeconds)}
              </span>
              <span className="text-sm opacity-75">remaining</span>
            </div>

            {/* Progress bar */}
            <div className="w-full bg-white/50 rounded-full h-2 overflow-hidden">
              <div
                className={`h-full transition-all duration-1000 ease-linear ${getProgressColorClass()}`}
                style={{ width: `${progress}%` }}
              />
            </div>

            {/* Additional info */}
            {rateLimitInfo.remaining !== undefined && (
              <p className="text-xs mt-2 opacity-75">
                Requests remaining: {rateLimitInfo.remaining}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
