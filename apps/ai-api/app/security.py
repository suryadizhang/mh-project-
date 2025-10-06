"""
Security Middleware for AI API
Provides comprehensive security controls for production deployment
"""

from fastapi import FastAPI, Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.sessions import SessionMiddleware
import time
import hashlib
import hmac
import os
import logging
from typing import Dict, List, Optional
from collections import defaultdict
from datetime import datetime, timedelta
import ipaddress

logger = logging.getLogger(__name__)

# Rate limiting storage (in production, use Redis)
rate_limit_storage: Dict[str, List[float]] = defaultdict(list)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware for production deployment"""
    
    def __init__(
        self,
        app: FastAPI,
        allowed_ips: Optional[List[str]] = None,
        rate_limit_requests: int = 100,
        rate_limit_window: int = 60,
        enable_ip_blocking: bool = True,
        enable_request_logging: bool = True
    ):
        super().__init__(app)
        self.allowed_ips = allowed_ips or []
        self.rate_limit_requests = rate_limit_requests
        self.rate_limit_window = rate_limit_window
        self.enable_ip_blocking = enable_ip_blocking
        self.enable_request_logging = enable_request_logging
        
        # Blocked IPs (in production, use Redis/database)
        self.blocked_ips = set()
        
        # Suspicious patterns
        self.suspicious_patterns = [
            'union select',
            'drop table',
            '<script',
            'javascript:',
            'eval(',
            'base64_decode',
            'file_get_contents',
            'system(',
            'exec(',
            'shell_exec',
            'passthru(',
            'proc_open',
            'popen(',
            'curl_exec',
            'curl_multi_exec',
            'parse_ini_file',
            'show_source',
        ]
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Get client IP
        client_ip = self.get_client_ip(request)
        
        try:
            # 1. IP Allow/Block List Check
            if self.enable_ip_blocking and not self.is_ip_allowed(client_ip):
                logger.warning(f"Blocked request from IP: {client_ip}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
            
            # 2. Rate Limiting
            if not self.check_rate_limit(client_ip):
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )
            
            # 3. Request Validation
            await self.validate_request(request)
            
            # 4. Security Headers
            response = await call_next(request)
            self.add_security_headers(response)
            
            # 5. Request Logging
            if self.enable_request_logging:
                processing_time = time.time() - start_time
                self.log_request(request, response, client_ip, processing_time)
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP from request headers"""
        # Check for proxy headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection IP
        return request.client.host if request.client else "unknown"
    
    def is_ip_allowed(self, ip: str) -> bool:
        """Check if IP is allowed and not blocked"""
        if ip in self.blocked_ips:
            return False
        
        # If allowlist is configured, check it
        if self.allowed_ips:
            try:
                client_ip = ipaddress.ip_address(ip)
                for allowed_range in self.allowed_ips:
                    if "/" in allowed_range:
                        # CIDR range
                        if client_ip in ipaddress.ip_network(allowed_range):
                            return True
                    else:
                        # Single IP
                        if str(client_ip) == allowed_range:
                            return True
                return False
            except ValueError:
                logger.warning(f"Invalid IP address: {ip}")
                return False
        
        return True
    
    def check_rate_limit(self, ip: str) -> bool:
        """Check if request is within rate limits"""
        current_time = time.time()
        window_start = current_time - self.rate_limit_window
        
        # Clean old entries
        rate_limit_storage[ip] = [
            timestamp for timestamp in rate_limit_storage[ip]
            if timestamp > window_start
        ]
        
        # Check current count
        if len(rate_limit_storage[ip]) >= self.rate_limit_requests:
            return False
        
        # Add current request
        rate_limit_storage[ip].append(current_time)
        return True
    
    async def validate_request(self, request: Request):
        """Validate request for security threats"""
        # Check request size
        max_request_size = 10 * 1024 * 1024  # 10MB
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > max_request_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Request too large"
            )
        
        # Check for suspicious patterns in URL
        url_path = str(request.url.path).lower()
        for pattern in self.suspicious_patterns:
            if pattern in url_path:
                logger.warning(f"Suspicious pattern detected in URL: {pattern}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid request"
                )
        
        # Check User-Agent
        user_agent = request.headers.get("user-agent", "").lower()
        suspicious_agents = ["sqlmap", "nikto", "nmap", "masscan", "curl/bot"]
        for agent in suspicious_agents:
            if agent in user_agent:
                logger.warning(f"Suspicious user agent: {user_agent}")
                # Don't block completely as some legitimate tools use these
                break
    
    def add_security_headers(self, response):
        """Add security headers to response"""
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # HSTS for HTTPS
        if os.getenv("APP_ENV") == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # CSP for enhanced security
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self' ws: wss:; "
            "font-src 'self' https://fonts.gstatic.com; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers["Content-Security-Policy"] = csp_policy
    
    def log_request(self, request: Request, response, client_ip: str, processing_time: float):
        """Log request for monitoring and security analysis"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "client_ip": client_ip,
            "method": request.method,
            "path": str(request.url.path),
            "query_params": str(request.query_params),
            "user_agent": request.headers.get("user-agent", ""),
            "status_code": response.status_code,
            "processing_time": processing_time,
            "content_length": response.headers.get("content-length", "0")
        }
        
        # Log level based on status code
        if response.status_code >= 500:
            logger.error(f"Request failed: {log_data}")
        elif response.status_code >= 400:
            logger.warning(f"Client error: {log_data}")
        else:
            logger.info(f"Request processed: {log_data}")


class WebhookSecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware specifically for webhook endpoints"""
    
    def __init__(self, app: FastAPI, webhook_secret: str):
        super().__init__(app)
        self.webhook_secret = webhook_secret.encode()
    
    async def dispatch(self, request: Request, call_next):
        # Only apply to webhook endpoints
        if not str(request.url.path).startswith("/webhooks/"):
            return await call_next(request)
        
        # Verify webhook signature
        signature = request.headers.get("X-Hub-Signature-256") or request.headers.get("X-Signature-256")
        if not signature:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing webhook signature"
            )
        
        # Read body
        body = await request.body()
        
        # Verify signature
        expected_signature = hmac.new(
            self.webhook_secret,
            body,
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        provided_signature = signature.replace("sha256=", "")
        if not hmac.compare_digest(expected_signature, provided_signature):
            logger.warning("Invalid webhook signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )
        
        return await call_next(request)


def setup_security_middleware(app: FastAPI):
    """Setup all security middleware for the application"""
    
    # Get configuration from environment
    cors_origins = os.getenv("CORS_ORIGINS", "").split(",")
    cors_origins = [origin.strip() for origin in cors_origins if origin.strip()]
    
    rate_limit_requests = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    rate_limit_period = int(os.getenv("RATE_LIMIT_PERIOD", "60"))
    
    webhook_secret = os.getenv("WEBHOOK_SECRET", "")
    jwt_secret = os.getenv("JWT_SECRET_KEY", "")
    
    app_env = os.getenv("APP_ENV", "development")
    
    # 1. Session middleware (should be first)
    if jwt_secret:
        app.add_middleware(
            SessionMiddleware,
            secret_key=jwt_secret,
            max_age=3600,  # 1 hour
            same_site="lax",
            https_only=(app_env == "production")
        )
    
    # 2. Trusted Host middleware (production only)
    if app_env == "production":
        allowed_hosts = cors_origins + ["localhost", "127.0.0.1"]
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=allowed_hosts
        )
    
    # 3. Main security middleware
    app.add_middleware(
        SecurityMiddleware,
        rate_limit_requests=rate_limit_requests,
        rate_limit_window=rate_limit_period,
        enable_ip_blocking=(app_env == "production"),
        enable_request_logging=True
    )
    
    # 4. Webhook security (if webhook secret is configured)
    if webhook_secret:
        app.add_middleware(
            WebhookSecurityMiddleware,
            webhook_secret=webhook_secret
        )
    
    # 5. CORS middleware (should be last)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins if cors_origins else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    logger.info("Security middleware configured successfully")


# Authentication helper
security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: HTTPAuthorizationCredentials = security):
    """Extract and validate user from JWT token (optional for public endpoints)"""
    if not credentials:
        return None
    
    try:
        # This would integrate with your JWT validation logic
        # For now, return a basic user object
        return {"user_id": "anonymous", "role": "user"}
    except Exception as e:
        logger.warning(f"Token validation failed: {e}")
        return None


async def require_auth(credentials: HTTPAuthorizationCredentials = security):
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