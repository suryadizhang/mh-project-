"""Enhanced admin dashboard with lead and newsletter analytics.

# =============================================================================
# MODULARIZATION TODO (BATCH 2 - Payment Processing)
# This file is 1,500+ lines and exceeds the 500-line limit.
# Target: Convert to `routers/v1/admin_analytics/` package with:
#   - __init__.py (router combiner)
#   - schemas.py (Pydantic response models)
#   - dashboard.py (main dashboard endpoints)
#   - leads.py (lead analytics)
#   - revenue.py (revenue/payment analytics)
#   - newsletter.py (newsletter/campaign analytics)
#   - trends.py (trend calculations)
# See: .github/instructions/22-QUALITY_CONTROL.instructions.md
# =============================================================================
"""

from datetime import date, datetime, timedelta, timezone
from typing import Any

from core.database import get_db
from db.models.core import Booking, Customer

# Fixed: Use unified lead schema instead of legacy models
from db.models.crm import Lead, LeadQuality, LeadStatus

# TODO: Newsletter/Campaign models need migration to proper schema
# Temporarily creating placeholder classes until newsletter schema is implemented
import enum


class CampaignStatus(str, enum.Enum):
    """Placeholder - needs migration to db.models.newsletter"""

    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"


class CampaignEventType(str, enum.Enum):
    """Placeholder - needs migration to db.models.newsletter"""

    SENT = "sent"
    OPENED = "opened"
    CLICKED = "clicked"


# Placeholder models (will cause runtime errors if used - need proper migration)
class Campaign:
    pass


class CampaignEvent:
    pass


class Subscriber:
    pass


from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

router = APIRouter(prefix="/admin/analytics", tags=["admin", "analytics"])


# Response models
class LeadAnalytics(BaseModel):
    total_leads: int
    new_leads: int
    qualified_leads: int
    converted_leads: int
    conversion_rate: float
    average_score: float
    leads_by_source: dict[str, int]
    leads_by_quality: dict[str, int]
    daily_lead_count: list[dict[str, Any]]


class NewsletterAnalytics(BaseModel):
    total_subscribers: int
    active_subscribers: int
    total_campaigns: int
    campaigns_sent: int
    average_open_rate: float
    average_click_rate: float
    subscriber_growth: list[dict[str, Any]]
    campaign_performance: list[dict[str, Any]]


class SalesAnalytics(BaseModel):
    total_revenue: float
    total_bookings: int
    conversion_value: float
    average_booking_value: float
    revenue_by_month: list[dict[str, Any]]
    lead_to_booking_conversion: float


class DashboardOverview(BaseModel):
    leads: LeadAnalytics
    newsletter: NewsletterAnalytics
    sales: SalesAnalytics
    recent_activity: list[dict[str, Any]]
    alerts: list[dict[str, Any]]


@router.get("/overview", response_model=DashboardOverview)
async def get_dashboard_overview(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: Session = Depends(get_db),
):
    """Get comprehensive dashboard overview."""

    # Default to last 30 days if no dates provided
    if not date_from:
        date_from = datetime.now(timezone.utc).date() - timedelta(days=30)
    if not date_to:
        date_to = datetime.now(timezone.utc).date()

    # Get analytics
    leads_analytics = await _get_lead_analytics(date_from, date_to, db)
    newsletter_analytics = await _get_newsletter_analytics(date_from, date_to, db)
    sales_analytics = await _get_sales_analytics(date_from, date_to, db)
    recent_activity = await _get_recent_activity(db)
    alerts = await _get_alerts(db)

    return DashboardOverview(
        leads=leads_analytics,
        newsletter=newsletter_analytics,
        sales=sales_analytics,
        recent_activity=recent_activity,
        alerts=alerts,
    )


@router.get("/leads", response_model=LeadAnalytics)
async def get_lead_analytics(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: Session = Depends(get_db),
):
    """Get detailed lead analytics."""

    if not date_from:
        date_from = datetime.now(timezone.utc).date() - timedelta(days=30)
    if not date_to:
        date_to = datetime.now(timezone.utc).date()

    return await _get_lead_analytics(date_from, date_to, db)


@router.get("/newsletter", response_model=NewsletterAnalytics)
async def get_newsletter_analytics(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: Session = Depends(get_db),
):
    """Get detailed newsletter analytics."""

    if not date_from:
        date_from = datetime.now(timezone.utc).date() - timedelta(days=30)
    if not date_to:
        date_to = datetime.now(timezone.utc).date()

    return await _get_newsletter_analytics(date_from, date_to, db)


@router.get("/funnel")
async def get_conversion_funnel(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: Session = Depends(get_db),
):
    """Get conversion funnel analytics."""

    if not date_from:
        date_from = datetime.now(timezone.utc).date() - timedelta(days=30)
    if not date_to:
        date_to = datetime.now(timezone.utc).date()

    # Count leads at each stage
    total_leads = (
        db.query(Lead).filter(Lead.created_at >= date_from, Lead.created_at <= date_to).count()
    )

    qualified_leads = (
        db.query(Lead)
        .filter(
            Lead.created_at >= date_from,
            Lead.created_at <= date_to,
            Lead.status.in_([LeadStatus.QUALIFIED, LeadStatus.CONVERTED]),
        )
        .count()
    )

    converted_leads = (
        db.query(Lead)
        .filter(
            Lead.created_at >= date_from,
            Lead.created_at <= date_to,
            Lead.status == LeadStatus.CONVERTED,
        )
        .count()
    )

    # Count actual bookings from converted leads
    bookings_from_leads = (
        db.query(Booking)
        .join(Lead, Lead.customer_id == Booking.customer_id)
        .filter(
            Lead.status == LeadStatus.CONVERTED,
            Booking.created_at >= date_from,
            Booking.created_at <= date_to,
        )
        .count()
    )

    return {
        "funnel_stages": [
            {
                "stage": "Total Leads",
                "count": total_leads,
                "conversion_rate": 100.0,
            },
            {
                "stage": "Qualified",
                "count": qualified_leads,
                "conversion_rate": (
                    (qualified_leads / total_leads * 100) if total_leads > 0 else 0
                ),
            },
            {
                "stage": "Converted",
                "count": converted_leads,
                "conversion_rate": (
                    (converted_leads / total_leads * 100) if total_leads > 0 else 0
                ),
            },
            {
                "stage": "Booked",
                "count": bookings_from_leads,
                "conversion_rate": (
                    (bookings_from_leads / total_leads * 100) if total_leads > 0 else 0
                ),
            },
        ],
        "overall_conversion_rate": (
            (bookings_from_leads / total_leads * 100) if total_leads > 0 else 0
        ),
    }


@router.get("/lead-scoring")
async def get_lead_scoring_analysis(db: Session = Depends(get_db)):
    """Get lead scoring analysis and distribution."""

    # Score distribution
    score_ranges = [
        ("0-20", 0, 20),
        ("21-40", 21, 40),
        ("41-60", 41, 60),
        ("61-80", 61, 80),
        ("81-100", 81, 100),
    ]

    score_distribution = []
    for range_name, min_score, max_score in score_ranges:
        count = db.query(Lead).filter(Lead.score >= min_score, Lead.score <= max_score).count()
        score_distribution.append({"range": range_name, "count": count})

    # Quality distribution
    quality_counts = (
        db.query(Lead.quality, func.count(Lead.id).label("count")).group_by(Lead.quality).all()
    )

    quality_distribution = [
        {"quality": quality.value if quality else "unrated", "count": count}
        for quality, count in quality_counts
    ]

    # Top performing sources by conversion
    source_performance = (
        db.query(
            Lead.source,
            func.count(Lead.id).label("total_leads"),
            func.sum(func.case([(Lead.status == LeadStatus.CONVERTED, 1)], else_=0)).label(
                "converted_leads"
            ),
            func.avg(Lead.score).label("avg_score"),
        )
        .group_by(Lead.source)
        .all()
    )

    source_analysis = []
    for source, total, converted, avg_score in source_performance:
        conversion_rate = (converted / total * 100) if total > 0 else 0
        source_analysis.append(
            {
                "source": source.value,
                "total_leads": total,
                "converted_leads": converted or 0,
                "conversion_rate": conversion_rate,
                "average_score": float(avg_score) if avg_score else 0,
            }
        )

    return {
        "score_distribution": score_distribution,
        "quality_distribution": quality_distribution,
        "source_performance": source_analysis,
    }


@router.get("/engagement-trends")
async def get_engagement_trends(days: int = Query(30, le=365), db: Session = Depends(get_db)):
    """Get engagement trends over time."""

    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Daily lead creation
    daily_leads = (
        db.query(
            func.date(Lead.created_at).label("date"),
            func.count(Lead.id).label("count"),
        )
        .filter(Lead.created_at >= start_date)
        .group_by(func.date(Lead.created_at))
        .order_by("date")
        .all()
    )

    # Daily newsletter signups
    daily_signups = (
        db.query(
            func.date(Subscriber.created_at).label("date"),
            func.count(Subscriber.id).label("count"),
        )
        .filter(Subscriber.created_at >= start_date)
        .group_by(func.date(Subscriber.created_at))
        .order_by("date")
        .all()
    )

    # Campaign performance over time
    campaign_performance = (
        db.query(
            func.date(Campaign.sent_at).label("date"),
            func.count(Campaign.id).label("campaigns_sent"),
            func.avg(
                func.cast(
                    db.query(func.count(CampaignEvent.id))
                    .filter(
                        CampaignEvent.campaign_id == Campaign.id,
                        CampaignEvent.type == CampaignEventType.OPENED,
                    )
                    .scalar_subquery(),
                    func.Float,
                )
                / Campaign.total_recipients
                * 100
            ).label("avg_open_rate"),
        )
        .filter(Campaign.sent_at >= start_date, Campaign.sent_at.isnot(None))
        .group_by(func.date(Campaign.sent_at))
        .order_by("date")
        .all()
    )

    return {
        "daily_leads": [{"date": date.isoformat(), "count": count} for date, count in daily_leads],
        "daily_signups": [
            {"date": date.isoformat(), "count": count} for date, count in daily_signups
        ],
        "campaign_performance": [
            {
                "date": date.isoformat(),
                "campaigns_sent": campaigns_sent,
                "avg_open_rate": float(avg_open_rate) if avg_open_rate else 0,
            }
            for date, campaigns_sent, avg_open_rate in campaign_performance
        ],
    }


# ============================================================================
# NEW ENDPOINTS: Missing Analytics Features
# ============================================================================


@router.get("/revenue-trends")
async def get_revenue_trends(
    days: int = Query(30, le=365),
    interval: str = Query("day", regex="^(day|week|month)$"),
    db: Session = Depends(get_db),
):
    """
    Get revenue trends over time with customizable intervals.

    Returns:
        - Daily/Weekly/Monthly revenue
        - Booking counts
        - Average order value
        - Growth rates
    """
    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Determine date truncation based on interval
    if interval == "day":
        date_trunc = func.date(Booking.created_at)
    elif interval == "week":
        date_trunc = func.date_trunc("week", Booking.created_at)
    else:  # month
        date_trunc = func.date_trunc("month", Booking.created_at)

    # Get revenue trends
    trends = (
        db.query(
            date_trunc.label("period"),
            func.sum(Booking.total_due_cents).label("revenue_cents"),
            func.count(Booking.id).label("booking_count"),
            func.avg(Booking.total_due_cents).label("avg_order_value_cents"),
        )
        .filter(Booking.created_at >= start_date, Booking.status != "cancelled")
        .group_by("period")
        .order_by("period")
        .all()
    )

    # Calculate growth rates
    result = []
    prev_revenue = 0
    for period, revenue_cents, booking_count, avg_order_value_cents in trends:
        revenue = float(revenue_cents or 0) / 100
        growth_rate = 0.0
        if prev_revenue > 0:
            growth_rate = ((revenue - prev_revenue) / prev_revenue) * 100

        result.append(
            {
                "period": (period.isoformat() if hasattr(period, "isoformat") else str(period)),
                "revenue": revenue,
                "booking_count": booking_count,
                "avg_order_value": float(avg_order_value_cents or 0) / 100,
                "growth_rate": growth_rate,
            }
        )
        prev_revenue = revenue

    # Calculate totals and summary
    total_revenue = sum(item["revenue"] for item in result)
    total_bookings = sum(item["booking_count"] for item in result)
    overall_avg_order_value = total_revenue / total_bookings if total_bookings > 0 else 0

    return {
        "trends": result,
        "summary": {
            "total_revenue": total_revenue,
            "total_bookings": total_bookings,
            "average_order_value": overall_avg_order_value,
            "period_count": len(result),
        },
    }


@router.get("/customer-lifetime-value")
async def get_customer_lifetime_value(
    top_n: int = Query(100, le=500), db: Session = Depends(get_db)
):
    """
    Calculate Customer Lifetime Value (CLV) metrics.

    Returns:
        - Average CLV
        - CLV distribution
        - Top customers by value
        - Repeat customer rates
    """

    # Calculate CLV for each customer
    customer_values = (
        db.query(
            Customer.id,
            func.count(Booking.id).label("booking_count"),
            func.sum(Booking.total_due_cents).label("total_spent_cents"),
            func.min(Booking.created_at).label("first_booking"),
            func.max(Booking.created_at).label("last_booking"),
        )
        .join(Booking, Customer.id == Booking.customer_id)
        .filter(Booking.status != "cancelled")
        .group_by(Customer.id)
        .all()
    )

    # Calculate metrics
    total_customers = len(customer_values)
    if total_customers == 0:
        return {
            "average_clv": 0,
            "median_clv": 0,
            "top_customers": [],
            "clv_distribution": [],
            "repeat_customer_rate": 0,
            "total_customers_analyzed": 0,
        }

    clv_list = [float(val.total_spent_cents or 0) / 100 for val in customer_values]
    clv_list.sort(reverse=True)

    avg_clv = sum(clv_list) / len(clv_list)
    median_clv = clv_list[len(clv_list) // 2]

    # Repeat customer rate (2+ bookings)
    repeat_customers = sum(1 for val in customer_values if val.booking_count >= 2)
    repeat_rate = (repeat_customers / total_customers) * 100

    # CLV distribution buckets
    distribution_buckets = [
        ("$0-100", 0, 10000),
        ("$100-250", 10000, 25000),
        ("$250-500", 25000, 50000),
        ("$500-1000", 50000, 100000),
        ("$1000+", 100000, float("inf")),
    ]

    distribution = []
    for label, min_cents, max_cents in distribution_buckets:
        count = sum(
            1 for val in customer_values if min_cents <= (val.total_spent_cents or 0) < max_cents
        )
        distribution.append(
            {
                "range": label,
                "count": count,
                "percentage": (count / total_customers) * 100,
            }
        )

    # Top customers
    top_customers = []
    for val in customer_values[:top_n]:
        customer_tenure_days = 0
        if val.first_booking and val.last_booking:
            customer_tenure_days = (val.last_booking - val.first_booking).days

        top_customers.append(
            {
                "customer_id": str(val.id),
                "total_spent": float(val.total_spent_cents or 0) / 100,
                "booking_count": val.booking_count,
                "customer_tenure_days": customer_tenure_days,
                "avg_order_value": float(val.total_spent_cents or 0) / 100 / val.booking_count,
            }
        )

    top_customers.sort(key=lambda x: x["total_spent"], reverse=True)

    return {
        "average_clv": avg_clv,
        "median_clv": median_clv,
        "top_customers": top_customers[:top_n],
        "clv_distribution": distribution,
        "repeat_customer_rate": repeat_rate,
        "total_customers_analyzed": total_customers,
    }


@router.get("/booking-conversion-funnel")
async def get_booking_conversion_funnel(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: Session = Depends(get_db),
):
    """
    Get detailed booking conversion funnel analytics.

    Tracks the journey from lead → quote → booking → payment
    """
    if not date_from:
        date_from = datetime.now(timezone.utc).date() - timedelta(days=30)
    if not date_to:
        date_to = datetime.now(timezone.utc).date()

    # Stage 1: Website Visits (proxy via leads created)
    total_leads = (
        db.query(Lead).filter(Lead.created_at >= date_from, Lead.created_at <= date_to).count()
    )

    # Stage 2: Quote Requests (leads with contact info)
    quote_requests = (
        db.query(Lead)
        .filter(
            Lead.created_at >= date_from,
            Lead.created_at <= date_to,
            Lead.contact_name.isnot(None),
        )
        .count()
    )

    # Stage 3: Qualified Leads
    qualified = (
        db.query(Lead)
        .filter(
            Lead.created_at >= date_from,
            Lead.created_at <= date_to,
            Lead.status.in_([LeadStatus.QUALIFIED, LeadStatus.CONVERTED]),
        )
        .count()
    )

    # Stage 4: Bookings Created
    bookings_created = (
        db.query(Booking)
        .filter(Booking.created_at >= date_from, Booking.created_at <= date_to)
        .count()
    )

    # Stage 5: Deposits Paid
    deposits_paid = (
        db.query(Booking)
        .filter(
            Booking.created_at >= date_from,
            Booking.created_at <= date_to,
            Booking.payment_status.in_(["deposit_paid", "paid"]),
        )
        .count()
    )

    # Stage 6: Fully Paid
    fully_paid = (
        db.query(Booking)
        .filter(
            Booking.created_at >= date_from,
            Booking.created_at <= date_to,
            Booking.payment_status == "paid",
        )
        .count()
    )

    # Stage 7: Completed Events
    completed = (
        db.query(Booking)
        .filter(
            Booking.created_at >= date_from,
            Booking.created_at <= date_to,
            Booking.status == "completed",
        )
        .count()
    )

    # Calculate conversion rates
    stages = [
        {
            "stage": "Total Leads",
            "count": total_leads,
            "conversion_rate": 100.0,
        },
        {
            "stage": "Quote Requests",
            "count": quote_requests,
            "conversion_rate": ((quote_requests / total_leads * 100) if total_leads > 0 else 0),
        },
        {
            "stage": "Qualified",
            "count": qualified,
            "conversion_rate": ((qualified / total_leads * 100) if total_leads > 0 else 0),
        },
        {
            "stage": "Bookings Created",
            "count": bookings_created,
            "conversion_rate": ((bookings_created / total_leads * 100) if total_leads > 0 else 0),
        },
        {
            "stage": "Deposits Paid",
            "count": deposits_paid,
            "conversion_rate": ((deposits_paid / total_leads * 100) if total_leads > 0 else 0),
        },
        {
            "stage": "Fully Paid",
            "count": fully_paid,
            "conversion_rate": ((fully_paid / total_leads * 100) if total_leads > 0 else 0),
        },
        {
            "stage": "Completed",
            "count": completed,
            "conversion_rate": ((completed / total_leads * 100) if total_leads > 0 else 0),
        },
    ]

    # Calculate drop-off rates between stages
    drop_offs = []
    for i in range(len(stages) - 1):
        current_count = stages[i]["count"]
        next_count = stages[i + 1]["count"]
        drop_off_count = current_count - next_count
        drop_off_rate = (drop_off_count / current_count * 100) if current_count > 0 else 0

        drop_offs.append(
            {
                "from_stage": stages[i]["stage"],
                "to_stage": stages[i + 1]["stage"],
                "drop_off_count": drop_off_count,
                "drop_off_rate": drop_off_rate,
            }
        )

    return {
        "funnel_stages": stages,
        "drop_offs": drop_offs,
        "overall_conversion_rate": ((completed / total_leads * 100) if total_leads > 0 else 0),
        "date_range": {
            "from": date_from.isoformat(),
            "to": date_to.isoformat(),
        },
    }


@router.get("/menu-item-popularity")
async def get_menu_item_popularity(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: Session = Depends(get_db),
):
    """
    Analyze menu item popularity and preferences.

    Note: This is a placeholder implementation. Requires menu_items table
    or extracting from booking special_requests/notes.
    """
    if not date_from:
        date_from = datetime.now(timezone.utc).date() - timedelta(days=30)
    if not date_to:
        date_to = datetime.now(timezone.utc).date()

    # For now, analyze guest count preferences as a proxy for menu tiers
    guest_count_distribution = (
        db.query(
            func.case(
                [
                    (Booking.total_guests <= 10, "Small (1-10)"),
                    (Booking.total_guests <= 25, "Medium (11-25)"),
                    (Booking.total_guests <= 50, "Large (26-50)"),
                ],
                else_="Extra Large (50+)",
            ).label("party_size"),
            func.count(Booking.id).label("booking_count"),
            func.sum(Booking.total_due_cents).label("revenue_cents"),
        )
        .filter(
            Booking.created_at >= date_from,
            Booking.created_at <= date_to,
            Booking.status != "cancelled",
        )
        .group_by("party_size")
        .all()
    )

    popularity_data = []
    total_bookings = sum(item.booking_count for item in guest_count_distribution)

    for party_size, booking_count, revenue_cents in guest_count_distribution:
        popularity_data.append(
            {
                "category": party_size,
                "booking_count": booking_count,
                "revenue": float(revenue_cents or 0) / 100,
                "popularity_percentage": (
                    (booking_count / total_bookings * 100) if total_bookings > 0 else 0
                ),
                "avg_order_value": (
                    float(revenue_cents or 0) / 100 / booking_count if booking_count > 0 else 0
                ),
            }
        )

    # Sort by popularity
    popularity_data.sort(key=lambda x: x["booking_count"], reverse=True)

    return {
        "items": popularity_data,
        "total_bookings_analyzed": total_bookings,
        "date_range": {
            "from": date_from.isoformat(),
            "to": date_to.isoformat(),
        },
        "note": "This endpoint analyzes party size distribution as a proxy for menu preferences. Full menu item tracking requires additional data model.",
    }


@router.get("/geographic-distribution")
async def get_geographic_distribution(db: Session = Depends(get_db)):
    """
    Analyze customer and booking geographic distribution.

    Returns distribution by station/location.
    """
    from models.legacy_identity import Station

    # Get bookings by station
    station_distribution = (
        db.query(
            Station.id,
            Station.name,
            Station.address,
            func.count(Booking.id).label("booking_count"),
            func.sum(Booking.total_due_cents).label("revenue_cents"),
            func.count(func.distinct(Booking.customer_id)).label("unique_customers"),
        )
        .join(Booking, Station.id == Booking.station_id)
        .filter(Booking.status != "cancelled")
        .group_by(Station.id, Station.name, Station.address)
        .all()
    )

    total_bookings = sum(item.booking_count for item in station_distribution)
    total_revenue = sum(item.revenue_cents or 0 for item in station_distribution) / 100

    distribution_data = []
    for item in station_distribution:
        distribution_data.append(
            {
                "station_id": str(item.id),
                "station_name": item.name,
                "location": item.address,
                "booking_count": item.booking_count,
                "revenue": float(item.revenue_cents or 0) / 100,
                "unique_customers": item.unique_customers,
                "market_share_bookings": (
                    (item.booking_count / total_bookings * 100) if total_bookings > 0 else 0
                ),
                "market_share_revenue": (
                    (float(item.revenue_cents or 0) / 100 / total_revenue * 100)
                    if total_revenue > 0
                    else 0
                ),
            }
        )

    # Sort by revenue
    distribution_data.sort(key=lambda x: x["revenue"], reverse=True)

    return {
        "stations": distribution_data,
        "summary": {
            "total_stations": len(distribution_data),
            "total_bookings": total_bookings,
            "total_revenue": total_revenue,
            "avg_bookings_per_station": (
                total_bookings / len(distribution_data) if distribution_data else 0
            ),
        },
    }


@router.get("/seasonal-trends")
async def get_seasonal_trends(years: int = Query(1, ge=1, le=5), db: Session = Depends(get_db)):
    """
    Analyze seasonal booking trends and patterns.

    Returns:
        - Monthly booking patterns
        - Day of week analysis
        - Seasonal revenue trends
        - Peak/off-peak identification
    """
    start_date = datetime.now(timezone.utc) - timedelta(days=365 * years)

    # Monthly trends
    monthly_trends = (
        db.query(
            func.extract("month", Booking.created_at).label("month"),
            func.count(Booking.id).label("booking_count"),
            func.sum(Booking.total_due_cents).label("revenue_cents"),
            func.avg(Booking.total_guests).label("avg_party_size"),
        )
        .filter(Booking.created_at >= start_date, Booking.status != "cancelled")
        .group_by("month")
        .order_by("month")
        .all()
    )

    month_names = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]

    monthly_data = []
    for month, booking_count, revenue_cents, avg_party_size in monthly_trends:
        monthly_data.append(
            {
                "month": month_names[int(month) - 1],
                "month_number": int(month),
                "booking_count": booking_count,
                "revenue": float(revenue_cents or 0) / 100,
                "avg_party_size": float(avg_party_size or 0),
            }
        )

    # Day of week trends
    day_of_week_trends = (
        db.query(
            func.extract("dow", Booking.date).label("day_of_week"),
            func.count(Booking.id).label("booking_count"),
            func.sum(Booking.total_due_cents).label("revenue_cents"),
        )
        .filter(Booking.created_at >= start_date, Booking.status != "cancelled")
        .group_by("day_of_week")
        .order_by("day_of_week")
        .all()
    )

    day_names = [
        "Sunday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
    ]

    day_of_week_data = []
    for day_num, booking_count, revenue_cents in day_of_week_trends:
        day_of_week_data.append(
            {
                "day": day_names[int(day_num)],
                "day_number": int(day_num),
                "booking_count": booking_count,
                "revenue": float(revenue_cents or 0) / 100,
            }
        )

    # Identify peak months
    if monthly_data:
        peak_month = max(monthly_data, key=lambda x: x["booking_count"])
        off_peak_month = min(monthly_data, key=lambda x: x["booking_count"])
    else:
        peak_month = off_peak_month = None

    # Identify peak days
    if day_of_week_data:
        peak_day = max(day_of_week_data, key=lambda x: x["booking_count"])
        slowest_day = min(day_of_week_data, key=lambda x: x["booking_count"])
    else:
        peak_day = slowest_day = None

    return {
        "monthly_trends": monthly_data,
        "day_of_week_trends": day_of_week_data,
        "peak_periods": {
            "peak_month": peak_month,
            "off_peak_month": off_peak_month,
            "peak_day": peak_day,
            "slowest_day": slowest_day,
        },
        "analysis_period_years": years,
    }


# Helper functions
async def _get_lead_analytics(date_from: date, date_to: date, db: Session) -> LeadAnalytics:
    """Get lead analytics for date range."""

    # Total leads
    total_leads = (
        db.query(Lead).filter(Lead.created_at >= date_from, Lead.created_at <= date_to).count()
    )

    # New leads (created in period)
    new_leads = total_leads

    # Qualified leads
    qualified_leads = (
        db.query(Lead)
        .filter(
            Lead.created_at >= date_from,
            Lead.created_at <= date_to,
            Lead.status.in_([LeadStatus.QUALIFIED, LeadStatus.CONVERTED]),
        )
        .count()
    )

    # Converted leads
    converted_leads = (
        db.query(Lead)
        .filter(
            Lead.created_at >= date_from,
            Lead.created_at <= date_to,
            Lead.status == LeadStatus.CONVERTED,
        )
        .count()
    )

    # Conversion rate
    conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0

    # Average score
    avg_score_result = (
        db.query(func.avg(Lead.score))
        .filter(Lead.created_at >= date_from, Lead.created_at <= date_to)
        .scalar()
    )
    average_score = float(avg_score_result) if avg_score_result else 0

    # Leads by source
    source_counts = (
        db.query(Lead.source, func.count(Lead.id).label("count"))
        .filter(Lead.created_at >= date_from, Lead.created_at <= date_to)
        .group_by(Lead.source)
        .all()
    )

    leads_by_source = {source.value: count for source, count in source_counts}

    # Leads by quality
    quality_counts = (
        db.query(Lead.quality, func.count(Lead.id).label("count"))
        .filter(Lead.created_at >= date_from, Lead.created_at <= date_to)
        .group_by(Lead.quality)
        .all()
    )

    leads_by_quality = {
        quality.value if quality else "unrated": count for quality, count in quality_counts
    }

    # Daily lead count
    daily_counts = (
        db.query(
            func.date(Lead.created_at).label("date"),
            func.count(Lead.id).label("count"),
        )
        .filter(Lead.created_at >= date_from, Lead.created_at <= date_to)
        .group_by(func.date(Lead.created_at))
        .order_by("date")
        .all()
    )

    daily_lead_count = [{"date": date.isoformat(), "count": count} for date, count in daily_counts]

    return LeadAnalytics(
        total_leads=total_leads,
        new_leads=new_leads,
        qualified_leads=qualified_leads,
        converted_leads=converted_leads,
        conversion_rate=conversion_rate,
        average_score=average_score,
        leads_by_source=leads_by_source,
        leads_by_quality=leads_by_quality,
        daily_lead_count=daily_lead_count,
    )


async def _get_newsletter_analytics(
    date_from: date, date_to: date, db: Session
) -> NewsletterAnalytics:
    """Get newsletter analytics for date range."""

    # Total subscribers
    total_subscribers = db.query(Subscriber).count()

    # Active subscribers
    active_subscribers = db.query(Subscriber).filter(Subscriber.subscribed).count()

    # Total campaigns
    total_campaigns = (
        db.query(Campaign)
        .filter(Campaign.created_at >= date_from, Campaign.created_at <= date_to)
        .count()
    )

    # Campaigns sent
    campaigns_sent = (
        db.query(Campaign)
        .filter(
            Campaign.created_at >= date_from,
            Campaign.created_at <= date_to,
            Campaign.status == CampaignStatus.SENT,
        )
        .count()
    )

    # Average open rate
    avg_open_rate = 0.0
    avg_click_rate = 0.0

    if campaigns_sent > 0:
        # Calculate average open rate across all sent campaigns
        open_rates = []
        click_rates = []

        sent_campaigns = (
            db.query(Campaign)
            .filter(
                Campaign.created_at >= date_from,
                Campaign.created_at <= date_to,
                Campaign.status == CampaignStatus.SENT,
            )
            .all()
        )

        for campaign in sent_campaigns:
            if campaign.total_recipients > 0:
                opens = (
                    db.query(CampaignEvent)
                    .filter(
                        CampaignEvent.campaign_id == campaign.id,
                        CampaignEvent.type == CampaignEventType.OPENED,
                    )
                    .count()
                )

                clicks = (
                    db.query(CampaignEvent)
                    .filter(
                        CampaignEvent.campaign_id == campaign.id,
                        CampaignEvent.type == CampaignEventType.CLICKED,
                    )
                    .count()
                )

                open_rates.append(opens / campaign.total_recipients * 100)
                click_rates.append(clicks / campaign.total_recipients * 100)

        avg_open_rate = sum(open_rates) / len(open_rates) if open_rates else 0
        avg_click_rate = sum(click_rates) / len(click_rates) if click_rates else 0

    # Subscriber growth
    daily_signups = (
        db.query(
            func.date(Subscriber.created_at).label("date"),
            func.count(Subscriber.id).label("count"),
        )
        .filter(
            Subscriber.created_at >= date_from,
            Subscriber.created_at <= date_to,
        )
        .group_by(func.date(Subscriber.created_at))
        .order_by("date")
        .all()
    )

    subscriber_growth = [
        {"date": date.isoformat(), "signups": count} for date, count in daily_signups
    ]

    # Campaign performance
    campaign_performance = []
    for campaign in sent_campaigns[:10]:  # Top 10 recent campaigns
        opens = (
            db.query(CampaignEvent)
            .filter(
                CampaignEvent.campaign_id == campaign.id,
                CampaignEvent.type == CampaignEventType.OPENED,
            )
            .count()
        )

        clicks = (
            db.query(CampaignEvent)
            .filter(
                CampaignEvent.campaign_id == campaign.id,
                CampaignEvent.type == CampaignEventType.CLICKED,
            )
            .count()
        )

        campaign_performance.append(
            {
                "campaign_name": campaign.name,
                "sent_at": (campaign.sent_at.isoformat() if campaign.sent_at else None),
                "recipients": campaign.total_recipients,
                "opens": opens,
                "clicks": clicks,
                "open_rate": (
                    (opens / campaign.total_recipients * 100)
                    if campaign.total_recipients > 0
                    else 0
                ),
                "click_rate": (
                    (clicks / campaign.total_recipients * 100)
                    if campaign.total_recipients > 0
                    else 0
                ),
            }
        )

    return NewsletterAnalytics(
        total_subscribers=total_subscribers,
        active_subscribers=active_subscribers,
        total_campaigns=total_campaigns,
        campaigns_sent=campaigns_sent,
        average_open_rate=avg_open_rate,
        average_click_rate=avg_click_rate,
        subscriber_growth=subscriber_growth,
        campaign_performance=campaign_performance,
    )


async def _get_sales_analytics(date_from: date, date_to: date, db: Session) -> SalesAnalytics:
    """Get sales analytics for date range."""

    # Get bookings in date range
    bookings = (
        db.query(Booking)
        .filter(Booking.created_at >= date_from, Booking.created_at <= date_to)
        .all()
    )

    total_bookings = len(bookings)
    total_revenue = sum(booking.total_cost_cents for booking in bookings) / 100
    average_booking_value = total_revenue / total_bookings if total_bookings > 0 else 0

    # Revenue from converted leads
    converted_leads = (
        db.query(Lead)
        .filter(
            Lead.status == LeadStatus.CONVERTED,
            Lead.conversion_date >= date_from,
            Lead.conversion_date <= date_to,
        )
        .all()
    )

    # Calculate conversion value (revenue from leads that converted)
    conversion_value = 0.0
    for lead in converted_leads:
        if lead.customer_id:
            customer_bookings = (
                db.query(Booking)
                .filter(
                    Booking.customer_id == lead.customer_id,
                    Booking.created_at >= lead.conversion_date,
                )
                .all()
            )
            conversion_value += sum(booking.total_cost_cents for booking in customer_bookings) / 100

    # Lead to booking conversion rate
    total_leads = (
        db.query(Lead).filter(Lead.created_at >= date_from, Lead.created_at <= date_to).count()
    )

    lead_to_booking_conversion = (
        (len(converted_leads) / total_leads * 100) if total_leads > 0 else 0
    )

    # Monthly revenue
    monthly_revenue = (
        db.query(
            func.date_trunc("month", Booking.created_at).label("month"),
            func.sum(Booking.total_cost_cents).label("revenue_cents"),
        )
        .filter(Booking.created_at >= date_from, Booking.created_at <= date_to)
        .group_by(func.date_trunc("month", Booking.created_at))
        .order_by("month")
        .all()
    )

    revenue_by_month = [
        {
            "month": month.strftime("%Y-%m") if month else "",
            "revenue": float(revenue_cents) / 100 if revenue_cents else 0,
        }
        for month, revenue_cents in monthly_revenue
    ]

    return SalesAnalytics(
        total_revenue=total_revenue,
        total_bookings=total_bookings,
        conversion_value=conversion_value,
        average_booking_value=average_booking_value,
        revenue_by_month=revenue_by_month,
        lead_to_booking_conversion=lead_to_booking_conversion,
    )


async def _get_recent_activity(db: Session) -> list[dict[str, Any]]:
    """Get recent activity across the system."""

    activities = []

    # Recent leads
    recent_leads = db.query(Lead).order_by(desc(Lead.created_at)).limit(5).all()
    for lead in recent_leads:
        activities.append(
            {
                "type": "new_lead",
                "title": f"New lead from {lead.source.value}",
                "description": f"Lead score: {lead.score}, Quality: {lead.quality.value if lead.quality else 'Unrated'}",
                "timestamp": lead.created_at.isoformat(),
                "id": str(lead.id),
            }
        )

    # Recent conversions
    recent_conversions = (
        db.query(Lead)
        .filter(Lead.status == LeadStatus.CONVERTED)
        .order_by(desc(Lead.conversion_date))
        .limit(3)
        .all()
    )

    for lead in recent_conversions:
        activities.append(
            {
                "type": "lead_converted",
                "title": "Lead converted to customer",
                "description": f"Lead from {lead.source.value} successfully converted",
                "timestamp": (
                    lead.conversion_date.isoformat()
                    if lead.conversion_date
                    else lead.updated_at.isoformat()
                ),
                "id": str(lead.id),
            }
        )

    # Recent campaigns
    recent_campaigns = db.query(Campaign).order_by(desc(Campaign.sent_at)).limit(3).all()
    for campaign in recent_campaigns:
        if campaign.sent_at:
            activities.append(
                {
                    "type": "campaign_sent",
                    "title": f"Campaign '{campaign.name}' sent",
                    "description": f"Sent to {campaign.total_recipients} recipients",
                    "timestamp": campaign.sent_at.isoformat(),
                    "id": str(campaign.id),
                }
            )

    # Sort by timestamp
    activities.sort(key=lambda x: x["timestamp"], reverse=True)

    return activities[:10]


async def _get_alerts(db: Session) -> list[dict[str, Any]]:
    """Get system alerts and notifications."""

    alerts = []

    # Overdue follow-ups
    overdue_followups = (
        db.query(Lead)
        .filter(
            Lead.follow_up_date < datetime.now(timezone.utc),
            Lead.status.in_([LeadStatus.NEW, LeadStatus.WORKING, LeadStatus.QUALIFIED]),
        )
        .count()
    )

    if overdue_followups > 0:
        alerts.append(
            {
                "type": "warning",
                "title": "Overdue Follow-ups",
                "message": f"{overdue_followups} leads have overdue follow-up dates",
                "action": "Review and update follow-up schedules",
                "count": overdue_followups,
            }
        )

    # Hot leads requiring attention
    hot_leads = (
        db.query(Lead)
        .filter(Lead.quality == LeadQuality.HOT, Lead.status == LeadStatus.NEW)
        .count()
    )

    if hot_leads > 0:
        alerts.append(
            {
                "type": "urgent",
                "title": "Hot Leads Need Attention",
                "message": f"{hot_leads} hot leads are still in 'new' status",
                "action": "Assign and contact immediately",
                "count": hot_leads,
            }
        )

    # Low engagement subscribers
    low_engagement = (
        db.query(Subscriber).filter(Subscriber.subscribed, Subscriber.engagement_score < 20).count()
    )

    if low_engagement > 0:
        alerts.append(
            {
                "type": "info",
                "title": "Low Engagement Subscribers",
                "message": f"{low_engagement} subscribers have low engagement scores",
                "action": "Consider re-engagement campaign",
                "count": low_engagement,
            }
        )

    return alerts
