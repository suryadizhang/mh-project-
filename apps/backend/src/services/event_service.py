"""
EventService for centralized event tracking across the application.

This service provides a unified interface for logging business events,
user actions, system events, and audit trails. Events are stored in the
database for analytics, debugging, and compliance purposes.

All services that use EventTrackingMixin will use this service.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.dialects.postgresql import insert

from core.base_service import BaseService
from models.system_event import SystemEvent  # We'll need to create this model


class EventService(BaseService):
    """
    Service for logging and retrieving system events.
    
    Events are used for:
    - Analytics and reporting
    - Audit trails for compliance
    - Debugging and troubleshooting
    - User activity tracking
    - System health monitoring
    
    Usage:
        event_service = EventService(db)
        await event_service.log_event(
            service="LeadService",
            action="lead_created",
            entity_type="lead",
            entity_id=123,
            user_id=45,
            metadata={"source": "facebook", "campaign_id": "summer2024"}
        )
    """
    
    async def log_event(
        self,
        service: str,
        action: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        user_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        severity: str = "info",
    ) -> SystemEvent:
        """
        Log an event to the database.
        
        Args:
            service: Name of the service logging the event (e.g., "LeadService")
            action: Action being performed (e.g., "lead_created", "booking_confirmed")
            entity_type: Type of entity involved (e.g., "lead", "booking", "user")
            entity_id: ID of the entity
            user_id: ID of user who triggered the event
            metadata: Additional JSON data about the event
            severity: Event severity ("debug", "info", "warning", "error")
        
        Returns:
            SystemEvent: The created event record
        """
        try:
            event = SystemEvent(
                service=service,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                user_id=user_id,
                metadata=metadata or {},
                severity=severity,
                timestamp=datetime.utcnow(),
            )
            
            self.db.add(event)
            await self.db.flush()
            
            await self._log_action(
                action="event_logged",
                entity_type="system_event",
                entity_id=event.id,
                metadata={"service": service, "action": action}
            )
            
            return event
            
        except Exception as e:
            await self._handle_error(e, "log_event")
            # Re-raise since we want to know if event logging fails
            raise
    
    async def log_lead_event(
        self,
        lead_id: int,
        action: str,
        user_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SystemEvent:
        """
        Convenience method for logging lead-related events.
        
        Args:
            lead_id: ID of the lead
            action: Action performed (e.g., "created", "updated", "converted")
            user_id: User who performed the action
            metadata: Additional context
        
        Returns:
            SystemEvent: The logged event
        """
        return await self.log_event(
            service="LeadService",
            action=f"lead_{action}",
            entity_type="lead",
            entity_id=lead_id,
            user_id=user_id,
            metadata=metadata,
        )
    
    async def log_booking_event(
        self,
        booking_id: int,
        action: str,
        user_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SystemEvent:
        """
        Convenience method for logging booking-related events.
        
        Args:
            booking_id: ID of the booking
            action: Action performed (e.g., "created", "confirmed", "cancelled")
            user_id: User who performed the action
            metadata: Additional context
        
        Returns:
            SystemEvent: The logged event
        """
        return await self.log_event(
            service="BookingService",
            action=f"booking_{action}",
            entity_type="booking",
            entity_id=booking_id,
            user_id=user_id,
            metadata=metadata,
        )
    
    async def log_user_event(
        self,
        user_id: int,
        action: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SystemEvent:
        """
        Convenience method for logging user-related events.
        
        Args:
            user_id: ID of the user
            action: Action performed (e.g., "login", "logout", "profile_updated")
            metadata: Additional context
        
        Returns:
            SystemEvent: The logged event
        """
        return await self.log_event(
            service="UserService",
            action=f"user_{action}",
            entity_type="user",
            entity_id=user_id,
            user_id=user_id,
            metadata=metadata,
        )
    
    async def get_events(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        user_id: Optional[int] = None,
        service: Optional[str] = None,
        action: Optional[str] = None,
        severity: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SystemEvent]:
        """
        Query events with filters.
        
        Args:
            entity_type: Filter by entity type
            entity_id: Filter by entity ID
            user_id: Filter by user ID
            service: Filter by service name
            action: Filter by action
            severity: Filter by severity level
            start_date: Filter events after this date
            end_date: Filter events before this date
            limit: Maximum number of results
            offset: Pagination offset
        
        Returns:
            List of matching events
        """
        try:
            query = select(SystemEvent)
            
            filters = []
            if entity_type:
                filters.append(SystemEvent.entity_type == entity_type)
            if entity_id:
                filters.append(SystemEvent.entity_id == entity_id)
            if user_id:
                filters.append(SystemEvent.user_id == user_id)
            if service:
                filters.append(SystemEvent.service == service)
            if action:
                filters.append(SystemEvent.action == action)
            if severity:
                filters.append(SystemEvent.severity == severity)
            if start_date:
                filters.append(SystemEvent.timestamp >= start_date)
            if end_date:
                filters.append(SystemEvent.timestamp <= end_date)
            
            if filters:
                query = query.where(and_(*filters))
            
            query = query.order_by(desc(SystemEvent.timestamp))
            query = query.limit(limit).offset(offset)
            
            result = await self.db.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            await self._handle_error(e, "get_events")
            return []
    
    async def get_recent_events(
        self,
        hours: int = 24,
        limit: int = 100,
    ) -> List[SystemEvent]:
        """
        Get recent events from the last N hours.
        
        Args:
            hours: Number of hours to look back
            limit: Maximum number of events to return
        
        Returns:
            List of recent events
        """
        start_date = datetime.utcnow() - timedelta(hours=hours)
        return await self.get_events(start_date=start_date, limit=limit)
    
    async def get_entity_timeline(
        self,
        entity_type: str,
        entity_id: int,
        limit: int = 50,
    ) -> List[SystemEvent]:
        """
        Get chronological timeline of events for a specific entity.
        
        Args:
            entity_type: Type of entity (e.g., "lead", "booking")
            entity_id: ID of the entity
            limit: Maximum number of events
        
        Returns:
            List of events in chronological order
        """
        return await self.get_events(
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit,
        )
    
    async def delete_old_events(self, days: int = 90) -> int:
        """
        Delete events older than specified days (for maintenance).
        
        Args:
            days: Delete events older than this many days
        
        Returns:
            Number of events deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            query = select(SystemEvent).where(SystemEvent.timestamp < cutoff_date)
            result = await self.db.execute(query)
            events_to_delete = result.scalars().all()
            
            for event in events_to_delete:
                await self.db.delete(event)
            
            await self.db.flush()
            
            count = len(events_to_delete)
            self.logger.info(f"Deleted {count} events older than {days} days")
            return count
            
        except Exception as e:
            await self._handle_error(e, "delete_old_events")
            return 0
