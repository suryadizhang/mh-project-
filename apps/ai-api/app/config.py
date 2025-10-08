"""
Configuration Management for AI API
Handles environment-specific configuration with validation and security
"""

import os
from typing import Optional, List, Dict, Any
from functools import lru_cache
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class AIAPISettings:
    """Configuration settings for AI API with validation"""
    
    def __init__(self):
        # Application Settings
        self.app_name = os.getenv("APP_NAME", "MyHibachi AI API")
        self.app_env = os.getenv("APP_ENV", "development")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        
        # Server Settings
        self.api_port = int(os.getenv("API_PORT", "8002"))
        self.api_host = os.getenv("API_HOST", "0.0.0.0")
        self.reload = os.getenv("RELOAD", "false").lower() == "true"
        
        # Database Configuration
        self.database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./ai_chat.db")
        self.database_pool_size = int(os.getenv("DATABASE_POOL_SIZE", "10"))
        self.database_max_overflow = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
        
        # OpenAI Configuration
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4")
        self.openai_max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "500"))
        self.openai_temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
        
        # Security Configuration
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY")
        self.webhook_secret = os.getenv("WEBHOOK_SECRET")
        self.cors_origins = self._parse_cors_origins(os.getenv("CORS_ORIGINS", "*"))
        
        # Rate Limiting
        self.rate_limit_requests = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
        self.rate_limit_period = int(os.getenv("RATE_LIMIT_PERIOD", "60"))
        self.rate_limit_enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
        
        # Chat Configuration
        self.max_conversation_length = int(os.getenv("MAX_CONVERSATION_LENGTH", "10"))
        self.confidence_high_threshold = float(os.getenv("CONFIDENCE_HIGH_THRESHOLD", "0.80"))
        self.confidence_medium_threshold = float(os.getenv("CONFIDENCE_MEDIUM_THRESHOLD", "0.50"))
        self.confidence_low_threshold = float(os.getenv("CONFIDENCE_LOW_THRESHOLD", "0.30"))
        
        # Feature Flags
        self.enable_conversation_memory = os.getenv("ENABLE_CONVERSATION_MEMORY", "true").lower() == "true"
        self.enable_menu_recommendations = os.getenv("ENABLE_MENU_RECOMMENDATIONS", "true").lower() == "true"
        self.enable_human_escalation = os.getenv("FEATURE_FLAG_HUMAN_ESCALATION", "true").lower() == "true"
        self.enable_self_learning = os.getenv("ENABLE_SELF_LEARNING", "true").lower() == "true"
        self.enable_websockets = os.getenv("ENABLE_WEBSOCKETS", "true").lower() == "true"
        
        # External Services
        self.ringcentral_enabled = os.getenv("RINGCENTRAL_ENABLED", "false").lower() == "true"
        self.ringcentral_client_id = os.getenv("RINGCENTRAL_CLIENT_ID")
        self.ringcentral_client_secret = os.getenv("RINGCENTRAL_CLIENT_SECRET")
        self.ringcentral_server_url = os.getenv("RINGCENTRAL_SERVER_URL", "https://platform.ringcentral.com")
        
        self.meta_app_id = os.getenv("META_APP_ID")
        self.meta_app_secret = os.getenv("META_APP_SECRET")
        self.meta_verify_token = os.getenv("META_VERIFY_TOKEN", "myhibachi_verify_2024")
        
        # Redis Configuration
        self.redis_url = os.getenv("REDIS_URL")
        self.redis_enabled = os.getenv("REDIS_ENABLED", "false").lower() == "true"
        
        # Monitoring
        self.metrics_enabled = os.getenv("METRICS_ENABLED", "true").lower() == "true"
        self.sentry_dsn = os.getenv("SENTRY_DSN")
        
        # Validate configuration
        self._validate()
    
    def _parse_cors_origins(self, cors_string: str) -> List[str]:
        """Parse CORS origins from environment variable"""
        if cors_string == "*":
            return ["*"]
        return [origin.strip() for origin in cors_string.split(",") if origin.strip()]
    
    def _validate(self):
        """Validate configuration"""
        # Validate environment
        valid_envs = ["development", "staging", "production"]
        if self.app_env not in valid_envs:
            raise ValueError(f"app_env must be one of {valid_envs}")
        
        # Validate log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        
        # Production-specific validations
        if self.app_env == "production":
            if not self.jwt_secret_key:
                logger.warning("JWT secret key not configured for production")
            elif len(self.jwt_secret_key) < 32:
                logger.warning("JWT secret key should be at least 32 characters for production")
            
            if not self.openai_api_key:
                logger.warning("OpenAI API key not configured for production")
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database connection configuration"""
        return {
            "url": self.database_url,
            "pool_size": self.database_pool_size,
            "max_overflow": self.database_max_overflow,
            "echo": self.debug and self.app_env == "development"
        }
    
    def get_openai_config(self) -> Dict[str, Any]:
        """Get OpenAI API configuration"""
        if not self.openai_api_key:
            return {"enabled": False}
        
        return {
            "enabled": True,
            "api_key": self.openai_api_key,
            "model": self.openai_model,
            "max_tokens": self.openai_max_tokens,
            "temperature": self.openai_temperature
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration"""
        return {
            "jwt_secret": self.jwt_secret_key,
            "webhook_secret": self.webhook_secret,
            "cors_origins": self.cors_origins,
            "rate_limit_enabled": self.rate_limit_enabled,
            "rate_limit_requests": self.rate_limit_requests,
            "rate_limit_period": self.rate_limit_period,
            "production_mode": self.app_env == "production"
        }
    
    def get_external_services_config(self) -> Dict[str, Any]:
        """Get external services configuration"""
        return {
            "ringcentral": {
                "enabled": self.ringcentral_enabled,
                "client_id": self.ringcentral_client_id,
                "client_secret": self.ringcentral_client_secret,
                "server_url": self.ringcentral_server_url
            },
            "meta": {
                "app_id": self.meta_app_id,
                "app_secret": self.meta_app_secret,
                "verify_token": self.meta_verify_token
            },
            "redis": {
                "enabled": self.redis_enabled,
                "url": self.redis_url
            }
        }
    
    def get_feature_flags(self) -> Dict[str, bool]:
        """Get feature flags configuration"""
        return {
            "conversation_memory": self.enable_conversation_memory,
            "menu_recommendations": self.enable_menu_recommendations,
            "human_escalation": self.enable_human_escalation,
            "self_learning": self.enable_self_learning,
            "websockets": self.enable_websockets,
            "metrics": self.metrics_enabled
        }
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.app_env == "production"
    
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.app_env == "development"


@lru_cache()
def get_settings() -> AIAPISettings:
    """Get cached settings instance"""
    return AIAPISettings()


def validate_configuration():
    """Validate configuration and log warnings/errors"""
    settings = get_settings()
    
    logger.info(f"AI API Configuration loaded for {settings.app_env} environment")
    
    # Production-specific validations
    if settings.is_production():
        issues = []
        
        if not settings.openai_api_key:
            issues.append("OpenAI API key not configured")
        
        if not settings.jwt_secret_key:
            issues.append("JWT secret key not configured")
        
        if settings.cors_origins == ["*"]:
            issues.append("CORS origins set to wildcard in production")
        
        if not settings.webhook_secret:
            issues.append("Webhook secret not configured")
        
        if issues:
            logger.error(f"Production configuration issues: {', '.join(issues)}")
            # Only log warnings, don't fail startup
        else:
            logger.info("Production configuration validated successfully")
    
    # Development warnings
    elif settings.is_development():
        if not settings.openai_api_key:
            logger.warning("OpenAI API key not configured - AI features will be limited")
        
        if settings.cors_origins == ["*"]:
            logger.info("CORS origins set to wildcard (OK for development)")
    
    # Log enabled features
    features = settings.get_feature_flags()
    enabled_features = [name for name, enabled in features.items() if enabled]
    logger.info(f"Enabled features: {', '.join(enabled_features)}")
    
    return settings