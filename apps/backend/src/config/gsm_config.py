"""
Google Secret Manager Configuration Module for My Hibachi Backend
Enterprise-grade secret loading with fallbacks and caching
"""

import os
import logging
from typing import Dict, Any, Optional
from functools import lru_cache
import asyncio
from datetime import datetime, timedelta, timezone

try:
    from google.cloud import secretmanager

    GSM_AVAILABLE = True
except ImportError:
    GSM_AVAILABLE = False
    secretmanager = None

logger = logging.getLogger(__name__)


class GSMConfig:
    """Google Secret Manager configuration loader with fallbacks"""

    def __init__(self, project_id: str = "my-hibachi-crm", environment: str = "prod"):
        self.project_id = project_id
        self.environment = environment
        self.client = None
        self._cache: Dict[str, Any] = {}
        self._cache_expiry: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(minutes=15)  # Cache for 15 minutes

        if GSM_AVAILABLE:
            try:
                self.client = secretmanager.SecretManagerServiceClient()
                logger.info(f"✅ GSM client initialized for project: {project_id}")
            except Exception as e:
                logger.warning(f"⚠️ GSM client initialization failed: {e}")
                self.client = None
        else:
            logger.warning(
                "⚠️ Google Cloud Secret Manager not available, using environment variables only"
            )

    def _build_secret_name(self, category: str, key: str) -> str:
        """Build the full secret name for GSM"""
        return f"{self.environment}-{category}-{key}"

    def _is_cache_valid(self, secret_name: str) -> bool:
        """Check if cached value is still valid"""
        if secret_name not in self._cache_expiry:
            return False
        return datetime.now(timezone.utc) < self._cache_expiry[secret_name]

    async def get_secret(
        self, category: str, key: str, fallback_env_var: Optional[str] = None
    ) -> Optional[str]:
        """
        Get secret value with GSM + environment variable fallback

        Args:
            category: Secret category (global, backend-api, frontend-web, frontend-admin)
            key: Secret key name
            fallback_env_var: Environment variable name for fallback

        Returns:
            Secret value or None if not found
        """
        secret_name = self._build_secret_name(category, key)

        # Check cache first
        if self._is_cache_valid(secret_name):
            return self._cache[secret_name]

        # Try GSM first
        if self.client:
            try:
                secret_path = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
                response = await asyncio.get_event_loop().run_in_executor(
                    None, self.client.access_secret_version, {"name": secret_path}
                )
                # Strip whitespace to handle Windows line endings (\r\n) in secret values
                value = response.payload.data.decode("UTF-8").strip()

                # Cache the result
                self._cache[secret_name] = value
                self._cache_expiry[secret_name] = datetime.now(timezone.utc) + self._cache_ttl

                logger.debug(f"✅ Retrieved secret from GSM: {secret_name}")
                return value

            except Exception as e:
                logger.warning(f"⚠️ Failed to retrieve {secret_name} from GSM: {e}")

        # Fallback to environment variable
        env_var = fallback_env_var or key
        env_value = os.getenv(env_var)
        if env_value:
            # Cache the fallback value
            self._cache[secret_name] = env_value
            self._cache_expiry[secret_name] = datetime.now(timezone.utc) + self._cache_ttl
            logger.debug(f"✅ Retrieved secret from environment: {env_var}")
            return env_value

        logger.error(f"❌ Secret not found: {secret_name} (env: {env_var})")
        return None

    async def get_secrets_batch(self, secrets: list) -> Dict[str, str]:
        """
        Get multiple secrets in batch

        Args:
            secrets: List of tuples (category, key, optional_env_var)

        Returns:
            Dictionary of {key: value}
        """
        results = {}
        tasks = []

        for secret_info in secrets:
            if len(secret_info) == 2:
                category, key = secret_info
                env_var = None
            else:
                category, key, env_var = secret_info

            task = self.get_secret(category, key, env_var)
            tasks.append((key, task))

        # Execute all requests concurrently
        for key, task in tasks:
            try:
                value = await task
                if value:
                    results[key] = value
            except Exception as e:
                logger.error(f"Failed to retrieve secret {key}: {e}")

        return results

    def clear_cache(self):
        """Clear the secret cache"""
        self._cache.clear()
        self._cache_expiry.clear()
        logger.info("🗑️ Secret cache cleared")


# Global instance
_gsm_config: Optional[GSMConfig] = None


@lru_cache()
def get_gsm_config() -> GSMConfig:
    """Get singleton GSM configuration instance.

    Environment Variables:
        GCP_PROJECT_ID: Google Cloud project ID (default: my-hibachi-crm)
        GSM_ENVIRONMENT: GSM secret prefix (default: prod)
            - Use 'prod' for production secrets (prod-backend-api-*)
            - Use 'staging' for staging secrets (staging-backend-api-*)
            - This is SEPARATE from the ENVIRONMENT variable used by Settings/Pydantic

    Note:
        GSM_ENVIRONMENT controls the secret naming prefix in GSM.
        ENVIRONMENT controls the Pydantic Settings validation (development/staging/production).
        These are intentionally separate to allow flexible naming in each system.
    """
    global _gsm_config
    if _gsm_config is None:
        project_id = os.getenv("GCP_PROJECT_ID", "my-hibachi-crm")
        # Use GSM_ENVIRONMENT for secret prefix, separate from ENVIRONMENT (Pydantic enum)
        # Default to "prod" to match existing GSM secrets (prod-backend-api-*)
        gsm_environment = os.getenv("GSM_ENVIRONMENT", "prod")
        _gsm_config = GSMConfig(project_id, gsm_environment)
    return _gsm_config


async def load_config() -> Dict[str, Any]:
    """
    Load complete configuration from GSM with environment fallbacks

    Returns:
        Dictionary with all configuration values
    """
    gsm = get_gsm_config()

    # Define all required secrets with their categories and fallback env vars
    required_secrets = [
        # Global secrets
        ("global", "CONFIG_VERSION", "CONFIG_VERSION"),
        ("global", "STRIPE_SECRET_KEY", "STRIPE_SECRET_KEY"),
        ("global", "OPENAI_API_KEY", "OPENAI_API_KEY"),
        ("global", "GOOGLE_MAPS_SERVER_KEY", "GOOGLE_MAPS_SERVER_KEY"),
        # Backend API secrets
        ("backend-api", "JWT_SECRET", "JWT_SECRET"),
        ("backend-api", "ENCRYPTION_KEY", "ENCRYPTION_KEY"),
        ("backend-api", "DB_URL", "DATABASE_URL"),
        ("backend-api", "REDIS_URL", "REDIS_URL"),
        ("backend-api", "RC_CLIENT_ID", "RINGCENTRAL_CLIENT_ID"),
        ("backend-api", "RC_CLIENT_SECRET", "RINGCENTRAL_CLIENT_SECRET"),
        ("backend-api", "DEEPGRAM_API_KEY", "DEEPGRAM_API_KEY"),
        ("backend-api", "SMTP_PASSWORD", "SMTP_PASSWORD"),
        ("backend-api", "GMAIL_APP_PASSWORD", "GMAIL_APP_PASSWORD"),
        # Cloudflare R2 Storage secrets
        ("backend-api", "cloudflare-r2-account-id", "CLOUDFLARE_R2_ACCOUNT_ID"),
        ("backend-api", "cloudflare-r2-access-key-id", "CLOUDFLARE_R2_ACCESS_KEY_ID"),
        ("backend-api", "cloudflare-r2-secret-access-key", "CLOUDFLARE_R2_SECRET_ACCESS_KEY"),
        ("backend-api", "cloudflare-r2-bucket", "CLOUDFLARE_R2_BUCKET"),
        ("backend-api", "cloudflare-r2-endpoint", "CLOUDFLARE_R2_ENDPOINT"),
        # Google Calendar integration (service account JSON)
        ("backend-api", "google-calendar-service-account", "GOOGLE_SERVICE_ACCOUNT_JSON"),
    ]

    logger.info("🔑 Loading configuration from GSM...")
    config = await gsm.get_secrets_batch(required_secrets)

    # Validate critical secrets
    critical_secrets = ["JWT_SECRET", "ENCRYPTION_KEY"]
    missing_critical = [key for key in critical_secrets if key not in config]

    if missing_critical:
        raise ValueError(f"Critical secrets missing: {missing_critical}")

    logger.info(f"✅ Loaded {len(config)} configuration values")
    return config


async def start_config_monitoring():
    """Start background monitoring for configuration changes"""
    logger.info("🔄 Configuration monitoring started")
    # This could be enhanced to watch for GSM changes
    pass
