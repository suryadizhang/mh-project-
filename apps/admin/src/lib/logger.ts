/**
 * Production-ready logging utility for Admin Dashboard
 * 
 * Features:
 * - Environment-aware logging (silent in production)
 * - Multiple log levels (debug, info, warn, error)
 * - Context enrichment for better debugging
 * - Sentry integration for production error tracking
 * - WebSocket-specific logging utilities
 * - Structured logging for better analysis
 * 
 * Usage:
 * ```typescript
 * import { logger } from '@/lib/logger';
 * 
 * // Basic logging
 * logger.debug('User clicked button');
 * logger.info('Payment processed', { amount: 1000, customer_id: 123 });
 * logger.warn('Deprecated API used', { endpoint: '/old-api' });
 * logger.error(new Error('Failed to fetch data'), { endpoint: '/api/bookings' });
 * 
 * // WebSocket logging
 * logger.websocket('connect', { url: 'ws://localhost:8000/ws' });
 * logger.websocket('message', { type: 'booking_update', booking_id: 456 });
 * logger.websocket('error', { error: 'Connection timeout' });
 * logger.websocket('disconnect', { code: 1000, reason: 'Normal closure' });
 * ```
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

type Environment = 'development' | 'production' | 'test';

interface LogContext {
  [key: string]: any;
}

interface LoggerConfig {
  environment: Environment;
  enableConsole: boolean;
  enableSentry: boolean;
  minLevel: LogLevel;
}

interface WebSocketEvent {
  type: 'connect' | 'disconnect' | 'message' | 'error' | 'reconnect';
  data?: any;
}

class Logger {
  private config: LoggerConfig;
  private logLevels: Record<LogLevel, number> = {
    debug: 0,
    info: 1,
    warn: 2,
    error: 3,
  };

  constructor(config: Partial<LoggerConfig> = {}) {
    const environment = (process.env.NODE_ENV || 'development') as Environment;
    
    this.config = {
      environment,
      enableConsole: environment !== 'production',
      enableSentry: environment === 'production',
      minLevel: environment === 'production' ? 'warn' : 'debug',
      ...config,
    };
  }

  /**
   * Check if a log level should be logged based on configuration
   */
  private shouldLog(level: LogLevel): boolean {
    return this.logLevels[level] >= this.logLevels[this.config.minLevel];
  }

  /**
   * Format log message with timestamp and context
   */
  private formatMessage(level: LogLevel, message: string, context?: LogContext): string {
    const timestamp = new Date().toISOString();
    const contextStr = context ? ` ${JSON.stringify(context)}` : '';
    return `[${timestamp}] [${level.toUpperCase()}] ${message}${contextStr}`;
  }

  /**
   * Send error to Sentry (if configured)
   */
  private sendToSentry(error: Error | string, context?: LogContext): void {
    if (!this.config.enableSentry) return;

    // Dynamically import Sentry only if configured
    // In production, this should be initialized in _app.tsx
    if (typeof window !== 'undefined' && (window as any).Sentry) {
      const Sentry = (window as any).Sentry;
      
      if (error instanceof Error) {
        Sentry.captureException(error, {
          extra: context,
        });
      } else {
        Sentry.captureMessage(error, {
          level: 'error',
          extra: context,
        });
      }
    }
  }

  /**
   * Debug level logging - detailed information for debugging
   * Only logged in development
   */
  debug(message: string, context?: LogContext): void {
    if (!this.shouldLog('debug')) return;

    if (this.config.enableConsole) {
      console.debug(this.formatMessage('debug', message, context));
    }
  }

  /**
   * Info level logging - general informational messages
   * Logged in development, silent in production
   */
  info(message: string, context?: LogContext): void {
    if (!this.shouldLog('info')) return;

    if (this.config.enableConsole) {
      console.info(this.formatMessage('info', message, context));
    }
  }

  /**
   * Warning level logging - potentially harmful situations
   * Logged in all environments, sent to Sentry in production
   */
  warn(message: string, context?: LogContext): void {
    if (!this.shouldLog('warn')) return;

    if (this.config.enableConsole) {
      console.warn(this.formatMessage('warn', message, context));
    }

    if (this.config.enableSentry) {
      this.sendToSentry(message, { ...context, level: 'warning' });
    }
  }

  /**
   * Error level logging - error events
   * Always logged and sent to Sentry in production
   */
  error(error: Error | string, context?: LogContext): void {
    if (!this.shouldLog('error')) return;

    const message = error instanceof Error ? error.message : error;

    if (this.config.enableConsole) {
      if (error instanceof Error) {
        console.error(this.formatMessage('error', message, context), error);
      } else {
        console.error(this.formatMessage('error', message, context));
      }
    }

    if (this.config.enableSentry) {
      this.sendToSentry(error, context);
    }
  }

  /**
   * WebSocket-specific logging utility
   * Provides structured logging for WebSocket events
   */
  websocket(event: WebSocketEvent['type'], data?: any): void {
    const context = { websocket: true, event, ...data };

    switch (event) {
      case 'connect':
        this.info('WebSocket connected', context);
        break;
      case 'disconnect':
        this.info('WebSocket disconnected', context);
        break;
      case 'message':
        this.debug('WebSocket message received', context);
        break;
      case 'reconnect':
        this.info('WebSocket reconnecting', context);
        break;
      case 'error':
        // Handle error data properly - could be string, Error, or object
        const errorMessage = typeof data?.error === 'string' 
          ? data.error 
          : data?.error?.message || 'WebSocket error';
        this.error(errorMessage, context);
        break;
      default:
        this.debug(`WebSocket event: ${event}`, context);
    }
  }

  /**
   * API request logging utility
   * Logs API calls with timing information
   */
  api(method: string, endpoint: string, context?: LogContext): void {
    this.debug(`API ${method.toUpperCase()} ${endpoint}`, context);
  }

  /**
   * API error logging utility
   * Logs API errors with status code and response
   */
  apiError(method: string, endpoint: string, error: any, context?: LogContext): void {
    const errorContext = {
      method,
      endpoint,
      status: error?.response?.status,
      statusText: error?.response?.statusText,
      ...context,
    };

    if (error?.response?.status === 401 || error?.response?.status === 403) {
      // Authentication/authorization errors - don't send to Sentry
      this.warn(`API ${method} ${endpoint} - Auth error`, errorContext);
    } else {
      // Other errors - send to Sentry in production
      this.error(error instanceof Error ? error : new Error(`API error: ${error}`), errorContext);
    }
  }

  /**
   * User action logging utility
   * Logs user interactions for analytics
   */
  userAction(action: string, context?: LogContext): void {
    this.info(`User action: ${action}`, { ...context, user_action: true });
  }

  /**
   * Performance logging utility
   * Logs timing information for performance monitoring
   */
  performance(label: string, durationMs: number, context?: LogContext): void {
    if (durationMs > 1000) {
      this.warn(`Slow operation: ${label} took ${durationMs}ms`, context);
    } else {
      this.debug(`Performance: ${label} took ${durationMs}ms`, context);
    }
  }

  /**
   * Create a child logger with additional context
   * Useful for component-specific logging
   */
  withContext(additionalContext: LogContext): Logger {
    const childLogger = new Logger(this.config);
    const originalMethods = {
      debug: this.debug.bind(this),
      info: this.info.bind(this),
      warn: this.warn.bind(this),
      error: this.error.bind(this),
    };

    // Override methods to include additional context
    childLogger.debug = (message: string, context?: LogContext) => {
      originalMethods.debug(message, { ...additionalContext, ...context });
    };

    childLogger.info = (message: string, context?: LogContext) => {
      originalMethods.info(message, { ...additionalContext, ...context });
    };

    childLogger.warn = (message: string, context?: LogContext) => {
      originalMethods.warn(message, { ...additionalContext, ...context });
    };

    childLogger.error = (error: Error | string, context?: LogContext) => {
      originalMethods.error(error, { ...additionalContext, ...context });
    };

    return childLogger;
  }
}

// Export singleton instance
export const logger = new Logger();

// Export types for TypeScript
export type { LogLevel, LogContext, WebSocketEvent };

// Export class for testing or custom configurations
export { Logger };
