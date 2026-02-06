/**
 * Debounce Utility
 *
 * Delays function execution until after a specified wait time has elapsed
 * since the last time it was invoked. Useful for optimizing performance
 * of frequently called functions like search inputs, window resize, etc.
 *
 * Features:
 * - Type-safe generic implementation
 * - Automatic cleanup of pending timeouts
 * - Returns debounced function with same signature
 *
 * Example Usage:
 * ```typescript
 * const debouncedSearch = debounce((query: string) => {
 *   console.log('Searching for:', query);
 * }, 300);
 *
 * debouncedSearch('hello'); // Will only execute after 300ms of inactivity
 * ```
 *
 * @param func - The function to debounce
 * @param wait - The delay in milliseconds (default: 300ms)
 * @returns Debounced version of the function
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number = 300,
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;

  return function debounced(...args: Parameters<T>): void {
    // Clear any pending timeout
    if (timeout) {
      clearTimeout(timeout);
    }

    // Set new timeout
    timeout = setTimeout(() => {
      func(...args);
      timeout = null;
    }, wait);
  };
}

/**
 * Throttle Utility
 *
 * Ensures a function is called at most once in a specified time period.
 * Unlike debounce, throttle ensures the function is executed at regular
 * intervals during rapid invocations.
 *
 * Features:
 * - Type-safe generic implementation
 * - Guarantees execution at regular intervals
 * - Trailing call option (execute after wait period)
 *
 * Example Usage:
 * ```typescript
 * const throttledScroll = throttle(() => {
 *   console.log('Scroll position:', window.scrollY);
 * }, 100);
 *
 * window.addEventListener('scroll', throttledScroll);
 * ```
 *
 * @param func - The function to throttle
 * @param wait - The minimum time between executions in milliseconds
 * @returns Throttled version of the function
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  wait: number = 100,
): (...args: Parameters<T>) => void {
  let inThrottle: boolean = false;
  let lastArgs: Parameters<T> | null = null;

  return function throttled(...args: Parameters<T>): void {
    lastArgs = args;

    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      lastArgs = null;

      setTimeout(() => {
        inThrottle = false;

        // Execute trailing call if there was one
        if (lastArgs) {
          func(...lastArgs);
          lastArgs = null;
        }
      }, wait);
    }
  };
}

/**
 * Create an AbortController that automatically aborts after a timeout
 *
 * Useful for fetch requests that need to be cancelled if they take too long.
 *
 * Example Usage:
 * ```typescript
 * const controller = createAbortController(5000); // 5 second timeout
 *
 * try {
 *   const response = await fetch('/api/search', {
 *     signal: controller.signal
 *   });
 * } catch (error) {
 *   if (error.name === 'AbortError') {
 *     console.log('Request timed out');
 *   }
 * }
 * ```
 *
 * @param timeoutMs - Timeout in milliseconds
 * @returns AbortController instance
 */
export function createAbortController(timeoutMs?: number): AbortController {
  const controller = new AbortController();

  if (timeoutMs) {
    setTimeout(() => controller.abort(), timeoutMs);
  }

  return controller;
}

/**
 * Debounced value hook for React
 *
 * Returns a debounced version of the input value that only updates
 * after the specified delay has elapsed since the last value change.
 *
 * Example Usage:
 * ```typescript
 * const [searchQuery, setSearchQuery] = useState('');
 * const debouncedQuery = useDebounce(searchQuery, 300);
 *
 * useEffect(() => {
 *   // This only runs 300ms after user stops typing
 *   fetchSearchResults(debouncedQuery);
 * }, [debouncedQuery]);
 * ```
 *
 * Note: This is a conceptual implementation. For actual React hook,
 * import from a separate file with React dependencies.
 */
export interface DebouncedValue<T> {
  value: T;
  isDebouncing: boolean;
}
