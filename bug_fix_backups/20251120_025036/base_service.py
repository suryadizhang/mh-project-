"""
Base service class and mixins for dependency injection architecture.

This module provides the foundation for all service classes in the application:
- BaseService: Base class with common functionality (DB session, logging)
- EventTrackingMixin: Automatic event tracking for service actions
- NotificationMixin: Notification capabilities for any service
- CacheMixin: Redis caching support for any service

All services should inherit from BaseService and optionally include mixins.
"""

from datetime import datetime
import logging
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class BaseService:
    """
    Base service class that all services should inherit from.

    Provides:
    - Database session management
    - Standardized logging
    - Common utility methods
    - Error handling patterns

    Usage:
        class MyService(BaseService):
            def __init__(self, db: AsyncSession, logger: Optional[logging.Logger] = None):
                super().__init__(db, logger)
    """

    def __init__(self, db: AsyncSession, logger: logging.Logger | None = None):
        """
        Initialize base service.

        Args:
            db: SQLAlchemy async session for database operations
            logger: Optional logger instance. If not provided, creates one based on class name
        """
        self.db = db
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    async def _log_action(
        self,
        action: str,
        entity_type: str,
        entity_id: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Log a service action with structured data.

        Args:
            action: Action being performed (e.g., 'create', 'update', 'delete')
            entity_type: Type of entity (e.g., 'lead', 'booking', 'user')
            entity_id: ID of the entity being acted upon
            metadata: Additional context data
        """
        log_data = {
            "service": self.__class__.__name__,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        if metadata:
            log_data["metadata"] = metadata

        self.logger.info(f"{action} {entity_type}", extra=log_data)

    async def _handle_error(self, error: Exception, context: str) -> None:
        """
        Standardized error handling and logging.

        Args:
            error: The exception that occurred
            context: Context string describing what was being attempted
        """
        self.logger.error(
            f"Error in {self.__class__.__name__}.{context}: {error!s}",
            exc_info=True,
            extra={
                "service": self.__class__.__name__,
                "context": context,
                "error_type": type(error).__name__,
            },
        )

    async def _exists(self, model, **filters) -> bool:
        """
        Check if a record exists with given filters.

        Args:
            model: SQLAlchemy model class
            **filters: Field filters (e.g., id=123, email='test@example.com')

        Returns:
            True if record exists, False otherwise
        """
        query = select(model).filter_by(**filters)
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def _count(self, model, **filters) -> int:
        """
        Count records matching filters.

        Args:
            model: SQLAlchemy model class
            **filters: Field filters

        Returns:
            Number of matching records
        """
        query = select(func.count()).select_from(model).filter_by(**filters)
        result = await self.db.execute(query)
        return result.scalar() or 0


class EventTrackingMixin:
    """
    Mixin to add event tracking capabilities to any service.

    Tracks service actions to an event log for analytics, auditing, and debugging.
    Requires the service to have an event_service injected.

    Usage:
        class MyService(BaseService, EventTrackingMixin):
            def __init__(self, db: AsyncSession, event_service: EventService):
                super().__init__(db)
                self.event_service = event_service

            async def do_something(self):
                result = await self._perform_action()
                await self.track_event("action_performed", {"result": result})
                return result
    """

    async def track_event(
        self,
        action: str,
        metadata: dict[str, Any] | None = None,
        entity_type: str | None = None,
        entity_id: int | None = None,
        user_id: int | None = None,
    ) -> None:
        """
        Track an event for analytics/auditing.

        Args:
            action: Event action name (e.g., 'lead_created', 'booking_confirmed')
            metadata: Additional event data
            entity_type: Type of entity involved
            entity_id: ID of entity involved
            user_id: User who triggered the event
        """
        if not hasattr(self, "event_service"):
            # If no event service injected, just log it
            if hasattr(self, "logger"):
                self.logger.warning(
                    f"EventTrackingMixin used but no event_service injected in {self.__class__.__name__}"
                )
            return

        try:
            await self.event_service.log_event(
                service=self.__class__.__name__,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                user_id=user_id,
                metadata=metadata or {},
            )
        except Exception as e:
            # Don't let event tracking failures break the service
            if hasattr(self, "logger"):
                self.logger.error(f"Failed to track event: {e!s}")


class NotificationMixin:
    """
    Mixin to add notification capabilities to any service.

    Allows services to send notifications (email, SMS, push) without directly
    depending on notification infrastructure.
    Requires the service to have a notification_service injected.

    Usage:
        class MyService(BaseService, NotificationMixin):
            def __init__(self, db: AsyncSession, notification_service: NotificationService):
                super().__init__(db)
                self.notification_service = notification_service

            async def process_order(self, order):
                # ... process order ...
                await self.send_notification(
                    user_id=order.user_id,
                    message="Order confirmed!",
                    notification_type="email"
                )
    """

    async def send_notification(
        self,
        user_id: int,
        message: str,
        notification_type: str = "email",
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """
        Send a notification to a user.

        Args:
            user_id: Target user ID
            message: Notification message
            notification_type: Type of notification ('email', 'sms', 'push')
            metadata: Additional data for the notification

        Returns:
            True if notification sent successfully, False otherwise
        """
        if not hasattr(self, "notification_service"):
            if hasattr(self, "logger"):
                self.logger.warning(
                    f"NotificationMixin used but no notification_service injected in {self.__class__.__name__}"
                )
            return False

        try:
            await self.notification_service.send(
                user_id=user_id,
                message=message,
                notification_type=notification_type,
                metadata=metadata or {},
            )
            return True
        except Exception as e:
            if hasattr(self, "logger"):
                self.logger.error(f"Failed to send notification: {e!s}")
            return False


class CacheMixin:
    """
    Mixin to add Redis caching capabilities to any service.

    Provides simple caching methods for frequently accessed data.
    Requires the service to have a redis_client injected.

    Usage:
        class MyService(BaseService, CacheMixin):
            def __init__(self, db: AsyncSession, redis_client):
                super().__init__(db)
                self.redis_client = redis_client

            async def get_expensive_data(self, key: str):
                # Try cache first
                cached = await self.get_cached(f"expensive_data:{key}")
                if cached:
                    return cached

                # Compute and cache
                data = await self._compute_expensive_data(key)
                await self.set_cached(f"expensive_data:{key}", data, ttl=300)
                return data
    """

    async def get_cached(self, key: str) -> Any | None:
        """
        Retrieve a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not hasattr(self, "redis_client") or self.redis_client is None:
            return None

        try:
            import json

            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            if hasattr(self, "logger"):
                self.logger.error(f"Cache get failed for key {key}: {e!s}")
            return None

    async def set_cached(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        Store a value in cache.

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time to live in seconds (default: 5 minutes)

        Returns:
            True if cached successfully, False otherwise
        """
        if not hasattr(self, "redis_client") or self.redis_client is None:
            return False

        try:
            import json

            serialized = json.dumps(value)
            await self.redis_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            if hasattr(self, "logger"):
                self.logger.error(f"Cache set failed for key {key}: {e!s}")
            return False

    async def invalidate_cached(self, key: str) -> bool:
        """
        Remove a value from cache.

        Args:
            key: Cache key to invalidate

        Returns:
            True if deleted, False otherwise
        """
        if not hasattr(self, "redis_client") or self.redis_client is None:
            return False

        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            if hasattr(self, "logger"):
                self.logger.error(
                    f"Cache invalidation failed for key {key}: {e!s}"
                )
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all cache keys matching a pattern.

        Args:
            pattern: Redis key pattern (e.g., 'user:*', 'lead:123:*')

        Returns:
            Number of keys deleted
        """
        if not hasattr(self, "redis_client") or self.redis_client is None:
            return 0

        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                return await self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            if hasattr(self, "logger"):
                self.logger.error(
                    f"Cache pattern invalidation failed for {pattern}: {e!s}"
                )
            return 0
