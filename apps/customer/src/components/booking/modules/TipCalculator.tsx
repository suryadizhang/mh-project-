'use client';

import { DollarSign, Heart, Star, Sparkles } from 'lucide-react';
import React, { useMemo } from 'react';
import { Control, Controller, UseFormWatch } from 'react-hook-form';

/**
 * Tip percentage options
 */
export type TipPercentage = 0 | 15 | 20 | 25 | 30 | 'custom';

/**
 * Tip form data structure
 */
export interface TipFormData {
  tipPercentage: TipPercentage;
  customTipAmount?: number;
}

export interface TipCalculatorProps {
  // Use 'any' to allow parent forms with additional fields
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  control: Control<any>;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  watch: UseFormWatch<any>;
  /** Subtotal before tip (food + travel fee) */
  subtotal: number;
  className?: string;
  /** Whether to show the tip section header */
  showHeader?: boolean;
  /** Callback when tip changes */
  onTipChange?: (tipAmount: number, percentage: TipPercentage) => void;
}

/**
 * Tip option configuration
 */
interface TipOption {
  percentage: TipPercentage;
  label: string;
  sublabel: string;
  icon: React.ReactNode;
  recommended?: boolean;
  description?: string;
}

const TIP_OPTIONS: TipOption[] = [
  {
    percentage: 20,
    label: '20%',
    sublabel: 'Good',
    icon: <Star className="h-5 w-5" />,
    description: 'Shows appreciation for excellent service',
  },
  {
    percentage: 25,
    label: '25%',
    sublabel: 'Recommended',
    icon: <Sparkles className="h-5 w-5" />,
    recommended: true,
    description: 'Our recommended gratuity for your chef',
  },
  {
    percentage: 30,
    label: '30%+',
    sublabel: 'Exceptional',
    icon: <Sparkles className="h-5 w-5 text-amber-500" />,
    description: 'For truly outstanding experience',
  },
];

/**
 * TipCalculator - Gratuity selection component for booking flow
 *
 * Features:
 * - Pre-defined tip percentages (15%, 20%, 25%, 30%)
 * - Custom tip amount option
 * - Real-time calculation based on subtotal
 * - Visual recommendation for 25%
 * - Explanation of gratuity importance
 */
export const TipCalculator: React.FC<TipCalculatorProps> = ({
  control,
  watch,
  subtotal,
  className = '',
  showHeader = true,
  onTipChange,
}) => {
  // Watch tip values
  const tipPercentage = watch('tipPercentage') || 0;
  const customTipAmount = watch('customTipAmount') || 0;

  // Calculate tip amount
  const tipAmount = useMemo(() => {
    if (tipPercentage === 'custom') {
      return customTipAmount || 0;
    }
    if (typeof tipPercentage === 'number' && tipPercentage > 0) {
      return (subtotal * tipPercentage) / 100;
    }
    return 0;
  }, [tipPercentage, customTipAmount, subtotal]);

  // Calculate total with tip
  const totalWithTip = useMemo(() => {
    return subtotal + tipAmount;
  }, [subtotal, tipAmount]);

  // Notify parent of tip changes
  React.useEffect(() => {
    if (onTipChange) {
      onTipChange(tipAmount, tipPercentage);
    }
  }, [tipAmount, tipPercentage, onTipChange]);

  /**
   * Get button classes based on selection state
   */
  const getOptionClasses = (option: TipOption, isSelected: boolean): string => {
    const baseClasses =
      'relative flex flex-col items-center justify-center rounded-lg border-2 p-4 transition-all duration-200 cursor-pointer';

    if (isSelected) {
      return `${baseClasses} border-red-500 bg-red-50 text-red-700 ring-2 ring-red-200`;
    }

    if (option.recommended) {
      return `${baseClasses} border-amber-300 bg-amber-50 text-amber-700 hover:border-amber-400 hover:bg-amber-100`;
    }

    return `${baseClasses} border-gray-200 bg-white text-gray-700 hover:border-gray-300 hover:bg-gray-50`;
  };

  return (
    <div className={`rounded-xl border border-gray-200 bg-white p-6 shadow-sm ${className}`}>
      {/* Section Header */}
      {showHeader && (
        <div className="mb-4">
          <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-900">
            <DollarSign className="h-5 w-5 text-green-500" />
            Gratuity for Your Chef
          </h2>
          <p className="mt-1 text-sm text-gray-600">
            Your hibachi chef provides a personalized entertainment and dining experience. Gratuity
            is a wonderful way to show appreciation for their skill and showmanship.
          </p>
        </div>
      )}

      {/* Tip Options Grid */}
      <Controller
        name="tipPercentage"
        control={control}
        defaultValue={0}
        render={({ field }) => (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {TIP_OPTIONS.map((option) => {
              const isSelected = field.value === option.percentage;
              const calculatedAmount = (subtotal * (option.percentage as number)) / 100;

              return (
                <button
                  key={option.percentage}
                  type="button"
                  onClick={() => field.onChange(option.percentage)}
                  className={getOptionClasses(option, isSelected)}
                  aria-label={`Select ${option.label} tip`}
                >
                  {option.recommended && (
                    <span className="absolute -top-2 left-1/2 -translate-x-1/2 rounded-full bg-amber-500 px-2 py-0.5 text-xs font-bold whitespace-nowrap text-white">
                      RECOMMENDED
                    </span>
                  )}
                  <span className="mb-1">{option.icon}</span>
                  <span className="text-xl font-bold">{option.label}</span>
                  <span className="text-xs font-medium">{option.sublabel}</span>
                  <span className="mt-1 text-sm font-semibold text-green-600">
                    ${calculatedAmount.toFixed(2)}
                  </span>
                </button>
              );
            })}
          </div>
        )}
      />

      {/* Custom Tip Option */}
      <div className="mt-4">
        <Controller
          name="tipPercentage"
          control={control}
          render={({ field }) => (
            <div
              className={`rounded-lg border-2 p-4 transition-all ${
                field.value === 'custom' ? 'border-red-500 bg-red-50' : 'border-gray-200 bg-gray-50'
              }`}
            >
              <label className="flex cursor-pointer items-center gap-3">
                <input
                  type="radio"
                  name="tipType"
                  checked={field.value === 'custom'}
                  onChange={() => field.onChange('custom')}
                  className="h-5 w-5 text-red-500 focus:ring-red-500"
                />
                <div className="flex-1">
                  <span className="font-semibold text-gray-900">Custom Amount</span>
                  <p className="text-xs text-gray-500">Enter your own tip amount</p>
                </div>
                {field.value === 'custom' && (
                  <Controller
                    name="customTipAmount"
                    control={control}
                    render={({ field: customField }) => (
                      <div className="flex items-center gap-1">
                        <span className="text-lg font-semibold text-gray-700">$</span>
                        <input
                          type="number"
                          min={0}
                          step={5}
                          value={customField.value || ''}
                          onChange={(e) => {
                            const value = parseFloat(e.target.value) || 0;
                            customField.onChange(value);
                          }}
                          placeholder="0.00"
                          className="w-24 rounded-md border border-gray-300 px-3 py-2 text-right font-semibold focus:border-red-500 focus:ring-2 focus:ring-red-200 focus:outline-none"
                        />
                      </div>
                    )}
                  />
                )}
              </label>
            </div>
          )}
        />
      </div>

      {/* No Tip Option */}
      <Controller
        name="tipPercentage"
        control={control}
        render={({ field }) => (
          <button
            type="button"
            onClick={() => field.onChange(0)}
            className={`mt-3 w-full rounded-lg border-2 p-3 text-center text-sm transition-all ${
              field.value === 0
                ? 'border-gray-500 bg-gray-100 font-semibold text-gray-700'
                : 'border-gray-200 text-gray-500 hover:border-gray-300'
            }`}
          >
            No tip at this time
          </button>
        )}
      />

      {/* Summary */}
      {subtotal > 0 && (
        <div className="mt-6 rounded-lg border-2 border-green-200 bg-green-50 p-4">
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Subtotal (Food + Travel)</span>
              <span className="font-medium">${subtotal.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">
                Gratuity{' '}
                {tipPercentage !== 'custom' && tipPercentage > 0 ? `(${tipPercentage}%)` : ''}
              </span>
              <span className="font-medium text-green-600">
                {tipAmount > 0 ? `+$${tipAmount.toFixed(2)}` : '$0.00'}
              </span>
            </div>
            <div className="mt-2 flex justify-between border-t border-green-300 pt-2">
              <span className="text-base font-bold text-gray-900">Total</span>
              <span className="text-xl font-bold text-green-700">${totalWithTip.toFixed(2)}</span>
            </div>
          </div>
        </div>
      )}

      {/* Chef appreciation note */}
      <div className="mt-4 rounded-lg bg-amber-50 p-4 text-sm text-amber-800">
        <div className="flex items-start gap-3">
          <Heart className="mt-0.5 h-5 w-5 flex-shrink-0 text-red-500" />
          <div>
            <p className="font-semibold">A Note About Gratuity</p>
            <p className="mt-1 text-xs text-amber-700">
              100% of your gratuity goes directly to your chef. Our chefs are skilled entertainers
              who bring the restaurant experience to your home. Your generosity is greatly
              appreciated and helps recognize their talent and dedication.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TipCalculator;
