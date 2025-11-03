"""
Authentication and authorization endpoints.

This module handles user authentication operations including:
- User login and token generation
- Token refresh
- User logout
- Current user information retrieval
- Password reset functionality

All endpoints except /login and /register require JWT Bearer token authentication.
"""

from typing import Any

from fastapi import APIRouter, status
from pydantic import BaseModel, EmailStr, Field

router = APIRouter(tags=["authentication"])


# Pydantic Schemas
class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")

    model_config = {
        "json_schema_extra": {
            "examples": [{"email": "john@example.com", "password": "SecurePass123!"}]
        }
    }


class TokenResponse(BaseModel):
    """Authentication token response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    refresh_token: str = Field(..., description="Refresh token for obtaining new access tokens")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 3600,
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                }
            ]
        }
    }


class UserResponse(BaseModel):
    """User information response."""

    id: str = Field(..., description="Unique user identifier")
    email: EmailStr = Field(..., description="User email address")
    name: str = Field(..., description="User full name")
    is_admin: bool = Field(default=False, description="Whether user has admin privileges")
    created_at: str = Field(..., description="Account creation timestamp (ISO 8601)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "user-abc123",
                    "email": "john@example.com",
                    "name": "John Doe",
                    "is_admin": False,
                    "created_at": "2024-10-19T10:30:00Z",
                }
            ]
        }
    }


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str = Field(..., description="Error message")


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="""
    Authenticate user and generate access tokens.

    ## Process:
    1. Validates user credentials (email + password)
    2. Generates JWT access token (expires in 1 hour)
    3. Generates refresh token (expires in 7 days)
    4. Returns both tokens for client storage

    ## Security:
    - Password hashing: bcrypt with 12 rounds
    - JWT signing: HS256 algorithm
    - Rate limiting: 5 attempts per 15 minutes per IP
    - Account lockout: After 5 failed attempts

    ## Token Usage:
    Store access_token securely and include in all API requests:
    ```
    Authorization: Bearer <access_token>
    ```

    When access_token expires, use refresh_token to obtain new tokens via `/refresh` endpoint.
    """,
    responses={
        200: {
            "description": "Login successful, tokens generated",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "expires_in": 3600,
                        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    }
                }
            },
        },
        400: {
            "description": "Invalid request data",
            "model": ErrorResponse,
            "content": {"application/json": {"example": {"detail": "Invalid email format"}}},
        },
        401: {
            "description": "Invalid credentials",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_credentials": {
                            "summary": "Wrong password",
                            "value": {"detail": "Invalid email or password"},
                        },
                        "account_locked": {
                            "summary": "Too many failed attempts",
                            "value": {
                                "detail": "Account locked due to too many failed login attempts. Try again in 15 minutes."
                            },
                        },
                    }
                }
            },
        },
        429: {
            "description": "Too many requests",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Too many login attempts. Please try again in 15 minutes."
                    }
                }
            },
        },
    },
)
async def login(credentials: LoginRequest) -> dict[str, Any]:
    """
    Authenticate user and generate access tokens.

    Args:
        credentials: User email and password

    Returns:
        Access token, refresh token, and token metadata

    Raises:
        HTTPException(400): Invalid email format
        HTTPException(401): Invalid credentials or account locked
        HTTPException(429): Too many login attempts
    """
    # Placeholder implementation
    return {
        "access_token": "dev-token-123",
        "token_type": "bearer",
        "expires_in": 3600,
        "refresh_token": "dev-refresh-token-123",
    }


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user information",
    description="""
    Retrieve information about the currently authenticated user.

    ## Authentication Required:
    This endpoint requires a valid JWT Bearer token in the Authorization header.

    ## Use Cases:
    - Display user profile
    - Check user permissions
    - Verify authentication status
    - Get user ID for other API calls

    ## Response:
    Returns complete user profile including role and account creation date.
    """,
    responses={
        200: {
            "description": "User information retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "user-abc123",
                        "email": "john@example.com",
                        "name": "John Doe",
                        "is_admin": False,
                        "created_at": "2024-10-19T10:30:00Z",
                    }
                }
            },
        },
        401: {
            "description": "Authentication required",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "missing_token": {
                            "summary": "No token provided",
                            "value": {"detail": "Not authenticated"},
                        },
                        "invalid_token": {
                            "summary": "Invalid or expired token",
                            "value": {"detail": "Invalid authentication credentials"},
                        },
                    }
                }
            },
        },
    },
)
async def get_current_user_info() -> dict[str, Any]:
    """
    Get current user information.

    Returns:
        User profile with id, email, name, role, and creation date

    Raises:
        HTTPException(401): Missing or invalid authentication token
    """
    # This is a placeholder for your existing auth system
    # In development, return mock data
    return {
        "id": "dev-user-123",
        "email": "dev@myhibachi.com",
        "name": "Dev User",
        "is_admin": True,
        "created_at": "2024-01-01T00:00:00Z",
    }


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="User logout",
    description="""
    Logout user and invalidate tokens.

    ## Process:
    1. Invalidates current access token
    2. Invalidates refresh token
    3. Removes user session from cache
    4. Logs logout event for security audit

    ## Client Actions Required:
    After successful logout, client should:
    - Remove stored access_token
    - Remove stored refresh_token
    - Redirect to login page
    - Clear any cached user data

    ## Note:
    This endpoint still requires authentication (the token being invalidated).
    """,
    responses={
        200: {
            "description": "Logout successful",
            "content": {"application/json": {"example": {"message": "Logged out successfully"}}},
        },
        401: {"description": "Authentication required", "model": ErrorResponse},
    },
)
async def logout() -> dict[str, str]:
    """
    Logout user and invalidate tokens.

    Returns:
        Success message

    Raises:
        HTTPException(401): Missing or invalid authentication token
    """
    # Placeholder implementation
    return {"message": "Logged out successfully"}


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="""
    Generate new access token using refresh token.

    ## When to Use:
    - Access token has expired (401 error)
    - Proactively before expiration
    - After long period of inactivity

    ## Process:
    1. Validates refresh token
    2. Generates new access token (1 hour expiry)
    3. Optionally generates new refresh token (7 days expiry)
    4. Returns new tokens

    ## Security:
    - Refresh tokens are single-use only
    - Old refresh token is immediately invalidated
    - New refresh token must be stored

    ## Request Body:
    ```json
    {
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```
    """,
    responses={
        200: {"description": "Tokens refreshed successfully"},
        401: {
            "description": "Invalid or expired refresh token",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "expired": {
                            "summary": "Refresh token expired",
                            "value": {"detail": "Refresh token has expired. Please login again."},
                        },
                        "invalid": {
                            "summary": "Invalid token",
                            "value": {"detail": "Invalid refresh token"},
                        },
                        "already_used": {
                            "summary": "Token already used",
                            "value": {
                                "detail": "Refresh token has already been used. Please login again."
                            },
                        },
                    }
                }
            },
        },
    },
)
async def refresh_token(refresh_token: str) -> dict[str, Any]:
    """
    Generate new access token using refresh token.

    Args:
        refresh_token: Valid refresh token from login response

    Returns:
        New access token and refresh token

    Raises:
        HTTPException(401): Invalid, expired, or already used refresh token
    """
    # Placeholder implementation
    return {
        "access_token": "new-dev-token-456",
        "token_type": "bearer",
        "expires_in": 3600,
        "refresh_token": "new-dev-refresh-token-456",
    }


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description="""
    Request a password reset link via email.

    ## Process:
    1. Validates email exists in system
    2. Generates secure reset token (expires in 1 hour)
    3. Sends reset link to user's email
    4. Logs security event

    ## Security:
    - Rate limited: 3 requests per hour per email
    - Token expires in 1 hour
    - One-time use only
    - Email verification required
    - No user enumeration (always returns success)

    ## Reset Link Format:
    ```
    https://myhibachi.com/reset-password?token=<reset_token>
    ```

    ## Request Body:
    ```json
    {
        "email": "john@example.com"
    }
    ```
    """,
    responses={
        200: {
            "description": "Reset email sent (if account exists)",
            "content": {
                "application/json": {
                    "example": {
                        "message": "If an account with that email exists, a password reset link has been sent."
                    }
                }
            },
        },
        400: {"description": "Invalid email format", "model": ErrorResponse},
        429: {
            "description": "Too many reset requests",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Too many password reset requests. Please try again in 1 hour."
                    }
                }
            },
        },
    },
)
async def reset_password(email: EmailStr) -> dict[str, str]:
    """
    Request password reset link.

    Args:
        email: User's email address

    Returns:
        Success message (always returns success for security)

    Raises:
        HTTPException(400): Invalid email format
        HTTPException(429): Too many reset requests
    """
    # Placeholder implementation
    return {"message": "If an account with that email exists, a password reset link has been sent."}
