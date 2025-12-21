'use client';

import {
  AlertCircle,
  CheckCircle,
  Globe,
  Loader2,
  Mail,
  Map,
  MapPin,
  Phone,
  Save,
  Settings,
  X,
} from 'lucide-react';
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { logger } from '@/lib/logger';
import { stationService, type Station } from '@/services/api';

interface StationEditFormProps {
  station: Station;
  onSave: (updatedStation: Station) => void;
  onCancel: () => void;
}

// Status badge component
const GeocodeBadge = ({ status }: { status?: string }) => {
  if (status === 'success') {
    return (
      <span className="inline-flex items-center px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">
        <CheckCircle className="h-3 w-3 mr-1" />
        Geocoded
      </span>
    );
  }
  if (status === 'failed') {
    return (
      <span className="inline-flex items-center px-2 py-1 text-xs rounded-full bg-red-100 text-red-800">
        <AlertCircle className="h-3 w-3 mr-1" />
        Failed
      </span>
    );
  }
  return (
    <span className="inline-flex items-center px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-800">
      <AlertCircle className="h-3 w-3 mr-1" />
      Pending
    </span>
  );
};

export const StationEditForm: React.FC<StationEditFormProps> = ({
  station,
  onSave,
  onCancel,
}) => {
  const [formData, setFormData] = useState<Partial<Station>>({
    name: station.name || '',
    display_name: station.display_name || '',
    address: station.address || '',
    city: station.city || '',
    state: station.state || '',
    postal_code: station.postal_code || '',
    country: station.country || 'US',
    phone: station.phone || '',
    email: station.email || '',
    timezone: station.timezone || 'America/Los_Angeles',
    lat: station.lat,
    lng: station.lng,
    service_area_radius: station.service_area_radius ?? 150,
    escalation_radius_miles: station.escalation_radius_miles ?? 150,
    status: station.status || 'active',
    max_concurrent_bookings: station.max_concurrent_bookings ?? 10,
    booking_lead_time_hours: station.booking_lead_time_hours ?? 24,
  });

  const [saving, setSaving] = useState(false);
  const [geocoding, setGeocoding] = useState(false);
  const [saveStatus, setSaveStatus] = useState<{
    type: 'success' | 'error' | null;
    message: string;
  }>({ type: null, message: '' });

  // Track which fields have been modified
  const [modifiedFields, setModifiedFields] = useState<Set<string>>(new Set());

  const handleInputChange = (field: keyof Station, value: string | number) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setModifiedFields(prev => new Set(prev).add(field));
  };

  // Check if address fields changed (need re-geocoding)
  const addressChanged = ['address', 'city', 'state', 'postal_code'].some(
    field => modifiedFields.has(field)
  );

  // Build full address for display
  const fullAddress = [
    formData.address,
    formData.city,
    formData.state,
    formData.postal_code,
  ]
    .filter(Boolean)
    .join(', ');

  // Geocode the station address
  const handleGeocode = async () => {
    if (!fullAddress) {
      setSaveStatus({
        type: 'error',
        message: 'Please enter an address first',
      });
      return;
    }

    setGeocoding(true);
    setSaveStatus({ type: null, message: '' });

    try {
      const response = await stationService.geocodeStation(station.id);
      if (response.data && response.data.lat && response.data.lng) {
        const { lat, lng, geocode_status, geocoded_at } = response.data;
        setFormData(prev => ({
          ...prev,
          lat,
          lng,
          geocode_status,
          geocoded_at,
        }));
        setSaveStatus({
          type: 'success',
          message: `Geocoded successfully! Lat: ${lat}, Lng: ${lng}`,
        });
      } else {
        setSaveStatus({
          type: 'error',
          message: response.error || 'Failed to geocode address',
        });
      }
    } catch (err) {
      logger.error('Geocoding failed', { error: err });
      setSaveStatus({
        type: 'error',
        message: 'Network error during geocoding',
      });
    } finally {
      setGeocoding(false);
    }
  };

  // Save station changes
  const handleSave = async () => {
    setSaving(true);
    setSaveStatus({ type: null, message: '' });

    try {
      // Build updates from modified fields
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const updates: any = {};
      modifiedFields.forEach(field => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        updates[field] = (formData as any)[field];
      });

      // Always include service area fields if editing
      if (modifiedFields.size > 0) {
        updates.service_area_radius = formData.service_area_radius;
        updates.escalation_radius_miles = formData.escalation_radius_miles;
      }

      const response = await stationService.updateStation(station.id, updates);
      if (response.data) {
        setSaveStatus({
          type: 'success',
          message: 'Station updated successfully!',
        });
        onSave(response.data);
      } else {
        setSaveStatus({
          type: 'error',
          message: response.error || 'Failed to update station',
        });
      }
    } catch (err) {
      logger.error('Station update failed', { error: err });
      setSaveStatus({
        type: 'error',
        message: 'Network error. Please try again.',
      });
    } finally {
      setSaving(false);
    }
  };

  const hasChanges = modifiedFields.size > 0;

  return (
    <div className="space-y-6">
      {/* Status Message */}
      {saveStatus.type && (
        <div
          className={`flex items-center p-4 rounded-lg ${
            saveStatus.type === 'success'
              ? 'bg-green-50 text-green-800 border border-green-200'
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}
        >
          {saveStatus.type === 'success' ? (
            <CheckCircle className="h-5 w-5 mr-2" />
          ) : (
            <AlertCircle className="h-5 w-5 mr-2" />
          )}
          {saveStatus.message}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Basic Information Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center text-lg">
              <Settings className="h-5 w-5 mr-2" />
              Basic Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Station Code
              </label>
              <Input
                value={station.code || ''}
                disabled
                className="bg-gray-100"
              />
              <p className="text-xs text-gray-500 mt-1">
                Auto-generated, cannot be changed
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Station Name *
              </label>
              <Input
                value={formData.name}
                onChange={e => handleInputChange('name', e.target.value)}
                placeholder="e.g., Fremont Station"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Display Name *
              </label>
              <Input
                value={formData.display_name}
                onChange={e =>
                  handleInputChange('display_name', e.target.value)
                }
                placeholder="e.g., My Hibachi - Fremont, CA (Main)"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Phone className="h-4 w-4 inline mr-1" />
                  Phone
                </label>
                <Input
                  value={formData.phone}
                  onChange={e => handleInputChange('phone', e.target.value)}
                  placeholder="+1 916-740-8768"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Mail className="h-4 w-4 inline mr-1" />
                  Email
                </label>
                <Input
                  value={formData.email}
                  onChange={e => handleInputChange('email', e.target.value)}
                  placeholder="cs@myhibachichef.com"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Globe className="h-4 w-4 inline mr-1" />
                  Timezone
                </label>
                <select
                  className="w-full h-10 px-3 rounded-md border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  value={formData.timezone}
                  onChange={e => handleInputChange('timezone', e.target.value)}
                >
                  <option value="America/Los_Angeles">
                    Pacific (Los Angeles)
                  </option>
                  <option value="America/Denver">Mountain (Denver)</option>
                  <option value="America/Chicago">Central (Chicago)</option>
                  <option value="America/New_York">Eastern (New York)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Status
                </label>
                <select
                  className="w-full h-10 px-3 rounded-md border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  value={formData.status}
                  onChange={e => handleInputChange('status', e.target.value)}
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="suspended">Suspended</option>
                  <option value="maintenance">Maintenance</option>
                </select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Location & Geocoding Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between text-lg">
              <span className="flex items-center">
                <MapPin className="h-5 w-5 mr-2" />
                Location & Geocoding
              </span>
              <GeocodeBadge
                status={formData.geocode_status || station.geocode_status}
              />
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Street Address *
              </label>
              <Input
                value={formData.address}
                onChange={e => handleInputChange('address', e.target.value)}
                placeholder="47481 Towhee St"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  City *
                </label>
                <Input
                  value={formData.city}
                  onChange={e => handleInputChange('city', e.target.value)}
                  placeholder="Fremont"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  State *
                </label>
                <Input
                  value={formData.state}
                  onChange={e => handleInputChange('state', e.target.value)}
                  placeholder="CA"
                  maxLength={2}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ZIP Code
                </label>
                <Input
                  value={formData.postal_code}
                  onChange={e =>
                    handleInputChange('postal_code', e.target.value)
                  }
                  placeholder="94539"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Country
                </label>
                <Input
                  value={formData.country}
                  onChange={e => handleInputChange('country', e.target.value)}
                  placeholder="US"
                  maxLength={2}
                />
              </div>
            </div>

            {/* Geocoding Results */}
            <div className="bg-gray-50 rounded-lg p-4 space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="font-medium text-gray-700">Coordinates</h4>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleGeocode}
                  disabled={geocoding || !fullAddress}
                  className="flex items-center"
                >
                  {geocoding ? (
                    <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                  ) : (
                    <Map className="h-4 w-4 mr-1" />
                  )}
                  {geocoding ? 'Geocoding...' : 'Geocode Address'}
                </Button>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">
                    Latitude
                  </label>
                  <Input
                    value={formData.lat ?? ''}
                    onChange={e =>
                      handleInputChange('lat', parseFloat(e.target.value) || 0)
                    }
                    placeholder="37.5485"
                    type="number"
                    step="0.00000001"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">
                    Longitude
                  </label>
                  <Input
                    value={formData.lng ?? ''}
                    onChange={e =>
                      handleInputChange('lng', parseFloat(e.target.value) || 0)
                    }
                    placeholder="-121.9886"
                    type="number"
                    step="0.00000001"
                  />
                </div>
              </div>

              {addressChanged && (
                <p className="text-xs text-yellow-600 flex items-center">
                  <AlertCircle className="h-3 w-3 mr-1" />
                  Address changed - click &quot;Geocode Address&quot; to update
                  coordinates
                </p>
              )}

              {station.geocoded_at && (
                <p className="text-xs text-gray-500">
                  Last geocoded:{' '}
                  {new Date(station.geocoded_at).toLocaleString()}
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Service Area Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center text-lg">
              <MapPin className="h-5 w-5 mr-2" />
              Service Area Configuration
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Service Area Radius (miles)
              </label>
              <Input
                type="number"
                min="0"
                max="500"
                value={formData.service_area_radius}
                onChange={e =>
                  handleInputChange(
                    'service_area_radius',
                    parseInt(e.target.value) || 0
                  )
                }
              />
              <p className="text-xs text-gray-500 mt-1">
                Maximum distance from station to accept bookings automatically.
                Addresses beyond this radius will be marked as not serviceable.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Escalation Threshold (miles)
              </label>
              <Input
                type="number"
                min="0"
                max="500"
                value={formData.escalation_radius_miles}
                onChange={e =>
                  handleInputChange(
                    'escalation_radius_miles',
                    parseInt(e.target.value) || 0
                  )
                }
              />
              <p className="text-xs text-gray-500 mt-1">
                Bookings beyond this distance require human approval before
                confirmation. Typically set equal to or less than service area
                radius.
              </p>
            </div>

            <div className="bg-blue-50 rounded-lg p-3">
              <h5 className="font-medium text-blue-800 text-sm mb-2">
                Current Configuration
              </h5>
              <ul className="text-xs text-blue-700 space-y-1">
                <li>
                  ✓ Auto-accept bookings within{' '}
                  <strong>{formData.service_area_radius}</strong> miles
                </li>
                <li>
                  ⚠ Require approval for bookings beyond{' '}
                  <strong>{formData.escalation_radius_miles}</strong> miles
                </li>
                <li>
                  ✗ Reject bookings beyond{' '}
                  <strong>{formData.service_area_radius}</strong> miles
                </li>
              </ul>
            </div>
          </CardContent>
        </Card>

        {/* Booking Settings Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center text-lg">
              <Settings className="h-5 w-5 mr-2" />
              Booking Settings
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Concurrent Bookings
              </label>
              <Input
                type="number"
                min="1"
                max="100"
                value={formData.max_concurrent_bookings}
                onChange={e =>
                  handleInputChange(
                    'max_concurrent_bookings',
                    parseInt(e.target.value) || 1
                  )
                }
              />
              <p className="text-xs text-gray-500 mt-1">
                Maximum number of bookings this station can handle
                simultaneously.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Minimum Lead Time (hours)
              </label>
              <Input
                type="number"
                min="0"
                max="168"
                value={formData.booking_lead_time_hours}
                onChange={e =>
                  handleInputChange(
                    'booking_lead_time_hours',
                    parseInt(e.target.value) || 0
                  )
                }
              />
              <p className="text-xs text-gray-500 mt-1">
                Minimum hours in advance a booking must be made.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-between pt-4 border-t">
        <div className="text-sm text-gray-500">
          {hasChanges ? (
            <span className="text-yellow-600">⚠ You have unsaved changes</span>
          ) : (
            <span>No changes made</span>
          )}
        </div>
        <div className="flex space-x-3">
          <Button variant="outline" onClick={onCancel} disabled={saving}>
            <X className="h-4 w-4 mr-2" />
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={saving || !hasChanges}
            className="flex items-center"
          >
            {saving ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Save className="h-4 w-4 mr-2" />
            )}
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default StationEditForm;
