"""
Growth Tracker for Customer Count Monitoring

Monitors customer growth and triggers alerts when milestones are reached.
This enables proactive scaling decisions (e.g., migrating to Neo4j).

Uses lazy import pattern to avoid circular dependencies with db.models.
"""

from datetime import datetime, timezone, timedelta
import logging
import os
from typing import TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .alerts import AlertManager

# Type-only import (no runtime circular dependency)
if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class GrowthTracker:
    """Monitor customer growth and trigger alerts"""

    def __init__(self):
        self.alert_manager = AlertManager()
        self.customer_threshold = int(os.getenv("CUSTOMER_COUNT_THRESHOLD", "1000"))
        self.logger = logger

        # Track if we've already alerted (avoid spam)
        self._growth_alert_sent = False

    async def check_customer_count(self, db: AsyncSession) -> dict:
        """
        Check customer count and send alert if threshold crossed.

        Uses lazy import to avoid circular dependency with db.models.

        Returns:
            Dict with customer count and alert status
        """
        # Lazy import to avoid circular dependency (enterprise pattern)
        from db.models.core import Customer

        # Get total customer count
        result = await db.execute(select(func.count(Customer.id)))
        customer_count = result.scalar() or 0

        # Get growth rate (last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        result = await db.execute(
            select(func.count(Customer.id)).where(Customer.created_at >= thirty_days_ago)
        )
        recent_customers = result.scalar() or 0

        # Check if threshold crossed
        alert_triggered = False
        if customer_count >= self.customer_threshold and not self._growth_alert_sent:
            # Send alert
            await self._send_growth_alert(
                customer_count=customer_count,
                recent_growth=recent_customers,
                threshold=self.customer_threshold,
            )
            self._growth_alert_sent = True
            alert_triggered = True

            self.logger.warning(
                f"🔥 Customer count threshold crossed: "
                f"{customer_count} >= {self.customer_threshold}"
            )

        return {
            "customer_count": customer_count,
            "recent_growth_30d": recent_customers,
            "threshold": self.customer_threshold,
            "threshold_crossed": customer_count >= self.customer_threshold,
            "alert_sent": alert_triggered,
            "percent_to_threshold": (customer_count / self.customer_threshold) * 100,
        }

    async def _send_growth_alert(self, customer_count: int, recent_growth: int, threshold: int):
        """Send alert when customer threshold is crossed."""
        message = f"""
🔥 **CUSTOMER GROWTH ALERT: Time to Migrate to Neo4j**

**Current Customer Count:** {customer_count:,}
**Growth (Last 30 Days):** {recent_growth:,}
**Threshold:** {threshold:,}

**💡 Recommended Action:**
Migrate to Neo4j graph database (6-hour upgrade) for 10x query speedup.

**Why Neo4j?**
• 10x faster relationship queries (1,250ms → 120ms)
• Customer journey visualization
• Complex relationship queries (cross-channel insights)
• Better scalability for 10,000+ customers

**Migration Guide:**
📖 See docs/migration/MIGRATION_GUIDE_NEO4J.md

**Expected Outcome:**
• Memory queries: 1,250ms → 120ms (P95)
• New capabilities: Customer journey graphs, relationship traversal
• Zero downtime: Dual-write migration strategy (7-day safety net)

**Next Steps:**
1. Review migration guide
2. Install Neo4j (30 min)
3. Implement Neo4jMemory (2 hours)
4. Run migration script (2 hours)
5. Enable dual-write (7 days)
6. Switch to Neo4j
        """.strip()

        # Send to Slack + Email
        await self.alert_manager.send_slack_alert(message)
        await self.alert_manager.send_email_alert(
            subject=f"🔥 Customer Growth Alert: {customer_count:,} customers", body=message
        )

        self.logger.info(f"Sent growth alert: {customer_count} >= {threshold}")

    async def get_growth_summary(self, db: AsyncSession) -> dict:
        """
        Get comprehensive growth summary for dashboard.

        Uses lazy import to avoid circular dependency with db.models.

        Returns:
            Dict with customer counts, growth rates, and recommendations
        """
        # Lazy import to avoid circular dependency (enterprise pattern)
        from db.models.core import Customer

        # Lazy import to avoid circular dependency (enterprise pattern)

        # Total count
        result = await db.execute(select(func.count(Customer.id)))
        total_customers = result.scalar() or 0

        # Growth over different periods
        now = datetime.now(timezone.utc)
        periods = {
            "7d": now - timedelta(days=7),
            "30d": now - timedelta(days=30),
            "90d": now - timedelta(days=90),
        }

        growth = {}
        for period_name, start_date in periods.items():
            result = await db.execute(
                select(func.count(Customer.id)).where(Customer.created_at >= start_date)
            )
            count = result.scalar() or 0
            growth[period_name] = count

        # Calculate if Neo4j upgrade is recommended
        neo4j_recommended = total_customers >= (self.customer_threshold * 0.8)  # 80% of threshold

        return {
            "total_customers": total_customers,
            "threshold": self.customer_threshold,
            "threshold_percent": (total_customers / self.customer_threshold) * 100,
            "growth": growth,
            "daily_average_7d": round(growth["7d"] / 7, 1),
            "daily_average_30d": round(growth["30d"] / 30, 1),
            "recommendations": {
                "neo4j_upgrade": {
                    "recommended": neo4j_recommended,
                    "reason": (
                        f"Customers approaching {self.customer_threshold:,}"
                        if neo4j_recommended
                        else None
                    ),
                }
            },
        }


# Global tracker instance
growth_tracker = GrowthTracker()


def get_growth_tracker() -> GrowthTracker:
    """Get the global growth tracker instance."""
    return growth_tracker
