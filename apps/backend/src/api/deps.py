"""
API Dependencies for authentication, rate limiting, and permissions
"""
from fastapi import Depends, HTTPException, status, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
from pydantic import BaseModel
from core.database import get_db
from core.security import extract_user_from_token, is_admin_user, is_super_admin
from core.config import UserRole
import logging

logger = logging.getLogger(__name__)

# Pydantic models for type hints
class AdminUser(BaseModel):
    """Authenticated admin user"""
    id: int
    email: str
    role: str
    full_name: Optional[str] = None
    
    class Config:
        from_attributes = True

# Security scheme
security = HTTPBearer(auto_error=False)

# User dependencies
async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """Get current user from JWT token (optional - no error if missing)"""
    if not credentials:
        return None
    
    try:
        user = extract_user_from_token(credentials.credentials)
        return user
    except Exception as e:
        logger.warning(f"Token validation failed: {e}")
        return None

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Get current user from JWT token (required)"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = extract_user_from_token(credentials.credentials)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

async def get_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Require admin user"""
    if not is_admin_user(current_user.get("role")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

async def get_current_admin_user(
    current_user: Dict[str, Any] = Depends(get_admin_user)
) -> AdminUser:
    """Get current admin user as typed object"""
    return AdminUser(
        id=current_user.get("id", 0),
        email=current_user.get("email", ""),
        role=current_user.get("role", ""),
        full_name=current_user.get("full_name")
    )

async def get_super_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Require super admin user (manager/owner)"""
    if not is_super_admin(current_user.get("role")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin privileges required"
        )
    return current_user

# Rate limiting dependencies
class RateLimitTier:
    """Rate limiting tier markers"""
    
    @staticmethod
    def public():
        """Public tier rate limiting"""
        async def _public_rate_limit():
            # Rate limiting is handled in middleware
            # This is just for documentation/marking
            pass
        return _public_rate_limit
    
    @staticmethod
    def admin():
        """Admin tier rate limiting"""
        async def _admin_rate_limit(user: Dict[str, Any] = Depends(get_admin_user)):
            # Rate limiting is handled in middleware based on user role
            return user
        return _admin_rate_limit
    
    @staticmethod
    def ai():
        """AI tier rate limiting (strict for all users)"""
        async def _ai_rate_limit():
            # Rate limiting is handled in middleware for AI endpoints
            pass
        return _ai_rate_limit

# API Key authentication (for external integrations)
async def verify_api_key(
    x_api_key: Optional[str] = Header(None)
) -> bool:
    """Verify API key from header"""
    if not x_api_key:
        return False
    
    # TODO: Implement API key verification against database
    # For now, just check if key is present
    return len(x_api_key) >= 32

async def require_api_key(
    x_api_key: str = Header(..., description="API Key")
) -> str:
    """Require valid API key"""
    if not await verify_api_key(x_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return x_api_key

# Webhook verification
async def verify_webhook_signature(
    request: Request,
    x_webhook_signature: Optional[str] = Header(None),
    x_hub_signature: Optional[str] = Header(None),
    x_hub_signature_256: Optional[str] = Header(None)
) -> bool:
    """Verify webhook signature"""
    # This will be implemented for each webhook type
    # RingCentral, Stripe, Meta, etc. have different signature schemes
    return True  # Placeholder

# Business rule dependencies
async def check_quiet_hours() -> bool:
    """Check if current time is within quiet hours"""
    from datetime import datetime
    import pytz
    
    tz = pytz.timezone("America/Los_Angeles")
    now = datetime.now(tz)
    current_hour = now.hour
    
    # Quiet hours: 9 PM to 8 AM Pacific
    return current_hour >= 21 or current_hour < 8

async def get_business_context() -> Dict[str, Any]:
    """Get business context information"""
    from core.security import get_public_business_info
    
    return {
        "business_info": get_public_business_info(),
        "quiet_hours": await check_quiet_hours(),
        "timezone": "America/Los_Angeles"
    }

# Pagination dependencies
async def get_pagination_params(
    page: int = 1,
    per_page: int = 20,
    max_per_page: int = 100
) -> Dict[str, int]:
    """Get pagination parameters with validation"""
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page must be >= 1"
        )
    
    if per_page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Per page must be >= 1"
        )
    
    if per_page > max_per_page:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Per page must be <= {max_per_page}"
        )
    
    return {
        "page": page,
        "per_page": per_page,
        "offset": (page - 1) * per_page
    }

# Database transaction decorator
def with_transaction(func):
    """Decorator to wrap function in database transaction"""
    async def wrapper(*args, **kwargs):
        db: AsyncSession = kwargs.get('db')
        if not db:
            raise ValueError("Database session required for transaction")
        
        try:
            result = await func(*args, **kwargs)
            await db.commit()
            return result
        except Exception:
            await db.rollback()
            raise
    
    return wrapper