"""
Centralized Exception Handling
Custom exceptions and error handling middleware for consistent error responses
"""
from typing import Dict, Any, Optional, List
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import traceback
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)

class ErrorCode(str, Enum):
    """Standardized error codes"""
    # General errors
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    CONFLICT = "CONFLICT"
    BAD_REQUEST = "BAD_REQUEST"
    
    # Business logic errors
    BOOKING_NOT_AVAILABLE = "BOOKING_NOT_AVAILABLE"
    BOOKING_ALREADY_CONFIRMED = "BOOKING_ALREADY_CONFIRMED"
    BOOKING_CANNOT_BE_CANCELLED = "BOOKING_CANNOT_BE_CANCELLED"
    CUSTOMER_NOT_FOUND = "CUSTOMER_NOT_FOUND"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    PAYMENT_ALREADY_PROCESSED = "PAYMENT_ALREADY_PROCESSED"
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    
    # Security errors
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Integration errors
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    STRIPE_ERROR = "STRIPE_ERROR"
    RINGCENTRAL_ERROR = "RINGCENTRAL_ERROR"
    OPENAI_ERROR = "OPENAI_ERROR"
    
    # Data errors
    DUPLICATE_ENTRY = "DUPLICATE_ENTRY"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"
    DATA_INTEGRITY_ERROR = "DATA_INTEGRITY_ERROR"

class AppException(Exception):
    """
    Base application exception with structured error information
    
    Features:
    - Standardized error codes
    - Detailed error messages
    - Additional context data
    - Proper HTTP status codes
    - Logging integration
    """
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INTERNAL_SERVER_ERROR,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.context = context or {}
        self.timestamp = datetime.utcnow()
        
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response"""
        return {
            "success": False,
            "error": {
                "code": self.error_code.value,
                "message": self.message,
                "details": self.details,
                "timestamp": self.timestamp.isoformat()
            }
        }
    
    def log_error(self, logger_instance: logging.Logger = None):
        """Log the error with appropriate level"""
        log = logger_instance or logger
        
        log_data = {
            "error_code": self.error_code.value,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details,
            "context": self.context
        }
        
        if self.status_code >= 500:
            log.error(f"Server error: {self.message}", extra=log_data)
        elif self.status_code >= 400:
            log.warning(f"Client error: {self.message}", extra=log_data)
        else:
            log.info(f"Application error: {self.message}", extra=log_data)

# Specific Exception Classes

class ValidationException(AppException):
    """Validation error with field-specific details"""
    
    def __init__(
        self,
        message: str = "Validation failed",
        field_errors: Optional[Dict[str, List[str]]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=422,
            details={
                "field_errors": field_errors or {},
                **(details or {})
            }
        )

class NotFoundException(AppException):
    """Resource not found exception"""
    
    def __init__(
        self,
        resource: str,
        identifier: str,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(
            message=message,
            error_code=ErrorCode.NOT_FOUND,
            status_code=404,
            details={
                "resource": resource,
                "identifier": identifier,
                **(details or {})
            }
        )

class UnauthorizedException(AppException):
    """Authentication required exception"""
    
    def __init__(
        self,
        message: str = "Authentication required",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.UNAUTHORIZED,
            status_code=401,
            details=details
        )

class ForbiddenException(AppException):
    """Insufficient permissions exception"""
    
    def __init__(
        self,
        message: str = "Insufficient permissions",
        required_permission: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.FORBIDDEN,
            status_code=403,
            details={
                "required_permission": required_permission,
                **(details or {})
            }
        )

class ConflictException(AppException):
    """Resource conflict exception"""
    
    def __init__(
        self,
        message: str,
        conflicting_resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.CONFLICT,
            status_code=409,
            details={
                "conflicting_resource": conflicting_resource,
                **(details or {})
            }
        )

class BusinessLogicException(AppException):
    """Business rule violation exception"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        rule: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=400,
            details={
                "business_rule": rule,
                **(details or {})
            }
        )

class ExternalServiceException(AppException):
    """External service integration error"""
    
    def __init__(
        self,
        service_name: str,
        message: str,
        error_code: ErrorCode = ErrorCode.EXTERNAL_SERVICE_ERROR,
        service_error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"{service_name}: {message}",
            error_code=error_code,
            status_code=502,
            details={
                "service_name": service_name,
                "service_error_code": service_error_code,
                **(details or {})
            }
        )

class RateLimitException(AppException):
    """Rate limit exceeded exception"""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        limit_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            status_code=429,
            details={
                "retry_after_seconds": retry_after,
                "limit_type": limit_type,
                **(details or {})
            }
        )

# Error Handler Functions

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions"""
    exc.log_error()
    
    response_data = exc.to_dict()
    
    # Add request context for debugging (in development)
    if hasattr(request.app.state, 'debug') and request.app.state.debug:
        response_data["debug"] = {
            "request_url": str(request.url),
            "request_method": request.method,
            "client_host": request.client.host if request.client else None
        }
    
    headers = {}
    
    # Add specific headers for certain error types
    if isinstance(exc, RateLimitException) and exc.details.get("retry_after_seconds"):
        headers["Retry-After"] = str(exc.details["retry_after_seconds"])
    
    if isinstance(exc, UnauthorizedException):
        headers["WWW-Authenticate"] = "Bearer"
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data,
        headers=headers
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors"""
    field_errors = {}
    
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        error_msg = error["msg"]
        error_type = error["type"]
        
        if field_path not in field_errors:
            field_errors[field_path] = []
        
        field_errors[field_path].append(f"{error_msg} (type: {error_type})")
    
    validation_exc = ValidationException(
        message="Request validation failed",
        field_errors=field_errors,
        details={
            "error_count": len(exc.errors()),
            "body": getattr(exc, 'body', None)
        }
    )
    
    return await app_exception_handler(request, validation_exc)

async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle standard HTTP exceptions"""
    # Convert HTTPException to AppException
    error_code_map = {
        400: ErrorCode.BAD_REQUEST,
        401: ErrorCode.UNAUTHORIZED,
        403: ErrorCode.FORBIDDEN,
        404: ErrorCode.NOT_FOUND,
        409: ErrorCode.CONFLICT,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
        500: ErrorCode.INTERNAL_SERVER_ERROR
    }
    
    error_code = error_code_map.get(exc.status_code, ErrorCode.INTERNAL_SERVER_ERROR)
    
    app_exc = AppException(
        message=exc.detail,
        error_code=error_code,
        status_code=exc.status_code
    )
    
    return await app_exception_handler(request, app_exc)

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    error_id = f"error_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    logger.error(
        f"Unhandled exception [{error_id}]: {str(exc)}",
        exc_info=True,
        extra={
            "error_id": error_id,
            "request_url": str(request.url),
            "request_method": request.method,
            "client_host": request.client.host if request.client else None,
            "traceback": traceback.format_exc()
        }
    )
    
    # Create generic error response
    app_exc = AppException(
        message="An unexpected error occurred. Please try again later.",
        error_code=ErrorCode.INTERNAL_SERVER_ERROR,
        status_code=500,
        details={"error_id": error_id}
    )
    
    return await app_exception_handler(request, app_exc)

# Utility Functions

def raise_not_found(resource: str, identifier: str, details: Optional[Dict[str, Any]] = None):
    """Convenience function to raise NotFoundException"""
    raise NotFoundException(resource, identifier, details)

def raise_validation_error(
    message: str = "Validation failed",
    field_errors: Optional[Dict[str, List[str]]] = None,
    details: Optional[Dict[str, Any]] = None
):
    """Convenience function to raise ValidationException"""
    raise ValidationException(message, field_errors, details)

def raise_unauthorized(message: str = "Authentication required"):
    """Convenience function to raise UnauthorizedException"""
    raise UnauthorizedException(message)

def raise_forbidden(
    message: str = "Insufficient permissions",
    required_permission: Optional[str] = None
):
    """Convenience function to raise ForbiddenException"""
    raise ForbiddenException(message, required_permission)

def raise_conflict(message: str, conflicting_resource: Optional[str] = None):
    """Convenience function to raise ConflictException"""
    raise ConflictException(message, conflicting_resource)

def raise_business_error(
    message: str,
    error_code: ErrorCode,
    rule: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
):
    """Convenience function to raise BusinessLogicException"""
    raise BusinessLogicException(message, error_code, rule, details)

def raise_external_service_error(
    service_name: str,
    message: str,
    error_code: ErrorCode = ErrorCode.EXTERNAL_SERVICE_ERROR,
    service_error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
):
    """Convenience function to raise ExternalServiceException"""
    raise ExternalServiceException(
        service_name, message, error_code, service_error_code, details
    )

# Error Response Helper

def create_error_response(
    message: str,
    error_code: ErrorCode = ErrorCode.INTERNAL_SERVER_ERROR,
    status_code: int = 500,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create standardized error response"""
    return {
        "success": False,
        "error": {
            "code": error_code.value,
            "message": message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        }
    }

def create_success_response(
    data: Any = None,
    message: str = "Operation successful",
    meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create standardized success response"""
    response = {
        "success": True,
        "message": message
    }
    
    if data is not None:
        response["data"] = data
    
    if meta:
        response["meta"] = meta
    
    return response