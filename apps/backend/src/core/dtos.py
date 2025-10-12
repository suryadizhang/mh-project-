"""
Common Data Transfer Objects (DTOs)
Standardized response schemas for API consistency
"""
from typing import Generic, TypeVar, Optional, List, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """
    Standard API response envelope
    
    Ensures consistent response structure across all endpoints
    """
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[T] = Field(None, description="Response data")
    message: Optional[str] = Field(None, description="Human-readable message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    request_id: Optional[str] = Field(None, description="Unique request identifier for tracing")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"id": "123", "name": "Example"},
                "message": "Operation completed successfully",
                "timestamp": "2025-10-09T12:00:00Z",
                "request_id": "req_abc123"
            }
        }


class ErrorDetail(BaseModel):
    """Detailed error information"""
    code: str = Field(..., description="Error code for programmatic handling")
    message: str = Field(..., description="Human-readable error message")
    field: Optional[str] = Field(None, description="Field name if validation error")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error context")


class ErrorResponse(BaseModel):
    """
    Standard error response
    
    Used for all error cases to provide consistent error handling
    """
    success: bool = Field(False, description="Always false for errors")
    error: ErrorDetail = Field(..., description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(None, description="Request ID for support/debugging")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Resource not found",
                    "field": None,
                    "details": {"resource_id": "123"}
                },
                "timestamp": "2025-10-09T12:00:00Z",
                "request_id": "req_abc123"
            }
        }


class PaginationMetadata(BaseModel):
    """Pagination metadata"""
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, le=100, description="Items per page")
    total_items: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")
    
    @classmethod
    def from_query_result(
        cls,
        total_items: int,
        page: int,
        per_page: int
    ) -> "PaginationMetadata":
        """Create pagination metadata from query results"""
        total_pages = (total_items + per_page - 1) // per_page
        
        return cls(
            page=page,
            per_page=per_page,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Paginated API response
    
    Used for list endpoints with pagination
    """
    success: bool = Field(True, description="Request success status")
    data: List[T] = Field(..., description="Page of items")
    pagination: PaginationMetadata = Field(..., description="Pagination metadata")
    message: Optional[str] = Field(None, description="Optional message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": [{"id": "1", "name": "Item 1"}, {"id": "2", "name": "Item 2"}],
                "pagination": {
                    "page": 1,
                    "per_page": 20,
                    "total_items": 100,
                    "total_pages": 5,
                    "has_next": True,
                    "has_prev": False
                },
                "timestamp": "2025-10-09T12:00:00Z",
                "request_id": "req_abc123"
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status: healthy, degraded, or unhealthy")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    checks: Dict[str, bool] = Field(..., description="Individual component health checks")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2025-10-09T12:00:00Z",
                "checks": {
                    "database": True,
                    "redis": True,
                    "external_api": True
                }
            }
        }


# Helper functions for creating responses

def create_success_response(
    data: Any,
    message: Optional[str] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a success response dictionary
    
    Args:
        data: Response data
        message: Optional success message
        request_id: Optional request ID
        
    Returns:
        Response dictionary
    """
    return {
        "success": True,
        "data": data,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id
    }


def create_error_response(
    code: str,
    message: str,
    field: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create an error response dictionary
    
    Args:
        code: Error code
        message: Error message
        field: Optional field name for validation errors
        details: Optional additional details
        request_id: Optional request ID
        
    Returns:
        Error response dictionary
    """
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "field": field,
            "details": details or {}
        },
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id
    }


def create_paginated_response(
    items: List[Any],
    total_items: int,
    page: int,
    per_page: int,
    message: Optional[str] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a paginated response dictionary
    
    Args:
        items: List of items for current page
        total_items: Total number of items across all pages
        page: Current page number
        per_page: Items per page
        message: Optional message
        request_id: Optional request ID
        
    Returns:
        Paginated response dictionary
    """
    pagination_meta = PaginationMetadata.from_query_result(
        total_items=total_items,
        page=page,
        per_page=per_page
    )
    
    return {
        "success": True,
        "data": items,
        "pagination": pagination_meta.dict(),
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id
    }
