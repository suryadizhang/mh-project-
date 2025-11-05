"""
Admin API Endpoints for Notification Group Management

Super admin endpoints for:
- Creating/editing/deleting notification groups
- Adding/removing team members
- Configuring event subscriptions
- Managing station-specific groups
"""

from typing import Any
from uuid import UUID

from api.app.database import get_db
from api.app.models.notification_groups import NotificationEventType
from api.app.utils.auth import require_super_admin
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from services.notification_group_service import NotificationGroupService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/notification-groups", tags=["notification-groups", "admin"])


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================


class GroupCreateRequest(BaseModel):
    """Request to create a new notification group"""

    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10)
    station_id: UUID | None = Field(None, description="Station ID (null = all stations)")
    event_types: list[str] = Field(default=["all"], description="Event types to subscribe to")

    @field_validator("event_types")
    @classmethod
    def validate_event_types(cls, v):
        valid_events = [e.value for e in NotificationEventType]
        for event in v:
            if event not in valid_events:
                raise ValueError(f"Invalid event type: {event}")
        return v


class GroupUpdateRequest(BaseModel):
    """Request to update a notification group"""

    name: str | None = Field(None, min_length=3, max_length=100)
    description: str | None = Field(None, min_length=10)
    is_active: bool | None = None


class MemberAddRequest(BaseModel):
    """Request to add a member to a group"""

    phone_number: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")
    name: str = Field(..., min_length=2, max_length=100)
    email: str | None = None
    user_id: UUID | None = None
    receive_whatsapp: bool = True
    receive_sms: bool = False
    receive_email: bool = False


class MemberUpdateRequest(BaseModel):
    """Request to update member preferences"""

    is_active: bool | None = None
    receive_whatsapp: bool | None = None
    receive_sms: bool | None = None
    receive_email: bool | None = None


class EventSubscriptionRequest(BaseModel):
    """Request to add event subscription"""

    event_type: str = Field(...)
    priority_filter: dict | None = None
    custom_filters: dict | None = None

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v):
        valid_events = [e.value for e in NotificationEventType]
        if v not in valid_events:
            raise ValueError(f"Invalid event type: {v}")
        return v


class GroupResponse(BaseModel):
    """Response model for notification group"""

    id: UUID
    name: str
    description: str
    station_id: UUID | None
    is_active: bool
    member_count: int
    event_count: int
    created_at: str


class MemberResponse(BaseModel):
    """Response model for group member"""

    id: UUID
    name: str
    phone_number: str
    email: str | None
    is_active: bool
    receive_whatsapp: bool
    receive_sms: bool
    receive_email: bool
    joined_at: str


# ============================================================================
# GROUP MANAGEMENT ENDPOINTS
# ============================================================================


@router.post(
    "/",
    response_model=GroupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create notification group",
    description="""
    Create a new notification group (Super Admin only).

    ## Examples:
    - "All Admins" - Receives all events from all stations
    - "Station CA-BAY-001 Managers" - Only receives events for CA-BAY-001
    - "Payment Team" - Only receives payment-related events
    """,
)
async def create_group(
    data: GroupCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(require_super_admin()),
):
    """Create a new notification group"""
    service = NotificationGroupService(db)

    try:
        group = await service.create_group(
            name=data.name,
            description=data.description,
            created_by=UUID(current_user["id"]),
            station_id=data.station_id,
            event_types=data.event_types,
        )

        return GroupResponse(
            id=group.id,
            name=group.name,
            description=group.description,
            station_id=group.station_id,
            is_active=group.is_active,
            member_count=len(group.members),
            event_count=len(group.event_subscriptions),
            created_at=group.created_at.isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/",
    response_model=list[GroupResponse],
    summary="List notification groups",
    description="Get all notification groups (optionally filtered by station)",
)
async def list_groups(
    station_id: UUID | None = None,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(require_super_admin()),
):
    """List all notification groups"""
    service = NotificationGroupService(db)

    groups = await service.list_groups(station_id=station_id, include_inactive=include_inactive)

    return [
        GroupResponse(
            id=g.id,
            name=g.name,
            description=g.description,
            station_id=g.station_id,
            is_active=g.is_active,
            member_count=len(g.members),
            event_count=len(g.event_subscriptions),
            created_at=g.created_at.isoformat(),
        )
        for g in groups
    ]


@router.get(
    "/{group_id}",
    summary="Get notification group details",
    description="Get detailed information about a notification group",
)
async def get_group(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(require_super_admin()),
):
    """Get notification group details"""
    service = NotificationGroupService(db)

    group = await service.get_group(group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    return {
        "id": str(group.id),
        "name": group.name,
        "description": group.description,
        "station_id": str(group.station_id) if group.station_id else None,
        "is_active": group.is_active,
        "created_at": group.created_at.isoformat(),
        "members": [
            {
                "id": str(m.id),
                "name": m.name,
                "phone_number": m.phone_number,
                "email": m.email,
                "is_active": m.is_active,
                "receive_whatsapp": m.receive_whatsapp,
                "receive_sms": m.receive_sms,
                "receive_email": m.receive_email,
                "joined_at": m.joined_at.isoformat(),
            }
            for m in group.members
        ],
        "event_subscriptions": [
            {
                "id": str(e.id),
                "event_type": e.event_type.value,
                "priority_filter": e.priority_filter,
                "custom_filters": e.custom_filters,
                "is_active": e.is_active,
            }
            for e in group.event_subscriptions
        ],
    }


@router.patch(
    "/{group_id}",
    response_model=GroupResponse,
    summary="Update notification group",
    description="Update group name, description, or active status",
)
async def update_group(
    group_id: UUID,
    data: GroupUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(require_super_admin()),
):
    """Update notification group"""
    service = NotificationGroupService(db)

    try:
        group = await service.update_group(
            group_id=group_id,
            name=data.name,
            description=data.description,
            is_active=data.is_active,
        )

        return GroupResponse(
            id=group.id,
            name=group.name,
            description=group.description,
            station_id=group.station_id,
            is_active=group.is_active,
            member_count=len(group.members),
            event_count=len(group.event_subscriptions),
            created_at=group.created_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete notification group",
    description="Delete a notification group (cascade deletes all members and subscriptions)",
)
async def delete_group(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(require_super_admin()),
):
    """Delete notification group"""
    service = NotificationGroupService(db)

    success = await service.delete_group(group_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")


# ============================================================================
# MEMBER MANAGEMENT ENDPOINTS
# ============================================================================


@router.post(
    "/{group_id}/members",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add member to group",
    description="Add a team member to a notification group",
)
async def add_member(
    group_id: UUID,
    data: MemberAddRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(require_super_admin()),
):
    """Add member to notification group"""
    service = NotificationGroupService(db)

    try:
        member = await service.add_member(
            group_id=group_id,
            phone_number=data.phone_number,
            name=data.name,
            added_by=UUID(current_user["id"]),
            user_id=data.user_id,
            email=data.email,
            receive_whatsapp=data.receive_whatsapp,
            receive_sms=data.receive_sms,
            receive_email=data.receive_email,
        )

        return MemberResponse(
            id=member.id,
            name=member.name,
            phone_number=member.phone_number,
            email=member.email,
            is_active=member.is_active,
            receive_whatsapp=member.receive_whatsapp,
            receive_sms=member.receive_sms,
            receive_email=member.receive_email,
            joined_at=member.joined_at.isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{group_id}/members",
    response_model=list[MemberResponse],
    summary="List group members",
    description="Get all members of a notification group",
)
async def list_members(
    group_id: UUID,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(require_super_admin()),
):
    """List group members"""
    service = NotificationGroupService(db)

    members = await service.list_group_members(group_id=group_id, include_inactive=include_inactive)

    return [
        MemberResponse(
            id=m.id,
            name=m.name,
            phone_number=m.phone_number,
            email=m.email,
            is_active=m.is_active,
            receive_whatsapp=m.receive_whatsapp,
            receive_sms=m.receive_sms,
            receive_email=m.receive_email,
            joined_at=m.joined_at.isoformat(),
        )
        for m in members
    ]


@router.patch(
    "/{group_id}/members/{member_id}",
    response_model=MemberResponse,
    summary="Update member preferences",
    description="Update member's notification preferences",
)
async def update_member(
    group_id: UUID,
    member_id: UUID,
    data: MemberUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(require_super_admin()),
):
    """Update member preferences"""
    service = NotificationGroupService(db)

    try:
        member = await service.update_member(
            member_id=member_id,
            is_active=data.is_active,
            receive_whatsapp=data.receive_whatsapp,
            receive_sms=data.receive_sms,
            receive_email=data.receive_email,
        )

        return MemberResponse(
            id=member.id,
            name=member.name,
            phone_number=member.phone_number,
            email=member.email,
            is_active=member.is_active,
            receive_whatsapp=member.receive_whatsapp,
            receive_sms=member.receive_sms,
            receive_email=member.receive_email,
            joined_at=member.joined_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/{group_id}/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove member from group",
    description="Remove a team member from a notification group",
)
async def remove_member(
    group_id: UUID,
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(require_super_admin()),
):
    """Remove member from group"""
    service = NotificationGroupService(db)

    success = await service.remove_member(member_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")


# ============================================================================
# EVENT SUBSCRIPTION ENDPOINTS
# ============================================================================


@router.post(
    "/{group_id}/events",
    status_code=status.HTTP_201_CREATED,
    summary="Add event subscription",
    description="Subscribe group to a notification event type",
)
async def add_event_subscription(
    group_id: UUID,
    data: EventSubscriptionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(require_super_admin()),
):
    """Add event subscription to group"""
    service = NotificationGroupService(db)

    try:
        event = await service.add_event_subscription(
            group_id=group_id,
            event_type=data.event_type,
            created_by=UUID(current_user["id"]),
            priority_filter=data.priority_filter,
            custom_filters=data.custom_filters,
        )

        return {
            "id": str(event.id),
            "event_type": event.event_type.value,
            "priority_filter": event.priority_filter,
            "custom_filters": event.custom_filters,
            "is_active": event.is_active,
            "created_at": event.created_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{group_id}/events/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove event subscription",
    description="Unsubscribe group from a notification event type",
)
async def remove_event_subscription(
    group_id: UUID,
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(require_super_admin()),
):
    """Remove event subscription from group"""
    service = NotificationGroupService(db)

    success = await service.remove_event_subscription(event_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event subscription not found"
        )


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================


@router.post(
    "/initialize-defaults",
    summary="Initialize default groups",
    description="Create default notification groups if they don't exist",
)
async def initialize_defaults(
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(require_super_admin()),
):
    """Initialize default notification groups"""
    service = NotificationGroupService(db)

    groups = await service.initialize_default_groups(created_by=UUID(current_user["id"]))

    return {"success": True, "created_count": len(groups), "groups": [g.name for g in groups]}


@router.get(
    "/event-types",
    summary="List available event types",
    description="Get list of all notification event types",
)
async def list_event_types():
    """List all available notification event types"""
    return {
        "event_types": [
            {
                "value": e.value,
                "description": {
                    "new_booking": "New booking created",
                    "booking_edit": "Booking updated",
                    "booking_cancellation": "Booking cancelled",
                    "payment_received": "Payment confirmed",
                    "review_received": "Customer review submitted",
                    "complaint_received": "Customer complaint submitted",
                    "all": "All event types",
                }[e.value],
            }
            for e in NotificationEventType
        ]
    }
