---
applyTo: '**'
---

# My Hibachi – Core Principles (NEVER Break These)

**Priority: HIGHEST** – These rules override ALL other instructions.

---

## 🔴 The 10 Commandments

### 1. Production Must Always Stay Stable

- Never deploy untested code to production
- Never bypass staging environment
- Always have rollback ready

### 2. Unfinished Features May NEVER Reach Customers

- All WIP code behind feature flags
- Experimental code = dev-only
- No "we'll fix it later" in production

### 3. All Behavior Changes Must Be Behind Feature Flags

- New UI → Flag
- New logic → Flag
- Changed behavior → Flag
- No exceptions

### 4. The `main` Branch Must ALWAYS Be Deployable

- Every commit on main = production-ready
- Broken main = stop everything and fix
- No "temporary" broken states

### 5. When Unsure → Dev-Only + Behind Flag

- Doubt about readiness? → Flag it
- Doubt about safety? → Dev-only
- Doubt about impact? → Test more

### 6. Quality Over Speed

- Clean code > Fast code
- Tested code > Quick code
- Documented code > Shipped code

### 7. Single Source of Truth – No Duplicates

- One place for each piece of info
- No duplicate documentation
- No duplicate logic
- **Fix existing files** instead of creating new duplicates
- If duplicates are necessary, consolidate or delete extras
  immediately
- Before creating any file, check if similar exists

### 8. Clean Main Branch – Production Only

**Main branch must ONLY contain production-ready code:**

| ✅ Allowed in `main`            | ❌ NOT Allowed in `main`          |
| ------------------------------- | --------------------------------- |
| Working source code             | `*_PLAN.md` planning documents    |
| README.md, CONTRIBUTING.md      | `*_ANALYSIS.md` development notes |
| `.github/instructions/` prompts | `*_SUMMARY.md` batch tracking     |
| CI/CD workflows                 | `*_STATUS.md` progress files      |
| Essential deployment guides     | Implementation roadmaps           |
| API documentation               | Development/debug logs            |

**Why this matters:**

- Each batch merge to `main` = traceable deployment
- When bugs occur, `git bisect` can identify the exact batch
- Clean commit history enables proper rollback
- Batch files stay in feature branches until batch completion

**Process:**

1. Planning docs stay in `feature/batch-X-*` branches
2. Only merge working code to `dev`, then to `main`
3. Archive batch planning docs locally or in `archives/` folder
   (gitignored)
4. Main branch commits should reference batch:
   `feat(batch-1): description`

### 9. Monorepo = Unified Deployment

- All 3 apps deploy together
- One branch = One state for all apps
- API compatibility always maintained

### 10. Fix Bugs at All Costs

- Production bug = Drop everything
- Never hide bugs with workarounds
- Root cause > Band-aid

### 11. Security is Non-Negotiable

- No secrets in code
- No credentials in logs
- No sensitive data exposed

---

## 🎯 Code Quality Standards

All code must be:

| Standard             | Requirement                              |
| -------------------- | ---------------------------------------- |
| **Clean**            | Readable, well-named, no dead code       |
| **Modular**          | Single responsibility, composable        |
| **Scalable**         | Async where needed, paginated, efficient |
| **Testable**         | Pure functions, dependency injection     |
| **Maintainable**     | Documented, consistent patterns          |
| **Enterprise-grade** | Production-ready from day one            |

---

## 🏛️ SOLID Principles (MANDATORY)

**All code MUST follow SOLID principles:**

### S - Single Responsibility

```python
# ❌ BAD - Service does too much
class BookingService:
    def create_booking(self): ...
    def send_email(self): ...      # Not its job!
    def calculate_price(self): ...
    def process_payment(self): ... # Not its job!

# ✅ GOOD - One responsibility per class
class BookingService:
    def create_booking(self): ...

class EmailService:
    def send_email(self): ...

class PricingService:
    def calculate_price(self): ...
```

### O - Open/Closed Principle

```python
# ✅ GOOD - Open for extension, closed for modification
class PaymentProcessor(ABC):
    @abstractmethod
    def process(self, amount: Decimal) -> PaymentResult: ...

class StripeProcessor(PaymentProcessor):
    def process(self, amount: Decimal) -> PaymentResult: ...

class PayPalProcessor(PaymentProcessor):  # NEW - no existing code changed!
    def process(self, amount: Decimal) -> PaymentResult: ...
```

### L - Liskov Substitution

```python
# ✅ GOOD - Subclasses are interchangeable with base
def process_payment(processor: PaymentProcessor, amount: Decimal):
    return processor.process(amount)  # Works with ANY processor
```

### I - Interface Segregation

```python
# ❌ BAD - One fat interface
class IBookingManager:
    def create(self): ...
    def delete(self): ...
    def send_notification(self): ...
    def generate_report(self): ...

# ✅ GOOD - Small, focused interfaces
class IBookingWriter:
    def create(self): ...
    def delete(self): ...

class INotifier:
    def send_notification(self): ...
```

### D - Dependency Injection

```python
# ❌ BAD - Hard-coded dependency
class BookingService:
    def __init__(self):
        self.email = EmailService()  # Hard-coded!
        self.db = Database()         # Hard-coded!

# ✅ GOOD - Inject dependencies
class BookingService:
    def __init__(self, email: IEmailService, db: IDatabase):
        self.email = email
        self.db = db
```

---

## 🔧 Error Handling Standards (MANDATORY)

### Python/FastAPI:

```python
# ✅ GOOD - Specific exceptions, proper handling
from fastapi import HTTPException
from app.core.exceptions import BookingNotFoundError, ValidationError

async def get_booking(booking_id: UUID) -> Booking:
    try:
        booking = await booking_repo.get(booking_id)
        if not booking:
            raise BookingNotFoundError(f"Booking {booking_id} not found")
        return booking
    except BookingNotFoundError:
        raise HTTPException(status_code=404, detail="Booking not found")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error getting booking {booking_id}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### TypeScript/React:

```tsx
// ✅ GOOD - Proper error boundaries and handling
async function fetchBooking(id: string): Promise<Booking> {
  try {
    const response = await apiFetch(`/bookings/${id}`);
    if (!response.ok) {
      throw new ApiError(response.status, await response.text());
    }
    return response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      // Handle known API errors
      if (error.status === 404)
        throw new NotFoundError('Booking not found');
      if (error.status === 401) throw new AuthError('Please login');
    }
    // Log unexpected errors
    console.error('Unexpected error:', error);
    throw new UnexpectedError('Something went wrong');
  }
}
```

### Error Handling Rules:

| Rule                       | Description                        |
| -------------------------- | ---------------------------------- |
| **Never swallow errors**   | Always log or re-throw             |
| **Specific over generic**  | Catch specific exceptions first    |
| **User-friendly messages** | Don't expose stack traces to users |
| **Log with context**       | Include IDs, user info, timestamp  |
| **Fail fast**              | Validate early, fail clearly       |

---

## 📡 API Design Standards (REST)

### URL Conventions:

| Pattern                 | Example                | Use            |
| ----------------------- | ---------------------- | -------------- |
| `GET /resources`        | `GET /bookings`        | List all       |
| `GET /resources/:id`    | `GET /bookings/123`    | Get one        |
| `POST /resources`       | `POST /bookings`       | Create         |
| `PUT /resources/:id`    | `PUT /bookings/123`    | Full update    |
| `PATCH /resources/:id`  | `PATCH /bookings/123`  | Partial update |
| `DELETE /resources/:id` | `DELETE /bookings/123` | Delete         |

### Response Codes:

| Code  | Meaning       | Use                      |
| ----- | ------------- | ------------------------ |
| `200` | OK            | Successful GET/PUT/PATCH |
| `201` | Created       | Successful POST          |
| `204` | No Content    | Successful DELETE        |
| `400` | Bad Request   | Validation error         |
| `401` | Unauthorized  | Not logged in            |
| `403` | Forbidden     | No permission            |
| `404` | Not Found     | Resource doesn't exist   |
| `409` | Conflict      | Duplicate/conflict       |
| `422` | Unprocessable | Business logic error     |
| `500` | Server Error  | Unexpected error         |

### Response Format:

```json
// ✅ GOOD - Consistent response structure
{
  "success": true,
  "data": { ... },
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 100
  }
}

// ✅ GOOD - Error response
{
  "success": false,
  "error": {
    "code": "BOOKING_NOT_FOUND",
    "message": "Booking not found",
    "details": { "id": "123" }
  }
}
```

---

## 📝 TypeScript Strict Mode (MANDATORY)

### tsconfig.json Requirements:

```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true
  }
}
```

### Type Safety Rules:

```typescript
// ❌ NEVER use `any`
function process(data: any) { ... }

// ✅ Use proper types or unknown
function process(data: BookingData) { ... }
function parseJSON(data: unknown): BookingData { ... }

// ❌ NEVER use non-null assertion carelessly
const name = user!.name;

// ✅ Use proper null checks
const name = user?.name ?? 'Unknown';
if (user) {
  const name = user.name;
}

// ❌ NEVER ignore type errors
// @ts-ignore
doSomething(wrongType);

// ✅ Fix the actual type issue
doSomething(correctType as ExpectedType);
```

---

## � Security Standards (OWASP Compliance)

### Input Validation (MANDATORY for all user input):

```python
# ✅ GOOD - Pydantic schema validation
from pydantic import BaseModel, EmailStr, Field, validator
from uuid import UUID

class CreateBookingRequest(BaseModel):
    customer_email: EmailStr  # Auto-validated
    guest_count: int = Field(ge=1, le=100)  # Range check
    event_date: date
    venue_address: str = Field(min_length=10, max_length=500)

    @validator('event_date')
    def date_must_be_future(cls, v):
        if v < date.today():
            raise ValueError('Event date must be in the future')
        return v
```

```typescript
// ✅ GOOD - Zod schema validation (TypeScript)
import { z } from 'zod';

const CreateBookingSchema = z.object({
  customerEmail: z.string().email(),
  guestCount: z.number().int().min(1).max(100),
  eventDate: z.string().datetime(),
  venueAddress: z.string().min(10).max(500),
});

// Use in API route
const validated = CreateBookingSchema.parse(req.body);
```

### SQL Injection Prevention:

```python
# ❌ NEVER - String concatenation
query = f"SELECT * FROM users WHERE email = '{email}'"

# ✅ ALWAYS - Parameterized queries (SQLAlchemy handles this)
result = await db.execute(
    select(User).where(User.email == email)  # Safe!
)
```

### XSS Prevention:

```tsx
// ❌ NEVER - Directly rendering user input
<div dangerouslySetInnerHTML={{ __html: userInput }} />

// ✅ ALWAYS - Use React's automatic escaping
<div>{userInput}</div>

// ✅ If HTML needed - sanitize first
import DOMPurify from 'dompurify';
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(userInput) }} />
```

### Authentication & Authorization Checklist:

| Check                    | Required                            |
| ------------------------ | ----------------------------------- |
| JWT tokens expire        | ✅ Max 1 hour for access tokens     |
| Refresh tokens rotate    | ✅ Single-use, invalidate on use    |
| Password hashing         | ✅ bcrypt with cost factor 12+      |
| Rate limiting on auth    | ✅ 5 attempts/minute per IP         |
| RBAC on every endpoint   | ✅ Check permissions, not just auth |
| Sensitive data encrypted | ✅ PII encrypted at rest            |

---

## 📊 Logging Standards (Structured Logging)

### Log Levels (Use Correctly):

| Level      | When to Use                  | Example                           |
| ---------- | ---------------------------- | --------------------------------- |
| `DEBUG`    | Development details          | Variable values, flow traces      |
| `INFO`     | Normal operations            | Request received, booking created |
| `WARNING`  | Recoverable issues           | Retry attempt, deprecated usage   |
| `ERROR`    | Failures requiring attention | API call failed, validation error |
| `CRITICAL` | System-breaking issues       | Database down, out of memory      |

### Structured Logging Format:

```python
import structlog

logger = structlog.get_logger()

# ✅ GOOD - Structured with context
logger.info(
    "booking_created",
    booking_id=str(booking.id),
    customer_id=str(customer.id),
    guest_count=booking.guest_count,
    event_date=booking.event_date.isoformat(),
)

# ❌ BAD - Unstructured string interpolation
logger.info(f"Created booking {booking.id} for {customer.id}")
```

### What to Log / NOT Log:

| ✅ DO Log           | ❌ NEVER Log                 |
| ------------------- | ---------------------------- |
| Request IDs         | Passwords/secrets            |
| User IDs (not PII)  | Credit card numbers          |
| Action taken        | Full SSN/tax IDs             |
| Timestamp           | API keys                     |
| Error codes         | Session tokens               |
| Performance metrics | Email content (may have PII) |

---

## 📈 Monitoring & Alerting Standards

### Required Metrics:

| Metric               | Alert Threshold  | Action            |
| -------------------- | ---------------- | ----------------- |
| Error rate           | > 1% of requests | Page on-call      |
| Response time p95    | > 2 seconds      | Investigate       |
| Database connections | > 80% pool       | Scale or optimize |
| Memory usage         | > 85%            | Investigate leak  |
| Failed logins        | > 10/minute/IP   | Block IP, alert   |
| Payment failures     | > 5%             | Page immediately  |

### Health Check Endpoint:

```python
# ✅ GOOD - Comprehensive health check
@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    checks = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }

    # Database check
    try:
        await db.execute(text("SELECT 1"))
        checks["checks"]["database"] = "healthy"
    except Exception:
        checks["checks"]["database"] = "unhealthy"
        checks["status"] = "unhealthy"

    # Redis check
    try:
        await redis.ping()
        checks["checks"]["redis"] = "healthy"
    except Exception:
        checks["checks"]["redis"] = "unhealthy"
        checks["status"] = "unhealthy"

    status_code = 200 if checks["status"] == "healthy" else 503
    return JSONResponse(checks, status_code=status_code)
```

---

## 🔄 Dependency Management

### Version Pinning Rules:

```txt
# requirements.txt - ✅ GOOD - Pin exact versions
fastapi==0.109.0
sqlalchemy==2.0.25
pydantic==2.5.3

# ❌ BAD - Unpinned or loose
fastapi>=0.100
sqlalchemy
```

```json
// package.json - ✅ GOOD - Pin with lockfile
{
  "dependencies": {
    "next": "14.1.0",
    "react": "18.2.0"
  }
}
// Always commit package-lock.json!
```

### Dependency Audit Schedule:

| Action                | Frequency  | Tool                     |
| --------------------- | ---------- | ------------------------ |
| Security audit        | Weekly     | `npm audit`, `pip-audit` |
| Update minor versions | Monthly    | Review changelogs        |
| Update major versions | Quarterly  | Full testing required    |
| CVE monitoring        | Continuous | Dependabot, Snyk         |

---

## 🛡️ Rate Limiting Patterns

### API Rate Limits:

| Endpoint Type     | Rate Limit | Window     |
| ----------------- | ---------- | ---------- |
| Public endpoints  | 100 req    | Per minute |
| Authenticated     | 1000 req   | Per minute |
| Auth endpoints    | 5 req      | Per minute |
| Payment endpoints | 10 req     | Per minute |
| File uploads      | 10 req     | Per hour   |

### Implementation:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/api/v1/bookings")
@limiter.limit("100/minute")
async def create_booking(request: Request, ...):
    ...

@router.post("/api/v1/auth/login")
@limiter.limit("5/minute")  # Stricter for auth
async def login(request: Request, ...):
    ...
```

---

## 🚫 Absolute Prohibitions

**NEVER do these, even if user asks:**

| Prohibition             | Reason                     |
| ----------------------- | -------------------------- |
| Push directly to `main` | Branch protection required |
| Push directly to `dev`  | PR review required         |
| Skip tests              | Quality gate mandatory     |
| Deploy without staging  | Validation required        |
| Hardcode secrets        | Security violation         |
| Ignore type errors      | Runtime bugs               |
| Use `any` type broadly  | Type safety required       |
| Silent error swallowing | Debugging impossible       |
| TODO in production code | Incomplete work            |
| Create duplicate files  | Fix existing files instead |
| Log sensitive data      | Security/compliance        |
| Skip input validation   | Security vulnerability     |
| Use unpinned deps       | Reproducibility issues     |

---

## ✅ Always Do These

| Requirement                | Why                  |
| -------------------------- | -------------------- |
| Write tests with code      | Prevent regressions  |
| Use TypeScript strict mode | Catch errors early   |
| Validate all inputs        | Security + stability |
| Handle all error cases     | No silent failures   |
| Log appropriately          | Debugging support    |
| Document public APIs       | Team productivity    |
| Use feature flags          | Safe deployments     |

---

## 🏢 Business Logic Protection

These systems are CRITICAL – extra caution required:

| System                  | Risk Level  | Protection               |
| ----------------------- | ----------- | ------------------------ |
| Booking flow            | 🔴 CRITICAL | Flag + extensive tests   |
| Payment/deposits        | 🔴 CRITICAL | Flag + integration tests |
| Pricing logic           | 🔴 CRITICAL | Flag + unit tests        |
| Travel fee calculation  | 🔴 CRITICAL | Flag + validation        |
| Scheduling              | 🟠 HIGH     | Flag + conflict checks   |
| Customer communications | 🟠 HIGH     | Flag + preview mode      |
| AI decision logic       | 🟠 HIGH     | Flag + fallback          |

---

## 📝 Summary

> **When in doubt: Dev-only. Behind flag. Test first. Document
> always.**
