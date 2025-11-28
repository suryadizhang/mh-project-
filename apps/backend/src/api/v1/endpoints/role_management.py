"""
Role Management API Endpoints
Handles role assignment and permission management for users
"""

from uuid import UUID
import logging

from api.deps import get_current_user
from core.database import get_db
from fastapi import APIRouter, Depends, HTTPException, status

# MIGRATED: from models.role → db.models.role
from db.models.role import Permission, Role
from db.models.identity import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/roles", tags=["Role Management"])


# ==================== DTOs ====================

from pydantic import BaseModel


class RoleResponse(BaseModel):
    """Role with permission details"""

    id: str
    name: str
    display_name: str
    description: str | None
    is_system_role: bool
    is_active: bool
    permission_count: int
    permissions: list[str]

    class Config:
        from_attributes = True


class PermissionResponse(BaseModel):
    """Permission details"""

    id: str
    name: str
    display_name: str
    description: str | None
    resource: str
    action: str

    class Config:
        from_attributes = True


class AssignRoleRequest(BaseModel):
    """Request to assign role to user"""

    role_id: str


class UserRolesResponse(BaseModel):
    """User's roles and effective permissions"""

    user_id: str
    user_email: str
    user_name: str
    roles: list[RoleResponse]
    all_permissions: list[str]


# ==================== Helper Functions ====================


async def get_current_user_model(
    user_data: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current user as User model from database
    Requires authentication and fetches full User object
    """
    try:
        result = await db.execute(select(User).where(User.id == user_data["id"]))
        user = result.scalar_one_or_none()

        if not user:
            logger.error(f"User {user_data['id']} from token not found in database")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user from database: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to authenticate user",
        )


async def require_super_admin(current_user: User = Depends(get_current_user_model)) -> User:
    """Require super admin access for role management"""
    if not current_user.is_super_admin:
        logger.warning(
            f"User {current_user.id} attempted role management without super admin privileges"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super administrators can manage roles",
        )
    return current_user


# ==================== Endpoints ====================


@router.get("", response_model=list[RoleResponse])
async def list_roles(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(require_super_admin)
):
    """
    List all roles with their permissions

    Requires: Super Admin
    """
    result = await db.execute(
        select(Role)
        .options(selectinload(Role.permissions))
        .where(Role.is_active)
        .order_by(Role.created_at)
    )
    roles = result.scalars().all()

    return [
        RoleResponse(
            id=str(role.id),
            name=role.name.value if hasattr(role.name, "value") else role.name,
            display_name=role.display_name,
            description=role.description,
            is_system_role=role.is_system_role,
            is_active=role.is_active,
            permission_count=len(role.permissions),
            permissions=[
                p.name.value if hasattr(p.name, "value") else p.name for p in role.permissions
            ],
        )
        for role in roles
    ]


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Get role details with all permissions

    Requires: Super Admin
    """
    result = await db.execute(
        select(Role).options(selectinload(Role.permissions)).where(Role.id == role_id)
    )
    role = result.scalar_one_or_none()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Role {role_id} not found"
        )

    return RoleResponse(
        id=str(role.id),
        name=role.name.value if hasattr(role.name, "value") else role.name,
        display_name=role.display_name,
        description=role.description,
        is_system_role=role.is_system_role,
        is_active=role.is_active,
        permission_count=len(role.permissions),
        permissions=[
            p.name.value if hasattr(p.name, "value") else p.name for p in role.permissions
        ],
    )


@router.get("/permissions/all", response_model=list[PermissionResponse])
async def list_all_permissions(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(require_super_admin)
):
    """
    List all available permissions

    Requires: Super Admin
    """
    result = await db.execute(select(Permission).order_by(Permission.resource, Permission.action))
    permissions = result.scalars().all()

    return [
        PermissionResponse(
            id=str(p.id),
            name=p.name.value if hasattr(p.name, "value") else p.name,
            display_name=p.display_name,
            description=p.description,
            resource=p.resource,
            action=p.action,
        )
        for p in permissions
    ]


@router.post("/users/{user_id}/roles", status_code=status.HTTP_200_OK)
async def assign_role_to_user(
    user_id: UUID,
    request: AssignRoleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Assign a role to a user

    Requires: Super Admin
    """
    # Get user
    result = await db.execute(
        select(User).options(selectinload(User.roles)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found"
        )

    # Get role
    role_result = await db.execute(select(Role).where(Role.id == UUID(request.role_id)))
    role = role_result.scalar_one_or_none()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Role {request.role_id} not found"
        )

    # Check if user already has this role
    if role in user.roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User already has role {role.display_name}",
        )

    # Assign role
    user.roles.append(role)
    await db.commit()

    return {
        "success": True,
        "message": f"Role {role.display_name} assigned to {user.email}",
        "user_id": str(user.id),
        "role_id": str(role.id),
    }


@router.delete("/users/{user_id}/roles/{role_id}", status_code=status.HTTP_200_OK)
async def remove_role_from_user(
    user_id: UUID,
    role_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Remove a role from a user

    Requires: Super Admin
    """
    # Get user with roles
    result = await db.execute(
        select(User).options(selectinload(User.roles)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found"
        )

    # Find the role
    role_to_remove = None
    for role in user.roles:
        if role.id == role_id:
            role_to_remove = role
            break

    if not role_to_remove:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User does not have role {role_id}"
        )

    # Remove role
    user.roles.remove(role_to_remove)
    await db.commit()

    return {
        "success": True,
        "message": f"Role {role_to_remove.display_name} removed from {user.email}",
        "user_id": str(user.id),
        "role_id": str(role_id),
    }


@router.get("/users/{user_id}/permissions", response_model=UserRolesResponse)
async def get_user_permissions(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Get user's roles and effective permissions

    Requires: Super Admin
    """
    # Get user with roles and permissions
    result = await db.execute(
        select(User)
        .options(selectinload(User.roles).selectinload(Role.permissions))
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found"
        )

    # Collect all unique permissions
    all_permissions = set()
    for role in user.roles:
        for permission in role.permissions:
            perm_name = (
                permission.name.value if hasattr(permission.name, "value") else permission.name
            )
            all_permissions.add(perm_name)

    # Build response
    roles_data = [
        RoleResponse(
            id=str(role.id),
            name=role.name.value if hasattr(role.name, "value") else role.name,
            display_name=role.display_name,
            description=role.description,
            is_system_role=role.is_system_role,
            is_active=role.is_active,
            permission_count=len(role.permissions),
            permissions=[
                p.name.value if hasattr(p.name, "value") else p.name for p in role.permissions
            ],
        )
        for role in user.roles
    ]

    return UserRolesResponse(
        user_id=str(user.id),
        user_email=user.email,
        user_name=user.full_name or user.email,
        roles=roles_data,
        all_permissions=sorted(all_permissions),
    )
