/**
 * ActivationButton Component
 * 
 * ONE-CLICK ACTIVATION BUTTON
 * Enables/disables local AI with confirmation modal and reason input
 */

'use client';

import React, { useState } from 'react';
import { Power, AlertTriangle, CheckCircle, Loader2 } from 'lucide-react';
import type { OverallReadiness } from '@/types/aiReadiness';

interface ActivationButtonProps {
  overallReadiness: OverallReadiness;
  onActivate: (reason: string, intents?: string[], startPercentage?: number) => Promise<void>;
  onDisable: (reason: string, emergency?: boolean) => Promise<void>;
  isActivating: boolean;
  currentMode: 'shadow' | 'active' | 'disabled';
}

export function ActivationButton({
  overallReadiness,
  onActivate,
  onDisable,
  isActivating,
  currentMode
}: ActivationButtonProps) {
  const [showModal, setShowModal] = useState(false);
  const [reason, setReason] = useState('');
  const [startPercentage, setStartPercentage] = useState(10);
  const [error, setError] = useState('');
  const [actionType, setActionType] = useState<'activate' | 'disable'>('activate');

  const isActive = currentMode === 'active';
  const canActivate = overallReadiness.can_activate && !isActive;

  const handleOpenModal = (type: 'activate' | 'disable') => {
    setActionType(type);
    setShowModal(true);
    setReason('');
    setError('');
  };

  const handleConfirm = async () => {
    if (!reason.trim()) {
      setError('Please provide a reason');
      return;
    }

    try {
      if (actionType === 'activate') {
        await onActivate(reason, overallReadiness.ready_intents, startPercentage);
      } else {
        await onDisable(reason, false);
      }
      setShowModal(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Operation failed');
    }
  };

  const handleEmergencyDisable = async () => {
    if (!confirm('⚠️ EMERGENCY DISABLE: This will immediately stop all local AI processing. Are you sure?')) {
      return;
    }

    try {
      await onDisable('Emergency disable triggered by admin', true);
      setShowModal(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Emergency disable failed');
    }
  };

  return (
    <>
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-1">
              AI Activation Control
            </h3>
            <p className="text-sm text-gray-600">
              {isActive 
                ? 'Local AI is currently active and handling requests'
                : currentMode === 'shadow'
                ? 'Shadow mode: Collecting training data without customer impact'
                : 'Local AI is disabled'}
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* Status Indicator */}
            <div className={`px-3 py-1.5 rounded-lg border flex items-center gap-2 ${
              isActive 
                ? 'bg-green-50 border-green-200 text-green-700'
                : currentMode === 'shadow'
                ? 'bg-blue-50 border-blue-200 text-blue-700'
                : 'bg-gray-50 border-gray-200 text-gray-700'
            }`}>
              <div className={`w-2 h-2 rounded-full ${
                isActive ? 'bg-green-500 animate-pulse' : currentMode === 'shadow' ? 'bg-blue-500' : 'bg-gray-400'
              }`} />
              <span className="font-medium text-sm">
                {isActive ? 'ACTIVE' : currentMode === 'shadow' ? 'SHADOW MODE' : 'DISABLED'}
              </span>
            </div>

            {/* Activate Button */}
            {!isActive && (
              <button
                onClick={() => handleOpenModal('activate')}
                disabled={!canActivate || isActivating}
                className={`px-6 py-3 rounded-lg font-semibold flex items-center gap-2 transition-all ${
                  canActivate && !isActivating
                    ? 'bg-green-600 text-white hover:bg-green-700 hover:shadow-lg'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
                title={!canActivate ? overallReadiness.blocking_reasons.join(', ') : ''}
              >
                {isActivating ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Activating...
                  </>
                ) : (
                  <>
                    <Power className="w-5 h-5" />
                    Activate Local AI
                  </>
                )}
              </button>
            )}

            {/* Disable Button */}
            {isActive && (
              <button
                onClick={() => handleOpenModal('disable')}
                disabled={isActivating}
                className="px-6 py-3 bg-red-600 text-white rounded-lg font-semibold hover:bg-red-700 flex items-center gap-2 transition-colors disabled:opacity-50"
              >
                <Power className="w-5 h-5" />
                Disable Local AI
              </button>
            )}
          </div>
        </div>

        {/* Quick Stats */}
        {isActive && (
          <div className="mt-4 pt-4 border-t border-gray-200 grid grid-cols-3 gap-4">
            <div>
              <div className="text-2xl font-bold text-gray-900">
                {overallReadiness.ready_intents.length}
              </div>
              <div className="text-xs text-gray-600">Active Intents</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-900">
                {(overallReadiness.avg_similarity * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-gray-600">Avg Quality</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">
                ${overallReadiness.estimated_cost_savings.toFixed(0)}
              </div>
              <div className="text-xs text-gray-600">Monthly Savings</div>
            </div>
          </div>
        )}
      </div>

      {/* Confirmation Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className={`p-6 border-b ${
              actionType === 'activate' ? 'border-green-200' : 'border-red-200'
            }`}>
              <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                {actionType === 'activate' ? (
                  <>
                    <CheckCircle className="w-6 h-6 text-green-600" />
                    Activate Local AI
                  </>
                ) : (
                  <>
                    <AlertTriangle className="w-6 h-6 text-red-600" />
                    Disable Local AI
                  </>
                )}
              </h3>
            </div>

            <div className="p-6 space-y-4">
              {actionType === 'activate' ? (
                <>
                  <p className="text-gray-700">
                    You're about to activate local AI for{' '}
                    <strong>{overallReadiness.ready_intents.length} intent(s)</strong>.
                  </p>
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800">
                    <strong>Ready Intents:</strong>{' '}
                    {overallReadiness.ready_intents.join(', ').toUpperCase()}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Starting Traffic Percentage
                    </label>
                    <input
                      type="number"
                      min="5"
                      max="50"
                      value={startPercentage}
                      onChange={(e) => setStartPercentage(Number(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    />
                    <p className="text-xs text-gray-600 mt-1">
                      Start conservatively (10-20%) and increase gradually
                    </p>
                  </div>
                </>
              ) : (
                <p className="text-gray-700">
                  This will disable local AI and route all requests back to the teacher AI (OpenAI).
                </p>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Reason (Required)
                </label>
                <textarea
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="e.g., Initial production deployment, Quality metrics stable"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={3}
                />
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-lg text-sm">
                  {error}
                </div>
              )}
            </div>

            <div className="p-6 border-t border-gray-200 flex items-center justify-between">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Cancel
              </button>

              <div className="flex items-center gap-2">
                {actionType === 'disable' && isActive && (
                  <button
                    onClick={handleEmergencyDisable}
                    className="px-4 py-2 bg-red-700 text-white rounded-lg hover:bg-red-800 transition-colors text-sm"
                  >
                    Emergency Stop
                  </button>
                )}
                <button
                  onClick={handleConfirm}
                  disabled={!reason.trim() || isActivating}
                  className={`px-6 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                    actionType === 'activate'
                      ? 'bg-green-600 text-white hover:bg-green-700'
                      : 'bg-red-600 text-white hover:bg-red-700'
                  }`}
                >
                  {isActivating ? 'Processing...' : 'Confirm'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
