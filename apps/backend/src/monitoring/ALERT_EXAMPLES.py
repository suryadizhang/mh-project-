"""
AlertService Usage Examples

This file demonstrates how the AlertService provides specific,
actionable diagnostic information for different types of problems.
"""

from monitoring.alert_service import (
    Alert,
    AlertCategory,
    AlertLevel,
    AlertPriority,
    AlertService,
)
from monitoring.models import NotificationChannel

# ============================================================================
# EXAMPLE 1: DATABASE SLOW QUERY - VERY SPECIFIC
# ============================================================================

def example_database_slow_query(alert_service: AlertService):
    """
    When a database query is slow, you get:
    - Exact query that's slow
    - How slow it is vs threshold
    - Query execution plan
    - Number of rows scanned
    - Specific recommendations (add index, optimize query)
    - Link to slow query log
    """
    alert = Alert(
        alert_type="database_slow_query",
        title="Slow Database Query Detected on Bookings Table",
        message=(
            "Query took 5.23 seconds (threshold: 1.0s, exceeded by 423%). "
            "Sequential scan on 50,000 rows without index."
        ),
        priority=AlertPriority.HIGH,
        category=AlertCategory.DATABASE,
        source="booking_service",
        resource="bookings table",
        metric_name="query_duration_seconds",
        metric_value=5.23,
        threshold_value=1.0,
        metadata={
            "query": "SELECT * FROM bookings WHERE customer_id = 12345 AND status = 'confirmed'",
            "execution_plan": "Seq Scan on bookings (cost=0.00..1234.56 rows=50000)",
            "rows_scanned": 50000,
            "database": "myhibachi_prod",
            "connection_pool_usage": "85%",
        },
        recommendations=[
            "✅ Add composite index: CREATE INDEX idx_bookings_customer_status ON bookings(customer_id, status);",
            "✅ Add WHERE clause to limit date range if applicable",
            "✅ Consider partitioning bookings table by date",
            "✅ Review query execution plan: EXPLAIN ANALYZE SELECT ...",
            "⚠️ Current sequential scan is reading all 50k rows",
        ],
        related_logs="/var/log/postgresql/slow_queries.log",
        affected_users=15,  # How many users experienced this slow query
        error_code="DB_SLOW_QUERY",
        notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
    )
    
    db_alert = alert_service.create_alert(alert)
    
    # What you get:
    # {
    #   "id": 123,
    #   "title": "Slow Database Query Detected on Bookings Table",
    #   "message": "Query took 5.23 seconds (threshold: 1.0s, exceeded by 423%)",
    #   "priority": "high",
    #   "resource": "bookings table",
    #   "metric_value": "5.23",
    #   "threshold_value": "1.0",
    #   "metadata": {
    #     "query": "SELECT * FROM bookings WHERE...",
    #     "execution_plan": "Seq Scan on bookings...",
    #     "recommendations": [
    #       "✅ Add composite index: CREATE INDEX...",
    #       ...
    #     ]
    #   },
    #   "affected_users": 15,
    #   "related_logs": "/var/log/postgresql/slow_queries.log"
    # }


# ============================================================================
# EXAMPLE 2: HIGH CPU USAGE - EXACT DETAILS
# ============================================================================

def example_high_cpu(alert_service: AlertService):
    """
    When CPU is high, you get:
    - Exact CPU percentage
    - Which server/resource
    - What's causing it (if detectable)
    - How to investigate further
    - How long it's been high
    """
    alert = Alert(
        alert_type="system_cpu_high",
        title="Critical: CPU Usage at 95% on web-server-01",
        message=(
            "CPU usage is at 95.3% (threshold: 80%, exceeded by 19.1%). "
            "Load average: 8.5, 7.2, 6.1 (1m, 5m, 15m)"
        ),
        priority=AlertPriority.CRITICAL,
        category=AlertCategory.SYSTEM,
        source="system_monitor",
        resource="web-server-01",
        metric_name="cpu_percent",
        metric_value=95.3,
        threshold_value=80.0,
        metadata={
            "load_average_1m": 8.5,
            "load_average_5m": 7.2,
            "load_average_15m": 6.1,
            "process_count": 245,
            "top_processes": [
                {"name": "gunicorn", "cpu": 45.2, "pid": 12345},
                {"name": "celery", "cpu": 30.1, "pid": 12346},
                {"name": "postgres", "cpu": 15.5, "pid": 12347},
            ],
            "duration_minutes": 15,  # How long it's been high
        },
        recommendations=[
            "🚨 IMMEDIATE: Check 'gunicorn' process (PID 12345) consuming 45% CPU",
            "✅ Run: sudo htop -p 12345 to monitor the process",
            "✅ Check application logs: tail -f /var/log/myhibachi/app.log",
            "✅ Review recent deployments in last 30 minutes",
            "✅ Consider scaling: Add more web server instances",
            "⚠️ If issue persists >30min, restart gunicorn: sudo systemctl restart myhibachi-backend",
        ],
        related_logs="/var/log/myhibachi/system_monitor.log",
        notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SMS],
    )
    
    return alert_service.create_alert(alert)


# ============================================================================
# EXAMPLE 3: APPLICATION ERROR - FULL STACK TRACE
# ============================================================================

def example_application_error(alert_service: AlertService):
    """
    When application crashes, you get:
    - Error type and message
    - Full stack trace
    - Which endpoint failed
    - How many users affected
    - Specific fix recommendations
    """
    stack_trace = """
Traceback (most recent call last):
  File "/app/routers/bookings.py", line 145, in create_booking
    result = await booking_service.create(booking_data)
  File "/app/services/booking_service.py", line 89, in create
    payment = await payment_gateway.charge(amount)
  File "/app/integrations/stripe.py", line 234, in charge
    raise StripeAPIError("Card declined: insufficient_funds")
StripeAPIError: Card declined: insufficient_funds
    """
    
    alert = alert_service.create_application_error_alert(
        error_type="StripeAPIError",
        error_message="Card declined: insufficient_funds",
        stack_trace=stack_trace,
        source="booking_service",
        affected_endpoint="POST /api/v1/bookings",
        affected_users=3,
        error_count=5,  # Happened 5 times in last hour
    )
    
    # The service automatically generates recommendations:
    # - Check Stripe API status
    # - Review card validation logic
    # - Implement better error handling for payment failures
    # - Add retry logic with exponential backoff
    # - Notify customer to update payment method
    
    return alert


# ============================================================================
# EXAMPLE 4: MEMORY LEAK - TRENDING DATA
# ============================================================================

def example_memory_leak(alert_service: AlertService):
    """
    When memory keeps growing, you get:
    - Current memory usage
    - Trend over time (is it growing?)
    - Which process
    - Heap dump location
    - Memory profiling recommendations
    """
    alert = Alert(
        alert_type="system_memory_leak",
        title="Memory Leak Detected: Backend Process Growing Steadily",
        message=(
            "Memory usage at 87% and growing 2.5% per hour. "
            "Process 'myhibachi-backend' using 6.8GB (started at 2.1GB 3 hours ago)."
        ),
        priority=AlertPriority.HIGH,
        category=AlertCategory.SYSTEM,
        source="system_monitor",
        resource="myhibachi-backend (PID 54321)",
        metric_name="memory_percent",
        metric_value=87.3,
        threshold_value=85.0,
        metadata={
            "process_name": "myhibachi-backend",
            "pid": 54321,
            "current_memory_gb": 6.8,
            "initial_memory_gb": 2.1,
            "hours_running": 3,
            "growth_rate_percent_per_hour": 2.5,
            "heap_dump_location": "/tmp/heap_dump_54321.hprof",
            "memory_timeline": [
                {"time": "15:00", "memory_gb": 2.1},
                {"time": "16:00", "memory_gb": 3.8},
                {"time": "17:00", "memory_gb": 5.2},
                {"time": "18:00", "memory_gb": 6.8},
            ],
        },
        recommendations=[
            "🔍 ANALYZE: Heap dump saved at /tmp/heap_dump_54321.hprof",
            "✅ Run memory profiler: py-spy record -o profile.svg --pid 54321",
            "✅ Check for unbounded caches or collections in recent code",
            "✅ Review database connection pool (may not be releasing connections)",
            "✅ Check for circular references preventing garbage collection",
            "⚠️ TEMPORARY FIX: Restart service if memory >90%: sudo systemctl restart myhibachi-backend",
            "📊 INVESTIGATE: Review code changes from last 3 days",
        ],
        related_logs="/var/log/myhibachi/memory_profile.log",
        notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
    )
    
    return alert_service.create_alert(alert)


# ============================================================================
# EXAMPLE 5: API ENDPOINT SLOW - PERFORMANCE BREAKDOWN
# ============================================================================

def example_slow_api(alert_service: AlertService):
    """
    When API is slow, you get:
    - Which endpoint
    - Response time percentiles (P50, P95, P99)
    - Breakdown of where time is spent
    - Sample of slow requests
    - Optimization recommendations
    """
    alert = alert_service.create_performance_alert(
        metric_name="response_time_ms",
        current_value=3250.5,  # P95 response time
        threshold_value=1000.0,
        resource="GET /api/v1/bookings",
        percentile="P95",
        sample_count=1250,
    )
    
    # Enhancement: Add detailed breakdown
    alert.metadata.update({
        "response_time_breakdown": {
            "database_query": 2100,  # 64% of time
            "external_api_call": 850,  # 26% of time
            "business_logic": 200,  # 6% of time
            "serialization": 100,  # 3% of time
        },
        "percentiles": {
            "p50": 450,
            "p75": 1200,
            "p90": 2500,
            "p95": 3250,
            "p99": 4800,
        },
        "slow_requests_sample": [
            {"request_id": "req_123", "duration_ms": 4800, "timestamp": "2025-11-10T15:30:22Z"},
            {"request_id": "req_124", "duration_ms": 3900, "timestamp": "2025-11-10T15:30:45Z"},
            {"request_id": "req_125", "duration_ms": 3650, "timestamp": "2025-11-10T15:31:12Z"},
        ],
    })
    
    # Service adds specific recommendations:
    # - 64% of time is database queries → optimize queries
    # - 26% is external API → add timeout, caching
    # - Check slow request IDs for patterns
    
    return alert


# ============================================================================
# EXAMPLE 6: SERVICE DOWN - AVAILABILITY ALERT
# ============================================================================

def example_service_down(alert_service: AlertService):
    """
    When service is down, you get:
    - Which service
    - When it went down
    - Last successful health check
    - How to restart
    - Impact assessment
    """
    alert = Alert(
        alert_type="service_unavailable",
        title="CRITICAL: PostgreSQL Database Service Down",
        message=(
            "PostgreSQL service is not responding. "
            "Last successful connection: 2 minutes ago. "
            "All booking operations are currently failing."
        ),
        priority=AlertPriority.CRITICAL,
        category=AlertCategory.AVAILABILITY,
        source="health_check_monitor",
        resource="postgresql-server",
        metadata={
            "service_name": "postgresql",
            "last_successful_check": "2025-11-10T15:28:00Z",
            "downtime_minutes": 2,
            "failed_connection_attempts": 12,
            "error_message": "could not connect to server: Connection refused",
            "affected_services": [
                "booking_service",
                "payment_service",
                "customer_service",
            ],
            "estimated_customer_impact": "HIGH - All bookings blocked",
        },
        recommendations=[
            "🚨 CRITICAL: Check PostgreSQL service status immediately",
            "✅ Run: sudo systemctl status postgresql",
            "✅ Check logs: sudo journalctl -u postgresql -n 50",
            "✅ Try restart: sudo systemctl restart postgresql",
            "✅ Verify disk space: df -h",
            "✅ Check for port conflicts: sudo netstat -tulpn | grep 5432",
            "📞 If issue persists >5min, escalate to database admin",
            "💡 Enable database replication for high availability",
        ],
        related_logs="/var/log/postgresql/postgresql.log",
        affected_users=50,  # Estimated based on traffic
        error_code="SERVICE_DOWN_POSTGRESQL",
        notification_channels=[
            NotificationChannel.EMAIL,
            NotificationChannel.SMS,
            NotificationChannel.SLACK,
        ],
    )
    
    return alert_service.create_alert(alert)


# ============================================================================
# EXAMPLE 7: SECURITY ALERT - SUSPICIOUS ACTIVITY
# ============================================================================

def example_security_alert(alert_service: AlertService):
    """
    When suspicious activity detected, you get:
    - What happened
    - Who/what IP address
    - Pattern analysis
    - Security recommendations
    """
    alert = Alert(
        alert_type="security_brute_force",
        title="Security Alert: Brute Force Login Attempts Detected",
        message=(
            "45 failed login attempts from IP 203.0.113.42 in last 5 minutes. "
            "Targeting admin accounts."
        ),
        priority=AlertPriority.HIGH,
        category=AlertCategory.SECURITY,
        source="security_monitor",
        resource="admin_login_endpoint",
        metadata={
            "ip_address": "203.0.113.42",
            "failed_attempts": 45,
            "time_window_minutes": 5,
            "targeted_usernames": ["admin", "administrator", "root", "admin@myhibachi.com"],
            "geolocation": "Unknown (VPN detected)",
            "user_agent": "Python-requests/2.28.0",
            "is_ip_blocked": False,
        },
        recommendations=[
            "🚨 IMMEDIATE: Block IP address 203.0.113.42",
            "✅ Run: sudo ufw deny from 203.0.113.42",
            "✅ Enable rate limiting on login endpoint (max 5 attempts per minute)",
            "✅ Implement CAPTCHA after 3 failed attempts",
            "✅ Enable 2FA for all admin accounts",
            "✅ Review other IPs with similar patterns",
            "✅ Check if any admin accounts were compromised",
            "📧 Notify affected users to reset passwords",
        ],
        affected_users=0,  # No successful breaches
        error_code="SEC_BRUTE_FORCE",
        notification_channels=[
            NotificationChannel.EMAIL,
            NotificationChannel.SMS,
            NotificationChannel.SLACK,
        ],
    )
    
    return alert_service.create_alert(alert)


# ============================================================================
# EXAMPLE 8: BUSINESS METRIC ALERT - REVENUE IMPACT
# ============================================================================

def example_business_alert(alert_service: AlertService):
    """
    When business metrics drop, you get:
    - Exact metric and value
    - Comparison to normal
    - Potential revenue impact
    - Business recommendations
    """
    alert = Alert(
        alert_type="business_booking_rate_drop",
        title="Business Alert: Booking Conversion Rate Dropped 35%",
        message=(
            "Booking conversion rate is 4.2% (normal: 6.5%, down 35%). "
            "Estimated revenue impact: $1,200/hour."
        ),
        priority=AlertPriority.HIGH,
        category=AlertCategory.BUSINESS,
        source="analytics_monitor",
        resource="booking_funnel",
        metric_name="conversion_rate_percent",
        metric_value=4.2,
        threshold_value=6.5,
        metadata={
            "normal_rate": 6.5,
            "current_rate": 4.2,
            "drop_percent": 35.4,
            "sessions_last_hour": 450,
            "bookings_last_hour": 19,
            "expected_bookings": 29,
            "revenue_impact_per_hour": 1200,
            "funnel_breakdown": {
                "view_booking_page": 450,
                "start_booking_form": 180,  # 40% (normal: 45%)
                "complete_payment": 19,  # 4.2% (normal: 6.5%)
            },
            "possible_causes": [
                "Payment gateway may be slow or failing",
                "Recent UI changes to booking form",
                "Price increase went live today",
            ],
        },
        recommendations=[
            "🔍 INVESTIGATE: Check payment gateway status (Stripe dashboard)",
            "✅ Test booking flow manually: Create test booking end-to-end",
            "✅ Review error logs for payment failures",
            "✅ Check if price increase is causing cart abandonment",
            "✅ A/B test reverting recent UI changes",
            "✅ Send recovery emails to abandoned carts",
            "💡 Consider adding live chat support during checkout",
        ],
        notification_channels=[
            NotificationChannel.EMAIL,
            NotificationChannel.SLACK,
            NotificationChannel.DASHBOARD,
        ],
    )
    
    return alert_service.create_alert(alert)


# ============================================================================
# HOW TO USE THESE EXAMPLES
# ============================================================================

"""
STEP 1: Initialize AlertService with database session
```python
from core.database import get_db
from monitoring.alert_service import AlertService

db = next(get_db())
alert_service = AlertService(db)
```

STEP 2: Create alerts when issues detected
```python
# Example: Database slow query detected by monitoring
alert_service.create_alert(
    Alert(
        alert_type="database_slow_query",
        title="Slow query on orders table",
        message="Query took 3.2s (threshold: 1.0s)",
        # ... full context as shown in examples above
    )
)
```

STEP 3: View alerts in admin dashboard
```python
# Get active critical alerts
critical_alerts = alert_service.get_active_alerts(
    priority=AlertPriority.CRITICAL
)

for alert in critical_alerts:
    print(f"Alert: {alert.title}")
    print(f"Problem: {alert.message}")
    print(f"Recommendations:")
    for rec in alert.metadata.get('recommendations', []):
        print(f"  - {rec}")
```

STEP 4: Acknowledge and resolve
```python
# Mark as acknowledged (you're working on it)
alert_service.acknowledge_alert(
    alert_id=123,
    acknowledged_by="admin@myhibachi.com",
    notes="Investigating the slow query, checking execution plan"
)

# Mark as resolved (fixed!)
alert_service.resolve_alert(
    alert_id=123,
    resolved_by="admin@myhibachi.com",
    resolution_notes="Added composite index on (customer_id, status). Query now takes 45ms."
)
```

STEP 5: Analyze patterns
```python
# See what keeps happening
patterns = alert_service.get_alert_patterns(days=7)
print(f"Most common alert: {patterns['most_common_type']}")
print(f"Peak hour for alerts: {patterns['peak_hour']}:00")
print(f"Average resolution time: {patterns['avg_resolution_time_minutes']} minutes")
```
"""
