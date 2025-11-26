"""
Holiday Analytics Endpoints - Seasonal Performance Tracking
Track bookings, revenue, and marketing ROI by holiday/season
"""

import logging
from datetime import datetime, timezone
from typing import Any

from api.deps import AdminUser, get_current_admin_user, get_db
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from services.holiday_analytics_service import get_holiday_analytics_service
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter()

# ==================== Response Models ====================


class HolidayTrendResponse(BaseModel):
    """Single holiday performance metrics"""

    holiday_key: str
    holiday_name: str
    holiday_date: str
    booking_count: int
    total_revenue: float
    avg_order_value: float
    top_event_types: list[dict[str, Any]]
    yoy_growth_percentage: float | str
    previous_year_bookings: int | str
    previous_year_revenue: float | str


class SeasonalTrendsResponse(BaseModel):
    """Seasonal trends for all holidays"""

    year: int
    holidays: list[HolidayTrendResponse]
    total_bookings: int
    total_revenue: float
    avg_yoy_growth: float


class PeakSeasonResponse(BaseModel):
    """Peak season identification"""

    holiday_name: str
    holiday_key: str
    total_revenue: float
    booking_count: int
    rank: int


class DashboardSummaryResponse(BaseModel):
    """High-level dashboard summary"""

    current_year: int
    total_bookings: int
    total_revenue: float
    avg_order_value: float
    yoy_bookings_growth: float | str
    yoy_revenue_growth: float | str
    top_5_holidays: list[PeakSeasonResponse]
    upcoming_holidays: list[dict[str, Any]]


class HolidayForecastResponse(BaseModel):
    """Forecast for specific holiday"""

    holiday_key: str
    holiday_name: str
    year: int
    forecasted_bookings: int
    forecasted_revenue: float
    confidence_level: str
    based_on_years: int
    growth_trend: str
    recommendations: list[str]


# ==================== Endpoints ====================


@router.get(
    "/analytics/holidays/trends",
    response_model=SeasonalTrendsResponse,
    summary="Get seasonal trends for all holidays",
    description="Analyze booking and revenue trends for all major holidays in a given year",
)
async def get_seasonal_trends(
    year: int = Query(default=None, description="Year to analyze (default: current year)"),
    db: AsyncSession = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin_user),
) -> SeasonalTrendsResponse:
    """
    Get comprehensive seasonal trends for all holidays.

    **Metrics Included:**
    - Booking count per holiday
    - Total revenue per holiday
    - Average order value
    - Top event types (weddings, corporate, birthdays)
    - Year-over-year growth comparison
    - Previous year performance

    **Use Cases:**
    - Identify which holidays drive most revenue
    - Compare current year vs previous year
    - Plan marketing budget allocation
    - Forecast demand for upcoming holidays
    """
    try:
        target_year = year or datetime.now(timezone.utc).year
        logger.info(f"Admin {current_user.email} fetching seasonal trends for {target_year}")

        # Get analytics service
        analytics = get_holiday_analytics_service(db)

        # Get trends for all holidays
        trends = await analytics.get_seasonal_trends(year=target_year)

        if not trends:
            logger.warning(f"No booking data found for year {target_year}")
            return SeasonalTrendsResponse(
                year=target_year,
                holidays=[],
                total_bookings=0,
                total_revenue=0.0,
                avg_yoy_growth=0.0,
            )

        # Convert to response format
        holiday_responses = []
        total_bookings = 0
        total_revenue = 0.0
        yoy_growths = []

        for trend in trends:
            # Convert top event types
            top_events = [
                {"event_type": et["event_type"], "count": et["count"]} for et in trend["top_event_types"]
            ]

            holiday_responses.append(
                HolidayTrendResponse(
                    holiday_key=trend["holiday_key"],
                    holiday_name=trend["holiday_name"],
                    holiday_date=trend["holiday_date"],
                    booking_count=trend["booking_count"],
                    total_revenue=trend["total_revenue"],
                    avg_order_value=trend["avg_order_value"],
                    top_event_types=top_events,
                    yoy_growth_percentage=trend["yoy_growth_percentage"],
                    previous_year_bookings=trend["previous_year_bookings"],
                    previous_year_revenue=trend["previous_year_revenue"],
                )
            )

            total_bookings += trend["booking_count"]
            total_revenue += trend["total_revenue"]

            # Calculate average YoY growth (only numeric values)
            if isinstance(trend["yoy_growth_percentage"], (int, float)):
                yoy_growths.append(trend["yoy_growth_percentage"])

        avg_yoy_growth = sum(yoy_growths) / len(yoy_growths) if yoy_growths else 0.0

        logger.info(
            f"Found {len(holiday_responses)} holidays, {total_bookings} bookings, "
            f"${total_revenue:,.2f} revenue"
        )

        return SeasonalTrendsResponse(
            year=target_year,
            holidays=holiday_responses,
            total_bookings=total_bookings,
            total_revenue=total_revenue,
            avg_yoy_growth=avg_yoy_growth,
        )

    except Exception as e:
        logger.error(f"Error fetching seasonal trends: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch seasonal trends: {str(e)}",
        )


@router.get(
    "/analytics/holidays/summary",
    response_model=DashboardSummaryResponse,
    summary="Get high-level holiday analytics summary",
    description="Dashboard summary with key metrics and top-performing holidays",
)
async def get_holiday_summary(
    year: int = Query(default=None, description="Year to analyze (default: current year)"),
    db: AsyncSession = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin_user),
) -> DashboardSummaryResponse:
    """
    Get high-level summary for admin dashboard.

    **Perfect for:**
    - Admin dashboard overview card
    - Executive reports
    - Quick performance snapshot
    - Identifying top revenue drivers
    """
    try:
        target_year = year or datetime.now(timezone.utc).year
        logger.info(f"Admin {current_user.email} fetching holiday summary for {target_year}")

        # Get analytics service
        analytics = get_holiday_analytics_service(db)

        # Get dashboard summary
        summary = await analytics.get_dashboard_summary(year=target_year)

        # Get peak seasons
        peak_seasons = await analytics.get_peak_seasons(year=target_year, limit=5)

        # Convert peak seasons to response format
        top_5_holidays = [
            PeakSeasonResponse(
                holiday_name=season["holiday_name"],
                holiday_key=season["holiday_key"],
                total_revenue=season["total_revenue"],
                booking_count=season["booking_count"],
                rank=idx + 1,
            )
            for idx, season in enumerate(peak_seasons)
        ]

        logger.info(
            f"Summary: {summary['total_bookings']} bookings, "
            f"${summary['total_revenue']:,.2f} revenue, "
            f"{summary['yoy_bookings_growth']}% YoY growth"
        )

        return DashboardSummaryResponse(
            current_year=target_year,
            total_bookings=summary["total_bookings"],
            total_revenue=summary["total_revenue"],
            avg_order_value=summary["avg_order_value"],
            yoy_bookings_growth=summary["yoy_bookings_growth"],
            yoy_revenue_growth=summary["yoy_revenue_growth"],
            top_5_holidays=top_5_holidays,
            upcoming_holidays=summary["upcoming_holidays"],
        )

    except Exception as e:
        logger.error(f"Error fetching holiday summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch summary: {str(e)}",
        )


@router.get(
    "/analytics/holidays/peaks",
    response_model=list[PeakSeasonResponse],
    summary="Get top revenue-generating holidays",
    description="Identify which holidays drive the most revenue",
)
async def get_peak_seasons(
    year: int = Query(default=None, description="Year to analyze (default: current year)"),
    limit: int = Query(default=5, ge=1, le=20, description="How many top holidays to return"),
    db: AsyncSession = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin_user),
) -> list[PeakSeasonResponse]:
    """
    Get top revenue-generating holidays.

    **Use Cases:**
    - Identify which holidays to focus marketing on
    - Allocate resources to peak seasons
    - Plan inventory and staffing
    - Compare holiday performance
    """
    try:
        target_year = year or datetime.now(timezone.utc).year
        logger.info(f"Admin {current_user.email} fetching top {limit} holidays for {target_year}")

        # Get analytics service
        analytics = get_holiday_analytics_service(db)

        # Get peak seasons
        peak_seasons = await analytics.get_peak_seasons(year=target_year, limit=limit)

        # Convert to response format
        responses = [
            PeakSeasonResponse(
                holiday_name=season["holiday_name"],
                holiday_key=season["holiday_key"],
                total_revenue=season["total_revenue"],
                booking_count=season["booking_count"],
                rank=idx + 1,
            )
            for idx, season in enumerate(peak_seasons)
        ]

        logger.info(f"Found {len(responses)} peak seasons")

        return responses

    except Exception as e:
        logger.error(f"Error fetching peak seasons: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch peak seasons: {str(e)}",
        )


@router.get(
    "/analytics/holidays/forecast/{holiday_key}",
    response_model=HolidayForecastResponse,
    summary="Forecast bookings for upcoming holiday",
    description="AI-powered forecast based on historical trends",
)
async def forecast_holiday(
    holiday_key: str,
    year: int = Query(default=None, description="Year to forecast (default: next occurrence)"),
    db: AsyncSession = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin_user),
) -> HolidayForecastResponse:
    """
    Forecast bookings and revenue for upcoming holiday.

    **Forecasting Method:**
    - Analyzes last 2 years of data
    - Calculates average bookings and growth trend
    - Applies growth rate to forecast next year
    - Provides confidence level based on data consistency

    **Use Cases:**
    - Plan staffing for busy holidays
    - Forecast revenue for financial planning
    - Determine marketing budget allocation
    - Set realistic goals and targets
    """
    try:
        target_year = year or (datetime.now(timezone.utc).year + 1)
        logger.info(
            f"Admin {current_user.email} forecasting {holiday_key} for {target_year}"
        )

        # Get analytics service
        analytics = get_holiday_analytics_service(db)

        # Get forecast
        forecast = await analytics._forecast_holiday(holiday_key=holiday_key, year=target_year)

        if forecast["forecasted_bookings"] == 0:
            logger.warning(f"No historical data for {holiday_key}, cannot forecast")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Insufficient historical data for '{holiday_key}' to generate forecast",
            )

        # Generate recommendations
        recommendations = []

        if forecast["growth_trend"] == "strong":
            recommendations.append(
                f"Strong growth trend! Increase marketing budget by 20-30% for {target_year}"
            )
            recommendations.append("Consider adding extra staff for this holiday")
            recommendations.append("Stock up on popular menu items")
        elif forecast["growth_trend"] == "moderate":
            recommendations.append(f"Steady growth expected. Maintain current strategy")
            recommendations.append("Monitor early bookings to adjust plans")
        elif forecast["growth_trend"] == "declining":
            recommendations.append(
                "Declining trend detected. Consider promotional campaigns"
            )
            recommendations.append("Review customer feedback from previous years")
            recommendations.append("Test new menu items or special offers")
        else:
            recommendations.append("Stable demand expected. Continue current approach")

        logger.info(
            f"Forecast: {forecast['forecasted_bookings']} bookings, "
            f"${forecast['forecasted_revenue']:,.2f} revenue"
        )

        return HolidayForecastResponse(
            holiday_key=holiday_key,
            holiday_name=forecast["holiday_name"],
            year=target_year,
            forecasted_bookings=forecast["forecasted_bookings"],
            forecasted_revenue=forecast["forecasted_revenue"],
            confidence_level=forecast["confidence_level"],
            based_on_years=forecast["based_on_years"],
            growth_trend=forecast["growth_trend"],
            recommendations=recommendations,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error forecasting holiday: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to forecast: {str(e)}",
        )


@router.get(
    "/analytics/holidays/comparison",
    summary="Compare holiday performance across years",
    description="Compare specific holiday performance year-over-year",
)
async def compare_holiday_performance(
    holiday_key: str = Query(..., description="Holiday to compare"),
    start_year: int = Query(..., description="Start year"),
    end_year: int = Query(..., description="End year"),
    db: AsyncSession = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin_user),
) -> dict[str, Any]:
    """
    Compare holiday performance across multiple years.

    **Use Cases:**
    - See how Christmas 2023 vs 2024 vs 2025 performed
    - Identify long-term trends
    - Measure impact of marketing campaigns
    - Validate forecasting accuracy
    """
    try:
        logger.info(
            f"Admin {current_user.email} comparing {holiday_key} "
            f"from {start_year} to {end_year}"
        )

        # Get analytics service
        analytics = get_holiday_analytics_service(db)

        # Get trends for each year
        year_comparisons = []

        for year in range(start_year, end_year + 1):
            trends = await analytics.get_seasonal_trends(year=year)

            # Find the specific holiday
            holiday_data = next(
                (t for t in trends if t["holiday_key"] == holiday_key), None
            )

            if holiday_data:
                year_comparisons.append(
                    {
                        "year": year,
                        "bookings": holiday_data["booking_count"],
                        "revenue": holiday_data["total_revenue"],
                        "avg_order_value": holiday_data["avg_order_value"],
                        "yoy_growth": holiday_data["yoy_growth_percentage"],
                    }
                )
            else:
                year_comparisons.append(
                    {
                        "year": year,
                        "bookings": 0,
                        "revenue": 0.0,
                        "avg_order_value": 0.0,
                        "yoy_growth": "N/A",
                    }
                )

        # Calculate overall trend
        total_bookings = sum(y["bookings"] for y in year_comparisons)
        total_revenue = sum(y["revenue"] for y in year_comparisons)

        logger.info(f"Comparison complete: {len(year_comparisons)} years analyzed")

        return {
            "holiday_key": holiday_key,
            "years_analyzed": len(year_comparisons),
            "year_comparisons": year_comparisons,
            "total_bookings": total_bookings,
            "total_revenue": total_revenue,
            "avg_annual_bookings": total_bookings / len(year_comparisons),
            "avg_annual_revenue": total_revenue / len(year_comparisons),
        }

    except Exception as e:
        logger.error(f"Error comparing holiday performance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare: {str(e)}",
        )
