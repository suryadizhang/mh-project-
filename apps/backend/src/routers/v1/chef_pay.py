"""
Chef Pay System API Router
==========================

API endpoints for chef pay rate management, earnings calculation, and score tracking.

**ACCESS CONTROL:**
- Chefs CANNOT see pay visibility (per user decision)
- Station Managers and Super Admins can view pay data
- Super Admins can modify pay rate classes

**PAY STRUCTURE (Per-Tier Fixed Rates):**
Each tier has its own fixed per-person rates (NOT a base × multiplier system):

- Junior Chef (new_chef): $10/adult, $5/kid, $0/toddler
- Chef:                   $12/adult, $6/kid, $0/toddler
- Senior Chef:            $13/adult, $6.50/kid, $0/toddler
- Station Manager:        $15/adult, $7.50/kid, $0/toddler
- Travel Fee:             100% goes to chef

**Formula:**
Chef Earnings = (adults × tier_adult_rate) + (kids × tier_kid_rate) + travel_fee

**SSoT Variables (chef_pay category):**
- junior_adult_cents, junior_kid_cents, junior_toddler_cents
- chef_adult_cents, chef_kid_cents, chef_toddler_cents
- senior_adult_cents, senior_kid_cents, senior_toddler_cents
- manager_adult_cents, manager_kid_cents, manager_toddler_cents
- travel_pct (100 = 100%)

Related:
- services/chef_pay_service.py: Business logic
- schemas/chef_pay.py: Request/response models
- 021_fix_chef_pay_tiers.sql: Per-tier rates migration
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from db.models.ops import Chef, ChefEarnings, PayRateClass
from schemas.chef_pay import (
    CalculateEarningsRequest,
    CalculateEarningsResponse,
    ChefEarningsListResponse,
    ChefPayConfigResponse,
    CreateEarningsRecordRequest,
    EarningsRecordResponse,
    EarningsSummaryRequest,
    EarningsSummaryResponse,
    PayRateClassUpdatedResponse,
    RecordScoreRequest,
    ScoreRecordedResponse,
    UpdatePayRateClassRequest,
)
from services.chef_pay_service import (
    calculate_chef_earnings,
    create_earnings_record,
    get_chef_earnings_summary,
    get_chef_pay_config,
    record_chef_score,
    update_chef_pay_rate_class,
)
from utils.auth import UserRole, require_role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chef-pay", tags=["Chef Pay"])


# ============================================================================
# Access Control Dependencies
# ============================================================================


async def require_station_manager_or_super_admin(
    current_user: dict = Depends(
        require_role([UserRole.STATION_MANAGER, UserRole.SUPER_ADMIN])
    ),
) -> dict:
    """
    Dependency that requires Station Manager or Super Admin role.

    Station Managers can view pay data and calculate earnings.
    Super Admins have full access including modifying pay rate classes.
    """
    return current_user


async def require_super_admin(
    current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN])),
) -> dict:
    """
    Dependency that requires Super Admin role.

    Only Super Admins can modify pay rate classes.
    """
    return current_user


# ============================================================================
# Configuration Endpoints
# ============================================================================


@router.get(
    "/config",
    response_model=ChefPayConfigResponse,
    summary="Get Chef Pay Configuration",
    description="Get current chef pay configuration from SSoT (dynamic_variables)",
)
async def get_pay_config(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_station_manager_or_super_admin),
):
    """
    Get current chef pay configuration values from the database.

    Returns SSoT values for per-tier fixed rates:
    - Junior Chef (new_chef): $10/adult, $5/kid
    - Chef: $12/adult, $6/kid
    - Senior Chef: $13/adult, $6.50/kid
    - Station Manager: $15/adult, $7.50/kid
    - Travel fee percentage

    Access: Station Manager, Super Admin
    """
    config = await get_chef_pay_config(db)

    return ChefPayConfigResponse(
        # Junior Chef rates
        junior_adult_cents=config.junior_adult_cents,
        junior_kid_cents=config.junior_kid_cents,
        junior_toddler_cents=config.junior_toddler_cents,
        # Chef rates
        chef_adult_cents=config.chef_adult_cents,
        chef_kid_cents=config.chef_kid_cents,
        chef_toddler_cents=config.chef_toddler_cents,
        # Senior Chef rates
        senior_adult_cents=config.senior_adult_cents,
        senior_kid_cents=config.senior_kid_cents,
        senior_toddler_cents=config.senior_toddler_cents,
        # Station Manager rates
        manager_adult_cents=config.manager_adult_cents,
        manager_kid_cents=config.manager_kid_cents,
        manager_toddler_cents=config.manager_toddler_cents,
        # Travel
        travel_pct=config.travel_pct,
        source=config.source,
    )


# ============================================================================
# Earnings Calculation Endpoints
# ============================================================================


@router.post(
    "/calculate",
    response_model=CalculateEarningsResponse,
    summary="Calculate Chef Earnings for Booking",
    description="Calculate expected chef earnings for a specific booking",
)
async def calculate_earnings(
    request: CalculateEarningsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_station_manager_or_super_admin),
):
    """
    Calculate chef earnings for a specific booking.

    Uses SSoT pay rates and the chef's pay rate class multiplier.

    Formula:
    - Base = (adults × adult_rate) + (kids × kid_rate) + (toddlers × toddler_rate) + travel_fee
    - Final = Base × pay_rate_multiplier

    Access: Station Manager, Super Admin
    """
    result = await calculate_chef_earnings(
        db=db,
        booking_id=request.booking_id,
        chef_id=request.chef_id,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking or chef not found",
        )

    return result


@router.get(
    "/chefs/{chef_id}/earnings",
    response_model=EarningsSummaryResponse,
    summary="Get Chef Earnings Summary",
    description="Get earnings summary for a chef within a date range",
)
async def get_earnings_summary(
    chef_id: UUID,
    start_date: Optional[str] = Query(
        None, description="Start date (YYYY-MM-DD). Defaults to 30 days ago."
    ),
    end_date: Optional[str] = Query(
        None, description="End date (YYYY-MM-DD). Defaults to today."
    ),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_station_manager_or_super_admin),
):
    """
    Get earnings summary for a specific chef.

    Aggregates earnings within the specified date range, including:
    - Total earnings (pending, approved, paid)
    - Breakdown by status
    - Event count and averages

    Access: Station Manager, Super Admin
    """
    from datetime import date, datetime, timedelta

    # Parse dates or use defaults
    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
    else:
        start = date.today() - timedelta(days=30)

    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    else:
        end = date.today()

    summary = await get_chef_earnings_summary(
        db=db,
        chef_id=chef_id,
        start_date=start,
        end_date=end,
    )

    if summary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chef not found",
        )

    return EarningsSummaryResponse(
        chef_id=summary.chef_id,
        chef_name=summary.chef_name,
        period_start=summary.period_start,
        period_end=summary.period_end,
        total_events=summary.total_events,
        total_earnings_cents=summary.total_earnings_cents,
        pending_cents=summary.pending_cents,
        approved_cents=summary.approved_cents,
        paid_cents=summary.paid_cents,
        average_per_event_cents=summary.average_per_event_cents,
    )


@router.post(
    "/earnings",
    response_model=EarningsRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Earnings Record",
    description="Create an earnings record for a completed booking",
)
async def create_earnings(
    request: CreateEarningsRecordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_station_manager_or_super_admin),
):
    """
    Create an earnings record for a completed booking.

    This records the calculated earnings after an event is completed.
    The earnings are calculated using SSoT rates at the time of creation.

    Access: Station Manager, Super Admin
    """
    result = await create_earnings_record(
        db=db,
        booking_id=request.booking_id,
        chef_id=request.chef_id,
        status=request.status or "pending",
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking or chef not found",
        )

    return result


@router.get(
    "/earnings",
    response_model=ChefEarningsListResponse,
    summary="List All Earnings Records",
    description="List earnings records with optional filters",
)
async def list_earnings(
    chef_id: Optional[UUID] = Query(None, description="Filter by chef ID"),
    status_filter: Optional[str] = Query(
        None, alias="status", description="Filter by status (pending, approved, paid)"
    ),
    limit: int = Query(50, ge=1, le=100, description="Maximum records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_station_manager_or_super_admin),
):
    """
    List earnings records with optional filtering.

    Supports filtering by chef and status.
    Results are paginated.

    Access: Station Manager, Super Admin
    """
    from db.models.ops import EarningsStatus

    query = select(ChefEarnings).order_by(ChefEarnings.event_date.desc())

    if chef_id:
        query = query.where(ChefEarnings.chef_id == chef_id)

    if status_filter:
        try:
            status_enum = EarningsStatus(status_filter.lower())
            query = query.where(ChefEarnings.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}. Must be pending, approved, or paid.",
            )

    # Get total count
    from sqlalchemy import func

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    records = result.scalars().all()

    items = []
    for record in records:
        # Get chef name
        chef_result = await db.execute(select(Chef).where(Chef.id == record.chef_id))
        chef = chef_result.scalar_one_or_none()
        chef_name = f"{chef.first_name} {chef.last_name}" if chef else "Unknown"

        items.append(
            {
                "earnings_id": record.id,
                "booking_id": record.booking_id,
                "chef_id": record.chef_id,
                "chef_name": chef_name,
                "event_date": record.event_date,
                "base_earnings_cents": record.base_earnings_cents,
                "final_earnings_cents": record.final_earnings_cents,
                "pay_rate_class": record.pay_rate_class.value
                if record.pay_rate_class
                else None,
                "status": record.status.value if record.status else "pending",
                "created_at": record.created_at,
            }
        )

    return ChefEarningsListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


# ============================================================================
# Score Tracking Endpoints
# ============================================================================


@router.post(
    "/scores",
    response_model=ScoreRecordedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record Chef Score",
    description="Record a performance score for a chef after an event",
)
async def record_score(
    request: RecordScoreRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_station_manager_or_super_admin),
):
    """
    Record a performance score for a chef.

    Scores are used for:
    - Performance tracking
    - Seniority level determination
    - Pay rate class advancement decisions

    Score scale: 1-5 (1=poor, 5=excellent)

    Access: Station Manager, Super Admin
    """
    result = await record_chef_score(
        db=db,
        chef_id=request.chef_id,
        booking_id=request.booking_id,
        score=request.score,
        rater_type=request.rater_type,
        rater_id=current_user.get("user_id"),
        comment=request.comment,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chef or booking not found",
        )

    return result


# ============================================================================
# Pay Rate Class Management Endpoints
# ============================================================================


@router.patch(
    "/chefs/{chef_id}/pay-rate-class",
    response_model=PayRateClassUpdatedResponse,
    summary="Update Chef Pay Rate Class",
    description="Update a chef's pay rate class (affects earnings multiplier)",
)
async def update_pay_rate(
    chef_id: UUID,
    request: UpdatePayRateClassRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_super_admin),
):
    """
    Update a chef's pay rate class.

    Pay rate classes affect the earnings multiplier:
    - NEW_CHEF: 80% of base earnings
    - CHEF: 100% of base earnings
    - SENIOR_CHEF: 115% of base earnings

    Access: Super Admin only
    """
    result = await update_chef_pay_rate_class(
        db=db,
        chef_id=chef_id,
        new_pay_rate_class=request.pay_rate_class,
        updated_by=current_user.get("user_id"),
        reason=request.reason,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chef not found",
        )

    return result
