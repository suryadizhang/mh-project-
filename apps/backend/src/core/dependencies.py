"""
Dependency injection providers for FastAPI.

This module provides Depends() functions that FastAPI uses to inject dependencies
into route handlers and services. This enables:
- Testability (easy to mock dependencies)
- Loose coupling (services don't create their own dependencies)
- Centralized configuration (dependencies configured in one place)

Usage in routes:
    @router.post("/leads")
    async def create_lead(
        data: LeadCreate,
        lead_service: LeadService = Depends(get_lead_service)
    ):
        return await lead_service.create_lead_with_consent(data)

Usage in tests:
    app.dependency_overrides[get_lead_service] = lambda: MockLeadService()
"""

from typing import AsyncGenerator, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from db.session import AsyncSessionLocal
from services.lead_service import LeadService
from services.newsletter_service import SubscriberService
from services.event_service import EventService
from services.booking_service import BookingService
from services.webhook_service import MetaWebhookHandler
from repositories.booking_repository import BookingRepository
from core.compliance import ComplianceValidator
from core.cache import CacheService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide database session for the request lifecycle.
    
    Automatically handles session creation, cleanup, and rollback on errors.
    
    Usage:
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
    
    Yields:
        AsyncSession: Database session that will be automatically closed
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_compliance_validator() -> ComplianceValidator:
    """
    Provide ComplianceValidator instance.
    
    Returns:
        ComplianceValidator: Validator for TCPA/CAN-SPAM compliance
    """
    return ComplianceValidator()


async def get_event_service(
    db: AsyncSession = Depends(get_db)
) -> EventService:
    """
    Provide EventService with database dependency injected.
    
    Args:
        db: Database session (automatically injected by FastAPI)
    
    Returns:
        EventService: Service for tracking events across the system
    """
    return EventService(db)


async def get_lead_service(
    db: AsyncSession = Depends(get_db),
    compliance_validator: ComplianceValidator = Depends(get_compliance_validator),
    event_service: EventService = Depends(get_event_service),
) -> LeadService:
    """
    Provide LeadService with all dependencies injected.
    
    Automatically injects:
    - Database session for data access
    - ComplianceValidator for TCPA validation
    - EventService for event tracking
    
    Args:
        db: Database session
        compliance_validator: TCPA/CAN-SPAM validator
        event_service: Event tracking service
    
    Returns:
        LeadService: Fully configured lead service
    
    Example:
        @router.post("/api/v1/leads")
        async def create_lead(
            data: LeadCreate,
            service: LeadService = Depends(get_lead_service)
        ):
            return await service.create_lead_with_consent(data)
    """
    return LeadService(
        db=db,
        compliance_validator=compliance_validator,
        event_service=event_service,
    )


async def get_newsletter_service(
    db: AsyncSession = Depends(get_db),
    compliance_validator: ComplianceValidator = Depends(get_compliance_validator),
    event_service: EventService = Depends(get_event_service),
) -> SubscriberService:
    """
    Provide SubscriberService (NewsletterService) with all dependencies injected.
    
    Automatically injects:
    - Database session for data access
    - ComplianceValidator for CAN-SPAM validation
    - EventService for subscription tracking
    
    Args:
        db: Database session
        compliance_validator: CAN-SPAM validator
        event_service: Event tracking service
    
    Returns:
        SubscriberService: Fully configured newsletter service
    
    Example:
        @router.post("/api/v1/newsletter/subscribe")
        async def subscribe(
            data: SubscribeRequest,
            service: SubscriberService = Depends(get_newsletter_service)
        ):
            return await service.subscribe(data)
    """
    return SubscriberService(
        db=db,
        compliance_validator=compliance_validator,
        event_service=event_service,
    )


async def get_booking_service(
    db: AsyncSession = Depends(get_db),
    lead_service: LeadService = Depends(get_lead_service),
    cache: Optional[CacheService] = None,
) -> BookingService:
    """
    Provide BookingService with all dependencies injected.
    
    Automatically injects:
    - Database session via BookingRepository
    - LeadService for failed booking capture
    - CacheService for performance optimization (optional)
    
    Args:
        db: Database session
        lead_service: Lead service for capturing failed bookings
        cache: Optional cache service
    
    Returns:
        BookingService: Fully configured booking service
    """
    repository = BookingRepository(db)
    return BookingService(
        repository=repository,
        lead_service=lead_service,
        cache=cache,
    )


async def get_meta_webhook_handler(
    db: AsyncSession = Depends(get_db),
    lead_service: LeadService = Depends(get_lead_service),
    event_service: EventService = Depends(get_event_service),
) -> MetaWebhookHandler:
    """
    Provide MetaWebhookHandler with all dependencies injected.
    
    Automatically injects:
    - Database session
    - LeadService for lead capture from social messages
    - EventService for webhook event tracking
    
    Args:
        db: Database session
        lead_service: Service for lead management
        event_service: Event tracking service
    
    Returns:
        MetaWebhookHandler: Fully configured Meta webhook handler
    
    Example:
        @router.post("/webhooks/meta")
        async def process_webhook(
            handler: MetaWebhookHandler = Depends(get_meta_webhook_handler)
        ):
            return await handler.handle_webhook(...)
    """
    return MetaWebhookHandler(
        db=db,
        lead_service=lead_service,
        event_service=event_service,
    )


async def get_referral_service(
    db: AsyncSession = Depends(get_db),
    event_service: EventService = Depends(get_event_service),
    notification_service: Optional[Any] = None,
) -> "ReferralService":
    """
    Provide ReferralService with all dependencies injected.
    
    Automatically injects:
    - Database session for data access
    - EventService for referral tracking
    - NotificationService for sending referral emails (optional)
    
    Args:
        db: Database session
        event_service: Event tracking service
        notification_service: Optional notification service
    
    Returns:
        ReferralService: Fully configured referral service
    
    Example:
        @router.post("/api/v1/referrals")
        async def create_referral(
            data: CreateReferralRequest,
            service: ReferralService = Depends(get_referral_service)
        ):
            return await service.create_referral(...)
    """
    from services.referral_service import ReferralService
    return ReferralService(
        db=db,
        event_service=event_service,
        notification_service=notification_service,
    )


async def get_nurture_campaign_service(
    db: AsyncSession = Depends(get_db),
    event_service: EventService = Depends(get_event_service),
    notification_service: Optional[Any] = None,
) -> "NurtureCampaignService":
    """
    Provide NurtureCampaignService with all dependencies injected.
    
    Automatically injects:
    - Database session for data access
    - EventService for campaign tracking
    - NotificationService for sending campaign messages (optional)
    
    Args:
        db: Database session
        event_service: Event tracking service
        notification_service: Optional notification service
    
    Returns:
        NurtureCampaignService: Fully configured nurture campaign service
    
    Example:
        @router.post("/api/v1/campaigns/enroll")
        async def enroll_lead(
            data: EnrollLeadRequest,
            service: NurtureCampaignService = Depends(get_nurture_campaign_service)
        ):
            return await service.enroll_lead(...)
    """
    from services.nurture_campaign_service import NurtureCampaignService
    return NurtureCampaignService(
        db=db,
        event_service=event_service,
        notification_service=notification_service,
    )
