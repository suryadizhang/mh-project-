"""
Stripe Invoices Endpoint
========================

Endpoints for listing and retrieving invoices.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from db.models.stripe import Invoice, InvoiceStatus
from utils.auth import Permission, get_current_user, require_permissions

from .schemas import InvoiceListResponse
from .utils import format_invoice_for_response

logger = logging.getLogger(__name__)
router = APIRouter(tags=["stripe-invoices"])


@router.get("/invoices", response_model=InvoiceListResponse)
async def get_invoices(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status: Optional[InvoiceStatus] = None,
    booking_id: Optional[UUID] = None,
    limit: int = Query(default=20, le=100, ge=1),
    cursor: Optional[str] = None,
):
    """
    List invoices for the current user.

    Supports cursor-based pagination and filtering.
    """
    try:
        # Build base query - filter by user's invoices
        query = select(Invoice).where(Invoice.user_id == current_user.id)

        # Apply filters
        if status:
            query = query.where(Invoice.status == status)
        if booking_id:
            query = query.where(Invoice.booking_id == booking_id)

        # Apply cursor pagination
        if cursor:
            try:
                from datetime import datetime

                cursor_date = datetime.fromisoformat(cursor)
                query = query.where(Invoice.created_at < cursor_date)
            except ValueError:
                logger.warning(f"Invalid cursor format: {cursor}")

        # Order and limit
        query = query.order_by(Invoice.created_at.desc()).limit(limit + 1)

        # Execute query
        result = await db.execute(query)
        invoices = result.scalars().all()

        # Determine if there are more results
        has_more = len(invoices) > limit
        if has_more:
            invoices = invoices[:limit]

        # Build next cursor
        next_cursor = None
        if has_more and invoices:
            next_cursor = invoices[-1].created_at.isoformat()

        # Format response
        invoice_list = [format_invoice_for_response(inv) for inv in invoices]

        return InvoiceListResponse(
            invoices=invoice_list,
            total=len(invoice_list),
            has_more=has_more,
            next_cursor=next_cursor,
        )

    except Exception as e:
        logger.exception(f"Error fetching invoices: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch invoices")


@router.get("/invoices/{invoice_id}")
async def get_invoice(
    invoice_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get details of a specific invoice.
    """
    try:
        invoice = await db.get(Invoice, invoice_id)

        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        # Check ownership
        if invoice.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Invoice does not belong to this user")

        return format_invoice_for_response(invoice)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error fetching invoice: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch invoice")


@router.get("/admin/invoices")
async def admin_list_invoices(
    current_user=Depends(require_permissions(Permission.MANAGE_PAYMENTS)),
    db: AsyncSession = Depends(get_db),
    user_id: Optional[UUID] = None,
    status: Optional[InvoiceStatus] = None,
    booking_id: Optional[UUID] = None,
    limit: int = Query(default=50, le=200, ge=1),
    offset: int = Query(default=0, ge=0),
):
    """
    Admin: List all invoices with optional filters.
    """
    try:
        # Build base query
        query = select(Invoice)
        count_query = select(func.count(Invoice.id))

        # Apply filters
        filters = []
        if user_id:
            filters.append(Invoice.user_id == user_id)
        if status:
            filters.append(Invoice.status == status)
        if booking_id:
            filters.append(Invoice.booking_id == booking_id)

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(Invoice.created_at.desc()).offset(offset).limit(limit)

        # Execute
        result = await db.execute(query)
        invoices = result.scalars().all()

        return {
            "invoices": [format_invoice_for_response(inv) for inv in invoices],
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(invoices) < total,
        }

    except Exception as e:
        logger.exception(f"Error in admin list invoices: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch invoices")
