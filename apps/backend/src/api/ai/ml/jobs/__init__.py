"""
Scheduled Jobs for AI Self-Learning Pipeline

Jobs:
1. KB Refresh - Weekly KB embedding updates (Sunday 2 AM)
2. Training Collector - Nightly training data collection (Daily 1 AM)
3. Performance Reporter - Weekly performance report (Monday 9 AM)

Author: MyHibachi Development Team
Created: October 31, 2025
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

logger = logging.getLogger(__name__)

# Initialize scheduler (singleton)
scheduler = AsyncIOScheduler()


def start_scheduler():
    """Start the APScheduler for background jobs"""
    if not scheduler.running:
        scheduler.start()
        logger.info("✅ APScheduler started for AI self-learning jobs")


def stop_scheduler():
    """Stop the APScheduler"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("🛑 APScheduler stopped")
