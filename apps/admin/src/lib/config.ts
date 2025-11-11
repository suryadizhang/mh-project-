/**
 * Admin Environment Configuration with Runtime Validation
 *
 * This module validates all environment variables at build time using Zod.
 * Invalid or missing variables will cause the build to fail with clear error messages.
 *
 * Usage:
 *   import { config } from '@/lib/config';
 *   const apiUrl = config.apiUrl; // Type-safe and validated
 *
 * @module config
 */

import { z } from 'zod';

/**
 * Environment variable schema with validation rules for admin app
 */
const envSchema = z.object({
  // API Configuration
  NEXT_PUBLIC_API_URL: z
    .string()
    .url('NEXT_PUBLIC_API_URL must be a valid URL')
    .refine((url) => url.startsWith('http://') || url.startsWith('https://'), {
      message: 'NEXT_PUBLIC_API_URL must start with http:// or https://',
    }),

  // Admin-specific: Auth0 or similar auth provider
  NEXT_PUBLIC_AUTH_DOMAIN: z
    .string()
    .min(1, 'NEXT_PUBLIC_AUTH_DOMAIN is required')
    .optional(),

  NEXT_PUBLIC_AUTH_CLIENT_ID: z
    .string()
    .min(1, 'NEXT_PUBLIC_AUTH_CLIENT_ID is required')
    .optional(),

  // WebSocket URL (optional)
  NEXT_PUBLIC_WS_URL: z
    .string()
    .url('NEXT_PUBLIC_WS_URL must be a valid URL')
    .refine((url) => url.startsWith('ws://') || url.startsWith('wss://'), {
      message: 'NEXT_PUBLIC_WS_URL must start with ws:// or wss://',
    })
    .optional(),

  // Google Analytics (optional for admin)
  NEXT_PUBLIC_GA_ID: z
    .string()
    .regex(/^G-[A-Z0-9]+$/, 'NEXT_PUBLIC_GA_ID must match format G-XXXXXXXXXX')
    .optional(),

  // Environment Type
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
});

/**
 * Validated environment variables
 *
 * This will throw a ZodError at build time if validation fails.
 * The error message will clearly indicate which variable is invalid and why.
 */
let env: z.infer<typeof envSchema>;

try {
  env = envSchema.parse({
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_AUTH_DOMAIN: process.env.NEXT_PUBLIC_AUTH_DOMAIN,
    NEXT_PUBLIC_AUTH_CLIENT_ID: process.env.NEXT_PUBLIC_AUTH_CLIENT_ID,
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL,
    NEXT_PUBLIC_GA_ID: process.env.NEXT_PUBLIC_GA_ID,
    NODE_ENV: process.env.NODE_ENV,
  });
} catch (error) {
  if (error instanceof z.ZodError) {
    console.error('\n❌ Admin Environment Variable Validation Failed:\n');
    error.issues.forEach((err: z.ZodIssue) => {
      console.error(`  • ${err.path.join('.')}: ${err.message}`);
    });
    console.error('\nPlease check your .env.local file and ensure all required variables are set correctly.\n');
    throw new Error('Invalid environment configuration');
  }
  throw error;
}

/**
 * Type-safe, validated configuration object for admin app
 *
 * Use this instead of accessing process.env directly to ensure:
 * - Type safety (TypeScript knows the types)
 * - Runtime validation (invalid values caught at build time)
 * - Clear error messages (know exactly what's wrong)
 * - Consistent access pattern across the app
 */
export const config = {
  // API
  apiUrl: env.NEXT_PUBLIC_API_URL,

  // Authentication
  authDomain: env.NEXT_PUBLIC_AUTH_DOMAIN,
  authClientId: env.NEXT_PUBLIC_AUTH_CLIENT_ID,

  // WebSocket
  wsUrl: env.NEXT_PUBLIC_WS_URL,

  // Analytics
  gaId: env.NEXT_PUBLIC_GA_ID,

  // Environment
  isDevelopment: env.NODE_ENV === 'development',
  isProduction: env.NODE_ENV === 'production',
  isTest: env.NODE_ENV === 'test',
  nodeEnv: env.NODE_ENV,
} as const;

/**
 * Type helper to extract config type
 */
export type Config = typeof config;
