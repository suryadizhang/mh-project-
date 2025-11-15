# Admin Dashboard Training Guide

Complete guide for using the MyHibachi Admin Dashboard with new SMS
tracking and compliance features.

## 📋 Table of Contents

1. [Dashboard Overview](#dashboard-overview)
2. [Newsletter Analytics](#newsletter-analytics)
3. [Campaign Management](#campaign-management)
4. [SMS Tracking & Delivery](#sms-tracking--delivery)
5. [Compliance Monitoring](#compliance-monitoring)
6. [Subscriber Management](#subscriber-management)
7. [Real-Time Updates](#real-time-updates)
8. [Cost Tracking](#cost-tracking)
9. [Troubleshooting](#troubleshooting)

---

## Dashboard Overview

### Main Navigation

```
Admin Dashboard
├── 📊 Overview (KPIs)
├── 📧 Newsletter
│   ├── Analytics
│   ├── Campaigns
│   ├── Subscribers
│   └── Compliance
├── 📱 SMS Tracking
├── 💰 Cost Analysis
└── ⚙️ Settings
```

### Key Features

- **Real-time metrics** - Live updates via WebSocket
- **SMS delivery tracking** - Per-message status tracking
- **TCPA compliance** - Automated consent management
- **Cost analytics** - Track SMS spending per campaign
- **Campaign scheduling** - Send now or schedule for later

---

## Newsletter Analytics

### Accessing Analytics

1. Navigate to **Newsletter** → **Analytics**
2. Select time range (7d, 30d, 90d, All Time)
3. View metrics across all campaigns

### Key Metrics

#### Overview Stats

```
┌─────────────────────────────────────────────────┐
│  📊 Campaign Performance                         │
├─────────────────────────────────────────────────┤
│  Total Subscribers: 1,250                       │
│  Active Subscribers: 1,180                      │
│  SMS Consented: 945                             │
│  Total Campaigns: 15                            │
│  Campaigns Sent: 12                             │
│  Total SMS Sent: 11,340                         │
│  Total Delivered: 11,150 (98.3%)                │
│  Total Failed: 190 (1.7%)                       │
│  Total Cost: $85.05                             │
│  Avg Cost/Campaign: $7.09                       │
│  TCPA Compliance Rate: 100%                     │
└─────────────────────────────────────────────────┘
```

#### Subscriber Growth

View trends over time:

- Total subscribers (line chart)
- New signups per day
- Unsubscribe rate
- SMS consent percentage

#### Campaign Performance Table

| Campaign       | Sent Date | Recipients | Delivery Rate | Failed | Cost  |
| -------------- | --------- | ---------- | ------------- | ------ | ----- |
| Holiday Promo  | Dec 10    | 945        | 98.5%         | 14     | $7.09 |
| Weekly Special | Dec 3     | 920        | 99.1%         | 8      | $6.90 |

### Reading the Analytics

**High Delivery Rate (>98%)** ✅ Good - Your campaigns are reaching
customers successfully

**Low Delivery Rate (<95%)** ⚠️ Warning - Check for:

- Invalid phone numbers in subscriber list
- RingCentral account issues
- Network connectivity problems

**High Cost Per Campaign (>$10)** 💡 Consider segmenting subscribers
to send targeted campaigns to smaller groups

---

## Campaign Management

### Creating a New Campaign

1. Go to **Newsletter** → **Campaigns** → **Create Campaign**
2. Fill in campaign details:

```
Campaign Name: Holiday Special 2025
Subject: Save 20% on Your Next Booking

Message Body:
🎉 Holiday Special! Book your hibachi experience now and save 20%
Use code: HOLIDAY2025
Book: https://myhibachi.com/book
Reply STOP to unsubscribe

Channel: SMS ✓  Email ☐
Schedule: Send Now ✓  Schedule for Later ☐
```

3. **Preview** - Review before sending
4. **Select Recipients**:
   - All active subscribers
   - SMS consented only ✓ (TCPA required)
   - Segment by location
   - Segment by engagement score

5. **Cost Estimate**:

   ```
   Recipients: 945
   Message Segments: 1
   Estimated Cost: $7.09
   Cost per recipient: $0.0075
   ```

6. Click **Send Campaign** or **Schedule**

### Campaign Status

After sending, track status:

```
Campaign: Holiday Special 2025
Status: ⏳ Sending... (423/945 sent)

Progress: ████████░░░░░░░░ 45%

Delivered: 415 (98.1%)
Failed: 8 (1.9%)
Pending: 522

Refresh automatically via WebSocket ⚡
```

---

## SMS Tracking & Delivery

### Real-Time Tracking

Each SMS is tracked individually:

```
┌─────────────────────────────────────────────────┐
│  SMS Delivery Details                            │
├─────────────────────────────────────────────────┤
│  Phone: +1 (555) 123-4567                       │
│  Status: ✅ Delivered                            │
│  Sent: Dec 10, 2025 10:15 AM                    │
│  Delivered: Dec 10, 2025 10:15 AM (0.3s)       │
│  Segments: 1                                    │
│  Cost: $0.0075                                  │
│  Message ID: RC-msg-123abc                      │
│  Carrier: Verizon                               │
└─────────────────────────────────────────────────┘
```

### Delivery Statuses

| Status    | Icon | Meaning                | Action                             |
| --------- | ---- | ---------------------- | ---------------------------------- |
| Queued    | ⏳   | Waiting to send        | Wait (processes in order)          |
| Sent      | 📤   | Sent to carrier        | Wait for delivery confirmation     |
| Delivered | ✅   | Successfully delivered | None needed                        |
| Failed    | ❌   | Delivery failed        | Check error, may need manual retry |
| Bounced   | ⚠️   | Invalid number         | Remove from list                   |

### Handling Failed Deliveries

When SMS fails:

1. Click on failed message
2. View error details:

   ```
   Error Code: INVALID_PHONE_NUMBER
   Error Message: The destination number is not valid
   Retry Attempts: 3
   ```

3. Common errors:
   - **INVALID_PHONE_NUMBER**: Remove or update subscriber
   - **CARRIER_VIOLATION**: Message blocked by carrier spam filter
   - **LANDLINE**: Cannot send SMS to landline numbers
   - **OPTED_OUT**: User previously opted out (TCPA)

4. Take action:
   - Update phone number
   - Mark subscriber inactive
   - Add to suppression list

---

## Compliance Monitoring

### TCPA Compliance Dashboard

Access: **Newsletter** → **Compliance**

```
┌─────────────────────────────────────────────────┐
│  📋 TCPA Compliance Status                       │
├─────────────────────────────────────────────────┤
│  Compliant: ✅ 100%                             │
│  Total Consents: 945                            │
│  Active Opt-Outs: 32                            │
│  Pending Verifications: 0                       │
│                                                  │
│  Last 30 Days:                                  │
│  - New Consents: 87                             │
│  - Opt-Outs: 12                                 │
│  - STOP Keywords: 12                            │
│  - Compliance Violations: 0 ✅                   │
└─────────────────────────────────────────────────┘
```

### Consent Verification

Each subscriber must have documented consent:

```
Subscriber: John Smith
Phone: +1 (555) 123-4567
SMS Consent: ✅ Yes
Consent Date: Nov 15, 2025 2:30 PM
Consent Source: Website Signup Form
IP Address: 192.168.1.1
User Agent: Mozilla/5.0...

Audit Trail:
├─ Nov 15, 2025 2:30 PM - Consent granted (Website)
├─ Nov 18, 2025 - First SMS sent (Welcome message)
├─ Dec 1, 2025 - Campaign SMS sent (Holiday Promo)
└─ Dec 10, 2025 - Campaign SMS sent (Weekly Special)
```

### Opt-Out Processing

When subscriber texts "STOP":

1. **Automatic Processing**:

   ```
   Incoming SMS: "STOP"
   From: +1 (555) 123-4567
   Timestamp: Dec 10, 2025 3:45 PM

   ✅ Auto-processed:
   - Subscriber marked inactive
   - SMS consent revoked
   - Added to suppression list
   - Confirmation sent: "You've been unsubscribed. Reply START to resubscribe."
   ```

2. **Dashboard Alert**:

   ```
   🔔 New Opt-Out
   Subscriber: John Smith
   Reason: User requested (STOP keyword)
   Status: Processed ✅
   Future messages: Blocked
   ```

3. **Verification**:
   - Check **Compliance** → **Recent Opt-Outs**
   - Verify subscriber is inactive
   - Confirm not in future campaigns

### Compliance Alerts

Real-time alerts for compliance issues:

```
⚠️ COMPLIANCE ALERT

Type: Attempted send without consent
Subscriber: Jane Doe (+1-555-999-8888)
Campaign: Holiday Special 2025
Status: ❌ Blocked
Reason: No SMS consent on record

Action Required: None (automatically prevented)
```

---

## Subscriber Management

### Subscriber List

View all subscribers: **Newsletter** → **Subscribers**

```
┌────────────────────────────────────────────────────────────────┐
│  Search: [________________] 🔍  Filter: [All ▼] Export: [CSV]  │
├────────────────────────────────────────────────────────────────┤
│  Name         │ Email            │ Phone         │ SMS  │ Score │
├───────────────┼──────────────────┼───────────────┼──────┼───────┤
│  John Smith   │ john@email.com   │ +1-555-1234   │ ✅   │ 85    │
│  Jane Doe     │ jane@email.com   │ +1-555-5678   │ ✅   │ 72    │
│  Bob Johnson  │ bob@email.com    │ +1-555-9012   │ ❌   │ 45    │
└────────────────────────────────────────────────────────────────┘

Legend:
✅ SMS Consent Active
❌ No SMS Consent
Score: Engagement score (0-100)
```

### Engagement Scores

Subscribers are scored 0-100 based on:

- **Delivery success** (40 points): High delivery rate = high score
- **Click-through** (30 points): Clicks links in messages
- **Recency** (20 points): Recent activity boosts score
- **Failure rate** (10 points deducted): Failed deliveries reduce
  score

**Score Interpretation**:

- 80-100: 🟢 Highly engaged - Priority recipients
- 50-79: 🟡 Moderately engaged - Continue sending
- 0-49: 🔴 Low engagement - Consider removing or re-engagement
  campaign

### Bulk Actions

Select multiple subscribers:

1. ☑️ Check boxes for subscribers
2. Choose action:
   - **Export** - Download CSV
   - **Add to Segment** - Create targeted group
   - **Remove from List** - Mark inactive
   - **Update Consent** - Bulk consent update

---

## Real-Time Updates

### WebSocket Connection

Dashboard connects via WebSocket for real-time updates:

```
🟢 Connected to real-time updates

Receiving:
- Campaign sending progress
- SMS delivery statuses
- Compliance events
- Opt-out requests
- System alerts
```

### Connection Status

Bottom right of dashboard:

```
🟢 Live Updates Active
Last update: 2 seconds ago
Next sync: Now
```

If disconnected:

```
🔴 Connection Lost
Reconnecting... (attempt 1/5)
```

### Manual Refresh

If updates seem stuck:

1. Check connection status (bottom right)
2. Click **Refresh** button
3. If still stuck, reload page (Ctrl+R)

---

## Cost Tracking

### Cost Dashboard

Access: **Newsletter** → **Cost Analysis**

```
┌─────────────────────────────────────────────────┐
│  💰 SMS Cost Analysis                            │
├─────────────────────────────────────────────────┤
│  Current Month: $142.50                         │
│  Previous Month: $128.25 (+11.1%)               │
│  Average/Day: $4.75                             │
│  Projected Month: $150.00                       │
│                                                  │
│  Cost Breakdown:                                │
│  - SMS Segments: $142.50 (100%)                 │
│  - API Calls: Included                          │
│  - Webhooks: Included                           │
│                                                  │
│  Top Campaigns by Cost:                         │
│  1. Holiday Special: $28.50 (1,140 SMS)         │
│  2. Weekly Digest: $22.75 (910 SMS)             │
│  3. Flash Sale: $19.00 (760 SMS)                │
└─────────────────────────────────────────────────┘
```

### Cost Optimization Tips

**🎯 Target Active Subscribers Only**

- Use engagement scores to filter low-performing subscribers
- Segment by location to send geo-targeted campaigns
- Remove invalid phone numbers

**📅 Schedule Strategically**

- Send at optimal times (10 AM - 2 PM, Tuesday-Thursday)
- Avoid weekends and holidays
- Batch campaigns to reduce duplicate sends

**📝 Optimize Message Length**

- Keep under 160 characters (1 segment = $0.0075)
- 161-320 characters = 2 segments ($0.015)
- Each segment adds $0.0075

**Example**:

```
❌ Long message (2 segments):
"🎉 Special holiday offer! Book your hibachi experience now and save 20% with code HOLIDAY2025. Valid through Dec 31. Visit https://myhibachi.com/book or call 555-1234. Reply STOP to unsubscribe."
Cost: $0.015 per recipient

✅ Optimized (1 segment):
"🎉 20% OFF hibachi! Use HOLIDAY2025
Book: myhibachi.com/book
Reply STOP to opt-out"
Cost: $0.0075 per recipient
```

### Budget Alerts

Set spending limits:

```
⚙️ Settings → Budget Alerts

Monthly Limit: $200.00
Current: $142.50 (71%)

Alerts:
☑️ Email at 75% ($150)
☑️ Email at 90% ($180)
☑️ Email at 100% ($200)
☑️ Block sends at 110% ($220)
```

---

## Troubleshooting

### Common Issues

#### Campaign Not Sending

**Symptoms**: Campaign stuck at 0% sent

**Causes & Solutions**:

1. **Celery worker not running**
   - Check: `Services` tab → Celery status
   - Fix: Restart Celery workers

2. **No consented subscribers**
   - Check: Campaign recipients filter
   - Fix: Ensure "SMS Consented" is selected

3. **RingCentral API error**
   - Check: Logs → RingCentral errors
   - Fix: Verify API credentials in Settings

#### Low Delivery Rate

**Symptoms**: <95% delivery rate

**Causes & Solutions**:

1. **Invalid phone numbers**
   - Check: Failed deliveries error codes
   - Fix: Clean subscriber list, remove invalid numbers

2. **Carrier blocking**
   - Check: Error messages for "SPAM" or "BLOCKED"
   - Fix: Adjust message content, add opt-out instructions

3. **Rate limiting**
   - Check: RingCentral API quota
   - Fix: Reduce sending rate or upgrade plan

#### Compliance Warnings

**Symptoms**: Compliance violations flagged

**Causes & Solutions**:

1. **Missing consent**
   - Check: Subscriber consent status
   - Fix: Re-request consent or remove subscriber

2. **Opt-out not processed**
   - Check: Opt-out keyword processing logs
   - Fix: Verify webhook configuration

3. **Audit trail gaps**
   - Check: System events log
   - Fix: Contact support if events missing

### Support Escalation

If issue persists:

1. **Collect Info**:
   - Screenshot of error
   - Campaign ID
   - Time of occurrence
   - Steps to reproduce

2. **Check Logs**:
   - Dashboard → Logs
   - Filter by error level
   - Export relevant entries

3. **Contact Support**:
   - Email: support@myhibachi.com
   - Include: Campaign ID, error screenshot, logs
   - Priority: Critical (< 1 hour), High (< 4 hours), Normal (< 24
     hours)

---

## Quick Reference Card

### Keyboard Shortcuts

| Shortcut | Action             |
| -------- | ------------------ |
| `Ctrl+/` | Search subscribers |
| `Ctrl+N` | New campaign       |
| `Ctrl+R` | Refresh dashboard  |
| `Ctrl+E` | Export data        |
| `Esc`    | Close modal        |

### Status Indicators

| Indicator | Meaning           |
| --------- | ----------------- |
| 🟢        | Online/Active     |
| 🟡        | Warning/Pending   |
| 🔴        | Error/Offline     |
| ✅        | Success/Delivered |
| ❌        | Failed/Blocked    |
| ⏳        | In Progress       |

### Best Practices

✅ **DO**:

- Verify consent before sending
- Monitor delivery rates
- Keep messages under 160 characters
- Use clear opt-out instructions
- Segment subscribers for targeted campaigns

❌ **DON'T**:

- Send to non-consented subscribers
- Ignore failed deliveries
- Exceed budget limits without approval
- Use unclear or misleading content
- Send during off-hours (before 9 AM or after 9 PM)

---

## Training Resources

### Video Tutorials

1. **Getting Started** (10 min)
   - Dashboard overview
   - Creating first campaign
   - Reading analytics

2. **Advanced Features** (15 min)
   - Subscriber segmentation
   - Compliance monitoring
   - Cost optimization

3. **Troubleshooting** (12 min)
   - Common issues
   - Error codes
   - Support escalation

### Documentation Links

- [Full API Documentation](./API_ENDPOINTS_COMPLETE.md)
- [Environment Setup](./ENVIRONMENT_CONFIGURATION.md)
- [Compliance Guide](./CAN_SPAM_TCPA_IMPLEMENTATION_COMPLETE.md)
- [Database Architecture](./DATABASE_ARCHITECTURE_ANALYSIS.md)

### Training Exercises

**Exercise 1**: Create Your First Campaign

1. Navigate to Campaigns → Create
2. Write message under 160 characters
3. Select 10 test subscribers
4. Schedule for tomorrow 10 AM
5. Monitor delivery status

**Exercise 2**: Analyze Campaign Performance

1. Go to Analytics
2. Select last 30 days
3. Identify campaign with lowest delivery rate
4. Review error codes
5. Propose improvement plan

**Exercise 3**: Handle Compliance Issue

1. Find subscriber without consent
2. Update consent status
3. Verify in compliance dashboard
4. Document in audit trail
5. Send test SMS

---

**Training Complete! 🎉**

For additional support:

- Email: admin-support@myhibachi.com
- Slack: #admin-dashboard-help
- Internal Wiki: wiki.myhibachi.com/admin

---

**Last Updated**: November 2025 **Version**: 1.0.0 **Trainer**: DevOps
Team
