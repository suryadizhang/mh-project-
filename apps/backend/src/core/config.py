"""
Centralized configuration using Pydantic Settings
All environment variables validated here
"""

from enum import Enum
from functools import lru_cache
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file (in parent directory)
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class UserRole(str, Enum):
    """User roles matching database schema - customers don't need login for frontend"""

    SUPER_ADMIN = "super_admin"  # Highest privilege - full system access
    ADMIN = "admin"  # Administrative access
    CUSTOMER_SUPPORT = "customer_support"  # Customer service team
    STATION_MANAGER = "station_manager"  # Station-specific operations
    # Note: Regular customers don't have accounts - they book as guests


class Settings(BaseSettings):
    """Application settings with type validation"""

    model_config = SettingsConfigDict(
        env_file=str(env_path),  # Use the calculated path
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "My Hibachi Chef CRM"
    DEBUG: bool = False
    ENVIRONMENT: Environment = Environment.PRODUCTION
    API_VERSION: str = "1.0.0"

    # Development Mode - Auto Super Admin
    DEV_MODE: bool = False
    DEV_SUPER_ADMIN_EMAIL: str | None = None
    DEV_SUPER_ADMIN_TOKEN: str | None = None

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str  # REQUIRED: Must come from .env
    DATABASE_URL_SYNC: str | None = None
    SQLITE_URL: str | None = None
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_ECHO: bool = False

    # Redis
    REDIS_URL: str  # REQUIRED: Must come from .env

    # Security
    SECRET_KEY: str  # REQUIRED: Must come from .env (32+ chars)
    JWT_SECRET: str | None = None
    ENCRYPTION_KEY: str  # REQUIRED: Must come from .env (32+ chars)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS - Multi-Domain Configuration (PRODUCTION)
    CORS_ORIGINS: str = "https://myhibachichef.com,https://admin.mysticdatanode.net"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # RingCentral - REQUIRED: Must come from .env
    RC_CLIENT_ID: str
    RC_CLIENT_SECRET: str
    RC_JWT_TOKEN: str
    RC_WEBHOOK_SECRET: str
    RC_SMS_FROM: str = "+19167408768"  # Public business phone
    RC_SERVER_URL: str = "https://platform.ringcentral.com"

    # OpenAI - REQUIRED: Must come from .env
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_REALTIME_MODEL: str = "gpt-4o-realtime-preview-2024-12-17"

    # Stripe - REQUIRED: Must come from .env
    STRIPE_SECRET_KEY: str
    STRIPE_PUBLISHABLE_KEY: str
    STRIPE_WEBHOOK_SECRET: str

    # Meta (Facebook/Instagram) - REQUIRED: Must come from .env
    META_APP_ID: str
    META_APP_SECRET: str
    META_VERIFY_TOKEN: str
    META_PAGE_ACCESS_TOKEN: str

    # Google Business - REQUIRED: Must come from .env
    GOOGLE_CLOUD_PROJECT: str
    GOOGLE_CREDENTIALS_JSON: str
    GBP_ACCOUNT_ID: str
    GBP_LOCATION_ID: str

    # Google OAuth - For admin panel authentication (optional in dev/test)
    GOOGLE_CLIENT_ID: str | None = "test-google-client-id"
    GOOGLE_CLIENT_SECRET: str | None = "test-google-client-secret"
    GOOGLE_REDIRECT_URI: str | None = "http://localhost:3001/auth/google/callback"

    # Frontend URLs
    FRONTEND_URL: str = "http://localhost:3001"
    ADMIN_URL: str = "http://localhost:3001"

    # Cloudinary (Image Upload) - REQUIRED: Must come from .env
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    # Business Info (PUBLIC SAFE DATA ONLY)
    BUSINESS_NAME: str = "my Hibachi LLC"
    BUSINESS_EMAIL: str = "cs@myhibachichef.com"
    BUSINESS_PHONE: str = "+19167408768"
    BUSINESS_CITY: str = "Fremont"
    BUSINESS_STATE: str = "California"
    SERVICE_AREAS: str = "Sacramento, Bay Area, Central Valley"

    # Email Configuration (IONOS) - SMTP_PASSWORD REQUIRED from .env
    EMAIL_ENABLED: bool = True
    EMAIL_PROVIDER: str = "smtp"
    SMTP_HOST: str = "smtp.ionos.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "cs@myhibachichef.com"  # Public business email
    SMTP_PASSWORD: str  # REQUIRED: Must come from .env (never hardcode!)
    SMTP_USE_TLS: bool = True
    FROM_EMAIL: str = "cs@myhibachichef.com"  # Public business email
    EMAILS_FROM_NAME: str = "My Hibachi Chef"
    EMAIL_TIMEOUT: int = 30

    # Gmail Configuration (for payment email monitoring)
    GMAIL_USER: str | None = None
    GMAIL_APP_PASSWORD: str | None = None
    GMAIL_APP_PASSWORD_IMAP: str | None = None
    PAYMENT_EMAIL_CHECK_INTERVAL_MINUTES: int = 5
    # Enabled with imapclient library for reliability
    PAYMENT_EMAIL_USE_IMAP_IDLE: bool = True

    # Backwards-compatibility aliases (legacy lowercase accessors)
    @property
    def database_url(self) -> str:
        return self.DATABASE_URL

    @property
    def database_url_sync(self) -> str | None:
        return self.DATABASE_URL_SYNC or os.getenv("DATABASE_URL_SYNC")

    @property
    def sqlite_url(self) -> str | None:
        return self.SQLITE_URL

    @property
    def debug(self) -> bool:
        return bool(self.DEBUG)

    @property
    def secret_key(self) -> str:
        return self.SECRET_KEY

    @property
    def jwt_secret(self) -> str | None:
        return self.JWT_SECRET

    # SMTP lowercase aliases
    @property
    def smtp_host(self) -> str:
        return self.SMTP_HOST

    @property
    def smtp_port(self) -> int:
        return self.SMTP_PORT

    @property
    def smtp_user(self) -> str:
        return self.SMTP_USER

    @property
    def smtp_password(self) -> str:
        return self.SMTP_PASSWORD

    @property
    def smtp_use_tls(self) -> bool:
        return self.SMTP_USE_TLS

    # Additional lowercase compatibility properties
    @property
    def workers_enabled(self) -> bool:
        return self.WORKERS_ENABLED

    @property
    def worker_batch_size(self) -> int:
        return self.WORKER_BATCH_SIZE

    @property
    def worker_poll_interval(self) -> int:
        return self.WORKER_POLL_INTERVAL

    @property
    def worker_max_retries(self) -> int:
        return self.WORKER_MAX_RETRIES

    @property
    def sms_worker_max_retries(self) -> int:
        return self.SMS_WORKER_MAX_RETRIES

    @property
    def sms_worker_batch_size(self) -> int:
        return self.SMS_WORKER_BATCH_SIZE

    @property
    def email_worker_max_retries(self) -> int:
        return self.EMAIL_WORKER_MAX_RETRIES

    @property
    def email_worker_batch_size(self) -> int:
        return self.EMAIL_WORKER_BATCH_SIZE

    @property
    def stripe_worker_max_retries(self) -> int:
        return self.STRIPE_WORKER_MAX_RETRIES

    @property
    def stripe_worker_batch_size(self) -> int:
        return self.STRIPE_WORKER_BATCH_SIZE

    @property
    def ringcentral_enabled(self) -> bool:
        return bool(self.RC_CLIENT_ID and self.RC_CLIENT_SECRET)

    @property
    def ringcentral_server_url(self) -> str:
        return self.RC_SERVER_URL

    @property
    def ringcentral_client_id(self) -> str:
        return self.RC_CLIENT_ID

    @property
    def ringcentral_client_secret(self) -> str:
        return self.RC_CLIENT_SECRET

    @property
    def ringcentral_username(self) -> str:
        return ""  # Not used in current config

    @property
    def ringcentral_password(self) -> str:
        return ""  # Not used in current config

    @property
    def ringcentral_from_number(self) -> str:
        return self.RC_SMS_FROM

    @property
    def ringcentral_jwt_token(self) -> str:
        return self.RC_JWT_TOKEN

    @property
    def ringcentral_phone_number(self) -> str:
        return self.RC_SMS_FROM

    @property
    def ringcentral_webhook_secret(self) -> str:
        return self.RC_WEBHOOK_SECRET

    @property
    def ringcentral_sandbox(self) -> bool:
        return self.ENVIRONMENT == Environment.DEVELOPMENT

    @property
    def email_enabled(self) -> bool:
        return self.EMAIL_ENABLED

    @property
    def openai_api_key(self) -> str:
        """Lowercase alias for OPENAI_API_KEY"""
        return self.OPENAI_API_KEY

    @property
    def openai_model(self) -> str:
        """Lowercase alias for OPENAI_MODEL"""
        return self.OPENAI_MODEL

    @property
    def ollama_base_url(self) -> str:
        """Lowercase alias for OLLAMA_BASE_URL"""
        return self.OLLAMA_BASE_URL

    @property
    def ollama_model_name(self) -> str:
        """Lowercase alias for OLLAMA_MODEL_NAME"""
        return self.OLLAMA_MODEL_NAME

    @property
    def stripe_publishable_key(self) -> str:
        """Lowercase alias for STRIPE_PUBLISHABLE_KEY"""
        return self.STRIPE_PUBLISHABLE_KEY

    @property
    def stripe_webhook_secret(self) -> str:
        """Lowercase alias for STRIPE_WEBHOOK_SECRET"""
        return self.STRIPE_WEBHOOK_SECRET

    @property
    def email_provider(self) -> str:
        return self.EMAIL_PROVIDER

    @property
    def from_email(self) -> str:
        return self.FROM_EMAIL

    @property
    def sendgrid_api_key(self) -> str:
        return ""  # Not configured yet

    @property
    def aws_region(self) -> str:
        return "us-east-1"

    @property
    def aws_access_key_id(self) -> str:
        return ""  # Not configured yet

    @property
    def aws_secret_access_key(self) -> str:
        return ""  # Not configured yet

    @property
    def stripe_enabled(self) -> bool:
        return bool(self.STRIPE_SECRET_KEY)

    @property
    def stripe_secret_key(self) -> str:
        return self.STRIPE_SECRET_KEY

    def get_worker_configs(self) -> dict:
        """Get worker configuration dictionary for backward compatibility."""
        return {
            "workers_enabled": self.workers_enabled,
            "worker_batch_size": self.worker_batch_size,
            "worker_poll_interval": self.worker_poll_interval,
            "worker_max_retries": self.worker_max_retries,
            "ringcentral": {
                "enabled": self.ringcentral_enabled,
                "server_url": self.ringcentral_server_url,
                "client_id": self.ringcentral_client_id,
                "client_secret": self.ringcentral_client_secret,
                "username": self.ringcentral_username,
                "password": self.ringcentral_password,
                "from_number": self.ringcentral_from_number,
                "jwt_token": self.ringcentral_jwt_token,
                "phone_number": self.ringcentral_phone_number,
                "webhook_secret": self.ringcentral_webhook_secret,
                "sandbox": self.ringcentral_sandbox,
            },
            "email": {
                "enabled": self.email_enabled,
                "provider": self.email_provider,
                "smtp_host": self.smtp_host,
                "smtp_port": self.smtp_port,
                "smtp_username": self.smtp_user,
                "smtp_password": self.smtp_password,
                "from_email": self.from_email,
                "sendgrid_api_key": self.sendgrid_api_key,
                "aws_region": self.aws_region,
                "aws_access_key_id": self.aws_access_key_id,
                "aws_secret_access_key": self.aws_secret_access_key,
            },
            "stripe": {
                "enabled": self.stripe_enabled,
                "secret_key": self.stripe_secret_key,
            },
            "sms_worker": {
                "max_retries": self.sms_worker_max_retries,
                "batch_size": self.sms_worker_batch_size,
            },
            "email_worker": {
                "max_retries": self.email_worker_max_retries,
                "batch_size": self.email_worker_batch_size,
            },
            "stripe_worker": {
                "max_retries": self.stripe_worker_max_retries,
                "batch_size": self.stripe_worker_batch_size,
            },
        }

    # Customer Review System
    CUSTOMER_APP_URL: str = "http://localhost:3000"
    YELP_REVIEW_URL: str = "https://www.yelp.com/biz/my-hibachi-chef"
    GOOGLE_REVIEW_URL: str = "https://g.page/r/YOUR_GOOGLE_PLACE_ID/review"
    REVIEW_COUPON_DISCOUNT_PERCENTAGE: int = 10
    REVIEW_COUPON_VALIDITY_DAYS: int = 90
    REVIEW_COUPON_MINIMUM_ORDER_CENTS: int = 5000

    # Alternative Payment Options
    ZELLE_EMAIL: str = "myhibachichef@gmail.com"
    ZELLE_PHONE: str = "+19167408768"
    VENMO_USERNAME: str = "@myhibachichef"

    # Worker Configuration
    WORKERS_ENABLED: bool = False
    WORKER_BATCH_SIZE: int = 10
    WORKER_POLL_INTERVAL: int = 5
    WORKER_MAX_RETRIES: int = 5
    WORKER_INITIAL_DELAY: int = 1
    WORKER_MAX_DELAY: int = 300

    # SMS Worker
    SMS_WORKER_ENABLED: bool = False
    SMS_WORKER_MAX_RETRIES: int = 5
    SMS_WORKER_BATCH_SIZE: int = 10

    # Email Worker
    EMAIL_WORKER_ENABLED: bool = False
    EMAIL_WORKER_MAX_RETRIES: int = 3
    EMAIL_WORKER_BATCH_SIZE: int = 20

    # Stripe Worker
    STRIPE_WORKER_ENABLED: bool = False
    STRIPE_WORKER_MAX_RETRIES: int = 3
    STRIPE_WORKER_BATCH_SIZE: int = 5

    # Feature Flags
    ENABLE_STRIPE_CONNECT: bool = False
    ENABLE_AUTOMATIC_TAX: bool = False
    ENABLE_SUBSCRIPTIONS: bool = False
    ENABLE_WEBSOCKETS: bool = True
    ENABLE_RATE_LIMITING: bool = True
    ENABLE_AUDIT_LOGGING: bool = True
    ENABLE_FIELD_ENCRYPTION: bool = True

    # AI Settings
    ENABLE_AI_AUTO_REPLY: bool = True
    AI_CONFIDENCE_THRESHOLD: int = 80
    SOCIAL_AI_ENABLED: bool = True
    SOCIAL_AUTO_REPLY_ENABLED: bool = False
    SOCIAL_SENTIMENT_THRESHOLD: float = 0.3
    SOCIAL_RESPONSE_DELAY_MINUTES: int = 2

    # Shadow Learning - Ollama/Llama-3 Integration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL_NAME: str = "llama3"
    OLLAMA_TIMEOUT_SECONDS: int = 60
    OLLAMA_MAX_TOKENS: int = 500
    OLLAMA_TEMPERATURE: float = 0.7

    # Shadow Learning Control
    SHADOW_LEARNING_ENABLED: bool = True  # Always collecting data
    # 1.0 = 100% of requests (reduce in production)
    SHADOW_LEARNING_SAMPLE_RATE: float = 1.0

    # Local AI Activation Mode
    # "shadow" = Learning only, customers see OpenAI
    # "active" = Production use based on confidence
    LOCAL_AI_MODE: str = "shadow"

    # Quality Thresholds (for readiness assessment)
    # Threshold for high-quality training pairs
    SHADOW_MIN_SIMILARITY_SCORE: float = 0.85
    # Minimum pairs before fine-tuning export
    SHADOW_EXPORT_MIN_PAIRS: int = 100
    # Minimum confidence to use local model (when active)
    LOCAL_AI_MIN_CONFIDENCE: float = 0.75

    # Intent-Specific Readiness Thresholds
    READINESS_FAQ_MIN_PAIRS: int = 50
    READINESS_FAQ_MIN_SIMILARITY: float = 0.80
    READINESS_QUOTE_MIN_PAIRS: int = 100
    READINESS_QUOTE_MIN_SIMILARITY: float = 0.85
    READINESS_BOOKING_MIN_PAIRS: int = 200
    READINESS_BOOKING_MIN_SIMILARITY: float = 0.90

    # ML Confidence Predictor Settings
    ML_PREDICTOR_ENABLED: bool = True
    ML_PREDICTOR_MIN_TRAINING_SAMPLES: int = 100
    ML_PREDICTOR_RETRAIN_INTERVAL_HOURS: int = 24

    # Quality Monitoring & Auto-Rollback
    QUALITY_MONITOR_ENABLED: bool = True
    QUALITY_DEGRADATION_THRESHOLD: float = 0.10  # 10% drop triggers alert
    AUTO_ROLLBACK_ENABLED: bool = True  # Auto switch to OpenAI if quality drops

    # Business Rules
    QUIET_HOURS_START: int = 21
    QUIET_HOURS_END: int = 8
    DEFAULT_TIMEZONE: str = "America/Los_Angeles"
    MAX_SMS_PER_THREAD: int = 3

    # Rate Limiting Configuration (ADMIN-OPTIMIZED)
    # Note: Burst limits for future token bucket algorithm
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

    # Backward Compatibility Aliases (for api/app/* code)
    # These provide lowercase aliases for uppercase env vars

    # Pydantic Validators for Critical Environment Variables
    # ruff: noqa: N805 - cls is correct for Pydantic validators

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Ensure SECRET_KEY is at least 32 characters for security"""
        if len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters long " "for cryptographic security"
            )
        return v

    @field_validator("ENCRYPTION_KEY")
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        """Ensure ENCRYPTION_KEY is at least 32 characters"""
        if len(v) < 32:
            raise ValueError(
                "ENCRYPTION_KEY must be at least 32 characters long " "for proper encryption"
            )
        return v

    @field_validator("STRIPE_SECRET_KEY")
    @classmethod
    def validate_stripe_secret_key(cls, v: str) -> str:
        """Validate Stripe secret key format"""
        if not v.startswith(("sk_test_", "sk_live_")):
            raise ValueError(
                "STRIPE_SECRET_KEY must start with sk_test_ "
                "(development) or sk_live_ (production)"
            )
        return v

    @field_validator("STRIPE_WEBHOOK_SECRET")
    @classmethod
    def validate_stripe_webhook_secret(cls, v: str) -> str:
        """Validate Stripe webhook secret format"""
        # Allow test/dev placeholders for local development
        if v in ["whsec_test_example", "whsec_local_dev"]:
            return v
        # Production webhook secrets must start with whsec_
        if not v.startswith("whsec_"):
            raise ValueError(
                "STRIPE_WEBHOOK_SECRET must start with whsec_ " "(Stripe webhook signing secret)"
            )
        return v

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format (PostgreSQL or SQLite)"""
        if not v.startswith(("postgresql", "sqlite")):
            raise ValueError(
                "DATABASE_URL must be a valid database connection "
                "string (postgresql:// or sqlite://)"
            )
        return v

    @field_validator("REDIS_URL")
    @classmethod
    def validate_redis_url(cls, v: str) -> str:
        """Validate Redis URL format"""
        if not v.startswith("redis://"):
            raise ValueError(
                "REDIS_URL must be a valid Redis connection " "string starting with redis://"
            )
        return v

    def get_rate_limit_for_user(self, user_role: UserRole | None = None) -> dict:
        """Get rate limit configuration based on user role"""
        if user_role in [UserRole.SUPER_ADMIN]:
            return {
                "per_minute": self.RATE_LIMIT_ADMIN_SUPER_PER_MINUTE,
                "per_hour": self.RATE_LIMIT_ADMIN_SUPER_PER_HOUR,
                "burst": self.RATE_LIMIT_ADMIN_SUPER_BURST,
                "tier": "admin_super",
            }
        elif user_role in [UserRole.ADMIN, UserRole.STATION_MANAGER]:
            return {
                "per_minute": self.RATE_LIMIT_ADMIN_PER_MINUTE,
                "per_hour": self.RATE_LIMIT_ADMIN_PER_HOUR,
                "burst": self.RATE_LIMIT_ADMIN_BURST,
                "tier": "admin",
            }
        else:
            return {
                "per_minute": self.RATE_LIMIT_PUBLIC_PER_MINUTE,
                "per_hour": self.RATE_LIMIT_PUBLIC_PER_HOUR,
                "burst": self.RATE_LIMIT_PUBLIC_BURST,
                "tier": "public",
            }

    def get_ai_rate_limit(self) -> dict:
        """Get AI-specific rate limits (same for all users due to cost)"""
        return {
            "per_minute": self.RATE_LIMIT_AI_PER_MINUTE,
            "per_hour": self.RATE_LIMIT_AI_PER_HOUR,
            "burst": self.RATE_LIMIT_AI_BURST,
            "tier": "ai",
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
