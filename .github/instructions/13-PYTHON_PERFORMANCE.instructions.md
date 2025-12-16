---
applyTo: 'apps/backend/**'
---

# My Hibachi – Python/FastAPI Performance Standards

**Priority: HIGH** – Backend performance directly impacts user experience.

---

## 🔴 The #1 Rule: Prevent N+1 Queries

**Never query inside a loop without eager loading.**

### ❌ The Classic N+1 Problem:

```python
# BAD - 1 query for bookings + N queries for customers
bookings = await db.execute(select(Booking).limit(100))
for booking in bookings.scalars():
    # This triggers a new query for EACH booking!
    print(booking.customer.name)  # N+1 queries!
```

### ✅ The Correct Pattern:

```python
# GOOD - 1 query with eager loading
from sqlalchemy.orm import joinedload, selectinload

query = (
    select(Booking)
    .options(joinedload(Booking.customer))  # Eager load!
    .limit(100)
)
bookings = await db.execute(query)
for booking in bookings.scalars():
    print(booking.customer.name)  # Already loaded!
```

---

## 📊 SQLAlchemy Relationship Loading

| Strategy       | Use When                      | SQL Generated        |
| -------------- | ----------------------------- | -------------------- |
| `joinedload`   | Single related object (1:1)   | LEFT JOIN            |
| `selectinload` | Collection (1:N)              | Separate IN query    |
| `subqueryload` | Large collections             | Subquery             |
| `lazyload`     | Rarely accessed (default)     | Query on access      |

### Example with Multiple Relationships:

```python
query = (
    select(Booking)
    .options(
        joinedload(Booking.customer),           # 1:1 - use JOIN
        selectinload(Booking.line_items),       # 1:N - use IN
        joinedload(Booking.chef),               # 1:1 - use JOIN
    )
    .where(Booking.status == "confirmed")
)
```

---

## 🚀 Lazy Loading for Heavy Services

**Load ML models and heavy dependencies on first use, not at startup.**

### ❌ BAD - Loads on Import (Slow Startup):

```python
# Every import loads 500MB of models!
from transformers import pipeline
nlp_model = pipeline("sentiment-analysis")  # 500MB, 3s load

class AIService:
    def __init__(self):
        self.model = nlp_model  # Already loaded at import
```

### ✅ GOOD - Lazy Load on First Use:

```python
class AIService:
    def __init__(self):
        self._nlp_model = None  # Not loaded yet

    @property
    def nlp_model(self):
        """Lazy load NLP model (500MB, 3s) on first use"""
        if self._nlp_model is None:
            from transformers import pipeline
            self._nlp_model = pipeline("sentiment-analysis")
        return self._nlp_model

    async def analyze(self, text: str):
        return self.nlp_model(text)  # Loads on first call
```

---

## 🔄 Async Best Practices

### 1. Use async for I/O Operations

```python
# ❌ BAD - blocks event loop
import requests
response = requests.get(url)  # Blocking!

# ✅ GOOD - non-blocking
import httpx
async with httpx.AsyncClient() as client:
    response = await client.get(url)  # Async!
```

### 2. Parallel Async Operations

```python
# ❌ BAD - sequential (slow)
result1 = await fetch_customer(id1)
result2 = await fetch_customer(id2)
result3 = await fetch_customer(id3)

# ✅ GOOD - parallel (fast)
import asyncio
results = await asyncio.gather(
    fetch_customer(id1),
    fetch_customer(id2),
    fetch_customer(id3),
)
```

### 3. Don't Block the Event Loop

```python
# ❌ BAD - CPU-intensive in async
async def process():
    # This blocks for 5 seconds!
    result = heavy_computation(data)
    return result

# ✅ GOOD - run in thread pool
from concurrent.futures import ThreadPoolExecutor
import asyncio

executor = ThreadPoolExecutor(max_workers=4)

async def process():
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        executor, heavy_computation, data
    )
    return result
```

---

## 🗄️ Database Optimization

### 1. Pagination for Large Results

```python
# ❌ BAD - loads everything
all_bookings = await db.execute(select(Booking))
return all_bookings.scalars().all()  # 10,000 rows in memory!

# ✅ GOOD - paginate
from src.utils.pagination import paginate

query = select(Booking).where(Booking.status == "confirmed")
result = await paginate(db, query, page=1, per_page=50)
return result  # Only 50 rows
```

### 2. Select Only Needed Columns

```python
# ❌ BAD - selects all 50 columns
query = select(Booking)

# ✅ GOOD - select only needed
query = select(Booking.id, Booking.date, Booking.status)
```

### 3. Use Indexes

```python
# In your model, add indexes for frequently queried columns
class Booking(Base):
    __tablename__ = "bookings"

    id = Column(UUID, primary_key=True)
    status = Column(String, index=True)  # Indexed!
    customer_id = Column(UUID, ForeignKey("customers.id"), index=True)
    created_at = Column(DateTime, index=True)

    __table_args__ = (
        Index("ix_booking_status_date", "status", "event_date"),  # Composite
    )
```

---

## 📦 Caching Patterns

### 1. Redis Caching for Hot Data

```python
from src.core.redis_client import redis_client

async def get_menu_items():
    # Try cache first
    cached = await redis_client.get("menu:items")
    if cached:
        return json.loads(cached)

    # Cache miss - fetch from DB
    items = await db.execute(select(MenuItem))
    result = [item.dict() for item in items.scalars()]

    # Cache for 5 minutes
    await redis_client.setex("menu:items", 300, json.dumps(result))
    return result
```

### 2. Memoization for Expensive Calculations

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def calculate_travel_fee(origin_zip: str, destination_zip: str) -> float:
    """Cached travel fee calculation"""
    # Expensive distance calculation
    distance = calculate_distance(origin_zip, destination_zip)
    return distance * RATE_PER_MILE
```

---

## 🔍 Logging Best Practices

### 1. Use Structured Logging

```python
# ❌ BAD - unstructured
logger.info(f"Processing booking {booking_id} for customer {customer_name}")

# ✅ GOOD - structured (searchable)
logger.info(
    "Processing booking",
    extra={
        "booking_id": booking_id,
        "customer_name": customer_name,
        "action": "process_booking",
    }
)
```

### 2. Appropriate Log Levels

| Level    | Use For                                |
| -------- | -------------------------------------- |
| DEBUG    | Detailed debugging (dev only)          |
| INFO     | Normal operations, milestones          |
| WARNING  | Recoverable issues                     |
| ERROR    | Failures that need attention           |
| CRITICAL | System failures                        |

### 3. Don't Log Sensitive Data

```python
# ❌ BAD
logger.info(f"User login: {email} with password {password}")

# ✅ GOOD
logger.info("User login", extra={"email": email})  # No password!
```

---

## 🚫 Common Anti-Patterns

### 1. Synchronous I/O in Async Functions

```python
# ❌ BAD
async def send_email(data):
    import smtplib
    server = smtplib.SMTP(host)  # Blocking!
    server.send_message(msg)

# ✅ GOOD - use async email library
from aiosmtplib import send

async def send_email(data):
    await send(msg, hostname=host)
```

### 2. Not Using Connection Pooling

```python
# ❌ BAD - new connection per request
async def get_data():
    conn = await asyncpg.connect(DATABASE_URL)
    result = await conn.fetch(query)
    await conn.close()

# ✅ GOOD - use connection pool
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
)
```

### 3. Loading Entire Result Sets

```python
# ❌ BAD - loads all into memory
customers = await db.execute(select(Customer))
all_customers = customers.scalars().all()
for customer in all_customers:  # 100,000 rows in memory!
    process(customer)

# ✅ GOOD - stream results
async with db.stream(select(Customer)) as result:
    async for customer in result.scalars():
        process(customer)  # One at a time
```

---

## 📋 Performance Checklist

Before PR:

- [ ] No N+1 queries (use joinedload/selectinload)
- [ ] Large results paginated
- [ ] Heavy services lazy-loaded
- [ ] Parallel async where possible
- [ ] No blocking I/O in async functions
- [ ] Sensitive data not logged
- [ ] Appropriate indexes on queried columns
- [ ] Redis caching for hot data

---

## 🎯 Performance Budgets

| Metric                    | Budget   | Action if Exceeded         |
| ------------------------- | -------- | -------------------------- |
| API response time (P95)   | < 200ms  | Add caching, optimize query |
| Startup time              | < 5s     | Lazy load services         |
| Memory per request        | < 50MB   | Stream large results       |
| Database queries per req  | < 10     | Use eager loading          |

---

## 🔗 Related Docs

- `docs/01-ARCHITECTURE/DATABASE_ARCHITECTURE.md` – DB design
- `apps/backend/src/utils/pagination.py` – Pagination helper
- `apps/backend/src/core/redis_client.py` – Redis setup

