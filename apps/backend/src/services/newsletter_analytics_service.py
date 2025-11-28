"""Newsletter analytics service for campaign and subscriber metrics."""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from core.cache import CacheService, cached

# MIGRATED: Imports moved from OLD models to NEW db.models system
# TODO: Manual migration needed for: SMSDeliveryEvent
# from models import SMSDeliveryEvent
# MIGRATED: Enum imports moved from models.enums to NEW db.models system
from db.models.newsletter import CampaignChannel

# TODO: Manual migration needed for enums: SMSDeliveryStatus
# from models.enums import SMSDeliveryStatus
from repositories.newsletter_analytics import NewsletterAnalyticsRepository


class NewsletterAnalyticsService:
    """
    Service layer for newsletter analytics and reporting.

    Features:
    - Dashboard metrics with caching (5-minute TTL)
    - Campaign performance tracking
    - Subscriber lifetime stats
    - TCPA/CAN-SPAM compliance monitoring
    - US compliance-focused reporting
    """

    def __init__(self, db: AsyncSession, cache: Optional[CacheService] = None):
        """Initialize service with database session and optional cache.

        Args:
            db: SQLAlchemy async database session
            cache: Optional Redis cache service for performance optimization
        """
        self.db = db
        self.cache = cache
        self.repository = NewsletterAnalyticsRepository(db)

    @cached(ttl=300, key_prefix="newsletter:dashboard")
    async def get_dashboard_overview(
        self,
        days: int = 30,
    ) -> dict:
        """Get comprehensive dashboard overview for the past N days.

        Args:
            days: Number of days to look back (default: 30)

        Returns:
            Dictionary with dashboard metrics:
            {
                "period": {"start": datetime, "end": datetime, "days": int},
                "overall": {...unsubscribe metrics...},
                "sms": {...SMS-specific metrics...},
                "email": {...email-specific metrics...},
                "trend": [...daily trend data...],
                "channel_comparison": {...channel comparison...}
            }
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # Get overall metrics
        overall_metrics = await self.repository.get_unsubscribe_rate(
            start_date=start_date,
            end_date=end_date,
        )

        # Get SMS-specific metrics (primary newsletter channel)
        sms_metrics = await self.repository.get_unsubscribe_rate(
            start_date=start_date,
            end_date=end_date,
            channel=CampaignChannel.SMS,
        )

        # Get email-specific metrics (admin/transactional only)
        email_metrics = await self.repository.get_unsubscribe_rate(
            start_date=start_date,
            end_date=end_date,
            channel=CampaignChannel.EMAIL,
        )

        # Get daily trend
        trend = await self.repository.get_daily_unsubscribe_trend(
            days=days,
        )

        # Get channel comparison
        channel_comparison = await self.repository.get_channel_comparison(
            start_date=start_date,
            end_date=end_date,
        )

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days,
            },
            "overall": overall_metrics,
            "sms": sms_metrics,
            "email": email_metrics,
            "trend": trend,
            "channel_comparison": channel_comparison,
            "compliance_status": self._check_compliance_status(
                sms_metrics,
                email_metrics,
            ),
        }

    @cached(ttl=600, key_prefix="newsletter:campaign")
    async def get_campaign_details(
        self,
        campaign_id: UUID,
    ) -> dict:
        """Get detailed performance metrics for a specific campaign.

        Cached for 10 minutes for performance.

        Args:
            campaign_id: Campaign UUID

        Returns:
            Dictionary with campaign performance metrics
        """
        return await self.repository.get_campaign_performance(campaign_id)

    @cached(ttl=900, key_prefix="newsletter:subscriber")
    async def get_subscriber_analytics(
        self,
        subscriber_id: UUID,
    ) -> dict:
        """Get lifetime analytics for a specific subscriber.

        Cached for 15 minutes for performance.

        Args:
            subscriber_id: Subscriber UUID

        Returns:
            Dictionary with subscriber lifetime metrics
        """
        return await self.repository.get_subscriber_lifetime_stats(subscriber_id)

    @cached(ttl=300, key_prefix="newsletter:trend")
    async def get_unsubscribe_trend(
        self,
        days: int = 30,
        channel: Optional[CampaignChannel] = None,
    ) -> list[dict]:
        """Get unsubscribe trend for the past N days.

        Args:
            days: Number of days to look back (default: 30)
            channel: Optional channel filter (EMAIL, SMS, BOTH)

        Returns:
            List of daily unsubscribe metrics
        """
        return await self.repository.get_daily_unsubscribe_trend(
            days=days,
            channel=channel,
        )

    @cached(ttl=3600, key_prefix="newsletter:compliance")
    async def get_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        """Get comprehensive compliance report for a time period.

        Cached for 1 hour for performance (compliance data changes slowly).

        Args:
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Dictionary with compliance metrics and status:
            {
                "period": {"start": datetime, "end": datetime},
                "sms_compliance": {
                    "tcpa_compliant": bool,
                    "unsubscribe_rate": float,
                    "stop_instructions_included": bool
                },
                "email_compliance": {
                    "can_spam_compliant": bool,
                    "unsubscribe_rate": float,
                    "list_unsubscribe_headers": bool
                },
                "recommendations": [...]
            }
        """
        # Get SMS metrics (TCPA compliance)
        sms_metrics = await self.repository.get_unsubscribe_rate(
            start_date=start_date,
            end_date=end_date,
            channel=CampaignChannel.SMS,
        )

        # Get email metrics (CAN-SPAM compliance)
        email_metrics = await self.repository.get_unsubscribe_rate(
            start_date=start_date,
            end_date=end_date,
            channel=CampaignChannel.EMAIL,
        )

        # Check compliance thresholds
        # Industry benchmark: <0.5% unsubscribe rate is excellent
        # 0.5-1% is good, >1% needs attention
        sms_compliant = sms_metrics["unsubscribe_rate"] < 1.0
        email_compliant = email_metrics["unsubscribe_rate"] < 1.0

        recommendations = []

        if not sms_compliant:
            recommendations.append(
                {
                    "severity": "high",
                    "channel": "SMS",
                    "message": f"SMS unsubscribe rate ({sms_metrics['unsubscribe_rate']}%) exceeds 1%. Review message content and targeting.",
                }
            )

        if not email_compliant:
            recommendations.append(
                {
                    "severity": "high",
                    "channel": "EMAIL",
                    "message": f"Email unsubscribe rate ({email_metrics['unsubscribe_rate']}%) exceeds 1%. Review email content and frequency.",
                }
            )

        # Add positive recommendations
        if sms_compliant and email_compliant:
            recommendations.append(
                {
                    "severity": "info",
                    "channel": "ALL",
                    "message": "All channels maintaining healthy unsubscribe rates. Continue current practices.",
                }
            )

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "sms_compliance": {
                "tcpa_compliant": sms_compliant,
                "unsubscribe_rate": sms_metrics["unsubscribe_rate"],
                "total_sent": sms_metrics["total_sent"],
                "total_unsubscribed": sms_metrics["total_unsubscribed"],
                "stop_instructions_included": True,  # Enforced by NewsletterSMSService
            },
            "email_compliance": {
                "can_spam_compliant": email_compliant,
                "unsubscribe_rate": email_metrics["unsubscribe_rate"],
                "total_sent": email_metrics["total_sent"],
                "total_unsubscribed": email_metrics["total_unsubscribed"],
                "list_unsubscribe_headers": True,  # Enforced by IONOSEmailProvider
            },
            "overall_health": (
                "healthy" if (sms_compliant and email_compliant) else "needs_attention"
            ),
            "recommendations": recommendations,
        }

    def _check_compliance_status(
        self,
        sms_metrics: dict,
        email_metrics: dict,
    ) -> dict:
        """Check compliance status based on metrics.

        Args:
            sms_metrics: SMS unsubscribe metrics
            email_metrics: Email unsubscribe metrics

        Returns:
            Dictionary with compliance status:
            {
                "overall": "healthy" | "needs_attention" | "critical",
                "sms_status": "healthy" | "warning" | "critical",
                "email_status": "healthy" | "warning" | "critical",
                "alerts": [...]
            }
        """
        alerts = []

        # Check SMS compliance (TCPA)
        sms_rate = sms_metrics["unsubscribe_rate"]
        if sms_rate < 0.5:
            sms_status = "healthy"
        elif sms_rate < 1.0:
            sms_status = "warning"
            alerts.append(
                {
                    "channel": "SMS",
                    "message": f"SMS unsubscribe rate ({sms_rate}%) approaching 1% threshold",
                }
            )
        else:
            sms_status = "critical"
            alerts.append(
                {
                    "channel": "SMS",
                    "message": f"SMS unsubscribe rate ({sms_rate}%) exceeds 1% - immediate review needed",
                }
            )

        # Check email compliance (CAN-SPAM)
        email_rate = email_metrics["unsubscribe_rate"]
        if email_rate < 0.5:
            email_status = "healthy"
        elif email_rate < 1.0:
            email_status = "warning"
            alerts.append(
                {
                    "channel": "EMAIL",
                    "message": f"Email unsubscribe rate ({email_rate}%) approaching 1% threshold",
                }
            )
        else:
            email_status = "critical"
            alerts.append(
                {
                    "channel": "EMAIL",
                    "message": f"Email unsubscribe rate ({email_rate}%) exceeds 1% - immediate review needed",
                }
            )

        # Overall status (worst of both)
        if sms_status == "critical" or email_status == "critical":
            overall = "critical"
        elif sms_status == "warning" or email_status == "warning":
            overall = "needs_attention"
        else:
            overall = "healthy"

        return {
            "overall": overall,
            "sms_status": sms_status,
            "email_status": email_status,
            "alerts": alerts,
        }
