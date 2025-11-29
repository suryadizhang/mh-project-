/**
 * My Hibachi Backend Configuration Loader
 * Loads secrets from GSM with environment variable fallbacks
 */

import { getGSMClient, createBackendAPIClient } from '../../../../libs/gsm-client/src/index';

export interface BackendConfig {
  // Database
  DB_URL: string;
  
  // Authentication
  JWT_SECRET: string;
  JWT_REFRESH_SECRET: string;
  SESSION_ENCRYPTION_KEY: string;
  
  // External APIs
  STRIPE_SECRET_KEY: string;
  STRIPE_WEBHOOK_SECRET: string;
  OPENAI_API_KEY: string;
  GOOGLE_MAPS_SERVER_KEY: string;
  
  // Communication
  SENDGRID_API_KEY: string;
  EMAIL_DEFAULT_FROM: string;
  
  // Internal
  REDIS_URL: string;
  ADMIN_PANEL_SECRET: string;
  
  // Feature Flags
  FF_ENABLE_AI_BOOKING_V3: boolean;
  FF_ENABLE_TRAVEL_FEE_V2: boolean;
  FF_ENABLE_SMS_REMINDERS: boolean;
  
  // Monitoring
  CONFIG_VERSION: string;
  NODE_ENV: string;
}

class ConfigManager {
  private config: BackendConfig | null = null;
  private environment: 'dev' | 'stg' | 'prod';
  private configVersion: string | null = null;
  
  constructor() {
    // Auto-detect environment
    this.environment = this.detectEnvironment();
    console.log(`🏗️ Initializing config for environment: ${this.environment}`);
  }

  /**
   * Load configuration from GSM with env fallbacks
   */
  async loadConfig(): Promise<BackendConfig> {
    console.log('📡 Loading configuration...');
    
    try {
      const gsmClient = createBackendAPIClient(this.environment);
      
      // Load all secrets
      const secrets = await gsmClient.getSecrets([
        // Database
        'DB_URL',
        
        // Auth
        'JWT_SECRET',
        'JWT_REFRESH_SECRET', 
        'SESSION_ENCRYPTION_KEY',
        
        // External APIs (from global)
        'STRIPE_SECRET_KEY',
        'STRIPE_WEBHOOK_SECRET',
        'OPENAI_API_KEY',
        'GOOGLE_MAPS_SERVER_KEY',
        'SENDGRID_API_KEY',
        
        // Communication
        'EMAIL_DEFAULT_FROM',
        
        // Internal
        'REDIS_URL',
        'ADMIN_PANEL_SECRET',
        
        // Feature Flags
        'FF_ENABLE_AI_BOOKING_V3',
        'FF_ENABLE_TRAVEL_FEE_V2', 
        'FF_ENABLE_SMS_REMINDERS',
        
        // Monitoring
        'CONFIG_VERSION'
      ]);

      this.config = {
        // Database
        DB_URL: secrets.DB_URL,
        
        // Authentication
        JWT_SECRET: secrets.JWT_SECRET,
        JWT_REFRESH_SECRET: secrets.JWT_REFRESH_SECRET,
        SESSION_ENCRYPTION_KEY: secrets.SESSION_ENCRYPTION_KEY || this.generateFallbackKey(),
        
        // External APIs
        STRIPE_SECRET_KEY: secrets.STRIPE_SECRET_KEY,
        STRIPE_WEBHOOK_SECRET: secrets.STRIPE_WEBHOOK_SECRET,
        OPENAI_API_KEY: secrets.OPENAI_API_KEY,
        GOOGLE_MAPS_SERVER_KEY: secrets.GOOGLE_MAPS_SERVER_KEY,
        
        // Communication
        SENDGRID_API_KEY: secrets.SENDGRID_API_KEY,
        EMAIL_DEFAULT_FROM: secrets.EMAIL_DEFAULT_FROM || 'noreply@myhibachichef.com',
        
        // Internal
        REDIS_URL: secrets.REDIS_URL || 'redis://localhost:6379',
        ADMIN_PANEL_SECRET: secrets.ADMIN_PANEL_SECRET,
        
        // Feature Flags (with safe defaults)
        FF_ENABLE_AI_BOOKING_V3: this.parseBoolean(secrets.FF_ENABLE_AI_BOOKING_V3, true),
        FF_ENABLE_TRAVEL_FEE_V2: this.parseBoolean(secrets.FF_ENABLE_TRAVEL_FEE_V2, false),
        FF_ENABLE_SMS_REMINDERS: this.parseBoolean(secrets.FF_ENABLE_SMS_REMINDERS, true),
        
        // Monitoring
        CONFIG_VERSION: secrets.CONFIG_VERSION || '1',
        NODE_ENV: process.env.NODE_ENV || this.environment
      };

      this.configVersion = this.config.CONFIG_VERSION;
      
      console.log('✅ Configuration loaded successfully');
      console.log(`📊 Config version: ${this.configVersion}`);
      console.log(`🚀 Feature flags: AI_V3=${this.config.FF_ENABLE_AI_BOOKING_V3}, Travel_V2=${this.config.FF_ENABLE_TRAVEL_FEE_V2}`);
      
      return this.config;
    } catch (error) {
      console.error('❌ Failed to load config from GSM:', error);
      console.log('🔄 Falling back to environment variables...');
      
      // Fallback to environment variables
      return this.loadFromEnv();
    }
  }

  /**
   * Get current configuration
   */
  getConfig(): BackendConfig {
    if (!this.config) {
      throw new Error('Configuration not loaded. Call loadConfig() first.');
    }
    return this.config;
  }

  /**
   * Check if config version changed and reload if needed
   */
  async checkAndReload(): Promise<boolean> {
    if (!this.config) return false;
    
    try {
      const gsmClient = createBackendAPIClient(this.environment);
      const hasChanged = await gsmClient.checkConfigVersion();
      
      if (hasChanged) {
        console.log('🔄 Config version changed, reloading...');
        await this.loadConfig();
        return true;
      }
      
      return false;
    } catch (error) {
      console.warn('⚠️ Could not check config version:', error);
      return false;
    }
  }

  /**
   * Get feature flag value
   */
  getFeatureFlag(flag: keyof BackendConfig): boolean {
    const config = this.getConfig();
    return Boolean(config[flag]);
  }

  /**
   * Start background config monitoring
   */
  startConfigMonitoring(intervalMinutes: number = 5): void {
    console.log(`🔍 Starting config monitoring (every ${intervalMinutes} minutes)`);
    
    setInterval(async () => {
      try {
        const changed = await this.checkAndReload();
        if (changed) {
          console.log('🔄 Configuration reloaded due to version change');
        }
      } catch (error) {
        console.error('❌ Config monitoring error:', error);
      }
    }, intervalMinutes * 60 * 1000);
  }

  // Private methods
  private detectEnvironment(): 'dev' | 'stg' | 'prod' {
    const env = process.env.NODE_ENV?.toLowerCase();
    const branch = process.env.VERCEL_GIT_COMMIT_REF || process.env.BRANCH_NAME;
    
    if (env === 'production' || branch === 'main') return 'prod';
    if (env === 'staging' || branch === 'dev') return 'stg';
    return 'dev';
  }

  private parseBoolean(value: string | undefined, defaultValue: boolean): boolean {
    if (!value) return defaultValue;
    return value.toLowerCase() === 'true' || value === '1';
  }

  private generateFallbackKey(): string {
    return process.env.SESSION_ENCRYPTION_KEY || 'fallback-key-' + Math.random().toString(36);
  }

  private loadFromEnv(): BackendConfig {
    console.log('📁 Loading configuration from environment variables');
    
    return {
      // Database
      DB_URL: process.env.DB_URL || 'postgresql://localhost/myhibachi_dev',
      
      // Authentication
      JWT_SECRET: process.env.JWT_SECRET || 'dev-jwt-secret',
      JWT_REFRESH_SECRET: process.env.JWT_REFRESH_SECRET || 'dev-refresh-secret',
      SESSION_ENCRYPTION_KEY: process.env.SESSION_ENCRYPTION_KEY || 'dev-session-key',
      
      // External APIs
      STRIPE_SECRET_KEY: process.env.STRIPE_SECRET_KEY || '',
      STRIPE_WEBHOOK_SECRET: process.env.STRIPE_WEBHOOK_SECRET || '',
      OPENAI_API_KEY: process.env.OPENAI_API_KEY || '',
      GOOGLE_MAPS_SERVER_KEY: process.env.GOOGLE_MAPS_SERVER_KEY || '',
      
      // Communication
      SENDGRID_API_KEY: process.env.SENDGRID_API_KEY || '',
      EMAIL_DEFAULT_FROM: process.env.EMAIL_DEFAULT_FROM || 'noreply@myhibachichef.com',
      
      // Internal
      REDIS_URL: process.env.REDIS_URL || 'redis://localhost:6379',
      ADMIN_PANEL_SECRET: process.env.ADMIN_PANEL_SECRET || 'dev-admin-secret',
      
      // Feature Flags
      FF_ENABLE_AI_BOOKING_V3: this.parseBoolean(process.env.FF_ENABLE_AI_BOOKING_V3, true),
      FF_ENABLE_TRAVEL_FEE_V2: this.parseBoolean(process.env.FF_ENABLE_TRAVEL_FEE_V2, false),
      FF_ENABLE_SMS_REMINDERS: this.parseBoolean(process.env.FF_ENABLE_SMS_REMINDERS, true),
      
      // Monitoring
      CONFIG_VERSION: process.env.CONFIG_VERSION || '1',
      NODE_ENV: process.env.NODE_ENV || 'development'
    };
  }
}

// Singleton instance
const configManager = new ConfigManager();

/**
 * Load and get configuration
 */
export async function loadConfig(): Promise<BackendConfig> {
  return await configManager.loadConfig();
}

/**
 * Get current configuration (must be loaded first)
 */
export function getConfig(): BackendConfig {
  return configManager.getConfig();
}

/**
 * Check for config updates and reload if needed
 */
export async function reloadConfigIfChanged(): Promise<boolean> {
  return await configManager.checkAndReload();
}

/**
 * Start background config monitoring
 */
export function startConfigMonitoring(intervalMinutes?: number): void {
  configManager.startConfigMonitoring(intervalMinutes);
}

/**
 * Get feature flag value
 */
export function getFeatureFlag(flag: keyof BackendConfig): boolean {
  return configManager.getFeatureFlag(flag);
}

/**
 * Convenience functions for common feature flags
 */
export const isAIBookingV3Enabled = () => getFeatureFlag('FF_ENABLE_AI_BOOKING_V3');
export const isTravelFeeV2Enabled = () => getFeatureFlag('FF_ENABLE_TRAVEL_FEE_V2');
export const isSMSRemindersEnabled = () => getFeatureFlag('FF_ENABLE_SMS_REMINDERS');
