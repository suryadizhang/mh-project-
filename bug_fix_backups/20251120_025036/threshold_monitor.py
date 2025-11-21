"""
ThresholdMonitor - Core monitoring engine with adaptive intervals.

Integrates all monitoring components:
- MetricCollector: Gathers metrics from system, database, application
- MetricSubscriber: Real-time Redis pub/sub listener
- RuleEvaluator: Threshold checking with duration and cooldown
- MonitoringState: IDLE/ACTIVE/ALERT state machine
- AlertService: Alert creation and management

Adaptive monitoring strategy:
- IDLE state: Critical checks only (3 metrics) every 5 minutes
- ACTIVE state: Full monitoring (30+ metrics) every 2 minutes
- ALERT state: Aggressive monitoring (30+ metrics) every 15 seconds
- Push-based: <1s detection when metrics pushed to Redis

Architecture:
┌─────────────────────────────────────────────────────┐
│  API Activity → MonitoringMiddleware                │
│                   ↓                                  │
│  MonitoringState.record_activity()                  │
│                   ↓                                  │
│  State: IDLE → ACTIVE (15min timeout)               │
│                   ↓                                  │
│  MetricCollector.collect_metrics()                  │
│                   ↓                                  │
│  MetricCollector.push_metric() → Redis pub/sub      │
│                   ↓                                  │
│  MetricSubscriber receives → on_metric_update()     │
│                   ↓                                  │
│  RuleEvaluator.evaluate_metric()                    │
│                   ↓                                  │
│  Check duration + cooldown                          │
│                   ↓                                  │
│  get_violations_ready_for_alert()                   │
│                   ↓                                  │
│  AlertService.create_alert() ← HERE!                │
│                   ↓                                  │
│  MonitoringState.enter_alert_state()                │
│                   ↓                                  │
│  Aggressive monitoring (15s intervals)              │
└─────────────────────────────────────────────────────┘
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
import logging
import time

from redis import Redis
from sqlalchemy.orm import Session

from .alert_rule_model import AlertRule
from .alert_service import Alert, AlertCategory, AlertLevel, AlertService
from .metric_collector import MetricCollector, get_metric_collector
from .metric_subscriber import MetricSubscriber
from .monitoring_state import MonitoringState, MonitoringStateEnum
from .rule_evaluator import RuleEvaluator, RuleViolation

logger = logging.getLogger(__name__)


class ThresholdMonitor:
    """
    Core monitoring engine that orchestrates all components.

    Features:
    - Adaptive monitoring intervals based on state
    - Real-time push-based detection via Redis pub/sub
    - Automatic alert creation when violations ready
    - State transitions (IDLE → ACTIVE → ALERT)
    - Duration and cooldown tracking
    - Background monitoring loop

    Usage:
        monitor = ThresholdMonitor(db_session, redis_client)
        await monitor.start()
        # ... monitoring runs in background
        await monitor.stop()
    """

    # Check intervals by state (seconds)
    INTERVAL_IDLE = 300  # 5 minutes - critical checks only
    INTERVAL_ACTIVE = 120  # 2 minutes - full monitoring
    INTERVAL_ALERT = 15  # 15 seconds - aggressive monitoring

    # Metrics to check in each state
    CRITICAL_METRICS = {
        "database_available",
        "redis_available",
        "disk_percent",
    }

    def __init__(
        self,
        db_session: Session,
        redis_client: Redis,
        alert_service: AlertService | None = None,
        metric_collector: MetricCollector | None = None,
        auto_start_subscriber: bool = True,
    ):
        """
        Initialize ThresholdMonitor.

        Args:
            db_session: Database session for rule queries
            redis_client: Redis client for state and pub/sub
            alert_service: AlertService instance (created if None)
            metric_collector: MetricCollector instance (created if None)
            auto_start_subscriber: Start subscriber automatically
        """
        self.db_session = db_session
        self.redis_client = redis_client

        # Core components
        self.alert_service = alert_service or AlertService(db_session)
        self.metric_collector = metric_collector or get_metric_collector(
            redis_client
        )
        self.rule_evaluator = RuleEvaluator(db_session, redis_client)
        self.monitoring_state = MonitoringState(redis_client)

        # Subscriber for push-based monitoring
        self.subscriber = MetricSubscriber(redis_client)
        self.subscriber.add_callback(self._on_metric_update)

        # State
        self._running = False
        self._monitor_task: asyncio.Task | None = None
        self._last_check_time = 0.0
        self._active_violations: dict[int, RuleViolation] = (
            {}
        )  # rule_id -> violation

        # Statistics
        self.stats = {
            "checks_performed": 0,
            "alerts_created": 0,
            "violations_detected": 0,
            "state_transitions": 0,
            "last_check_timestamp": None,
            "last_alert_timestamp": None,
            "uptime_seconds": 0,
            "start_time": None,
        }

        # Auto-start subscriber
        if auto_start_subscriber:
            self.subscriber.start_in_background()
            logger.info("MetricSubscriber started in background")

    async def start(self):
        """Start the monitoring loop."""
        if self._running:
            logger.warning("ThresholdMonitor already running")
            return

        self._running = True
        self.stats["start_time"] = datetime.utcnow()
        logger.info("ThresholdMonitor starting...")

        # Start monitoring loop
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("ThresholdMonitor started successfully")

    async def stop(self):
        """Stop the monitoring loop."""
        if not self._running:
            return

        logger.info("ThresholdMonitor stopping...")
        self._running = False

        # Stop subscriber
        self.subscriber.stop()

        # Cancel monitoring task
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        logger.info("ThresholdMonitor stopped")

    async def _monitoring_loop(self):
        """
        Main monitoring loop with adaptive intervals.

        Behavior:
        - IDLE: Check critical metrics every 5 minutes
        - ACTIVE: Check all metrics every 2 minutes
        - ALERT: Check all metrics every 15 seconds
        - Also responds to push notifications via subscriber
        """
        logger.info("Monitoring loop started")

        try:
            while self._running:
                try:
                    # Get current state
                    current_state = self.monitoring_state.get_current_state()

                    # Determine check interval
                    if current_state == MonitoringStateEnum.IDLE:
                        interval = self.INTERVAL_IDLE
                        check_critical_only = True
                    elif current_state == MonitoringStateEnum.ACTIVE:
                        interval = self.INTERVAL_ACTIVE
                        check_critical_only = False
                    else:  # ALERT
                        interval = self.INTERVAL_ALERT
                        check_critical_only = False

                    # Check if enough time has passed
                    current_time = time.time()
                    if current_time - self._last_check_time >= interval:
                        await self._perform_check(check_critical_only)
                        self._last_check_time = current_time

                    # Update uptime
                    if self.stats["start_time"]:
                        self.stats["uptime_seconds"] = (
                            datetime.utcnow() - self.stats["start_time"]
                        ).total_seconds()

                    # Sleep for a short interval (responsive to stop signal)
                    await asyncio.sleep(1)

                except Exception as e:
                    logger.error(
                        f"Error in monitoring loop: {e}", exc_info=True
                    )
                    await asyncio.sleep(5)  # Back off on error

        except asyncio.CancelledError:
            logger.info("Monitoring loop cancelled")
            raise

    async def _perform_check(self, check_critical_only: bool = False):
        """
        Perform a monitoring check.

        Args:
            check_critical_only: If True, only check critical metrics
        """
        try:
            start_time = time.time()

            # Collect metrics
            if check_critical_only:
                logger.debug("Performing critical-only check")
                metrics = await self._collect_critical_metrics()
            else:
                logger.debug("Performing full metrics check")
                metrics = await self._collect_all_metrics()

            # Evaluate rules
            timestamp = time.time()
            violations = self.rule_evaluator.evaluate_metrics(
                metrics, timestamp
            )

            # Update active violations
            self._update_active_violations(violations)

            # Check for violations ready to alert
            ready_violations = (
                self.rule_evaluator.get_violations_ready_for_alert()
            )

            # Create alerts
            alerts_created = await self._create_alerts_for_violations(
                ready_violations
            )

            # Update state based on results
            if alerts_created > 0:
                self.monitoring_state.enter_alert_state()
                self.stats["state_transitions"] += 1
            elif len(violations) == 0:
                # No violations, can potentially transition to lower state
                # (State machine handles timeout-based transitions)
                pass

            # Update statistics
            self.stats["checks_performed"] += 1
            self.stats["violations_detected"] += len(violations)
            self.stats["last_check_timestamp"] = datetime.utcnow()

            duration = time.time() - start_time
            logger.debug(
                f"Check completed in {duration:.2f}s: "
                f"{len(metrics)} metrics, {len(violations)} violations, "
                f"{alerts_created} alerts created"
            )

        except Exception as e:
            logger.error(f"Error performing check: {e}", exc_info=True)

    async def _collect_critical_metrics(self) -> dict[str, float]:
        """Collect only critical metrics (for IDLE state)."""
        metrics = {}

        for metric_name in self.CRITICAL_METRICS:
            try:
                value = await self._collect_single_metric(metric_name)
                if value is not None:
                    metrics[metric_name] = value
            except Exception as e:
                logger.error(f"Error collecting {metric_name}: {e}")

        return metrics

    async def _collect_all_metrics(self) -> dict[str, float]:
        """Collect all metrics (for ACTIVE/ALERT states)."""
        try:
            # Use MetricCollector to gather all metrics
            all_metrics = self.metric_collector.collect_all_metrics()

            # Push to Redis (triggers subscriber callbacks)
            for metric_name, value in all_metrics.items():
                self.metric_collector.push_metric(metric_name, value)

            return all_metrics

        except Exception as e:
            logger.error(f"Error collecting all metrics: {e}", exc_info=True)
            return {}

    async def _collect_single_metric(self, metric_name: str) -> float | None:
        """Collect a single metric by name."""
        try:
            # Map metric names to collector methods
            if metric_name == "database_available":
                return (
                    1.0
                    if self.metric_collector._check_database_available()
                    else 0.0
                )
            elif metric_name == "redis_available":
                return (
                    1.0
                    if self.metric_collector._check_redis_available()
                    else 0.0
                )
            elif metric_name == "disk_percent":
                system_metrics = (
                    self.metric_collector._collect_system_metrics()
                )
                return system_metrics.get("disk_percent")
            else:
                # For other metrics, collect all and extract
                all_metrics = self.metric_collector.collect_all_metrics()
                return all_metrics.get(metric_name)

        except Exception as e:
            logger.error(f"Error collecting metric {metric_name}: {e}")
            return None

    def _on_metric_update(
        self, metric_name: str, value: float, timestamp: float
    ):
        """
        Callback for MetricSubscriber - real-time metric updates.

        This provides push-based monitoring with <1s latency.

        Args:
            metric_name: Name of metric that was updated
            value: New metric value
            timestamp: Timestamp of metric
        """
        try:
            # Evaluate this specific metric
            violations = self.rule_evaluator.evaluate_metric(
                metric_name, value, timestamp
            )

            if violations:
                logger.info(
                    f"Push notification: {metric_name}={value:.2f} triggered "
                    f"{len(violations)} violation(s)"
                )

                # Update active violations
                self._update_active_violations(violations)

                # Check if any violations are ready for alerting
                ready_violations = (
                    self.rule_evaluator.get_violations_ready_for_alert()
                )

                # Create alerts asynchronously
                if ready_violations:
                    # Schedule alert creation (don't block callback)
                    asyncio.create_task(
                        self._create_alerts_for_violations(ready_violations)
                    )

        except Exception as e:
            logger.error(
                f"Error in metric update callback: {e}", exc_info=True
            )

    def _update_active_violations(self, violations: list[RuleViolation]):
        """Update the active violations tracking."""
        for violation in violations:
            self._active_violations[violation.rule_id] = violation

        # Remove violations that are no longer active
        # (RuleEvaluator clears Redis keys when violations resolve)
        active_rule_ids = {v.rule_id for v in violations}
        resolved_rule_ids = (
            set(self._active_violations.keys()) - active_rule_ids
        )

        for rule_id in resolved_rule_ids:
            if rule_id in self._active_violations:
                logger.info(f"Violation resolved for rule {rule_id}")
                del self._active_violations[rule_id]

    async def _create_alerts_for_violations(
        self, ready_violations: list[tuple[AlertRule, RuleViolation]]
    ) -> int:
        """
        Create alerts for violations that are ready.

        Args:
            ready_violations: List of (rule, violation) tuples

        Returns:
            Number of alerts created
        """
        alerts_created = 0

        for rule, violation in ready_violations:
            try:
                # Map rule severity to alert level
                severity_map = {
                    "critical": AlertLevel.CRITICAL,
                    "high": AlertLevel.HIGH,
                    "medium": AlertLevel.MEDIUM,
                    "low": AlertLevel.LOW,
                    "info": AlertLevel.INFO,
                }
                alert_level = severity_map.get(
                    rule.severity, AlertLevel.MEDIUM
                )

                # Format alert messages
                title = rule.format_alert_title(violation.current_value)
                message = rule.format_alert_message(
                    violation.current_value, violation.duration_exceeded
                )

                # Create Alert object
                alert_obj = Alert(
                    alert_type="threshold_violation",
                    title=title,
                    message=message,
                    priority=alert_level,
                    category=AlertCategory.PERFORMANCE,  # Default, can be customized per rule
                    source="threshold_monitor",
                    resource=rule.metric_name,
                    metric_name=rule.metric_name,
                    metric_value=violation.current_value,
                    threshold_value=violation.threshold_value,
                    metadata={
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "operator": violation.operator,
                        "duration_exceeded": violation.duration_exceeded,
                        "tags": rule.tags,
                        "rule_metadata": rule.metadata,
                    },
                    recommendations=[],  # Could be added from rule metadata
                )

                # Create alert via service
                alert = self.alert_service.create_alert(alert_obj)

                # Start cooldown
                self.rule_evaluator.start_cooldown(
                    rule.id, rule.cooldown_seconds
                )

                # Update rule statistics
                rule.last_triggered_at = datetime.utcnow()
                rule.trigger_count += 1
                self.db_session.commit()

                alerts_created += 1
                self.stats["alerts_created"] += 1
                self.stats["last_alert_timestamp"] = datetime.utcnow()

                logger.info(
                    f"Alert created: {title} "
                    f"(rule={rule.name}, value={violation.current_value:.2f}, "
                    f"duration={violation.duration_exceeded:.0f}s)"
                )

            except Exception as e:
                logger.error(
                    f"Error creating alert for rule {rule.id}: {e}",
                    exc_info=True,
                )
                # Continue with other violations

        return alerts_created

    def get_stats(self) -> dict:
        """Get monitoring statistics."""
        return {
            **self.stats,
            "is_running": self._running,
            "current_state": self.monitoring_state.get_current_state().value,
            "active_violations": len(self._active_violations),
            "subscriber_stats": (
                self.subscriber.get_stats()
                if self.subscriber.is_running()
                else None
            ),
            "rule_evaluator_violations": len(
                self.rule_evaluator.get_all_violations()
            ),
        }

    def get_active_violations(self) -> list[dict]:
        """Get current active violations."""
        return [v.to_dict() for v in self._active_violations.values()]

    def is_running(self) -> bool:
        """Check if monitor is running."""
        return self._running

    def is_healthy(self) -> bool:
        """Check if monitor is healthy."""
        if not self._running:
            return False

        # Check subscriber health
        if not self.subscriber.is_healthy():
            return False

        # Check if we've performed checks recently
        if self.stats["last_check_timestamp"]:
            time_since_check = (
                datetime.utcnow() - self.stats["last_check_timestamp"]
            ).total_seconds()

            # Should have checked within last 10 minutes
            if time_since_check > 600:
                return False

        return True


# Singleton instance
_threshold_monitor: ThresholdMonitor | None = None


def get_threshold_monitor(
    db_session: Session, redis_client: Redis, force_new: bool = False
) -> ThresholdMonitor:
    """
    Get or create ThresholdMonitor singleton.

    Args:
        db_session: Database session
        redis_client: Redis client
        force_new: Force creation of new instance

    Returns:
        ThresholdMonitor instance
    """
    global _threshold_monitor

    if force_new or _threshold_monitor is None:
        _threshold_monitor = ThresholdMonitor(db_session, redis_client)

    return _threshold_monitor


@asynccontextmanager
async def threshold_monitor_context(db_session: Session, redis_client: Redis):
    """
    Context manager for ThresholdMonitor lifecycle.

    Usage:
        async with threshold_monitor_context(db_session, redis_client) as monitor:
            # Monitor runs in background
            await asyncio.sleep(60)
        # Monitor automatically stopped
    """
    monitor = get_threshold_monitor(db_session, redis_client)

    try:
        await monitor.start()
        yield monitor
    finally:
        await monitor.stop()
