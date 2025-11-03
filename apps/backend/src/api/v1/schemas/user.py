"""
User Pydantic Schemas
Data validation and serialization for user endpoints
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class AuthProviderSchema(str, Enum):
    """Authentication provider types"""

    GOOGLE = "google"
    EMAIL = "email"
    MICROSOFT = "microsoft"
    APPLE = "apple"


class UserStatusSchema(str, Enum):
    """User status types"""

    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


class UserBase(BaseModel):
    """Base user schema with common fields"""

    email: EmailStr
    full_name: str
    avatar_url: str | None = None
    auth_provider: AuthProviderSchema
    status: UserStatusSchema
    is_super_admin: bool = False
    is_email_verified: bool = False


class UserCreate(BaseModel):
    """Schema for creating a new user"""

    email: EmailStr
    full_name: str
    avatar_url: str | None = None
    auth_provider: AuthProviderSchema
    google_id: str | None = None
    microsoft_id: str | None = None
    apple_id: str | None = None
    is_email_verified: bool = False


class UserUpdate(BaseModel):
    """Schema for updating an existing user"""

    full_name: str | None = None
    avatar_url: str | None = None
    status: UserStatusSchema | None = None
    is_super_admin: bool | None = None


class UserInDB(UserBase):
    """User schema with database fields"""

    id: str
    google_id: str | None = None
    microsoft_id: str | None = None
    apple_id: str | None = None
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None

    class Config:
        from_attributes = True


class UserPublic(BaseModel):
    """Public user schema (safe for client exposure)"""

    id: str
    email: EmailStr
    full_name: str
    avatar_url: str | None = None
    auth_provider: AuthProviderSchema
    status: UserStatusSchema
    is_super_admin: bool
    is_email_verified: bool
    created_at: datetime
    last_login_at: datetime | None = None

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """API response for single user"""

    success: bool = True
    data: UserPublic
    message: str = "User retrieved successfully"


class UserListResponse(BaseModel):
    """API response for list of users"""

    success: bool = True
    data: list[UserPublic]
    message: str = "Users retrieved successfully"


class ApproveUserRequest(BaseModel):
    """Request schema for approving a user"""

    send_notification: bool = Field(default=True, description="Send approval email to user")


class RejectUserRequest(BaseModel):
    """Request schema for rejecting a user"""

    reason: str | None = Field(None, description="Reason for rejection")
    send_notification: bool = Field(default=True, description="Send rejection email to user")


class SuspendUserRequest(BaseModel):
    """Request schema for suspending a user"""

    reason: str | None = Field(None, description="Reason for suspension")
    send_notification: bool = Field(default=True, description="Send suspension email to user")
