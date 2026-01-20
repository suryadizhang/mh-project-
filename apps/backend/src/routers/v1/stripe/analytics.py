"""
Stripe Analytics Endpoint
=========================

Admin endpoints for payment analytics and reporting.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from db.models.stripe import Invoice, InvoiceStatus, PaymentStatus, StripePayment
from utils.auth import Permission, get_current_user, require_permissions

from .schemas import PaymentAnalyticsResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["stripe-analytics"])


@router.get("/analytics", response_model=PaymentAnalyticsResponse)
async def get_payment_analytics(
    current_user=Depends(require_permissions(Permission.MANAGE_PAYMENTS)),
    db: AsyncSession = Depends(get_db),
    days: int = Query(default=30, ge=1, le=365),
    station_id: Optional[UUID] = None,
):
    """
    Get payment analytics for admin dashboard.

    Returns:
        - Total revenue in period
        - Number of successful payments
        - Average payment amount
        - Payment method breakdown
        - Refund summary
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Base filter for successful payments
        base_filter = and_(
            StripePayment.status == PaymentStatus.SUCCEEDED,
            StripePayment.created_at >= start_date,
            StripePayment.created_at <= end_date,
        )

        # Add station filter if provided
        if station_id:
            # Would need to join through booking to get station
            pass  # TODO: Implement station filtering through booking relationship

        # Total revenue
        revenue_result = await db.execute(
            select(func.sum(StripePayment.amount)).where(base_filter)
        )
        total_revenue = revenue_result.scalar() or Decimal("0")

        # Payment count
        count_result = await db.execute(
            select(func.count(StripePayment.id)).where(base_filter)
        )
        payment_count = count_result.scalar() or 0

        # Average payment
        avg_payment = (
            total_revenue / payment_count if payment_count > 0 else Decimal("0")
        )

        # Payment method breakdown
        method_result = await db.execute(
            select(
                StripePayment.payment_method,
                func.count(StripePayment.id).label("count"),
                func.sum(StripePayment.amount).label("total"),
            )
            .where(base_filter)
            .group_by(StripePayment.payment_method)
        )
        method_breakdown = {
            row.payment_method: {
                "count": row.count,
                "total": float(row.total or 0),
            }
            for row in method_result
        }

        # Refund stats
        refund_filter = and_(
            StripePayment.status == PaymentStatus.REFUNDED,
            StripePayment.created_at >= start_date,
            StripePayment.created_at <= end_date,
        )
        refund_result = await db.execute(
            select(
                func.count(StripePayment.id),
                func.sum(StripePayment.amount),
            ).where(refund_filter)
        )
        refund_row = refund_result.first()
        refund_count = refund_row[0] or 0 if refund_row else 0
        refund_total = refund_row[1] or Decimal("0") if refund_row else Decimal("0")

        # Pending payments
        pending_result = await db.execute(
            select(func.count(StripePayment.id)).where(
                and_(
                    StripePayment.status == PaymentStatus.PENDING,
                    StripePayment.created_at >= start_date,
                )
            )
        )
        pending_count = pending_result.scalar() or 0

        # Failed payments
        failed_result = await db.execute(
            select(func.count(StripePayment.id)).where(
                and_(
                    StripePayment.status == PaymentStatus.FAILED,
                    StripePayment.created_at >= start_date,
                )
            )
        )
        failed_count = failed_result.scalar() or 0

        return PaymentAnalyticsResponse(
            period_days=days,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            total_revenue=float(total_revenue),
            payment_count=payment_count,
            average_payment=float(avg_payment),
            method_breakdown=method_breakdown,
            refund_count=refund_count,
            refund_total=float(refund_total),
            pending_count=pending_count,
            failed_count=failed_count,
            zelle_savings=float(total_revenue * Decimal("0.03")),  # 3% fee savings
        )

    except Exception as e:
        logger.exception(f"Error generating payment analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate analytics")


@router.get("/analytics/daily")
async def get_daily_analytics(
    current_user=Depends(require_permissions(Permission.MANAGE_PAYMENTS)),
    db: AsyncSession = Depends(get_db),
    days: int = Query(default=30, ge=1, le=90),
):
    """
    Get daily payment breakdown for charts.
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Daily aggregation
        result = await db.execute(
            select(
                func.date_trunc("day", StripePayment.created_at).label("day"),
                func.count(StripePayment.id).label("count"),
                func.sum(StripePayment.amount).label("total"),
            )
            .where(
                and_(
                    StripePayment.status == PaymentStatus.SUCCEEDED,
                    StripePayment.created_at >= start_date,
                    StripePayment.created_at <= end_date,
                )
            )
            .group_by(func.date_trunc("day", StripePayment.created_at))
            .order_by(func.date_trunc("day", StripePayment.created_at))
        )

        daily_data = [
            {
                "date": row.day.isoformat() if row.day else None,
                "count": row.count,
                "total": float(row.total or 0),
            }
            for row in result
        ]

        return {
            "period_days": days,
            "daily_breakdown": daily_data,
        }

    except Exception as e:
        logger.exception(f"Error generating daily analytics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to generate daily analytics"
        )
