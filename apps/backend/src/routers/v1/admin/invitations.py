"""
Staff Invitation & Management API
===================================

Endpoints for inviting new staff members (chefs, station managers, admins)
and managing existing staff (deactivation, reactivation).

Implements role-based permission checks per 5-tier RBAC system.

Permission Matrix:
- SUPER_ADMIN: Can invite/manage any role, any station
- ADMIN: Can invite/manage CUSTOMER_SUPPORT, STATION_MANAGER, CHEF for their assigned stations
- STATION_MANAGER: Can invite/manage CHEF for their station only
- CUSTOMER_SUPPORT, CHEF: Cannot invite or manage anyone

Invitation Endpoints:
    POST /api/admin/invitations - Create invitation and send email
    GET /api/admin/invitations - List pending invitations (filtered by caller's scope)
    DELETE /api/admin/invitations/{id} - Revoke pending invitation
    POST /api/admin/invitations/{id}/resend - Resend invitation email

Staff Management Endpoints:
    GET /api/admin/invitations/staff - List staff members (filtered by caller's scope)
    DELETE /api/admin/invitations/staff/{user_id} - Deactivate (soft-delete) staff member
    POST /api/admin/invitations/staff/{user_id}/reactivate - Reactivate staff member
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.auth.station_middleware import AuthenticatedUser, require_station_permission
from core.database import get_db_session
from db.models.identity import (
    Role,
    Station,
    StationUser,
    User,
)
from db.models.identity import UserRole as UserRoleModel
from db.models.identity import (
    UserStatus,
)
from db.models.identity.admin import (
    AdminInvitation,
    InvitationStatus,
    create_admin_invitation,
)
from services.password_reset_service import PasswordResetService
from utils.auth import UserRole, get_role_hierarchy_level

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin-invitations"])


# =============================================================================
# Pydantic Schemas
# =============================================================================


class InvitationCreateRequest(BaseModel):
    """Request model for creating a staff invitation."""

    email: EmailStr = Field(..., description="Email address to invite")
    role: str = Field(
        ...,
        description="Role for the invited user (CHEF, STATION_MANAGER, CUSTOMER_SUPPORT, ADMIN)",
    )
    station_id: Optional[UUID] = Field(
        None,
        description="Station to assign (required for CHEF, STATION_MANAGER roles)",
    )
    notes: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional notes for the invitation",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "chef@example.com",
                "role": "CHEF",
                "station_id": "22222222-2222-2222-2222-222222222222",
                "notes": "New chef for weekend shifts",
            }
        }
    )


class InvitationResponse(BaseModel):
    """Response model for invitation details."""

    id: UUID
    email: str
    role: str
    station_id: Optional[UUID]
    station_name: Optional[str] = None
    status: str
    invited_by_name: Optional[str] = None
    invited_at: datetime
    expires_at: datetime
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class InvitationListResponse(BaseModel):
    """Response model for listing invitations."""

    invitations: list[InvitationResponse]
    total: int


# =============================================================================
# Role-Based Permission Helpers
# =============================================================================


# Roles that can be invited by each role level
INVITABLE_ROLES = {
    UserRole.SUPER_ADMIN: [
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
        UserRole.STATION_MANAGER,
        UserRole.CHEF,
    ],
    UserRole.ADMIN: [
        UserRole.CUSTOMER_SUPPORT,
        UserRole.STATION_MANAGER,
        UserRole.CHEF,
    ],
    UserRole.STATION_MANAGER: [UserRole.CHEF],
    UserRole.CUSTOMER_SUPPORT: [],
    UserRole.CHEF: [],
}


def can_invite_role(inviter_role: UserRole, target_role: UserRole) -> bool:
    """Check if inviter can invite the target role."""
    allowed = INVITABLE_ROLES.get(inviter_role, [])
    return target_role in allowed


async def get_inviter_stations(db: AsyncSession, user_id: UUID, user_role: UserRole) -> list[UUID]:
    """
    Get list of station IDs the user can manage.

    - SUPER_ADMIN: All stations
    - ADMIN: Their assigned stations
    - STATION_MANAGER: Their station only
    """
    if user_role == UserRole.SUPER_ADMIN:
        # All active stations
        result = await db.execute(select(Station.id).where(Station.status == "active"))
        return [row[0] for row in result.fetchall()]

    # For other roles, query station_users assignment
    result = await db.execute(
        select(StationUser.station_id).where(
            and_(
                StationUser.user_id == user_id,
                StationUser.is_active == True,
            )
        )
    )
    return [row[0] for row in result.fetchall()]


async def validate_station_access(
    db: AsyncSession,
    user_id: UUID,
    user_role: UserRole,
    station_id: Optional[UUID],
    target_role: str,
) -> tuple[bool, str]:
    """
    Validate station access for the invitation.

    Returns:
        (is_valid, error_message)
    """
    # Station required for CHEF and STATION_MANAGER
    station_required_roles = ["CHEF", "STATION_MANAGER"]

    if target_role in station_required_roles and not station_id:
        return False, f"station_id is required for {target_role} role"

    if station_id:
        # Check if station exists
        result = await db.execute(select(Station).where(Station.id == station_id))
        station = result.scalar_one_or_none()
        if not station:
            return False, "Station not found"

        # Super admin can access any station
        if user_role == UserRole.SUPER_ADMIN:
            return True, ""

        # Check if inviter has access to this station
        allowed_stations = await get_inviter_stations(db, user_id, user_role)
        if station_id not in allowed_stations:
            return False, "You do not have permission to invite to this station"

    return True, ""


# =============================================================================
# API Endpoints
# =============================================================================


@router.post(
    "",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create staff invitation",
    description="Create a new staff invitation and send invitation email",
)
async def create_invitation(
    request: InvitationCreateRequest,
    current_user: AuthenticatedUser = Depends(require_station_permission("manage_users")),
    db: AsyncSession = Depends(get_db_session),
) -> InvitationResponse:
    """
    Create a staff invitation.

    Permission checks:
    - Must have manage_users permission
    - Can only invite roles lower in hierarchy
    - Can only invite to stations you have access to
    """
    try:
        # Parse and validate roles
        try:
            target_role = UserRole(request.role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {request.role}. Must be one of: CHEF, STATION_MANAGER, CUSTOMER_SUPPORT, ADMIN",
            )

        inviter_role = UserRole(current_user.role) if current_user.role else UserRole.CHEF

        # Check if inviter can invite this role
        if not can_invite_role(inviter_role, target_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You do not have permission to invite {target_role.value} users",
            )

        # Validate station access
        is_valid, error_msg = await validate_station_access(
            db, current_user.id, inviter_role, request.station_id, request.role
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_msg,
            )

        # Check if email already has pending invitation
        existing = await db.execute(
            select(AdminInvitation).where(
                and_(
                    AdminInvitation.email == request.email.lower(),
                    AdminInvitation.status == InvitationStatus.PENDING,
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A pending invitation already exists for this email",
            )

        # Create invitation record using helper function
        invitation = create_admin_invitation(
            email=request.email,
            role=request.role,
            invited_by_id=current_user.id,
            station_id=request.station_id,
            expiry_days=7,  # 7 days to accept
            notes=request.notes,
        )

        db.add(invitation)
        await db.commit()
        await db.refresh(invitation)

        # Get station name if applicable
        station_name = None
        if request.station_id:
            result = await db.execute(select(Station.name).where(Station.id == request.station_id))
            station_name = result.scalar_one_or_none()

        # Send invitation email using password reset service
        password_service = PasswordResetService(db)
        inviter_name = current_user.full_name or current_user.email or "Admin"

        email_sent = await password_service.request_invite(
            email=request.email,
            invited_by=inviter_name,
            role=request.role,
        )

        if not email_sent:
            logger.warning(f"Failed to send invitation email to {request.email[:3]}***")
            # Don't fail the invitation creation, just log it

        logger.info(
            f"✅ Invitation created: {request.email[:3]}*** as {request.role} "
            f"by {current_user.email[:3]}***"
        )

        return InvitationResponse(
            id=invitation.id,
            email=invitation.email,
            role=invitation.role,
            station_id=invitation.station_id,
            station_name=station_name,
            status=invitation.status.value,
            invited_by_name=inviter_name,
            invited_at=invitation.invited_at,
            expires_at=invitation.expires_at,
            notes=invitation.notes,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error creating invitation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create invitation",
        )


@router.get(
    "",
    response_model=InvitationListResponse,
    summary="List pending invitations",
    description="Get list of pending invitations (filtered by caller's scope)",
)
async def list_invitations(
    status_filter: Optional[str] = None,
    current_user: AuthenticatedUser = Depends(require_station_permission("manage_users")),
    db: AsyncSession = Depends(get_db_session),
) -> InvitationListResponse:
    """
    List invitations based on caller's permission scope.

    - SUPER_ADMIN: All invitations
    - ADMIN: Invitations for their stations
    - STATION_MANAGER: Invitations for their station
    """
    try:
        inviter_role = UserRole(current_user.role) if current_user.role else UserRole.CHEF

        # Build base query
        query = select(AdminInvitation)

        # Filter by status if provided
        if status_filter:
            try:
                inv_status = InvitationStatus(status_filter.upper())
                query = query.where(AdminInvitation.status == inv_status)
            except ValueError:
                pass  # Ignore invalid status filter

        # Filter by accessible stations (non-super admin)
        if inviter_role != UserRole.SUPER_ADMIN:
            allowed_stations = await get_inviter_stations(db, current_user.id, inviter_role)
            if allowed_stations:
                query = query.where(AdminInvitation.station_id.in_(allowed_stations))
            else:
                # No stations = no invitations visible
                return InvitationListResponse(invitations=[], total=0)

        # Order by most recent first
        query = query.order_by(AdminInvitation.invited_at.desc())

        result = await db.execute(query)
        invitations = result.scalars().all()

        # Build response with station names
        response_items = []
        for inv in invitations:
            station_name = None
            if inv.station_id:
                station_result = await db.execute(
                    select(Station.name).where(Station.id == inv.station_id)
                )
                station_name = station_result.scalar_one_or_none()

            response_items.append(
                InvitationResponse(
                    id=inv.id,
                    email=inv.email,
                    role=inv.role,
                    station_id=inv.station_id,
                    station_name=station_name,
                    status=inv.status.value,
                    invited_at=inv.invited_at,
                    expires_at=inv.expires_at,
                    notes=inv.notes,
                )
            )

        return InvitationListResponse(
            invitations=response_items,
            total=len(response_items),
        )

    except Exception as e:
        logger.exception(f"Error listing invitations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list invitations",
        )


@router.delete(
    "/{invitation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke invitation",
    description="Revoke a pending invitation",
)
async def revoke_invitation(
    invitation_id: UUID,
    current_user: AuthenticatedUser = Depends(require_station_permission("manage_users")),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """
    Revoke a pending invitation.

    Only pending invitations can be revoked.
    User must have access to the invitation's station.
    """
    try:
        # Get the invitation
        result = await db.execute(
            select(AdminInvitation).where(AdminInvitation.id == invitation_id)
        )
        invitation = result.scalar_one_or_none()

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found",
            )

        # Check if user has access to this invitation
        inviter_role = UserRole(current_user.role) if current_user.role else UserRole.CHEF

        if inviter_role != UserRole.SUPER_ADMIN and invitation.station_id:
            allowed_stations = await get_inviter_stations(db, current_user.id, inviter_role)
            if invitation.station_id not in allowed_stations:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to revoke this invitation",
                )

        # Check if invitation can be revoked
        if not invitation.can_be_revoked():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot revoke invitation with status: {invitation.status.value}",
            )

        # Revoke the invitation
        invitation.status = InvitationStatus.REVOKED
        await db.commit()

        logger.info(
            f"✅ Invitation revoked: {invitation.email[:3]}*** " f"by {current_user.email[:3]}***"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error revoking invitation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke invitation",
        )


@router.post(
    "/{invitation_id}/resend",
    response_model=InvitationResponse,
    summary="Resend invitation email",
    description="Resend the invitation email for a pending invitation",
)
async def resend_invitation(
    invitation_id: UUID,
    current_user: AuthenticatedUser = Depends(require_station_permission("manage_users")),
    db: AsyncSession = Depends(get_db_session),
) -> InvitationResponse:
    """
    Resend invitation email for a pending invitation.

    Updates the expiry date to give another 7 days.
    """
    try:
        from datetime import timedelta

        # Get the invitation
        result = await db.execute(
            select(AdminInvitation).where(AdminInvitation.id == invitation_id)
        )
        invitation = result.scalar_one_or_none()

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found",
            )

        # Check permission
        inviter_role = UserRole(current_user.role) if current_user.role else UserRole.CHEF

        if inviter_role != UserRole.SUPER_ADMIN and invitation.station_id:
            allowed_stations = await get_inviter_stations(db, current_user.id, inviter_role)
            if invitation.station_id not in allowed_stations:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to resend this invitation",
                )

        # Only pending invitations can be resent
        if invitation.status != InvitationStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot resend invitation with status: {invitation.status.value}",
            )

        # Extend expiry
        invitation.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        await db.commit()
        await db.refresh(invitation)

        # Get station name
        station_name = None
        if invitation.station_id:
            station_result = await db.execute(
                select(Station.name).where(Station.id == invitation.station_id)
            )
            station_name = station_result.scalar_one_or_none()

        # Resend email
        password_service = PasswordResetService(db)
        inviter_name = current_user.full_name or current_user.email or "Admin"

        await password_service.request_invite(
            email=invitation.email,
            invited_by=inviter_name,
            role=invitation.role,
        )

        logger.info(
            f"✅ Invitation resent: {invitation.email[:3]}*** " f"by {current_user.email[:3]}***"
        )

        return InvitationResponse(
            id=invitation.id,
            email=invitation.email,
            role=invitation.role,
            station_id=invitation.station_id,
            station_name=station_name,
            status=invitation.status.value,
            invited_by_name=inviter_name,
            invited_at=invitation.invited_at,
            expires_at=invitation.expires_at,
            notes=invitation.notes,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error resending invitation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend invitation",
        )


# =============================================================================
# Staff Management Endpoints (Deactivate/Delete Users)
# =============================================================================


class StaffMemberResponse(BaseModel):
    """Response schema for staff member."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: Optional[str] = None
    role: str
    status: str
    station_id: Optional[UUID] = None
    station_name: Optional[str] = None
    created_at: Optional[datetime] = None


class StaffListResponse(BaseModel):
    """Response schema for staff list."""

    staff: list[StaffMemberResponse]
    total: int


def can_delete_role(inviter_role: UserRole, target_role: UserRole) -> bool:
    """
    Check if inviter can delete target role.

    Uses same hierarchy as invitations:
    - SUPER_ADMIN: Can delete ADMIN, CUSTOMER_SUPPORT, STATION_MANAGER, CHEF
    - ADMIN: Can delete CUSTOMER_SUPPORT, STATION_MANAGER, CHEF (in assigned stations)
    - STATION_MANAGER: Can delete CHEF only (in their station only)
    - CUSTOMER_SUPPORT, CHEF: Cannot delete anyone
    """
    # Reuse the INVITABLE_ROLES permission hierarchy
    allowed_roles = INVITABLE_ROLES.get(inviter_role, [])
    return target_role in allowed_roles


@router.get(
    "/staff",
    response_model=StaffListResponse,
    summary="List staff members",
    description="List staff members that the current user can manage (deactivate/delete).",
)
async def list_staff(
    current_user: AuthenticatedUser = Depends(require_station_permission("manage_users")),
    db: AsyncSession = Depends(get_db_session),
    station_id: Optional[UUID] = None,
    include_inactive: bool = False,
) -> StaffListResponse:
    """
    List staff members that the current user can manage.

    Scoping rules:
    - SUPER_ADMIN: Can see all staff
    - ADMIN: Can see staff in their assigned stations
    - STATION_MANAGER: Can see CHEFs in their station only
    """
    try:
        inviter_role = UserRole(current_user.role) if current_user.role else UserRole.CHEF

        # Get stations the inviter can manage
        inviter_stations = await get_inviter_stations(db, current_user.id, inviter_role)

        # Build query with relationships loaded
        query = select(User).options(
            selectinload(User.user_roles).selectinload(UserRoleModel.role),
            selectinload(User.station_users).selectinload(StationUser.station),
        )

        # Filter by status
        if not include_inactive:
            query = query.where(User.status == UserStatus.ACTIVE)
        else:
            query = query.where(User.status.in_([UserStatus.ACTIVE, UserStatus.INACTIVE]))

        # Exclude super admins from results (can't delete them)
        query = query.where(User.is_super_admin == False)

        # Execute query
        result = await db.execute(query)
        all_users = result.scalars().all()

        # Filter users based on inviter's permissions
        staff_members = []
        for user in all_users:
            # Skip if no roles assigned
            if not user.user_roles:
                continue

            # Get user's primary role
            user_role_name = user.user_roles[0].role.name.upper()
            try:
                target_role = UserRole(user_role_name)
            except ValueError:
                continue  # Skip unknown roles

            # Check if inviter can delete this role
            if not can_delete_role(inviter_role, target_role):
                continue

            # For station-scoped roles, check station access
            user_station_id = None
            user_station_name = None
            if user.station_users:
                user_station_id = user.station_users[0].station_id
                user_station_name = (
                    user.station_users[0].station.name if user.station_users[0].station else None
                )

            # Station scoping for non-super-admins
            if inviter_role != UserRole.SUPER_ADMIN:
                if target_role in [UserRole.CHEF, UserRole.STATION_MANAGER]:
                    if not user_station_id or user_station_id not in inviter_stations:
                        continue

            # Filter by specific station if requested
            if station_id and user_station_id != station_id:
                continue

            staff_members.append(
                StaffMemberResponse(
                    id=user.id,
                    email=user.email,
                    full_name=user.full_name,
                    role=user_role_name,
                    status=user.status.value if user.status else "UNKNOWN",
                    station_id=user_station_id,
                    station_name=user_station_name,
                    created_at=user.created_at,
                )
            )

        logger.info(
            f"📋 Staff list: {len(staff_members)} members returned "
            f"for {current_user.email[:3]}*** (role: {inviter_role.value})"
        )

        return StaffListResponse(staff=staff_members, total=len(staff_members))

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error listing staff: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list staff members",
        )


@router.delete(
    "/staff/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate staff member",
    description="Soft-delete a staff member by setting status to INACTIVE. "
    "User will no longer be able to log in.",
)
async def delete_staff(
    user_id: UUID,
    current_user: AuthenticatedUser = Depends(require_station_permission("manage_users")),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """
    Deactivate (soft-delete) a staff member.

    This sets the user's status to INACTIVE, preventing login.
    The user record is preserved for audit trail purposes.

    Permission rules:
    - SUPER_ADMIN: Can deactivate ADMIN, CUSTOMER_SUPPORT, STATION_MANAGER, CHEF
    - ADMIN: Can deactivate CUSTOMER_SUPPORT, STATION_MANAGER, CHEF (in assigned stations)
    - STATION_MANAGER: Can deactivate CHEF only (in their station only)

    Raises:
        403: If caller doesn't have permission to delete the target user
        404: If user not found
        400: If trying to delete self or super admin
    """
    try:
        inviter_role = UserRole(current_user.role) if current_user.role else UserRole.CHEF

        # Prevent self-deletion
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own account",
            )

        # Fetch target user with roles and station assignments
        result = await db.execute(
            select(User)
            .options(
                selectinload(User.user_roles).selectinload(UserRoleModel.role),
                selectinload(User.station_users),
            )
            .where(User.id == user_id)
        )
        target_user = result.scalar_one_or_none()

        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Prevent deactivating super admins
        if target_user.is_super_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate super admin accounts",
            )

        # Check if already inactive
        if target_user.status == UserStatus.INACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already inactive",
            )

        # Get target user's role
        if not target_user.user_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User has no assigned role",
            )

        target_role_name = target_user.user_roles[0].role.name.upper()
        try:
            target_role = UserRole(target_role_name)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown role: {target_role_name}",
            )

        # Check permission hierarchy
        if not can_delete_role(inviter_role, target_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You don't have permission to deactivate {target_role.value} users",
            )

        # For station-scoped roles, validate station access
        if target_role in [UserRole.CHEF, UserRole.STATION_MANAGER]:
            if inviter_role != UserRole.SUPER_ADMIN:
                # Get target user's station
                target_station_id = None
                if target_user.station_users:
                    target_station_id = target_user.station_users[0].station_id

                if not target_station_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Target user has no station assignment",
                    )

                # Get inviter's manageable stations
                inviter_stations = await get_inviter_stations(db, current_user.id, inviter_role)

                if target_station_id not in inviter_stations:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You can only deactivate staff from your assigned stations",
                    )

        # Perform soft-delete
        target_user.status = UserStatus.INACTIVE
        target_user.updated_at = datetime.now(timezone.utc)

        await db.commit()

        logger.info(
            f"🗑️ Staff deactivated: {target_user.email[:3]}*** (role: {target_role.value}) "
            f"by {current_user.email[:3]}*** (role: {inviter_role.value})"
        )

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error deactivating staff: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate staff member",
        )


@router.post(
    "/staff/{user_id}/reactivate",
    response_model=StaffMemberResponse,
    summary="Reactivate staff member",
    description="Reactivate a previously deactivated staff member.",
)
async def reactivate_staff(
    user_id: UUID,
    current_user: AuthenticatedUser = Depends(require_station_permission("manage_users")),
    db: AsyncSession = Depends(get_db_session),
) -> StaffMemberResponse:
    """
    Reactivate a previously deactivated staff member.

    Sets user status back to ACTIVE, allowing them to log in again.
    Uses same permission rules as delete_staff.
    """
    try:
        inviter_role = UserRole(current_user.role) if current_user.role else UserRole.CHEF

        # Fetch target user with roles and station assignments
        result = await db.execute(
            select(User)
            .options(
                selectinload(User.user_roles).selectinload(UserRoleModel.role),
                selectinload(User.station_users).selectinload(StationUser.station),
            )
            .where(User.id == user_id)
        )
        target_user = result.scalar_one_or_none()

        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Check if already active
        if target_user.status == UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already active",
            )

        # Get target user's role
        if not target_user.user_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User has no assigned role",
            )

        target_role_name = target_user.user_roles[0].role.name.upper()
        try:
            target_role = UserRole(target_role_name)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown role: {target_role_name}",
            )

        # Check permission hierarchy
        if not can_delete_role(inviter_role, target_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You don't have permission to reactivate {target_role.value} users",
            )

        # For station-scoped roles, validate station access
        if target_role in [UserRole.CHEF, UserRole.STATION_MANAGER]:
            if inviter_role != UserRole.SUPER_ADMIN:
                target_station_id = None
                if target_user.station_users:
                    target_station_id = target_user.station_users[0].station_id

                if target_station_id:
                    inviter_stations = await get_inviter_stations(db, current_user.id, inviter_role)
                    if target_station_id not in inviter_stations:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="You can only reactivate staff from your assigned stations",
                        )

        # Reactivate user
        target_user.status = UserStatus.ACTIVE
        target_user.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(target_user)

        # Get station info for response
        user_station_id = None
        user_station_name = None
        if target_user.station_users:
            user_station_id = target_user.station_users[0].station_id
            user_station_name = (
                target_user.station_users[0].station.name
                if target_user.station_users[0].station
                else None
            )

        logger.info(
            f"✅ Staff reactivated: {target_user.email[:3]}*** (role: {target_role.value}) "
            f"by {current_user.email[:3]}*** (role: {inviter_role.value})"
        )

        return StaffMemberResponse(
            id=target_user.id,
            email=target_user.email,
            full_name=target_user.full_name,
            role=target_role_name,
            status=target_user.status.value,
            station_id=user_station_id,
            station_name=user_station_name,
            created_at=target_user.created_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error reactivating staff: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reactivate staff member",
        )
