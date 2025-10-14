"""
Request ID Middleware for distributed tracing
Generates or extracts X-Request-ID for every incoming request
"""
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract or generate X-Request-ID for request tracing.
    
    This middleware enables distributed tracing across the entire stack:
    - Frontend generates UUID and sends as X-Request-ID header
    - Backend extracts existing ID or generates new one
    - ID is attached to request.state for use in endpoints and logging
    - ID is returned in response headers for client-side correlation
    - All logs can be filtered by request_id for end-to-end tracing
    
    Usage:
        app.add_middleware(RequestIDMiddleware)
    
    Access in endpoints:
        request.state.request_id
    
    Example log entry:
        logger.info("Processing booking", extra={"request_id": request.state.request_id})
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process incoming request and attach request ID
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            Response with X-Request-ID header
        """
        # Extract existing request ID from header or generate new UUID
        request_id = request.headers.get('X-Request-ID')
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Attach to request state for use in endpoints
        request.state.request_id = request_id
        
        # Log incoming request with ID for tracing
        logger.info(
            f"{request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else "unknown",
            }
        )
        
        # Process request through remaining middleware/handlers
        response = await call_next(request)
        
        # Add request ID to response headers for client correlation
        response.headers['X-Request-ID'] = request_id
        
        # Log response status
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
            }
        )
        
        return response
