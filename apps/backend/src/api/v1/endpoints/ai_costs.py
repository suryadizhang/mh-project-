"""
AI Cost Monitoring API Endpoints
Provides cost analysis, trends, and budget management for OpenAI API usage
"""
# ruff: noqa: B008 - FastAPI Depends() in function defaults is standard pattern

from datetime import datetime, timedelta
from typing import Any

from api.ai.endpoints.models import AIUsage
from core.database import get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/ai/costs", tags=["AI Cost Monitoring"])


# Cost thresholds
MONTHLY_BUDGET_USD = 100.00  # Configure based on your budget
DAILY_WARNING_THRESHOLD = 10.00
HOURLY_CRITICAL_THRESHOLD = 2.00


@router.get("/summary")
async def get_cost_summary(
    db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """
    Get comprehensive cost summary including:
    - Current month spending vs threshold
    - Today's costs
    - Model breakdown
    - Llama3 upgrade recommendations
    """

    # Get current month dates
    now = datetime.utcnow()
    month_start = now.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    next_month = month_start.replace(month=month_start.month % 12 + 1, day=1)
    days_in_month = (next_month - timedelta(days=1)).day
    days_elapsed = (now - month_start).days + 1
    days_remaining = days_in_month - days_elapsed

    # Query current month costs
    month_query = select(
        func.sum(AIUsage.cost_usd).label("total_cost"),
        func.count(AIUsage.id).label("total_calls"),
        func.sum(AIUsage.total_tokens).label("total_tokens")
    ).where(
        AIUsage.created_at >= month_start
    )

    month_result = await db.execute(month_query)
    month_data = month_result.first()

    current_month_spend = float(month_data.total_cost or 0)
    if days_elapsed > 0:
        daily_average = current_month_spend / days_elapsed
    else:
        daily_average = 0
    projected_spend = daily_average * days_in_month

    # Today's costs
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    today_query = select(
        func.sum(AIUsage.cost_usd).label("total_cost"),
        func.count(AIUsage.id).label("total_calls"),
        func.sum(AIUsage.total_tokens).label("total_tokens")
    ).where(
        AIUsage.created_at >= today_start
    )


    today_result = await db.execute(today_query)
    today_data = today_result.first()

    # Model breakdown
    breakdown_query = select(
        AIUsage.model_used,
        func.sum(AIUsage.input_tokens).label("input_tokens"),
        func.sum(AIUsage.output_tokens).label("output_tokens"),
        func.sum(AIUsage.total_tokens).label("total_tokens"),
        func.sum(AIUsage.cost_usd).label("cost_usd"),
        func.count(AIUsage.id).label("call_count")
    ).where(
        AIUsage.created_at >= month_start
    ).group_by(AIUsage.model_used)

    breakdown_result = await db.execute(breakdown_query)
    breakdown_data = breakdown_result.all()

    breakdown_dict = {}
    for row in breakdown_data:
        breakdown_dict[row.model_used or "unknown"] = {
            "input_tokens": int(row.input_tokens or 0),
            "output_tokens": int(row.output_tokens or 0),
            "total_tokens": int(row.total_tokens or 0),
            "cost_usd": float(row.cost_usd or 0),
            "call_count": int(row.call_count or 0)
        }

    # Llama3 upgrade recommendation
    # If monthly cost > $50 and mostly using GPT-4, recommend local
    recommend_llama3 = False
    potential_savings = 0
    reason = None

    if current_month_spend > 50:
        gpt4_cost = sum(
            data["cost_usd"]
            for model, data in breakdown_dict.items()
            if "gpt-4" in model.lower()
        )
        if gpt4_cost > current_month_spend * 0.5:  # >50% is GPT-4
            recommend_llama3 = True
            potential_savings = gpt4_cost * 0.6  # 60% savings
            reason = (
                f"You're spending ${gpt4_cost:.2f}/month on GPT-4. "
                f"Shadow Learning could handle 60% of queries."
            )

    return {
        "current_month": {
            "spend": current_month_spend,
            "projected": projected_spend,
            "threshold": MONTHLY_BUDGET_USD,
            "threshold_percent": (
                (current_month_spend / MONTHLY_BUDGET_USD) * 100
            ),
            "days_elapsed": days_elapsed,
            "days_remaining": days_remaining,
            "daily_average": daily_average
        },
        "today": {
            "spend": float(today_data.total_cost or 0),
            "calls": int(today_data.total_calls or 0),
            "tokens": int(today_data.total_tokens or 0)
        },
        "breakdown": breakdown_dict,
        "recommendations": {
            "llama3_upgrade": {
                "recommended": recommend_llama3,
                "potential_savings": potential_savings,
                "reason": reason
            }
        }
    }


@router.get("/trend")
async def get_cost_trend(
    days: int = Query(default=30, ge=1, le=90),
    db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """
    Get daily cost trend for the specified number of days
    """

    now = datetime.utcnow()
    start_date = now - timedelta(days=days)

    # Query daily aggregates
    daily_query = select(
        func.date(AIUsage.created_at).label("date"),
        func.sum(AIUsage.cost_usd).label("total_cost"),
        func.count(AIUsage.id).label("total_calls"),
        func.sum(AIUsage.total_tokens).label("total_tokens")
    ).where(
        AIUsage.created_at >= start_date
    ).group_by(
        func.date(AIUsage.created_at)
    ).order_by(
        func.date(AIUsage.created_at)
    )

    result = await db.execute(daily_query)
    daily_data = result.all()

    dates = []
    costs = []
    calls = []
    avg_cost_per_call = []

    for row in daily_data:
        dates.append(row.date.isoformat())
        cost = float(row.total_cost or 0)
        call_count = int(row.total_calls or 0)

        costs.append(cost)
        calls.append(call_count)
        if call_count > 0:
            avg_cost_per_call.append(cost / call_count)
        else:
            avg_cost_per_call.append(0)

    return {
        "dates": dates,
        "costs": costs,
        "calls": calls,
        "average_cost_per_call": avg_cost_per_call
    }


@router.get("/hourly")
async def get_hourly_costs(
    date: str | None = Query(
        default=None,
        description="Date in YYYY-MM-DD format (defaults to today)"
    ),
    db: AsyncSession = Depends(get_db)
) -> list[dict[str, Any]]:
    """
    Get hourly cost breakdown for a specific date
    """

    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use YYYY-MM-DD"
            ) from None
    else:
        target_date = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    next_day = target_date + timedelta(days=1)

    # Query hourly aggregates
    hourly_query = select(
        func.extract('hour', AIUsage.created_at).label("hour"),
        func.sum(AIUsage.cost_usd).label("total_cost"),
        func.count(AIUsage.id).label("total_calls")
    ).where(
        and_(
            AIUsage.created_at >= target_date,
            AIUsage.created_at < next_day
        )
    ).group_by(
        func.extract('hour', AIUsage.created_at)
    ).order_by(
        func.extract('hour', AIUsage.created_at)
    )

    result = await db.execute(hourly_query)
    hourly_data = result.all()

    hourly_breakdown = []
    for row in hourly_data:
        hourly_breakdown.append({
            "hour": f"{int(row.hour):02d}:00",
            "cost": float(row.total_cost or 0),
            "calls": int(row.total_calls or 0)
        })

    return hourly_breakdown


@router.get("/alerts")
async def check_cost_alerts(
    db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """
    Check if any cost thresholds have been exceeded
    Returns alerts that should trigger notifications
    """

    now = datetime.utcnow()
    alerts = []

    # Check hourly costs
    hour_ago = now - timedelta(hours=1)

    hourly_query = select(
        func.sum(AIUsage.cost_usd).label("total_cost")
    ).where(
        AIUsage.created_at >= hour_ago
    )

    hourly_result = await db.execute(hourly_query)
    hourly_cost = float(hourly_result.scalar() or 0)

    if hourly_cost > HOURLY_CRITICAL_THRESHOLD:
        msg = (
            f"Hourly cost of ${hourly_cost:.2f} exceeds "
            f"critical threshold of ${HOURLY_CRITICAL_THRESHOLD}"
        )
        alerts.append({
            "severity": "critical",
            "type": "hourly_threshold",
            "message": msg,
            "cost": hourly_cost,
            "threshold": HOURLY_CRITICAL_THRESHOLD
        })

    # Check daily costs
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    daily_query = select(
        func.sum(AIUsage.cost_usd).label("total_cost")
    ).where(
        AIUsage.created_at >= today_start
    )

    daily_result = await db.execute(daily_query)
    daily_cost = float(daily_result.scalar() or 0)

    if daily_cost > DAILY_WARNING_THRESHOLD:
        msg = (
            f"Daily cost of ${daily_cost:.2f} exceeds "
            f"warning threshold of ${DAILY_WARNING_THRESHOLD}"
        )
        alerts.append({
            "severity": "warning",
            "type": "daily_threshold",
            "message": msg,
            "cost": daily_cost,
            "threshold": DAILY_WARNING_THRESHOLD
        })

    # Check monthly budget
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    monthly_query = select(
        func.sum(AIUsage.cost_usd).label("total_cost")
    ).where(
        AIUsage.created_at >= month_start
    )

    monthly_result = await db.execute(monthly_query)
    monthly_cost = float(monthly_result.scalar() or 0)

    if monthly_cost > MONTHLY_BUDGET_USD:
        msg = (
            f"Monthly cost of ${monthly_cost:.2f} exceeds "
            f"budget of ${MONTHLY_BUDGET_USD}"
        )
        alerts.append({
            "severity": "critical",
            "type": "monthly_budget",
            "message": msg,
            "cost": monthly_cost,
            "threshold": MONTHLY_BUDGET_USD
        })
    elif monthly_cost > MONTHLY_BUDGET_USD * 0.8:
        msg = (
            f"Monthly cost of ${monthly_cost:.2f} is approaching "
            f"budget of ${MONTHLY_BUDGET_USD}"
        )
        alerts.append({
            "severity": "warning",
            "type": "monthly_budget",
            "message": msg,
            "cost": monthly_cost,
            "threshold": MONTHLY_BUDGET_USD
        })

    return {
        "has_alerts": len(alerts) > 0,
        "alert_count": len(alerts),
        "alerts": alerts,
        "checked_at": now.isoformat()
    }


@router.get("/top-expensive")
async def get_top_expensive_queries(
    limit: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
) -> list[dict[str, Any]]:
    """
    Get the most expensive API calls
    Useful for identifying optimization opportunities
    """

    query = select(AIUsage).order_by(desc(AIUsage.cost_usd)).limit(limit)

    result = await db.execute(query)
    expensive_queries = result.scalars().all()

    return [
        {
            "id": str(usage.id),
            "created_at": usage.created_at.isoformat(),
            "model": usage.model_used,
            "cost_usd": float(usage.cost_usd or 0),
            "total_tokens": int(usage.total_tokens or 0),
            "input_tokens": int(usage.input_tokens or 0),
            "output_tokens": int(usage.output_tokens or 0),
            "response_time_ms": int(usage.response_time_ms or 0)
        }
        for usage in expensive_queries
    ]


@router.post("/set-budget")
async def set_monthly_budget(
    budget_usd: float = Query(
        ...,
        gt=0,
        description="Monthly budget in USD"
    ),
) -> dict[str, Any]:
    """
    Update the monthly budget threshold
    """

    global MONTHLY_BUDGET_USD  # noqa: PLW0603
    MONTHLY_BUDGET_USD = budget_usd

    return {
        "success": True,
        "new_budget": budget_usd,
        "message": f"Monthly budget updated to ${budget_usd}"
    }
