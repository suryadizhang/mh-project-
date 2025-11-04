"""
Admin User Management Endpoints
Handles user approval, rejection, and management for super admins
"""

from datetime import datetime
import logging

from api.v1.schemas.user import UserListResponse, UserResponse
from core.database import get_db
from core.exceptions import ForbiddenException, ValidationException
from core.security import require_auth
from fastapi import APIRouter, Depends, HTTPException, Query, status
from models.user import User, UserStatus
from services.email_service import email_service
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_current_user_model(
    user_data: dict = Depends(require_auth),
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
    """Dependency to ensure user is a super admin"""
    if not current_user.is_super_admin:
        logger.warning(f"User {current_user.id} attempted super admin action without privileges")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can access this resource",
        )
    return current_user


@router.get("/admin/users", response_model=UserListResponse)
async def list_users(
    status_filter: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    List all users with optional filtering
    Requires super admin privileges
    """
    try:
        query = select(User)

        # Apply status filter if provided
        if status_filter:
            query = query.where(User.status == status_filter)

        # Order by creation date (newest first)
        query = query.order_by(User.created_at.desc())

        # Apply pagination
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        users = result.scalars().all()

        return {"success": True, "data": users, "message": f"Retrieved {len(users)} users"}
    except Exception as e:
        logger.error(f"Error listing users: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve users"
        )


@router.get("/admin/users/pending", response_model=UserListResponse)
async def list_pending_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    List all users pending approval
    Requires super admin privileges
    """
    try:
        query = (
            select(User).where(User.status == UserStatus.PENDING).order_by(User.created_at.desc())
        )

        result = await db.execute(query)
        users = result.scalars().all()

        return {"success": True, "data": users, "message": f"Found {len(users)} pending users"}
    except Exception as e:
        logger.error(f"Error listing pending users: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pending users",
        )


@router.post("/admin/users/{user_id}/approve", response_model=UserResponse)
async def approve_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Approve a pending user
    Changes status from PENDING to ACTIVE
    Requires super admin privileges
    """
    try:
        # Find user
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found"
            )

        if user.status != UserStatus.PENDING:
            raise ValidationException(
                f"User is already {user.status}. Only pending users can be approved."
            )

        # Update user status
        user.status = UserStatus.ACTIVE
        user.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(user)

        # Send approval email
        try:
            email_service.send_approval_email(user.email, user.full_name)
        except Exception as e:
            logger.warning(f"Failed to send approval email to {user.email}: {e}")

        logger.info(f"User {user.email} approved by super admin {current_user.email}")

        return {
            "success": True,
            "data": user,
            "message": f"User {user.email} has been approved and activated",
        }
    except HTTPException:
        raise
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error approving user {user_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to approve user"
        )


@router.post("/admin/users/{user_id}/reject", response_model=UserResponse)
async def reject_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Reject a pending user
    Changes status from PENDING to DEACTIVATED
    Requires super admin privileges
    """
    try:
        # Find user
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found"
            )

        if user.status != UserStatus.PENDING:
            raise ValidationException(
                f"User is already {user.status}. Only pending users can be rejected."
            )

        # Update user status
        user.status = UserStatus.DEACTIVATED
        user.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(user)

        # Send rejection email
        try:
            email_service.send_rejection_email(user.email, user.full_name, reason=None)
        except Exception as e:
            logger.warning(f"Failed to send rejection email to {user.email}: {e}")

        logger.info(f"User {user.email} rejected by super admin {current_user.email}")

        return {"success": True, "data": user, "message": f"User {user.email} has been rejected"}
    except HTTPException:
        raise
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error rejecting user {user_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reject user"
        )


@router.post("/admin/users/{user_id}/suspend", response_model=UserResponse)
async def suspend_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Suspend an active user
    Changes status from ACTIVE to SUSPENDED
    Requires super admin privileges
    """
    try:
        # Find user
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found"
            )

        if user.is_super_admin:
            raise ForbiddenException("Cannot suspend a super admin")

        if user.status != UserStatus.ACTIVE:
            raise ValidationException(f"User is {user.status}. Only active users can be suspended.")

        # Update user status
        user.status = UserStatus.SUSPENDED
        user.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(user)

        # Send suspension email
        try:
            email_service.send_suspension_email(user.email, user.full_name, reason=None)
        except Exception as e:
            logger.warning(f"Failed to send suspension email to {user.email}: {e}")

        logger.info(f"User {user.email} suspended by super admin {current_user.email}")

        return {"success": True, "data": user, "message": f"User {user.email} has been suspended"}
    except HTTPException:
        raise
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ForbiddenException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Error suspending user {user_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to suspend user"
        )


@router.get("/admin/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Get detailed information about a specific user
    Requires super admin privileges
    """
    try:
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found"
            )

        return {"success": True, "data": user, "message": "User retrieved successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve user"
        )
