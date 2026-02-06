'use client';

import React from 'react';
import { Users, Minus, Plus } from 'lucide-react';
import type {
  FieldErrors,
  UseFormRegister,
  UseFormSetValue,
  UseFormWatch,
  Path,
  FieldValues,
} from 'react-hook-form';
import type { FormLayout } from '../types';

/**
 * Props for GuestCountField component
 */
export interface GuestCountFieldProps<
  TFieldValues extends FieldValues = FieldValues,
> {
  /** react-hook-form register function */
  register: UseFormRegister<TFieldValues>;
  /** react-hook-form errors object */
  errors: FieldErrors<TFieldValues>;
  /** react-hook-form setValue function (required for stepper variant) */
  setValue?: UseFormSetValue<TFieldValues>;
  /** react-hook-form watch function (required for stepper variant) */
  watch?: UseFormWatch<TFieldValues>;

  /** Field name (default: 'guestCount') */
  fieldName?: string;

  /** Minimum guest count */
  min?: number;
  /** Maximum guest count */
  max?: number;

  /** UI variant */
  variant?: 'input' | 'stepper' | 'slider';

  /** Split by age groups (adults/children) */
  splitByAge?: boolean;
  /** Field names for split mode */
  splitFieldNames?: {
    adults: string;
    children: string;
  };

  /** Layout variant */
  layout?: FormLayout;

  /** Show label */
  showLabel?: boolean;

  /** Show icon */
  showIcon?: boolean;

  /** Label text */
  label?: string;

  /** Helper text */
  helperText?: string;

  /** Show guest count tiers/pricing hints */
  showTierHints?: boolean;
  /** Tier thresholds for hints */
  tierThresholds?: number[];

  /** Additional CSS class */
  className?: string;

  /** Disable the field */
  disabled?: boolean;

  /** Callback when value changes */
  onChange?: (value: number) => void;
}

/**
 * Reusable guest count field with various display modes
 *
 * @example
 * // Basic input
 * <GuestCountField register={register} errors={errors} />
 *
 * @example
 * // Stepper with +/- buttons
 * <GuestCountField
 *   register={register}
 *   errors={errors}
 *   setValue={setValue}
 *   watch={watch}
 *   variant="stepper"
 * />
 *
 * @example
 * // Split by age groups
 * <GuestCountField
 *   register={register}
 *   errors={errors}
 *   splitByAge={true}
 *   splitFieldNames={{ adults: 'adultCount', children: 'childCount' }}
 * />
 */
export function GuestCountField<
  TFieldValues extends FieldValues = FieldValues,
>({
  register,
  errors,
  setValue,
  watch,
  fieldName = 'guestCount',
  min = 10,
  max = 100,
  variant = 'input',
  splitByAge = false,
  splitFieldNames = { adults: 'adultCount', children: 'childCount' },
  layout = 'stacked',
  showLabel = true,
  showIcon = false,
  label = 'Number of Guests',
  helperText,
  showTierHints = false,
  tierThresholds = [15, 25, 50],
  className = '',
  disabled = false,
  onChange,
}: GuestCountFieldProps<TFieldValues>) {
  const field = fieldName as Path<TFieldValues>;
  const adultsField = splitFieldNames.adults as Path<TFieldValues>;
  const childrenField = splitFieldNames.children as Path<TFieldValues>;

  // Get error for a field
  const getError = (fieldPath: string): string | undefined => {
    const parts = fieldPath.split('.');
    let error: unknown = errors;
    for (const part of parts) {
      if (error && typeof error === 'object' && part in error) {
        error = (error as Record<string, unknown>)[part];
      } else {
        return undefined;
      }
    }
    return (error as { message?: string })?.message;
  };

  const fieldError = getError(field);

  // Get current value for stepper
  const currentValue = watch ? watch(field) : undefined;
  const numericValue =
    typeof currentValue === 'number'
      ? currentValue
      : parseInt(String(currentValue ?? '')) || min;

  // Handle stepper increment/decrement
  const handleIncrement = () => {
    if (!setValue || disabled) return;
    const newValue = Math.min(numericValue + 1, max);
    setValue(field, newValue as never, { shouldValidate: true });
    onChange?.(newValue);
  };

  const handleDecrement = () => {
    if (!setValue || disabled) return;
    const newValue = Math.max(numericValue - 1, min);
    setValue(field, newValue as never, { shouldValidate: true });
    onChange?.(newValue);
  };

  // Get tier hint based on value
  const getTierHint = (value: number): string => {
    if (value <= tierThresholds[0]) return 'Intimate gathering';
    if (value <= tierThresholds[1]) return 'Medium party';
    if (value <= tierThresholds[2]) return 'Large event';
    return 'Grand celebration';
  };

  // Render split fields for adults/children
  if (splitByAge) {
    const adultsError = getError(adultsField);
    const childrenError = getError(childrenField);

    return (
      <div className={`space-y-4 ${className}`}>
        {showLabel && (
          <label className="form-label font-medium">
            {showIcon && <Users className="mr-1 inline-block h-4 w-4" />}
            {label}
          </label>
        )}

        <div className={layout === 'inline' ? 'flex gap-4' : 'space-y-3'}>
          {/* Adults */}
          <div className="flex-1">
            <label htmlFor={adultsField} className="form-label text-sm">
              Adults
            </label>
            <input
              type="number"
              id={adultsField}
              className={`form-control ${adultsError ? 'is-invalid' : ''}`}
              min={1}
              max={max}
              disabled={disabled}
              {...register(adultsField, {
                required: 'Number of adults is required',
                min: { value: 1, message: 'At least 1 adult required' },
                max: { value: max, message: `Maximum ${max} adults` },
                valueAsNumber: true,
              })}
            />
            {adultsError && (
              <div className="invalid-feedback">{adultsError}</div>
            )}
          </div>

          {/* Children */}
          <div className="flex-1">
            <label htmlFor={childrenField} className="form-label text-sm">
              Children
            </label>
            <input
              type="number"
              id={childrenField}
              className={`form-control ${childrenError ? 'is-invalid' : ''}`}
              min={0}
              max={max}
              disabled={disabled}
              {...register(childrenField, {
                min: { value: 0, message: 'Cannot be negative' },
                max: { value: max, message: `Maximum ${max} children` },
                valueAsNumber: true,
              })}
            />
            {childrenError && (
              <div className="invalid-feedback">{childrenError}</div>
            )}
          </div>
        </div>

        {helperText && <p className="text-sm text-gray-500">{helperText}</p>}
      </div>
    );
  }

  // Render stepper variant
  if (variant === 'stepper' && setValue && watch) {
    return (
      <div className={`form-group ${className}`}>
        {showLabel && (
          <label className="form-label">
            {showIcon && <Users className="mr-1 inline-block h-4 w-4" />}
            {label}
          </label>
        )}

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleDecrement}
            disabled={disabled || numericValue <= min}
            className="btn btn-outline-secondary p-2 rounded-full disabled:opacity-50"
            aria-label="Decrease guest count"
          >
            <Minus className="h-4 w-4" />
          </button>

          <div className="flex-1 text-center">
            <input
              type="number"
              id={field}
              className={`form-control text-center text-lg font-semibold ${fieldError ? 'is-invalid' : ''}`}
              min={min}
              max={max}
              disabled={disabled}
              {...register(field, {
                required: 'Guest count is required',
                min: { value: min, message: `Minimum ${min} guests` },
                max: { value: max, message: `Maximum ${max} guests` },
                valueAsNumber: true,
                onChange: e => onChange?.(parseInt(e.target.value) || min),
              })}
            />
          </div>

          <button
            type="button"
            onClick={handleIncrement}
            disabled={disabled || numericValue >= max}
            className="btn btn-outline-secondary p-2 rounded-full disabled:opacity-50"
            aria-label="Increase guest count"
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>

        {fieldError && (
          <div className="invalid-feedback text-center">{fieldError}</div>
        )}

        {showTierHints && (
          <p className="text-sm text-center text-gray-500 mt-2">
            {getTierHint(numericValue)}
          </p>
        )}

        {helperText && (
          <p className="text-sm text-center text-gray-500">{helperText}</p>
        )}
      </div>
    );
  }

  // Default input variant
  return (
    <div className={`form-group ${className}`}>
      {showLabel && (
        <label htmlFor={field} className="form-label">
          {showIcon && <Users className="mr-1 inline-block h-4 w-4" />}
          {label}
          <span className="text-red-500 ml-1">*</span>
        </label>
      )}

      <input
        type="number"
        id={field}
        className={`form-control ${fieldError ? 'is-invalid' : ''}`}
        min={min}
        max={max}
        disabled={disabled}
        placeholder={`${min}-${max} guests`}
        {...register(field, {
          required: 'Guest count is required',
          min: { value: min, message: `Minimum ${min} guests` },
          max: { value: max, message: `Maximum ${max} guests` },
          valueAsNumber: true,
          onChange: e => onChange?.(parseInt(e.target.value) || min),
        })}
      />

      {fieldError && <div className="invalid-feedback">{fieldError}</div>}

      {showTierHints && numericValue >= min && (
        <p className="text-sm text-gray-500 mt-1">
          {getTierHint(numericValue)}
        </p>
      )}

      {helperText && <p className="text-sm text-gray-500">{helperText}</p>}
    </div>
  );
}

export default GuestCountField;
