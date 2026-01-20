"""
Stripe Payments List Endpoint
=============================

Endpoints for listing and retrieving payments.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.database import get_db
from db.models.stripe import PaymentStatus, StripePayment
from utils.auth import Permission, get_current_user, require_permissions

from .schemas import PaymentListResponse
from .utils import format_payment_for_response

logger = logging.getLogger(__name__)
router = APIRouter(tags=["stripe-payments"])


@router.get("/payments", response_model=PaymentListResponse)
async def get_payments(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status: Optional[PaymentStatus] = None,
    booking_id: Optional[UUID] = None,
    limit: int = Query(default=20, le=100, ge=1),
    cursor: Optional[str] = None,
):
    """
    List payments for the current user.

    Supports cursor-based pagination and filtering.
    """
    try:
        # Build base query - filter by user's payments
        query = select(StripePayment).where(StripePayment.user_id == current_user.id)

        # Apply filters
        if status:
            query = query.where(StripePayment.status == status)
        if booking_id:
            query = query.where(StripePayment.booking_id == booking_id)

        # Apply cursor pagination
        if cursor:
            try:
                from datetime import datetime

                cursor_date = datetime.fromisoformat(cursor)
                query = query.where(StripePayment.created_at < cursor_date)
            except ValueError:
                logger.warning(f"Invalid cursor format: {cursor}")

        # Order and limit
        query = query.order_by(StripePayment.created_at.desc()).limit(limit + 1)

        # Execute query
        result = await db.execute(query)
        payments = result.scalars().all()

        # Determine if there are more results
        has_more = len(payments) > limit
        if has_more:
            payments = payments[:limit]

        # Build next cursor
        next_cursor = None
        if has_more and payments:
            next_cursor = payments[-1].created_at.isoformat()

        # Format response
        payment_list = [
            format_payment_for_response(p, include_sensitive=False) for p in payments
        ]

        return PaymentListResponse(
            payments=payment_list,
            total=len(payment_list),
            has_more=has_more,
            next_cursor=next_cursor,
        )

    except Exception as e:
        logger.exception(f"Error fetching payments: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch payments")


@router.get("/payments/{payment_id}")
async def get_payment(
    payment_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get details of a specific payment.
    """
    try:
        payment = await db.get(Payment, payment_id)

        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")

        # Check ownership
        if payment.user_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="Payment does not belong to this user"
            )

        return format_payment_for_response(payment, include_sensitive=True)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error fetching payment: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch payment")


@router.get("/admin/payments")
async def admin_list_payments(
    current_user=Depends(require_permissions(Permission.MANAGE_PAYMENTS)),
    db: AsyncSession = Depends(get_db),
    user_id: Optional[UUID] = None,
    status: Optional[PaymentStatus] = None,
    booking_id: Optional[UUID] = None,
    limit: int = Query(default=50, le=200, ge=1),
    offset: int = Query(default=0, ge=0),
):
    """
    Admin: List all payments with optional filters.
    """
    try:
        # Build base query
        query = select(StripePayment)
        count_query = select(func.count(StripePayment.id))

        # Apply filters
        filters = []
        if user_id:
            filters.append(StripePayment.user_id == user_id)
        if status:
            filters.append(StripePayment.status == status)
        if booking_id:
            filters.append(StripePayment.booking_id == booking_id)

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and ordering
        query = (
            query.order_by(StripePayment.created_at.desc()).offset(offset).limit(limit)
        )

        # Execute
        result = await db.execute(query)
        payments = result.scalars().all()

        return {
            "payments": [
                format_payment_for_response(p, include_sensitive=True) for p in payments
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(payments) < total,
        }

    except Exception as e:
        logger.exception(f"Error in admin list payments: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch payments")
