import winston from 'winston';
import { config } from './config.js';

// Custom format for clean console output
const consoleFormat = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
  winston.format.colorize(),
  winston.format.printf(({ timestamp, level, message, ...meta }) => {
    let msg = `${timestamp} [${level}] ${message}`;

    // Add metadata if present
    if (Object.keys(meta).length > 0) {
      msg += `\n${JSON.stringify(meta, null, 2)}`;
    }

    return msg;
  })
);

// JSON format for file logging (future enhancement)
const jsonFormat = winston.format.combine(
  winston.format.timestamp(),
  winston.format.json()
);

// Create logger instance
export const logger = winston.createLogger({
  level: config.logging.level,
  transports: [
    new winston.transports.Console({
      format: consoleFormat,
    }),
  ],
});

// Helper function to log with structured context
export function logWithContext(level: string, message: string, context?: Record<string, any>) {
  logger.log(level, message, context);
}

// Specific helpers
export const logInfo = (message: string, context?: Record<string, any>) =>
  logWithContext('info', message, context);

export const logError = (message: string, error?: Error | unknown, context?: Record<string, any>) => {
  const errorContext = {
    ...context,
    error: error instanceof Error ? {
      message: error.message,
      stack: error.stack,
      name: error.name,
    } : error,
  };
  logWithContext('error', message, errorContext);
};

export const logDebug = (message: string, context?: Record<string, any>) =>
  logWithContext('debug', message, context);

export const logWarn = (message: string, context?: Record<string, any>) =>
  logWithContext('warn', message, context);
