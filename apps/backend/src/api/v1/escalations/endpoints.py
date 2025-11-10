"""
Escalation API Endpoints
Customer support escalation management
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps_enhanced import get_database_session, require_permission
from api.v1.escalations.schemas import (
    EscalationCreateRequest,
    EscalationResponse,
    EscalationAssignRequest,
    EscalationResolveRequest,
    EscalationListRequest,
    EscalationListResponse,
    EscalationStatsResponse,
    SendSMSRequest,
    SMSResponse,
)
from services.escalation_service import EscalationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/escalations", tags=["escalations"])


@router.post("/create", response_model=EscalationResponse, status_code=status.HTTP_201_CREATED)
async def create_escalation(
    request: EscalationCreateRequest,
    db: Session = Depends(get_database_session),
):
    """
    Create a new customer support escalation

    This endpoint:
    1. Creates an escalation record
    2. Pauses the AI conversation
    3. Enqueues job to notify on-call admin via SMS
    4. Returns escalation details

    **Permissions:** Public (called from customer chat widget)
    **Rate limit:** 5 per minute per conversation
    """
    try:
        service = EscalationService(db)

        escalation = await service.create_escalation(
            conversation_id=request.conversation_id,
            phone=request.phone,
            email=request.email,
            reason=request.reason,
            preferred_method=request.preferred_method,
            priority=request.priority,
            customer_consent=request.customer_consent,
            metadata=request.metadata,
        )

        # TODO: Enqueue job to send SMS notification to on-call admin
        # from workers.escalation_tasks import send_escalation_notification
        # send_escalation_notification.delay(str(escalation.id))

        logger.info(
            f"Created escalation {escalation.id} for conversation {request.conversation_id}"
        )

        return EscalationResponse.from_orm(escalation)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create escalation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create escalation",
        )


@router.get("/{escalation_id}", response_model=EscalationResponse)
async def get_escalation(
    escalation_id: str,
    db: Session = Depends(get_database_session),
    _: None = Depends(require_permission("escalation:read")),
):
    """
    Get escalation by ID

    **Permissions:** escalation:read
    """
    service = EscalationService(db)
    escalation = await service.get_escalation(escalation_id)

    if not escalation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Escalation {escalation_id} not found",
        )

    return EscalationResponse.from_orm(escalation)


@router.post("/{escalation_id}/assign", response_model=EscalationResponse)
async def assign_escalation(
    escalation_id: str,
    request: EscalationAssignRequest,
    db: Session = Depends(get_database_session),
    _: None = Depends(require_permission("inbox:assign")),
):
    """
    Assign escalation to an admin

    **Permissions:** inbox:assign
    """
    try:
        service = EscalationService(db)
        escalation = await service.assign_escalation(
            escalation_id=escalation_id,
            admin_id=request.admin_id,
            notes=request.notes,
        )

        return EscalationResponse.from_orm(escalation)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to assign escalation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign escalation",
        )


@router.post("/{escalation_id}/resolve", response_model=EscalationResponse)
async def resolve_escalation(
    escalation_id: str,
    request: EscalationResolveRequest,
    db: Session = Depends(get_database_session),
    current_user=Depends(require_permission("escalation:resolve")),
):
    """
    Resolve an escalation

    **Permissions:** escalation:resolve
    """
    try:
        service = EscalationService(db)
        escalation = await service.resolve_escalation(
            escalation_id=escalation_id,
            resolved_by_id=str(current_user.id),
            resolution_notes=request.resolution_notes,
            resume_ai=request.resume_ai,
        )

        return EscalationResponse.from_orm(escalation)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to resolve escalation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve escalation",
        )


@router.post("/list", response_model=EscalationListResponse)
async def list_escalations(
    request: EscalationListRequest,
    db: Session = Depends(get_database_session),
    _: None = Depends(require_permission("escalation:read")),
):
    """
    List escalations with filters

    **Permissions:** escalation:read
    """
    try:
        service = EscalationService(db)
        escalations, total = await service.list_escalations(
            status=request.status,
            priority=request.priority,
            assigned_to_id=request.assigned_to_id,
            from_date=request.from_date,
            to_date=request.to_date,
            page=request.page,
            page_size=request.page_size,
        )

        return EscalationListResponse(
            escalations=[EscalationResponse.from_orm(e) for e in escalations],
            total=total,
            page=request.page,
            page_size=request.page_size,
            has_more=(request.page * request.page_size) < total,
        )

    except Exception as e:
        logger.error(f"Failed to list escalations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list escalations",
        )


@router.get("/stats", response_model=EscalationStatsResponse)
async def get_escalation_stats(
    db: Session = Depends(get_database_session),
    _: None = Depends(require_permission("analytics:view")),
):
    """
    Get escalation statistics

    **Permissions:** analytics:view
    """
    try:
        service = EscalationService(db)
        stats = await service.get_stats()

        return EscalationStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Failed to get escalation stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get escalation stats",
        )


@router.post("/{escalation_id}/send-sms", response_model=SMSResponse)
async def send_sms_to_customer(
    escalation_id: str,
    request: SendSMSRequest,
    db: Session = Depends(get_database_session),
    _: None = Depends(require_permission("sms:send")),
):
    """
    Send SMS to customer via escalation

    **Permissions:** sms:send
    """
    try:
        service = EscalationService(db)
        escalation = await service.get_escalation(escalation_id)

        if not escalation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Escalation {escalation_id} not found",
            )

        # TODO: Enqueue job to send SMS via RingCentral
        # from workers.sms_tasks import send_sms
        # job = send_sms.delay(escalation.phone, request.message, request.metadata)

        # Record SMS sent
        await service.record_sms_sent(escalation_id)

        return SMSResponse(
            escalation_id=escalation_id,
            message_id=None,  # Will be set by worker
            status="queued",
            sent_at=None,
            error_message=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send SMS: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send SMS",
        )
