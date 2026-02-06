'use client';

import { GoogleOAuthProvider } from '@react-oauth/google';
import { Building, Eye, EyeOff, LogIn } from 'lucide-react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useState, Suspense } from 'react';

import GoogleSignInButton from '@/components/auth/GoogleSignInButton';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { logger } from '@/lib/logger';
import type { Station, StationLoginResponse } from '@/services/api';
import { authService, tokenManager } from '@/services/api';

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuth();
  const [step, setStep] = useState<'login' | 'station'>('login');
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [userStations, setUserStations] = useState<Station[]>([]);
  const [selectedStation, setSelectedStation] = useState<string>('');
  const [tempToken, setTempToken] = useState<string>('');
  const [isOAuthFlow, setIsOAuthFlow] = useState(false);
  const [oauthEmail, setOauthEmail] = useState<string>('');

  // Handle OAuth redirect with token and email params
  useEffect(() => {
    const oauthToken = searchParams.get('oauth_token');
    const email = searchParams.get('email');

    if (oauthToken && email) {
      console.log(
        '[Login] OAuth redirect detected, loading stations for:',
        email
      );
      setIsOAuthFlow(true);
      setOauthEmail(email);
      setTempToken(oauthToken);
      setFormData(prev => ({ ...prev, email }));

      // Fetch stations for OAuth user
      (async () => {
        setLoading(true);
        try {
          const stationsResponse = await authService.getUserStations(email);
          const rawData = stationsResponse.data as any;
          const stations = rawData?.data?.stations || rawData?.stations || [];
          console.log('[Login] OAuth user stations:', stations);

          if (stations.length > 0) {
            setUserStations(stations);
            setStep('station');
          } else {
            setError('No stations assigned to your account.');
          }
        } catch (err: any) {
          logger.error(err, { context: 'oauth_stations', email });
          setError('Failed to load stations. Please try again.');
        } finally {
          setLoading(false);
        }
      })();
    }
  }, [searchParams]);

  const handleInitialLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await authService.login(
        formData.email,
        formData.password
      );

      if (response.data?.access_token) {
        setTempToken(response.data.access_token);

        // Store refresh token for token refresh
        if (response.data?.refresh_token) {
          tokenManager.setRefreshToken(response.data.refresh_token);
          console.log('[Login] Refresh token stored');
        }

        // Get user's stations (pass email, not token!)
        const stationsResponse = await authService.getUserStations(
          formData.email
        );

        // Extract stations from nested response structure
        // Backend returns: { success: true, data: { stations: [...] } }
        // After apiFetch wrapping: { data: { success: true, data: { stations: [...] } }, success: true }
        const rawData = stationsResponse.data as any;
        const stations = rawData?.data?.stations || rawData?.stations || [];

        if (stations.length > 1) {
          // Multiple stations - show station selection
          setUserStations(stations);
          setStep('station');
        } else if (stations.length === 1) {
          // Single station - auto-select and continue
          const station = stations[0];
          await completeStationLogin(
            response.data.access_token,
            station.id.toString()
          );
        } else {
          // No stations assigned
          setError(
            'No stations assigned to your account. Please contact an administrator.'
          );
        }
      } else {
        setError('Login failed. Please try again.');
      }
    } catch (err: any) {
      logger.error(err as Error, { context: 'login', email: formData.email });
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const completeStationLogin = async (token: string, stationId: string) => {
    setLoading(true);
    setError('');

    try {
      // For now, since we already have the token and station info,
      // we'll call the station login with the original credentials
      const response = await authService.stationLogin(
        formData.email,
        formData.password,
        stationId // Pass UUID string directly, no parseInt
      );

      console.log(
        'Station login full response:',
        JSON.stringify(response, null, 2)
      );

      // Check if the API call itself failed (network error, CORS, etc.)
      if (!response.success) {
        console.error('Station login API call failed:', response.error);
        setError(response.error || 'Station login failed. Please try again.');
        return;
      }

      // Backend wraps response in { success: true, data: StationLoginResponse }
      // apiFetch adds another layer: { data: backendResponse, success: true }
      // So the actual structure is:
      //   response.data = { success: true, data: { access_token, station_context } }
      // OR if backend returns flat response:
      //   response.data = { access_token, station_context }
      // We need to handle both cases
      const backendResponse = response.data as unknown as Record<
        string,
        unknown
      >;
      const loginData =
        (backendResponse?.data as StationLoginResponse) ||
        (backendResponse as unknown as StationLoginResponse);

      console.log('Extracted loginData:', JSON.stringify(loginData, null, 2));

      if (loginData?.access_token && loginData?.station_context) {
        // Pass refresh_token to login() so token refresh works correctly
        // This is CRITICAL - without it, WebSocket reconnections fail after token expires
        login(
          loginData.access_token,
          loginData.station_context,
          loginData.refresh_token
        );
        console.log(
          '[StationLogin] Refresh token passed to login:',
          !!loginData.refresh_token
        );
        router.push('/');
      } else {
        console.error('Station login response missing data:', response);
        setError(
          'Station login failed: Missing access token or station context.'
        );
      }
    } catch (err: any) {
      logger.error(err as Error, {
        context: 'station_login',
        email: formData.email,
        station_id: stationId,
      });
      setError(err.message || 'Station login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // OAuth-specific station login (uses OAuth token instead of password)
  const completeOAuthStationLogin = async (
    oauthToken: string,
    stationId: string
  ) => {
    setLoading(true);
    setError('');

    try {
      console.log('[Login] OAuth station login for station:', stationId);

      // Call station-login endpoint with OAuth token
      // NOTE: station_auth router is mounted at /api/station, not /api/auth
      const apiUrl =
        process.env.NEXT_PUBLIC_API_URL || 'https://mhapi.mysticdatanode.net';
      const response = await fetch(`${apiUrl}/api/station/station-login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${oauthToken}`,
        },
        body: JSON.stringify({
          email: oauthEmail, // Required for validation
          station_id: stationId,
          oauth_token: oauthToken,
        }),
      });

      const data = await response.json();
      console.log('[Login] OAuth station login response:', data);

      if (!response.ok) {
        throw new Error(data.detail || 'Station login failed');
      }

      // Extract login data (handle nested response structure)
      const loginData = data?.data || data;

      if (loginData?.access_token && loginData?.station_context) {
        console.log('[Login] OAuth station login successful');
        login(loginData.access_token, loginData.station_context);
        router.push('/');
      } else {
        console.error('[Login] OAuth station login missing data:', data);
        setError(
          'Station login failed: Missing access token or station context.'
        );
      }
    } catch (err: any) {
      logger.error(err as Error, {
        context: 'oauth_station_login',
        email: oauthEmail,
        station_id: stationId,
      });
      setError(err.message || 'Station login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleStationSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedStation) {
      setError('Please select a station.');
      return;
    }

    // Use OAuth-specific login if in OAuth flow, otherwise use password-based login
    if (isOAuthFlow) {
      await completeOAuthStationLogin(tempToken, selectedStation);
    } else {
      await completeStationLogin(tempToken, selectedStation);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const renderLoginForm = () => (
    <form className="mt-8 space-y-6" onSubmit={handleInitialLogin}>
      <div className="rounded-md shadow-sm -space-y-px">
        <div>
          <label htmlFor="email" className="sr-only">
            Email address
          </label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
            placeholder="Email address"
            value={formData.email}
            onChange={handleInputChange}
          />
        </div>
        <div className="relative">
          <label htmlFor="password" className="sr-only">
            Password
          </label>
          <input
            id="password"
            name="password"
            type={showPassword ? 'text' : 'password'}
            autoComplete="current-password"
            required
            className="appearance-none rounded-none relative block w-full px-3 py-2 pr-10 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
            placeholder="Password"
            value={formData.password}
            onChange={handleInputChange}
          />
          <button
            type="button"
            className="absolute inset-y-0 right-0 pr-3 flex items-center"
            onClick={() => setShowPassword(!showPassword)}
            aria-label={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? (
              <EyeOff className="h-4 w-4 text-gray-400" aria-hidden="true" />
            ) : (
              <Eye className="h-4 w-4 text-gray-400" aria-hidden="true" />
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md text-sm">
          {error}
        </div>
      )}

      <div>
        <Button
          type="submit"
          disabled={loading}
          variant="ghost"
          className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md !text-white !bg-blue-600 hover:!bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <div className="flex items-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Signing in...
            </div>
          ) : (
            'Sign in'
          )}
        </Button>
      </div>

      {/* Divider */}
      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-gray-300"></div>
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-2 bg-gray-50 text-gray-500">
            Or continue with
          </span>
        </div>
      </div>

      {/* Google OAuth Button */}
      <GoogleOAuthProvider
        clientId={process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || ''}
      >
        <GoogleSignInButton />
      </GoogleOAuthProvider>
    </form>
  );

  const renderStationSelection = () => (
    <form className="mt-8 space-y-6" onSubmit={handleStationSubmit}>
      <div>
        <label
          htmlFor="station"
          className="block text-sm font-medium text-gray-700 mb-2"
        >
          Select Station
        </label>
        <select
          id="station"
          value={selectedStation}
          onChange={e => setSelectedStation(e.target.value)}
          className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          required
        >
          <option value="">Choose a station...</option>
          {userStations.map(station => (
            <option key={station.id} value={station.id}>
              {station.name} - {station.location}
            </option>
          ))}
        </select>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md text-sm">
          {error}
        </div>
      )}

      <div className="flex space-x-3">
        <Button
          type="button"
          variant="outline"
          onClick={() => {
            setStep('login');
            setError('');
          }}
          className="flex-1"
        >
          Back
        </Button>
        <Button
          type="submit"
          disabled={loading || !selectedStation}
          className="flex-1"
        >
          {loading ? (
            <div className="flex items-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Accessing...
            </div>
          ) : (
            'Access Station'
          )}
        </Button>
      </div>
    </form>
  );

  return (
    <main className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-12 w-12 bg-blue-600 rounded-lg flex items-center justify-center">
            {step === 'login' ? (
              <LogIn className="h-6 w-6 text-white" />
            ) : (
              <Building className="h-6 w-6 text-white" />
            )}
          </div>
          <h1 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            MyHibachi Admin
          </h1>
          <p className="mt-2 text-center text-sm text-gray-600">
            {step === 'login'
              ? 'Sign in to your admin account'
              : 'Select your station to continue'}
          </p>
        </div>

        {step === 'login' ? renderLoginForm() : renderStationSelection()}
      </div>
    </main>
  );
}
// Wrap with Suspense because we use useSearchParams
export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </main>
      }
    >
      <LoginContent />
    </Suspense>
  );
}
