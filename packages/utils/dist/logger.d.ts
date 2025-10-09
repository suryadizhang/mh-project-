declare class Logger {
    private isDevelopment;
    private formatMessage;
    debug(message: string, data?: any): void;
    info(message: string, data?: any): void;
    warn(message: string, data?: any): void;
    error(message: string, error?: any): void;
}
export declare const logger: Logger;
export {};
//# sourceMappingURL=logger.d.ts.map