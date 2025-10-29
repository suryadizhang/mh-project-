"""
User Pydantic Schemas
Data validation and serialization for user endpoints
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


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
    avatar_url: Optional[str] = None
    auth_provider: AuthProviderSchema
    status: UserStatusSchema
    is_super_admin: bool = False
    is_email_verified: bool = False


class UserCreate(BaseModel):
    """Schema for creating a new user"""
    email: EmailStr
    full_name: str
    avatar_url: Optional[str] = None
    auth_provider: AuthProviderSchema
    google_id: Optional[str] = None
    microsoft_id: Optional[str] = None
    apple_id: Optional[str] = None
    is_email_verified: bool = False


class UserUpdate(BaseModel):
    """Schema for updating an existing user"""
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    status: Optional[UserStatusSchema] = None
    is_super_admin: Optional[bool] = None


class UserInDB(UserBase):
    """User schema with database fields"""
    id: str
    google_id: Optional[str] = None
    microsoft_id: Optional[str] = None
    apple_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserPublic(BaseModel):
    """Public user schema (safe for client exposure)"""
    id: str
    email: EmailStr
    full_name: str
    avatar_url: Optional[str] = None
    auth_provider: AuthProviderSchema
    status: UserStatusSchema
    is_super_admin: bool
    is_email_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
    
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
    data: List[UserPublic]
    message: str = "Users retrieved successfully"


class ApproveUserRequest(BaseModel):
    """Request schema for approving a user"""
    send_notification: bool = Field(default=True, description="Send approval email to user")


class RejectUserRequest(BaseModel):
    """Request schema for rejecting a user"""
    reason: Optional[str] = Field(None, description="Reason for rejection")
    send_notification: bool = Field(default=True, description="Send rejection email to user")


class SuspendUserRequest(BaseModel):
    """Request schema for suspending a user"""
    reason: Optional[str] = Field(None, description="Reason for suspension")
    send_notification: bool = Field(default=True, description="Send suspension email to user")
