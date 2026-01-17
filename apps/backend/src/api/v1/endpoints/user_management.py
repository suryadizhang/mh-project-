"""
Admin User Management Endpoints
Handles user approval, rejection, and management for super admins
"""

from datetime import datetime, timezone
import logging
from typing import Optional

from api.v1.schemas.user import UserListResponse, UserResponse
from core.database import get_db
from core.exceptions import ForbiddenException, ValidationException
from core.security import require_auth, hash_password
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field
from db.models.identity import User, UserStatus, AuthProvider
from services.email_service import email_service
from services.password_reset_service import PasswordResetService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ==================== REQUEST SCHEMAS ====================


class CreateUserRequest(BaseModel):
    """Request schema for creating a new admin user"""

    email: EmailStr = Field(..., description="User's email address")
    full_name: str = Field(..., min_length=1, max_length=255, description="Full name")
    password: Optional[str] = Field(
        None, min_length=8, description="Optional password. If not provided, sends invite email."
    )
    is_super_admin: bool = Field(False, description="Grant super admin privileges")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "newadmin@company.com",
                "full_name": "John Smith",
                "password": "SecurePass123!",
                "is_super_admin": False,
            }
        }


class UpdateUserRequest(BaseModel):
    """Request schema for updating an existing user"""

    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[str] = Field(None, description="User status: active, inactive, suspended")
    is_super_admin: Optional[bool] = Field(None, description="Super admin privileges")

    class Config:
        json_schema_extra = {
            "example": {
                "full_name": "John Smith Updated",
                "status": "active",
                "is_super_admin": False,
            }
        }


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
        user.updated_at = datetime.now(timezone.utc)

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
        user.updated_at = datetime.now(timezone.utc)

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
        user.updated_at = datetime.now(timezone.utc)

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


# ==================== CREATE USER ====================


@router.post("/admin/users", response_model=UserResponse)
async def create_user(
    request: CreateUserRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Create a new admin user.

    If password is provided, user is created with that password.
    If password is NOT provided, sends a password reset email for the user to set their password.

    Requires super admin privileges.
    """
    try:
        email_lower = request.email.lower().strip()

        # Check if user already exists
        existing = await db.execute(select(User).where(User.email == email_lower))
        if existing.scalar_one_or_none():
            raise ValidationException(f"User with email {email_lower} already exists")

        # Create user
        new_user = User(
            email=email_lower,
            full_name=request.full_name.strip(),
            status=UserStatus.ACTIVE,  # Admin-created users are active immediately
            is_super_admin=request.is_super_admin,
            is_verified=True,  # Admin-created users are pre-verified
            is_email_verified=True,
            auth_provider=AuthProvider.EMAIL,
        )

        # Set password if provided, otherwise will send reset email
        if request.password:
            new_user.password_hash = hash_password(request.password)
        else:
            new_user.password_hash = None  # Will need to set via reset link

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        # If no password provided, send invitation email with password setup link
        if not request.password:
            try:
                password_reset_service = PasswordResetService(db)
                invited_by = current_user.full_name or current_user.email
                await password_reset_service.request_invite(email_lower, invited_by=invited_by)
                logger.info(f"Sent invitation email to new user {email_lower}")
            except Exception as e:
                logger.warning(f"Failed to send invitation email to {email_lower}: {e}")

        logger.info(
            f"Admin user {email_lower} created by super admin {current_user.email}"
            + (" (with password)" if request.password else " (invite sent)")
        )

        return {
            "success": True,
            "data": new_user,
            "message": f"User {email_lower} created successfully"
            + ("" if request.password else ". Invitation email sent."),
        }

    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user"
        )


# ==================== UPDATE USER ====================


@router.put("/admin/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    request: UpdateUserRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Update an existing user's profile.

    Requires super admin privileges.
    """
    try:
        # Find user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found"
            )

        # Prevent removing super admin from yourself
        if (
            str(user.id) == str(current_user.id)
            and request.is_super_admin is False
            and user.is_super_admin
        ):
            raise ForbiddenException("Cannot remove super admin privileges from yourself")

        # Update fields
        if request.full_name is not None:
            user.full_name = request.full_name.strip()

        if request.status is not None:
            try:
                user.status = UserStatus(request.status.lower())
            except ValueError:
                raise ValidationException(
                    f"Invalid status: {request.status}. Must be one of: active, inactive, suspended, pending"
                )

        if request.is_super_admin is not None:
            user.is_super_admin = request.is_super_admin

        user.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(user)

        logger.info(f"User {user.email} updated by super admin {current_user.email}")

        return {
            "success": True,
            "data": user,
            "message": f"User {user.email} updated successfully",
        }

    except (ValidationException, ForbiddenException) as e:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
                if isinstance(e, ValidationException)
                else status.HTTP_403_FORBIDDEN
            ),
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update user"
        )


# ==================== DELETE USER ====================


@router.delete("/admin/users/{user_id}", response_model=UserResponse)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Delete a user (soft delete - sets status to INACTIVE).

    Cannot delete:
    - Yourself
    - Other super admins

    Requires super admin privileges.
    """
    try:
        # Find user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found"
            )

        # Prevent self-deletion
        if str(user.id) == str(current_user.id):
            raise ForbiddenException("Cannot delete yourself")

        # Prevent deleting super admins
        if user.is_super_admin:
            raise ForbiddenException(
                "Cannot delete a super admin. Remove super admin privileges first."
            )

        # Soft delete: set status to INACTIVE
        user.status = UserStatus.INACTIVE
        user.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(user)

        logger.info(f"User {user.email} deleted (soft) by super admin {current_user.email}")

        return {
            "success": True,
            "data": user,
            "message": f"User {user.email} has been deleted",
        }

    except ForbiddenException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete user"
        )


# ==================== FORCE PASSWORD RESET ====================


@router.post("/admin/users/{user_id}/force-reset-password", response_model=UserResponse)
async def force_reset_password(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Force a password reset for a user.

    Sends a password reset email to the user's email address.
    The user will need to click the link and set a new password.

    Requires super admin privileges.
    """
    try:
        # Find user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found"
            )

        # Trigger password reset
        password_reset_service = PasswordResetService(db)
        await password_reset_service.request_reset(user.email)

        logger.info(f"Password reset forced for {user.email} by super admin {current_user.email}")

        return {
            "success": True,
            "data": user,
            "message": f"Password reset email sent to {user.email}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error forcing password reset for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send password reset email",
        )


# ==================== REACTIVATE USER ====================


@router.post("/admin/users/{user_id}/reactivate", response_model=UserResponse)
async def reactivate_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Reactivate a suspended or inactive user.

    Changes status from SUSPENDED/INACTIVE to ACTIVE.
    Requires super admin privileges.
    """
    try:
        # Find user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found"
            )

        if user.status == UserStatus.ACTIVE:
            raise ValidationException("User is already active")

        if user.status == UserStatus.PENDING:
            raise ValidationException(
                "Cannot reactivate pending user. Use approve endpoint instead."
            )

        # Reactivate user
        user.status = UserStatus.ACTIVE
        user.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(user)

        logger.info(f"User {user.email} reactivated by super admin {current_user.email}")

        return {
            "success": True,
            "data": user,
            "message": f"User {user.email} has been reactivated",
        }

    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reactivating user {user_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reactivate user"
        )
