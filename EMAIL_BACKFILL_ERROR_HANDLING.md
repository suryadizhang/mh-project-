# Email Backfill Error Handling & Fallback Guide

**Last Updated**: November 2025 **Status**: ✅ Production-Ready

---

## Overview

The email backfill script now includes **enterprise-level error
handling** integrated with the existing ErrorLog system. All errors
are logged to the `error_logs` table and can be viewed in the admin
dashboard.

### Key Features

✅ **Database Error Logging** - All errors written to `error_logs`
table ✅ **Severity Classification** - CRITICAL, ERROR, WARNING levels
✅ **Correlation ID Tracking** - Unique operation ID for all related
errors ✅ **Automatic Retry Logic** - Exponential backoff for
transient failures ✅ **Graceful Degradation** - Continue processing
even when emails fail ✅ **Critical Error Detection** - Automatic
abort on catastrophic failures ✅ **Comprehensive Fallback
Mechanisms** - Multiple recovery strategies

---

## Error Logging Architecture

### ErrorLog Integration

The backfill script uses `EmailBackfillErrorLogger` which integrates
with the existing `ErrorLog` model in
`middleware/structured_logging.py`.

**ErrorLog Model Fields**:

- `correlation_id` - Unique operation ID (tracks all errors for this
  backfill run)
- `timestamp` - When error occurred
- `error_type` - Exception class name (e.g., `ConnectionError`,
  `TimeoutError`)
- `error_message` - Human-readable error message
- `error_traceback` - Full Python traceback for debugging
- `level` - Severity: `CRITICAL`, `ERROR`, `WARNING`
- `resolved` - Resolution status (0 = unresolved, 1 = resolved)
- `request_body` - Context information (batch number, email ID, etc.)

### Error Categories

| Category                | Severity | Retry?              | Action                         |
| ----------------------- | -------- | ------------------- | ------------------------------ |
| IMAP Connection Failed  | CRITICAL | ✅ Yes (3 attempts) | Abort if all retries fail      |
| Email Fetch Failed      | ERROR    | ✅ Yes (3 attempts) | Skip email, continue batch     |
| Database Sync Failed    | ERROR    | ✅ Yes (3 attempts) | Skip email, continue batch     |
| Batch Processing Failed | ERROR    | ❌ No               | Log error, continue next batch |
| Operation Aborted       | CRITICAL | ❌ No               | Stop all processing            |

---

## Retry Logic

### Exponential Backoff Strategy

```python
max_retries = 3
retry_delay = 2  # seconds

# Retry sequence:
# Attempt 1: Immediate
# Attempt 2: Wait 2s  (2 * 2^0)
# Attempt 3: Wait 4s  (2 * 2^1)
# Attempt 4: Wait 8s  (2 * 2^2)
```

### What Gets Retried?

✅ **IMAP Connection**

- Network timeouts
- Connection refused
- SSL/TLS errors

✅ **Email Fetching**

- IMAP fetch failures
- Malformed email data
- Encoding errors

✅ **Database Syncing**

- Database connection issues
- Transaction conflicts
- Temporary database locks

❌ **Not Retried**:

- Duplicate emails (expected behavior)
- Missing credentials (configuration error)
- Invalid inbox name (user error)

---

## Fallback Mechanisms

### 1. Skip and Continue (Individual Email Failures)

**When**: Email fetch or sync fails after all retries **Action**: Log
error, increment error counter, continue with next email **Result**:
Batch processing continues

```
✅ Email 1: Synced
❌ Email 2: Failed (logged to ErrorLog) → SKIP
✅ Email 3: Synced
✅ Email 4: Synced
```

### 2. Batch-Level Recovery (Batch Failures)

**When**: Entire batch fails due to exception **Action**: Log batch
error, continue with next batch **Result**: Other batches still
processed

```
✅ Batch 1: Complete (100 emails)
❌ Batch 2: FAILED (logged to ErrorLog) → CONTINUE
✅ Batch 3: Complete (100 emails)
```

### 3. Critical Error Abort (Catastrophic Failures)

**When**: Critical errors detected OR >50% failure rate **Action**:
Abort entire operation, log critical error **Result**: Operation
stops, manual intervention required

**Triggers**:

- IMAP connection fails after all retries
- Database completely unavailable
- Invalid credentials
- `should_abort_operation()` returns True

---

## Error Logging Examples

### Example 1: IMAP Connection Error

```python
# Error logged to database:
{
  "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "error_type": "ConnectionError",
  "error_message": "Failed to connect to imap.ionos.com:993",
  "level": "ERROR",
  "request_body": {
    "connection_type": "IMAP",
    "retry_attempt": 3
  },
  "inbox": "customer_support"
}
```

### Example 2: Email Sync Error

```python
{
  "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "error_type": "DatabaseError",
  "error_message": "Unique constraint violation on message_id",
  "level": "ERROR",
  "request_body": {
    "database_operation": "sync_email"
  },
  "email_id": "12345"
}
```

### Example 3: Batch Processing Error

```python
{
  "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "error_type": "TimeoutError",
  "error_message": "Database query timeout after 30s",
  "level": "ERROR",
  "request_body": {
    "batch_number": 5,
    "batch_size": 100,
    "emails_processed": 47,
    "completion_percentage": 47.0
  }
}
```

### Example 4: Critical Failure

```python
{
  "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "error_type": "ValueError",
  "error_message": "GMAIL_APP_PASSWORD_IMAP not set in environment",
  "level": "CRITICAL",
  "request_body": {
    "critical_operation": "get_imap_monitor",
    "recovery_attempted": False,
    "requires_manual_intervention": True
  }
}
```

---

## Viewing Errors in Admin Dashboard

### Accessing Error Logs

1. **Admin Dashboard** → **Error Logs** section
2. Filter by correlation ID to see all errors from a specific backfill
   run
3. Errors are ordered by timestamp (newest first)
4. Unresolved errors highlighted

### Error Log Fields

| Field          | Description           | Example                                |
| -------------- | --------------------- | -------------------------------------- |
| Correlation ID | Unique operation ID   | `a1b2c3d4-...`                         |
| Timestamp      | When error occurred   | `2025-11-25 14:30:45 UTC`              |
| Level          | Severity              | `CRITICAL`, `ERROR`, `WARNING`         |
| Error Type     | Exception class       | `ConnectionError`                      |
| Message        | Human-readable error  | `IMAP connection failed`               |
| Traceback      | Full Python traceback | `Traceback (most recent call last)...` |
| Context        | Additional info       | Batch #, email ID, etc.                |
| Resolved       | Resolution status     | `0` (unresolved) / `1` (resolved)      |

### Resolving Errors

Once you've addressed an error:

1. Click **Resolve** button in admin dashboard
2. Add resolution notes (e.g., "Fixed credentials")
3. Error marked as resolved (`resolved = 1`)

---

## Statistics & Monitoring

### Enhanced Statistics Output

```
================================================================================
📊 BACKFILL COMPLETE
================================================================================
   Total fetched: 1000
   Total synced:  950 ✅
   Total skipped: 25 ⏭️  (duplicates)
   Total errors:  25 ❌
   Total retries: 15 🔄
   Elapsed time:  45.3s
   Success rate:  95.0%

📝 ERROR SUMMARY (logged to database):
   Critical: 0 🔴
   Errors:   25 🟠
   Warnings: 0 🟡
   Operation ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
   View in admin dashboard under Error Logs
================================================================================
```

### Success Rate Calculation

```python
success_rate = (total_synced / total_fetched) * 100

# Example:
# 950 synced / 1000 fetched = 95% success rate
```

### Retry Rate

```python
# If total_retries = 15 and total_errors = 25:
# - 15 errors were retried and recovered
# - 10 errors failed even after retries
```

---

## Troubleshooting

### High Error Rate (>10%)

**Symptoms**: More than 10% of emails failing to sync **Possible
Causes**:

- IMAP server issues (check `imap.ionos.com` or `imap.gmail.com`
  status)
- Database connection problems (check PostgreSQL logs)
- Malformed email data (check error traceback for parsing errors)

**Resolution**:

1. Check error logs for common error types
2. Filter by correlation ID to see all related errors
3. Address root cause (credentials, network, database)
4. Re-run backfill for failed emails

### Critical Errors

**Symptoms**: Operation aborted immediately **Possible Causes**:

- Missing environment variables (`GMAIL_APP_PASSWORD_IMAP`,
  `SMTP_PASSWORD`)
- Invalid credentials
- Database unavailable
- IMAP server completely down

**Resolution**:

1. Check error log with `level = CRITICAL`
2. Read `request_body` for context
3. Fix configuration issue
4. Re-run backfill

### All Emails Skipped

**Symptoms**: `total_skipped = total_fetched`, `total_synced = 0`
**Cause**: Emails already in database (duplicate detection working
correctly) **Resolution**: This is expected behavior if backfill
already ran successfully

---

## Best Practices

### 1. Monitor Error Logs During Backfill

```bash
# Run backfill in one terminal
python -m scripts.backfill_emails --inbox customer_support

# Watch error logs in another terminal (PostgreSQL)
psql -d myhibachi -c "SELECT * FROM error_logs ORDER BY timestamp DESC LIMIT 10;"
```

### 2. Review Errors After Completion

1. Note the **Operation ID** from the final statistics
2. Query error logs by correlation ID:
   ```sql
   SELECT error_type, COUNT(*) as count
   FROM error_logs
   WHERE correlation_id = 'a1b2c3d4-...'
   GROUP BY error_type
   ORDER BY count DESC;
   ```
3. Identify most common error types
4. Address root causes

### 3. Re-Run Failed Emails

If backfill fails with high error rate:

1. Fix root cause (credentials, network, database)
2. Re-run backfill script
3. Duplicate detection will skip already-synced emails
4. Only failed emails will be retried

### 4. Clean Up Test Runs

For dry-run or test environments:

```sql
-- Delete error logs from test operations
DELETE FROM error_logs
WHERE correlation_id = 'test-operation-id';
```

---

## Configuration

### Environment Variables Required

```bash
# Customer Support Inbox (IONOS)
SMTP_PASSWORD=your-ionos-password

# Payments Inbox (Gmail)
GMAIL_USER=myhibachichef@gmail.com
GMAIL_APP_PASSWORD_IMAP=your-gmail-app-password
```

### Retry Configuration

Edit `backfill_emails.py` to adjust retry behavior:

```python
class EmailBackfillService:
    def __init__(self, db: AsyncSession):
        # ...
        self.max_retries = 3      # Number of retry attempts
        self.retry_delay = 2      # Base delay in seconds
```

**Retry Delay Formula**: `delay = retry_delay * (2 ** attempt)`

---

## API Reference

### `EmailBackfillErrorLogger`

**Constructor**:

```python
logger = EmailBackfillErrorLogger(
    db=db,                    # AsyncSession
    operation_id=None         # Auto-generates UUID if not provided
)
```

**Methods**:

#### `log_error(error, context, severity, email_id, inbox)`

Log general error to database.

**Parameters**:

- `error` (Exception): The exception that occurred
- `context` (dict, optional): Additional context information
- `severity` (str): `"CRITICAL"`, `"ERROR"`, or `"WARNING"`
- `email_id` (str, optional): IMAP email ID being processed
- `inbox` (str, optional): Inbox name

#### `log_batch_error(batch_number, batch_size, error, emails_processed)`

Log batch processing error.

**Parameters**:

- `batch_number` (int): Batch number that failed
- `batch_size` (int): Size of the batch
- `error` (Exception): The exception that occurred
- `emails_processed` (int): Emails successfully processed in batch

#### `log_critical_failure(operation, error, recovery_attempted)`

Log critical failure that stops the backfill.

**Parameters**:

- `operation` (str): Operation that failed critically
- `error` (Exception): The exception that occurred
- `recovery_attempted` (bool): Whether automatic recovery was
  attempted

#### `log_imap_connection_error(inbox, error, retry_attempt)`

Log IMAP connection error.

**Parameters**:

- `inbox` (str): Inbox that failed to connect
- `error` (Exception): Connection error
- `retry_attempt` (int, optional): Retry attempt number

#### `log_database_error(operation, error, email_id)`

Log database operation error.

**Parameters**:

- `operation` (str): Database operation that failed
- `error` (Exception): Database error
- `email_id` (str, optional): Email ID being processed

#### `get_error_summary()`

Get summary of errors logged.

**Returns**: `dict`

```python
{
    "critical": 0,
    "errors": 25,
    "warnings": 0,
    "total": 25,
    "operation_id": "a1b2c3d4-..."
}
```

#### `should_abort_operation(threshold_percentage=50.0)`

Determine if operation should be aborted.

**Returns**: `bool` - True if critical errors detected

---

## Migration Guide

### From Old Error Handling

**Before** (basic logging):

```python
except Exception as e:
    logger.exception(f"Error: {e}")
    stats["total_errors"] += 1
```

**After** (ErrorLog integration):

```python
except Exception as e:
    await error_logger.log_error(
        error=e,
        context={"operation": "sync_email"},
        severity="ERROR",
        email_id=str(email_id),
        inbox=inbox,
    )
    logger.exception(f"Error: {e}")
    stats["total_errors"] += 1
```

### Benefits

✅ **Centralized Error Tracking** - All errors in one database table
✅ **Admin Visibility** - View/resolve errors in admin dashboard ✅
**Correlation** - Track all errors for a specific operation ✅
**Analytics** - Query error patterns and trends ✅ **Audit Trail** -
Complete error history with resolution status

---

## FAQ

### Q: What happens if ErrorLog database write fails?

**A**: The error logger has a fallback mechanism:

1. Attempts to write to `error_logs` table
2. If database write fails, logs to standard Python logger
3. Original error is still logged to console
4. Script continues processing (doesn't crash)

### Q: Can I disable error logging to database?

**A**: Not recommended, but you can modify the code to skip ErrorLog
writes. However, you'll lose admin dashboard visibility and error
analytics.

### Q: How do I find all errors from a specific backfill run?

**A**: Use the correlation ID (Operation ID) shown in the final
statistics:

```sql
SELECT * FROM error_logs
WHERE correlation_id = 'your-operation-id'
ORDER BY timestamp;
```

### Q: What if I get >50% error rate?

**A**: The operation will automatically abort to prevent data issues.
Review the error logs, fix the root cause, and re-run.

### Q: Are duplicate emails logged as errors?

**A**: No. Duplicates are expected behavior and logged to standard
logger only (not ErrorLog table).

---

## Related Documentation

- [EMAIL_BACKFILL_GUIDE.md](./EMAIL_BACKFILL_GUIDE.md) - Main backfill
  usage guide
- [EMAIL_INTEGRATION_COMPLETE.md](./EMAIL_INTEGRATION_COMPLETE.md) -
  Email system overview
- [middleware/structured_logging.py](../apps/backend/src/middleware/structured_logging.py) -
  ErrorLog model

---

## Changelog

### November 2025 - Initial Release

- ✅ Created `EmailBackfillErrorLogger` class
- ✅ Integrated with ErrorLog model
- ✅ Added retry logic with exponential backoff
- ✅ Implemented graceful degradation
- ✅ Added critical error detection
- ✅ Enhanced statistics with error summary
- ✅ Added correlation ID tracking
- ✅ Documented all error handling mechanisms
