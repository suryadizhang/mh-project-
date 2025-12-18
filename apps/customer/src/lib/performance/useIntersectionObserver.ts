/**
 * Intersection Observer Hook for Smart Lazy Loading
 *
 * This hook provides viewport-aware lazy loading capabilities:
 * - Only loads components when they're about to enter the viewport
 * - Configurable rootMargin for preloading before visibility
 * - Threshold options for fine-grained control
 * - SSR-safe with proper hydration handling
 */

import { useEffect, useState, useRef, useCallback, type RefObject } from 'react';

export interface UseIntersectionObserverOptions {
  /**
   * Margin around the root element to trigger loading early.
   * Use positive values to preload before the element is visible.
   * @default '100px' - Preload 100px before entering viewport
   */
  rootMargin?: string;

  /**
   * Percentage of element visibility needed to trigger.
   * 0 = any pixel visible, 1 = fully visible
   * @default 0
   */
  threshold?: number | number[];

  /**
   * Root element for intersection checking.
   * null = viewport
   * @default null
   */
  root?: Element | null;

  /**
   * Only trigger once, then disconnect.
   * Use for lazy loading that doesn't need to re-trigger.
   * @default true
   */
  triggerOnce?: boolean;

  /**
   * Disable the observer entirely.
   * Useful for SSR or when you want immediate loading.
   * @default false
   */
  disabled?: boolean;

  /**
   * Callback when intersection changes.
   */
  onChange?: (isIntersecting: boolean, entry?: IntersectionObserverEntry) => void;
}

export interface UseIntersectionObserverReturn {
  /** Ref to attach to the target element */
  ref: RefObject<HTMLDivElement>;
  /** Whether the element is currently intersecting (visible) */
  isIntersecting: boolean;
  /** Whether the element has ever been visible (for triggerOnce) */
  hasBeenVisible: boolean;
  /** The raw IntersectionObserverEntry if available */
  entry: IntersectionObserverEntry | null;
}

/**
 * Hook to detect when an element enters the viewport
 *
 * @example
 * ```tsx
 * function LazyComponent() {
 *   const { ref, hasBeenVisible } = useIntersectionObserver({
 *     rootMargin: '200px', // Preload 200px before visible
 *     triggerOnce: true,
 *   });
 *
 *   return (
 *     <div ref={ref}>
 *       {hasBeenVisible ? <HeavyComponent /> : <Skeleton />}
 *     </div>
 *   );
 * }
 * ```
 */
export function useIntersectionObserver(
  options: UseIntersectionObserverOptions = {},
): UseIntersectionObserverReturn {
  const {
    rootMargin = '100px',
    threshold = 0,
    root = null,
    triggerOnce = true,
    disabled = false,
    onChange,
  } = options;

  const ref = useRef<HTMLDivElement>(null);
  const [isIntersecting, setIsIntersecting] = useState(false);
  const [hasBeenVisible, setHasBeenVisible] = useState(false);
  const [entry, setEntry] = useState<IntersectionObserverEntry | null>(null);

  useEffect(() => {
    // Skip if disabled or SSR
    if (disabled || typeof window === 'undefined' || !('IntersectionObserver' in window)) {
      // In SSR or when disabled, consider it visible immediately
      if (disabled) {
        setIsIntersecting(true);
        setHasBeenVisible(true);
      }
      return;
    }

    const element = ref.current;
    if (!element) return;

    // Don't observe if we've already triggered and triggerOnce is true
    if (triggerOnce && hasBeenVisible) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const [observerEntry] = entries;
        const isVisible = observerEntry.isIntersecting;

        setIsIntersecting(isVisible);
        setEntry(observerEntry);

        if (isVisible) {
          setHasBeenVisible(true);

          // Disconnect if we only need to trigger once
          if (triggerOnce) {
            observer.disconnect();
          }
        }

        // Call the onChange callback if provided
        onChange?.(isVisible, observerEntry);
      },
      {
        root,
        rootMargin,
        threshold,
      },
    );

    observer.observe(element);

    return () => {
      observer.disconnect();
    };
  }, [root, rootMargin, threshold, triggerOnce, disabled, hasBeenVisible, onChange]);

  return {
    ref,
    isIntersecting,
    hasBeenVisible,
    entry,
  };
}

/**
 * Presets for common use cases
 */
export const INTERSECTION_PRESETS = {
  /** Load immediately when any pixel is visible */
  immediate: {
    rootMargin: '0px',
    threshold: 0,
    triggerOnce: true,
  },
  /** Preload 100px before entering viewport */
  preload: {
    rootMargin: '100px',
    threshold: 0,
    triggerOnce: true,
  },
  /** Preload 200px before - good for images and heavy components */
  aggressivePreload: {
    rootMargin: '200px',
    threshold: 0,
    triggerOnce: true,
  },
  /** Wait until 50% visible */
  halfVisible: {
    rootMargin: '0px',
    threshold: 0.5,
    triggerOnce: true,
  },
  /** Wait until fully visible */
  fullyVisible: {
    rootMargin: '0px',
    threshold: 1,
    triggerOnce: true,
  },
  /** Track visibility continuously (for analytics, animations) */
  continuous: {
    rootMargin: '0px',
    threshold: [0, 0.25, 0.5, 0.75, 1],
    triggerOnce: false,
  },
} as const;

// Note: Higher-order component withViewportLoading is available in ViewportLazy.tsx
// which uses proper JSX syntax in a .tsx file.
