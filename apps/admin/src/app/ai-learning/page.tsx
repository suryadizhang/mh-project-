/**
 * AI Learning Dashboard Page
 * 
 * Complete dashboard for Shadow Learning System monitoring and control
 * Includes: Readiness overview, intent cards, activation control, alerts, and charts
 */

'use client';

import React from 'react';
import { ReadinessOverview } from '@/components/ai-learning/ReadinessOverview';
import { ActivationButton } from '@/components/ai-learning/ActivationButton';
import { useAIReadiness } from '@/hooks/useAIReadiness';
import { AlertCircle, TrendingUp, Activity, Loader2 } from 'lucide-react';

export default function AILearningPage() {
  const {
    dashboard,
    loading,
    refreshing,
    error,
    refresh,
    updateTrafficSplit,
    enableAI,
    disableAI,
    rollbackIntent,
    dismissAlert,
  } = useAIReadiness({
    autoRefresh: true,
    refreshInterval: 30000, // 30 seconds
  });

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading AI Readiness Dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-lg">
          <AlertCircle className="w-12 h-12 text-red-600 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-red-900 text-center mb-2">
            Failed to Load Dashboard
          </h2>
          <p className="text-red-700 text-center mb-4">{error.message}</p>
          <button
            onClick={refresh}
            className="w-full px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!dashboard) {
    return null;
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          AI Learning Dashboard
        </h1>
        <p className="text-gray-600">
          Monitor shadow learning progress, manage AI activation, and track quality metrics
        </p>
      </div>

      {/* Main Readiness Overview */}
      <ReadinessOverview
        dashboard={dashboard}
        onRefresh={refresh}
        isRefreshing={refreshing}
      />

      {/* Activation Button */}
      <ActivationButton
        overallReadiness={dashboard.overall_readiness}
        onActivate={async (reason, intents, startPercentage) => {
          await enableAI(reason, intents as any, startPercentage);
        }}
        onDisable={async (reason, emergency) => {
          await disableAI(reason, emergency);
        }}
        isActivating={false}
        currentMode={dashboard.system_config?.local_ai_mode || 'shadow'}
      />

      {/* Alerts Section */}
      {dashboard.recent_alerts && dashboard.recent_alerts.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-yellow-600" />
            Recent Alerts ({dashboard.recent_alerts.length})
          </h2>
          <div className="space-y-3">
            {dashboard.recent_alerts.map((alert) => (
              <div
                key={alert.id}
                className={`p-4 rounded-lg border flex items-start gap-3 ${
                  alert.severity === 'critical'
                    ? 'bg-red-50 border-red-200'
                    : alert.severity === 'warning'
                    ? 'bg-yellow-50 border-yellow-200'
                    : 'bg-blue-50 border-blue-200'
                }`}
              >
                <AlertCircle
                  className={`w-5 h-5 mt-0.5 ${
                    alert.severity === 'critical'
                      ? 'text-red-600'
                      : alert.severity === 'warning'
                      ? 'text-yellow-600'
                      : 'text-blue-600'
                  }`}
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-gray-900 uppercase text-sm">
                      {alert.intent}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium ${
                        alert.severity === 'critical'
                          ? 'bg-red-100 text-red-700'
                          : alert.severity === 'warning'
                          ? 'bg-yellow-100 text-yellow-700'
                          : 'bg-blue-100 text-blue-700'
                      }`}
                    >
                      {alert.severity}
                    </span>
                  </div>
                  <p className="text-sm text-gray-700">{alert.message}</p>
                  {alert.metrics && (
                    <div className="mt-2 text-xs text-gray-600">
                      Similarity: {((alert.metrics.current_similarity || 0) * 100).toFixed(1)}%
                      {alert.metrics.threshold && ` (threshold: ${(alert.metrics.threshold * 100).toFixed(1)}%)`}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {alert.auto_rollback_triggered && (
                    <span className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded">
                      Auto-Rollback
                    </span>
                  )}
                  <button
                    onClick={() => dismissAlert(alert.id)}
                    className="text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    ×
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Intent Breakdown */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Activity className="w-5 h-5 text-blue-600" />
          Intent Readiness Breakdown
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(dashboard.intent_breakdown).map(([intent, readiness]) => (
            <div
              key={intent}
              className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="font-semibold text-gray-900 uppercase">{intent}</span>
                <span
                  className={`px-2 py-1 rounded text-xs font-medium ${
                    readiness.status === 'ready'
                      ? 'bg-green-100 text-green-700'
                      : readiness.status === 'training'
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  {readiness.status}
                </span>
              </div>

              {/* Progress Bar */}
              <div className="mb-3">
                <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                  <span>Training Progress</span>
                  <span>{readiness.readiness_score}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all ${
                      readiness.readiness_score >= 80
                        ? 'bg-green-500'
                        : readiness.readiness_score >= 50
                        ? 'bg-blue-500'
                        : 'bg-yellow-500'
                    }`}
                    style={{ width: `${readiness.readiness_score}%` }}
                  />
                </div>
              </div>

              {/* Stats */}
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Pairs Collected:</span>
                  <span className="font-medium text-gray-900">
                    {readiness.pairs_collected} / {readiness.min_pairs_required}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Similarity:</span>
                  <span className="font-medium text-gray-900">
                    {(readiness.avg_similarity * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Traffic:</span>
                  <span className="font-medium text-gray-900">
                    {readiness.current_traffic_percent}%
                  </span>
                </div>
              </div>

              {/* Traffic Control Slider */}
              {readiness.can_activate && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <label className="text-xs text-gray-600 block mb-2">
                    Adjust Traffic Split
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    step="5"
                    value={readiness.current_traffic_percent}
                    onChange={async (e) => {
                      await updateTrafficSplit(
                        readiness.intent,
                        Number(e.target.value)
                      );
                    }}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>0%</span>
                    <span>{readiness.recommended_traffic_percent}% (recommended)</span>
                    <span>100%</span>
                  </div>
                </div>
              )}

              {/* Blocking Reasons */}
              {readiness.blocking_reasons.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <p className="text-xs text-gray-600 mb-1">Blocking Issues:</p>
                  <ul className="space-y-1">
                    {readiness.blocking_reasons.map((reason, idx) => (
                      <li key={idx} className="text-xs text-yellow-700 flex items-start gap-1">
                        <span>•</span>
                        <span>{reason}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Quality Metrics */}
      {dashboard.quality_metrics && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-green-600" />
            Quality Comparison (Teacher vs Student)
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="text-sm text-blue-700 mb-1">Teacher AI (OpenAI)</div>
              <div className="text-2xl font-bold text-blue-900">
                {dashboard.quality_metrics.teacher_metrics.avg_response_time_ms.toFixed(0)}ms
              </div>
              <div className="text-xs text-blue-600 mt-1">Average Response Time</div>
            </div>
            <div className="bg-green-50 rounded-lg p-4">
              <div className="text-sm text-green-700 mb-1">Student AI (Llama3)</div>
              <div className="text-2xl font-bold text-green-900">
                {dashboard.quality_metrics.student_metrics.avg_response_time_ms.toFixed(0)}ms
              </div>
              <div className="text-xs text-green-600 mt-1">Average Response Time</div>
            </div>
            <div className="bg-purple-50 rounded-lg p-4">
              <div className="text-sm text-purple-700 mb-1">Performance Improvement</div>
              <div className="text-2xl font-bold text-purple-900">
                {dashboard.quality_metrics.comparison.cost_savings_percent.toFixed(1)}%
              </div>
              <div className="text-xs text-purple-600 mt-1">Cost Savings</div>
            </div>
          </div>
        </div>
      )}

      {/* ML Predictor Status */}
      {dashboard.ml_predictor_status && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            ML Confidence Predictor Status
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <div className="text-sm text-gray-600 mb-1">Model Version</div>
              <div className="text-lg font-semibold text-gray-900">
                {dashboard.ml_predictor_status.model_version}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600 mb-1">Training Samples</div>
              <div className="text-lg font-semibold text-gray-900">
                {dashboard.ml_predictor_status.training_samples.toLocaleString()}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600 mb-1">Model Accuracy</div>
              <div className="text-lg font-semibold text-green-600">
                {(dashboard.ml_predictor_status.model_accuracy * 100).toFixed(1)}%
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600 mb-1">Total Predictions</div>
              <div className="text-lg font-semibold text-gray-900">
                {dashboard.ml_predictor_status.prediction_stats.total_predictions.toLocaleString()}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
