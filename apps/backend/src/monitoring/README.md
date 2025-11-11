# Monitoring & AlertService

**Production-ready alerting system with detailed diagnostics and actionable recommendations.**

## 🎯 Purpose

Instead of generic alerts like "something broke", this system provides:
- ✅ **Specific error details** (what, where, when, why)
- ✅ **Actionable recommendations** (how to fix)
- ✅ **Full diagnostic context** (stack traces, logs, metrics)
- ✅ **Impact assessment** (how many users affected)
- ✅ **Pattern analysis** (is this recurring?)

## 📁 Structure

```
monitoring/
├── __init__.py              # Package exports
├── models.py                # Database models (AlertModel, AlertRule)
├── alert_service.py         # Core service (800+ lines)
├── ALERT_EXAMPLES.py        # Usage examples with 8 scenarios
└── README.md                # This file
```

## 🚀 Quick Start

### 1. Run Database Migration

```bash
cd apps/backend
alembic upgrade head
```

This creates:
- `monitoring_alerts` table - stores all alerts
- `monitoring_alert_rules` table - configurable thresholds
- 10+ indexes for fast queries

### 2. Initialize AlertService

```python
from monitoring.alert_service import AlertService, Alert, AlertPriority, AlertCategory
from monitoring.models import NotificationChannel
from db.session import get_db

db = next(get_db())
alert_service = AlertService(db)
```

### 3. Create Your First Alert

```python
# Simple system alert
alert = alert_service.create_system_alert(
    metric_name="cpu_percent",
    current_value=92,
    threshold_value=80,
    resource="web-server-01",
)

# What you get:
# - Title: "High CPU Usage - web-server-01"
# - Message: "CPU is at 92% (threshold: 80%, exceeded by 15.0%)"
# - Priority: HIGH (auto-calculated)
# - Recommendations: ["Check for runaway processes...", "Review deployments...", ...]
```

## 📊 Real-World Examples

### Example 1: Database Slow Query

```python
alert = Alert(
    alert_type="database_slow_query",
    title="Slow Database Query on Bookings Table",
    message="Query took 5.23 seconds (threshold: 1.0s, exceeded by 423%)",
    priority=AlertPriority.HIGH,
    category=AlertCategory.DATABASE,
    resource="bookings table",
    metadata={
        "query": "SELECT * FROM bookings WHERE customer_id = ?",
        "execution_plan": "Seq Scan on bookings (50,000 rows)",
        "rows_scanned": 50000,
    },
    recommendations=[
        "✅ Add index: CREATE INDEX idx_bookings_customer_id ON bookings(customer_id)",
        "✅ Review execution plan: EXPLAIN ANALYZE SELECT ...",
        "⚠️ Current sequential scan is reading all 50k rows",
    ],
    related_logs="/var/log/postgresql/slow_queries.log",
    affected_users=15,
)

db_alert = alert_service.create_alert(alert)
```

**What makes this specific?**
- Exact query that's slow
- How slow (5.23s vs 1.0s threshold = 423% overage)
- Why it's slow (sequential scan, 50k rows)
- How to fix (add specific index with exact SQL command)
- Where to investigate (/var/log/postgresql/slow_queries.log)
- Business impact (15 users affected)

### Example 2: High CPU with Process Details

```python
alert = alert_service.create_system_alert(
    metric_name="cpu_percent",
    current_value=95.3,
    threshold_value=80.0,
    resource="web-server-01",
)

# Enhance with process details
alert.metadata.update({
    "top_processes": [
        {"name": "gunicorn", "cpu": 45.2, "pid": 12345},
        {"name": "celery", "cpu": 30.1, "pid": 12346},
    ],
    "load_average": [8.5, 7.2, 6.1],
})
```

**What makes this actionable?**
- Specific process consuming CPU (gunicorn PID 12345 at 45%)
- Exact commands to investigate (`htop -p 12345`)
- Load average trend (is it getting worse?)
- When to escalate (if >30min, restart service)

### Example 3: Application Error with Stack Trace

```python
alert = alert_service.create_application_error_alert(
    error_type="StripeAPIError",
    error_message="Card declined: insufficient_funds",
    stack_trace="Traceback...\n  File booking_service.py...\n  StripeAPIError...",
    source="booking_service",
    affected_endpoint="POST /api/v1/bookings",
    affected_users=3,
    error_count=5,
)
```

**What makes this debuggable?**
- Full stack trace (exact line of code)
- Which endpoint failed (POST /api/v1/bookings)
- Business impact (3 users, 5 failed transactions)
- Auto-generated recommendations (check Stripe status, add retry logic)

## 🎨 Alert Categories

| Category | Use Case | Priority Levels | Example |
|----------|----------|----------------|---------|
| **SYSTEM** | CPU, memory, disk | CRITICAL, HIGH, MEDIUM | CPU at 95% |
| **DATABASE** | Slow queries, connection pools | CRITICAL, HIGH | Query took 5s |
| **APPLICATION** | Code errors, crashes | CRITICAL, HIGH, MEDIUM | NullPointerException |
| **PERFORMANCE** | Response times, throughput | HIGH, MEDIUM | API P95 > 1s |
| **SECURITY** | Brute force, suspicious activity | CRITICAL, HIGH | 45 failed logins |
| **BUSINESS** | Conversion drops, revenue impact | HIGH, MEDIUM | Booking rate -35% |
| **AVAILABILITY** | Service down, health checks | CRITICAL | PostgreSQL down |

## 🔔 Notification Channels

```python
from monitoring.models import NotificationChannel

alert = Alert(
    ...,
    notification_channels=[
        NotificationChannel.EMAIL,    # Send email
        NotificationChannel.SMS,      # Send text message (critical only)
        NotificationChannel.SLACK,    # Post to #alerts channel
        NotificationChannel.WEBHOOK,  # POST to custom endpoint
        NotificationChannel.DISCORD,  # Discord webhook
        NotificationChannel.DASHBOARD, # Show in admin dashboard
    ]
)
```

## 📈 Alert Lifecycle

```
ACTIVE → ACKNOWLEDGED → RESOLVED
   ↓
SUPPRESSED (temporary)
   ↓
EXPIRED (auto-resolved after TTL)
```

### Acknowledge Alert

```python
# Someone is working on it
alert_service.acknowledge_alert(
    alert_id=123,
    acknowledged_by="admin@myhibachi.com",
    notes="Investigating slow query, checking execution plan"
)
```

### Resolve Alert

```python
# Problem fixed!
alert_service.resolve_alert(
    alert_id=123,
    resolved_by="admin@myhibachi.com",
    resolution_notes="Added composite index on (customer_id, status). Query now takes 45ms."
)
```

### Suppress Alert (Maintenance Mode)

```python
# Temporarily mute during planned maintenance
alert_service.suppress_alert(
    alert_id=456,
    suppressed_by="admin@myhibachi.com",
    reason="Planned database maintenance",
    duration_hours=2
)
```

## 📊 Pattern Analysis

```python
# Analyze last 7 days of alerts
patterns = alert_service.get_alert_patterns(days=7)

print(f"Total alerts: {patterns['total_alerts']}")
print(f"Most common: {patterns['most_common_type']}")
print(f"Peak hour: {patterns['peak_hour']}:00")
print(f"Avg resolution: {patterns['avg_resolution_time_minutes']} minutes")

# Type distribution
for alert_type, count in patterns['type_distribution'].items():
    print(f"  {alert_type}: {count}")

# Hourly pattern (detect rush hours)
for hour, count in enumerate(patterns['hourly_distribution']):
    if count > 5:
        print(f"⚠️ High alert volume at {hour}:00 ({count} alerts)")
```

**Example insights:**
```
Total alerts: 45
Most common: database_slow_query (12 occurrences)
Peak hour: 14:00 (lunch rush)
Avg resolution: 32.5 minutes

Hourly distribution:
  12:00 → 8 alerts  (lunch prep)
  14:00 → 12 alerts (lunch rush) ⚠️
  18:00 → 7 alerts  (dinner prep)
  
💡 Insight: Database queries slow down during lunch rush
✅ Action: Add indexes, optimize queries, scale database before 12 PM
```

## 🧠 Smart Features

### 1. Auto-Priority Calculation

```python
# System alerts: based on threshold overage
if overage > 50%:
    priority = CRITICAL  # 50%+ over threshold
elif overage > 20%:
    priority = HIGH      # 20-50% over
else:
    priority = MEDIUM    # <20% over

# Application errors: based on impact
if "database" in error_type or affected_users > 10:
    priority = CRITICAL
elif error_count > 5:
    priority = HIGH
```

### 2. Context-Aware Recommendations

```python
# Database errors → check connections, credentials, locks
# Memory errors → heap dumps, leak analysis
# Timeout errors → response times, circuit breakers
# Performance → slow operations, deployments, profiling
```

### 3. Deduplication (Prevent Alert Spam)

```python
# If same alert_type + resource within last hour:
#   → Increment notification_count
#   → Don't create duplicate

# Example: CPU high alert every minute
# Result: 1 alert with notification_count=60 (not 60 separate alerts)
```

### 4. Rich Metadata Storage

```python
alert.metadata = {
    "query": "SELECT * FROM...",           # What happened
    "execution_plan": "Seq Scan...",       # How it happened
    "recommendations": [...],               # How to fix
    "stack_trace": "...",                  # Full trace
    "related_logs": "/var/log/...",        # Where to look
    "affected_users": 15,                  # Business impact
    "top_processes": [...],                # System state
    # ... any custom data
}
```

## 🔌 Integration with Existing Systems

### Connect to System Health Monitor

```python
# ops/system_health_monitor.py
from monitoring.alert_service import AlertService

class SystemHealthMonitor:
    def __init__(self):
        self.alert_service = AlertService(db)
    
    def check_cpu(self):
        cpu_percent = psutil.cpu_percent()
        
        if cpu_percent > self.cpu_threshold:
            self.alert_service.create_system_alert(
                metric_name="cpu_percent",
                current_value=cpu_percent,
                threshold_value=self.cpu_threshold,
                resource=socket.gethostname(),
            )
```

### Connect to Prometheus Metrics

```python
# Monitor Prometheus metrics and create alerts
from prometheus_client import Gauge

response_time = Gauge('api_response_time_seconds', 'API response time')

def monitor_api_performance():
    p95 = get_p95_response_time()
    
    if p95 > 1.0:  # Threshold: 1 second
        alert_service.create_performance_alert(
            metric_name="api_response_time_ms",
            current_value=p95 * 1000,
            threshold_value=1000,
            resource="/api/bookings",
            percentile="P95",
        )
```

### Connect to Sentry Error Tracking

```python
# sentry_sdk integration
import sentry_sdk

def sentry_before_send(event, hint):
    # Create alert from Sentry event
    alert_service.create_application_error_alert(
        error_type=event['exception']['values'][0]['type'],
        error_message=event['exception']['values'][0]['value'],
        stack_trace=str(hint['exc_info']),
        source=event['request']['url'],
    )
    return event

sentry_sdk.init(before_send=sentry_before_send)
```

## 🧪 Testing

```python
# tests/test_alert_service.py
import pytest
from monitoring.alert_service import AlertService, Alert, AlertPriority

def test_create_system_alert(db_session):
    service = AlertService(db_session)
    
    alert = service.create_system_alert(
        metric_name="cpu_percent",
        current_value=95,
        threshold_value=80,
        resource="test-server",
    )
    
    assert alert.priority == AlertPriority.CRITICAL  # >50% over threshold
    assert "exceeded by" in alert.message
    assert len(alert.metadata['recommendations']) > 0

def test_deduplication(db_session):
    service = AlertService(db_session)
    
    # Create same alert twice
    alert1 = service.create_system_alert(...)
    alert2 = service.create_system_alert(...)  # Same type + resource
    
    assert alert1.id == alert2.id  # Same alert
    assert alert2.notification_count == 2  # Count incremented
```

## 📚 Complete Examples

See [`ALERT_EXAMPLES.py`](./ALERT_EXAMPLES.py) for 8 detailed scenarios:
1. Database Slow Query
2. High CPU Usage
3. Application Error with Stack Trace
4. Memory Leak Detection
5. API Performance Degradation
6. Service Unavailable
7. Security/Brute Force Attack
8. Business Metric Drop

## 🎯 Next Steps

1. ✅ **Week 1: AlertService** ← YOU ARE HERE
2. ⏳ **Week 2: ThresholdMonitor** - Define alert rules
3. ⏳ **Week 3: NotificationChannel** - Email/SMS/Slack delivery
4. ⏳ **Week 4: Dashboard** - Admin UI for alert management
5. ⏳ **Week 5: Testing & Docs** - Production validation

## 🤔 FAQ

**Q: How is this different from generic logging?**
A: Logs say "something happened". Alerts say "something BAD happened, here's exactly what's wrong, and here's how to fix it".

**Q: Won't this create alert fatigue?**
A: No! Deduplication prevents spam, smart priority prevents over-alerting, and suppression allows maintenance windows.

**Q: Can I customize recommendations?**
A: Yes! Pass custom `recommendations` list, or let the service auto-generate based on error type.

**Q: How do I know what's a "normal" threshold?**
A: Use pattern analysis to see historical data, then set thresholds at P95 + 20% headroom.

**Q: What if I want alerts in Microsoft Teams?**
A: Add `NotificationChannel.TEAMS` enum and implement in NotificationChannel service (Week 3).

## 🚀 Production Checklist

- [x] Database models defined
- [x] AlertService implemented
- [x] Migration created
- [x] Examples documented
- [ ] Run migration: `alembic upgrade head`
- [ ] Connect to system_health_monitor.py
- [ ] Add alert rules for your metrics
- [ ] Set up notification channels
- [ ] Test end-to-end alert flow
- [ ] Monitor alert patterns weekly

---

**Remember:** Specific alerts = faster debugging = happier customers! 🎉
