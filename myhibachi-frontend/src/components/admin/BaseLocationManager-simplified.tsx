'use client'

import { AlertTriangle, CheckCircle, MapPin, Save, Settings } from 'lucide-react'
import { useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import { apiFetch } from '@/lib/api'

interface CompanySettings {
  baseFeeStructure: {
    freeRadius: number // Free travel radius in miles
    ratePerMile: number // Rate per mile beyond free radius
  }
  serviceArea: {
    description: string
    maxRadius: number // Maximum service radius
  }
  contactInfo: {
    phone: string
    email: string
  }
  lastUpdated: string
  updatedBy: string
}

export function BaseLocationManager() {
  const [currentSettings, setCurrentSettings] = useState<CompanySettings>({
    baseFeeStructure: {
      freeRadius: 30,
      ratePerMile: 2
    },
    serviceArea: {
      description: 'Northern California',
      maxRadius: 150
    },
    contactInfo: {
      phone: '(916) 740-8768',
      email: 'cs@myhibachichef.com'
    },
    lastUpdated: '2025-01-15',
    updatedBy: 'System Admin'
  })

  const [formData, setFormData] = useState(currentSettings)
  const [isUpdating, setIsUpdating] = useState(false)

  const [updateStatus, setUpdateStatus] = useState<{
    type: 'success' | 'error' | null
    message: string
  }>({ type: null, message: '' })

  // Load current settings on component mount
  useEffect(() => {
    loadCurrentSettings()
  }, [])

  const loadCurrentSettings = async () => {
    try {
      const result = await apiFetch('/api/v1/admin/company-settings')
      if (result.success) {
        setCurrentSettings(result.data)
        setFormData(result.data)
      }
    } catch (err) {
      console.error('Error loading company settings:', err)
    }
  }

  const handleInputChange = (field: string, value: string | number) => {
    setFormData(prev => {
      const newData = { ...prev }

      // Handle nested field updates
      if (field.includes('.')) {
        const keys = field.split('.')
        if (keys[0] === 'baseFeeStructure') {
          return {
            ...newData,
            baseFeeStructure: {
              ...newData.baseFeeStructure,
              [keys[1]]: value
            }
          }
        } else if (keys[0] === 'serviceArea') {
          return {
            ...newData,
            serviceArea: {
              ...newData.serviceArea,
              [keys[1]]: value
            }
          }
        } else if (keys[0] === 'contactInfo') {
          return {
            ...newData,
            contactInfo: {
              ...newData.contactInfo,
              [keys[1]]: value
            }
          }
        }
      }

      return newData
    })
  }

  const updateSettings = async () => {
    setIsUpdating(true)
    setUpdateStatus({ type: null, message: '' })

    try {
      const response = await apiFetch('/api/v1/admin/company-settings', {
        method: 'PUT',
        body: JSON.stringify({
          ...formData,
          updatedBy: 'Super Admin', // In a real app, get this from auth context
          lastUpdated: new Date().toISOString().split('T')[0]
        })
      })

      if (response.success) {
        const updatedData = response.data
        setCurrentSettings(updatedData)
        setFormData(updatedData)
        setUpdateStatus({
          type: 'success',
          message: 'Company settings updated successfully! Changes will apply to new quotes.'
        })
      } else {
        setUpdateStatus({
          type: 'error',
          message: response.error || 'Failed to update settings'
        })
      }
    } catch (err) {
      console.error('Update error:', err)
      setUpdateStatus({
        type: 'error',
        message: 'Network error. Please try again.'
      })
    } finally {
      setIsUpdating(false)
    }
  }

  const hasChanges = JSON.stringify(currentSettings) !== JSON.stringify(formData)

  return (
    <div className="space-y-6">
      {/* Current Settings Display */}
      <div className="bg-white rounded-lg shadow border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <Settings className="w-5 h-5 mr-2" />
            Travel Fee & Service Settings
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Configure travel fee structure and service area information for customer quotes
          </p>
        </div>

        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Travel Fee Structure */}
            <div className="space-y-4">
              <h4 className="text-md font-medium text-gray-800">Travel Fee Structure</h4>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Free Travel Radius (miles)
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={formData.baseFeeStructure.freeRadius}
                  onChange={e =>
                    handleInputChange('baseFeeStructure.freeRadius', parseInt(e.target.value) || 0)
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Distance from base location with no travel fee
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Rate per Mile ($)
                </label>
                <input
                  type="number"
                  min="0"
                  step="0.5"
                  value={formData.baseFeeStructure.ratePerMile}
                  onChange={e =>
                    handleInputChange(
                      'baseFeeStructure.ratePerMile',
                      parseFloat(e.target.value) || 0
                    )
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">Cost per mile beyond free radius</p>
              </div>

              {/* Fee Preview */}
              <div className="p-3 bg-blue-50 rounded-lg">
                <h5 className="text-sm font-medium text-blue-900 mb-2">Fee Structure Preview:</h5>
                <div className="text-sm text-blue-800 space-y-1">
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
                        formData.baseFeeStructure.ratePerMile
                    )}
                  </p>
                </div>
              </div>
            </div>

            {/* Service Area */}
            <div className="space-y-4">
              <h4 className="text-md font-medium text-gray-800">Service Area</h4>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Service Area Description
                </label>
                <input
                  type="text"
                  value={formData.serviceArea.description}
                  onChange={e => handleInputChange('serviceArea.description', e.target.value)}
                  placeholder="e.g., Northern California, Bay Area..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">General description shown to customers</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Maximum Service Radius (miles)
                </label>
                <input
                  type="number"
                  min="50"
                  max="300"
                  value={formData.serviceArea.maxRadius}
                  onChange={e =>
                    handleInputChange('serviceArea.maxRadius', parseInt(e.target.value) || 150)
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Maximum distance from base location served
                </p>
              </div>

              {/* Contact Info */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Customer Service Phone
                </label>
                <input
                  type="text"
                  value={formData.contactInfo.phone}
                  onChange={e => handleInputChange('contactInfo.phone', e.target.value)}
                  placeholder="(916) 740-8768"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Customer Service Email
                </label>
                <input
                  type="email"
                  value={formData.contactInfo.email}
                  onChange={e => handleInputChange('contactInfo.email', e.target.value)}
                  placeholder="cs@myhibachichef.com"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Current Status */}
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">
                  Last Updated: {currentSettings.lastUpdated} by {currentSettings.updatedBy}
                </p>
              </div>
              <div className="flex items-center space-x-3">
                {hasChanges && (
                  <span className="text-sm text-orange-600 font-medium">Unsaved changes</span>
                )}
                <Button
                  onClick={updateSettings}
                  disabled={isUpdating || !hasChanges}
                  className={hasChanges ? 'bg-blue-600 hover:bg-blue-700' : ''}
                >
                  <Save className="w-4 h-4 mr-2" />
                  {isUpdating ? 'Updating...' : 'Save Changes'}
                </Button>
              </div>
            </div>
          </div>

          {/* Update Status */}
          {updateStatus.type && (
            <div
              className={`mt-4 p-4 rounded-lg border ${
                updateStatus.type === 'success'
                  ? 'bg-green-50 border-green-200'
                  : 'bg-red-50 border-red-200'
              }`}
            >
              <div className="flex items-center">
                {updateStatus.type === 'success' ? (
                  <CheckCircle className="w-4 h-4 text-green-600 mr-2" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-red-600 mr-2" />
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
      <div className="bg-white rounded-lg shadow border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <MapPin className="w-5 h-5 mr-2" />
            Manual Travel Fee Calculator
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Quick tool for customer service to calculate travel fees manually
          </p>
        </div>

        <div className="p-6">
          <TravelFeeCalculator settings={currentSettings} />
        </div>
      </div>
    </div>
  )
}

// Quick manual calculator component
function TravelFeeCalculator({ settings }: { settings: CompanySettings }) {
  const [distance, setDistance] = useState<number>(0)

  const calculateFee = (miles: number) => {
    if (miles <= settings.baseFeeStructure.freeRadius) {
      return 0
    }
    return (miles - settings.baseFeeStructure.freeRadius) * settings.baseFeeStructure.ratePerMile
  }

  const fee = calculateFee(distance)

  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-4">
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">Distance (miles)</label>
          <input
            type="number"
            min="0"
            step="0.1"
            value={distance}
            onChange={e => setDistance(parseFloat(e.target.value) || 0)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter distance in miles"
          />
        </div>

        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">Travel Fee</label>
          <div className="px-3 py-2 bg-blue-50 border border-blue-200 rounded-md text-lg font-semibold text-blue-900">
            ${fee.toFixed(2)}
          </div>
        </div>
      </div>

      {distance > 0 && (
        <div className="p-3 bg-gray-50 rounded-lg text-sm text-gray-700">
          <strong>Calculation:</strong>{' '}
          {distance <= settings.baseFeeStructure.freeRadius
            ? `Distance within free ${settings.baseFeeStructure.freeRadius}-mile radius`
            : `${settings.baseFeeStructure.freeRadius} miles free + ${(distance - settings.baseFeeStructure.freeRadius).toFixed(1)} miles × $${settings.baseFeeStructure.ratePerMile} = $${fee.toFixed(2)}`}
        </div>
      )}
    </div>
  )
}
