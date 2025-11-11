# Monitoring Rules API - Quick Reference

**Base URL**: `/api/v1/monitoring/rules`

---

## 📚 Quick Links

- **Swagger UI**: http://localhost:8000/docs
- **OpenAPI JSON**: http://localhost:8000/openapi.json
- **Complete Documentation**: [WEEK_2_7_API_ENDPOINTS_COMPLETE.md](./WEEK_2_7_API_ENDPOINTS_COMPLETE.md)

---

## 🚀 Quick Start

### Create Your First Rule

```bash
curl -X POST "http://localhost:8000/api/v1/monitoring/rules" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "High API Response Time",
    "description": "Alert when API response time exceeds 2 seconds",
    "metric_name": "api_response_time_p95_ms",
    "operator": "gt",
    "threshold_value": 2000.0,
    "duration_seconds": 180,
    "cooldown_seconds": 300,
    "severity": "high",
    "enabled": true
  }'
```

### List All Rules

```bash
curl "http://localhost:8000/api/v1/monitoring/rules"
```

### Test a Rule

```bash
curl -X POST "http://localhost:8000/api/v1/monitoring/rules/1/test" \
  -H "Content-Type: application/json" \
  -d '{"test_value": 2500.0}'
```

---

## 📋 All Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/monitoring/rules` | Create new rule |
| `GET` | `/api/v1/monitoring/rules` | List all rules |
| `GET` | `/api/v1/monitoring/rules/{id}` | Get rule details |
| `PATCH` | `/api/v1/monitoring/rules/{id}` | Update rule |
| `DELETE` | `/api/v1/monitoring/rules/{id}` | Delete rule |
| `POST` | `/api/v1/monitoring/rules/{id}/enable` | Enable rule |
| `POST` | `/api/v1/monitoring/rules/{id}/disable` | Disable rule |
| `POST` | `/api/v1/monitoring/rules/{id}/test` | Test rule |
| `GET` | `/api/v1/monitoring/rules/{id}/stats` | Get statistics |
| `POST` | `/api/v1/monitoring/rules/bulk` | Bulk operations |

---

## 🔑 Key Parameters

### Operators

- `gt` - Greater than (>)
- `gte` - Greater than or equal (≥)
- `lt` - Less than (<)
- `lte` - Less than or equal (≤)
- `eq` - Equal (=)
- `ne` - Not equal (≠)

### Severity Levels

- `low` - Low priority
- `medium` - Medium priority  
- `high` - High priority
- `critical` - Critical priority

### Query Filters

- `enabled=true|false` - Filter by enabled status
- `severity=low|medium|high|critical` - Filter by severity
- `metric_name=<name>` - Filter by metric name
- `skip=<number>` - Pagination offset
- `limit=<number>` - Results per page (max 1000)

---

## 💡 Common Use Cases

### 1. Monitor API Performance

```json
{
  "name": "Slow API Responses",
  "metric_name": "api_response_time_p95_ms",
  "operator": "gt",
  "threshold_value": 1000.0,
  "duration_seconds": 300,
  "severity": "high"
}
```

### 2. Monitor Database Connections

```json
{
  "name": "High DB Connections",
  "metric_name": "db_active_connections",
  "operator": "gt",
  "threshold_value": 80.0,
  "duration_seconds": 120,
  "severity": "critical"
}
```

### 3. Monitor Error Rate

```json
{
  "name": "High Error Rate",
  "metric_name": "error_rate_percent",
  "operator": "gt",
  "threshold_value": 5.0,
  "duration_seconds": 60,
  "severity": "high"
}
```

### 4. Monitor System Resources

```json
{
  "name": "High CPU Usage",
  "metric_name": "cpu_usage_percent",
  "operator": "gt",
  "threshold_value": 80.0,
  "duration_seconds": 300,
  "severity": "medium"
}
```

### 5. Monitor User Activity

```json
{
  "name": "Low Active Users",
  "metric_name": "active_users_count",
  "operator": "lt",
  "threshold_value": 10.0,
  "duration_seconds": 600,
  "severity": "low"
}
```

---

## 🧪 Testing Workflow

### 1. Create Test Rule (Disabled)

```bash
curl -X POST "http://localhost:8000/api/v1/monitoring/rules" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Rule",
    "metric_name": "test_metric",
    "operator": "gt",
    "threshold_value": 100.0,
    "enabled": false
  }'
```

### 2. Test with Different Values

```bash
# Test with value below threshold
curl -X POST "http://localhost:8000/api/v1/monitoring/rules/1/test" \
  -d '{"test_value": 50.0}'

# Test with value above threshold
curl -X POST "http://localhost:8000/api/v1/monitoring/rules/1/test" \
  -d '{"test_value": 150.0}'
```

### 3. Enable When Ready

```bash
curl -X POST "http://localhost:8000/api/v1/monitoring/rules/1/enable"
```

### 4. Monitor Performance

```bash
curl "http://localhost:8000/api/v1/monitoring/rules/1/stats"
```

---

## 🔧 Bulk Operations

### Disable Multiple Rules

```bash
curl -X POST "http://localhost:8000/api/v1/monitoring/rules/bulk" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_ids": [1, 2, 3],
    "operation": "disable"
  }'
```

### Enable Multiple Rules

```bash
curl -X POST "http://localhost:8000/api/v1/monitoring/rules/bulk" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_ids": [4, 5, 6],
    "operation": "enable"
  }'
```

### Delete Multiple Rules

```bash
curl -X POST "http://localhost:8000/api/v1/monitoring/rules/bulk" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_ids": [7, 8, 9],
    "operation": "delete"
  }'
```

---

## 📊 Filtering Examples

### Get Only Enabled Rules

```bash
curl "http://localhost:8000/api/v1/monitoring/rules?enabled=true"
```

### Get Critical Severity Rules

```bash
curl "http://localhost:8000/api/v1/monitoring/rules?severity=critical"
```

### Get Rules for Specific Metric

```bash
curl "http://localhost:8000/api/v1/monitoring/rules?metric_name=api_response_time_p95_ms"
```

### Pagination

```bash
# First 10 rules
curl "http://localhost:8000/api/v1/monitoring/rules?skip=0&limit=10"

# Next 10 rules
curl "http://localhost:8000/api/v1/monitoring/rules?skip=10&limit=10"
```

### Combined Filters

```bash
curl "http://localhost:8000/api/v1/monitoring/rules?enabled=true&severity=high&limit=20"
```

---

## 🐍 Python Examples

### Using requests

```python
import requests

BASE_URL = "http://localhost:8000/api/v1/monitoring/rules"

# Create rule
rule_data = {
    "name": "High Error Rate",
    "metric_name": "error_rate_percent",
    "operator": "gt",
    "threshold_value": 5.0,
    "duration_seconds": 60,
    "severity": "high",
    "enabled": True
}
response = requests.post(BASE_URL, json=rule_data)
rule_id = response.json()["id"]

# List rules
response = requests.get(BASE_URL)
rules = response.json()

# Test rule
test_data = {"test_value": 7.5}
response = requests.post(f"{BASE_URL}/{rule_id}/test", json=test_data)
print(response.json()["message"])

# Disable rule
requests.post(f"{BASE_URL}/{rule_id}/disable")

# Delete rule
requests.delete(f"{BASE_URL}/{rule_id}")
```

### Using httpx (async)

```python
import httpx
import asyncio

BASE_URL = "http://localhost:8000/api/v1/monitoring/rules"

async def manage_rules():
    async with httpx.AsyncClient() as client:
        # Create rule
        rule_data = {
            "name": "High CPU",
            "metric_name": "cpu_usage_percent",
            "operator": "gt",
            "threshold_value": 80.0,
            "enabled": True
        }
        response = await client.post(BASE_URL, json=rule_data)
        rule = response.json()
        
        # Test rule
        test_data = {"test_value": 85.0}
        response = await client.post(
            f"{BASE_URL}/{rule['id']}/test",
            json=test_data
        )
        print(response.json())

asyncio.run(manage_rules())
```

---

## 🌐 JavaScript/TypeScript Examples

### Using fetch

```javascript
const BASE_URL = 'http://localhost:8000/api/v1/monitoring/rules';

// Create rule
const createRule = async () => {
  const response = await fetch(BASE_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: 'High Memory Usage',
      metric_name: 'memory_usage_percent',
      operator: 'gt',
      threshold_value: 85.0,
      duration_seconds: 180,
      severity: 'high',
      enabled: true
    })
  });
  return response.json();
};

// List rules
const listRules = async (filters = {}) => {
  const params = new URLSearchParams(filters);
  const response = await fetch(`${BASE_URL}?${params}`);
  return response.json();
};

// Test rule
const testRule = async (ruleId, testValue) => {
  const response = await fetch(`${BASE_URL}/${ruleId}/test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ test_value: testValue })
  });
  return response.json();
};

// Disable rule
const disableRule = async (ruleId) => {
  const response = await fetch(`${BASE_URL}/${ruleId}/disable`, {
    method: 'POST'
  });
  return response.json();
};
```

### Using axios

```typescript
import axios from 'axios';

const BASE_URL = 'http://localhost:8000/api/v1/monitoring/rules';

interface AlertRule {
  name: string;
  metric_name: string;
  operator: string;
  threshold_value: number;
  duration_seconds?: number;
  severity?: string;
  enabled?: boolean;
}

// Create rule
const createRule = async (rule: AlertRule) => {
  const response = await axios.post(BASE_URL, rule);
  return response.data;
};

// List rules with filters
const listRules = async (filters?: {
  enabled?: boolean;
  severity?: string;
  skip?: number;
  limit?: number;
}) => {
  const response = await axios.get(BASE_URL, { params: filters });
  return response.data;
};

// Bulk disable
const bulkDisable = async (ruleIds: number[]) => {
  const response = await axios.post(`${BASE_URL}/bulk`, {
    rule_ids: ruleIds,
    operation: 'disable'
  });
  return response.data;
};
```

---

## ⚠️ Error Handling

### Common Error Responses

**404 Not Found**:
```json
{
  "detail": "Rule 123 not found"
}
```

**400 Bad Request**:
```json
{
  "detail": "Rule with name 'Test Rule' already exists"
}
```

**422 Validation Error**:
```json
{
  "detail": [
    {
      "loc": ["body", "threshold_value"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**500 Internal Server Error**:
```json
{
  "detail": "Failed to create rule: Database connection error"
}
```

---

## 🎯 Best Practices

### 1. Test Before Enabling

Always create rules as disabled and test them first:

```bash
# Create disabled
curl -X POST "http://localhost:8000/api/v1/monitoring/rules" \
  -d '{"name": "Test", "enabled": false, ...}'

# Test with different values
curl -X POST "http://localhost:8000/api/v1/monitoring/rules/1/test" \
  -d '{"test_value": 100}'

# Enable when confident
curl -X POST "http://localhost:8000/api/v1/monitoring/rules/1/enable"
```

### 2. Use Appropriate Durations

- **Short duration (60s)**: For critical issues
- **Medium duration (300s)**: For important but not urgent
- **Long duration (600s+)**: For trending issues

### 3. Set Cooldowns Wisely

- Prevent alert spam
- Typical: 300s (5 minutes)
- Critical: 60s (1 minute)
- Low priority: 1800s (30 minutes)

### 4. Use Tags for Organization

```json
{
  "tags": ["api", "performance", "production"],
  "metadata": {
    "team": "backend",
    "oncall": "john@example.com"
  }
}
```

### 5. Monitor Rule Performance

```bash
# Check trigger count
curl "http://localhost:8000/api/v1/monitoring/rules/1/stats"

# List most triggered rules
curl "http://localhost:8000/api/v1/monitoring/rules" | \
  jq 'sort_by(.trigger_count) | reverse | .[0:5]'
```

---

## 📖 Additional Resources

- **Complete Documentation**: [WEEK_2_7_API_ENDPOINTS_COMPLETE.md](./WEEK_2_7_API_ENDPOINTS_COMPLETE.md)
- **Monitoring System Overview**: See Week 2.1-2.6 documentation
- **Swagger UI**: http://localhost:8000/docs
- **Source Code**: `apps/backend/src/routers/v1/monitoring_rules.py`

---

**Last Updated**: 2025 (Week 2.7 completion)
**Version**: 1.0
**Status**: Production-ready ✅
