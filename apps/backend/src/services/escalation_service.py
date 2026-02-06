"""
Escalation Service
Business logic for customer support escalations
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

# MIGRATED: from models.escalation → db.models.escalation
from db.models.support_communications import (
    Escalation,
    EscalationStatus,
    EscalationMethod,
    EscalationPriority,
)
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class EscalationService:
    """Service for managing customer support escalations"""

    def __init__(self, db: Session):
        self.db = db

    async def create_escalation(
        self,
        conversation_id: str,
        phone: str,
        reason: str,
        preferred_method: str = "sms",
        priority: str = "medium",
        email: Optional[str] = None,
        customer_id: Optional[str] = None,
        customer_consent: bool = True,
        metadata: Optional[dict] = None,
    ) -> Escalation:
        """
        Create a new escalation and pause the conversation

        Args:
            conversation_id: ID of the conversation to escalate
            phone: Customer phone number
            reason: Reason for escalation
            preferred_method: sms, call, or email
            priority: low, medium, high, or urgent
            email: Optional customer email
            customer_id: Optional customer ID
            customer_consent: Customer consent for SMS/calls
            metadata: Additional context

        Returns:
            Created Escalation object

        Raises:
            ValueError: If validation fails
            RuntimeError: If escalation creation fails
        """
        try:
            # Check for existing open escalation for this conversation
            existing = (
                self.db.query(Escalation)
                .filter(
                    and_(
                        Escalation.conversation_id == UUID(conversation_id),
                        Escalation.status.in_(
                            [
                                EscalationStatus.PENDING,
                                EscalationStatus.ASSIGNED,
                                EscalationStatus.IN_PROGRESS,
                                EscalationStatus.WAITING_CUSTOMER,
                            ]
                        ),
                    )
                )
                .first()
            )

            if existing:
                logger.warning(f"Escalation already exists for conversation {conversation_id}")
                return existing

            # Create escalation
            escalation = Escalation(
                id=uuid4(),
                conversation_id=UUID(conversation_id),
                customer_id=UUID(customer_id) if customer_id else None,
                phone=phone,
                email=email,
                preferred_method=EscalationMethod(preferred_method),
                reason=reason,
                priority=EscalationPriority(priority),
                status=EscalationStatus.PENDING,
                customer_consent=str(customer_consent).lower(),
                metadata=metadata or {},
                tags=[],
            )

            self.db.add(escalation)

            # TODO: Pause conversation (update conversation.paused = True)
            # This will be implemented when we add conversation model

            self.db.commit()
            self.db.refresh(escalation)

            # Broadcast WebSocket event to all connected admins
            try:
                import asyncio
                from api.v1.websockets.escalations import broadcast_escalation_event

                # Run async broadcast in background (non-blocking)
                asyncio.create_task(
                    broadcast_escalation_event(
                        "created",
                        escalation_data={
                            "id": str(escalation.id),
                            "priority": escalation.priority,
                            "status": escalation.status,
                            "customer_phone": escalation.phone,
                            "reason": escalation.reason[:100],
                            "method": escalation.preferred_method,
                            "created_at": (
                                escalation.created_at.isoformat() if escalation.created_at else None
                            ),
                        },
                    )
                )
                logger.info(f"✅ Broadcasted escalation_created event for {escalation.id}")
            except Exception as e:
                logger.error(f"Failed to broadcast WebSocket event: {e}")
                # Don't fail escalation creation if WebSocket broadcast fails

            logger.info(
                f"Created escalation {escalation.id} for conversation {conversation_id}, "
                f"priority: {priority}, method: {preferred_method}"
            )

            return escalation

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create escalation: {str(e)}")
            raise RuntimeError(f"Failed to create escalation: {str(e)}")

    async def get_escalation(self, escalation_id: str) -> Optional[Escalation]:
        """Get escalation by ID"""
        return self.db.query(Escalation).filter(Escalation.id == UUID(escalation_id)).first()

    async def assign_escalation(
        self, escalation_id: str, admin_id: str, notes: Optional[str] = None
    ) -> Escalation:
        """Assign escalation to an admin"""
        escalation = await self.get_escalation(escalation_id)
        if not escalation:
            raise ValueError(f"Escalation {escalation_id} not found")

        escalation.assigned_to_id = UUID(admin_id)
        escalation.assigned_at = datetime.utcnow()
        escalation.status = EscalationStatus.ASSIGNED

        if notes:
            escalation.escalation_metadata["assignment_notes"] = notes

        self.db.commit()
        self.db.refresh(escalation)

        # Broadcast WebSocket event
        try:
            import asyncio
            from api.v1.websockets.escalations import broadcast_escalation_event

            asyncio.create_task(
                broadcast_escalation_event(
                    "updated",
                    escalation_data={
                        "id": str(escalation.id),
                        "status": escalation.status,
                        "assigned_to_id": str(escalation.assigned_to_id),
                        "assigned_at": (
                            escalation.assigned_at.isoformat() if escalation.assigned_at else None
                        ),
                        "update_type": "assigned",
                    },
                )
            )
        except Exception as e:
            logger.error(f"Failed to broadcast assignment event: {e}")

        logger.info(f"Assigned escalation {escalation_id} to admin {admin_id}")
        return escalation

    async def update_status(
        self, escalation_id: str, status: str, notes: Optional[str] = None
    ) -> Escalation:
        """Update escalation status"""
        escalation = await self.get_escalation(escalation_id)
        if not escalation:
            raise ValueError(f"Escalation {escalation_id} not found")

        old_status = escalation.status
        escalation.status = EscalationStatus(status)
        escalation.updated_at = datetime.utcnow()

        if notes:
            if "status_history" not in escalation.escalation_metadata:
                escalation.escalation_metadata["status_history"] = []
            escalation.escalation_metadata["status_history"].append(
                {
                    "from": old_status,
                    "to": status,
                    "notes": notes,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        self.db.commit()
        self.db.refresh(escalation)

        # Broadcast WebSocket event
        try:
            import asyncio
            from api.v1.websockets.escalations import broadcast_escalation_event

            asyncio.create_task(
                broadcast_escalation_event(
                    "updated",
                    escalation_data={
                        "id": str(escalation.id),
                        "status": escalation.status,
                        "old_status": old_status,
                        "update_type": "status_change",
                        "updated_at": escalation.updated_at.isoformat(),
                    },
                )
            )
        except Exception as e:
            logger.error(f"Failed to broadcast status update event: {e}")

        logger.info(f"Updated escalation {escalation_id} status: {old_status} -> {status}")
        return escalation

    async def resolve_escalation(
        self, escalation_id: str, resolved_by_id: str, resolution_notes: str, resume_ai: bool = True
    ) -> Escalation:
        """
        Resolve an escalation

        Args:
            escalation_id: ID of the escalation
            resolved_by_id: ID of the admin resolving
            resolution_notes: Notes about the resolution
            resume_ai: Whether to resume AI conversation

        Returns:
            Updated Escalation object
        """
        escalation = await self.get_escalation(escalation_id)
        if not escalation:
            raise ValueError(f"Escalation {escalation_id} not found")

        escalation.status = EscalationStatus.RESOLVED
        escalation.resolved_by_id = UUID(resolved_by_id)
        escalation.resolved_at = datetime.utcnow()
        escalation.resolution_notes = resolution_notes

        # TODO: Resume conversation (update conversation.paused = False) if resume_ai is True
        if resume_ai:
            escalation.escalation_metadata["ai_resumed"] = True
            logger.info(f"AI conversation resumed for escalation {escalation_id}")

        self.db.commit()
        self.db.refresh(escalation)

        # Broadcast WebSocket event
        try:
            import asyncio
            from api.v1.websockets.escalations import broadcast_escalation_event

            asyncio.create_task(
                broadcast_escalation_event(
                    "resolved",
                    escalation_data={
                        "id": str(escalation.id),
                        "status": escalation.status,
                        "resolved_by_id": str(escalation.resolved_by_id),
                        "resolved_at": escalation.resolved_at.isoformat(),
                        "resolution_notes": resolution_notes[:200],  # Truncate for broadcast
                        "update_type": "resolved",
                    },
                )
            )
        except Exception as e:
            logger.error(f"Failed to broadcast resolution event: {e}")

        logger.info(f"Resolved escalation {escalation_id} by admin {resolved_by_id}")
        return escalation

    async def list_escalations(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_to_id: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Escalation], int]:
        """
        List escalations with filters

        Returns:
            Tuple of (escalations, total_count)
        """
        query = self.db.query(Escalation)

        # Apply filters
        if status:
            query = query.filter(Escalation.status == EscalationStatus(status))
        if priority:
            query = query.filter(Escalation.priority == EscalationPriority(priority))
        if assigned_to_id:
            query = query.filter(Escalation.assigned_to_id == UUID(assigned_to_id))
        if from_date:
            query = query.filter(Escalation.created_at >= from_date)
        if to_date:
            query = query.filter(Escalation.created_at <= to_date)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        escalations = (
            query.order_by(Escalation.created_at.desc()).offset(offset).limit(page_size).all()
        )

        return escalations, total

    async def get_stats(self) -> dict:
        """Get escalation statistics"""
        # Count by status
        status_counts = dict(
            self.db.query(Escalation.status, func.count(Escalation.id))
            .group_by(Escalation.status)
            .all()
        )

        # Total escalations
        total = sum(status_counts.values())

        # Average resolution time (in hours)
        resolved_escalations = (
            self.db.query(
                func.avg(
                    func.extract("epoch", Escalation.resolved_at - Escalation.created_at) / 3600
                )
            )
            .filter(Escalation.resolved_at.isnot(None))
            .scalar()
        )

        # Escalations today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        escalations_today = (
            self.db.query(func.count(Escalation.id))
            .filter(Escalation.created_at >= today_start)
            .scalar()
        )

        # Escalations this week
        week_start = today_start - timedelta(days=today_start.weekday())
        escalations_this_week = (
            self.db.query(func.count(Escalation.id))
            .filter(Escalation.created_at >= week_start)
            .scalar()
        )

        return {
            "total_escalations": total,
            "pending": status_counts.get(EscalationStatus.PENDING, 0),
            "assigned": status_counts.get(EscalationStatus.ASSIGNED, 0),
            "in_progress": status_counts.get(EscalationStatus.IN_PROGRESS, 0),
            "resolved": status_counts.get(EscalationStatus.RESOLVED, 0),
            "closed": status_counts.get(EscalationStatus.CLOSED, 0),
            "error": status_counts.get(EscalationStatus.ERROR, 0),
            "average_resolution_time_hours": resolved_escalations,
            "escalations_today": escalations_today,
            "escalations_this_week": escalations_this_week,
        }

    async def record_sms_sent(self, escalation_id: str) -> Escalation:
        """Record that SMS was sent to customer"""
        escalation = await self.get_escalation(escalation_id)
        if not escalation:
            raise ValueError(f"Escalation {escalation_id} not found")

        escalation.sms_sent = datetime.utcnow()
        escalation.last_contact_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(escalation)

        return escalation

    async def record_call_initiated(self, escalation_id: str) -> Escalation:
        """Record that call was initiated to customer"""
        escalation = await self.get_escalation(escalation_id)
        if not escalation:
            raise ValueError(f"Escalation {escalation_id} not found")

        escalation.call_initiated = datetime.utcnow()
        escalation.last_contact_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(escalation)

        return escalation

    async def record_error(self, escalation_id: str, error_message: str) -> Escalation:
        """Record an error with the escalation"""
        escalation = await self.get_escalation(escalation_id)
        if not escalation:
            raise ValueError(f"Escalation {escalation_id} not found")

        escalation.status = EscalationStatus.ERROR
        escalation.error_message = error_message
        escalation.retry_count = str(int(escalation.retry_count) + 1)

        self.db.commit()
        self.db.refresh(escalation)

        logger.error(f"Escalation {escalation_id} error: {error_message}")
        return escalation


# Import timedelta at the top if not already imported
from datetime import timedelta
