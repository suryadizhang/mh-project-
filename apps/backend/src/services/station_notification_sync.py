"""
Station Event Listeners for Notification Groups

Automatically creates/updates/deletes notification groups when stations change.
Integrates with station CRUD operations to keep notification groups in sync.
"""

import logging
from uuid import UUID, uuid4

from models.legacy_notification_groups import (  # Phase 2C: Updated from api.app.models.notification_groups
    NotificationGroup,
    NotificationGroupEvent,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Events station managers should receive
STATION_EVENTS = [
    "new_booking",
    "booking_edit",
    "booking_cancellation",
    "payment_received",
    "review_received",
    "complaint_received",
]


async def create_station_notification_group(
    db: AsyncSession,
    station_id: UUID,
    station_name: str,
    station_location: str,
    created_by: UUID | None = None,
) -> NotificationGroup:
    """
    Create notification group for a station.
    Called automatically when a new station is created.

    Args:
        db: Database session
        station_id: UUID of the station
        station_name: Name of the station
        station_location: Location string (e.g., "Sacramento, CA")
        created_by: User who created the station

    Returns:
        Created NotificationGroup
    """
    system_admin = created_by or UUID("00000000-0000-0000-0000-000000000000")

    group_name = f"Station Managers - {station_name}"

    # Check if group already exists
    result = await db.execute(
        select(NotificationGroup).where(
            NotificationGroup.name == group_name, NotificationGroup.station_id == station_id
        )
    )
    existing_group = result.scalar_one_or_none()

    if existing_group:
        logger.info(f"⏭️ Notification group already exists for station {station_name}")
        return existing_group

    # Create notification group
    group = NotificationGroup(
        id=uuid4(),
        name=group_name,
        description=f"Station managers and staff for {station_name} ({station_location}) - receive all station-specific notifications",
        station_id=station_id,
        is_active=True,
        created_by=system_admin,
    )

    db.add(group)
    await db.flush()

    # Subscribe to all station events
    for event_type in STATION_EVENTS:
        event_subscription = NotificationGroupEvent(
            id=uuid4(),
            group_id=group.id,
            event_type=event_type,
            is_active=True,
            created_by=system_admin,
        )
        db.add(event_subscription)

    await db.commit()
    await db.refresh(group)

    logger.info(f"✅ Created notification group for station: {station_name}")
    logger.info(f"   Group ID: {group.id}")
    logger.info(f"   Subscribed to: {', '.join(STATION_EVENTS)}")

    return group


async def update_station_notification_group(
    db: AsyncSession,
    station_id: UUID,
    new_station_name: str | None = None,
    new_station_location: str | None = None,
) -> NotificationGroup | None:
    """
    Update notification group when station is updated.
    Called automatically when a station is edited.

    Args:
        db: Database session
        station_id: UUID of the station
        new_station_name: New station name (if changed)
        new_station_location: New location (if changed)

    Returns:
        Updated NotificationGroup or None if not found
    """
    # Find the notification group for this station
    result = await db.execute(
        select(NotificationGroup).where(
            NotificationGroup.station_id == station_id, NotificationGroup.is_active
        )
    )
    group = result.scalar_one_or_none()

    if not group:
        logger.warning(f"⚠️ No notification group found for station {station_id}")
        return None

    # Update group if name or location changed
    if new_station_name:
        group.name = f"Station Managers - {new_station_name}"

    if new_station_location:
        group.description = f"Station managers and staff for {new_station_name or 'this station'} ({new_station_location}) - receive all station-specific notifications"

    await db.commit()
    await db.refresh(group)

    logger.info(f"✅ Updated notification group for station: {new_station_name or station_id}")

    return group


async def deactivate_station_notification_group(
    db: AsyncSession, station_id: UUID
) -> NotificationGroup | None:
    """
    Deactivate notification group when station is deactivated.
    Called automatically when a station is set to inactive.

    Args:
        db: Database session
        station_id: UUID of the station

    Returns:
        Deactivated NotificationGroup or None if not found
    """
    # Find the notification group for this station
    result = await db.execute(
        select(NotificationGroup).where(NotificationGroup.station_id == station_id)
    )
    group = result.scalar_one_or_none()

    if not group:
        logger.warning(f"⚠️ No notification group found for station {station_id}")
        return None

    # Deactivate the group (don't delete, preserve history)
    group.is_active = False

    await db.commit()
    await db.refresh(group)

    logger.info(f"✅ Deactivated notification group for station {station_id}")
    logger.info(f"   Group: {group.name}")
    logger.info("   Members will no longer receive notifications")

    return group


async def reactivate_station_notification_group(
    db: AsyncSession, station_id: UUID
) -> NotificationGroup | None:
    """
    Reactivate notification group when station is reactivated.
    Called automatically when a station is set back to active.

    Args:
        db: Database session
        station_id: UUID of the station

    Returns:
        Reactivated NotificationGroup or None if not found
    """
    # Find the notification group for this station
    result = await db.execute(
        select(NotificationGroup).where(NotificationGroup.station_id == station_id)
    )
    group = result.scalar_one_or_none()

    if not group:
        logger.warning(f"⚠️ No notification group found for station {station_id}")
        return None

    # Reactivate the group
    group.is_active = True

    await db.commit()
    await db.refresh(group)

    logger.info(f"✅ Reactivated notification group for station {station_id}")
    logger.info(f"   Group: {group.name}")
    logger.info("   Members will resume receiving notifications")

    return group


async def delete_station_notification_group(db: AsyncSession, station_id: UUID) -> bool:
    """
    Delete notification group when station is permanently deleted.
    Called automatically when a station is deleted.

    Args:
        db: Database session
        station_id: UUID of the station

    Returns:
        True if deleted, False if not found
    """
    # Find the notification group for this station
    result = await db.execute(
        select(NotificationGroup).where(NotificationGroup.station_id == station_id)
    )
    group = result.scalar_one_or_none()

    if not group:
        logger.warning(f"⚠️ No notification group found for station {station_id}")
        return False

    group_name = group.name

    # Delete the group (CASCADE will delete members and events)
    await db.delete(group)
    await db.commit()

    logger.info(f"✅ Deleted notification group: {group_name}")
    logger.info("   All members and event subscriptions removed")

    return True


# ============================================================================
# INTEGRATION HELPERS
# ============================================================================


async def sync_station_with_notification_group(
    db: AsyncSession,
    station_id: UUID,
    station_name: str,
    station_location: str,
    is_active: bool,
    created_by: UUID | None = None,
) -> NotificationGroup:
    """
    Helper function to ensure notification group exists and is synced with station.

    Use this in station CRUD operations:
    - After creating a station
    - After updating a station

    Args:
        db: Database session
        station_id: UUID of the station
        station_name: Name of the station
        station_location: Location string
        is_active: Whether station is active
        created_by: User who created/updated the station

    Returns:
        NotificationGroup (created or updated)
    """
    # Find existing group
    result = await db.execute(
        select(NotificationGroup).where(NotificationGroup.station_id == station_id)
    )
    existing_group = result.scalar_one_or_none()

    if existing_group:
        # Update existing group
        existing_group.name = f"Station Managers - {station_name}"
        existing_group.description = f"Station managers and staff for {station_name} ({station_location}) - receive all station-specific notifications"
        existing_group.is_active = is_active

        await db.commit()
        await db.refresh(existing_group)

        logger.info(f"✅ Synced notification group for station: {station_name}")
        return existing_group
    else:
        # Create new group
        return await create_station_notification_group(
            db=db,
            station_id=station_id,
            station_name=station_name,
            station_location=station_location,
            created_by=created_by,
        )
