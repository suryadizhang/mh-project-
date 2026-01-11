import { z } from 'zod';

// Customer app environment schema
const CustomerEnvSchema = z.object({
  // App configuration
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  NEXT_PUBLIC_APP_URL: z.string().url(),
  NEXT_PUBLIC_APP_NAME: z.string().default('MyHibachi'),

  // API configuration
  NEXT_PUBLIC_API_URL: z.string().url(),
  NEXT_PUBLIC_AI_API_URL: z.string().url().optional(),

  // Payment providers (optional until Batch 2 - Stripe integration)
  NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: z.string().optional(),
  STRIPE_SECRET_KEY: z.string().optional(),
  STRIPE_WEBHOOK_SECRET: z.string().optional(),

  // Zelle configuration
  NEXT_PUBLIC_ZELLE_ENABLED: z
    .string()
    .default('false')
    .transform((val) => val === 'true'),
  NEXT_PUBLIC_ZELLE_EMAIL: z.string().email().optional(),
  NEXT_PUBLIC_ZELLE_PHONE: z.string().optional(),

  // Venmo configuration
  NEXT_PUBLIC_VENMO_ENABLED: z
    .string()
    .default('false')
    .transform((val) => val === 'true'),
  NEXT_PUBLIC_VENMO_USERNAME: z.string().optional(),

  // Analytics & Monitoring
  NEXT_PUBLIC_GA_MEASUREMENT_ID: z.string().optional(),
  NEXT_PUBLIC_HOTJAR_ID: z.string().optional(),
  VERCEL_URL: z.string().optional(),

  // Feature Flags - Customer Site
  // Following naming convention: NEXT_PUBLIC_FEATURE_<SCOPE>_<DESCRIPTION>_<VERSION>
  // Default to 'false' in production for safety

  // Core Features
  NEXT_PUBLIC_MAINTENANCE_MODE: z
    .string()
    .default('false')
    .transform((val) => val === 'true'),
  NEXT_PUBLIC_BOOKING_ENABLED: z
    .string()
    .default('true')
    .transform((val) => val === 'true'),
  NEXT_PUBLIC_AI_CHAT_ENABLED: z
    .string()
    .default('false')
    .transform((val) => val === 'true'),

  // New Features (Behind Flags)
  NEXT_PUBLIC_FEATURE_NEW_BOOKING_CALENDAR: z
    .string()
    .default('false')
    .transform((val) => val === 'true'),
  NEXT_PUBLIC_FEATURE_V2_PRICING_ENGINE: z
    .string()
    .default('false')
    .transform((val) => val === 'true'),
  NEXT_PUBLIC_FEATURE_CUSTOMER_PORTAL_BETA: z
    .string()
    .default('false')
    .transform((val) => val === 'true'),
  NEXT_PUBLIC_FEATURE_NEW_MENU_SELECTOR: z
    .string()
    .default('false')
    .transform((val) => val === 'true'),
  NEXT_PUBLIC_FEATURE_BETA_PAYMENT_FLOW: z
    .string()
    .default('false')
    .transform((val) => val === 'true'),
  NEXT_PUBLIC_FEATURE_SHARED_MULTI_CHEF_SCHEDULING: z
    .string()
    .default('false')
    .transform((val) => val === 'true'),

  // Security (optional until auth is fully implemented)
  NEXTAUTH_SECRET: z.string().optional(),
  NEXTAUTH_URL: z.string().url().optional(),

  // Email service
  RESEND_API_KEY: z.string().min(1).optional(),

  // Rate limiting
  UPSTASH_REDIS_REST_URL: z.string().url().optional(),
  UPSTASH_REDIS_REST_TOKEN: z.string().optional(),
});

export type CustomerEnv = z.infer<typeof CustomerEnvSchema>;

// Validate and export environment
function createEnv(): CustomerEnv {
  // On client-side, process.env only has NEXT_PUBLIC_* vars that were inlined at build time
  // We need to be more lenient to avoid crashing the entire app
  const parsed = CustomerEnvSchema.safeParse(process.env);

  if (!parsed.success) {
    // Log the error for debugging (but don't crash the build)
    console.error('❌ Invalid environment variables:', parsed.error.flatten().fieldErrors);
    console.warn('⚠️ Using fallback defaults for missing environment variables.');

    // Return safe defaults to prevent build/runtime crashes
    // This allows builds to complete even when some env vars are missing
    return {
      NODE_ENV: (process.env.NODE_ENV as 'development' | 'production' | 'test') || 'production',
      NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL || 'https://myhibachichef.com',
      NEXT_PUBLIC_APP_NAME: process.env.NEXT_PUBLIC_APP_NAME || 'MyHibachi',
      NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'https://mhapi.mysticdatanode.net',
      NEXT_PUBLIC_AI_API_URL: process.env.NEXT_PUBLIC_AI_API_URL,
      NEXT_PUBLIC_MAINTENANCE_MODE: false,
      NEXT_PUBLIC_BOOKING_ENABLED: true,
      NEXT_PUBLIC_AI_CHAT_ENABLED: process.env.NEXT_PUBLIC_AI_CHAT_ENABLED === 'true',
      NEXT_PUBLIC_ZELLE_ENABLED: process.env.NEXT_PUBLIC_ZELLE_ENABLED === 'true',
      NEXT_PUBLIC_VENMO_ENABLED: process.env.NEXT_PUBLIC_VENMO_ENABLED === 'true',
      NEXT_PUBLIC_FEATURE_NEW_BOOKING_CALENDAR: false,
      NEXT_PUBLIC_FEATURE_V2_PRICING_ENGINE: false,
      NEXT_PUBLIC_FEATURE_CUSTOMER_PORTAL_BETA: false,
      NEXT_PUBLIC_FEATURE_NEW_MENU_SELECTOR: false,
      NEXT_PUBLIC_FEATURE_BETA_PAYMENT_FLOW: false,
      NEXT_PUBLIC_FEATURE_SHARED_MULTI_CHEF_SCHEDULING: false,
    } as CustomerEnv;
  }

  return parsed.data;
}

export const env = createEnv();

// Helper function to check if we're in production
export const isProd = env.NODE_ENV === 'production';
export const isDev = env.NODE_ENV === 'development';
export const isTest = env.NODE_ENV === 'test';

// API URLs with fallbacks
export const getApiUrl = () => {
  if (typeof window !== 'undefined') {
    // Client-side
    return env.NEXT_PUBLIC_API_URL;
  }
  // Server-side
  return env.NEXT_PUBLIC_API_URL;
};

export const getAiApiUrl = () => {
  return env.NEXT_PUBLIC_AI_API_URL || `${env.NEXT_PUBLIC_API_URL}/ai`;
};

/**
 * Get WebSocket URL with proper protocol (ws/wss)
 * Derives from API URL if NEXT_PUBLIC_WS_URL is not set
 *
 * @returns WebSocket base URL (without path)
 *
 * @example
 * const wsUrl = `${getWsUrl()}/api/v1/ws/chat?user_id=123`;
 */
export const getWsUrl = () => {
  // If NEXT_PUBLIC_WS_URL is explicitly set, use it
  if (process.env.NEXT_PUBLIC_WS_URL) {
    return process.env.NEXT_PUBLIC_WS_URL;
  }

  // Derive from API URL - convert http(s) to ws(s)
  const apiUrl = env.NEXT_PUBLIC_API_URL;
  return apiUrl.replace(/^https/, 'wss').replace(/^http/, 'ws');
};

/**
 * Type-safe feature flag checker for customer site
 *
 * @param flag - Feature flag name (must start with NEXT_PUBLIC_FEATURE_)
 * @returns boolean - True if feature is enabled
 * @throws Error if flag name is invalid or doesn't exist
 *
 * @example
 * if (isFeatureEnabled('NEXT_PUBLIC_FEATURE_NEW_BOOKING_CALENDAR')) {
 *   return <NewBookingCalendar />;
 * }
 * return <LegacyBookingCalendar />;
 */
export function isFeatureEnabled(flag: keyof CustomerEnv): boolean {
  const flagStr = flag as string;

  if (!flagStr.startsWith('NEXT_PUBLIC_FEATURE_')) {
    throw new Error(`Invalid feature flag: ${flag}. Must start with NEXT_PUBLIC_FEATURE_`);
  }

  if (!(flag in env)) {
    throw new Error(`Feature flag not found: ${flag}. Add it to CustomerEnvSchema in env.ts`);
  }

  return env[flag] as boolean;
}

/**
 * Get all enabled feature flags (for debugging/monitoring)
 * Only works in development/staging
 */
export function getEnabledFeatures(): string[] {
  if (isProd) {
    return []; // Don't expose in production
  }

  return Object.entries(env)
    .filter(([key, value]) => key.startsWith('NEXT_PUBLIC_FEATURE_') && value === true)
    .map(([key]) => key);
}
