from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App Configuration
    app_name: str = "My Hibachi API"
    environment: str = "development"
    debug: bool = True

    # Database
    database_url: str
    database_url_sync: str

    # Stripe
    stripe_secret_key: str
    stripe_webhook_secret: str
    stripe_publishable_key: str

    # URLs
    app_url: str = "http://localhost:3000"
    api_base_url: str = "http://localhost:8000"
    webhook_path: str = "/api/stripe/webhook"

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS
    allowed_origins: list[str] = ["http://localhost:3000"]

    # Email (Optional)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = "myhibachichef@gmail.com"

    # Admin
    admin_email: str = "admin@myhibachi.com"
    admin_phone: str = "+19167408768"

    # Payment Methods
    zelle_email: str = "myhibachichef@gmail.com"
    zelle_phone: str = "+19167408768"
    venmo_username: str = "@myhibachichef"

    # Feature Flags
    enable_stripe_connect: bool = False
    enable_automatic_tax: bool = False
    enable_subscriptions: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
