"""
Campaign Metrics Worker
Periodic tasks for updating campaign cached metrics
"""

from workers.celery_config import celery_app
from core.database import get_db_session
from models import Campaign, CampaignEvent
from models.enums import CampaignStatus, CampaignEventType
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@celery_app.task(
    name="workers.campaign_metrics_tasks.update_active_campaign_metrics"
)
def update_active_campaign_metrics():
    """
    Update cached metrics for all active campaigns

    Runs every 5 minutes to keep dashboard analytics fresh.
    Only processes campaigns that:
    - Are in ACTIVE or SCHEDULED status
    - Have been updated more than 5 minutes ago (to avoid duplicate work)

    This improves dashboard performance by precomputing expensive aggregations.
    """
    db = next(get_db_session())

    try:
        # Find campaigns that need metrics refresh
        cutoff_time = datetime.utcnow() - timedelta(minutes=5)

        campaigns = (
            db.query(Campaign)
            .filter(
                Campaign.status.in_(
                    [CampaignStatus.ACTIVE, CampaignStatus.SCHEDULED]
                ),
                Campaign.last_metrics_updated < cutoff_time,
            )
            .all()
        )

        if not campaigns:
            logger.info("No campaigns need metrics update")
            return {"status": "success", "updated_count": 0}

        updated_count = 0
        error_count = 0

        for campaign in campaigns:
            try:
                # Use the Campaign model's method to recalculate metrics
                campaign.update_cached_metrics(db)
                updated_count += 1

                logger.info(
                    f"Updated metrics for campaign {campaign.id} ({campaign.name}): "
                    f"sent={campaign.total_sent}, delivered={campaign.total_delivered}, "
                    f"delivery_rate={campaign.delivery_rate_cached:.2%}"
                )

            except Exception as e:
                error_count += 1
                logger.error(
                    f"Failed to update metrics for campaign {campaign.id}: {str(e)}"
                )
                # Continue processing other campaigns
                continue

        db.commit()

        logger.info(
            f"Campaign metrics update complete: {updated_count} updated, {error_count} errors"
        )

        return {
            "status": "success",
            "updated_count": updated_count,
            "error_count": error_count,
            "total_campaigns": len(campaigns),
        }

    except Exception as e:
        logger.error(f"Failed to update campaign metrics: {str(e)}")
        db.rollback()
        raise

    finally:
        db.close()


@celery_app.task(
    name="workers.campaign_metrics_tasks.update_single_campaign_metrics"
)
def update_single_campaign_metrics(campaign_id: str):
    """
    Update cached metrics for a single campaign

    Can be called on-demand when:
    - Campaign is completed
    - Manual refresh requested from admin UI
    - Large batch of SMS messages delivered

    Args:
        campaign_id: UUID of the campaign to update
    """
    db = next(get_db_session())

    try:
        campaign = (
            db.query(Campaign).filter(Campaign.id == campaign_id).first()
        )

        if not campaign:
            logger.error(f"Campaign {campaign_id} not found")
            return {"status": "error", "message": "Campaign not found"}

        # Update cached metrics
        campaign.update_cached_metrics(db)
        db.commit()

        logger.info(
            f"Updated metrics for campaign {campaign.id} ({campaign.name}): "
            f"sent={campaign.total_sent}, delivered={campaign.total_delivered}, "
            f"delivery_rate={campaign.delivery_rate_cached:.2%}"
        )

        return {
            "status": "success",
            "campaign_id": str(campaign_id),
            "total_sent": campaign.total_sent,
            "total_delivered": campaign.total_delivered,
            "delivery_rate": campaign.delivery_rate_cached,
        }

    except Exception as e:
        logger.error(
            f"Failed to update metrics for campaign {campaign_id}: {str(e)}"
        )
        db.rollback()
        raise

    finally:
        db.close()


@celery_app.task(
    name="workers.campaign_metrics_tasks.cleanup_completed_campaign_metrics"
)
def cleanup_completed_campaign_metrics():
    """
    Final metrics update for completed campaigns

    Runs hourly to ensure all COMPLETED campaigns have final accurate metrics.
    This is important for historical reporting and analytics.
    """
    db = next(get_db_session())

    try:
        # Find completed campaigns that haven't been updated in the last hour
        cutoff_time = datetime.utcnow() - timedelta(hours=1)

        campaigns = (
            db.query(Campaign)
            .filter(
                Campaign.status == CampaignStatus.COMPLETED,
                Campaign.last_metrics_updated < cutoff_time,
            )
            .all()
        )

        if not campaigns:
            logger.info("No completed campaigns need final metrics update")
            return {"status": "success", "updated_count": 0}

        updated_count = 0

        for campaign in campaigns:
            try:
                campaign.update_cached_metrics(db)
                updated_count += 1

                logger.info(
                    f"Final metrics update for completed campaign {campaign.id}: "
                    f"sent={campaign.total_sent}, delivered={campaign.total_delivered}"
                )

            except Exception as e:
                logger.error(
                    f"Failed final metrics update for campaign {campaign.id}: {str(e)}"
                )
                continue

        db.commit()

        logger.info(
            f"Completed campaign metrics update: {updated_count} campaigns"
        )

        return {"status": "success", "updated_count": updated_count}

    except Exception as e:
        logger.error(f"Failed to update completed campaign metrics: {str(e)}")
        db.rollback()
        raise

    finally:
        db.close()
