'use client';

import React from 'react';
import { User, MapPin, Users, CalendarCheck } from 'lucide-react';
import { BookingStep } from '../types';

// Step configuration
const BOOKING_STEPS: BookingStep[] = [
  { step: 1, label: 'Contact', icon: User },
  { step: 2, label: 'Venue', icon: MapPin },
  { step: 3, label: 'Party Size', icon: Users },
  { step: 4, label: 'Date & Time', icon: CalendarCheck },
];

interface StepIndicatorProps {
  currentStep: number;
  totalSteps?: number;
  onStepClick?: (step: number) => void;
  completedSteps?: number[];
  variant?: 'dots' | 'numbers' | 'icons';
}

/**
 * Step indicator for multi-step booking form
 * Shows progress through the booking wizard
 */
export function StepIndicator({
  currentStep,
  totalSteps = 4,
  onStepClick,
  completedSteps = [],
  variant = 'icons',
}: StepIndicatorProps) {
  return (
    <div className="mb-8">
      <div className="flex items-center justify-between">
        {BOOKING_STEPS.slice(0, totalSteps).map((step, index) => {
          const isActive = currentStep === step.step;
          const isCompleted = completedSteps.includes(step.step) || currentStep > step.step;
          const isClickable = onStepClick && (isCompleted || step.step <= currentStep);
          const IconComponent = step.icon;

          return (
            <React.Fragment key={step.step}>
              {/* Step Circle */}
              <button
                type="button"
                onClick={() => isClickable && onStepClick?.(step.step)}
                disabled={!isClickable}
                className={`relative flex flex-col items-center ${isClickable ? 'cursor-pointer' : 'cursor-default'} `}
              >
                {/* Circle */}
                <div
                  className={`flex h-12 w-12 items-center justify-center rounded-full transition-all ${
                    isActive
                      ? 'bg-gradient-to-r from-amber-500 to-orange-600 text-white shadow-lg shadow-amber-500/25'
                      : isCompleted
                        ? 'bg-green-500 text-white'
                        : 'bg-gray-700 text-gray-400'
                  } `}
                >
                  {variant === 'icons' ? (
                    <IconComponent className="h-5 w-5" />
                  ) : variant === 'numbers' ? (
                    <span className="text-sm font-semibold">{step.step}</span>
                  ) : (
                    <div
                      className={`h-3 w-3 rounded-full ${
                        isActive || isCompleted ? 'bg-white' : 'bg-gray-500'
                      }`}
                    />
                  )}
                </div>

                {/* Label */}
                <span
                  className={`mt-2 text-xs font-medium ${isActive ? 'text-amber-500' : isCompleted ? 'text-green-400' : 'text-gray-500'} `}
                >
                  {step.label}
                </span>

                {/* Active indicator */}
                {isActive && (
                  <div className="absolute -bottom-1 left-1/2 h-2 w-2 -translate-x-1/2 animate-pulse rounded-full bg-amber-500" />
                )}
              </button>

              {/* Connector Line */}
              {index < totalSteps - 1 && (
                <div className="mx-2 flex-1">
                  <div
                    className={`h-0.5 transition-all ${
                      currentStep > step.step ? 'bg-green-500' : 'bg-gray-700'
                    }`}
                  />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Progress bar (alternative visual) */}
      <div className="mt-4 h-1 overflow-hidden rounded-full bg-gray-700">
        <div
          className="h-full bg-gradient-to-r from-amber-500 to-orange-600 transition-all duration-500"
          style={{ width: `${((currentStep - 1) / (totalSteps - 1)) * 100}%` }}
        />
      </div>
    </div>
  );
}
