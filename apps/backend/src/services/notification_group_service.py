"""
Notification Group Management Service

Handles CRUD operations for notification groups, members, and event subscriptions.
Integrates with unified_notification_service.py to send notifications to groups.
"""

import logging
from typing import Any
from uuid import UUID, uuid4

from api.app.models.notification_groups import (
    DEFAULT_GROUPS,
    NotificationEventType,
    NotificationGroup,
    NotificationGroupEvent,
    NotificationGroupMember,
)
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)


class NotificationGroupService:
    """Service for managing notification groups"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========================================================================
    # GROUP MANAGEMENT
    # ========================================================================

    async def create_group(
        self,
        name: str,
        description: str,
        created_by: UUID,
        station_id: UUID | None = None,
        event_types: list[str] | None = None,
    ) -> NotificationGroup:
        """
        Create a new notification group.

        Args:
            name: Group name
            description: Group description
            created_by: User ID creating the group
            station_id: Optional station ID for filtering (None = all stations)
            event_types: List of event types to subscribe to (default: ["all"])

        Returns:
            Created NotificationGroup
        """
        # Create group
        group = NotificationGroup(
            id=uuid4(),
            name=name,
            description=description,
            station_id=station_id,
            created_by=created_by,
        )

        self.db.add(group)
        await self.db.flush()  # Get group ID

        # Add event subscriptions
        if event_types is None:
            event_types = ["all"]

        for event_type in event_types:
            event = NotificationGroupEvent(
                id=uuid4(),
                group_id=group.id,
                event_type=event_type,  # Store as string directly
                created_by=created_by,
            )
            self.db.add(event)

        await self.db.commit()
        await self.db.refresh(group)

        logger.info(f"✅ Created notification group: {name} (ID: {group.id})")

        return group

    async def get_group(self, group_id: UUID) -> NotificationGroup | None:
        """Get group by ID with members and events loaded"""
        query = (
            select(NotificationGroup)
            .options(
                selectinload(NotificationGroup.members),
                selectinload(NotificationGroup.event_subscriptions),
            )
            .where(NotificationGroup.id == group_id)
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_groups(
        self, station_id: UUID | None = None, include_inactive: bool = False
    ) -> list[NotificationGroup]:
        """
        List all notification groups.

        Args:
            station_id: Filter by station (None = all stations)
            include_inactive: Include inactive groups

        Returns:
            List of NotificationGroups
        """
        query = select(NotificationGroup).options(
            selectinload(NotificationGroup.members),
            selectinload(NotificationGroup.event_subscriptions),
        )

        # Apply filters
        conditions = []
        if station_id:
            conditions.append(
                or_(
                    NotificationGroup.station_id == station_id,
                    NotificationGroup.station_id.is_(None),  # Include all-stations groups
                )
            )

        if not include_inactive:
            conditions.append(NotificationGroup.is_active)

        if conditions:
            query = query.where(and_(*conditions))

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_group(
        self,
        group_id: UUID,
        name: str | None = None,
        description: str | None = None,
        is_active: bool | None = None,
    ) -> NotificationGroup:
        """Update group details"""
        group = await self.get_group(group_id)
        if not group:
            raise ValueError(f"Group {group_id} not found")

        if name is not None:
            group.name = name
        if description is not None:
            group.description = description
        if is_active is not None:
            group.is_active = is_active

        await self.db.commit()
        await self.db.refresh(group)

        logger.info(f"✅ Updated notification group: {group.name}")

        return group

    async def delete_group(self, group_id: UUID) -> bool:
        """Delete a notification group (cascade deletes members and events)"""
        group = await self.get_group(group_id)
        if not group:
            return False

        await self.db.delete(group)
        await self.db.commit()

        logger.info(f"✅ Deleted notification group: {group.name}")

        return True

    # ========================================================================
    # MEMBER MANAGEMENT
    # ========================================================================

    async def add_member(
        self,
        group_id: UUID,
        phone_number: str,
        name: str,
        added_by: UUID,
        user_id: UUID | None = None,
        email: str | None = None,
        receive_whatsapp: bool = True,
        receive_sms: bool = False,
        receive_email: bool = False,
    ) -> NotificationGroupMember:
        """
        Add a member to a notification group.

        Args:
            group_id: Group to add member to
            phone_number: Member's WhatsApp phone number
            name: Member's name
            added_by: User ID adding the member
            user_id: Optional link to users table
            email: Optional email address
            receive_whatsapp: Enable WhatsApp notifications
            receive_sms: Enable SMS notifications
            receive_email: Enable email notifications

        Returns:
            Created NotificationGroupMember
        """
        member = NotificationGroupMember(
            id=uuid4(),
            group_id=group_id,
            user_id=user_id,
            phone_number=phone_number,
            name=name,
            email=email,
            receive_whatsapp=receive_whatsapp,
            receive_sms=receive_sms,
            receive_email=receive_email,
            added_by=added_by,
        )

        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)

        logger.info(f"✅ Added {name} ({phone_number}) to group {group_id}")

        return member

    async def remove_member(self, member_id: UUID) -> bool:
        """Remove a member from a notification group"""
        query = select(NotificationGroupMember).where(NotificationGroupMember.id == member_id)
        result = await self.db.execute(query)
        member = result.scalar_one_or_none()

        if not member:
            return False

        await self.db.delete(member)
        await self.db.commit()

        logger.info(f"✅ Removed {member.name} from group")

        return True

    async def update_member(
        self,
        member_id: UUID,
        is_active: bool | None = None,
        receive_whatsapp: bool | None = None,
        receive_sms: bool | None = None,
        receive_email: bool | None = None,
    ) -> NotificationGroupMember:
        """Update member notification preferences"""
        query = select(NotificationGroupMember).where(NotificationGroupMember.id == member_id)
        result = await self.db.execute(query)
        member = result.scalar_one_or_none()

        if not member:
            raise ValueError(f"Member {member_id} not found")

        if is_active is not None:
            member.is_active = is_active
        if receive_whatsapp is not None:
            member.receive_whatsapp = receive_whatsapp
        if receive_sms is not None:
            member.receive_sms = receive_sms
        if receive_email is not None:
            member.receive_email = receive_email

        await self.db.commit()
        await self.db.refresh(member)

        logger.info(f"✅ Updated preferences for {member.name}")

        return member

    async def list_group_members(
        self, group_id: UUID, include_inactive: bool = False
    ) -> list[NotificationGroupMember]:
        """List all members of a group"""
        query = select(NotificationGroupMember).where(NotificationGroupMember.group_id == group_id)

        if not include_inactive:
            query = query.where(NotificationGroupMember.is_active)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ========================================================================
    # EVENT SUBSCRIPTION MANAGEMENT
    # ========================================================================

    async def add_event_subscription(
        self, group_id: UUID, event_type: str, created_by: UUID
    ) -> NotificationGroupEvent:
        """Add an event subscription to a group"""
        event = NotificationGroupEvent(
            id=uuid4(),
            group_id=group_id,
            event_type=event_type,  # Store as string directly
            created_by=created_by,
        )

        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)

        logger.info(f"✅ Added {event_type} subscription to group {group_id}")

        return event

    async def remove_event_subscription(self, event_id: UUID) -> bool:
        """Remove an event subscription from a group"""
        query = select(NotificationGroupEvent).where(NotificationGroupEvent.id == event_id)
        result = await self.db.execute(query)
        event = result.scalar_one_or_none()

        if not event:
            return False

        await self.db.delete(event)
        await self.db.commit()

        logger.info("✅ Removed event subscription")

        return True

    # ========================================================================
    # NOTIFICATION ROUTING
    # ========================================================================

    async def get_recipients_for_event(
        self,
        event_type: NotificationEventType,
        station_id: UUID | None = None,
        priority: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get all members who should receive a specific event notification.

        Args:
            event_type: Type of event (new_booking, payment_received, etc.)
            station_id: Optional station ID for filtering
            priority: Optional priority for priority-based filtering

        Returns:
            List of dicts with member info and notification preferences
        """
        # Build query to find all groups subscribed to this event
        query = (
            select(NotificationGroup, NotificationGroupMember)
            .join(NotificationGroupEvent, NotificationGroup.id == NotificationGroupEvent.group_id)
            .join(NotificationGroupMember, NotificationGroup.id == NotificationGroupMember.group_id)
            .where(
                and_(
                    NotificationGroup.is_active,
                    NotificationGroupMember.is_active,
                    NotificationGroupEvent.is_active,
                    or_(
                        NotificationGroupEvent.event_type == event_type,
                        NotificationGroupEvent.event_type == NotificationEventType.ALL,
                    ),
                )
            )
        )

        # Apply station filtering
        if station_id:
            query = query.where(
                or_(
                    NotificationGroup.station_id == station_id,
                    NotificationGroup.station_id.is_(None),  # Include all-stations groups
                )
            )

        result = await self.db.execute(query)
        rows = result.all()

        # Build recipients list
        recipients = []
        seen_phones = set()  # Deduplicate by phone number

        for group, member in rows:
            if member.phone_number in seen_phones:
                continue

            seen_phones.add(member.phone_number)

            recipients.append(
                {
                    "phone_number": member.phone_number,
                    "name": member.name,
                    "email": member.email,
                    "user_id": str(member.user_id) if member.user_id else None,
                    "group_name": group.name,
                    "receive_whatsapp": member.receive_whatsapp,
                    "receive_sms": member.receive_sms,
                    "receive_email": member.receive_email,
                }
            )

        logger.info(f"📧 Found {len(recipients)} recipients for {event_type.value} event")

        return recipients

    # ========================================================================
    # INITIALIZATION
    # ========================================================================

    async def initialize_default_groups(self, created_by: UUID) -> list[NotificationGroup]:
        """Create default notification groups if they don't exist"""
        created_groups = []

        for group_config in DEFAULT_GROUPS:
            # Check if group already exists
            query = select(NotificationGroup).where(NotificationGroup.name == group_config["name"])
            result = await self.db.execute(query)
            existing = result.scalar_one_or_none()

            if existing:
                logger.info(f"⏭️  Group '{group_config['name']}' already exists")
                continue

            # Create group
            group = await self.create_group(
                name=group_config["name"],
                description=group_config["description"],
                created_by=created_by,
                station_id=group_config.get("station_id"),
                event_types=group_config["events"],
            )

            created_groups.append(group)

        logger.info(f"✅ Initialized {len(created_groups)} default groups")

        return created_groups
