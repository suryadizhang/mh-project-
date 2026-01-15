"""
Admin Configuration Router
===========================

Endpoints for managing dynamic business configuration variables.

Security:
- GET endpoints: Admin or higher (can view configuration)
- PUT/POST endpoints: Super Admin only (can modify pricing/policies)
- Critical variable changes: Require 2 admin approvals OR 1 super admin
- All changes logged to config_audit_log

Endpoints:
- GET /admin/config - List all variables
- GET /admin/config/{category} - List variables by category
- GET /admin/config/{category}/{key} - Get specific variable
- PUT /admin/config/{category}/{key} - Update variable (may require approval)
- POST /admin/config - Create new variable (Super Admin)
- GET /admin/config/audit - Get audit log
- POST /admin/config/bulk - Bulk update variables (Super Admin)
- POST /admin/config/cache/invalidate - Invalidate config cache

Approval Endpoints:
- GET /admin/config/approvals/pending - List pending approvals
- POST /admin/config/approvals/request - Create approval request
- POST /admin/config/approvals/{id}/approve - Approve a request
- POST /admin/config/approvals/{id}/reject - Reject a request
- DELETE /admin/config/approvals/{id} - Cancel a request

Related:
- services.dynamic_variables_service.DynamicVariablesService
- services.approval_service.ApprovalService
- services.business_config_service.get_business_config
- 20-SINGLE_SOURCE_OF_TRUTH.instructions.md
"""

import logging
from typing import Optional, Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.auth import require_roles
from core.config import UserRole
from services.dynamic_variables_service import DynamicVariablesService
from services.approval_service import ApprovalService, ApprovalStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/config", tags=["admin", "config"])


# =============================================================================
# Request/Response Models
# =============================================================================


class VariableResponse(BaseModel):
    """Response model for a single dynamic variable."""

    id: UUID
    category: str
    key: str
    value: Any
    value_type: str
    description: Optional[str] = None
    is_active: bool
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class VariableListResponse(BaseModel):
    """Response model for list of variables."""

    variables: list[dict]
    count: int
    category: Optional[str] = None


class VariableCreateRequest(BaseModel):
    """Request model for creating a new variable."""

    category: str = Field(..., description="Category: pricing, deposit, travel, booking")
    key: str = Field(..., description="Variable key, e.g., adult_price_cents")
    value: Any = Field(..., description="Variable value")
    value_type: str = Field("integer", description="Type: integer, number, boolean, string, json")
    description: Optional[str] = Field(None, description="Human-readable description")
    effective_from: Optional[str] = Field(
        None, description="ISO datetime when value becomes effective"
    )
    effective_to: Optional[str] = Field(None, description="ISO datetime when value expires")


class VariableUpdateRequest(BaseModel):
    """Request model for updating a variable."""

    value: Any = Field(..., description="New value")
    change_reason: Optional[str] = Field(None, description="Reason for change (for audit log)")
    effective_from: Optional[str] = Field(
        None, description="ISO datetime when value becomes effective"
    )
    effective_to: Optional[str] = Field(None, description="ISO datetime when value expires")


class BulkUpdateRequest(BaseModel):
    """Request model for bulk updating variables."""

    updates: list[dict] = Field(
        ...,
        description="List of updates: [{category, key, value, change_reason?}]",
    )


class AuditLogResponse(BaseModel):
    """Response model for audit log entries."""

    entries: list[dict]
    count: int
    page: int
    limit: int


class SuccessResponse(BaseModel):
    """Generic success response."""

    success: bool = True
    message: str
    data: Optional[dict] = None


# =============================================================================
# Approval Request/Response Models
# =============================================================================


class ApprovalRequestCreate(BaseModel):
    """Request model for creating an approval request."""

    category: str = Field(..., description="Variable category")
    key: str = Field(..., description="Variable key")
    proposed_value: Any = Field(..., description="Proposed new value")
    change_reason: Optional[str] = Field(None, description="Reason for the change")
    effective_from: Optional[str] = Field(
        None, description="ISO datetime when value becomes effective"
    )
    effective_to: Optional[str] = Field(None, description="ISO datetime when value expires")


class ApprovalActionRequest(BaseModel):
    """Request model for approve/reject actions."""

    comment: Optional[str] = Field(None, description="Optional comment for action")


class ApprovalResponse(BaseModel):
    """Response model for a single approval request."""

    id: UUID
    category: str
    key: str
    current_value: Any
    proposed_value: Any
    change_reason: Optional[str] = None
    status: str
    required_approvals: int
    current_approvals: int
    requested_by_id: UUID
    requested_by_email: Optional[str] = None
    requested_at: str
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    resolved_at: Optional[str] = None
    actions: List[dict] = []

    class Config:
        from_attributes = True


class ApprovalListResponse(BaseModel):
    """Response model for list of approval requests."""

    approvals: List[dict]
    count: int
    status_filter: Optional[str] = None


# =============================================================================
# Helper Functions
# =============================================================================


def get_current_user_id(current_user) -> Optional[UUID]:
    """Extract user ID from current user object."""
    if hasattr(current_user, "id"):
        return current_user.id
    if isinstance(current_user, dict) and "id" in current_user:
        return current_user["id"]
    return None


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/", response_model=VariableListResponse)
async def list_all_variables(
    include_inactive: bool = Query(False, description="Include inactive variables"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
):
    """
    List all dynamic configuration variables.

    Returns all active variables grouped by category.
    Super Admin can include inactive variables.
    """
    service = DynamicVariablesService(db)
    # get_all returns dict grouped by category, flatten to list for response
    all_vars = await service.get_all()
    variables = []
    for category, items in all_vars.items():
        for key, info in items.items():
            variables.append({"category": category, "key": key, **info})

    return VariableListResponse(
        variables=variables,
        count=len(variables),
        category=None,
    )


@router.get("/categories")
async def list_categories(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
):
    """
    List all configuration categories.

    Returns list of unique category names.
    """
    service = DynamicVariablesService(db)
    all_vars = await service.get_all()

    # Extract unique categories (keys of grouped dict)
    categories = sorted(all_vars.keys())

    return {"categories": categories, "count": len(categories)}


@router.get("/audit", response_model=AuditLogResponse)
async def get_audit_log(
    category: Optional[str] = Query(None, description="Filter by category"),
    key: Optional[str] = Query(None, description="Filter by key"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
):
    """
    Get configuration change audit log.

    Returns paginated list of all configuration changes.
    """
    service = DynamicVariablesService(db)
    entries = await service.get_audit_log(
        category=category,
        key=key,
        limit=limit,
        offset=(page - 1) * limit,
    )

    return AuditLogResponse(
        entries=entries,
        count=len(entries),
        page=page,
        limit=limit,
    )


@router.get("/{category}", response_model=VariableListResponse)
async def list_variables_by_category(
    category: str,
    include_inactive: bool = Query(False, description="Include inactive variables"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
):
    """
    List all variables in a category.

    Categories: pricing, deposit, travel, booking
    """
    service = DynamicVariablesService(db)
    category_vars = await service.get_category(category=category)
    # Convert to list format
    variables = [{"category": category, "key": key, **info} for key, info in category_vars.items()]

    return VariableListResponse(
        variables=variables,
        count=len(variables),
        category=category,
    )


@router.get("/{category}/{key}")
async def get_variable(
    category: str,
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
):
    """
    Get a specific configuration variable.
    """
    service = DynamicVariablesService(db)
    variable = await service.get_variable_details(category=category, key=key)

    if not variable:
        raise HTTPException(
            status_code=404,
            detail=f"Variable not found: {category}/{key}",
        )

    return variable


@router.put("/{category}/{key}", response_model=SuccessResponse)
async def update_variable(
    category: str,
    key: str,
    request: VariableUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
):
    """
    Update a configuration variable.

    **Admin or Super Admin.**

    For critical variables (pricing/deposit), Admin changes require approval.
    Super Admin can bypass approval (god mode).

    Changes are logged to audit trail and cache is invalidated.
    """
    service = DynamicVariablesService(db)
    approval_service = ApprovalService(db)
    user_id = get_current_user_id(current_user)

    # Determine if current user is super admin (god mode - bypasses approval)
    # Note: AuthenticatedUser has .role (singular), not .roles (plural)
    user_role = getattr(current_user, "role", None)
    is_super_admin = False
    if user_role:
        # Handle both Role enum (lowercase) and UserRole enum (UPPERCASE)
        role_value = user_role.value if hasattr(user_role, "value") else str(user_role)
        is_super_admin = role_value.upper() == UserRole.SUPER_ADMIN.value

    # Get actor info for audit trail
    actor_email = getattr(current_user, "email", "unknown@myhibachi.com")
    actor_role = "super_admin" if is_super_admin else "admin"

    try:
        # Check if approval is required for this variable
        needs_approval = await approval_service.requires_approval(category, key, actor_role)

        if needs_approval:
            # Parse effective dates for scheduled changes
            effective_from_dt = None
            effective_to_dt = None
            if request.effective_from:
                try:
                    from datetime import datetime as dt

                    effective_from_dt = dt.fromisoformat(
                        request.effective_from.replace("Z", "+00:00")
                    )
                except (ValueError, AttributeError):
                    pass
            if request.effective_to:
                try:
                    from datetime import datetime as dt

                    effective_to_dt = dt.fromisoformat(request.effective_to.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pass

            # Validate user_id is present (required for approval requests)
            if not user_id:
                raise HTTPException(
                    status_code=401,
                    detail="User ID required for approval requests",
                )

            # Create pending approval request instead of immediate update
            pending = await approval_service.create_approval_request(
                category=category,
                key=key,
                proposed_value=request.value,
                requested_by=user_id,
                requested_by_email=actor_email,
                change_type="update",
                change_reason=request.change_reason,
                effective_from=effective_from_dt,
                effective_to=effective_to_dt,
            )

            logger.info(
                f"Approval request created for {category}/{key} by {actor_email}",
                extra={
                    "approval_id": str(pending.id),
                    "category": category,
                    "key": key,
                    "user_email": actor_email,
                },
            )

            # Build response with optional scheduled date info
            response_data = {
                "approval_id": str(pending.id),
                "status": "pending_approval",
                "category": category,
                "key": key,
                "proposed_value": request.value,
            }
            if effective_from_dt:
                response_data["scheduled_effective_from"] = effective_from_dt.isoformat()
            if effective_to_dt:
                response_data["scheduled_effective_to"] = effective_to_dt.isoformat()

            scheduled_msg = ""
            if effective_from_dt:
                scheduled_msg = f" (scheduled for {effective_from_dt.strftime('%Y-%m-%d %H:%M')})"

            return SuccessResponse(
                success=True,
                message=f"Change to {category}/{key} submitted for approval{scheduled_msg}",
                data=response_data,
            )

        # Validate user_id for immediate updates
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="User ID required for updates",
            )

        # No approval needed (super admin or non-critical variable) - immediate update
        result = await service.update_value(
            category=category,
            key=key,
            value=request.value,
            user_id=user_id,
            reason=request.change_reason or "Admin update",
            user_email=getattr(current_user, "email", "unknown@myhibachi.com"),
        )

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Variable not found: {category}/{key}",
            )

        logger.info(
            f"Config updated: {category}/{key} by user {user_id} (role: {actor_role})",
            extra={
                "category": category,
                "key": key,
                "user_id": str(user_id),
                "actor_role": actor_role,
                "change_reason": request.change_reason,
            },
        )

        # Invalidate cache after successful update
        try:
            from services.business_config_service import invalidate_business_config_cache
            from core.cache import get_cache_service

            cache = await get_cache_service()
            if cache:
                await invalidate_business_config_cache(cache)
                logger.info(f"Cache invalidated after config update: {category}/{key}")
        except Exception as cache_error:
            logger.warning(f"Failed to invalidate cache (non-critical): {cache_error}")

        return SuccessResponse(
            success=True,
            message=f"Updated {category}/{key}",
            data={"category": category, "key": key, "value": request.value},
        )

    except Exception as e:
        logger.error(f"Failed to update config {category}/{key}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update variable: {str(e)}",
        )


@router.post("/", response_model=SuccessResponse)
async def create_variable(
    request: VariableCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([UserRole.SUPER_ADMIN])),
):
    """
    Create a new configuration variable.

    **Super Admin only.**
    """
    service = DynamicVariablesService(db)
    user_id = get_current_user_id(current_user)

    # Validate user_id
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="User ID required for creating variables",
        )

    try:
        result = await service.create_variable(
            category=request.category,
            key=request.key,
            value=request.value,
            display_name=request.key.replace("_", " ").title(),
            description=request.description,
            unit=None,
            validation_rules=None,
            user_id=user_id,
            reason="Initial creation",
            user_email=getattr(current_user, "email", "unknown@myhibachi.com"),
        )

        logger.info(
            f"Config created: {request.category}/{request.key} by user {user_id}",
            extra={
                "category": request.category,
                "key": request.key,
                "user_id": str(user_id),
            },
        )

        return SuccessResponse(
            success=True,
            message=f"Created {request.category}/{request.key}",
            data=result,
        )

    except Exception as e:
        logger.error(f"Failed to create config {request.category}/{request.key}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create variable: {str(e)}",
        )


@router.post("/bulk", response_model=SuccessResponse)
async def bulk_update_variables(
    request: BulkUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([UserRole.SUPER_ADMIN])),
):
    """
    Bulk update multiple configuration variables.

    **Super Admin only.**

    All updates are applied in a single transaction.
    """
    service = DynamicVariablesService(db)
    user_id = get_current_user_id(current_user)

    # Validate user_id
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="User ID required for bulk updates",
        )

    try:
        # Process each update individually
        results = []
        user_email = getattr(current_user, "email", "unknown@myhibachi.com")
        for update in request.updates:
            # Validate required fields
            category = update.get("category")
            key = update.get("key")
            if not category or not key:
                raise HTTPException(
                    status_code=400,
                    detail="Each update requires 'category' and 'key' fields",
                )
            result = await service.update_value(
                category=str(category),
                key=str(key),
                value=update.get("value"),
                user_id=user_id,
                reason=str(update.get("change_reason") or "Bulk update"),
                user_email=user_email,
            )
            results.append(result)

        logger.info(
            f"Bulk config update: {len(request.updates)} variables by user {user_id}",
            extra={
                "update_count": len(request.updates),
                "user_id": str(user_id),
            },
        )

        return SuccessResponse(
            success=True,
            message=f"Updated {len(results)} variables",
            data={"updated_count": len(results), "results": results},
        )

    except Exception as e:
        logger.error(f"Failed bulk config update: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to bulk update variables: {str(e)}",
        )


@router.delete("/{category}/{key}", response_model=SuccessResponse)
async def delete_variable(
    category: str,
    key: str,
    hard_delete: bool = Query(False, description="Permanently delete (vs soft delete)"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([UserRole.SUPER_ADMIN])),
):
    """
    Delete (deactivate) a configuration variable.

    **Super Admin only.**

    By default, performs soft delete (sets is_active=false).
    Use hard_delete=true to permanently remove.
    """
    service = DynamicVariablesService(db)
    user_id = get_current_user_id(current_user)

    # Validate user_id
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="User ID required for deletion",
        )

    try:
        # Use single delete_variable method (soft delete by default)
        user_email = getattr(current_user, "email", "unknown@myhibachi.com")
        result = await service.delete_variable(
            category=category,
            key=key,
            user_id=user_id,
            reason="Admin deletion" if not hard_delete else "Hard delete by super admin",
            user_email=user_email,
        )

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Variable not found: {category}/{key}",
            )

        action = "deleted" if hard_delete else "deactivated"
        logger.info(
            f"Config {action}: {category}/{key} by user {user_id}",
            extra={
                "category": category,
                "key": key,
                "user_id": str(user_id),
                "hard_delete": hard_delete,
            },
        )

        return SuccessResponse(
            success=True,
            message=f"Variable {action}: {category}/{key}",
            data={"category": category, "key": key, "action": action},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete config {category}/{key}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete variable: {str(e)}",
        )


@router.post("/cache/invalidate", response_model=SuccessResponse)
async def invalidate_config_cache(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([UserRole.SUPER_ADMIN])),
):
    """
    Manually invalidate the configuration cache.

    **Super Admin only.**

    Forces all services to reload configuration from database.
    Cache is automatically invalidated on updates, but this can be
    used for manual refresh.
    """
    try:
        # Import here to avoid circular imports
        from services.business_config_service import (
            invalidate_business_config_cache,
            BUSINESS_CONFIG_CACHE_KEY,
        )
        from core.cache import get_cache_service

        # Get cache service and actually invalidate
        cache = await get_cache_service()
        cache_invalidated = False

        if cache:
            cache_invalidated = await invalidate_business_config_cache(cache)
            logger.info(
                f"Cache invalidation {'succeeded' if cache_invalidated else 'failed'} "
                f"for user {get_current_user_id(current_user)}"
            )
        else:
            logger.warning("Cache service not available - cache invalidation skipped")

        return SuccessResponse(
            success=True,
            message="Cache invalidation triggered. All services will reload configuration.",
            data={
                "cache_key": BUSINESS_CONFIG_CACHE_KEY,
                "cache_invalidated": cache_invalidated,
            },
        )

    except Exception as e:
        logger.error(f"Failed to invalidate cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to invalidate cache: {str(e)}",
        )


# =============================================================================
# APPROVAL WORKFLOW ENDPOINTS
# =============================================================================
# Two-Person Approval System for Critical Variables
# - Critical variables (pricing/*, deposit/*) require 2 Admin approvals
# - Super Admin can bypass approval ("god mode")
# - Non-critical variables update immediately
# =============================================================================


@router.get("/approvals/pending", response_model=ApprovalListResponse)
async def list_pending_approvals(
    status: Optional[str] = Query(
        None, description="Filter by status: pending, approved, rejected, expired"
    ),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
):
    """
    List approval requests.

    **Admin and Super Admin access.**

    Filter by status to see pending, approved, rejected, or expired requests.
    Defaults to showing pending requests if no status specified.
    """
    try:
        approval_service = ApprovalService(db)

        # Convert status string to enum if provided
        status_enum = None
        if status:
            try:
                status_enum = ApprovalStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid status. Must be one of: pending, approved, rejected, expired",
                )

        approvals = await approval_service.get_pending_approvals(status=status_enum)

        # Convert PendingApproval objects to dicts for response
        approvals_dicts = [
            approval.model_dump() if hasattr(approval, "model_dump") else vars(approval)
            for approval in approvals
        ]

        return ApprovalListResponse(
            approvals=approvals_dicts,
            count=len(approvals),
            status_filter=status,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list approvals: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list approvals: {str(e)}",
        )


@router.post("/approvals/request", response_model=SuccessResponse)
async def create_approval_request(
    request: ApprovalRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
):
    """
    Create an approval request for a critical variable change.

    **Admin and Super Admin access.**

    For critical variables (pricing, deposit), changes require approval from:
    - 2 Admin users, OR
    - 1 Super Admin (bypasses approval requirement)

    Super Admins can also use the regular PUT endpoint which bypasses approval.
    """
    try:
        approval_service = ApprovalService(db)
        user_id = get_current_user_id(current_user)

        # Check if this variable actually requires approval
        requires = await approval_service.requires_approval(request.category, request.key)

        if not requires:
            raise HTTPException(
                status_code=400,
                detail=f"Variable {request.category}/{request.key} does not require approval. "
                f"Use PUT /{request.category}/{request.key} to update directly.",
            )

        # Parse effective dates if provided
        effective_from_dt = None
        effective_to_dt = None
        if request.effective_from:
            try:
                from datetime import datetime

                effective_from_dt = datetime.fromisoformat(
                    request.effective_from.replace("Z", "+00:00")
                )
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid effective_from date format. Use ISO 8601 format.",
                )
        if request.effective_to:
            try:
                from datetime import datetime

                effective_to_dt = datetime.fromisoformat(
                    request.effective_to.replace("Z", "+00:00")
                )
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid effective_to date format. Use ISO 8601 format.",
                )

        # Validate user_id
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="User ID required for approval requests",
            )

        actor_email = getattr(current_user, "email", "unknown@myhibachi.com")

        # Create the approval request
        pending = await approval_service.create_approval_request(
            category=request.category,
            key=request.key,
            proposed_value=request.proposed_value,
            requested_by=user_id,
            requested_by_email=actor_email,
            change_reason=request.change_reason,
            effective_from=effective_from_dt,
            effective_to=effective_to_dt,
        )
        approval_id = pending.id

        logger.info(
            f"Approval request created: {request.category}/{request.key} by user {user_id}",
            extra={
                "approval_id": str(approval_id),
                "category": request.category,
                "key": request.key,
                "user_id": str(user_id),
            },
        )

        return SuccessResponse(
            success=True,
            message=f"Approval request created for {request.category}/{request.key}. "
            f"Requires 2 Admin approvals or 1 Super Admin approval.",
            data={
                "approval_id": str(approval_id),
                "category": request.category,
                "key": request.key,
                "status": "pending",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create approval request: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create approval request: {str(e)}",
        )


@router.get("/approvals/{approval_id}")
async def get_approval_request(
    approval_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
):
    """
    Get details of a specific approval request.

    **Admin and Super Admin access.**
    """
    try:
        approval_service = ApprovalService(db)
        approval = await approval_service.get_pending_approval(approval_id)

        if not approval:
            raise HTTPException(
                status_code=404,
                detail=f"Approval request not found: {approval_id}",
            )

        return {"success": True, "data": approval}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get approval {approval_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get approval request: {str(e)}",
        )


@router.post("/approvals/{approval_id}/approve", response_model=SuccessResponse)
async def approve_request(
    approval_id: UUID,
    request: ApprovalActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
):
    """
    Approve a pending approval request.

    **Admin and Super Admin access.**

    Approval requirements:
    - 2 Admin approvals required, OR
    - 1 Super Admin approval (instant approval - "god mode")

    If this is the final required approval, the variable is automatically updated.
    """
    try:
        approval_service = ApprovalService(db)
        user_id = get_current_user_id(current_user)

        # Determine if current user is super admin
        # Note: AuthenticatedUser has .role (singular), not .roles (plural)
        user_role = getattr(current_user, "role", None)
        is_super_admin = False
        if user_role:
            # Handle both Role enum (lowercase) and UserRole enum (UPPERCASE)
            role_value = user_role.value if hasattr(user_role, "value") else str(user_role)
            is_super_admin = role_value.upper() == UserRole.SUPER_ADMIN.value

        # Validate user_id
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="User ID required for approval actions",
            )

        # Get actor email for audit trail
        actor_email = getattr(current_user, "email", "unknown@myhibachi.com")
        actor_role = "super_admin" if is_super_admin else "admin"

        result = await approval_service.approve_request(
            pending_id=approval_id,
            actor_id=user_id,
            actor_email=actor_email,
            actor_role=actor_role,
            comment=request.comment,
        )

        if not result.success:
            raise HTTPException(
                status_code=400,
                detail=result.message or "Failed to approve request",
            )

        logger.info(
            f"Approval action: approved {approval_id} by user {user_id}",
            extra={
                "approval_id": str(approval_id),
                "user_id": str(user_id),
                "actor_role": actor_role,
                "is_complete": result.is_complete,
            },
        )

        message = result.message or "Approval recorded"
        if result.is_complete:
            message = f"✅ Variable updated! {message}"

            # Invalidate cache if variable was applied
            try:
                from services.business_config_service import invalidate_business_config_cache
                from core.cache import get_cache_service

                cache = await get_cache_service()
                if cache:
                    await invalidate_business_config_cache(cache)
            except Exception as cache_error:
                logger.warning(f"Failed to invalidate cache after approval: {cache_error}")

        # Convert result to dict for response
        result_data = (
            result.model_dump()
            if hasattr(result, "model_dump")
            else {
                "success": result.success,
                "message": result.message,
                "is_complete": result.is_complete,
            }
        )

        return SuccessResponse(
            success=True,
            message=message,
            data=result_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve request {approval_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to approve request: {str(e)}",
        )


@router.post("/approvals/{approval_id}/reject", response_model=SuccessResponse)
async def reject_request(
    approval_id: UUID,
    request: ApprovalActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
):
    """
    Reject a pending approval request.

    **Admin and Super Admin access.**

    A rejection by any Admin or Super Admin will reject the entire request.
    """
    try:
        approval_service = ApprovalService(db)
        user_id = get_current_user_id(current_user)

        # Determine actor role for audit trail
        # Note: AuthenticatedUser has .role (singular), not .roles (plural)
        user_role = getattr(current_user, "role", None)
        is_super_admin = False
        if user_role:
            # Handle both Role enum (lowercase) and UserRole enum (UPPERCASE)
            role_value = user_role.value if hasattr(user_role, "value") else str(user_role)
            is_super_admin = role_value.upper() == UserRole.SUPER_ADMIN.value

        # Validate user_id
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="User ID required for rejection actions",
            )

        actor_email = getattr(current_user, "email", "unknown@myhibachi.com")
        actor_role = "super_admin" if is_super_admin else "admin"

        result = await approval_service.reject_request(
            pending_id=approval_id,
            actor_id=user_id,
            actor_email=actor_email,
            actor_role=actor_role,
            comment=request.comment,
        )

        if not result.success:
            raise HTTPException(
                status_code=400,
                detail=result.message or "Failed to reject request",
            )

        logger.info(
            f"Approval action: rejected {approval_id} by user {user_id}",
            extra={
                "approval_id": str(approval_id),
                "user_id": str(user_id),
                "actor_role": actor_role,
            },
        )

        # Convert result to dict for response
        result_data = (
            result.model_dump()
            if hasattr(result, "model_dump")
            else {
                "success": result.success,
                "message": result.message,
                "is_complete": result.is_complete,
            }
        )

        return SuccessResponse(
            success=True,
            message=result.message or "Request rejected",
            data=result_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reject request {approval_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reject request: {str(e)}",
        )


@router.delete("/approvals/{approval_id}", response_model=SuccessResponse)
async def cancel_approval_request(
    approval_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
):
    """
    Cancel/delete an approval request.

    **Admin and Super Admin access.**

    Only the original requester or a Super Admin can cancel a request.
    Only pending requests can be cancelled.
    """
    try:
        approval_service = ApprovalService(db)
        user_id = get_current_user_id(current_user)

        # Check if user is super admin
        # Note: AuthenticatedUser has .role (singular), not .roles (plural)
        user_role = getattr(current_user, "role", None)
        is_super_admin = False
        if user_role:
            # Handle both Role enum (lowercase) and UserRole enum (UPPERCASE)
            role_value = user_role.value if hasattr(user_role, "value") else str(user_role)
            is_super_admin = role_value.upper() == UserRole.SUPER_ADMIN.value

        # Validate user_id
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="User ID required for cancellation actions",
            )

        actor_email = getattr(current_user, "email", "unknown@myhibachi.com")
        actor_role = "super_admin" if is_super_admin else "admin"

        result = await approval_service.cancel_request(
            pending_id=approval_id,
            actor_id=user_id,
            actor_email=actor_email,
            actor_role=actor_role,
        )

        if not result.success:
            raise HTTPException(
                status_code=400,
                detail=result.message or "Failed to cancel request",
            )

        logger.info(
            f"Approval cancelled: {approval_id} by user {user_id}",
            extra={
                "approval_id": str(approval_id),
                "user_id": str(user_id),
                "actor_role": actor_role,
            },
        )

        # Convert result to dict for response
        result_data = (
            result.model_dump()
            if hasattr(result, "model_dump")
            else {
                "success": result.success,
                "message": result.message,
                "is_complete": result.is_complete,
            }
        )

        return SuccessResponse(
            success=True,
            message=result.message or "Approval request cancelled",
            data=result_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel request {approval_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel request: {str(e)}",
        )


@router.get("/approvals/check/{category}/{key}")
async def check_requires_approval(
    category: str,
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
):
    """
    Check if a variable requires approval to update.

    **Admin and Super Admin access.**

    Returns whether this variable is considered "critical" and requires
    the two-person approval workflow.
    """
    try:
        approval_service = ApprovalService(db)
        requires = await approval_service.requires_approval(category, key)

        return {
            "success": True,
            "data": {
                "category": category,
                "key": key,
                "requires_approval": requires,
                "approval_info": (
                    "Requires 2 Admin approvals or 1 Super Admin"
                    if requires
                    else "No approval required"
                ),
            },
        }

    except Exception as e:
        logger.error(f"Failed to check approval requirement for {category}/{key}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check approval requirement: {str(e)}",
        )
