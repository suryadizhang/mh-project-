"""
Agreements Service Package
==========================

Handles legal agreements, liability waivers, allergen disclosures,
and signing workflows for My Hibachi bookings.

Components:
- agreement_service.py: Core CRUD operations for agreements
- signing_service.py: Signature capture and verification
- pdf_service.py: PDF generation for signed agreements
- slot_hold_service.py: 2-hour slot holds during signing

Usage:
    from services.agreements import AgreementService, SigningService

    agreement_service = AgreementService(db)
    await agreement_service.create_signed_agreement(
        booking_id=booking.id,
        agreement_type='liability_waiver',
        signature_data=signature_bytes,
        signer_info={...}
    )

Related Tables (core schema):
- agreement_templates: Versioned waiver text templates
- signed_agreements: Immutable signed agreement records
- allergen_disclosures: Per-booking allergen info
- slot_holds: 2-hour holds during signing process

See: database/migrations/008_legal_agreements_system.sql
See: 20-SINGLE_SOURCE_OF_TRUTH.instructions.md for SSoT architecture
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from .agreement_service import AgreementService
from .signing_service import SigningService
from .slot_hold_service import SlotHoldService


# FastAPI Dependency Injection Factories
# These use Depends(get_db) to automatically inject the database session
# Pattern from: routers/v1/stripe.py


async def get_agreement_service(
    db: AsyncSession = Depends(get_db),
) -> AgreementService:
    """
    Factory for AgreementService with auto-injected database session.

    Usage in router:
        @router.get("/")
        async def list_agreements(
            service: AgreementService = Depends(get_agreement_service)
        ):
            ...
    """
    return AgreementService(db)


async def get_signing_service(
    db: AsyncSession = Depends(get_db),
) -> SigningService:
    """
    Factory for SigningService with auto-injected database session.

    Usage in router:
        @router.post("/sign")
        async def sign_agreement(
            service: SigningService = Depends(get_signing_service)
        ):
            ...
    """
    return SigningService(db)


async def get_slot_hold_service(
    db: AsyncSession = Depends(get_db),
) -> SlotHoldService:
    """
    Factory for SlotHoldService with auto-injected database session.

    Usage in router:
        @router.post("/holds")
        async def create_hold(
            service: SlotHoldService = Depends(get_slot_hold_service)
        ):
            ...
    """
    return SlotHoldService(db)


__all__ = [
    # Service classes
    "AgreementService",
    "SigningService",
    "SlotHoldService",
    # Dependency factories
    "get_agreement_service",
    "get_signing_service",
    "get_slot_hold_service",
]
