"""Newsletter analytics repository for campaign and subscriber metrics."""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

# MIGRATED: Imports moved from OLD models to NEW db.models system
from db.models.newsletter import Campaign, CampaignEvent, Subscriber

# MIGRATED: Enum imports moved from models.enums to NEW db.models system
from db.models.newsletter import CampaignChannel, CampaignEventType


class NewsletterAnalyticsRepository:
    """Repository for newsletter analytics and reporting."""

    def __init__(self, db: AsyncSession):
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy async database session
        """
        self.db = db

    async def get_unsubscribe_rate(
        self,
        start_date: datetime,
        end_date: datetime,
        channel: Optional[CampaignChannel] = None,
    ) -> dict:
        """Get unsubscribe rate for a time period.

        Args:
            start_date: Start of date range
            end_date: End of date range
            channel: Optional channel filter (EMAIL, SMS, BOTH)

        Returns:
            Dictionary with unsubscribe metrics:
            {
                "total_sent": int,
                "total_unsubscribed": int,
                "unsubscribe_rate": float,
                "period_start": datetime,
                "period_end": datetime,
                "channel": str
            }
        """
        # Get total campaigns sent in period
        sent_query = (
            select(func.count(CampaignEvent.id))
            .join(Campaign, CampaignEvent.campaign_id == Campaign.id)
            .where(
                and_(
                    CampaignEvent.type == CampaignEventType.SENT,
                    CampaignEvent.created_at >= start_date,
                    CampaignEvent.created_at <= end_date,
                )
            )
        )

        # Get total unsubscribes in period
        unsub_query = (
            select(func.count(CampaignEvent.id))
            .join(Campaign, CampaignEvent.campaign_id == Campaign.id)
            .where(
                and_(
                    CampaignEvent.type == CampaignEventType.UNSUBSCRIBED,
                    CampaignEvent.created_at >= start_date,
                    CampaignEvent.created_at <= end_date,
                )
            )
        )

        # Apply channel filter if specified
        if channel:
            sent_query = sent_query.where(Campaign.channel == channel)
            unsub_query = unsub_query.where(Campaign.channel == channel)

        # Execute queries
        total_sent = (await self.db.execute(sent_query)).scalar() or 0
        total_unsubscribed = (await self.db.execute(unsub_query)).scalar() or 0

        # Calculate rate
        unsubscribe_rate = (total_unsubscribed / total_sent * 100) if total_sent > 0 else 0.0

        return {
            "total_sent": total_sent,
            "total_unsubscribed": total_unsubscribed,
            "unsubscribe_rate": round(unsubscribe_rate, 2),
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "channel": channel.value if channel else "ALL",
        }

    async def get_campaign_performance(
        self,
        campaign_id: UUID,
    ) -> dict:
        """Get detailed performance metrics for a specific campaign.

        Args:
            campaign_id: Campaign UUID

        Returns:
            Dictionary with campaign metrics:
            {
                "campaign_id": UUID,
                "total_sent": int,
                "total_delivered": int,
                "total_opened": int,
                "total_clicked": int,
                "total_unsubscribed": int,
                "delivery_rate": float,
                "open_rate": float,
                "click_rate": float,
                "unsubscribe_rate": float
            }
        """
        # Get campaign details
        campaign = (
            (await self.db.execute(select(Campaign).where(Campaign.id == campaign_id)))
            .scalars()
            .first()
        )

        if not campaign:
            return {}

        # Count events by type
        event_counts = (
            await self.db.execute(
                select(
                    CampaignEvent.type,
                    func.count(CampaignEvent.id).label("count"),
                )
                .where(CampaignEvent.campaign_id == campaign_id)
                .group_by(CampaignEvent.type)
            )
        ).all()

        # Build metrics dictionary
        metrics = {
            CampaignEventType.SENT: 0,
            CampaignEventType.DELIVERED: 0,
            CampaignEventType.OPENED: 0,
            CampaignEventType.CLICKED: 0,
            CampaignEventType.UNSUBSCRIBED: 0,
        }

        for event_type, count in event_counts:
            metrics[event_type] = count

        total_sent = metrics[CampaignEventType.SENT]

        return {
            "campaign_id": str(campaign_id),
            "campaign_name": campaign.name,
            "channel": campaign.channel.value,
            "status": campaign.status.value,
            "sent_at": campaign.sent_at.isoformat() if campaign.sent_at else None,
            "total_sent": total_sent,
            "total_delivered": metrics[CampaignEventType.DELIVERED],
            "total_opened": metrics[CampaignEventType.OPENED],
            "total_clicked": metrics[CampaignEventType.CLICKED],
            "total_unsubscribed": metrics[CampaignEventType.UNSUBSCRIBED],
            "delivery_rate": round(
                (
                    (metrics[CampaignEventType.DELIVERED] / total_sent * 100)
                    if total_sent > 0
                    else 0.0
                ),
                2,
            ),
            "open_rate": round(
                (
                    (metrics[CampaignEventType.OPENED] / metrics[CampaignEventType.DELIVERED] * 100)
                    if metrics[CampaignEventType.DELIVERED] > 0
                    else 0.0
                ),
                2,
            ),
            "click_rate": round(
                (
                    (
                        metrics[CampaignEventType.CLICKED]
                        / metrics[CampaignEventType.DELIVERED]
                        * 100
                    )
                    if metrics[CampaignEventType.DELIVERED] > 0
                    else 0.0
                ),
                2,
            ),
            "unsubscribe_rate": round(
                (
                    (metrics[CampaignEventType.UNSUBSCRIBED] / total_sent * 100)
                    if total_sent > 0
                    else 0.0
                ),
                2,
            ),
        }

    async def get_daily_unsubscribe_trend(
        self,
        days: int = 30,
        channel: Optional[CampaignChannel] = None,
    ) -> list[dict]:
        """Get daily unsubscribe trend for the past N days.

        Args:
            days: Number of days to look back (default: 30)
            channel: Optional channel filter (EMAIL, SMS, BOTH)

        Returns:
            List of daily metrics:
            [
                {
                    "date": "2025-01-01",
                    "sent": int,
                    "unsubscribed": int,
                    "unsubscribe_rate": float
                },
                ...
            ]
        """
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Get daily sent counts
        sent_query = (
            select(
                func.date(CampaignEvent.created_at).label("date"),
                func.count(CampaignEvent.id).label("sent_count"),
            )
            .join(Campaign, CampaignEvent.campaign_id == Campaign.id)
            .where(
                and_(
                    CampaignEvent.type == CampaignEventType.SENT,
                    CampaignEvent.created_at >= start_date,
                )
            )
            .group_by(func.date(CampaignEvent.created_at))
            .order_by(func.date(CampaignEvent.created_at))
        )

        # Get daily unsubscribe counts
        unsub_query = (
            select(
                func.date(CampaignEvent.created_at).label("date"),
                func.count(CampaignEvent.id).label("unsub_count"),
            )
            .join(Campaign, CampaignEvent.campaign_id == Campaign.id)
            .where(
                and_(
                    CampaignEvent.type == CampaignEventType.UNSUBSCRIBED,
                    CampaignEvent.created_at >= start_date,
                )
            )
            .group_by(func.date(CampaignEvent.created_at))
            .order_by(func.date(CampaignEvent.created_at))
        )

        # Apply channel filter if specified
        if channel:
            sent_query = sent_query.where(Campaign.channel == channel)
            unsub_query = unsub_query.where(Campaign.channel == channel)

        # Execute queries
        sent_results = (await self.db.execute(sent_query)).all()
        unsub_results = (await self.db.execute(unsub_query)).all()

        # Build lookup dictionaries
        sent_by_date = {str(date): count for date, count in sent_results}
        unsub_by_date = {str(date): count for date, count in unsub_results}

        # Merge results
        all_dates = sorted(set(sent_by_date.keys()) | set(unsub_by_date.keys()))

        trend = []
        for date_str in all_dates:
            sent = sent_by_date.get(date_str, 0)
            unsubscribed = unsub_by_date.get(date_str, 0)

            trend.append(
                {
                    "date": date_str,
                    "sent": sent,
                    "unsubscribed": unsubscribed,
                    "unsubscribe_rate": round(
                        (unsubscribed / sent * 100) if sent > 0 else 0.0,
                        2,
                    ),
                }
            )

        return trend

    async def get_subscriber_lifetime_stats(
        self,
        subscriber_id: UUID,
    ) -> dict:
        """Get lifetime statistics for a subscriber.

        Args:
            subscriber_id: Subscriber UUID

        Returns:
            Dictionary with subscriber lifetime metrics:
            {
                "subscriber_id": UUID,
                "email": str,
                "total_campaigns_received": int,
                "total_campaigns_opened": int,
                "total_campaigns_clicked": int,
                "engagement_rate": float,
                "subscribed_date": datetime,
                "last_interaction": datetime
            }
        """
        # Get subscriber
        subscriber = (
            (await self.db.execute(select(Subscriber).where(Subscriber.id == subscriber_id)))
            .scalars()
            .first()
        )

        if not subscriber:
            return {}

        # Get event counts
        event_counts = (
            await self.db.execute(
                select(
                    CampaignEvent.type,
                    func.count(CampaignEvent.id).label("count"),
                )
                .where(CampaignEvent.subscriber_id == subscriber_id)
                .group_by(CampaignEvent.type)
            )
        ).all()

        metrics = {
            CampaignEventType.SENT: 0,
            CampaignEventType.DELIVERED: 0,
            CampaignEventType.OPENED: 0,
            CampaignEventType.CLICKED: 0,
        }

        for event_type, count in event_counts:
            if event_type in metrics:
                metrics[event_type] = count

        # Get last interaction date
        last_interaction = (
            await self.db.execute(
                select(func.max(CampaignEvent.created_at)).where(
                    and_(
                        CampaignEvent.subscriber_id == subscriber_id,
                        CampaignEvent.type.in_(
                            [
                                CampaignEventType.OPENED,
                                CampaignEventType.CLICKED,
                            ]
                        ),
                    )
                )
            )
        ).scalar()

        total_delivered = metrics[CampaignEventType.DELIVERED]
        total_engaged = metrics[CampaignEventType.OPENED] + metrics[CampaignEventType.CLICKED]

        return {
            "subscriber_id": str(subscriber_id),
            "email": subscriber.email,
            "total_campaigns_received": metrics[CampaignEventType.DELIVERED],
            "total_campaigns_opened": metrics[CampaignEventType.OPENED],
            "total_campaigns_clicked": metrics[CampaignEventType.CLICKED],
            "engagement_rate": round(
                (total_engaged / total_delivered * 100) if total_delivered > 0 else 0.0,
                2,
            ),
            "subscribed_date": subscriber.created_at.isoformat(),
            "last_interaction": last_interaction.isoformat() if last_interaction else None,
            "subscribed": subscriber.subscribed,
            "email_consent": subscriber.email_consent,
            "sms_consent": subscriber.sms_consent,
        }

    async def get_channel_comparison(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        """Compare performance across channels (EMAIL vs SMS).

        Args:
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Dictionary with channel comparison metrics:
            {
                "EMAIL": {"sent": int, "delivered": int, "unsubscribed": int, ...},
                "SMS": {"sent": int, "delivered": int, "unsubscribed": int, ...},
                "BOTH": {"sent": int, "delivered": int, "unsubscribed": int, ...}
            }
        """
        comparison = {}

        for channel in [CampaignChannel.EMAIL, CampaignChannel.SMS, CampaignChannel.BOTH]:
            # Get metrics for this channel
            metrics = await self.get_unsubscribe_rate(
                start_date=start_date,
                end_date=end_date,
                channel=channel,
            )

            comparison[channel.value] = metrics

        return comparison
