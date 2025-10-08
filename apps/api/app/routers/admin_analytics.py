"""Enhanced admin dashboard with lead and newsletter analytics."""

from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from pydantic import BaseModel

from ..database import get_db
from ..models.lead_newsletter import (
    Lead, LeadStatus, LeadQuality, LeadSource,
    Subscriber, Campaign, CampaignStatus, CampaignEvent, CampaignEventType
)
from ..models.core import Customer, Booking


router = APIRouter(prefix="/admin/analytics", tags=["admin", "analytics"])


# Response models
class LeadAnalytics(BaseModel):
    total_leads: int
    new_leads: int
    qualified_leads: int
    converted_leads: int
    conversion_rate: float
    average_score: float
    leads_by_source: Dict[str, int]
    leads_by_quality: Dict[str, int]
    daily_lead_count: List[Dict[str, Any]]


class NewsletterAnalytics(BaseModel):
    total_subscribers: int
    active_subscribers: int
    total_campaigns: int
    campaigns_sent: int
    average_open_rate: float
    average_click_rate: float
    subscriber_growth: List[Dict[str, Any]]
    campaign_performance: List[Dict[str, Any]]


class SalesAnalytics(BaseModel):
    total_revenue: float
    total_bookings: int
    conversion_value: float
    average_booking_value: float
    revenue_by_month: List[Dict[str, Any]]
    lead_to_booking_conversion: float


class DashboardOverview(BaseModel):
    leads: LeadAnalytics
    newsletter: NewsletterAnalytics
    sales: SalesAnalytics
    recent_activity: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]


@router.get("/overview", response_model=DashboardOverview)
async def get_dashboard_overview(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard overview."""
    
    # Default to last 30 days if no dates provided
    if not date_from:
        date_from = datetime.now().date() - timedelta(days=30)
    if not date_to:
        date_to = datetime.now().date()
    
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
        alerts=alerts
    )


@router.get("/leads", response_model=LeadAnalytics)
async def get_lead_analytics(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Get detailed lead analytics."""
    
    if not date_from:
        date_from = datetime.now().date() - timedelta(days=30)
    if not date_to:
        date_to = datetime.now().date()
    
    return await _get_lead_analytics(date_from, date_to, db)


@router.get("/newsletter", response_model=NewsletterAnalytics)
async def get_newsletter_analytics(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Get detailed newsletter analytics."""
    
    if not date_from:
        date_from = datetime.now().date() - timedelta(days=30)
    if not date_to:
        date_to = datetime.now().date()
    
    return await _get_newsletter_analytics(date_from, date_to, db)


@router.get("/funnel")
async def get_conversion_funnel(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Get conversion funnel analytics."""
    
    if not date_from:
        date_from = datetime.now().date() - timedelta(days=30)
    if not date_to:
        date_to = datetime.now().date()
    
    # Count leads at each stage
    total_leads = db.query(Lead).filter(
        Lead.created_at >= date_from,
        Lead.created_at <= date_to
    ).count()
    
    qualified_leads = db.query(Lead).filter(
        Lead.created_at >= date_from,
        Lead.created_at <= date_to,
        Lead.status.in_([LeadStatus.QUALIFIED, LeadStatus.CONVERTED])
    ).count()
    
    converted_leads = db.query(Lead).filter(
        Lead.created_at >= date_from,
        Lead.created_at <= date_to,
        Lead.status == LeadStatus.CONVERTED
    ).count()
    
    # Count actual bookings from converted leads
    bookings_from_leads = db.query(Booking).join(
        Lead, Lead.customer_id == Booking.customer_id
    ).filter(
        Lead.status == LeadStatus.CONVERTED,
        Booking.created_at >= date_from,
        Booking.created_at <= date_to
    ).count()
    
    return {
        "funnel_stages": [
            {"stage": "Total Leads", "count": total_leads, "conversion_rate": 100.0},
            {
                "stage": "Qualified", 
                "count": qualified_leads, 
                "conversion_rate": (qualified_leads / total_leads * 100) if total_leads > 0 else 0
            },
            {
                "stage": "Converted", 
                "count": converted_leads, 
                "conversion_rate": (converted_leads / total_leads * 100) if total_leads > 0 else 0
            },
            {
                "stage": "Booked", 
                "count": bookings_from_leads, 
                "conversion_rate": (bookings_from_leads / total_leads * 100) if total_leads > 0 else 0
            }
        ],
        "overall_conversion_rate": (bookings_from_leads / total_leads * 100) if total_leads > 0 else 0
    }


@router.get("/lead-scoring")
async def get_lead_scoring_analysis(
    db: Session = Depends(get_db)
):
    """Get lead scoring analysis and distribution."""
    
    # Score distribution
    score_ranges = [
        ("0-20", 0, 20),
        ("21-40", 21, 40),
        ("41-60", 41, 60),
        ("61-80", 61, 80),
        ("81-100", 81, 100)
    ]
    
    score_distribution = []
    for range_name, min_score, max_score in score_ranges:
        count = db.query(Lead).filter(
            Lead.score >= min_score,
            Lead.score <= max_score
        ).count()
        score_distribution.append({
            "range": range_name,
            "count": count
        })
    
    # Quality distribution
    quality_counts = db.query(
        Lead.quality,
        func.count(Lead.id).label('count')
    ).group_by(Lead.quality).all()
    
    quality_distribution = [
        {"quality": quality.value if quality else "unrated", "count": count}
        for quality, count in quality_counts
    ]
    
    # Top performing sources by conversion
    source_performance = db.query(
        Lead.source,
        func.count(Lead.id).label('total_leads'),
        func.sum(func.case([(Lead.status == LeadStatus.CONVERTED, 1)], else_=0)).label('converted_leads'),
        func.avg(Lead.score).label('avg_score')
    ).group_by(Lead.source).all()
    
    source_analysis = []
    for source, total, converted, avg_score in source_performance:
        conversion_rate = (converted / total * 100) if total > 0 else 0
        source_analysis.append({
            "source": source.value,
            "total_leads": total,
            "converted_leads": converted or 0,
            "conversion_rate": conversion_rate,
            "average_score": float(avg_score) if avg_score else 0
        })
    
    return {
        "score_distribution": score_distribution,
        "quality_distribution": quality_distribution,
        "source_performance": source_analysis
    }


@router.get("/engagement-trends")
async def get_engagement_trends(
    days: int = Query(30, le=365),
    db: Session = Depends(get_db)
):
    """Get engagement trends over time."""
    
    start_date = datetime.now() - timedelta(days=days)
    
    # Daily lead creation
    daily_leads = db.query(
        func.date(Lead.created_at).label('date'),
        func.count(Lead.id).label('count')
    ).filter(
        Lead.created_at >= start_date
    ).group_by(func.date(Lead.created_at)).order_by('date').all()
    
    # Daily newsletter signups
    daily_signups = db.query(
        func.date(Subscriber.created_at).label('date'),
        func.count(Subscriber.id).label('count')
    ).filter(
        Subscriber.created_at >= start_date
    ).group_by(func.date(Subscriber.created_at)).order_by('date').all()
    
    # Campaign performance over time
    campaign_performance = db.query(
        func.date(Campaign.sent_at).label('date'),
        func.count(Campaign.id).label('campaigns_sent'),
        func.avg(
            func.cast(
                db.query(func.count(CampaignEvent.id)).filter(
                    CampaignEvent.campaign_id == Campaign.id,
                    CampaignEvent.type == CampaignEventType.OPENED
                ).scalar_subquery(), 
                func.Float
            ) / Campaign.total_recipients * 100
        ).label('avg_open_rate')
    ).filter(
        Campaign.sent_at >= start_date,
        Campaign.sent_at.isnot(None)
    ).group_by(func.date(Campaign.sent_at)).order_by('date').all()
    
    return {
        "daily_leads": [
            {"date": date.isoformat(), "count": count}
            for date, count in daily_leads
        ],
        "daily_signups": [
            {"date": date.isoformat(), "count": count}
            for date, count in daily_signups
        ],
        "campaign_performance": [
            {
                "date": date.isoformat(), 
                "campaigns_sent": campaigns_sent,
                "avg_open_rate": float(avg_open_rate) if avg_open_rate else 0
            }
            for date, campaigns_sent, avg_open_rate in campaign_performance
        ]
    }


# Helper functions
async def _get_lead_analytics(date_from: date, date_to: date, db: Session) -> LeadAnalytics:
    """Get lead analytics for date range."""
    
    # Total leads
    total_leads = db.query(Lead).filter(
        Lead.created_at >= date_from,
        Lead.created_at <= date_to
    ).count()
    
    # New leads (created in period)
    new_leads = total_leads
    
    # Qualified leads
    qualified_leads = db.query(Lead).filter(
        Lead.created_at >= date_from,
        Lead.created_at <= date_to,
        Lead.status.in_([LeadStatus.QUALIFIED, LeadStatus.CONVERTED])
    ).count()
    
    # Converted leads
    converted_leads = db.query(Lead).filter(
        Lead.created_at >= date_from,
        Lead.created_at <= date_to,
        Lead.status == LeadStatus.CONVERTED
    ).count()
    
    # Conversion rate
    conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
    
    # Average score
    avg_score_result = db.query(func.avg(Lead.score)).filter(
        Lead.created_at >= date_from,
        Lead.created_at <= date_to
    ).scalar()
    average_score = float(avg_score_result) if avg_score_result else 0
    
    # Leads by source
    source_counts = db.query(
        Lead.source,
        func.count(Lead.id).label('count')
    ).filter(
        Lead.created_at >= date_from,
        Lead.created_at <= date_to
    ).group_by(Lead.source).all()
    
    leads_by_source = {source.value: count for source, count in source_counts}
    
    # Leads by quality
    quality_counts = db.query(
        Lead.quality,
        func.count(Lead.id).label('count')
    ).filter(
        Lead.created_at >= date_from,
        Lead.created_at <= date_to
    ).group_by(Lead.quality).all()
    
    leads_by_quality = {
        quality.value if quality else "unrated": count 
        for quality, count in quality_counts
    }
    
    # Daily lead count
    daily_counts = db.query(
        func.date(Lead.created_at).label('date'),
        func.count(Lead.id).label('count')
    ).filter(
        Lead.created_at >= date_from,
        Lead.created_at <= date_to
    ).group_by(func.date(Lead.created_at)).order_by('date').all()
    
    daily_lead_count = [
        {"date": date.isoformat(), "count": count}
        for date, count in daily_counts
    ]
    
    return LeadAnalytics(
        total_leads=total_leads,
        new_leads=new_leads,
        qualified_leads=qualified_leads,
        converted_leads=converted_leads,
        conversion_rate=conversion_rate,
        average_score=average_score,
        leads_by_source=leads_by_source,
        leads_by_quality=leads_by_quality,
        daily_lead_count=daily_lead_count
    )


async def _get_newsletter_analytics(date_from: date, date_to: date, db: Session) -> NewsletterAnalytics:
    """Get newsletter analytics for date range."""
    
    # Total subscribers
    total_subscribers = db.query(Subscriber).count()
    
    # Active subscribers
    active_subscribers = db.query(Subscriber).filter(
        Subscriber.subscribed == True
    ).count()
    
    # Total campaigns
    total_campaigns = db.query(Campaign).filter(
        Campaign.created_at >= date_from,
        Campaign.created_at <= date_to
    ).count()
    
    # Campaigns sent
    campaigns_sent = db.query(Campaign).filter(
        Campaign.created_at >= date_from,
        Campaign.created_at <= date_to,
        Campaign.status == CampaignStatus.SENT
    ).count()
    
    # Average open rate
    avg_open_rate = 0.0
    avg_click_rate = 0.0
    
    if campaigns_sent > 0:
        # Calculate average open rate across all sent campaigns
        open_rates = []
        click_rates = []
        
        sent_campaigns = db.query(Campaign).filter(
            Campaign.created_at >= date_from,
            Campaign.created_at <= date_to,
            Campaign.status == CampaignStatus.SENT
        ).all()
        
        for campaign in sent_campaigns:
            if campaign.total_recipients > 0:
                opens = db.query(CampaignEvent).filter(
                    CampaignEvent.campaign_id == campaign.id,
                    CampaignEvent.type == CampaignEventType.OPENED
                ).count()
                
                clicks = db.query(CampaignEvent).filter(
                    CampaignEvent.campaign_id == campaign.id,
                    CampaignEvent.type == CampaignEventType.CLICKED
                ).count()
                
                open_rates.append(opens / campaign.total_recipients * 100)
                click_rates.append(clicks / campaign.total_recipients * 100)
        
        avg_open_rate = sum(open_rates) / len(open_rates) if open_rates else 0
        avg_click_rate = sum(click_rates) / len(click_rates) if click_rates else 0
    
    # Subscriber growth
    daily_signups = db.query(
        func.date(Subscriber.created_at).label('date'),
        func.count(Subscriber.id).label('count')
    ).filter(
        Subscriber.created_at >= date_from,
        Subscriber.created_at <= date_to
    ).group_by(func.date(Subscriber.created_at)).order_by('date').all()
    
    subscriber_growth = [
        {"date": date.isoformat(), "signups": count}
        for date, count in daily_signups
    ]
    
    # Campaign performance
    campaign_performance = []
    for campaign in sent_campaigns[:10]:  # Top 10 recent campaigns
        opens = db.query(CampaignEvent).filter(
            CampaignEvent.campaign_id == campaign.id,
            CampaignEvent.type == CampaignEventType.OPENED
        ).count()
        
        clicks = db.query(CampaignEvent).filter(
            CampaignEvent.campaign_id == campaign.id,
            CampaignEvent.type == CampaignEventType.CLICKED
        ).count()
        
        campaign_performance.append({
            "campaign_name": campaign.name,
            "sent_at": campaign.sent_at.isoformat() if campaign.sent_at else None,
            "recipients": campaign.total_recipients,
            "opens": opens,
            "clicks": clicks,
            "open_rate": (opens / campaign.total_recipients * 100) if campaign.total_recipients > 0 else 0,
            "click_rate": (clicks / campaign.total_recipients * 100) if campaign.total_recipients > 0 else 0
        })
    
    return NewsletterAnalytics(
        total_subscribers=total_subscribers,
        active_subscribers=active_subscribers,
        total_campaigns=total_campaigns,
        campaigns_sent=campaigns_sent,
        average_open_rate=avg_open_rate,
        average_click_rate=avg_click_rate,
        subscriber_growth=subscriber_growth,
        campaign_performance=campaign_performance
    )


async def _get_sales_analytics(date_from: date, date_to: date, db: Session) -> SalesAnalytics:
    """Get sales analytics for date range."""
    
    # Get bookings in date range
    bookings = db.query(Booking).filter(
        Booking.created_at >= date_from,
        Booking.created_at <= date_to
    ).all()
    
    total_bookings = len(bookings)
    total_revenue = sum(booking.total_cost_cents for booking in bookings) / 100
    average_booking_value = total_revenue / total_bookings if total_bookings > 0 else 0
    
    # Revenue from converted leads
    converted_leads = db.query(Lead).filter(
        Lead.status == LeadStatus.CONVERTED,
        Lead.conversion_date >= date_from,
        Lead.conversion_date <= date_to
    ).all()
    
    # Calculate conversion value (revenue from leads that converted)
    conversion_value = 0.0
    for lead in converted_leads:
        if lead.customer_id:
            customer_bookings = db.query(Booking).filter(
                Booking.customer_id == lead.customer_id,
                Booking.created_at >= lead.conversion_date
            ).all()
            conversion_value += sum(booking.total_cost_cents for booking in customer_bookings) / 100
    
    # Lead to booking conversion rate
    total_leads = db.query(Lead).filter(
        Lead.created_at >= date_from,
        Lead.created_at <= date_to
    ).count()
    
    lead_to_booking_conversion = (len(converted_leads) / total_leads * 100) if total_leads > 0 else 0
    
    # Monthly revenue
    monthly_revenue = db.query(
        func.date_trunc('month', Booking.created_at).label('month'),
        func.sum(Booking.total_cost_cents).label('revenue_cents')
    ).filter(
        Booking.created_at >= date_from,
        Booking.created_at <= date_to
    ).group_by(func.date_trunc('month', Booking.created_at)).order_by('month').all()
    
    revenue_by_month = [
        {
            "month": month.strftime('%Y-%m') if month else "",
            "revenue": float(revenue_cents) / 100 if revenue_cents else 0
        }
        for month, revenue_cents in monthly_revenue
    ]
    
    return SalesAnalytics(
        total_revenue=total_revenue,
        total_bookings=total_bookings,
        conversion_value=conversion_value,
        average_booking_value=average_booking_value,
        revenue_by_month=revenue_by_month,
        lead_to_booking_conversion=lead_to_booking_conversion
    )


async def _get_recent_activity(db: Session) -> List[Dict[str, Any]]:
    """Get recent activity across the system."""
    
    activities = []
    
    # Recent leads
    recent_leads = db.query(Lead).order_by(desc(Lead.created_at)).limit(5).all()
    for lead in recent_leads:
        activities.append({
            "type": "new_lead",
            "title": f"New lead from {lead.source.value}",
            "description": f"Lead score: {lead.score}, Quality: {lead.quality.value if lead.quality else 'Unrated'}",
            "timestamp": lead.created_at.isoformat(),
            "id": str(lead.id)
        })
    
    # Recent conversions
    recent_conversions = db.query(Lead).filter(
        Lead.status == LeadStatus.CONVERTED
    ).order_by(desc(Lead.conversion_date)).limit(3).all()
    
    for lead in recent_conversions:
        activities.append({
            "type": "lead_converted",
            "title": "Lead converted to customer",
            "description": f"Lead from {lead.source.value} successfully converted",
            "timestamp": lead.conversion_date.isoformat() if lead.conversion_date else lead.updated_at.isoformat(),
            "id": str(lead.id)
        })
    
    # Recent campaigns
    recent_campaigns = db.query(Campaign).order_by(desc(Campaign.sent_at)).limit(3).all()
    for campaign in recent_campaigns:
        if campaign.sent_at:
            activities.append({
                "type": "campaign_sent",
                "title": f"Campaign '{campaign.name}' sent",
                "description": f"Sent to {campaign.total_recipients} recipients",
                "timestamp": campaign.sent_at.isoformat(),
                "id": str(campaign.id)
            })
    
    # Sort by timestamp
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return activities[:10]


async def _get_alerts(db: Session) -> List[Dict[str, Any]]:
    """Get system alerts and notifications."""
    
    alerts = []
    
    # Overdue follow-ups
    overdue_followups = db.query(Lead).filter(
        Lead.follow_up_date < datetime.now(),
        Lead.status.in_([LeadStatus.NEW, LeadStatus.WORKING, LeadStatus.QUALIFIED])
    ).count()
    
    if overdue_followups > 0:
        alerts.append({
            "type": "warning",
            "title": "Overdue Follow-ups",
            "message": f"{overdue_followups} leads have overdue follow-up dates",
            "action": "Review and update follow-up schedules",
            "count": overdue_followups
        })
    
    # Hot leads requiring attention
    hot_leads = db.query(Lead).filter(
        Lead.quality == LeadQuality.HOT,
        Lead.status == LeadStatus.NEW
    ).count()
    
    if hot_leads > 0:
        alerts.append({
            "type": "urgent",
            "title": "Hot Leads Need Attention",
            "message": f"{hot_leads} hot leads are still in 'new' status",
            "action": "Assign and contact immediately",
            "count": hot_leads
        })
    
    # Low engagement subscribers
    low_engagement = db.query(Subscriber).filter(
        Subscriber.subscribed == True,
        Subscriber.engagement_score < 20
    ).count()
    
    if low_engagement > 0:
        alerts.append({
            "type": "info",
            "title": "Low Engagement Subscribers",
            "message": f"{low_engagement} subscribers have low engagement scores",
            "action": "Consider re-engagement campaign",
            "count": low_engagement
        })
    
    return alerts