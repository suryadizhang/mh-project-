import { z } from 'zod';

// Admin Panel environment schema
const AdminEnvSchema = z.object({
  // App configuration
  NODE_ENV: z
    .enum(['development', 'production', 'test'])
    .default('development'),
  NEXT_PUBLIC_APP_URL: z.string().url(),
  NEXT_PUBLIC_APP_NAME: z.string().default('MyHibachi Admin'),
  NEXT_PUBLIC_ENV: z
    .enum(['development', 'staging', 'production'])
    .default('development'),

  // API configuration
  NEXT_PUBLIC_API_URL: z.string().url(),
  NEXT_PUBLIC_AI_API_URL: z.string().url().optional(),

  // Analytics & Monitoring
  NEXT_PUBLIC_GA_MEASUREMENT_ID: z.string().optional(),
  VERCEL_URL: z.string().optional(),

  // Feature Flags - Admin Panel
  // Following naming convention: NEXT_PUBLIC_FEATURE_<SCOPE>_<DESCRIPTION>_<VERSION>
  // Default to 'false' in production for safety

  // Admin-Specific Features
  NEXT_PUBLIC_FEATURE_ADMIN_DASHBOARD_V2: z
    .string()
    .default('false')
    .transform(val => val === 'true'),
  NEXT_PUBLIC_FEATURE_ADMIN_ANALYTICS_BETA: z
    .string()
    .default('false')
    .transform(val => val === 'true'),
  NEXT_PUBLIC_FEATURE_ADMIN_BOOKING_MANAGER_V2: z
    .string()
    .default('false')
    .transform(val => val === 'true'),
  NEXT_PUBLIC_FEATURE_ADMIN_TRAVEL_FEE_EDITOR: z
    .string()
    .default('false')
    .transform(val => val === 'true'),
  NEXT_PUBLIC_FEATURE_ADMIN_AI_INSIGHTS: z
    .string()
    .default('false')
    .transform(val => val === 'true'),

  // Shared Features (across customer + admin)
  NEXT_PUBLIC_FEATURE_SHARED_MULTI_CHEF_SCHEDULING: z
    .string()
    .default('false')
    .transform(val => val === 'true'),
  NEXT_PUBLIC_FEATURE_SHARED_ONEDRIVE_SYNC: z
    .string()
    .default('false')
    .transform(val => val === 'true'),

  // Security
  NEXTAUTH_SECRET: z.string().min(32),
  NEXTAUTH_URL: z.string().url(),

  // Rate limiting
  UPSTASH_REDIS_REST_URL: z.string().url().optional(),
  UPSTASH_REDIS_REST_TOKEN: z.string().optional(),
});

export type AdminEnv = z.infer<typeof AdminEnvSchema>;

// Validate and export environment
function createEnv(): AdminEnv {
  const parsed = AdminEnvSchema.safeParse(process.env);

  if (!parsed.success) {
    console.error(
      '❌ Invalid environment variables:',
      parsed.error.flatten().fieldErrors
    );
    throw new Error('Invalid environment variables');
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
 * Type-safe feature flag checker for admin panel
 *
 * @param flag - Feature flag name (must start with NEXT_PUBLIC_FEATURE_)
 * @returns boolean - True if feature is enabled
 * @throws Error if flag name is invalid or doesn't exist
 *
 * @example
 * if (isFeatureEnabled('NEXT_PUBLIC_FEATURE_ADMIN_DASHBOARD_V2')) {
 *   return <DashboardV2 />;
 * }
 * return <DashboardV1 />;
 */
export function isFeatureEnabled(flag: keyof AdminEnv): boolean {
  const flagStr = flag as string;

  if (!flagStr.startsWith('NEXT_PUBLIC_FEATURE_')) {
    throw new Error(
      `Invalid feature flag: ${flag}. Must start with NEXT_PUBLIC_FEATURE_`
    );
  }

  if (!(flag in env)) {
    throw new Error(
      `Feature flag not found: ${flag}. Add it to AdminEnvSchema in env.ts`
    );
  }

  return env[flag] as boolean;
}

/**
 * Get all enabled feature flags (for debugging/monitoring)
 */
export function getEnabledFeatures(): string[] {
  return Object.entries(env)
    .filter(
      ([key, value]) => key.startsWith('NEXT_PUBLIC_FEATURE_') && value === true
    )
    .map(([key]) => key);
}

/**
 * Feature flag metadata for admin UI display
 */
export interface FeatureFlagMetadata {
  name: string;
  scope: 'admin' | 'shared';
  enabled: boolean;
  description: string;
}

/**
 * Get all feature flags with metadata (for admin settings page)
 */
export function getAllFeatureFlags(): FeatureFlagMetadata[] {
  return [
    {
      name: 'NEXT_PUBLIC_FEATURE_ADMIN_DASHBOARD_V2',
      scope: 'admin',
      enabled: env.NEXT_PUBLIC_FEATURE_ADMIN_DASHBOARD_V2,
      description:
        'New admin dashboard with enhanced analytics and real-time updates',
    },
    {
      name: 'NEXT_PUBLIC_FEATURE_ADMIN_ANALYTICS_BETA',
      scope: 'admin',
      enabled: env.NEXT_PUBLIC_FEATURE_ADMIN_ANALYTICS_BETA,
      description:
        'Advanced analytics dashboard with custom reports and insights',
    },
    {
      name: 'NEXT_PUBLIC_FEATURE_ADMIN_BOOKING_MANAGER_V2',
      scope: 'admin',
      enabled: env.NEXT_PUBLIC_FEATURE_ADMIN_BOOKING_MANAGER_V2,
      description:
        'Redesigned booking manager with bulk operations and filters',
    },
    {
      name: 'NEXT_PUBLIC_FEATURE_ADMIN_TRAVEL_FEE_EDITOR',
      scope: 'admin',
      enabled: env.NEXT_PUBLIC_FEATURE_ADMIN_TRAVEL_FEE_EDITOR,
      description: 'Visual travel fee zone editor with map integration',
    },
    {
      name: 'NEXT_PUBLIC_FEATURE_ADMIN_AI_INSIGHTS',
      scope: 'admin',
      enabled: env.NEXT_PUBLIC_FEATURE_ADMIN_AI_INSIGHTS,
      description: 'AI-powered insights and recommendations for operations',
    },
    {
      name: 'NEXT_PUBLIC_FEATURE_SHARED_MULTI_CHEF_SCHEDULING',
      scope: 'shared',
      enabled: env.NEXT_PUBLIC_FEATURE_SHARED_MULTI_CHEF_SCHEDULING,
      description: 'Multi-chef scheduling system with automatic assignments',
    },
    {
      name: 'NEXT_PUBLIC_FEATURE_SHARED_ONEDRIVE_SYNC',
      scope: 'shared',
      enabled: env.NEXT_PUBLIC_FEATURE_SHARED_ONEDRIVE_SYNC,
      description: 'Two-way sync with OneDrive Excel booking spreadsheet',
    },
  ];
}
