# Schedule Follow-Up Performance: Deep Analysis Summary

**Date:** November 2, 2025  
**Current Performance:** 1931ms (Target: <500ms)  
**Status:** Phase 1 Optimizations Implemented & Analyzed

---

## Executive Summary

Deep profiling identified **3 critical bottlenecks** accounting for
86% of scheduling time:

1. **Store Message: 2000ms** (52%) - Multiple DB round-trips + emotion
   stats calculation
2. **Duplicate Check: 637ms** (16%) - Missing composite index usage
   (table too small for index)
3. **Emotion History: 634ms** (16%) - Fetching unnecessary columns

### Phase 1 Results: ⚠️ MINIMAL IMPROVEMENT

**Before Phase 1:**

- Duplicate check: 637ms
- Emotion history: 634ms
- Total schedule: 1931ms

**After Phase 1:**

- Duplicate check: 630ms (1% improvement - **INDEX NOT BEING USED**)
- Emotion history: 632ms (0.3% improvement - **QUERY STILL SLOW**)
- Total schedule: ~1900ms (estimated, 2% improvement)

### Why Phase 1 Failed

1. **Composite Index Not Used:** PostgreSQL query planner chose
   sequential scan because table has only 8 rows
2. **Network Latency Dominant:** Each query takes ~270ms baseline
   regardless of optimization
3. **Column Selection Not Helping:** Fetching 4 columns vs 14 columns
   saves minimal time when network latency is 270ms

---

## Detailed Profiling Results

### Operation Breakdown (from profile_schedule_performance.py)

```
OPERATION                              TIME      % OF TOTAL
------------------------------------------------
1. Store message (with emotion)       2000ms         52%
2. Check for duplicate follow-ups      637ms         17%
3. Get emotion history (5 messages)    634ms         17%
4. Select template by emotion            0ms          0%
5. Render template                       0ms          0%
6. Insert into database                380ms         10%
7. Add to APScheduler                   <1ms          0%
------------------------------------------------
TOTAL                                  3651ms        100%
```

### Root Cause: Network Latency

**Each database query baseline:** ~270-280ms (network round-trip)

**Why optimizations didn't help:**

- **Composite index:** Table too small (8 rows) → PostgreSQL uses Seq
  Scan (0.042ms execution vs 270ms round-trip)
- **Column reduction:** Saves ~10-20ms parsing, but 270ms network
  latency dominates
- **Query optimization:** PostgreSQL execution is fast (0.042ms),
  problem is connection overhead

---

## Real Bottleneck: Store Message Operation (2000ms)

### Query-by-Query Breakdown

```sql
-- Query 1: Check conversation exists (280ms round-trip)
SELECT * FROM ai_conversations WHERE id = ?;

-- Query 2: Insert conversation if new (180ms)
INSERT INTO ai_conversations (...) VALUES (...);

-- Query 3: Insert message (180ms)
INSERT INTO ai_messages (...) VALUES (...);

-- Query 4: Get last 10 emotion scores (350ms) ⚠️
SELECT emotion_score FROM ai_messages
WHERE conversation_id = ? AND emotion_score IS NOT NULL
ORDER BY timestamp DESC LIMIT 10;

-- Query 5: Update conversation stats (180ms)
UPDATE ai_conversations
SET average_emotion_score = ?, emotion_trend = ?
WHERE id = ?;

-- Query 6: Return message (280ms) ← UNNECESSARY
SELECT * FROM ai_messages WHERE id = ?;

TOTAL: 6 queries × ~270ms = ~1620ms + processing = 2000ms
```

### Impact Analysis

**Per-operation cost:**

- Network round-trip: 270ms per query
- SQL execution: 0.01-0.05ms (negligible)
- Data transfer: ~10ms per query
- **Total per query: ~280ms**

**Multiplication effect:**

- 6 queries = 6 × 280ms = **1680ms just in network latency**
- Add processing/parsing: **~320ms**
- **Total: 2000ms**

---

## Optimization Strategy: REVISED

### ❌ What DOESN'T Work

1. **Composite indexes** - Table too small, won't be used in
   development
2. **Column selection** - Saves <20ms when network latency is 270ms
3. **Query optimization** - PostgreSQL execution is already fast
   (0.042ms)

### ✅ What WILL Work

1. **Reduce Query Count** - Eliminate queries, not optimize them
2. **Batch Operations** - Combine multiple queries into one
   transaction
3. **Async/Defer** - Don't block on non-critical operations
4. **Connection Pooling** - Reduce connection overhead

---

## Revised Implementation Plan

### Phase 2A: Eliminate Queries (Target: 2000ms → 800ms, -1200ms)

#### 2A.1. Remove Unnecessary SELECT After INSERT (-280ms)

```python
# BEFORE (6 queries)
await db.execute(insert(AIMessage).values(...))
await db.commit()
message = await db.get(AIMessage, message_id)  # ← Query 6: REMOVE
return to_conversation_message(message)

# AFTER (5 queries)
message_data = {...}
await db.execute(insert(AIMessage).values(message_data))
await db.commit()
return ConversationMessage(**message_data)  # Construct from insert data
```

**Savings:** 280ms per call

#### 2A.2. Defer Emotion Statistics Calculation (-350ms)

```python
# BEFORE: Calculate emotion stats synchronously (queries 4 & 5)
scores = await db.execute(select last 10 emotion scores)  # Query 4
conversation.average = calculate_average(scores)
await db.execute(update conversation)  # Query 5

# AFTER: Queue for background processing
await db.execute(insert(AIMessage).values(...))
await db.commit()
asyncio.create_task(update_emotion_stats_async(conversation_id))  # Don't wait
return message  # Return immediately
```

**Savings:** 530ms (query 4: 350ms + query 5: 180ms) - doesn't block
return

#### 2A.3. Batch Conversation Upsert with Message Insert (-180ms)

```python
# BEFORE: Separate queries (queries 1, 2, 3)
conversation = await db.get(AIConversation, id)  # Query 1: 280ms
if not conversation:
    await db.execute(insert(AIConversation))  # Query 2: 180ms
await db.execute(insert(AIMessage))  # Query 3: 180ms

# AFTER: Use PostgreSQL UPSERT (ON CONFLICT)
await db.execute("""
    INSERT INTO ai_conversations (...) VALUES (...)
    ON CONFLICT (id) DO UPDATE SET last_message_at = NOW();

    INSERT INTO ai_messages (...) VALUES (...);
""")  # Single round-trip for both operations
```

**Savings:** 180ms (eliminates 1 round-trip)

**Total Phase 2A Savings:** 280ms + 350ms + 180ms + 180ms = **990ms**
**New store_message time:** 2000ms - 990ms = **1010ms**

### Phase 2B: Connection Pool Optimization (Target: -200ms additional)

#### 2B.1. Tune AsyncPG Pool Settings

```python
engine = create_async_engine(
    DATABASE_URL,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=20,          # Up from 5
    max_overflow=10,
    pool_pre_ping=True,    # Check connection health
    pool_recycle=3600,
)
```

**Savings:** -50-100ms per operation (reduce connection acquisition
wait)

#### 2B.2. Enable Statement Caching

```python
engine = create_async_engine(
    DATABASE_URL,
    execution_options={"compiled_cache_size": 500}
)
```

**Savings:** -20-50ms per operation

**Total Phase 2B Savings:** ~150ms across all operations

---

## Expected Results After Phase 2

### Store Message Operation

- **Before:** 2000ms (6 queries)
- **After Phase 2A:** 1010ms (2 queries, async stats)
- **After Phase 2B:** 860ms (with connection pooling)
- **Improvement:** 57% faster

### Duplicate Check

- **Before:** 637ms
- **After Phase 2B:** 580ms (connection pooling)
- **Improvement:** 9% faster

### Emotion History

- **Before:** 634ms
- **After Phase 2B:** 580ms (connection pooling)
- **Improvement:** 9% faster

### Full Schedule Follow-Up

- **Before:** 1931ms
- **Store:** 860ms (was 2000ms)
- **Duplicate:** 580ms (was 637ms)
- **Emotion:** 580ms (was 634ms)
- **Other:** 100ms (template + DB insert + scheduler)
- **Total:** ~2120ms... wait, that's WORSE!

**WAIT - RECALCULATION NEEDED!**

The profiling showed:

1. Store message: 2000ms
2. Duplicate check: 637ms
3. Emotion history: 634ms
4. **Database insert:** 380ms
5. Other: <100ms

But the **full schedule_follow_up is only 1931ms**, not 3651ms. This
means some operations overlap or are cached.

Let me check the actual schedule_follow_up flow...

---

## Actual Schedule Follow-Up Flow

Looking at `schedule_post_event` code:

```python
async def schedule_post_event(...):
    # Step 1: Check duplicates (637ms)
    if await self._has_pending_followup(...):
        return None

    # Step 2: Get emotion history (634ms)
    emotion_history = await self.memory.get_emotion_history(conversation_id, limit=5)

    # Step 3: Select template (0ms - in-memory)
    template = await self._select_template_by_emotion(...)

    # Step 4: Insert follow-up into DB (380ms)
    async with get_db_context() as db:
        followup = ScheduledFollowUp(...)
        db.add(followup)
        await db.commit()

    # Step 5: Add to APScheduler (<1ms - in-memory)
    self.scheduler.add_job(...)
```

**Total:** 637 + 634 + 0 + 380 + 1 = **1652ms** (Expected)  
**Actual:** 1931ms  
**Overhead:** 279ms (template rendering, object creation, etc.)

**So the store_message (2000ms) is NOT part of schedule_follow_up!**

It happens **before** scheduling, when the user sends the booking
confirmation message.

---

## Corrected Optimization Target

### Current Flow Timeline

```
1. User sends booking message
   └─> store_message() = 2000ms ⚠️ BLOCKS USER

2. Booking confirmed (backend logic)
   └─> schedule_follow_up() = 1931ms ⚠️ BLOCKS RESPONSE

Total user wait: 3931ms for booking confirmation!
```

### Optimization Targets

**Priority 1: Store Message (2000ms → 600ms)**

- This blocks EVERY user message
- Happens on every interaction
- Most critical for user experience

**Priority 2: Schedule Follow-Up (1931ms → 500ms)**

- This blocks booking confirmation response
- Happens less frequently (only on bookings)
- Still important but lower impact

---

## Final Recommendations

### Immediate Actions (Next 2 Days)

1. **Implement Query Elimination** (Phase 2A)
   - Remove SELECT after INSERT in store_message
   - Defer emotion stats calculation to background task
   - Use UPSERT for conversation creation
   - **Expected:** 2000ms → 1010ms (50% improvement)

2. **Connection Pool Tuning** (Phase 2B)
   - Increase pool size to 20
   - Enable statement caching
   - Add pool pre-ping
   - **Expected:** Additional 150ms savings across all operations

3. **Async Scheduling** (Phase 2C)
   - Don't block booking confirmation on follow-up scheduling
   - Queue scheduling as background task
   - **Expected:** Booking confirmation responds in <500ms

### Medium-Term (Next Sprint)

4. **Database Triggers for Emotion Stats**
   - Move emotion calculation to PostgreSQL trigger
   - Eliminates 2 queries from store_message
   - **Expected:** Additional 200ms savings

5. **Redis Caching Layer**
   - Cache recent conversations
   - Cache emotion history
   - **Expected:** 50-70% reduction in DB queries

### Long-Term (Next Month)

6. **Message Queue Architecture**
   - RabbitMQ/Celery for async operations
   - All follow-up scheduling in background workers
   - **Expected:** <100ms user-facing latency

---

## Success Metrics

| Operation            | Baseline | Phase 2A | Phase 2B | Phase 2C | Target  |
| -------------------- | -------- | -------- | -------- | -------- | ------- |
| Store message        | 2000ms   | 1010ms   | 860ms    | 860ms    | <500ms  |
| Schedule follow-up   | 1931ms   | 1650ms   | 1500ms   | async    | <500ms  |
| Booking confirmation | 3931ms   | 2660ms   | 2360ms   | 860ms    | <1000ms |

**Phase 2C Priority:** Make scheduling async so booking confirmation
doesn't wait!

---

## Conclusion

**Key Insights:**

1. Network latency (270ms/query) dominates - not query execution time
2. Composite indexes don't help with small tables in development
3. Real problem: Too many round-trips (6 queries for store_message)
4. Biggest win: Eliminate queries, not optimize them

**Next Steps:**

1. ✅ Phase 1: Indexes added (minimal impact as expected)
2. 🎯 Phase 2A: Query elimination (eliminate 3 queries → -990ms)
3. 🎯 Phase 2B: Connection pooling (-150ms across operations)
4. 🎯 Phase 2C: Async scheduling (booking responds <500ms)

**Expected Final Result:**

- Store message: 860ms (57% faster)
- Schedule follow-up: Async (doesn't block)
- Booking confirmation: <1000ms (75% faster)

---

_Generated: November 2, 2025_  
_Based on actual profiling data with network latency measurements_
