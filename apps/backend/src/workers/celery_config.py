"""
Celery Configuration
Background task processing for escalations, SMS, and call recordings
"""

from celery import Celery
from kombu import Queue
import os

# Redis connection
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

# Create Celery app
celery_app = Celery(
    "myhibachi_workers",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "workers.escalation_tasks",
        "workers.recording_tasks",
        "workers.review_worker",
        "workers.outbox_processors",
        "workers.monitoring_tasks",  # Added monitoring tasks
        "workers.campaign_metrics_tasks",  # Added campaign metrics tasks
        "workers.slot_hold_tasks",  # Slot hold auto-cancel tasks (Batch 1)
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        "workers.escalation_tasks.*": {"queue": "escalations"},
        "workers.recording_tasks.*": {"queue": "recordings"},
        "workers.review_worker.*": {"queue": "reviews"},
        "workers.outbox_processors.*": {"queue": "outbox"},
        "monitoring.*": {"queue": "monitoring"},  # Added monitoring queue
        "workers.campaign_metrics_tasks.*": {"queue": "campaigns"},  # Added campaign metrics queue
        "workers.slot_hold_tasks.*": {"queue": "holds"},  # Slot hold auto-cancel (Batch 1)
        "slot_holds.*": {"queue": "holds"},  # Slot hold tasks by name prefix
    },
    # Task queues
    task_queues=(
        Queue("escalations", routing_key="escalations"),
        Queue("recordings", routing_key="recordings"),
        Queue("reviews", routing_key="reviews"),
        Queue("outbox", routing_key="outbox"),
        Queue("monitoring", routing_key="monitoring"),  # Added monitoring queue
        Queue("campaigns", routing_key="campaigns"),  # Added campaigns queue
        Queue("holds", routing_key="holds"),  # Slot hold auto-cancel queue (Batch 1)
        Queue("default", routing_key="default"),
    ),
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task execution
    task_acks_late=True,  # Acknowledge after task completion
    task_reject_on_worker_lost=True,  # Reject if worker dies
    worker_prefetch_multiplier=1,  # Process one task at a time per worker
    # Retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    # Result backend
    result_expires=3600,  # 1 hour
    result_persistent=True,
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    # Flower monitoring configuration
    flower_basic_auth=[
        os.getenv("FLOWER_ADMIN_USERNAME", "admin")
        + ":"
        + os.getenv("FLOWER_ADMIN_PASSWORD", "admin123")
    ],
    flower_port=int(os.getenv("FLOWER_PORT", "5555")),
    flower_url_prefix=os.getenv("FLOWER_URL_PREFIX", ""),
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    # Cleanup old recordings based on retention policy
    "cleanup-expired-recordings": {
        "task": "workers.recording_tasks.cleanup_expired_recordings",
        "schedule": 3600.0,  # Every hour
    },
    # Retry failed escalations
    "retry-failed-escalations": {
        "task": "workers.escalation_tasks.retry_failed_escalations",
        "schedule": 300.0,  # Every 5 minutes
    },
    # Monitoring tasks (backup safety net)
    "collect-metrics-backup": {
        "task": "monitoring.collect_metrics",
        "schedule": 300.0,  # Every 5 minutes (backup for push-based)
    },
    "verify-rules": {
        "task": "monitoring.verify_rules",
        "schedule": 120.0,  # Every 2 minutes
    },
    "monitoring-health-check": {
        "task": "monitoring.health_check",
        "schedule": 600.0,  # Every 10 minutes
    },
    "cleanup-monitoring-data": {
        "task": "monitoring.cleanup_old_data",
        "schedule": 3600.0,  # Every hour
    },
    "aggregate-monitoring-stats": {
        "task": "monitoring.aggregate_statistics",
        "schedule": 3600.0,  # Every hour
    },
    # Campaign metrics updates
    "update-active-campaign-metrics": {
        "task": "workers.campaign_metrics_tasks.update_active_campaign_metrics",
        "schedule": 300.0,  # Every 5 minutes
    },
    "cleanup-completed-campaign-metrics": {
        "task": "workers.campaign_metrics_tasks.cleanup_completed_campaign_metrics",
        "schedule": 3600.0,  # Every hour
    },
    # ============================================================
    # Slot Hold Auto-Cancel System (Batch 1 - Legal Protection)
    # 2 hours to sign agreement, 4 hours to pay deposit after signing
    # 1 hour warning before each deadline
    # ============================================================
    "check-signing-warnings": {
        "task": "slot_holds.check_signing_warnings",
        "schedule": 300.0,  # Every 5 minutes
    },
    "check-payment-warnings": {
        "task": "slot_holds.check_payment_warnings",
        "schedule": 300.0,  # Every 5 minutes
    },
    "expire-unsigned-holds": {
        "task": "slot_holds.expire_unsigned_holds",
        "schedule": 300.0,  # Every 5 minutes
    },
    "expire-unpaid-holds": {
        "task": "slot_holds.expire_unpaid_holds",
        "schedule": 300.0,  # Every 5 minutes
    },
}

if __name__ == "__main__":
    celery_app.start()
