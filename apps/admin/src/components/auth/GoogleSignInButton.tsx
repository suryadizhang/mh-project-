'use client';

import { useGoogleLogin } from '@react-oauth/google';
import { Loader2 } from 'lucide-react';
import { useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import { logger } from '@/lib/logger';

/**
 * Generate a state token that includes CSRF protection and the origin URL.
 * This allows the backend callback to redirect back to the correct frontend (admin vs customer).
 *
 * Format: URL-safe base64 encoded JSON: {"csrf": "<random>", "origin": "<current_origin>"}
 */
function generateStateWithOrigin(): string {
  // Generate a random CSRF token
  const csrfToken = Array.from(crypto.getRandomValues(new Uint8Array(24)))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');

  // Get current origin (e.g., https://admin.mysticdatanode.net)
  const origin = typeof window !== 'undefined' ? window.location.origin : '';

  // Create state object
  const stateData = {
    csrf: csrfToken,
    origin: origin,
  };

  // Encode as URL-safe base64
  const jsonString = JSON.stringify(stateData);
  // Use btoa for base64 encoding, then make URL-safe
  const base64 = btoa(jsonString)
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');

  return base64;
}

export default function GoogleSignInButton() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Generate state token once per component mount (includes origin)
  const stateToken = useMemo(() => generateStateWithOrigin(), []);

  // Trim API URL to remove any accidental trailing spaces from env var
  const apiUrl = (process.env.NEXT_PUBLIC_API_URL || '').trim();

  const handleGoogleLogin = useGoogleLogin({
    flow: 'auth-code',
    ux_mode: 'redirect',
    redirect_uri: `${apiUrl}/auth/google/callback`,
    // Include state with CSRF token and origin URL for proper redirect after callback
    state: stateToken,
    // Always show account chooser so user can pick which Google account to use
    select_account: true,
    onError: error => {
      logger.error(new Error(`Google OAuth error: ${JSON.stringify(error)}`), {
        context: 'google_oauth_login',
      });
      setError('Failed to sign in with Google. Please try again.');
      setLoading(false);
    },
  });

  const handleClick = () => {
    setLoading(true);
    setError('');
    try {
      handleGoogleLogin();
    } catch (err) {
      logger.error(err as Error, { context: 'google_oauth_click' });
      setError('Failed to initiate Google sign-in. Please try again.');
      setLoading(false);
    }
  };

  return (
    <div className="space-y-2">
      <Button
        type="button"
        variant="outline"
        onClick={handleClick}
        disabled={loading}
        className="w-full flex items-center justify-center space-x-2 py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Redirecting to Google...</span>
          </>
        ) : (
          <>
            <svg className="h-5 w-5" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>
            <span>Sign in with Google</span>
          </>
        )}
      </Button>
      {error && <p className="text-sm text-red-600 text-center">{error}</p>}
    </div>
  );
}
