"""
Holiday Analytics Service

Track bookings, revenue, and marketing performance by holiday/season.

Features:
- Booking trends by holiday
- Revenue analysis by season
- Marketing ROI tracking
- Peak season identification
- Year-over-year comparisons
- Forecasting

Usage:
    analytics = HolidayAnalyticsService(db)

    # Get seasonal trends
    trends = await analytics.get_seasonal_trends(year=2025)

    # Track marketing ROI
    roi = await analytics.get_marketing_roi(campaign_id="thanksgiving_2025")

    # Forecast next season
    forecast = await analytics.forecast_holiday_bookings("christmas", 2026)
"""

from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Optional
from decimal import Decimal
import logging

from sqlalchemy import select, func, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession

from services.holiday_service import get_holiday_service, HolidayCategory
from db.models.core import Booking  # Booking model
from core.database import get_db

logger = logging.getLogger(__name__)


class HolidayAnalyticsService:
    """
    Analytics service for tracking holiday/season performance.

    Provides insights for:
    - Which holidays drive most bookings
    - Revenue by season
    - Marketing campaign effectiveness
    - Peak booking periods
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.holiday_service = get_holiday_service()

    async def get_seasonal_trends(
        self, year: Optional[int] = None, include_forecast: bool = False
    ) -> List[Dict]:
        """
        Get booking and revenue trends by holiday/season.

        Returns:
            List of seasonal analytics:
            [
                {
                    "season": "Summer Wedding Season",
                    "holiday_key": "summer_wedding_season",
                    "date_range": {"start": "2025-06-01", "end": "2025-08-31"},
                    "booking_count": 156,
                    "total_revenue": 125600.00,
                    "avg_order_value": 805.13,
                    "top_event_types": ["wedding", "rehearsal_dinner"],
                    "yoy_growth": "+23%",
                },
                ...
            ]
        """
        if year is None:
            year = datetime.now(timezone.utc).year

        trends = []

        # Get all holidays for the year
        upcoming = self.holiday_service.get_upcoming_holidays(days=365, from_date=date(year, 1, 1))

        for holiday_key, holiday_obj, holiday_date in upcoming:
            # Determine date range for this holiday/season
            date_range = self._get_holiday_date_range(holiday_obj, holiday_date)

            # Get bookings in this range
            bookings = await self._get_bookings_in_range(date_range["start"], date_range["end"])

            if not bookings:
                logger.info(f"No bookings for {holiday_obj.name} in {year}")
                continue

            # Calculate metrics
            booking_count = len(bookings)
            total_revenue = sum(b.total_amount_cents for b in bookings) / 100
            avg_order_value = total_revenue / booking_count if booking_count > 0 else 0

            # Get top event types
            event_types = {}
            for booking in bookings:
                event_type = booking.event_type or "unknown"
                event_types[event_type] = event_types.get(event_type, 0) + 1

            top_event_types = sorted(event_types.items(), key=lambda x: x[1], reverse=True)[:3]

            # Calculate YoY growth (if previous year data exists)
            yoy_growth = await self._calculate_yoy_growth(holiday_key, year, booking_count)

            trend = {
                "season": holiday_obj.name,
                "holiday_key": holiday_key,
                "category": holiday_obj.category.value,
                "date_range": {
                    "start": date_range["start"].isoformat(),
                    "end": date_range["end"].isoformat(),
                },
                "booking_count": booking_count,
                "total_revenue": float(total_revenue),
                "avg_order_value": float(avg_order_value),
                "top_event_types": [et[0] for et in top_event_types],
                "yoy_growth": yoy_growth,
                "is_peak_season": holiday_obj.category == HolidayCategory.EVENT_SEASON,
            }

            trends.append(trend)
            logger.info(f"✅ {holiday_obj.name}: {booking_count} bookings, ${total_revenue:,.2f}")

        # Sort by revenue (highest first)
        trends.sort(key=lambda x: x["total_revenue"], reverse=True)

        # Add forecasts if requested
        if include_forecast:
            for trend in trends:
                trend["forecast_next_year"] = await self._forecast_holiday(
                    trend["holiday_key"], year + 1
                )

        return trends

    def _get_holiday_date_range(self, holiday: any, holiday_date: date) -> Dict[str, date]:
        """Get the full date range to analyze for a holiday/season."""

        # Event seasons have longer ranges
        if holiday.category == HolidayCategory.EVENT_SEASON:
            if "wedding" in holiday.name.lower():
                # Summer wedding season: June-August
                return {
                    "start": date(holiday_date.year, 6, 1),
                    "end": date(holiday_date.year, 8, 31),
                }
            elif "graduation" in holiday.name.lower():
                # Graduation season: May-June
                return {
                    "start": date(holiday_date.year, 5, 1),
                    "end": date(holiday_date.year, 6, 30),
                }
            else:
                # Generic season: 2 months
                return {
                    "start": holiday_date - timedelta(days=30),
                    "end": holiday_date + timedelta(days=30),
                }

        # Regular holidays: marketing window + few days after
        else:
            return {
                "start": holiday_date - timedelta(days=holiday.marketing_window_days),
                "end": holiday_date + timedelta(days=3),
            }

    async def _get_bookings_in_range(self, start_date: date, end_date: date) -> List:
        """Get all bookings in date range."""

        # TODO: Adjust this query based on your Booking model
        result = await self.db.execute(
            select(Booking).where(
                and_(
                    Booking.event_date >= start_date,
                    Booking.event_date <= end_date,
                    Booking.status.in_(["confirmed", "completed"]),
                )
            )
        )

        return result.scalars().all()

    async def _calculate_yoy_growth(
        self, holiday_key: str, current_year: int, current_bookings: int
    ) -> str:
        """Calculate year-over-year growth percentage."""

        try:
            # Get previous year's holiday date
            prev_year = current_year - 1
            prev_holiday_date = self.holiday_service.get_holiday_date(holiday_key, prev_year)

            if not prev_holiday_date:
                return "N/A"

            # Get previous year's bookings
            prev_holiday = self.holiday_service.holidays.get(holiday_key)
            if not prev_holiday:
                return "N/A"

            prev_date_range = self._get_holiday_date_range(prev_holiday, prev_holiday_date)
            prev_bookings = await self._get_bookings_in_range(
                prev_date_range["start"], prev_date_range["end"]
            )

            prev_count = len(prev_bookings)

            if prev_count == 0:
                return "+100%" if current_bookings > 0 else "N/A"

            growth_pct = ((current_bookings - prev_count) / prev_count) * 100

            if growth_pct > 0:
                return f"+{growth_pct:.1f}%"
            else:
                return f"{growth_pct:.1f}%"

        except Exception as e:
            logger.error(f"YoY calculation failed: {e}")
            return "N/A"

    async def _forecast_holiday(self, holiday_key: str, year: int) -> Dict:
        """Forecast bookings for next year based on historical data."""

        # Simple forecast: average of last 2 years + growth trend
        try:
            current_year = year - 1
            prev_year = year - 2

            # Get bookings for last 2 years
            current_bookings = await self._get_holiday_bookings_count(holiday_key, current_year)
            prev_bookings = await self._get_holiday_bookings_count(holiday_key, prev_year)

            if current_bookings == 0 and prev_bookings == 0:
                return {"forecast_bookings": 0, "confidence": "low"}

            # Calculate trend
            if prev_bookings > 0:
                growth_rate = (current_bookings - prev_bookings) / prev_bookings
            else:
                growth_rate = 0.1  # Default 10% growth

            # Forecast: current year bookings + growth
            forecast = int(current_bookings * (1 + growth_rate))

            # Determine confidence
            confidence = "high" if abs(growth_rate) < 0.3 else "medium"

            return {
                "forecast_bookings": forecast,
                "growth_assumption": f"{growth_rate*100:.1f}%",
                "confidence": confidence,
            }

        except Exception as e:
            logger.error(f"Forecast failed: {e}")
            return {"forecast_bookings": 0, "confidence": "low"}

    async def _get_holiday_bookings_count(self, holiday_key: str, year: int) -> int:
        """Get booking count for specific holiday in specific year."""

        holiday_date = self.holiday_service.get_holiday_date(holiday_key, year)
        if not holiday_date:
            return 0

        holiday_obj = self.holiday_service.holidays.get(holiday_key)
        if not holiday_obj:
            return 0

        date_range = self._get_holiday_date_range(holiday_obj, holiday_date)
        bookings = await self._get_bookings_in_range(date_range["start"], date_range["end"])

        return len(bookings)

    async def get_peak_seasons(self, year: Optional[int] = None) -> List[Dict]:
        """
        Identify peak booking seasons (highest revenue/bookings).

        Returns top 5 seasons ranked by revenue.
        """
        trends = await self.get_seasonal_trends(year=year)

        # Sort by revenue
        peaks = sorted(trends, key=lambda x: x["total_revenue"], reverse=True)[:5]

        return peaks

    async def get_marketing_roi(self, campaign_id: str) -> Dict:
        """
        Calculate ROI for a marketing campaign.

        Args:
            campaign_id: Campaign identifier

        Returns:
            ROI metrics:
            {
                "campaign_id": "thanksgiving_2025",
                "budget_spent": 4500.00,
                "bookings_generated": 18,
                "revenue_generated": 12400.00,
                "roi": "2.76x",
                "cost_per_booking": 250.00,
            }
        """
        # TODO: Implement campaign tracking
        # For now, return placeholder

        return {
            "campaign_id": campaign_id,
            "budget_spent": 0.0,
            "bookings_generated": 0,
            "revenue_generated": 0.0,
            "roi": "0x",
            "cost_per_booking": 0.0,
            "status": "tracking_not_implemented",
        }

    async def get_dashboard_summary(self, year: Optional[int] = None) -> Dict:
        """
        Get high-level summary for admin dashboard.

        Returns:
            Summary metrics for the year:
            {
                "total_bookings": 450,
                "total_revenue": 385000.00,
                "peak_season": "Summer Wedding Season",
                "peak_season_revenue": 125600.00,
                "yoy_growth": "+18%",
                "top_holidays": [...],
            }
        """
        if year is None:
            year = datetime.now(timezone.utc).year

        trends = await self.get_seasonal_trends(year=year)

        if not trends:
            return {
                "total_bookings": 0,
                "total_revenue": 0.0,
                "peak_season": "N/A",
                "message": "No booking data for this year",
            }

        # Aggregate metrics
        total_bookings = sum(t["booking_count"] for t in trends)
        total_revenue = sum(t["total_revenue"] for t in trends)

        # Peak season
        peak = max(trends, key=lambda x: x["total_revenue"])

        # Average YoY growth (excluding N/A)
        yoy_values = [
            float(t["yoy_growth"].rstrip("%").lstrip("+"))
            for t in trends
            if t["yoy_growth"] != "N/A"
        ]
        avg_yoy = sum(yoy_values) / len(yoy_values) if yoy_values else 0

        return {
            "year": year,
            "total_bookings": total_bookings,
            "total_revenue": total_revenue,
            "avg_order_value": total_revenue / total_bookings if total_bookings > 0 else 0,
            "peak_season": peak["season"],
            "peak_season_revenue": peak["total_revenue"],
            "peak_season_bookings": peak["booking_count"],
            "yoy_growth": f"{avg_yoy:+.1f}%",
            "top_3_holidays": [
                {
                    "name": t["season"],
                    "revenue": t["total_revenue"],
                    "bookings": t["booking_count"],
                }
                for t in trends[:3]
            ],
        }


async def get_holiday_analytics_service(db: AsyncSession) -> HolidayAnalyticsService:
    """Get holiday analytics service instance."""
    return HolidayAnalyticsService(db)
