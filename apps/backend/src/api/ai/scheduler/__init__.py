"""
Smart Follow-Up Scheduler Module
================================

Automated engagement system for catering service using APScheduler.
"""

from api.ai.scheduler.follow_up_scheduler import (
    FOLLOW_UP_TEMPLATES,
    FollowUpJob,
    FollowUpScheduler,
    FollowUpTemplate,
    schedule_followup_in_background,
)
# Import enums and model from db.models.ai
from db.models.ai import (
    CustomerEngagementFollowUp,
    FollowUpStatus,
    FollowUpTriggerType,
)

# Global scheduler instance (initialized by application startup)
_global_scheduler: FollowUpScheduler = None


def set_scheduler(scheduler: FollowUpScheduler) -> None:
    """Set global scheduler instance (called during app startup)"""
    global _global_scheduler
    _global_scheduler = scheduler


def get_scheduler() -> FollowUpScheduler:
    """Get global scheduler instance"""
    return _global_scheduler


__all__ = [
    "CustomerEngagementFollowUp",
    "FOLLOW_UP_TEMPLATES",
    "FollowUpJob",
    "FollowUpScheduler",
    "FollowUpStatus",
    "FollowUpTemplate",
    "FollowUpTriggerType",
    "get_scheduler",
    "schedule_followup_in_background",
    "set_scheduler",
]
