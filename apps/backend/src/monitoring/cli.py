#!/usr/bin/env python
"""
Monitoring System CLI

Command-line interface for managing and testing the threshold monitoring system.

Commands:
    start       - Start monitoring in foreground
    stats       - Show monitoring statistics
    violations  - List active violations
    rules       - List all alert rules
    test-rule   - Test a specific rule
    health      - Check system health

Usage:
    python -m monitoring.cli start
    python -m monitoring.cli stats
    python -m monitoring.cli violations
    python -m monitoring.cli rules
    python -m monitoring.cli test-rule <rule_id>
    python -m monitoring.cli health
"""

import asyncio
import sys
import logging
from typing import Optional
import json
from datetime import datetime

import click
from sqlalchemy.orm import Session

from core.database import SessionLocal
from core.config import settings
from monitoring import (
    ThresholdMonitor,
    get_threshold_monitor,
    MonitoringState,
    RuleEvaluator,
)
from monitoring.models import AlertRule
import redis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_redis_client():
    """Get Redis client configured from settings."""
    return redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        decode_responses=True
    )


@click.group()
def cli():
    """Monitoring System CLI"""
    pass


@cli.command()
@click.option("--duration", default=0, help="Run duration in seconds (0 = forever)")
def start(duration: int):
    """Start monitoring system."""
    logger.info("Starting monitoring system...")

    async def run_monitor():
        db = SessionLocal()
        redis_client = get_redis_client()

        monitor = get_threshold_monitor(db, redis_client)

        try:
            await monitor.start()

            if duration > 0:
                logger.info(f"Monitoring for {duration} seconds...")
                await asyncio.sleep(duration)
            else:
                logger.info("Monitoring indefinitely (Ctrl+C to stop)...")
                while True:
                    await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            await monitor.stop()
            db.close()

    try:
        asyncio.run(run_monitor())
    except KeyboardInterrupt:
        logger.info("Monitoring stopped")


@cli.command()
def stats():
    """Show monitoring statistics."""
    db = SessionLocal()
    redis_client = get_redis_client()

    try:
        monitor = get_threshold_monitor(db, redis_client, force_new=False)
        stats_data = monitor.get_stats()

        # Format for display
        click.echo("\n=== Monitoring Statistics ===\n")
        click.echo(f"Status: {'Running' if stats_data['is_running'] else 'Stopped'}")
        click.echo(f"Current State: {stats_data['current_state']}")
        click.echo(f"Uptime: {stats_data['uptime_seconds']:.0f} seconds")
        click.echo(f"\nChecks Performed: {stats_data['checks_performed']}")
        click.echo(f"Alerts Created: {stats_data['alerts_created']}")
        click.echo(f"Violations Detected: {stats_data['violations_detected']}")
        click.echo(f"State Transitions: {stats_data['state_transitions']}")
        click.echo(f"Active Violations: {stats_data['active_violations']}")

        if stats_data['last_check_timestamp']:
            click.echo(f"\nLast Check: {stats_data['last_check_timestamp']}")

        if stats_data['last_alert_timestamp']:
            click.echo(f"Last Alert: {stats_data['last_alert_timestamp']}")

        # Subscriber stats
        if stats_data.get('subscriber_stats'):
            sub_stats = stats_data['subscriber_stats']
            click.echo(f"\n=== Subscriber Statistics ===")
            click.echo(f"Messages Received: {sub_stats.get('messages_received', 0)}")
            click.echo(f"Callbacks Executed: {sub_stats.get('callbacks_executed', 0)}")
            click.echo(f"Errors: {sub_stats.get('errors', 0)}")

    finally:
        db.close()


@cli.command()
def violations():
    """List active violations."""
    db = SessionLocal()
    redis_client = get_redis_client()

    try:
        monitor = get_threshold_monitor(db, redis_client, force_new=False)
        active_violations = monitor.get_active_violations()

        if not active_violations:
            click.echo("No active violations")
            return

        click.echo(f"\n=== Active Violations ({len(active_violations)}) ===\n")

        for violation in active_violations:
            click.echo(f"Rule ID: {violation['rule_id']}")
            click.echo(f"Metric: {violation['metric_name']}")
            click.echo(f"Current Value: {violation['current_value']:.2f}")
            click.echo(f"Threshold: {violation['operator']} {violation['threshold_value']:.2f}")
            click.echo(f"Duration Exceeded: {violation['duration_exceeded']:.0f}s")
            click.echo(f"Duration Required: {violation['duration_required']:.0f}s")
            click.echo(f"Duration Met: {violation['is_duration_met']}")

            if not violation['is_duration_met']:
                click.echo(f"Remaining: {violation['remaining_duration']:.0f}s")

            click.echo("---")

    finally:
        db.close()


@cli.command()
@click.option("--enabled-only", is_flag=True, help="Show only enabled rules")
def rules(enabled_only: bool):
    """List all alert rules."""
    db = SessionLocal()

    try:
        query = db.query(AlertRule)

        if enabled_only:
            query = query.filter(AlertRule.enabled == True)

        rules = query.all()

        if not rules:
            click.echo("No rules found")
            return

        click.echo(f"\n=== Alert Rules ({len(rules)}) ===\n")

        for rule in rules:
            status = "✓" if rule.enabled else "✗"
            click.echo(f"[{status}] {rule.name} (ID: {rule.id})")
            click.echo(f"    Condition: {rule.get_condition_display()}")
            click.echo(f"    Severity: {rule.severity}")
            click.echo(f"    Cooldown: {rule.cooldown_seconds}s")

            if rule.trigger_count > 0:
                click.echo(f"    Triggered: {rule.trigger_count} times")
                if rule.last_triggered_at:
                    click.echo(f"    Last Triggered: {rule.last_triggered_at}")

            click.echo()

    finally:
        db.close()


@cli.command()
@click.argument("rule_id", type=int)
@click.option("--test-value", type=float, required=True, help="Value to test")
def test_rule(rule_id: int, test_value: float):
    """Test a specific rule with a value."""
    db = SessionLocal()
    redis_client = get_redis_client()

    try:
        # Get rule
        rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()

        if not rule:
            click.echo(f"Rule {rule_id} not found", err=True)
            return

        click.echo(f"\n=== Testing Rule: {rule.name} ===\n")
        click.echo(f"Condition: {rule.get_condition_display()}")
        click.echo(f"Test Value: {test_value}")

        # Create evaluator
        evaluator = RuleEvaluator(db, redis_client)

        # Evaluate
        violations = evaluator.evaluate_metric(
            rule.metric_name,
            test_value,
            datetime.utcnow().timestamp()
        )

        if violations:
            click.echo(f"\n✗ VIOLATION DETECTED")

            for violation in violations:
                if violation.rule_id == rule_id:
                    click.echo(f"\nCurrent Value: {violation.current_value:.2f}")
                    click.echo(f"Threshold: {violation.operator} {violation.threshold_value:.2f}")
                    click.echo(f"Duration Exceeded: {violation.duration_exceeded:.0f}s")
                    click.echo(f"Duration Required: {violation.duration_required:.0f}s")

                    if violation.is_duration_met:
                        click.echo("✓ Duration requirement MET - would create alert")
                    else:
                        click.echo(f"⏳ Duration requirement NOT met - need {violation.remaining_duration:.0f}s more")
        else:
            click.echo(f"\n✓ No violation - value is within threshold")

    finally:
        db.close()


@cli.command()
def health():
    """Check monitoring system health."""
    db = SessionLocal()
    redis_client = get_redis_client()

    try:
        monitor = get_threshold_monitor(db, redis_client, force_new=False)

        is_healthy = monitor.is_healthy()
        is_running = monitor.is_running()

        click.echo("\n=== System Health Check ===\n")

        if is_healthy:
            click.echo("✓ System is HEALTHY")
        else:
            click.echo("✗ System is UNHEALTHY")

        click.echo(f"\nMonitor Running: {is_running}")

        # Check components
        from monitoring import MonitoringState
        state = MonitoringState(redis_client)
        current_state = state.get_current_state()

        click.echo(f"Current State: {current_state.value}")

        # Check subscriber
        if hasattr(monitor, 'subscriber'):
            subscriber_healthy = monitor.subscriber.is_healthy()
            subscriber_running = monitor.subscriber.is_running()

            click.echo(f"\nSubscriber Running: {subscriber_running}")
            click.echo(f"Subscriber Healthy: {subscriber_healthy}")

        # Check Redis
        try:
            redis_client.ping()
            click.echo("\n✓ Redis connection: OK")
        except Exception as e:
            click.echo(f"\n✗ Redis connection: FAILED - {e}")

        # Check database
        try:
            db.execute("SELECT 1")
            click.echo("✓ Database connection: OK")
        except Exception as e:
            click.echo(f"✗ Database connection: FAILED - {e}")

        sys.exit(0 if is_healthy else 1)

    finally:
        db.close()


if __name__ == "__main__":
    cli()
