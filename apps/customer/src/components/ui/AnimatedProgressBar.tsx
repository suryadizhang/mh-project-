'use client';

import React from 'react';

interface ProgressStep {
  icon: string;
  completedIcon?: string;
  label: string;
  isComplete: boolean;
}

interface AnimatedProgressBarProps {
  steps: ProgressStep[];
  className?: string;
}

export function AnimatedProgressBar({ steps, className = '' }: AnimatedProgressBarProps) {
  const completedCount = steps.filter((s) => s.isComplete).length;
  const percentage = Math.round((completedCount / steps.length) * 100);

  const getMessage = () => {
    if (percentage === 100) return '🎉 All sections complete! Ready to submit.';
    if (percentage >= 75) return '💪 Almost there! Just a few more fields.';
    if (percentage >= 50) return '👍 Great progress! Keep going.';
    return '✨ Fill in the sections below to complete your booking.';
  };

  return (
    <div className={`rounded-2xl border border-gray-200 bg-white p-6 shadow-lg ${className}`}>
      <h3 className="mb-6 text-center text-lg font-bold text-gray-900">📋 Booking Progress</h3>

      {/* Progress Steps with Connecting Lines */}
      <div className="relative">
        {/* Connecting Line Background */}
        <div className="absolute top-7 right-0 left-0 mx-8 hidden h-1 bg-gray-200 md:block" />
        {/* Animated Progress Line */}
        <div
          className="absolute top-7 left-0 mx-8 hidden h-1 bg-gradient-to-r from-red-500 via-orange-500 to-green-500 transition-all duration-700 ease-out md:block"
          style={{
            width: `calc(${percentage}% - 4rem)`,
          }}
        />

        <div className="relative z-10 grid grid-cols-2 gap-4 text-center md:grid-cols-4">
          {steps.map((step, index) => (
            <div key={index} className="group space-y-3">
              <div
                className={`mx-auto flex h-14 w-14 transform items-center justify-center rounded-full text-2xl transition-all duration-500 ${
                  step.isComplete
                    ? 'scale-110 bg-gradient-to-br from-green-400 to-green-600 text-white shadow-lg shadow-green-200'
                    : 'bg-gray-100 text-gray-400 group-hover:bg-gray-200'
                }`}
              >
                {step.isComplete ? step.completedIcon || '✓' : step.icon}
              </div>
              <div>
                <div className="font-semibold text-gray-800">{step.label}</div>
                <div
                  className={`text-xs font-medium transition-colors duration-300 ${
                    step.isComplete ? 'text-green-600' : 'text-gray-400'
                  }`}
                >
                  {step.isComplete ? '✓ Complete' : '○ Pending'}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Enhanced Overall Progress Bar */}
      <div className="mt-8">
        <div className="mb-3 flex items-center justify-between">
          <span className="text-sm font-medium text-gray-600">Form Completion</span>
          <span className="bg-gradient-to-r from-red-600 to-orange-500 bg-clip-text text-lg font-bold text-transparent">
            {percentage}%
          </span>
        </div>
        <div className="h-4 w-full overflow-hidden rounded-full bg-gray-100 shadow-inner">
          <div
            className="relative h-full rounded-full bg-gradient-to-r from-red-500 via-orange-500 to-green-500 transition-all duration-700 ease-out"
            style={{ width: `${percentage}%` }}
          >
            {/* Animated shine effect */}
            <div className="absolute inset-0 animate-pulse bg-gradient-to-r from-transparent via-white/30 to-transparent" />
          </div>
        </div>
        {/* Progress message */}
        <p className="mt-3 text-center text-sm text-gray-500">{getMessage()}</p>
      </div>
    </div>
  );
}

export default AnimatedProgressBar;
