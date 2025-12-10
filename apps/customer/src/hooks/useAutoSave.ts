/**
 * useAutoSave - Form auto-save hook
 *
 * Automatically saves form data to localStorage with debouncing.
 * Features:
 * - Debounced saves (default 1 second)
 * - Automatic restore on mount
 * - Clear saved data after successful submission
 * - Expiration support
 * - Type-safe form data
 *
 * @example
 * ```tsx
 * const { register, setValue, watch } = useForm<FormData>();
 * const { hasSavedData, clearSavedData, lastSaved } = useAutoSave({
 *   key: 'booking-form',
 *   data: watch(),
 *   onRestore: (data) => {
 *     Object.entries(data).forEach(([key, value]) => {
 *       setValue(key as keyof FormData, value);
 *     });
 *   },
 * });
 * ```
 */

import { useCallback, useEffect, useRef, useState } from 'react';

import { logger } from '@/lib/logger';

export interface AutoSaveOptions<T> {
  /** Unique key for localStorage (will be prefixed with 'mh-autosave-') */
  key: string;
  /** Current form data to save */
  data: T;
  /** Callback when saved data is restored */
  onRestore?: (data: T) => void;
  /** Debounce delay in ms (default: 1000) */
  debounceMs?: number;
  /** Expiration time in ms (default: 24 hours) */
  expirationMs?: number;
  /** Whether auto-save is enabled (default: true) */
  enabled?: boolean;
  /** Fields to exclude from saving (e.g., sensitive data) */
  excludeFields?: (keyof T)[];
}

export interface AutoSaveResult {
  /** Whether there is saved data available */
  hasSavedData: boolean;
  /** Timestamp of last save */
  lastSaved: Date | null;
  /** Clear saved data manually */
  clearSavedData: () => void;
  /** Save data manually (bypasses debounce) */
  saveNow: () => void;
  /** Restore saved data manually */
  restoreSavedData: () => void;
  /** Whether data is currently being saved */
  isSaving: boolean;
}

interface SavedFormData<T> {
  data: T;
  timestamp: number;
  version: number;
}

const STORAGE_PREFIX = 'mh-autosave-';
const CURRENT_VERSION = 1;
const DEFAULT_DEBOUNCE_MS = 1000;
const DEFAULT_EXPIRATION_MS = 24 * 60 * 60 * 1000; // 24 hours

/**
 * Default deny list for sensitive fields that should NEVER be saved to localStorage.
 * These fields are automatically excluded unless explicitly overridden.
 * This prevents accidental exposure of PII or sensitive data.
 */
const DEFAULT_SENSITIVE_FIELDS: string[] = [
  // Payment/Financial
  'cardNumber',
  'card_number',
  'creditCard',
  'credit_card',
  'cvv',
  'cvc',
  'securityCode',
  'security_code',
  'expiry',
  'expiryDate',
  'expiry_date',
  'accountNumber',
  'account_number',
  'routingNumber',
  'routing_number',
  'bankAccount',
  'bank_account',
  // Authentication
  'password',
  'currentPassword',
  'newPassword',
  'confirmPassword',
  'pin',
  'token',
  'accessToken',
  'refreshToken',
  'apiKey',
  'api_key',
  'secret',
  'privateKey',
  'private_key',
  // Personal Identifiers
  'ssn',
  'socialSecurityNumber',
  'social_security',
  'taxId',
  'tax_id',
  'driverLicense',
  'drivers_license',
  'passportNumber',
  'passport_number',
  // Healthcare
  'healthInfo',
  'medicalRecord',
  'diagnosis',
  'prescription',
];

export function useAutoSave<T extends Record<string, unknown>>({
  key,
  data,
  onRestore,
  debounceMs = DEFAULT_DEBOUNCE_MS,
  expirationMs = DEFAULT_EXPIRATION_MS,
  enabled = true,
  excludeFields = [],
}: AutoSaveOptions<T>): AutoSaveResult {
  const [hasSavedData, setHasSavedData] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const storageKey = `${STORAGE_PREFIX}${key}`;
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isInitialMount = useRef(true);
  const lastDataRef = useRef<string>('');

  /**
   * Filter out excluded fields from data.
   * Automatically excludes sensitive fields from DEFAULT_SENSITIVE_FIELDS
   * plus any additional fields specified in excludeFields.
   */
  const filterData = useCallback((inputData: T): Partial<T> => {
    const filtered = { ...inputData };

    // Always exclude default sensitive fields using precise word matching
    // Split camelCase and snake_case keys into words to avoid false positives
    const inputKeys = Object.keys(filtered);
    inputKeys.forEach((key) => {
      // Split camelCase (e.g., cardNumber -> card number) and snake_case (e.g., card_number -> card number)
      const keyParts = key
        .replace(/([a-z])([A-Z])/g, '$1 $2')
        .toLowerCase()
        .split(/[\s_]+/);

      // Check if any part of the key matches a sensitive field
      if (keyParts.some(part => DEFAULT_SENSITIVE_FIELDS.map(s => s.toLowerCase()).includes(part))) {
        delete filtered[key as keyof T];
      }
    });

    // Also exclude explicitly specified fields
    excludeFields.forEach((field) => {
      delete filtered[field];
    });

    return filtered;
  }, [excludeFields]);

  /**
   * Save data to localStorage
   */
  const saveToStorage = useCallback((dataToSave: T) => {
    if (!enabled) return;

    try {
      const filteredData = filterData(dataToSave);
      const savedData: SavedFormData<Partial<T>> = {
        data: filteredData,
        timestamp: Date.now(),
        version: CURRENT_VERSION,
      };

      localStorage.setItem(storageKey, JSON.stringify(savedData));
      setLastSaved(new Date(savedData.timestamp));
      setHasSavedData(true);
      setIsSaving(false);

      logger.debug('[AutoSave] Saved form data', { key, timestamp: savedData.timestamp });
    } catch (error) {
      logger.error('[AutoSave] Failed to save form data', error instanceof Error ? error : undefined, { key });
      setIsSaving(false);
    }
  }, [enabled, filterData, key, storageKey]);

  /**
   * Load saved data from localStorage
   */
  const loadFromStorage = useCallback((): T | null => {
    try {
      const stored = localStorage.getItem(storageKey);
      if (!stored) return null;

      const parsed: SavedFormData<T> = JSON.parse(stored);

      // Check version compatibility
      if (parsed.version !== CURRENT_VERSION) {
        logger.debug('[AutoSave] Version mismatch, clearing saved data', {
          key,
          savedVersion: parsed.version,
          currentVersion: CURRENT_VERSION
        });
        localStorage.removeItem(storageKey);
        return null;
      }

      // Check expiration
      const age = Date.now() - parsed.timestamp;
      if (age > expirationMs) {
        logger.debug('[AutoSave] Data expired, clearing', { key, age, expirationMs });
        localStorage.removeItem(storageKey);
        return null;
      }

      setLastSaved(new Date(parsed.timestamp));
      return parsed.data;
    } catch (error) {
      logger.error('[AutoSave] Failed to load saved data', error instanceof Error ? error : undefined, { key });
      return null;
    }
  }, [expirationMs, key, storageKey]);

  /**
   * Clear saved data
   */
  const clearSavedData = useCallback(() => {
    try {
      localStorage.removeItem(storageKey);
      setHasSavedData(false);
      setLastSaved(null);
      logger.debug('[AutoSave] Cleared saved data', { key });
    } catch (error) {
      logger.error('[AutoSave] Failed to clear saved data', error instanceof Error ? error : undefined, { key });
    }
  }, [key, storageKey]);

  /**
   * Restore saved data manually
   */
  const restoreSavedData = useCallback(() => {
    const savedData = loadFromStorage();
    if (savedData && onRestore) {
      onRestore(savedData);
      logger.info('[AutoSave] Restored form data', { key });
    }
  }, [key, loadFromStorage, onRestore]);

  /**
   * Save now (bypass debounce)
   */
  const saveNow = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    saveToStorage(data);
  }, [data, saveToStorage]);

  /**
   * Check for saved data on mount and restore if available
   */
  useEffect(() => {
    if (!enabled) return;

    const savedData = loadFromStorage();
    if (savedData) {
      setHasSavedData(true);
      // Optionally auto-restore
      if (onRestore) {
        onRestore(savedData);
        logger.info('[AutoSave] Auto-restored form data on mount', { key });
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, key]); // Only run on mount and key change

  /**
   * Debounced save when data changes
   */
  useEffect(() => {
    if (!enabled) return;

    // Skip initial mount
    if (isInitialMount.current) {
      isInitialMount.current = false;
      lastDataRef.current = JSON.stringify(data);
      return;
    }

    // Check if data actually changed
    const dataString = JSON.stringify(data);
    if (dataString === lastDataRef.current) return;
    lastDataRef.current = dataString;

    // Clear existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    setIsSaving(true);

    // Set new debounced save
    timeoutRef.current = setTimeout(() => {
      saveToStorage(data);
    }, debounceMs);

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [data, debounceMs, enabled, saveToStorage]);

  /**
   * Save on page unload
   */
  useEffect(() => {
    if (!enabled) return;

    const handleBeforeUnload = () => {
      // Synchronous save on unload
      try {
        const filteredData = filterData(data);
        const savedData: SavedFormData<Partial<T>> = {
          data: filteredData,
          timestamp: Date.now(),
          version: CURRENT_VERSION,
        };
        localStorage.setItem(storageKey, JSON.stringify(savedData));
      } catch {
        // Ignore errors on unload
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [data, enabled, filterData, storageKey]);

  return {
    hasSavedData,
    lastSaved,
    clearSavedData,
    saveNow,
    restoreSavedData,
    isSaving,
  };
}

/**
 * Hook for managing auto-save state UI
 * Shows a small indicator when data is being saved/saved
 */
export function useAutoSaveIndicator(isSaving: boolean, lastSaved: Date | null) {
  const [status, setStatus] = useState<'idle' | 'saving' | 'saved'>('idle');

  useEffect(() => {
    if (isSaving) {
      setStatus('saving');
    } else if (lastSaved) {
      setStatus('saved');
      // Reset to idle after 2 seconds
      const timeout = setTimeout(() => setStatus('idle'), 2000);
      return () => clearTimeout(timeout);
    }
  }, [isSaving, lastSaved]);

  return status;
}
