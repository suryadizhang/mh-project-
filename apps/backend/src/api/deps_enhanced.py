"""
Enhanced API Dependencies with Dependency Injection Integration
Combines authentication, rate limiting, and business services
"""
from fastapi import Depends, HTTPException, status, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from pydantic import BaseModel
import logging

# Import our new DI system
from core.container import DependencyInjectionContainer
from core.service_registry import get_container
from repositories.booking_repository import BookingRepository
from repositories.customer_repository import CustomerRepository

# Legacy imports (to be gradually replaced)
from core.security import extract_user_from_token, is_admin_user, is_super_admin
from core.config import UserRole

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

class AuthenticatedUser(BaseModel):
    """Base authenticated user"""
    id: int
    email: str
    role: str
    full_name: Optional[str] = None
    permissions: Optional[list] = None
    
    class Config:
        from_attributes = True

# Security scheme
security = HTTPBearer(auto_error=False)

# Dependency Injection Dependencies

def get_di_container() -> DependencyInjectionContainer:
    """Get the dependency injection container"""
    def _get_container(request: Request) -> DependencyInjectionContainer:
        if not hasattr(request.state, 'container'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Dependency injection container not available"
            )
        return request.state.container
    
    return Depends(_get_container)

def get_booking_repository(
    container: DependencyInjectionContainer = get_di_container()
) -> BookingRepository:
    """Get booking repository from DI container"""
    try:
        return container.resolve("booking_repository")
    except Exception as e:
        logger.error(f"Failed to resolve booking repository: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Booking service unavailable"
        )

def get_customer_repository(
    container: DependencyInjectionContainer = get_di_container()
) -> CustomerRepository:
    """Get customer repository from DI container"""
    try:
        return container.resolve("customer_repository")
    except Exception as e:
        logger.error(f"Failed to resolve customer repository: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Customer service unavailable"
        )

def get_database_session(
    container: DependencyInjectionContainer = get_di_container()
):
    """Get database session from DI container"""
    try:
        return container.resolve("database_session")
    except Exception as e:
        logger.error(f"Failed to resolve database session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database service unavailable"
        )

# Authentication Dependencies (Enhanced)

async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[AuthenticatedUser]:
    """Get current user from JWT token (optional - no error if missing)"""
    if not credentials:
        return None
    
    try:
        user_data = extract_user_from_token(credentials.credentials)
        if user_data:
            return AuthenticatedUser(**user_data)
        return None
    except Exception as e:
        logger.warning(f"Token validation failed: {e}")
        return None

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> AuthenticatedUser:
    """Get current user from JWT token (required)"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_data = extract_user_from_token(credentials.credentials)
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return AuthenticatedUser(**user_data)

async def get_admin_user(
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> AdminUser:
    """Require admin user"""
    if not is_admin_user(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return AdminUser(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        full_name=current_user.full_name
    )

async def get_super_admin_user(
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> AdminUser:
    """Require super admin user (manager/owner)"""
    if not is_super_admin(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin privileges required"
        )
    
    return AdminUser(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        full_name=current_user.full_name
    )

# Service-aware Dependencies (combining auth + services)

def get_authenticated_booking_service():
    """Get booking repository with authenticated user context"""
    def _get_service(
        current_user: AuthenticatedUser = Depends(get_current_user),
        booking_repo: BookingRepository = Depends(get_booking_repository)
    ) -> tuple[AuthenticatedUser, BookingRepository]:
        return current_user, booking_repo
    
    return Depends(_get_service)

def get_admin_booking_service():
    """Get booking repository with admin user context"""
    def _get_service(
        admin_user: AdminUser = Depends(get_admin_user),
        booking_repo: BookingRepository = Depends(get_booking_repository)
    ) -> tuple[AdminUser, BookingRepository]:
        return admin_user, booking_repo
    
    return Depends(_get_service)

def get_authenticated_customer_service():
    """Get customer repository with authenticated user context"""
    def _get_service(
        current_user: AuthenticatedUser = Depends(get_current_user),
        customer_repo: CustomerRepository = Depends(get_customer_repository)
    ) -> tuple[AuthenticatedUser, CustomerRepository]:
        return current_user, customer_repo
    
    return Depends(_get_service)

def get_admin_customer_service():
    """Get customer repository with admin user context"""
    def _get_service(
        admin_user: AdminUser = Depends(get_admin_user),
        customer_repo: CustomerRepository = Depends(get_customer_repository)
    ) -> tuple[AdminUser, CustomerRepository]:
        return admin_user, customer_repo
    
    return Depends(_get_service)

# Rate limiting dependencies (unchanged for now)
class RateLimitTier:
    """Rate limiting tier markers"""
    
    @staticmethod
    def public():
        """Public tier rate limiting"""
        async def _public_rate_limit():
            # Rate limiting is handled in middleware
            pass
        return Depends(_public_rate_limit)
    
    @staticmethod
    def admin():
        """Admin tier rate limiting"""
        async def _admin_rate_limit(user: AdminUser = Depends(get_admin_user)):
            # Rate limiting is handled in middleware based on user role
            return user
        return Depends(_admin_rate_limit)
    
    @staticmethod
    def ai():
        """AI tier rate limiting (strict for all users)"""
        async def _ai_rate_limit():
            # Rate limiting is handled in middleware for AI endpoints
            pass
        return Depends(_ai_rate_limit)

# Business Context Dependencies

async def get_business_context(
    container: DependencyInjectionContainer = Depends(get_di_container)
) -> Dict[str, Any]:
    """Get business context information"""
    try:
        # This could be enhanced to use services from the container
        config = container.resolve("app_config") if container.is_registered("app_config") else {}
        
        from datetime import datetime
        import pytz
        
        tz = pytz.timezone("America/Los_Angeles")
        now = datetime.now(tz)
        current_hour = now.hour
        
        # Quiet hours: 9 PM to 8 AM Pacific
        quiet_hours = current_hour >= 21 or current_hour < 8
        
        return {
            "business_info": config.get("business_info", {}),
            "quiet_hours": quiet_hours,
            "timezone": "America/Los_Angeles",
            "current_time": now.isoformat()
        }
    except Exception as e:
        logger.warning(f"Failed to get business context: {e}")
        return {
            "business_info": {},
            "quiet_hours": False,
            "timezone": "America/Los_Angeles"
        }

# API Key authentication (unchanged)
async def verify_api_key(
    x_api_key: Optional[str] = Header(None)
) -> bool:
    """Verify API key from header"""
    if not x_api_key:
        return False
    
    # TODO: Implement API key verification using repository pattern
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

# Pagination dependencies (enhanced)
class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int
    per_page: int
    offset: int
    
    @property
    def limit(self) -> int:
        return self.per_page

async def get_pagination_params(
    page: int = 1,
    per_page: int = 20,
    max_per_page: int = 100
) -> PaginationParams:
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
    
    return PaginationParams(
        page=page,
        per_page=per_page,
        offset=(page - 1) * per_page
    )

# Transaction Management
def with_database_transaction():
    """
    Dependency that provides a database session with automatic transaction management
    """
    def _with_transaction(
        session = Depends(get_database_session)
    ):
        """Wrapper that provides transaction context"""
        class TransactionManager:
            def __init__(self, session):
                self.session = session
                self._committed = False
            
            def __enter__(self):
                return self.session
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                try:
                    if exc_type is None and not self._committed:
                        self.session.commit()
                        self._committed = True
                    elif exc_type is not None:
                        self.session.rollback()
                except Exception as e:
                    logger.error(f"Transaction management error: {e}")
                    self.session.rollback()
                finally:
                    self.session.close()
            
            def commit(self):
                self.session.commit()
                self._committed = True
            
            def rollback(self):
                self.session.rollback()
        
        return TransactionManager(session)
    
    return Depends(_with_transaction)

# Permission Dependencies

def require_permission(required_permission: str):
    """Require specific permission"""
    def _permission_check(
        current_user: AuthenticatedUser = Depends(get_current_user)
    ) -> AuthenticatedUser:
        user_permissions = current_user.permissions or []
        
        if required_permission not in user_permissions and not is_admin_user(current_user.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{required_permission}' required"
            )
        
        return current_user
    
    return Depends(_permission_check)

def require_any_permission(*required_permissions: str):
    """Require any of the specified permissions"""
    def _permission_check(
        current_user: AuthenticatedUser = Depends(get_current_user)
    ) -> AuthenticatedUser:
        user_permissions = current_user.permissions or []
        
        has_permission = any(
            perm in user_permissions for perm in required_permissions
        ) or is_admin_user(current_user.role)
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of these permissions required: {', '.join(required_permissions)}"
            )
        
        return current_user
    
    return Depends(_permission_check)

# Convenience Composition Dependencies

def get_admin_booking_context():
    """Get admin user with booking repository and pagination"""
    def _get_context(
        admin_user: AdminUser = Depends(get_admin_user),
        booking_repo: BookingRepository = Depends(get_booking_repository),
        pagination: PaginationParams = Depends(get_pagination_params)
    ) -> tuple[AdminUser, BookingRepository, PaginationParams]:
        return admin_user, booking_repo, pagination
    
    return Depends(_get_context)

def get_customer_service_context():
    """Get authenticated user with customer repository and business context"""
    def _get_context(
        current_user: AuthenticatedUser = Depends(get_current_user),
        customer_repo: CustomerRepository = Depends(get_customer_repository),
        business_context: Dict[str, Any] = Depends(get_business_context)
    ) -> tuple[AuthenticatedUser, CustomerRepository, Dict[str, Any]]:
        return current_user, customer_repo, business_context
    
    return Depends(_get_context)