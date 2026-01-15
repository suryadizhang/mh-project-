"""
Variable Approval Service
=========================

Manages the two-person approval workflow for critical business variables.

Key Rules:
- Critical variables (pricing/*, deposit/*) require 2 admin approvals
- Super Admin can bypass approval entirely ("god mode")
- Pending approvals expire after 7 days
- Self-approval is NOT allowed (can't approve your own request)

Usage:
    from services.approval_service import ApprovalService

    approval_service = ApprovalService(db)

    # Check if variable needs approval
    needs_approval = await approval_service.requires_approval("pricing", "adult_price_cents")

    # Request approval for a change
    pending = await approval_service.create_approval_request(
        variable_id=var_id,
        proposed_value={"value": 6000},
        requested_by=user_id,
        effective_from=datetime.now(),
        change_reason="Annual price increase"
    )

    # Approve a pending request (2nd admin or super admin)
    result = await approval_service.approve_request(
        pending_id=pending.id,
        actor_id=approver_id,
        actor_role="super_admin",  # bypasses 2-approval requirement
        comment="Approved for Q2"
    )

See: database/migrations/005_variable_approval_system.sql
See: 20-SINGLE_SOURCE_OF_TRUTH.instructions.md
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"  # Super admin bypass
    EXPIRED = "expired"
    APPLIED = "applied"  # Successfully applied to variable


class ApprovalAction(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    CANCEL = "cancel"


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    STAFF = "staff"
    CUSTOMER = "customer"


# =============================================================================
# PYDANTIC MODELS
# =============================================================================


class PendingApproval(BaseModel):
    """A pending variable change awaiting approval."""

    id: UUID
    variable_id: Optional[UUID] = None
    category: str
    key: str
    current_value: Optional[Any] = None
    proposed_value: Any
    change_type: str  # update, create, delete
    change_reason: Optional[str] = None
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    requested_by: UUID
    requested_by_email: Optional[str] = None
    status: ApprovalStatus
    approvals_required: int = 2
    approvals_received: int = 0
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class ApprovalActionRecord(BaseModel):
    """A record of an approval/rejection action."""

    id: UUID
    pending_approval_id: UUID
    actor_id: UUID
    actor_email: str
    actor_role: str
    action: ApprovalAction
    comment: Optional[str] = None
    acted_at: datetime

    class Config:
        from_attributes = True


class ApprovalResult(BaseModel):
    """Result of an approval action."""

    success: bool
    status: ApprovalStatus
    message: str
    approvals_received: int = 0
    approvals_required: int = 2
    is_complete: bool = False  # True if fully approved and applied
    applied_variable_id: Optional[UUID] = None


class CriticalVariableRule(BaseModel):
    """Configuration for which variables require approval."""

    category_pattern: str
    key_pattern: Optional[str] = None
    approvals_required: int = 2
    super_admin_can_bypass: bool = True


# =============================================================================
# APPROVAL SERVICE
# =============================================================================


class ApprovalService:
    """
    Service for managing variable approval workflows.

    Two-Person Approval Logic:
    1. Non-critical variables: No approval needed, apply immediately
    2. Critical variables + Regular Admin: Requires 2 admin approvals
    3. Critical variables + Super Admin: Bypasses approval (god mode)
    """

    DEFAULT_EXPIRY_DAYS = 7

    def __init__(self, db: AsyncSession):
        self.db = db

    # -------------------------------------------------------------------------
    # APPROVAL REQUIREMENT CHECKS
    # -------------------------------------------------------------------------

    async def requires_approval(self, category: str, key: str, actor_role: str = "admin") -> bool:
        """
        Check if a variable change requires approval.

        Super Admins ALWAYS bypass approval (god mode).

        Args:
            category: Variable category (e.g., "pricing")
            key: Variable key (e.g., "adult_price_cents")
            actor_role: Role of the user making the change

        Returns:
            True if approval is required, False if can apply immediately
        """
        # Super Admin bypasses all approval requirements
        # Handle both "super_admin" and "superadmin" formats
        if actor_role.lower().replace("_", "") == "superadmin":
            logger.info(f"🔓 Super Admin bypass for {category}/{key}")
            return False

        # Check database for critical variable patterns
        result = await self.db.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1 FROM critical_variable_config
                    WHERE is_active = true
                    AND :category LIKE REPLACE(category_pattern, '*', '%')
                    AND (
                        key_pattern IS NULL
                        OR :key LIKE REPLACE(key_pattern, '*', '%')
                    )
                )
            """
            ),
            {"category": category, "key": key},
        )
        is_critical = result.scalar()

        if is_critical:
            logger.info(f"🔐 Critical variable {category}/{key} requires approval")

        return is_critical or False

    async def get_approval_requirements(
        self, category: str, key: str
    ) -> Optional[CriticalVariableRule]:
        """
        Get the approval requirements for a specific variable.

        Returns:
            CriticalVariableRule if critical, None otherwise
        """
        result = await self.db.execute(
            text(
                """
                SELECT
                    category_pattern,
                    key_pattern,
                    approvals_required,
                    super_admin_can_bypass
                FROM critical_variable_config
                WHERE is_active = true
                AND :category LIKE REPLACE(category_pattern, '*', '%')
                AND (
                    key_pattern IS NULL
                    OR :key LIKE REPLACE(key_pattern, '*', '%')
                )
                ORDER BY
                    CASE WHEN key_pattern IS NOT NULL THEN 0 ELSE 1 END,
                    created_at DESC
                LIMIT 1
            """
            ),
            {"category": category, "key": key},
        )
        row = result.fetchone()

        if row:
            return CriticalVariableRule(
                category_pattern=row.category_pattern,
                key_pattern=row.key_pattern,
                approvals_required=row.approvals_required,
                super_admin_can_bypass=row.super_admin_can_bypass,
            )
        return None

    # -------------------------------------------------------------------------
    # CREATE APPROVAL REQUEST
    # -------------------------------------------------------------------------

    async def create_approval_request(
        self,
        category: str,
        key: str,
        proposed_value: Any,
        requested_by: UUID,
        requested_by_email: str,
        change_type: str = "update",
        variable_id: Optional[UUID] = None,
        current_value: Optional[Any] = None,
        effective_from: Optional[datetime] = None,
        effective_to: Optional[datetime] = None,
        change_reason: Optional[str] = None,
        expires_in_days: int = DEFAULT_EXPIRY_DAYS,
    ) -> PendingApproval:
        """
        Create a new pending approval request.

        Args:
            category: Variable category
            key: Variable key
            proposed_value: The new value (as JSON-serializable dict/value)
            requested_by: UUID of requesting user
            requested_by_email: Email of requesting user
            change_type: "create", "update", or "delete"
            variable_id: UUID of existing variable (for updates)
            current_value: Current value before change
            effective_from: When the change should take effect
            effective_to: When the change should expire (optional)
            change_reason: Human-readable reason for change
            expires_in_days: Days until pending request expires

        Returns:
            PendingApproval with the new request details
        """
        # Get approval requirements
        requirements = await self.get_approval_requirements(category, key)
        approvals_required = requirements.approvals_required if requirements else 2

        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        result = await self.db.execute(
            text(
                """
                INSERT INTO pending_variable_approvals (
                    variable_id,
                    category,
                    key,
                    current_value,
                    proposed_value,
                    change_type,
                    change_reason,
                    effective_from,
                    effective_to,
                    requested_by,
                    requested_by_email,
                    status,
                    approvals_required,
                    approvals_received,
                    expires_at
                ) VALUES (
                    :variable_id,
                    :category,
                    :key,
                    :current_value::jsonb,
                    :proposed_value::jsonb,
                    :change_type,
                    :change_reason,
                    :effective_from,
                    :effective_to,
                    :requested_by,
                    :requested_by_email,
                    'pending',
                    :approvals_required,
                    0,
                    :expires_at
                )
                RETURNING *
            """
            ),
            {
                "variable_id": str(variable_id) if variable_id else None,
                "category": category,
                "key": key,
                "current_value": self._to_json_str(current_value),
                "proposed_value": self._to_json_str(proposed_value),
                "change_type": change_type,
                "change_reason": change_reason,
                "effective_from": effective_from or datetime.utcnow(),
                "effective_to": effective_to,
                "requested_by": str(requested_by),
                "requested_by_email": requested_by_email,
                "approvals_required": approvals_required,
                "expires_at": expires_at,
            },
        )
        row = result.fetchone()
        await self.db.commit()

        logger.info(
            f"📝 Created approval request for {category}/{key} "
            f"(requires {approvals_required} approvals)"
        )

        return self._row_to_pending_approval(row)

    # -------------------------------------------------------------------------
    # APPROVE / REJECT
    # -------------------------------------------------------------------------

    async def approve_request(
        self,
        pending_id: UUID,
        actor_id: UUID,
        actor_email: str,
        actor_role: str,
        comment: Optional[str] = None,
    ) -> ApprovalResult:
        """
        Approve a pending variable change request.

        Logic:
        - Super Admin: Immediate approval (bypasses 2-person requirement)
        - Regular Admin: Adds 1 approval, fully approved when approvals_received >= approvals_required
        - Self-approval: NOT allowed (can't approve your own request)

        Args:
            pending_id: UUID of the pending approval
            actor_id: UUID of the approving user
            actor_email: Email of the approving user
            actor_role: Role of approver ("super_admin" or "admin")
            comment: Optional comment for audit trail

        Returns:
            ApprovalResult with status and applied variable info
        """
        # Get pending approval
        pending = await self.get_pending_approval(pending_id)
        if not pending:
            return ApprovalResult(
                success=False, status=ApprovalStatus.PENDING, message="Pending approval not found"
            )

        # Check if already processed
        if pending.status != ApprovalStatus.PENDING:
            return ApprovalResult(
                success=False,
                status=pending.status,
                message=f"Request already {pending.status.value}",
            )

        # Check for self-approval
        if str(pending.requested_by) == str(actor_id):
            return ApprovalResult(
                success=False,
                status=ApprovalStatus.PENDING,
                message="Cannot approve your own request",
            )

        # Check if user already approved
        existing = await self.db.execute(
            text(
                """
                SELECT 1 FROM variable_approval_actions
                WHERE pending_approval_id = :pending_id
                AND actor_id = :actor_id
                AND action = 'approve'
            """
            ),
            {"pending_id": str(pending_id), "actor_id": str(actor_id)},
        )
        if existing.fetchone():
            return ApprovalResult(
                success=False,
                status=ApprovalStatus.PENDING,
                message="You have already approved this request",
            )

        # Record the approval action
        await self.db.execute(
            text(
                """
                INSERT INTO variable_approval_actions (
                    pending_approval_id, actor_id, actor_email, actor_role, action, comment
                ) VALUES (
                    :pending_id, :actor_id, :actor_email, :actor_role, 'approve', :comment
                )
            """
            ),
            {
                "pending_id": str(pending_id),
                "actor_id": str(actor_id),
                "actor_email": actor_email,
                "actor_role": actor_role,
                "comment": comment,
            },
        )

        # Determine if fully approved
        # Handle both "super_admin" and "superadmin" formats
        is_super_admin = actor_role.lower().replace("_", "") == "superadmin"
        new_approvals = pending.approvals_received + 1

        if is_super_admin:
            # Super Admin bypasses - immediate full approval
            new_status = ApprovalStatus.AUTO_APPROVED
            is_complete = True
            logger.info(
                f"⚡ Super Admin {actor_email} auto-approved {pending.category}/{pending.key}"
            )
        elif new_approvals >= pending.approvals_required:
            # Met threshold with regular admins
            new_status = ApprovalStatus.APPROVED
            is_complete = True
            logger.info(
                f"✅ Fully approved {pending.category}/{pending.key} ({new_approvals}/{pending.approvals_required})"
            )
        else:
            # Partial approval
            new_status = ApprovalStatus.PENDING
            is_complete = False
            logger.info(
                f"📊 Partial approval {pending.category}/{pending.key} ({new_approvals}/{pending.approvals_required})"
            )

        # Update pending approval status
        await self.db.execute(
            text(
                """
                UPDATE pending_variable_approvals
                SET
                    approvals_received = :new_approvals,
                    status = :new_status,
                    updated_at = NOW()
                WHERE id = :pending_id
            """
            ),
            {
                "pending_id": str(pending_id),
                "new_approvals": new_approvals,
                "new_status": new_status.value,
            },
        )

        applied_variable_id = None

        # If fully approved, apply the change
        if is_complete:
            applied_variable_id = await self._apply_approved_change(pending)

            # Update status to APPLIED
            await self.db.execute(
                text(
                    """
                    UPDATE pending_variable_approvals
                    SET status = 'applied', updated_at = NOW()
                    WHERE id = :pending_id
                """
                ),
                {"pending_id": str(pending_id)},
            )

        await self.db.commit()

        return ApprovalResult(
            success=True,
            status=new_status if not is_complete else ApprovalStatus.APPLIED,
            message=(
                "Approved and applied"
                if is_complete
                else f"Approved ({new_approvals}/{pending.approvals_required})"
            ),
            approvals_received=new_approvals,
            approvals_required=pending.approvals_required,
            is_complete=is_complete,
            applied_variable_id=applied_variable_id,
        )

    async def reject_request(
        self,
        pending_id: UUID,
        actor_id: UUID,
        actor_email: str,
        actor_role: str,
        comment: Optional[str] = None,
    ) -> ApprovalResult:
        """
        Reject a pending variable change request.

        Any admin or super admin can reject a pending request.

        Args:
            pending_id: UUID of the pending approval
            actor_id: UUID of the rejecting user
            actor_email: Email of the rejecting user
            actor_role: Role of rejector
            comment: Required reason for rejection

        Returns:
            ApprovalResult with rejection status
        """
        # Get pending approval
        pending = await self.get_pending_approval(pending_id)
        if not pending:
            return ApprovalResult(
                success=False, status=ApprovalStatus.PENDING, message="Pending approval not found"
            )

        # Check if already processed
        if pending.status != ApprovalStatus.PENDING:
            return ApprovalResult(
                success=False,
                status=pending.status,
                message=f"Request already {pending.status.value}",
            )

        # Record the rejection
        await self.db.execute(
            text(
                """
                INSERT INTO variable_approval_actions (
                    pending_approval_id, actor_id, actor_email, actor_role, action, comment
                ) VALUES (
                    :pending_id, :actor_id, :actor_email, :actor_role, 'reject', :comment
                )
            """
            ),
            {
                "pending_id": str(pending_id),
                "actor_id": str(actor_id),
                "actor_email": actor_email,
                "actor_role": actor_role,
                "comment": comment,
            },
        )

        # Update status to rejected
        await self.db.execute(
            text(
                """
                UPDATE pending_variable_approvals
                SET status = 'rejected', updated_at = NOW()
                WHERE id = :pending_id
            """
            ),
            {"pending_id": str(pending_id)},
        )

        await self.db.commit()

        logger.info(f"❌ Rejected {pending.category}/{pending.key} by {actor_email}")

        return ApprovalResult(
            success=True,
            status=ApprovalStatus.REJECTED,
            message=f"Rejected by {actor_email}",
            approvals_received=pending.approvals_received,
            approvals_required=pending.approvals_required,
            is_complete=True,
        )

    async def cancel_request(
        self, pending_id: UUID, actor_id: UUID, actor_email: str, actor_role: str
    ) -> ApprovalResult:
        """
        Cancel a pending approval request.

        Only the original requester or a super admin can cancel.
        """
        pending = await self.get_pending_approval(pending_id)
        if not pending:
            return ApprovalResult(
                success=False, status=ApprovalStatus.PENDING, message="Pending approval not found"
            )

        if pending.status != ApprovalStatus.PENDING:
            return ApprovalResult(
                success=False,
                status=pending.status,
                message=f"Request already {pending.status.value}",
            )

        # Only requester or super admin can cancel
        # Handle both "super_admin" and "superadmin" formats
        is_super_admin = actor_role.lower().replace("_", "") == "superadmin"
        is_requester = str(pending.requested_by) == str(actor_id)

        if not is_super_admin and not is_requester:
            return ApprovalResult(
                success=False,
                status=ApprovalStatus.PENDING,
                message="Only the requester or a super admin can cancel",
            )

        # Record cancellation
        await self.db.execute(
            text(
                """
                INSERT INTO variable_approval_actions (
                    pending_approval_id, actor_id, actor_email, actor_role, action, comment
                ) VALUES (
                    :pending_id, :actor_id, :actor_email, :actor_role, 'cancel', 'Cancelled by user'
                )
            """
            ),
            {
                "pending_id": str(pending_id),
                "actor_id": str(actor_id),
                "actor_email": actor_email,
                "actor_role": actor_role,
            },
        )

        # Soft delete by marking expired
        await self.db.execute(
            text(
                """
                UPDATE pending_variable_approvals
                SET status = 'expired', updated_at = NOW()
                WHERE id = :pending_id
            """
            ),
            {"pending_id": str(pending_id)},
        )

        await self.db.commit()

        return ApprovalResult(
            success=True,
            status=ApprovalStatus.EXPIRED,
            message="Request cancelled",
            is_complete=True,
        )

    # -------------------------------------------------------------------------
    # QUERY METHODS
    # -------------------------------------------------------------------------

    async def get_pending_approval(self, pending_id: UUID) -> Optional[PendingApproval]:
        """Get a single pending approval by ID."""
        result = await self.db.execute(
            text(
                """
                SELECT * FROM pending_variable_approvals
                WHERE id = :pending_id
            """
            ),
            {"pending_id": str(pending_id)},
        )
        row = result.fetchone()
        return self._row_to_pending_approval(row) if row else None

    async def get_pending_approvals(
        self,
        status: Optional[ApprovalStatus] = None,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PendingApproval]:
        """
        Get pending approvals with optional filtering.

        Args:
            status: Filter by status (default: pending only)
            category: Filter by category
            limit: Max results
            offset: Pagination offset

        Returns:
            List of PendingApproval objects
        """
        filters: list[str] = []
        params: dict[str, Any] = {"limit": limit, "offset": offset}

        if status:
            filters.append("status = :status")
            params["status"] = status.value
        else:
            filters.append("status = 'pending'")

        if category:
            filters.append("category = :category")
            params["category"] = category

        where_clause = " AND ".join(filters) if filters else "1=1"

        result = await self.db.execute(
            text(
                f"""
                SELECT * FROM pending_variable_approvals
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """
            ),
            params,
        )
        rows = result.fetchall()
        return [self._row_to_pending_approval(row) for row in rows]

    async def get_approval_actions(self, pending_id: UUID) -> list[ApprovalActionRecord]:
        """Get all approval actions for a pending request."""
        result = await self.db.execute(
            text(
                """
                SELECT * FROM variable_approval_actions
                WHERE pending_approval_id = :pending_id
                ORDER BY acted_at ASC
            """
            ),
            {"pending_id": str(pending_id)},
        )
        rows = result.fetchall()
        return [
            ApprovalActionRecord(
                id=row.id,
                pending_approval_id=row.pending_approval_id,
                actor_id=row.actor_id,
                actor_email=row.actor_email,
                actor_role=row.actor_role,
                action=ApprovalAction(row.action),
                comment=row.comment,
                acted_at=row.acted_at,
            )
            for row in rows
        ]

    async def count_pending_approvals(self) -> int:
        """Count all pending approvals (for badge/notification)."""
        result = await self.db.execute(
            text("SELECT COUNT(*) FROM pending_variable_approvals WHERE status = 'pending'")
        )
        return result.scalar() or 0

    # -------------------------------------------------------------------------
    # PRIVATE HELPERS
    # -------------------------------------------------------------------------

    async def _apply_approved_change(self, pending: PendingApproval) -> Optional[UUID]:
        """
        Apply an approved change to the dynamic_variables table.

        Returns the UUID of the affected variable.

        Uses DynamicVariablesService methods:
        - update_value(category, key, value, user_id, reason, ..., effective_from, effective_to)
        - create_variable(category, key, value, display_name, description, unit, validation_rules, user_id, reason, ...)
        - delete_variable(category, key, user_id, reason, ...)
        """
        from services.dynamic_variables_service import DynamicVariablesService

        dv_service = DynamicVariablesService(self.db)

        if pending.change_type == "update":
            # Update existing variable using category + key (the correct API)
            result = await dv_service.update_value(
                category=pending.category,
                key=pending.key,
                value=pending.proposed_value,
                user_id=pending.requested_by,
                reason=f"Approved: {pending.change_reason or 'No reason provided'}",
                user_email=pending.requested_by_email,
                effective_from=pending.effective_from,
                effective_to=pending.effective_to,
            )
            # Return the variable_id from the pending record or fetch it
            return pending.variable_id

        elif pending.change_type == "create":
            # Create new variable - requires display_name which we can derive from key
            display_name = pending.key.replace("_", " ").title()
            result = await dv_service.create_variable(
                category=pending.category,
                key=pending.key,
                value=pending.proposed_value,
                display_name=display_name,
                description=pending.change_reason,
                unit=None,
                validation_rules=None,
                user_id=pending.requested_by,
                reason=f"Approved: {pending.change_reason or 'No reason provided'}",
                user_email=pending.requested_by_email,
            )
            # Return the new variable ID from result
            return UUID(result["id"]) if result and "id" in result else None

        elif pending.change_type == "delete":
            # Soft delete using category + key
            await dv_service.delete_variable(
                category=pending.category,
                key=pending.key,
                user_id=pending.requested_by,
                reason=f"Approved deletion: {pending.change_reason or 'No reason provided'}",
                user_email=pending.requested_by_email,
            )
            return pending.variable_id

        return None

    def _row_to_pending_approval(self, row) -> PendingApproval:
        """Convert a database row to PendingApproval model."""
        return PendingApproval(
            id=row.id,
            variable_id=row.variable_id,
            category=row.category,
            key=row.key,
            current_value=row.current_value,
            proposed_value=row.proposed_value,
            change_type=row.change_type,
            change_reason=row.change_reason,
            effective_from=row.effective_from,
            effective_to=row.effective_to,
            requested_by=row.requested_by,
            requested_by_email=row.requested_by_email,
            status=ApprovalStatus(row.status),
            approvals_required=row.approvals_required,
            approvals_received=row.approvals_received,
            expires_at=row.expires_at,
            created_at=row.created_at,
        )

    def _to_json_str(self, value: Any) -> Optional[str]:
        """Convert a value to JSON string for JSONB storage."""
        import json

        if value is None:
            return None
        if isinstance(value, str):
            return value
        return json.dumps(value)


# =============================================================================
# HELPER FUNCTION
# =============================================================================


async def check_approval_required(
    db: AsyncSession, category: str, key: str, actor_role: str
) -> bool:
    """
    Convenience function to check if approval is required.

    Usage:
        if await check_approval_required(db, "pricing", "adult_price_cents", user.role):
            # Create approval request
        else:
            # Apply directly
    """
    service = ApprovalService(db)
    return await service.requires_approval(category, key, actor_role)
