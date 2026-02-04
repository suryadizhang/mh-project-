"""
Admin User Management API
=========================

CRUD endpoints for managing admin users (staff, chefs, station managers, etc.)
Implements 5-tier RBAC system.

Permission Matrix:
- SUPER_ADMIN: Full access to all users and operations
- ADMIN: Can view/manage users in their assigned stations (except super_admin)
- STATION_MANAGER: Can view users in their station
- CUSTOMER_SUPPORT, CHEF: Can only view own profile

Endpoints:
    GET    /api/v1/admin/users           - List all admin users
    POST   /api/v1/admin/users           - Create new admin user
    GET    /api/v1/admin/users/{id}      - Get user by ID
    PUT    /api/v1/admin/users/{id}      - Update user
    DELETE /api/v1/admin/users/{id}      - Soft-delete user
    POST   /api/v1/admin/users/{id}/reactivate - Reactivate user
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.security import decode_access_token
from db.models.identity import Role, Station, StationUser, User
from db.models.identity import UserRole as UserRoleModel
from db.models.identity import UserStatus
from utils.auth import UserRole

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin-users"])

# HTTP Bearer security scheme
security = HTTPBearer()


# =============================================================================
# Authentication Dependencies
# =============================================================================


async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Get current user from JWT token.
    Validates token and fetches full User model from database.
    """
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        result = await db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is {user.status.value.lower()}",
            )

        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid user ID in token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_super_admin(
    current_user: User = Depends(get_current_user_from_token),
) -> User:
    """Dependency to ensure user is a super admin."""
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin privileges required",
        )
    return current_user


async def require_admin_or_super_admin(
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """Dependency to ensure user is admin or super admin."""
    if current_user.is_super_admin:
        return current_user

    # Check if user has ADMIN role
    result = await db.execute(
        select(Role.role_type)
        .join(UserRoleModel, UserRoleModel.role_id == Role.id)
        .where(UserRoleModel.user_id == current_user.id)
    )
    roles = [str(r).upper() for r in result.scalars().all()]

    if "ADMIN" not in roles and "SUPER_ADMIN" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


async def require_view_users_permission(
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Dependency to ensure user can view users.
    Super admins, admins, and station managers can view users.
    """
    if current_user.is_super_admin:
        return current_user

    # Get user's role
    result = await db.execute(
        select(Role.role_type)
        .join(UserRoleModel, UserRoleModel.role_id == Role.id)
        .where(UserRoleModel.user_id == current_user.id)
    )
    roles = [str(r).upper() for r in result.scalars().all()]

    allowed_roles = {"SUPER_ADMIN", "ADMIN", "STATION_MANAGER", "CUSTOMER_SUPPORT"}
    if not any(role in allowed_roles for role in roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view users",
        )
    return current_user


# =============================================================================
# Pydantic Schemas
# =============================================================================


class UserCreateRequest(BaseModel):
    """Request model for creating a new admin user."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="Initial password")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    role: str = Field(
        ...,
        description="User role (CHEF, STATION_MANAGER, CUSTOMER_SUPPORT, ADMIN)",
    )
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    station_id: Optional[UUID] = Field(
        None,
        description="Station to assign (required for CHEF, STATION_MANAGER)",
    )
    is_active: bool = Field(default=True, description="Whether user is active")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "newchef@myhibachi.com",
                "password": "SecurePassword123!",
                "first_name": "John",
                "last_name": "Chef",
                "role": "CHEF",
                "phone": "+1-555-0100",
                "station_id": "22222222-2222-2222-2222-222222222222",
                "is_active": True,
            }
        }
    )


class UserUpdateRequest(BaseModel):
    """Request model for updating a user."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    role: Optional[str] = Field(None, description="New role for user")
    station_id: Optional[UUID] = Field(None, description="New station assignment")
    is_active: Optional[bool] = Field(None, description="Active status")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "first_name": "Updated",
                "last_name": "User",
            }
        }
    )


class UserResponse(BaseModel):
    """Response model for user details."""

    id: UUID
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: str
    status: str
    is_verified: bool = False
    is_super_admin: bool = False
    station_id: Optional[UUID] = None
    station_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """Response model for listing users with pagination."""

    items: list[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# Helper Functions
# =============================================================================


async def get_user_role(db: AsyncSession, user_id: UUID) -> Optional[str]:
    """Get the primary role for a user."""
    result = await db.execute(
        select(Role.role_type)
        .join(UserRoleModel, UserRoleModel.role_id == Role.id)
        .where(UserRoleModel.user_id == user_id)
        .order_by(Role.id)  # Prefer first assigned role
        .limit(1)
    )
    role = result.scalar_one_or_none()
    return str(role).upper() if role else None


async def get_user_station(
    db: AsyncSession, user_id: UUID
) -> tuple[Optional[UUID], Optional[str]]:
    """Get the primary station assignment for a user."""
    result = await db.execute(
        select(Station.id, Station.name)
        .join(StationUser, StationUser.station_id == Station.id)
        .where(
            and_(
                StationUser.user_id == user_id,
                StationUser.is_active == True,
            )
        )
        .limit(1)
    )
    row = result.first()
    if row:
        return row[0], row[1]
    return None, None


async def get_accessible_user_ids(
    db: AsyncSession,
    current_user: User,
) -> Optional[list[UUID]]:
    """
    Get list of user IDs the current user can manage.
    Returns None if user has access to all users (super_admin).
    """
    if current_user.is_super_admin:
        return None  # Access to all

    # Get current user's role
    user_role = await get_user_role(db, current_user.id)
    if user_role == "SUPER_ADMIN":
        return None

    # For ADMIN: Users in their assigned stations
    if user_role == "ADMIN":
        # Get admin's stations
        station_result = await db.execute(
            select(StationUser.station_id).where(
                and_(
                    StationUser.user_id == current_user.id,
                    StationUser.is_active == True,
                )
            )
        )
        station_ids = [row[0] for row in station_result.fetchall()]

        if not station_ids:
            return []

        # Get users in those stations
        user_result = await db.execute(
            select(StationUser.user_id).where(StationUser.station_id.in_(station_ids))
        )
        return [row[0] for row in user_result.fetchall()]

    # For STATION_MANAGER: Users in their station
    if user_role == "STATION_MANAGER":
        station_result = await db.execute(
            select(StationUser.station_id).where(
                and_(
                    StationUser.user_id == current_user.id,
                    StationUser.is_active == True,
                )
            )
        )
        station_ids = [row[0] for row in station_result.fetchall()]

        if not station_ids:
            return []

        user_result = await db.execute(
            select(StationUser.user_id).where(StationUser.station_id.in_(station_ids))
        )
        return [row[0] for row in user_result.fetchall()]

    # Others can only view themselves
    return [current_user.id]


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    role: Optional[str] = Query(None, description="Filter by role"),
    status: Optional[str] = Query(None, description="Filter by status"),
    station_id: Optional[UUID] = Query(None, description="Filter by station"),
    current_user: User = Depends(require_view_users_permission),
    db: AsyncSession = Depends(get_db_session),
) -> UserListResponse:
    """
    List all admin users with pagination and filtering.

    Only super_admin can see all users.
    Other roles see users based on their station assignments.
    """
    try:
        # Get accessible user IDs based on current user's permissions
        accessible_ids = await get_accessible_user_ids(db, current_user)

        # Build base query
        query = select(User)
        count_query = select(func.count(User.id))

        # Filter by accessible users if not super_admin
        if accessible_ids is not None:
            query = query.where(User.id.in_(accessible_ids))
            count_query = count_query.where(User.id.in_(accessible_ids))

        # Search filter
        if search:
            search_filter = or_(
                User.email.ilike(f"%{search}%"),
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%"),
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        # Status filter
        if status:
            try:
                status_enum = UserStatus[status.upper()]
                query = query.where(User.status == status_enum)
                count_query = count_query.where(User.status == status_enum)
            except KeyError:
                pass  # Invalid status, ignore filter

        # Station filter
        if station_id:
            station_users = await db.execute(
                select(StationUser.user_id).where(StationUser.station_id == station_id)
            )
            station_user_ids = [row[0] for row in station_users.fetchall()]
            query = query.where(User.id.in_(station_user_ids))
            count_query = count_query.where(User.id.in_(station_user_ids))

        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(User.created_at.desc())

        # Execute query
        result = await db.execute(query)
        users = result.scalars().all()

        # Build response items with role and station info
        items = []
        for user in users:
            user_role = await get_user_role(db, user.id)
            station_id_val, station_name = await get_user_station(db, user.id)

            # Apply role filter if specified
            if role and user_role and user_role.upper() != role.upper():
                continue

            items.append(
                UserResponse(
                    id=user.id,
                    email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    full_name=user.full_name
                    or f"{user.first_name or ''} {user.last_name or ''}".strip(),
                    phone=user.phone,
                    role=user_role or "UNKNOWN",
                    status=user.status.value if user.status else "active",
                    is_verified=user.is_verified,
                    is_super_admin=user.is_super_admin,
                    station_id=station_id_val,
                    station_name=station_name,
                    created_at=user.created_at,
                    updated_at=user.updated_at,
                    last_login_at=user.last_login_at,
                )
            )

        # Recalculate total if role filter was applied (post-filter)
        actual_total = len(items) if role else total
        total_pages = (actual_total + page_size - 1) // page_size

        # TODO: Add audit logging
        # await audit_log_action(
        #     action="list_users",
        #     auth_user=current_user,
        #     db=db,
        #     resource_type="user",
        #     details={"count": len(items), "page": page},
        # )

        return UserListResponse(
            items=items,
            total=actual_total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    except Exception as e:
        logger.error(f"Error listing users: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve users",
        )


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: UserCreateRequest,
    current_user: User = Depends(require_admin_or_super_admin),
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """
    Create a new admin user.

    Only super_admin and admin can create users.
    Admins can only create users with lower roles in their stations.
    """
    try:
        # Check if email already exists
        existing = await db.execute(select(User).where(User.email == request.email))
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )

        # Validate role
        try:
            target_role = UserRole[request.role.upper()]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {request.role}. Valid roles: CHEF, STATION_MANAGER, CUSTOMER_SUPPORT, ADMIN",
            )

        # Permission check: Only super_admin can create super_admin or admin
        current_role = await get_user_role(db, current_user.user_id)
        if not current_user.is_super_admin and current_role != "SUPER_ADMIN":
            if target_role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only super_admin can create admin users",
                )

        # Station validation for station-scoped roles
        station_required = target_role in [UserRole.CHEF, UserRole.STATION_MANAGER]
        if station_required and not request.station_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"station_id is required for {request.role} role",
            )

        # Validate station exists
        station = None
        if request.station_id:
            station_result = await db.execute(
                select(Station).where(Station.id == request.station_id)
            )
            station = station_result.scalar_one_or_none()
            if not station:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Station not found",
                )

        # Hash password
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        password_hash = pwd_context.hash(request.password)

        # Create user
        user = User(
            email=request.email,
            password_hash=password_hash,
            first_name=request.first_name,
            last_name=request.last_name,
            full_name=f"{request.first_name} {request.last_name}",
            phone=request.phone,
            status=UserStatus.ACTIVE if request.is_active else UserStatus.INACTIVE,
            is_verified=True,  # Admin-created users are pre-verified
            is_email_verified=True,
        )
        db.add(user)
        await db.flush()  # Get user.id

        # Assign role
        role_result = await db.execute(
            select(Role).where(Role.role_type == target_role.value.lower())
        )
        role_record = role_result.scalar_one_or_none()
        if role_record:
            user_role = UserRoleModel(
                user_id=user.id,
                role_id=role_record.id,
            )
            db.add(user_role)

        # Assign to station
        if request.station_id:
            station_user = StationUser(
                user_id=user.id,
                station_id=request.station_id,
                role=target_role.value.lower(),
                is_active=True,
            )
            db.add(station_user)

        await db.commit()
        await db.refresh(user)

        await audit_log_action(
            action="create_user",
            auth_user=current_user,
            db=db,
            resource_type="user",
            resource_id=str(user.id),
            details={
                "email": user.email,
                "role": request.role,
                "station_id": str(request.station_id) if request.station_id else None,
            },
        )

        return UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            phone=user.phone,
            role=request.role,
            status=user.status.value,
            is_verified=user.is_verified,
            is_super_admin=user.is_super_admin,
            station_id=request.station_id,
            station_name=station.name if station else None,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login_at=user.last_login_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to create user: {str(e)}",
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(require_view_users_permission),
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """
    Get a specific user by ID.
    """
    try:
        # Check access permissions
        accessible_ids = await get_accessible_user_ids(db, current_user)
        if accessible_ids is not None and user_id not in accessible_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this user",
            )

        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        user_role = await get_user_role(db, user.id)
        station_id_val, station_name = await get_user_station(db, user.id)

        return UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            phone=user.phone,
            role=user_role or "UNKNOWN",
            status=user.status.value if user.status else "active",
            is_verified=user.is_verified,
            is_super_admin=user.is_super_admin,
            station_id=station_id_val,
            station_name=station_name,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login_at=user.last_login_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve user",
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    request: UserUpdateRequest,
    current_user: User = Depends(require_admin_or_super_admin),
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """
    Update an existing user.

    Super_admin can update any user.
    Others can only update users in their scope.
    """
    try:
        # Check access permissions
        accessible_ids = await get_accessible_user_ids(db, current_user)
        if accessible_ids is not None and user_id not in accessible_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update this user",
            )

        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Prevent non-super_admin from modifying super_admin users
        if user.is_super_admin and not current_user.is_super_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot modify super_admin user",
            )

        # Update fields
        if request.first_name is not None:
            user.first_name = request.first_name
        if request.last_name is not None:
            user.last_name = request.last_name
        if request.first_name or request.last_name:
            user.full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        if request.phone is not None:
            user.phone = request.phone
        if request.is_active is not None:
            user.status = (
                UserStatus.ACTIVE if request.is_active else UserStatus.INACTIVE
            )

        # Role update (only super_admin)
        if request.role is not None:
            if not current_user.is_super_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only super_admin can change user roles",
                )
            # Update role logic would go here
            # For now, just log it
            logger.info(f"Role change requested for user {user_id} to {request.role}")

        # Station update
        if request.station_id is not None:
            # Validate station
            station_result = await db.execute(
                select(Station).where(Station.id == request.station_id)
            )
            if not station_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Station not found",
                )
            # Update station assignment
            # Deactivate old assignments
            await db.execute(
                update(StationUser)
                .where(StationUser.user_id == user_id)
                .values(is_active=False)
            )
            # Create new assignment
            station_user = StationUser(
                user_id=user_id,
                station_id=request.station_id,
                role=await get_user_role(db, user_id) or "unknown",
                is_active=True,
            )
            db.add(station_user)

        user.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(user)

        user_role = await get_user_role(db, user.id)
        station_id_val, station_name = await get_user_station(db, user.id)

        await audit_log_action(
            action="update_user",
            auth_user=current_user,
            db=db,
            resource_type="user",
            resource_id=str(user.id),
            details={"changes": request.model_dump(exclude_none=True)},
        )

        return UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            phone=user.phone,
            role=user_role or "UNKNOWN",
            status=user.status.value if user.status else "active",
            is_verified=user.is_verified,
            is_super_admin=user.is_super_admin,
            station_id=station_id_val,
            station_name=station_name,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login_at=user.last_login_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to update user: {str(e)}",
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Soft-delete a user (set status to INACTIVE).

    Only super_admin can delete users.
    Cannot delete yourself or other super_admins (unless you're super_admin).
    """
    try:
        # Only super_admin can delete users
        if not current_user.is_super_admin:
            current_role = await get_user_role(db, current_user.id)
            if current_role != "SUPER_ADMIN":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only super_admin can delete users",
                )

        # Cannot delete yourself
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account",
            )

        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Cannot delete super_admin
        if user.is_super_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete super_admin user",
            )

        # Soft delete - set status to INACTIVE
        user.status = UserStatus.INACTIVE
        user.updated_at = datetime.now(timezone.utc)

        # Deactivate station assignments
        await db.execute(
            update(StationUser)
            .where(StationUser.user_id == user_id)
            .values(is_active=False)
        )

        await db.commit()

        await audit_log_action(
            action="delete_user",
            auth_user=current_user,
            db=db,
            resource_type="user",
            resource_id=str(user_id),
            details={"email": user.email, "soft_delete": True},
        )

        return None

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to delete user: {str(e)}",
        )


@router.post("/{user_id}/reactivate", response_model=UserResponse)
async def reactivate_user(
    user_id: UUID,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """
    Reactivate a previously deactivated user.
    """
    try:
        # Only super_admin can reactivate
        if not current_user.is_super_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super_admin can reactivate users",
            )

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        user.status = UserStatus.ACTIVE
        user.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(user)

        user_role = await get_user_role(db, user.id)
        station_id_val, station_name = await get_user_station(db, user.id)

        await audit_log_action(
            action="reactivate_user",
            auth_user=current_user,
            db=db,
            resource_type="user",
            resource_id=str(user_id),
            details={"email": user.email},
        )

        return UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            phone=user.phone,
            role=user_role or "UNKNOWN",
            status=user.status.value,
            is_verified=user.is_verified,
            is_super_admin=user.is_super_admin,
            station_id=station_id_val,
            station_name=station_name,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login_at=user.last_login_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error reactivating user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to reactivate user: {str(e)}",
        )
