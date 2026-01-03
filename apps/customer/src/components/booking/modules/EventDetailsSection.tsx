'use client';

import {
  AlertCircle,
  Baby,
  Car,
  ChevronDown,
  ChevronUp,
  DollarSign,
  Minus,
  Plus,
  Users,
} from 'lucide-react';
import React, { useCallback, useMemo, useState } from 'react';
import { Control, Controller, FieldErrors, UseFormSetValue, UseFormWatch } from 'react-hook-form';

/**
 * Event Details form data structure (with toddlers and tips)
 */
export interface EventDetailsFormData {
  adults: number;
  children: number;
  toddlers: number;
  tipPercentage: TipPercentage;
  customTipAmount?: number;
}

/**
 * Tip percentage options
 */
export type TipPercentage = 0 | 20 | 25 | 30 | 'custom';

/**
 * Cost breakdown structure
 */
export interface CostBreakdown {
  baseAdults: number;
  baseChildren: number;
  travelFee: number;
  subtotal: number;
  tipAmount: number;
  total: number;
  depositAmount: number;
  /** Original food cost before minimum applied */
  foodCost?: number;
  /** Effective food cost after minimum enforcement */
  effectiveFoodCost?: number;
  /** Whether minimum order was applied */
  minimumApplied?: boolean;
  /** The minimum order threshold */
  partyMinimum?: number;
}

export interface EventDetailsSectionProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  control: Control<any>;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  errors: FieldErrors<any>;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  watch: UseFormWatch<any>;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  setValue: UseFormSetValue<any>;
  className?: string;
  showCompletionBadge?: boolean;
  /** Price per adult (from API - no default) */
  adultPrice: number;
  /** Price per child (from API - no default) */
  childPrice: number;
  /** Age under which children are free */
  childFreeUnderAge?: number;
  /** Travel fee from VenueAddressSection */
  travelFee?: number;
  /** Minimum party order amount (from API - no default) */
  partyMinimum: number;
  /** Fixed deposit amount (from API - no default) */
  depositAmount: number;
  /** Callback when cost changes */
  onCostChange?: (cost: CostBreakdown) => void;
  /** Alias callback for page compatibility */
  onCostBreakdownChange?: (cost: CostBreakdown) => void;
  /** Loading state for pricing data */
  isLoading?: boolean;
}

/**
 * Counter input component with +/- buttons
 */
const CounterInput: React.FC<{
  id: string;
  label: string;
  value: number;
  min?: number;
  max?: number;
  priceLabel?: string;
  hint?: React.ReactNode;
  error?: string;
  onChange: (value: number) => void;
  icon?: React.ReactNode;
  required?: boolean;
}> = ({
  id,
  label,
  value,
  min = 0,
  max = 50,
  priceLabel,
  hint,
  error,
  onChange,
  icon,
  required = false,
}) => {
  const handleDecrement = () => {
    if (value > min) onChange(value - 1);
  };

  const handleIncrement = () => {
    if (value < max) onChange(value + 1);
  };

  return (
    <div className="flex flex-col space-y-1.5">
      <label htmlFor={id} className="flex items-center gap-2 text-sm font-semibold text-gray-700">
        {icon}
        {label}
        {required && <span className="text-red-500">*</span>}
      </label>
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={handleDecrement}
          disabled={value <= min}
          className={`flex h-10 w-10 items-center justify-center rounded-lg border-2 transition-all duration-200 ${
            value <= min
              ? 'cursor-not-allowed border-gray-200 bg-gray-100 text-gray-400'
              : 'border-gray-300 bg-white text-gray-700 hover:border-red-500 hover:bg-red-50'
          }`}
          aria-label={`Decrease ${label}`}
        >
          <Minus className="h-4 w-4" />
        </button>
        <input
          id={id}
          type="number"
          min={min}
          max={max}
          value={value}
          onChange={(e) => {
            const newValue = parseInt(e.target.value, 10);
            if (!isNaN(newValue) && newValue >= min && newValue <= max) {
              onChange(newValue);
            }
          }}
          className={`h-10 w-16 rounded-lg border-2 text-center text-lg font-semibold transition-all duration-200 focus:ring-2 focus:ring-offset-1 focus:outline-none ${
            error
              ? 'border-red-300 bg-red-50 focus:border-red-500 focus:ring-red-200'
              : 'border-gray-200 hover:border-gray-300 focus:border-red-500 focus:ring-red-200'
          }`}
        />
        <button
          type="button"
          onClick={handleIncrement}
          disabled={value >= max}
          className={`flex h-10 w-10 items-center justify-center rounded-lg border-2 transition-all duration-200 ${
            value >= max
              ? 'cursor-not-allowed border-gray-200 bg-gray-100 text-gray-400'
              : 'border-gray-300 bg-white text-gray-700 hover:border-red-500 hover:bg-red-50'
          }`}
          aria-label={`Increase ${label}`}
        >
          <Plus className="h-4 w-4" />
        </button>
      </div>
      {error ? (
        <p className="flex items-center gap-1 text-sm text-red-600">
          <AlertCircle className="h-4 w-4" />
          {error}
        </p>
      ) : (
        <>
          {priceLabel && <p className="text-xs font-medium text-green-600">{priceLabel}</p>}
          {hint && <div className="text-xs text-gray-500">{hint}</div>}
        </>
      )}
    </div>
  );
};

/**
 * EventDetailsSection - Guest counts, toddlers, tips, and total cost estimate
 */
export const EventDetailsSection: React.FC<EventDetailsSectionProps> = ({
  control,
  errors,
  watch,
  setValue,
  className = '',
  showCompletionBadge = true,
  adultPrice,
  childPrice,
  childFreeUnderAge = 5,
  travelFee = 0,
  partyMinimum,
  depositAmount: depositAmountProp,
  onCostChange,
  onCostBreakdownChange,
  isLoading = false,
}) => {
  // Watch values
  const adults = watch('adults') || 0;
  const children = watch('children') || 0;
  const toddlers = watch('toddlers') || 0;
  const tipPercentage = watch('tipPercentage') ?? 25;
  const customTipAmount = watch('customTipAmount') || 0;

  // State for collapsible breakdown
  const [isBreakdownExpanded, setIsBreakdownExpanded] = useState(false);

  // Check if section is complete
  const isComplete = adults >= 1;

  // Calculate all costs with minimum order enforcement
  const costBreakdown = useMemo<CostBreakdown>(() => {
    const baseAdults = adults * adultPrice;
    const baseChildren = children * childPrice;
    const foodCost = baseAdults + baseChildren;

    // Enforce minimum order (food cost must meet or exceed partyMinimum)
    const effectiveFoodCost = Math.max(foodCost, partyMinimum);
    const minimumApplied = foodCost < partyMinimum && (adults > 0 || children > 0);

    const subtotal = effectiveFoodCost + travelFee;

    // Calculate tip on the full subtotal (including minimum)
    let tipAmount = 0;
    if (tipPercentage === 'custom') {
      tipAmount = customTipAmount || 0;
    } else if (typeof tipPercentage === 'number' && tipPercentage > 0) {
      tipAmount = (subtotal * tipPercentage) / 100;
    }

    const total = subtotal + tipAmount;
    // Default to $100 if depositAmount prop is undefined (SSoT fallback)
    const depositAmount = depositAmountProp ?? 100;

    return {
      baseAdults,
      baseChildren,
      travelFee,
      subtotal,
      tipAmount,
      total,
      depositAmount,
      // Additional info for minimum order display
      foodCost,
      effectiveFoodCost,
      minimumApplied,
      partyMinimum,
    } as CostBreakdown;
  }, [
    adults,
    children,
    adultPrice,
    childPrice,
    travelFee,
    tipPercentage,
    customTipAmount,
    partyMinimum,
    depositAmountProp,
  ]);

  // Notify parent of cost changes
  React.useEffect(() => {
    onCostChange?.(costBreakdown);
    onCostBreakdownChange?.(costBreakdown);
  }, [costBreakdown, onCostChange, onCostBreakdownChange]);

  // Handle counter changes
  const handleCounterChange = useCallback(
    (field: string, value: number) => {
      setValue(field, value, { shouldValidate: true });
    },
    [setValue],
  );

  // Show loading state when pricing data is loading
  if (isLoading) {
    return (
      <div className={`space-y-6 ${className}`}>
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center gap-2">
            <Users className="h-5 w-5 text-gray-400" />
            <span className="text-lg font-semibold text-gray-400">Loading pricing...</span>
          </div>
          <div className="animate-pulse space-y-4">
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
              <div className="h-24 rounded-lg bg-gray-200" />
              <div className="h-24 rounded-lg bg-gray-200" />
              <div className="h-24 rounded-lg bg-gray-200" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Guest Count Section */}
      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-900">
            <Users className="h-5 w-5 text-red-500" />
            Party Size
          </h2>
          {showCompletionBadge && (
            <div className="text-xs">
              {isComplete ? (
                <span className="rounded-full bg-green-100 px-2 py-0.5 font-semibold text-green-800">
                  ✅ Complete
                </span>
              ) : (
                <span className="rounded-full bg-amber-100 px-2 py-0.5 text-amber-800">
                  ⏳ Pending
                </span>
              )}
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
          {/* Adults Counter */}
          <Controller
            name="adults"
            control={control}
            rules={{
              required: 'At least 1 adult is required',
              min: { value: 1, message: 'At least 1 adult is required' },
              max: { value: 50, message: 'Maximum 50 adults' },
            }}
            render={({ field }) => (
              <CounterInput
                id="adults"
                label="Adults (13+)"
                value={field.value || 0}
                min={1}
                max={50}
                priceLabel={`$${adultPrice} per person`}
                error={(errors.adults as { message?: string })?.message}
                onChange={(v) => handleCounterChange('adults', v)}
                icon={<Users className="h-4 w-4 text-gray-400" />}
                required
              />
            )}
          />

          {/* Children Counter */}
          <Controller
            name="children"
            control={control}
            rules={{
              min: { value: 0, message: 'Cannot be negative' },
              max: { value: 20, message: 'Maximum 20 children' },
            }}
            render={({ field }) => (
              <CounterInput
                id="children"
                label="Children (6-12)"
                value={field.value || 0}
                min={0}
                max={20}
                priceLabel={`$${childPrice} per child`}
                error={(errors.children as { message?: string })?.message}
                onChange={(v) => handleCounterChange('children', v)}
                icon={<Baby className="h-4 w-4 text-gray-400" />}
              />
            )}
          />

          {/* Toddlers Counter */}
          <Controller
            name="toddlers"
            control={control}
            rules={{
              min: { value: 0, message: 'Cannot be negative' },
              max: { value: 15, message: 'Maximum 15 toddlers' },
            }}
            render={({ field }) => (
              <CounterInput
                id="toddlers"
                label={`Toddlers (${childFreeUnderAge} & under)`}
                value={field.value || 0}
                min={0}
                max={15}
                priceLabel="FREE! 🎉"
                hint={
                  <span className="text-amber-600">Please let us know for food preparation</span>
                }
                error={(errors.toddlers as { message?: string })?.message}
                onChange={(v) => handleCounterChange('toddlers', v)}
                icon={<Baby className="h-4 w-4 text-pink-400" />}
              />
            )}
          />
        </div>

        {/* Total Guests Summary */}
        {(adults > 0 || children > 0 || toddlers > 0) && (
          <div className="mt-4 rounded-lg bg-gray-50 p-3 text-center">
            <span className="text-sm text-gray-600">Total Party Size: </span>
            <span className="text-lg font-bold text-gray-900">
              {adults + children + toddlers} guests
            </span>
            {toddlers > 0 && (
              <span className="ml-2 text-xs text-amber-600">
                (includes {toddlers} toddler{toddlers !== 1 ? 's' : ''} eating free)
              </span>
            )}
          </div>
        )}
      </div>

      {/* Combined Cost + Tips Section - Only shows when adults > 0 */}
      {adults > 0 && (
        <div className="rounded-xl border-2 border-green-200 bg-gradient-to-r from-green-50 to-emerald-50 p-6 shadow-sm">
          <h3 className="mb-4 flex items-center gap-2 text-lg font-bold text-gray-900">
            <DollarSign className="h-5 w-5 text-green-600" />
            Your Estimated Total
          </h3>

          {/* Collapsible Cost Breakdown */}
          <div className="mb-3 border-b border-green-200 pb-3">
            <button
              type="button"
              onClick={() => setIsBreakdownExpanded(!isBreakdownExpanded)}
              className="flex w-full items-center justify-between text-sm text-gray-600 transition-colors hover:text-gray-900"
              aria-expanded={isBreakdownExpanded}
            >
              <span className="font-medium">View price breakdown</span>
              {isBreakdownExpanded ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </button>

            {/* Expandable breakdown details */}
            <div
              className={`overflow-hidden transition-all duration-300 ease-in-out ${
                isBreakdownExpanded ? 'mt-3 max-h-60 opacity-100' : 'max-h-0 opacity-0'
              }`}
            >
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">
                    {adults} Adult{adults !== 1 ? 's' : ''} × ${adultPrice}
                  </span>
                  <span className="font-medium">${costBreakdown.baseAdults.toFixed(2)}</span>
                </div>
                {children > 0 && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">
                      {children} Child{children !== 1 ? 'ren' : ''} × ${childPrice}
                    </span>
                    <span className="font-medium">${costBreakdown.baseChildren.toFixed(2)}</span>
                  </div>
                )}
                {/* Minimum Order Notice */}
                {costBreakdown.minimumApplied && (
                  <div className="my-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
                    <span className="font-medium">Minimum order: ${partyMinimum}</span>
                    <span className="block text-amber-600">
                      (Your selection ${costBreakdown.foodCost?.toFixed(0)} → adjusted to $
                      {costBreakdown.effectiveFoodCost?.toFixed(0)})
                    </span>
                  </div>
                )}
                {toddlers > 0 && (
                  <div className="flex justify-between text-green-600">
                    <span>
                      {toddlers} Toddler{toddlers !== 1 ? 's' : ''}
                    </span>
                    <span className="font-medium">FREE</span>
                  </div>
                )}
                {travelFee > 0 && (
                  <div className="flex justify-between text-blue-700">
                    <span className="flex items-center gap-1">
                      <Car className="h-4 w-4" />
                      Travel Fee
                    </span>
                    <span className="font-medium">+${travelFee.toFixed(2)}</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Subtotal Display */}
          <div className="rounded-lg bg-white/70 p-4">
            <div className="flex justify-between">
              <span className="text-lg font-bold text-gray-900">Subtotal (Food + Travel)</span>
              <span className="text-2xl font-bold text-green-700">
                ${costBreakdown.subtotal.toFixed(2)}
              </span>
            </div>
            <p className="mt-2 text-xs text-gray-500 italic">
              * Gratuity selection available in the order summary below
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default EventDetailsSection;
