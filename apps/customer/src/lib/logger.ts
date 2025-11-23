/**
 * Production-safe logging utility
 *
 * Features:
 * - Automatically strips debug logs in production
 * - Structured logging with context
 * - Error tracking integration ready
 * - Performance timing utilities
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogContext {
  [key: string]: any;
}

class Logger {
  private isDevelopment: boolean;
  private enabledLevels: Set<LogLevel>;

  constructor() {
    this.isDevelopment = process.env.NODE_ENV === 'development';

    // In production, only log warnings and errors
    this.enabledLevels = this.isDevelopment
      ? new Set(['debug', 'info', 'warn', 'error'])
      : new Set(['warn', 'error']);
  }

  /**
   * Debug logging - stripped in production
   */
  debug(message: string, context?: LogContext): void {
    if (!this.enabledLevels.has('debug')) return;

    if (context) {
      console.log(`[DEBUG] ${message}`, context);
    } else {
      console.log(`[DEBUG] ${message}`);
    }
  }

  /**
   * Info logging - stripped in production
   */
  info(message: string, context?: LogContext): void {
    if (!this.enabledLevels.has('info')) return;

    if (context) {
      console.info(`[INFO] ${message}`, context);
    } else {
      console.info(`[INFO] ${message}`);
    }
  }

  /**
   * Warning logging - kept in production
   */
  warn(message: string, context?: LogContext): void {
    if (!this.enabledLevels.has('warn')) return;

    if (context) {
      console.warn(`[WARN] ${message}`, context);
    } else {
      console.warn(`[WARN] ${message}`);
    }
  }

  /**
   * Error logging - kept in production, sends to error tracking
   */
  error(message: string, error?: Error, context?: LogContext): void {
    if (!this.enabledLevels.has('error')) return;

    const errorData = {
      message,
      ...(error && {
        name: error.name,
        message: error.message,
        stack: this.isDevelopment ? error.stack : undefined,
      }),
      ...context,
    };

    console.error(`[ERROR] ${message}`, errorData);

    // TODO: Send to error tracking service (Sentry, DataDog, etc.)
    // if (!this.isDevelopment && typeof window !== 'undefined') {
    //   window.Sentry?.captureException(error, { extra: context });
    // }
  }

  /**
   * Performance timing utility
   */
  time(label: string): void {
    if (!this.isDevelopment) return;
    console.time(label);
  }

  timeEnd(label: string): void {
    if (!this.isDevelopment) return;
    console.timeEnd(label);
  }

  /**
   * Group logs - development only
   */
  group(label: string): void {
    if (!this.isDevelopment) return;
    console.group(label);
  }

  groupEnd(): void {
    if (!this.isDevelopment) return;
    console.groupEnd();
  }

  /**
   * Table logging - development only
   */
  table(data: any): void {
    if (!this.isDevelopment) return;
    console.table(data);
  }
}

// Export singleton instance
export const logger = new Logger();

/**
 * Web Vitals logging - sends to analytics instead of console
 */
export function logWebVital(metric: {
  name: string;
  value: number;
  id: string;
  delta: number;
}): void {
  // In production, send to analytics service
  if (process.env.NODE_ENV === 'production') {
    // TODO: Send to Google Analytics, DataDog, etc.
    // gtag('event', metric.name, {
    //   value: Math.round(metric.value),
    //   metric_id: metric.id,
    //   metric_delta: metric.delta,
    // });
    return;
  }

  // In development, log to console
  logger.debug(`Web Vital: ${metric.name}`, {
    value: Math.round(metric.value),
    id: metric.id,
    delta: Math.round(metric.delta),
  });
}

/**
 * API request logging utility
 */
export function logApiRequest(
  method: string,
  url: string,
  status?: number,
  duration?: number,
  error?: Error
): void {
  const context = {
    method,
    url,
    status,
    duration: duration ? `${Math.round(duration)}ms` : undefined,
  };

  if (error) {
    logger.error(`API ${method} ${url} failed`, error, context);
  } else if (status && status >= 400) {
    logger.warn(`API ${method} ${url} returned ${status}`, context);
  } else {
    logger.debug(`API ${method} ${url} completed`, context);
  }
}

/**
 * WebSocket connection logging
 */
export function logWebSocket(event: string, data?: LogContext): void {
  if (event === 'error') {
    logger.error('WebSocket error', undefined, data);
  } else if (event === 'close' && data?.code && data.code !== 1000) {
    logger.warn('WebSocket closed unexpectedly', data);
  } else {
    logger.debug(`WebSocket ${event}`, data);
  }
}

export default logger;
