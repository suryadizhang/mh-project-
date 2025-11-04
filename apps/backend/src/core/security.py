"""
Security Module - Consolidated
Unified security utilities: authentication, encryption, middleware, audit logging
Single source of truth for all security functions across MyHibachi backend

Consolidated from:
- core/security.py (base authentication & encryption)
- api/app/security.py (extended utilities)
- api/app/middleware/security.py (middleware classes)
- api/ai/endpoints/security.py (AI API security setup)
"""

import base64
from collections import defaultdict
from collections.abc import Callable
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import hmac
import ipaddress
import logging
import re
import secrets
import time
from typing import Any
import uuid

import bcrypt
from cryptography.fernet import Fernet
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.types import ASGIApp

try:
    import prometheus_client

    PROMETHEUS_AVAILABLE = True

    # Metrics for monitoring
    REQUEST_COUNT = prometheus_client.Counter(
        "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status_code"]
    )
    REQUEST_DURATION = prometheus_client.Histogram(
        "http_request_duration_seconds", "HTTP request duration", ["method", "endpoint"]
    )
    SECURITY_VIOLATIONS = prometheus_client.Counter(
        "security_violations_total", "Security violations detected", ["violation_type"]
    )
except ImportError:
    PROMETHEUS_AVAILABLE = False
    REQUEST_COUNT = None
    REQUEST_DURATION = None
    SECURITY_VIOLATIONS = None

from core.config import UserRole, get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================


class SecurityConfig:
    """Security configuration constants"""

    # CSRF Protection
    CSRF_TOKEN_BYTES = 32
    CSRF_COOKIE_NAME = "csrf_token"
    CSRF_HEADER_NAME = "X-CSRF-Token"

    # Rate Limiting
    DEFAULT_RATE_LIMIT = 100  # requests per minute
    AUTH_RATE_LIMIT = 5  # requests per minute for auth endpoints

    # Security Headers
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data: https://fonts.gstatic.com; "
            "connect-src 'self' ws: wss:; "
            "media-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        ),
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    }

    # Input Validation
    MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_JSON_KEYS = 1000
    MAX_STRING_LENGTH = 10000

    # Trusted Networks (for development)
    TRUSTED_NETWORKS = ["127.0.0.0/8", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]

    # Dangerous patterns for input validation
    DANGEROUS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"eval\s*\(",
        r"expression\s*\(",
        r"--",
        r";.*?--",
        r"union.*?select",
        r"drop\s+table",
    ]

    # Suspicious user agents
    SUSPICIOUS_USER_AGENTS = ["sqlmap", "nikto", "nmap", "masscan", "curl/bot"]


# =============================================================================
# PASSWORD HASHING & AUTHENTICATION
# =============================================================================

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def hash_password_bcrypt(password: str, rounds: int = 12) -> str:
    """Hash password with bcrypt (alternative method)"""
    salt = bcrypt.gensalt(rounds=rounds)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password_bcrypt(password: str, hashed: str) -> bool:
    """Verify password against bcrypt hash"""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


# =============================================================================
# JWT TOKEN MANAGEMENT
# =============================================================================


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def verify_token(token: str) -> dict[str, Any] | None:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        return None


def extract_user_from_token(token: str) -> dict[str, Any] | None:
    """Extract user information from JWT token"""
    payload = verify_token(token)
    if payload:
        user_id: str = payload.get("sub")
        role_str: str = payload.get("role", "customer")
        email: str = payload.get("email")

        if user_id is None:
            return None

        # Safely convert role string to UserRole enum
        try:
            role = UserRole(role_str.lower())
        except (ValueError, AttributeError):
            role = None  # No default role - must be valid staff role

        return {"id": user_id, "email": email, "role": role}
    return None


# =============================================================================
# ENCRYPTION (PII & FIELD-LEVEL)
# =============================================================================


def get_fernet_key() -> Fernet:
    """Get encryption key for PII data"""
    key = settings.ENCRYPTION_KEY.encode()
    if len(key) != 44:  # Fernet key must be 32 bytes base64 encoded (44 chars)
        hashed = hashlib.sha256(key).digest()
        key = base64.urlsafe_b64encode(hashed)
    return Fernet(key)


fernet = get_fernet_key()


def encrypt_pii(data: str) -> str:
    """Encrypt personally identifiable information"""
    if not data:
        return ""

    try:
        encrypted = fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    except Exception as e:
        raise ValueError(f"Encryption failed: {e}")


def decrypt_pii(encrypted_data: str) -> str:
    """Decrypt personally identifiable information"""
    if not encrypted_data:
        return ""

    try:
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted = fernet.decrypt(encrypted_bytes)
        return decrypted.decode()
    except Exception as e:
        raise ValueError(f"Decryption failed: {e}")


class FieldEncryption:
    """Field-level encryption for sensitive data"""

    def __init__(self, key: str | None = None):
        if key:
            self.key = base64.urlsafe_b64decode(key.encode())
        else:
            self.key = Fernet.generate_key()
        self.fernet = Fernet(self.key)

    def encrypt(self, data: str) -> str:
        """Encrypt sensitive field data"""
        if not data:
            return data
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive field data"""
        if not encrypted_data:
            return encrypted_data
        return self.fernet.decrypt(encrypted_data.encode()).decode()

    def encrypt_dict(self, data: dict[str, Any], fields: list[str]) -> dict[str, Any]:
        """Encrypt specific fields in a dictionary"""
        result = data.copy()
        for field in fields:
            if result.get(field):
                result[field] = self.encrypt(str(result[field]))
        return result

    def decrypt_dict(self, data: dict[str, Any], fields: list[str]) -> dict[str, Any]:
        """Decrypt specific fields in a dictionary"""
        result = data.copy()
        for field in fields:
            if result.get(field):
                result[field] = self.decrypt(result[field])
        return result


# Global field encryption instance
field_encryption = FieldEncryption(
    settings.field_encryption_key if hasattr(settings, "field_encryption_key") else None
)

# =============================================================================
# API KEY MANAGEMENT
# =============================================================================


def generate_api_key() -> str:
    """Generate secure API key"""
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """Hash API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify API key against hash"""
    return hash_api_key(plain_key) == hashed_key


def generate_secure_token(length: int = 32) -> str:
    """Generate cryptographically secure random token"""
    return secrets.token_urlsafe(length)


# =============================================================================
# ROLE & PERMISSION CHECKS
# =============================================================================


def get_user_rate_limit_tier(user_role: UserRole | None) -> str:
    """Get rate limit tier based on user role"""
    if user_role == UserRole.SUPER_ADMIN:
        return "admin_super"
    elif user_role in [UserRole.ADMIN, UserRole.STATION_MANAGER]:
        return "admin"
    elif user_role == UserRole.CUSTOMER_SUPPORT:
        return "support"
    else:
        return "public"


def is_admin_user(user_role: UserRole | None) -> bool:
    """Check if user has admin privileges"""
    return user_role in [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.STATION_MANAGER,
        UserRole.CUSTOMER_SUPPORT,
    ]


def is_super_admin(user_role: UserRole | None) -> bool:
    """Check if user has super admin privileges"""
    return user_role == UserRole.SUPER_ADMIN


# =============================================================================
# INPUT VALIDATION & SANITIZATION
# =============================================================================


def sanitize_input(input_str: str, max_length: int = 1000) -> str:
    """Sanitize user input"""
    if not input_str:
        return ""

    # Truncate to max length
    sanitized = input_str[:max_length]

    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', "", sanitized)

    # Remove control characters
    sanitized = "".join(char for char in sanitized if ord(char) >= 32)

    return sanitized.strip()


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def is_safe_url(url: str, allowed_hosts: list[str]) -> bool:
    """Check if URL is safe for redirects"""
    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)

        if not parsed.netloc:
            return True

        return parsed.netloc in allowed_hosts
    except Exception:
        return False


def is_trusted_network(ip: str) -> bool:
    """Check if IP is from trusted network"""
    try:
        ip_addr = ipaddress.ip_address(ip)
        for network in SecurityConfig.TRUSTED_NETWORKS:
            if ip_addr in ipaddress.ip_network(network):
                return True
        return False
    except ValueError:
        return False


def contains_dangerous_patterns(text: str) -> bool:
    """Check if text contains dangerous patterns"""
    text_lower = text.lower()
    for pattern in SecurityConfig.DANGEROUS_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    return False


def constant_time_compare(a: str, b: str) -> bool:
    """Constant-time string comparison to prevent timing attacks"""
    return hmac.compare_digest(a, b)


# =============================================================================
# BUSINESS DATA SANITIZATION
# =============================================================================


def sanitize_business_data(data: dict[str, Any]) -> dict[str, Any]:
    """Remove sensitive business data from public responses"""
    sensitive_fields = [
        "ein",
        "tax_id",
        "ssn",
        "full_address",
        "personal_email",
        "api_key",
        "secret",
    ]

    sanitized = data.copy()
    for field in sensitive_fields:
        if field in sanitized:
            del sanitized[field]

    return sanitized


def get_public_business_info() -> dict[str, Any]:
    """Get public-safe business information"""
    return {
        "business_name": settings.BUSINESS_NAME,
        "email": settings.BUSINESS_EMAIL,
        "phone": settings.BUSINESS_PHONE,
        "city": settings.BUSINESS_CITY,
        "state": settings.BUSINESS_STATE,
        "service_areas": settings.SERVICE_AREAS,
    }


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def get_client_ip(request: Request) -> str:
    """Extract client IP from request headers"""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    return request.client.host if request.client else "unknown"


def get_endpoint_pattern(path: str) -> str:
    """Convert path to pattern for metrics grouping"""
    patterns = [
        (r"/api/booking/\d+", "/api/booking/{id}"),
        (r"/api/stripe/\w+", "/api/stripe/{id}"),
        (r"/api/auth/\w+", "/api/auth/{action}"),
        (r"/api/customers/\d+", "/api/customers/{id}"),
        (r"/api/admin/\w+/\d+", "/api/admin/{resource}/{id}"),
    ]

    for pattern, replacement in patterns:
        path = re.sub(pattern, replacement, path)

    return path


# =============================================================================
# MIDDLEWARE CLASSES
# =============================================================================


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Add security headers
        for header, value in SecurityConfig.SECURITY_HEADERS.items():
            # Only add HSTS in production with HTTPS
            if header == "Strict-Transport-Security":
                if (
                    getattr(settings, "environment", "development") == "production"
                    and request.url.scheme == "https"
                ):
                    response.headers[header] = value
            else:
                response.headers[header] = value

        # Add custom headers
        response.headers["X-API-Version"] = "2.0.0"
        response.headers["X-Request-ID"] = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Remove server information
        response.headers.pop("server", None)

        return response


class RateLimitByIPMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware by IP address"""

    def __init__(self, app: ASGIApp, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: dict[str, list[float]] = defaultdict(list)
        self.last_cleanup = time.time()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = get_client_ip(request)
        current_time = time.time()

        # Cleanup old entries periodically
        if current_time - self.last_cleanup > 60:
            self._cleanup_old_entries(current_time)
            self.last_cleanup = current_time

        # Remove requests older than 1 minute
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip] if current_time - req_time < 60
        ]

        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            if PROMETHEUS_AVAILABLE and SECURITY_VIOLATIONS:
                SECURITY_VIOLATIONS.labels(violation_type="rate_limit").inc()

            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "detail": f"Maximum {self.requests_per_minute} requests per minute",
                    "retry_after": 60,
                },
                headers={"Retry-After": "60"},
            )

        # Add current request
        self.requests[client_ip].append(current_time)

        return await call_next(request)

    def _cleanup_old_entries(self, current_time: float):
        """Remove old entries to prevent memory growth"""
        for ip in list(self.requests.keys()):
            self.requests[ip] = [
                req_time for req_time in self.requests[ip] if current_time - req_time < 60
            ]
            if not self.requests[ip]:
                del self.requests[ip]


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Validate and sanitize incoming requests"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip validation for certain endpoints
        if request.url.path in ["/docs", "/redoc", "/openapi.json", "/metrics", "/health"]:
            return await call_next(request)

        # Validate request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > SecurityConfig.MAX_REQUEST_SIZE:
            if PROMETHEUS_AVAILABLE and SECURITY_VIOLATIONS:
                SECURITY_VIOLATIONS.labels(violation_type="large_request").inc()

            logger.warning(f"Request too large: {content_length} bytes")
            return JSONResponse(
                status_code=413,
                content={"error": "Request too large", "max_size": SecurityConfig.MAX_REQUEST_SIZE},
            )

        # Check for suspicious patterns in URL
        if contains_dangerous_patterns(str(request.url)):
            if PROMETHEUS_AVAILABLE and SECURITY_VIOLATIONS:
                SECURITY_VIOLATIONS.labels(violation_type="malicious_url").inc()

            logger.warning(f"Suspicious URL detected: {request.url.path}")
            return JSONResponse(status_code=400, content={"error": "Invalid request"})

        # Validate User-Agent
        user_agent = request.headers.get("user-agent", "").lower()
        if not user_agent or len(user_agent) > 1000:
            if PROMETHEUS_AVAILABLE and SECURITY_VIOLATIONS:
                SECURITY_VIOLATIONS.labels(violation_type="invalid_user_agent").inc()

            return JSONResponse(status_code=400, content={"error": "Invalid user agent"})

        # Check for suspicious user agents
        for agent in SecurityConfig.SUSPICIOUS_USER_AGENTS:
            if agent in user_agent:
                logger.warning(f"Suspicious user agent: {user_agent}")
                # Don't block, just log
                break

        # Validate content type for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if content_type and not any(
                allowed in content_type.lower()
                for allowed in [
                    "application/json",
                    "application/x-www-form-urlencoded",
                    "multipart/form-data",
                ]
            ):
                return JSONResponse(status_code=415, content={"error": "Unsupported media type"})

        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests for security monitoring"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        client_ip = get_client_ip(request)
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} from {client_ip}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": client_ip,
                "user_agent": request.headers.get("user-agent", "unknown"),
            },
        )

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log response
            log_level = (
                logging.ERROR
                if response.status_code >= 500
                else (logging.WARNING if response.status_code >= 400 else logging.INFO)
            )
            logger.log(
                log_level,
                f"Response: {response.status_code} in {process_time:.3f}s",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "process_time": process_time,
                },
            )

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = str(round(process_time * 1000, 2))

            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {e!s}",
                extra={"request_id": request_id, "error": str(e), "process_time": process_time},
                exc_info=True,
            )
            raise


class MetricsMiddleware(BaseHTTPMiddleware):
    """Collect metrics for monitoring"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.request_count = 0
        self.error_count = 0
        self.response_times = []

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        endpoint = get_endpoint_pattern(request.url.path)

        self.request_count += 1

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            logger.exception(f"Request failed: {e}")
            response = JSONResponse(status_code=500, content={"error": "Internal server error"})

        process_time = time.time() - start_time
        self.response_times.append(process_time)

        # Keep only last 1000 response times
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]

        if status_code >= 400:
            self.error_count += 1

        # Record Prometheus metrics if available
        if PROMETHEUS_AVAILABLE:
            if REQUEST_COUNT:
                REQUEST_COUNT.labels(
                    method=request.method, endpoint=endpoint, status_code=status_code
                ).inc()

            if REQUEST_DURATION:
                REQUEST_DURATION.labels(method=request.method, endpoint=endpoint).observe(
                    process_time
                )

        return response

    def get_stats(self) -> dict[str, Any]:
        """Get collected metrics"""
        if not self.response_times:
            return {
                "request_count": self.request_count,
                "error_count": self.error_count,
                "avg_response_time": 0,
            }

        return {
            "request_count": self.request_count,
            "error_count": self.error_count,
            "avg_response_time": sum(self.response_times) / len(self.response_times),
            "min_response_time": min(self.response_times),
            "max_response_time": max(self.response_times),
        }


class WebhookSecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware specifically for webhook endpoints"""

    def __init__(self, app: ASGIApp, webhook_secret: str):
        super().__init__(app)
        self.webhook_secret = webhook_secret.encode()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only apply to webhook endpoints
        if not str(request.url.path).startswith("/webhooks/"):
            return await call_next(request)

        # Verify webhook signature
        signature = request.headers.get("X-Hub-Signature-256") or request.headers.get(
            "X-Signature-256"
        )
        if not signature:
            logger.warning("Missing webhook signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing webhook signature"
            )

        # Read body
        body = await request.body()

        # Verify signature
        expected_signature = hmac.new(self.webhook_secret, body, hashlib.sha256).hexdigest()

        # Compare signatures (constant time)
        provided_signature = signature.replace("sha256=", "")
        if not constant_time_compare(expected_signature, provided_signature):
            logger.warning("Invalid webhook signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature"
            )

        return await call_next(request)


# =============================================================================
# AUDIT LOGGING
# =============================================================================


class AuditLogger:
    """Audit logging for security events"""

    def __init__(self):
        self.audit_logger = logging.getLogger("audit")

    def log_authentication(self, user_id: str, success: bool, ip: str, details: dict | None = None):
        """Log authentication attempt"""
        self.audit_logger.info(
            f"Authentication {'successful' if success else 'failed'} for user {user_id}",
            extra={
                "event_type": "authentication",
                "user_id": user_id,
                "success": success,
                "ip_address": ip,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    def log_authorization(self, user_id: str, action: str, resource: str, success: bool):
        """Log authorization check"""
        self.audit_logger.info(
            f"Authorization {'granted' if success else 'denied'} for user {user_id}",
            extra={
                "event_type": "authorization",
                "user_id": user_id,
                "action": action,
                "resource": resource,
                "success": success,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    def log_data_access(self, user_id: str, resource: str, operation: str):
        """Log data access"""
        self.audit_logger.info(
            f"Data access: {operation} on {resource} by user {user_id}",
            extra={
                "event_type": "data_access",
                "user_id": user_id,
                "resource": resource,
                "operation": operation,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    def log_security_event(self, event_type: str, details: dict[str, Any]):
        """Log general security event"""
        self.audit_logger.warning(
            f"Security event: {event_type}",
            extra={
                "event_type": "security",
                "security_event": event_type,
                "details": details,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


# Global audit logger instance
audit_logger = AuditLogger()

# =============================================================================
# AUTHENTICATION DEPENDENCIES
# =============================================================================

# HTTPBearer security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any] | None:
    """Extract and validate user from JWT token (optional for public endpoints)"""
    if not credentials:
        return None

    try:
        user = extract_user_from_token(credentials.credentials)
        if user:
            audit_logger.log_authentication(
                user_id=user["id"],
                success=True,
                ip="unknown",  # Will be set by middleware
                details={"method": "jwt"},
            )
        return user
    except Exception as e:
        logger.warning(f"Token validation failed: {e}")
        return None


async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any]:
    """Require authentication for protected endpoints"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_current_user(credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def require_admin(user: dict[str, Any] = Depends(require_auth)) -> dict[str, Any]:
    """Require admin privileges"""
    if not is_admin_user(user.get("role")):
        audit_logger.log_authorization(
            user_id=user["id"], action="admin_access", resource="admin_endpoint", success=False
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required"
        )

    return user


async def require_super_admin(user: dict[str, Any] = Depends(require_auth)) -> dict[str, Any]:
    """Require super admin privileges"""
    if not is_super_admin(user.get("role")):
        audit_logger.log_authorization(
            user_id=user["id"],
            action="super_admin_access",
            resource="super_admin_endpoint",
            success=False,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Super admin privileges required"
        )

    return user


# =============================================================================
# DECORATORS
# =============================================================================


def require_https(func):
    """Decorator to require HTTPS in production"""

    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        if (
            getattr(settings, "environment", "development") == "production"
            and request.url.scheme != "https"
        ):
            raise HTTPException(status_code=400, detail="HTTPS required in production")
        return await func(request, *args, **kwargs)

    return wrapper


# =============================================================================
# SETUP FUNCTIONS
# =============================================================================


def setup_security_middleware(
    app: FastAPI,
    enable_rate_limiting: bool = True,
    enable_input_validation: bool = True,
    enable_request_logging: bool = True,
    enable_metrics: bool = True,
    rate_limit_requests: int = 100,
    webhook_secret: str | None = None,
):
    """
    Setup all security middleware for the application

    Args:
        app: FastAPI application instance
        enable_rate_limiting: Enable rate limiting middleware
        enable_input_validation: Enable input validation middleware
        enable_request_logging: Enable request logging middleware
        enable_metrics: Enable metrics collection middleware
        rate_limit_requests: Requests per minute for rate limiting
        webhook_secret: Secret for webhook signature validation
    """

    # Get configuration from settings/environment
    cors_origins = getattr(settings, "CORS_ORIGINS", ["*"])
    if isinstance(cors_origins, str):
        cors_origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]

    app_env = getattr(settings, "environment", "development")
    jwt_secret = getattr(settings, "SECRET_KEY", "")

    logger.info(f"Setting up security middleware for {app_env} environment")

    # 1. Session middleware (should be first)
    if jwt_secret:
        app.add_middleware(
            SessionMiddleware,
            secret_key=jwt_secret,
            max_age=3600,  # 1 hour
            same_site="lax",
            https_only=(app_env == "production"),
        )

    # 2. Trusted Host middleware (production only)
    if app_env == "production":
        allowed_hosts = [*cors_origins, "localhost", "127.0.0.1"]
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

    # 3. Security Headers middleware
    app.add_middleware(SecurityHeadersMiddleware)

    # 4. Rate Limiting middleware
    if enable_rate_limiting:
        app.add_middleware(RateLimitByIPMiddleware, requests_per_minute=rate_limit_requests)

    # 5. Input Validation middleware
    if enable_input_validation:
        app.add_middleware(InputValidationMiddleware)

    # 6. Request Logging middleware
    if enable_request_logging:
        app.add_middleware(RequestLoggingMiddleware)

    # 7. Metrics middleware
    if enable_metrics:
        app.add_middleware(MetricsMiddleware)

    # 8. Webhook security (if webhook secret is configured)
    if webhook_secret:
        app.add_middleware(WebhookSecurityMiddleware, webhook_secret=webhook_secret)

    # 9. CORS middleware (should be last)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    logger.info("Security middleware configured successfully")


def get_security_config() -> dict[str, Any]:
    """Get current security configuration for debugging"""
    return {
        "max_request_size": SecurityConfig.MAX_REQUEST_SIZE,
        "default_rate_limit": SecurityConfig.DEFAULT_RATE_LIMIT,
        "auth_rate_limit": SecurityConfig.AUTH_RATE_LIMIT,
        "trusted_networks": SecurityConfig.TRUSTED_NETWORKS,
        "prometheus_available": PROMETHEUS_AVAILABLE,
        "environment": getattr(settings, "environment", "development"),
    }
