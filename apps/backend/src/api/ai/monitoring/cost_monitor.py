"""
Cost Monitoring and Alerting System

Monitors API spending and triggers alerts when thresholds are crossed.
This enables proactive scaling decisions (e.g., adding local Llama 3).
"""

import logging
import os

from sqlalchemy.ext.asyncio import AsyncSession

from .alerts import AlertManager
from .pricing import DAILY_ALERT_THRESHOLD, MONTHLY_ALERT_THRESHOLD
from .usage_tracker import UsageTracker

logger = logging.getLogger(__name__)


class CostMonitor:
    """Monitor AI API costs and trigger alerts"""

    def __init__(self):
        self.usage_tracker = UsageTracker()
        self.alert_manager = AlertManager()
        self.monthly_threshold = float(
            os.getenv("API_COST_MONTHLY_THRESHOLD", MONTHLY_ALERT_THRESHOLD)
        )
        self.daily_threshold = float(os.getenv("API_COST_DAILY_THRESHOLD", DAILY_ALERT_THRESHOLD))
        self.logger = logger

        # Track if we've already alerted this month (avoid spam)
        self._monthly_alert_sent = False
        self._last_alert_month = None

    async def check_monthly_spend(self, db: AsyncSession) -> dict:
        """
        Check monthly spend and send alert if threshold crossed.

        Returns:
            Dict with spend info and alert status
        """
        # Get current month usage
        usage = await self.usage_tracker.get_monthly_usage(db)

        current_spend = usage["total_cost"]
        projected_spend = usage["projected_total"]

        # Reset alert tracker if new month
        current_month = f"{usage['year']}-{usage['month']:02d}"
        if current_month != self._last_alert_month:
            self._monthly_alert_sent = False
            self._last_alert_month = current_month

        # Check if threshold crossed
        alert_triggered = False
        if current_spend >= self.monthly_threshold and not self._monthly_alert_sent:
            # Send alert
            await self._send_cost_alert(
                current_spend=current_spend,
                projected_spend=projected_spend,
                threshold=self.monthly_threshold,
                breakdown=usage["breakdown"],
            )
            self._monthly_alert_sent = True
            alert_triggered = True

            self.logger.warning(
                f"🔥 Monthly API spend threshold crossed: "
                f"${current_spend:.2f} >= ${self.monthly_threshold:.2f}"
            )

        return {
            "current_spend": current_spend,
            "projected_spend": projected_spend,
            "threshold": self.monthly_threshold,
            "threshold_crossed": current_spend >= self.monthly_threshold,
            "alert_sent": alert_triggered,
            "days_elapsed": usage["days_elapsed"],
            "days_remaining": usage["days_remaining"],
            "daily_average": usage["daily_average"],
        }

    async def check_daily_spend(self, db: AsyncSession) -> dict:
        """
        Check daily spend and send warning if unusually high.

        Returns:
            Dict with daily spend info
        """
        # Get today's usage
        usage = await self.usage_tracker.get_daily_usage(db)

        daily_spend = usage["total_cost"]

        # Check if daily threshold crossed (projects to >$1,500/month)
        if daily_spend >= self.daily_threshold:
            # Send warning
            await self._send_daily_warning(
                daily_spend=daily_spend,
                threshold=self.daily_threshold,
                breakdown=usage["breakdown"],
            )

            self.logger.warning(
                f"⚠️  Daily API spend high: "
                f"${daily_spend:.2f} (projects to ${daily_spend * 30:.2f}/month)"
            )

        return {
            "daily_spend": daily_spend,
            "monthly_projection": daily_spend * 30,
            "threshold": self.daily_threshold,
            "threshold_crossed": daily_spend >= self.daily_threshold,
        }

    async def _send_cost_alert(
        self, current_spend: float, projected_spend: float, threshold: float, breakdown: dict
    ):
        """Send alert when monthly threshold is crossed."""
        # Format breakdown for message
        breakdown_text = "\n".join(
            [
                f"  • {model}: ${data['cost_usd']:.2f} ({data['call_count']} calls)"
                for model, data in breakdown.items()
            ]
        )

        message = f"""
🔥 **API SPEND ALERT: Time to Add Local Llama 3**

**Current Month Spend:** ${current_spend:.2f}
**Projected End-of-Month:** ${projected_spend:.2f}
**Threshold:** ${threshold:.2f}

**Breakdown:**
{breakdown_text}

**💡 Recommended Action:**
Enable local Llama 3 (12-hour upgrade) for 75% cost savings.

**Migration Guide:**
📖 See docs/migration/MIGRATION_GUIDE_LLAMA3.md

**Expected Outcome:**
• 80% queries handled by Llama 3 (local, free)
• 20% queries fallback to OpenAI (quality ensured)
• Monthly spend: ${projected_spend:.2f} → ${projected_spend * 0.25:.2f} (75% savings)

**Next Steps:**
1. Review migration guide
2. Install Ollama (30 min)
3. Implement LlamaProvider (4 hours)
4. Shadow deploy and test (24 hours)
5. Gradual rollout (1 week)
        """.strip()

        # Send to Slack + Email
        await self.alert_manager.send_slack_alert(message)
        await self.alert_manager.send_email_alert(
            subject=f"🔥 API Spend Alert: ${current_spend:.2f}/month", body=message
        )

        self.logger.info(f"Sent cost alert: ${current_spend:.2f} >= ${threshold:.2f}")

    async def _send_daily_warning(self, daily_spend: float, threshold: float, breakdown: dict):
        """Send warning when daily spend is unusually high."""
        breakdown_text = "\n".join(
            [
                f"  • {model}: ${data['cost_usd']:.2f} ({data['call_count']} calls)"
                for model, data in breakdown.items()
            ]
        )

        message = f"""
⚠️  **Daily API Spend Warning**

**Today's Spend:** ${daily_spend:.2f}
**Monthly Projection:** ${daily_spend * 30:.2f}
**Daily Threshold:** ${threshold:.2f}

**Breakdown:**
{breakdown_text}

**Note:** High daily spend may indicate:
• Traffic spike (good! more customers)
• Inefficient prompts (check token usage)
• Repeated calls (check for loops)

If this continues, monthly spend will exceed ${self.monthly_threshold:.2f}.
Consider adding local Llama 3 for cost savings.
        """.strip()

        # Send to Slack only (not email, less urgent)
        await self.alert_manager.send_slack_alert(message)

        self.logger.info(f"Sent daily warning: ${daily_spend:.2f}")

    async def get_cost_summary(self, db: AsyncSession) -> dict:
        """
        Get comprehensive cost summary for dashboard.

        Returns:
            Dict with current costs, projections, and recommendations
        """
        monthly_usage = await self.usage_tracker.get_monthly_usage(db)
        daily_usage = await self.usage_tracker.get_daily_usage(db)

        current_spend = monthly_usage["total_cost"]
        projected_spend = monthly_usage["projected_total"]

        # Calculate if Llama 3 upgrade is recommended
        llama3_recommended = current_spend >= (self.monthly_threshold * 0.8)  # 80% of threshold
        llama3_savings = projected_spend * 0.75 if llama3_recommended else 0

        return {
            "current_month": {
                "spend": current_spend,
                "projected": projected_spend,
                "threshold": self.monthly_threshold,
                "threshold_percent": (current_spend / self.monthly_threshold) * 100,
                "days_elapsed": monthly_usage["days_elapsed"],
                "days_remaining": monthly_usage["days_remaining"],
                "daily_average": monthly_usage["daily_average"],
            },
            "today": {
                "spend": daily_usage["total_cost"],
                "calls": daily_usage["total_calls"],
                "tokens": daily_usage["total_tokens"],
            },
            "breakdown": monthly_usage["breakdown"],
            "recommendations": {
                "llama3_upgrade": {
                    "recommended": llama3_recommended,
                    "potential_savings": round(llama3_savings, 2),
                    "reason": "API costs approaching $500/month" if llama3_recommended else None,
                }
            },
        }


# Global monitor instance
cost_monitor = CostMonitor()


def get_cost_monitor() -> CostMonitor:
    """Get the global cost monitor instance."""
    return cost_monitor
