'use client';

import { AlertTriangle, CheckCircle, MapPin, Save, Settings } from 'lucide-react';
import { useEffect, useState } from 'react';

import { Button } from '@/components/ui/button';
import { apiFetch } from '@/lib/api';

interface CompanySettings {
  baseFeeStructure: {
    freeRadius: number; // Free travel radius in miles
    ratePerMile: number; // Rate per mile beyond free radius
  };
  serviceArea: {
    description: string;
    maxRadius: number; // Maximum service radius
  };
  contactInfo: {
    phone: string;
    email: string;
  };
  lastUpdated: string;
  updatedBy: string;
}

export function BaseLocationManager() {
  const [currentSettings, setCurrentSettings] = useState<CompanySettings>({
    baseFeeStructure: {
      freeRadius: 30,
      ratePerMile: 2,
    },
    serviceArea: {
      description: 'Northern California',
      maxRadius: 150,
    },
    contactInfo: {
      phone: '(916) 740-8768',
      email: 'cs@myhibachichef.com',
    },
    lastUpdated: '2025-01-15',
    updatedBy: 'System Admin',
  });

  const [formData, setFormData] = useState(currentSettings);
  const [isUpdating, setIsUpdating] = useState(false);

  const [updateStatus, setUpdateStatus] = useState<{
    type: 'success' | 'error' | null;
    message: string;
  }>({ type: null, message: '' });

  // Load current settings on component mount
  useEffect(() => {
    loadCurrentSettings();
  }, []);

  const loadCurrentSettings = async () => {
    try {
      const result = await apiFetch('/api/v1/admin/company-settings');
      if (result.success && result.data) {
        setCurrentSettings(result.data as unknown as CompanySettings);
        setFormData(result.data as unknown as CompanySettings);
      }
    } catch (err) {
      console.error('Error loading company settings:', err);
    }
  };

  const handleInputChange = (field: string, value: string | number) => {
    setFormData((prev) => {
      const newData = { ...prev };

      // Handle nested field updates
      if (field.includes('.')) {
        const keys = field.split('.');
        if (keys[0] === 'baseFeeStructure') {
          return {
            ...newData,
            baseFeeStructure: {
              ...newData.baseFeeStructure,
              [keys[1]]: value,
            },
          };
        } else if (keys[0] === 'serviceArea') {
          return {
            ...newData,
            serviceArea: {
              ...newData.serviceArea,
              [keys[1]]: value,
            },
          };
        } else if (keys[0] === 'contactInfo') {
          return {
            ...newData,
            contactInfo: {
              ...newData.contactInfo,
              [keys[1]]: value,
            },
          };
        }
      }

      return newData;
    });
  };

  const updateSettings = async () => {
    setIsUpdating(true);
    setUpdateStatus({ type: null, message: '' });

    try {
      const response = await apiFetch('/api/v1/admin/company-settings', {
        method: 'PUT',
        body: JSON.stringify({
          ...formData,
          updatedBy: 'Super Admin', // In a real app, get this from auth context
          lastUpdated: new Date().toISOString().split('T')[0],
        }),
      });

      if (response.success) {
        const updatedData = response.data;
        setCurrentSettings(updatedData);
        setFormData(updatedData);
        setUpdateStatus({
          type: 'success',
          message: 'Company settings updated successfully! Changes will apply to new quotes.',
        });
      } else {
        setUpdateStatus({
          type: 'error',
          message: response.error || 'Failed to update settings',
        });
      }
    } catch (err) {
      console.error('Update error:', err);
      setUpdateStatus({
        type: 'error',
        message: 'Network error. Please try again.',
      });
    } finally {
      setIsUpdating(false);
    }
  };

  const hasChanges = JSON.stringify(currentSettings) !== JSON.stringify(formData);

  return (
    <div className="space-y-6">
      {/* Current Settings Display */}
      <div className="rounded-lg border border-gray-200 bg-white shadow">
        <div className="border-b border-gray-200 p-6">
          <h3 className="flex items-center text-lg font-semibold text-gray-900">
            <Settings className="mr-2 h-5 w-5" />
            Travel Fee & Service Settings
          </h3>
          <p className="mt-1 text-sm text-gray-600">
            Configure travel fee structure and service area information for customer quotes
          </p>
        </div>

        <div className="p-6">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            {/* Travel Fee Structure */}
            <div className="space-y-4">
              <h4 className="text-md font-medium text-gray-800">Travel Fee Structure</h4>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Free Travel Radius (miles)
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={formData.baseFeeStructure.freeRadius}
                  onChange={(e) =>
                    handleInputChange('baseFeeStructure.freeRadius', parseInt(e.target.value) || 0)
                  }
                  className="w-full rounded-md border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Distance from base location with no travel fee
                </p>
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Rate per Mile ($)
                </label>
                <input
                  type="number"
                  min="0"
                  step="0.5"
                  value={formData.baseFeeStructure.ratePerMile}
                  onChange={(e) =>
                    handleInputChange(
                      'baseFeeStructure.ratePerMile',
                      parseFloat(e.target.value) || 0,
                    )
                  }
                  className="w-full rounded-md border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
                <p className="mt-1 text-xs text-gray-500">Cost per mile beyond free radius</p>
              </div>

              {/* Fee Preview */}
              <div className="rounded-lg bg-blue-50 p-3">
                <h5 className="mb-2 text-sm font-medium text-blue-900">Fee Structure Preview:</h5>
                <div className="space-y-1 text-sm text-blue-800">
                  <p>
                    • 0-{formData.baseFeeStructure.freeRadius} miles: <strong>Free</strong>
                  </p>
                  <p>
                    • Beyond {formData.baseFeeStructure.freeRadius} miles:{' '}
                    <strong>${formData.baseFeeStructure.ratePerMile}/mile</strong>
                  </p>
                  <p>
                    • Example 50 miles: $
                    {Math.max(
                      0,
                      (50 - formData.baseFeeStructure.freeRadius) *
                        formData.baseFeeStructure.ratePerMile,
                    )}
                  </p>
                </div>
              </div>
            </div>

            {/* Service Area */}
            <div className="space-y-4">
              <h4 className="text-md font-medium text-gray-800">Service Area</h4>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Service Area Description
                </label>
                <input
                  type="text"
                  value={formData.serviceArea.description}
                  onChange={(e) => handleInputChange('serviceArea.description', e.target.value)}
                  placeholder="e.g., Northern California, Bay Area..."
                  className="w-full rounded-md border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
                <p className="mt-1 text-xs text-gray-500">General description shown to customers</p>
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Maximum Service Radius (miles)
                </label>
                <input
                  type="number"
                  min="50"
                  max="300"
                  value={formData.serviceArea.maxRadius}
                  onChange={(e) =>
                    handleInputChange('serviceArea.maxRadius', parseInt(e.target.value) || 150)
                  }
                  className="w-full rounded-md border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Maximum distance from base location served
                </p>
              </div>

              {/* Contact Info */}
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Customer Service Phone
                </label>
                <input
                  type="text"
                  value={formData.contactInfo.phone}
                  onChange={(e) => handleInputChange('contactInfo.phone', e.target.value)}
                  placeholder="(916) 740-8768"
                  className="w-full rounded-md border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Customer Service Email
                </label>
                <input
                  type="email"
                  value={formData.contactInfo.email}
                  onChange={(e) => handleInputChange('contactInfo.email', e.target.value)}
                  placeholder="cs@myhibachichef.com"
                  className="w-full rounded-md border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>
            </div>
          </div>

          {/* Current Status */}
          <div className="mt-6 rounded-lg bg-gray-50 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">
                  Last Updated: {currentSettings.lastUpdated} by {currentSettings.updatedBy}
                </p>
              </div>
              <div className="flex items-center space-x-3">
                {hasChanges && (
                  <span className="text-sm font-medium text-orange-600">Unsaved changes</span>
                )}
                <Button
                  onClick={updateSettings}
                  disabled={isUpdating || !hasChanges}
                  className={hasChanges ? 'bg-blue-600 hover:bg-blue-700' : ''}
                >
                  <Save className="mr-2 h-4 w-4" />
                  {isUpdating ? 'Updating...' : 'Save Changes'}
                </Button>
              </div>
            </div>
          </div>

          {/* Update Status */}
          {updateStatus.type && (
            <div
              className={`mt-4 rounded-lg border p-4 ${
                updateStatus.type === 'success'
                  ? 'border-green-200 bg-green-50'
                  : 'border-red-200 bg-red-50'
              }`}
            >
              <div className="flex items-center">
                {updateStatus.type === 'success' ? (
                  <CheckCircle className="mr-2 h-4 w-4 text-green-600" />
                ) : (
                  <AlertTriangle className="mr-2 h-4 w-4 text-red-600" />
                )}
                <span
                  className={`text-sm ${
                    updateStatus.type === 'success' ? 'text-green-800' : 'text-red-800'
                  }`}
                >
                  {updateStatus.message}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Manual Travel Fee Calculator */}
      <div className="rounded-lg border border-gray-200 bg-white shadow">
        <div className="border-b border-gray-200 p-6">
          <h3 className="flex items-center text-lg font-semibold text-gray-900">
            <MapPin className="mr-2 h-5 w-5" />
            Manual Travel Fee Calculator
          </h3>
          <p className="mt-1 text-sm text-gray-600">
            Quick tool for customer service to calculate travel fees manually
          </p>
        </div>

        <div className="p-6">
          <TravelFeeCalculator settings={currentSettings} />
        </div>
      </div>
    </div>
  );
}

// Quick manual calculator component
function TravelFeeCalculator({ settings }: { settings: CompanySettings }) {
  const [distance, setDistance] = useState<number>(0);

  const calculateFee = (miles: number) => {
    if (miles <= settings.baseFeeStructure.freeRadius) {
      return 0;
    }
    return (miles - settings.baseFeeStructure.freeRadius) * settings.baseFeeStructure.ratePerMile;
  };

  const fee = calculateFee(distance);

  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-4">
        <div className="flex-1">
          <label className="mb-1 block text-sm font-medium text-gray-700">Distance (miles)</label>
          <input
            type="number"
            min="0"
            step="0.1"
            value={distance}
            onChange={(e) => setDistance(parseFloat(e.target.value) || 0)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
            placeholder="Enter distance in miles"
          />
        </div>

        <div className="flex-1">
          <label className="mb-1 block text-sm font-medium text-gray-700">Travel Fee</label>
          <div className="rounded-md border border-blue-200 bg-blue-50 px-3 py-2 text-lg font-semibold text-blue-900">
            ${fee.toFixed(2)}
          </div>
        </div>
      </div>

      {distance > 0 && (
        <div className="rounded-lg bg-gray-50 p-3 text-sm text-gray-700">
          <strong>Calculation:</strong>{' '}
          {distance <= settings.baseFeeStructure.freeRadius
            ? `Distance within free ${settings.baseFeeStructure.freeRadius}-mile radius`
            : `${settings.baseFeeStructure.freeRadius} miles free + ${(
                distance - settings.baseFeeStructure.freeRadius
              ).toFixed(1)} miles × $${settings.baseFeeStructure.ratePerMile} = $${fee.toFixed(2)}`}
        </div>
      )}
    </div>
  );
}
