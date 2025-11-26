# Email Backfill Guide

## Overview

The email backfill script syncs existing emails from IMAP to
PostgreSQL database. This is a **one-time operation** that should be
run after the initial deployment to populate the database with
historical emails.

### 🔥 **NEW: Enterprise Error Handling** 🔥

The backfill script now includes comprehensive error handling
integrated with the ErrorLog system:

- ✅ All errors logged to database (`error_logs` table)
- ✅ Automatic retry with exponential backoff
- ✅ Graceful degradation (continues processing even when emails fail)
- ✅ Critical error detection (aborts on catastrophic failures)
- ✅ View all errors in admin dashboard

📖 **See**:
[EMAIL_BACKFILL_ERROR_HANDLING.md](./EMAIL_BACKFILL_ERROR_HANDLING.md)
for complete error handling documentation

---

## Prerequisites

### 1. Database Migration Applied

```bash
cd apps/backend
alembic upgrade head
# Should show: 20251124_email_storage (head)
```

### 2. Backend Server Stopped

Stop the backend server during backfill to avoid conflicts with IMAP
IDLE monitors:

```bash
# If running via pm2
pm2 stop myhibachi-backend

# If running via systemctl
systemctl stop myhibachi-backend

# If running manually
# Press Ctrl+C to stop
```

### 3. Environment Variables Configured

Ensure `.env` has IMAP credentials:

```bash
# Customer Support (IONOS)
SMTP_PASSWORD=your_ionos_password

# Payments (Gmail)
PAYMENT_EMAIL_ADDRESS=myhibachichef@gmail.com
PAYMENT_EMAIL_PASSWORD=your_gmail_app_password
```

---

## Usage

### Basic Syntax

```bash
cd apps/backend
python -m src.scripts.backfill_emails --inbox <INBOX> [OPTIONS]
```

### Arguments

**Required:**

- `--inbox` - Which inbox to backfill
  - `customer_support` - cs@myhibachichef.com (IONOS)
  - `payments` - myhibachichef@gmail.com (Gmail)

**Optional:**

- `--limit N` - Sync only N most recent emails (default: all)
- `--batch-size N` - Process N emails per batch (default: 100)
- `--dry-run` - Preview without syncing to database

---

## Examples

### 1. Dry Run (Preview Only)

Test connection and see how many emails would be synced:

```bash
python -m src.scripts.backfill_emails \
  --inbox customer_support \
  --dry-run
```

**Output:**

```
🚀 Starting email backfill for inbox: customer_support
📡 Connecting to IMAP server...
📬 Found 1234 total emails in IMAP
🔍 DRY RUN MODE - No emails will be synced
   Would process: 1234 emails
```

### 2. Sync Customer Support Inbox (All Emails)

```bash
python -m src.scripts.backfill_emails \
  --inbox customer_support
```

**Progress:**

```
🚀 Starting email backfill for inbox: customer_support
📡 Connecting to IMAP server...
📬 Found 1234 total emails in IMAP

📦 Processing batch 1/13 (100 emails)
   ✅ [1/100] Synced (created): Payment question from customer
   ⏭️  [2/100] Skipped (already exists): Re: Booking confirmation
   ✅ [3/100] Synced (created): Catering inquiry for wedding
   ...

📊 BACKFILL COMPLETE
   Total fetched: 1234
   Total synced:  1150 ✅
   Total skipped: 84 ⏭️
   Total errors:  0 ❌
   Elapsed time:  245.3s
   Success rate:  93.2%
```

### 3. Sync Payments Inbox (Limited to 500)

```bash
python -m src.scripts.backfill_emails \
  --inbox payments \
  --limit 500
```

### 4. Sync with Custom Batch Size

```bash
python -m src.scripts.backfill_emails \
  --inbox customer_support \
  --batch-size 50
```

**Use case:** Smaller batches for slower connections or debugging.

---

## What Gets Synced

### Email Data

- ✅ Message-ID (unique identifier)
- ✅ From address and name
- ✅ To/Cc addresses
- ✅ Subject
- ✅ Text body and HTML body
- ✅ Received date/time
- ✅ Attachments metadata (filename, size, content type)
- ✅ Thread grouping (based on subject)

### Flags/Labels

- ⚠️ Read/unread status NOT synced (defaults to unread)
- ⚠️ Stars NOT synced (defaults to unstarred)
- ⚠️ Labels NOT synced (empty)

**Why?** IMAP doesn't reliably store these flags across all providers.

---

## Deduplication

The script automatically skips emails that already exist in the
database:

**Check:** Compares `message_id` field (Email Message-ID header)
**Action if exists:** Logs "Skipped (already exists)" and continues
**Action if new:** Syncs to database

**Safe to re-run:** Yes! The script won't create duplicates.

---

## Thread Grouping

Emails are automatically grouped into threads:

**Thread ID Generation:**

1. Normalize subject (remove "Re:", "Fwd:", "RE:", "FW:")
2. Sort participants (from + to addresses)
3. Generate MD5 hash: `hash(normalized_subject + sorted_participants)`
4. Thread ID: `thread_abc123def456`

**Example:**

```
Email 1: "Payment Question"
Email 2: "Re: Payment Question"
Email 3: "RE: PAYMENT QUESTION"
→ All grouped into same thread (same thread_id)
```

---

## Performance

### Expected Times

| Emails | Batch Size | Estimated Time |
| ------ | ---------- | -------------- |
| 100    | 100        | ~20 seconds    |
| 500    | 100        | ~1.5 minutes   |
| 1000   | 100        | ~3 minutes     |
| 5000   | 100        | ~15 minutes    |

**Factors:**

- IMAP server speed
- Network latency
- Database write speed
- Email size (attachments slow down parsing)

### Optimization Tips

1. **Use smaller batch size for debugging:**

   ```bash
   --batch-size 10
   ```

2. **Limit sync during testing:**

   ```bash
   --limit 50
   ```

3. **Use dry-run first:**
   ```bash
   --dry-run
   ```

---

## Troubleshooting

### Error: "Failed to connect to IMAP server"

**Cause:** IMAP credentials incorrect or network issue **Fix:**

1. Check `.env` file: `SMTP_PASSWORD` for customer_support,
   `PAYMENT_EMAIL_PASSWORD` for payments
2. Test IMAP connection manually:
   ```bash
   python apps/backend/test_ionos_imap.py
   ```
3. Check firewall/network (port 993 must be open)

### Error: "AsyncEngine' object has no attribute 'connect'"

**Cause:** Using synchronous database methods with async engine
**Fix:** Script already uses async session, ensure you're using latest
version

### Error: "No module named 'src.scripts'"

**Cause:** Running from wrong directory **Fix:** Must run from
`apps/backend/` directory:

```bash
cd apps/backend
python -m src.scripts.backfill_emails --inbox customer_support
```

### Error: "Table 'email_messages' does not exist"

**Cause:** Migration not applied **Fix:**

```bash
cd apps/backend
alembic upgrade head
```

### Warning: "Skipped (already exists)" for all emails

**Cause:** Emails already synced (not an error!) **Action:** None
needed, script is working correctly

### Many errors: "Failed to parse email"

**Cause:** Corrupted emails in IMAP or encoding issues **Action:**

1. Check error logs for specific email IDs
2. Continue backfill (errors are logged but don't stop process)
3. Manually inspect problematic emails in IMAP client

---

## Post-Backfill Verification

### 1. Check Database Records

```sql
-- Count emails per inbox
SELECT inbox, COUNT(*)
FROM email_messages
GROUP BY inbox;

-- Count threads per inbox
SELECT inbox, COUNT(*)
FROM email_threads
GROUP BY inbox;

-- View recent synced emails
SELECT message_id, subject, from_address, received_at
FROM email_messages
ORDER BY received_at DESC
LIMIT 10;
```

### 2. Test API Endpoints

```bash
# Get customer support emails
curl http://localhost:8000/api/v1/admin/emails/customer-support?limit=10

# Get email stats
curl http://localhost:8000/api/v1/admin/emails/stats
```

### 3. Check Sync Status

```sql
SELECT * FROM email_sync_status;
```

**Expected output:**

```
inbox             | last_sync_at | total_synced | sync_errors
customer_support  | 2025-11-24   | 1150         | []
payments          | 2025-11-24   | 450          | []
```

---

## Restart Backend After Backfill

Once backfill is complete, restart the backend server:

```bash
# If using pm2
pm2 start myhibachi-backend

# If using systemctl
systemctl start myhibachi-backend

# If running manually
cd apps/backend
uvicorn src.main:app --reload
```

**Important:** IMAP IDLE monitors will continue syncing new emails
automatically.

---

## Advanced Usage

### Backfill Both Inboxes Sequentially

```bash
# Customer support
python -m src.scripts.backfill_emails --inbox customer_support

# Payments
python -m src.scripts.backfill_emails --inbox payments
```

### Re-run for New Emails

```bash
# Safe to re-run anytime
# Only syncs emails not already in database
python -m src.scripts.backfill_emails --inbox customer_support
```

### Debug Single Email

```bash
# Limit to 1 email with verbose logging
python -m src.scripts.backfill_emails \
  --inbox customer_support \
  --limit 1 \
  --batch-size 1
```

---

## Exit Codes

- `0` - Success (all emails synced without errors)
- `1` - Partial success (some errors occurred) or fatal error

**Example:**

```bash
python -m src.scripts.backfill_emails --inbox customer_support
echo $?  # Check exit code
# 0 = success
# 1 = errors occurred
```

---

## Logging

### Log Levels

**INFO:** Progress updates, sync results **WARNING:** Skipped emails,
non-fatal errors **ERROR:** Failed to sync email, IMAP errors
**DEBUG:** Detailed email parsing (enable with `--verbose` flag if
added)

### Log Output

**Console:** Real-time progress **File:**
`apps/backend/logs/backfill_emails.log` (if configured)

**Example log:**

```
2025-11-24 10:30:15 - backfill_emails - INFO - 🚀 Starting email backfill
2025-11-24 10:30:16 - backfill_emails - INFO - 📬 Found 1234 total emails
2025-11-24 10:30:17 - backfill_emails - INFO - 📦 Processing batch 1/13
2025-11-24 10:30:18 - backfill_emails - INFO -    ✅ [1/100] Synced (created)
```

---

## Frequently Asked Questions

### Q: How long does backfill take?

**A:** ~3-5 minutes per 1000 emails. Depends on IMAP server speed and
email size.

### Q: Can I run backfill while backend is running?

**A:** Not recommended. IMAP IDLE monitors may conflict. Stop backend
first.

### Q: What happens if backfill crashes mid-way?

**A:** Safe to re-run! Deduplication ensures no duplicates. Already
synced emails are skipped. All errors are logged to the `error_logs`
table - check admin dashboard to see what went wrong.

### Q: How do I troubleshoot errors during backfill?

**A:** Check the **Error Summary** at the end of backfill output. Note
the **Operation ID** and view detailed errors in admin dashboard under
**Error Logs**. See
[EMAIL_BACKFILL_ERROR_HANDLING.md](./EMAIL_BACKFILL_ERROR_HANDLING.md)
for troubleshooting guide.

### Q: Can I backfill only recent emails?

**A:** Yes! Use `--limit` flag:

```bash
python -m src.scripts.backfill_emails --inbox customer_support --limit 100
```

### Q: How do I know if backfill is working?

**A:** Check console output for "✅ Synced (created)" messages. Query
database to verify records.

### Q: Should I backfill both inboxes?

**A:** Yes, run backfill for both `customer_support` and `payments`
inboxes.

### Q: Can I automate backfill on deployment?

**A:** Yes, add to deployment script:

```bash
# After migration
alembic upgrade head

# Backfill emails
python -m src.scripts.backfill_emails --inbox customer_support
python -m src.scripts.backfill_emails --inbox payments

# Start backend
pm2 start myhibachi-backend
```

---

## Summary Checklist

- [ ] Stop backend server
- [ ] Apply database migration (`alembic upgrade head`)
- [ ] Run dry-run to preview (`--dry-run`)
- [ ] Run backfill for customer_support inbox
- [ ] Run backfill for payments inbox
- [ ] Verify database records (SQL queries)
- [ ] Test API endpoints
- [ ] Restart backend server
- [ ] Monitor IMAP IDLE auto-sync logs

---

**Created:** November 24, 2025 **Script:**
`apps/backend/src/scripts/backfill_emails.py` **Status:** ✅ Ready for
Use
