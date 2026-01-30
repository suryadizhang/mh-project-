'use client';

/**
 * Customer Preferences Panel
 * ===========================
 *
 * Unified panel for capturing and displaying:
 * 1. Chef Request Info (for 10% bonus tracking)
 * 2. Allergen Disclosure (for food safety)
 *
 * Usage:
 *   <CustomerPreferencesPanel bookingId={bookingId} />
 *
 * Features:
 * - Auto-loads preferences on mount
 * - Real-time update with optimistic UI
 * - Chef search/select for request tracking
 * - Multi-select allergen disclosure
 * - Confirmation checkbox for allergen review
 * - Visual indicators for bonus eligibility
 *
 * @see apps/backend/src/routers/v1/customer_preferences.py
 * @see database/migrations/022_customer_preferences_capture.sql
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  AlertTriangle,
  Award,
  Check,
  ChefHat,
  Info,
  Loader2,
  MessageSquare,
  Phone,
  Save,
  User,
  X,
} from 'lucide-react';
import { customerPreferencesService } from '@/services/api';
import type {
  CommonAllergen,
  CustomerPreferences,
  CustomerPreferencesUpdate,
  ChefBonusInfo,
  ChefRequestSource,
  CHEF_REQUEST_SOURCE_LABELS,
  CHEF_REQUEST_SOURCE_ICONS,
} from '@/types/customer-preferences';

// Re-define labels here to avoid import issues
const SOURCE_LABELS: Record<ChefRequestSource, string> = {
  booking_form: 'Booking Form',
  sms: 'SMS/Text',
  phone_call: 'Phone Call',
  email: 'Email',
  social_dm: 'Social Media DM',
  ai_chat: 'AI Chat',
  repeat_customer: 'Repeat Customer',
  admin_manual: 'Admin Entry',
};

const SOURCE_ICONS: Record<ChefRequestSource, string> = {
  booking_form: '📝',
  sms: '💬',
  phone_call: '📞',
  email: '📧',
  social_dm: '📱',
  ai_chat: '🤖',
  repeat_customer: '🔄',
  admin_manual: '👤',
};

interface CustomerPreferencesPanelProps {
  bookingId: string;
  /** Optional: pre-loaded chef list for selection */
  chefs?: Array<{ id: string; name: string; tier: string }>;
  /** Optional: called when preferences are updated */
  onUpdate?: (preferences: CustomerPreferences) => void;
  /** Optional: compact mode for sidebar */
  compact?: boolean;
}

export function CustomerPreferencesPanel({
  bookingId,
  chefs = [],
  onUpdate,
  compact = false,
}: CustomerPreferencesPanelProps) {
  // State
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [preferences, setPreferences] = useState<CustomerPreferences | null>(
    null
  );
  const [allergens, setAllergens] = useState<CommonAllergen[]>([]);
  const [bonusInfo, setBonusInfo] = useState<ChefBonusInfo | null>(null);

  // Form state (for editing)
  const [editMode, setEditMode] = useState(false);
  const [formData, setFormData] = useState<CustomerPreferencesUpdate>({});

  // Load preferences and allergens on mount
  useEffect(() => {
    loadData();
  }, [bookingId]);

  const loadData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Load all data in parallel
      const [prefsRes, allergensRes, bonusRes] = await Promise.all([
        customerPreferencesService.getBookingPreferences(bookingId),
        customerPreferencesService.getCommonAllergens(),
        customerPreferencesService.getChefBonus(bookingId),
      ]);

      if (prefsRes.success && prefsRes.data) {
        setPreferences(prefsRes.data);
        // Initialize form with current values
        // Note: Use undefined for optional fields (|| undefined), use null only where type allows
        setFormData({
          chef_was_requested:
            prefsRes.data.chef_request?.chef_was_requested || false,
          requested_chef_id:
            prefsRes.data.chef_request?.requested_chef_id ?? undefined,
          chef_request_source:
            prefsRes.data.chef_request?.chef_request_source ?? undefined,
          allergen_disclosure:
            prefsRes.data.allergens?.allergen_disclosure ?? undefined,
          common_allergens: prefsRes.data.allergens?.common_allergens || [],
          allergen_confirmed:
            prefsRes.data.allergens?.allergen_confirmed || false,
        });
      }

      if (allergensRes.success && allergensRes.data) {
        setAllergens(allergensRes.data);
      }

      if (bonusRes.success && bonusRes.data) {
        setBonusInfo(bonusRes.data);
      }
    } catch (err) {
      setError('Failed to load preferences');
      console.error('CustomerPreferencesPanel load error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);

    try {
      const res = await customerPreferencesService.updateBookingPreferences(
        bookingId,
        formData
      );

      if (res.success && res.data) {
        setPreferences(res.data);
        setEditMode(false);
        onUpdate?.(res.data);

        // Reload bonus info after update
        const bonusRes =
          await customerPreferencesService.getChefBonus(bookingId);
        if (bonusRes.success && bonusRes.data) {
          setBonusInfo(bonusRes.data);
        }
      } else {
        setError(res.error || 'Failed to save preferences');
      }
    } catch (err) {
      setError('Failed to save preferences');
      console.error('CustomerPreferencesPanel save error:', err);
    } finally {
      setSaving(false);
    }
  };

  const toggleAllergen = (code: string) => {
    const current = formData.common_allergens || [];
    if (current.includes(code)) {
      setFormData({
        ...formData,
        common_allergens: current.filter(c => c !== code),
      });
    } else {
      setFormData({
        ...formData,
        common_allergens: [...current, code],
      });
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center p-6">
        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
        <span className="ml-2 text-gray-500">Loading preferences...</span>
      </div>
    );
  }

  // Error state
  if (error && !preferences) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4">
        <div className="flex items-center">
          <AlertTriangle className="h-5 w-5 text-red-500" />
          <span className="ml-2 text-red-700">{error}</span>
        </div>
        <button
          onClick={loadData}
          className="mt-2 text-sm text-red-600 underline hover:text-red-800"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${compact ? 'text-sm' : ''}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="flex items-center text-lg font-semibold text-gray-900">
          <User className="mr-2 h-5 w-5" />
          Customer Preferences
        </h3>
        {!editMode ? (
          <button
            onClick={() => setEditMode(true)}
            className="rounded-md bg-gray-100 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-200"
          >
            Edit
          </button>
        ) : (
          <div className="flex gap-2">
            <button
              onClick={() => setEditMode(false)}
              className="rounded-md bg-gray-100 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-200"
              disabled={saving}
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? (
                <Loader2 className="mr-1 h-4 w-4 animate-spin" />
              ) : (
                <Save className="mr-1 h-4 w-4" />
              )}
              Save
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Chef Request Section */}
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <h4 className="mb-3 flex items-center font-medium text-gray-900">
          <ChefHat className="mr-2 h-4 w-4" />
          Chef Request
          {bonusInfo?.bonus_applies && (
            <span className="ml-2 inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800">
              <Award className="mr-1 h-3 w-3" />
              Bonus Eligible
            </span>
          )}
        </h4>

        {editMode ? (
          <div className="space-y-3">
            {/* Chef Was Requested Toggle */}
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.chef_was_requested || false}
                onChange={e =>
                  setFormData({
                    ...formData,
                    chef_was_requested: e.target.checked,
                    // Clear chef info if unchecking
                    ...(e.target.checked
                      ? {}
                      : {
                          requested_chef_id: null,
                          chef_request_source: undefined,
                        }),
                  })
                }
                className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="ml-2 text-gray-700">
                Customer requested a specific chef
              </span>
            </label>

            {formData.chef_was_requested && (
              <>
                {/* Chef Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Requested Chef
                  </label>
                  <select
                    value={formData.requested_chef_id || ''}
                    onChange={e =>
                      setFormData({
                        ...formData,
                        requested_chef_id: e.target.value || null,
                      })
                    }
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    <option value="">Select a chef...</option>
                    {chefs.map(chef => (
                      <option key={chef.id} value={chef.id}>
                        {chef.name} ({chef.tier})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Request Source */}
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    How did customer request?
                  </label>
                  <select
                    value={formData.chef_request_source || ''}
                    onChange={e =>
                      setFormData({
                        ...formData,
                        chef_request_source: e.target.value
                          ? (e.target.value as ChefRequestSource)
                          : undefined,
                      })
                    }
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    <option value="">Select source...</option>
                    {Object.entries(SOURCE_LABELS).map(([key, label]) => (
                      <option key={key} value={key}>
                        {SOURCE_ICONS[key as ChefRequestSource]} {label}
                      </option>
                    ))}
                  </select>
                </div>
              </>
            )}
          </div>
        ) : (
          // View mode
          <div className="space-y-2">
            {preferences?.chef_request?.chef_was_requested ? (
              <>
                <div className="flex items-center text-green-700">
                  <Check className="mr-2 h-4 w-4" />
                  Customer requested a specific chef
                </div>
                {preferences.chef_request.requested_chef_name && (
                  <div className="ml-6 text-gray-600">
                    <strong>Chef:</strong>{' '}
                    {preferences.chef_request.requested_chef_name}
                  </div>
                )}
                {preferences.chef_request.chef_request_source && (
                  <div className="ml-6 text-gray-600">
                    <strong>Source:</strong>{' '}
                    {SOURCE_ICONS[preferences.chef_request.chef_request_source]}{' '}
                    {
                      SOURCE_LABELS[
                        preferences.chef_request.chef_request_source
                      ]
                    }
                  </div>
                )}
              </>
            ) : (
              <div className="flex items-center text-gray-500">
                <X className="mr-2 h-4 w-4" />
                No specific chef requested
              </div>
            )}

            {/* Bonus Info */}
            {bonusInfo && (
              <div className="mt-3 rounded-md bg-gray-50 p-3">
                <div className="text-sm">
                  {bonusInfo.bonus_applies ? (
                    <div className="text-green-700">
                      <Award className="mr-1 inline h-4 w-4" />
                      <strong>Bonus:</strong> $
                      {(bonusInfo.bonus_cents / 100).toFixed(2)} (
                      {bonusInfo.bonus_pct}%)
                      <div className="mt-1 text-xs text-gray-500">
                        Based on $
                        {(bonusInfo.base_earnings_cents / 100).toFixed(2)} base
                        total
                      </div>
                    </div>
                  ) : (
                    <div className="text-gray-500">
                      <Info className="mr-1 inline h-4 w-4" />
                      {bonusInfo.message || 'No bonus applies'}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Allergen Disclosure Section */}
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <h4 className="mb-3 flex items-center font-medium text-gray-900">
          <AlertTriangle className="mr-2 h-4 w-4 text-amber-500" />
          Allergen Disclosure
          {preferences?.allergens?.allergen_confirmed && (
            <span className="ml-2 inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800">
              <Check className="mr-1 h-3 w-3" />
              Confirmed
            </span>
          )}
        </h4>

        {editMode ? (
          <div className="space-y-4">
            {/* Common Allergens Multi-Select */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Common Allergens
              </label>
              <div className="mt-2 flex flex-wrap gap-2">
                {allergens.map(allergen => {
                  const isSelected = (formData.common_allergens || []).includes(
                    allergen.code
                  );
                  return (
                    <button
                      key={allergen.code}
                      type="button"
                      onClick={() => toggleAllergen(allergen.code)}
                      className={`inline-flex items-center rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
                        isSelected
                          ? 'bg-red-100 text-red-800 ring-2 ring-red-500'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      <span className="mr-1">{allergen.icon}</span>
                      {allergen.display_name}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Additional Notes */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Additional Allergen Notes
              </label>
              <textarea
                value={formData.allergen_disclosure || ''}
                onChange={e =>
                  setFormData({
                    ...formData,
                    allergen_disclosure: e.target.value,
                  })
                }
                rows={3}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="Any additional allergen information or special requests..."
              />
            </div>

            {/* Confirmation Checkbox */}
            <label className="flex items-start">
              <input
                type="checkbox"
                checked={formData.allergen_confirmed || false}
                onChange={e =>
                  setFormData({
                    ...formData,
                    allergen_confirmed: e.target.checked,
                  })
                }
                className="mt-0.5 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="ml-2 text-sm text-gray-700">
                Customer has confirmed allergen information is complete and
                accurate
              </span>
            </label>
          </div>
        ) : (
          // View mode
          <div className="space-y-3">
            {/* Selected Allergens */}
            {preferences?.allergens?.common_allergens &&
            preferences.allergens.common_allergens.length > 0 ? (
              <div>
                <span className="text-sm font-medium text-gray-700">
                  Allergens:
                </span>
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {preferences.allergens.common_allergens.map(code => {
                    const allergen = allergens.find(a => a.code === code);
                    return (
                      <span
                        key={code}
                        className="inline-flex items-center rounded-full bg-red-100 px-2.5 py-1 text-sm font-medium text-red-800"
                      >
                        <span className="mr-1">{allergen?.icon || '⚠️'}</span>
                        {allergen?.display_name || code}
                      </span>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="text-sm text-gray-500">
                No common allergens selected
              </div>
            )}

            {/* Additional Notes */}
            {preferences?.allergens?.allergen_disclosure && (
              <div>
                <span className="text-sm font-medium text-gray-700">
                  Notes:
                </span>
                <p className="mt-1 text-sm text-gray-600">
                  {preferences.allergens.allergen_disclosure}
                </p>
              </div>
            )}

            {/* Confirmation Status */}
            <div className="flex items-center">
              {preferences?.allergens?.allergen_confirmed ? (
                <span className="inline-flex items-center text-sm text-green-700">
                  <Check className="mr-1 h-4 w-4" />
                  Allergen info confirmed by customer
                </span>
              ) : (
                <span className="inline-flex items-center text-sm text-amber-600">
                  <AlertTriangle className="mr-1 h-4 w-4" />
                  Allergen info not yet confirmed
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Footer Info */}
      <div className="text-xs text-gray-500">
        <Info className="mr-1 inline h-3 w-3" />
        Chef request bonus applies only when the requested chef is assigned to
        this booking.
      </div>
    </div>
  );
}

export default CustomerPreferencesPanel;
