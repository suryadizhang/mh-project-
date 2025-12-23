"""
FAQ Settings API Endpoints
Allows admins to update FAQ data that AI uses in responses
"""

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.faq_settings import FAQSettings
from ...services.faq_service import FAQService
from ...services.faq_health_check import FAQHealthCheck

router = APIRouter(prefix="/api/faq-settings", tags=["FAQ Settings"])


# Request/Response Schemas
class FAQSettingsUpdate(BaseModel):
    """Schema for updating FAQ settings"""

    service_area: str = Field(..., min_length=5, max_length=500)
    service_area_details: str | None = None

    deposit_amount: int = Field(..., ge=0, le=1000, description="Deposit amount in dollars")
    deposit_policy: str = Field(..., min_length=10, max_length=1000)

    pricing_info: dict = Field(..., description="Pricing structure as JSON")
    cancellation_policy: str = Field(..., min_length=10, max_length=1000)

    event_duration_default: int = Field(default=2, ge=1, le=12)
    advance_booking_required: str = Field(..., min_length=10, max_length=500)

    business_phone: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")
    business_email: str | None = None
    booking_page_url: str = Field(..., pattern=r"^https?://")

    faq_content: dict | None = None

    updated_by: str | None = Field(None, description="Admin user making the update")


class FAQSettingsResponse(BaseModel):
    """Response schema with FAQ settings"""

    id: str
    service_area: str
    service_area_details: str | None
    deposit_amount: int
    deposit_policy: str
    pricing_info: dict
    cancellation_policy: str
    event_duration_default: int
    advance_booking_required: str
    business_phone: str
    business_email: str | None
    booking_page_url: str
    faq_content: dict | None
    is_active: bool
    updated_at: datetime
    updated_by: str | None

    class Config:
        from_attributes = True


# API Endpoints
@router.get("/current", response_model=FAQSettingsResponse)
async def get_current_faq_settings(db: AsyncSession = Depends(get_db)):
    """
    Get currently active FAQ settings

    This is the data AI is using right now for responses
    """
    faq_settings = await FAQService.get_active_faq_settings(db)

    if not faq_settings:
        raise HTTPException(
            status_code=404, detail="No active FAQ settings found. Please create initial settings."
        )

    return faq_settings


@router.post("/", response_model=FAQSettingsResponse, status_code=201)
async def create_faq_settings(settings_data: FAQSettingsUpdate, db: AsyncSession = Depends(get_db)):
    """
    Create new FAQ settings

    Automatically deactivates any existing active settings
    AI will immediately start using these new settings
    """

    # Deactivate all existing settings
    result = await db.execute(select(FAQSettings).where(FAQSettings.is_active == True))
    existing_settings = result.scalars().all()

    for setting in existing_settings:
        setting.is_active = False

    # Create new settings
    new_settings = FAQSettings(
        id=str(uuid4()),
        service_area=settings_data.service_area,
        service_area_details=settings_data.service_area_details,
        deposit_amount=settings_data.deposit_amount,
        deposit_policy=settings_data.deposit_policy,
        pricing_info=settings_data.pricing_info,
        cancellation_policy=settings_data.cancellation_policy,
        event_duration_default=settings_data.event_duration_default,
        advance_booking_required=settings_data.advance_booking_required,
        business_phone=settings_data.business_phone,
        business_email=settings_data.business_email,
        booking_page_url=settings_data.booking_page_url,
        faq_content=settings_data.faq_content,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        updated_by=settings_data.updated_by,
    )

    db.add(new_settings)
    await db.commit()
    await db.refresh(new_settings)

    return new_settings


@router.put("/current", response_model=FAQSettingsResponse)
async def update_current_faq_settings(
    settings_data: FAQSettingsUpdate, db: AsyncSession = Depends(get_db)
):
    """
    Update current active FAQ settings

    Changes take effect immediately - AI will use updated data
    in next response (typically < 1 second)
    """

    # Get current active settings
    faq_settings = await FAQService.get_active_faq_settings(db)

    if not faq_settings:
        raise HTTPException(
            status_code=404,
            detail="No active FAQ settings found. Use POST to create initial settings.",
        )

    # Update fields
    faq_settings.service_area = settings_data.service_area
    faq_settings.service_area_details = settings_data.service_area_details
    faq_settings.deposit_amount = settings_data.deposit_amount
    faq_settings.deposit_policy = settings_data.deposit_policy
    faq_settings.pricing_info = settings_data.pricing_info
    faq_settings.cancellation_policy = settings_data.cancellation_policy
    faq_settings.event_duration_default = settings_data.event_duration_default
    faq_settings.advance_booking_required = settings_data.advance_booking_required
    faq_settings.business_phone = settings_data.business_phone
    faq_settings.business_email = settings_data.business_email
    faq_settings.booking_page_url = settings_data.booking_page_url
    faq_settings.faq_content = settings_data.faq_content
    faq_settings.updated_at = datetime.utcnow()
    faq_settings.updated_by = settings_data.updated_by

    await db.commit()
    await db.refresh(faq_settings)

    return faq_settings


@router.get("/preview-prompt")
async def preview_ai_prompt(db: AsyncSession = Depends(get_db)):
    """
    Preview what the AI system prompt looks like with current FAQ data

    Useful for admins to see exactly what information AI has access to
    """
    faq_data = await FAQService.get_faq_for_ai_prompt(db)
    formatted_prompt = FAQService.format_faq_for_prompt(faq_data)

    return {
        "raw_data": faq_data,
        "formatted_prompt": formatted_prompt,
        "last_updated": faq_data.get("last_updated"),
        "note": "This is what AI sees in every system prompt",
    }


@router.post("/calculate-quote")
async def calculate_quote_preview(
    party_size: int = Field(..., ge=1, le=500),
    menu_type: str = Field(..., pattern="^(classic|premium)$"),
    db: AsyncSession = Depends(get_db),
):
    """
    Calculate booking quote using current pricing

    Shows what AI would tell a customer for this party size/menu
    """
    try:
        quote = await FAQService.calculate_booking_quote(
            party_size=party_size, menu_type=menu_type, db=db
        )
        return quote
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history")
async def get_faq_settings_history(limit: int = 10, db: AsyncSession = Depends(get_db)):
    """
    Get history of FAQ settings changes

    Shows who changed what and when
    """
    result = await db.execute(
        select(FAQSettings).order_by(FAQSettings.updated_at.desc()).limit(limit)
    )
    history = result.scalars().all()

    return [
        {
            "id": str(setting.id),
            "service_area": setting.service_area,
            "deposit_amount": setting.deposit_amount,
            "is_active": setting.is_active,
            "updated_at": setting.updated_at,
            "updated_by": setting.updated_by or "Unknown",
        }
        for setting in history
    ]


# ========== HEALTH CHECK & ERROR DETECTION ==========


@router.get("/health-check")
async def faq_health_check(db: AsyncSession = Depends(get_db)):
    """
    🩺 **FAQ Health Check & Error Detection**

    Detects if FAQ updates are working correctly:
    - ✅ Checks if data is fresh (updated recently)
    - ✅ Validates pricing matches expected values
    - ⚠️ Alerts if FAQ hasn't been updated in 7+ days
    - 🚨 Catches pricing errors that could cause incorrect quotes

    **Use this after updating FAQ to verify changes took effect!**
    """
    health_report = await FAQHealthCheck.run_full_health_check(db)

    return health_report


@router.get("/freshness-check")
async def check_faq_freshness(db: AsyncSession = Depends(get_db)):
    """
    Check if FAQ data is fresh and being used by AI

    Returns:
        - last_update: When FAQ was last modified
        - age_minutes: How old the data is
        - is_stale: True if not updated in 7+ days
    """
    freshness = await FAQHealthCheck.check_faq_freshness(db)
    return freshness


@router.get("/validate-pricing")
async def validate_pricing(db: AsyncSession = Depends(get_db)):
    """
    Validate that pricing in FAQ matches expected business rules

    Checks:
    - Deposit is $100
    - Adult price is $55
    - Child price is $30
    - Party minimum is $550
    - Travel fee is configured

    **Run this after updating pricing to catch errors!**
    """
    validation = await FAQHealthCheck.validate_pricing_consistency(db)
    return validation


@router.post("/compare-with-source")
async def compare_with_source(source_data: dict, db: AsyncSession = Depends(get_db)):
    """
    Compare FAQ database with source of truth (e.g., faqsData.ts)

    Request body example:
    ```json
    {
        "deposit_amount": 100,
        "adult_price": 55.0,
        "child_price": 30.0,
        "service_area": "Bay Area, Sacramento..."
    }
    ```

    Returns list of differences (if any)
    """
    comparison = await FAQHealthCheck.compare_faq_with_source(db, source_data)
    return comparison


@router.get("/scrape-website-data")
async def scrape_website_data():
    """
    🌐 **Scrape Current Website Data**

    Fetches pricing, service area, and policy data from the actual website.
    This endpoint reads from faqsData.ts to get the source of truth.

    Returns:
    - service_area: Current service coverage
    - pricing: Adult/child prices, party minimum, premium upgrades
    - deposit: Deposit amount and policy
    - cancellation: Cancellation policy
    - contact: Phone, email, booking URL

    **Note**: This simulates website scraping. In production, you could:
    1. Read from a JSON API on the website
    2. Parse HTML from public pages
    3. Query a CMS API
    """
    from datetime import datetime

    # For now, return hardcoded data from faqsData.ts
    # TODO: Implement actual website scraping or API call

    return {
        "success": True,
        "timestamp": datetime.utcnow().isoformat(),
        "website_data": {
            "service_area": "Bay Area, Northern California",
            "service_area_details": "We serve San Francisco, Oakland, San Jose, Sacramento, and surrounding communities. First 30 miles free, then $2/mile.",
            "pricing": {
                "adult_13_plus": 55.0,
                "child_6_to_12": 30.0,
                "child_under_5": 0.0,
                "party_minimum": 550.0,
                "premium_upgrades": {
                    "salmon": 5.0,
                    "scallops": 5.0,
                    "filet_mignon": 5.0,
                    "lobster_tail": 15.0,
                },
                "add_ons": {
                    "yakisoba_noodles": 5.0,
                    "extra_fried_rice": 5.0,
                    "extra_vegetables": 5.0,
                    "edamame": 5.0,
                    "gyoza": 10.0,
                    "extra_protein": 10.0,
                },
            },
            "deposit": {
                "amount": 100,
                "policy": "$100 deposit required to secure your booking. The deposit is fully deducted from your total balance, which is paid on the event day with your chef or online. Refundable if canceled 7+ days before event.",
            },
            "cancellation_policy": "Full refund if canceled 7+ days before event. $100 deposit is non-refundable within 7 days of event. One free reschedule within 48 hours of booking; additional reschedules cost $100.",
            "contact": {
                "phone": "+1-916-740-8768",
                "email": None,
                "booking_url": "https://myhibachichef.com/booking",
            },
            "travel_fee": {
                "first_30_miles": "FREE",
                "after_30_miles": 2.0,
            },
            "faq_highlights": {
                "equipment_provided": "Yes! We bring all cooking equipment, propane, utensils, and serving supplies.",
                "included_in_price": "Chef service, all equipment, cooking, entertainment, and cleanup. Food costs are separate.",
                "advance_booking": "We recommend booking at least 48 hours in advance (2+ weeks for weekend events).",
                "tipping": "Tips are appreciated and paid directly to your chef after the party. We suggest 20-35% of total service cost.",
            },
        },
        "source": "faqsData.ts hardcoded (production: implement web scraper or API)",
    }
