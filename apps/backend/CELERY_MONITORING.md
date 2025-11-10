# 🌸 Celery Task Monitoring with Flower

## Overview

Flower is a web-based monitoring tool for Celery that provides
real-time insights into your background task processing system.

**Access URL:** http://localhost:5555 (development)

**Default Credentials:**

- Username: `admin`
- Password: `admin123`

⚠️ **IMPORTANT:** Change these credentials in production via
environment variables!

---

## 🚀 Quick Start

### Development Mode

Run the launch script to start all services:

```powershell
cd apps/backend
.\start-celery-dev.ps1
```

This will open 3 terminal windows:

1. **Celery Worker** - Processes tasks
2. **Celery Beat** - Schedules periodic tasks
3. **Flower Dashboard** - Monitoring UI at http://localhost:5555

### Manual Start (Alternative)

If you prefer to start services manually:

```bash
# Terminal 1 - Worker
celery -A src.workers.celery_config worker -l info --pool=solo

# Terminal 2 - Beat
celery -A src.workers.celery_config beat -l info

# Terminal 3 - Flower
celery -A src.workers.celery_config flower --port=5555 \
  --basic_auth=admin:admin123
```

---

## 📊 What Can Super Admin See?

### 1. **Dashboard** (Home Page)

- **Active Tasks:** Tasks currently being processed
- **Task Success Rate:** Percentage of tasks completed successfully
- **Task Throughput:** Tasks/minute processing rate
- **Worker Status:** Online/offline workers
- **Broker Connection:** Redis connection health

### 2. **Tasks Page**

Real-time task monitoring:

| Task Name                    | Status  | Runtime | Args              | Result             |
| ---------------------------- | ------- | ------- | ----------------- | ------------------ |
| send_escalation_notification | SUCCESS | 2.3s    | escalation_id=123 | {"status": "sent"} |
| fetch_call_recording         | RUNNING | -       | recording_id=456  | -                  |
| cleanup_old_recordings       | PENDING | -       | -                 | -                  |

**Task Statuses:**

- 🟢 **SUCCESS** - Completed successfully
- 🔵 **RUNNING** - Currently executing
- 🟡 **PENDING** - Waiting in queue
- 🔴 **FAILURE** - Failed with error
- ⚪ **RETRY** - Being retried

### 3. **Workers Page**

Monitor worker health:

- Worker hostname and status (online/offline)
- Number of active tasks per worker
- Memory usage and CPU load
- Task completion count
- Last heartbeat time

### 4. **Monitor Page** (Real-time Updates)

Live stream of task events:

```
[13:45:23] Task send_customer_sms[abc123] received
[13:45:24] Task send_customer_sms[abc123] started
[13:45:26] Task send_customer_sms[abc123] succeeded in 2.1s
```

### 5. **Broker Page**

Redis connection status:

- Connection string
- Number of active connections
- Queue lengths
- Memory usage

### 6. **Task Details**

Click any task to see:

- **Arguments:** Input parameters (phone number, escalation_id, etc.)
- **Result:** Return value or error traceback
- **Exception:** Full error details if failed
- **Execution Time:** How long it took
- **Retries:** Number of retry attempts
- **Worker:** Which worker processed it
- **Timestamp:** When it was executed

---

## 🔍 Common Monitoring Scenarios

### Check if SMS/Call Tasks are Working

1. Open Flower: http://localhost:5555
2. Navigate to **Tasks** tab
3. Filter by task name: `send_customer_sms` or
   `initiate_outbound_call`
4. Check status:
   - ✅ GREEN (SUCCESS) = Working correctly
   - ❌ RED (FAILURE) = Click to see error details

### Monitor Call Recording Downloads

1. Go to **Tasks** tab
2. Search: `fetch_call_recording`
3. Check:
   - How many recordings are being downloaded
   - Average download time
   - Any failures (check RingCentral API issues)

### View Scheduled Tasks

1. Go to **Beat Schedule** section
2. See next execution times:
   ```
   cleanup_old_recordings     Next: 2:00 AM (in 8 hours)
   archive_old_recordings     Next: 3:00 AM (in 9 hours)
   ```

### Troubleshoot Failed Tasks

1. **Tasks** → Filter by "FAILURE"
2. Click failed task
3. View **Exception** section for error:
   ```python
   RingCentralAPIError: SMS delivery failed
   Response: {"error": "Invalid phone number"}
   ```
4. Check **Args** to see what data caused failure
5. Check **Retries** to see if auto-retry is happening

### Monitor System Performance

1. **Dashboard** shows:
   - Tasks/minute throughput
   - Average task execution time
   - Queue backlog (if tasks are piling up)

2. **Workers** page shows:
   - If workers are overloaded
   - Memory/CPU usage
   - If any workers have died

---

## 🔔 Alert Scenarios for Admins

### 🚨 Critical Issues

**1. Worker Offline**

- **What it means:** Background tasks are not being processed
- **Impact:** SMS not sent, recordings not downloaded, escalations
  stuck
- **How to spot:** Workers page shows red "OFFLINE" status
- **Fix:** Restart worker process

**2. High Task Failure Rate**

- **What it means:** Many tasks are failing (e.g., RingCentral API
  issues)
- **Impact:** Customer escalations not reaching admins
- **How to spot:** Dashboard shows <80% success rate
- **Fix:** Check error logs in failed tasks

**3. Queue Backlog Growing**

- **What it means:** Tasks are queuing faster than being processed
- **Impact:** Delays in SMS delivery, call recordings
- **How to spot:** Dashboard shows increasing "Pending" count
- **Fix:** Scale up workers or investigate slow tasks

### ⚠️ Warning Issues

**4. Slow Task Execution**

- **What it means:** Individual tasks taking too long
- **Impact:** Reduced throughput
- **How to spot:** Monitor page shows tasks >10 seconds
- **Fix:** Check network issues or API rate limits

**5. Scheduled Tasks Not Running**

- **What it means:** Beat scheduler is down or misconfigured
- **Impact:** Old recordings not deleted, metrics not sent
- **How to spot:** Beat Schedule shows missed executions
- **Fix:** Restart beat scheduler

---

## 🔒 Production Security

### Change Default Credentials

In `.env` file:

```bash
FLOWER_ADMIN_USERNAME=super_admin
FLOWER_ADMIN_PASSWORD=StrongP@ssw0rd!2024
```

### Enable HTTPS (Production)

Use reverse proxy (Nginx) to add SSL:

```nginx
# /etc/nginx/sites-available/flower
server {
    listen 443 ssl;
    server_name flower.myhibachi.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:5555;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### IP Whitelist (Optional)

Restrict access to admin IPs only:

```nginx
location / {
    allow 203.0.113.0/24;  # Office IP range
    deny all;
    proxy_pass http://localhost:5555;
}
```

---

## 📈 Performance Metrics to Watch

| Metric        | Healthy Range | Warning | Critical |
| ------------- | ------------- | ------- | -------- |
| Success Rate  | >95%          | 90-95%  | <90%     |
| Avg Task Time | <5 seconds    | 5-10s   | >10s     |
| Queue Length  | <10           | 10-50   | >50      |
| Worker CPU    | <70%          | 70-85%  | >85%     |
| Worker Memory | <1GB          | 1-2GB   | >2GB     |

---

## 🛠️ Troubleshooting Commands

### Check Worker Status

```bash
celery -A src.workers.celery_config inspect active
```

### Purge All Queues (CAUTION: Deletes pending tasks)

```bash
celery -A src.workers.celery_config purge
```

### View Task Statistics

```bash
celery -A src.workers.celery_config inspect stats
```

### Check Scheduled Tasks

```bash
celery -A src.workers.celery_config inspect scheduled
```

---

## 📞 Integration with MyHibachi Features

### Escalation Flow Monitoring

When customer requests human help:

1. **Customer clicks "Talk to Human"** →
   `send_escalation_notification` task queued

2. **Flower shows:**

   ```
   send_escalation_notification [RUNNING]
   Args: escalation_id=789, customer_phone=+1234567890
   ```

3. **Task completes:**

   ```
   send_escalation_notification [SUCCESS] 1.8s
   Result: {"sms_sent": true, "notification_sent": true}
   ```

4. **If SMS fails:**
   ```
   send_customer_sms [FAILURE]
   Exception: RingCentralAPIError("Rate limit exceeded")
   Retries: 1/3
   ```

### Call Recording Flow

1. **Call ends** → RingCentral webhook triggers
2. **`fetch_call_recording` task queued**
3. **Flower shows download progress:**
   ```
   fetch_call_recording [RUNNING] 5.2s
   Args: recording_id=456, rc_recording_uri=/recordings/...
   ```
4. **Success:**
   ```
   [SUCCESS] 12.1s
   Result: {"file_path": "/var/www/.../2024/11/recording_456.mp3"}
   ```

---

## 💡 Pro Tips

1. **Bookmark Flower Dashboard** - Keep it open during business hours
2. **Set up alerts** - Monitor success rate and worker status
3. **Check logs daily** - Review failed tasks each morning
4. **Scale workers** - Add more workers during peak hours
5. **Archive old task results** - Clear history monthly to keep UI
   fast

---

## 🆘 Support

If you see persistent issues:

1. Check worker logs in terminal
2. Verify Redis is running: `redis-cli ping`
3. Check RingCentral API status: https://status.ringcentral.com
4. Review task error details in Flower
5. Contact dev team with task ID and error traceback

---

**Remember:** Flower is your window into the background task system.
If something's wrong with SMS, calls, or recordings, Flower will show
you exactly what's happening! 🌸
