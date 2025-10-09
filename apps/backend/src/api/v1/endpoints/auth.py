"""
Authentication endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import timedelta

from api.deps import get_db, get_current_user
from core.security import verify_password, create_access_token
from core.config import get_settings, UserRole

router = APIRouter()
settings = get_settings()

# Pydantic models
class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: "UserResponse"

class UserResponse(BaseModel):
    id: str
    email: str
    role: UserRole
    full_name: Optional[str] = None
    is_active: bool = True

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

@router.post("/login", response_model=Token, tags=["Authentication"])
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password
    Returns JWT access token with user information
    """
    # TODO: Implement user lookup from database
    # For now, hardcoded admin user for testing
    
    # Mock user data (replace with actual database lookup)
    if login_data.email == "admin@myhibachichef.com" and login_data.password == "admin123":
        user_data = {
            "id": "admin-001",
            "email": "admin@myhibachichef.com", 
            "role": UserRole.ADMIN,
            "full_name": "Admin User"
        }
    elif login_data.email == "owner@myhibachichef.com" and login_data.password == "owner123":
        user_data = {
            "id": "owner-001",
            "email": "owner@myhibachichef.com",
            "role": UserRole.OWNER,
            "full_name": "Business Owner"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user_data["id"],
            "email": user_data["email"],
            "role": user_data["role"]
        },
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(**user_data)
    )

@router.post("/logout", tags=["Authentication"])
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout current user
    In a real implementation, you might want to blacklist the token
    """
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserResponse, tags=["Authentication"])
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        role=current_user["role"],
        full_name=current_user.get("full_name"),
        is_active=True
    )

@router.post("/refresh", response_model=Token, tags=["Authentication"])
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token
    TODO: Implement refresh token validation and rotation
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Refresh token functionality not yet implemented"
    )