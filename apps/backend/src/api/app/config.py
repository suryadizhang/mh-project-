from typing import Any

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Core Configuration
    app_name: str = "MyHibachi CRM API"
    environment: str = "development"
    log_level: str = "info"
    port: int = 8000
    debug: bool = True

    # Database Configuration
    # PostgreSQL for production
    database_url: str
    database_url_sync: str
    # SQLite for development/testing (compatibility with source backend)
    sqlite_url: str = "sqlite:///./mh-bookings.db"

    # Security & Authentication
    secret_key: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30
    bcrypt_rounds: int = 12

    # OAuth 2.1 + OIDC Configuration
    oauth_issuer: str = "https://auth.myhibachi.com"
    oauth_audience: str = "myhibachi-api"
    oidc_discovery_url: str = ""

    # MFA Configuration
    totp_issuer: str = "MyHibachi"
    mfa_backup_codes_count: int = 10

    # Default admin credentials (only for initial setup)
    default_admin_email: str = "admin@myhibachi.com"
    default_admin_password: str = "ChangeThisPassword123!"

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60

    # Rate Limiting Configuration
    rate_limit_booking: str = "10/minute"
    rate_limit_waitlist: str = "10/minute"
    rate_limit_general: str = "100/minute"
    rate_limit_auth: str = "5/minute"
    rate_limit_sms: str = "30/minute"

    # Monitoring & Metrics
    enable_metrics: bool = True
    metrics_port: int = 8001
    prometheus_multiproc_dir: str = "/tmp/prometheus_multiproc_dir"
    
    # Sentry Configuration
    sentry_dsn: str = ""
    sentry_environment: str = ""  # Will use environment if not set
    sentry_traces_sample_rate: float = 0.1  # 10% of transactions
    sentry_profiles_sample_rate: float = 0.1  # 10% profiling

    # CORS Configuration
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:3001",
        "https://myhibachichef.com",
        "https://admin.myhibachichef.com"
    ]
    allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:3001",
        "https://myhibachichef.com",
        "https://admin.myhibachichef.com"
    ]

    # Email Configuration
    email_enabled: bool = True
    email_provider: str = "smtp"  # smtp, sendgrid, ses

    # SMTP Configuration
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True

    # SendGrid Configuration
    sendgrid_api_key: str = ""

    # AWS SES Configuration
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    # Email Settings
    emails_from_email: str = "no-reply@myhibachichef.com"
    from_email: str = "myhibachichef@gmail.com"
    disable_email: bool = False

    # RingCentral SMS Configuration
    ringcentral_enabled: bool = False
    ringcentral_server_url: str = "https://platform.ringcentral.com"
    ringcentral_client_id: str = ""
    ringcentral_client_secret: str = ""
    ringcentral_username: str = ""
    ringcentral_password: str = ""
    ringcentral_from_number: str = ""
    # Additional fields for our enhanced integration
    ringcentral_jwt_token: str = ""
    ringcentral_phone_number: str = ""
    ringcentral_webhook_secret: str = ""
    ringcentral_sandbox: bool = True

    # Stripe Payment Configuration
    stripe_enabled: bool = True
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_publishable_key: str = ""

    # Application URLs
    app_url: str = "http://localhost:3000"
    api_base_url: str = "http://localhost:8000"
    webhook_path: str = "/api/stripe/webhook"

    # Admin Configuration
    admin_email: str = "admin@myhibachi.com"
    admin_phone: str = "+19167408768"

    # Alternative Payment Options
    zelle_email: str = "myhibachichef@gmail.com"
    zelle_phone: str = "+19167408768"
    venmo_username: str = "@myhibachichef"
    cashapp_username: str = "$myhibachichef"

    # Feature Flags
    enable_stripe_connect: bool = False
    enable_automatic_tax: bool = False
    enable_subscriptions: bool = False
    enable_websockets: bool = True
    enable_rate_limiting: bool = True
    enable_audit_logging: bool = True
    enable_field_encryption: bool = True

    # Worker Configuration
    workers_enabled: bool = True
    worker_batch_size: int = 10
    worker_poll_interval: int = 5
    worker_max_retries: int = 5
    worker_initial_delay: int = 1
    worker_max_delay: int = 300

    # SMS Worker Configuration
    sms_worker_enabled: bool = True
    sms_worker_max_retries: int = 5
    sms_worker_batch_size: int = 10

    # Email Worker Configuration
    email_worker_enabled: bool = True
    email_worker_max_retries: int = 3
    email_worker_batch_size: int = 20

    # Stripe Worker Configuration
    stripe_worker_enabled: bool = True
    stripe_worker_max_retries: int = 3
    stripe_worker_batch_size: int = 5

    # Testing Configuration
    testing: bool = False
    test_database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/myhibachi_ci"

    # Monitoring & Health
    api_health_url: str = "http://127.0.0.1:8000/health"
    enable_health_checks: bool = True
    backup_dir: str = "/var/backups/myhibachi"

    # Business Configuration
    restaurant_name: str = "MyHibachi"
    restaurant_phone: str = "+19167408768"
    restaurant_email: str = "info@myhibachichef.com"

    # Booking Configuration
    min_advance_booking_hours: int = 4
    max_advance_booking_days: int = 90
    default_event_duration_minutes: int = 180
    base_price_per_person_cents: int = 4500
    deposit_percentage: float = 0.25

    # Available time slots
    available_slots: list[str] = [
        "11:00 AM", "11:30 AM",
        "12:00 PM", "12:30 PM",
        "1:00 PM", "1:30 PM", "2:00 PM", "2:30 PM",
        "3:00 PM", "3:30 PM", "4:00 PM", "4:30 PM",
        "5:00 PM", "5:30 PM", "6:00 PM", "6:30 PM", "7:00 PM"
    ]

    # Encryption Configuration
    field_encryption_key: str = ""  # Base64 encoded 32-byte key
    field_encryption_algorithm: str = "AES-GCM"

    # Social Media Integration Configuration
    # Meta (Instagram/Facebook) Configuration
    meta_app_secret: str = ""
    meta_app_id: str = ""
    meta_access_token: str = ""
    meta_verify_token: str = "myhibachi_social_webhook_verify"

    # Google Business Profile Configuration
    google_service_account_key: str = ""  # Path to service account JSON file
    google_project_id: str = ""
    google_pubsub_topic: str = "social-media-notifications"

    # Yelp Configuration
    yelp_api_key: str = ""
    yelp_business_id: str = ""

    # OpenAI Configuration for AI Responses
    openai_api_key: str = ""
    openai_model: str = "gpt-4"
    openai_max_tokens: int = 500

    # Social Media Settings
    social_ai_enabled: bool = True
    social_auto_reply_enabled: bool = False
    social_sentiment_threshold: float = 0.3  # Below this is considered negative
    social_response_delay_minutes: int = 2  # Minimum delay before AI response

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields in .env

    def get_worker_configs(self) -> dict[str, Any]:
        """Get worker configuration dictionary."""
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
                "sandbox": self.ringcentral_sandbox
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
                "aws_secret_access_key": self.aws_secret_access_key
            },

            "stripe": {
                "enabled": self.stripe_enabled,
                "secret_key": self.stripe_secret_key
            },

            "sms_worker": {
                "max_retries": self.sms_worker_max_retries,
                "batch_size": self.sms_worker_batch_size
            },

            "email_worker": {
                "max_retries": self.email_worker_max_retries,
                "batch_size": self.email_worker_batch_size
            },

            "stripe_worker": {
                "max_retries": self.stripe_worker_max_retries,
                "batch_size": self.stripe_worker_batch_size
            }
        }


# Global settings instance
settings = Settings()
