"""
Centralized configuration using Pydantic Settings
All environment variables validated here
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional, List
from enum import Enum
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class UserRole(str, Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"
    MANAGER = "manager"
    OWNER = "owner"

class Settings(BaseSettings):
    """Application settings with type validation"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    APP_NAME: str = "My Hibachi Chef CRM"
    DEBUG: bool = False
    ENVIRONMENT: Environment = Environment.PRODUCTION
    API_VERSION: str = "1.0.0"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_ECHO: bool = False
    
    # Redis
    REDIS_URL: str
    
    # Security
    SECRET_KEY: str
    ENCRYPTION_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: str = "https://myhibachichef.com,https://admin.myhibachichef.com"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    # RingCentral
    RC_CLIENT_ID: str = "dev-client-id"
    RC_CLIENT_SECRET: str = "dev-client-secret"
    RC_JWT_TOKEN: str = "dev-jwt-token"
    RC_WEBHOOK_SECRET: str = "dev-webhook-secret"
    RC_SMS_FROM: str = "+19167408768"
    RC_SERVER_URL: str = "https://platform.ringcentral.com"
    
    # OpenAI
    OPENAI_API_KEY: str = "sk-dev-placeholder-key"
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_REALTIME_MODEL: str = "gpt-4o-realtime-preview-2024-12-17"
    
    # Stripe
    STRIPE_SECRET_KEY: str = "sk_test_dev_placeholder"
    STRIPE_PUBLISHABLE_KEY: str = "pk_test_dev_placeholder"
    STRIPE_WEBHOOK_SECRET: str = "whsec_dev_placeholder"
    
    # Plaid
    PLAID_CLIENT_ID: str = "dev-plaid-client-id"
    PLAID_SECRET: str = "dev-plaid-secret"
    PLAID_ENV: str = "sandbox"
    
    # Meta (Facebook/Instagram)
    META_APP_ID: str = "dev-meta-app-id"
    META_APP_SECRET: str = "dev-meta-app-secret"
    META_VERIFY_TOKEN: str = "dev-meta-verify-token"
    META_PAGE_ACCESS_TOKEN: str = "dev-meta-page-access-token"
    
    # Google Business
    GOOGLE_CLOUD_PROJECT: str = "dev-google-cloud-project"
    GOOGLE_CREDENTIALS_JSON: str = "/dev/null/credentials.json"
    GBP_ACCOUNT_ID: str = "dev-google-business-account-id"
    GBP_LOCATION_ID: str = "dev-google-business-location-id"
    
    # Business Info (PUBLIC SAFE DATA ONLY)
    BUSINESS_NAME: str = "my Hibachi LLC"
    BUSINESS_EMAIL: str = "cs@myhibachichef.com"
    BUSINESS_PHONE: str = "+19167408768"
    BUSINESS_CITY: str = "Fremont"
    BUSINESS_STATE: str = "California"
    SERVICE_AREAS: str = "Sacramento, Bay Area, Central Valley"
    
    # AI Settings
    ENABLE_AI_AUTO_REPLY: bool = True
    AI_CONFIDENCE_THRESHOLD: int = 80
    
    # Business Rules
    QUIET_HOURS_START: int = 21
    QUIET_HOURS_END: int = 8
    DEFAULT_TIMEZONE: str = "America/Los_Angeles"
    MAX_SMS_PER_THREAD: int = 3
    
    # Rate Limiting Configuration (ADMIN-OPTIMIZED)
    # Note: Burst limits are defined for future implementation of token bucket algorithm
    # Currently using sliding window with per-minute and per-hour limits
    RATE_LIMIT_PUBLIC_PER_MINUTE: int = 20
    RATE_LIMIT_PUBLIC_PER_HOUR: int = 1000
    RATE_LIMIT_PUBLIC_BURST: int = 30  # For future token bucket implementation
    
    RATE_LIMIT_ADMIN_PER_MINUTE: int = 100
    RATE_LIMIT_ADMIN_PER_HOUR: int = 5000
    RATE_LIMIT_ADMIN_BURST: int = 150
    
    RATE_LIMIT_ADMIN_SUPER_PER_MINUTE: int = 200
    RATE_LIMIT_ADMIN_SUPER_PER_HOUR: int = 10000
    RATE_LIMIT_ADMIN_SUPER_BURST: int = 300
    
    RATE_LIMIT_AI_PER_MINUTE: int = 10
    RATE_LIMIT_AI_PER_HOUR: int = 300
    RATE_LIMIT_AI_BURST: int = 15
    
    RATE_LIMIT_WEBHOOK_PER_MINUTE: int = 100
    RATE_LIMIT_WEBHOOK_PER_HOUR: int = 5000
    RATE_LIMIT_WEBHOOK_BURST: int = 200
    
    def get_rate_limit_for_user(self, user_role: Optional[UserRole] = None) -> dict:
        """Get rate limit configuration based on user role"""
        if user_role in [UserRole.OWNER, UserRole.MANAGER]:
            return {
                "per_minute": self.RATE_LIMIT_ADMIN_SUPER_PER_MINUTE,
                "per_hour": self.RATE_LIMIT_ADMIN_SUPER_PER_HOUR,
                "burst": self.RATE_LIMIT_ADMIN_SUPER_BURST,
                "tier": "admin_super"
            }
        elif user_role == UserRole.ADMIN:
            return {
                "per_minute": self.RATE_LIMIT_ADMIN_PER_MINUTE,
                "per_hour": self.RATE_LIMIT_ADMIN_PER_HOUR,
                "burst": self.RATE_LIMIT_ADMIN_BURST,
                "tier": "admin"
            }
        else:
            return {
                "per_minute": self.RATE_LIMIT_PUBLIC_PER_MINUTE,
                "per_hour": self.RATE_LIMIT_PUBLIC_PER_HOUR,
                "burst": self.RATE_LIMIT_PUBLIC_BURST,
                "tier": "public"
            }
    
    def get_ai_rate_limit(self) -> dict:
        """Get AI-specific rate limits (same for all users due to cost)"""
        return {
            "per_minute": self.RATE_LIMIT_AI_PER_MINUTE,
            "per_hour": self.RATE_LIMIT_AI_PER_HOUR,
            "burst": self.RATE_LIMIT_AI_BURST,
            "tier": "ai"
        }

@lru_cache()
def get_settings() -> Settings:
    return Settings()