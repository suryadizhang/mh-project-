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
  
  // Payment providers
  NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: z.string().min(1),
  STRIPE_SECRET_KEY: z.string().min(1),
  STRIPE_WEBHOOK_SECRET: z.string().min(1),
  
  // Zelle configuration
  NEXT_PUBLIC_ZELLE_ENABLED: z.string().default('false').transform(val => val === 'true'),
  NEXT_PUBLIC_ZELLE_EMAIL: z.string().email().optional(),
  NEXT_PUBLIC_ZELLE_PHONE: z.string().optional(),
  
  // Venmo configuration
  NEXT_PUBLIC_VENMO_ENABLED: z.string().default('false').transform(val => val === 'true'),
  NEXT_PUBLIC_VENMO_USERNAME: z.string().optional(),
  
  // Analytics & Monitoring
  NEXT_PUBLIC_GA_MEASUREMENT_ID: z.string().optional(),
  NEXT_PUBLIC_HOTJAR_ID: z.string().optional(),
  VERCEL_URL: z.string().optional(),
  
  // Feature flags
  NEXT_PUBLIC_MAINTENANCE_MODE: z.string().default('false').transform(val => val === 'true'),
  NEXT_PUBLIC_BOOKING_ENABLED: z.string().default('true').transform(val => val === 'true'),
  NEXT_PUBLIC_AI_CHAT_ENABLED: z.string().default('true').transform(val => val === 'true'),
  
  // Security
  NEXTAUTH_SECRET: z.string().min(32),
  NEXTAUTH_URL: z.string().url(),
  
  // Email service
  RESEND_API_KEY: z.string().min(1).optional(),
  
  // Rate limiting
  UPSTASH_REDIS_REST_URL: z.string().url().optional(),
  UPSTASH_REDIS_REST_TOKEN: z.string().optional(),
});

export type CustomerEnv = z.infer<typeof CustomerEnvSchema>;

// Validate and export environment
function createEnv(): CustomerEnv {
  const parsed = CustomerEnvSchema.safeParse(process.env);
  
  if (!parsed.success) {
    console.error('❌ Invalid environment variables:', parsed.error.flatten().fieldErrors);
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