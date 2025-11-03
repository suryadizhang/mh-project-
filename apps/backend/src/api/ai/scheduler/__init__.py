"""
Smart Follow-Up Scheduler Module
================================

Automated engagement system for catering service using APScheduler.
"""

from api.ai.scheduler.follow_up_scheduler import (
    FollowUpScheduler,
    FollowUpTriggerType,
    FollowUpStatus,
    FollowUpTemplate,
    FollowUpJob,
    ScheduledFollowUp,
    FOLLOW_UP_TEMPLATES,
    schedule_followup_in_background,
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
    "FollowUpScheduler",
    "FollowUpTriggerType",
    "FollowUpStatus",
    "FollowUpTemplate",
    "FollowUpJob",
    "ScheduledFollowUp",
    "FOLLOW_UP_TEMPLATES",
    "schedule_followup_in_background",
    "get_scheduler",
    "set_scheduler",
]
