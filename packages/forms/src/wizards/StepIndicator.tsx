'use client';

import React from 'react';
import { Check } from 'lucide-react';
import type { WizardStep } from '../types';

/**
 * Props for StepIndicator component
 */
export interface StepIndicatorProps {
  /** Current step (1-indexed) */
  currentStep: number;

  /** Total number of steps */
  totalSteps?: number;

  /** Step configurations (overrides totalSteps if provided) */
  steps?: WizardStep[];

  /** Visual variant */
  variant?: 'dots' | 'numbers' | 'labels' | 'progress';

  /** Allow clicking on steps to navigate */
  allowStepClick?: boolean;

  /** Only allow clicking on completed steps */
  onlyCompletedClickable?: boolean;

  /** Callback when a step is clicked */
  onStepClick?: (step: number) => void;

  /** Show step labels below indicators */
  showLabels?: boolean;

  /** Size variant */
  size?: 'sm' | 'md' | 'lg';

  /** Orientation */
  orientation?: 'horizontal' | 'vertical';

  /** Additional CSS class */
  className?: string;
}

/**
 * Default step labels if none provided
 */
const defaultSteps: WizardStep[] = [
  { id: 1, label: 'Step 1' },
  { id: 2, label: 'Step 2' },
  { id: 3, label: 'Step 3' },
  { id: 4, label: 'Step 4' },
];

/**
 * Reusable step indicator for multi-step forms/wizards
 *
 * @example
 * // Simple dots
 * <StepIndicator currentStep={2} totalSteps={4} variant="dots" />
 *
 * @example
 * // With labels
 * <StepIndicator
 *   currentStep={1}
 *   steps={[
 *     { id: 1, label: 'Contact Info' },
 *     { id: 2, label: 'Event Details' },
 *     { id: 3, label: 'Review' },
 *   ]}
 *   variant="labels"
 *   showLabels={true}
 * />
 *
 * @example
 * // Clickable steps
 * <StepIndicator
 *   currentStep={currentStep}
 *   totalSteps={4}
 *   allowStepClick={true}
 *   onlyCompletedClickable={true}
 *   onStepClick={(step) => setCurrentStep(step)}
 * />
 */
export function StepIndicator({
  currentStep,
  totalSteps,
  steps: customSteps,
  variant = 'dots',
  allowStepClick = false,
  onlyCompletedClickable = true,
  onStepClick,
  showLabels = false,
  size = 'md',
  orientation = 'horizontal',
  className = '',
}: StepIndicatorProps) {
  // Determine steps array
  const steps: WizardStep[] = customSteps ??
    Array.from({ length: totalSteps ?? 4 }, (_, i) => ({
      id: i + 1,
      label: `Step ${i + 1}`,
    }));

  // Size classes
  const sizeClasses = {
    sm: {
      dot: 'h-2 w-2',
      number: 'h-6 w-6 text-xs',
      connector: 'h-0.5',
      icon: 'h-3 w-3',
    },
    md: {
      dot: 'h-3 w-3',
      number: 'h-8 w-8 text-sm',
      connector: 'h-0.5',
      icon: 'h-4 w-4',
    },
    lg: {
      dot: 'h-4 w-4',
      number: 'h-10 w-10 text-base',
      connector: 'h-1',
      icon: 'h-5 w-5',
    },
  };

  const sizes = sizeClasses[size];

  // Check if step is clickable
  const isStepClickable = (stepNum: number): boolean => {
    if (!allowStepClick) return false;
    if (onlyCompletedClickable) {
      return stepNum < currentStep;
    }
    return true;
  };

  // Handle step click
  const handleStepClick = (stepNum: number) => {
    if (isStepClickable(stepNum) && onStepClick) {
      onStepClick(stepNum);
    }
  };

  // Get step state
  const getStepState = (stepNum: number): 'completed' | 'current' | 'upcoming' => {
    if (stepNum < currentStep) return 'completed';
    if (stepNum === currentStep) return 'current';
    return 'upcoming';
  };

  // Progress bar variant
  if (variant === 'progress') {
    const progress = ((currentStep - 1) / (steps.length - 1)) * 100;

    return (
      <div className={`w-full ${className}`}>
        <div className="relative h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="absolute left-0 top-0 h-full bg-primary-600 transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        {showLabels && (
          <div className="flex justify-between mt-2">
            {steps.map((step) => (
              <span
                key={step.id}
                className={`text-xs ${step.id <= currentStep ? 'text-primary-600 font-medium' : 'text-gray-400'
                  }`}
              >
                {step.label}
              </span>
            ))}
          </div>
        )}
      </div>
    );
  }

  // Container classes based on orientation
  const containerClass = orientation === 'horizontal'
    ? 'flex items-center justify-between'
    : 'flex flex-col items-start space-y-4';

  return (
    <div className={`${containerClass} ${className}`}>
      {steps.map((step, index) => {
        const state = getStepState(step.id);
        const isClickable = isStepClickable(step.id);
        const isLast = index === steps.length - 1;

        return (
          <React.Fragment key={step.id}>
            <div
              className={`flex flex-col items-center ${orientation === 'vertical' ? 'flex-row gap-3' : ''
                }`}
            >
              {/* Step indicator */}
              <button
                type="button"
                onClick={() => handleStepClick(step.id)}
                disabled={!isClickable}
                className={`
                  flex items-center justify-center rounded-full transition-all
                  ${variant === 'dots' ? sizes.dot : sizes.number}
                  ${isClickable ? 'cursor-pointer hover:scale-110' : 'cursor-default'}
                  ${state === 'completed'
                    ? 'bg-primary-600 text-white'
                    : state === 'current'
                      ? 'bg-primary-600 text-white ring-4 ring-primary-200'
                      : 'bg-gray-200 text-gray-500'
                  }
                `}
                aria-label={`Step ${step.id}: ${step.label}`}
                aria-current={state === 'current' ? 'step' : undefined}
              >
                {variant === 'dots' ? null : (
                  state === 'completed' ? (
                    <Check className={sizes.icon} />
                  ) : (
                    <span>{step.id}</span>
                  )
                )}
              </button>

              {/* Label */}
              {(showLabels || variant === 'labels') && (
                <span
                  className={`
                    mt-1 text-center
                    ${size === 'sm' ? 'text-xs' : 'text-sm'}
                    ${state === 'current'
                      ? 'text-primary-600 font-medium'
                      : state === 'completed'
                        ? 'text-gray-700'
                        : 'text-gray-400'
                    }
                    ${orientation === 'vertical' ? 'mt-0' : ''}
                  `}
                >
                  {step.label}
                </span>
              )}
            </div>

            {/* Connector line (not for last step) */}
            {!isLast && orientation === 'horizontal' && (
              <div
                className={`
                  flex-1 mx-2 ${sizes.connector} rounded-full
                  ${state === 'completed' || (state === 'current' && index < currentStep - 1)
                    ? 'bg-primary-600'
                    : 'bg-gray-200'
                  }
                `}
                aria-hidden="true"
              />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}

export default StepIndicator;
