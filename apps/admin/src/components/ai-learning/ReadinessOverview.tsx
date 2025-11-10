/**
 * ReadinessOverview Component
 *
 * Displays overall AI readiness score, status, and key metrics
 * Shows at-a-glance system health and activation status
 */

'use client';

import {
  Activity,
  AlertCircle,
  CheckCircle,
  DollarSign,
  TrendingUp,
  Zap,
} from 'lucide-react';
import React from 'react';

import type { ReadinessDashboard } from '@/types/aiReadiness';

interface ReadinessOverviewProps {
  dashboard: ReadinessDashboard;
  onRefresh: () => void;
  isRefreshing: boolean;
}

export function ReadinessOverview({
  dashboard,
  onRefresh,
  isRefreshing,
}: ReadinessOverviewProps) {
  const { overall_readiness } = dashboard;

  // Determine status color and icon
  const getStatusDisplay = () => {
    switch (overall_readiness.status) {
      case 'ready':
        return {
          color: 'text-green-600 bg-green-50 border-green-200',
          icon: <CheckCircle className="w-5 h-5" />,
          label: 'Ready to Activate',
        };
      case 'training':
        return {
          color: 'text-blue-600 bg-blue-50 border-blue-200',
          icon: <Activity className="w-5 h-5 animate-pulse" />,
          label: 'Collecting Training Data',
        };
      case 'not_ready':
        return {
          color: 'text-yellow-600 bg-yellow-50 border-yellow-200',
          icon: <AlertCircle className="w-5 h-5" />,
          label: 'Not Ready Yet',
        };
      default:
        return {
          color: 'text-gray-600 bg-gray-50 border-gray-200',
          icon: <AlertCircle className="w-5 h-5" />,
          label: 'Unknown Status',
        };
    }
  };

  const statusDisplay = getStatusDisplay();

  // Calculate readiness score color
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 50) return 'text-blue-600';
    if (score >= 30) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            AI Readiness Overview
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            Shadow learning system monitoring and activation control
          </p>
        </div>
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
        >
          <Activity
            className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`}
          />
          {isRefreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {/* Main Score Display */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        {/* Readiness Score */}
        <div className="relative">
          <div className="text-center">
            <div
              className={`text-5xl font-bold ${getScoreColor(overall_readiness.score)}`}
            >
              {overall_readiness.score}%
            </div>
            <div className="text-sm text-gray-600 mt-2">Overall Readiness</div>
          </div>
          <div
            className={`mt-4 px-4 py-2 rounded-lg border flex items-center gap-2 ${statusDisplay.color}`}
          >
            {statusDisplay.icon}
            <span className="font-medium text-sm">{statusDisplay.label}</span>
          </div>
        </div>

        {/* Training Data Collected */}
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-purple-700 font-medium">Training Pairs</span>
            <Activity className="w-5 h-5 text-purple-600" />
          </div>
          <div className="text-3xl font-bold text-purple-900">
            {overall_readiness.total_pairs_collected.toLocaleString()}
          </div>
          <div className="text-xs text-purple-700 mt-1">
            High-quality teacher-student pairs
          </div>
        </div>

        {/* Average Similarity */}
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-blue-700 font-medium">Avg Similarity</span>
            <TrendingUp className="w-5 h-5 text-blue-600" />
          </div>
          <div className="text-3xl font-bold text-blue-900">
            {(overall_readiness.avg_similarity * 100).toFixed(1)}%
          </div>
          <div className="text-xs text-blue-700 mt-1">
            Student matching teacher quality
          </div>
        </div>

        {/* Estimated Savings */}
        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-green-700 font-medium">Cost Savings</span>
            <DollarSign className="w-5 h-5 text-green-600" />
          </div>
          <div className="text-3xl font-bold text-green-900">
            ${overall_readiness.estimated_cost_savings.toFixed(2)}
          </div>
          <div className="text-xs text-green-700 mt-1">
            Potential monthly savings
          </div>
        </div>
      </div>

      {/* Ready Intents */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-green-600" />
            Ready Intents ({overall_readiness.ready_intents.length})
          </h3>
          <div className="flex flex-wrap gap-2">
            {overall_readiness.ready_intents.length > 0 ? (
              overall_readiness.ready_intents.map(intent => (
                <span
                  key={intent}
                  className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium"
                >
                  {intent.toUpperCase()}
                </span>
              ))
            ) : (
              <span className="text-gray-500 text-sm italic">
                No intents ready yet
              </span>
            )}
          </div>
        </div>

        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <Activity className="w-4 h-4 text-blue-600" />
            Training Intents ({overall_readiness.training_intents.length})
          </h3>
          <div className="flex flex-wrap gap-2">
            {overall_readiness.training_intents.length > 0 ? (
              overall_readiness.training_intents.map(intent => (
                <span
                  key={intent}
                  className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium"
                >
                  {intent.toUpperCase()}
                </span>
              ))
            ) : (
              <span className="text-gray-500 text-sm italic">
                No intents training
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Blocking Reasons (if not ready) */}
      {!overall_readiness.can_activate &&
        overall_readiness.blocking_reasons.length > 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-yellow-800 mb-2 flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              Activation Requirements
            </h3>
            <ul className="space-y-1">
              {overall_readiness.blocking_reasons.map((reason, index) => (
                <li
                  key={index}
                  className="text-sm text-yellow-700 flex items-start gap-2"
                >
                  <span className="text-yellow-500 mt-0.5">•</span>
                  <span>{reason}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

      {/* Recommendations */}
      {dashboard.recommendations && dashboard.recommendations.length > 0 && (
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-blue-800 mb-2 flex items-center gap-2">
            <Zap className="w-4 h-4" />
            Recommendations
          </h3>
          <ul className="space-y-1">
            {dashboard.recommendations.map((recommendation, index) => (
              <li
                key={index}
                className="text-sm text-blue-700 flex items-start gap-2"
              >
                <span className="text-blue-500 mt-0.5">→</span>
                <span>{recommendation}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
