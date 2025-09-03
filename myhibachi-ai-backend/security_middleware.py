"""
Advanced Security Middleware for My Hibachi API
Implements comprehensive security controls for production deployment
"""

import logging
import re
import time
from collections import defaultdict

from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityConfig:
    """Security configuration constants"""

    # Rate limiting
    RATE_LIMIT_REQUESTS = 100  # requests per window
    RATE_LIMIT_WINDOW = 900  # 15 minutes in seconds

    # IP whitelist (for trusted services)
    TRUSTED_IPS = {
        "127.0.0.1",
        "::1",
        # Add production load balancer IPs here
    }

    # Security headers
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": ("max-age=31536000; includeSubDomains; preload"),
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Cross-Origin-Resource-Policy": "same-origin",
        "Cache-Control": ("no-store, no-cache, must-revalidate, proxy-revalidate"),
        "Pragma": "no-cache",
        "Expires": "0",
    }

    # Suspicious patterns
    SUSPICIOUS_PATTERNS = [
        r"(?i)(union.*select|select.*from|insert.*into|delete.*from)",
        r"(?i)(<script|javascript:|vbscript:|onload=|onerror=)",
        r"(?i)(\.\.\/|\.\.\\|\.\.%2f|\.\.%5c)",
        r"(?i)(exec\(|eval\(|system\(|shell_exec)",
        r"(?i)(drop\s+table|truncate\s+table|alter\s+table)",
    ]

    # Blocked user agents
    BLOCKED_USER_AGENTS = [
        r"(?i)(sqlmap|nikto|nessus|openvas|w3af)",
        r"(?i)(havij|pangolin|jsql|bsqlbf)",
        r"(?i)(masscan|nmap|zmap|zgrab)",
        # Block basic tools but allow versioned
        r"(?i)(curl|wget|python-requests)(?!/[\d\.])",
    ]

    # Content-Type validation
    ALLOWED_CONTENT_TYPES = {
        "application/json",
        "application/x-www-form-urlencoded",
        "multipart/form-data",
        "text/plain",
    }


class RateLimiter:
    """Simple in-memory rate limiter"""

    def __init__(self):
        self.requests: dict[str, list] = defaultdict(list)

    def is_rate_limited(self, identifier: str, limit: int, window: int) -> bool:
        now = time.time()
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier] if now - req_time < window
        ]

        # Check if limit exceeded
        if len(self.requests[identifier]) >= limit:
            return True

        # Add current request
        self.requests[identifier].append(now)
        return False


class SecurityMiddleware(BaseHTTPMiddleware):
    """Advanced security middleware for API protection"""

    def __init__(self, app, config: SecurityConfig = None):
        super().__init__(app)
        self.config = config or SecurityConfig()
        self.rate_limiter = RateLimiter()
        self.blocked_ips = set()

    def get_client_ip(self, request: Request) -> str:
        """Extract client IP with proxy support"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def validate_user_agent(self, user_agent: str) -> bool:
        """Check if user agent is suspicious"""
        if not user_agent:
            return False

        for pattern in self.config.BLOCKED_USER_AGENTS:
            if re.search(pattern, user_agent):
                return False

        return True

    def validate_content_type(self, content_type: str) -> bool:
        """Validate Content-Type header"""
        if not content_type:
            return True  # GET requests don't need Content-Type

        # Extract main content type (before semicolon)
        main_type = content_type.split(";")[0].strip().lower()
        return main_type in self.config.ALLOWED_CONTENT_TYPES

    def scan_for_attacks(self, text: str) -> bool:
        """Scan text for common attack patterns"""
        for pattern in self.config.SUSPICIOUS_PATTERNS:
            if re.search(pattern, text):
                return True
        return False

    def validate_request_content(self, request: Request, body: bytes) -> bool:
        """Validate request content for security threats"""
        # Check URL path
        if self.scan_for_attacks(str(request.url)):
            return False

        # Check query parameters
        for value in request.query_params.values():
            if self.scan_for_attacks(value):
                return False

        # Check headers
        for header_value in request.headers.values():
            if self.scan_for_attacks(header_value):
                return False

        # Check body content
        if body:
            try:
                body_text = body.decode("utf-8", errors="ignore")
                if self.scan_for_attacks(body_text):
                    return False
            except Exception:
                # If we can't decode, it might be binary - allow it
                pass

        return True

    def log_security_event(self, event_type: str, client_ip: str, details: str):
        """Log security events for monitoring"""
        logger.warning(f"SECURITY_EVENT: {event_type} | IP: {client_ip} | " f"Details: {details}")

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        client_ip = self.get_client_ip(request)

        # Skip security checks for trusted IPs
        if client_ip in self.config.TRUSTED_IPS:
            response = await call_next(request)
            self.add_security_headers(response)
            return response

        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            self.log_security_event("BLOCKED_IP", client_ip, "IP is in blocklist")
            return JSONResponse(
                status_code=403,
                content={"error": "Access denied"},
                headers=self.config.SECURITY_HEADERS,
            )

        # Rate limiting
        if self.rate_limiter.is_rate_limited(
            client_ip, self.config.RATE_LIMIT_REQUESTS, self.config.RATE_LIMIT_WINDOW
        ):
            self.log_security_event("RATE_LIMIT", client_ip, "Rate limit exceeded")
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded"},
                headers={
                    **self.config.SECURITY_HEADERS,
                    "Retry-After": str(self.config.RATE_LIMIT_WINDOW),
                },
            )

        # Validate User-Agent
        user_agent = request.headers.get("user-agent", "")
        if not self.validate_user_agent(user_agent):
            self.log_security_event("SUSPICIOUS_USER_AGENT", client_ip, f"UA: {user_agent}")
            # Block IP after suspicious activity
            self.blocked_ips.add(client_ip)
            return JSONResponse(
                status_code=403,
                content={"error": "Access denied"},
                headers=self.config.SECURITY_HEADERS,
            )

        # Validate Content-Type
        content_type = request.headers.get("content-type", "")
        if not self.validate_content_type(content_type):
            self.log_security_event("INVALID_CONTENT_TYPE", client_ip, f"CT: {content_type}")
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid content type"},
                headers=self.config.SECURITY_HEADERS,
            )

        # Read and validate request body
        body = b""
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
            except Exception as e:
                self.log_security_event("BODY_READ_ERROR", client_ip, str(e))
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid request body"},
                    headers=self.config.SECURITY_HEADERS,
                )

        # Validate request content for attacks
        if not self.validate_request_content(request, body):
            self.log_security_event("ATTACK_PATTERN", client_ip, "Suspicious content detected")
            # Block IP after attack attempt
            self.blocked_ips.add(client_ip)
            return JSONResponse(
                status_code=403,
                content={"error": "Access denied"},
                headers=self.config.SECURITY_HEADERS,
            )

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            self.log_security_event("REQUEST_ERROR", client_ip, str(e))
            raise

        # Add security headers
        self.add_security_headers(response)

        # Log request completion
        process_time = time.time() - start_time
        logger.info(
            f"REQUEST: {request.method} {request.url.path} | "
            f"IP: {client_ip} | Status: {response.status_code} | "
            f"Time: {process_time:.3f}s"
        )

        return response

    def add_security_headers(self, response: Response):
        """Add security headers to response"""
        for header, value in self.config.SECURITY_HEADERS.items():
            response.headers[header] = value


# Example usage in FastAPI app:
"""
from fastapi import FastAPI
from myhibachi_security import SecurityMiddleware

app = FastAPI()
app.add_middleware(SecurityMiddleware)

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
"""
