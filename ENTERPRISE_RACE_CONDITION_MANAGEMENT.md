# Enterprise Race Condition Management Guide

**Date**: January 2025 **Context**: Bug #13 - Double Booking Race
Condition Fix **Target**: Production-grade concurrency control

---

## The Problem: TOCTOU Race Condition

**TOCTOU** = Time Of Check, Time Of Use

### Original Bug #13:

```
Request A: check_availability() → TRUE (time: 0ms)
Request B: check_availability() → TRUE (time: 40ms) ← RACE WINDOW
Request A: create_booking() → SUCCESS (time: 80ms)
Request B: create_booking() → SUCCESS (time: 120ms) ❌ DOUBLE BOOKING!
```

**Gap**: 80ms window where both requests see "available" but both
succeed

---

## Enterprise Solutions (Defense in Depth)

### ⭐ Layer 1: Database-Level Unique Constraints **REQUIRED**

**Who uses**: Google, Amazon, Stripe, Shopify

```sql
CREATE UNIQUE INDEX idx_booking_datetime_active
ON bookings(booking_datetime)
WHERE status NOT IN ('cancelled', 'no_show');
```

**Why it's #1**:

- ✅ **Last line of defense** - works even if code fails
- ✅ **Atomic** - guaranteed by database ACID properties
- ✅ **Zero code bugs** - enforced at infrastructure level
- ✅ **Fast** - index-level check (~1ms)

**How it works**:

```python
# Request A creates booking → Index entry added
# Request B tries to create → IntegrityError (unique violation)
```

**Best Practice**:

```python
try:
    booking = Booking(datetime=datetime)
    session.add(booking)
    session.commit()
except IntegrityError as e:
    if "idx_booking_datetime_active" in str(e):
        raise ConflictException("Time slot already booked")
    raise  # Re-raise if different error
```

---

### ⭐ Layer 2: SELECT FOR UPDATE (Row-Level Locking) **RECOMMENDED**

**Who uses**: Uber, Airbnb, DoorDash (high-concurrency booking
systems)

```python
# PostgreSQL row-level locking
booking = session.query(TimeSlot)\
    .filter(TimeSlot.datetime == target_datetime)\
    .with_for_update(nowait=True)\  # ← Acquires exclusive lock
    .first()

if booking:
    raise ConflictException("Already booked")

# Lock held until transaction commits
new_booking = Booking(datetime=target_datetime)
session.add(new_booking)
session.commit()  # ← Lock released
```

**How it works**:

```
Request A: SELECT FOR UPDATE → Lock acquired
Request B: SELECT FOR UPDATE → Waits for lock
Request A: COMMIT → Lock released
Request B: Lock acquired → Sees booking exists → Raises error
```

**Lock Modes**:

- `FOR UPDATE` - Exclusive write lock (blocks all reads/writes)
- `FOR UPDATE SKIP LOCKED` - Skip locked rows (returns empty)
- `FOR UPDATE NOWAIT` - Fail immediately if locked (**best for UI**)

**Best Practice** (NOWAIT):

```python
from sqlalchemy.exc import OperationalError

try:
    slot = session.query(TimeSlot)\
        .with_for_update(nowait=True)\
        .filter_by(datetime=target_datetime)\
        .first()
except OperationalError as e:
    if "could not obtain lock" in str(e):
        raise ConflictException("Another booking in progress")
    raise
```

---

### ⭐ Layer 3: Optimistic Locking (Version Column) **ENTERPRISE STANDARD**

**Who uses**: Hibernate (Java), Entity Framework (.NET), Django ORM

```python
class Booking(Base):
    version = Column(Integer, default=1, nullable=False)

# When updating:
UPDATE bookings
SET status = 'confirmed', version = version + 1
WHERE id = ? AND version = ?  # ← CAS operation

# If rows_affected = 0 → Conflict (someone else updated)
```

**How it works**:

```python
# Request A: Read booking (version=1)
# Request B: Read booking (version=1)
# Request A: UPDATE WHERE version=1 → Success (version=2)
# Request B: UPDATE WHERE version=1 → 0 rows (version is now 2) → Conflict!
```

**SQLAlchemy Implementation**:

```python
from sqlalchemy.orm import Session

booking = session.query(Booking).filter_by(id=booking_id).first()
old_version = booking.version

booking.status = BookingStatus.CONFIRMED
booking.version += 1  # Increment version

session.flush()  # Generate UPDATE

# SQLAlchemy automatically adds:
# WHERE id = ? AND version = old_version

if session.query(Booking).filter_by(id=booking_id).count() == 0:
    raise ConflictException("Booking was modified by another request")
```

**Best Practice** (Automatic with SQLAlchemy 2.0):

```python
from sqlalchemy.orm import Mapped, mapped_column

class Booking(Base):
    version: Mapped[int] = mapped_column(default=1, nullable=False)

    __mapper_args__ = {
        "version_id_col": "version",  # ← Automatic optimistic locking!
    }
```

---

### Layer 4: Distributed Locks (Redis) **ADVANCED**

**Who uses**: Netflix, Twitter, LinkedIn (microservices)

```python
import redis
from contextlib import contextmanager

redis_client = redis.Redis()

@contextmanager
def distributed_lock(resource_id: str, timeout: int = 5):
    """Distributed lock using Redis"""
    lock_key = f"lock:booking:{resource_id}"
    lock_acquired = redis_client.set(lock_key, "1", nx=True, ex=timeout)

    if not lock_acquired:
        raise ConflictException("Resource locked by another process")

    try:
        yield
    finally:
        redis_client.delete(lock_key)

# Usage:
with distributed_lock(f"datetime:{booking_datetime}"):
    booking = create_booking(...)
```

**When to use**:

- ✅ Multi-server deployments (load balancer)
- ✅ Microservices architecture
- ✅ Cross-database transactions
- ❌ Single server (use SELECT FOR UPDATE instead)

---

### Layer 5: Idempotency Keys **API BEST PRACTICE**

**Who uses**: Stripe, Plaid, Twilio (payment/financial APIs)

```python
@app.post("/bookings")
async def create_booking(
    data: BookingCreate,
    idempotency_key: str = Header(...),  # ← Client-provided unique key
):
    # Check if already processed
    existing = get_cached_result(idempotency_key)
    if existing:
        return existing  # ← Return same result (idempotent)

    booking = service.create_booking(data)
    cache_result(idempotency_key, booking, ttl=86400)  # 24h
    return booking
```

**How clients use it**:

```javascript
// Frontend retries are safe
const response = await fetch('/bookings', {
  headers: {
    'Idempotency-Key': generateUUID(), // Same key for retries
  },
  body: bookingData,
});
```

**Best Practice** (Redis cache):

```python
def create_booking_idempotent(data: BookingCreate, idempotency_key: str):
    # Try to get cached result
    cached = redis.get(f"idempotency:{idempotency_key}")
    if cached:
        return json.loads(cached)

    # Create booking
    try:
        booking = create_booking(data)
        # Cache for 24 hours
        redis.setex(
            f"idempotency:{idempotency_key}",
            86400,
            json.dumps(booking.dict())
        )
        return booking
    except IntegrityError:
        # Race condition - fetch the winning booking
        existing = find_booking_by_datetime(data.datetime)
        redis.setex(f"idempotency:{idempotency_key}", 86400, json.dumps(existing.dict()))
        raise ConflictException("Time slot already booked")
```

---

## Recommended Stack (My Hibachi)

### Current Architecture:

- ✅ **Single database** (PostgreSQL)
- ✅ **Single server** (VPS)
- ⚠️ **No distributed locks needed** (yet)

### Recommended Layers:

#### 🔴 **MUST HAVE** (Production blockers):

1. **Unique Index** (`idx_booking_datetime_active`)
   - Prevents double bookings at database level
   - 0 code required, pure SQL

2. **SELECT FOR UPDATE** in `check_availability()`
   - Serializes concurrent requests
   - Prevents TOCTOU race

#### 🟠 **SHOULD HAVE** (Best practices):

3. **Optimistic Locking** (version column)
   - Prevents update conflicts
   - Standard in enterprise ORMs

4. **IntegrityError Handling**
   - User-friendly error messages
   - Lead capture for failed bookings

#### 🟡 **NICE TO HAVE** (Future scaling):

5. **Idempotency Keys** (when adding mobile app/webhooks)
6. **Distributed Locks** (when scaling to multiple servers)

---

## Implementation Plan (Bug #13)

### Step 1: Add Unique Index (Alembic Migration)

```python
# alembic/versions/xxxx_add_booking_unique_index.py
def upgrade():
    op.execute("""
        CREATE UNIQUE INDEX idx_booking_datetime_active
        ON bookings(booking_datetime)
        WHERE status NOT IN ('cancelled', 'no_show')
    """)
```

### Step 2: Add SELECT FOR UPDATE to Repository

```python
class BookingRepository:
    def check_availability_with_lock(
        self,
        datetime: datetime,
        lock: bool = True
    ) -> bool:
        """Check availability with optional row-level lock"""
        query = self.session.query(Booking)\
            .filter(
                Booking.booking_datetime == datetime,
                Booking.status.notin_(['cancelled', 'no_show'])
            )

        if lock:
            query = query.with_for_update(nowait=True)

        existing = query.first()
        return existing is None  # True = available
```

### Step 3: Update Service Layer

```python
class BookingService:
    def create_booking(self, data: BookingCreate) -> Booking:
        try:
            # Lock check (prevents TOCTOU)
            is_available = self.repository.check_availability_with_lock(
                datetime=data.datetime,
                lock=True  # ← Acquires lock
            )

            if not is_available:
                raise ConflictException("Time slot unavailable")

            # Create booking (still holds lock)
            booking = Booking(**data.dict())
            self.session.add(booking)
            self.session.commit()  # ← Releases lock

            return booking

        except IntegrityError as e:
            # Layer 1 caught race (backup defense)
            if "idx_booking_datetime_active" in str(e):
                self.session.rollback()

                # Capture lead for analytics
                if self.lead_service:
                    self.lead_service.capture_failed_booking(data)

                raise ConflictException(
                    message="This time slot was just booked by another customer",
                    error_code=ErrorCode.BOOKING_CONFLICT
                )
            raise
```

### Step 4: Fix Test Fixtures (Async/Sync)

```python
@pytest.fixture
async def db_session(async_session):
    """Async database session for tests"""
    async with async_session() as session:
        yield session
        await session.rollback()

# Update test to use async
async def test_unique_constraint(db_session):
    booking1 = Booking(...)
    db_session.add(booking1)
    await db_session.commit()  # ← await

    booking2 = Booking(...)
    db_session.add(booking2)

    with pytest.raises(IntegrityError):
        await db_session.commit()  # ← await
```

---

## Performance Impact

### SELECT FOR UPDATE Overhead:

- **No contention**: +1-2ms (lock acquisition)
- **High contention**: Requests queue (better than double booking!)
- **Lock timeout**: 5 seconds default (configurable)

### Benchmarks (PostgreSQL):

```
Operation                    Latency    Throughput
----------------------------------------------------
Unique Index Check          0.5ms      2000 req/s
SELECT FOR UPDATE           1.5ms      1500 req/s
Distributed Lock (Redis)    3.0ms      800 req/s
```

**Recommendation**: Use `SELECT FOR UPDATE NOWAIT` for UI (fail fast)

---

## Real-World Examples

### Stripe (Payment Idempotency):

```python
# Every API call requires idempotency key
stripe.PaymentIntent.create(
    amount=1000,
    currency='usd',
    idempotency_key='unique_key_123'  # ← Safe to retry
)
```

### Uber (Ride Matching):

```python
# Distributed lock per driver
with redis_lock(f"driver:{driver_id}"):
    if driver.status == 'available':
        driver.status = 'assigned'
        trip.driver_id = driver.id
        db.commit()
```

### Airbnb (Booking Conflicts):

```sql
-- Unique constraint on (property_id, date, status)
CREATE UNIQUE INDEX idx_property_booking_active
ON bookings(property_id, check_in_date, check_out_date)
WHERE status = 'confirmed';
```

### GitHub (PR Merge Conflicts):

```python
# Optimistic locking with commit SHA
if pr.base_sha != latest_sha:
    raise ConflictException("Branch was updated, please rebase")
```

---

## Testing Strategy

### Unit Tests:

```python
def test_unique_constraint_prevents_double_booking():
    """Database enforces uniqueness"""

def test_select_for_update_queues_requests():
    """Second request waits for first"""

def test_optimistic_locking_detects_conflicts():
    """Version mismatch raises error"""
```

### Integration Tests:

```python
def test_concurrent_booking_attempts():
    """Simulate real race condition"""
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(create_booking, data) for _ in range(10)]
        results = [f.result() for f in futures]

    assert len([r for r in results if r.success]) == 1  # Only 1 succeeds
    assert len([r for r in results if r.conflict]) == 9  # 9 get conflict
```

### Load Tests:

```bash
# Apache Bench - 100 concurrent requests
ab -n 100 -c 10 -p booking.json http://localhost:8000/bookings

# Expected:
# - 1 success (201 Created)
# - 99 conflicts (409 Conflict)
# - 0 errors (500 Internal Server Error) ← CRITICAL
```

---

## Summary: Best Practices

### ✅ DO:

1. **Use unique constraints** - Always your #1 defense
2. **Use SELECT FOR UPDATE** - For TOCTOU prevention
3. **Handle IntegrityError gracefully** - User-friendly messages
4. **Test with concurrent requests** - ThreadPoolExecutor in tests
5. **Use NOWAIT for UI** - Fail fast, don't make users wait
6. **Capture failed bookings as leads** - Business intelligence

### ❌ DON'T:

1. **Don't rely on application-level locks** - Process crashes =
   deadlock
2. **Don't use sleep() for "debouncing"** - Doesn't prevent races
3. **Don't ignore IntegrityError** - Means your uniqueness failed
4. **Don't use shared global state** - Not thread-safe
5. **Don't skip testing race conditions** - Use threading in tests
6. **Don't add locks without timeouts** - Risk deadlocks

---

## Migration Checklist

- [ ] Create Alembic migration for unique index
- [ ] Add `with_for_update()` to repository
- [ ] Update service layer with lock parameter
- [ ] Handle IntegrityError with user message
- [ ] Fix test fixtures (async/await)
- [ ] Add concurrent booking tests
- [ ] Load test with Apache Bench
- [ ] Monitor error rates in production
- [ ] Document for team (this guide!)

**Estimated Time**: 3-4 hours **Risk**: Low (backward compatible,
additive changes) **Business Impact**: Eliminates double bookings
(critical for reputation)
