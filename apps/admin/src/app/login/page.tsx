'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Eye, EyeOff, LogIn, Building } from 'lucide-react';
import { authService, stationService } from '@/services/api';
import type { Station } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';
import { logger } from '@/lib/logger';

export default function LoginPage() {
  const router = useRouter();
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

  const handleInitialLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await authService.login(formData.email, formData.password);
      
      if (response.data?.access_token) {
        setTempToken(response.data.access_token);
        
        // Get user's stations
        const stationsResponse = await authService.getUserStations(response.data.access_token);
        
        if (stationsResponse.data && stationsResponse.data.length > 1) {
          // Multiple stations - show station selection
          setUserStations(stationsResponse.data);
          setStep('station');
        } else if (stationsResponse.data && stationsResponse.data.length === 1) {
          // Single station - auto-select and continue
          const station = stationsResponse.data[0];
          await completeStationLogin(response.data.access_token, station.id.toString());
        } else {
          // No stations assigned
          setError('No stations assigned to your account. Please contact an administrator.');
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
        parseInt(stationId)
      );
      
      if (response.data?.access_token && response.data?.station_context) {
        login(response.data.access_token, response.data.station_context);
        router.push('/');
      } else {
        setError('Station login failed. Please try again.');
      }
    } catch (err: any) {
      logger.error(err as Error, { context: 'station_login', email: formData.email, station_id: stationId });
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

    await completeStationLogin(tempToken, selectedStation);
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
          >
            {showPassword ? (
              <EyeOff className="h-4 w-4 text-gray-400" />
            ) : (
              <Eye className="h-4 w-4 text-gray-400" />
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
          className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
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

      <div className="text-center">
        <p className="text-sm text-gray-600">
          Demo credentials:
        </p>
        <p className="text-xs text-gray-500 mt-1">
          Email: admin@myhibachi.com | Password: admin123
        </p>
      </div>
    </form>
  );

  const renderStationSelection = () => (
    <form className="mt-8 space-y-6" onSubmit={handleStationSubmit}>
      <div>
        <label htmlFor="station" className="block text-sm font-medium text-gray-700 mb-2">
          Select Station
        </label>
        <select
          id="station"
          value={selectedStation}
          onChange={(e) => setSelectedStation(e.target.value)}
          className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          required
        >
          <option value="">Choose a station...</option>
          {userStations.map((station) => (
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
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-12 w-12 bg-blue-600 rounded-lg flex items-center justify-center">
            {step === 'login' ? (
              <LogIn className="h-6 w-6 text-white" />
            ) : (
              <Building className="h-6 w-6 text-white" />
            )}
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            MyHibachi Admin
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            {step === 'login' 
              ? 'Sign in to your admin account'
              : 'Select your station to continue'
            }
          </p>
        </div>
        
        {step === 'login' ? renderLoginForm() : renderStationSelection()}
      </div>
    </div>
  );
}