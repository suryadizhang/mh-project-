type LogLevel = 'debug' | 'info' | 'warn' | 'error';

class Logger {
  private isDevelopment = process.env.NODE_ENV === 'development';

  private formatMessage(level: LogLevel, message: string, data?: any): string {
    const timestamp = new Date().toISOString();
    const prefix = `[${timestamp}] [${level.toUpperCase()}]`;
    return data
      ? `${prefix} ${message} ${JSON.stringify(data)}`
      : `${prefix} ${message}`;
  }

  debug(message: string, data?: any): void {
    if (this.isDevelopment) {
      console.debug(this.formatMessage('debug', message, data));
    }
  }

  info(message: string, data?: any): void {
    console.info(this.formatMessage('info', message, data));
  }

  warn(message: string, data?: any): void {
    console.warn(this.formatMessage('warn', message, data));
  }

  error(message: string, error?: any): void {
    console.error(this.formatMessage('error', message, error));

    // In production, you might want to send to error tracking service
    if (!this.isDevelopment && error) {
      // Example: Sentry.captureException(error);
    }
  }
}

export const logger = new Logger();
