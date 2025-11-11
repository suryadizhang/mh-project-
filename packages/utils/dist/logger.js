class Logger {
    isDevelopment = process.env.NODE_ENV === 'development';
    formatMessage(level, message, data) {
        const timestamp = new Date().toISOString();
        const prefix = `[${timestamp}] [${level.toUpperCase()}]`;
        return data ? `${prefix} ${message} ${JSON.stringify(data)}` : `${prefix} ${message}`;
    }
    debug(message, data) {
        if (this.isDevelopment) {
            console.debug(this.formatMessage('debug', message, data));
        }
    }
    info(message, data) {
        console.info(this.formatMessage('info', message, data));
    }
    warn(message, data) {
        console.warn(this.formatMessage('warn', message, data));
    }
    error(message, error) {
        console.error(this.formatMessage('error', message, error));
        // In production, you might want to send to error tracking service
        if (!this.isDevelopment && error) {
            // Example: Sentry.captureException(error);
        }
    }
}
export const logger = new Logger();
//# sourceMappingURL=logger.js.map