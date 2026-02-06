# 🏥 Comprehensive Health Check System

**Status:** ✅ **PRODUCTION READY**  
**Created:** October 12, 2025  
**Purpose:** Kubernetes-ready health checks with Prometheus metrics

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Endpoints](#endpoints)
3. [Kubernetes Configuration](#kubernetes-configuration)
4. [Monitoring & Metrics](#monitoring--metrics)
5. [Service Checks](#service-checks)
6. [Troubleshooting](#troubleshooting)
7. [Development Guide](#development-guide)

---

## 🎯 Overview

Comprehensive health check system designed for production Kubernetes
deployments with:

- **Readiness Probe** - Determines if service can accept traffic
- **Liveness Probe** - Detects if process is alive
- **Detailed Health** - Comprehensive metrics for monitoring
- **Prometheus Metrics** - Health check telemetry
- **Individual Service Checks** - Database, Redis, Stripe, etc.

### Architecture

```
┌─────────────────────────────────────────────────┐
│         Health Check System                      │
├─────────────────────────────────────────────────┤
│                                                  │
│  /api/v1/health/readiness  ← K8s Readiness     │
│  /api/v1/health/liveness   ← K8s Liveness      │
│  /api/v1/health/detailed   ← Monitoring        │
│  /api/v1/health/           ← Basic Check        │
│                                                  │
├─────────────────────────────────────────────────┤
│         Individual Service Checks                │
├─────────────────────────────────────────────────┤
│  ✅ PostgreSQL Database    (CRITICAL)           │
│  ✅ Redis Cache            (DEGRADED OK)        │
│  ✅ Stripe API             (DEGRADED OK)        │
│  ✅ System Metrics         (INFO ONLY)          │
└─────────────────────────────────────────────────┘
```

---

## 🔌 Endpoints

### 1. Readiness Probe (`/api/v1/health/readiness`)

**Purpose:** Kubernetes readiness probe - determines if service is
ready to accept traffic.

**HTTP Method:** `GET`

**Response Codes:**

- `200 OK` - Service is ready
- `503 Service Unavailable` - Service not ready

**Response Schema:**

```json
{
  "status": "ready",
  "timestamp": "2025-10-12T10:30:00Z",
  "ready": true,
  "details": "All critical services ready",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 15.3,
      "details": "Database connected and responsive",
      "timestamp": "2025-10-12T10:30:00Z"
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 2.1,
      "details": "Redis connected (memory: 128.5MB)",
      "timestamp": "2025-10-12T10:30:00Z"
    },
    "stripe": {
      "status": "healthy",
      "response_time_ms": 1.2,
      "details": "Stripe API key configured (webhook secret configured)",
      "timestamp": "2025-10-12T10:30:00Z"
    }
  }
}
```

**Critical Checks:**

- ✅ **Database** - MUST be healthy (returns 503 if unhealthy)
- ⚠️ **Redis** - Can be degraded (falls back to memory cache)
- ⚠️ **Stripe** - Can be degraded (non-payment endpoints still work)

**Example Request:**

```bash
curl http://localhost:8000/api/v1/health/readiness
```

---

### 2. Liveness Probe (`/api/v1/health/liveness`)

**Purpose:** Kubernetes liveness probe - checks if process is alive.

**HTTP Method:** `GET`

**Response Codes:**

- `200 OK` - Always (unless process completely hung)

**Response Schema:**

```json
{
  "status": "alive",
  "timestamp": "2025-10-12T10:30:00Z",
  "uptime_seconds": 3600.5,
  "pid": 12345
}
```

**Notes:**

- Should **ALWAYS** return 200 unless process is frozen
- Does NOT check external dependencies
- Lightweight and fast (<1ms)

**Example Request:**

```bash
curl http://localhost:8000/api/v1/health/liveness
```

---

### 3. Detailed Health (`/api/v1/health/detailed`)

**Purpose:** Comprehensive health check with full system metrics.

**HTTP Method:** `GET`

**Response Codes:**

- `200 OK` - System healthy or degraded
- `500 Internal Server Error` - Critical failure

**Response Schema:**

```json
{
  "status": "healthy",
  "timestamp": "2025-10-12T10:30:00Z",
  "uptime_seconds": 3600.5,
  "version": "1.0.0",
  "environment": "production",
  "services": {
    "database": {
      "status": "healthy",
      "response_time_ms": 15.3,
      "details": "..."
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 2.1,
      "details": "..."
    },
    "stripe": {
      "status": "healthy",
      "response_time_ms": 1.2,
      "details": "..."
    }
  },
  "system": {
    "cpu": {
      "count": 8,
      "usage_percent": 25.3
    },
    "memory": {
      "total_gb": 16.0,
      "available_gb": 8.5,
      "used_gb": 7.5,
      "used_percent": 46.9
    },
    "disk": {
      "total_gb": 100.0,
      "free_gb": 55.2,
      "used_gb": 44.8,
      "used_percent": 44.8
    },
    "process": {
      "pid": 12345,
      "memory_mb": 512.5,
      "cpu_percent": 5.2,
      "threads": 10,
      "open_files": 25
    }
  },
  "configuration": {
    "environment": "production",
    "debug_mode": false,
    "log_level": "INFO",
    "cors_enabled": true,
    "rate_limiting_enabled": true,
    "database_url_configured": true,
    "redis_url_configured": true,
    "stripe_configured": true,
    "email_configured": true
  }
}
```

**Use Cases:**

- Monitoring dashboards (Grafana, Datadog)
- Performance analysis
- Debugging production issues
- **NOT for K8s probes** (too heavy)

**Example Request:**

```bash
curl http://localhost:8000/api/v1/health/detailed | jq
```

---

### 4. Basic Health (`/api/v1/health/`)

**Purpose:** Backward compatibility, simple alive check.

**HTTP Method:** `GET`

**Response Schema:**

```json
{
  "status": "healthy",
  "timestamp": "2025-10-12T10:30:00Z",
  "uptime_seconds": 3600.5,
  "service": "myhibachi-backend"
}
```

---

## ☸️ Kubernetes Configuration

### Deployment YAML

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myhibachi-backend
  namespace: production
spec:
  replicas: 3
  template:
    spec:
      containers:
        - name: backend
          image: myhibachi/backend:latest
          ports:
            - containerPort: 8000
              name: http

          # === Readiness Probe ===
          readinessProbe:
            httpGet:
              path: /api/v1/health/readiness
              port: 8000
              scheme: HTTP
            initialDelaySeconds: 10 # Wait 10s after container starts
            periodSeconds: 10 # Check every 10 seconds
            timeoutSeconds: 5 # Timeout after 5 seconds
            successThreshold: 1 # 1 success = ready
            failureThreshold: 3 # 3 failures = not ready

          # === Liveness Probe ===
          livenessProbe:
            httpGet:
              path: /api/v1/health/liveness
              port: 8000
              scheme: HTTP
            initialDelaySeconds: 30 # Wait 30s for app startup
            periodSeconds: 30 # Check every 30 seconds
            timeoutSeconds: 5 # Timeout after 5 seconds
            successThreshold: 1 # 1 success = alive
            failureThreshold: 3 # 3 failures = restart pod

          # === Startup Probe (Optional) ===
          startupProbe:
            httpGet:
              path: /api/v1/health/liveness
              port: 8000
            initialDelaySeconds: 0
            periodSeconds: 5
            timeoutSeconds: 3
            successThreshold: 1
            failureThreshold: 30 # 30 * 5s = 150s max startup time

          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: backend-secrets
                  key: database-url
            - name: REDIS_URL
              valueFrom:
                secretKeyRef:
                  name: backend-secrets
                  key: redis-url

          resources:
            requests:
              memory: '512Mi'
              cpu: '500m'
            limits:
              memory: '1Gi'
              cpu: '1000m'
```

### Service YAML

```yaml
apiVersion: v1
kind: Service
metadata:
  name: myhibachi-backend-svc
  namespace: production
spec:
  selector:
    app: myhibachi-backend
  ports:
    - name: http
      port: 80
      targetPort: 8000
  type: ClusterIP
```

### Probe Timing Guidelines

| Probe         | Initial Delay | Period | Timeout | Failure Threshold | Notes                                            |
| ------------- | ------------- | ------ | ------- | ----------------- | ------------------------------------------------ |
| **Readiness** | 10s           | 10s    | 5s      | 3                 | Remove from load balancer after 30s (3 failures) |
| **Liveness**  | 30s           | 30s    | 5s      | 3                 | Restart pod after 90s (3 failures)               |
| **Startup**   | 0s            | 5s     | 3s      | 30                | Max 150s startup time (30 failures)              |

### Best Practices

1. **Readiness vs Liveness:**
   - Use **readiness** for temporary issues (DB connection lost)
   - Use **liveness** for permanent issues (deadlock, memory leak)

2. **Failure Thresholds:**
   - Set `failureThreshold >= 3` to avoid false positives
   - Consider network latency and load

3. **Timeout Values:**
   - Set `timeoutSeconds` based on p95 response times
   - Add 2-3x buffer for peak load

4. **Period Values:**
   - Readiness: Check frequently (10-15s)
   - Liveness: Check infrequently (30-60s)

---

## 📊 Monitoring & Metrics

### Prometheus Metrics

The health check system exports the following Prometheus metrics:

#### 1. Request Counter

```
health_check_total{endpoint="readiness",status="ready"} 1500
health_check_total{endpoint="liveness",status="alive"} 3000
health_check_total{endpoint="detailed",status="healthy"} 250
```

**Labels:**

- `endpoint`: readiness, liveness, detailed
- `status`: ready/not_ready, alive, healthy/unhealthy/error

#### 2. Response Time Histogram

```
health_check_duration_seconds{endpoint="readiness",check_type="all"} 0.025
health_check_duration_seconds{endpoint="liveness",check_type="simple"} 0.001
health_check_duration_seconds{endpoint="detailed",check_type="comprehensive"} 0.150
```

**Labels:**

- `endpoint`: readiness, liveness, detailed
- `check_type`: all, simple, comprehensive

**Buckets:** 0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5,
5, 10

#### 3. Service Health Gauge

```
service_health_status{service="database"} 1
service_health_status{service="redis"} 1
service_health_status{service="stripe"} 1
```

**Labels:**

- `service`: database, redis, stripe

**Values:**

- `1` = healthy
- `0` = unhealthy

### Grafana Dashboard

Example Prometheus queries for Grafana:

**Health Check Success Rate:**

```promql
sum(rate(health_check_total{status="ready"}[5m]))
/
sum(rate(health_check_total[5m]))
```

**Health Check P95 Response Time:**

```promql
histogram_quantile(0.95,
  sum(rate(health_check_duration_seconds_bucket[5m])) by (le, endpoint)
)
```

**Service Availability:**

```promql
avg(service_health_status) by (service) * 100
```

**Pod Restart Rate:**

```promql
rate(kube_pod_container_status_restarts_total{pod=~"myhibachi-backend.*"}[1h])
```

### Alerting Rules

```yaml
groups:
  - name: health_checks
    interval: 30s
    rules:
      # Database unhealthy
      - alert: DatabaseUnhealthy
        expr: service_health_status{service="database"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: 'Database health check failing'
          description:
            'Database is unreachable or unhealthy for 2+ minutes'

      # Redis degraded (warning only)
      - alert: RedisDegraded
        expr: service_health_status{service="redis"} == 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: 'Redis health check failing'
          description:
            'Redis is unavailable, using memory cache fallback'

      # Health check timeout
      - alert: HealthCheckTimeout
        expr: |
          histogram_quantile(0.95, 
            sum(rate(health_check_duration_seconds_bucket{endpoint="readiness"}[5m])) by (le)
          ) > 3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: 'Health checks taking too long'
          description: 'P95 health check duration > 3 seconds'

      # Pod restart loop
      - alert: PodRestartLoop
        expr: |
          rate(kube_pod_container_status_restarts_total{pod=~"myhibachi-backend.*"}[15m]) > 0.1
        labels:
          severity: critical
        annotations:
          summary: 'Pod restart loop detected'
          description: 'Pod restarting more than 1.5 times per minute'
```

---

## 🔍 Service Checks

### 1. Database Check (PostgreSQL)

**Purpose:** Verify database connectivity and performance.

**Tests:**

- Connection availability
- Execute `SELECT 1` query
- Execute `SELECT version()` query
- Measure response time

**Status Levels:**

- **healthy** - Connection successful, queries execute < 100ms
- **unhealthy** - Connection failed or exception

**Critical:** YES - Service cannot operate without database

**Example Response:**

```json
{
  "status": "healthy",
  "response_time_ms": 15.3,
  "details": "Database connected and responsive (query time: 15.30ms)",
  "timestamp": "2025-10-12T10:30:00Z"
}
```

---

### 2. Redis Check

**Purpose:** Verify Redis cache connectivity and performance.

**Tests:**

- Connection availability
- PING command
- Memory usage query
- Measure response time

**Status Levels:**

- **healthy** - Connected, PING successful, memory info retrieved
- **degraded** - Connection failed (falls back to memory cache)
- **unhealthy** - Timeout or critical error

**Critical:** NO - Service has memory cache fallback

**Example Response:**

```json
{
  "status": "healthy",
  "response_time_ms": 2.1,
  "details": "Redis connected (memory: 128.5MB, ping: 2.10ms)",
  "timestamp": "2025-10-12T10:30:00Z"
}
```

**Degraded Response:**

```json
{
  "status": "degraded",
  "response_time_ms": 1500.0,
  "details": "Redis connection failed (using memory cache fallback)",
  "error": "Connection timeout",
  "timestamp": "2025-10-12T10:30:00Z"
}
```

---

### 3. Stripe Check

**Purpose:** Verify Stripe API configuration (no actual API call).

**Tests:**

- API key environment variable exists
- API key format validation (starts with `sk_`)
- Webhook secret configuration (optional)

**Status Levels:**

- **healthy** - API key configured and valid format
- **unhealthy** - API key missing or invalid format

**Critical:** NO - Only payment endpoints need Stripe

**Example Response:**

```json
{
  "status": "healthy",
  "response_time_ms": 1.2,
  "details": "Stripe API key configured (webhook secret configured)",
  "timestamp": "2025-10-12T10:30:00Z"
}
```

---

### 4. System Metrics

**Purpose:** Collect system performance metrics.

**Collected Metrics:**

- **CPU:** Count, usage percentage
- **Memory:** Total, available, used (GB and %)
- **Disk:** Total, free, used (GB and %)
- **Process:** PID, memory, CPU, threads, open files

**Status:** Informational only (not used for readiness)

**Requires:** `psutil` Python package

**Example Response:**

```json
{
  "cpu": {
    "count": 8,
    "usage_percent": 25.3
  },
  "memory": {
    "total_gb": 16.0,
    "available_gb": 8.5,
    "used_gb": 7.5,
    "used_percent": 46.9
  },
  "disk": {
    "total_gb": 100.0,
    "free_gb": 55.2,
    "used_gb": 44.8,
    "used_percent": 44.8
  },
  "process": {
    "pid": 12345,
    "memory_mb": 512.5,
    "cpu_percent": 5.2,
    "threads": 10,
    "open_files": 25
  }
}
```

---

## 🔧 Troubleshooting

### Problem: Readiness probe failing

**Symptoms:**

- Pods showing "0/1 Ready"
- No traffic reaching pods
- `kubectl describe pod` shows readiness failures

**Check:**

```bash
# Test readiness endpoint directly
kubectl exec -it <pod-name> -- curl http://localhost:8000/api/v1/health/readiness

# Check pod logs
kubectl logs <pod-name> | grep -i "health\|database\|redis"

# Check events
kubectl describe pod <pod-name> | grep -A 10 Events
```

**Common Causes:**

1. **Database Unreachable**
   - Check DATABASE_URL environment variable
   - Verify database service is running
   - Check network policies/firewall rules
   - Test database connection manually

2. **Database Connection Pool Exhausted**
   - Check concurrent connections
   - Increase pool size in configuration
   - Look for connection leaks

3. **Slow Database Queries**
   - Check database performance
   - Review slow query logs
   - Optimize database indexes

**Fix:**

```yaml
# Increase timeout if queries are slow
readinessProbe:
  timeoutSeconds: 10 # Increase from 5 to 10
  failureThreshold: 5 # More tolerance
```

---

### Problem: Liveness probe failing (pod restarting)

**Symptoms:**

- Pods constantly restarting
- High restart count
- Application logs truncated

**Check:**

```bash
# Check restart count
kubectl get pods | grep myhibachi-backend

# Check previous pod logs
kubectl logs <pod-name> --previous | tail -100

# Check liveness endpoint
kubectl exec -it <pod-name> -- curl http://localhost:8000/api/v1/health/liveness
```

**Common Causes:**

1. **Application Deadlock**
   - Thread pool exhausted
   - Database connection deadlock
   - Infinite loop

2. **Memory Leak**
   - OOM (Out of Memory)
   - Heap exhaustion
   - File descriptor leak

3. **Slow Startup**
   - Application taking too long to start
   - Database migrations running
   - Data loading

**Fix:**

```yaml
# Increase initial delay for slow startup
livenessProbe:
  initialDelaySeconds: 60 # Increase from 30 to 60
  periodSeconds: 60 # Check less frequently

# Or use startup probe
startupProbe:
  httpGet:
    path: /api/v1/health/liveness
    port: 8000
  failureThreshold: 60 # 60 * 5s = 300s max startup
  periodSeconds: 5
```

---

### Problem: Health checks timing out

**Symptoms:**

- Health check taking > 5 seconds
- Timeout errors in logs
- Intermittent failures

**Check:**

```bash
# Test health check response time
time curl http://localhost:8000/api/v1/health/readiness

# Check detailed metrics
curl http://localhost:8000/api/v1/health/detailed | jq '.services[].response_time_ms'
```

**Common Causes:**

1. **Database Slow**
   - Long-running queries blocking
   - Database overloaded
   - Network latency

2. **Resource Exhaustion**
   - CPU at 100%
   - Memory swap thrashing
   - Disk I/O saturation

3. **Connection Pool Exhausted**
   - All connections in use
   - Waiting for available connection

**Fix:**

```yaml
# Increase resource limits
resources:
  limits:
    memory: '2Gi' # Increase from 1Gi
    cpu: '2000m' # Increase from 1000m

# Increase timeouts
readinessProbe:
  timeoutSeconds: 10 # Increase from 5
```

---

### Problem: Redis check always degraded

**Symptoms:**

- Redis status showing "degraded"
- Using memory cache fallback
- No actual Redis connection

**Check:**

```bash
# Verify REDIS_URL environment variable
kubectl exec -it <pod-name> -- env | grep REDIS

# Test Redis connectivity
kubectl exec -it <pod-name> -- redis-cli -u $REDIS_URL ping

# Check Redis service
kubectl get svc | grep redis
```

**Common Causes:**

1. **Redis Service Not Running**
   - Redis pod not started
   - Redis service not created
   - Wrong namespace

2. **Incorrect REDIS_URL**
   - Wrong hostname
   - Wrong port
   - Wrong database number

3. **Network Policy Blocking**
   - NetworkPolicy preventing connection
   - Firewall rules

**Fix:**

```bash
# Deploy Redis if missing
helm install redis bitnami/redis

# Update REDIS_URL in secret
kubectl create secret generic backend-secrets \
  --from-literal=redis-url=redis://redis-master:6379/0
```

---

## 🛠️ Development Guide

### Local Development

**Start Services:**

```bash
# Start PostgreSQL
docker run -d --name postgres \
  -e POSTGRES_USER=myhibachi \
  -e POSTGRES_PASSWORD=dev_password \
  -e POSTGRES_DB=myhibachi \
  -p 5432:5432 \
  postgres:15

# Start Redis
docker run -d --name redis \
  -p 6379:6379 \
  redis:7-alpine

# Set environment variables
export DATABASE_URL="postgresql://<username>:<password>@localhost:5432/myhibachi"
export REDIS_URL="redis://localhost:6379/0"
export STRIPE_SECRET_KEY="sk_test_..."
```

**Run Backend:**

```bash
cd apps/backend
python -m uvicorn main:app --reload --port 8000
```

**Test Endpoints:**

```bash
# Readiness
curl http://localhost:8000/api/v1/health/readiness | jq

# Liveness
curl http://localhost:8000/api/v1/health/liveness | jq

# Detailed
curl http://localhost:8000/api/v1/health/detailed | jq

# Check response time
time curl -s http://localhost:8000/api/v1/health/readiness > /dev/null
```

---

### Adding New Service Checks

**Step 1:** Create check function in `api/v1/endpoints/health.py`:

```python
async def check_email_service() -> ServiceHealthCheck:
    """Check email service connectivity."""
    start_time = time.time()

    try:
        from api.app.config import settings

        # Your check logic here
        smtp_configured = bool(getattr(settings, 'SMTP_USER', None))

        if not smtp_configured:
            return ServiceHealthCheck(
                status="unhealthy",
                details="Email service not configured"
            )

        response_time = (time.time() - start_time) * 1000

        return ServiceHealthCheck(
            status="healthy",
            response_time_ms=round(response_time, 2),
            details="Email service configured"
        )

    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return ServiceHealthCheck(
            status="unhealthy",
            response_time_ms=round(response_time, 2),
            details="Email service check failed",
            error=str(e)
        )
```

**Step 2:** Add to readiness probe:

```python
@router.get("/readiness")
async def readiness_probe(request: Request):
    # Add your check
    checks_results = await asyncio.gather(
        check_database(db),
        check_redis(request),
        check_stripe(),
        check_email_service(),  # NEW
        return_exceptions=True
    )

    # Parse results
    db_check, redis_check, stripe_check, email_check = checks_results

    checks = {
        "database": db_check,
        "redis": redis_check,
        "stripe": stripe_check,
        "email": email_check  # NEW
    }
```

**Step 3:** Update Prometheus metrics:

```python
if PROMETHEUS_AVAILABLE:
    SERVICE_HEALTH_GAUGE.labels(service='email').set(
        1 if email_check.status == "healthy" else 0
    )
```

---

### Testing Health Checks

**Unit Tests:**

```python
import pytest
from fastapi.testclient import TestClient

def test_readiness_probe_healthy(client: TestClient):
    """Test readiness probe returns 200 when services healthy."""
    response = client.get("/api/v1/health/readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["ready"] is True
    assert "database" in data["checks"]

def test_readiness_probe_db_down(client: TestClient, mock_db_error):
    """Test readiness probe returns 503 when database down."""
    response = client.get("/api/v1/health/readiness")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "not_ready"
    assert data["ready"] is False
```

**Integration Tests:**

```bash
# Test with real services
pytest tests/integration/test_health_checks.py -v

# Test with mocked services
pytest tests/unit/test_health_endpoints.py -v
```

---

## 📚 References

- [Kubernetes Liveness and Readiness Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
- [FastAPI Health Checks](https://fastapi.tiangolo.com/)
- [Health Check Response Format (RFC 7807)](https://datatracker.ietf.org/doc/html/rfc7807)

---

## ✅ Checklist

- [x] Readiness probe endpoint implemented
- [x] Liveness probe endpoint implemented
- [x] Detailed health endpoint implemented
- [x] Database connectivity check
- [x] Redis connectivity check
- [x] Stripe configuration check
- [x] System metrics collection
- [x] Prometheus metrics integration
- [x] Timeout protection (2 seconds)
- [x] Graceful degradation
- [x] Comprehensive documentation
- [x] Kubernetes YAML examples
- [x] Troubleshooting guide
- [x] Development setup guide

---

**Last Updated:** October 12, 2025  
**Status:** ✅ **PRODUCTION READY**  
**Maintainer:** DevOps Team
