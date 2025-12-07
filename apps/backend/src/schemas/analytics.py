"""
Analytics Schemas

Pydantic models for business analytics and reporting.

NOTE: These are BUSINESS ANALYTICS (customer behavior, booking patterns, retention)
      NOT traffic analytics (Google Analytics handles that separately).

FUTURE SCALING CONSIDERATIONS:
- Real-time dashboard integration (WebSocket push updates)
- Time-series aggregation for historical trend analysis
- Chef performance metrics (bookings per chef, ratings, revenue)
- Geographic heatmaps (popular booking areas, travel fee optimization)
- Seasonal demand forecasting (ML-based predictions)
- Revenue analytics (deposits, full payments, cancellation rates)
- Customer lifetime value (CLV) calculations
- Cohort analysis (retention by signup month)

Integration Points:
- Admin dashboard: /admin/analytics endpoints
- Scheduled reports: Email digest of key metrics
- Export: CSV/Excel for external analysis
"""

from pydantic import BaseModel, Field


class CustomerAnalytics(BaseModel):
    """
    Customer analytics response model.

    Used by admin dashboard to display customer insights.
    Data is aggregated from bookings, customers, and transaction tables.
    """

    total_customers: int = Field(..., description="Total registered customers")
    new_customers_this_month: int = Field(
        ..., description="New signups this calendar month"
    )
    returning_customers: int = Field(
        ..., description="Customers with 2+ bookings"
    )
    customer_tiers: dict = Field(
        ...,
        description="Count by tier: {'standard': N, 'vip': N, 'premium': N}",
    )
    top_customers: list = Field(
        ..., description="Top 10 customers by booking count or spend"
    )
    booking_patterns: dict = Field(
        ...,
        description="Patterns: {'weekday_preference': {...}, 'time_slot_preference': {...}}",
    )
    retention_rate: float = Field(
        ..., ge=0.0, le=1.0, description="30-day retention rate (0.0 to 1.0)"
    )
