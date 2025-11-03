"""
Usage Tracking for AI API Calls

Tracks token usage across all OpenAI API calls to enable:
1. Cost monitoring and alerts
2. Usage analytics
3. Optimization opportunities
4. Budget forecasting
"""

from datetime import datetime, timedelta
import logging

from api.ai.endpoints.models import AIUsage
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .pricing import calculate_cost

logger = logging.getLogger(__name__)


class UsageTracker:
    """Track AI API usage and costs"""

    def __init__(self):
        self.logger = logger

    async def record_usage(
        self,
        db: AsyncSession,
        model: str,
        input_tokens: int,
        output_tokens: int,
        conversation_id: str | None = None,
        customer_id: str | None = None,
        channel: str | None = None,
        agent_type: str | None = None,
    ):
        """
        Record token usage for an API call.

        Args:
            db: Database session
            model: Model used (e.g., "gpt-4o-mini")
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            conversation_id: Associated conversation (optional)
            customer_id: Associated customer (optional)
            channel: Channel used (web, email, voice, etc.)
            agent_type: Agent type (lead_nurturing, customer_care, etc.)

        Returns:
            AIUsage record
        """
        # Calculate cost
        cost_usd = calculate_cost(model, input_tokens, output_tokens)

        # Create usage record
        usage = AIUsage(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost_usd=cost_usd,
            conversation_id=conversation_id,
            customer_id=customer_id,
            channel=channel,
            agent_type=agent_type,
            created_at=datetime.utcnow(),
        )

        db.add(usage)
        await db.commit()
        await db.refresh(usage)

        self.logger.info(
            f"Recorded usage: {model} | "
            f"tokens={input_tokens}+{output_tokens} | "
            f"cost=${cost_usd:.4f} | "
            f"conversation={conversation_id}"
        )

        return usage

    async def get_daily_usage(self, db: AsyncSession, date: datetime | None = None) -> dict:
        """
        Get usage statistics for a specific day.

        Args:
            db: Database session
            date: Date to query (defaults to today)

        Returns:
            Dict with usage stats (total_cost, total_tokens, breakdown by model)
        """
        if date is None:
            date = datetime.utcnow()

        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        # Query usage for the day
        result = await db.execute(
            select(
                AIUsage.model,
                func.sum(AIUsage.input_tokens).label("total_input"),
                func.sum(AIUsage.output_tokens).label("total_output"),
                func.sum(AIUsage.cost_usd).label("total_cost"),
                func.count(AIUsage.id).label("call_count"),
            )
            .where(AIUsage.created_at >= start_of_day)
            .where(AIUsage.created_at < end_of_day)
            .group_by(AIUsage.model)
        )

        rows = result.all()

        # Aggregate results
        breakdown = {}
        total_cost = 0.0
        total_tokens = 0
        total_calls = 0

        for row in rows:
            model = row.model
            input_tokens = row.total_input or 0
            output_tokens = row.total_output or 0
            cost = row.total_cost or 0.0
            calls = row.call_count or 0

            breakdown[model] = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "cost_usd": round(cost, 2),
                "call_count": calls,
            }

            total_cost += cost
            total_tokens += input_tokens + output_tokens
            total_calls += calls

        return {
            "date": date.date().isoformat(),
            "total_cost": round(total_cost, 2),
            "total_tokens": total_tokens,
            "total_calls": total_calls,
            "breakdown": breakdown,
        }

    async def get_monthly_usage(
        self, db: AsyncSession, year: int | None = None, month: int | None = None
    ) -> dict:
        """
        Get usage statistics for a specific month.

        Args:
            db: Database session
            year: Year (defaults to current year)
            month: Month (defaults to current month)

        Returns:
            Dict with monthly usage stats
        """
        now = datetime.utcnow()
        if year is None:
            year = now.year
        if month is None:
            month = now.month

        # Start and end of month
        start_of_month = datetime(year, month, 1)
        if month == 12:
            end_of_month = datetime(year + 1, 1, 1)
        else:
            end_of_month = datetime(year, month + 1, 1)

        # Query usage for the month
        result = await db.execute(
            select(
                AIUsage.model,
                func.sum(AIUsage.input_tokens).label("total_input"),
                func.sum(AIUsage.output_tokens).label("total_output"),
                func.sum(AIUsage.cost_usd).label("total_cost"),
                func.count(AIUsage.id).label("call_count"),
            )
            .where(AIUsage.created_at >= start_of_month)
            .where(AIUsage.created_at < end_of_month)
            .group_by(AIUsage.model)
        )

        rows = result.all()

        # Aggregate results
        breakdown = {}
        total_cost = 0.0
        total_tokens = 0
        total_calls = 0

        for row in rows:
            model = row.model
            input_tokens = row.total_input or 0
            output_tokens = row.total_output or 0
            cost = row.total_cost or 0.0
            calls = row.call_count or 0

            breakdown[model] = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "cost_usd": round(cost, 2),
                "call_count": calls,
            }

            total_cost += cost
            total_tokens += input_tokens + output_tokens
            total_calls += calls

        # Calculate projection to end of month
        days_in_month = (end_of_month - start_of_month).days
        days_elapsed = (now - start_of_month).days + 1  # Include today
        days_remaining = days_in_month - days_elapsed

        daily_average = total_cost / days_elapsed if days_elapsed > 0 else 0
        projected_total = total_cost + (daily_average * days_remaining)

        return {
            "year": year,
            "month": month,
            "days_elapsed": days_elapsed,
            "days_remaining": days_remaining,
            "total_cost": round(total_cost, 2),
            "projected_total": round(projected_total, 2),
            "daily_average": round(daily_average, 2),
            "total_tokens": total_tokens,
            "total_calls": total_calls,
            "breakdown": breakdown,
        }

    async def get_usage_by_agent(
        self, db: AsyncSession, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> dict:
        """
        Get usage breakdown by agent type.

        Args:
            db: Database session
            start_date: Start date (defaults to 30 days ago)
            end_date: End date (defaults to now)

        Returns:
            Dict with usage by agent type
        """
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        result = await db.execute(
            select(
                AIUsage.agent_type,
                func.sum(AIUsage.cost_usd).label("total_cost"),
                func.count(AIUsage.id).label("call_count"),
            )
            .where(AIUsage.created_at >= start_date)
            .where(AIUsage.created_at < end_date)
            .where(AIUsage.agent_type.isnot(None))
            .group_by(AIUsage.agent_type)
        )

        rows = result.all()

        breakdown = {}
        for row in rows:
            agent_type = row.agent_type
            cost = row.total_cost or 0.0
            calls = row.call_count or 0

            breakdown[agent_type] = {
                "cost_usd": round(cost, 2),
                "call_count": calls,
                "avg_cost_per_call": round(cost / calls, 4) if calls > 0 else 0.0,
            }

        return {
            "start_date": start_date.date().isoformat(),
            "end_date": end_date.date().isoformat(),
            "breakdown": breakdown,
        }


# Global tracker instance
usage_tracker = UsageTracker()


def get_usage_tracker() -> UsageTracker:
    """Get the global usage tracker instance."""
    return usage_tracker
