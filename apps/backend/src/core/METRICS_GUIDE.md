# Prometheus Metrics Management Guide

## 🎯 Single Source of Truth

**`core/metrics.py`** is the **ONLY** place where the metrics registry
is created.

### ✅ Correct Pattern: Import Registry

```python
# ✅ CORRECT - Import registry from core.metrics
from core.metrics import registry
from prometheus_client import Counter, Histogram

# Define your domain-specific metrics
my_custom_metric = Counter(
    "my_metric_total",
    "Description of my metric",
    ["label1", "label2"],
    registry=registry  # ← ALWAYS use the shared registry
)
```

### ❌ Wrong Pattern: Create New Registry

```python
# ❌ WRONG - Never create a new registry
from prometheus_client import CollectorRegistry, Counter

registry = CollectorRegistry()  # ← This causes conflicts!
my_metric = Counter("my_metric_total", "...", registry=registry)
```

### ❌ Wrong Pattern: Use Default Registry

```python
# ❌ WRONG - Metrics without explicit registry use REGISTRY (global default)
from prometheus_client import Counter

my_metric = Counter("my_metric_total", "...")  # ← Uses global registry, causes conflicts
```

## 📊 Creating Domain-Specific Metrics

### Example: Voice AI Metrics

```python
# services/realtime_voice/metrics.py
from core.metrics import registry  # ← Import shared registry
from prometheus_client import Counter, Gauge, Histogram

# Define voice-specific metrics
voice_calls_total = Counter(
    "voice_calls_total",
    "Total voice calls",
    ["status"],
    registry=registry  # ← Use shared registry
)

voice_call_duration = Histogram(
    "voice_call_duration_seconds",
    "Call duration",
    ["status"],
    registry=registry,
    buckets=(5, 10, 30, 60, 120, 300, 600)
)
```

## 🔒 Preventing Double Registration

### Problem

During tests, modules can be imported multiple times, causing:

```
ValueError: Duplicated timeseries in CollectorRegistry
```

### Solution 1: Module-Level Guard (Preferred)

```python
# Only define metrics at module level - they auto-register on first import
from core.metrics import registry
from prometheus_client import Counter

# This runs only once per Python process
my_metric = Counter("my_metric_total", "...", registry=registry)
```

### Solution 2: Try/Except for Tests

```python
try:
    my_metric = Counter("my_metric_total", "...", registry=registry)
except ValueError:
    # Already registered (test re-import)
    for collector in registry._collector_to_names:
        if hasattr(collector, '_name') and collector._name == 'my_metric_total':
            my_metric = collector
            break
```

## 📈 Using Existing Metrics

### Core HTTP Metrics

```python
from core.metrics import request_count, request_duration

# Record HTTP request
request_count.labels(method="GET", endpoint="/api/users", status="200").inc()
request_duration.labels(method="GET", endpoint="/api/users").observe(0.123)
```

### Security Metrics

```python
from core.metrics import security_violations

# Record security violation
security_violations.labels(violation_type="rate_limit_exceeded").inc()
```

### Cache Metrics

```python
from core.metrics import cache_hits, cache_misses

cache_hits.labels(cache_key_prefix="user").inc()
cache_misses.labels(cache_key_prefix="booking").inc()
```

## 🧪 Testing with Metrics

### conftest.py Setup

```python
import pytest
from prometheus_client import REGISTRY

@pytest.fixture(autouse=True)
def clear_metrics():
    """Clear metrics between tests"""
    # Clear collectors (optional, only if needed)
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass

    yield

    # Cleanup after test
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass
```

### Using Custom Registry in Tests

```python
from core.metrics import registry  # Use our custom registry, not REGISTRY

def test_my_metric():
    """Test metric recording"""
    from services.my_module.metrics import my_metric

    initial_value = my_metric._value.get()
    my_metric.inc()
    assert my_metric._value.get() == initial_value + 1
```

## 🚀 Best Practices

1. **Always import `registry` from `core.metrics`**
2. **Define metrics at module level** (not inside functions)
3. **Use descriptive metric names** with domain prefix (e.g.,
   `voice_calls_total`, not `calls`)
4. **Document your labels** - what values do they accept?
5. **Use appropriate metric types**:
   - **Counter**: Monotonically increasing (requests, errors)
   - **Gauge**: Can go up/down (active connections, queue size)
   - **Histogram**: Distributions (latency, sizes)
   - **Summary**: Similar to histogram, but calculates quantiles
6. **Add appropriate buckets** for histograms based on expected values
7. **Keep labels low cardinality** - avoid user IDs, UUIDs as labels

## 📦 Metrics Endpoint

Metrics are exposed at `/metrics`:

```bash
curl http://localhost:8000/metrics
```

Output:

```
# HELP voice_calls_total Total voice calls
# TYPE voice_calls_total counter
voice_calls_total{status="completed"} 42.0
voice_calls_total{status="failed"} 3.0

# HELP voice_call_duration_seconds Call duration
# TYPE voice_call_duration_seconds histogram
voice_call_duration_seconds_bucket{status="completed",le="5.0"} 10.0
voice_call_duration_seconds_bucket{status="completed",le="10.0"} 25.0
...
```

## 🐛 Troubleshooting

### Error: "Duplicated timeseries in CollectorRegistry"

**Cause**: Metric is being registered twice

**Solution**:

1. Check you're importing `registry` from `core.metrics`
2. Ensure metric is defined at module level, not in function
3. Don't manually call `registry.register()`

### Error: "No module named 'core.metrics'"

**Cause**: Wrong import path or missing src in PYTHONPATH

**Solution**:

```python
# Add to conftest.py or test runner
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
```

### Metrics not appearing at /metrics

**Cause**: Using wrong registry or metrics not initialized

**Solution**: Verify you're using `registry` from `core.metrics`, not
`REGISTRY` from prometheus_client

## 📚 References

- [Prometheus Client Python Docs](https://github.com/prometheus/client_python)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
