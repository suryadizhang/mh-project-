'use client';

import { AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useState } from 'react';

import { useAuth } from '@/contexts/AuthContext';
import { logger } from '@/lib/logger';

/**
 * Inner component that uses useSearchParams
 * Must be wrapped in Suspense boundary for Next.js 13+ App Router
 */
function CallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuth();
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>(
    'processing'
  );
  const [message, setMessage] = useState('Processing your login...');

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Get token and error from URL params
        const token = searchParams.get('token');
        const error = searchParams.get('error');

        console.log('[OAuth Callback] Processing callback...', {
          hasToken: !!token,
          hasError: !!error,
        });

        if (error) {
          setStatus('error');
          setMessage(decodeURIComponent(error));
          logger.error(new Error(`OAuth error: ${error}`), {
            context: 'oauth_callback',
          });
          return;
        }

        if (!token) {
          setStatus('error');
          setMessage('No authentication token received. Please try again.');
          logger.error(new Error('No token in OAuth callback'), {
            context: 'oauth_callback',
          });
          return;
        }

        console.log(
          '[OAuth Callback] Token received, storing in localStorage as admin_token'
        );

        // Store token in localStorage with correct key that tokenManager expects
        // CRITICAL: Must use 'admin_token' key to match tokenManager.getToken() in api.ts
        localStorage.setItem('admin_token', token);

        console.log('[OAuth Callback] Calling /api/auth/me to validate token');

        // Verify token is valid by making a test request
        // CRITICAL: Auth router is mounted at /api/auth, NOT /api/v1/auth
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/auth/me`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        console.log('[OAuth Callback] /api/auth/me response:', response.status);

        if (response.ok) {
          const userData = await response.json();
          console.log('[OAuth Callback] User data received:', userData);
          const userEmail = userData.data?.email || userData.email;

          if (!userEmail) {
            throw new Error('User email not found in response');
          }

          // Fetch user's stations to determine if station selection is needed
          console.log('[OAuth Callback] Fetching stations for:', userEmail);
          const stationsResponse = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/api/station/user-stations?email=${encodeURIComponent(userEmail)}`,
            {
              headers: {
                Authorization: `Bearer ${token}`,
              },
            }
          );

          if (!stationsResponse.ok) {
            throw new Error('Failed to fetch user stations');
          }

          const stationsData = await stationsResponse.json();
          console.log('[OAuth Callback] Stations response:', stationsData);

          // Extract stations from response (handle nested structure)
          const stations =
            stationsData?.data?.stations ||
            stationsData?.stations ||
            stationsData?.data ||
            [];
          console.log('[OAuth Callback] Extracted stations:', stations);

          if (stations.length === 0) {
            setStatus('error');
            setMessage(
              'No stations assigned to your account. Please contact an administrator.'
            );
            setTimeout(() => router.push('/login'), 3000);
            return;
          }

          if (stations.length === 1) {
            // Single station - auto-select and complete login
            const station = stations[0];
            console.log(
              '[OAuth Callback] Auto-selecting single station:',
              station
            );

            // Call station-login to get proper station context
            const stationLoginResponse = await fetch(
              `${process.env.NEXT_PUBLIC_API_URL}/api/auth/station-login`,
              {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({
                  email: userEmail,
                  station_id: station.id.toString(),
                  oauth_token: token, // Pass OAuth token for verification
                }),
              }
            );

            if (!stationLoginResponse.ok) {
              throw new Error('Station login failed');
            }

            const stationLoginData = await stationLoginResponse.json();
            console.log(
              '[OAuth Callback] Station login response:',
              stationLoginData
            );

            // Extract login data (handle nested structure)
            const loginData = stationLoginData?.data || stationLoginData;
            if (loginData?.access_token && loginData?.station_context) {
              login(loginData.access_token, loginData.station_context);
              setStatus('success');
              setMessage(
                `Welcome back, ${userData.data?.full_name || 'User'}!`
              );
              setTimeout(() => router.push('/'), 1000);
            } else {
              throw new Error(
                'Station login response missing access_token or station_context'
              );
            }
          } else {
            // Multiple stations - redirect to login page for station selection
            console.log(
              '[OAuth Callback] Multiple stations, redirecting to station selection'
            );
            setStatus('success');
            setMessage('Multiple stations found. Please select a station.');

            // Redirect to login page with OAuth token for station selection
            setTimeout(() => {
              router.push(
                `/login?oauth_token=${encodeURIComponent(token)}&email=${encodeURIComponent(userEmail)}`
              );
            }, 1000);
          }
        } else {
          throw new Error('Token validation failed');
        }
      } catch (err) {
        console.error('[OAuth Callback] Error:', err);
        logger.error(err as Error, { context: 'oauth_callback' });
        setStatus('error');
        setMessage('Authentication failed. Please try again.');

        // Redirect to login after 3 seconds
        setTimeout(() => {
          router.push('/login');
        }, 3000);
      }
    };

    handleCallback();
  }, [searchParams, router]);

  return (
    <div className="flex flex-col items-center justify-center space-y-4">
      {status === 'processing' && (
        <>
          <Loader2 className="h-12 w-12 text-blue-600 animate-spin" />
          <h2 className="text-xl font-semibold text-gray-900">
            Completing sign in...
          </h2>
          <p className="text-sm text-gray-600 text-center">{message}</p>
        </>
      )}

      {status === 'success' && (
        <>
          <CheckCircle className="h-12 w-12 text-green-600" />
          <h2 className="text-xl font-semibold text-gray-900">Success!</h2>
          <p className="text-sm text-gray-600 text-center">{message}</p>
          <p className="text-xs text-gray-500">Redirecting to dashboard...</p>
        </>
      )}

      {status === 'error' && (
        <>
          <AlertCircle className="h-12 w-12 text-red-600" />
          <h2 className="text-xl font-semibold text-gray-900">
            Authentication Failed
          </h2>
          <p className="text-sm text-gray-600 text-center">{message}</p>
          <p className="text-xs text-gray-500">Redirecting to login...</p>
        </>
      )}
    </div>
  );
}

/**
 * Loading fallback for Suspense boundary
 */
function CallbackLoading() {
  return (
    <div className="flex flex-col items-center justify-center space-y-4">
      <Loader2 className="h-12 w-12 text-blue-600 animate-spin" />
      <h2 className="text-xl font-semibold text-gray-900">Loading...</h2>
      <p className="text-sm text-gray-600 text-center">
        Preparing authentication...
      </p>
    </div>
  );
}

/**
 * OAuth Callback Page
 *
 * Handles the redirect from Google OAuth and validates the token.
 * Uses Suspense boundary for useSearchParams (required in Next.js 13+ App Router)
 */
export default function OAuthCallbackPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
        <Suspense fallback={<CallbackLoading />}>
          <CallbackContent />
        </Suspense>
      </div>
    </div>
  );
}
