"""
Security module for MyHibachi API
Comprehensive security utilities and middleware
"""

import hashlib
import hmac
import secrets
import time
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
import ipaddress
import re
import logging
import asyncio
from functools import wraps

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import bcrypt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from core.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)

class SecurityConfig:
    """Security configuration constants"""
    
    # CSRF Protection
    CSRF_TOKEN_BYTES = 32
    CSRF_COOKIE_NAME = "csrf_token"
    CSRF_HEADER_NAME = "X-CSRF-Token"
    
    # Rate Limiting
    DEFAULT_RATE_LIMIT = "100/minute"
    AUTH_RATE_LIMIT = "5/minute"
    
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
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss:; "
            "media-src 'self'; "
            "object-src 'none'; "
            "child-src 'none'; "
            "worker-src 'none'; "
            "manifest-src 'self'; "
            "base-uri 'self'; "
            "form-action 'self'"
        ),
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": (
            "geolocation=(), microphone=(), camera=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=()"
        )
    }
    
    # Input Validation
    MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_JSON_KEYS = 1000
    MAX_STRING_LENGTH = 10000
    
    # Trusted Networks (for development)
    TRUSTED_NETWORKS = [
        "127.0.0.0/8",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16"
    ]

class FieldEncryption:
    """Field-level encryption for sensitive data"""
    
    def __init__(self, key: Optional[str] = None):
        if key:
            self.key = base64.urlsafe_b64decode(key.encode())
        else:
            # Generate a new key if none provided
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
    
    def encrypt_dict(self, data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """Encrypt specific fields in a dictionary"""
        result = data.copy()
        for field in fields:
            if field in result and result[field]:
                result[field] = self.encrypt(str(result[field]))
        return result
    
    def decrypt_dict(self, data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """Decrypt specific fields in a dictionary"""
        result = data.copy()
        for field in fields:
            if field in result and result[field]:
                result[field] = self.decrypt(result[field])
        return result

class SecurityUtils:
    """Security utility functions"""
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate cryptographically secure random token"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_password(password: str, rounds: int = 12) -> str:
        """Hash password with bcrypt"""
        salt = bcrypt.gensalt(rounds=rounds)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    @staticmethod
    def constant_time_compare(a: str, b: str) -> bool:
        """Constant-time string comparison to prevent timing attacks"""
        return hmac.compare_digest(a, b)
    
    @staticmethod
    def sanitize_input(input_str: str, max_length: int = 1000) -> str:
        """Sanitize user input"""
        if not input_str:
            return ""
        
        # Truncate to max length
        sanitized = input_str[:max_length]
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', sanitized)
        
        # Remove control characters
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32)
        
        return sanitized.strip()
    
    @staticmethod
    def is_safe_url(url: str, allowed_hosts: List[str]) -> bool:
        """Check if URL is safe for redirects"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            
            # Relative URLs are generally safe
            if not parsed.netloc:
                return True
            
            # Check against allowed hosts
            return parsed.netloc in allowed_hosts
        except Exception:
            return False
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
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

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        for header, value in SecurityConfig.SECURITY_HEADERS.items():
            response.headers[header] = value
        
        # Add custom headers
        response.headers["X-API-Version"] = "2.0.0"
        response.headers["X-Request-ID"] = request.headers.get("X-Request-ID", "unknown")
        
        return response

class RateLimitByIPMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware by IP address"""
    
    def __init__(self, app: ASGIApp, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, List[float]] = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = self.get_client_ip(request)
        current_time = time.time()
        
        # Initialize or clean old requests for this IP
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        # Remove requests older than 1 minute
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if current_time - req_time < 60
        ]
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "detail": f"Maximum {self.requests_per_minute} requests per minute",
                    "retry_after": 60
                }
            )
        
        # Add current request
        self.requests[client_ip].append(current_time)
        
        return await call_next(request)
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"

class InputValidationMiddleware(BaseHTTPMiddleware):
    """Validate and sanitize input data"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > SecurityConfig.MAX_REQUEST_SIZE:
            return JSONResponse(
                status_code=413,
                content={"error": "Request too large", "max_size": SecurityConfig.MAX_REQUEST_SIZE}
            )
        
        # Validate content type for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if content_type and not any(
                allowed in content_type.lower() 
                for allowed in ["application/json", "application/x-www-form-urlencoded", "multipart/form-data"]
            ):
                return JSONResponse(
                    status_code=415,
                    content={"error": "Unsupported media type"}
                )
        
        return await call_next(request)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests for security monitoring"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        client_ip = self.get_client_ip(request)
        
        # Generate request ID if not present
        request_id = request.headers.get("X-Request-ID", secrets.token_urlsafe(8))
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} from {client_ip}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": client_ip,
                "user_agent": request.headers.get("user-agent", "unknown")
            }
        )
        
        response = await call_next(request)
        
        # Calculate response time
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            f"Response: {response.status_code} in {process_time:.3f}s",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "process_time": process_time
            }
        )
        
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = str(round(process_time * 1000, 2))
        
        return response
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"

class MetricsMiddleware(BaseHTTPMiddleware):
    """Collect metrics for monitoring"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.request_count = 0
        self.error_count = 0
        self.response_times = []
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        self.request_count += 1
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        self.response_times.append(process_time)
        
        # Keep only last 1000 response times
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]
        
        if response.status_code >= 400:
            self.error_count += 1
        
        return response

class AuditLogger:
    """Audit logging for security events"""
    
    def __init__(self):
        self.audit_logger = logging.getLogger("audit")
    
    def log_authentication(self, user_id: str, success: bool, ip: str, details: Dict = None):
        """Log authentication attempt"""
        self.audit_logger.info(
            f"Authentication {'successful' if success else 'failed'} for user {user_id}",
            extra={
                "event_type": "authentication",
                "user_id": user_id,
                "success": success,
                "ip_address": ip,
                "details": details or {}
            }
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
                "success": success
            }
        )
    
    def log_data_access(self, user_id: str, resource: str, operation: str):
        """Log data access"""
        self.audit_logger.info(
            f"Data access: {operation} on {resource} by user {user_id}",
            extra={
                "event_type": "data_access",
                "user_id": user_id,
                "resource": resource,
                "operation": operation
            }
        )
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log general security event"""
        self.audit_logger.warning(
            f"Security event: {event_type}",
            extra={
                "event_type": "security",
                "security_event": event_type,
                "details": details
            }
        )

# Global instances
field_encryption = FieldEncryption(settings.field_encryption_key if hasattr(settings, 'field_encryption_key') else None)
audit_logger = AuditLogger()

# Decorator for requiring HTTPS in production
def require_https(func):
    """Decorator to require HTTPS in production"""
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        if settings.environment == "production" and request.url.scheme != "https":
            raise HTTPException(
                status_code=400,
                detail="HTTPS required in production"
            )
        return await func(request, *args, **kwargs)
    return wrapper

def get_client_ip(request: Request) -> str:
    """Extract client IP from request headers"""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host if request.client else "unknown"