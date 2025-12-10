'use client';

/**
 * Toast Notification System
 *
 * Provides global toast notifications for success, error, warning, and info messages.
 * Built on sonner for smooth animations and accessibility.
 *
 * Usage:
 *   import { toast } from "@/components/ui/toaster";
 *
 *   // Basic usage
 *   toast.success("Booking confirmed!");
 *   toast.error("Payment failed");
 *   toast.warning("Low inventory");
 *   toast.info("Processing your request...");
 *
 *   // With options
 *   toast.success("Saved!", { duration: 3000 });
 *   toast.error("Failed to save", { description: "Please try again" });
 *
 *   // Promise handling (loading -> success/error)
 *   toast.promise(saveBooking(), {
 *     loading: "Saving...",
 *     success: "Booking saved!",
 *     error: "Failed to save booking"
 *   });
 *
 * @see https://sonner.emilkowal.ski/
 */

import { Toaster as SonnerToaster, toast as sonnerToast } from 'sonner';

/**
 * Toaster Provider Component
 *
 * Add this once in your root layout to enable toast notifications.
 *
 * @example
 * // In app/layout.tsx:
 * import { Toaster } from "@/components/ui/toaster";
 *
 * export default function RootLayout({ children }) {
 *   return (
 *     <html>
 *       <body>
 *         {children}
 *         <Toaster />
 *       </body>
 *     </html>
 *   );
 * }
 */
export function Toaster() {
  return (
    <SonnerToaster
      position="top-right"
      toastOptions={{
        // Default styling for all toasts
        classNames: {
          toast:
            'group toast bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700 shadow-lg rounded-lg',
          title: 'text-sm font-semibold',
          description: 'text-sm text-gray-500 dark:text-gray-400',
          actionButton:
            'bg-primary text-white hover:bg-primary/90 rounded px-3 py-1.5 text-xs font-medium',
          cancelButton:
            'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 rounded px-3 py-1.5 text-xs font-medium',
          closeButton:
            'bg-gray-100 dark:bg-gray-800 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300',
          success: 'border-l-4 border-l-green-500',
          error: 'border-l-4 border-l-red-500',
          warning: 'border-l-4 border-l-yellow-500',
          info: 'border-l-4 border-l-blue-500',
        },
        // Default duration (5 seconds)
        duration: 5000,
      }}
      // Show close button on toasts
      closeButton
      // Expand toasts on hover for better readability
      expand
      // Rich colors for better visual feedback
      richColors
      // Limit visible toasts
      visibleToasts={4}
    />
  );
}

/**
 * Toast API
 *
 * Re-export sonner's toast function with our custom configuration.
 * Use this for all toast notifications throughout the app.
 */
export const toast = sonnerToast;

/**
 * Type-safe toast helpers for common scenarios
 */
export const showToast = {
  /**
   * Show success toast
   * @example showToast.success("Booking confirmed!")
   */
  success: (message: string, options?: Parameters<typeof sonnerToast.success>[1]) => {
    return sonnerToast.success(message, options);
  },

  /**
   * Show error toast
   * @example showToast.error("Payment failed", { description: "Card declined" })
   */
  error: (message: string, options?: Parameters<typeof sonnerToast.error>[1]) => {
    return sonnerToast.error(message, options);
  },

  /**
   * Show warning toast
   * @example showToast.warning("Limited availability")
   */
  warning: (message: string, options?: Parameters<typeof sonnerToast.warning>[1]) => {
    return sonnerToast.warning(message, options);
  },

  /**
   * Show info toast
   * @example showToast.info("Processing your request...")
   */
  info: (message: string, options?: Parameters<typeof sonnerToast.info>[1]) => {
    return sonnerToast.info(message, options);
  },

  /**
   * Show loading toast that resolves to success or error
   * @example
   * showToast.promise(saveBooking(), {
   *   loading: "Saving...",
   *   success: "Saved!",
   *   error: "Failed to save"
   * });
   */
  promise: <T,>(
    promise: Promise<T>,
    options: {
      loading: string;
      success: string | ((data: T) => string);
      error: string | ((error: Error) => string);
    },
  ) => {
    return sonnerToast.promise(promise, options);
  },

  /**
   * Dismiss a specific toast or all toasts
   * @example showToast.dismiss() // dismiss all
   * @example showToast.dismiss(toastId) // dismiss specific
   */
  dismiss: (toastId?: string | number) => {
    return sonnerToast.dismiss(toastId);
  },
};

export default Toaster;
