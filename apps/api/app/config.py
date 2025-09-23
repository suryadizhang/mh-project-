from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Core Configuration
    app_name: str = "MyHibachi Backend API"
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
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    bcrypt_rounds: int = 12
    
    # Default admin credentials (only for initial setup)
    default_admin_email: str = "admin@myhibachi.com"
    default_admin_password: str = "ChangeThisPassword123!"

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60

    # Monitoring & Metrics
    enable_metrics: bool = True
    metrics_port: int = 8001
    prometheus_multiproc_dir: str = "/tmp/prometheus_multiproc_dir"

    # CORS Configuration
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173", 
        "http://localhost:3001",
        "https://myhibachichef.com",
        "https://admin.myhibachichef.com"
    ]
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:3001", 
        "https://myhibachichef.com",
        "https://admin.myhibachichef.com"
    ]

    # Email Configuration (SMTP)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    emails_from_email: str = "no-reply@myhibachichef.com"
    email_user: str = ""
    email_pass: str = ""
    from_email: str = "myhibachichef@gmail.com"
    disable_email: bool = False

    # Stripe Payment Configuration
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

    # Testing Configuration
    testing: bool = False
    test_database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/myhibachi_ci"

    # Monitoring & Health
    api_health_url: str = "http://127.0.0.1:8000/health"
    enable_health_checks: bool = True
    backup_dir: str = "/var/backups/myhibachi"

    # Rate Limiting Configuration
    rate_limit_enabled: bool = True
    rate_limit_booking: str = "5/minute"
    rate_limit_waitlist: str = "10/minute"
    rate_limit_general: str = "100/minute"

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
