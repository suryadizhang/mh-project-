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
        "workers.sms_tasks",
        "workers.recording_tasks",
        "workers.notification_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        "workers.escalation_tasks.*": {"queue": "escalations"},
        "workers.sms_tasks.*": {"queue": "sms"},
        "workers.recording_tasks.*": {"queue": "recordings"},
        "workers.notification_tasks.*": {"queue": "notifications"},
    },
    # Task queues
    task_queues=(
        Queue("escalations", routing_key="escalations"),
        Queue("sms", routing_key="sms"),
        Queue("recordings", routing_key="recordings"),
        Queue("notifications", routing_key="notifications"),
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
    # Send escalation metrics
    "send-escalation-metrics": {
        "task": "workers.notification_tasks.send_escalation_metrics",
        "schedule": 86400.0,  # Daily
    },
}

if __name__ == "__main__":
    celery_app.start()
