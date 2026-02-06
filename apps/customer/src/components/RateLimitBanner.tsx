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
      className={`fixed top-4 left-1/2 z-50 mx-auto w-full max-w-2xl -translate-x-1/2 px-4 transition-all duration-300 ease-in-out ${isVisible ? 'translate-y-0 opacity-100' : '-translate-y-4 opacity-0'} `}
      role="alert"
      aria-live="assertive"
    >
      <div className={`relative rounded-lg border-2 p-4 shadow-lg ${getColorClass()} `}>
        {/* Close button */}
        <button
          onClick={handleDismiss}
          className="absolute top-2 right-2 rounded-full p-1 transition-colors hover:bg-black/10"
          aria-label="Dismiss rate limit warning"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="flex items-start gap-3 pr-8">
          {/* Icon */}
          <div className="mt-0.5 flex-shrink-0">
            <AlertTriangle className={`h-6 w-6 ${getIconColorClass()}`} />
          </div>

          {/* Content */}
          <div className="flex-1">
            <h3 className="mb-1 text-lg font-semibold">Rate Limit Reached</h3>

            <p className="mb-3 text-sm">
              {"You've reached the limit for"} <strong>{getEndpointDisplay()}</strong>. Please wait
              before trying again.
            </p>

            {/* Countdown */}
            <div className="mb-3 flex items-center gap-2">
              <Clock className={`h-4 w-4 ${getIconColorClass()}`} />
              <span className="font-mono text-lg font-bold">{formatTime(remainingSeconds)}</span>
              <span className="text-sm opacity-75">remaining</span>
            </div>

            {/* Progress bar */}
            <div className="h-2 w-full overflow-hidden rounded-full bg-white/50">
              <div
                className={`h-full transition-all duration-1000 ease-linear ${getProgressColorClass()}`}
                style={{ width: `${progress}%` }}
              />
            </div>

            {/* Additional info */}
            {rateLimitInfo.remaining !== undefined && (
              <p className="mt-2 text-xs opacity-75">
                Requests remaining: {rateLimitInfo.remaining}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
