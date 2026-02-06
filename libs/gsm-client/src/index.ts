/**
 * Google Cloud Secret Manager Client for My Hibachi
 * Enterprise-grade secret management with fallback to environment variables
 */

import { SecretManagerServiceClient } from '@google-cloud/secret-manager';

export interface SecretConfig {
  environment: 'dev' | 'stg' | 'prod';
  service:
    | 'global'
    | 'backend-api'
    | 'backend-ai'
    | 'backend-crm'
    | 'frontend-web'
    | 'frontend-admin';
  projectId?: string;
  fallbackToEnv?: boolean;
}

export interface Secret {
  key: string;
  value: string;
  version: string;
  lastModified: Date;
  source: 'gsm' | 'env' | 'fallback';
}

export class GSMClient {
  private client: SecretManagerServiceClient;
  private config: SecretConfig;
  private cache: Map<string, Secret> = new Map();
  private configVersion: string | null = null;

  constructor(config: SecretConfig) {
    this.config = {
      fallbackToEnv: true,
      ...config,
    };

    this.client = new SecretManagerServiceClient({
      projectId: config.projectId || process.env.GCP_PROJECT_ID,
    });
  }

  /**
   * Get secret value with automatic fallback to environment variables
   */
  async getSecret(key: string): Promise<string> {
    const secretId = this.buildSecretId(key);

    try {
      // Try cache first
      if (this.cache.has(secretId)) {
        const cached = this.cache.get(secretId)!;
        return cached.value;
      }

      // Try GSM
      const gsmValue = await this.getFromGSM(secretId);
      if (gsmValue) {
        this.cache.set(secretId, {
          key: secretId,
          value: gsmValue,
          version: 'latest',
          lastModified: new Date(),
          source: 'gsm',
        });
        return gsmValue;
      }

      // Fallback to environment variable
      if (this.config.fallbackToEnv) {
        const envValue = process.env[key];
        if (envValue) {
          this.cache.set(secretId, {
            key: secretId,
            value: envValue,
            version: 'env',
            lastModified: new Date(),
            source: 'env',
          });
          return envValue;
        }
      }

      throw new Error(`Secret not found: ${secretId}`);
    } catch (error) {
      console.error(`Error getting secret ${secretId}:`, error);

      // Last resort: try direct env var
      const envValue = process.env[key];
      if (envValue) {
        return envValue;
      }

      throw error;
    }
  }

  /**
   * Get multiple secrets in batch
   */
  async getSecrets(keys: string[]): Promise<Record<string, string>> {
    const results: Record<string, string> = {};

    await Promise.all(
      keys.map(async key => {
        try {
          results[key] = await this.getSecret(key);
        } catch (error) {
          console.error(`Failed to get secret ${key}:`, error);
          // Continue with other secrets
        }
      })
    );

    return results;
  }

  /**
   * Set secret in GSM (for admin operations)
   */
  async setSecret(key: string, value: string): Promise<void> {
    const secretId = this.buildSecretId(key);

    try {
      // Create secret if it doesn't exist
      await this.createSecretIfNotExists(secretId);

      // Add new version
      await this.client.addSecretVersion({
        parent: `projects/${this.config.projectId}/secrets/${secretId}`,
        payload: {
          data: Buffer.from(value, 'utf8'),
        },
      });

      // Update cache
      this.cache.set(secretId, {
        key: secretId,
        value,
        version: 'latest',
        lastModified: new Date(),
        source: 'gsm',
      });

      // Secret updated successfully (logging removed for production security)
    } catch (error) {
      console.error(`Error setting secret:`, error);
      throw error;
    }
  }

  /**
   * Check if config version changed and reload if needed
   */
  async checkConfigVersion(): Promise<boolean> {
    try {
      const currentVersion = await this.getSecret('CONFIG_VERSION');

      if (this.configVersion !== currentVersion) {
        // Config version changed, clearing cache (logging removed for production)
        this.configVersion = currentVersion;
        this.clearCache();
        return true;
      }

      return false;
    } catch (error) {
      console.warn('Could not check config version:', error);
      return false;
    }
  }

  /**
   * Get all secrets for this service
   */
  async getAllServiceSecrets(): Promise<Record<string, Secret>> {
    const secrets: Record<string, Secret> = {};

    // Get global secrets
    const globalKeys = [
      'STRIPE_SECRET_KEY',
      'STRIPE_WEBHOOK_SECRET',
      'OPENAI_API_KEY',
      'GOOGLE_MAPS_SERVER_KEY',
      'SENDGRID_API_KEY',
      'CONFIG_VERSION',
    ];

    // Get service-specific secrets based on config
    let serviceKeys: string[] = [];
    switch (this.config.service) {
      case 'backend-api':
        serviceKeys = [
          'DB_URL',
          'JWT_SECRET',
          'JWT_REFRESH_SECRET',
          'REDIS_URL',
          'ADMIN_PANEL_SECRET',
        ];
        break;
      case 'backend-ai':
        serviceKeys = ['OPENAI_API_KEY', 'VECTOR_DB_URL', 'RAG_STORAGE_BUCKET'];
        break;
      case 'frontend-web':
        serviceKeys = [
          'NEXT_PUBLIC_API_URL',
          'NEXT_PUBLIC_AI_API_URL',
          'NEXT_PUBLIC_STRIPE_PUBLIC_KEY',
        ];
        break;
      case 'frontend-admin':
        serviceKeys = ['NEXT_PUBLIC_API_URL', 'NEXT_PUBLIC_ADMIN_PANEL_SECRET'];
        break;
    }

    // Fetch all secrets
    const allKeys = [...globalKeys, ...serviceKeys];
    for (const key of allKeys) {
      try {
        const value = await this.getSecret(key);
        secrets[key] = {
          key,
          value,
          version: 'latest',
          lastModified: new Date(),
          source: 'gsm',
        };
      } catch (error) {
        console.warn(`Could not load secret ${key}:`, error);
      }
    }

    return secrets;
  }

  /**
   * Clear cache (for config reload)
   */
  clearCache(): void {
    this.cache.clear();
    // Cache cleared (logging removed for production)
  }

  /**
   * Get cache statistics
   */
  getCacheStats(): {
    size: number;
    keys: string[];
    sources: Record<string, number>;
  } {
    const sources: Record<string, number> = {};
    const keys: string[] = [];

    for (const secret of this.cache.values()) {
      keys.push(secret.key);
      sources[secret.source] = (sources[secret.source] || 0) + 1;
    }

    return {
      size: this.cache.size,
      keys,
      sources,
    };
  }

  // Private methods
  private buildSecretId(key: string): string {
    return `${this.config.environment}-${this.config.service}-${key}`;
  }

  private async getFromGSM(secretId: string): Promise<string | null> {
    try {
      const [version] = await this.client.accessSecretVersion({
        name: `projects/${this.config.projectId}/secrets/${secretId}/versions/latest`,
      });

      if (!version.payload?.data) {
        return null;
      }

      return version.payload.data.toString();
    } catch (error: any) {
      if (error.code === 5) {
        // NOT_FOUND
        return null;
      }
      throw error;
    }
  }

  private async createSecretIfNotExists(secretId: string): Promise<void> {
    try {
      await this.client.createSecret({
        parent: `projects/${this.config.projectId}`,
        secretId,
        secret: {
          replication: {
            automatic: {},
          },
        },
      });
      // Secret created successfully (logging removed for production security)
    } catch (error: any) {
      if (error.code !== 6) {
        // ALREADY_EXISTS
        throw error;
      }
    }
  }
}

/**
 * Convenience functions for common operations
 */

// Singleton instances for each service type
const clients: Map<string, GSMClient> = new Map();

export function getGSMClient(config: SecretConfig): GSMClient {
  const key = `${config.environment}-${config.service}`;

  if (!clients.has(key)) {
    clients.set(key, new GSMClient(config));
  }

  return clients.get(key)!;
}

/**
 * Quick access functions for specific services
 */
export const createBackendAPIClient = (env: 'dev' | 'stg' | 'prod') =>
  getGSMClient({ environment: env, service: 'backend-api' });

export const createBackendAIClient = (env: 'dev' | 'stg' | 'prod') =>
  getGSMClient({ environment: env, service: 'backend-ai' });

export const createFrontendWebClient = (env: 'dev' | 'stg' | 'prod') =>
  getGSMClient({ environment: env, service: 'frontend-web' });

export const createFrontendAdminClient = (env: 'dev' | 'stg' | 'prod') =>
  getGSMClient({ environment: env, service: 'frontend-admin' });

export const createGlobalClient = (env: 'dev' | 'stg' | 'prod') =>
  getGSMClient({ environment: env, service: 'global' });
