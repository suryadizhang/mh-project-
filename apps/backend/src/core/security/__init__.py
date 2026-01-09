"""
Security Module
===============

Comprehensive security utilities for the My Hibachi backend.

This module has been modularized from a single 1,085-line file into focused submodules:
- config.py: Security configuration constants
- password.py: Password hashing (bcrypt)
- tokens.py: JWT token management
- encryption.py: Field-level encryption (Fernet)
- api_keys.py: API key generation/verification
- validation.py: Input sanitization and validation
- roles.py: Role-based access control utilities
- request_utils.py: HTTP request utilities
- middleware.py: Security middleware classes
- audit.py: Security event logging
- dependencies.py: FastAPI authentication dependencies
- setup.py: Middleware setup functions

Usage (backwards compatible):
    from core.security import (
        verify_password,
        get_password_hash,
        create_access_token,
        verify_token,
        encrypt_pii,
        decrypt_pii,
        setup_security_middleware,
    )

See: .github/instructions/22-QUALITY_CONTROL.instructions.md for modularization standards
"""

# Configuration
from .config import SecurityConfig

# Password hashing
from .password import (
    verify_password,
    get_password_hash,
    hash_password,
    hash_password_bcrypt,
    verify_password_bcrypt,
)

# JWT tokens
from .tokens import (
    create_access_token,
    create_refresh_token,
    verify_token,
    verify_refresh_token,
    extract_user_from_token,
    decode_access_token,
)

# Encryption
from .encryption import (
    get_fernet_key,
    encrypt_pii,
    decrypt_pii,
    fernet,
    FieldEncryption,
    field_encryption,
)

# API keys
from .api_keys import (
    generate_api_key,
    hash_api_key,
    verify_api_key,
    generate_secure_token,
)

# Validation
from .validation import (
    sanitize_input,
    validate_email,
    is_safe_url,
    is_trusted_network,
    contains_dangerous_patterns,
    constant_time_compare,
    sanitize_business_data,
    get_public_business_info,
)

# Roles
from .roles import (
    get_user_rate_limit_tier,
    is_admin_user,
    is_super_admin,
)

# Request utilities
from .request_utils import (
    get_client_ip,
    get_endpoint_pattern,
)

# Middleware
from .middleware import (
    SecurityHeadersMiddleware,
    RateLimitByIPMiddleware,
    InputValidationMiddleware,
    RequestLoggingMiddleware,
    MetricsMiddleware,
    WebhookSecurityMiddleware,
)

# Audit
from .audit import (
    AuditLogger,
    audit_logger,
)

# Dependencies
from .dependencies import (
    security,
    get_current_user,
    require_auth,
    require_admin,
    require_super_admin,
    require_https,
)

# Setup
from .setup import (
    setup_security_middleware,
    get_security_config,
)


# Complete exports for backwards compatibility
__all__ = [
    # Config
    "SecurityConfig",
    # Password
    "verify_password",
    "get_password_hash",
    "hash_password",
    "hash_password_bcrypt",
    "verify_password_bcrypt",
    # Tokens
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "verify_refresh_token",
    "extract_user_from_token",
    "decode_access_token",
    # Encryption
    "get_fernet_key",
    "encrypt_pii",
    "decrypt_pii",
    "fernet",
    "FieldEncryption",
    "field_encryption",
    # API Keys
    "generate_api_key",
    "hash_api_key",
    "verify_api_key",
    "generate_secure_token",
    # Validation
    "sanitize_input",
    "validate_email",
    "is_safe_url",
    "is_trusted_network",
    "contains_dangerous_patterns",
    "constant_time_compare",
    "sanitize_business_data",
    "get_public_business_info",
    # Roles
    "get_user_rate_limit_tier",
    "is_admin_user",
    "is_super_admin",
    # Request Utils
    "get_client_ip",
    "get_endpoint_pattern",
    # Middleware
    "SecurityHeadersMiddleware",
    "RateLimitByIPMiddleware",
    "InputValidationMiddleware",
    "RequestLoggingMiddleware",
    "MetricsMiddleware",
    "WebhookSecurityMiddleware",
    # Audit
    "AuditLogger",
    "audit_logger",
    # Dependencies
    "security",
    "get_current_user",
    "require_auth",
    "require_admin",
    "require_super_admin",
    "require_https",
    # Setup
    "setup_security_middleware",
    "get_security_config",
]
