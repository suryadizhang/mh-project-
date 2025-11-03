"""
Inactive User Detection and Re-Engagement
==========================================

Background task to identify inactive users and schedule re-engagement campaigns.

This module:
- Runs daily to check for users with no activity in the past 30 days
- Schedules automated re-engagement follow-ups
- Integrates with the FollowUpScheduler
"""

from datetime import datetime, timedelta
import logging

from api.ai.memory.postgresql_memory import AIConversation
from core.database import get_db_context
from sqlalchemy import and_, func, select

logger = logging.getLogger(__name__)


async def detect_inactive_users(
    inactive_threshold_days: int = 30, limit: int | None = None
) -> list[dict]:
    """
    Detect users who have been inactive for a specified period.

    Args:
        inactive_threshold_days: Number of days to consider a user inactive (default: 30)
        limit: Optional limit on number of users to return

    Returns:
        List of dictionaries containing user_id and last_activity_at
    """
    try:
        threshold_date = datetime.utcnow() - timedelta(days=inactive_threshold_days)

        async with get_db_context() as db:
            # Find users whose last message was before threshold
            query = (
                select(
                    AIConversation.user_id,
                    func.max(AIConversation.last_message_at).label("last_activity"),
                )
                .where(
                    and_(
                        AIConversation.user_id.isnot(None),
                        AIConversation.last_message_at < threshold_date,
                        AIConversation.is_active,
                    )
                )
                .group_by(AIConversation.user_id)
                .order_by(func.max(AIConversation.last_message_at).asc())
            )

            if limit:
                query = query.limit(limit)

            result = await db.execute(query)
            rows = result.all()

            inactive_users = [
                {"user_id": row.user_id, "last_activity_at": row.last_activity} for row in rows
            ]

            logger.info(
                f"Found {len(inactive_users)} inactive users (threshold: {inactive_threshold_days} days)"
            )
            return inactive_users

    except Exception as e:
        logger.exception(f"Failed to detect inactive users: {e}")
        return []


async def schedule_reengagement_campaigns(
    scheduler, inactive_threshold_days: int = 30, batch_size: int = 100
) -> int:
    """
    Detect inactive users and schedule re-engagement campaigns.

    Args:
        scheduler: FollowUpScheduler instance
        inactive_threshold_days: Number of days to consider a user inactive (default: 30)
        batch_size: Number of users to process in one batch (default: 100)

    Returns:
        Number of re-engagement campaigns scheduled
    """
    if not scheduler:
        logger.warning("No scheduler provided - cannot schedule re-engagement")
        return 0

    try:
        # Detect inactive users
        inactive_users = await detect_inactive_users(
            inactive_threshold_days=inactive_threshold_days, limit=batch_size
        )

        if not inactive_users:
            logger.info("No inactive users found - no re-engagement needed")
            return 0

        # Schedule re-engagement for each user
        scheduled_count = 0
        for user in inactive_users:
            try:
                job_id = await scheduler.schedule_reengagement(
                    user_id=user["user_id"],
                    last_activity=user["last_activity_at"],
                    inactive_threshold=timedelta(days=inactive_threshold_days),
                )
                if job_id:
                    scheduled_count += 1
                    logger.debug(f"Scheduled re-engagement for user {user['user_id']}: {job_id}")
            except Exception as e:
                logger.exception(
                    f"Failed to schedule re-engagement for user {user['user_id']}: {e}"
                )

        logger.info(f"Scheduled {scheduled_count}/{len(inactive_users)} re-engagement campaigns")
        return scheduled_count

    except Exception as e:
        logger.exception(f"Failed to schedule re-engagement campaigns: {e}")
        return 0


async def run_daily_reengagement_check(scheduler):
    """
    Daily task to check for inactive users and schedule re-engagement.

    This is designed to be called by APScheduler or a cron job.

    Args:
        scheduler: FollowUpScheduler instance
    """
    logger.info("Starting daily inactive user re-engagement check")

    try:
        scheduled_count = await schedule_reengagement_campaigns(
            scheduler=scheduler, inactive_threshold_days=30, batch_size=100
        )
        logger.info(f"Daily re-engagement check complete: {scheduled_count} campaigns scheduled")
    except Exception as e:
        logger.exception(f"Daily re-engagement check failed: {e}")
