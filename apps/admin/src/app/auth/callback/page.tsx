'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Loader2, AlertCircle, CheckCircle } from 'lucide-react';
import { logger } from '@/lib/logger';

export default function OAuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');
  const [message, setMessage] = useState('Processing your login...');

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Get token and error from URL params
        const token = searchParams.get('token');
        const error = searchParams.get('error');
        const email = searchParams.get('email');

        if (error) {
          setStatus('error');
          setMessage(decodeURIComponent(error));
          logger.error(new Error(`OAuth error: ${error}`), { context: 'oauth_callback' });
          return;
        }

        if (!token) {
          setStatus('error');
          setMessage('No authentication token received. Please try again.');
          logger.error(new Error('No token in OAuth callback'), { context: 'oauth_callback' });
          return;
        }

        // Store token in localStorage
        localStorage.setItem('access_token', token);
        
        // Verify token is valid by making a test request
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/me`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const userData = await response.json();
          setStatus('success');
          setMessage(`Welcome back, ${userData.data?.full_name || 'User'}!`);
          
          // Redirect to dashboard after 1 second
          setTimeout(() => {
            router.push('/');
          }, 1000);
        } else {
          throw new Error('Token validation failed');
        }
      } catch (err) {
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
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
        <div className="flex flex-col items-center justify-center space-y-4">
          {status === 'processing' && (
            <>
              <Loader2 className="h-12 w-12 text-blue-600 animate-spin" />
              <h2 className="text-xl font-semibold text-gray-900">
                Completing sign in...
              </h2>
              <p className="text-sm text-gray-600 text-center">
                {message}
              </p>
            </>
          )}

          {status === 'success' && (
            <>
              <CheckCircle className="h-12 w-12 text-green-600" />
              <h2 className="text-xl font-semibold text-gray-900">
                Success!
              </h2>
              <p className="text-sm text-gray-600 text-center">
                {message}
              </p>
              <p className="text-xs text-gray-500">
                Redirecting to dashboard...
              </p>
            </>
          )}

          {status === 'error' && (
            <>
              <AlertCircle className="h-12 w-12 text-red-600" />
              <h2 className="text-xl font-semibold text-gray-900">
                Authentication Failed
              </h2>
              <p className="text-sm text-gray-600 text-center">
                {message}
              </p>
              <p className="text-xs text-gray-500">
                Redirecting to login...
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
