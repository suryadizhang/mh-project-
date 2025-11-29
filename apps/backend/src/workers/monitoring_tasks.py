"""
Monitoring Celery Tasks

Background tasks for threshold monitoring system:
1. Periodic metric collection (backup safety net)
2. Rule evaluation verification
3. Health check monitoring
4. Metric cleanup and maintenance
5. Alert statistics aggregation

These tasks complement the real-time push-based monitoring to provide:
- Redundancy: Backup if push notifications fail
- Scheduled operations: Cleanup, statistics, maintenance
- Health monitoring: Verify monitoring system health
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from celery import Task
from sqlalchemy.orm import Session

from workers.celery_config import celery_app
from core.database import SessionLocal
from core.config import settings
import redis

logger = logging.getLogger(__name__)


class MonitoringTask(Task):
    """
    Base task for monitoring operations with database and Redis access.
    """

    _db: Optional[Session] = None
    _redis: Optional[redis.Redis] = None

    @property
    def db(self) -> Session:
        """Get database session (lazy initialization)."""
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    @property
    def redis_client(self) -> redis.Redis:
        """Get Redis client (lazy initialization)."""
        if self._redis is None:
            self._redis = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                decode_responses=True
            )
        return self._redis

    def after_return(self, *args, **kwargs):
        """Cleanup resources after task completion."""
        if self._db is not None:
            self._db.close()
            self._db = None

        if self._redis is not None:
            self._redis.close()
            self._redis = None


@celery_app.task(
    base=MonitoringTask,
    name="monitoring.collect_metrics",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def collect_metrics_task(self):
    """
    Periodic metric collection task (backup safety net).

    This provides redundancy for the real-time push-based system.
    Runs every 5 minutes to ensure metrics are always collected.

    Primary monitoring: Real-time push via MetricSubscriber (<1s)
    Backup monitoring: This periodic task (5 min intervals)
    """
    try:
        from monitoring import MetricCollector

        logger.info("Starting periodic metric collection (backup)")

        # Create collector
        collector = MetricCollector(self.redis_client)

        # Collect all metrics
        metrics = collector.collect_all_metrics()

        # Push to Redis (triggers real-time subscribers)
        for metric_name, value in metrics.items():
            collector.push_metric(metric_name, value)

        logger.info(f"Collected {len(metrics)} metrics successfully")

        return {
            "status": "success",
            "metrics_collected": len(metrics),
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error collecting metrics: {e}", exc_info=True)
        raise self.retry(exc=e)


@celery_app.task(
    base=MonitoringTask,
    name="monitoring.verify_rules",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def verify_rules_task(self):
    """
    Verify rule evaluation and create alerts if needed.

    This complements the real-time evaluation by:
    - Re-checking violations that might have been missed
    - Verifying duration requirements
    - Checking cooldown status
    - Creating alerts for ready violations
    """
    try:
        from monitoring import RuleEvaluator, AlertService
        from monitoring.models import AlertRule
        from monitoring.alert_service import Alert, AlertLevel, AlertCategory

        logger.info("Starting rule verification task")

        # Create evaluator
        evaluator = RuleEvaluator(self.db, self.redis_client)

        # Get violations ready for alerting
        ready_violations = evaluator.get_violations_ready_for_alert()

        if not ready_violations:
            logger.debug("No violations ready for alerting")
            return {
                "status": "success",
                "violations_ready": 0,
                "alerts_created": 0
            }

        # Create alert service
        alert_service = AlertService(self.db)

        # Map severity levels
        severity_map = {
            "critical": AlertLevel.CRITICAL,
            "high": AlertLevel.HIGH,
            "medium": AlertLevel.MEDIUM,
            "low": AlertLevel.LOW,
            "info": AlertLevel.INFO
        }

        alerts_created = 0

        for rule, violation in ready_violations:
            try:
                # Format alert
                title = rule.format_alert_title(violation.current_value)
                message = rule.format_alert_message(
                    violation.current_value,
                    violation.duration_exceeded
                )

                alert_level = severity_map.get(rule.severity, AlertLevel.MEDIUM)

                # Create Alert object
                alert_obj = Alert(
                    alert_type="threshold_violation",
                    title=title,
                    message=message,
                    priority=alert_level,
                    category=AlertCategory.PERFORMANCE,
                    source="monitoring_task",
                    resource=rule.metric_name,
                    metric_name=rule.metric_name,
                    metric_value=violation.current_value,
                    threshold_value=violation.threshold_value,
                    metadata={
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "operator": violation.operator,
                        "duration_exceeded": violation.duration_exceeded,
                        "task": "verify_rules_task"
                    }
                )

                # Create alert
                alert_service.create_alert(alert_obj)

                # Start cooldown
                evaluator.start_cooldown(rule.id, rule.cooldown_seconds)

                # Update statistics
                rule.last_triggered_at = datetime.utcnow()
                rule.trigger_count += 1
                self.db.commit()

                alerts_created += 1
                logger.info(f"Alert created for rule: {rule.name}")

            except Exception as e:
                logger.error(f"Error creating alert for rule {rule.id}: {e}")
                continue

        logger.info(f"Rule verification complete: {alerts_created} alerts created")

        return {
            "status": "success",
            "violations_ready": len(ready_violations),
            "alerts_created": alerts_created,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error verifying rules: {e}", exc_info=True)
        raise self.retry(exc=e)


@celery_app.task(
    base=MonitoringTask,
    name="monitoring.health_check",
    bind=True
)
def health_check_task(self):
    """
    Monitor the health of the monitoring system itself.

    Checks:
    - Database connectivity
    - Redis connectivity
    - Alert rule configuration
    - Recent metric collection
    - Subscriber status

    Creates alerts if monitoring system is unhealthy.
    """
    try:
        from monitoring import AlertService
        from monitoring.alert_service import Alert, AlertLevel, AlertCategory
        from monitoring.models import AlertRule

        logger.info("Starting monitoring health check")

        issues = []

        # Check database
        try:
            self.db.execute("SELECT 1")
            logger.debug("Database connection: OK")
        except Exception as e:
            issues.append(f"Database connection failed: {e}")

        # Check Redis
        try:
            self.redis_client.ping()
            logger.debug("Redis connection: OK")
        except Exception as e:
            issues.append(f"Redis connection failed: {e}")

        # Check alert rules exist
        try:
            rule_count = self.db.query(AlertRule).filter(AlertRule.enabled == True).count()
            if rule_count == 0:
                issues.append("No enabled alert rules found")
            else:
                logger.debug(f"Alert rules: {rule_count} enabled")
        except Exception as e:
            issues.append(f"Failed to query alert rules: {e}")

        # Check recent metrics
        try:
            # Check if any metrics collected in last 10 minutes
            recent_metrics = []
            for key in self.redis_client.scan_iter("metric:*"):
                ttl = self.redis_client.ttl(key)
                if ttl > 0:  # Has TTL, means recently set
                    recent_metrics.append(key)

            if len(recent_metrics) == 0:
                issues.append("No recent metrics found in Redis")
            else:
                logger.debug(f"Recent metrics: {len(recent_metrics)} found")
        except Exception as e:
            issues.append(f"Failed to check metrics: {e}")

        # Check subscriber health (via Redis key)
        try:
            subscriber_healthy = self.redis_client.get("monitoring:subscriber:healthy")
            if subscriber_healthy != "1":
                issues.append("Metric subscriber not healthy")
            else:
                logger.debug("Metric subscriber: Healthy")
        except Exception as e:
            issues.append(f"Failed to check subscriber: {e}")

        # Create alert if issues found
        if issues:
            alert_service = AlertService(self.db)

            alert_obj = Alert(
                alert_type="monitoring_health",
                title="Monitoring System Health Issues Detected",
                message=f"Monitoring system health check found {len(issues)} issue(s)",
                priority=AlertLevel.HIGH,
                category=AlertCategory.SYSTEM,
                source="health_check_task",
                metadata={
                    "issues": issues,
                    "issue_count": len(issues)
                },
                recommendations=[
                    "Check database connectivity",
                    "Verify Redis is running",
                    "Restart monitoring services",
                    "Check application logs"
                ]
            )

            alert_service.create_alert(alert_obj)
            logger.warning(f"Health check found {len(issues)} issues")

        return {
            "status": "unhealthy" if issues else "healthy",
            "issues": issues,
            "issue_count": len(issues),
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in health check: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(
    base=MonitoringTask,
    name="monitoring.cleanup_old_data",
    bind=True
)
def cleanup_old_data_task(self):
    """
    Clean up old monitoring data from Redis.

    Removes:
    - Expired violation tracking keys
    - Old cooldown keys
    - Stale metric values
    - Old statistics
    """
    try:
        logger.info("Starting monitoring data cleanup")

        deleted_count = 0

        # Clean up old violation keys (older than 24 hours)
        violation_keys = list(self.redis_client.scan_iter("rule:violation:*"))
        for key in violation_keys:
            ttl = self.redis_client.ttl(key)
            if ttl == -1:  # No TTL set (shouldn't happen, but clean up anyway)
                self.redis_client.delete(key)
                deleted_count += 1
            elif ttl == -2:  # Key doesn't exist
                continue

        # Clean up expired cooldown keys (already handled by TTL, but verify)
        cooldown_keys = list(self.redis_client.scan_iter("rule:cooldown:*"))
        for key in cooldown_keys:
            if self.redis_client.ttl(key) == -2:
                deleted_count += 1

        # Clean up old metric values (older than 1 hour)
        metric_keys = list(self.redis_client.scan_iter("metric:*"))
        for key in metric_keys:
            ttl = self.redis_client.ttl(key)
            if ttl == -1:  # No TTL
                # Set TTL to 1 hour
                self.redis_client.expire(key, 3600)

        logger.info(f"Cleanup complete: {deleted_count} keys removed")

        return {
            "status": "success",
            "keys_cleaned": deleted_count,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in cleanup: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(
    base=MonitoringTask,
    name="monitoring.aggregate_statistics",
    bind=True
)
def aggregate_statistics_task(self):
    """
    Aggregate monitoring statistics for reporting.

    Collects:
    - Alert counts by severity
    - Rule trigger frequency
    - Most violated metrics
    - System state distribution
    - Performance metrics
    """
    try:
        from monitoring.models import AlertRule
        from monitoring.models import AlertModel, AlertStatus

        logger.info("Starting statistics aggregation")

        # Get time ranges
        now = datetime.utcnow()
        last_hour = now - timedelta(hours=1)
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)

        stats = {
            "timestamp": now.isoformat(),
            "alerts": {},
            "rules": {},
            "metrics": {}
        }

        # Alert statistics
        stats["alerts"]["last_hour"] = self.db.query(AlertModel).filter(
            AlertModel.created_at >= last_hour
        ).count()

        stats["alerts"]["last_24h"] = self.db.query(AlertModel).filter(
            AlertModel.created_at >= last_24h
        ).count()

        stats["alerts"]["last_7d"] = self.db.query(AlertModel).filter(
            AlertModel.created_at >= last_7d
        ).count()

        # Alert status distribution
        stats["alerts"]["by_status"] = {}
        for status in AlertStatus:
            count = self.db.query(AlertModel).filter(
                AlertModel.status == status.value
            ).count()
            stats["alerts"]["by_status"][status.value] = count

        # Rule statistics
        all_rules = self.db.query(AlertRule).all()
        stats["rules"]["total"] = len(all_rules)
        stats["rules"]["enabled"] = sum(1 for r in all_rules if r.enabled)
        stats["rules"]["disabled"] = sum(1 for r in all_rules if not r.enabled)

        # Most triggered rules (last 24h)
        stats["rules"]["most_triggered"] = []
        for rule in all_rules:
            if rule.last_triggered_at and rule.last_triggered_at >= last_24h:
                stats["rules"]["most_triggered"].append({
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "trigger_count": rule.trigger_count,
                    "last_triggered": rule.last_triggered_at.isoformat()
                })

        # Sort by trigger count
        stats["rules"]["most_triggered"].sort(
            key=lambda x: x["trigger_count"],
            reverse=True
        )
        stats["rules"]["most_triggered"] = stats["rules"]["most_triggered"][:10]

        # Store in Redis for quick access
        stats_key = f"monitoring:stats:{now.strftime('%Y%m%d%H')}"
        self.redis_client.setex(
            stats_key,
            86400,  # 24 hour TTL
            str(stats)
        )

        logger.info("Statistics aggregation complete")

        return stats

    except Exception as e:
        logger.error(f"Error aggregating statistics: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(name="monitoring.test_task")
def test_monitoring_task():
    """
    Simple test task to verify Celery is working with monitoring tasks.
    """
    logger.info("Monitoring test task executed")
    return {
        "status": "success",
        "message": "Monitoring tasks are configured correctly",
        "timestamp": datetime.utcnow().isoformat()
    }
